"""Builds judged@10 by hand for BM25's test rankings, checks it against lib.metrics, and lists where BM25's unjudged
products sit in the top 10s. The prose's point rests on the `unjudged products in the top 10s` line and on the
`irrelevant judgments` line for pull out sleeper loveseat."""
import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
# 100 products per query are kept; this example reads only the top 10 of each
run = LexicalSearch(products).run(queries, k=100)


def judged_at_k(ranking, judged, k):
    """The share of the top k that has a judgment of any grade."""
    return sum(product_id in judged for product_id in ranking[:k]) / k


rows = []
for query_id, ranking in run.items():
    unjudged = [product_id for product_id in ranking[:10] if product_id not in judgments[query_id]]
    # the name is cut to 45 characters so that the table fits on the page
    rows.append({"query": queries.at[query_id, "query"], "judged@10": judged_at_k(ranking, judgments[query_id], 10),
                 "unjudged": len(unjudged), "first unjudged product": products.at[unjudged[0], "name"][:45] if unjudged else ""})
table = pd.DataFrame(rows)

print(f"mean judged@10: {table['judged@10'].mean():.3f}")
# lib.metrics' judged@10 per query, indexed by query_id
library = evaluate(run, judgments)["judged@10"]
# 1e-12 allows for floating-point rounding when the two judged@10 values are compared
agree = sum(abs(row["judged@10"] - library[query_id]) < 1e-12 for query_id, row in zip(run, rows))
print(f"queries where the hand-built judged@10 equals lib.metrics: {agree} of {len(rows)}")
print("unjudged products in the top 10s:", table["unjudged"].sum())
print("test queries with an unjudged product in the top 10:", (table["judged@10"] < 1).sum())
sleeper = list(judgments[244].values())                      # pull out sleeper loveseat
print("judgments for pull out sleeper loveseat:", len(sleeper))
print("irrelevant judgments for pull out sleeper loveseat:", sleeper.count(0))  # grade 0 is irrelevant
print()
# judged@10 below 1 means the query has at least one unjudged product in its top 10
print(table[table["judged@10"] < 1].sort_values("judged@10").to_string(index=False))
