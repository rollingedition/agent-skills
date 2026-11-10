from lib.blend import best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

lexical, semantic = LexicalSearch(load_products()), SemanticSearch()


def blends(queries):
    tables, bm25, semantic_run = candidates(lexical, semantic, queries), lexical.run(queries), semantic.run(queries)
    return {"weighted sum": lambda alpha: weighted_sum(tables, alpha),          # each blend's run at a given alpha
            "weighted rrf": lambda alpha: weighted_rrf(bm25, semantic_run, alpha)}


train, test = blends(load_queries("train")), blends(load_queries("test"))
threshold = 0.05 / len(test)                                 # two planned comparisons, Bonferroni-corrected
semantic_scores = evaluate(semantic.run(load_queries("test")), qrels("test"))
print("test queries:", len(semantic_scores))
print(f"semantic ndcg@10: {semantic_scores['ndcg@10'].mean():.3f}")
unweighted = evaluate(test["weighted rrf"](0.5), qrels("test"))          # alpha 0.5 is chapter 1's fusion
print(f"unweighted rrf ndcg@10: {unweighted['ndcg@10'].mean():.3f}")
print(f"p-value threshold for each comparison: {threshold:.3f}")
print(f"confidence level of each interval: {1 - threshold:.3f}")
judged = [semantic_scores["judged@10"].mean()]
for name, blend in test.items():
    alpha = best_alpha(scores_by_alpha(train[name], qrels("train")))       # train only
    scores = evaluate(blend(alpha), qrels("test"))
    judged.append(scores["judged@10"].mean())
    result = compare(scores["ndcg@10"], semantic_scores["ndcg@10"], confidence=1 - threshold)
    print(f"{name} alpha chosen on train: {alpha}")
    print(f"{name} ndcg@10: {scores['ndcg@10'].mean():.3f}")
    print(f"{name} minus semantic: {result['mean difference']:.3f}")
    print(f"{name} permutation p: {result['permutation p']:.3f}")
    print(f"{name} t-test p: {result['t-test p']:.3f}")
    print(f"{name} interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
    print(f"{name} established: {result['permutation p'] < threshold}")
print(f"lowest judged@10: {min(judged):.3f}")
print(f"highest judged@10: {max(judged):.3f}")
