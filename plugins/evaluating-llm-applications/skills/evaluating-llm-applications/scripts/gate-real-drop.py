"""Runs the gate on second-model against the baseline over the eighty dev items: both pass rates with their counts, the paired
difference, its interval, the threshold and the decision. The gate fails only when the upper bound of the interval is below
minus the threshold, so a drop that the interval cannot rule out below the threshold does not fail it."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.gate import FAIL, gate
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import interval_points, pct
from lib.testset import load_items

BASELINE = "judge-answers-baseline"
CANDIDATE = "judge-answers-second-model"
# Five points is this gate's threshold, chosen for the book, not a standard. With eighty dev items one item moves a rate
# by 1.25 points, so five points is four items net: a smaller threshold would ask the gate to see drops the interval
# cannot resolve at this size.
THRESHOLD_POINTS = 5.0

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
baseline_found, baseline_unreadable = readable_verdicts(BASELINE, items, REF_SHA256)
candidate_found, candidate_unreadable = readable_verdicts(CANDIDATE, items, REF_SHA256)
for label, unreadable in (("baseline", baseline_unreadable), ("second-model", candidate_unreadable)):
    details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
    print(f"unreadable verdicts, {label}: {len(unreadable)}{details}")
# An item the judge did not give a readable verdict on, under either run, is left out of both sides: a paired
# difference needs the same items under both runs.
excluded = {item_id for item_id, _ in baseline_unreadable + candidate_unreadable}
kept = [item_id for item_id in items if item_id not in excluded]
first = passed({item_id: baseline_found[item_id] for item_id in kept})  # 1.0 or 0.0 per item, in id order
second = passed({item_id: candidate_found[item_id] for item_id in kept})

result = gate(first, second, threshold_points=THRESHOLD_POINTS)
print(f"dev items compared (n): {result.n}")
print(f"baseline pass rate: {pct(int(first.sum()), result.n)}")
print(f"second-model pass rate: {pct(int(second.sum()), result.n)}")
print(f"difference, second-model minus baseline: {100 * result.difference:+.1f} points")
print(f"{100 * result.level:.0f}% interval of the difference: {interval_points(result.lo, result.hi)}")
print(f"upper bound of the interval: {100 * result.hi:+.1f} points")
print(f"threshold: {THRESHOLD_POINTS:.1f} points")
if result.decision == FAIL:
    print(f"decision: fail, since the upper bound {100 * result.hi:+.1f} is below {-THRESHOLD_POINTS:+.1f}")
else:
    print(f"decision: pass, since the upper bound {100 * result.hi:+.1f} is not below {-THRESHOLD_POINTS:+.1f}")
