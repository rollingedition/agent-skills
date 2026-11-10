import pandas as pd

from lib.store import load_labels, load_products, load_queries

products, queries, labels = load_products(), load_queries(), load_labels()
exact = labels[labels["label"] == "exact"].join(products["product_class"], on="product_id")

rows = []
for query_id, group in exact.groupby("query_id"):
    predicted = queries.at[query_id, "query_class"]
    classes = group["product_class"].str.split("|")                 # a product can have several classes
    rows.append({"query": queries.at[query_id, "query"], "query_class": predicted,
                 "share of exact products in it": classes.apply(lambda names: predicted in names).mean(),
                 "commonest class of exact products": group["product_class"].value_counts().index[0] or "(none)"})
check = pd.DataFrame(rows)

print("queries:", len(check))
print("queries without a query_class:", check["query_class"].isna().sum())
print("queries where most exact products have the query_class:",
      (check["share of exact products in it"] > 0.5).sum())
missed = check[(check["share of exact products in it"] == 0) & check["query_class"].notna()]
print("queries where no exact product has the query_class:", len(missed))
print()
print(missed.drop(columns="share of exact products in it").to_string(index=False))
