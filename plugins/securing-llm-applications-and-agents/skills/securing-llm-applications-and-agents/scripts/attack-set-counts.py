"""The fixed attack set, 120 cases (60 dev, 60 held-out): how many fall under each goal, location and style. The goal
counts are the set's denominators. Chapter 1's 20 rough cases are not part of the set, so they are printed on their own."""
from collections import Counter

from lib import cases

fixed = cases.load_cases("dev") + cases.load_cases("held-out")
# The set's size, asserted so a change to the data fails this run rather than the prose.
assert len(fixed) == 120, len(fixed)

for label, field in (("goal", "goal"), ("location", "location"), ("style", "style")):
    # Counter keys are unique, so sorting the items sorts by the ID alone.
    counts = Counter(getattr(case, field) for case in fixed)
    for key, count in sorted(counts.items()):
        print(f"{label} {key}: {count}")

print(f"split dev: {len(cases.load_cases('dev'))}")
print(f"split held-out: {len(cases.load_cases('held-out'))}")
print(f"split rough: {len(cases.load_cases('rough'))}")
