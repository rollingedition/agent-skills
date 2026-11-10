import numpy as np

from lib.metrics import evaluate
from lib.recorded import embeddings
from lib.significance import compare, verdict
from lib.store import load_queries, qrels
from lib.vectors import as_run, choose_ef_search, exact_search, hnsw_index, hnsw_search, recall_against_exact

# Planned before scoring: HNSW at faiss's default efSearch, and at the setting chosen on train, each against exact.
PLANNED = 2
threshold = 0.05 / PLANNED
product_ids, product_vectors, query_ids, query_vectors = embeddings()
rows = np.isin(query_ids, load_queries("test").index)
index = hnsw_index(product_vectors, links=32)
chosen = choose_ef_search(index, query_vectors[np.isin(query_ids, load_queries("train").index)], product_vectors)
exact = exact_search(query_vectors[rows], product_vectors, 100)
exact_ndcg = evaluate(as_run(exact, query_ids[rows], product_ids), qrels("test"))["ndcg@10"]
print("planned test comparisons:", PLANNED)
print(f"p-value threshold: {threshold:.3f}")
print("efSearch chosen on train queries:", chosen)
print(f"exact ndcg@10: {exact_ndcg.mean():.3f}")

for name, ef_search in [("default", 16), ("chosen", chosen)]:
    found, _ = hnsw_search(index, query_vectors[rows], 100, ef_search)
    recall = recall_against_exact(found[:, :10], exact[:, :10])
    ndcg = evaluate(as_run(found, query_ids[rows], product_ids), qrels("test"))["ndcg@10"]
    result = compare(ndcg, exact_ndcg, confidence=1 - threshold)
    print(f"\n{name}, recall@10 against exact: {recall.mean():.3f}")
    print(f"{name}, queries with recall@10 of 0: {(recall == 0).sum()}")
    print(f"{name}, those queries:", ", ".join(load_queries().loc[query_ids[rows][recall == 0], "query"]) or "none")
    print(f"{name}, recall@100 against exact: {recall_against_exact(found, exact).mean():.3f}")
    print(f"{name}, hnsw ndcg@10: {ndcg.mean():.3f}")
    print(f"{name}, queries whose ndcg@10 changes: {result['wins'] + result['losses']}")
    print(f"{name}, permutation p: {result['permutation p']:.3f}")
    print(f"{name}, t-test p: {result['t-test p']:.3f}")
    print(f"{name}, {1 - threshold:.1%} interval: {result['ci low']:.4f} to {result['ci high']:.4f}")
    for check, passed in verdict(result, threshold).items():      # established, t-test agrees, interval agrees
        print(f"{name}, {check}: {'yes' if passed else 'no'}")
