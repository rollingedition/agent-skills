"""Compares the top 10s of two probe queries that differ only in a code no product holds, and shows where one product ranks for two resolutions, semantically and with BM25. The prose's point rests on the shared-top-10 line for the code and on the rank lines for the resolutions."""
from lib.lexical import LexicalSearch
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, product_text

# Probe queries written for the book, embedded by the same model; no judgments, so nothing is scored.
probe_queries, probe_vectors = probes()
products = load_products()
text = product_text(products).str.lower()
semantic, bm25 = SemanticSearch(), LexicalSearch(products)

# A code no product holds: does changing it change the results?
first, second = probe_queries.index[probe_queries["pair"] == "code"]
tops = [set(semantic.search_vector(probe_vectors[row], k=10).index) for row in (first, second)]
print("products whose text contains w003096809:", text.str.contains("w003096809").sum())
print(f"code, similarity of the two queries: {probe_vectors[first] @ probe_vectors[second]:.3f}")
print("code, products in both top 10s:", len(tops[0] & tops[1]))

# A code one product holds: where does that product rank, with its code and with another?
holder = text.index[text.str.contains("1920x1080p")]
print()
print("products whose text contains 1920x1080p:", len(holder))
print("that product:", products.at[holder[0], "name"])
print("products in the Projectors class:", (products["product_class"] == "Projectors").sum())
for row in probe_queries.index[probe_queries["pair"] == "resolution"]:
    query = probe_queries.at[row, "query"]
    ranked = semantic.search_vector(probe_vectors[row], k=len(products))  # ranks every product, so the rank is exact
    lexical = list(bm25.search(query, k=100).index)  # BM25 ranks are read from its top 100 only
    print(f"{query}, its semantic rank: {list(ranked.index).index(holder[0]) + 1}")  # ranks count from 1
    print(f"{query}, its similarity: {ranked[holder[0]]:.3f}")
    # the best product other than this one
    print(f"{query}, similarity of the next product: {ranked.drop(holder[0]).iloc[0]:.3f}")
    print(f"{query}, its bm25 rank:", lexical.index(holder[0]) + 1 if holder[0] in lexical else "not in the top 100")
