from collections import Counter

from lib import bpe
from lib.store import load_products, words

train = load_products("train")
word_counts = Counter(w for text in train["name"] + " " + train["description"] for w in words(text))
tokenizer = bpe.Tokenizer(bpe.train(word_counts, merges=4000), bpe.alphabet(word_counts))   # the training split's text

print("different words in training text:", f"{len(word_counts):,}")
print("characters and the end marker:", len(bpe.alphabet(word_counts)))
print("tokens in the vocabulary:", f"{len(tokenizer.vocabulary):,}")
for name in ["set of 2 barstools", "sled coffee table", "chair chairs", "48 49", "noise noise-free"]:
    print(name, "->", " ".join(tokenizer.encode(name)))
