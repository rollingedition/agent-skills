from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])           # k = 60 and equal votes, as in chapter 1
bm25_scores, semantic_scores, hybrid_scores = (evaluate(run, judgments) for run in (bm25, semantic, hybrid))

print(f"bm25 judged@10: {bm25_scores['judged@10'].mean():.3f}")
print(f"semantic judged@10: {semantic_scores['judged@10'].mean():.3f}")
for name, after, before in [("semantic minus bm25", semantic_scores, bm25_scores),
                            ("hybrid minus semantic", hybrid_scores, semantic_scores)]:
    result = compare(after["ndcg@10"], before["ndcg@10"])                    # paired by query
    print(f"{name}, mean ndcg@10: {result['mean difference']:.3f}")
    print(f"{name}, permutation p: {result['permutation p']:.3f}")
    print(f"{name}, t-test p: {result['t-test p']:.3f}")
print()

change = (hybrid_scores["ndcg@10"] - semantic_scores["ndcg@10"]).round(3)   # fusion against semantic alone
lead = (bm25_scores["ndcg@10"] - semantic_scores["ndcg@10"]).round(3)       # above 0 means BM25 wins
for name, group in [("bm25 wins", lead > 0), ("semantic wins", lead < 0)]:
    print(f"{name}, queries: {group.sum()}")
    print(f"{name}, fusion better than semantic: {(change[group] > 0).sum()}")
    print(f"{name}, fusion worse than semantic: {(change[group] < 0).sum()}")
    print(f"{name}, mean change in ndcg@10: {change[group].mean():.3f}")
