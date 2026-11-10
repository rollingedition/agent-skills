import bm25s
import Stemmer

from lib.lexical_by_hand import InvertedIndex
from lib.store import load_products, load_queries, product_text

products, queries = load_products(), load_queries()
texts = product_text(products)
stemmer = Stemmer.Stemmer("english")

library = bm25s.BM25()                                            # k1=1.5, b=0.75, as in chapter 1
library.index(bm25s.tokenize(texts.tolist(), stopwords="en", stemmer=stemmer, show_progress=False),
              show_progress=False)
by_hand = InvertedIndex(texts, stem=True)

gaps = []
for query in queries["query"]:
    tokens = bm25s.tokenize([query], stopwords="en", stemmer=stemmer, return_ids=False, show_progress=False)[0]
    scores = library.get_scores(tokens)                           # every product, in catalog order
    gaps.append(abs(by_hand.search(query, k=len(products)).reindex(products.index, fill_value=0) - scores).max())
print("query terms for pool floats:", bm25s.tokenize(["pool floats"], stopwords="en", stemmer=stemmer,
                                                     return_ids=False, show_progress=False)[0])
print(f"largest score difference from bm25s with a stemmer: {max(gaps):.0e}")
