from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, SemanticSearch().run(queries, k=100)])
before, after = evaluate(bm25, judgments), evaluate(hybrid, judgments)

difference = (after["ndcg@10"] - before["ndcg@10"]).round(3).sort_values()   # one value per test query
print(f"mean difference: {difference.mean():.3f}")
print(f"median difference: {difference.median():.3f}")
print("hybrid better:", (difference > 0).sum())
print("bm25 better:", (difference < 0).sum())
print("tied:", (difference == 0).sum())

print("\nhybrid's three largest losses:")
print(queries.loc[difference.index[:3], "query"].to_frame().assign(difference=difference[:3]).to_string())
largest = difference.index[-1]
print("\nlargest gain:", queries.at[largest, "query"])
print(f"its gain: {difference[largest]:.3f}")
print(f"its bm25 judged@10: {before.at[largest, 'judged@10']:.3f}")
print(f"share of the mean gain from this query: {difference[largest] / difference.sum():.3f}")

relative = after["ndcg@10"] / before["ndcg@10"] - 1                            # per-query relative gains
print(f"\nrelative gain of the means: {after['ndcg@10'].mean() / before['ndcg@10'].mean() - 1:.3f}")
print(f"mean of per-query relative gains: {relative.mean():.3f}")
print(f"its bm25 ndcg@10: {before.at[largest, 'ndcg@10']:.3f}")
print(f"its relative gain: {relative[largest]:.3f}")
print(f"mean of per-query relative gains without it: {relative.drop(largest).mean():.3f}")
