# Packages
import os 
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from transformers import BertForMaskedLM, BertConfig, AutoTokenizer, DataCollatorForLanguageModeling, get_scheduler
from torch.optim import AdamW
from tqdm import tqdm
from latin_dataset import LatinDataset

# Define paths, find corpus and metadata files
dir_in = os.getcwd()
dir_out = os.path.join(dir_in, "output")
# data_dir = os.path.join("/Users", "valentinalunardi", "Documents", "UCLA_PhD", "Thesis", "Metadata_corrections")
files = os.listdir(os.path.join(dir_in, "new_lemmatized_texts")) # data_dir
files = [f for f in files[:] if ("IT" in f or "MQDQ" in f)]

# Read selected metadata 
metadata_df = pd.read_csv(os.path.join(dir_in, 'latinise_metadata_2024.csv'), sep = ",") # data_dir
metadata_df = metadata_df[metadata_df['id'].str.startswith(("IT", "MQDQ"))]
metadata_df['date'] = metadata_df['date'].astype(int)

metadata_ph = metadata_df[(metadata_df['date'] >= -300) & (metadata_df['date'] <= 600)]
metadata_ph = metadata_ph.copy()

# Prepare corpus
punctuation = ['.', ',', '...', ';', ':', '?', '(', ')', '-', '!', '[', ']', '"', "'", '""', '\n', '']
corpus = list()

# Read files and create corpus
# files_corpus = metadata_ph.head(5)  # Take only the first 5 files for testing
files_corpus = metadata_ph
for index, df_line in files_corpus.iterrows():
    sign = "+"
    if df_line['date'] < 0:
        sign = "-"
    file_name = df_line['file']
    file = open(os.path.join(dir_in, "new_lemmatized_texts", file_name), 'r') # data_dir
    while True:
        line = file.readline().strip()
        if line != "":
            corpus.append([token.lower() for token in line.split(" ") if token not in punctuation])
        if not line:
            break
    file.close()

 
### Fine tune Latin BERT ###

# Set device (use GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Flatten sentences for tokenization
corpus_texts = [" ".join(sent) for sent in corpus]

# Define paths to pre-trained model (huggingface-compatible: https://github.com/andbue/latin-bert-huggingface)
bert_path = os.path.join(dir_in, "models", "latin_bert_huggingface") 

# Load huggingface-compatible tokenizer
tokenizer = AutoTokenizer.from_pretrained(bert_path)

# Tokenize Corpus
dataset = LatinDataset(corpus_texts, tokenizer, max_length=256) # tried max_length=512, but switched back to 256 for compatibility with original LatinBERT

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=True,
    mlm_probability=0.15
)

# DataLoader
dataloader = DataLoader(dataset, batch_size=32, shuffle=True, collate_fn=data_collator, num_workers=4)

# Adjust configuration for dropout (new)
config = BertConfig.from_pretrained(bert_path)
config.hidden_dropout_prob = 0.2
config.attention_probs_dropout_prob = 0.2

# Load pre-trained LatinBERT and prepare for fine-tuning
model = BertForMaskedLM.from_pretrained(bert_path, config=config) # added config
model.to(device)
model.train() 

# Define optimizer & learning rate scheduler
optimizer = AdamW(model.parameters(), lr=3e-5, weight_decay=0.01) # tried lr=5e-5; added weight decay
epochs = 3 # does this need changing?
num_training_steps = len(dataloader) * epochs
lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=int(0.1 * num_training_steps), num_training_steps=num_training_steps) # tried num_warmup_steps=500

# 4. Fine-Tune LatinBERT
for epoch in range(epochs):
    loop = tqdm(dataloader, leave=True)
    total_loss = 0

    for batch in loop: 
        # Move batch to GPU if available
        batch = {k: v.to(device) for k, v in batch.items()}

        # Forward pass
        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],  
            labels=batch["labels"]  # this was "input_ids" – mistake? or necessary change because of Huggingface data collator?
        )
        loss = outputs.loss
        total_loss += loss.item()

        # Backpropagation
        loss.backward()
        optimizer.step()
        lr_scheduler.step()
        optimizer.zero_grad()

        # Update progress bar
        loop.set_description(f"Epoch {epoch + 1}/{epochs}")
        loop.set_postfix(loss=loss.item())

    avg_loss = total_loss / len(dataloader)
    print(f"Epoch {epoch + 1} - Average Loss: {avg_loss:.4f}")

# 5. Save Fine-Tuned Model
model.save_pretrained(os.path.join(dir_out, "fine_tuned_latinbert"))
tokenizer.save_pretrained(os.path.join(dir_out, "fine_tuned_latinbert"))
print("Fine-tuning complete! Model saved.")