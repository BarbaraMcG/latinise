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

# Prepare Christian subcorpus: IT
tertullian = ['LAT0058', 'LAT0062','LAT0246', 'LAT0248', 'LAT0256', 'LAT0350', 'LAT0448', 'LAT0606', 'LAT0733', 'LAT0736', 'LAT0737', 'LAT0744', 'LAT0746', 'LAT0747', 'LAT0749', 'LAT0750', 'LAT0755', 'LAT0788']
novatian = ['LAT0865']
minucius_felix = ['LAT0267']
arnobius = ['LAT0264']
lactantius = ['LAT0268']
commodian = ['LAT0607']
egeria = ['LAT0719']
auctor_incertus_1 = ['LAT0471', 'LAT0203']
early_selected_texts = tertullian + novatian + minucius_felix + arnobius + lactantius + commodian + egeria + auctor_incertus_1
jerome1 = ['LAT0001', 'LAT0001_1', 'LAT0001_2', 'LAT0001_3', 'LAT0001_4', 'LAT0001_5', 'LAT0001_6', 'LAT0001_7', 'LAT0001_8', 'LAT0001_9', 'LAT0001_10', 'LAT0001_11', 'LAT0001_12', 'LAT0001_13', 'LAT0001_14', 'LAT0001_15', 'LAT0001_16', 'LAT0001_17', 'LAT0001_18', 'LAT0001_19', 'LAT0001_20', 'LAT0001_21', 'LAT0001_22', 'LAT0001_23', 'LAT0001_24', 'LAT0001_25', 'LAT0001_26', 'LAT0001_27', 'LAT0001_28', 'LAT0001_29', 'LAT0001_30', 'LAT0001_31', 'LAT0001_32', 'LAT0001_33', 'LAT0001_34', 'LAT0001_35']
jerome2 = ['LAT0001_36', 'LAT0001_37', 'LAT0001_38', 'LAT0001_39', 'LAT0001_40', 'LAT0001_41', 'LAT0001_42', 'LAT0001_43', 'LAT0001_44', 'LAT0001_45', 'LAT0001_46', 'LAT0001_47', 'LAT0001_48', 'LAT0001_49', 'LAT0001_50', 'LAT0001_51', 'LAT0001_52', 'LAT0001_53', 'LAT0001_54', 'LAT0001_55', 'LAT0001_56', 'LAT0001_57', 'LAT0001_58', 'LAT0001_59', 'LAT0001_60', 'LAT0001_61', 'LAT0001_62', 'LAT0001_63', 'LAT0001_64', 'LAT0001_65', 'LAT0001_66', 'LAT0001_67', 'LAT0001_68', 'LAT0001_69', 'LAT1039', 'LAT0726', 'LAT0843', 'LAT0878', 'LAT0880']
augustine = ['LAT0061', 'LAT0793', 'LAT0016', 'LAT0015', 'LAT0397', 'LAT0403', 'LAT0768']
ambrose = ['LAT0263', 'LAT0847']
paulinus_nola = ['LAT0609']
sulpicius_severus = ['LAT0612', 'LAT0410']
apophthegmata = ['LAT0978']
hydatius = ['LAT0775', 'LAT0776']
macarius_alex = ['LAT1004']
prudentius = ['LAT0270']
prosper_aquit = ['LAT0610']
sedulius = ['LAT0414']
eucherius_lyon = ['LAT0608']
vincent_lerins = ['LAT0904']
# boethius = ['LAT0917']
benedict_nursia = ['LAT0011']
cassiodorus = ['LAT0250', 'LAT0251', 'LAT0252', 'LAT0243', 'LAT0482']
thomas_edessa = ['LAT0875']
marcellinus_comes = ['LAT0791']
gregory_tours = ['LAT0783']
martin_braga = ['LAT0990', 'LAT0990_1', 'LAT0990_2', 'LAT0990_3', 'LAT0990_4', 'LAT0990_5', 'LAT0990_6', 'LAT0990_7', 'LAT0990_8', 'LAT0990_9']
isidore_seville = ['LAT0908', 'LAT0909', 'LAT0957']
auctor_incertus_2 = ['LAT0383']
late_selected_texts = jerome1 + jerome2 + augustine + ambrose + paulinus_nola + sulpicius_severus + apophthegmata + hydatius + macarius_alex + prudentius + prosper_aquit + sedulius + eucherius_lyon + vincent_lerins + benedict_nursia + cassiodorus + thomas_edessa + marcellinus_comes + gregory_tours + martin_braga + isidore_seville + auctor_incertus_2 # + boethius
selected_texts_1 = early_selected_texts + late_selected_texts
selected_texts_1 = ['IT-'+f for f in selected_texts_1]

# Prepare Christian subcorpus: MQDQ
commodian = ['MQDQ-39', 'MQDQ-40', 'MQDQ-41']
tertullian = ['MQDQ-491', 'MQDQ-492']
lactantius = ['MQDQ-157', 'MQDQ-158', 'MQDQ-159']
laudes_dom = ['MQDQ-1']
iuvencus = ['MQDQ-151']
proba = ['MQDQ-350']
marius_vic = ['MQDQ-617']
hilarius_pic = ['MQDQ-117', 'MQDQ-118', 'MQDQ-119', 'MQDQ-120']
ambrose = ['MQDQ-179', 'MQDQ-180', 'MQDQ-181', 'MQDQ-182', 'MQDQ-183']
damasus = ['MQDQ-56']
prudentius = ['MQDQ-366', 'MQDQ-367', 'MQDQ-368', 'MQDQ-369', 'MQDQ-371', 'MQDQ-372', 'MQDQ-373', 'MQDQ-374', 'MQDQ-375']
augustine = ['MQDQ-512', 'MQDQ-513', 'MQDQ-514', 'MQDQ-515', 'MQDQ-516']
paulinus_nol = ['MQDQ-279', 'MQDQ-280', 'MQDQ-281', 'MQDQ-282']
pseud_cyp = ['MQDQ-379', 'MQDQ-380', 'MQDQ-381', 'MQDQ-382', 'MQDQ-383']
paulinus_pel = ['MQDQ-283', 'MQDQ-284']
agrestius_gal = ['MQDQ-66']
auspicius_tul = ['MQDQ-608']
carmen_sib = ['MQDQ-5']
cyprian_gal = ['MQDQ-48', 'MQDQ-49', 'MQDQ-50', 'MQDQ-51', 'MQDQ-52', 'MQDQ-53', 'MQDQ-54', 'MQDQ-55']
dracontius = ['MQDQ-59', 'MQDQ-60']
paulinus_bae = ['MQDQ-278']
orientius = ['MQDQ-242', 'MQDQ-243']
paulinus_pet = ['MQDQ-285', 'MQDQ-286', 'MQDQ-287']
prosper_aqu = ['MQDQ-360', 'MQDQ-361', 'MQDQ-362', 'MQDQ-363', 'MQDQ-364', 'MQDQ-365']
sedulius = ['MQDQ-422', 'MQDQ-423']
victorinus = ['MQDQ-564', 'MQDQ-565', 'MQDQ-566']
marius_vic = ['MQDQ-189']
sidonius = ['MQDQ-444', 'MQDQ-445']
ruricius_lem = ['MQDQ-111']
anonymous = ['MQDQ-140']
parthenius_afr = ['MQDQ-277']
alcimus_avi = ['MQDQ-622', 'MQDQ-623']
cyprianus_tol = ['MQDQ-621']
remigius_rem = ['MQDQ-618']
gildas = ['MQDQ-574', 'MQDQ-575']
# boethius = ['MQDQ-627', 'MQDQ-628']
ennodius = ['MQDQ-75', 'MQDQ-76', 'MQDQ-77', 'MQDQ-78', 'MQDQ-79', 'MQDQ-80', 'MQDQ-81', 'MQDQ-82', 'MQDQ-83', 'MQDQ-84', 'MQDQ-85', 'MQDQ-86']
arator = ['MQDQ-351', 'MQDQ-352', 'MQDQ-353', 'MQDQ-354', 'MQDQ-355']
flavius_cab = ['MQDQ-95']
marcus_cas = ['MQDQ-244']
rusticius_hel = ['MQDQ-415', 'MQDQ-416']
severus_mal = ['MQDQ-191']
columba = ['MQDQ-619']
columbanus = ['MQDQ-30', 'MQDQ-31', 'MQDQ-32', 'MQDQ-33', 'MQDQ-34', 'MQDQ-35']
martin_bra = ['MQDQ-209', 'MQDQ-210', 'MQDQ-211']
marius_ave = ['MQDQ-188']
isidore_sev = ['MQDQ-148']
selected_texts_2 = commodian + tertullian + lactantius + laudes_dom + iuvencus + proba + marius_vic + hilarius_pic + ambrose + damasus + prudentius + augustine + paulinus_nol + pseud_cyp + paulinus_pel + agrestius_gal + auspicius_tul + carmen_sib + cyprian_gal + dracontius + paulinus_bae + orientius + paulinus_pet + prosper_aqu + sedulius + victorinus + sidonius + ruricius_lem + anonymous + parthenius_afr + alcimus_avi + cyprianus_tol + remigius_rem + gildas + ennodius + arator + flavius_cab + marcus_cas + rusticius_hel + severus_mal + columba + columbanus + martin_bra + marius_ave + isidore_sev

# Merge IT and MQDQ Christian subcorpora
selected_texts = selected_texts_1 + selected_texts_2

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