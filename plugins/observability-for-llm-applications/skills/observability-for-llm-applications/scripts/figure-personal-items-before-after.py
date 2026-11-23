"""How many spans of baseline day 1 hold each kind of personal item, before and after redaction, in two panels: the
synthetic users' items, which redaction removes, and MASSIVE's personal-looking values, which it cannot tell apart from
other words and so leaves. The figure's point rests on the printed counts: the top panel's bars drop to zero, and the
bottom panel's stay where they were."""
import lib  # lib first: threads and seeds are fixed before anything else

from lib.figures import ACCENT, MUTED, RULE, new_figure, save
from lib.report import fmt_int
from lib.scan import SLOT_LABELS, SYNTHETIC, assistant_rows, captured_day, spans_holding

DAY = "2026-12-08"
rows = assistant_rows(DAY) + captured_day(DAY)  # the day's spans, capture on for the package's
cleaned = assistant_rows(DAY, redact=True) + captured_day(DAY, redact=True)  # the same, through the processor
before, after = spans_holding(rows), spans_holding(cleaned)
for kind in SYNTHETIC + tuple(f"slot:{label}" for label in SLOT_LABELS):
    label = kind.replace("slot:", "") + (" slot" if kind.startswith("slot:") else "")
    print(f"{label} spans before redaction: {fmt_int(before[kind])}")
    print(f"{label} spans after redaction: {fmt_int(after[kind])}")
assert all(after[kind] == 0 for kind in SYNTHETIC)  # the synthetic users' spans are all clean after redaction
assert all(after[f"slot:{label}"] == before[f"slot:{label}"] for label in SLOT_LABELS)  # measured, not moved

top_kinds = list(SYNTHETIC)
bottom_kinds = [f"slot:{label}" for label in SLOT_LABELS]
fig, (top, bottom) = new_figure(rows=2, height=5.6, sharex=False)  # one x scale per panel: 200 and 55 do not share one


def panel(ax, kinds, title):
    """Before and after, as horizontal bars, with each count printed at the bar's end."""
    ys = list(range(len(kinds)))
    xmax = max(before[kind] for kind in kinds) * 1.3 or 1  # room for the count and the legend
    ax.barh([y - 0.18 for y in ys], [before[kind] for kind in kinds], height=0.34, color=MUTED,
            label="before redaction")
    ax.barh([y + 0.18 for y in ys], [after[kind] for kind in kinds], height=0.34, color=RULE, edgecolor=ACCENT,
            hatch="////", label="after redaction")  # hatched, so the two bars differ by pattern as well as colour
    for y, kind in zip(ys, kinds):
        ax.text(before[kind] + xmax * 0.01, y - 0.18, str(before[kind]), va="center", fontsize=7.5)
        ax.text(after[kind] + xmax * 0.01, y + 0.18, str(after[kind]), va="center", fontsize=7.5)
    ax.set_yticks(ys, [kind.replace("slot:", "") for kind in kinds])
    ax.invert_yaxis()
    ax.set_xlim(0, xmax)
    ax.set_title(title, loc="left", fontsize=9)


panel(top, top_kinds, "Synthetic users' items: redaction removes them")
panel(bottom, bottom_kinds, "MASSIVE's personal-looking values: counted, not removed")
bottom.set_xlabel("spans holding each kind, baseline day 1")
top.legend(loc="lower right", fontsize=7.5)
save(fig, "personal-items-before-after")
