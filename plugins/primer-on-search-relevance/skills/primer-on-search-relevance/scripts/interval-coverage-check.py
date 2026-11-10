import numpy as np
from scipy.stats import bootstrap, ttest_1samp

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([LexicalSearch(load_products()).run(queries, k=100), semantic])
population = (evaluate(hybrid, judgments)["ndcg@10"] - evaluate(semantic, judgments)["ndcg@10"]).to_numpy()
true_gap = population.mean()            # known, because these differences stand in for every query there is

rng, trials = np.random.default_rng(2026), 1000
print("trials:", trials)
print(f"standard error of a coverage near 0.95: {(0.95 * 0.05 / trials) ** 0.5:.3f}")
for level in [0.95, round(1 - 0.05 / 3, 4)]:          # the usual level, and the level for three comparisons
    covered = {"bca": 0, "t": 0}
    for _ in range(trials):
        sample = rng.choice(population, size=len(population))      # another set of 30 queries like these
        bca = bootstrap((sample,), np.mean, confidence_level=level, n_resamples=1999, rng=rng).confidence_interval
        t = ttest_1samp(sample, 0).confidence_interval(level)     # the interval that matches the t-test
        covered["bca"] += bca.low <= true_gap <= bca.high
        covered["t"] += t.low <= true_gap <= t.high
    for method, count in covered.items():
        print(f"{method} coverage at {level}: {count / trials:.3f}")
