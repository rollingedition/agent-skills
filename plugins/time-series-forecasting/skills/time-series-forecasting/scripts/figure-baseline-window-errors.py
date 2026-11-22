"""Score the three baselines on each of the seven held-out windows, and draw each window's MAE as a group of three bars.
The printed count says how often the lowest baseline changes from one window to the next."""
import numpy as np
import pandas as pd

from lib.backtest import held_out_cutoffs, scoring_counts, window_mae
from lib.baselines import BASELINES, baseline_forecasts
from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.settings import LEAD, show

cutoffs = held_out_cutoffs()                                 # the same seven windows as naive-baselines-held-out-week
df = load([LEAD])[["unique_id", "ds", "y"]]
forecasts = baseline_forecasts(df, cutoffs)
labels = ["naive", "seasonal naive", "average of weeks"]     # printed names, in the order of BASELINES

for model in BASELINES:
    assert scoring_counts(df, forecasts, model)["missing_forecasts"] == 0   # a missing forecast would drop out of its window's MAE
mae = pd.DataFrame({label: window_mae(df, forecasts, model) for model, label in zip(BASELINES, labels)})   # rows: window days; columns: baselines
leader = mae.idxmin(axis=1)                                  # the baseline with the lowest MAE in each window
assert all(row.nsmallest(2).iloc[0] < row.nsmallest(2).iloc[1] for _, row in mae.iterrows())   # no two baselines tie for a window

show("windows", len(mae))
# leader.shift() is NaN for the first window, so the comparison starts at the second
show("changes of lowest baseline between neighbouring windows", int((leader != leader.shift()).iloc[1:].sum()))

fig, ax = new_figure(height=2.8)
x = np.arange(len(mae))
width = 0.27                                                 # three bars per window; offset (i - 1) puts the middle bar on the tick
for i, (label, color) in enumerate(zip(labels, (ACCENT, INK, MUTED))):
    hatch = "//" if label == "average of weeks" else ""      # a pattern too, so the third bar is not told apart by colour alone
    ax.bar(x + (i - 1) * width, mae[label].values, width, color=color, label=label, hatch=hatch, edgecolor=INK, linewidth=0.6)
ax.set_axisbelow(True)                                       # grid lines stay behind the bars
ax.set_xticks(x, [f"{day:%b} {day.day}" for day in mae.index])
ax.set_xlabel("window, by the day its forecast hours fall on")
ax.set_ylabel("MAE in the window, kWh")
ax.set_ylim(bottom=0)
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "baseline-window-errors")
