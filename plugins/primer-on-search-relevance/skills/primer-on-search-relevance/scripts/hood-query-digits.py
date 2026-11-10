from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}
products = load_products()
query_id = 482
query = load_queries().at[query_id, "query"]
judgments = qrels()[query_id]
# The width sits in the attributes column, which the embeddings never saw: product_text leaves it out.
width = products["attributes"].str.extract(r"\bwidth: ([\d.]+)", expand=False).astype(float)

semantic = SemanticSearch().search(query_id, k=10).index
bm25 = LexicalSearch(products).search(query, k=10).index
print("query:", query)
print("     judgment   width  name")
for rank, product_id in enumerate(semantic, start=1):
    label = LABELS.get(judgments.get(product_id), "unjudged")
    print(f"{rank:>2}   {label:<10} {width[product_id]:>5g}  {products.at[product_id, 'name'][:50]}")

print()
for name, top in [("semantic", semantic), ("bm25", bm25)]:
    print(f"{name}, width 48 in the top 10:", (width[top] == 48).sum())
    print(f"{name}, exact in the top 10:", sum(judgments.get(product_id) == 2 for product_id in top))
