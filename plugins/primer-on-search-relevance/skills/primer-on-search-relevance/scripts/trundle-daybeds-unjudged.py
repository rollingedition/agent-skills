from collections import Counter

from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries(), qrels()
LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}

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

print("first unjudged daybed:", products.at[unjudged[0], "name"])
print("second unjudged daybed:", products.at[unjudged[1], "name"])
