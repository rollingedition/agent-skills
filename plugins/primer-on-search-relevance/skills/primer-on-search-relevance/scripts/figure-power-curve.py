"""Draws the power the normal approximation gives against the change in nDCG@10, for the test queries and for the query count a change of 0.01 needs, on the regression set. The prose rests on the 'smallest change 30 queries detect', 'queries needed for a change of 0.01' and 'smallest change for the larger query set' lines, which are the same lines that example prints."""
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

import numpy as np
from scipy import stats

SIGNIFICANCE, POWER = 0.05, 0.80
queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])
change = evaluate(hybrid, judgments)["ndcg@10"] - evaluate(semantic, judgments)["ndcg@10"]
spread = change.std()                                     # of the per-query differences
n_test = len(change)

z = stats.norm.ppf(1 - SIGNIFICANCE / 2) + stats.norm.ppf(POWER)
n_larger = round(z ** 2 * spread ** 2 / 0.01 ** 2)        # queries a change of 0.01 needs
print(f"spread of per-query changes: {spread:.3f}")
print(f"smallest change 30 queries detect: {z * spread / np.sqrt(n_test):.3f}")
print(f"queries needed for a change of 0.01: {n_larger}")
print(f"smallest change for the larger query set: {z * spread / np.sqrt(n_larger):.3f}")

# power at a change delta with n queries: the normal approximation's chance the statistic clears the two-sided critical value
def power(delta, n):
    return stats.norm.cdf(delta * np.sqrt(n) / spread - stats.norm.ppf(1 - SIGNIFICANCE / 2))

changes = np.linspace(0, 0.06, 121)
fig, ax = new_figure(height=2.8)
ax.plot(changes, power(changes, n_test), color=ACCENT, label=f"{n_test} test queries")
ax.plot(changes, power(changes, n_larger), color=INK, marker="s", markersize=3, markevery=8, label=f"{n_larger} queries")
ax.axhline(POWER, color=MUTED, linestyle="--", label="planned power, 0.8")
ax.set_xlabel("change in nDCG@10 between the hybrid and semantic retrieval")
ax.set_ylabel("power")
ax.set_ylim(0, 1)
ax.legend(loc="lower right", frameon=False)
save(fig, "power-curve")
