"""How a change shows up in the flags. This is a stated test, not a fact about the data: from Dec 27, 2014 every reading of
all thirty clients is multiplied by 0.6, as if demand had dropped by 40%. The held-out week runs on the changed readings,
with the same cadence, reference, rule and bands as the examples before it. The calibration days are earlier than the
change, so the bands are fixed before it happens."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import (CAL_DAYS, HELD_OUT_DAYS, band, coverage_by_day, daily_mase, flagged, prepare, run_days,
                         scale_from, with_actuals)
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
cal = with_actuals(run_days(df, CAL_DAYS), df)
reference = daily_mase(cal, scale).median()
changed = df.copy()
after = changed["ds"] >= pd.Timestamp("2014-12-27")
changed.loc[after, "y"] = changed.loc[after, "y"] * 0.6
held = with_actuals(run_days(changed, HELD_OUT_DAYS), changed)
show("reference, median daily MASE", reference)
mase = daily_mase(held, scale)
for day, value in mase.items():
    show(f"MASE {day:%Y-%m-%d}", value)
show("held-out days flagged", len(flagged(mase, reference)))
cov = coverage_by_day(band(held, cal, scale))
for day, value in cov.items():
    show(f"coverage 80 {day:%Y-%m-%d}", value, digits=3)
