import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
run = LexicalSearch(products).run(queries, k=100)


def judged_at_k(ranking, judged, k):
    """The share of the top k that has a judgment of any grade."""
    return sum(product_id in judged for product_id in ranking[:k]) / k


rows = []
for query_id, ranking in run.items():
    unjudged = [product_id for product_id in ranking[:10] if product_id not in judgments[query_id]]
    rows.append({"query": queries.at[query_id, "query"], "judged@10": judged_at_k(ranking, judgments[query_id], 10),
                 "unjudged": len(unjudged), "first unjudged product": products.at[unjudged[0], "name"][:45] if unjudged else ""})
table = pd.DataFrame(rows)

print(f"mean judged@10: {table['judged@10'].mean():.3f}")
library = evaluate(run, judgments)["judged@10"]
agree = sum(abs(row["judged@10"] - library[query_id]) < 1e-12 for query_id, row in zip(run, rows))
print(f"queries where the hand-built judged@10 equals lib.metrics: {agree} of {len(rows)}")
print("unjudged products in the top 10s:", table["unjudged"].sum())
print("test queries with an unjudged product in the top 10:", (table["judged@10"] < 1).sum())
sleeper = list(judgments[244].values())                      # pull out sleeper loveseat
print("judgments for pull out sleeper loveseat:", len(sleeper))
print("irrelevant judgments for pull out sleeper loveseat:", sleeper.count(0))
print()
print(table[table["judged@10"] < 1].sort_values("judged@10").to_string(index=False))
