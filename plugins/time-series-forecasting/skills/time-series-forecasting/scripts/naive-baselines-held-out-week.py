"""Score the three baselines for the lead client over the held-out week: naive, seasonal naive, average of weeks."""
import pandas as pd

from lib.backtest import held_out_cutoffs, score_windows, window_mae
from lib.baselines import BASELINES, baseline_forecasts
from lib.electricity import load
from lib.settings import LEAD, show

cutoffs = held_out_cutoffs()
df = load([LEAD])[["unique_id", "ds", "y"]]
forecasts = baseline_forecasts(df, cutoffs)
labels = ["naive", "seasonal naive", "average of weeks"]

show("windows", len(cutoffs))
show("scored hours", len(forecasts))
show("missing forecasts", int(forecasts[BASELINES].isna().sum().sum()))
show("mean demand", df[df["ds"].isin(forecasts["ds"])]["y"].mean())
for model, label in zip(BASELINES, labels):
    show(f"{label} MAE", score_windows(df, forecasts, model)["mae"])
for model, label in zip(BASELINES, labels):
    per_window = window_mae(df, forecasts, model)
    show(f"{label} worst window MAE", per_window.max())
    show(f"{label} worst window", per_window.idxmax().strftime("%b %d, %Y"))
    for day in ["2014-12-25", "2014-12-26"]:
        show(f"{label} MAE {pd.Timestamp(day):%b %d} window", per_window[pd.Timestamp(day)])
