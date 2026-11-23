"""Draws each query's share of exact, partial and irrelevant judgments as one stacked column, queries sorted by exact share.
The prose's point rests on the `queries drawn`, `queries where partial is the largest share` and
`queries with an irrelevant share above 0.2` lines, which the figure prints from the same judgments."""
import pandas as pd

from matplotlib.colors import to_rgba

from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.store import load_labels

labels = load_labels()
counts = pd.crosstab(labels["query_id"], labels["label"])[["exact", "partial", "irrelevant"]]
shares = counts.div(counts.sum(axis=1), axis=0).sort_values("exact")

print(f"queries drawn: {len(shares)}")
print(f"queries where partial is the largest share: {(shares.idxmax(axis=1) == 'partial').sum()}")
print(f"queries with an irrelevant share above 0.2: {(shares['irrelevant'] > 0.2).sum()}")

fig, ax = new_figure(height=3.4)
columns = range(len(shares))
bottom = pd.Series(0.0, index=shares.index)
# exact solid, partial light with dots, irrelevant hatched: told apart by pattern as well as by colour
for label, color, hatch in [("exact", ACCENT, None), ("partial", to_rgba(MUTED, 0.3), "."),
                            ("irrelevant", "none", "///")]:
    ax.bar(columns, shares[label], bottom=bottom, width=0.85, color=color, edgecolor=INK if hatch else "none",
           hatch=hatch, linewidth=0, label=label)
    bottom = bottom + shares[label]
ax.set_xticks([])
ax.set_xlim(-0.6, len(shares) - 0.4)
ax.set_ylim(0, 1)
ax.set_ylabel("share of the query's judgments")
ax.set_xlabel(f"each column is one query, sorted by its exact share ({len(shares)} queries)")
ax.legend(title=None, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
save(fig, "label-mix-per-query")
