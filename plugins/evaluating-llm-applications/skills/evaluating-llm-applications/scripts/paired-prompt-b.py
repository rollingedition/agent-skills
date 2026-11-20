"""Compares prompt-b (P2) with the baseline prompt (P1) on the eighty dev items: each pass rate, the paired difference with
its 95% interval, and how the items split between the two prompts. 'Better' is used only when the whole interval is above
zero (plan section 6.4); the interval here includes zero, so the reading is no difference detected."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import bootstrap_mean, interval_points, pct
from lib.testset import load_items

BASELINE = "judge-answers-baseline"
PROMPT_B = "judge-answers-prompt-b"

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
p1_found, p1_unreadable = readable_verdicts(BASELINE, items, REF_SHA256)
p2_found, p2_unreadable = readable_verdicts(PROMPT_B, items, REF_SHA256)
for label, unreadable in (("P1 (baseline)", p1_unreadable), ("P2 (prompt-b)", p2_unreadable)):
    details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
    print(f"unreadable verdicts, {label}: {len(unreadable)}{details}")
# An item without a readable verdict under either prompt is dropped from both sides: a paired difference needs the same items.
excluded = {item_id for item_id, _ in p1_unreadable + p2_unreadable}
kept = [item_id for item_id in items if item_id not in excluded]
first = passed({item_id: p1_found[item_id] for item_id in kept})  # 1.0 or 0.0 per item, in id order
second = passed({item_id: p2_found[item_id] for item_id in kept})

n = len(kept)
lo, hi = bootstrap_mean(second - first)  # 95%, one comparison: the default level
print(f"P1 (baseline) pass rate: {pct(int(first.sum()), n)}")
print(f"P2 (prompt-b) pass rate: {pct(int(second.sum()), n)}")
print(f"difference, P2 minus P1: {100 * float((second - first).mean()):+.1f} points")
print(f"95% interval of the difference: {interval_points(lo, hi)}")
print(f"paired items (n): {n}")
print(f"items only P1 passes: {int(((first == 1) & (second == 0)).sum())}")
print(f"items only P2 passes: {int(((first == 0) & (second == 1)).sum())}")
print(f"items both pass: {int(((first == 1) & (second == 1)).sum())}")
print(f"items neither passes: {int(((first == 0) & (second == 0)).sum())}")
if lo > 0:
    print(f"reading: P2 is better at n = {n}")
elif hi < 0:
    print(f"reading: P2 is worse at n = {n}")
else:
    print(f"reading: no difference detected at n = {n}")
