from lib.metrics import evaluate
from lib.ranking import DEPTH, rerank, report_planned
from lib.recorded import llm_pointwise, manifest
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")       # scored on the human judgments, not the LLM's
semantic = SemanticSearch().run(queries, k=100)
answers = llm_pointwise()                                       # one call per product: a label and a score
print("llm:", manifest("llm-rerank")["model"])
print("licence in the manifest:", manifest("llm-rerank")["model_licence"])
print(f"calls per query: {len(answers) // answers['query_id'].nunique()}")
print(f"answers without a score: {answers['score'].isna().sum()}")
print(f"distinct scores per query, median: {answers.groupby('query_id')['score'].nunique().median():.0f}")
print(f"share of products scored 100: {(answers['score'] == 100).mean():.3f}")
people = answers.apply(lambda row: judgments[row["query_id"]].get(row["product_id"]), axis=1)
for label, grade in [("exact", 2), ("partial", 1), ("irrelevant", 0)]:
    print(f"products the llm labels {label}: {(answers['label'] == label).sum()}")
    print(f"products people judged {label}: {(people == grade).sum()}")
print(f"products nobody judged: {people.isna().sum()}")

score = dict(zip(zip(answers["query_id"], answers["product_id"]), answers["score"]))
reranked = rerank(semantic, score, DEPTH)                       # equal scores keep semantic retrieval's order
counts = answers.groupby("query_id")["score"].value_counts()          # products per score, for each query
shared = {query_id: sum(counts[(query_id, score[(query_id, product_id)])] > 1 for product_id in reranked[query_id][:10])
          for query_id in queries.index}                                # top-10 products that share their score
print(f"queries where most of the reranked top 10 shares its score: {sum(n > 5 for n in shared.values())}")
before, after = evaluate(semantic, judgments), evaluate(reranked, judgments)
for name, frame in [("semantic", before), ("llm pointwise", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
report_planned("llm pointwise", after["ndcg@10"], before["ndcg@10"])
