from lib.blend import weighted_rrf
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries

alpha, k = 0.75, 60                                          # an illustrative weight; tuning picks one on train
products, queries = load_products(), load_queries("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
query_id = 36                                                # laundry basket with wheels


def part(ranking, weight, product_id):
    """weight / (k + rank) from one ranking, or 0 when the product isn't in it."""
    return weight / (k + ranking.index(product_id) + 1) if product_id in ranking else 0.0


candidates = dict.fromkeys(bm25[query_id] + semantic[query_id])   # the union, in the order first seen
score = {product_id: part(bm25[query_id], 1 - alpha, product_id) + part(semantic[query_id], alpha, product_id)
         for product_id in candidates}
ranking = sorted(score, key=lambda product_id: (-score[product_id], product_id))   # ties by product_id
first = ranking[0]
print("first product:", products.at[first, "name"])
print("its bm25 rank:", bm25[query_id].index(first) + 1)
print("its semantic rank:", semantic[query_id].index(first) + 1)
print(f"its weighted rrf score: {score[first]:.5f}")
library = weighted_rrf(bm25, semantic, alpha)[query_id]          # the top 100
matches = sum(mine == theirs for mine, theirs in zip(ranking, library))
print(f"places that match lib.blend.weighted_rrf: {matches} of {len(library)}")
