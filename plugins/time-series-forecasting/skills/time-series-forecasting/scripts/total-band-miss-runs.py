"""Whether the total's misses at 80 come in runs: the longest run of missed hours and the share of misses whose next
hour also misses, on the scored days in time order and on the same hours shuffled. The longest run is the line to read."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.intervals import CAL_CUTOFFS, bounds, paired, total_of
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, SEED, show

df = mask_clock_changes(load(ALL30))[["unique_id", "ds", "y"]]
cal = total_of(paired(df, CAL_CUTOFFS))
# The three scored days are 72 hours back to back, so the sort puts them in time order.
sc = total_of(paired(df, pd.to_datetime(EVAL_CUTOFFS))).sort_values("ds")
lo, hi = bounds(sc, cal, 80)
missed = ~((sc["y"] >= lo) & (sc["y"] <= hi)).to_numpy()


def longest_run(m):
    """The most consecutive hours outside the band."""
    best = run = 0
    for x in m:
        run = run + 1 if x else 0
        best = max(best, run)
    return best


def miss_after_miss(m):
    """The share of missed hours, the last hour aside, whose next hour also misses."""
    return float(m[1:][m[:-1]].mean())


rng = np.random.default_rng(SEED)
# 10,000 orderings of the same hours: as many misses, with any order in time broken.
shuffles = [rng.permutation(missed) for _ in range(10_000)]
show("scored hours", len(missed), 0)
show("hours missed at 80", int(missed.sum()), 0)
show("longest run of missed hours", longest_run(missed), 0)
show("longest run of missed hours, shuffled, mean", np.mean([longest_run(s) for s in shuffles]), 1)
show("share of shuffles with a run this long", np.mean([longest_run(s) >= longest_run(missed) for s in shuffles]), 3)
show("misses followed by a miss", miss_after_miss(missed), 3)
show("misses followed by a miss, shuffled, mean", np.mean([miss_after_miss(s) for s in shuffles]), 3)
