from typing import List, Dict, Any
from torch.utils.data import Dataset

# class LatinDataset(Dataset): 
#     def __init__(self, texts, tokenizer, max_length=256): 
#         self.texts = texts
#         self.tokenizer = tokenizer
#         self.max_length = max_length

#     def __len__(self): 
#         return len(self.texts)

#     def __getitem__(self, idx): 
#         text = self.texts[idx] 
#         tokens = self.tokenizer.tokenize(text) 
#         token_ids = self.tokenizer.convert_tokens_to_ids(tokens) 
#         # Truncate to max_length 
#         if len(token_ids) > self.max_length: 
#             token_ids = token_ids[:self.max_length] 
#         # Create attention mask 
#         attention_mask = [1] * len(token_ids) # 1 for real tokens 
#         padding_length = self.max_length - len(token_ids)
#         # Pad input_ids and attention_mask 
#         input_ids = token_ids + [0] * padding_length # 0 is the padding token ID 
#         attention_mask = attention_mask + [0] * padding_length # 0 for padding tokens 
#         return { 
#             "input_ids": torch.tensor(input_ids, dtype=torch.long), 
#             "attention_mask": torch.tensor(attention_mask, dtype=torch.long) 
#         }

class LatinDataset(Dataset):
    """
    HF-compatible dataset for masked language modeling.

    Key points:
    - DOES NOT pad or return tensors. Returns Python lists of input_ids.
    - Uses tokenizer overflow+stride to split long texts into chunks so you never
      exceed max_length (prevents 921>512 errors).
    - Leaves padding + attention_mask + labels creation to DataCollatorForLanguageModeling.
    """

    def __init__(
        self,
        texts: List[str],
        tokenizer,
        max_length: int = 256,
        stride: int = 128,
        add_special_tokens: bool = True,
    ):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = int(max_length)
        self.stride = int(stride)
        self.add_special_tokens = bool(add_special_tokens)

        if self.max_length <= 0:
            raise ValueError("max_length must be > 0")
        if self.stride < 0:
            raise ValueError("stride must be >= 0")
        if self.stride >= self.max_length:
            raise ValueError("stride must be smaller than max_length")

        self.examples: List[Dict[str, Any]] = []
        self.example_to_text_index: List[int] = []
        self.example_chunk_index: List[int] = []
        self._build_examples()

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.examples[idx]

    def _build_examples(self) -> None:
        for text_idx, text in enumerate(self.texts):
            text = (text or "").strip()
            if not text:
                continue

            enc = self.tokenizer(
                text,
                add_special_tokens=self.add_special_tokens,
                truncation=True,
                max_length=self.max_length,
                stride=self.stride,
                return_overflowing_tokens=True,
                padding=False,
                return_attention_mask=False,
                return_special_tokens_mask=False,
            )

            input_ids = enc.get("input_ids", [])
            if not input_ids:
                continue

            # If only one chunk returned, HF sometimes gives a flat list
            if isinstance(input_ids[0], int):
                self.examples.append({"input_ids": input_ids})
                self.example_to_text_index.append(text_idx)
                self.example_chunk_index.append(0)
                continue

            for chunk_pos, ids in enumerate(input_ids):
                if ids:
                    self.examples.append({"input_ids": ids})
                    self.example_to_text_index.append(text_idx)
                    self.example_chunk_index.append(chunk_pos)