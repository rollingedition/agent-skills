"""Draw the burn rate over the incident day, by window, with the page's threshold (chapter 9, `burn-rate-incident-day`).

A burn rate is a rate of budget use, not a count of errors: 14.4 means the window spends the budget 14.4 times as fast
as the objective allows. The one-hour burn is drawn as a gap wherever the hour holds fewer than the minimum of 10
messages, since a burn over two or three messages is noise. The five-minute burn is drawn as a gap wherever its window
holds no message, since a zero there would read as no failures among many. The page fires where the hour and the five
minutes both reach the threshold. The peaks are printed so a reader can find the spike on the figure."""
import math

from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, THRESHOLD, MIN_REQUESTS = "2026-12-09", 14.4, 10
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
run_day_traced(DAY, meter_provider=meter.provider, after_message=meter.after)  # live: faults on virtual time
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
slow = alert_verdicts(tallies, slo=0.95, measure="slow", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
hours = [(v.tick_ns - VirtualClock(DAY).now_ns) / 3_600_000_000_000 for v in errors]   # hours from the day's midnight
error_hour = [v.long.burn if v.long.requests >= MIN_REQUESTS else math.nan for v in errors]
error_five = [v.short.burn if v.short.requests else math.nan for v in errors]   # no message in five minutes: no burn
latency_hour = [v.long.burn if v.long.requests >= MIN_REQUESTS else math.nan for v in slow]


def peak(series):
    """The highest value of a series and the first tick that reaches it, as hours and minutes UTC."""
    known = [(x, i) for i, x in enumerate(series) if not math.isnan(x)]
    value = max(x for x, _ in known)
    index = min(i for x, i in known if x == value)     # the first tick at the peak, not the last
    minutes = round(hours[index] * 60)
    return fmt_burn(value), f"{minutes // 60:02d}:{minutes % 60:02d}"


print("gaps, one-hour burn at ticks under the minimum:", fmt_int(sum(math.isnan(x) for x in error_hour)))
print("peak error burn, 1 hour:", *peak(error_hour))
print("peak error burn, 5 minutes:", *peak(error_five))
print("peak latency burn, 1 hour:", *peak(latency_hour))
print("page threshold:", fmt_burn(THRESHOLD))

fig, ax = new_figure(height=2.8)
ax.plot(hours, error_hour, color=ACCENT, linewidth=1.8, label="error burn, 1 hour")
ax.plot(hours, error_five, color=INK, linewidth=1.2, marker="o", markersize=2.5, label="error burn, 5 minutes")
ax.plot(hours, latency_hour, color=MUTED, linewidth=1.2, linestyle="--", label="latency burn, 1 hour")
ax.axhline(THRESHOLD, color=INK, linewidth=1, linestyle=":", label="page threshold, 14.4")
ax.set_xlim(0, 24)
ax.set_xticks(range(0, 25, 3), [f"{h:02d}:00" for h in range(0, 25, 3)])
ax.set_ylim(0, 130)                                   # headroom above the 91.7 peak, for the legend
ax.set_yticks(range(0, 101, 20))
ax.set_ylabel("burn rate")
ax.legend(loc="upper left", ncol=2, frameon=False)    # in the headroom above the data, left of the 15:35 spike
save(fig, "burn-rate-incident-day")
