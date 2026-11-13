"""Builds a 95% percentile interval by hand from 9,999 resampled means, checks it against SciPy's percentile method, then reads SciPy's default BCa interval and the effect size for each gap. The prose's point rests on the BCa low and high lines and on the line that says whether each interval includes 0."""
import numpy as np
from scipy.stats import bootstrap

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"bm25": bm25, "semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}
ndcg = {name: evaluate(run, judgments)["ndcg@10"] for name, run in runs.items()}   # per test query

for after, before in [("semantic", "bm25"), ("hybrid", "semantic")]:
    difference, name = (ndcg[after] - ndcg[before]).to_numpy(), f"{after} minus {before}"
    # choice draws with replacement, so a query can appear twice in one set and not at all in another
    resampled = np.random.default_rng(2026).choice(difference, size=(9999, len(difference)))  # 9,999 sets of queries
    # 2.5% in each tail leaves the middle 95%
    low, high = np.percentile(resampled.mean(axis=1), [2.5, 97.5])      # the middle 95% of their means
    print(f"{name}: {difference.mean():.3f}")
    print(f"{name} interval by hand: {low:.3f} to {high:.3f}")
    percentile = bootstrap((difference,), np.mean, method="percentile", rng=np.random.default_rng(2026))
    print(f"{name} percentile interval from scipy: "
          f"{percentile.confidence_interval.low:.3f} to {percentile.confidence_interval.high:.3f}")
    # BCa is SciPy's default method, so no method argument is given
    bca = bootstrap((difference,), np.mean, rng=np.random.default_rng(2026)).confidence_interval
    print(f"{name} bca low: {bca.low:.3f}\n{name} bca high: {bca.high:.3f}")
    print(f"{name} bca interval and 0: {'includes 0' if bca.low <= 0 <= bca.high else 'excludes 0'}")
    # ddof=1: the standard deviation of the differences, with n - 1 in the denominator
    print(f"{name} effect size: {difference.mean() / difference.std(ddof=1):.3f}")
