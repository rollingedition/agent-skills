"""Draws the bootstrap distribution of the paired difference, P2 minus P1, over the twenty items of twenty-cannot-tell:
how many resamples give each possible difference. The printed interval and its width are the ones that example prints,
and the asserts check that the resamples drawn here give the same ends, land on whole steps, and reach past zero."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import numpy as np

from lib import SEED
from lib.answers import chapter_items
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.judging import paired
from lib.stats import RESAMPLES, interval_points

result = paired("judge-answers-baseline", "judge-answers-prompt-b", [item.id for item in chapter_items()])
diff = result.second - result.first  # per item: +1, 0 or -1, in the sorted item order the interval uses
# bootstrap_mean keeps only the interval, so this redraws its resamples: the same generator, seed and count.
rng = np.random.default_rng(SEED)
picks = rng.integers(0, diff.size, size=(RESAMPLES, diff.size))
gaps = 100 * diff[picks].mean(axis=1)  # each resampled difference, in points
lo, hi = np.quantile(gaps, [0.025, 0.975])  # the middle 95% of the resampled differences
assert np.isclose(lo, 100 * result.diff_lo) and np.isclose(hi, 100 * result.diff_hi), "the resamples must give the interval"
assert lo < 0.0 < hi, "the middle 95% must reach past zero on both sides"
# One differing item moves the difference by 100 / n points, so every resample is a whole number of steps.
step = 100 / result.n
assert np.allclose(gaps / step, np.round(gaps / step)), "every resampled difference must be a multiple of the step"
values, value_counts = np.unique(np.round(gaps, 6), return_counts=True)
assert values[value_counts.argmax()] == 0.0, "the most common resampled difference must be zero"

print(f"paired items (n): {result.n}")
differing = int((result.first != result.second).sum())
print(f"items where the two verdicts differ: {differing}")
print(f"bootstrap resamples: {RESAMPLES}")
print(f"difference, P2 minus P1: {100 * result.difference:+.1f} points")
print(f"95% interval of the difference: {interval_points(result.diff_lo, result.diff_hi)}")
print(f"interval width: {100 * (result.diff_hi - result.diff_lo):.1f} points")
print(f"step between possible differences: {step:.1f} points")
print(f"most common difference: {values[value_counts.argmax()]:+.1f} points")
print(f"resamples at the most common difference: {value_counts.max()}")

fig, ax = new_figure(height=2.8)
# One bar per step, centred on each possible difference, so a resample at -25 gets a bar of its own.
edges = np.arange(gaps.min() - step / 2, gaps.max() + step, step)
counts, _, _ = ax.hist(gaps, bins=edges, rwidth=0.8, color=ACCENT, label="resampled differences")
assert counts.sum() == RESAMPLES, "every resample must fall in a bar"
# Zero is the claim: the interval includes it, so no difference is ruled out at this size.
ax.axvline(0, color=INK, linewidth=1.2, label="zero: no difference")
ax.axvline(100 * result.diff_lo, color=MUTED, linestyle="--", label="ends of the middle 95%")
ax.axvline(100 * result.diff_hi, color=MUTED, linestyle="--")
ax.set_xlabel("difference, P2 minus P1, in percentage points")
ax.set_ylabel("resamples")
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2)  # above the plot, where no line crosses it
save(fig, "twenty-difference")
