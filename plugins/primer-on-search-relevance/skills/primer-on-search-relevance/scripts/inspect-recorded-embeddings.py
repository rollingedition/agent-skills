"""Loads the recorded vectors and shows the lengths lib.recorded stores and rescales, and how close two shopper queries are. The prose's point about rounding rests on the stored- and rescaled-length lines, and its point about nearby queries on the median and nearest-query lines."""
import re

import numpy as np

from lib.recorded import RECORDED, embeddings, manifest
from lib.store import load_queries

# unit-length rows, one per ID; the queries carry the model's query prefix
product_ids, product_vectors, query_ids, query_vectors = embeddings()
recording = manifest("embeddings")
print("embedding model:", recording["model"])
print("query prompt:", recording["prompts"]["query"])
print(f"products embedded: {len(product_ids):,}")
print("dimensions:", product_vectors.shape[1])
print("stored as:", recording["dtype"])
print("longest product text, tokens:", recording["longest_product_tokens"])
print("model's input limit, tokens:", recording["max_seq_length"])
# row 0 is product 1; [0, :4] takes its first four numbers
print(f"product {product_ids[0]}, first four numbers:", ", ".join(f"{x:.3f}" for x in product_vectors[0, :4]))
stored = np.load(RECORDED / "embeddings" / "products.npy").astype(np.float32)   # as saved, before lib.recorded
stored_lengths, lengths = np.linalg.norm(stored, axis=1), np.linalg.norm(product_vectors, axis=1)
print(f"stored vector lengths: {stored_lengths.min():.5f} to {stored_lengths.max():.5f}")
print(f"lengths after lib.recorded rescales: {lengths.min():.5f} to {lengths.max():.5f}")

# How close are two shopper queries? Compare every query with every other one.
queries = load_queries().loc[query_ids, "query"].tolist()
similarity = query_vectors @ query_vectors.T  # unit length, so the dot product is the cosine
np.fill_diagonal(similarity, np.nan)               # leave out each query's similarity to itself
print(f"median similarity of two queries: {np.nanmedian(similarity):.3f}")
for query in ["whimsical solar lights", "wall design shelf"]:
    row = queries.index(query)
    nearest = int(np.nanargmax(similarity[row]))
    # whole words as typed, with no stemming, so `lights` and `light` differ
    shared = set(re.findall(r"\w+", query)) & set(re.findall(r"\w+", queries[nearest]))
    print()
    print(f"{query}, nearest other query:", queries[nearest])
    print(f"{query}, similarity: {similarity[row, nearest]:.3f}")
    print(f"{query}, words in common:", len(shared))
