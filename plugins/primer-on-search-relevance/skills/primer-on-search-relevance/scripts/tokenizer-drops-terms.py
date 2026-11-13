"""Tokenizes one train query, one test query and the products' text with bm25s, and counts the products that have `chairs` or only `chair`. The prose's points rest on the printed token lists and on the two product counts."""
import bm25s

from lib.store import load_products, product_text


def tokenize(texts):
    """The tokenizer lib.lexical uses for products and queries, with bm25s's default settings."""
    # stopwords="en" removes English words such as "and"; no stemmer is set, so "chairs" and "chair" stay different tokens
    return bm25s.tokenize(texts, stopwords="en", return_ids=False, show_progress=False)


for query in ["ge top loading washer 4.5", "bistro table and chairs"]:
    print(f"{query!r} -> {tokenize([query])[0]}")

products = tokenize(product_text(load_products()).tolist())
print()
print("products with the token chairs:", sum("chairs" in tokens for tokens in products))
print("products with chair but not chairs:", sum("chair" in tokens and "chairs" not in tokens for tokens in products))
