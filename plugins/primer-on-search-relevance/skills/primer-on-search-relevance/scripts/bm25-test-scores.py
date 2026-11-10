from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
run = LexicalSearch(products).run(queries, k=100)       # {query_id: [product_id, ...]}
scores = evaluate(run, judgments)                        # one row per test query
scores["query"] = queries["query"]

print("test queries:", len(scores))
print(f"mean ndcg@10: {scores['ndcg@10'].mean():.3f}")
print(f"mean judged@10: {scores['judged@10'].mean():.3f}")
print(f"lowest ndcg@10: {scores['ndcg@10'].min():.3f}")
print(f"median ndcg@10: {scores['ndcg@10'].median():.3f}")
print(f"highest ndcg@10: {scores['ndcg@10'].max():.3f}")
print("queries with ndcg@10 of 1:", (scores["ndcg@10"].round(3) == 1).sum())
print()
lowest = scores.nsmallest(3, "ndcg@10")
print(lowest[["query", "ndcg@10", "judged@10"]].round(3).to_string())
print("lowest query:", lowest["query"].iloc[0])
print(f"judged@10 of the lowest query: {lowest['judged@10'].iloc[0]:.3f}")
print()
print(f"judged@10 for {queries.at[133, 'query']}: {scores.at[133, 'judged@10']:.3f}")
print("bm25 top 5 for", queries.at[133, "query"])
for product_id in run[133][:5]:
    label = LABELS.get(judgments[133].get(product_id), "unjudged")
    print(f"  {label:<10}  {products.at[product_id, 'name'][:60]}")
