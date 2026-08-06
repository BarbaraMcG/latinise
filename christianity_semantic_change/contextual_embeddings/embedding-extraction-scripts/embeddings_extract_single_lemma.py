# Packages
import os 
import time
import unicodedata
from contextlib import ExitStack
from collections import defaultdict
from typing import Any, Iterable, cast

import h5py
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm

# Define paths for local testing
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
dir_in = os.path.join(BASE_DIR, "contextual_embeddings")
dir_out = os.path.join(dir_in, "output", "single_word_embeddings_finetuned")  
metadata_file = os.path.join(BASE_DIR, "data", "latinise_metadata_2026_with_predictions.csv")  
texts_dir = os.path.join(BASE_DIR, "data", "non_lemmatized_texts")  
latin_bert_finetuned = os.path.join(dir_in, "latin-bert-finetuned")
latin_bert_pretrained = "latincy/latin-bert"

# Define paths for HPC
# dir_in = os.getcwd()
# dir_out = os.path.join(dir_in, "output", "embeddings_finetuned") 
# metadata_file = os.path.join(dir_in, 'latinise_metadata_2026_with_predictions.csv')  
# texts_dir = os.path.join(dir_in, "non_lemmatized_texts")
# latin_bert_finetuned = os.path.join(dir_in, "output", "fine_tuned_latinbert")

TARGET_LEMMAS = {
    "altare", # newly coined?
    "ara",
    "basilica",
    "beatus",
    "caritas",
    "caro",
    "codex",
    "communico",
    "communio",
    "confessio",
    "confiteor",
    "conuersio",
    "conuerto",
    "credo",
    "cultus",
    "culpa",
    "deus",
    "disciplina",
    "dominus",
    "fidelis",
    "fides",
    "gentilis",
    "gens",
    "gloria",
    "gratia",
    "lectio",
    "lex",
    "lux",
    "lumen",
    "mors",
    "mundus",
    "mysterium",
    "oratio",
    "ordo",
    "paenitentia",
    "paganus",
    "peccatum",
    "pontifex",
    "regula",
    "religio",
    "sacramentum",
    "salus",
    "saluo", # newly coined?
    "saeculum",
    "sanctus",
    "scriptura",
    "spiritus",
    "tenebra",
    "tenebrae",
    "templum",
    "testamentum",
    "uita",
    "uirtus",
}
# # Potential additions to the above list
# missing_from_second = [
#     "creator",
#     "factor",
#     "deductor",
#     "altarium",
#     "tabernaculum",
#     "memoria",
#     "recessus",
#     "frater",
#     "soror",
#     "canticum",
#     "panis",
#     "anima",
# ]

# Ensure output directory exists
os.makedirs(dir_out, exist_ok=True)


def normalize_lemma(token: str) -> str:
    """Lowercase, strip diacritics/punctuation, and fold v→u for Latin lemmas."""
    if token is None:
        return ""
    normalized = unicodedata.normalize("NFKD", token)
    normalized = "".join(ch for ch in normalized if ch.isalpha())
    normalized = normalized.lower()
    normalized = normalized.replace("v", "u")
    return normalized


def assign_time_slice(date_range_end: int) -> str:
    return "pre_180" if date_range_end < 180 else "post_180"

# Function to build corpus texts from metadata and text files
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
            text = " ".join(parts)
            metadata_dict = row.to_dict()
            corpus_texts.append({
                "text": text,
                "metadata": metadata_dict
            })

    return corpus_texts

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


# # Optional debug limit
# metadata_ph = metadata_ph.sample(n=20, random_state=42).reset_index(drop=True)

# Build full corpus texts
print("Creating the corpus...")
corpus_texts = build_corpus_texts(metadata_ph, texts_dir)

def safe_attr_value(value):
    """
    Convert values to HDF5-storable attribute values.
    """
    if pd.isna(value):
        return "NA"
    return str(value)


def build_sentence_records(doc, max_sent_chars=500):
    """Return sentence spans and text for a spaCy doc.

    If spaCy produces a sentence longer than max_sent_chars (e.g. when the
    parser finds no boundaries in a verse-formatted text like the Vulgate),
    the span is split on newlines as a fallback, giving one record per line.
    """
    try:
        sentences = list(doc.sents)
    except ValueError:
        sentences = [doc[:]]

    if not sentences:
        sentences = [doc[:]]

    records = []
    for sentence in sentences:
        text = sentence.text
        start = int(sentence.start_char)
        if len(text) <= max_sent_chars:
            records.append(
                {
                    "sentence_index": len(records),
                    "start": start,
                    "end": int(sentence.end_char),
                    "text": text.strip(),
                }
            )
        else:
            # Fallback: split on newlines (handles verse-per-line Bible texts etc.)
            offset = 0
            for line in text.split("\n"):
                stripped = line.strip()
                if stripped:
                    records.append(
                        {
                            "sentence_index": len(records),
                            "start": start + offset,
                            "end": start + offset + len(line),
                            "text": stripped,
                        }
                    )
                offset += len(line) + 1  # +1 for the newline character
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

def calculate_embeddings_latincy_lemma_match(
    corpus_texts,
    model_name,
    output_filename,
    batch_size=8,
    max_length=256,
    target_terms=None,
    latincy_model="la_core_web_lg",
    split_by_target=False,
    checkpoint_every=20,
):
    """
    Extract contextual embeddings, but filter/group by LatinCy lemmas so nominative
    targets (e.g., 'deus') capture inflected forms (dei, deum, deo, ...).

    Notes:
    - Keeps your current transformer input behavior (surface text, chunking, offsets).
    - Adds LatinCy-based lemma lookup per matched word span.
    - Writes the same HDF5 structure plus lemma fields from LatinCy.
    """
    import json
    import spacy
    from collections import defaultdict
    import os
    import time

    import h5py
    import pandas as pd
    import torch
    from tqdm import tqdm
    from transformers import AutoModel, AutoTokenizer

    output_path = os.path.join(dir_out, output_filename)
    if not output_path.endswith(".h5"):
        output_path += ".h5"
    output_stem = output_path[:-3]

    normalized_targets = None
    if target_terms:
        normalized_targets = {normalize_lemma(term) for term in target_terms}

    if split_by_target and not normalized_targets:
        raise ValueError("split_by_target=True requires non-empty target_terms.")

    target_output_paths = {}
    if split_by_target:
        assert normalized_targets is not None
        for lemma in sorted(normalized_targets):
            target_output_paths[lemma] = f"{output_stem}_{lemma}.h5"

    # Checkpoint: track the last fully flushed batch so we can resume
    checkpoint_path = f"{output_stem}_checkpoint.json"
    resume_from_batch = 0
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, "r") as _cp:
                _cp_data = json.load(_cp)
            resume_from_batch = int(_cp_data.get("last_flushed_batch", 0))
            print(f"Resuming from batch {resume_from_batch} (checkpoint found at {checkpoint_path})")
        except Exception:
            resume_from_batch = 0

    tokenizer = AutoTokenizer.from_pretrained("latincy/latin-bert", trust_remote_code=True)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    latincy_nlp = spacy.load(latincy_model)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    print(f"Processing {len(corpus_texts)} texts for {output_filename}...")
    start_time = time.time()

    chunk_counters = defaultdict(int)
    text_annotations_cache = {}

    def build_text_annotations(text, chunk_char_limit=200000):
        """Annotate text with LatinCy in chunks to respect spaCy max_length."""
        if not text:
            return {"token_records": [], "sentence_records": []}

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

    with ExitStack() as stack:
        if split_by_target:
            target_h5_files = {
                lemma: stack.enter_context(h5py.File(path, "a"))
                for lemma, path in target_output_paths.items()
            }
            main_h5f = None
        else:
            target_h5_files = {}
            main_h5f = stack.enter_context(h5py.File(output_path, "a"))

        total_batches = max(1, (len(corpus_texts) + batch_size - 1) // batch_size)

        for batch_number, batch_start in enumerate(
            tqdm(range(0, len(corpus_texts), batch_size), desc="Processing text batches"),
            start=1,
        ):
            # Skip batches already completed in a previous run
            if batch_number <= resume_from_batch:
                continue
            batch_records = corpus_texts[batch_start:batch_start + batch_size]

            annotation_candidates = []
            for local_idx, record in enumerate(batch_records):
                source_text_idx = batch_start + local_idx
                if source_text_idx not in text_annotations_cache:
                    annotation_candidates.append((source_text_idx, record["text"]))

            if annotation_candidates:
                for source_text_idx, text in tqdm(
                    annotation_candidates,
                    desc=f"LatinCy annotations {batch_number}/{total_batches}",
                    leave=False,
                ):
                    text_annotations_cache[source_text_idx] = build_text_annotations(text)

            batch_tokens = [
                [
                    token_record["surface"]
                    for token_record in text_annotations_cache[batch_start + idx]["token_records"]
                ]
                for idx, _ in enumerate(batch_records)
            ]

            print(
                f"Batch {batch_number}/{total_batches}: tokenizing {len(batch_tokens)} texts...",
                flush=True,
            )

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

            print(
                f"Batch {batch_number}/{total_batches}: running model on {len(overflow_to_sample_mapping)} chunks...",
                flush=True,
            )

            model_inputs = {k: v.to(device) for k, v in encodings.items()}

            with torch.no_grad():
                outputs = model(**model_inputs)

            last_hidden_state = outputs.last_hidden_state.cpu()

            del outputs
            del model_inputs

            for seq_idx in tqdm(
                range(last_hidden_state.size(0)),
                desc=f"Chunk embeddings {batch_number}/{total_batches}",
                leave=False,
            ):
                sample_idx = overflow_to_sample_mapping[seq_idx].item()
                record = batch_records[sample_idx]
                text_metadata = record["metadata"]
                source_text_idx = batch_start + sample_idx

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

                    if normalized_targets and lemma_norm not in normalized_targets:
                        continue

                    sentence_index = token_record["sentence_index"]
                    sentence_record = sentence_records[sentence_index] if 0 <= sentence_index < len(sentence_records) else find_sentence_record(sentence_records, start_char, end_char)

                    token_embeddings = sequence_embeddings[token_indices, :]
                    word_embedding = token_embeddings.mean(dim=0).numpy()

                    matches.append(
                        {
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
                        }
                    )

                if not matches:
                    continue

                if split_by_target:
                    grouped_matches = defaultdict(list)
                    for match in matches:
                        grouped_matches[match["normalized"]].append(match)
                    write_groups = grouped_matches.items()
                else:
                    write_groups = [(None, matches)]

                for target_lemma, target_matches in write_groups:
                    if split_by_target:
                        h5f = target_h5_files[target_lemma]
                    else:
                        assert main_h5f is not None
                        h5f = main_h5f

                    sentence_grouped_matches = defaultdict(list)
                    for match in target_matches:
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
                        if split_by_target:
                            grp.attrs["target_lemma"] = target_lemma

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

            # Flush all open H5 files and save checkpoint every N batches
            if batch_number % checkpoint_every == 0:
                if split_by_target:
                    for h5f_flush in target_h5_files.values():
                        h5f_flush.flush()
                else:
                    assert main_h5f is not None
                    main_h5f.flush()
                with open(checkpoint_path, "w") as _cp:
                    json.dump({"last_flushed_batch": batch_number}, _cp)
                print(f"  [checkpoint] Flushed after batch {batch_number}/{total_batches}", flush=True)

    # Clean up checkpoint — job completed successfully, so it must not persist
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    if split_by_target:
        print(f"Embeddings saved to {len(target_output_paths)} files in {dir_out}")
    else:
        print(f"Embeddings saved to {output_path}")
    print(f"Processing completed in {int(minutes)}m {seconds:.2f}s")

    if split_by_target:
        return target_output_paths
    return output_path


if __name__ == "__main__":
    # Extract embeddings using LatinCy lemma matching
    print("Producing embeddings for the full corpus...")
    berts_pretrained_full = calculate_embeddings_latincy_lemma_match(
        corpus_texts=corpus_texts,
        model_name=latin_bert_pretrained,
        output_filename="berts_pretrained_full_with_metadata",
        batch_size=8,
        max_length=256,
        target_terms=TARGET_LEMMAS,
        latincy_model="la_core_web_lg",
        split_by_target=True,
    )
    print("Embeddings for the full corpus completed.\n")