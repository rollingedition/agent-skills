from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

ALPHA = 1                                   # each loss counts alpha + 1 times: here, double


def urisk(change, alpha):
    """Mean change per query, with every loss counted alpha + 1 times (TREC 2013 Web track)."""
    wins, losses = change.clip(lower=0).sum(), -change.clip(upper=0).sum()
    return (wins - (alpha + 1) * losses) / len(change)


products, queries, judgments = load_products(), load_queries("test"), qrels("test")
baseline = evaluate(LexicalSearch(products).run(queries, k=100), judgments)
candidates = {"semantic": SemanticSearch(), "semantic 128": SemanticSearch(dims=128)}   # all 768 numbers, or the first 128

print(f"bm25 judged@10: {baseline['judged@10'].mean():.3f}")
evaluated = {name: evaluate(search.run(queries, k=100), judgments) for name, search in candidates.items()}
for name, scores in evaluated.items():
    change = (scores["ndcg@10"] - baseline["ndcg@10"]).round(3)
    print(f"{name} judged@10: {scores['judged@10'].mean():.3f}")
    print(f"{name} mean change: {change.mean():.3f}")
    print(f"{name} wins: {(change > 0).sum()}")
    print(f"{name} losses: {(change < 0).sum()}")
    print(f"{name} largest loss: {change.min():.3f}")
    print(f"{name} urisk with alpha {ALPHA}: {urisk(change, ALPHA):.3f}")

# a demonstration, chosen for how it behaves on test: its tests describe it, and it is never established
result = compare(evaluated["semantic 128"]["ndcg@10"], baseline["ndcg@10"], confidence=0.95)
print(f"semantic 128 permutation test p: {result['permutation p']:.3f}")
print(f"semantic 128 paired t-test p: {result['t-test p']:.3f}")
print(f"semantic 128 interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
