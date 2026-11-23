"""Draw, for each scenario route on baseline day 1, how many of its messages the router sent right, to another tool route,
or to the fallback reply. The failing modes are coloured; the modes with no count on this day (truncated replies,
malformed tool calls) are printed as zero and named in the caption. Every value the figure draws is printed first."""
from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int

traced = run_day_traced("2026-12-08", live=False)  # the 4B's real replies, replayed from the recording
runs = traced.runs
malformed = sum(run.outcome.malformed_tool_calls for run in runs)  # calls the parser rejected
truncated = sum("length" in row["attributes"]["gen_ai.response.finish_reasons"]  # replies cut at the cap
                for row in traced.spans if row["name"].startswith("chat"))
assert malformed == 0 and truncated == 0
rows = []
for route in sorted({run.outcome.expected_route for run in runs}):
    group = [run for run in runs if run.outcome.expected_route == route]
    right = sum(run.outcome.route == route for run in group)
    fallback = sum(run.outcome.route == "fallback" and route != "fallback" for run in group)
    other = len(group) - right - fallback
    assert right + fallback + other == len(group)
    rows.append((route, len(group), right, other, fallback))
    print(f"route {route}, messages (n): {fmt_int(len(group))}")
    print(f"route {route}, routed right: {fmt_int(right)}")
    print(f"route {route}, wrong, to another tool route: {fmt_int(other)}")
    print(f"route {route}, wrong, to the fallback reply: {fmt_int(fallback)}")
print(f"truncated replies, baseline day 1: {fmt_int(truncated)}")
print(f"malformed tool calls, baseline day 1: {fmt_int(malformed)}")

fig, ax = new_figure(height=3.4)
ys = list(range(len(rows)))[::-1]  # the first route at the top
for y, (route, n, right, other, fallback) in zip(ys, rows):
    ax.barh(y, right, color=MUTED, alpha=0.35, label="routed right" if y == ys[0] else None)
    ax.barh(y, other, left=right, color=INK, label="wrong, to another tool route" if y == ys[0] else None)
    ax.barh(y, fallback, left=right + other, color=ACCENT, label="wrong, to the fallback reply" if y == ys[0] else None)
ax.set_xlim(0, 1.12 * max(right + other + fallback for _, _, right, other, fallback in rows))   # headroom so the longest bar is not clipped
ax.set_yticks(ys, [f"{route} (n = {n})" for route, n, *_ in rows])
ax.set_xlabel("messages on baseline day 1")
ax.legend(loc="lower right", frameon=False)
save(fig, "failure-modes-by-route")
