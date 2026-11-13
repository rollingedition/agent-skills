import json

import numpy as np

from lib.vectors import nearest

recorded = "data/recorded/skipgram/"
vectors = np.load(recorded + "vectors.npy")
vocabulary = json.load(open(recorded + "vocabulary.json", encoding="utf-8"))
losses = np.load(recorded + "losses.npy")
index = {token: i for i, token in enumerate(vocabulary)}

print("training loss, first batch:", f"{losses[0]:.2f}")
print("training loss, last 100 batches:", f"{losses[-100:].mean():.2f}")
for token in ["patio</w>", "outdoor</w>", "sofa</w>", "oak</w>", "blue</w>", "48</w>"]:
    neighbours = nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))
    print(f"{token:<12} -> " + ", ".join(f"{t} {s:.2f}" for t, s in neighbours))
