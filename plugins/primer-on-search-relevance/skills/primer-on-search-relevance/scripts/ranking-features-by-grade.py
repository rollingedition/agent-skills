import pandas as pd

from lib.ranking import FEATURES, feature_table
from lib.store import load_products, load_queries

products, queries = load_products(), load_queries("train")      # train queries: features are design work
table = feature_table(products, queries)
print(f"features: {len(FEATURES)}")
print(f"train candidates: {len(table)}")
print(f"train candidates per query, median: {table.groupby('query_id').size().median():.0f}")
print(f"share of train candidates nobody judged: {table['grade'].isna().mean():.3f}")

query_id = queries.index[queries["query"] == "laundry basket with wheels"][0]
one = table[table["query_id"] == query_id].sort_values("cross_encoder", ascending=False)
one = one.assign(name=products.loc[one["product_id"], "name"].str[:38].to_numpy())
pd.set_option("display.width", 200)
print(f"\ncandidates for laundry basket with wheels: {len(one)}")
print(one[["name", "bm25", "similarity", "cross_encoder", "name_match", "attribute_match", "rating_count", "grade"]]
      .head(6).round(3).to_string(index=False))
print(f"top 6 by cross-encoder, exact: {(one['grade'].head(6) == 2).sum()}")

label = table["grade"].map({2: "exact", 1: "partial", 0: "irrelevant"}).fillna("unjudged")
means = table[FEATURES].groupby(label).mean().loc[["exact", "partial", "irrelevant", "unjudged"]]
print("\nmean of each feature by grade, train candidates:")
print(means.round(3).to_string())
for grade in means.index:
    print(f"mean cross_encoder, {grade}: {means.at[grade, 'cross_encoder']:.3f}")
relevance = ["bm25", "similarity", "cross_encoder", "name_match"]
nearer = [name for name in relevance if abs(means.at["unjudged", name] - means.at["irrelevant", name])
          < abs(means.at["unjudged", name] - means.at["partial", name])]
print(f"relevance features where unjudged sits nearer irrelevant than partial: {len(nearer)} of {len(relevance)}")
medians = table[["rating_count", "review_count"]].groupby(label).median().loc[means.index]  # counts are skewed
for grade in ["exact", "partial", "irrelevant"]:
    print(f"rating_count, {grade}, mean: {means.at[grade, 'rating_count']:.3f}")
    print(f"rating_count, {grade}, median: {medians.at[grade, 'rating_count']:.1f}")
print(f"products with no rating: {products['rating_count'].isna().sum()}")
