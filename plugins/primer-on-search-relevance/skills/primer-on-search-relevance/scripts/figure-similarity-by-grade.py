"""Draws the cosine similarity of every judged test pair, one line per grade: exact, partial and irrelevant. The prose rests on the pair counts, the median similarity by grade, and the shares above and below 0.5 that a cutoff there would keep or drop."""
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.recorded import embeddings
from lib.store import load_labels, load_queries

import numpy as np
import pandas as pd

product_ids, product_vectors, query_ids, query_vectors = embeddings()   # unit length, so a dot product is a cosine
test = load_queries("test")
labels = load_labels()
labels = labels[labels["query_id"].isin(test.index)]                    # judged pairs for the test queries only

product_row = pd.Series(range(len(product_ids)), index=product_ids)     # product_id -> row in product_vectors
query_row = pd.Series(range(len(query_ids)), index=query_ids)
pairs = labels[labels["product_id"].isin(product_row.index) & labels["query_id"].isin(query_row.index)]
q = query_vectors[query_row[pairs["query_id"]].to_numpy()]
p = product_vectors[product_row[pairs["product_id"]].to_numpy()]
pairs = pairs.assign(similarity=np.einsum("ij,ij->i", q, p))

fig, ax = new_figure()
edges = np.linspace(0, 1, 41)                                           # 0.025 wide, across the whole cosine range from 0 to 1
styles = (("exact", ACCENT, "-"), ("partial", INK, ":"), ("irrelevant", MUTED, "--"))
for label, color, style in styles:
    s = pairs.loc[pairs["label"] == label, "similarity"]
    counts, _ = np.histogram(s, bins=edges)
    share = counts / counts.sum()                                       # each grade's shape, so unequal counts compare
    print(f"pairs, {label}: {len(s)}")
    print(f"median similarity, {label}: {s.median():.3f}")
    ax.stairs(share, edges, color=color, linestyle=style, linewidth=1.6, label=f"{label} pairs ({len(s)})")

exact = pairs.loc[pairs["label"] == "exact", "similarity"]
print(f"share of exact pairs below 0.5: {(exact < 0.5).mean():.3f}")
for label in ("partial", "irrelevant"):
    s = pairs.loc[pairs["label"] == label, "similarity"]
    print(f"share of {label} pairs above 0.5: {(s > 0.5).mean():.3f}")

ax.set_xlabel("cosine similarity between query and product vectors")
ax.set_ylabel("share of pairs in each grade")
ax.set_xlim(0, 1)
ax.set_ylim(bottom=0)
ax.legend(loc="upper left", frameon=False)
save(fig, "similarity-by-grade")
