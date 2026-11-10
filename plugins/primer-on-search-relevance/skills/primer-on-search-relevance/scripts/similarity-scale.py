import numpy as np

from lib.recorded import embeddings
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

product_ids, product_vectors, query_ids, query_vectors = embeddings()
test = load_queries("test")
rows = np.isin(query_ids, test.index)
similarity = np.sort(query_vectors[rows] @ product_vectors.T, axis=1)[:, ::-1]   # best first, per query
queries = test.loc[query_ids[rows], "query"].to_numpy()

weakest = similarity[:, 0].argmin()                    # the query whose best match is least similar
strongest = similarity[:, 9].argmax()                  # the query whose 10th match is most similar
print("first query, lowest best similarity:", queries[weakest])
print(f"its best similarity: {similarity[weakest, 0]:.3f}")
judgments = qrels()[query_ids[rows][weakest]]
top = SemanticSearch().search(query_ids[rows][weakest], k=10).index
print("exact products in its top 10:", sum(judgments.get(product_id) == 2 for product_id in top))
print("second query, highest 10th similarity:", queries[strongest])
print(f"its 10th similarity: {similarity[strongest, 9]:.3f}")

cutoff = 0.5
print()
print(f"products above {cutoff} for the first query:", (similarity[weakest] > cutoff).sum())
print(f"products above {cutoff} for the second query:", (similarity[strongest] > cutoff).sum())
print(f"test queries with no product above {cutoff}:", (similarity[:, 0] <= cutoff).sum())
