from lib.lexical import LexicalSearch
from lib.store import load_products, load_queries

products = load_products()
query = load_queries().at[246, "query"]       # a test query
lexical = LexicalSearch(products)              # BM25 over name, class, category and description

scores = lexical.search(query, k=10)           # the 10 highest scores, best first
print("query:", query)
print()
for rank, (product_id, score) in enumerate(scores.items(), start=1):
    print(f"{rank:>2}  {product_id:>5}  {score:5.2f}  {products.at[product_id, 'name'][:55]}")
