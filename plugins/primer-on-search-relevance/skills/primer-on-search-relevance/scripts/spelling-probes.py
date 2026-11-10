from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

# Each spelling probe is the correctly spelled text of one store query (of_query_id), embedded by the same
# model. It asks for the same thing, so it is scored with that query's judgments. A diagnosis, not a test.
probe_queries, probe_vectors = probes()
products, queries, judgments = load_products(), load_queries(), qrels()
semantic, bm25 = SemanticSearch(), LexicalSearch(products)

spelling = probe_queries[probe_queries["kind"] == "spelling"]
for row, probe in spelling.iterrows():
    query_id, pair = int(probe["of_query_id"]), probe["pair"]
    typed, corrected = semantic.search(query_id, k=10).index, semantic.search_vector(probe_vectors[row], k=10).index
    print(f"{pair}: {queries.at[query_id, 'query']} | {probe['query']} ({queries.at[query_id, 'split']} query)")
    print(f"{pair}, similarity of the two spellings: {semantic.query_vectors[query_id] @ probe_vectors[row]:.3f}")
    print(f"{pair}, products in both semantic top 10s:", len(set(typed) & set(corrected)))
    print(f"{pair}, semantic ndcg@10 as typed: {ndcg_at_k(list(typed), judgments[query_id], 10):.3f}")
    print(f"{pair}, semantic ndcg@10 corrected: {ndcg_at_k(list(corrected), judgments[query_id], 10):.3f}")
    for name, text in [("as typed", queries.at[query_id, "query"]), ("corrected", probe["query"])]:
        print(f"{pair}, bm25 ndcg@10 {name}: {ndcg_at_k(list(bm25.search(text, k=10).index), judgments[query_id], 10):.3f}")
    print()
print("spelling probes:", len(spelling))
print(f"smallest two-sided permutation p-value possible with {len(spelling)} queries: {2 / 2 ** len(spelling):.3f}")
