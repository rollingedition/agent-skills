"""Three analogies on the skip-gram vectors, each answered by the tokens nearest b minus a plus c; whether lamps and light
have vectors at all; and the nearest tokens to a few single words. The prose rests on the three analogy lines, the lamps line and the neighbour lists."""
import json

import numpy as np

from lib.vectors import nearest

vectors = np.load("data/recorded/skipgram/vectors.npy")               # saved by recordings/skipgram.py, which trains once
vocabulary = json.load(open("data/recorded/skipgram/vocabulary.json", encoding="utf-8"))
index = {token: i for i, token in enumerate(vocabulary)}

for a, b, c in [("chair", "chairs", "table"), ("chair", "chairs", "lamp"), ("black", "white", "dark")]:   # each reads: a is to b as c is to what
    a, b, c = (word + "</w>" for word in (a, b, c))       # the tokenizer marks each word's last token with </w>, so words are looked up in that form
    query = vectors[index[b]] - vectors[index[a]] + vectors[index[c]]   # b - a + c: "c, changed the way a became b"
    answers = nearest(vectors, vocabulary, query, k=3, skip=(a, b, c))  # the words in the question can't be their own answer
    print(f"{a} : {b} :: {c} : ? -> " + ", ".join(t for t, _ in answers))
print("lamps in the vocabulary:", "lamps</w>" in index)
print("light in the vocabulary:", "light</w>" in index)
for token in ["light</w>", "dark</w>", "small</w>"]:
    print(f"{token:<12} -> " + ", ".join(t for t, _ in nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))))
