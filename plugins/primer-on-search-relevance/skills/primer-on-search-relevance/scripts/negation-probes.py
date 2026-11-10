import bm25s

from lib.lexical import LexicalSearch
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text

# Probe queries written for the book, with no judgments: count what the top 10 holds, never score it.
probe_queries, probe_vectors = probes()
products = load_products()
names, text = products["name"].str.lower(), product_text(products).str.lower()
semantic, bm25 = SemanticSearch(), LexicalSearch(products)
FEATURES = {"arms": ("armless", names), "glass": ("glass", text), "round": ("round", names)}

negated = load_queries()["query"].str.contains(r"\b(?:no|not|without|non)\b")
print("store queries with no, not, without or non:", negated.sum())
tokens = bm25s.tokenize(["rug that is not round"], stopwords="en", return_ids=False, show_progress=False)
print("bm25 terms of rug that is not round:", " ".join(tokens[0]))
print("products named armless:", names.str.contains(r"\barmless\b").sum())
coffee_tables = products["product_class"] == "Coffee & Cocktail Tables"
area_rugs = products["product_class"] == "Area Rugs"
print("coffee tables that never mention glass:", (coffee_tables & ~text.str.contains(r"\bglass\b")).sum())
print("area rugs not named round:", (area_rugs & ~names.str.contains(r"\bround\b")).sum())

negation = probe_queries[probe_queries["kind"] == "negation"]
print("negation probe pairs:", negation["pair"].nunique())
for row, probe in negation.iterrows():
    word, field = FEATURES[probe["pair"]]
    has_feature = field.str.contains(rf"\b{word}\b")
    semantic_top = semantic.search_vector(probe_vectors[row], k=10).index
    bm25_top = bm25.search(probe["query"], k=10).index
    print()
    print(f"{probe['query']}, semantic top 10 with {word}:", has_feature[semantic_top].sum())
    print(f"{probe['query']}, bm25 top 10 with {word}:", has_feature[bm25_top].sum())
