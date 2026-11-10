import math

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


def dcg(grades, k):
    """Each grade divided by log2 of its position plus one, added up over the top k."""
    return sum(grade / math.log2(position + 1) for position, grade in enumerate(grades[:k], start=1))


def ndcg(ranking, judgments, k=10):
    """DCG of the ranking over DCG of the best order of every judged product (unjudged counts as 0)."""
    ideal = dcg(sorted(judgments.values(), reverse=True), k)
    return dcg([judgments.get(product_id, 0) for product_id in ranking], k) / ideal


queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"bm25": bm25, "semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}

gaps = [abs(ndcg(run[query_id], judgments[query_id]) - ndcg_at_k(run[query_id], judgments[query_id], 10))
        for run in runs.values() for query_id in judgments]
print("rankings checked:", len(gaps))
print(f"largest difference from lib.metrics: {max(gaps):.3f}")

ranking, per_query = bm25[461], judgments[461]                     # luau string lights
print()
print("query:", queries.at[461, "query"])
print("grades in the top 10:", [per_query.get(product_id, 0) for product_id in ranking[:10]])
print("best possible grades:", sorted(per_query.values(), reverse=True)[:10])
print("exact products judged:", sum(grade == 2 for grade in per_query.values()))
print("exact in the top 10:", sum(per_query.get(product_id, 0) == 2 for product_id in ranking[:10]))
print(f"ndcg@10: {ndcg(ranking, per_query):.3f}")
