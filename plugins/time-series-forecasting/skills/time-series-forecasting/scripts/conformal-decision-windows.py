"""The two calibration choices, scaling each client's residuals and the finite-sample levels, decided on the four decision
windows (Nov 25 to Dec 3, 2014), with calibration on Nov 9 to 20. Compare the lowest client's coverage and the interval scores printed for each variant;
the standard cutoffs are not read."""
from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.intervals import DECISION_CAL, bounds, calibration_facts, coverage, interval_score, paired, total_of
from lib.panel import ALL30, DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.scoring import book_scale
from lib.settings import show

raw = load(ALL30)
# Every clock-change hour (four changes, 2013 and 2014) is masked as NaN, as in every example of this chapter.
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
# One row per client and hour, with the forecast f, the reading y and the residual e.
cal, sc = paired(df, DECISION_CAL), paired(df, DECISION_CUTOFFS)
# Each client's MASE-style scale, from the history before the first calibration cutoff.
scale = seasonal_scale(book_scale(raw, DECISION_CAL[0]))

for label, value in calibration_facts(df, DECISION_CUTOFFS, DECISION_CAL).items():
    show(label, value)
show("residuals per hour of the day", len(cal) // 24)
variants = (("unscaled", None, False), ("scaled", scale, False),
            ("unscaled, finite", None, True), ("scaled, finite", scale, True))
for name, s, fin in variants:
    for level in (80, 95):
        # scale=None pools the raw kWh residuals; finite=True applies the (n + 1) quantile correction.
        lo, hi = bounds(sc, cal, level, scale=s, finite=fin)
        show(f"{name}, coverage at {level}", coverage(sc["y"], lo, hi), 3)
        show(f"{name}, interval score at {level}", interval_score(sc["y"], lo, hi, level))
    lo, hi = bounds(sc, cal, 80, scale=s, finite=fin)
    # Coverage per client, then the lowest of the thirty clients.
    show(f"{name}, lowest client coverage at 80", ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean().min(), 3)
# One series, so no scale: the scale exists only to pool clients of different size.
tcal, tsc = total_of(cal), total_of(sc)
for name, fin in (("total", False), ("total, finite", True)):
    lo, hi = bounds(tsc, tcal, 80, finite=fin)
    show(f"{name}, coverage at 80", coverage(tsc["y"], lo, hi), 3)
    show(f"{name}, interval score at 80", interval_score(tsc["y"], lo, hi, 80))
