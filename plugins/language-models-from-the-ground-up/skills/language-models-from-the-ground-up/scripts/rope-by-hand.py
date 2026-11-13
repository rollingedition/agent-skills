"""Rotates one random query and key for each of 20 positions, checks that the rotation keeps their lengths, and scores
three pairs of positions. The prose's point rests on the two scores for pairs 3 apart, which match, and the score for
the pair 6 apart, which doesn't."""
import numpy as np

from lib.transformer import rope

rng = np.random.default_rng(2026)                             # a fixed seed: the same random query and key on every run
size = 32                                                      # 32 numbers: the store's width of 128 split across 4 heads
query, key = rng.normal(0, 1, size), rng.normal(0, 1, size)
positions = 20
rotated_q = rope(np.tile(query, (positions, 1)))              # the same query, rotated for each position 0 to 19
rotated_k = rope(np.tile(key, (positions, 1)))
kept = np.allclose(np.linalg.norm(rotated_q, axis=1), np.linalg.norm(query)) and \
    np.allclose(np.linalg.norm(rotated_k, axis=1), np.linalg.norm(key))   # rotation turns a vector, never changes its length
assert kept
print("length kept by the rotation, for the query and the key:", "yes")
for i, j in [(2, 5), (12, 15), (2, 8)]:                       # (key position, query position): the first two are 3 apart, the third 6
    print(f"score with the key at {i} and the query at {j}:", f"{rotated_q[j] @ rotated_k[i] / np.sqrt(size):.3f}")   # scaled, as chapter 6 defines it
