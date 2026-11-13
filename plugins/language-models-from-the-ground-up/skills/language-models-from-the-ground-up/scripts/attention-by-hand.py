"""Computes one attention layer by hand for four tokens, with random matrices. The prose's point rests on the
printed weight matrix: each row says which positions one position draws from, and how much."""
import numpy as np

tokens = ["<s>", "sled</w>", "coffee</w>", "table</w>"]
rng = np.random.default_rng(2026)                            # a fixed seed, so the same numbers come out on every run
x = rng.normal(0, 1, (4, 8))                        # one 8-number vector per token, as an embedding table gives
w_query, w_key, w_value = (rng.normal(0, 0.5, (8, 4)) for _ in range(3))

queries, keys, values = x @ w_query, x @ w_key, x @ w_value   # what each token looks for, offers, and passes on
scores = queries @ keys.T / np.sqrt(4)                       # how well each query matches each key, scaled
weights = np.exp(scores - scores.max(1, keepdims=True))      # subtracting each row's largest score keeps exp from overflowing
weights /= weights.sum(1, keepdims=True)                     # softmax along each row: each row sums to 1
output = weights @ values                                     # each token: a weighted average of all the values

np.set_printoptions(precision=2, suppress=True)
print("attention weights (rows attend to columns):")
for token, row in zip(tokens, weights):
    print(f"  {token:<11}", row)
assert np.allclose(weights.sum(1), 1)                        # each row sums to 1, which the prose relies on
print("output shape:", output.shape)
