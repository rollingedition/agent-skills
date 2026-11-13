"""The smallest change the regression set detects with 80% power, from the spread of per-query changes, and a simulation that checks the power formula. The prose's point rests on the 'smallest change 30 queries detect' line and the simulated power lines."""
import numpy as np
from scipy import stats

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

SIGNIFICANCE, POWER = 0.05, 0.80
queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])
change = evaluate(hybrid, judgments)["ndcg@10"] - evaluate(semantic, judgments)["ndcg@10"]
spread = change.std()                                     # of the per-query differences

z = stats.norm.ppf(1 - SIGNIFICANCE / 2) + stats.norm.ppf(POWER)
print(f"spread of per-query changes: {spread:.3f}")
print(f"coefficient for paired queries: {z ** 2:.1f}")     # one sample of differences, so half of 16
# z standard errors of the mean change: the smallest change the test can detect
detectable = z * spread / np.sqrt(len(change))
print(f"smallest change 30 queries detect: {detectable:.3f}")
# n = z squared times spread squared, over the change squared, solved for n
print(f"queries needed for a change of 0.01: {z ** 2 * spread ** 2 / 0.01 ** 2:.0f}")

# Check the arithmetic by simulation: draw 30 normally distributed changes with that mean and spread,
# 10,000 times, and test each. The real differences aren't normal, so this checks the formula, not the data.
rng = np.random.default_rng(2026)
# ttest_1samp tests each draw against popmean 0, the no-change null
power = stats.power(stats.ttest_1samp, lambda size: rng.normal(detectable, spread, size=size), (len(change),),
                    significance=SIGNIFICANCE, kwargs={"popmean": 0})
# .item() takes the single value out of the result, which holds one simulated power
print(f"simulated power at that change: {power.power.item():.3f}")
print("simulated power below the planned 0.8:", "yes" if power.power.item() < POWER else "no")
