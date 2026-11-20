"""How many items a paired comparison needs to detect a difference of 5 and of 10 points, with 95% confidence and 80% power.

The main estimate reads the paired differences that prompt-b and the baseline show on the dev items: each item's d is
+1, 0 or -1 (P2 minus P1), and the items on which they disagree set the variance. The floor uses only the judge's
within-item sampling noise over five samples; it leaves the disagreement between variants out, so it is a lower bound.
"""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib import variance
from lib.answers import chapter_items
from lib.calibration import readable_verdicts
from lib.judging import paired, passed
from lib.prompts import REF_SHA256
from lib.stats import pct
from lib.testset import load_items

# n = (z_alpha + z_beta)^2 * var_d / delta^2, rounded up (variance.items_needed). var_d = p_discordant - mean(d)^2.
# Smallest difference that n items detect: (z_alpha + z_beta) * sqrt(var_d / n) (variance.smallest_difference_points).
BASELINE, PROMPT_B = "judge-answers-baseline", "judge-answers-prompt-b"
CHAPTER_ONE_ITEMS = 20  # the chapter 1 set, read below the way twenty-cannot-tell reads it

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
p1_found, p1_unreadable = readable_verdicts(BASELINE, items, REF_SHA256)
p2_found, p2_unreadable = readable_verdicts(PROMPT_B, items, REF_SHA256)
kept = [item_id for item_id in items if item_id not in {i for i, _ in p1_unreadable + p2_unreadable}]
first = passed({item_id: p1_found[item_id] for item_id in kept})  # 1.0 or 0.0 per item
second = passed({item_id: p2_found[item_id] for item_id in kept})
var_d = variance.paired_difference_variance(first, second)
print(f"share of discordant items, P2 and P1 disagree: {pct(int((first != second).sum()), len(kept))}")
print(f"assumption, the next change disagrees with the baseline on about as many items as prompt-b did "
      f"({100 * (first != second).mean():.1f}% of items)")

# Floor: five samples of a 0/1 verdict with k PASS give the unbiased within-item variance k(5 - k) / (5 * 4).
rows = [row for row in variance.item_pass_counts("judge-answers-variance", items) if row.complete]
noise = sum(row.passes * (5 - row.passes) / 20 for row in rows) / len(rows)
print(f"floor, sampling noise only: dev items with five readable verdicts (n): {len(rows)}")
print(f"floor, sampling noise only: mean within-item variance of one verdict: {noise:.4f}")

# Two variants judged separately: their two noises add and the item's difficulty cancels, so the floor is 2 * noise.
for label, var in (("main estimate", var_d), ("floor, sampling noise only", 2 * noise)):
    print(f"{label}, variance of one item's paired difference: {var:.4f}")
    for delta in (5.0, 10.0):
        print(f"{label}, items needed for a {delta:.0f}-point difference: {variance.items_needed(var, delta)}")
    print(f"{label}, smallest difference that {CHAPTER_ONE_ITEMS} items detect, 80% power and 95% confidence: "
          f"{variance.smallest_difference_points(var, CHAPTER_ONE_ITEMS):.1f} points")

# The chapter 1 set, read as twenty-cannot-tell reads it: its share of discordant items and its interval width.
chapter_one = paired(BASELINE, PROMPT_B, [item.id for item in chapter_items()])
width_20 = variance.interval_width_points(var_d, CHAPTER_ONE_ITEMS)
print(f"chapter 1 set, share of items where the two verdicts differ: "
      f"{pct(int((chapter_one.first != chapter_one.second).sum()), chapter_one.n)}")
print(f"chapter 1 set, 95% interval width: {100 * (chapter_one.diff_hi - chapter_one.diff_lo):.1f} points")
print(f"main estimate, 95% width at {CHAPTER_ONE_ITEMS} items: {width_20:.1f} points")
print(f"reading: with {CHAPTER_ONE_ITEMS} items and a change that disagrees with the baseline on "
      f"{100 * (first != second).mean():.1f}% of items, as prompt-b did, the smallest difference detected with 80% power "
      f"at 95% confidence is {variance.smallest_difference_points(var_d, CHAPTER_ONE_ITEMS):.1f} points")
