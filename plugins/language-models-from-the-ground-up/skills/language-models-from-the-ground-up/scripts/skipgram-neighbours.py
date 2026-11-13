"""Reads the skip-gram vectors and training losses that recordings/skipgram.py saved, and lists the same six tokens' four
nearest neighbours as the SVD example. The prose's point rests on the two loss lines and on outdoor's nearest neighbour."""
import json

import numpy as np

from lib.vectors import nearest

recorded = "data/recorded/skipgram/"                 # saved by recordings/skipgram.py, which trains once: its values depend on the machine
vectors = np.load(recorded + "vectors.npy")
vocabulary = json.load(open(recorded + "vocabulary.json", encoding="utf-8"))
losses = np.load(recorded + "losses.npy")            # one loss per batch, in training order
index = {token: i for i, token in enumerate(vocabulary)}

print("training loss, first batch:", f"{losses[0]:.2f}")                        # index 0: the first batch, when nothing has been learned yet
print("training loss, last 100 batches:", f"{losses[-100:].mean():.2f}")
for token in ["patio</w>", "outdoor</w>", "sofa</w>", "oak</w>", "blue</w>", "48</w>"]:
    neighbours = nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))   # skip leaves out the token itself
    print(f"{token:<12} -> " + ", ".join(f"{t} {s:.2f}" for t, s in neighbours))
