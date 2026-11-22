"""Forecasts the lead client's next day with seasonal naive for each day of the held-out week, then scores it.
The point rests on the MAE and RMSE lines, which score a copy of yesterday, and on the missing forecasts line."""
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows, held_out_cutoffs, scoring_counts, score_windows, window_mae
from lib.electricity import load
from lib.settings import HORIZON, LEAD, show


def day_mean(day):
    return df[df["ds"].dt.normalize() == pd.Timestamp(day)]["y"].mean()


# statsforecast reads a frame with three columns: the series id, the time and the value.
df = load([LEAD])[["unique_id", "ds", "y"]]
# season_length 24 is the daily cycle of hourly data; freq "h" is pandas' code for hourly steps; one job runs in one process.
sf = StatsForecast(models=[SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df, held_out_cutoffs())
scores = score_windows(df, forecasts, "SeasonalNaive")
counts = scoring_counts(df, forecasts, "SeasonalNaive")

show("horizon hours", HORIZON)
show("windows", counts["windows"])
show("scored hours", counts["scored_hours"])
show("missing forecasts", counts["missing_forecasts"])
# The readings at the forecast hours, which are the hours the scores cover.
show("mean demand", df[df["ds"].isin(forecasts["ds"])]["y"].mean())
show("mean demand 2014-12-24", day_mean("2014-12-24"))
show("mean demand 2014-12-25", day_mean("2014-12-25"))
show("MAE", scores["mae"])
show("RMSE", scores["rmse"])
for day, mae_day in window_mae(df, forecasts, "SeasonalNaive").items():
    show(f"MAE {day:%Y-%m-%d}", mae_day)

# The check is run on a history with one hour removed, to show it refuses a short history.
cutoff = held_out_cutoffs()[0]
gap = df[df["ds"] != cutoff - pd.Timedelta(1, unit="h")]  # drops the hour just before the first cutoff
try:
    forecast_windows(sf, gap, [cutoff])  # history_before raises ValueError unless every client has exactly HISTORY_HOURS rows before the cutoff.
    refused = "no"
except ValueError:
    refused = "yes"
show("history with one hour removed refused", refused)
