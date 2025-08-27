# Packages
import os 
import pandas as pd
import torch
import h5py
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm
import time

# Define paths
# dir_in = os.path.dirname(os.getcwd())
# dir_out = os.path.join(dir_in, "output")  
# metadata_file = os.path.join(os.path.dirname(dir_in), 'latinise_metadata_2024.csv')  
# lemmatized_texts_dir = os.path.join(os.path.dirname(dir_in),"data", "new_lemmatized_texts")  
# latin_bert_finetuned = os.path.join(dir_in, "fine_tuned_latinbert")
dir_in = os.getcwd()
dir_out = os.path.join(dir_in, "output", "embeddings_neolatin_finetuned") 
metadata_file = os.path.join(dir_in, 'latinise_metadata_2024.csv')  
lemmatized_texts_dir = os.path.join(dir_in, "preprocessed_tokens_2024")
latin_bert_finetuned = os.path.join(dir_in, "output", "fine_tuned_neolatinbert")


# Ensure output directory exists
os.makedirs(dir_out, exist_ok=True)

# Find corpus files
files = os.listdir(lemmatized_texts_dir)
files = [f for f in files if ("IT" in f or "MQDQ" in f)]

# Read selected metadata 
metadata_df = pd.read_csv(metadata_file, sep = ",")
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
second_date = -1
third_date = 599
fourth_date = 1399
last_date = max(metadata_df.date)

intervals = [first_date, second_date + 1, third_date + 1, fourth_date + 1, last_date]
n_intervals = 4

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
def calculate_embeddings(corpus, model_name, output_filename, batch_size=32):
    """
    Calculate embeddings for a given corpus using a Hugging Face-compatible tokenizer and model.

    Args:
        corpus (list of list of str): List of tokenized sentences (each sentence is a list of words).
        model_name (str): Name or path of the Hugging Face model to use.
        output_path (str): Path to save the calculated embeddings.
        batch_size (int): Batch size for processing sentences.

    Returns:
        list: A list of sentence embeddings, where each sentence is a list of (word, embedding) tuples.
    """
    output_path = os.path.join(dir_out, output_filename)

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()  # Set model to evaluation mode

    # Device setup (GPU if available)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Initialize list to store embeddings for all sentences
    all_embeddings = []

    # Initialize progress bar
    print(f"Processing {len(corpus)} sentences for {output_filename}...")
    start_time = time.time()

    # Process sentences in batches
    for i in tqdm(range(0, len(corpus), batch_size), desc="Processing batches"):
        batch = corpus[i:i + batch_size]

        # Tokenize with word alignment
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True,
                           is_split_into_words=True, max_length=256)
        inputs = {key: val.to(device) for key, val in inputs.items()}

        # Forward pass to get embeddings
        with torch.no_grad():
            outputs = model(**inputs)

        # Extract embeddings (use the last hidden state)
        last_hidden_state = outputs.last_hidden_state

        # For each sentence in the batch
        for j, sentence in enumerate(batch):
            word_ids = tokenizer(batch[j], is_split_into_words=True).word_ids()
            sentence_embedding = []

            # Add [CLS] token embedding
            cls_embedding = last_hidden_state[j, 0].cpu().numpy()
            sentence_embedding.append(("[CLS]", cls_embedding))

            # Add word embeddings
            for word_idx in sorted(set(wid for wid in word_ids if wid is not None)):
                if word_idx is None:
                    continue
                
                # Get the token indices corresponding to the word
                token_indices = [idx for idx, wid in enumerate(word_ids) if wid == word_idx]

                # Filter out indices that are out of bounds
                token_indices = [idx for idx in token_indices if idx < last_hidden_state.size(1)]

                # Skip if token_indices is empty
                if not token_indices:
                    print(f"Skipping word_idx {word_idx} due to empty or invalid token_indices.")
                    continue

                # Average the embeddings for the tokens corresponding to the word
                word_embedding = last_hidden_state[j, token_indices, :].mean(dim=0).cpu().numpy()

                # Get the word (lemma) from the original sentence
                lemma = sentence[word_idx]

                # Append the lemma and its embedding
                sentence_embedding.append((lemma, word_embedding))

            # Add [SEP] token embedding
            sep_embedding = last_hidden_state[j, -1].cpu().numpy()
            sentence_embedding.append(("[SEP]", sep_embedding))

            # Append full sentence embedding to master list
            all_embeddings.append(sentence_embedding)

    # Save to file
    if not output_path.endswith('.h5'):
        output_path += '.h5'

    with h5py.File(output_path, 'w') as f:
        for idx, sentence_embedding in enumerate(all_embeddings):
            grp = f.create_group(f"sentence_{idx}")
            for j, (lemma, embedding) in enumerate(sentence_embedding):
                grp.create_dataset(f"token_{j}_embedding", data=embedding, compression="gzip")
                grp.attrs[f"token_{j}"] = lemma

    # Calculate and display elapsed time
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Embeddings saved to {output_path}.")
    print(f"Processing completed in {int(minutes)}m {seconds:.2f}s.")

    return output_path


# Extract embeddings for first timeframe and save
print("Producing embeddings for the first timeframe...")
berts_finetuned_t0 = calculate_embeddings(time2corpus[0], latin_bert_finetuned, "berts_finetuned_t0.h5")
print("Embeddings for the first timeframe completed.\n")

# # Extract embeddings for second timeframe and save
# print("Producing embeddings for the second timeframe...")
# berts_finetuned_t1 = calculate_embeddings(time2corpus[1], latin_bert_finetuned, "berts_finetuned_t1.h5")
# print("Embeddings for the second timeframe completed.\n")

# # Extract embeddings for third timeframe and save
# print("Producing embeddings for the third timeframe...")
# berts_finetuned_t2 = calculate_embeddings(time2corpus[2], latin_bert_finetuned, "berts_finetuned_t2.h5")
# print("Embeddings for the third timeframe completed.\n")

# # Extract embeddings for third timeframe and save
# print("Producing embeddings for the third timeframe...")
# berts_finetuned_t3 = calculate_embeddings(time2corpus[3], latin_bert_finetuned, "berts_finetuned_t3.h5")
# print("Embeddings for the fourth timeframe completed.\n")