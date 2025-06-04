import torch
from torch.utils.data import Dataset

class LatinDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=256):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        tokens = self.tokenizer.tokenize(text)
        token_ids = self.tokenizer.convert_tokens_to_ids(tokens)

        # Truncate to max_length
        if len(token_ids) > self.max_length:
            token_ids = token_ids[:self.max_length]

        # Create attention mask
        attention_mask = [1] * len(token_ids)  # 1 for real tokens
        padding_length = self.max_length - len(token_ids)

        # Pad input_ids and attention_mask
        input_ids = token_ids + [0] * padding_length  # 0 is the padding token ID
        attention_mask = attention_mask + [0] * padding_length  # 0 for padding tokens

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long)
        }