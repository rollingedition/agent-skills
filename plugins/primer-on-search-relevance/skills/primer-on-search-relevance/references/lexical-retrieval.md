---
title: "A Primer on Search Relevance"
chapter: "Lexical retrieval"
chapter_id: lexical-retrieval
book: primer-on-search-relevance
edition: 2026.11.8
verified: 2026-11-13
edition_code: W7B6-3VSA
canonical: https://rollingedition.com/primer-on-search-relevance/lexical-retrieval
license: CC BY 4.0
attribution: "“Lexical retrieval,” chapter 5 of A Primer on Search Relevance, Edition 2026.11.8, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/lexical-retrieval. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Lexical retrieval

By the end of this chapter you can build lexical search from scratch: turn product text into terms, index the terms, and score products with TF-IDF and BM25, matching the bm25s library score for score. You can also decide which changes to the text processing and to BM25's parameters are worth keeping, by choosing on train queries and checking on test queries.

**Lexical retrieval** finds and ranks products by the words they share with the query. It ranks results when a shopper searches [the store](#store-data)'s furniture and home goods: BM25, through the bm25s library. When a shopper types `7qt slow cooker` or `pool floats`, the results of [chapter 1](#rank-with-bm25)'s BM25 are weak. Its mean [nDCG@10](#score-one-ranking) on the test queries, 0.725, shows that, but not why, because chapter 1 used it as a black box at bm25s's defaults. This chapter opens the box. You rebuild each step by hand on the store's 12,000 products and check it against bm25s, then change one step at a time and measure each change against the store's [judgments](#store-data).

Each change is chosen on the 50 [train queries](#store-data) and checked on the 30 test queries. Before reading any test result, the chapter fixes its planned comparisons on the test queries. There are five, each against the same search without the change:

1. [stemming](#check-stemming-on-test)
2. the best `k1` and `b` on train, against bm25s's defaults ([tuning](#tune-bm25-parameters))
3. the best weight on train for the product name ([fields](#weight-the-product-name))
4. product attributes as a field ([attributes](#index-attributes-as-a-field))
5. the best phrase bonus on train ([phrases](#match-phrases-with-positions))

With five planned comparisons, [the book's rule](#when-a-difference-is-established) sets the bar at a p-value of 0.01. A gain is established if the paired [permutation test](#permutation-test-on-queries) gives a p-value below that bar. Each comparison also reports the paired [t-test](#paired-t-test-on-queries) and a 99% [bootstrap interval](#report-the-size-of-a-gap), and says whether each agrees with the permutation test.

## Split product text into terms {#split-text-into-terms}

Search never compares raw strings. The query and every product's text first go through the same steps. Splitting the text into pieces gives **tokens**. Lowercasing makes `Chair` and `chair` one token. Removing **stop words**, very common words such as `the` and `with`, leaves the **terms** that search compares, and all the terms in the catalog form its **vocabulary**. A product can only match a query on terms they share, so these steps decide what can match at all, before any scoring starts.

bm25s, which runs the store's BM25, makes three choices here. It lowercases. It keeps every run of two or more word characters, which are letters, digits or underscores, with the regular expression `(?u)\b\w\w+\b`, which its docstring describes as the method of scikit-learn's `CountVectorizer`. And it removes 33 English stop words, among them `no`, `not`, `with` and `for`. It doesn't stem words unless you pass it a stemmer ([bm25s tokenizer](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/tokenization.py), [stop words](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/stopwords.py)). To see the steps one at a time, write them out by hand, check the result against `bm25s.tokenize` on every product, and run the train query `7qt slow cooker` through them:

Example `tokenize-product-text` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Splits product text into terms by hand, checks the split against bm25s on every product, then shows what the store's sizes and a negation turn into. The prose's point rests on the line that counts products tokenized differently, and on the lines that count products with the term 7qt and products whose text says 7 qt."""
import re

import bm25s
from bm25s.stopwords import STOPWORDS_EN

from lib.lexical import LexicalSearch
from lib.store import load_products, load_queries, product_text, qrels

# two or more word characters (letters, digits or underscores): a single character, such as the 7 in 7 qt, is no token
TOKEN = re.compile(r"(?u)\b\w\w+\b")
STOPWORDS = set(STOPWORDS_EN)               # the 33 English stop words bm25s removes


def tokenize(text, pattern=TOKEN):
    """Lowercase, split into tokens, and drop stop words."""
    return [token for token in pattern.findall(text.lower()) if token not in STOPWORDS]


products, queries = load_products(), load_queries()
texts = product_text(products).tolist()
by_hand = [tokenize(text) for text in texts]
# bm25s's own split, with stopwords="en": the same 33 words as STOPWORDS above
with_bm25s = bm25s.tokenize(texts, stopwords="en", return_ids=False, show_progress=False)
print("products tokenized differently:", sum(mine != theirs for mine, theirs in zip(by_hand, with_bm25s)))
print()
query = queries.at[62, "query"]                                    # a train query
print("query 62:", query, "->", tokenize(query))
print("product 1:", products.at[1, "name"], "->", tokenize(products.at[1, "name"]))
print("products with the term 7qt:", sum("7qt" in terms for terms in by_hand))
# a 7 on its own: the lookbehind skips 27 qt and 3.7 qt, which are other sizes
print("products whose text says 7 qt:", sum(re.search(r"(?<![\d.])7 qt\b", text.lower()) is not None for text in texts))
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
# whole words, so note and nothing don't count
print("queries with not or no:", queries["query"].str.contains(r"\b(?:not|no)\b").sum())
```

Output:

```text
products tokenized differently: 0

query 62: 7qt slow cooker -> ['7qt', 'slow', 'cooker']
product 1: all-clad 7 qt . slow cooker -> ['all', 'clad', 'qt', 'slow', 'cooker']
products with the term 7qt: 0
products whose text says 7 qt: 8
exact products judged for query 62: 9
exact products in bm25's top 10: 1
train queries whose terms change with digits apart: 4
test queries whose terms change with digits apart: 0

probe: rug not wool -> ['rug', 'wool']
queries with not or no: 0
```

The number of products that the hand-written tokenizer and bm25s split differently is 0, so the trouble isn't in either one: it's in the rules they share. A shopper who types `7qt slow cooker` wants a 7-quart cooker, and `7qt` does survive as one token. But it matches 0 products, because product text writes the size apart, as `7 qt` in 8 products, and the tokenizer drops the one-character `7`. So the size plays no part in the ranking, on either side of the match, and BM25 can't tell a 7-quart cooker from any other slow cooker. Of the 9 products the judges marked [exact](#store-data) for this query, BM25's top 10 holds 1.

A pattern that keeps single digits and splits numbers from their units, `(?u)\d+|[^\W\d_]+`, changes the terms of 4 train queries and 0 test queries, so the store's judgments can say little about it.

The stop list fails the same way, and bm25s raises no error. Take `rug not wool`, a **probe query**: one written for this chapter to test a behaviour, not one of the store's queries. It becomes `rug wool`, so a wool rug matches both of its terms. The judgments can measure this harm only on queries with a negation, and 0 of the store's queries contain `not` or `no`. Search systems have moved from long stop lists to short ones or none, in part because stop words carry meaning in some queries, and in part because keeping them has become cheap ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/dropping-common-terms-stop-words-1.html)).

**Working rule:** Print the terms that your queries and products become before you tune any scoring, and run both through the same tokenizer. Start from bm25s's defaults, as the store does. When shoppers type sizes, quantities or model numbers, use a token pattern that keeps single digits and splits a number from its unit, such as the one above. When they type negations, turn the stop list off. Each is a change to search, so measure it on the [train queries](#store-data) and check it on test queries before you keep it.

## Build an inverted index {#build-an-inverted-index}

To score a query made of [those terms](#split-text-into-terms), search needs the products that contain each one. Reading every product's text for every query works for a small sample, but not for a catalog of millions. An **inverted index** turns the texts around: for each term, it keeps the list of products that contain it, called the term's **postings** ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/a-first-take-at-building-an-inverted-index-1.html)). With each product, the postings store the **term frequency**, the number of times the term occurs in that product's text. The number of products in a term's postings is its **document frequency**: search engines call the items they search documents, and in this book they are products. A query reads only the postings of its own terms.

The store's index maps each term to a dictionary of product IDs and term frequencies. It also keeps each product's length in terms, which [BM25](#bm25-from-scratch) needs. Building it takes one pass over every product's text, with the tokenizer from [the previous section](#split-text-into-terms). Then the code looks up the terms of the train query `7qt slow cooker`:

Example `inverted-index-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Builds the store's inverted index by hand from each product's tokenized text, then looks up a train query's terms in it. The prose's point rests on the lines that count products with every query term and with any query term, and on the line for the product code."""
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
# (product ID, term frequency) pairs, starting from product 1
print("postings for cooker, first 3:", list(postings["cooker"].items())[:3])
print()
query = load_queries().at[62, "query"]
for term in tokenize(query):
    print(f"products with {term}:", len(postings.get(term, {})))
found = [set(postings.get(term, {})) for term in tokenize(query)]
print("products with any query term:", len(set.union(*found)))
print("products with every query term:", len(set.intersection(*found)))
print("products with w003096809:", len(postings.get("w003096809", {})))    # the code in query 205
```

Output:

```text
vocabulary: 20,393 terms
average product length: 50.3 terms
postings for cooker, first 3: [(1, 3), (2, 2), (115, 1)]

products with 7qt: 0
products with slow: 157
products with cooker: 141
products with any query term: 158
products with every query term: 0
products with w003096809: 0
```

The store's 12,000 products use 20,393 terms, and a product's text averages 50.3 terms. Each pair in the postings for `cooker` is a product ID and a term frequency. The first is product 1, the 7 qt slow cooker from [the tokenizer section](#split-text-into-terms).

For `7qt slow cooker`, the postings list 157 products for `slow`, 141 for `cooker` and 0 for `7qt`, and together they cover 158 products. Those are all that scoring this query has to read. The products that hold all three terms come to 0, because none has `7qt`. So a Boolean AND query, which returns only the products that contain every query term, returns nothing for this query. A search that scores every product containing any of the terms, as BM25 does, still returns slow cookers, and leaves it to the scores to decide which come first.

**Working rule:** When a query's results look wrong, look up its terms in the index before you change the scoring. A term with no postings, such as `7qt`, can't help any product whatever the scorer does, so fix the tokenizer or the query instead. For queries that shoppers type, match products that contain any of the terms rather than all of them, because one unmatched word would otherwise empty the results. Serve from a library's index, and keep a small one like this to check what a term matches.

## Weight terms with TF-IDF {#weight-terms-with-tf-idf}

Not every match is worth the same. Two ideas weight them. A term that occurs often in a product's text is more likely to be what the product is about: that is its term frequency, tf. And a match on a rare term says more than a match on a common one. Karen Spärck Jones proposed weighting terms by how many documents contain them, so that "matches on less frequent, more specific, terms are of greater value than matches on frequent terms" ([Spärck Jones, 1972](https://doi.org/10.1108/eb026526); [free reprint](http://www.staff.city.ac.uk/~sbrp622/idfpapers/ksj_orig.pdf)). That weight became the **inverse document frequency**, IDF: the logarithm of the number of products divided by the term's document frequency, high for a rare term and low for a common one ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/inverse-document-frequency-1.html)). TF-IDF multiplies the two for each query term and adds them up ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/tf-idf-weighting-1.html)):

```text
idf(t)       = ln(N / df(t))                        N products, df(t) of them contain t
tf-idf(q, d) = sum over query terms t of  tf(t, d) × idf(t)
```

`furniture` is a common term in the store's products. TF-IDF builds on the [inverted index](#build-an-inverted-index). The code shows the IDF of `furniture` and of each term in the train query `laundry basket with wheels`, then TF-IDF's top 3 for that query, with each product's score and term frequencies. Last, it scores all 50 train queries with TF-IDF and with [BM25 as chapter 1 runs it](#rank-with-bm25):

Example `tf-idf-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Computes TF-IDF over the inverted index, shows the IDF of each term of one train query and TF-IDF's top 3 for it, then scores every train query with TF-IDF and with BM25. The prose's point rests on the train nDCG@10 and judged@10 lines, and on the line that counts the queries where BM25 scores higher or lower."""
import math

import pandas as pd

from lib.lexical import LexicalSearch
from lib.lexical_by_hand import InvertedIndex, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, train, judgments = load_products(), load_queries("train"), qrels("train")
index = InvertedIndex(product_text(products))
n = len(index.lengths)                                      # every product, the N in the IDF formula


def tf_idf(query):
    """TF-IDF scores of the products that contain a query term, best first."""
    scores = {}
    for term in tokenize(query):
        postings = index.postings.get(term, {})
        # a term no product contains has no postings, so it adds nothing to any score
        idf = math.log(n / len(postings)) if postings else 0.0
        for product_id, tf in postings.items():
            scores[product_id] = scores.get(product_id, 0.0) + tf * idf
    # stable: tied products keep the order in which they were first scored
    return pd.Series(scores, dtype=float).sort_values(ascending=False, kind="stable")


# train query 36, by its ID; judgments grade 2, 1 and 0 as exact, partial and irrelevant
query, labels = train.at[36, "query"], {2: "exact", 1: "partial", 0: "irrelevant"}
for term in ["furniture"] + tokenize(query):
    print(f"idf of {term}: {math.log(n / len(index.postings[term])):.3f}")
print(f"\ntf-idf top 3 for {query!r}:")
for rank, (product_id, score) in enumerate(tf_idf(query).head(3).items(), start=1):
    counts = ", ".join(f"{term} {index.postings[term].get(product_id, 0)}" for term in tokenize(query))
    print(f"  {rank}  {score:4.1f}  {labels[judgments[36][product_id]]:<8} {counts:<29} {products.at[product_id, 'name'][:22]}")
print()
# the top 100 of each scorer on every train query; bm25 is chapter 1's, from lib.lexical
runs = {"tf-idf": {query_id: list(tf_idf(text).index[:100]) for query_id, text in train["query"].items()},
        "bm25": LexicalSearch(products).run(train)}
results = {name: evaluate(run, judgments) for name, run in runs.items()}        # one row per train query
for name, frame in results.items():
    print(f"{name} train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name} train judged@10: {frame['judged@10'].mean():.3f}")
# rounded to three decimals, so a difference too small to show counts as a tie
change = (results["bm25"]["ndcg@10"] - results["tf-idf"]["ndcg@10"]).round(3)
print(f"train queries where bm25 scores higher, lower: {(change > 0).sum()}, {(change < 0).sum()}")
```

Output:

```text
idf of furniture: 0.919
idf of laundry: 3.985
idf of basket: 3.925
idf of wheels: 4.839

tf-idf top 3 for 'laundry basket with wheels':
  1  51.3  partial  laundry 4, basket 9, wheels 0 dirty clothes basket ,
  2  45.4  exact    laundry 6, basket 3, wheels 2 laundry sorter basket
  3  39.7  partial  laundry 7, basket 3, wheels 0 weave laundry basket

tf-idf train ndcg@10: 0.579
tf-idf train judged@10: 0.836
bm25 train ndcg@10: 0.695
bm25 train judged@10: 0.930
train queries where bm25 scores higher, lower: 36, 10
```

TF-IDF's first product is [partial](#store-data), a basket that never says `wheels` but repeats `basket` more than either product below it. The IDFs set this up. `furniture` gets 0.919, and the query's terms get 3.985 for `laundry`, 3.925 for `basket` and 4.839 for `wheels`: rarer, and close to one another. With IDFs this close, the repeats outweigh the missing `wheels`, as the scores show. The exact product, the only one of the three that says `wheels`, comes second. Term frequency has no ceiling in TF-IDF, so a product can outscore another by repeating a word.

Over the train queries, TF-IDF averages an [nDCG@10](#score-one-ranking) of 0.579 against BM25's 0.695, and BM25 scores higher and lower on 36, 10 queries respectively. TF-IDF's [judged@10](#score-every-test-query) is 0.836 against BM25's 0.930; when a run's judged@10 is lower, part of its gap may be products that nobody judged rather than worse ones. This comparison on train queries tells you which scorer to build on, and the book keeps its evidence for the test queries.

**Working rule:** Weight terms by IDF in any lexical scorer, because a match on a rare term is better evidence. Don't rank products by raw TF-IDF: cap what a repeated term can add, and correct for long texts, which is what BM25 does. Keep TF-IDF for explaining a ranking, where you can read off each term's tf and idf.

## Rebuild BM25 by hand to match bm25s {#bm25-from-scratch}

BM25 keeps IDF and changes how term frequency counts, in two ways. With **saturation**, each repeat of a term adds less than the one before, and no number of repeats can push the term's contribution past a ceiling ([Robertson and Zaragoza, 2009](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)). The parameter `k1` sets how quickly a term approaches it. With **length normalization**, a long text, which has more chances to contain any term, gets its term frequencies discounted. The parameter `b` sets how much: "b = 1 will perform full document-length normalisation, while b = 0 will switch normalisation off" (Robertson and Zaragoza). In the form bm25s computes by default ([bm25s scoring](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/scoring.py)):

```text
idf(t)     = ln(1 + (N − df(t) + 0.5) / (df(t) + 0.5))
bm25(q, d) = sum over query terms t of
             idf(t) × tf(t, d) / (tf(t, d) + k1 × (1 − b + b × length(d) / average length))
```

Two details differ between textbooks and libraries. A common variant multiplies the fraction by `k1` + 1, which grows every score by the same factor and so leaves the ranking unchanged (Robertson and Zaragoza, section 3.5.1). And Robertson's original IDF, without the 1 inside the logarithm, is negative for a term in more than half of the documents, so Lucene, an open-source search library, adds the 1 ([Kamphuis et al., 2020](https://cs.uwaterloo.ca/~jimmylin/publications/Kamphuis_etal_ECIR2020_preprint.pdf)). bm25s's default, `method="lucene"`, is Lucene's formula computed with exact document lengths ([bm25s README](https://github.com/xhluca/bm25s/blob/0.3.15/README.md)), where Lucene itself approximates them (Kamphuis et al.). "BM25" names a family of such variants, and a study of eight of them found no significant differences in effectiveness on three newswire collections (Kamphuis et al.).

Write the formula over the store's [inverted index](#build-an-inverted-index) at bm25s's defaults, `k1=1.5` and `b=0.75`, and check it against bm25s 0.3.16: first every product's score for each of the 80 queries, then the two rankings, by their top 100s and by [nDCG@10](#score-one-ranking):

Example `bm25-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Writes BM25 by hand over the inverted index at bm25s's defaults, and checks every score and every ranking against bm25s. The prose's point rests on the IDF lines for the word your, the largest score difference, the same-top-100 line and the test nDCG@10 lines."""
import math

import pandas as pd

from lib.lexical import LexicalSearch
from lib.lexical_by_hand import InvertedIndex, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, queries = load_products(), load_queries()
index, library = InvertedIndex(product_text(products)), LexicalSearch(products)  # by hand, and bm25s as chapter 1 uses it
# k1 and b at bm25s's defaults
n, k1, b = len(index.lengths), 1.5, 0.75


def bm25(query):
    scores = {}
    for term in tokenize(query):
        df = len(index.postings.get(term, {}))
        # Lucene's IDF: the 1 in the logarithm keeps it positive, even for a term in most products
        idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
        for product_id, tf in index.postings.get(term, {}).items():
            # length normalization: a product of average length gets a factor of 1
            length = 1 - b + b * index.lengths[product_id] / index.average_length
            scores[product_id] = scores.get(product_id, 0.0) + idf * tf / (tf + k1 * length)
    return pd.Series(scores, dtype=float)


df = len(index.postings["your"])
print(f"products with your: {df:,}")
# Robertson's IDF has no 1 in the logarithm, so it goes negative for a term in over half the products
print(f"robertson idf of your: {math.log((n - df + 0.5) / (df + 0.5)):.3f}")
print(f"lucene idf of your: {math.log(1 + (n - df + 0.5) / (df + 0.5)):.3f}")
for tf in [1, 2, 4, 9]:                                   # one term, in a product of average length
    print(f"term weight at tf {tf}: {tf / (tf + k1):.3f}")
# products that share no term with a query score 0, as bm25s gives them
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
```

Output:

```text
products with your: 6,135
robertson idf of your: -0.045
lucene idf of your: 0.671
term weight at tf 1: 0.400
term weight at tf 2: 0.571
term weight at tf 4: 0.727
term weight at tf 9: 0.857

largest score difference from bm25s: 1e-06
bm25s score type: float32
same top 100 for every query: yes
train ndcg@10 by hand: 0.695
train ndcg@10 with bm25s: 0.695
test ndcg@10 by hand: 0.725
test ndcg@10 with bm25s: 0.725
```

The word `your` occurs in 6,135 of the 12,000 products. Robertson's original IDF gives it -0.045, and Lucene's gives it 0.671. A negative IDF would make a match on a word lower a product's score. The term weights show saturation: in a product of average length, one occurrence of a term earns 0.400 of its IDF, and nine earn 0.857.

The scores match. The largest difference over every product and query is 1e-06, at the precision of the `float32` numbers bm25s returns. Matching scores don't settle a ranking on their own, though: where scores are equal, an implementation still has to choose which tied product comes first. Ours lists tied products by product ID. So does the book's shared BM25, `lib.lexical` from [chapter 1](#rank-with-bm25), which takes every product's score from bm25s and then orders equal scores by product ID. Asked whether both give the same top 100 for every query, the example answers yes.

The rankings follow from the scores. On the train queries, the mean nDCG@10 is 0.695 by hand and 0.695 with bm25s; on the test queries, 0.725 and 0.725.

**Working rule:** Serve BM25 from a library such as bm25s, and keep a small version you wrote yourself to check it, because yours shows where every part of a score comes from. Compare two implementations by their scores first, then by their rankings. Before you compare rankings, break ties the same way in both, by product ID as the book's BM25 does, or tied products alone can make two correct implementations rank differently. When two BM25 systems rank differently, compare their tokenizers before their formulas. The study of variants held tokenization and stop words fixed, and notes that more mundane settings, such as the choice of stop words, often make larger differences than the formula (Kamphuis et al.).

## Stem terms so word forms match {#stem-word-forms}

A shopper types `pool floats`, and a product says `float` or `floating`. To the tokenizer, those are different terms, so they don't match. **Stemming** cuts common endings off words, so that the forms of a word share one term, its **stem**. Martin Porter designed his suffix-stripping algorithm for retrieval, and in his test it reduced a vocabulary of 10,000 words to 6,370 stems, a cut of about one third ([Porter, 1980](https://tartarus.org/martin/PorterStemmer/def.txt)). His page recommends its successor, the Snowball English or Porter2 stemmer ([Porter](https://tartarus.org/martin/PorterStemmer/)), which stems slightly over 5% of words differently ([Snowball](https://snowballstem.org/algorithms/english/stemmer.html)). Stemming trades precision for recall. It raises recall while harming precision, and it helps some queries a lot while hurting others as much ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/stemming-and-lemmatization-1.html)).

A crude stemmer takes a few lines. Write one by hand that cuts `-ing`, `-es`, `-ed` or `-s` when at least three letters remain, and compare it with the Snowball English stemmer from PyStemmer, which bm25s's tokenizer recommends ([bm25s tokenizer](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/tokenization.py)) and the book pins at 3.1.0 ([PyStemmer](https://pypi.org/project/PyStemmer/)). Then count the products whose text contains a word, and those whose text contains its stem:

Example `stemmer-merges-word-forms` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Compares a hand-written suffix stripper with the Snowball English stemmer on a few words, then counts the products whose text contains each word and its stem. The prose's point rests on the counts for floats and for molding, and on the vocabulary reduction line."""
import Stemmer

from lib.lexical_by_hand import InvertedIndex
from lib.store import load_products, product_text


def strip_suffix(word):
    """A stemmer by hand: cut the first ending that matches, if at least three letters are left."""
    # the first ending that matches is cut, so the order matters: "es" is tried before "s"
    for ending in ["ing", "es", "ed", "s"]:
        # at least three letters must remain, so short words such as "is" keep their endings
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[: -len(ending)]
    return word


stemmer = Stemmer.Stemmer("english")          # Snowball English, also called Porter2
words = ["floats", "floating", "molding", "molded", "moldings", "shelves", "shelving", "shelf"]
for word, stem in zip(words, stemmer.stemWords(words)):
    print(f"{word}: snowball {stem}, by hand {strip_suffix(word)}")

products = load_products()
text = product_text(products)
plain, stemmed = InvertedIndex(text), InvertedIndex(text, stem=True)
print()
for word in ["floats", "molding"]:
    print(f"products with {word}:", len(plain.postings[word]))
    print(f"products with the stem of {word}:", len(stemmed.postings[stemmer.stemWord(word)]))
# every product with a word whose stem is float: float, floats, floating and any other form
float_products = list(stemmed.postings["float"])
print("products with the stem of floats that say floating:", len(plain.postings["floating"].keys() & set(float_products)))
for product_class, count in products.loc[float_products, "product_class"].value_counts().head(2).items():
    print(f"products with the stem of floats in {product_class}: {count}")
print(f"vocabulary without stemming: {len(plain.postings):,} terms")
print(f"vocabulary with stemming: {len(stemmed.postings):,} terms")
print(f"vocabulary reduction: {1 - len(stemmed.postings) / len(plain.postings):.0%}")
```

Output:

```text
floats: snowball float, by hand float
floating: snowball float, by hand float
molding: snowball mold, by hand mold
molded: snowball mold, by hand mold
moldings: snowball mold, by hand molding
shelves: snowball shelv, by hand shelv
shelving: snowball shelv, by hand shelv
shelf: snowball shelf, by hand shelf

products with floats: 11
products with the stem of floats: 288
products with molding: 123
products with the stem of molding: 262
products with the stem of floats that say floating: 244
products with the stem of floats in Wall Mounted Shelves: 57
products with the stem of floats in Desks: 36
vocabulary without stemming: 20,393 terms
vocabulary with stemming: 15,258 terms
vocabulary reduction: 25%
```

The hand-written stemmer agrees with Snowball on every word but `moldings`, where it stops after cutting `-s`, and Snowball's rules go on to `mold`. Both turn `shelves` into `shelv` and leave `shelf` alone: rules that cut endings don't know that shelves is the plural of shelf.

The counts show both sides of the trade. `floats` is in 11 products and its stem in 288, but 244 of those say `floating`. The two most common product classes among them are wall-mounted shelves, with 57, and desks, with 36. So the stem reaches floating shelves as well as pool floats, and only the judgments can say which effect wins ([next section](#check-stemming-on-test)).

`molding` occurs in 123 and its stem in 262, because `mold` also stands for `molded`, `moldings` and `mold` itself, a word with more than one meaning. The vocabulary shrinks by 25%, from 20,393 terms to 15,258 terms. Porter's test used different text and an earlier algorithm, so they don't compare directly.

To serve stemmed BM25 from bm25s, pass the same stemmer to `bm25s.tokenize` for the products and for every query. Then check that bm25s, given the same stemmer, scores like the hand-built index with stemming, `InvertedIndex(text, stem=True)` from `lib.lexical_by_hand`:

Example `bm25s-with-a-stemmer` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Builds bm25s with the same stemmer as the hand-built index, then checks every score on every query against it. The prose's point rests on the line that prints the largest score difference from bm25s."""
import bm25s
import Stemmer

from lib.lexical_by_hand import InvertedIndex
from lib.store import load_products, load_queries, product_text

products, queries = load_products(), load_queries()
texts = product_text(products)
stemmer = Stemmer.Stemmer("english")

library = bm25s.BM25()                                            # k1=1.5, b=0.75, as in chapter 1
# products and queries must go through the same stop list and stemmer, or their terms won't match
library.index(bm25s.tokenize(texts.tolist(), stopwords="en", stemmer=stemmer, show_progress=False),
              show_progress=False)
by_hand = InvertedIndex(texts, stem=True)

gaps = []
for query in queries["query"]:
    tokens = bm25s.tokenize([query], stopwords="en", stemmer=stemmer, return_ids=False, show_progress=False)[0]
    scores = library.get_scores(tokens)                           # every product, in catalog order
    # search keeps only matching products, best first: reindex puts each in its catalog place, 0 for the rest
    gaps.append(abs(by_hand.search(query, k=len(products)).reindex(products.index, fill_value=0) - scores).max())
print("query terms for pool floats:", bm25s.tokenize(["pool floats"], stopwords="en", stemmer=stemmer,
                                                     return_ids=False, show_progress=False)[0])
print(f"largest score difference from bm25s with a stemmer: {max(gaps):.0e}")
```

Output:

```text
query terms for pool floats: ['pool', 'float']
largest score difference from bm25s with a stemmer: 2e-06
```

`pool floats` becomes `pool` and `float`, and the largest score difference over all products and queries is 2e-06, the same rounding as [without stemming](#bm25-from-scratch).

**Working rule:** Stem English product text and queries with the Snowball English stemmer, at indexing time and at query time alike: in bm25s, pass `stemmer=` to `bm25s.tokenize` on both sides. Read the products that a stem adds, as the `floats` counts do, before you trust a gain. When a stem merges words that your shoppers keep apart, such as `molding` and `mold`, keep a list of words you don't stem. For text in another language, use that language's stemmer.

## Check stemming on the test queries {#check-stemming-on-test}

[Stemming](#stem-word-forms) trades precision for recall, so only the judgments can say whether it pays for the store. The choice to stem comes from the 50 [train queries](#store-data). This is the first of the chapter's [five planned comparisons](#lexical-retrieval), run on the 30 test queries. Next, the [stemmed index](#stem-word-forms) runs against the unstemmed one from [the BM25 section](#bm25-from-scratch):

Example `measure-stemming` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Compares the stemmed index with the unstemmed one on train and test queries, and runs the planned test comparison for stemming. The prose's point rests on the test permutation p and t-test p lines, and on the line that reports the query with the largest gain."""
from lib.lexical_by_hand import THRESHOLD, InvertedIndex, report_test_comparison
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

text = product_text(load_products())
indexes = {"without stemming": InvertedIndex(text), "with stemming": InvertedIndex(text, stem=True)}
scores = {split: {name: evaluate(index.run(load_queries(split)), qrels(split)) for name, index in indexes.items()}
          for split in ["train", "test"]}

for split in ["train", "test"]:
    for name, frame in scores[split].items():
        print(f"{split} ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
        print(f"{split} judged@10 {name}: {frame['judged@10'].mean():.3f}")
change = (scores["train"]["with stemming"]["ndcg@10"] - scores["train"]["without stemming"]["ndcg@10"]).round(3)
print(f"train queries better, worse: {(change > 0).sum()}, {(change < 0).sum()}")    # for choosing, not evidence
for query_id in [410, 359]:                       # pool floats and french molding, train queries
    for name, frame in scores["train"].items():
        print(f"query {query_id} {name}: {frame.at[query_id, 'ndcg@10']:.3f}")

print(f"\nthe planned test comparison, threshold {THRESHOLD:.2f}:")
after, before = scores["test"]["with stemming"]["ndcg@10"], scores["test"]["without stemming"]["ndcg@10"]
# the planned test comparison: permutation test, t-test and bootstrap interval
report_test_comparison(after, before)
gain = after - before
print("test query with the largest gain:", gain.idxmax())
print(f"its gain: {gain.max():.3f}")
print(f"mean test gain without it: {gain.drop(gain.idxmax()).mean():.3f}")
```

Output:

```text
train ndcg@10 without stemming: 0.695
train judged@10 without stemming: 0.930
train ndcg@10 with stemming: 0.725
train judged@10 with stemming: 0.950
test ndcg@10 without stemming: 0.725
test judged@10 without stemming: 0.927
test ndcg@10 with stemming: 0.774
test judged@10 with stemming: 0.950
train queries better, worse: 24, 14
query 410 without stemming: 0.360
query 410 with stemming: 0.921
query 359 without stemming: 0.961
query 359 with stemming: 0.809

the planned test comparison, threshold 0.01:
mean difference: 0.050
wins, losses, ties: 16, 6, 8
permutation p: 0.005
established at 0.01: yes
t-test p: 0.037
t-test agrees: no
99% interval: 0.016 to 0.162
interval agrees: yes
test query with the largest gain: 133
its gain: 0.635
mean test gain without it: 0.029
```

On the train queries, stemming takes the mean [nDCG@10](#score-one-ranking) from 0.695 to 0.725, and [judged@10](#score-every-test-query) from 0.930 to 0.950. The train queries that get better and worse number 24, 14. `pool floats` goes from 0.360 to 0.921, and `french molding` from 0.961 to 0.809. These train numbers choose stemming. They aren't evidence that it helps.

On the test queries, stemming's gain is established at 0.01, though the t-test disagrees ([the planned comparisons](#lexical-retrieval-decisions)): mean nDCG@10 goes from 0.725 to 0.774, a mean difference of 0.050. Judged@10 rises too, from 0.927 to 0.950, so part of that gain may come from products the unstemmed run left unjudged.

One query explains why the two tests split. Query 133, `outdoor light fixtures`, gains 0.635, and without it the mean gain is 0.029. The t-test assumes the differences are roughly normal, so one large gain widens their spread and lowers t; the permutation test assumes nothing about their shape ([chapter 3](#when-a-difference-is-established)). That query is also the one whose unstemmed top 10 [chapter 1 found full of unjudged light bulbs](#score-every-test-query).

**Working rule:** Choose a text-processing change on train queries, and keep it only if its planned comparison is established. When the permutation test and the t-test disagree, read the largest per-query differences, and report the gain without the largest one beside the mean. Stemming is established, so stem when you build lexical search. The book's shared BM25 stays unstemmed, so that later chapters' results stay comparable ([decisions](#lexical-retrieval-decisions)). Treat the size of the gain as fragile.

## Tune BM25's parameters on train queries {#tune-bm25-parameters}

BM25's two parameters have no single right value, and libraries ship different defaults. bm25s uses `k1=1.5` and `b=0.75` ([bm25s source](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/__init__.py)). [Lucene](#bm25-from-scratch) uses `k1=1.2` and `b=0.75` ([Lucene `BM25Similarity`](https://lucene.apache.org/core/10_3_0/core/org/apache/lucene/search/similarities/BM25Similarity.html)). [Kamphuis et al. (2020)](https://cs.uwaterloo.ca/~jimmylin/publications/Kamphuis_etal_ECIR2020_preprint.pdf) report `k1=0.9` and `b=0.4` as the defaults of Anserini, a research toolkit. [Robertson and Zaragoza (2009)](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf) give a rule of thumb, not a measurement: `b` between 0.5 and 0.8 and `k1` between 1.2 and 2 are reasonably good in many circumstances, but the best values depend on the kind of documents and queries. So you tune them on your own train queries, and check the result on test queries.

The [inverted index](#build-an-inverted-index) stores term frequencies and lengths, not scores, so `k1` and `b` can change from one search to the next without rebuilding it. bm25s computes every score when it builds its index ([Lù, 2024](https://arxiv.org/abs/2407.03618)), which makes its searches fast, but each new `k1` or `b` needs a new index. A sweep over the [stemmed index](#stem-word-forms) tries a grid of 25 settings on the 50 [train queries](#store-data) and picks the best. Then it compares the best with the defaults on the 30 test queries: the second [planned comparison](#lexical-retrieval), at the threshold of 0.01.

Before you run it, predict: at the defaults, stemmed BM25 scores 0.774 on the test queries. How much will the best setting on train add?

Example `sweep-k1-and-b` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Sweeps k1 and b over the stemmed index on train queries, picks the best setting, and checks it against the defaults on test queries. The prose's point rests on the train best and grid-edge lines, and on the test permutation p line."""
import pandas as pd

from lib.lexical_by_hand import InvertedIndex, report_test_comparison
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

index = InvertedIndex(product_text(load_products()), stem=True)     # stemmed terms, k1 and b set per search
train, test = load_queries("train"), load_queries("test")
# the grid: five values of k1 and five of b, with the defaults 1.5 and 0.75 among them
k1_values, b_values = [0.5, 0.9, 1.2, 1.5, 2.0], [0.0, 0.25, 0.5, 0.75, 1.0]


def scores(queries, split, k1, b):
    """One row per query, with BM25 at these parameters."""
    return evaluate(index.run(queries, k1=k1, b=b), qrels(split))


# one column per b, one row per k1
grid = pd.DataFrame({b: {k1: scores(train, "train", k1, b)["ndcg@10"].mean() for k1 in k1_values} for b in b_values})
print("train ndcg@10, k1 down and b across:")
print(grid.round(3).to_string())
# the (k1, b) pair with the highest mean nDCG@10 on train
best_k1, best_b = grid.stack().idxmax()
print("settings in the grid:", grid.size)
print(f"best k1 on train: {best_k1}")
print(f"best b on train: {best_b}")
# a best value at an end of the grid can mean a better one lies beyond it
edge = best_k1 in (k1_values[0], k1_values[-1]) or best_b in (b_values[0], b_values[-1])
print("best setting on the grid's edge:", "yes" if edge else "no")
print(f"train ndcg@10 at the train best: {grid.at[best_k1, best_b]:.3f}")
print(f"train ndcg@10 at k1 1.5, b 0.75: {grid.at[1.5, 0.75]:.3f}")
print(f"train gain of the best over the defaults: {grid.at[best_k1, best_b] - grid.at[1.5, 0.75]:.3f}")
print(f"lowest train ndcg@10 in the grid: {grid.min().min():.3f}")
print()
runs = {"at k1 1.5, b 0.75": scores(test, "test", 1.5, 0.75), "at the train best": scores(test, "test", best_k1, best_b)}
for name, frame in runs.items():
    print(f"test ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
    print(f"test judged@10 {name}: {frame['judged@10'].mean():.3f}")
# the planned test comparison: permutation test, t-test and bootstrap interval
report_test_comparison(runs["at the train best"]["ndcg@10"], runs["at k1 1.5, b 0.75"]["ndcg@10"])
```

Output:

```text
train ndcg@10, k1 down and b across:
      0.00   0.25   0.50   0.75   1.00
0.5  0.707  0.710  0.716  0.720  0.720
0.9  0.711  0.711  0.716  0.722  0.720
1.2  0.709  0.711  0.715  0.723  0.720
1.5  0.709  0.714  0.719  0.725  0.715
2.0  0.714  0.720  0.726  0.729  0.713
settings in the grid: 25
best k1 on train: 2.0
best b on train: 0.75
best setting on the grid's edge: yes
train ndcg@10 at the train best: 0.729
train ndcg@10 at k1 1.5, b 0.75: 0.725
train gain of the best over the defaults: 0.004
lowest train ndcg@10 in the grid: 0.707

test ndcg@10 at k1 1.5, b 0.75: 0.774
test judged@10 at k1 1.5, b 0.75: 0.950
test ndcg@10 at the train best: 0.775
test judged@10 at the train best: 0.953
mean difference: 0.001
wins, losses, ties: 7, 6, 17
permutation p: 0.757
established at 0.01: no
t-test p: 0.754
t-test agrees: yes
99% interval: -0.008 to 0.008
interval agrees: yes
```

On train, the whole grid lies between 0.707 and 0.729. The best setting, `k1` = 2.0 and `b` = 0.75, scores 0.729, against 0.725 at the defaults. The example reports whether it lies on the grid's edge: yes. A wider grid could find a higher train score, but with the whole grid this close, it would change little.

Tuning shows no established gain on the test queries. The best setting scores 0.775 against 0.774, with [judged@10](#score-every-test-query) of 0.953 and 0.950, and the difference isn't established ([the planned comparisons](#lexical-retrieval-decisions)).

If you predicted a gain of a few hundredths, the train grid makes it unlikely. On train, the best setting beats the defaults by 0.004, and even that is an optimistic estimate: of all the settings, it is the one that happened to fit these queries best, so on other queries you should expect less.

**Working rule:** Start from the library's defaults. Tune `k1` and `b` on train queries when you change what you index, such as fields or stemming, and keep a tuned setting only if its planned comparison is established. The store's tuned setting isn't, so the store keeps `k1=1.5` and `b=0.75`.

## Weight the product name above the description {#weight-the-product-name}

A product's text has parts, called **fields**: the store's text fields are name, class, category and description. They aren't equal evidence. A query word in the name says more about what the product is than the same word somewhere in a description. There are two ways to weight fields. The first that comes to mind scores each field with BM25 and adds the scores. [Robertson and Zaragoza (2009, section 3.6)](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf) argue for the opposite order, "first streams, then terms": combine each term's weighted frequencies across the fields first, and then saturate the total evidence for that term. That is BM25F. Their rule implies that adding per-field scores lets a term that matches in two fields escape saturation, because each field saturates on its own. With whole-number weights, simple BM25F gives the same result as plain BM25 on a text in which each field is repeated as many times as its weight (Robertson and Zaragoza, section 3.6.4), so you can try it with any BM25 library.

The store's search indexes one field, the name, class, category and description joined. The first try is the one that comes to mind: on the 50 [train queries](#store-data) with [stemming](#stem-word-forms), the name and the other three fields are indexed apart, scored apart and added. Indexed apart, each field also gets its own IDF and its own average length, so this changes more than saturation. By Robertson and Zaragoza's argument, we expect it to do worse. On train queries, the result informs a choice and proves nothing:

Example `fields-scored-apart` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Scores the name and the other fields as separate BM25 indexes and adds the scores, then compares the result with one field on train queries. The prose's point rests on the two train nDCG@10 lines and the line that counts the queries that get better and worse."""
from collections import Counter

from lib.lexical_by_hand import InvertedIndex
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, train = load_products(), load_queries("train")
others = products["product_class"] + ". " + products["category"] + ". " + products["description"]
one_field = InvertedIndex(product_text(products), stem=True)                 # name, class, category, description
name, rest = InvertedIndex(products["name"], stem=True), InvertedIndex(others, stem=True)   # own IDF and lengths

summed = {}
for query_id, query in train["query"].items():
    scores = Counter(name.bm25(query)) + Counter(rest.bm25(query))           # each field saturates on its own
    # the top 100, as in every other run
    summed[query_id] = [product_id for product_id, _ in scores.most_common(100)]

runs = {"one field": one_field.run(train), "fields scored apart": summed}
scores = {label: evaluate(run, qrels("train")) for label, run in runs.items()}
for label, frame in scores.items():
    print(f"{label}, train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{label}, train judged@10: {frame['judged@10'].mean():.3f}")
change = (scores["fields scored apart"]["ndcg@10"] - scores["one field"]["ndcg@10"]).round(3)
print(f"train queries better, worse with fields scored apart: {(change > 0).sum()}, {(change < 0).sum()}")
```

Output:

```text
one field, train ndcg@10: 0.725
one field, train judged@10: 0.950
fields scored apart, train ndcg@10: 0.686
fields scored apart, train judged@10: 0.970
train queries better, worse with fields scored apart: 15, 24
```

Scored apart, the fields give a train [nDCG@10](#score-one-ranking) of 0.686 against 0.725 for one field, with [judged@10](#score-every-test-query) of 0.970 and 0.950. The train queries that get better and worse number 15, 24. That is enough to choose one field over this design, and not enough to say why: saturation, IDF and length normalization all changed at once.

A second try uses BM25F with whole-number weights: the name counted 1, 2, 3 or 5 times in the indexed text. It picks the weight with the best train score, then compares it with one field on the 30 test queries: the third [planned comparison](#lexical-retrieval).

Example `repeat-the-name-field` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Repeats the product name in the indexed text, once per extra weight, and picks the weight with the best train nDCG@10 for the test comparison. The prose's point rests on the best-weight line and the test permutation p line."""
from lib.lexical_by_hand import InvertedIndex, report_test_comparison
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, train, test = load_products(), load_queries("train"), load_queries("test")
# product_text already holds the name once, so weight - 1 more copies make it weight in all
indexes = {weight: InvertedIndex((products["name"] + ". ") * (weight - 1) + product_text(products), stem=True)
           for weight in [1, 2, 3, 5]}            # BM25F with whole-number weights: the name counted weight times

train_scores = {weight: evaluate(index.run(train), qrels("train")) for weight, index in indexes.items()}
for weight, frame in train_scores.items():
    print(f"name weight {weight}, train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"name weight {weight}, train judged@10: {frame['judged@10'].mean():.3f}")
# on a tie, max keeps the first weight, the smaller one
best = max(train_scores, key=lambda weight: train_scores[weight]["ndcg@10"].mean())
print("best name weight on train:", best)
print()
runs = {"one field": indexes[1].run(test), "best name weight": indexes[best].run(test)}
scores = {label: evaluate(run, qrels("test")) for label, run in runs.items()}
for label, frame in scores.items():
    print(f"{label}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{label}, test judged@10: {frame['judged@10'].mean():.3f}")
# the planned test comparison: permutation test, t-test and bootstrap interval
report_test_comparison(scores["best name weight"]["ndcg@10"], scores["one field"]["ndcg@10"])
```

Output:

```text
name weight 1, train ndcg@10: 0.725
name weight 1, train judged@10: 0.950
name weight 2, train ndcg@10: 0.734
name weight 2, train judged@10: 0.968
name weight 3, train ndcg@10: 0.729
name weight 3, train judged@10: 0.970
name weight 5, train ndcg@10: 0.722
name weight 5, train judged@10: 0.972
best name weight on train: 2

one field, test ndcg@10: 0.774
one field, test judged@10: 0.950
best name weight, test ndcg@10: 0.786
best name weight, test judged@10: 0.970
mean difference: 0.012
wins, losses, ties: 15, 9, 6
permutation p: 0.149
established at 0.01: no
t-test p: 0.153
t-test agrees: yes
99% interval: -0.009 to 0.032
interval agrees: yes
```

On train, the best name weight is 2, which scores 0.734 against 0.725 for one field, with judged@10 of 0.968 and 0.950.

Repeating the name shows no established gain on test: the best name weight scores 0.786 against 0.774, with judged@10 of 0.970 and 0.950, and the gain isn't established ([the planned comparisons](#lexical-retrieval-decisions)). Neither the t-test nor the interval disagrees.

**Working rule:** Don't add up BM25 scores from separate fields. To weight a field, combine term frequencies before saturation, with BM25F or by repeating the field. Tune the weight on train queries, and keep it only if its planned comparison is established. For the store, one combined field stays.

## Index product attributes as a field {#index-attributes-as-a-field}

Shoppers often add a modifier, a word that narrows what they want: a color, a material, a size. The WANDS judges mark a product partial when it matches the thing asked for but not its [modifiers](#intent-in-product-search). Product names and descriptions don't always state a modifier, but a catalog often keeps such facts as structured **attributes**, such as `color: clear` or `material: glass`. The store's products carry a few from WANDS: color, material, style, finish, shape, size, width, height and depth (`examples/data/wands/README.md`). Indexed as one more field, attributes give a modifier something to match. They also add terms to every product that has them, so whether they help is a question for the judgments.

In [chapter 1](#rank-with-bm25), BM25's results for `clear shower curtain` couldn't show which curtains were clear. The example adds each product's attributes, names and values, to its indexed text, as a field with weight 1, combined before saturation as [the previous section](#weight-the-product-name) recommends. It counts the exact products for that test query that contain `clear`, with and without attributes. It measures this one candidate, fixed in advance, on the 50 [train queries](#store-data) and checks it on the 30 test queries: the fourth [planned comparison](#lexical-retrieval). Being planned, it goes to test whatever train shows.

Example `add-attributes-field` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Adds each product's attributes, names and values, to its indexed text as one more field, and checks that single candidate on train and test. The prose's point rests on the two lines that count exact products with clear, and on the test permutation p line."""
from lib.lexical_by_hand import InvertedIndex, report_test_comparison, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products = load_products()
text = product_text(products)
with_attributes = text + ". " + products["attributes"]      # names and values, one more field, weight 1

exact = [product_id for product_id, grade in qrels("test")[246].items() if grade == 2]    # clear shower curtain
print("exact products for query 246:", len(exact))
print("exact, with clear in their text:", sum("clear" in tokenize(text[product_id]) for product_id in exact))
print("exact, with clear in text or attributes:", sum("clear" in tokenize(with_attributes[product_id]) for product_id in exact))
# a product whose attributes say clear and whose text does not, to show what the field adds
found = next(product_id for product_id in exact
             if "clear" in tokenize(products.at[product_id, "attributes"]) and "clear" not in tokenize(text[product_id]))
print(f"for example: {products.at[found, 'name']} -> {products.at[found, 'attributes']}")
names = {"color", "material", "style", "finish", "shape", "size", "width", "height", "depth"}       # the attribute names
print("queries that contain an attribute name:", load_queries()["query"].map(lambda query: bool(names & set(tokenize(query)))).sum())
print("products whose attributes name size:", sum("size" in tokenize(value) for value in products["attributes"]))

indexes = {"one field": InvertedIndex(text, stem=True), "with attributes": InvertedIndex(with_attributes, stem=True)}
scores = {split: {label: evaluate(index.run(load_queries(split)), qrels(split)) for label, index in indexes.items()}
          for split in ["train", "test"]}           # one candidate, fixed in advance: tuned on nothing
for split in ["train", "test"]:
    print()
    for label, frame in scores[split].items():
        print(f"{split} ndcg@10, {label}: {frame['ndcg@10'].mean():.3f}")
        print(f"{split} judged@10, {label}: {frame['judged@10'].mean():.3f}")
print()
for query_id in [246, 58]:                       # clear shower curtain, medium size chandelier: test queries
    for label, frame in scores["test"].items():
        print(f"query {query_id} ndcg@10, {label}: {frame.at[query_id, 'ndcg@10']:.3f}")
# the planned test comparison: permutation test, t-test and bootstrap interval
report_test_comparison(scores["test"]["with attributes"]["ndcg@10"], scores["test"]["one field"]["ndcg@10"])
```

Output:

```text
exact products for query 246: 12
exact, with clear in their text: 4
exact, with clear in text or attributes: 8
for example: wynsum vinyl single shower curtain -> color: clear; width: 72; height: 84
queries that contain an attribute name: 1
products whose attributes name size: 950

train ndcg@10, one field: 0.725
train judged@10, one field: 0.950
train ndcg@10, with attributes: 0.717
train judged@10, with attributes: 0.948

test ndcg@10, one field: 0.774
test judged@10, one field: 0.950
test ndcg@10, with attributes: 0.787
test judged@10, with attributes: 0.963

query 246 ndcg@10, one field: 0.714
query 246 ndcg@10, with attributes: 0.844
query 58 ndcg@10, one field: 0.731
query 58 ndcg@10, with attributes: 0.667
mean difference: 0.013
wins, losses, ties: 8, 10, 12
permutation p: 0.303
established at 0.01: no
t-test p: 0.281
t-test agrees: yes
99% interval: -0.009 to 0.053
interval agrees: yes
```

For `clear shower curtain`, the attributes do what they should: 4 of the 12 exact products say `clear` in their text, and 8 do once attributes count, such as the vinyl curtain whose attributes say `color: clear`. For this query, nDCG@10 goes from 0.714 to 0.844. Indexing the attribute names has a cost, though: `size` now matches the 950 products whose attributes give a size. The store has 1 query that contains an attribute name, the test query `medium size chandelier`, and it goes from 0.731 to 0.667.

On train, judged@10 goes from 0.950 to 0.948, and nDCG@10 from 0.725 to 0.717. On test, judged@10 goes from 0.950 to 0.963, and nDCG@10 from 0.774 to 0.787, but the permutation test doesn't establish the gain ([the planned comparisons](#lexical-retrieval-decisions)).

**Working rule:** Keep structured attributes, and read the queries they help, but don't add them to the BM25 text on the strength of a few queries. Index the values without the names, so that a query word such as `size` doesn't match every product with a size, and keep the field only if its planned comparison is established. For the store, the attributes stay out of the BM25 text. When a modifier names an attribute value exactly, such as a color, a filter or a ranking feature can use it without adding its words to every product's text.

## Match phrases with term positions {#match-phrases-with-positions}

BM25 scores a bag of words: it counts which terms a product contains and how often, never their order. To BM25, `barn door` and `door barn` are the same query. A **phrase** match needs the terms next to each other and in order, and an index of counts can't check that. A **positional index** stores, for each term and product, the positions where the term occurs, so that a phrase becomes a check on positions ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/positional-indexes-1.html)). bm25s precomputes one score for each pair of product and term ([Lù, 2024](https://arxiv.org/abs/2407.03618)). Its index keeps no positions ([bm25s source](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/__init__.py)), so phrases need an index of their own.

A positional index over the store's product names comes first, with stemmed terms as in [the stemming section](#stem-word-forms). Positions count terms after stop words are removed, so `door for laundry` holds the adjacent terms `door` and `laundri`: a phrase can match across a removed stop word. Take `barn door`, two words from one of the store's queries: assert that BM25 can't tell its two orders apart, and count the names with both words against those with the phrase:

Example `phrase-positions-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Builds a positional index over the product names, asserts that BM25 scores both word orders alike, and lists the names that have both words without the phrase. The prose's point rests on the two count lines, names with barn and door and names with the phrase barn door."""
from lib.lexical_by_hand import InvertedIndex, tokenize
from lib.store import load_products, product_text

products = load_products()
positions = {}            # {term: {product_id: [where the term occurs in the name, counted after stop words go]}}
for product_id, name in products["name"].items():
    # positions count the terms left after stop words are removed, so a phrase can span one
    for place, term in enumerate(tokenize(name, stem=True)):
        positions.setdefault(term, {}).setdefault(product_id, []).append(place)


def has_phrase(product_id, terms):
    """True if the terms occur next to each other, in this order, in the product's name."""
    def places(term):
        return positions.get(term, {}).get(product_id, [])
    # each term has to sit at the next position after the one before it
    return any(all(start + offset in places(term) for offset, term in enumerate(terms)) for start in places(terms[0]))


index = InvertedIndex(product_text(products), stem=True)
# BM25 counts words, not their order, so both orders must score alike
assert index.bm25("barn door") == index.bm25("door barn")
both = set(positions["barn"]) & set(positions["door"])
print("names with barn and door:", len(both))
print("names with the phrase barn door:", sum(has_phrase(product_id, ["barn", "door"]) for product_id in both))
for product_id in sorted(product_id for product_id in both if not has_phrase(product_id, ["barn", "door"])):
    print("  ", products.at[product_id, "name"])
```

Output:

```text
names with barn and door: 71
names with the phrase barn door: 66
   low ceiling single bypass double door barn hardware kit
   artemas barn owl welcome non-slip outdoor door mat
   vintage rustic wooden door of old barn duvet cover set
   barnes entrance scraper non-slip outdoor door mat
   glass barn 60 '' w x 76 '' h single sliding frameless shower door
```

BM25 gives `barn door` and `door barn` the same scores, as the code asserts. Of the 71 names that contain both `barn` and `door`, 66 contain the phrase. The names without it show what a phrase check catches and what it costs. Two door mats and a duvet cover match both words but aren't barn doors, and one of the mats matches only because `barnes` stems to `barn`. The bypass hardware kit, on the other hand, is hardware for barn doors, and the glass sliding shower door is a barn-style door. A strict phrase filter would remove both.

A bonus is gentler than a filter: a fixed amount added to a product's BM25 score for each pair of adjacent query terms that appears, in order, in its name. The bonus example uses `PositionalIndex` from `lib.lexical_by_hand`, which holds the same positions, and it picks the bonus on the 50 [train queries](#store-data), then checks it on the 30 test queries: the last [planned comparison](#lexical-retrieval).

Example `phrase-bonus-train-and-test` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Adds a bonus for each adjacent pair of query terms that appears in order in a product's name, picks the bonus on train and checks it on test. The prose's point rests on the test permutation p line and the test nDCG@10 lines."""
from lib.lexical_by_hand import InvertedIndex, PositionalIndex, report_test_comparison, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products = load_products()
index = InvertedIndex(product_text(products), stem=True)
names = PositionalIndex(products["name"], stem=True)      # the positions phrase-positions-by-hand builds


def with_bonus(split, bonus):
    """BM25's top 100, plus the bonus for each pair of adjacent query terms found, in order, in the name."""
    run = {}
    for query_id, query in load_queries(split)["query"].items():
        terms, scores = tokenize(query, stem=True), index.search(query)
        pairs = list(zip(terms, terms[1:]))
        # only BM25's top 100 get a bonus, so it reorders them and adds no product
        scores += [bonus * sum(names.has_phrase(product_id, list(pair)) for pair in pairs) for product_id in scores.index]
        run[query_id] = list(scores.sort_values(ascending=False, kind="stable").index)
    return evaluate(run, qrels(split))


train_scores = {bonus: with_bonus("train", bonus) for bonus in [0, 0.5, 1, 2]}
for bonus, frame in train_scores.items():
    print(f"bonus {bonus}, train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"bonus {bonus}, train judged@10: {frame['judged@10'].mean():.3f}")
best = max(train_scores, key=lambda bonus: train_scores[bonus]["ndcg@10"].mean())
print("best bonus on train:", best)
print()
# the defaults, with no bonus, and the best bonus on train
test_scores = {bonus: with_bonus("test", bonus) for bonus in [0, best]}
for bonus, frame in test_scores.items():
    print(f"bonus {bonus}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"bonus {bonus}, test judged@10: {frame['judged@10'].mean():.3f}")
# the planned test comparison: permutation test, t-test and bootstrap interval
report_test_comparison(test_scores[best]["ndcg@10"], test_scores[0]["ndcg@10"])
```

Output:

```text
bonus 0, train ndcg@10: 0.725
bonus 0, train judged@10: 0.950
bonus 0.5, train ndcg@10: 0.727
bonus 0.5, train judged@10: 0.956
bonus 1, train ndcg@10: 0.725
bonus 1, train judged@10: 0.964
bonus 2, train ndcg@10: 0.716
bonus 2, train judged@10: 0.968
best bonus on train: 0.5

bonus 0, test ndcg@10: 0.774
bonus 0, test judged@10: 0.950
bonus 0.5, test ndcg@10: 0.776
bonus 0.5, test judged@10: 0.950
mean difference: 0.002
wins, losses, ties: 6, 7, 17
permutation p: 0.758
established at 0.01: no
t-test p: 0.769
t-test agrees: yes
99% interval: -0.012 to 0.015
interval agrees: yes
```

On train, the best bonus is 0.5, which scores 0.727 against 0.725 without one, with [judged@10](#score-every-test-query) of 0.956 and 0.950.

The best bonus scores 0.776 against 0.774, with judged@10 of 0.950 and 0.950, and the gain isn't established ([the planned comparisons](#lexical-retrieval-decisions)).

**Working rule:** Don't add a phrase bonus to every query by default, and keep one only if its planned comparison is established. Build positions when shoppers quote phrases, or when word order changes what they want, as between `table lamp` and `lamp table`. Prefer a bonus that you measure on train queries to a filter, because a filter removes products like the hardware kit.

## What goes wrong in production {#lexical-retrieval-in-production}

**The index and the queries drift apart.** Every step from [the tokenizer](#split-text-into-terms) to [the stemmer](#stem-word-forms) must run the same way on products and on queries. Stem the queries but not the products, and a query term such as `shelv` finds no postings. Nothing warns you: bm25s leaves out query tokens that aren't in its vocabulary ([bm25s source](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/__init__.py)). Change text processing for both sides in one release, and rebuild the whole index.

**Sizes, units and codes don't survive tokenizing.** `7qt` and `7 qt` never meet, as [the tokenizer section](#split-text-into-terms) shows. Train query 205 ends in a product code, `w003096809`, that appears in no product's text in the sample: its postings hold 0 products, so no lexical scorer can match it. A misspelled term such as the `ligth` in `ligth bulb` can only match products with the same misspelling, and [chapter 8](#correct-spelling-from-catalog) builds a corrector and shows what it still gets wrong.

**IDF depends on the catalog.** Every IDF in this chapter comes from the sample, which holds every product judged for the 80 queries plus randomly chosen unjudged ones (`examples/data/wands/README.md`). On the full catalog, document frequencies differ, and so do IDFs and scores. Recompute them whenever you rebuild the index.

**A BM25 score has no fixed scale.** Each query term adds at most its own IDF, so the highest possible score depends on which terms the query holds, and a score of 6 can be high for one query and low for another. Don't keep results above a fixed score threshold; cut the list by rank.

**Stop words and stemming change meaning on a few queries.** The store's judged queries have no negations, but shoppers type them, and the default stop list removes `not` and `no`. Stemming hurts some queries badly, as `french molding` shows in [the stemming check](#check-stemming-on-test). The judgments can't warn you about queries they don't include.

**The test queries wear out.** This chapter makes [five planned comparisons](#lexical-retrieval) on the same test queries, and the Bonferroni threshold of 0.01 keeps the chance of any false positive among them at 5% or less when none of the changes does anything. It can't count what nobody planned: every extra setting tried on test, and every look at a test query to explain a result, is another comparison. Confirm stemming's gain on queries and judgments that none of these choices has seen.

**Working rule:** Keep a set of probe queries for negations, sizes and codes, and read their results after every change to text processing. Store the tokenizer's and stemmer's settings with the index they built, log the terms that each query becomes, and watch for queries whose terms have no postings.

## Decisions this chapter made {#lexical-retrieval-decisions}

Each setting here was picked on the train queries. Before reading any test result, the chapter fixed [five planned comparisons](#lexical-retrieval) on the test queries, read with [chapter 3's harness](#compare-runs-in-a-harness): stemming and the attributes field as single candidates fixed in advance, and the best setting on train for `k1` and `b`, the name weight and the phrase bonus. The attributes field went to test whatever train showed, because it was planned. Only an established difference changes a decision. Each column compares nDCG@10 on the test queries with the change against the same search without it, at the threshold of 0.01:

| Measure | [Stemming](#check-stemming-on-test) | [Best `k1` and `b`](#tune-bm25-parameters) | [Best name weight](#weight-the-product-name) | [Attributes field](#index-attributes-as-a-field) | [Best phrase bonus](#match-phrases-with-positions) |
| --- | --- | --- | --- | --- | --- |
| Mean difference | 0.050 | 0.001 | 0.012 | 0.013 | 0.002 |
| 99% interval | 0.016 to 0.162 | -0.008 to 0.008 | -0.009 to 0.032 | -0.009 to 0.053 | -0.012 to 0.015 |
| Permutation p | 0.005 | 0.757 | 0.149 | 0.303 | 0.758 |
| t-test p | 0.037 | 0.754 | 0.153 | 0.281 | 0.769 |
| Wins, losses, ties | 16, 6, 8 | 7, 6, 17 | 15, 9, 6 | 8, 10, 12 | 6, 7, 17 |
| Established | yes | no | no | no | no |
| t-test agrees | no | yes | yes | yes | yes |
| Interval agrees | yes | yes | yes | yes | yes |

- **Tokenizer: bm25s's defaults.** Lowercasing, tokens of two or more word characters (letters, digits or underscores), and its 33 English stop words, rebuilt by hand and matched on every product. They lose single-digit sizes and negations. Too few judged queries could measure either: a size-aware pattern changes 4 train queries and 0 test queries, and 0 queries hold a negation. The defaults stay until probe queries or new judgments can.
- **Stemming: Snowball English from PyStemmer, on products and queries.** Its test gain, from 0.725 to 0.774, is established by the permutation test, though the t-test disagrees and one query carries much of it. The book's shared baseline, `lib.lexical` from chapter 1, stays at bm25s's defaults without stemming, so that every chapter's results stay comparable. This chapter's stemmed BM25 is `InvertedIndex(text, stem=True)` in `lib.lexical_by_hand`, or bm25s with `stemmer=`.
- **Scoring: BM25 as bm25s computes it by default,** Lucene's formula with exact lengths, `k1=1.5` and `b=0.75`, with equal scores ordered by product ID. The best setting on train isn't established on test, so the defaults stay.
- **Fields: one field** that joins name, class, category and description. Per-field scores, added, score lower on train. The best name weight on train and the attributes field aren't established on test.
- **Phrases: no phrase bonus.** Positions over product names are cheap to build, but the best bonus on train isn't established on test.
- **Implementation: a by-hand index for experiments, a library for serving.** The by-hand index lets `k1` and `b` change without rebuilding, and bm25s precomputes scores so that searches are fast. On the same test queries, semantic retrieval with the recorded `Snowflake/snowflake-arctic-embed-m-v1.5` embeddings scores 0.830 ([chapter 1](#search-by-meaning)).
- **What the chapter showed:** BM25 can be rebuilt by hand and matched score for score. Of the choices made on the train queries, only stemming held up on test, and even it rests on a few queries.
