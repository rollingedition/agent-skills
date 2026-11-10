from lib.metrics import ndcg_at_k
from lib.recorded import manifest
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}

products = load_products()
query_id = 246
judgments = qrels()[query_id]
semantic = SemanticSearch()                  # recorded embeddings of every product and query

print("embedding model:", manifest("embeddings")["model"])
print("dimensions:", semantic.products.shape[1])
print("query:", load_queries().at[query_id, "query"])
print()
similarity = semantic.search(query_id, k=10)  # the query's embedding against every product's
for rank, (product_id, score) in enumerate(similarity.items(), start=1):
    label = LABELS.get(judgments.get(product_id), "unjudged")
    print(f"{rank:>2}  {score:.3f}  {label:<10}  {products.at[product_id, 'name'][:50]}")

print()
labels = [LABELS.get(judgments.get(product_id), "unjudged") for product_id in similarity.index]
for label in ["exact", "partial", "irrelevant", "unjudged"]:
    print(f"{label} in the top 10: {labels.count(label)}")
print(f"similarity spread in the top 10: {similarity.max() - similarity.min():.3f}")
print(f"ndcg@10: {ndcg_at_k(list(similarity.index), judgments, 10):.3f}")
