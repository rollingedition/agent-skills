import numpy as np

tokens = ["<s>", "sled</w>", "coffee</w>", "table</w>"]
rng = np.random.default_rng(2026)
x = rng.normal(0, 1, (4, 8))
w_query, w_key, w_value = (rng.normal(0, 0.5, (8, 4)) for _ in range(3))   # the same draws as attention-by-hand
allowed = np.tril(np.ones((4, 4), dtype=bool))               # position i may look at positions 0 to i only


def attend(x, mask):
    scores = (x @ w_query) @ (x @ w_key).T / np.sqrt(4)
    if mask:
        scores = np.where(allowed, scores, -np.inf)          # a score of minus infinity becomes a weight of 0
    weights = np.exp(scores - scores.max(1, keepdims=True))
    weights /= weights.sum(1, keepdims=True)
    return weights, weights @ (x @ w_value)


weights, _ = attend(x, mask=True)
np.set_printoptions(precision=2, suppress=True)
print("weights with the causal mask:")
for token, row in zip(tokens, weights):
    print(f"  {token:<11}", row)
print("weight on later tokens:", float(weights[~allowed].sum()))

changed = x.copy()
changed[3] = rng.normal(0, 1, 8)                             # a different last token in place of `table`
for mask in [False, True]:
    before, after = attend(x, mask)[1][2], attend(changed, mask)[1][2]
    print(f"output at coffee changes with the last token, {'with' if mask else 'without'} the mask:",
          bool(not np.allclose(before, after)))
