"""Compares the baseline prompt (P1) with prompt-b (P2) on the twenty chapter items: each pass rate, the paired difference, its interval and n.

The word 'better' is used only when the whole interval is above zero, and 'worse' only when it is below zero. A difference
whose interval includes zero is reported as no difference detected."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import chapter_items
from lib.judging import paired
from lib.stats import interval_points, pct

result = paired("judge-answers-baseline", "judge-answers-prompt-b", [item.id for item in chapter_items()])
first, second = result.first, result.second  # 1.0 or 0.0 per item, in id order
print(f"P1 (baseline) pass rate: {pct(int(first.sum()), result.n)}")
print(f"P2 (prompt-b) pass rate: {pct(int(second.sum()), result.n)}")
print(f"items that P2 passes and P1 fails: {int(((second == 1) & (first == 0)).sum())}")
print(f"items that P1 passes and P2 fails: {int(((second == 0) & (first == 1)).sum())}")
print(f"paired items (n): {result.n}")
print(f"difference, P2 minus P1: {100 * result.difference:+.1f} points")
print(f"95% interval of the difference: {interval_points(result.diff_lo, result.diff_hi)}")
if result.diff_lo > 0:
    reading = f"P2 is better at n = {result.n}"
elif result.diff_hi < 0:
    reading = f"P2 is worse at n = {result.n}"
else:
    reading = f"no difference detected at n = {result.n}"
print(f"reading: {reading}")
# The two prompts tie: the same number of items pass under each, so the pass rates and the reading say the same thing.
assert int(first.sum()) == int(second.sum()), "the two prompts must tie: the same pass count under each"
