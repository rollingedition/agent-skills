import pandas as pd

from lib.store import load_labels, load_queries

queries, labels = load_queries(), load_labels()
counts = pd.crosstab(labels["query_id"], labels["label"])[["exact", "partial", "irrelevant"]]
shares = counts.div(counts.sum(axis=1), axis=0).join(queries[["query", "split"]])

print(f"partial share of all judgments: {(labels['label'] == 'partial').mean():.3f}")
print(f"median exact share: {shares['exact'].median():.3f}")
print(f"median irrelevant share: {shares['irrelevant'].median():.3f}")
for label, which in [("exact", "lowest"), ("exact", "highest"), ("irrelevant", "highest")]:
    query_id = shares[label].idxmin() if which == "lowest" else shares[label].idxmax()
    print(f"{which} {label} share: {shares.at[query_id, label]:.3f}")
    print(f"query with the {which} {label} share: {shares.at[query_id, 'query']}")
print("queries with no irrelevant judgment:", (counts["irrelevant"] == 0).sum())
print("fewest exact products for a query:", counts["exact"].min())
print("most exact products for a query:", counts["exact"].max())
few = counts["exact"] < 10
print("queries with fewer than 10 exact products:", few.sum())
print("test queries with fewer than 10 exact products:", (few & (shares["split"] == "test")).sum())

print("queries with an exact share of 0.1 or less:", (shares["exact"] <= 0.1).sum())
print()
print("exact share  queries")
bins = pd.cut(shares["exact"], [tenth / 10 for tenth in range(11)])     # no share is 0: each query has 3 or more exact
for interval, number in bins.value_counts(sort=False).items():
    print(f"{interval.left:.1f} to {interval.right:.1f}  {number:>3}  {'#' * number}".rstrip())
