from sklearn.metrics import ndcg_score

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


def sklearn_ndcg(ranking, judgments, k=10):
    """One row for one query: every judged product, plus any retrieved product nobody judged."""
    products = list(dict.fromkeys([*judgments, *ranking]))
    position = {product_id: i for i, product_id in enumerate(ranking)}
    grades = [[judgments.get(product_id, 0) for product_id in products]]
    scores = [[-position.get(product_id, len(ranking)) for product_id in products]]  # not retrieved: below all
    return ndcg_score(grades, scores, k=k)


queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"bm25": bm25, "semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}

top = bm25[246][:10]                                                # clear shower curtain
naive = ndcg_score([[judgments[246].get(product_id, 0) for product_id in top]], [list(range(10, 0, -1))], k=10)
print(f"ndcg@10, only the top 10 passed: {naive:.3f}")
print(f"ndcg@10 from lib.metrics: {ndcg_at_k(top, judgments[246], 10):.3f}")
print(f"ndcg@10, every judged product passed: {sklearn_ndcg(top, judgments[246]):.3f}")

gaps = [abs(sklearn_ndcg(run[query_id], judgments[query_id]) - ndcg_at_k(run[query_id], judgments[query_id], 10))
        for run in runs.values() for query_id in judgments]
print("rankings compared:", len(gaps))
print(f"largest difference: {max(gaps):.3f}")

short = bm25[246][:5]                                               # a ranking shorter than k
print(f"5-product ranking, lib.metrics: {ndcg_at_k(short, judgments[246], 10):.3f}")
print(f"5-product ranking, scikit-learn: {sklearn_ndcg(short, judgments[246]):.3f}")
