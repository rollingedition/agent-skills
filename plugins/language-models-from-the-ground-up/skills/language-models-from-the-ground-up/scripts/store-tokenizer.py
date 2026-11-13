"""Learns 4,000 merges from the training names and descriptions, then encodes five short texts with the resulting
tokenizer. Read the vocabulary size and the tokens of each text, which the prose cites."""
from collections import Counter

from lib import bpe
from lib.store import load_products, words

train = load_products("train")
word_counts = Counter(w for text in train["name"] + " " + train["description"] for w in words(text))   # names and descriptions, read as one text
tokenizer = bpe.Tokenizer(bpe.train(word_counts, merges=4000), bpe.alphabet(word_counts))   # the merges, then the characters they start from

print("different words in training text:", f"{len(word_counts):,}")
print("characters and the end marker:", len(bpe.alphabet(word_counts)))
print("tokens in the vocabulary:", f"{len(tokenizer.vocabulary):,}")
# an unseen word, a word and its plural, digits, and a hyphenated word, in that order
for name in ["set of 2 barstools", "sled coffee table", "chair chairs", "48 49", "noise noise-free"]:
    print(name, "->", " ".join(tokenizer.encode(name)))
