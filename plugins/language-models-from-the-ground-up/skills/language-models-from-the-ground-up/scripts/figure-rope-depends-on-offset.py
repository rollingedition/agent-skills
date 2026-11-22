"""Scores the same random query and key as rope-by-hand, for every offset between them, once for a key at position 2 and
once for a key at position 12. The two lines are one line, and the scores at offsets 3 and 6 are rope-by-hand's."""
from lib.transformer import rope
from lib.figures import ACCENT, INK, new_figure, save

import numpy as np

rng = np.random.default_rng(2026)                              # rope-by-hand's seed: the same random query and key
size = 32                                                      # 32 numbers: the store's width of 128 split across 4 heads
query, key = rng.normal(0, 1, size), rng.normal(0, 1, size)
positions = 64
rotated_q = rope(np.tile(query, (positions, 1)))              # the query turned for each position 0 to 63
rotated_k = rope(np.tile(key, (positions, 1)))
KEYS = (2, 12)                                                 # two key positions, 10 apart
offsets = np.arange(positions - max(KEYS))                    # the query at key + offset must exist: the later key stops at 63 - 12
lines = {k: np.array([rotated_q[k + d] @ rotated_k[k] / np.sqrt(size) for d in offsets]) for k in KEYS}

PRINTED = {3: 0.217, 6: -0.765}                               # rope-by-hand.out, copied so a change there fails here
for offset, value in PRINTED.items():
    assert round(lines[2][offset], 3) == value
gap = np.abs(lines[2] - lines[12]).max()
assert gap < 1e-9                                             # floating-point rounding, nothing more
print("smallest offset drawn:", offsets[0])
print("largest offset drawn:", offsets[-1])

fig, ax = new_figure(height=3.0)
ax.plot(offsets, lines[2], color=ACCENT, linewidth=4, alpha=0.4, label="key at position 2 (wide band)")  # wide, so the dashed line shows inside it
ax.plot(offsets, lines[12], color=INK, linestyle="--", marker="s", markersize=2.5, label="key at position 12 (dashed)")
ax.set(xlabel="offset from the key to the query, in positions", ylabel="scaled score of the query and key")
ax.set_ylim(-2.0, 1.5)                                        # room under the lowest score, clear of the legend
ax.legend(loc="lower right")
save(fig, "rope-depends-on-offset")
