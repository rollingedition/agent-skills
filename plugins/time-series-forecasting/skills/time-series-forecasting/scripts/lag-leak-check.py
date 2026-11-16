"""Shows which lag leaks: a lag of 1 reads the hour before each target hour, which a 24-hour forecast does not have at its
cutoff. The rows-differing lines are the shift test, and the two MAE lines show how much the leak flatters the score."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.features import fit_window_mae, lag_values
from lib.settings import EVAL_CUTOFFS, HORIZON, LEAD, show

y = load([LEAD]).set_index("ds")["y"].asfreq("h")  # asfreq gives every hour a row, so a missing hour is NaN, not skipped
HONEST, LEAKY = [24, 168], [1, 24, 168]  # HONEST lags are both at least the horizon; LEAKY adds lag 1
CUTOFFS = pd.to_datetime(EVAL_CUTOFFS)


def shift_test(lag):
    """Target hours where the lag differs between the history cut at each cutoff and the whole series, and how many."""
    compared = differing = 0
    for c in CUTOFFS:
        targets = pd.date_range(c, periods=HORIZON, freq="h")  # the 24 hours each forecast must predict
        honest = lag_values(y[y.index < c], lag, targets)  # readings before the cutoff only, as the forecast has them
        whole = lag_values(y, lag, targets)  # the same lag read from the whole series, as a table built once would read it
        same = (honest == whole) | (np.isnan(honest) & np.isnan(whole))  # NaN never equals NaN, so the second term counts two missing readings as the same
        compared += len(targets)
        differing += int((~same).sum())
    return compared, differing


show("cutoffs", len(CUTOFFS))
show("rows compared", shift_test(1)[0])  # the first value is the hours compared, the same for every lag
for lag in (1, 24, 168):
    show(f"rows differing for lag {lag}", shift_test(lag)[1])
show("MAE honest, lags 24 and 168", fit_window_mae(y, HONEST, CUTOFFS, leaky=False))  # the table holds the lags and the hour of day; leaky=False reads the target lags from the cut history
show("MAE leaky, lags 1, 24 and 168", fit_window_mae(y, LEAKY, CUTOFFS, leaky=True))  # leaky=True reads the whole series
