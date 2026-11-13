"""Runs two heads of causal attention over four positions, each head working in four of the eight numbers, then mixes
the heads with an output projection. The prose's point rests on the last position's weights differing between the heads,
and on the output keeping the input's shape."""
import numpy as np

rng = np.random.default_rng(2026)                            # a fixed seed, so the printed weights are the same on every run
positions, dims, heads = 4, 8, 2
size = dims // heads                                          # each head works in 4 of the 8 dimensions
x = rng.normal(0, 1, (positions, dims))
w_query, w_key, w_value, output_projection = (rng.normal(0, 0.5, (dims, dims)) for _ in range(4))


def split(m):                                                 # (positions, dims) -> (heads, positions, size)
    return m.reshape(positions, heads, size).transpose(1, 0, 2)   # head 1 takes the first four numbers of each vector


queries, keys, values = split(x @ w_query), split(x @ w_key), split(x @ w_value)
scores = queries @ keys.transpose(0, 2, 1) / np.sqrt(size)             # one score matrix per head
scores = np.where(np.tril(np.ones((positions, positions), dtype=bool)), scores, -np.inf)   # the causal mask, for both heads
weights = np.exp(scores - scores.max(-1, keepdims=True))
weights /= weights.sum(-1, keepdims=True)
joined = (weights @ values).transpose(1, 0, 2).reshape(positions, dims)   # the heads' outputs side by side
output = joined @ output_projection                                       # mixed back together by one more matrix

print("weights shape (heads, positions, positions):", weights.shape)
print("what the last token attends to, head 1:", np.round(weights[0, -1], 2))   # -1 is the last position, which sees all four
print("what the last token attends to, head 2:", np.round(weights[1, -1], 2))
print("output shape:", output.shape)
