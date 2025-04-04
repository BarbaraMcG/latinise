# Packages
import os 
import csv
import pickle
import numpy as np
import pandas as pd
import torch
from gen_berts import LatinBERT, LatinTokenizer, BertLatin
from torch.utils.data import DataLoader, Dataset
from torch.nn.utils.rnn import pad_sequence
from transformers import BertForMaskedLM, BertTokenizer, AdamW, get_scheduler
from tqdm import tqdm
from latin_dataset import LatinDataset, collate_fn

# Define paths, find corpus and metadata files
dir_in = os.getcwd()
dir_out = os.path.join(dir_in, "output")
# data_dir = os.path.join("/Users", "valentinalunardi", "Documents", "UCLA_PhD", "Thesis", "Metadata_corrections")
lemmas_or_tokens = "lemmas"
files = os.listdir(os.path.join(dir_in, "preprocessed_"+lemmas_or_tokens+"_2024")) # data_dir
files = [f for f in files[:] if ("IT" in f or "MQDQ" in f)]

# Read selected metadata 
metadata_df = pd.read_csv(os.path.join(dir_in, 'latinise_metadata_2024.csv'), sep = ",") # data_dir
metadata_df = metadata_df[metadata_df['id'].str.startswith(("IT", "MQDQ"))]
metadata_df['date'] = metadata_df['date'].astype(int)

metadata_ph = metadata_df[(metadata_df['date'] >= -300) & (metadata_df['date'] <= 600)]
metadata_ph = metadata_ph.copy()

# Make corpus
punctuation = ['.', ',', '...', ';', ':', '?', '(', ')', '-', '!', '[', ']', '"', "'", '""', '\n', '']

corpus = list()
# files_corpus = metadata_ph.head(5)  # Take only the first 20 files for testing
files_corpus = metadata_ph
for index, df_line in files_corpus.iterrows():
    sign = "+"
    if df_line['date'] < 0:
        sign = "-"
    file_name = df_line['file']
    file = open(os.path.join(dir_in, "preprocessed_"+lemmas_or_tokens+"_2024", file_name), 'r') # data_dir
    while True:
        line = file.readline().strip()
        if line != "":
            corpus.append([token for token in line.split(" ") if token not in punctuation])
        if not line:
            break
    file.close()

# Fine tune Latin BERT

# Set device (use GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 1. Load Corpus Data

# Flatten sentences for tokenization
corpus_texts = [" ".join(sent) for sent in corpus]

# 2. Tokenize Corpus
# tokenizer_path = os.path.join("/Users", "valentinalunardi", "Documents", "GitHub", "latin-bert", "models", "subword_tokenizer_latin", "latin.subword.encoder")
# bert_path = os.path.join("/Users", "valentinalunardi", "Documents", "GitHub", "latin-bert", "models", "latin_bert")
tokenizer_path = os.path.join(dir_in, "models", "subword_tokenizer_latin", "latin.subword.encoder") 
bert_path = os.path.join(dir_in, "models", "latin_bert") 

latin_bert = LatinBERT(tokenizerPath=tokenizer_path, bertPath=bert_path)  # Load model and tokenizer
tokenizer = latin_bert.wp_tokenizer  # LatinTokenizer

dataset = LatinDataset(corpus_texts, tokenizer, max_length=512)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True, collate_fn=collate_fn, num_workers=4)

# 3. Load LatinBERT & Prepare for Fine-Tuning
model = BertForMaskedLM.from_pretrained(bert_path)
model.to(device)
model.train()  # Set to training mode

# Define optimizer & learning rate scheduler
optimizer = AdamW(model.parameters(), lr=5e-5)
lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=500, num_training_steps=len(dataloader) * 3)

# 4. Fine-Tune LatinBERT
epochs = 3  # Number of training epochs

for epoch in range(epochs):
    loop = tqdm(dataloader, leave=True)
    total_loss = 0

    for batch in loop:
        # Move batch to GPU if available
        batch = {k: v.to(device) for k, v in batch.items()}

        # Forward pass
        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],  # Pass attention_mask here
            labels=batch["input_ids"]  # Labels for MLM
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