"""Draw each release's paired difference from baseline r0 on the same messages, in p95 message time and in input tokens per message, each with its interval. A line that crosses the zero line is a difference the interval cannot rule out; the p95 uses messages resampled jointly, and the token mean uses per-message differences."""
from lib.gate import P95, measured, paired
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int, fmt_ms
from lib.stats import paired_interval, paired_mean_difference
from matplotlib.ticker import FuncFormatter

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
RELEASES_TO_DRAW = [   # name, the row's label as the prose gives it, the recording folder, the model; each against r0
    ("r1", "Prompt change", "release-prompt-v2", MODEL),
    ("r2", "Model swap", "release-model-swap", "Qwen3-0.6B"),
    ("r3", "Top-8 release", "release-top-8", MODEL),
    ("r4", "Cache-off release", "release-cache-off", MODEL),
]
def show(line, point, low, high, fmt):
    """Print one difference with its 95% interval."""
    print(line, fmt(round(point)), f"(interval {fmt(round(low))} to {fmt(round(high))})")

base = measured("baseline-day-1", DAY, MODEL)
fig, (left, right) = new_figure(height=3.2, columns=2, sharex=False)
ticks = []
for row, (name, label, folder, model) in zip(range(len(RELEASES_TO_DRAW))[::-1], RELEASES_TO_DRAW):   # the top row first
    ids, before, after = paired(base, measured(folder, DAY, model))
    time_p, (time_low, time_high) = paired_interval([m["time"] for m in before], [m["time"] for m in after], P95)
    token_p, (token_low, token_high) = paired_interval([m["tokens"] for m in before], [m["tokens"] for m in after],
                                                       paired_mean_difference)
    show(f"{name}, p95 message time, difference:", time_p, time_low, time_high, fmt_ms)
    show(f"{name}, input tokens per message, difference:", token_p, token_low, token_high, fmt_int)
    left.hlines(row, time_low / 1e6, time_high / 1e6, color=MUTED, linewidth=3)
    left.scatter([time_p / 1e6], [row], color=ACCENT, zorder=3)
    right.hlines(row, token_low, token_high, color=MUTED, linewidth=3)
    right.scatter([token_p], [row], color=ACCENT, zorder=3)
    ticks.append((row, f"{label} (n = {len(ids)})"))
for axis in (left, right):
    axis.axvline(0, color=INK, linewidth=0.8)            # no difference: a release that changed nothing
    axis.set_yticks(*zip(*ticks))
right.tick_params(axis="y", labelleft=False)          # the rows are named once, on the left
left.set_xlabel("difference in p95\nmessage time (ms)")
left.set_xticks([-10_000, 0, 10_000])
left.xaxis.set_major_formatter(FuncFormatter(lambda ms, _: f"{ms:,.0f}".replace("-", "−")))   # thousands separators
right.set_xlabel("mean difference in input\ntokens per message")
right.set_xticks([-200, 0, 200])
save(fig, "paired-differences")
