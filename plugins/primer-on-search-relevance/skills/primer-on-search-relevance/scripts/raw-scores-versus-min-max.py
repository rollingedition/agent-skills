from lib.blend import candidates, weighted_sum
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
lexical, semantic = LexicalSearch(products), SemanticSearch()
tables = candidates(lexical, semantic, queries)              # both scores for each query's candidates

table = tables[36]                                           # laundry basket with wheels
print("candidates for laundry basket with wheels:", len(table))
print(f"bm25 range: {table['bm25'].min():.3f} to {table['bm25'].max():.3f}")
print(f"similarity range: {table['similarity'].min():.3f} to {table['similarity'].max():.3f}")


def min_max(scores):
    return (scores - scores.min()) / (scores.max() - scores.min())


def blend(normalize, alpha=0.5):
    run = {}
    for query_id, table in tables.items():
        score = alpha * normalize(table["similarity"]) + (1 - alpha) * normalize(table["bm25"])
        run[query_id] = list(score.sort_values(ascending=False, kind="stable").index[:100])
    return run


top_10s = {"bm25": lexical.run(queries, k=10), "semantic": semantic.run(queries, k=10)}
per_query = {}
for name, normalize in [("raw", lambda scores: scores), ("min-max", min_max)]:
    run = blend(normalize)
    per_query[name] = evaluate(run, judgments)["ndcg@10"]
    print(f"{name} sum ndcg@10: {per_query[name].mean():.3f}")
    for other, top in top_10s.items():
        shared = [len(set(run[query_id][:10]) & set(top[query_id])) for query_id in queries.index]
        print(f"{name} sum, products shared with the {other} top 10: {sum(shared) / len(shared):.1f}")
by_hand, library = blend(min_max), weighted_sum(tables, 0.5)
matches = sum(by_hand[query_id] == library[query_id] for query_id in tables)
print(f"train queries ranked as lib.blend.weighted_sum ranks them: {matches} of {len(tables)}")
p_value = compare(per_query["min-max"], per_query["raw"])["permutation p"]          # a tuning check on train
print("min-max minus raw, permutation p:", "below 0.001" if p_value < 0.001 else f"{p_value:.3f}")
