from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
bm25 = evaluate(LexicalSearch(products).run(queries, k=100), judgments)
semantic = evaluate(SemanticSearch().run(queries, k=100), judgments)

for name, scores in [("bm25", bm25), ("semantic", semantic)]:
    print(f"{name} ndcg@10: {scores['ndcg@10'].mean():.3f}")
    print(f"{name} judged@10: {scores['judged@10'].mean():.3f}")

difference = (semantic["ndcg@10"] - bm25["ndcg@10"]).round(3)    # per test query
print("semantic better:", (difference > 0).sum())
print("bm25 better:", (difference < 0).sum())
print("tied:", (difference == 0).sum())
sized = queries["query"].str.contains(r"\d+\s*(?:inch|in\b|\"|'')")             # a size in inches
print("test queries with a size in inches:", sized.sum())
print("of those, bm25 better:", (difference[sized] < 0).sum())
print()
print("queries where bm25 is better:")
print(queries.loc[difference[difference < 0].index, "query"].to_string())
