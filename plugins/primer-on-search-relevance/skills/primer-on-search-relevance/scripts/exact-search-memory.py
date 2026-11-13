"""Prints the bytes one product's float32 vector takes, and the memory the catalog's vectors use, for the store and for a million products. The prose's point rests on the MB line for the store's catalog and the GB line for a million products."""
from lib.recorded import embeddings

# Exact search keeps every product vector in memory, as 32-bit floats.
product_ids, product_vectors, _, _ = embeddings()
print(f"products: {len(product_ids):,}")
print(f"float32 bytes per product: {product_vectors[0].nbytes:,}")
# decimal MB and GB: a megabyte is a million bytes, a gigabyte a billion
print(f"product vectors in memory, MB: {product_vectors.nbytes / 1e6:.1f}")
print(f"the same for 1,000,000 products, GB: {1_000_000 * product_vectors[0].nbytes / 1e9:.1f}")
