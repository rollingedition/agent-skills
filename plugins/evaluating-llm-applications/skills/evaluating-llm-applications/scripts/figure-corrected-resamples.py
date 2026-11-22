"""Draws the bootstrap distribution of the corrected pass rate over the 2,000 resamples of correction-sensitivity: the bars
below the 100% cap, and the bar at the cap. The printed lines are the ones correction-sensitivity prints, and the asserts
check that the bars hold every kept resample and that the upper end of the interval is the cap."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import numpy as np
from matplotlib.ticker import PercentFormatter

from lib.calibration import MIN_DENOMINATOR, correction_interval, helpsteer2_judgments, readable_verdicts
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import RESAMPLES, interval_pct, pct
from lib.testset import load_items

found, _ = readable_verdicts("judge-answers-baseline", [item.id for item in load_items()], REF_SHA256)
dev_rows, item_passes = helpsteer2_judgments("dev"), passed(found)
lo, hi, capped, refused = correction_interval(dev_rows, item_passes)

# correction_interval keeps only the ends: this redraws its resamples, with the same generator, seed and draw order.
judge, human = (np.array([getattr(j, f) for j in dev_rows], dtype=bool) for f in ("judge_pass", "human_pass"))
rng = np.random.default_rng(lib.SEED)
dev, item = (rng.integers(0, n, size=(RESAMPLES, n)) for n in (judge.size, item_passes.size))  # dev rows first, readable items second
pass_s, fail_s = human[dev].sum(axis=1), (~human[dev]).sum(axis=1)
tpr = (judge[dev] & human[dev]).sum(axis=1) / np.maximum(pass_s, 1)  # a resample with no PASS row is refused below
tnr = (~judge[dev] & ~human[dev]).sum(axis=1) / np.maximum(fail_s, 1)
usable = (pass_s > 0) & (fail_s > 0) & (tpr + tnr - 1.0 >= MIN_DENOMINATOR)
rates = np.clip((item_passes[item].mean(axis=1)[usable] + tnr[usable] - 1.0) / (tpr + tnr - 1.0)[usable], 0.0, 1.0)  # clipped to [0, 1] as correction_interval clips it

assert np.allclose(np.quantile(rates, [0.025, 0.975]), [lo, hi]) and hi == 1.0, "the resamples must give the interval"
assert int((~usable).sum()) == refused and int((rates >= 1.0).sum()) == capped, "counts must match correction-sensitivity"
BIN = 0.02  # the width of each bin below the cap, in rate units: two points
counts, edges = np.histogram(rates[rates < 1.0], bins=np.append(np.arange(np.floor(rates[rates < 1.0].min() / BIN) * BIN, 1.0, BIN), 1.0))  # bins below the cap, BIN wide
assert counts.sum() + capped == rates.size and capped > counts.max(), "every kept resample must be drawn, the cap tallest"

print(f"corrected pass rate, 95% interval: {interval_pct(lo, hi)}")
print(f"resamples at the 100% cap: {pct(capped, RESAMPLES)}")
print(f"resamples refused, TPR + TNR - 1 below 0.1: {pct(refused, RESAMPLES)}")
print(f"resamples in the fullest bin below the cap: {counts.max()}")
print(f"bin width below the cap, in points: {BIN * 100:.0f}")

fig, ax = new_figure(height=2.8)
ax.bar((edges[:-1] + edges[1:]) / 2, counts, width=0.016, color=INK, label="resamples below the cap")
ax.bar(1.02, capped, width=0.016, color=ACCENT, label="resamples at the 100% cap")  # just past the 100% line, clear of the bins
ax.text(1.024, capped, "cap", ha="left", va="bottom")  # names the bar, starting clear of the 100% line at its left
ax.vlines([lo, hi], 0, 1, transform=ax.get_xaxis_transform(), color=MUTED, linestyle="--", label="ends of the middle 95%")  # full height; the upper end is the cap itself
ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0))
ax.set(xlabel="corrected pass rate, clipped to 0% to 100%", ylabel="resamples")
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2)  # above the plot, where no bar or line crosses it
save(fig, "corrected-resamples")
