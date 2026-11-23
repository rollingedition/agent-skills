"""Draw each route's median and p95 of message time on baseline day 1, with a 95% interval on the p95, so the tail's place
in each route shows at a glance. Every value the figure draws is printed first, with its message count n. The interval
is a bootstrap over messages (2,000 resamples, seed 20261207); the route is the one the assistant chose."""

from lib.dayrun import run_day
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int, fmt_ms
from lib.stats import bootstrap_interval, nearest_rank

from collections import defaultdict

runs = run_day("2026-12-08")
times = {"all routes": [run.replied_ns - run.arrived_ns for run in runs]}
for run in runs:
    times.setdefault(run.outcome.route, []).append(run.replied_ns - run.arrived_ns)
names = ["all routes"] + sorted(name for name in times if name != "all routes")
summary = []
for name in names:
    values = times[name]
    low, high = bootstrap_interval(values, lambda units: nearest_rank(units, 95))
    summary.append((name, len(values), nearest_rank(values, 50), nearest_rank(values, 95), low, high))
    print(f"{name}, messages (n): {fmt_int(len(values))}")
    print(f"{name}, median: {fmt_ms(summary[-1][2])}")
    print(f"{name}, p95: {fmt_ms(summary[-1][3])}, interval: {fmt_ms(low)} to {fmt_ms(high)}")

fig, ax = new_figure(height=3.8)
rows = list(range(len(summary)))[::-1]                 # the first row, all routes, at the top
for row, (name, count, median, p95, low, high) in zip(rows, summary):
    ax.hlines(row, low / 1e6, high / 1e6, color=MUTED, linewidth=3, label="95% interval of the p95" if row == rows[0] else None)
    ax.scatter([median / 1e6], [row], facecolors="none", edgecolors=INK, linewidths=1.4, s=52, zorder=3,
               label="median" if row == rows[0] else None)     # a hollow circle, so the two dots differ in shape as well as colour
    ax.scatter([p95 / 1e6], [row], color=ACCENT, marker="D", s=44, zorder=3, label="p95" if row == rows[0] else None)
ax.set_yticks(rows, [f"{name} (n = {count})" for name, count, *_ in summary])
ax.set_xlabel("message time, milliseconds")
ax.set_xlim(0, 30000)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3)   # below the axis, clear of every row
save(fig, "latency-tail-by-route")
