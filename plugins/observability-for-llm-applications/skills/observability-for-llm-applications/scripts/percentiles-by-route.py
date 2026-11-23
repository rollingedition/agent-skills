"""Print each route's median, p95 and p99 of message time on baseline day 1, every one with its message count n, and a 95%
interval on each p95. Percentiles are nearest rank: the value at position ceil(p/100 x n). The interval is a bootstrap over
messages, 2,000 resamples, seed 20261207. A route with fewer than 20 messages has its p95 at its largest message, which the
example prints and asserts."""

from lib.dayrun import run_day
from lib.report import fmt_int, fmt_ms
from lib.stats import bootstrap_interval, nearest_rank

from collections import defaultdict

runs = run_day("2026-12-08")
by_route = defaultdict(list)
for run in runs:
    by_route[run.outcome.route].append(run.replied_ns - run.arrived_ns)   # the message's time on the virtual clock
times = [run.replied_ns - run.arrived_ns for run in runs]
groups = {"all routes": times, **by_route}
intervals = {}
print("interval method: bootstrap over messages, 2,000 resamples, seed 20261207, 95%")
print("p99 of the values 1 to 200 (n = 200), nearest rank:", nearest_rank(list(range(1, 201)), 99))
assert nearest_rank(list(range(1, 201)), 99) == 198   # the 198th value, the third largest of 200
print("fewest values before the p95 is not the largest, nearest rank:",
      next(n for n in range(1, 201) if nearest_rank(list(range(1, n + 1)), 95) != n))
for name in ["all routes"] + sorted(by_route):
    values = groups[name]
    low, high = bootstrap_interval(values, lambda units: nearest_rank(units, 95))
    intervals[name] = (low, high)
    print(f"{name}, messages (n): {fmt_int(len(values))}")
    print(f"{name}, median: {fmt_ms(nearest_rank(values, 50))}")
    print(f"{name}, p95: {fmt_ms(nearest_rank(values, 95))}")
    print(f"{name}, p95, 95% interval: {fmt_ms(low)} to {fmt_ms(high)}")
    print(f"{name}, p99: {fmt_ms(nearest_rank(values, 99))}")
small = [name for name in sorted(by_route) if len(by_route[name]) < 20]
print("routes under 20 messages, count:", len(small))
print("routes under 20 messages, p95 is their largest message:", ", ".join(small))
for name in small:
    assert nearest_rank(by_route[name], 95) == max(by_route[name])   # ceil(0.95 n) = n for every n up to 19
assert len(times) == len(runs) == 200
# Two routes' p95 intervals overlap, so the largest p95 cannot be told apart from the next one with this many messages.
low_m, high_m = intervals["messages"]
low_c, high_c = intervals["calendar"]
assert low_m <= high_c and low_c <= high_m
