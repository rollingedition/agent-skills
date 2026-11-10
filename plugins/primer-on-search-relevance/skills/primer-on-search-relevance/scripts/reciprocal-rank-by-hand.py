import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


def reciprocal_rank(ranking, judgments, relevant=2):
    """1 / the position of the first relevant product, or 0 if the ranking has none."""
    for position, product_id in enumerate(ranking, start=1):
        if judgments.get(product_id, 0) >= relevant:
            return 1 / position
    return 0.0


queries, judgments = load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(load_products()).run(queries, k=100), "semantic": SemanticSearch().run(queries, k=100)}

ranking = runs["bm25"][246]                                        # clear shower curtain
print(f"rr, exact counts as relevant: {reciprocal_rank(ranking, judgments[246]):.3f}")
print(f"rr, partial or better counts: {reciprocal_rank(ranking, judgments[246], relevant=1):.3f}")

for name, run in runs.items():
    rr = pd.Series({query_id: reciprocal_rank(run[query_id], judgments[query_id]) for query_id in judgments})
    print(f"{name} mrr: {rr.mean():.3f}")
    print(f"{name} mrr from lib.metrics: {evaluate(run, judgments)['rr'].mean():.3f}")
    print(f"{name} queries with rr of 1:", (rr == 1).sum())
