"""One window's history, cut by its cutoff: its first and last timestamps, and what a cut at or before the cutoff adds."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.settings import HISTORY_HOURS, LEAD, show

df = load([LEAD])
cutoff = pd.Timestamp("2014-12-29")
hist = history_before(df, cutoff)
show("history rows", len(hist))
show("first history timestamp", hist["ds"].min().strftime("%Y-%m-%d %H:%M"))
show("last history timestamp", hist["ds"].max().strftime("%Y-%m-%d %H:%M"))

wrong = df[(df["ds"] >= cutoff - pd.Timedelta(hours=HISTORY_HOURS)) & (df["ds"] <= cutoff)]  # an off-by-one cut
show("history rows with ds at or before the cutoff", len(wrong))
show("target-day readings in that cut", int((wrong["ds"] == cutoff).sum()))
