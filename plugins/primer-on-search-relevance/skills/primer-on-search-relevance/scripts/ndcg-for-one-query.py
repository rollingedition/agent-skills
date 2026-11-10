import math

from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.store import load_products, load_queries, qrels

products = load_products()
query = load_queries().at[246, "query"]                      # "clear shower curtain"
judgments = qrels("test")[246]                                # {product_id: grade}
ranking = list(LexicalSearch(products).search(query, k=10).index)

grades = [judgments.get(product_id, 0) for product_id in ranking]     # unjudged counts as 0
dcg = sum(grade / math.log2(position + 1) for position, grade in enumerate(grades, start=1))
best = sorted(judgments.values(), reverse=True)[:10]                  # the best possible top 10
ideal = sum(grade / math.log2(position + 1) for position, grade in enumerate(best, start=1))

print("grades:", grades)
print("best grades:", best)
print(f"dcg@10: {dcg:.3f}")
print(f"ideal dcg@10: {ideal:.3f}")
print(f"ndcg@10: {dcg / ideal:.3f}")
print(f"ndcg@10 from lib.metrics: {ndcg_at_k(ranking, judgments, 10):.3f}")
