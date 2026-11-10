from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.recorded import llm_rewrites, manifest
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

recording = manifest("llm-rewrites")
print("model:", recording["model"])
print("embedding model:", recording["embedding_model"])
print("rewrite prompt, first line:", recording["prompts"]["rewrite"].split("\n")[0])
table, rewrite_vectors, _ = llm_rewrites()
rewrites = table.set_index("query_id")["rewrite"]
row = {query_id: position for position, query_id in enumerate(table["query_id"])}
for query_id in [20, 205, 313]:
    print(f"rewrite of {load_queries().at[query_id, 'query']}: {rewrites[query_id]}")

queries, judgments = load_queries("train"), qrels("train")
products = load_products()
exact = [product_id for product_id, grade in judgments[313].items() if grade == 2]
print("exact products for malachi sled:", "; ".join(products.loc[exact, "name"]))
bm25, semantic = LexicalSearch(products), SemanticSearch()
runs = {"bm25, typed": bm25.run(queries),
        "bm25, rewrite": bm25.run(queries.assign(query=rewrites[queries.index].to_numpy())),
        "semantic, typed": semantic.run(queries),
        "semantic, rewrite": {query_id: list(semantic.search_vector(rewrite_vectors[row[query_id]]).index)
                              for query_id in queries.index}}
scores = {name: evaluate(run, judgments) for name, run in runs.items()}
for name, frame in scores.items():
    print(f"train ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
    print(f"train judged@10 {name}: {frame['judged@10'].mean():.3f}")
for retriever in ["bm25", "semantic"]:                       # for choosing, not evidence
    change = (scores[f"{retriever}, rewrite"]["ndcg@10"] - scores[f"{retriever}, typed"]["ndcg@10"]).round(3)
    print(f"train queries better, worse, {retriever}: {(change > 0).sum()}, {(change < 0).sum()}")
    print(f"largest train loss, {retriever}: {queries.at[change.idxmin(), 'query']}")
    print(f"largest train loss, {retriever}, change: {change.min():+.3f}")
