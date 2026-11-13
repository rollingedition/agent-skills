"""Reranks semantic retrieval's top 20 with the recorded cross-encoder scores, and compares the two on the test queries.
The prose's point rests on the planned comparison's permutation p-value, and on the judged@10 lines, which show what the
rerank does to the judgments it can score."""
from lib.metrics import evaluate
from lib.ranking import DEPTH, rerank, report_planned
from lib.recorded import cross_encoder_scores, llm_listwise, manifest
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")       # scored on the human judgments
semantic = SemanticSearch().run(queries, k=100)
recorded = cross_encoder_scores()
# the recorded score of each (query, product) pair
score = dict(zip(zip(recorded["query_id"], recorded["product_id"]), recorded["score"]))
print("cross-encoder model:", manifest("cross-encoder")["model"])
print("licence in the manifest:", manifest("cross-encoder")["model_licence"])

# the set of products the LLM was shown for each query, from the listwise recording
shown = llm_listwise().groupby("query_id")["product_id"].apply(set)  # what the LLM rerankers saw
same = sum(set(semantic[query_id][:DEPTH]) == shown[query_id] for query_id in queries.index)
print(f"rerank depth: {DEPTH}")
print(f"queries whose top {DEPTH} holds the products the llm rerankers saw: {same} of {len(queries)}")

reranked = rerank(semantic, score, DEPTH)                       # top 20 reordered, the rest in place
before, after = evaluate(semantic, judgments), evaluate(reranked, judgments)
for name, frame in [("semantic", before), ("cross-encoder", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
# index 0 is the first place
moved = sum(reranked[query_id][0] != semantic[query_id][0] for query_id in queries.index)
print(f"queries whose first product changes: {moved}")
report_planned("cross-encoder", after["ndcg@10"], before["ndcg@10"])
