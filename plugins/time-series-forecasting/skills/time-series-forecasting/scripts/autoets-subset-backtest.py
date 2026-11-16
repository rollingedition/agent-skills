"""Backtest AutoETS and seasonal naive for the eight clients of SUBSET8 over the three standard cutoffs, and score both.
The fits lines count the forms AutoETS chose, and the MASE and coverage lines are the scores the comparison table quotes."""
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
# season_length=24 for hourly demand; the default of 1 would mean no season at all. n_jobs=1 keeps the output the same from run to run.
sf = StatsForecast(models=[AutoETS(season_length=24), SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
parts, forms, by_client = [], Counter(), defaultdict(list)
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])   # the eight weeks before c, clock hours filled from them
    part = sf.predict(h=HORIZON, level=[95])                          # level=[95] asks for the 95% interval the coverage line scores
    # the first forecast hour must be the cutoff itself, or the window is misaligned
    if part["ds"].min() != c:
        raise ValueError(f"forecast for {c:%Y-%m-%d} does not start at the cutoff")
    parts.append(part)
    for i, uid in enumerate(sf.uids):
        form = sf.fitted_[i, 0].model_["method"]                    # model 0 is AutoETS; its method name is the form, such as ETS(A,N,A)
        forms[form] += 1
        by_client[uid].append(form)
forecasts = pd.concat(parts, ignore_index=True)
summary, per_client = score_clients(forecasts, masked, ["AutoETS", "SeasonalNaive"], scale, interval_model="AutoETS")
show("horizon hours", HORIZON)
show("windows", len(parts))
for form, n in sorted(forms.items()):
    show(f"fits that chose {form}", n)
# the form reads ETS(error,trend,season): a multiplicative part is an M in any of the three slots
show("fits with a multiplicative part", sum(n for form, n in forms.items() if "M" in form[4:-1].split(",")))
for label, value in summary.items():
    show(label, value, digits=3 if label.startswith("coverage") else 2)   # coverage is a share, to three decimals; the rest are kWh or ratios
show("clients where AutoETS has lower MASE", int((per_client["AutoETS"] < per_client["SeasonalNaive"]).sum()))
show_client_lines(by_client, per_client, ["AutoETS", "SeasonalNaive"])
