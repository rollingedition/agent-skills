"""Draw the average day of the total of the thirty clients, of the largest client and of a typical client, each divided by its
own daily mean, on the history before the first standard cutoff. The typical client is the one in the middle, by gap, of the
clients whose average day peaks at another hour from the total's; the lines print how it was chosen and the values the prose quotes."""
import pandas as pd

from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.panel import ALL30, panel_history
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show
from lib.totals import shares, total_history

raw = load(ALL30)
cut = pd.Timestamp(EVAL_CUTOFFS[0])                               # the first standard cutoff: shares and profiles read before it


def normalised(hist):
    """Mean load at each hour of the day, divided by the mean of those 24 means: the shape, on one scale."""
    by_hour = hist.groupby(hist["ds"].dt.hour)["y"].mean()
    return by_hour / by_hour.mean()


total_day = normalised(total_history(raw, cut))                   # the total's history has no missing hour
clients = panel_history(mask_clock_changes(raw)[["unique_id", "ds", "y"]], cut, start_rule=True)
days = pd.DataFrame({uid: normalised(g) for uid, g in clients.groupby("unique_id")}).T   # one row per client, 24 hours
largest = shares(raw, cut).idxmax()                               # the largest client by share of the total
gap = (days - total_day).abs().mean(axis=1)                       # mean absolute difference from the total's day
peak = days.idxmax(axis=1)                                        # each client's peak hour
elsewhere = gap[peak != total_day.idxmax()].sort_values()         # the clients peaking at another hour, by gap
typical = elsewhere.index[len(elsewhere) // 2]                    # the one in the middle of them
assert peak[typical] != total_day.idxmax()                        # the prose says the typical client peaks at another hour

show("clients whose average day peaks at a different hour from the total's", len(elsewhere))
show("typical client, the median gap among those", typical)
show("median gap across the thirty clients", gap.median())
show("mean absolute difference from the total's day, largest client", gap[largest], digits=3)
show("peak hour of the total's average day", f"{total_day.idxmax():02d}:00")
show("peak hour of the typical client's average day", f"{peak[typical]:02d}:00")
for name, day in (("the total's", total_day), ("the largest client's", days.loc[largest]), ("the typical client's", days.loc[typical])):
    show(f"night mean of {name} average day, hours 0 to 5, over its mean", day.loc[:5].mean())   # midnight to 05:00

fig, ax = new_figure(height=2.8)
ax.plot(total_day.index, total_day.values, color=INK, label="total of the thirty clients")
ax.plot(days.columns, days.loc[largest].values, color=MUTED, linestyle="--", label=f"largest client, {largest}")
ax.plot(days.columns, days.loc[typical].values, color=ACCENT, linewidth=2.0, label=f"typical client, {typical}")
ax.set(xlabel="hour of the day", ylabel="load over its daily mean")
ax.set_xticks(range(0, 24, 3))
ax.set_ylim(bottom=0)
fig.legend(loc="outside upper left", ncols=1, frameon=False, labelcolor=INK)
save(fig, "client-daily-profiles")
