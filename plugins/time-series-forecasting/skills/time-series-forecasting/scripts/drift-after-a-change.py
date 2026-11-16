"""Shows how a change appears in the flags: a stated test, not a fact about the data, in which every reading from Dec 27,
2014 is multiplied by 0.6, as if demand had dropped by 40%. The calibration windows are earlier than the change, so the
reference and bands are fixed before it happens. The `held-out days flagged` and `coverage 80` lines show what the flags
and bands do, with the same cadence, reference, rule and bands as the held-out runs in drift-flag-rolling and
rolling-refit-seven-days."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import (CAL_DAYS, HELD_OUT_DAYS, band, coverage_by_day, daily_mase, flagged, prepare, run_days,
                         scale_from, with_actuals)
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
cal = with_actuals(run_days(df, CAL_DAYS), df)  # calibration windows come before the change, so the reference is fixed before it
reference = daily_mase(cal, scale).median()
changed = df.copy()
after = changed["ds"] >= pd.Timestamp("2014-12-27")  # the first changed day, Dec 27, from its midnight on
changed.loc[after, "y"] = changed.loc[after, "y"] * 0.6  # a stated test: every reading from Dec 27 at 60%, as if demand fell 40%
held = with_actuals(run_days(changed, HELD_OUT_DAYS), changed)  # the changed readings go through the same loop, refits included

show("reference, median daily MASE", reference)
mase = daily_mase(held, scale)
for day, value in mase.items():
    show(f"MASE {day:%Y-%m-%d}", value)
show("held-out days flagged", len(flagged(mase, reference)))
cov = coverage_by_day(band(held, cal, scale))  # the bands use the unchanged calibration days, as in the held-out run
for day, value in cov.items():
    show(f"coverage 80 {day:%Y-%m-%d}", value, digits=3)
