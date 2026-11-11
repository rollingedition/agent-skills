"""Conformal bands for every client, calibrated on twelve holiday-free days before the scored week, with each client's
residuals scaled first. The example also prints unscaled, three-day and finite-sample variants, for comparison."""
import pandas as pd

from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.intervals import CAL_CUTOFFS, bounds, calibration_facts, coverage, interval_score, paired
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import book_scale
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
scored_cutoffs = pd.to_datetime(EVAL_CUTOFFS)
cal, sc = paired(df, CAL_CUTOFFS), paired(df, scored_cutoffs)
scale = seasonal_scale(book_scale(raw, CAL_CUTOFFS[0]))
big = sc.groupby("unique_id")["y"].mean().idxmax()

for label, value in calibration_facts(df, scored_cutoffs).items():
    show(label, value)
show("calibration residuals per hour of the day", len(cal) // 24)
show("largest client", big)
show("mean hourly load of the largest client", sc.groupby("unique_id")["y"].mean().max())
for level in (80, 95):
    lo, hi = bounds(sc, cal, level, scale=scale)
    show(f"coverage at {level}", coverage(sc["y"], lo, hi), 3)
    show(f"mean width at {level}", (hi - lo).mean())
    show(f"interval score at {level}", interval_score(sc["y"], lo, hi, level))
lo, hi = bounds(sc, cal, 80, scale=scale)
per_client = ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean()
show("lowest client coverage at 80", per_client.min(), 3)
lo, hi = bounds(sc, cal, 80)
unscaled = ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean()
show("largest client coverage at 80, unscaled residuals", unscaled[big], 3)
recent = cal[cal["cutoff"] >= "2014-12-18"]
lo, hi = bounds(sc, recent, 80, scale=scale)
show("coverage at 80 from three calibration days", coverage(sc["y"], lo, hi), 3)
lo, hi = bounds(sc, cal, 80, scale=scale, finite=True)
show("coverage at 80 with finite-sample levels", coverage(sc["y"], lo, hi), 3)
