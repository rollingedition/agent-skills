"""Backtest the fixed seasonal ARIMA(1,0,0)(1,1,0)[24] and seasonal naive for the eight clients of SUBSET8 over the three standard cutoffs.
The MASE gap and the count of clients where ARIMA wins, printed last, are the figures the comparison section quotes."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import ARIMA, SeasonalNaive

from lib.scoring import book_scale
from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, HORIZON, SEED, SUBSET8, show
from lib.subsets import score_clients

np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
masked = mask_clock_changes(load(SUBSET8))                  # clock-change hours become NaN, so they are never scored; filled_history fills them from their neighbours before each fit
scale = book_scale(load(SUBSET8), EVAL_CUTOFFS[0])        # MASE scale: rows before the first cutoff, from each client's first reading
# The order is fixed, not searched: one AR term, one seasonal difference and one seasonal AR term, all at lag 24.
# n_jobs=1 keeps the output the same from run to run.
sf = StatsForecast(models=[ARIMA(order=(1, 0, 0), season_length=24, seasonal_order=(1, 1, 0)),
                           SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
parts = []
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])   # the eight weeks before c, clock hours filled from them
    part = sf.predict(h=HORIZON)
    # the first forecast hour must be the cutoff itself, or the window is misaligned
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
