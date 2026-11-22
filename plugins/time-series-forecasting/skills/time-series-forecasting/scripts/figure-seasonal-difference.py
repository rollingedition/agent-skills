"""Draw the lead client's last two weeks before the first standard cutoff above their change from the same hour
yesterday, and measure what the change still carries, over the model's 1,344 hours of history."""
import matplotlib.dates as mdates
import pandas as pd

from lib.electricity import load
from lib.figures import ACCENT, MUTED, new_figure, save
from lib.settings import EVAL_CUTOFFS, HISTORY_HOURS, LEAD, show

cutoff = pd.Timestamp(EVAL_CUTOFFS[0])
history = load([LEAD], cutoff - pd.Timedelta(HISTORY_HOURS, unit="h"), cutoff - pd.Timedelta(1, unit="h")).set_index("ds")["y"]
change = history.diff(24)                                       # (1 - B^24) y_t: each hour minus the same hour yesterday
show("history hours", len(history))
show("mean load, kWh", history.mean())
show("mean change from the same hour yesterday, kWh", change.mean())
show("spread of the load (standard deviation), kWh", history.std())
show("spread of the change (standard deviation), kWh", change.std())
# the correlations the ARIMA's two autoregressive terms model: with the hour before, and with the same hour yesterday
show("correlation of the change with the hour before", change.autocorr(1))
show("correlation of the change with the same hour yesterday", change.autocorr(24))

fortnight = history.iloc[-14 * 24:]                             # the same 14 days as the lead client's fortnight
fig, (top, bottom) = new_figure(rows=2, height=3.8)
top.plot(fortnight.index, fortnight.values, color=MUTED, linewidth=0.7)
top.set_ylabel("kWh")
top.set_title("each hour's load", loc="left", fontsize=10, color=MUTED)
top.set_ylim(bottom=0)
bottom.plot(fortnight.index, change.iloc[-14 * 24:].values, color=ACCENT, linewidth=0.7)
bottom.axhline(0, color=MUTED, linewidth=0.8)
bottom.set_ylabel("change, kWh")
bottom.set_title("its change from the same hour yesterday", loc="left", fontsize=10, color=MUTED)
bottom.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
save(fig, "seasonal-difference")
