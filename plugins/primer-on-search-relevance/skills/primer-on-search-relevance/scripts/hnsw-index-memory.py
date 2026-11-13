"""Counts the links per product in the HNSW graph, and the bytes per product of the exact and the HNSW index. The prose's point rests on the two bytes-per-product lines, set against faiss's estimate."""
import faiss

from lib.recorded import embeddings
from lib.vectors import hnsw_index

product_ids, product_vectors, _, _ = embeddings()
dimensions = product_vectors.shape[1]
flat = faiss.IndexFlatIP(dimensions)                    # exact search: the vectors only
flat.add(product_vectors)
index = hnsw_index(product_vectors, links=32)           # the vectors, plus the graph's links

# layer 0 is the bottom layer: 2 × M links there, and M on each upper layer
print("links per product, upper layers:", index.hnsw.nb_neighbors(1))
print("links per product, bottom layer:", index.hnsw.nb_neighbors(0))
# 8M with M = 32: 4 bytes for each of the 2M bottom-layer links
print(f"faiss's estimate, 4d + 8M bytes per product: {4 * dimensions + 8 * 32:,}")
# the saved index's size, spread over the products
for name, built in [("exact index", flat), ("hnsw index", index)]:
    print(f"bytes per product, {name}: {faiss.serialize_index(built).nbytes / len(product_ids):,.0f}")
