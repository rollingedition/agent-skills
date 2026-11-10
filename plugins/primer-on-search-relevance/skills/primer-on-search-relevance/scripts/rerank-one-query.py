import re

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.recorded import cross_encoder_scores
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}

products = load_products()
query_id = 406
query = load_queries().at[query_id, "query"]
judgments = qrels()[query_id]
recorded = cross_encoder_scores()
score = recorded[recorded["query_id"] == query_id].set_index("product_id")["score"]

bm25 = {query_id: list(LexicalSearch(products).search(query, k=100).index)}
semantic = {query_id: list(SemanticSearch().search(query_id, k=100).index)}
hybrid = reciprocal_rank_fusion([bm25, semantic])[query_id]
reranked = sorted(hybrid[:50], key=score.get, reverse=True) + hybrid[50:]

print("query:", query)
for name, ranking in [("hybrid", hybrid), ("reranked", reranked)]:
    first_exact = next(rank for rank, product_id in enumerate(ranking, start=1) if judgments.get(product_id) == 2)
    print()
    print(f"{name} ndcg@10: {ndcg_at_k(ranking, judgments, 10):.3f}")
    print(f"{name} rank of the first exact product: {first_exact}")
    for product_id in ranking[:5]:
        label = LABELS.get(judgments.get(product_id), "unjudged")
        print(f"  {score[product_id]:.2f}  {label:<10}  {products.at[product_id, 'name']}")


exact = next(product_id for product_id in hybrid if judgments.get(product_id) == 2)
words = set(re.findall(r"\w+", product_text(products).at[exact].lower()))   # name, class, category, description
print()
print("hybrid's first exact product:", products.at[exact, "name"])
print("its text says ice or water:", "yes" if {"ice", "water"} & words else "no")
