from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)

for k in [1, 60]:
    print(f"rank 1 over rank 10 at k={k}: {(1 / (k + 1)) / (1 / (k + 10)):.3f}")
scores = {k: evaluate(reciprocal_rank_fusion([bm25, semantic], k=k), judgments)["ndcg@10"]
          for k in [1, 10, 30, 60, 100, 300]}
for k, per_query in scores.items():
    print(f"k={k} ndcg@10: {per_query.mean():.3f}")

best = max(scores, key=lambda k: scores[k].mean())           # ties go to the smaller k
print("best k on train:", best)
result = compare(scores[best], scores[60])                     # the planned check: best k against the default
print(f"best k minus k=60: {result['mean difference']:.3f}")
print(f"best k minus k=60, permutation p: {result['permutation p']:.3f}")
print(f"best k minus k=60, t-test p: {result['t-test p']:.3f}")
print(f"best k minus k=60, 95% interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
print(f"best k minus k=60, wins, losses, ties: {result['wins']}, {result['losses']}, {result['ties']}")
