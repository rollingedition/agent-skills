"""Draws the candidates for laundry basket with wheels twice, each retriever's scores on one axis: raw, then after min-max scaling. The prose rests on the two raw ranges and the two scaled ranges printed below the chart."""
import numpy as np

from lib.blend import candidates, min_max
from lib.figures import ACCENT, INK, new_figure, save
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries

products, queries = load_products(), load_queries("train")
tables = candidates(LexicalSearch(products), SemanticSearch(), queries)
table = tables[36]                                          # laundry basket with wheels
bm25, similarity = table["bm25"], table["similarity"]

print("candidates for laundry basket with wheels:", len(table))
print(f"bm25 range: {bm25.min():.3f} to {bm25.max():.3f}")
print(f"similarity range: {similarity.min():.3f} to {similarity.max():.3f}")
print(f"after min-max, bm25 range: {min_max(bm25).min():.3f} to {min_max(bm25).max():.3f}")
print(f"after min-max, similarity range: {min_max(similarity).min():.3f} to {min_max(similarity).max():.3f}")

rng = np.random.default_rng(0)                              # fixed jitter, so the dots fall the same way every run
fig, (raw_ax, scaled_ax) = new_figure(rows=2, height=4.2, sharex=False)
for ax, (bm25_scores, similarity_scores), xlabel in [
    (raw_ax, (bm25, similarity), "raw score, one dot per candidate"),
    (scaled_ax, (min_max(bm25), min_max(similarity)), "score after min-max scaling, one dot per candidate"),
]:
    ax.scatter(bm25_scores, 1 + rng.uniform(-0.12, 0.12, len(bm25_scores)), s=12, color=ACCENT)
    ax.scatter(similarity_scores, rng.uniform(-0.12, 0.12, len(similarity_scores)), s=12, color=INK)
    ax.set_yticks([0, 1], ["similarity", "BM25"])
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlabel(xlabel)
save(fig, "score-scales")
