"""Resamples the train queries with a fixed seed and counts which α wins each resample, for the weighted sum and for
weighted RRF on the same resamples. The prose's point rests on the α tuned on all train queries and on the counts of
resamples choosing each α."""
import numpy as np
import pandas as pd

from lib.blend import best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
lexical, semantic = LexicalSearch(products), SemanticSearch()
tables = candidates(lexical, semantic, queries)
bm25, semantic_run = lexical.run(queries, k=100), semantic.run(queries, k=100)
blends = {"weighted sum": scores_by_alpha(lambda alpha: weighted_sum(tables, alpha), judgments),
          "weighted rrf": scores_by_alpha(lambda alpha: weighted_rrf(bm25, semantic_run, alpha), judgments)}

resamples = 1000
print("resamples:", resamples)
# a fixed seed, so every run draws the same resamples
rng = np.random.default_rng(2026)
draws = [rng.integers(0, len(queries), len(queries)) for _ in range(resamples)]   # the same draws for both
for name, per_query in blends.items():                       # per_query: train queries x alphas
    print(f"{name} alpha tuned on all train queries: {best_alpha(per_query)}")
    # best alpha per resample; idxmax takes the first, smaller alpha when two tie
    chosen = pd.Series([per_query.iloc[draw].mean().idxmax() for draw in draws])
    for alpha, count in chosen.value_counts().sort_index().items():
        print(f"{name} resamples choosing alpha {alpha}: {count}")
