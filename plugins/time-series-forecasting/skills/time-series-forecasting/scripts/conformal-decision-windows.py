"""The two choices of the calibration design, decided on the four decision windows before the held-out week: scaling each
client's residuals before they are pooled, and the finite-sample levels. The calibration is Nov 9 to 20, 2014, twelve
holiday-free days, and the scored windows are the decision cutoffs, Nov 25 to Dec 3, 2014. The standard cutoffs are not read."""
from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.intervals import DECISION_CAL, bounds, calibration_facts, coverage, interval_score, paired, total_of
from lib.panel import ALL30, DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.scoring import book_scale
from lib.settings import show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cal, sc = paired(df, DECISION_CAL), paired(df, DECISION_CUTOFFS)
scale = seasonal_scale(book_scale(raw, DECISION_CAL[0]))

for label, value in calibration_facts(df, DECISION_CUTOFFS, DECISION_CAL).items():
    show(label, value)
show("residuals per hour of the day", len(cal) // 24)
variants = (("unscaled", None, False), ("scaled", scale, False),
            ("unscaled, finite", None, True), ("scaled, finite", scale, True))
for name, s, fin in variants:
    for level in (80, 95):
        lo, hi = bounds(sc, cal, level, scale=s, finite=fin)
        show(f"{name}, coverage at {level}", coverage(sc["y"], lo, hi), 3)
        show(f"{name}, interval score at {level}", interval_score(sc["y"], lo, hi, level))
    lo, hi = bounds(sc, cal, 80, scale=s, finite=fin)
    show(f"{name}, lowest client coverage at 80", ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean().min(), 3)
tcal, tsc = total_of(cal), total_of(sc)
for name, fin in (("total", False), ("total, finite", True)):
    lo, hi = bounds(tsc, tcal, 80, finite=fin)
    show(f"{name}, coverage at 80", coverage(tsc["y"], lo, hi), 3)
    show(f"{name}, interval score at 80", interval_score(tsc["y"], lo, hi, 80))
