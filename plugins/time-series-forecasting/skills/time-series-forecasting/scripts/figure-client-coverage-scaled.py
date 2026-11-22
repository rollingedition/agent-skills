"""Each client's share of hours inside the 80% band on the decision windows, sorted, with residuals unscaled and scaled.
The lowest client, and how many sit within 0.1 of the target, are printed for each variant."""
import numpy as np

from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.intervals import DECISION_CAL, bounds, paired
from lib.panel import ALL30, DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.scoring import book_scale
from lib.settings import show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]          # clock-change hours masked as NaN, as in every example here
cal, sc = paired(df, DECISION_CAL), paired(df, DECISION_CUTOFFS)  # residuals on Nov 9 to 20, scored on the four decision cutoffs
scale = seasonal_scale(book_scale(raw, DECISION_CAL[0]))        # each client's scale, from the history before the first calibration cutoff

fig, ax = new_figure(height=2.8)
ranks = np.arange(1, 31)                                        # one point per client, from the lowest coverage to the highest
# scale None pools the raw kWh residuals; otherwise each client's residuals are divided by its scale first
for name, s, color, marker in (("unscaled residuals", None, MUTED, "o"), ("scaled residuals", scale, ACCENT, "s")):
    lo, hi = bounds(sc, cal, 80, scale=s)
    inside = ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean()   # each client's share of its hours in the band
    cov = np.sort(inside.to_numpy())
    show(f"{name}, lowest client coverage at 80", cov[0], 3)
    show(f"{name}, clients within 0.1 of 0.8", int(np.sum(np.abs(cov - 0.8) <= 0.1)), 0)  # a tolerance chosen for this figure, not a judging measure
    if s is None:
        assert round(cov[0], 3) == 0.021                        # the lowest client, as conformal-decision-windows prints it
    else:
        assert round(cov[0], 3) == 0.365
    ax.plot(ranks, cov, color=color, marker=marker, markersize=4, linestyle="none", label=name)
ax.axhline(0.8, color=INK, linestyle="--", linewidth=1.0, label="target, 0.8")
ax.set_ylim(0, 1)
ax.set_ylabel("share of hours inside the band")
ax.set_xlabel("client, sorted by its coverage")
ax.set_xticks([1, 10, 20, 30])
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "client-coverage-scaled")
