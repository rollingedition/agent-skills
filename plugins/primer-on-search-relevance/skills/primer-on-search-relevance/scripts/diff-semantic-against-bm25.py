import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

PLANNED_COMPARISONS = 1                      # this chapter's tests on the test queries
threshold = 0.05 / PLANNED_COMPARISONS       # Bonferroni: one comparison keeps 0.05

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
baseline = evaluate(LexicalSearch(products).run(queries, k=100), judgments)      # what the store runs
candidate = evaluate(SemanticSearch().run(queries, k=100), judgments)            # the change

diff = pd.DataFrame({"query": queries["query"], "bm25": baseline["ndcg@10"], "semantic": candidate["ndcg@10"]})
diff["change"] = (diff["semantic"] - diff["bm25"]).round(3)        # one row per test query

print(f"bm25 ndcg@10: {diff['bm25'].mean():.3f}")
print(f"semantic ndcg@10: {diff['semantic'].mean():.3f}")
result = compare(candidate["ndcg@10"], baseline["ndcg@10"], confidence=1 - threshold)    # chapter 3's comparison
print(f"mean change: {result['mean difference']:.3f}")
print(f"threshold: {threshold:g}")
print(f"permutation test p: {result['permutation p']:.3f}")
print(f"paired t-test p: {result['t-test p']:.3f}")
print(f"{(1 - threshold) * 100:g}% interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
print("established:", "yes" if result["permutation p"] < threshold else "no")
print("wins:", (diff["change"] > 0).sum())
print("losses:", (diff["change"] < 0).sum())
print("ties:", (diff["change"] == 0).sum())
print(f"largest loss: {diff['change'].min():.3f}")
print()
print(diff[diff["change"] < 0].sort_values("change").round(3).to_string())
