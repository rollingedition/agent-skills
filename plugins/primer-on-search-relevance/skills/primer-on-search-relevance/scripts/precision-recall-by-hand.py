"""Counts the exact products in BM25's top 10 for one query, computes precision and recall by hand, and checks them against lib.metrics, then finds the best score each test query could reach. The prose's point rests on the "exact in the top 10" and "exact products judged" lines, and on the ceiling lines after the blank line."""
import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import precision_at_k, recall_at_k
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
ranking = list(LexicalSearch(load_products()).search(queries.at[246, "query"], k=10).index)  # clear shower curtain
# grade 2 is exact; a product the judges never graded is absent from this dict, so it is not exact
exact = {product_id for product_id, grade in judgments[246].items() if grade == 2}

found = sum(product_id in exact for product_id in ranking[:10])
print("exact in the top 10:", found)
print("exact products judged:", len(exact))
print(f"precision@10 by hand: {found / 10:.3f}")
print(f"recall@10 by hand: {found / len(exact):.3f}")
print(f"precision@10 from lib.metrics: {precision_at_k(ranking, judgments[246], 10):.3f}")
print(f"recall@10 from lib.metrics: {recall_at_k(ranking, judgments[246], 10):.3f}")

# the best any ranking can do: a top 10 that holds as many exact products as the query has
exact_counts = pd.Series({query_id: sum(grade == 2 for grade in per_query.values())
                          for query_id, per_query in judgments.items()})
# a top 10 can hold at most 10 exact products, and no more than the query has
best_precision = exact_counts.clip(upper=10) / 10
# only 10 results are shown, so at most 10 of a query's exact products can be retrieved
best_recall = exact_counts.clip(upper=10) / exact_counts
print()
print("queries where precision@10 can't reach 1:", (best_precision < 1).sum())
print("fewest exact products for a query:", exact_counts.min())
print("queries with that few:", (exact_counts == exact_counts.min()).sum())
print(f"best precision@10 for those queries: {best_precision.min():.3f}")
print("queries where recall@10 can't reach 1:", (best_recall < 1).sum())
most = exact_counts.idxmax()
print("query with the most exact products:", queries.at[most, "query"])
print("its exact products:", exact_counts[most])
print(f"its best recall@10: {best_recall[most]:.3f}")
