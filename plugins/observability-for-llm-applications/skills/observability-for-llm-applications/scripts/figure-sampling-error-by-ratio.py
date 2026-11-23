"""Draw the error of a head sample's estimate of baseline day 1's total tokens against the sampling ratio, with the 95 percent
interval (chapter 11, `estimating-totals-from-a-sample`). The interval narrows as the ratio rises, and at ratio 1.0 every message
is kept, so the interval has no width. The points the prose names are printed, so a reader can read them off the lines."""
import math

from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share
from lib.sampling import estimate_total, head_sample, message_traces, only_messages

MODEL = "Qwen3-4B-Instruct-2507"
DAY = "2026-12-08"
RATIOS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)
traces = only_messages(message_traces(run_day_traced(DAY, live=False).spans, DAY, MODEL, PriceTable()))
full = sum(t.tokens for t in traces)
points = []                                         # (ratio, estimate share, interval low share, interval high share)
for ratio in RATIOS:
    sample = head_sample(traces, ratio)
    estimate, (low, high) = estimate_total([t.tokens for t in sample], ratio)
    points.append((ratio, 100 * estimate / full, 100 * low / full, 100 * high / full))
    if ratio in (0.01, 0.1, 0.5):
        print(f"messages kept at ratio {ratio}, of {len(traces)}:", fmt_int(len(sample)))
        print(f"estimate as a share of the full count, ratio {ratio}:", fmt_share(estimate, full))
        print(f"interval low end as a share of the full count, ratio {ratio}:", fmt_share(low, full))
        print(f"interval high end as a share of the full count, ratio {ratio}:", fmt_share(high, full))
print("full count of tokens, all messages:", fmt_int(full))
xs, estimate_share, low, high = zip(*points)
fig, ax = new_figure(height=2.8)
ax.fill_between(xs, low, high, color=MUTED, alpha=0.35, linewidth=0, label="95% interval")
ax.plot(xs, estimate_share, color=ACCENT, linewidth=1.8, marker="o", markersize=3, label="estimate, head sample")
ax.axhline(100, color=INK, linewidth=1, linestyle=":", label="full count")
ax.set_xscale("log")
ax.set_xticks(RATIOS, [f"{r:g}" for r in RATIOS])
ax.set_xlabel("sampling ratio (log scale)")
ax.set_ylabel("estimate, % of full count")
bottom, top = float(min(low)), float(max(high))      # the axis starts at the lowest interval end, not at zero
pad = 0.1 * (top - bottom)
ax.set_ylim(bottom - pad, top + 2 * pad)            # headroom above the widest interval, where the legend sits
ax.legend(loc="upper right", ncol=3, frameon=False)
save(fig, "sampling-error-by-ratio")
assert all(math.isclose(p[1], 100) for p in points if p[0] == 1.0)   # at ratio 1 every message is kept, so no error
assert all(math.isclose(p[2], p[3]) for p in points if p[0] == 1.0)  # and the interval has no width
