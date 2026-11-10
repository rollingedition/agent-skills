from lib.recorded import embeddings

# Exact search keeps every product vector in memory, as 32-bit floats.
product_ids, product_vectors, _, _ = embeddings()
print(f"products: {len(product_ids):,}")
print(f"float32 bytes per product: {product_vectors[0].nbytes:,}")
print(f"product vectors in memory, MB: {product_vectors.nbytes / 1e6:.1f}")
print(f"the same for 1,000,000 products, GB: {1_000_000 * product_vectors[0].nbytes / 1e9:.1f}")
