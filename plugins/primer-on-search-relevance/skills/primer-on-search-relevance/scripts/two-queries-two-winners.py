from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}
products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=10)
semantic = SemanticSearch().run(queries, k=10)
text = product_text(products)
print("products containing 7qt:", text.str.contains(r"\b7qt\b", case=False).sum())
print("products containing 7 qt:", text.str.contains(r"\b7 qt\b", case=False).sum())

for query_id in [432, 62]:                                   # butcher block island, 7qt slow cooker
    query = queries.at[query_id, "query"]
    for name, run in [("bm25", bm25), ("semantic", semantic)]:
        grades = [judgments[query_id].get(product_id) for product_id in run[query_id]]
        print()
        print(f"exact in {name} top 10 for {query}: {grades.count(2)}")
        for product_id, grade in list(zip(run[query_id], grades))[:5]:
            print(f"  {LABELS.get(grade, 'unjudged'):<10}  {products.at[product_id, 'name'][:55]}")
