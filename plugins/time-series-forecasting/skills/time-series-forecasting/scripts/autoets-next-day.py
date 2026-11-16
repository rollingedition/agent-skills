"""Forecasts the lead client's next day with AutoETS for each day of the held-out week, then scores it.
The point rests on the MAE and RMSE lines, read against the seasonal naive example, and on the form counts."""
import numpy as np
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

from lib.backtest import chosen_forms, forecast_windows, held_out_cutoffs, scoring_counts, score_windows, window_mae
from lib.electricity import load
from lib.settings import HORIZON, LEAD, SEED, show

# Seeded by convention. AutoETS's point forecast draws no random numbers, so this line changes nothing here.
np.random.seed(SEED)
# statsforecast reads a frame with three columns: the series id, the time and the value.
df = load([LEAD])[["unique_id", "ds", "y"]]
# model="ZZA": AICc chooses the error and trend forms; the seasonal form is fixed to additive, so every form has a day cycle.
sf = StatsForecast(models=[AutoETS(season_length=24, model="ZZA")], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df, held_out_cutoffs())
scores = score_windows(df, forecasts, "AutoETS")
counts = scoring_counts(df, forecasts, "AutoETS")
# chosen_forms refits at each cutoff to read the form each fit picked; the forecasts above do not report it.
forms = chosen_forms(sf, df, held_out_cutoffs())

show("horizon hours", HORIZON)
show("windows", counts["windows"])
show("scored hours", counts["scored_hours"])
show("missing forecasts", counts["missing_forecasts"])
for form, n in forms.items():
    show(f"windows that chose {form}", n)
show("MAE", scores["mae"])
show("RMSE", scores["rmse"])
for day, mae_day in window_mae(df, forecasts, "AutoETS").items():
    show(f"MAE {day:%Y-%m-%d}", mae_day)
