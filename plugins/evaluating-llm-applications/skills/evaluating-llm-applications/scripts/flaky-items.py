"""The dev items flagged as flaky: the judge's verdict differs across their five variance samples. Each flagged item prints its
PASS count out of five, sorted by id, and the count matches the flip rate in flip-rate.py, since both read the same per-item
counts. A flagged item is kept as it is, so the rule printed last is the whole policy: flagged, never edited or deleted."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.testset import load_items
from lib.variance import VARIANCE_SAMPLES, item_pass_counts

VARIANCE = "judge-answers-variance"
SAMPLES = len(VARIANCE_SAMPLES)

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
counts = item_pass_counts(VARIANCE, items)
for row in counts:
    if not row.complete:  # an unreadable sample is not a FAIL: the item is named here and not flagged
        samples = ", ".join(str(sample) for sample in row.unreadable)
        print(f"left out, unreadable verdict, {row.item_id}: samples {samples}")
flagged = [row for row in counts if row.flaky]
for row in flagged:
    print(f"{row.item_id}: {row.passes} of {SAMPLES} PASS")
print(f"flagged items: {len(flagged)}")
print(f"dev items compared (n): {sum(1 for row in counts if row.complete)}")
print("rule: flagged, never edited or deleted")
