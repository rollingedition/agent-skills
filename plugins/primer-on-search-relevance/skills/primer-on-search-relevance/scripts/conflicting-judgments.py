import pandas as pd

from lib.store import DATA, load_labels, load_products, load_queries

GRADES = {"exact": 2, "partial": 1, "irrelevant": 0}

products, queries, labels = load_products(), load_queries(), load_labels()
conflicts = pd.read_csv(DATA / "label_conflicts.csv")       # pairs WANDS lists more than once, with different labels
kept = labels.set_index(["query_id", "product_id"])["label"]

for row in conflicts.itertuples():
    print(f"{queries.at[row.query_id, 'query']:<32} {products.at[row.product_id, 'name'][:40]:<41} "
          f"{row.labels:<19} kept: {kept[(row.query_id, row.product_id)]}")

pairs = conflicts["labels"].str.split("|")
spread = pairs.apply(lambda both: max(GRADES[label] for label in both) - min(GRADES[label] for label in both))
print()
print("pairs with conflicting labels:", len(conflicts))
print("exact against partial:", (pairs.apply(frozenset) == frozenset(["exact", "partial"])).sum())
print("partial against irrelevant:", (pairs.apply(frozenset) == frozenset(["partial", "irrelevant"])).sum())
print(f"conflicts between neighbouring grades: {(spread == 1).sum()} of {len(conflicts)}")
