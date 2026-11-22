"""Draw the lead client's three scored days: the recorded Chronos-2 median, its 80% and 95% ranges, and the actual load,
each cutoff's forecast as its own segment. The ranges are the recording's own quantiles, the 0.025 and 0.975 interpolated
by the package, so the printed coverage is for the model and the package together."""
import matplotlib.dates as mdates

from lib.compare import recorded_forecasts, score
from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.intervals import coverage
from lib.panel import ALL30
from lib.settings import LEAD, show

raw = load(ALL30)
# the recording, read only after each output matches its manifest hash; scored against the readings of the lead only
_, scored = score(raw, recorded_forecasts(), ["Chronos"], [LEAD])
lead = scored.sort_values("ds")                                 # the 72 hours of the three standard cutoffs, in time order
lo80, hi80, lo95, hi95 = lead["q10"], lead["q90"], lead["q025"], lead["q975"]
day = lead["ds"].dt.normalize()                                 # each cutoff falls at midnight: the day is the cutoff

show("hours scored", len(lead), 0)
show("readings inside the 80% range", int(((lead["y"] >= lo80) & (lead["y"] <= hi80)).sum()), 0)
show("readings inside the 95% range", int(((lead["y"] >= lo95) & (lead["y"] <= hi95)).sum()), 0)
show("coverage 80, lead Chronos", coverage(lead["y"], lo80, hi80), 3)
show("coverage 95, lead Chronos", coverage(lead["y"], lo95, hi95), 3)
show("MAE, lead Chronos median, kWh", (lead["y"] - lead["Chronos"]).abs().mean())

fig, ax = new_figure(height=3.2)
for i, (_, d) in enumerate(lead.groupby(day)):                  # one segment per cutoff, so no line crosses a cutoff
    first = i == 0                                              # the legend names each series once
    ax.fill_between(d["ds"], d["q025"], d["q975"], color=MUTED, alpha=0.15, linewidth=0,
                    label="95% range" if first else None)       # lighter: the wider band
    ax.fill_between(d["ds"], d["q10"], d["q90"], color=MUTED, alpha=0.35, linewidth=0,
                    label="80% range" if first else None)
    ax.plot(d["ds"], d["Chronos"], color=INK, linewidth=1.6, linestyle="--",
            label="Chronos-2 median" if first else None)        # dashed, so it differs from the load by more than colour
    ax.plot(d["ds"], d["y"], color=ACCENT, linewidth=1.2, linestyle="-",   # solid: the style cycle would dash later segments
            label="actual load" if first else None)
ax.set_ylabel("kWh in the hour")
ax.set_ylim(bottom=0)
ax.xaxis.set_major_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
fig.legend(loc="outside upper left", ncols=2, frameon=False, labelcolor=INK)
save(fig, "chronos-ranges")
