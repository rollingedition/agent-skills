import numpy as np

rng = np.random.default_rng(2026)
for size in [4, 32, 256]:
    queries, keys = rng.normal(0, 1, (1000, size)), rng.normal(0, 1, (16, size))
    for divide in [False, True]:
        scores = queries @ keys.T / (np.sqrt(size) if divide else 1)
        weights = np.exp(scores - scores.max(1, keepdims=True))
        weights /= weights.sum(1, keepdims=True)
        label = "scaled" if divide else "unscaled"
        print(f"size {size}, {label}, average largest weight in a row: {weights.max(1).mean():.2f}")
