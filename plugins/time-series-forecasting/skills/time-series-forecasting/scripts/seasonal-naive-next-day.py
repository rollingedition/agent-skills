"""Forecast the lead client's next day with seasonal naive for each day of the held-out week, and score it."""
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows, held_out_cutoffs, scoring_counts, score_windows, window_mae
from lib.electricity import load
from lib.settings import HORIZON, LEAD, show


def day_mean(day):
    return df[df["ds"].dt.normalize() == pd.Timestamp(day)]["y"].mean()


df = load([LEAD])[["unique_id", "ds", "y"]]
sf = StatsForecast(models=[SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df, held_out_cutoffs())
scores = score_windows(df, forecasts, "SeasonalNaive")
counts = scoring_counts(df, forecasts, "SeasonalNaive")

show("horizon hours", HORIZON)
show("windows", counts["windows"])
show("scored hours", counts["scored_hours"])
show("missing forecasts", counts["missing_forecasts"])
show("mean demand", df[df["ds"].isin(forecasts["ds"])]["y"].mean())
show("mean demand 2014-12-24", day_mean("2014-12-24"))
show("mean demand 2014-12-25", day_mean("2014-12-25"))
show("MAE", scores["mae"])
show("RMSE", scores["rmse"])
for day, mae_day in window_mae(df, forecasts, "SeasonalNaive").items():
    show(f"MAE {day:%Y-%m-%d}", mae_day)

# The check is run on a history with one hour removed, to show it refuses a short history.
cutoff = held_out_cutoffs()[0]
gap = df[df["ds"] != cutoff - pd.Timedelta(hours=1)]
try:
    forecast_windows(sf, gap, [cutoff])
    refused = "no"
except ValueError:
    refused = "yes"
show("history with one hour removed refused", refused)
