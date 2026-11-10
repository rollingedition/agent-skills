import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from lib.recorded import embeddings
from lib.store import load_products

products = load_products()
product_ids, product_vectors, query_ids, query_vectors = embeddings()
query = query_vectors[list(query_ids).index(246)]           # clear shower curtain
best = int(np.argmax(product_vectors @ query))
product = product_vectors[best]
print("product:", products.at[product_ids[best], "name"])

# cosine = dot product / (length of q * length of d)
dot = query @ product
cosine = dot / (np.linalg.norm(query) * np.linalg.norm(product))
print(f"dot product: {dot:.3f}")
print(f"cosine by hand: {cosine:.3f}")
print(f"cosine from scikit-learn: {cosine_similarity([query], [product])[0, 0]:.3f}")

# Keep the first 256 numbers of each vector and don't rescale: the lengths are no longer 1.
short_products, short_queries = product_vectors[:, :256], query_vectors[:, :256]
lengths = np.linalg.norm(short_products, axis=1)
print(f"shortened product lengths: {lengths.min():.3f} to {lengths.max():.3f}")
by_dot = np.argsort(-(short_queries @ short_products.T), axis=1, kind="stable")[:, :10]
by_cosine = np.argsort(-(short_queries @ (short_products / lengths[:, None]).T), axis=1, kind="stable")[:, :10]
changed = sum(set(dot_top) != set(cosine_top) for dot_top, cosine_top in zip(by_dot, by_cosine))
print("queries:", len(query_ids))
print("queries whose top 10 changes:", changed)
