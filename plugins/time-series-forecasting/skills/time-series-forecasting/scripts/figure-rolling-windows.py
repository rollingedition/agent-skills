"""Draw the first four Sunday windows of 2014 on one date axis: each fixed 1,344-hour history with its 24 targets, and the
expanding history that cross_validation takes when input_size is not passed, drawn from the dates alone with no model fitted.
The lines print the lengths and dates the prose quotes."""
import matplotlib.dates as mdates
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.settings import HISTORY_HOURS, HORIZON, LEAD, show

cutoffs = pd.date_range("2014-01-05", periods=4, freq="W-SUN")  # the first four Sunday cutoffs of the sample
lead = load([LEAD])
first = lead["ds"].min()
fixed = [history_before(lead, c) for c in cutoffs]               # raises unless each window holds 1,344 hours
expanding = [int(((lead["ds"] >= first) & (lead["ds"] < c)).sum()) for c in cutoffs]

show("fixed history hours per window", len(fixed[0]))
show("step between cutoffs, days", (cutoffs[1] - cutoffs[0]).days)
show("first reading of the series", f"{first:%b %-d, %Y %H:%M}")
show("expanding history hours at the first window", expanding[0])
show("expanding history hours at the last drawn window", expanding[-1])

fig, (top, bottom) = new_figure(rows=2, height=5.4)              # one date axis, shared by both panels, to scale
rows = [4, 3, 2, 1]                                              # the first window on top
for y, c in zip(rows, cutoffs):
    top.barh(y, HISTORY_HOURS / 24, left=mdates.date2num(c - pd.Timedelta(HISTORY_HOURS, unit="h")), height=0.56,
             color=ACCENT, label="fixed history, 1,344 hours" if y == 4 else None)
    top.barh(y, HORIZON / 24, left=mdates.date2num(c), height=0.56, color=INK, label="24 targets" if y == 4 else None)
    bottom.barh(y, (c - first) / pd.Timedelta(1, unit="D"), left=mdates.date2num(first), height=0.56, color=MUTED,
                label="expanding history, from the first reading" if y == 4 else None)
    bottom.plot([mdates.date2num(c)] * 2, [y - 0.4, y + 0.4], color=INK, linewidth=2.0,
                label="cutoff" if y == 4 else None)
for ax in (top, bottom):
    ax.set_xlim(mdates.date2num(first - pd.Timedelta(5, unit="D")), mdates.date2num(cutoffs[-1] + pd.Timedelta(3, unit="D")))
    ax.set_yticks(rows, [f"{c:%b} {c.day}, {c.year}" for c in cutoffs])
    ax.set_axisbelow(True)                                      # grid behind the bars, so no cutoff mark looks broken
    ax.set_ylim(0.4, 4.6)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
top.set_title("the same eight weeks before each cutoff", loc="left", color=MUTED)
bottom.set_title("the history that grows, from the first reading", loc="left", color=MUTED)
handles, labels = [sum(x, []) for x in zip(top.get_legend_handles_labels(), bottom.get_legend_handles_labels())]
fig.legend(handles, labels, loc="outside upper left", ncols=2, frameon=False, labelcolor=INK)
save(fig, "rolling-windows")
