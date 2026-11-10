from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.recorded import cross_encoder_scores
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

lexical, embeddings = LexicalSearch(load_products()), SemanticSearch()
score = {(query_id, product_id): value for query_id, product_id, value in cross_encoder_scores().itertuples(index=False)}

for split in ["test", "train"]:                      # the same comparison on another sample of the store's queries
    queries, judgments = load_queries(split), qrels(split)
    semantic = embeddings.run(queries, k=100)
    hybrid = reciprocal_rank_fusion([lexical.run(queries, k=100), semantic])
    reranked = {query_id: sorted(ranking[:50], key=lambda product_id: score[(query_id, product_id)], reverse=True)
                + ranking[50:] for query_id, ranking in hybrid.items()}
    result = compare(evaluate(reranked, judgments)["ndcg@10"], evaluate(semantic, judgments)["ndcg@10"])
    gap = result["mean difference"]
    print(f"{split} queries:", len(judgments))
    print(f"{split} reranked minus semantic: {gap:.3f}")
    print(f"{split} higher-scoring run:", "reranked" if gap > 0 else "semantic" if gap < 0 else "neither")
    if split == "test":
        print(f"test permutation p: {result['permutation p']:.3f}")
