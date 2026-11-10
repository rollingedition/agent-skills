from lib.lexical import LexicalSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}

products = load_products()
query_id = 246
query = load_queries().at[query_id, "query"]
judgments = qrels()[query_id]                        # {product_id: grade} for this query

top = LexicalSearch(products).search(query, k=10).index
results = [LABELS.get(judgments.get(product_id), "unjudged") for product_id in top]
print("query:", query)
print()
for rank, (product_id, label) in enumerate(zip(top, results), start=1):
    print(f"{rank:>2}  {label:<10}  {products.at[product_id, 'name'][:55]}")

print()
for label in ["exact", "partial", "irrelevant", "unjudged"]:
    print(f"{label} in the top 10: {results.count(label)}")
print("products judged for this query:", len(judgments))
print("exact products judged for this query:", sum(grade == 2 for grade in judgments.values()))
