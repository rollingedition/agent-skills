from lib.blend import ALPHAS, NORMALIZATIONS, best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
lexical, semantic = LexicalSearch(products), SemanticSearch()
tables = candidates(lexical, semantic, queries)
bm25, semantic_run = lexical.run(queries, k=100), semantic.run(queries, k=100)

per_query = {}                                               # nDCG@10 per query (rows) and alpha (columns)
for name in NORMALIZATIONS:
    per_query[name] = scores_by_alpha(lambda alpha: weighted_sum(tables, alpha, name), judgments)
per_query["weighted rrf"] = scores_by_alpha(lambda alpha: weighted_rrf(bm25, semantic_run, alpha), judgments)
semantic_alone = per_query["min-max"][1.0]                   # alpha = 1 is semantic retrieval in either blend
print("alphas tried:", len(ALPHAS))
print("min-max ndcg@10 for alpha 0 to 1:", " ".join(f"{mean:.3f}" for mean in per_query["min-max"].mean()))
print(f"semantic alone ndcg@10: {semantic_alone.mean():.3f}")
print(f"unweighted rrf (alpha 0.5) ndcg@10: {per_query['weighted rrf'][0.5].mean():.3f}")

best = {name: frame[best_alpha(frame)] for name, frame in per_query.items()}
for name, frame in per_query.items():
    print(f"{name} best alpha: {best_alpha(frame)}")
    print(f"{name} best ndcg@10: {best[name].mean():.3f}")
for name in ["theoretical min-max", "z-score", "weighted rrf"]:          # each tuned, against tuned min-max
    print(f"{name} against min-max, permutation p: {compare(best[name], best['min-max'])['permutation p']:.3f}")
for name in ["min-max", "weighted rrf"]:                                 # the two blends that go to test
    gain = compare(best[name], semantic_alone)
    print(f"{name} gain over semantic: {gain['mean difference']:.3f}")
    print(f"{name} gain over semantic, permutation p: {gain['permutation p']:.3f}")
    print(f"{name} gain over semantic, t-test p: {gain['t-test p']:.3f}")
