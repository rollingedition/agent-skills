import re

import bm25s
from bm25s.stopwords import STOPWORDS_EN

from lib.lexical import LexicalSearch
from lib.store import load_products, load_queries, product_text, qrels

TOKEN = re.compile(r"(?u)\b\w\w+\b")      # two or more word characters: letters, digits or underscores
STOPWORDS = set(STOPWORDS_EN)               # the 33 English stop words bm25s removes


def tokenize(text, pattern=TOKEN):
    """Lowercase, split into tokens, and drop stop words."""
    return [token for token in pattern.findall(text.lower()) if token not in STOPWORDS]


products, queries = load_products(), load_queries()
texts = product_text(products).tolist()
by_hand = [tokenize(text) for text in texts]
with_bm25s = bm25s.tokenize(texts, stopwords="en", return_ids=False, show_progress=False)
print("products tokenized differently:", sum(mine != theirs for mine, theirs in zip(by_hand, with_bm25s)))
print()
query = queries.at[62, "query"]                                    # a train query
print("query 62:", query, "->", tokenize(query))
print("product 1:", products.at[1, "name"], "->", tokenize(products.at[1, "name"]))
print("products with the term 7qt:", sum("7qt" in terms for terms in by_hand))
print("products whose text says 7 qt:", sum(re.search(r"(?<![\d.])7 qt\b", text.lower()) is not None for text in texts))   # not 3.7 qt
grades = qrels("train")[62]
print("exact products judged for query 62:", sum(grade == 2 for grade in grades.values()))
top_10 = LexicalSearch(products).search(query, k=10).index                # chapter 1's BM25
print("exact products in bm25's top 10:", sum(grades.get(product_id) == 2 for product_id in top_10))
digits_apart = re.compile(r"(?u)\d+|[^\W\d_]+")                    # keeps single digits; 7qt -> 7, qt
changed = queries["query"].map(lambda text: tokenize(text) != tokenize(text, digits_apart))
for split in ["train", "test"]:
    print(f"{split} queries whose terms change with digits apart:", changed[queries["split"] == split].sum())
print()
print("probe:", "rug not wool", "->", tokenize("rug not wool"))      # written for this chapter
print("queries with not or no:", queries["query"].str.contains(r"\b(?:not|no)\b").sum())
