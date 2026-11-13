"""Reorders the top 50 of the hybrid run by cross-encoder score, keeps the rest in place, and scores the result. The prose's point rests on the reranked nDCG@10 line, set beside the hybrid's score, and on the better and worse counts."""
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.recorded import cross_encoder_scores, manifest
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])        # the same function as in the hybrid section

recorded = cross_encoder_scores()                        # one score per (query, product) pair
score = {(query_id, product_id): value for query_id, product_id, value in recorded.itertuples(index=False)}
print("cross-encoder model:", manifest("cross-encoder")["model"])

depth = 50                                               # rerank the top 50
reranked = {}
for query_id, ranking in hybrid.items():
    # the top 50 are reordered by score; equal scores keep the hybrid's order
    top = sorted(ranking[:depth], key=lambda product_id: score[(query_id, product_id)], reverse=True)
    # products below the top 50 keep their hybrid order
    reranked[query_id] = top + ranking[depth:]

before, after = evaluate(hybrid, judgments), evaluate(reranked, judgments)
print(f"reranked ndcg@10: {after['ndcg@10'].mean():.3f}")
print(f"reranked judged@10: {after['judged@10'].mean():.3f}")
difference = (after["ndcg@10"] - before["ndcg@10"]).round(3)
print("better than hybrid:", (difference > 0).sum())
print("worse than hybrid:", (difference < 0).sum())
