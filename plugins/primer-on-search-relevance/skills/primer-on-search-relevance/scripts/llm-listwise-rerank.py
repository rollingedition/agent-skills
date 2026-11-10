from lib.metrics import evaluate
from lib.ranking import DEPTH, report_planned
from lib.recorded import llm_listwise, manifest
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")       # scored on the human judgments, not the LLM's
semantic = SemanticSearch().run(queries, k=100)
answers = llm_listwise()                                        # one call per query and order shown
calls = answers.drop_duplicates(["query_id", "order"])
print(f"listwise calls, both orders: {len(calls)}")
print(f"answers that needed repair: {(~calls['valid']).sum()}")
print(f"products per call: {answers.groupby(['query_id', 'order']).size().max()}")
print("prompt asks for:", manifest("llm-rerank")["prompts"]["listwise"].splitlines()[-1].replace("{n}", str(DEPTH)))

shown_in_semantic_order = answers[answers["order"] == "semantic"].sort_values(["query_id", "position"])
order = shown_in_semantic_order.groupby("query_id")["product_id"].apply(list)
reranked = {query_id: order[query_id] + ranking[DEPTH:] for query_id, ranking in semantic.items()}
before, after = evaluate(semantic, judgments), evaluate(reranked, judgments)
for name, frame in [("semantic", before), ("llm listwise", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
moved = sum(reranked[query_id][0] != semantic[query_id][0] for query_id in queries.index)
print(f"queries whose first product changes: {moved}")
report_planned("llm listwise", after["ndcg@10"], before["ndcg@10"])
