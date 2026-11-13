"""Builds exact search from one matrix product, then checks its top 10 against lib.semantic and faiss's IndexFlatIP. The prose's point rests on the two 'same top 10' lines, which show the hand-built search matches both."""
import faiss
import numpy as np

from lib.metrics import evaluate
from lib.recorded import embeddings
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

product_ids, product_vectors, query_ids, query_vectors = embeddings()
test = load_queries("test").index
rows = np.isin(query_ids, test)


def top_k(scores, k):
    """Column indices of the k highest scores in each row, best first."""
    # argpartition's kth is 0-based: with k - 1, the first k positions hold the k highest scores, in no order
    candidates = np.argpartition(-scores, k - 1, axis=1)[:, :k]          # the top k, in no order
    # stable sort: tied scores keep their candidate order
    order = np.argsort(-np.take_along_axis(scores, candidates, axis=1), axis=1, kind="stable")
    return np.take_along_axis(candidates, order, axis=1)


scores = query_vectors[rows] @ product_vectors.T      # one row per test query, one column per product
top = top_k(scores, 10)
print("similarities computed:", f"{scores.size:,}")
print("similarities per query:", f"{scores.shape[1]:,}")

semantic = SemanticSearch()
# two lists match only if the same products come in the same order
same = sum(list(product_ids[found]) == list(semantic.search(query_id, 10).index)
           for query_id, found in zip(query_ids[rows], top))
print("same top 10 as lib.semantic:", same, "of", rows.sum())

flat = faiss.IndexFlatIP(product_vectors.shape[1])     # faiss's exact index: inner product with every product
flat.add(product_vectors)
_, found = flat.search(query_vectors[rows], 10)
# the same products in the same order, row by row
print("same top 10 as faiss IndexFlatIP:", (found == top).all(axis=1).sum(), "of", rows.sum())
run = {query_id: list(product_ids[row]) for query_id, row in zip(query_ids[rows], top)}
print(f"ndcg@10 of the exact run: {evaluate(run, qrels('test'))['ndcg@10'].mean():.3f}")

