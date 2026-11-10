from collections import Counter

from lib.lexical_by_hand import tokenize
from lib.store import load_products, load_queries, product_text

postings = {}       # {term: {product_id: how many times the term occurs in that product}}
lengths = {}        # {product_id: number of terms}
for product_id, text in product_text(load_products()).items():
    terms = tokenize(text)
    lengths[product_id] = len(terms)
    for term, count in Counter(terms).items():
        postings.setdefault(term, {})[product_id] = count

print(f"vocabulary: {len(postings):,} terms")
print(f"average product length: {sum(lengths.values()) / len(lengths):.1f} terms")
print("postings for cooker, first 3:", list(postings["cooker"].items())[:3])
print()
query = load_queries().at[62, "query"]
for term in tokenize(query):
    print(f"products with {term}:", len(postings.get(term, {})))
found = [set(postings.get(term, {})) for term in tokenize(query)]
print("products with any query term:", len(set.union(*found)))
print("products with every query term:", len(set.intersection(*found)))
print("products with w003096809:", len(postings.get("w003096809", {})))    # the code in query 205
