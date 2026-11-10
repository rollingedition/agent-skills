import numpy as np
from scipy import stats

from lib.experiments import SHOPPERS, simulate_searches
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
arms = {"bm25": LexicalSearch(load_products()).run(queries, k=100),     # control
        "semantic": SemanticSearch().run(queries, k=100)}               # treatment
metrics = {"clicks per search": "clicks", "share of searches with an exact click": "exact_click"}

significant_leaders = {label: set() for label in metrics}      # rankers ahead at p below 0.05
for shopper_name, shopper in SHOPPERS.items():                         # navigational, then perfect
    rng = np.random.default_rng(2026)
    searches = {name: simulate_searches(run, judgments, 5_000, rng, shopper) for name, run in arms.items()}
    for label, column in metrics.items():
        means = {name: table[column].mean() for name, table in searches.items()}
        for name, mean in means.items():
            print(f"{shopper_name} shopper, {name} {label}: {mean:.3f}")
        p = stats.ttest_ind(searches["semantic"][column].astype(float), searches["bm25"][column].astype(float)).pvalue
        print(f"{shopper_name} shopper, {label} p: " + (f"{p:.3f}" if p >= 0.001 else "below 0.001"))
        if p < 0.05:
            significant_leaders[label].add(max(means, key=means.get))
for label in metrics:
    print(f"{label} reverses between shoppers:", "yes" if len(significant_leaders[label]) > 1 else "no")
