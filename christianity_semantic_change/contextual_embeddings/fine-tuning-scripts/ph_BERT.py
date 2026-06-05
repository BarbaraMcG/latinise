# Packages
import os 
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import re
import numpy as np
import pandas as pd
import torch
import random
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from transformers import AutoModelForMaskedLM, AutoConfig, AutoTokenizer, AutoModel, DataCollatorForLanguageModeling, get_scheduler
from torch.optim import AdamW
from tqdm import tqdm
from latin_dataset import LatinDataset

# # Earlier corpus-building script which keeps sentence separation
# def build_corpus_texts(metadata_subset, texts_dir):
#     corpus_texts = []
#     for _, df_line in metadata_subset.iterrows():
#         file_name = df_line['file']
#         file_path = os.path.join(texts_dir, file_name)

#         with open(file_path, 'r', encoding='utf-8') as file:
#             for raw_line in file:
#                 line = raw_line.strip()
#                 if not line:
#                     continue

#                 tokens = line.split()
#                 if tokens:
#                     corpus_texts.append(" ".join(tokens))

#     return corpus_texts

# Newer version which concatenates sentences
def build_corpus_texts(metadata_subset, texts_dir):
    corpus_texts = []

    for _, row in metadata_subset.iterrows():
        file_path = os.path.join(texts_dir, row["file"])

        parts = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                parts.append(line)

        if parts:
            corpus_texts.append(" ".join(parts))

    return corpus_texts

# Reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# Define paths, find corpus and metadata files
dir_in = os.getcwd()
dir_out = os.path.join(dir_in, "output")

# Ensure output directory exists
os.makedirs(dir_out, exist_ok=True)

# Workflow mode:
# - prepare_corpus: build and save corpus cache, then exit
# - train: load existing corpus cache and run training
RUN_MODE = os.getenv("RUN_MODE", "prepare_corpus").strip().lower()
corpus_cache_path = os.path.join(dir_out, "ph_corpus_texts.npy")

# To resume from a previous checkpoint directory, set resume_path to that directory instead of None.
# It should contain the saved model, tokenizer, optimizer.pt, scheduler.pt, and training_state.pt.
resume_path = os.path.join(dir_out, "checkpoint_epoch_1")
# resume_path = None

# Build metadata subset only for corpus preparation.
if RUN_MODE == "prepare_corpus":
    metadata_df = pd.read_csv(os.path.join(dir_in, 'latinise_metadata_2026.csv'), sep=",")
    metadata_df['date_range_end'] = pd.to_numeric(
        metadata_df['date_range_end'], errors="coerce"
    )
    metadata_df = metadata_df.dropna(subset=['date_range_end'])
    metadata_df['date_range_end'] = metadata_df['date_range_end'].astype(int)

    metadata_ph = metadata_df[(metadata_df['date_range_end'] > -300) & (metadata_df['date_range_end'] <= 605)]
    metadata_ph = metadata_ph.copy()

    # # TEMPORARY TESTING: sample 20 random texts; comment out for full fine-tuning
    # metadata_ph = metadata_ph.sample(n=20, random_state=SEED).reset_index(drop=True)

    texts_dir = os.path.join(dir_in, "non_lemmatized_texts")
    corpus_texts = build_corpus_texts(metadata_ph, texts_dir)
    np.save(corpus_cache_path, np.array(corpus_texts, dtype=object))
    print(f"Saved corpus cache to {corpus_cache_path}", flush=True)
    raise SystemExit("RUN_MODE=prepare_corpus complete.")
elif RUN_MODE == "train":
    if not os.path.exists(corpus_cache_path):
        raise FileNotFoundError(
            f"Corpus cache not found at {corpus_cache_path}. Run with RUN_MODE=prepare_corpus first."
        )
    corpus_texts = np.load(corpus_cache_path, allow_pickle=True).tolist()
    print(f"Loaded cached corpus from {corpus_cache_path}", flush=True)
else:
    raise ValueError("RUN_MODE must be one of: prepare_corpus, train")

 
### Fine tune Latin BERT ###

# Set device (use GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define path to pre-trained model
# bert_path = os.path.join(dir_in, "models", "latin_bert_huggingface") 
bert_path = "latincy/latin-bert"

# Load official Latin BERT HF tokenizer
tokenizer = AutoTokenizer.from_pretrained(bert_path, trust_remote_code=True)

# Split texts into train and validation sets (90/10)
train_texts, val_texts = train_test_split(corpus_texts, test_size=0.1, random_state=SEED)

# Tokenize
train_dataset = LatinDataset(train_texts, tokenizer, max_length=256, stride=32)
val_dataset = LatinDataset(val_texts, tokenizer, max_length=256, stride=32)
# stride handles long sentences by chunking to max_length using tokenizer overflow.

# Sanity check (truncation)
lens = [len(x["input_ids"]) for x in train_dataset]
print("Train examples:", len(train_dataset))
print("Min/Max len:", min(lens), max(lens))

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=True,
    mlm_probability=0.15
)

# DataLoader settings (overridable on cluster)
num_workers = int(os.getenv("DATALOADER_NUM_WORKERS", "4"))
pin_memory = torch.cuda.is_available()

# DataLoader
train_dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)
val_dataloader = DataLoader(val_dataset, batch_size=32, shuffle=False, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)

# Adjust configuration for dropout
config = AutoConfig.from_pretrained(bert_path, trust_remote_code=True)
config.hidden_dropout_prob = 0.1
config.attention_probs_dropout_prob = 0.1

# Load pre-trained LatinBERT and prepare for fine-tuning
load_path = resume_path if resume_path else bert_path
model = AutoModelForMaskedLM.from_pretrained(load_path, trust_remote_code=True) # add config=config for first epoch; for second epoch, config is loaded from checkpoint and doesn't need to be re-applied (but it should be there if not using checkpoints)
model.to(device)
model.train() 

# Define optimizer & learning rate scheduler
optimizer = AdamW(model.parameters(), lr=1e-5, weight_decay=0.01) # tried lr=5e-5 and lr=3e-5; added weight decay
epochs = 1 # set to 1 if using checkpoints, 2 if not
TOTAL_EPOCHS = 2 # comment out if using checkpoints; only used to calculate num_training_steps for lr_scheduler when using checkpoints
num_training_steps = len(train_dataloader) * TOTAL_EPOCHS # TOTAL_EPOCHS if using checkpoints, epochs if not
lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=int(0.1 * num_training_steps), num_training_steps=num_training_steps) # tried num_warmup_steps=500

start_epoch = 0

# Resume optimizer/scheduler/training state if resuming
if resume_path:
    opt_path = os.path.join(resume_path, "optimizer.pt")
    sched_path = os.path.join(resume_path, "scheduler.pt")
    state_path = os.path.join(resume_path, "training_state.pt")

    if os.path.exists(opt_path):
        optimizer.load_state_dict(torch.load(opt_path, map_location=device))
        print(f"Loaded optimizer state from {opt_path}", flush=True)
    else:
        print("No optimizer state found; starting optimizer fresh.", flush=True)

    if os.path.exists(sched_path):
        lr_scheduler.load_state_dict(torch.load(sched_path, map_location=device))
        print(f"Loaded scheduler state from {sched_path}", flush=True)
    else:
        print("No scheduler state found; starting scheduler fresh.", flush=True)

    if os.path.exists(state_path):
        training_state = torch.load(state_path, map_location="cpu")
        start_epoch = training_state.get("completed_epochs", 0)
        print(f"Resuming after {start_epoch} completed epoch(s)", flush=True)
    else:
        print("No training_state.pt found; start_epoch set to 0.", flush=True)

## SANITY CHECKS ##
print("\n=== TOKENIZER ===")
print("Loaded from:", tokenizer.name_or_path)
print("Class:", tokenizer.__class__.__name__)
print("Vocab size:", tokenizer.vocab_size)
print("Model max length:", tokenizer.model_max_length)
print("Special tokens:", tokenizer.special_tokens_map)
print("tokenizer vocab:", tokenizer.vocab_size)

print("\n=== TOKENIZER CHECK FOR EPOCH 2 ===")
print("model vocab:", model.get_input_embeddings().num_embeddings)
assert tokenizer.vocab_size == model.get_input_embeddings().num_embeddings

print("\n=== CONFIG ===")
print("Hidden size:", config.hidden_size)
print("Layers:", config.num_hidden_layers)
print("Heads:", config.num_attention_heads)
print("Max position embeddings:", config.max_position_embeddings)
print("Vocab size (config):", config.vocab_size)

print("\n=== MODEL ===")
print("Class:", model.__class__.__name__)
print("Embedding shape:", model.get_input_embeddings().weight.shape)

print("\n=== DEVICE ===")
print("CUDA available:", torch.cuda.is_available())




# Fine-Tune LatinBERT
for epoch in range(start_epoch, start_epoch + epochs): # start_epoch, start_epoch + epochs OR epochs if not using checkpoints
    loop = tqdm(train_dataloader, leave=True)
    total_loss = 0

    for batch in loop: 
        # Move batch to GPU if available
        batch = {k: v.to(device) for k, v in batch.items()}

        # Forward pass
        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],  
            labels=batch["labels"]
        )
        loss = outputs.loss
        total_loss += loss.item()

        # Backpropagation
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        lr_scheduler.step()
        optimizer.zero_grad()

        # Update progress bar
        loop.set_description(f"Epoch {epoch + 1}/{TOTAL_EPOCHS}") # f"Epoch {epoch + 1}/{epochs}" if not using checkpoints
        loop.set_postfix(loss=loss.item())

    avg_train_loss = total_loss / len(train_dataloader)
    print(f"Epoch {epoch + 1} - Average Training Loss: {avg_train_loss:.4f}")


    # Validation
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for batch in val_dataloader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
            val_loss += outputs.loss.item()
    avg_val_loss = val_loss / len(val_dataloader)
    print(f"Epoch {epoch + 1} - Validation Loss: {avg_val_loss:.4f}")
    model.train()
    
    # # Save checkpoint after each epoch
    # ckpt_dir = os.path.join(dir_out, f"checkpoint_epoch_{epoch + 1}")
    # os.makedirs(ckpt_dir, exist_ok=True)

    # model.save_pretrained(ckpt_dir)
    # # tokenizer.save_pretrained(ckpt_dir)
    # torch.save(optimizer.state_dict(), os.path.join(ckpt_dir, "optimizer.pt"))
    # torch.save(lr_scheduler.state_dict(), os.path.join(ckpt_dir, "scheduler.pt"))
    # torch.save(
    #     {"completed_epochs": epoch + 1},
    #     os.path.join(ckpt_dir, "training_state.pt"),
    # )

    # print(f"Saved checkpoint to {ckpt_dir}", flush=True)

# Save fine-tuned model (full)
full_ckpt_dir = os.path.join(dir_out, "fine_tuned_latinbert")
os.makedirs(full_ckpt_dir, exist_ok=True)
model.save_pretrained(full_ckpt_dir)
tokenizer.save_pretrained(full_ckpt_dir)
print("Fine-tuning on whole corpus complete! Full model saved.")



# ### Second MLM stage: pre-180 CE subset (date_range_end < 180) ###

# # Filter metadata for early subset
# metadata_pre180 = metadata_df[(metadata_df['date_range_end'] > -300) & (metadata_df['date_range_end'] < 180)].copy()

# # Build corpus for subset
# corpus_pre180_texts = build_corpus_texts(metadata_pre180, texts_dir)

# # Split texts into train and validation sets (90/10)
# train_texts_early, val_texts_early = train_test_split(corpus_pre180_texts, test_size=0.1, random_state=SEED)

# # Tokenize
# train_dataset_early = LatinDataset(train_texts_early, tokenizer, max_length=256, stride=32)
# val_dataset_early = LatinDataset(val_texts_early, tokenizer, max_length=256, stride=32)

# # DataLoader
# train_dataloader_early = DataLoader(train_dataset_early, batch_size=32, shuffle=True, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)
# val_dataloader_early = DataLoader(val_dataset_early, batch_size=32, shuffle=False, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)

# # Load checkpoint from full-corpus fine-tuning
# config_early = BertConfig.from_pretrained(full_ckpt_dir)
# config_early.hidden_dropout_prob = 0.2
# config_early.attention_probs_dropout_prob = 0.2
# model_early = BertForMaskedLM.from_pretrained(full_ckpt_dir, config=config_early)
# model_early.to(device)
# model_early.train()

# # Define optimizer & learning rate scheduler (smaller subset)
# optimizer_early = AdamW(model_early.parameters(), lr=5e-6, weight_decay=0.01)
# epochs_early = 1
# num_training_steps_early = len(train_dataloader_early) * epochs_early
# lr_scheduler_early = get_scheduler(
#     "linear",
#     optimizer=optimizer_early,
#     num_warmup_steps=int(0.05 * num_training_steps_early),
#     num_training_steps=num_training_steps_early
# )

# # Fine-tune on pre-180 subset
# for epoch in range(epochs_early):
#     loop = tqdm(train_dataloader_early, leave=True)
#     total_loss = 0

#     for batch in loop:
#         batch = {k: v.to(device) for k, v in batch.items()}
#         outputs = model_early(
#             input_ids=batch["input_ids"],
#             attention_mask=batch["attention_mask"],
#             labels=batch["labels"]
#         )
#         loss = outputs.loss
#         total_loss += loss.item()

#         loss.backward()
#         torch.nn.utils.clip_grad_norm_(model_early.parameters(), max_norm=1.0)
#         optimizer_early.step()
#         lr_scheduler_early.step()
#         optimizer_early.zero_grad()

#         loop.set_description(f"Early Epoch {epoch + 1}/{epochs_early}")
#         loop.set_postfix(loss=loss.item())

#     avg_train_loss = total_loss / len(train_dataloader_early)
#     print(f"Early Epoch {epoch + 1} - Average Training Loss: {avg_train_loss:.4f}")

#     # Validation
#     model_early.eval()
#     val_loss = 0
#     with torch.no_grad():
#         for batch in val_dataloader_early:
#             batch = {k: v.to(device) for k, v in batch.items()}
#             outputs = model_early(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
#             val_loss += outputs.loss.item()
#     avg_val_loss = val_loss / len(val_dataloader_early)
#     print(f"Early Epoch {epoch + 1} - Validation Loss: {avg_val_loss:.4f}")
#     model_early.train()

# # Save early model
# early_ckpt_dir = os.path.join(dir_out, "fine_tuned_latinbert_pre180")
# os.makedirs(early_ckpt_dir, exist_ok=True)
# model_early.save_pretrained(early_ckpt_dir)
# tokenizer.save_pretrained(early_ckpt_dir)
# print("Pre-180 fine-tuning complete! Model saved.")



# ### Third MLM stage: post-180 CE subset (date_range_end >= 180) ###

# # Filter metadata for late subset
# metadata_post180 = metadata_df[(metadata_df['date_range_end'] >= 180) & (metadata_df['date_range_end'] <= 605)].copy()

# # Build corpus for subset
# corpus_post180_texts = build_corpus_texts(metadata_post180, texts_dir)

# # Split texts into train and validation sets (90/10)
# train_texts_late, val_texts_late = train_test_split(corpus_post180_texts, test_size=0.1, random_state=SEED)

# # Tokenize
# train_dataset_late = LatinDataset(train_texts_late, tokenizer, max_length=256, stride=32)
# val_dataset_late = LatinDataset(val_texts_late, tokenizer, max_length=256, stride=32)

# # DataLoader
# train_dataloader_late = DataLoader(train_dataset_late, batch_size=32, shuffle=True, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)
# val_dataloader_late = DataLoader(val_dataset_late, batch_size=32, shuffle=False, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)

# # Load checkpoint from full-corpus fine-tuning
# config_late = BertConfig.from_pretrained(full_ckpt_dir)
# config_late.hidden_dropout_prob = 0.2
# config_late.attention_probs_dropout_prob = 0.2
# model_late = BertForMaskedLM.from_pretrained(full_ckpt_dir, config=config_late)
# model_late.to(device)
# model_late.train()

# # Define optimizer & learning rate scheduler (smaller subset)
# optimizer_late = AdamW(model_late.parameters(), lr=5e-6, weight_decay=0.01)
# epochs_late = 1
# num_training_steps_late = len(train_dataloader_late) * epochs_late
# lr_scheduler_late = get_scheduler(
#     "linear",
#     optimizer=optimizer_late,
#     num_warmup_steps=int(0.05 * num_training_steps_late),
#     num_training_steps=num_training_steps_late
# )

# # Fine-tune on post-180 subset
# for epoch in range(epochs_late):
#     loop = tqdm(train_dataloader_late, leave=True)
#     total_loss = 0

#     for batch in loop:
#         batch = {k: v.to(device) for k, v in batch.items()}
#         outputs = model_late(
#             input_ids=batch["input_ids"],
#             attention_mask=batch["attention_mask"],
#             labels=batch["labels"]
#         )
#         loss = outputs.loss
#         total_loss += loss.item()

#         loss.backward()
#         torch.nn.utils.clip_grad_norm_(model_late.parameters(), max_norm=1.0)
#         optimizer_late.step()
#         lr_scheduler_late.step()
#         optimizer_late.zero_grad()

#         loop.set_description(f"Late Epoch {epoch + 1}/{epochs_late}")
#         loop.set_postfix(loss=loss.item())

#     avg_train_loss = total_loss / len(train_dataloader_late)
#     print(f"Late Epoch {epoch + 1} - Average Training Loss: {avg_train_loss:.4f}")

#     # Validation
#     model_late.eval()
#     val_loss = 0
#     with torch.no_grad():
#         for batch in val_dataloader_late:
#             batch = {k: v.to(device) for k, v in batch.items()}
#             outputs = model_late(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
#             val_loss += outputs.loss.item()
#     avg_val_loss = val_loss / len(val_dataloader_late)
#     print(f"Late Epoch {epoch + 1} - Validation Loss: {avg_val_loss:.4f}")
#     model_late.train()

# # Save late model
# late_ckpt_dir = os.path.join(dir_out, "fine_tuned_latinbert_post180")
# os.makedirs(late_ckpt_dir, exist_ok=True)
# model_late.save_pretrained(late_ckpt_dir)
# tokenizer.save_pretrained(late_ckpt_dir)
# print("Post-180 fine-tuning complete! Model saved.")
