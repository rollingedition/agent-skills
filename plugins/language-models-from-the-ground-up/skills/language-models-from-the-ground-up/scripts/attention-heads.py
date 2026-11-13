import numpy as np

rng = np.random.default_rng(2026)
positions, dims, heads = 4, 8, 2
size = dims // heads                                          # each head works in 4 of the 8 dimensions
x = rng.normal(0, 1, (positions, dims))
w_query, w_key, w_value, output_projection = (rng.normal(0, 0.5, (dims, dims)) for _ in range(4))


def split(m):                                                 # (positions, dims) -> (heads, positions, size)
    return m.reshape(positions, heads, size).transpose(1, 0, 2)


queries, keys, values = split(x @ w_query), split(x @ w_key), split(x @ w_value)
scores = queries @ keys.transpose(0, 2, 1) / np.sqrt(size)             # one score matrix per head
scores = np.where(np.tril(np.ones((positions, positions), dtype=bool)), scores, -np.inf)
weights = np.exp(scores - scores.max(-1, keepdims=True))
weights /= weights.sum(-1, keepdims=True)
joined = (weights @ values).transpose(1, 0, 2).reshape(positions, dims)   # the heads' outputs side by side
output = joined @ output_projection                                       # mixed back together by one more matrix

print("weights shape (heads, positions, positions):", weights.shape)
print("what the last token attends to, head 1:", np.round(weights[0, -1], 2))
print("what the last token attends to, head 2:", np.round(weights[1, -1], 2))
print("output shape:", output.shape)
