from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


def rrf_scores(rankings, k=60):
    """Each product scores the sum of 1 / (k + rank) over the rankings that contain it."""
    scores = {}
    for ranking in rankings:
        for rank, product_id in enumerate(ranking, start=1):
            scores[product_id] = scores.get(product_id, 0) + 1 / (k + rank)
    return scores


def reciprocal_rank_fusion(runs, k=60, depth=100):
    """For each query, products in order of their RRF scores, best first; equal scores by product_id."""
    fused = {}
    for query_id in runs[0]:
        scores = rrf_scores([run[query_id] for run in runs], k)
        fused[query_id] = sorted(scores, key=lambda product_id: (-scores[product_id], product_id))[:depth]
    return fused


products, queries, judgments = load_products(), load_queries("test"), qrels("test")
bm25, semantic = LexicalSearch(products).run(queries, k=100), SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])

for place, product_id in zip(["first", "second"], hybrid[246]):       # query 246, "clear shower curtain"
    bm25_rank, semantic_rank = bm25[246].index(product_id) + 1, semantic[246].index(product_id) + 1
    print(f"{place} product: {products.at[product_id, 'name']}")
    print(f"{place} product's bm25 rank: {bm25_rank}")
    print(f"{place} product's semantic rank: {semantic_rank}")
    print(f"{place} product's score by hand: {1 / (60 + bm25_rank) + 1 / (60 + semantic_rank):.5f}")
    print(f"{place} product's score from rrf_scores: {rrf_scores([bm25[246], semantic[246]])[product_id]:.5f}")

hybrid_scores, semantic_scores = evaluate(hybrid, judgments), evaluate(semantic, judgments)
print(f"hybrid ndcg@10: {hybrid_scores['ndcg@10'].mean():.3f}")
print(f"hybrid judged@10: {hybrid_scores['judged@10'].mean():.3f}")
difference = (hybrid_scores["ndcg@10"] - semantic_scores["ndcg@10"]).round(3)
print("better than semantic:", (difference > 0).sum())
print("worse than semantic:", (difference < 0).sum())
print("tied with semantic:", (difference == 0).sum())
