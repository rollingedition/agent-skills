"""Estimates the p-value of the hybrid's deficit against semantic retrieval by flipping each query's sign at random, once by hand and once with SciPy's permutation_test. The prose's point rests on the observed mean, the two p-value lines, and the line that compares the p-value with 0.05."""
import numpy as np
from scipy.stats import permutation_test

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([LexicalSearch(load_products()).run(queries, k=100), semantic])
after = evaluate(hybrid, judgments)["ndcg@10"].to_numpy()
before = evaluate(semantic, judgments)["ndcg@10"].to_numpy()
difference = after - before                                       # hybrid minus semantic, per test query
print("test queries:", len(difference))
print(f"sign patterns for the test queries: {2 ** len(difference):,}")
print(f"observed mean difference: {difference.mean():.3f}")

# if the two rankers were interchangeable, each query's difference would be as likely to have the other sign
# a fixed seed, so every run draws the same sign patterns
rng = np.random.default_rng(2026)
# 9,999 random sign patterns, one sign for each query in each
signs = rng.choice([-1, 1], size=(9999, len(difference)))
flipped = (signs * difference).mean(axis=1)                       # 9,999 mean differences under that assumption
# the 95th percentile of the flipped means' sizes
print(f"95% of flipped means are smaller than: {np.quantile(np.abs(flipped), 0.95):.3f}")
print(f"p-value by hand: {np.mean(np.abs(flipped) >= abs(difference.mean())):.3f}")

result = permutation_test((after, before), lambda after_scores, before_scores, axis: np.mean(after_scores - before_scores, axis=axis),
                          # samples: flip each query's pair of scores, which is the paired setting
                          permutation_type="samples", rng=np.random.default_rng(2026))
print(f"p-value from scipy: {result.pvalue:.3f}")
print("difference at the 0.05 level:", "larger than chance" if result.pvalue < 0.05 else "within chance")
