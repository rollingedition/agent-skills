"""Draws the min-max weighted sum's mean nDCG@10 on the train queries for each alpha from 0 to 1, with semantic retrieval alone as a dashed line. The prose rests on the best alpha and its nDCG@10, the nDCG@10 at each alpha, the first and last alphas above semantic retrieval alone, and the BM25-alone and semantic-alone values printed below the chart."""
from lib.blend import ALPHAS, best_alpha, candidates, scores_by_alpha, weighted_sum
from lib.figures import ACCENT, MUTED, new_figure, save
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
tables = candidates(LexicalSearch(products), SemanticSearch(), queries)
per_query = scores_by_alpha(lambda alpha: weighted_sum(tables, alpha, "min-max"), judgments)
means = per_query.mean()                                    # mean nDCG@10 over the train queries, one per alpha
best = best_alpha(per_query)

print(f"best alpha: {best:.1f}")
print(f"best ndcg@10: {means[best]:.3f}")
print(f"bm25 alone ndcg@10: {means[0.0]:.3f}")
print(f"semantic alone ndcg@10: {means[1.0]:.3f}")
for alpha in ALPHAS:
    print(f"alpha {alpha:.1f} ndcg@10: {means[alpha]:.3f}")
above = [alpha for alpha in ALPHAS if means[alpha] > means[1.0]]
print(f"first alpha above semantic alone: {above[0]:.1f}")
print(f"last alpha above semantic alone: {above[-1]:.1f}")

fig, ax = new_figure(height=2.8)
ax.plot(ALPHAS, means.values, color=ACCENT, marker="o", markersize=3.5, label="min-max weighted sum")
ax.axhline(means[1.0], color=MUTED, linestyle="--", label=f"semantic retrieval alone, {means[1.0]:.3f}")
ax.set_xticks(ALPHAS)
ax.set_xlabel("weight on semantic retrieval, alpha (0 is BM25 alone, 1 is semantic alone)")
ax.set_ylabel("mean nDCG@10, train queries")
ax.legend(loc="lower right", frameon=False)
save(fig, "blend-weight-curve")
