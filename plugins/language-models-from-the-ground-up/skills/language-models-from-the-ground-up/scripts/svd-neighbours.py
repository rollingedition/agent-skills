"""Compresses the PPMI matrix into 64 numbers per token, and lists the four nearest neighbours of six tokens. The prose's
point rests on the first two lists and the last line: patio and outdoor are each other's nearest neighbour, at the cosine printed last."""
from lib.vectors import DIMENSIONS, nearest, svd_vectors          # svd_vectors does the PPMI and SVD steps; nearest ranks tokens by cosine similarity

vectors, vocabulary = svd_vectors()                               # one 64-number row per token, each scaled to unit length
index = {token: i for i, token in enumerate(vocabulary)}

print("dimensions per token:", DIMENSIONS)
for token in ["patio</w>", "outdoor</w>", "sofa</w>", "oak</w>", "blue</w>", "48</w>"]:     # </w> marks a word's last token
    neighbours = nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))   # skip leaves out the token itself, which would otherwise be its own nearest at 1.00
    print(f"{token:<12} -> " + ", ".join(f"{t} {s:.2f}" for t, s in neighbours))
print("cosine(patio, outdoor):", f"{float(vectors[index['patio</w>']] @ vectors[index['outdoor</w>']]):.2f}")   # unit-length vectors, so the dot product is the cosine
