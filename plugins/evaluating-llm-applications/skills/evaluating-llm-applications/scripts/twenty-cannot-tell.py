"""Shows that twenty items cannot tell the two prompts apart: the interval of the paired difference includes zero.

The assert is the chapter's claim, checked against the numbers; the example prints no verdict word."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import chapter_items
from lib.judging import paired
from lib.stats import interval_points

result = paired("judge-answers-baseline", "judge-answers-prompt-b", [item.id for item in chapter_items()])
print(f"paired items (n): {result.n}")
differing = int((result.first != result.second).sum())
print(f"items where the two verdicts differ: {differing}")
print(f"difference, P2 minus P1: {100 * result.difference:+.1f} points")
print(f"95% interval of the difference: {interval_points(result.diff_lo, result.diff_hi)}")
print(f"interval width: {100 * (result.diff_hi - result.diff_lo):.1f} points")
# Zero inside the interval is the claim: no difference that twenty items can show.
assert result.diff_lo <= 0.0 <= result.diff_hi, "the interval of the difference must include zero"
# Two items carry the whole comparison: the pass rates differ only where these two verdicts differ.
assert differing == 2, "exactly two items must have differing verdicts"
