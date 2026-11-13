"""Counts the products judged exact for the train query `trundle daybed` that have no judgment for the test query `full
bed with trundle`, and grades the ones that do. The prose's point rests on the `of them unjudged for full bed with
trundle` line and the `judged partial` line."""
from collections import Counter

from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries(), qrels()
LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}

# 433 is the train query trundle daybed, and its exact products come out in product_id order
daybeds = sorted(product_id for product_id, grade in judgments[433].items() if grade == 2)
full_bed = judgments[436]                                    # {product_id: grade} for "full bed with trundle"
print(f"433: {queries.at[433, 'query']} ({queries.at[433, 'split']})")
print(f"436: {queries.at[436, 'query']} ({queries.at[436, 'split']})")
print("exact for trundle daybed:", len(daybeds))

unjudged = [product_id for product_id in daybeds if product_id not in full_bed]
print("of them unjudged for full bed with trundle:", len(unjudged))
print("of them judged for full bed with trundle:", len(daybeds) - len(unjudged))
judged = Counter(LABELS[full_bed[product_id]] for product_id in daybeds if product_id in full_bed)
for label in LABELS.values():
    print(f"judged {label}: {judged[label]}")

# daybeds is in product_id order, so the first two unjudged are the two lowest product_ids among them
print("first unjudged daybed:", products.at[unjudged[0], "name"])
print("second unjudged daybed:", products.at[unjudged[1], "name"])
