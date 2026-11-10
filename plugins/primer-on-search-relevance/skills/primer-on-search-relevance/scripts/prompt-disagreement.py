import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from lib.agreement import LABELS, graded_pairs
from lib.store import load_products, load_queries


def kappa_gap(sample):
    """Kappa with people under the guidelines prompt, minus kappa under the short prompt."""
    human = sample["human"].astype(int)
    return cohen_kappa_score(human, sample["guidelines"].astype(int)) - cohen_kappa_score(human, sample["short"].astype(int))


order = list(LABELS.values())                     # exact, partial, irrelevant
for pool in ["train", "test"]:
    pairs = graded_pairs(pool)
    print(f"\n{pool} pairs where the prompts disagree: {(pairs['short'] != pairs['guidelines']).sum()} of {len(pairs)}\n"
          f"kappa between the prompts, {pool} pool: {cohen_kappa_score(pairs['short'], pairs['guidelines']):.3f}")
    table = pd.crosstab(pairs["short"].map(LABELS).rename(f"short, {pool}"), pairs["guidelines"].map(LABELS).rename("guidelines"))
    table = table.reindex(index=order, columns=order, fill_value=0)
    cells = {f"{row} under short, {column} under guidelines": table.at[row, column] for row in order for column in order if row != column}
    print(f"{table}\nlargest disagreement, {pool} pool: {max(cells, key=cells.get)} ({max(cells.values())})")

pairs, products, queries = graded_pairs("train"), load_products(), load_queries()
moved = pairs[(pairs["short"] == 1) & (pairs["guidelines"] == 0)]          # partial under one prompt, irrelevant under the other
print("\n".join(f"moved train pairs judged {label} by people: {(moved['human'] == grade).sum()}" for grade, label in LABELS.items()))
for query_id, product_id in moved[["query_id", "product_id"]].drop_duplicates("query_id").head(5).itertuples(index=False):
    print(f"  {queries.at[query_id, 'query']:<28} {products.at[product_id, 'name'][:50]}")

rng, train_queries = np.random.default_rng(2026), pairs["query_id"].unique()
by_query = {query_id: group for query_id, group in pairs.groupby("query_id")}
gaps = [kappa_gap(pd.concat([by_query[query_id] for query_id in rng.choice(train_queries, len(train_queries))]))
        for _ in range(2000)]                                               # resample whole train queries
low, high = np.percentile(gaps, [2.5, 97.5])
print(f"kappa with people, guidelines minus short: {kappa_gap(pairs):.3f}\n95% interval over resampled train queries: {low:.3f} to {high:.3f}")
