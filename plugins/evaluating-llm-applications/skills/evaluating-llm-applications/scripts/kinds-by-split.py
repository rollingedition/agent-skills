"""Prints the stratification of plan section 3.4 as counts: kind by split, then planted items by split, with totals.
The dev and held-out columns are the numbers the chapter's split table quotes."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.testset import load_items

items = load_items()
splits = ("dev", "held-out")
kinds = ("answerable", "unanswerable", "version-dependent", "ambiguous")
counts = Counter((item.kind, item.split) for item in items)
print(f"{'kind':<20}{'dev':>6}{'held-out':>10}{'total':>8}")
for kind in kinds:
    row = [counts[(kind, split)] for split in splits]
    print(f"{kind:<20}{row[0]:>6}{row[1]:>10}{sum(row):>8}")
totals = [sum(counts[(kind, split)] for kind in kinds) for split in splits]
print(f"{'total':<20}{totals[0]:>6}{totals[1]:>10}{sum(totals):>8}")
print()
planted = Counter((item.planted_why, item.split) for item in items if item.planted)
print(f"{'planted':<20}{'dev':>6}{'held-out':>10}{'total':>8}")
reasons = sorted({why for why, _ in planted})
for why in reasons:
    row = [planted[(why, split)] for split in splits]
    print(f"{why:<20}{row[0]:>6}{row[1]:>10}{sum(row):>8}")
planted_totals = [sum(planted[(why, split)] for why in reasons) for split in splits]
print(f"{'total':<20}{planted_totals[0]:>6}{planted_totals[1]:>10}{sum(planted_totals):>8}")
print()
print(f"items: {len(items)}")
