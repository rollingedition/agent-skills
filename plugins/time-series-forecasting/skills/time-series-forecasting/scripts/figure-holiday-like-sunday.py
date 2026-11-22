"""Draw the lead client's Dec 25, 2014 hour by hour beside the average Thursday and the average Sunday of the eight weeks
before it. The mean absolute differences show which average day Dec 25 is closer to."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.features import is_holiday
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.settings import HISTORY_HOURS, LEAD, show

DAY = pd.Timestamp("2014-12-25")
y = load([LEAD]).set_index("ds")["y"].asfreq("h")  # asfreq gives every hour a row, so a missing hour is NaN
before = pd.date_range(DAY - pd.Timedelta(HISTORY_HOURS, unit="h"), DAY - pd.Timedelta(1, unit="h"), freq="h")
hist = y.reindex(before)
assert hist.notna().all()                          # no clock-change hour is masked: the Oct 26, 2014 change is before the window
assert not is_holiday(before)[np.isin(before.dayofweek, [3, 6])].any()  # no holiday on a Thursday or a Sunday, so none is left out

avg = hist.groupby([hist.index.dayofweek, hist.index.hour]).mean()  # mean load at each hour, per weekday: Monday 0, Sunday 6
thursday, sunday = avg.loc[3].to_numpy(), avg.loc[6].to_numpy()
day = y.reindex(pd.date_range(DAY, periods=24, freq="h")).to_numpy()  # Dec 25, hours 00:00 to 23:00
assert (day[8:] < thursday[8:]).all()              # from 08:00 on, Dec 25 is below the average Thursday in every hour
mad_thursday = np.abs(day - thursday).mean()       # hour by hour, then averaged over the 24 hours
mad_sunday = np.abs(day - sunday).mean()
show("mean absolute difference from the average Thursday, kWh", mad_thursday)
show("mean absolute difference from the average Sunday, kWh", mad_sunday)
assert mad_sunday < mad_thursday                   # the prose says Dec 25 is closer to a Sunday than to a Thursday

hours = np.arange(24)
fig, ax = new_figure(height=2.8)
ax.plot(hours, sunday, color=MUTED, linestyle="--", label="average Sunday")
ax.plot(hours, thursday, color=INK, label="average Thursday")
ax.plot(hours, day, color=ACCENT, linewidth=2.0, label="Dec 25, 2014")  # drawn last, so it sits on top
ax.set_xlabel("hour of the day")
ax.set_ylabel("kWh in the hour")
ax.set_xticks(range(0, 24, 3))
ax.set_ylim(bottom=0)
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "holiday-like-sunday")
