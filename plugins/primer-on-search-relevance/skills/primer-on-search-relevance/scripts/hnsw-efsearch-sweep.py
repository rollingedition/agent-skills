import faiss
import numpy as np

from lib.recorded import embeddings
from lib.store import load_products, load_queries
from lib.vectors import EF_SEARCH_GRID, WORST_RECALL, exact_search, hnsw_index, hnsw_search, recall_against_exact

product_ids, product_vectors, query_ids, query_vectors = embeddings()
names = load_products().loc[product_ids, "name"].str[:36].to_numpy()   # by row number, cut to 36 characters
rows = np.isin(query_ids, load_queries("train").index)                 # tune on train queries only
queries = load_queries().loc[query_ids[rows], "query"].to_numpy()

index = hnsw_index(product_vectors, links=32)          # M = 32, and faiss's default efConstruction of 40
levels = faiss.vector_to_array(index.hnsw.levels)      # how many layers each product reaches
for layer in range(1, levels.max() + 1):
    print(f"products in layer {layer}: {(levels >= layer).sum():,}")

exact = exact_search(query_vectors[rows], product_vectors, 10)
print("\nefSearch  mean recall@10  worst  queries at 0  similarities per query")
sweep = {}
for ef_search in EF_SEARCH_GRID:
    found, similarities = hnsw_search(index, query_vectors[rows], 10, ef_search)
    recall = recall_against_exact(found, exact)
    sweep[ef_search] = (recall, similarities)
    print(f"{ef_search:>8}  {recall.mean():>14.3f}  {recall.min():>5.1f}  {(recall == 0).sum():>12}  {similarities:>22.0f}")

recall, similarities = sweep[16]                       # faiss's default
print(f"\nefSearch 16, recall@10 against exact: {recall.mean():.3f}")
print(f"efSearch 16, similarities computed per query: {similarities:.0f}")
print(f"efSearch 16, train queries with recall@10 of 0: {(recall == 0).sum()}")
print("efSearch 16, those queries:", ", ".join(queries[recall == 0]))
print("smallest efSearch with no query at 0:", min(ef for ef, (r, _) in sweep.items() if r.min() > 0))
chosen = min(ef for ef, (r, _) in sweep.items() if r.min() >= WORST_RECALL)
print(f"smallest efSearch with every query at {WORST_RECALL} or more:", chosen)
print(f"chosen efSearch, recall@10 against exact: {sweep[chosen][0].mean():.3f}")
print(f"chosen efSearch, similarities computed per query: {sweep[chosen][1]:.0f}\n")

found, _ = hnsw_search(index, query_vectors[rows], 3, 16)
row = list(queries).index("foutains with brick look")
for rank, (approximate, nearest) in enumerate(zip(found[row], exact[row]), start=1):
    print(f"{rank}  hnsw: {names[approximate]:<36}  exact: {names[nearest]}")
