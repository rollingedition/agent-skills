import math

from scipy.stats import t, ttest_rel

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
    difference = ndcg[after] - ndcg[before]
    n = len(difference)
    standard_error = difference.std(ddof=1) / math.sqrt(n)      # how much the mean would move between samples
    statistic = difference.mean() / standard_error
    p_value = 2 * t.sf(abs(statistic), df=n - 1)               # both tails of the t distribution
    print(f"{after} minus {before}: {difference.mean():.3f}")
    print(f"{after} minus {before} t by hand: {statistic:.3f}")
    print(f"{after} minus {before} p by hand: {p_value:.3f}")
    print(f"{after} minus {before} p from ttest_rel: {ttest_rel(ndcg[after], ndcg[before]).pvalue:.3f}")
