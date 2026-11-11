"""Score the lead client's held-out week in MASE with a scale from history and with a scale from the whole series.

Both scales have the clock-change readings masked, so the only difference between them is the test week.
"""
import pandas as pd

from lib.backtest import held_out_cutoffs
from lib.baselines import BASELINES, baseline_forecasts, mase_scores, scale_history, seasonal_scale
from lib.electricity import load
from lib.quirks import mask_clock_changes
from lib.settings import HELD_OUT_WEEK, LEAD, show

LABELS = ["naive", "seasonal naive", "average of weeks"]
first_day = pd.Timestamp(HELD_OUT_WEEK[0])

full = load([LEAD])
df = full[["unique_id", "ds", "y"]]
forecasts = baseline_forecasts(df, held_out_cutoffs())
history = scale_history(full, first_day)
masked_history = mask_clock_changes(history)
masked_whole = mask_clock_changes(full)
test_rows = len(full[full["ds"] >= first_day])

show("scale rows from history", len(history))
show("last scale reading from history", history["ds"].max().strftime("%b %d, %Y %H:%M"))
show("scale rows from whole series", len(full))
show("last reading of whole series", full["ds"].max().strftime("%b %d, %Y %H:%M"))
show("test week share of whole-series rows in percent", 100 * test_rows / len(full), digits=3)
show("clock-change rows in scale history", int(history["quirk"].ne("normal").sum()))
show("test week own mean day-to-day difference", seasonal_scale(full[full["ds"] >= first_day - pd.Timedelta(hours=24)]).loc[LEAD], digits=4)
show("scale from history as recorded", seasonal_scale(history).loc[LEAD], digits=4)
show("scale from history clock changes masked", seasonal_scale(masked_history).loc[LEAD], digits=4)
show("scale from whole series clock changes masked", seasonal_scale(masked_whole).loc[LEAD], digits=4)

hist = mase_scores(df, forecasts, BASELINES, masked_history).loc[LEAD]
whole = mase_scores(df, forecasts, BASELINES, masked_whole).loc[LEAD]
for model, label in zip(BASELINES, LABELS):
    show(f"{label} MASE from history scale", hist[model])
    show(f"{label} MASE from whole-series scale", whole[model])
    show(f"{label} MASE ratio whole-series over history", whole[model] / hist[model], digits=4)
show("seasonal naive MASE from history scale at four decimals", hist["SeasonalNaive"], digits=4)
show("seasonal naive MASE from whole-series scale at four decimals", whole["SeasonalNaive"], digits=4)
