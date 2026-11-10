import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
bm25_scores, semantic_scores = evaluate(bm25, judgments)["ndcg@10"], evaluate(semantic, judgments)["ndcg@10"]

print("train queries:", len(queries))
print(f"bm25 ndcg@10: {bm25_scores.mean():.3f}")
print(f"semantic ndcg@10: {semantic_scores.mean():.3f}")
lead = (bm25_scores - semantic_scores).round(3)              # per train query; above 0 means BM25 wins
print("bm25 better:", (lead > 0).sum())
print("semantic better:", (lead < 0).sum())
print("tied:", (lead == 0).sum())
print(f"better of the two, chosen per query: {np.maximum(bm25_scores, semantic_scores).mean():.3f}")
has_digit = queries["query"].str.contains(r"\d")
print("queries with a digit:", has_digit.sum())
print("queries with a digit, bm25 better:", (lead[has_digit] > 0).sum())
print()
print("queries where bm25 leads by 0.1 or more:", (lead >= 0.1).sum())
print(queries.loc[lead[lead >= 0.1].index, "query"].to_string())
