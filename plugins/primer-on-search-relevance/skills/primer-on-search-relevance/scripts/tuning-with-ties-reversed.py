import numpy as np

from lib.blend import best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


class TiesReversed(LexicalSearch):
    """BM25 with equal scores in descending product_id order, an order as arbitrary as ascending."""

    def search(self, query, k=100):
        scores = super().search(query, k=len(self.ids))           # every match, so the cut at k can move too
        order = np.lexsort((-scores.index.to_numpy(), -scores.to_numpy()))
        return scores.iloc[order[:k]]


products, queries, judgments = load_products(), load_queries("train"), qrels("train")
semantic = SemanticSearch()
semantic_run = semantic.run(queries, k=100)
for ties, lexical in [("ties by product_id", LexicalSearch(products)), ("ties reversed", TiesReversed(products))]:
    bm25 = lexical.run(queries, k=100)
    by_k = {k: evaluate(reciprocal_rank_fusion([bm25, semantic_run], k=k), judgments)["ndcg@10"].mean()
            for k in [1, 10, 30, 60, 100, 300]}
    print(f"best rrf k, {ties}: {max(by_k, key=by_k.get)}")                # ties go to the smaller k
    rrf = scores_by_alpha(lambda alpha: weighted_rrf(bm25, semantic_run, alpha), judgments)
    print(f"weighted rrf alpha, {ties}: {best_alpha(rrf)}")
    tables = candidates(lexical, semantic, queries)
    total = scores_by_alpha(lambda alpha: weighted_sum(tables, alpha), judgments)
    print(f"weighted sum alpha, {ties}: {best_alpha(total)}")
