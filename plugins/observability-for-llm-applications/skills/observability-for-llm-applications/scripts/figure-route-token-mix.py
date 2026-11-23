"""Draw the input, cached and output tokens per message on each route, over baseline day 1's 200 messages. The cached part is
drawn inside the input bar, hatched, so no reader adds it to input; output stands beside it. Every bar is printed by route
with its message count, since a tokens-per-message rate names its denominator (PL-11)."""
from lib.dayrun import run_day
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int

runs = run_day("2026-12-08")
routes = sorted({run.outcome.route for run in runs})
per_message = {}                            # route: (input, cached, output) tokens per message, as floats
for route in routes:
    mine = [run for run in runs if run.outcome.route == route]
    steps = [s for run in mine for s in run.outcome.steps if s.name == "chat"]   # model calls only; no tool time here
    averages = tuple(sum(values) / len(mine) for values in (
        [s.prompt_tokens for s in steps], [s.cached_tokens for s in steps], [s.completion_tokens for s in steps]))
    per_message[route] = averages
    print(f"route {route}, messages:", fmt_int(len(mine)))
    print(f"route {route}, input tokens per message:", f"{averages[0]:.1f}")
    print(f"route {route}, cached input tokens per message:", f"{averages[1]:.1f}")
    print(f"route {route}, output tokens per message:", f"{averages[2]:.1f}")

fig, ax = new_figure(height=2.8)
positions, width = list(range(len(routes))), 0.36
left, right = [p - width / 2 for p in positions], [p + width / 2 for p in positions]
cached = [per_message[r][1] for r in routes]
uncached = [per_message[r][0] - per_message[r][1] for r in routes]   # input minus its cached part, stacked on top of it
ax.bar(left, cached, width=width, color=MUTED, hatch="///", edgecolor=INK, label="cached input, part of input")
ax.bar(left, uncached, bottom=cached, width=width, color=ACCENT, label="input not cached")
ax.bar(right, [per_message[r][2] for r in routes], width=width, color=INK, label="output tokens")
ax.set_xticks(positions, routes)
ax.set_ylabel("tokens per message")
ax.set_ylim(0, 1.35 * max(v[0] for v in per_message.values()))   # headroom above the tallest bar for the legend
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False)   # below the plot, clear of the top tick
save(fig, "route-token-mix")
