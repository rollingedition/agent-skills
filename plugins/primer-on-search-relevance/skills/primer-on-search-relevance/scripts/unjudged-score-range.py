import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(products).run(queries, k=100),
        "semantic 128": SemanticSearch(dims=128).run(queries, k=100),
        "semantic": SemanticSearch().run(queries, k=100)}


def unjudged(run):
    """(query_id, product_id) pairs in a run's top 10 that nobody judged."""
    return {(query_id, product_id) for query_id in judgments for product_id in run[query_id][:10]
            if product_id not in judgments[query_id]}


def score(run, exact=()):
    """Mean nDCG@10 with the given unjudged pairs judged exact, for every run alike: the ideal moves too."""
    scenario = {query_id: dict(grades) for query_id, grades in judgments.items()}
    for query_id, product_id in exact:
        scenario[query_id][product_id] = 2
    return np.mean([ndcg_at_k(run[query_id], scenario[query_id], 10) for query_id in scenario])


for name in ["bm25", "semantic 128"]:
    print(f"unjudged pairs in the top 10, {name}: {len(unjudged(runs[name]))}")
scenarios = {"as judged": set(), **{f"{name}'s unjudged exact": unjudged(runs[name]) for name in runs}}
scores = {(scenario, name): score(run, exact) for scenario, exact in scenarios.items() for name, run in runs.items()}
for scenario, name in [("as judged", "bm25"), ("as judged", "semantic 128"), ("bm25's unjudged exact", "bm25"),
                       ("bm25's unjudged exact", "semantic 128"), ("bm25's unjudged exact", "semantic"),
                       ("semantic 128's unjudged exact", "bm25"), ("semantic 128's unjudged exact", "semantic 128")]:
    print(f"{scenario}, {name}: {scores[scenario, name]:.3f}")
for candidate in ["semantic 128", "semantic"]:
    leaders = {scores[s, candidate] > scores[s, "bm25"] for s in scenarios}
    print(f"leader changes, {candidate} against bm25:", "yes" if len(leaders) > 1 else "no")
print("pairs to judge, semantic 128 against bm25:", len(unjudged(runs["bm25"]) | unjudged(runs["semantic 128"])))
