"""Backtest AutoETS and seasonal naive for the eight clients of SUBSET8 over the three standard cutoffs, and score them."""
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS, SeasonalNaive

from lib.scoring import book_scale
from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, HORIZON, SEED, SUBSET8, show
from lib.subsets import score_clients, show_client_lines
np.random.seed(SEED)
masked = mask_clock_changes(load(SUBSET8))
scale = book_scale(load(SUBSET8), EVAL_CUTOFFS[0])
sf = StatsForecast(models=[AutoETS(season_length=24), SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
parts, forms, by_client = [], Counter(), defaultdict(list)
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])
    part = sf.predict(h=HORIZON, level=[95])
    if part["ds"].min() != c:
        raise ValueError(f"forecast for {c:%Y-%m-%d} does not start at the cutoff")
    parts.append(part)
    for i, uid in enumerate(sf.uids):
        form = sf.fitted_[i, 0].model_["method"]
        forms[form] += 1
        by_client[uid].append(form)
forecasts = pd.concat(parts, ignore_index=True)
summary, per_client = score_clients(forecasts, masked, ["AutoETS", "SeasonalNaive"], scale, interval_model="AutoETS")
show("horizon hours", HORIZON)
show("windows", len(parts))
for form, n in sorted(forms.items()):
    show(f"fits that chose {form}", n)
show("fits with a multiplicative part", sum(n for form, n in forms.items() if "M" in form[4:-1].split(",")))
for label, value in summary.items():
    show(label, value, digits=3 if label.startswith("coverage") else 2)
show("clients where AutoETS has lower MASE", int((per_client["AutoETS"] < per_client["SeasonalNaive"]).sum()))
show_client_lines(by_client, per_client, ["AutoETS", "SeasonalNaive"])
