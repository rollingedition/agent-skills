"""The dev and held-out splits, counted per goal, location and style: each value appears in both, and no rough case
is held out. The per-value counts show where the held-out check has few cases to stand on."""
from collections import Counter

from lib import cases, scorers

dev = cases.load_cases("dev")
held = cases.load_cases("held-out")
assert len(dev) == 60 and len(held) == 60, (len(dev), len(held))

# The rough cases (IDs r-01 to r-20) belong to chapter 1's set only; none may appear in the held-out split.
assert not any(case.split == "held-out" for case in cases.load_cases() if case.id.startswith("r-"))

for label, field in (("goal", "goal"), ("location", "location"), ("style", "style")):
    dev_counts = Counter(getattr(case, field) for case in dev)
    held_counts = Counter(getattr(case, field) for case in held)
    # Every value must appear in both splits, or a rate on one split has nothing to compare with the other.
    values = sorted(set(dev_counts) | set(held_counts))
    assert all(dev_counts[v] > 0 and held_counts[v] > 0 for v in values), label
    for value in values:
        print(f"{value} dev: {dev_counts[value]}")
        print(f"{value} held-out: {held_counts[value]}")

# The goals must be the twelve the scorers check, so no goal is left unmeasured on either split.
assert set(case.goal for case in dev + held) == set(scorers.GOALS)
