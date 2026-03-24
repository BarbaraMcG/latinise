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
# latin_bert_finetuned = os.path.join(dir_in, "latin-bert-huggingface-finetuned")
dir_in = os.getcwd()
dir_out = os.path.join(dir_in, "output", "embeddings_finetuned_2") 
metadata_file = os.path.join(dir_in, 'latinise_metadata_2024.csv')  
lemmatized_texts_dir = os.path.join(dir_in, "new_lemmatized_texts")
latin_bert_finetuned = os.path.join(dir_in, "output", "fine_tuned_latinbert_2")


# Ensure output directory exists
os.makedirs(dir_out, exist_ok=True)

# Find corpus files
files = os.listdir(lemmatized_texts_dir)
files = [f for f in files if ("IT" in f or "MQDQ" in f)]

# Read selected metadata 
metadata_df = pd.read_csv(metadata_file, sep = ",")
metadata_df = metadata_df[metadata_df['id'].str.startswith(("IT", "MQDQ"))]
metadata_df['date'] = metadata_df['date'].astype(int)
metadata_ph = metadata_df[(metadata_df['date'] >= -300) & (metadata_df['date'] <= 600)]
metadata_ph = metadata_ph.copy()

# Prepare corpus
print("Creating the corpora...")
punctuation = ['.', ',', '...', ';', ':', '?', '(', ')', '-', '!', '[', ']', '"', "'", '""', '\n', '']
corpus = list()

# Read files and create corpus
files_corpus = metadata_ph
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
first_date = -300
last_date = 600
size_interval = 450
n_intervals = round((last_date-first_date)/size_interval)

intervals = [None]*(n_intervals+1)
for t in range(n_intervals+1):
    if t == 0:
        intervals[t] = int(first_date)
    else:
        intervals[t] = int(intervals[t-1]+size_interval)

metadata_ph['time_interval'] = ""
for t in range(len(intervals)-1):
    metadata_df_t = metadata_ph.loc[metadata_ph['date'].isin(range(intervals[t],intervals[t+1]))]
    metadata_ph.loc[metadata_df['date'].isin(range(intervals[t],intervals[t+1])),'time_interval'] = intervals[t]

#Prepare time corpora
time2corpus = dict()

# Read files and create time corpora:
for t in range(n_intervals+1):
    files_corpus_t = metadata_ph.loc[metadata_ph['time_interval'] == intervals[t]]
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

# Prepare Christian and non-Christian subcorpus
selected_texts = [
    "IT-LAT0062", "IT-LAT0246", "IT-LAT0737", "IT-LAT0058", "IT-LAT0749", "IT-LAT0256",
    "IT-LAT0350", "IT-LAT0750", "IT-LAT0606", "IT-LAT0744", "IT-LAT0736", "IT-LAT0747",
    "IT-LAT0755", "IT-LAT0788", "IT-LAT0471", "IT-LAT0746", "IT-LAT0865", "IT-LAT0059",
    "MQDQ-41", "MQDQ-39", "MQDQ-40", "IT-LAT0264", "IT-LAT0268", "MQDQ-1",
    "MQDQ-151", "MQDQ-350", "MQDQ-617", "MQDQ-581", "MQDQ-579", "IT-LAT0878",
    "MQDQ-56", "IT-LAT0719", "IT-LAT0263", "IT-LAT0793", "IT-LAT0397", "MQDQ-512",
    "MQDQ-609", "MQDQ-281", "IT-LAT0410", "MQDQ-180", "IT-LAT0847", "IT-LAT0843",
    "IT-LAT0726", "IT-LAT0403", "MQDQ-492", "IT-LAT1004", "IT-LAT0015", "IT-LAT0612",
    "MQDQ-282", "MQDQ-368", "MQDQ-367", "MQDQ-371", "MQDQ-374", "MQDQ-375",
    "MQDQ-369", "MQDQ-373", "MQDQ-366", "MQDQ-372", "IT-LAT0270", "MQDQ-280",
    "MQDQ-279", "IT-LAT0001", "MQDQ-278", "MQDQ-365", "IT-LAT0880", "MQDQ-52",
    "MQDQ-49", "MQDQ-55", "MQDQ-48", "MQDQ-53", "MQDQ-54", "MQDQ-50", "MQDQ-51",
    "MQDQ-243", "MQDQ-242", "MQDQ-381", "IT-LAT0016", "IT-LAT0768", "IT-LAT0608",
    "MQDQ-360", "MQDQ-361", "MQDQ-189", "MQDQ-422", "MQDQ-364", "IT-LAT0904",
    "MQDQ-66", "MQDQ-423", "IT-LAT0610", "MQDQ-363", "LC-16_1", "IT-LAT0776",
    "MQDQ-285", "MQDQ-608", "MQDQ-445", "MQDQ-120", "MQDQ-118", "MQDQ-59",
    "MQDQ-60", "MQDQ-382", "MQDQ-287", "MQDQ-383", "MQDQ-111", "MQDQ-79",
    "MQDQ-81", "MQDQ-623", "MQDQ-622", "MQDQ-415", "MQDQ-416", "MQDQ-618",
    "IT-LAT0987", "IT-LAT0791", "IT-LAT0867", "IT-LAT0250", "MQDQ-353", "MQDQ-183",
    "IT-LAT1001", "MQDQ-354", "MQDQ-352", "IT-LAT0196", "IT-LAT0906", "IT-LAT0990_6",
    "MQDQ-537", "MQDQ-209", "MQDQ-210", "IT-LAT0482", "IT-LAT0990", "IT-LAT0990_1",
    "IT-LAT0990_9", "IT-LAT0990_2", "IT-LAT0011", "IT-LAT0990_3", "MQDQ-523",
    "MQDQ-524", "MQDQ-525", "MQDQ-526", "MQDQ-527", "MQDQ-528", "IT-LAT0990_4",
    "IT-LAT0990_5", "IT-LAT0990_7", "MQDQ-211", "IT-LAT0435", "MQDQ-531",
    "MQDQ-532", "IT-LAT0783", "MQDQ-619", "IT-LAT0978", "MQDQ-182", "MQDQ-95",
    "MQDQ-475", "MQDQ-191", "MQDQ-188", "MQDQ-535", "MQDQ-536", "MQDQ-533",
    "MQDQ-534"
]

# Metadata for Christian and non-Christian subcorpus
metadata_ph_christian = metadata_ph[(metadata_ph['id'].isin(selected_texts))]
metadata_ph_nonchristian = metadata_ph[(metadata_ph['time_interval']==150) & (~metadata_ph['id'].isin(selected_texts))]

# Read files and create Christian subcorpus
corpus_christi = list()
files_corpus_christi = metadata_ph_christian
for index, df_line in files_corpus_christi.iterrows():
    sign = "+"
    if df_line['date'] < 0:
        sign = "-"
    file_name = df_line['file']
    file = open(os.path.join(lemmatized_texts_dir, file_name), 'r')
    # sentences_this_file = list()
    while True:
        line = file.readline().strip()
        if line != "":
            corpus_christi.append([token.lower() for token in line.split(" ") if token not in punctuation])
        # if line is empty end of file is reached
        if not line:
            break
    file.close()
# corpus_christi.append(sentences_this_file)

# Read files and create non-Christian subcorpus
corpus_non_christi = list()
files_corpus_non_christi = metadata_ph_nonchristian
for index, df_line in files_corpus_non_christi.iterrows():
    sign = "+"
    if df_line['date'] < 0:
        sign = "-"
    file_name = df_line['file'] 
    file = open(os.path.join(lemmatized_texts_dir, file_name), 'r')
    # sentences_this_file = list()
    while True:
        line = file.readline().strip()
        if line != "":
            corpus_non_christi.append([token.lower() for token in line.split(" ") if token not in punctuation])
        # if line is empty end of file is reached
        if not line:
            break
    file.close()
#


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

# # Extract embeddings for Christian subcorpus and save
# print("Producing embeddings for the Christian subcorpus...")
# berts_finetuned_christian = calculate_embeddings(corpus_christi, latin_bert_finetuned, "berts_finetuned_christian.h5")
# print("Embeddings for the Christian subcorpus completed.\n")

# # Extract embeddings for non-Christian subcorpus and save
# print("Producing embeddings for the non-Christian subcorpus...")
# berts_finetuned_non_christian = calculate_embeddings(corpus_non_christi, latin_bert_finetuned, "berts_finetuned_non_christian.h5")
# print("Embeddings for the non-Christian subcorpus completed.\n")