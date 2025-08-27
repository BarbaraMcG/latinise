# Packages
import os 
import pandas as pd
# import pickle
import h5py
from gen_berts import LatinBERT
from tqdm import tqdm
import time

# Define paths (re-check)
dir_in = os.path.dirname(os.getcwd())
dir_out = os.path.join(dir_in, "bert_output")  
metadata_file = os.path.join(os.path.dirname(dir_in), 'latinise_metadata_2024.csv')  
lemmatized_texts_dir = os.path.join(os.path.dirname(dir_in), "new_lemmatized_texts")  
github_dir = os.path.abspath(os.path.join(os.path.dirname(dir_in), "..", ".."))
tokenizer_path = os.path.join(github_dir, "latin-bert", "models", "subword_tokenizer_latin", "latin.subword.encoder")
bert_path = os.path.join(github_dir, "latin-bert", "models", "latin_bert")

# Ensure output directory exists
os.makedirs(dir_out, exist_ok=True)

# Find corpus files
files = os.listdir(lemmatized_texts_dir)
files = [f for f in files if ("IT" in f or "MQDQ" in f)]

# Read selected metadata
metadata_df = pd.read_csv(metadata_file, sep=",")
metadata_df = metadata_df[metadata_df['id'].str.startswith(("IT", "MQDQ"))]
metadata_df['date'] = metadata_df['date'].astype(int)

# Prepare corpus
print("Creating the corpora...")
punctuation = ['.', ',', '...', ';', ':', '?', '(', ')', '-', '!', '[', ']', '"', "'", '""', '\n', '']
corpus = list()

# Read files and create corpus
files_corpus = metadata_df
for index, df_line in files_corpus.iterrows():
    sign = "+"
    if df_line['date'] < 0:
        sign = "-"
    file_name = df_line['file']
    file = open(os.path.join(lemmatized_texts_dir, file_name), 'r')
    while True:
        line = file.readline().strip()
        if line != "":
            corpus.append([token.lower() for token in line.split(" ") if token not in punctuation])
        if not line:
            break
    file.close()

# Create time intervals
first_date = min(metadata_df.date)
second_date = 499
third_date = 1399
last_date = max(metadata_df.date)

intervals = [first_date, second_date + 1, third_date + 1, last_date]
n_intervals = 3

metadata_df['time_interval'] = ""
for t in range(len(intervals)-1):
    metadata_df_t = metadata_df.loc[metadata_df['date'].isin(range(intervals[t],intervals[t+1]))]
    metadata_df.loc[metadata_df['date'].isin(range(intervals[t],intervals[t+1])),'time_interval'] = intervals[t]

#Prepare time corpora
time2corpus = dict()

# Read files and create time corpora:
for t in range(n_intervals+1):
    files_corpus_t = metadata_df.loc[metadata_df['time_interval'] == intervals[t]]
    corpus_t = list()
    for index, df_line in files_corpus_t.iterrows():
        sign = "+"
        if df_line['date'] < 0:
            sign = "-"
        file_name = df_line['file']
        file = open(os.path.join(lemmatized_texts_dir, file_name), 'r')
        # sentences_this_file = list()
        while True:
            line = file.readline().strip()
            if line != "":
                corpus_t.append([token.lower() for token in line.split(" ") if token not in punctuation])
            # if line is empty end of file is reached
            if not line:
                break
        file.close()
    time2corpus[t] = corpus_t

# Define function to extract embeddings
def calculate_embeddings(corpus, dir_out, output_filename, tokenizer_path, bert_path, max_seq_length=256):
    output_path = os.path.join(dir_out, output_filename)

    # Initialize the LatinBERT class
    latin_bert = LatinBERT(tokenizerPath=tokenizer_path, bertPath=bert_path)

    # Flatten the lists into strings and truncate to max_seq_length
    flattened_corpus = [' '.join(sent)[:max_seq_length] for sent in corpus]

    # Initialize progress bar
    print(f"Processing {len(flattened_corpus)} sentences for {output_filename}...")
    start_time = time.time()
    bert_sents = []

    # Process the corpus in chunks to track progress
    chunk_size = 100  # Adjust chunk size as needed
    for i in tqdm(range(0, len(flattened_corpus), chunk_size), desc="Processing"):
        chunk = flattened_corpus[i:i + chunk_size]
        bert_sents.extend(latin_bert.get_berts(chunk))

    # Save output to HDF5
    with h5py.File(output_path, 'w') as f:
        for idx, emb_list in enumerate(bert_sents):
            grp = f.create_group(f"sentence_{idx}")
            for j, (token, embedding) in enumerate(emb_list):
                grp.create_dataset(f"token_{j}_embedding", data=embedding, compression="gzip")
                grp.attrs[f"token_{j}"] = token
    print(f"Results saved to {output_path}")

    # Calculate and display elapsed time
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Processing completed in {int(minutes)}m {seconds:.2f}s.")

    return output_path

# # Extract embeddings for first timeframe and save
print("Producing embeddings for the first timeframe...")
bert_sents_t0_path = calculate_embeddings(time2corpus[0], dir_out, "bert_t0_results.h5", tokenizer_path, bert_path)
print("Embeddings for the first timeframe completed.\n")

# Extract embeddings for second timeframe and save
print("Producing embeddings for the second timeframe...")
bert_sents_t1_path = calculate_embeddings(time2corpus[1], dir_out, "bert_t1_results.h5", tokenizer_path, bert_path)
print("Embeddings for the second timeframe completed.\n")

# Extract embeddings for third timeframe and save
print("Producing embeddings for the third timeframe...")
bert_sents_t1_path = calculate_embeddings(time2corpus[2], dir_out, "bert_t2_results.h5", tokenizer_path, bert_path)
print("Embeddings for the third timeframe completed.\n")
