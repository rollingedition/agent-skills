"""Fit the fixed seasonal ARIMA with statsmodels on the lead client's history before the first standard cutoff, and print its parameter names."""
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from lib.backtest import history_before
from lib.electricity import load
from lib.settings import EVAL_CUTOFFS, LEAD, show

hist = history_before(load([LEAD]), pd.Timestamp(EVAL_CUTOFFS[0]))
y = pd.Series(hist["y"].to_numpy(), index=pd.DatetimeIndex(hist["ds"], freq="h"))
res = SARIMAX(y, order=(1, 0, 0), seasonal_order=(1, 1, 0, 24)).fit(disp=False)
show("hours of history", len(y))
for name in res.params.index:
    show("parameter", name)
