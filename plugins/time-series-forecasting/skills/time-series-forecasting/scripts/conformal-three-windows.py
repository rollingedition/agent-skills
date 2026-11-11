"""mlforecast's own conformal intervals, with three calibration windows, on the three standard cutoffs. Each cutoff is
refitted, and its intervals are calibrated on the three cutoffs before it. The coverage falls short of the level, and the
design, three residuals per client and hour, caps what the bands can cover."""
import pandas as pd

from lib.electricity import load
from lib.intervals import builtin_intervals, design_coverage, symmetric_ceiling
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cv = builtin_intervals(df, pd.to_datetime(EVAL_CUTOFFS))

show("scored hours", len(cv))
show("calibration windows per cutoff", 3)
show("residuals per client and hour", 3)
show("highest coverage three windows allow, any level", symmetric_ceiling(3), 3)
for level in (80, 95):
    show(f"simulated coverage at {level}, exchangeable errors", design_coverage(level, 3, "builtin"), 3)
for level in (80, 95):
    lo, hi = cv[f"LGBMRegressor-lo-{level}"], cv[f"LGBMRegressor-hi-{level}"]
    inside = (cv["y"] >= lo) & (cv["y"] <= hi)
    show(f"coverage at {level}", inside.mean(), 3)
    show(f"mean width at {level}", (hi - lo).mean())
    if level == 80:
        day = cv["ds"].dt.floor("D")
        for d, share in inside.groupby(day).mean().items():
            show(f"coverage at 80 on {d:%Y-%m-%d}", share, 3)
        for d, err in (cv["y"] - cv["LGBMRegressor"]).abs().groupby(day).mean().items():
            show(f"mean absolute error on {d:%Y-%m-%d}", err)
