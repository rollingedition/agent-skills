"""Measures the largest softmax weight in each row, at three sizes of query and key, with and without dividing by the
square root of the size. The prose's point rests on the unscaled averages growing with the size, and the scaled ones staying level."""
import numpy as np

rng = np.random.default_rng(2026)                            # a fixed seed, so the printed averages are the same on every run
for size in [4, 32, 256]:
    # numbers with mean 0 and variance 1, the case the scaling argument assumes; 1,000 queries against 16 keys
    queries, keys = rng.normal(0, 1, (1000, size)), rng.normal(0, 1, (16, size))
    for divide in [False, True]:
        scores = queries @ keys.T / (np.sqrt(size) if divide else 1)
        weights = np.exp(scores - scores.max(1, keepdims=True))
        weights /= weights.sum(1, keepdims=True)
        label = "scaled" if divide else "unscaled"
        print(f"size {size}, {label}, average largest weight in a row: {weights.max(1).mean():.2f}")
