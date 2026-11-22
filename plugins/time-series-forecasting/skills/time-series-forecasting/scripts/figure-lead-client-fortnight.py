"""Draw the lead client's last two weeks before the first standard cutoff, with its 24-hour mean.
The hour lines show the daily shape the prose calls the season, and the 24-hour mean lines show the level."""
import matplotlib.dates as mdates
import pandas as pd

from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.settings import EVAL_CUTOFFS, LEAD, show

end = pd.Timestamp(EVAL_CUTOFFS[0]) - pd.Timedelta(1, unit="h")   # the last hour before the first standard cutoff
start = end - pd.Timedelta(14 * 24 - 1, unit="h")                   # 14 days of hours, ending there
lead = load([LEAD], start, end).set_index("ds")["y"]
mean_24 = lead.rolling(24).mean()                               # each hour's mean of the 24 hours up to it: the level, seen

by_hour = lead.groupby(lead.index.hour).mean()                  # the average day: mean load at each hour of the day
show("hours drawn", len(lead))
show("mean load, kWh", lead.mean())
show("highest hour of the average day", f"{by_hour.idxmax():02d}:00")
show("mean load at the highest hour, kWh", by_hour.max())
show("lowest hour of the average day", f"{by_hour.idxmin():02d}:00")
show("mean load at the lowest hour, kWh", by_hour.min())
show("24-hour mean on the first full day, kWh", mean_24.iloc[23])
show("24-hour mean on the last day, kWh", mean_24.iloc[-1])
show("lowest 24-hour mean, kWh", mean_24.min())
show("day of the lowest 24-hour mean", f"{mean_24.idxmin():%b %-d}")

fig, ax = new_figure(height=2.8)
ax.plot(lead.index, lead.values, color=MUTED, linewidth=0.7, label="each hour")
ax.plot(mean_24.index, mean_24.values, color=ACCENT, linewidth=2.0, label="mean of the last 24 hours")
ax.set_ylabel("kWh in the hour")
ax.set_ylim(bottom=0)
fig.legend(loc="outside upper left", ncols=2, frameon=False, labelcolor=INK)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
save(fig, "lead-client-fortnight")
