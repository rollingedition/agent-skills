"""Reads the top 10 of BM25 and of semantic retrieval for `clear shower curtain` as a cascade of clicks, which stops at
the first exact product. The prose's point rests on the `clicked rank` lines and on the `exact products shown below the
click` lines."""
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, qrels

products = load_products()
judgments = qrels()[246]                                     # clear shower curtain: {product_id: grade}
# search returns scores indexed by product_id, so .index is the ranking; semantic search takes the query's id, 246
rankings = {"bm25": list(LexicalSearch(products).search("clear shower curtain", k=10).index),
            "semantic": list(SemanticSearch().search(246, k=10).index)}

for name, ranking in rankings.items():
    grades = [judgments.get(product_id, 0) for product_id in ranking]     # an unjudged product counts as grade 0
    rank = grades.index(2) + 1             # cascade: read from the top, click the first exact product, stop
    print(f"{name} grades, ranks 1 to 10: {' '.join(map(str, grades))}")
    print(f"{name} clicked rank: {rank}")
    # rank counts from 1 and the list from 0, so the clicked product sits at index rank - 1
    print(f"{name} clicked product: {products.at[ranking[rank - 1], 'name']}")
    # grades[rank:] starts just after the click, since rank is the clicked product's position counted from 1
    print(f"{name} exact products shown below the click: {grades[rank:].count(2)}")
