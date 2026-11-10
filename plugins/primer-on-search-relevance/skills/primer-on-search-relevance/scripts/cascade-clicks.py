from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, qrels

products = load_products()
judgments = qrels()[246]                                     # clear shower curtain: {product_id: grade}
rankings = {"bm25": list(LexicalSearch(products).search("clear shower curtain", k=10).index),
            "semantic": list(SemanticSearch().search(246, k=10).index)}

for name, ranking in rankings.items():
    grades = [judgments.get(product_id, 0) for product_id in ranking]
    rank = grades.index(2) + 1             # cascade: read from the top, click the first exact product, stop
    print(f"{name} grades, ranks 1 to 10: {' '.join(map(str, grades))}")
    print(f"{name} clicked rank: {rank}")
    print(f"{name} clicked product: {products.at[ranking[rank - 1], 'name']}")
    print(f"{name} exact products shown below the click: {grades[rank:].count(2)}")
