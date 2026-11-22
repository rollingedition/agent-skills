"""Draw the daily MASE of the held-out week as recorded, and after the stated test in which every reading from Dec 27 is
multiplied by 0.6, against the flag line at twice the reference. The two lines are the same through Dec 26; from Dec 27
the as-recorded line stays under the flag line and the after-the-test line stays above it. The asserts check that shape,
and the counts drift-flag-rolling and drift-after-a-change print."""
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.figures import ACCENT, INK, new_figure, save
from lib.panel import ALL30
from lib.running import (CAL_DAYS, FLAG_FACTOR, HELD_OUT_DAYS, daily_mase, flagged, prepare, run_days, scale_from,
                         with_actuals)
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
reference = daily_mase(with_actuals(run_days(df, CAL_DAYS), df), scale).median()    # calibration days, before the change
line = FLAG_FACTOR * reference                                                      # twice the reference
recorded = daily_mase(with_actuals(run_days(df, HELD_OUT_DAYS), df), scale)

changed = df.copy()
after = changed["ds"] >= pd.Timestamp("2014-12-27")                                 # the stated test, from Dec 27 on
changed.loc[after, "y"] = changed.loc[after, "y"] * 0.6
tested = daily_mase(with_actuals(run_days(changed, HELD_OUT_DAYS), changed), scale)

from_dec27 = recorded.index >= pd.Timestamp("2014-12-27")                           # the test starts here
assert np.allclose(recorded[~from_dec27], tested[~from_dec27])                      # the same through Dec 26
assert (recorded[from_dec27] < line).all() and (tested[from_dec27] > line).all()    # the shape from Dec 27 on
assert len(flagged(recorded, reference)) == 2 and len(flagged(tested, reference)) == 7  # the counts the drift examples print
show("reference, median daily MASE", reference)
show("flag line, MASE", line)

fig, ax = new_figure(height=3.2)
ax.plot(recorded.index, recorded.values, color=INK, marker="o", markersize=3, label="as recorded")
ax.plot(tested.index, tested.values, color=ACCENT, marker="s", markersize=6, markerfacecolor="none",
        label="after the stated test: readings from Dec 27 at 60%")    # hollow squares, so a dot under them shows
ax.axhline(line, color=INK, linestyle="--", linewidth=1.0, label="flag line, twice the reference")
ax.set_ylabel("daily MASE")
ax.set_ylim(bottom=0)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
fig.legend(loc="outside upper left", ncols=1, frameon=False, labelcolor=INK)
save(fig, "drift-flags")
