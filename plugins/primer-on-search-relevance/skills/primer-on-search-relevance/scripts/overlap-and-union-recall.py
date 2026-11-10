import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import recall_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)

shared = [len(set(bm25[query_id][:10]) & set(semantic[query_id][:10])) for query_id in queries.index]
print(f"products in both top 10s, mean: {np.mean(shared):.1f}")


def share_retrieved(run):
    """The share of each query's exact products that the run's list holds, averaged over queries."""
    shares = [recall_at_k(ranking, judgments[query_id], k=len(ranking)) for query_id, ranking in run.items()]
    return np.mean(shares)


for depth in [100, 20]:
    lists = {"bm25": {query_id: ranking[:depth] for query_id, ranking in bm25.items()},
             "semantic": {query_id: ranking[:depth] for query_id, ranking in semantic.items()}}
    lists["union"] = {query_id: list(dict.fromkeys(lists["bm25"][query_id] + lists["semantic"][query_id]))
                      for query_id in queries.index}
    for name, run in lists.items():
        print(f"{name} top {depth}, share of exact products retrieved: {share_retrieved(run):.3f}")
