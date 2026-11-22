"""One window's history, cut by its cutoff: its first and last timestamps, and what a cut that keeps the cutoff hour adds.
The prose's timestamps rest on the first two lines, and its off-by-one point on the row counts
with the cutoff hour in and out."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.settings import HISTORY_HOURS, LEAD, show

df = load([LEAD])  # the lead client's readings only: one series is enough to show the cut
cutoff = pd.Timestamp("2014-12-29")  # the window's cutoff at midnight, which is also its first forecast hour
hist = history_before(df, cutoff)  # the 1,344 hours before the cutoff; the cutoff hour itself is not in it
show("history rows", len(hist))
show("first history timestamp", hist["ds"].min().strftime("%Y-%m-%d %H:%M"))
show("last history timestamp", hist["ds"].max().strftime("%Y-%m-%d %H:%M"))

wrong = df[(df["ds"] >= cutoff - pd.Timedelta(HISTORY_HOURS, unit="h")) & (df["ds"] <= cutoff)]  # the off-by-one cut: <= keeps the cutoff hour
show("history rows with ds at or before the cutoff", len(wrong))
show("target-day readings in that cut", int((wrong["ds"] == cutoff).sum()))
