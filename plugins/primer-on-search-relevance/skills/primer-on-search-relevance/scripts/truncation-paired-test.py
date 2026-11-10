from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_queries, qrels

# Train queries: these comparisons tune the vector size. They are not evidence about the test queries.
train, judgments = load_queries("train"), qrels("train")


def ndcg(dims):
    return evaluate(SemanticSearch(dims=dims).run(train, k=100), judgments)["ndcg@10"]


def p_value(p):
    return "below 0.001" if p < 0.001 else f"{p:.3f}"


full = ndcg(768)
for dims in [256, 128]:
    result = compare(ndcg(dims), full)                    # paired by train query: shortened minus full
    print(f"{dims} vs 768, mean difference in ndcg@10: {result['mean difference']:.3f}")
    print(f"{dims} vs 768, queries worse: {result['losses']}")
    print(f"{dims} vs 768, permutation test p: {p_value(result['permutation p'])}")
    print(f"{dims} vs 768, paired t-test p: {p_value(result['t-test p'])}")
    print(f"{dims} vs 768, 95% bootstrap interval: {result['ci low']:.4f} to {result['ci high']:.4f}")
    print(f"{dims} vs 768, interval excludes 0: {'yes' if result['ci high'] < 0 or result['ci low'] > 0 else 'no'}")
    print(f"{dims} vs 768, effect size: {result['effect size']:.3f}")
    print()
