"""Catch a lag that leaks: a lag of 1 reads the hour before each target hour, which is not known at a 24-hour cutoff."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.features import fit_window_mae, lag_values
from lib.settings import EVAL_CUTOFFS, HORIZON, LEAD, show

y = load([LEAD]).set_index("ds")["y"].asfreq("h")
HONEST, LEAKY = [24, 168], [1, 24, 168]
CUTOFFS = pd.to_datetime(EVAL_CUTOFFS)


def shift_test(lag):
    """Target hours where the lag differs between the history cut at each cutoff and the whole series, and how many."""
    compared = differing = 0
    for c in CUTOFFS:
        targets = pd.date_range(c, periods=HORIZON, freq="h")
        honest = lag_values(y[y.index < c], lag, targets)
        whole = lag_values(y, lag, targets)
        same = (honest == whole) | (np.isnan(honest) & np.isnan(whole))
        compared += len(targets)
        differing += int((~same).sum())
    return compared, differing


show("cutoffs", len(CUTOFFS))
show("rows compared", shift_test(1)[0])
for lag in (1, 24, 168):
    show(f"rows differing for lag {lag}", shift_test(lag)[1])
show("MAE honest, lags 24 and 168", fit_window_mae(y, HONEST, CUTOFFS, leaky=False))
show("MAE leaky, lags 1, 24 and 168", fit_window_mae(y, LEAKY, CUTOFFS, leaky=True))
