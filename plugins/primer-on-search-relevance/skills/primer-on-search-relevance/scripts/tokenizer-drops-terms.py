import bm25s

from lib.store import load_products, product_text


def tokenize(texts):
    """The tokenizer lib.lexical uses for products and queries, with bm25s's default settings."""
    return bm25s.tokenize(texts, stopwords="en", return_ids=False, show_progress=False)


for query in ["ge top loading washer 4.5", "bistro table and chairs"]:
    print(f"{query!r} -> {tokenize([query])[0]}")

products = tokenize(product_text(load_products()).tolist())
print()
print("products with the token chairs:", sum("chairs" in tokens for tokens in products))
print("products with chair but not chairs:", sum("chair" in tokens and "chairs" not in tokens for tokens in products))
