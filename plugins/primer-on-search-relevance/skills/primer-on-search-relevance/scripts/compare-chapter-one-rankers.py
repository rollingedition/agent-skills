"""Runs chapter 1's four rankers through the harness and applies the Bonferroni threshold to the three planned comparisons and one exploratory comparison. The prose's point rests on the judged@10 lines, the established lines, and the exploratory comparison's p-value and agreement lines."""
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
# chapter 1's rerank: only the top 50 are reordered; the rest keep their hybrid order
reranked = {query_id: sorted(ranking[:50], key=lambda product_id: score[(query_id, product_id)], reverse=True)
            + ranking[50:] for query_id, ranking in hybrid.items()}

runs = {"bm25": bm25, "semantic": semantic, "hybrid": hybrid, "reranked": reranked}
scores = {name: evaluate(run, judgments) for name, run in runs.items()}       # one row per test query
for name, frame in scores.items():
    print(f"{name} ndcg@10: {frame['ndcg@10'].mean():.3f}\n{name} judged@10: {frame['judged@10'].mean():.3f}")

planned = [("semantic", "bm25"), ("hybrid", "semantic"), ("reranked", "hybrid")]    # each stage against the last
exploratory = [("reranked", "semantic")]                       # chosen after chapter 1 saw the test means
threshold = 0.05 / len(planned)                                # Bonferroni, over the planned comparisons only
print(f"\nplanned comparisons: {len(planned)}\np-value threshold: {threshold:.4f}\ninterval level: {1 - threshold:.4f}")
# each planned test has a 0.95 chance of no false positive, if its gap is noise
print(f"chance of a false positive, all gaps noise, tests independent: {1 - 0.95 ** len(planned):.3f}")
established, disagreements = 0, 0
for after, before in planned + exploratory:
    result, name = compare(scores[after]["ndcg@10"], scores[before]["ndcg@10"], confidence=1 - threshold), f"{after} minus {before}"
    # verdict runs on the exploratory one too, only for its agreement checks; it is never counted as established
    checks, kind = verdict(result, threshold), "planned" if (after, before) in planned else "exploratory"
    print(f"\n{name}: {result['mean difference']:.3f}\n{name} kind: {kind}")
    print(f"{name} interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
    print(f"{name} permutation p: {result['permutation p']:.3f}\n{name} t-test p: {result['t-test p']:.3f}")
    print(f"{name} effect size: {result['effect size']:.3f}\n{name} wins, losses, ties: {result['wins']} / {result['losses']} / {result['ties']}")
    # only a planned comparison can be established; the exploratory one is labelled and never called so
    print(f"{name} established: {'yes' if checks['established'] and kind == 'planned' else 'no'}")
    for method in ["t-test", "interval"]:
        print(f"{name} {method} agrees: {'yes' if checks[method + ' agrees'] else 'no'}")
    if kind == "planned":
        established += checks["established"]
        # a planned comparison where the t-test or the interval disagrees with the permutation test
        disagreements += not (checks["t-test agrees"] and checks["interval agrees"])
print(f"\nplanned comparisons established: {established}\nplanned comparisons with a disagreement: {disagreements}")
