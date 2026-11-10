from bm25s.stopwords import STOPWORDS_EN

from lib.lexical import LexicalSearch
from lib.metrics import evaluate, ndcg_at_k
from lib.queries import rewrite_runs
from lib.recorded import llm_rewrites, probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products())
rewrites = llm_rewrites()[0].set_index("query_id")["rewrite"]
largest = {}
for retriever, (rewritten, typed) in rewrite_runs(queries, bm25, SemanticSearch()).items():
    change = evaluate(rewritten, judgments)["ndcg@10"] - evaluate(typed, judgments)["ndcg@10"]
    for kind, query_id in [("loss", change.idxmin()), ("gain", change.idxmax())]:
        label, largest[(retriever, kind)] = f"{retriever}, largest {kind}", query_id
        print(f"{label}: {queries.at[query_id, 'query']}")
        print(f"{label}, change: {change[query_id]:+.3f}")
        print(f"{label}, rewrite: {rewrites[query_id]}")
        unjudged = sum(product_id not in judgments[query_id] for product_id in rewritten[query_id][:10])
        print(f"{label}, unjudged products in the rewrite's top 10: {unjudged}")

# BM25's largest gain: score the query with only its spelling fixed (chapter 6's probe), apart from the added words
query_id = largest[("bm25", "gain")]
spelled = probes()[0].dropna(subset=["of_query_id"]).set_index("of_query_id")["query"]
if query_id in spelled.index:
    for name, text in [("typed", queries.at[query_id, "query"]), ("spelling fixed only", spelled[query_id])]:
        ranking = list(bm25.search(text, k=10).index)
        print(f"bm25, largest gain, ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
    print("bm25 stop words among an and and:", ", ".join(word for word in ["an", "and"] if word in STOPWORDS_EN))
