import numpy as np

from lib.blend import best_alpha, scores_by_alpha, weighted_rrf
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries(), qrels()                  # all 80 queries, train and test
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
per_query = scores_by_alpha(lambda weight: weighted_rrf(bm25, semantic, weight), judgments)   # nDCG@10, a column per weight
train = per_query.loc[load_queries("train").index]
test = per_query.loc[load_queries("test").index]

chosen_on_train, chosen_on_test = best_alpha(train), best_alpha(test)
print("settings tried:", per_query.shape[1])
print(f"semantic alone, test ndcg@10: {test[1.0].mean():.3f}")
print("semantic weight chosen on train:", chosen_on_train)
print(f"test ndcg@10, weight chosen on train: {test[chosen_on_train].mean():.3f}")
print("semantic weight chosen on test:", chosen_on_test)
print(f"test ndcg@10, weight chosen on test: {test[chosen_on_test].mean():.3f}")

# How much does choosing on the queries you report inflate the score? Split the train queries
# at random, 30 to choose on and 20 to report on, and compare the two ways of choosing.
rng = np.random.default_rng(2026)
scores = train.to_numpy()
inflation = []
for _ in range(1000):
    order = rng.permutation(len(scores))
    choose, report = scores[order[:30]].mean(axis=0), scores[order[30:]].mean(axis=0)
    inflation.append(report.max() - report[choose.argmax()])
print(f"average inflation, 20 reported queries: {np.mean(inflation):.3f}")
