"""Draws the average largest weight in a row against the size of each query and key, from 2 to 512, with and without
dividing by the square root of the size. The printed lines are the values the prose quotes, and the asserts check the
unscaled line rises at every size and that the three sizes of scaling-matters print the same values."""
from lib.figures import ACCENT, INK, new_figure, save

import numpy as np
from matplotlib.ticker import NullLocator

SIZES = [2 ** k for k in range(1, 10)]                  # 2 to 512, powers of two
# scaling-matters draws 4, 32 and 256 first from one seed, so draw those three first and the others after: the points
# at those sizes are then the same numbers scaling-matters prints
ORDER = [4, 32, 256] + [size for size in SIZES if size not in (4, 32, 256)]
PRINTED = {("unscaled", 4): 0.45, ("scaled", 4): 0.25, ("unscaled", 32): 0.78, ("scaled", 32): 0.24,
           ("unscaled", 256): 0.92, ("scaled", 256): 0.25}   # scaling-matters.out, copied so a change there fails here

rng = np.random.default_rng(2026)                       # the seed scaling-matters uses
unscaled, scaled = {}, {}
for size in ORDER:
    # 1,000 queries and 16 keys, numbers with mean 0 and variance 1, as scaling-matters draws them
    queries, keys = rng.normal(0, 1, (1000, size)), rng.normal(0, 1, (16, size))
    for divide in [False, True]:
        scores = queries @ keys.T / (np.sqrt(size) if divide else 1)
        weights = np.exp(scores - scores.max(1, keepdims=True))   # subtract each row's largest score before exp
        weights /= weights.sum(1, keepdims=True)
        (scaled if divide else unscaled)[size] = weights.max(1).mean()

for (label, size), value in PRINTED.items():
    assert round((scaled if label == "scaled" else unscaled)[size], 2) == value
unscaled_line = np.array([unscaled[s] for s in SIZES])
scaled_line = np.array([scaled[s] for s in SIZES])
assert (np.diff(unscaled_line) > 0).all()                           # the unscaled average rises at every step
print("sizes drawn:", len(SIZES))
print("smallest size drawn:", SIZES[0])
print("largest size drawn:", SIZES[-1])
print("sizes 4, 32 and 256 match scaling-matters: yes")
print("unscaled, average largest weight at size 512:", f"{unscaled_line[-1]:.2f}")
print("scaled, lowest average largest weight across sizes:", f"{scaled_line.min():.2f}")
print("scaled, highest average largest weight across sizes:", f"{scaled_line.max():.2f}")
print("unscaled rises at every size: yes")

fig, ax = new_figure(height=3.0)
ax.plot(SIZES, unscaled_line, color=ACCENT, marker="o", markersize=3, label="unscaled")
ax.plot(SIZES, scaled_line, color=INK, marker="o", markersize=3, label="scaled by the square root of the size")
ax.set_xscale("log", base=2)
ax.set_xticks(SIZES, [str(s) for s in SIZES])
ax.xaxis.set_minor_locator(NullLocator())               # one label per power of two, no minor ticks
ax.set(xlabel="size of each query and key, in numbers (log scale)", ylabel="average largest weight in a row",
       ylim=(0, 1))
ax.legend(loc="center right")
save(fig, "scaling-keeps-spread")
