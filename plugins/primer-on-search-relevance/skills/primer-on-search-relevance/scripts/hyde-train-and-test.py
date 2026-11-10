import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.queries import THRESHOLD, report_planned
from lib.recorded import llm_rewrites
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

table, _, hypothetical_vectors = llm_rewrites()
hypothetical, vectors = table.set_index("query_id")["hypothetical"], dict(zip(table["query_id"], hypothetical_vectors))
bm25, semantic = LexicalSearch(load_products()), SemanticSearch()


def hyde(query_id):
    """Gao et al.'s average of the hypothetical product's embedding and the query's, scaled back to length 1."""
    average = (vectors[query_id] + semantic.query_vectors[query_id]) / 2
    return average / np.linalg.norm(average)


def runs(queries):
    ids, typed = queries.index, queries["query"]
    return {"semantic": semantic.run(queries),
            "hypothetical alone": {query_id: list(semantic.search_vector(vectors[query_id]).index) for query_id in ids},
            "hyde": {query_id: list(semantic.search_vector(hyde(query_id)).index) for query_id in ids},
            "bm25": bm25.run(queries),
            "bm25, hypothetical alone": bm25.run(queries.assign(query=ids.map(hypothetical))),
            "bm25, query five times plus hypothetical": bm25.run(queries.assign(           # query2doc's weighting
                query=[" ".join([typed[query_id]] * 5 + [hypothetical[query_id]]) for query_id in ids]))}


train = {name: evaluate(run, qrels("train")) for name, run in runs(load_queries("train")).items()}
for name, frame in train.items():
    print(f"train ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
    print(f"train judged@10 {name}: {frame['judged@10'].mean():.3f}")
change = (train["hypothetical alone"]["ndcg@10"] - train["semantic"]["ndcg@10"]).round(3)    # for choosing, not evidence
print(f"train queries better, worse, hypothetical alone: {(change > 0).sum()}, {(change < 0).sum()}")

print(f"\nthe planned test comparison, threshold {THRESHOLD:.2f}:")
test = {name: evaluate(run, qrels("test")) for name, run in runs(load_queries("test")).items()
        if name in ["semantic", "hyde"]}
for name, frame in test.items():
    print(f"test judged@10 {name}: {frame['judged@10'].mean():.3f}")
report_planned("hyde, semantic", test["hyde"]["ndcg@10"], test["semantic"]["ndcg@10"])
