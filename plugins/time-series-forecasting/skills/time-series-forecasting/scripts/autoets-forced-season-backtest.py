"""Backtest AutoETS with the season forced to additive (model ZZA) and seasonal naive, for the eight clients of SUBSET8 over the three standard cutoffs.
The ZZA lines are the forced-season scores that the comparison table and the forced-season paragraph quote."""
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
np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
masked = mask_clock_changes(load(SUBSET8))                  # clock-change hours become NaN, so they are never scored; filled_history fills them from their neighbours before each fit
scale = book_scale(load(SUBSET8), EVAL_CUTOFFS[0])        # MASE scale: rows before the first cutoff, from each client's first reading
# ZZA: Z lets the model choose the error and the trend, A forces an additive season. alias names the output columns.
sf = StatsForecast(models=[AutoETS(model="ZZA", season_length=24, alias="ZZA"), SeasonalNaive(season_length=24)],
                   freq="h", n_jobs=1)
parts, forms, by_client = [], Counter(), defaultdict(list)
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])   # the eight weeks before c, clock hours filled from them
    part = sf.predict(h=HORIZON, level=[95])                          # level=[95] asks for the 95% interval the coverage line scores
    # the first forecast hour must be the cutoff itself, or the window is misaligned
    if part["ds"].min() != c:
        raise ValueError(f"forecast for {c:%Y-%m-%d} does not start at the cutoff")
    parts.append(part)
    for i, uid in enumerate(sf.uids):
        form = sf.fitted_[i, 0].model_["method"]                    # model 0 is the forced AutoETS; its method name is the form
        forms[form] += 1
        by_client[uid].append(form)
forecasts = pd.concat(parts, ignore_index=True)
summary, per_client = score_clients(forecasts, masked, ["ZZA", "SeasonalNaive"], scale, interval_model="ZZA")
show("horizon hours", HORIZON)
show("windows", len(parts))
for form, n in sorted(forms.items()):
    show(f"fits that chose {form}", n)
for label, value in summary.items():
    show(label, value, digits=3 if label.startswith("coverage") else 2)
show("clients where ZZA has lower MASE", int((per_client["ZZA"] < per_client["SeasonalNaive"]).sum()))
show_client_lines(by_client, per_client, ["ZZA", "SeasonalNaive"])
