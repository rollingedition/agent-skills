"""Score the three baselines for the lead client over the held-out week, on the same seven windows. The point rests on the missing-forecasts line, which must be zero for the scores to compare, and on the three MAE lines."""
import pandas as pd

from lib.backtest import held_out_cutoffs, score_windows, window_mae
from lib.baselines import BASELINES, baseline_forecasts
from lib.electricity import load
from lib.settings import LEAD, show

cutoffs = held_out_cutoffs()                                 # seven daily cutoffs at 00:00; every baseline uses these same windows
df = load([LEAD])[["unique_id", "ds", "y"]]                  # unique_id, ds and y only: the baselines read no other column
forecasts = baseline_forecasts(df, cutoffs)                  # one row per forecast hour, one column per baseline; each window reads its own history
labels = ["naive", "seasonal naive", "average of weeks"]     # printed names, in the order of BASELINES, which the loops below zip with

show("windows", len(cutoffs))
show("scored hours", len(forecasts))
show("missing forecasts", int(forecasts[BASELINES].isna().sum().sum()))   # NaN marks a forecast that could not be made; the two sums count them over every column
show("mean demand", df[df["ds"].isin(forecasts["ds"])]["y"].mean())       # the mean over the scored hours only, not over the whole history
for model, label in zip(BASELINES, labels):
    show(f"{label} MAE", score_windows(df, forecasts, model)["mae"])      # pooled over every scored hour; the result is keyed by metric name
for model, label in zip(BASELINES, labels):
    per_window = window_mae(df, forecasts, model)                         # one MAE per window, keyed by the day its forecast hours fall on
    show(f"{label} worst window MAE", per_window.max())
    show(f"{label} worst window", per_window.idxmax().strftime("%b %d, %Y"))
    for day in ["2014-12-25", "2014-12-26"]:                              # Dec 25 is the holiday and Dec 26 the day after: the two windows the prose reads
        show(f"{label} MAE {pd.Timestamp(day):%b %d} window", per_window[pd.Timestamp(day)])   # windows are keyed by midnight of their day, so a Timestamp at 00:00 finds one
