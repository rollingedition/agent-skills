"""Compares prompt-b, k5 and unfiltered with the baseline on the held-out items, each variant once, at the level the
Bonferroni rule gives for three comparisons (98.33%). Each variant gets its paired difference, interval, n and a reading by
plan section 6.4. Nothing was chosen with these numbers: the variants, the level and the reading rule were fixed before
this run, and the run happens once."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import RESAMPLES, bootstrap_mean, interval_points
from lib.testset import load_items

BASELINE = "baseline"
VARIANTS = ("prompt-b", "k5", "unfiltered")
M = len(VARIANTS)  # one comparison per variant, each against the baseline
LEVEL = 1 - 0.05 / M  # Bonferroni: 1 - 0.05/m, which is 98.33% for m = 3 (plan section 6.3)

items = [item.id for item in load_items(split="held-out")]  # sorted by id
print(f"comparisons (m): {M}")
print(f"share of the 5% for each comparison, 0.05 / m: {0.05 / M:.4f}")
print(f"level of each interval, 1 - 0.05 / m: {100 * LEVEL:.2f}%")
print(f"resamples beyond each end of an interval: {RESAMPLES * (1 - LEVEL) / 2:.1f}")
base_found, base_unreadable = readable_verdicts(f"judge-answers-{BASELINE}", items, REF_SHA256)
details = "".join(f' ({item_id}, "{first}")' for item_id, first in base_unreadable)
print(f"unreadable verdicts, baseline: {len(base_unreadable)}{details}")
for name in VARIANTS:
    found, unreadable = readable_verdicts(f"judge-answers-{name}", items, REF_SHA256)
    details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
    print(f"unreadable verdicts, {name}: {len(unreadable)}{details}")
    # An item unreadable under the baseline or this variant is dropped from both sides of this pair only.
    excluded = {item_id for item_id, _ in base_unreadable + unreadable}
    kept = [item_id for item_id in items if item_id not in excluded]
    first = passed({item_id: base_found[item_id] for item_id in kept})
    second = passed({item_id: found[item_id] for item_id in kept})
    n = len(kept)
    lo, hi = bootstrap_mean(second - first, level=LEVEL)
    if name == "prompt-b":  # the chapter says this lower end is exactly zero, so the run must show it
        assert lo == 0.0, "the prompt-b lower bound must be exactly zero"
    print(f"{name} minus baseline, difference: {100 * float((second - first).mean()):+.1f} points")
    print(f"{name} minus baseline, {100 * LEVEL:.2f}% interval: {interval_points(lo, hi)}")
    print(f"{name} minus baseline, n: {n}")
    if lo > 0:
        print(f"{name} minus baseline, reading: better at n = {n}")
    elif hi < 0:
        print(f"{name} minus baseline, reading: worse at n = {n}")
    else:
        print(f"{name} minus baseline, reading: no difference detected at n = {n}")
