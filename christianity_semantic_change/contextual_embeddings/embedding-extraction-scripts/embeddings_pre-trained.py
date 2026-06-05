# Packages
import os 
import unicodedata
from collections import defaultdict
from typing import Any, Iterable, cast
import pandas as pd
import torch
import h5py
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm
import time
import spacy


# Define paths for HPC
dir_in = os.getcwd()
dir_out = os.path.join(dir_in, "output", "embeddings_pretrained")  
metadata_file = os.path.join(dir_in, 'latinise_metadata_2026_with_predictions.csv')  
texts_dir = os.path.join(dir_in, "non_lemmatized_texts")  
latin_bert_pretrained = "latincy/latin-bert"
stopwords_path = os.path.join(dir_in, 'stopwords_latin2.txt')

# # Define paths for local testing
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# BASE_DIR = os.path.dirname(SCRIPT_DIR)
# dir_in = BASE_DIR
# dir_out = os.path.join(dir_in, "output", "embeddings_pretrained") 
# metadata_file = os.path.join(dir_in, "..", "data", 'latinise_metadata_2026_with_predictions.csv')  
# texts_dir = os.path.join(dir_in, "..", "data", "non_lemmatized_texts")
# stopwords_path = os.path.join(dir_in, "..", "data", "stopwords", "stopwords_latin2.txt")

# Ensure output directory exists
os.makedirs(dir_out, exist_ok=True)


def normalize_lemma(token: str) -> str:
    """Lowercase, strip diacritics/punctuation, and fold v→u for each lemma."""
    if token is None:
        return ""
    normalized = unicodedata.normalize("NFKD", token)
    normalized = "".join(ch for ch in normalized if ch.isalpha())
    normalized = normalized.lower()
    normalized = normalized.replace("v", "u")
    return normalized


def build_sentence_records(doc):
    """Return sentence spans and text for a spaCy doc."""
    try:
        sentences = list(doc.sents)
    except ValueError:
        sentences = [doc[:]]

    if not sentences:
        sentences = [doc[:]]

    records = []
    for sentence_idx, sentence in enumerate(sentences):
        records.append(
            {
                "sentence_index": sentence_idx,
                "start": int(sentence.start_char),
                "end": int(sentence.end_char),
                "text": sentence.text.strip(),
            }
        )
    return records


def find_sentence_record(sentence_records, start_char, end_char):
    """Find the sentence record that contains a character span."""
    for record in sentence_records:
        if record["start"] <= start_char and end_char <= record["end"]:
            return record

    for record in sentence_records:
        overlaps = start_char < record["end"] and end_char > record["start"]
        if overlaps:
            return record

    if sentence_records:
        return sentence_records[0]

    return {
        "sentence_index": 0,
        "start": 0,
        "end": 0,
        "text": "",
    }


def safe_attr_value(value):
    """Convert values to HDF5-storable attribute values."""
    if pd.isna(value):
        return "NA"
    return str(value)


def annotate_text_with_latincy(text, latincy_nlp, chunk_char_limit=200000):
    """Annotate text with LatinCy in chunks to avoid spaCy max_length errors."""
    if not text:
        return {"token_records": [], "sentence_records": []}

    if chunk_char_limit <= 0:
        raise ValueError("chunk_char_limit must be positive")

    token_records = []
    sentence_records = []
    sentence_counter = 0

    text_length = len(text)
    chunk_start = 0

    while chunk_start < text_length:
        chunk_end = min(chunk_start + chunk_char_limit, text_length)

        if chunk_end < text_length:
            split_at = text.rfind(" ", chunk_start, chunk_end)
            if split_at > chunk_start:
                chunk_end = split_at

        chunk_text = text[chunk_start:chunk_end]
        if not chunk_text:
            chunk_start = chunk_end + 1
            continue

        doc = latincy_nlp(chunk_text)
        local_sentence_records = build_sentence_records(doc)
        local_sentence_index_to_global = {}
        for local_record in local_sentence_records:
            global_sentence_index = sentence_counter
            sentence_records.append(
                {
                    "sentence_index": global_sentence_index,
                    "start": int(chunk_start + local_record["start"]),
                    "end": int(chunk_start + local_record["end"]),
                    "text": local_record["text"],
                }
            )
            local_sentence_index_to_global[local_record["sentence_index"]] = global_sentence_index
            sentence_counter += 1

        for tok in doc:
            if tok.is_space:
                continue

            start = int(chunk_start + tok.idx)
            end = int(start + len(tok.text))
            lemma_norm = normalize_lemma(tok.lemma_)

            local_sentence_record = find_sentence_record(local_sentence_records, tok.idx, tok.idx + len(tok.text))
            global_sentence_index = local_sentence_index_to_global.get(local_sentence_record["sentence_index"], 0)
            global_sentence_record = sentence_records[global_sentence_index] if sentence_records else {
                "sentence_index": 0,
                "start": 0,
                "end": 0,
                "text": "",
            }

            token_records.append(
                {
                    "surface": tok.text,
                    "normalized": lemma_norm,
                    "start": start,
                    "end": end,
                    "sentence_index": global_sentence_index,
                    "sentence_text": global_sentence_record["text"],
                    "sentence_start": global_sentence_record["start"],
                    "sentence_end": global_sentence_record["end"],
                    "sentence_relative_start": int(start - global_sentence_record["start"]),
                    "sentence_relative_end": int(end - global_sentence_record["start"]),
                }
            )

        chunk_start = chunk_end

    return {
        "token_records": token_records,
        "sentence_records": sentence_records,
    }


def is_bible_file(file_path):
    """Check if file is from the Bible corpus (data/bible_separate/no-lem or equivalent)."""
    basename = os.path.basename(file_path)
    return "bible_separate" in file_path or basename.startswith("lat_0382_IT-LAT0001")


def build_corpus_texts(metadata_subset, texts_dir):
    """Build corpus as list of dicts with text and metadata (no tokenization)."""
    corpus_texts = []

    for _, row in metadata_subset.iterrows():
        file_path = os.path.join(texts_dir, row["file"])

        parts = []
        # Auto-detect Bible files: only apply punctuation to Bible texts
        should_append_period = is_bible_file(file_path)
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                if should_append_period and line[-1] not in {".", "!", "?", ";", ":"}:
                    line = f"{line}."
                parts.append(line)

        if parts:
            text = " ".join(parts)
            metadata_dict = row.to_dict()
            corpus_texts.append({
                "text": text,
                "metadata": metadata_dict
            })

    return corpus_texts


def assign_time_slice(date_range_end: int) -> str:
    return "pre_180" if date_range_end < 180 else "post_180"


# Read selected metadata 
metadata_df = pd.read_csv(metadata_file, sep=",")
metadata_df['date_range_end'] = pd.to_numeric(metadata_df['date_range_end'], errors="coerce")
metadata_df = metadata_df.dropna(subset=['date_range_end'])
metadata_df['date_range_end'] = metadata_df['date_range_end'].astype(int)

metadata_ph = metadata_df[
    (metadata_df['date_range_end'] > -300) & 
    (metadata_df['date_range_end'] <= 605)
    ].copy()
metadata_ph["time_slice"] = metadata_ph["date_range_end"].apply(assign_time_slice)

# Prepare time corpora as structured text records
print("Creating the corpora...")
time2corpus = {}

for time_slice in ["pre_180", "post_180"]:
    files_corpus_t = metadata_ph[metadata_ph["time_slice"] == time_slice]
    corpus_t = build_corpus_texts(files_corpus_t, texts_dir)
    time2corpus[time_slice] = corpus_t

# # Build full corpus
# corpus_texts = build_corpus_texts(metadata_ph, texts_dir)

# # For testing: sample a small subset
# corpus_texts = corpus_texts[:20]  # Use only first 20 texts for testing

# Load stopwords
stopwords = set()
if os.path.exists(stopwords_path):
    with open(stopwords_path, "r", encoding="utf-8") as f:
        stopwords = {line.strip().lower() for line in f if line.strip()}
else:
    print(f"Warning: Stopwords file not found at {stopwords_path}")


# Define function to extract embeddings with metadata and frequency/stopword filtering
def calculate_embeddings(
    corpus_texts,
    model_name,
    output_filename,
    batch_size=8,
    max_length=256,
    min_frequency=10,
    stopwords=None,
):
    """
    Extract contextual embeddings from corpus with metadata preservation.
    
    Filters out:
    - Stopwords
    - Words appearing < min_frequency times
    
    Args:
        corpus_texts: list of dicts with "text" and "metadata" keys
        model_name: path/name of Hugging Face model
        output_filename: basename for HDF5 file
        batch_size: texts per batch
        max_length: tokenizer max length
        min_frequency: minimum occurrences for a word to be saved
        stopwords: set of stopwords to exclude
    """
    
    output_path = os.path.join(dir_out, output_filename)
    if not output_path.endswith('.h5'):
        output_path += '.h5'
    
    if stopwords is None:
        stopwords = set()
    
    # Load tokenizer from original HF model and model from fine-tuned path
    tokenizer = AutoTokenizer.from_pretrained("latincy/latin-bert", trust_remote_code=True)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    
    # Load LatinCy for lemmatization
    latincy_nlp = spacy.load("la_core_web_lg")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    print(f"Processing {len(corpus_texts)} texts for {output_filename}...")
    print(f"Filtering: min_frequency={min_frequency}, stopwords={len(stopwords)}")
    start_time = time.time()
    
    # First pass: count word frequencies
    print("Counting word frequencies...")
    word_counts = defaultdict(int)
    text_annotations_cache = {}
    
    for text_idx, record in enumerate(corpus_texts):
        text = record["text"]
        annotations = annotate_text_with_latincy(text, latincy_nlp)
        sentence_records = annotations["sentence_records"]
        token_records = annotations["token_records"]
        
        text_annotations_cache[text_idx] = {
            "token_records": token_records,
            "sentence_records": sentence_records,
        }
        
        # Count lemmas in this text
        for token_record in token_records:
            lemma_norm = token_record["normalized"]
            if lemma_norm and lemma_norm not in stopwords:
                word_counts[lemma_norm] += 1
    
    # Filter by frequency
    frequent_words = {lemma for lemma, count in word_counts.items() if count >= min_frequency}
    print(f"Words meeting frequency threshold: {len(frequent_words)} / {len(word_counts)}")
    
    # Second pass: extract and save embeddings
    print("Extracting embeddings...")
    chunk_counters = defaultdict(int)
    
    with h5py.File(output_path, 'w') as h5f:
        for batch_start in tqdm(range(0, len(corpus_texts), batch_size), desc="Processing batches"):
            batch_records = corpus_texts[batch_start:batch_start + batch_size]
            batch_tokens = [
                [token_record["surface"] for token_record in text_annotations_cache[batch_start + idx]["token_records"]]
                for idx, _ in enumerate(batch_records)
            ]
            
            encodings = tokenizer(
                batch_tokens,
                is_split_into_words=True,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
                return_overflowing_tokens=True,
            )
            
            overflow_to_sample_mapping = encodings.pop("overflow_to_sample_mapping")
            
            model_inputs = {k: v.to(device) for k, v in encodings.items()}
            
            with torch.no_grad():
                outputs = model(**model_inputs)
            
            last_hidden_state = outputs.last_hidden_state.cpu()
            
            for seq_idx in range(last_hidden_state.size(0)):
                sample_idx = overflow_to_sample_mapping[seq_idx].item()
                record = batch_records[sample_idx]
                text_metadata = record["metadata"]
                source_text_idx = batch_start + sample_idx
                
                # Get cached annotations
                token_records = text_annotations_cache[source_text_idx]["token_records"]
                sentence_records = text_annotations_cache[source_text_idx]["sentence_records"]
                
                chunk_idx = chunk_counters[source_text_idx]
                chunk_counters[source_text_idx] += 1
                
                sequence_embeddings = last_hidden_state[seq_idx]
                
                encoding = encodings.encodings[seq_idx]
                raw_word_ids = getattr(encoding, "word_ids", None)
                if callable(raw_word_ids):
                    word_ids = raw_word_ids()
                else:
                    word_ids = raw_word_ids

                if word_ids is None:
                    try:
                        word_ids = encodings.word_ids(batch_index=seq_idx)
                    except TypeError:
                        word_ids = encodings.word_ids(seq_idx)

                if word_ids is None:
                    continue

                if not hasattr(word_ids, "__iter__"):
                    continue

                word_ids_list = list(cast(Iterable[Any], word_ids))
                
                word_to_token_indices = defaultdict(list)
                for tok_idx, word_id in enumerate(word_ids_list):
                    if word_id is None:
                        continue
                    word_to_token_indices[word_id].append(tok_idx)
                
                matches = []
                
                for token_indices in word_to_token_indices.values():
                    word_id = word_ids_list[token_indices[0]]
                    if word_id is None or word_id >= len(token_records):
                        continue

                    token_record = token_records[word_id]
                    token_indices = sorted(token_indices)
                    surface_form = token_record["surface"]
                    lemma_norm = token_record["normalized"]
                    start_char = token_record["start"]
                    end_char = token_record["end"]
                    
                    # Filter by frequency and stopwords
                    if lemma_norm not in frequent_words:
                        continue
                    
                    # Get sentence info
                    sentence_index = token_record["sentence_index"]
                    sentence_record = sentence_records[sentence_index] if 0 <= sentence_index < len(sentence_records) else find_sentence_record(sentence_records, start_char, end_char)
                    
                    # Average subword embeddings
                    token_embeddings = sequence_embeddings[token_indices, :]
                    word_embedding = token_embeddings.mean(dim=0).numpy()
                    
                    matches.append({
                        "surface": surface_form,
                        "normalized": lemma_norm,
                        "start": int(start_char),
                        "end": int(end_char),
                        "chunk_index": chunk_idx,
                        "sentence_index": sentence_record["sentence_index"],
                        "sentence_text": sentence_record["text"],
                        "sentence_start": sentence_record["start"],
                        "sentence_end": sentence_record["end"],
                        "sentence_relative_start": int(start_char - sentence_record["start"]),
                        "sentence_relative_end": int(end_char - sentence_record["start"]),
                        "embedding": word_embedding,
                    })
                
                if not matches:
                    continue
                
                # Group by sentence
                sentence_grouped_matches = defaultdict(list)
                for match in matches:
                    sentence_grouped_matches[match["sentence_index"]].append(match)
                
                for sentence_index, sentence_matches in sentence_grouped_matches.items():
                    sentence_match = sentence_matches[0]
                    grp_name = f"text_{source_text_idx:05d}_sentence_{sentence_index:05d}"
                    grp = h5f.require_group(grp_name)
                    existing_words = int(grp.attrs.get("n_matched_words", 0))
                    
                    grp.attrs["source_text_index"] = source_text_idx
                    grp.attrs["sentence_index"] = sentence_index
                    grp.attrs["sentence_text"] = sentence_match["sentence_text"]
                    grp.attrs["sentence_char_start"] = sentence_match["sentence_start"]
                    grp.attrs["sentence_char_end"] = sentence_match["sentence_end"]
                    
                    for key, value in text_metadata.items():
                        grp.attrs[key] = safe_attr_value(value)
                    
                    for offset, match in enumerate(sentence_matches):
                        word_counter = existing_words + offset
                        ds_name = f"word_{word_counter:04d}_embedding"
                        grp.create_dataset(ds_name, data=match["embedding"], compression="gzip")
                        grp.attrs[f"word_{word_counter:04d}_surface"] = match["surface"]
                        grp.attrs[f"word_{word_counter:04d}_normalized"] = match["normalized"]
                        grp.attrs[f"word_{word_counter:04d}_char_start"] = match["start"]
                        grp.attrs[f"word_{word_counter:04d}_char_end"] = match["end"]
                        grp.attrs[f"word_{word_counter:04d}_chunk_index"] = match["chunk_index"]
                        grp.attrs[f"word_{word_counter:04d}_sentence_relative_start"] = match["sentence_relative_start"]
                        grp.attrs[f"word_{word_counter:04d}_sentence_relative_end"] = match["sentence_relative_end"]
                    
                    grp.attrs["n_matched_words"] = existing_words + len(sentence_matches)

            h5f.flush()

            del outputs
            del model_inputs
            del encodings
            del last_hidden_state
    
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Embeddings saved to {output_path}")
    print(f"Processing completed in {int(minutes)}m {seconds:.2f}s")
    
    return output_path



if __name__ == "__main__":
    # # Extract embeddings for pre-180 timeframe and save
    # print("Producing embeddings for pre-180 timeframe using pre-trained model...")
    # berts_pretrained_pre_180 = calculate_embeddings(
    #     time2corpus["pre_180"],
    #     latin_bert_pretrained,
    #     "berts_pretrained_pre_180.h5",
    #     stopwords=stopwords,
    # )
    # print("Embeddings for pre-180 timeframe using pre-trained model completed.\n")

    # Extract embeddings for post-180 timeframe and save
    print("Producing embeddings for post-180 timeframe using pre-trained model...")
    berts_pretrained_post_180 = calculate_embeddings(
        time2corpus["post_180"],
        latin_bert_pretrained,
        "berts_pretrained_post_180.h5",
        stopwords=stopwords,
    )
    print("Embeddings for post-180 timeframe using pre-trained model completed.\n")

    # # Extract embeddings for the 20-text sample and save
    # print("Producing embeddings for the 20-text sample using pre-trained model...")
    # berts_pretrained_sample_20 = calculate_embeddings(
    #     corpus_texts,
    #     latin_bert_pretrained,
    #     "berts_pretrained_sample_20.h5",
    #     stopwords=stopwords,
    # )
    # print("Embeddings for the 20-text sample using pre-trained model completed.\n")
