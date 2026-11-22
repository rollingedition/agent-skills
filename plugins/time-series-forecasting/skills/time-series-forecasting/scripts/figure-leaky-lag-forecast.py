"""Draw the lead client's actual load over the day after each standard cutoff, with the forecast from honest lags and the
forecast from the leaky set. Each forecast is made as lag-leak-check makes it, and its MAE is checked against that example's."""
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from lib.electricity import load
from lib.features import LGBM_PARAMS, fit_window_mae, lag_table
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.settings import EVAL_CUTOFFS, HISTORY_HOURS, HORIZON, LEAD, show

y = load([LEAD]).set_index("ds")["y"].asfreq("h")  # asfreq gives every hour a row, so a missing hour is NaN
HONEST, LEAKY = [24, 168], [1, 24, 168]            # the same lag sets as lag-leak-check
CUTOFFS = pd.to_datetime(EVAL_CUTOFFS)


def forecasts(lags, leaky):
    """The actual load and the forecast for the 24 hours after each cutoff, each fitted as fit_window_mae fits it."""
    actual, pred = [], []
    for c in CUTOFFS:
        hist = pd.date_range(c - pd.Timedelta(HISTORY_HOURS, unit="h"), c - pd.Timedelta(1, unit="h"), freq="h")
        targets = pd.date_range(c, periods=HORIZON, freq="h")
        train = lag_table(y, lags, hist).assign(y=y.reindex(hist).to_numpy()).dropna()  # rows whose lag reads a gap are left out
        cols = [col for col in train.columns if col != "y"]
        model = LGBMRegressor(**LGBM_PARAMS).fit(train[cols], train["y"])
        actual.append(y.reindex(targets).to_numpy())
        source = y if leaky else y[y.index < c]    # the honest model reads the history cut at the cutoff only
        pred.append(model.predict(lag_table(source, lags, targets)[cols]))
    return np.concatenate(actual), np.concatenate(pred)


actual, honest = forecasts(HONEST, leaky=False)
_, leaky_pred = forecasts(LEAKY, leaky=True)
times = pd.DatetimeIndex(np.concatenate([pd.date_range(c, periods=HORIZON, freq="h") for c in CUTOFFS]))
assert np.isclose(np.abs(actual - honest).mean(), fit_window_mae(y, HONEST, CUTOFFS, leaky=False))  # lag-leak-check's MAE
assert np.isclose(np.abs(actual - leaky_pred).mean(), fit_window_mae(y, LEAKY, CUTOFFS, leaky=True))

show("hours forecast", len(actual))
for name, pred in (("honest", honest), ("leaky", leaky_pred)):
    show(f"correlation of the {name} forecast with the actuals", np.corrcoef(actual, pred)[0, 1], digits=3)  # [0, 1]: actual against forecast

fig, ax = new_figure(height=2.8)
ax.plot(times, actual, color=INK, linewidth=1.2, label="actual load")
ax.plot(times, honest, color=MUTED, linestyle="--", linewidth=1.2, label="forecast, lags 24 and 168")
ax.plot(times, leaky_pred, color=ACCENT, linewidth=2.0, label="forecast, lags 1, 24 and 168")
ax.set(ylabel="kWh in the hour", ylim=(0, None))
# a tick at each cutoff's midnight, labelled as the book labels days: "Dec 29"
ax.set_xticks(times[::HORIZON], [f"{d:%b} {d.day}" for d in times[::HORIZON]])
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "leaky-lag-forecast")
