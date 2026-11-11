"""Backtest the fixed seasonal ARIMA and seasonal naive for the eight clients of SUBSET8 over the three standard cutoffs."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import ARIMA, SeasonalNaive

from lib.scoring import book_scale
from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, HORIZON, SEED, SUBSET8, show
from lib.subsets import score_clients

np.random.seed(SEED)
masked = mask_clock_changes(load(SUBSET8))
scale = book_scale(load(SUBSET8), EVAL_CUTOFFS[0])
sf = StatsForecast(models=[ARIMA(order=(1, 0, 0), season_length=24, seasonal_order=(1, 1, 0)),
                           SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
parts = []
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])
    part = sf.predict(h=HORIZON)
    if part["ds"].min() != c:
        raise ValueError(f"forecast for {c:%Y-%m-%d} does not start at the cutoff")
    parts.append(part)
forecasts = pd.concat(parts, ignore_index=True)

summary, per_client = score_clients(forecasts, masked, ["ARIMA", "SeasonalNaive"], scale)
show("horizon hours", HORIZON)
show("windows", len(parts))
for label, value in summary.items():
    show(label, value)
show("MASE gap, SeasonalNaive minus ARIMA", summary["MASE SeasonalNaive"] - summary["MASE ARIMA"])
show("clients where ARIMA has lower MASE", int((per_client["ARIMA"] < per_client["SeasonalNaive"]).sum()))
