"""Backtest AutoETS for MT_115, a late starter, on three February cutoffs: on its raw history, and on its history from its first reading."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import fill_clock_change_hours, mask_clock_changes
from lib.settings import HORIZON, SEED, SUBSET8, show
from lib.starts import check_start_rule, history_from_start

LATE = "MT_115"
CUTOFFS = pd.to_datetime(["2014-02-01", "2014-02-15", "2014-02-28"])

np.random.seed(SEED)
dropped, flagged = check_start_rule(load(SUBSET8))
show("start rule drops, SUBSET8", dropped)
show("flagged before_first_reading, SUBSET8", flagged)
masked = mask_clock_changes(load([LATE]))[["unique_id", "ds", "y", "quirk"]]


def fit_and_score(hist, c):
    """Fit AutoETS on one history, forecast the day after c, and score it on that day."""
    sf = StatsForecast(models=[AutoETS(season_length=24)], freq="h", n_jobs=1)
    sf.fit(df=fill_clock_change_hours(hist)[["unique_id", "ds", "y"]])
    fc = sf.predict(h=HORIZON)
    actual = masked[(masked["ds"] >= c) & (masked["ds"] < c + pd.Timedelta(hours=HORIZON))]
    joined = fc.merge(actual[["ds", "y"]], on="ds", how="left")
    return sf.fitted_[0, 0].model_["method"], float(joined["AutoETS"].mean()), float((joined["y"] - joined["AutoETS"]).abs().mean()), float(joined["y"].mean())


maes = {"raw": [], "start": []}
for c in CUTOFFS:
    raw_hist = history_before(masked, c)
    show(f"zero percent before {c:%Y-%m-%d}", round(100 * (raw_hist["y"] == 0).mean()))
    for label, hist in [("raw", raw_hist), ("start", history_from_start(masked, c))]:
        form, fc_mean, window_mae, actual_mean = fit_and_score(hist, c)
        show(f"{label} history hours {c:%Y-%m-%d}", len(hist))
        show(f"{label} form {c:%Y-%m-%d}", form)
        show(f"{label} mean forecast {c:%Y-%m-%d}", fc_mean)
        show(f"{label} mean actual {c:%Y-%m-%d}", actual_mean)
        show(f"MAE {label} {c:%Y-%m-%d}", window_mae)
        maes[label].append(window_mae)
for label in maes:
    show(f"MAE {label}, three windows", np.mean(maes[label]))
    show(f"MAE {label}, 2014-02-15 and 2014-02-28", np.mean(maes[label][1:]))
