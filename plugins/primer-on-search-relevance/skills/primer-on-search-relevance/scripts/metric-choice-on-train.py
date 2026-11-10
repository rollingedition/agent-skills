from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # choosing a metric is tuning: use train
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}

exponential = {query_id: {product_id: 2 ** grade - 1 for product_id, grade in per_query.items()}
               for query_id, per_query in judgments.items()}       # gains 0, 1, 3 instead of 0, 1, 2
means = {}
for name, run in runs.items():
    scores = evaluate(run, judgments)
    means[name] = {"precision@10": scores["precision@10"].mean(), "mrr": scores["rr"].mean(),
                   "ndcg@10": scores["ndcg@10"].mean(),
                   "ndcg@10 with exponential gains": evaluate(run, exponential)["ndcg@10"].mean()}

print("train queries:", len(judgments))
winners = []
for metric in means["semantic"]:
    for name in runs:
        print(f"{name} {metric}: {means[name][metric]:.3f}")
    winners.append(max(runs, key=lambda name: means[name][metric]))
    print(f"higher {metric}: {winners[-1]}")
for name in runs:
    print(f"metrics won by {name}:", winners.count(name))
print(f"largest gap: {max(abs(means['semantic'][m] - means['hybrid'][m]) for m in means['semantic']):.3f}")
