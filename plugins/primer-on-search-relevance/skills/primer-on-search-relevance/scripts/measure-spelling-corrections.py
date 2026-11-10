from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.queries import correct_query, word_counts
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

products, queries, judgments = load_products(), load_queries(), qrels()
counts = word_counts(product_text(products))
bm25, semantic = LexicalSearch(products), SemanticSearch()
probe_queries, probe_vectors = probes()      # recorded embeddings of the four typo queries, spelled correctly
spelling = probe_queries[probe_queries["kind"] == "spelling"]
spelled = {row["query"]: probe_vectors[index] for index, row in spelling.iterrows()}
typo_queries = spelling["of_query_id"].astype(int).tolist()
print("typo queries:", len(typo_queries))
print("of them, test queries:", (queries.loc[typo_queries, "split"] == "test").sum())

for query_id in typo_queries + [459]:        # the typo queries, then the one variant spelling, tye dye
    typed = queries.at[query_id, "query"]
    corrected = correct_query(typed, counts)
    label = f"{query_id} ({queries.at[query_id, 'split']})"
    print(f"{label}: {typed} -> {corrected}")
    for name, text in [("typed", typed), ("corrected", corrected)]:
        ranking = list(bm25.search(text, k=10).index)
        print(f"{label}, bm25 ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
    if corrected == typed.lower():
        print(f"{label}: the corrector changes nothing")
    elif corrected in spelled:
        for name, vector in [("typed", semantic.query_vectors[query_id]), ("corrected", spelled[corrected])]:
            ranking = list(semantic.search_vector(vector, k=10).index)
            print(f"{label}, semantic ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
    else:
        print(f"{label}: no recorded embedding of the corrected text")
