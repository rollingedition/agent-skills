import numpy as np

from lib.transformer import rope

rng = np.random.default_rng(2026)
size = 32                                                      # one head's query and key, as in the store's model
query, key = rng.normal(0, 1, size), rng.normal(0, 1, size)
positions = 20
rotated_q = rope(np.tile(query, (positions, 1)))              # the same query, rotated for each position 0 to 19
rotated_k = rope(np.tile(key, (positions, 1)))
kept = np.allclose(np.linalg.norm(rotated_q, axis=1), np.linalg.norm(query)) and \
    np.allclose(np.linalg.norm(rotated_k, axis=1), np.linalg.norm(key))
print("length kept by the rotation, for the query and the key:", bool(kept))
for i, j in [(2, 5), (12, 15), (2, 8)]:
    print(f"score with the key at {i} and the query at {j}:", f"{rotated_q[j] @ rotated_k[i] / np.sqrt(size):.3f}")
