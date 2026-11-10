from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.recorded import cross_encoder_scores
from lib.semantic import SemanticSearch
from lib.significance import compare, verdict
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])
score = {(query_id, product_id): value for query_id, product_id, value in cross_encoder_scores().itertuples(index=False)}
reranked = {query_id: sorted(ranking[:50], key=lambda product_id: score[(query_id, product_id)], reverse=True)
            + ranking[50:] for query_id, ranking in hybrid.items()}          # chapter 1's rerank of the top 50

runs = {"bm25": bm25, "semantic": semantic, "hybrid": hybrid, "reranked": reranked}
scores = {name: evaluate(run, judgments) for name, run in runs.items()}       # one row per test query
for name, frame in scores.items():
    print(f"{name} ndcg@10: {frame['ndcg@10'].mean():.3f}\n{name} judged@10: {frame['judged@10'].mean():.3f}")

planned = [("semantic", "bm25"), ("hybrid", "semantic"), ("reranked", "hybrid")]    # each stage against the last
exploratory = [("reranked", "semantic")]                       # chosen after chapter 1 saw the test means
threshold = 0.05 / len(planned)                                # Bonferroni, over the planned comparisons only
print(f"\nplanned comparisons: {len(planned)}\np-value threshold: {threshold:.4f}\ninterval level: {1 - threshold:.4f}")
print(f"chance of a false positive, all gaps noise, tests independent: {1 - 0.95 ** len(planned):.3f}")
established, disagreements = 0, 0
for after, before in planned + exploratory:
    result, name = compare(scores[after]["ndcg@10"], scores[before]["ndcg@10"], confidence=1 - threshold), f"{after} minus {before}"
    checks, kind = verdict(result, threshold), "planned" if (after, before) in planned else "exploratory"
    print(f"\n{name}: {result['mean difference']:.3f}\n{name} kind: {kind}")
    print(f"{name} interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
    print(f"{name} permutation p: {result['permutation p']:.3f}\n{name} t-test p: {result['t-test p']:.3f}")
    print(f"{name} effect size: {result['effect size']:.3f}\n{name} wins, losses, ties: {result['wins']} / {result['losses']} / {result['ties']}")
    print(f"{name} established: {'yes' if checks['established'] and kind == 'planned' else 'no'}")
    for method in ["t-test", "interval"]:
        print(f"{name} {method} agrees: {'yes' if checks[method + ' agrees'] else 'no'}")
    if kind == "planned":
        established += checks["established"]
        disagreements += not (checks["t-test agrees"] and checks["interval agrees"])
print(f"\nplanned comparisons established: {established}\nplanned comparisons with a disagreement: {disagreements}")
