"""Draws BM25's nDCG@10 on each test query as one bar, sorted from lowest to highest, with the mean as a dashed line. The prose rests on the count-below-mean line; the other printed lines repeat bm25-test-scores and match it."""
from lib.figures import ACCENT, INK, new_figure, save
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
run = LexicalSearch(products).run(queries, k=100)       # the same run as bm25-test-scores: top 100 per query
scores = evaluate(run, judgments).sort_values("ndcg@10")  # one row per query, lowest nDCG@10 first
ndcg = scores["ndcg@10"]
mean = ndcg.mean()

print(f"mean ndcg@10: {mean:.3f}")
print(f"median ndcg@10: {ndcg.median():.3f}")
print(f"lowest ndcg@10: {ndcg.min():.3f}")
print(f"highest ndcg@10: {ndcg.max():.3f}")
print("queries with ndcg@10 of 1:", (ndcg.round(3) == 1).sum())
print("queries below the mean:", (ndcg < mean).sum())

fig, ax = new_figure()
ax.bar(range(1, len(ndcg) + 1), ndcg.values, color=ACCENT, width=0.7, label="one query's nDCG@10")
ax.axhline(mean, color=INK, linestyle="--", linewidth=1.2, label=f"mean over {len(ndcg)} queries, {mean:.3f}")
ax.set_xlabel("test queries, sorted from lowest to highest nDCG@10")
ax.set_ylabel("nDCG@10")
ax.set_xlim(0.3, len(ndcg) + 0.7)
ax.set_ylim(0, 1.05)
ax.legend(loc="upper left", frameon=False)
save(fig, "bm25-test-query-scores")
