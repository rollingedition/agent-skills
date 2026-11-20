"""Loads all 120 test-set items, runs the per-item and the cross-item rules, and prints the problem count with the
counts by kind and by split. The point rests on the first line: a set that passes prints zero problems."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.testset import cross_item_problems, item_problems

items, row_problems = item_problems()  # every row, even a bad one, is reported rather than stopping the run
problems = sorted(row_problems) + cross_item_problems(items)
print(f"items: {len(items)}")
print(f"problems: {len(problems)}")
for problem in problems:
    print(f"  {problem}")

kinds = Counter(item.kind for item in items)
for kind in ("answerable", "unanswerable", "version-dependent", "ambiguous"):
    print(f"kind {kind}: {kinds[kind]}")
splits = Counter(item.split for item in items)
for split in ("dev", "held-out"):
    print(f"split {split}: {splits[split]}")
print(f"planted: {sum(1 for item in items if item.planted)}")
