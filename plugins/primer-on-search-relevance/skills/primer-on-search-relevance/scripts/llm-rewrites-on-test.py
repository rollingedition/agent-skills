"""Scores BM25 and semantic retrieval on the test queries, as typed and rewritten, as the chapter's planned comparisons,
then repeats both on condensed runs as an exploratory check. The prose's point rests on the "established at 0.01" lines."""
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.queries import THRESHOLD, condensed, report_planned, rewrite_runs
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")             # scored on the human judgments
# for each retriever, its run on the rewrite, then its run on the query as typed
runs = rewrite_runs(queries, LexicalSearch(load_products()), SemanticSearch())

print(f"the planned test comparisons, threshold {THRESHOLD:.2f}:")
for retriever, (rewritten, typed) in runs.items():
    name = f"llm rewrite, {retriever}"
    after, before = evaluate(rewritten, judgments), evaluate(typed, judgments)
    for form, frame in [("typed", before), ("rewrite", after)]:
        print(f"{name}, test ndcg@10 {form}: {frame['ndcg@10'].mean():.3f}")
        print(f"{name}, test judged@10 {form}: {frame['judged@10'].mean():.3f}")
    report_planned(name, after["ndcg@10"], before["ndcg@10"])

    # Exploratory, never established: the same comparison on condensed runs, which drop unjudged products
    # rewritten comes first in each pair, as rewrite_runs returns them; the rewrite is "after"
    after, before = (evaluate(condensed(run, judgments), judgments)["ndcg@10"] for run in (rewritten, typed))
    # confidence = 1 - THRESHOLD: a 99% interval, at the level the planned comparisons use
    result = compare(after, before, confidence=1 - THRESHOLD)
    print(f"{name}, condensed ndcg@10 typed: {before.mean():.3f}")
    print(f"{name}, condensed ndcg@10 rewrite: {after.mean():.3f}")
    print(f"{name}, condensed, exploratory mean difference: {result['mean difference']:.3f}")
    print(f"{name}, condensed, exploratory permutation p: {result['permutation p']:.3f}")
    low, high = result["ci low"], result["ci high"]
    print(f"{name}, condensed, exploratory {1 - THRESHOLD:.0%} interval: {low:.3f} to {high:.3f}")
