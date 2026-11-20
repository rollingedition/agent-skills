"""The flip rate over the dev variance set: the share of items whose judge verdict differs across their five samples. The
printed line 'flip rate' rests on the per-item PASS counts, which are printed with it: how many items passed 0, 1, 2, 3, 4
or 5 of 5 samples, and the mean pass rate. The temperature-0 baseline's pass rate over the same items is printed for
comparison. An item with an unreadable verdict is printed by id and left out, never counted as FAIL."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import pct
from lib.testset import load_items
from lib.variance import VARIANCE_SAMPLES, item_pass_counts

VARIANCE = "judge-answers-variance"
BASELINE = "judge-answers-baseline"
SAMPLES = len(VARIANCE_SAMPLES)

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
counts = item_pass_counts(VARIANCE, items)
excluded = [row for row in counts if not row.complete]
kept = [row for row in counts if row.complete]
for row in excluded:
    samples = ", ".join(str(sample) for sample in row.unreadable)
    print(f"unreadable, {row.item_id}: samples {samples} (left out, not counted as FAIL)")
print(f"left out of the flip rate (unreadable verdict): {len(excluded)}")

n = len(kept)
print(f"variance items compared (n): {n}")
print(f"flip rate: {pct(sum(1 for row in kept if row.flaky), n)}")
spread = [sum(1 for row in kept if row.passes == passes) for passes in range(SAMPLES + 1)]
assert sum(spread) == n  # every kept item falls in exactly one PASS count
for passes, count in enumerate(spread):
    print(f"items with {passes} of {SAMPLES} PASS: {count}")
print(f"mean per-item pass rate across samples: {pct(sum(row.passes for row in kept), n * SAMPLES)}")

found, baseline_unreadable = readable_verdicts(BASELINE, [row.item_id for row in kept], REF_SHA256)
assert not baseline_unreadable  # q-0043 is already left out above, so no kept item is unreadable under the baseline
baseline = passed(found)
print(f"baseline pass rate, same items (temperature 0): {pct(int(baseline.sum()), len(baseline))}")
