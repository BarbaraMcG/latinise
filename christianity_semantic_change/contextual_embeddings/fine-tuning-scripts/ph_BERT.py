# Packages
import os 
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import pandas as pd
import torch
import random
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from transformers import BertForMaskedLM, BertConfig, AutoTokenizer, DataCollatorForLanguageModeling, get_scheduler
from torch.optim import AdamW
from tqdm import tqdm
from latin_dataset import LatinDataset


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

#                 tokens = [token.lower() for token in line.split()]
#                 if tokens:
#                     corpus_texts.append(" ".join(tokens))

#     return corpus_texts

def build_corpus_texts(metadata_subset, texts_dir, lowercase=True):
    corpus_texts = []

    for _, row in metadata_subset.iterrows():
        file_path = os.path.join(texts_dir, row["file"])

        parts = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                if lowercase:
                    line = line.lower()
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

# Read selected metadata 
metadata_df = pd.read_csv(os.path.join(dir_in, 'latinise_metadata_2026.csv'), sep=",")
metadata_df['date_range_end'] = pd.to_numeric(
    metadata_df['date_range_end'], errors="coerce"
)
metadata_df = metadata_df.dropna(subset=['date_range_end'])
metadata_df['date_range_end'] = metadata_df['date_range_end'].astype(int)

metadata_ph = metadata_df[(metadata_df['date_range_end'] > -300) & (metadata_df['date_range_end'] <= 605)]
metadata_ph = metadata_ph.copy()

# Build full corpus texts
texts_dir = os.path.join(dir_in, "non_lemmatized_texts")
corpus_texts = build_corpus_texts(metadata_ph, texts_dir)

 
### Fine tune Latin BERT ###

# Set device (use GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define paths to pre-trained model (huggingface-compatible: https://github.com/andbue/latin-bert-huggingface)
bert_path = os.path.join(dir_in, "models", "latin_bert_huggingface") 

# Load huggingface-compatible tokenizer
tokenizer = AutoTokenizer.from_pretrained(bert_path)

# Split texts into train and validation sets (90/10)
train_texts, val_texts = train_test_split(corpus_texts, test_size=0.1, random_state=SEED)

# Tokenize
train_dataset = LatinDataset(train_texts, tokenizer, max_length=256, stride=128)
val_dataset = LatinDataset(val_texts, tokenizer, max_length=256, stride=128)
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

# Adjust configuration for dropout (new)
config = BertConfig.from_pretrained(bert_path)
config.hidden_dropout_prob = 0.2
config.attention_probs_dropout_prob = 0.2

# Load pre-trained LatinBERT and prepare for fine-tuning
model = BertForMaskedLM.from_pretrained(bert_path, config=config) # added config
model.to(device)
model.train() 

# Define optimizer & learning rate scheduler
optimizer = AdamW(model.parameters(), lr=1e-5, weight_decay=0.01) # tried lr=5e-5 and lr=3e-5; added weight decay
epochs = 2 # tried epochs=3 and epochs=4
num_training_steps = len(train_dataloader) * epochs
lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=int(0.1 * num_training_steps), num_training_steps=num_training_steps) # tried num_warmup_steps=500

# Fine-Tune LatinBERT
for epoch in range(epochs):
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
        loop.set_description(f"Epoch {epoch + 1}/{epochs}")
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

# # Save fine-tuned model (full)
full_ckpt_dir = os.path.join(dir_out, "fine_tuned_latinbert_all")
os.makedirs(full_ckpt_dir, exist_ok=True)
model.save_pretrained(full_ckpt_dir)
tokenizer.save_pretrained(full_ckpt_dir)
print("Fine-tuning on whole corpus complete! Full model saved.")



### Second MLM stage: pre-180 CE subset (date_range_end < 180) ###

# Filter metadata for early subset
metadata_pre180 = metadata_df[(metadata_df['date_range_end'] > -300) & (metadata_df['date_range_end'] < 180)].copy()

# Build corpus for subset
corpus_pre180_texts = build_corpus_texts(metadata_pre180, texts_dir)

# Split texts into train and validation sets (90/10)
train_texts_early, val_texts_early = train_test_split(corpus_pre180_texts, test_size=0.1, random_state=42)

# Tokenize
train_dataset_early = LatinDataset(train_texts_early, tokenizer, max_length=256, stride=128)
val_dataset_early = LatinDataset(val_texts_early, tokenizer, max_length=256, stride=128)

# DataLoader
train_dataloader_early = DataLoader(train_dataset_early, batch_size=32, shuffle=True, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)
val_dataloader_early = DataLoader(val_dataset_early, batch_size=32, shuffle=False, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)

# Load checkpoint from full-corpus fine-tuning
config_early = BertConfig.from_pretrained(full_ckpt_dir)
config_early.hidden_dropout_prob = 0.2
config_early.attention_probs_dropout_prob = 0.2
model_early = BertForMaskedLM.from_pretrained(full_ckpt_dir, config=config_early)
model_early.to(device)
model_early.train()

# Define optimizer & learning rate scheduler (smaller subset)
optimizer_early = AdamW(model_early.parameters(), lr=5e-6, weight_decay=0.01)
epochs_early = 1
num_training_steps_early = len(train_dataloader_early) * epochs_early
lr_scheduler_early = get_scheduler(
    "linear",
    optimizer=optimizer_early,
    num_warmup_steps=int(0.05 * num_training_steps_early),
    num_training_steps=num_training_steps_early
)

# Fine-tune on pre-180 subset
for epoch in range(epochs_early):
    loop = tqdm(train_dataloader_early, leave=True)
    total_loss = 0

    for batch in loop:
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model_early(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"]
        )
        loss = outputs.loss
        total_loss += loss.item()

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model_early.parameters(), max_norm=1.0)
        optimizer_early.step()
        lr_scheduler_early.step()
        optimizer_early.zero_grad()

        loop.set_description(f"Early Epoch {epoch + 1}/{epochs_early}")
        loop.set_postfix(loss=loss.item())

    avg_train_loss = total_loss / len(train_dataloader_early)
    print(f"Early Epoch {epoch + 1} - Average Training Loss: {avg_train_loss:.4f}")

    # Validation
    model_early.eval()
    val_loss = 0
    with torch.no_grad():
        for batch in val_dataloader_early:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model_early(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
            val_loss += outputs.loss.item()
    avg_val_loss = val_loss / len(val_dataloader_early)
    print(f"Early Epoch {epoch + 1} - Validation Loss: {avg_val_loss:.4f}")
    model_early.train()

# Save early model
early_ckpt_dir = os.path.join(dir_out, "fine_tuned_latinbert_pre180")
os.makedirs(early_ckpt_dir, exist_ok=True)
model_early.save_pretrained(early_ckpt_dir)
tokenizer.save_pretrained(early_ckpt_dir)
print("Pre-180 fine-tuning complete! Model saved.")



### Third MLM stage: post-180 CE subset (date_range_end >= 180) ###

# Filter metadata for late subset
metadata_post180 = metadata_df[(metadata_df['date_range_end'] >= 180) & (metadata_df['date_range_end'] <= 605)].copy()

# Build corpus for subset
corpus_post180_texts = build_corpus_texts(metadata_post180, texts_dir)

# Split texts into train and validation sets (90/10)
train_texts_late, val_texts_late = train_test_split(corpus_post180_texts, test_size=0.1, random_state=42)

# Tokenize
train_dataset_late = LatinDataset(train_texts_late, tokenizer, max_length=256, stride=128)
val_dataset_late = LatinDataset(val_texts_late, tokenizer, max_length=256, stride=128)

# DataLoader
train_dataloader_late = DataLoader(train_dataset_late, batch_size=32, shuffle=True, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)
val_dataloader_late = DataLoader(val_dataset_late, batch_size=32, shuffle=False, collate_fn=data_collator, num_workers=num_workers, pin_memory=pin_memory)

# Load checkpoint from full-corpus fine-tuning
config_late = BertConfig.from_pretrained(full_ckpt_dir)
config_late.hidden_dropout_prob = 0.2
config_late.attention_probs_dropout_prob = 0.2
model_late = BertForMaskedLM.from_pretrained(full_ckpt_dir, config=config_late)
model_late.to(device)
model_late.train()

# Define optimizer & learning rate scheduler (smaller subset)
optimizer_late = AdamW(model_late.parameters(), lr=5e-6, weight_decay=0.01)
epochs_late = 1
num_training_steps_late = len(train_dataloader_late) * epochs_late
lr_scheduler_late = get_scheduler(
    "linear",
    optimizer=optimizer_late,
    num_warmup_steps=int(0.05 * num_training_steps_late),
    num_training_steps=num_training_steps_late
)

# Fine-tune on post-180 subset
for epoch in range(epochs_late):
    loop = tqdm(train_dataloader_late, leave=True)
    total_loss = 0

    for batch in loop:
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model_late(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"]
        )
        loss = outputs.loss
        total_loss += loss.item()

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model_late.parameters(), max_norm=1.0)
        optimizer_late.step()
        lr_scheduler_late.step()
        optimizer_late.zero_grad()

        loop.set_description(f"Late Epoch {epoch + 1}/{epochs_late}")
        loop.set_postfix(loss=loss.item())

    avg_train_loss = total_loss / len(train_dataloader_late)
    print(f"Late Epoch {epoch + 1} - Average Training Loss: {avg_train_loss:.4f}")

    # Validation
    model_late.eval()
    val_loss = 0
    with torch.no_grad():
        for batch in val_dataloader_late:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model_late(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
            val_loss += outputs.loss.item()
    avg_val_loss = val_loss / len(val_dataloader_late)
    print(f"Late Epoch {epoch + 1} - Validation Loss: {avg_val_loss:.4f}")
    model_late.train()

# Save late model
late_ckpt_dir = os.path.join(dir_out, "fine_tuned_latinbert_post180")
os.makedirs(late_ckpt_dir, exist_ok=True)
model_late.save_pretrained(late_ckpt_dir)
tokenizer.save_pretrained(late_ckpt_dir)
print("Post-180 fine-tuning complete! Model saved.")
