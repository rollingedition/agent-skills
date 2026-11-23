"""Draw baseline day 1's message times twice, on one millisecond scale: each message as a point in the upper panel, and the
bucket counts for the same messages in the lower panel, each bucket drawn across the span it covers. The edges are the ones
bucket-edges-hide-tail uses. Every value the figure shows is printed first, and the nearest-rank p95 is drawn as a line."""
from lib import genai
from lib.dayrun import run_day
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.stats import bucket_counts, nearest_rank

EDGES_S = genai.BUCKETS["gen_ai.client.invoke_agent.duration"]  # the conventions' advised upper bounds, in seconds, as there
runs = run_day("2026-12-08")
times = sorted(run.replied_ns - run.arrived_ns for run in runs)
n = len(times)
edges = [round(edge * 1_000_000_000) for edge in EDGES_S]      # integer nanoseconds, as every time here is
counts = bucket_counts(times, edges)
exact = nearest_rank(times, 95)
lows = [0] + edges                                             # each bucket starts at the edge before it
print("messages (n):", fmt_int(n))
for number, count in enumerate(counts):
    if number < len(edges):
        print(f"bucket above {fmt_ms(lows[number])} up to {fmt_ms(edges[number])}: {fmt_int(count)} messages, {fmt_share(count, n)}")
    else:
        print(f"bucket above {fmt_ms(lows[number])}: {fmt_int(count)} messages, {fmt_share(count, n)}")
print("p95, nearest rank of the raw values:", fmt_ms(exact))

fig, (top, bottom) = new_figure(rows=2, height=4.6, sharex=True)
top.scatter([t / 1e6 for t in times], [(i + 1) / n for i in range(n)], s=10, color=INK, label="each message")
for edge in edges:
    top.axvline(edge / 1e6, color=MUTED, linestyle=":", linewidth=0.8)
top.axvline(exact / 1e6, color=ACCENT, linestyle="--", linewidth=1.2, label="p95, nearest rank")
top.set_ylabel("share at or below")
top.legend(loc="lower right")
highs = edges + [edges[-1] + 10_000_000_000]                   # the last bucket is open; drawn 10 s wide, past the axis
centres = [(lo + hi) / 2 / 1e6 for lo, hi in zip(lows, highs)]
widths = [(hi - lo) / 1e6 for lo, hi in zip(lows, highs)]
bars = bottom.bar(centres, counts, width=widths, color=MUTED)
bottom.bar_label(bars, labels=[fmt_int(c) if c else "" for c in counts], padding=2)   # empty buckets carry no label
bottom.set_xticks([e / 1e6 for e in edges], [f"{e / 1e6:,.0f}" if e >= 10_240_000_000 else "" for e in edges])   # the small edges crowd the left
bottom.set_ylabel("messages")
bottom.set_xlim(0, 42000)                                      # set after the ticks, which would widen it
bottom.set_ylim(0, max(counts) * 1.15)
bottom.set_xlabel("message time, milliseconds; bucket edges as ticks")
save(fig, "bucket-hides-tail")
