"""The total's 72 scored hours with its 80% band, the actual total, and each hour outside the band marked.
The missed hours and the longest run of them in a row are printed; the run is the line to read."""
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.intervals import CAL_CUTOFFS, bounds, paired, total_of
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

df = mask_clock_changes(load(ALL30))[["unique_id", "ds", "y"]]   # clock-change hours masked as NaN, as in every example here
cal = total_of(paired(df, CAL_CUTOFFS))                          # the total over the twelve calibration days
sc = total_of(paired(df, pd.to_datetime(EVAL_CUTOFFS))).sort_values("ds")   # the three scored days, in time order
lo, hi = bounds(sc, cal, 80)                                     # the total's band at 80, from its own residuals
missed = ~((sc["y"] >= lo) & (sc["y"] <= hi)).to_numpy()         # True for each hour the reading falls outside the band

# Run starts and ends, found where the 0/1 flags change; the longest run is the largest gap between a start and its end.
edges = np.flatnonzero(np.diff(np.r_[0, missed.astype(int), 0]))
longest = int(np.max(edges[1::2] - edges[::2]))
hours = sc["ds"].to_numpy()
run_start = edges[::2][np.argmax(edges[1::2] - edges[::2])]      # the first hour of the longest run
show("scored hours", len(missed), 0)
show("hours missed at 80", int(missed.sum()), 0)
show("longest run of missed hours", longest, 0)
show("longest run starts", f"{pd.Timestamp(hours[run_start]):%b %-d, %H:00}")
assert int(missed.sum()) == 24 and longest == 8                  # the same hours as total-band-miss-runs

fig, ax = new_figure(height=2.8)
ax.fill_between(hours, lo.to_numpy(), hi.to_numpy(), color=MUTED, alpha=0.25, linewidth=0, label="80% band")
ax.plot(hours, sc["y"].to_numpy(), color=INK, linewidth=1.2, label="actual total")
ax.plot(hours[missed], sc["y"].to_numpy()[missed], color=ACCENT, linestyle="none", marker="o", markersize=4,
        label="missed hour")
ax.set_ylabel("kWh in the hour")
ax.xaxis.set_major_locator(mdates.DayLocator())               # a tick at each midnight, so no day is labelled twice
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "total-band-misses")
