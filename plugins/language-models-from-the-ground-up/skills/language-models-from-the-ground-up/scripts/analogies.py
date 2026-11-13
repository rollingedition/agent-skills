import json

import numpy as np

from lib.vectors import nearest

vectors = np.load("data/recorded/skipgram/vectors.npy")
vocabulary = json.load(open("data/recorded/skipgram/vocabulary.json", encoding="utf-8"))
index = {token: i for i, token in enumerate(vocabulary)}

for a, b, c in [("chair", "chairs", "table"), ("chair", "chairs", "lamp"), ("black", "white", "dark")]:
    a, b, c = (word + "</w>" for word in (a, b, c))
    query = vectors[index[b]] - vectors[index[a]] + vectors[index[c]]   # b - a + c: "c, changed the way a became b"
    answers = nearest(vectors, vocabulary, query, k=3, skip=(a, b, c))
    print(f"{a} : {b} :: {c} : ? -> " + ", ".join(t for t, _ in answers))
print("lamps in the vocabulary:", "lamps</w>" in index)
print("light in the vocabulary:", "light</w>" in index)
for token in ["light</w>", "dark</w>", "small</w>"]:
    print(f"{token:<12} -> " + ", ".join(t for t, _ in nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))))
