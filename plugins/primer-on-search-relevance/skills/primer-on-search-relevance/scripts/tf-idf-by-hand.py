import math

import pandas as pd

from lib.lexical import LexicalSearch
from lib.lexical_by_hand import InvertedIndex, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, train, judgments = load_products(), load_queries("train"), qrels("train")
index = InvertedIndex(product_text(products))
n = len(index.lengths)                                      # 12,000 products


def tf_idf(query):
    """TF-IDF scores of the products that contain a query term, best first."""
    scores = {}
    for term in tokenize(query):
        postings = index.postings.get(term, {})
        idf = math.log(n / len(postings)) if postings else 0.0
        for product_id, tf in postings.items():
            scores[product_id] = scores.get(product_id, 0.0) + tf * idf
    return pd.Series(scores, dtype=float).sort_values(ascending=False, kind="stable")


query, labels = train.at[36, "query"], {2: "exact", 1: "partial", 0: "irrelevant"}
for term in ["furniture"] + tokenize(query):
    print(f"idf of {term}: {math.log(n / len(index.postings[term])):.3f}")
print(f"\ntf-idf top 3 for {query!r}:")
for rank, (product_id, score) in enumerate(tf_idf(query).head(3).items(), start=1):
    counts = ", ".join(f"{term} {index.postings[term].get(product_id, 0)}" for term in tokenize(query))
    print(f"  {rank}  {score:4.1f}  {labels[judgments[36][product_id]]:<8} {counts:<29} {products.at[product_id, 'name'][:22]}")
print()
runs = {"tf-idf": {query_id: list(tf_idf(text).index[:100]) for query_id, text in train["query"].items()},
        "bm25": LexicalSearch(products).run(train)}
results = {name: evaluate(run, judgments) for name, run in runs.items()}        # one row per train query
for name, frame in results.items():
    print(f"{name} train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name} train judged@10: {frame['judged@10'].mean():.3f}")
change = (results["bm25"]["ndcg@10"] - results["tf-idf"]["ndcg@10"]).round(3)
print(f"train queries where bm25 scores higher, lower: {(change > 0).sum()}, {(change < 0).sum()}")
