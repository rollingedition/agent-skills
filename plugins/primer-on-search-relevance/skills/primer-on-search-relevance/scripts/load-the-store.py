import pandas as pd

from lib.store import DATA, load_labels, load_products, load_queries

products = load_products()
queries = load_queries()
labels = load_labels()                                   # one row per judged (query, product) pair
conflicts = pd.read_csv(DATA / "label_conflicts.csv")    # pairs WANDS labelled two ways

print(f"products: {len(products):,}")
print("queries:", len(queries))
print("train queries:", (queries["split"] == "train").sum())
print("test queries:", (queries["split"] == "test").sum())
print(f"judged pairs: {len(labels):,}")
print("pairs with conflicting labels:", len(conflicts))
for label in ["exact", "partial", "irrelevant"]:
    print(f"{label} pairs: {(labels['label'] == label).sum():,}")
print(f"products judged for at least one query: {labels['product_id'].nunique():,}")

print()
print(queries.head(4).to_string())
