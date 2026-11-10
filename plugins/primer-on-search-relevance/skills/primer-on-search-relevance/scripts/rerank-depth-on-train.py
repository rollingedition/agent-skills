from lib.metrics import evaluate
from lib.ranking import rerank
from lib.recorded import cross_encoder_scores
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")      # choosing a depth is tuning: train queries
semantic = SemanticSearch().run(queries, k=100)
recorded = cross_encoder_scores()
score = dict(zip(zip(recorded["query_id"], recorded["product_id"]), recorded["score"]))
train_pairs = recorded[recorded["query_id"].isin(queries.index)]

print(f"depth 0 (semantic alone), train ndcg@10: {evaluate(semantic, judgments)['ndcg@10'].mean():.3f}")
previous = round(evaluate(semantic, judgments)["ndcg@10"].mean(), 3)     # changes between the printed values
for depth in [5, 10, 20, 30, 50, 75]:
    mean = round(evaluate(rerank(semantic, score, depth), judgments)["ndcg@10"].mean(), 3)
    print(f"depth {depth}, train ndcg@10: {mean:.3f}")
    print(f"depth {depth}, change from the depth before: {mean - previous:+.3f}")
    previous = mean
print(f"pairs per query to score every candidate, median: {train_pairs.groupby('query_id').size().median():.0f}")
