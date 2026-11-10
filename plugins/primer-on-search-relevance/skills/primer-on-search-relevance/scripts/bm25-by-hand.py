import math

import pandas as pd

from lib.lexical import LexicalSearch
from lib.lexical_by_hand import InvertedIndex, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, queries = load_products(), load_queries()
index, library = InvertedIndex(product_text(products)), LexicalSearch(products)  # by hand, and bm25s as chapter 1 uses it
n, k1, b = len(index.lengths), 1.5, 0.75


def bm25(query):
    scores = {}
    for term in tokenize(query):
        df = len(index.postings.get(term, {}))
        idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
        for product_id, tf in index.postings.get(term, {}).items():
            length = 1 - b + b * index.lengths[product_id] / index.average_length
            scores[product_id] = scores.get(product_id, 0.0) + idf * tf / (tf + k1 * length)
    return pd.Series(scores, dtype=float)


df = len(index.postings["your"])
print(f"products with your: {df:,}")
print(f"robertson idf of your: {math.log((n - df + 0.5) / (df + 0.5)):.3f}")
print(f"lucene idf of your: {math.log(1 + (n - df + 0.5) / (df + 0.5)):.3f}")
for tf in [1, 2, 4, 9]:                                   # one term, in a product of average length
    print(f"term weight at tf {tf}: {tf / (tf + k1):.3f}")
gaps = [(bm25(query).reindex(products.index, fill_value=0) - library.retriever.get_scores(tokenize(query))).abs().max()
        for query in queries["query"]]
print(f"\nlargest score difference from bm25s: {max(gaps):.0e}")
print("bm25s score type:", library.retriever.get_scores(["chair"]).dtype)
ranked = {query_id: list(bm25(query).sort_index().sort_values(ascending=False, kind="stable").index[:100])
          for query_id, query in queries["query"].items()}         # equal scores in product_id order
library_ranked = library.run(queries)                     # lib.lexical also orders equal scores by product_id
print("same top 100 for every query:", "yes" if ranked == library_ranked else "no")
for split in ["train", "test"]:
    for name, run in [("by hand", ranked), ("with bm25s", library_ranked)]:
        print(f"{split} ndcg@10 {name}: {evaluate(run, qrels(split))['ndcg@10'].mean():.3f}")
