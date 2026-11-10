---
title: "A Primer on Search Relevance"
chapter: "Measuring search"
chapter_id: measuring-search
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/measuring-search
license: CC BY 4.0
attribution: "“Measuring search,” chapter 3 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/measuring-search. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Measuring search

By the end of this chapter you can compute the standard ranking metrics from scratch, check them against scikit-learn, choose one before you compare rankers, and tell whether the gap between two rankers on your test queries is established or could be chance.

[Chapter 1](#score-every-test-query) left the store, [the furniture and home-goods retailer](#store-data) whose search the book works on, with four numbers. On its test queries, BM25 scores an nDCG@10 of 0.725, semantic retrieval 0.830, the hybrid 0.812 and the reranked hybrid 0.798. Semantic retrieval ranks by recorded embeddings from the open model `Snowflake/snowflake-arctic-embed-m-v1.5`, and the reranker is the recorded cross-encoder `Alibaba-NLP/gte-reranker-modernbert-base`. Chapter 1's decision rests on the order of the four scores: semantic retrieval alone is the ranker to beat. Before you trust it, two questions need answers. Do the metrics measure what matters to a shopper, and are they computed correctly? And are the gaps real, or what 30 queries produce by chance? This chapter answers both. It ends with the rule the book uses from here on to call a difference established, and an evaluation harness that applies it.

## Count the relevant products in the top k {#count-relevant-in-top-k}

Most ranking metrics start from one question: how many of the results a shopper sees are relevant? **Precision at k**, written precision@k, is the share of the top k results that are relevant. **Recall at k**, recall@k, is the share of all relevant products that appear in the top k. In the textbook's words, precision "is the fraction of retrieved documents that are relevant" and recall "is the fraction of relevant documents that are retrieved", and raising one usually costs the other ([Manning et al., 2008, section 8.3](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html)). Both need a yes-or-no idea of relevant. In this book a product is relevant to a query when its [judgment](#store-data) is exact, grade 2, and a product nobody judged for the query counts as not relevant.

[BM25](#rank-with-bm25)'s top 10 for the store's test query `clear shower curtain` mixes clear curtains, curtains that aren't clear, and [shower curtain hooks](#check-against-judgments). Count the exact products by hand, compare with `lib.metrics`, then work out the best score each test query could reach:

Example `precision-recall-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import precision_at_k, recall_at_k
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
ranking = list(LexicalSearch(load_products()).search(queries.at[246, "query"], k=10).index)  # clear shower curtain
exact = {product_id for product_id, grade in judgments[246].items() if grade == 2}

found = sum(product_id in exact for product_id in ranking[:10])
print("exact in the top 10:", found)
print("exact products judged:", len(exact))
print(f"precision@10 by hand: {found / 10:.3f}")
print(f"recall@10 by hand: {found / len(exact):.3f}")
print(f"precision@10 from lib.metrics: {precision_at_k(ranking, judgments[246], 10):.3f}")
print(f"recall@10 from lib.metrics: {recall_at_k(ranking, judgments[246], 10):.3f}")

# the best any ranking can do: a top 10 that holds as many exact products as the query has
exact_counts = pd.Series({query_id: sum(grade == 2 for grade in per_query.values())
                          for query_id, per_query in judgments.items()})
best_precision = exact_counts.clip(upper=10) / 10
best_recall = exact_counts.clip(upper=10) / exact_counts
print()
print("queries where precision@10 can't reach 1:", (best_precision < 1).sum())
print("fewest exact products for a query:", exact_counts.min())
print("queries with that few:", (exact_counts == exact_counts.min()).sum())
print(f"best precision@10 for those queries: {best_precision.min():.3f}")
print("queries where recall@10 can't reach 1:", (best_recall < 1).sum())
most = exact_counts.idxmax()
print("query with the most exact products:", queries.at[most, "query"])
print("its exact products:", exact_counts[most])
print(f"its best recall@10: {best_recall[most]:.3f}")
```

Output:

```text
exact in the top 10: 4
exact products judged: 12
precision@10 by hand: 0.400
recall@10 by hand: 0.333
precision@10 from lib.metrics: 0.400
recall@10 from lib.metrics: 0.333

queries where precision@10 can't reach 1: 7
fewest exact products for a query: 4
queries with that few: 4
best precision@10 for those queries: 0.400
queries where recall@10 can't reach 1: 22
query with the most exact products: outdoor light fixtures
its exact products: 170
its best recall@10: 0.059
```

4 of the top 10 are exact, so precision@10 is 0.400. The judges marked 12 products exact for this query, so recall@10 is 0.333. `precision_at_k` and `recall_at_k` give the same values.

Neither metric has the same ceiling for every query. A query with fewer than 10 exact products can't fill its top 10 with them: 7 test queries are like that, and the 4 with only 4 exact products can reach a precision@10 of 0.400 at best. A query with more than 10 exact products can't reach full recall in 10 results: 22 test queries are like that. The query `outdoor light fixtures` has 170 exact products, so its recall@10 tops out at 0.059. A mean over the test queries mixes queries that can score 1 with queries that can't.

Recall has a second problem: its denominator counts only the exact products the judges found. WANDS judged candidates gathered for each query, not the whole catalog ([chapter 1](#store-data)), so some exact products were never judged. Zobel found that judgments gathered this way overestimate recall ([Know where the judgments came from](#pooled-judgments)).

**Working rule:** Use precision@10 when you care how much of the first page is right, and read it next to each query's ceiling. Don't make recall@10 a headline in product search, where a query can have more than a hundred relevant products, as `outdoor light fixtures` has. We recommend recall at a deep cutoff, such as the top 100, for one job only: checking that retrieval passes enough relevant products to a reranker. Even then, read it as an overestimate.

## Score the first relevant result with reciprocal rank {#score-the-first-relevant-result}

Precision counts a whole page, but some shoppers want one product: a replacement part, or a model they already know. For them, what matters is how far down the first good result sits. **Reciprocal rank** (RR) scores a query as 1 divided by the position of the first relevant result, or 0 if there is none, and its mean over queries is the **mean reciprocal rank** (MRR). TREC, the Text REtrieval Conference, is a series of shared evaluations of search systems. MRR was the official measure of its question-answering track at TREC-8, where each question "received a score equal to the reciprocal of the rank at which the first correct response was returned, or 0 if none of the five responses contained a correct answer". The track chose it partly because it "is bounded between 0 and 1, inclusive, and averages well" ([Voorhees, 1999](https://trec.nist.gov/pubs/trec8/papers/qa_report.ps)).

Whether you may average RR is disputed. Fuhr points out that in RR "the difference between ranks 1 and 2 is the same as that between ranks 2 and ∞". So RR isn't an interval scale, a scale on which equal steps mean equal differences, and in his view its mean shouldn't be computed ([Fuhr, 2017, section 2.1](https://sigir.org/wp-content/uploads/2018/01/p032.pdf)). Sakai sees no reason to forbid it ([Sakai, 2020](https://sigir.org/wp-content/uploads/2020/06/p14.pdf)), and Moffat argues that such metrics "are more meaningful in their current form than in the proposed 'intervalized' versions" ([Moffat, 2022](https://arxiv.org/abs/2207.03103)). We use MRR with that caveat: it is a coarse summary.

Write RR by hand, score [BM25](#rank-with-bm25)'s ranking for the store's query `clear shower curtain` with two thresholds for relevant, then compute MRR for BM25 and [semantic retrieval](#search-by-meaning) over the test queries:

Example `reciprocal-rank-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


def reciprocal_rank(ranking, judgments, relevant=2):
    """1 / the position of the first relevant product, or 0 if the ranking has none."""
    for position, product_id in enumerate(ranking, start=1):
        if judgments.get(product_id, 0) >= relevant:
            return 1 / position
    return 0.0


queries, judgments = load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(load_products()).run(queries, k=100), "semantic": SemanticSearch().run(queries, k=100)}

ranking = runs["bm25"][246]                                        # clear shower curtain
print(f"rr, exact counts as relevant: {reciprocal_rank(ranking, judgments[246]):.3f}")
print(f"rr, partial or better counts: {reciprocal_rank(ranking, judgments[246], relevant=1):.3f}")

for name, run in runs.items():
    rr = pd.Series({query_id: reciprocal_rank(run[query_id], judgments[query_id]) for query_id in judgments})
    print(f"{name} mrr: {rr.mean():.3f}")
    print(f"{name} mrr from lib.metrics: {evaluate(run, judgments)['rr'].mean():.3f}")
    print(f"{name} queries with rr of 1:", (rr == 1).sum())
```

Output:

```text
rr, exact counts as relevant: 0.500
rr, partial or better counts: 1.000
bm25 mrr: 0.650
bm25 mrr from lib.metrics: 0.650
bm25 queries with rr of 1: 16
semantic mrr: 0.787
semantic mrr from lib.metrics: 0.787
semantic queries with rr of 1: 22
```

BM25's first result for `clear shower curtain` is a partial match and its second is exact, so RR is 0.500 when only exact products count, and 1.000 when partial ones count too. Whenever you quote RR, say which grades count. Over the test queries, BM25's MRR is 0.650 and semantic retrieval's is 0.787, matching the `rr` column of `lib.metrics.evaluate`. That column looks for the first exact product anywhere in the [run](#score-every-test-query), not only in the top 10.

RR is 1 for 22 test queries under semantic retrieval, and for 16 under BM25. On those queries RR sees nothing below the first result: a ranker that puts one exact product first and nine irrelevant ones after it scores the same as a perfect top 10.

**Working rule:** Report MRR as the headline only when shoppers need one right product, as for a model number or a named product such as `kohler whitehaven farmhouse kitchen sink`. For queries where shoppers browse a page of options, such as `wooden chair outdoor`, use nDCG@10 as the headline and report MRR beside it.

## Build nDCG from discounted gains {#build-ndcg-from-dcg}

[Chapter 1](#score-one-ranking) scored one ranking with nDCG@10, which, unlike precision and RR, uses the grades. Each result's grade is its gain, a discount that grows with position shrinks it, and the sum is the **discounted cumulative gain** (DCG). **Normalized DCG** (nDCG) divides that by the DCG of the ideal ranking. Two of its parts come in several versions that change the number. The first is the ideal ranking. Järvelin and Kekäläinen, who introduced DCG, base it on "the recall base of the search topic rather than on the result of some IR technique" ([Järvelin and Kekäläinen, 2002](https://doi.org/10.1145/582415.582418)): the best order of every product judged for the query, not only of the products a ranker returned. The second is the discount. They proposed that "a simple way of discounting with this requirement is to divide the document score by the log of its rank", and versions differ in which log, from which rank.

The formula in `lib.metrics`, where grade(i) is the grade of the product at position i:

```text
DCG@k  = sum over positions i from 1 to k of  grade(i) / log2(i + 1)
nDCG@k = DCG@k / DCG@k of the ideal ranking
```

This isn't the only version in use. Järvelin and Kekäläinen left the ranks below the log's base undiscounted, so with base 2 the first two positions count in full. Burges et al. used an exponential gain, 2^grade − 1, with a log(1 + rank) discount ([Burges et al., 2005](https://icml.cc/Conferences/2005/proceedings/papers/012_LearningToRank_BurgesEtAl.pdf)). Evaluation tools differ as well: the ir-measures documentation lists different nDCG options for pytrec_eval and for gdeval ([ir-measures](https://ir-measur.es/en/latest/measures.html)). So whenever you quote an nDCG, name the variant.

Write DCG and nDCG from scratch and check them against `lib.metrics` on the store's BM25, semantic and [hybrid](#fuse-with-rrf) runs from chapter 1. Then look at one test query with a perfect score:

Example `ndcg-from-scratch` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import math

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


def dcg(grades, k):
    """Each grade divided by log2 of its position plus one, added up over the top k."""
    return sum(grade / math.log2(position + 1) for position, grade in enumerate(grades[:k], start=1))


def ndcg(ranking, judgments, k=10):
    """DCG of the ranking over DCG of the best order of every judged product (unjudged counts as 0)."""
    ideal = dcg(sorted(judgments.values(), reverse=True), k)
    return dcg([judgments.get(product_id, 0) for product_id in ranking], k) / ideal


queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"bm25": bm25, "semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}

gaps = [abs(ndcg(run[query_id], judgments[query_id]) - ndcg_at_k(run[query_id], judgments[query_id], 10))
        for run in runs.values() for query_id in judgments]
print("rankings checked:", len(gaps))
print(f"largest difference from lib.metrics: {max(gaps):.3f}")

ranking, per_query = bm25[461], judgments[461]                     # luau string lights
print()
print("query:", queries.at[461, "query"])
print("grades in the top 10:", [per_query.get(product_id, 0) for product_id in ranking[:10]])
print("best possible grades:", sorted(per_query.values(), reverse=True)[:10])
print("exact products judged:", sum(grade == 2 for grade in per_query.values()))
print("exact in the top 10:", sum(per_query.get(product_id, 0) == 2 for product_id in ranking[:10]))
print(f"ndcg@10: {ndcg(ranking, per_query):.3f}")
```

Output:

```text
rankings checked: 90
largest difference from lib.metrics: 0.000

query: luau string lights
grades in the top 10: [2, 2, 2, 2, 1, 1, 1, 1, 1, 1]
best possible grades: [2, 2, 2, 2, 1, 1, 1, 1, 1, 1]
exact products judged: 4
exact in the top 10: 4
ndcg@10: 1.000
```

All 90 rankings agree with `lib.metrics` to three decimals: the largest difference is 0.000. For `luau string lights`, BM25's top 10 holds 4 exact products and scores 1.000. That's not a mistake. The query has only 4 exact products judged, so the best possible top 10 holds those and then partial ones, and BM25 found that order. An nDCG@10 of 1 means "as good as the best order of the judged products", not "ten exact products".

**Working rule:** Use the linear-gain, log2(i + 1) form at a cutoff of 10, with the ideal ranking built from every judged product, and state that variant whenever you quote a number. Compare nDCG only between runs scored on the same judgments: new judgments change the ideal ranking, and with it every score.

## Match scikit-learn's `ndcg_score` {#match-scikit-learn-ndcg}

Once you've built a metric, check it against a library that computes it independently. At scikit-learn 1.9.1, `ndcg_score` uses the same variant as `lib.metrics`: the grades are the gains, each is divided by log2(rank + 1), and the normalizing DCG is that of the same grades sorted into the best order, cut at `k` ([scikit-learn source](https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.9.1/sklearn/metrics/_ranking.py)). Its documentation cites Järvelin and Kekäläinen, though the code implements the later rank + 1 form ([scikit-learn documentation](https://scikit-learn.org/1.9/modules/generated/sklearn.metrics.ndcg_score.html)). Three details make a naive call disagree with your own:

- It scores only the products you pass, so it builds the ideal ranking from those alone.
- By default it averages the gains of products whose scores tie (scikit-learn documentation). That equals the average over every order of the tied products ([McSherry and Najork, 2008](https://www.microsoft.com/en-us/research/?p=144984)).
- It takes one row per query, every row the same length, and returns the mean over the rows (scikit-learn source).

In the store, first pass `ndcg_score` the grades of BM25's top 10 for `clear shower curtain`, with scores that put them in BM25's order. Then build each query's row the way `lib.metrics` sees the query, and compare all three runs:

Example `ndcg-matches-scikit-learn` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from sklearn.metrics import ndcg_score

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


def sklearn_ndcg(ranking, judgments, k=10):
    """One row for one query: every judged product, plus any retrieved product nobody judged."""
    products = list(dict.fromkeys([*judgments, *ranking]))
    position = {product_id: i for i, product_id in enumerate(ranking)}
    grades = [[judgments.get(product_id, 0) for product_id in products]]
    scores = [[-position.get(product_id, len(ranking)) for product_id in products]]  # not retrieved: below all
    return ndcg_score(grades, scores, k=k)


queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"bm25": bm25, "semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}

top = bm25[246][:10]                                                # clear shower curtain
naive = ndcg_score([[judgments[246].get(product_id, 0) for product_id in top]], [list(range(10, 0, -1))], k=10)
print(f"ndcg@10, only the top 10 passed: {naive:.3f}")
print(f"ndcg@10 from lib.metrics: {ndcg_at_k(top, judgments[246], 10):.3f}")
print(f"ndcg@10, every judged product passed: {sklearn_ndcg(top, judgments[246]):.3f}")

gaps = [abs(sklearn_ndcg(run[query_id], judgments[query_id]) - ndcg_at_k(run[query_id], judgments[query_id], 10))
        for run in runs.values() for query_id in judgments]
print("rankings compared:", len(gaps))
print(f"largest difference: {max(gaps):.3f}")

short = bm25[246][:5]                                               # a ranking shorter than k
print(f"5-product ranking, lib.metrics: {ndcg_at_k(short, judgments[246], 10):.3f}")
print(f"5-product ranking, scikit-learn: {sklearn_ndcg(short, judgments[246]):.3f}")
```

Output:

```text
ndcg@10, only the top 10 passed: 0.901
ndcg@10 from lib.metrics: 0.615
ndcg@10, every judged product passed: 0.615
rankings compared: 90
largest difference: 0.000
5-product ranking, lib.metrics: 0.539
5-product ranking, scikit-learn: 0.629
```

Passed only the top 10, `ndcg_score` returns 0.901, against 0.615 from `lib.metrics`. It divides by the best order of those ten products, not of the [253 products judged](#check-against-judgments) for the query, so it can't see the exact products BM25 missed. The example's `sklearn_ndcg` fixes that with a recipe. Each row holds every judged product, plus any retrieved product nobody judged (grade 0). The recipe scores retrieved products by their rank, and gives every other product one score below all of them. With that recipe the two agree on all 90 rankings (largest difference 0.000). Call `ndcg_score` once per query and average the results yourself, because each query's row has a different length.

The recipe has one limit. When a run holds fewer than k products, the products it didn't retrieve tie for the empty places inside the top k, and `ndcg_score` credits them with their average gain. `lib.metrics` gives an empty place nothing, because the shopper sees nothing there. For BM25's ranking cut to 5 products, `lib.metrics` gives 0.539 and `ndcg_score` gives 0.629. Short runs happen: `LexicalSearch` returns only products with a score above 0.

**Working rule:** Report your own nDCG, and use `ndcg_score` as an independent check, with every judged product in each query's row and scores taken from ranks. Before you compare the two, check that every run holds at least k products. If you pass a ranker's raw scores instead, break ties in a fixed order first, such as by `product_id`, or the two will disagree wherever scores tie.

## Choose a metric before you compare {#choose-a-ranking-metric}

Every metric is a model of a shopper. Precision@10 assumes the shopper looks at the whole first page and counts the good products on it. RR assumes the shopper stops at the first good product. nDCG@10 assumes attention fades down the page and that an exact product is worth more than a partial one: with the book's grades, twice as much. Exponential gains, 2^grade − 1 as in [Burges et al. (2005)](https://icml.cc/Conferences/2005/proceedings/papers/012_LearningToRank_BurgesEtAl.pdf), turn the grades into gains of 0, 1 and 3, so an exact product is worth three partial ones. As a rule of thumb, these models agree when two rankers are far apart. When the rankers are close, the metric can pick the winner, which is why you choose it before you look at results. Fuhr asks for hypotheses stated before the experiment, in the form "We want to compare methods A and B using metric X" ([Fuhr, 2017, section 2.6](https://sigir.org/wp-content/uploads/2018/01/p032.pdf)).

In the store, take semantic retrieval, the ranker to beat, and the hybrid, which [chapter 1](#fuse-with-rrf) couldn't separate from it. Choosing a metric is part of tuning the evaluation, so make the choice on the 50 train queries and keep the test queries for reporting. Score both rankers four ways:

Example `metric-choice-on-train` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # choosing a metric is tuning: use train
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}

exponential = {query_id: {product_id: 2 ** grade - 1 for product_id, grade in per_query.items()}
               for query_id, per_query in judgments.items()}       # gains 0, 1, 3 instead of 0, 1, 2
means = {}
for name, run in runs.items():
    scores = evaluate(run, judgments)
    means[name] = {"precision@10": scores["precision@10"].mean(), "mrr": scores["rr"].mean(),
                   "ndcg@10": scores["ndcg@10"].mean(),
                   "ndcg@10 with exponential gains": evaluate(run, exponential)["ndcg@10"].mean()}

print("train queries:", len(judgments))
winners = []
for metric in means["semantic"]:
    for name in runs:
        print(f"{name} {metric}: {means[name][metric]:.3f}")
    winners.append(max(runs, key=lambda name: means[name][metric]))
    print(f"higher {metric}: {winners[-1]}")
for name in runs:
    print(f"metrics won by {name}:", winners.count(name))
print(f"largest gap: {max(abs(means['semantic'][m] - means['hybrid'][m]) for m in means['semantic']):.3f}")
```

Output:

```text
train queries: 50
semantic precision@10: 0.502
hybrid precision@10: 0.488
higher precision@10: semantic
semantic mrr: 0.673
hybrid mrr: 0.710
higher mrr: hybrid
semantic ndcg@10: 0.772
hybrid ndcg@10: 0.774
higher ndcg@10: hybrid
semantic ndcg@10 with exponential gains: 0.709
hybrid ndcg@10 with exponential gains: 0.708
higher ndcg@10 with exponential gains: semantic
metrics won by semantic: 2
metrics won by hybrid: 2
largest gap: 0.037
```

Semantic retrieval scores higher on 2 of the four metrics and the hybrid on 2. Precision@10 puts `semantic` ahead (0.502 for semantic retrieval, 0.488 for the hybrid), and MRR puts `hybrid` ahead (0.673 and 0.710, in the same order). nDCG@10 favours `hybrid` (0.772 and 0.774), and exponential gains favour `semantic` (0.709 and 0.708). The largest of the four gaps is 0.037. These are train queries, so the gaps say nothing about which ranker is better. They show that when two rankers are this close, the metric decides which way the gap falls.

So the choice should follow the shopper, not the result. The store shows a page of products and its judgments are graded, so nDCG@10 with linear gains stays the headline, as [chapter 1](#score-one-ranking) chose, with precision@10 and MRR beside it.

**Working rule:** Choose one headline metric, its gains and its cutoff before you compare rankers, and write them down. We recommend nDCG@10 with linear gains when judgments are graded and shoppers browse a page. Switch to exponential gains when an exact match is worth far more than a near one, as for a spare part that must fit, and to MRR when most queries have one right answer. Report the other metrics beside the headline, and never change the headline after you've seen which ranker it favours.

## Read per-query differences, not only the mean {#read-per-query-differences}

A mean of the headline metric over queries is a summary for the store. A shopper sees one query's results. The TREC Robust track was built on that point: "an individual user does not see the average performance of the system, but only the effectiveness of the system on his or her requests". It found that optimizing the average "further improves the effectiveness of the already-effective topics, sometimes at the expense of the poor performers" ([Voorhees, 2004](https://trec.nist.gov/pubs/trec13/papers/ROBUST.OVERVIEW.pdf)). So before you trust a change in the mean, look at the **per-query differences**: one number per query, the new ranker's score minus the old one's. They are also the evidence that the [significance tests](#permutation-test-on-queries) use.

The store's hybrid run from [chapter 1](#fuse-with-rrf) scores well above BM25 on average. Compare the two query by query on nDCG@10:

Example `per-query-hybrid-versus-bm25` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, SemanticSearch().run(queries, k=100)])
before, after = evaluate(bm25, judgments), evaluate(hybrid, judgments)

difference = (after["ndcg@10"] - before["ndcg@10"]).round(3).sort_values()   # one value per test query
print(f"mean difference: {difference.mean():.3f}")
print(f"median difference: {difference.median():.3f}")
print("hybrid better:", (difference > 0).sum())
print("bm25 better:", (difference < 0).sum())
print("tied:", (difference == 0).sum())

print("\nhybrid's three largest losses:")
print(queries.loc[difference.index[:3], "query"].to_frame().assign(difference=difference[:3]).to_string())
largest = difference.index[-1]
print("\nlargest gain:", queries.at[largest, "query"])
print(f"its gain: {difference[largest]:.3f}")
print(f"its bm25 judged@10: {before.at[largest, 'judged@10']:.3f}")
print(f"share of the mean gain from this query: {difference[largest] / difference.sum():.3f}")

relative = after["ndcg@10"] / before["ndcg@10"] - 1                            # per-query relative gains
print(f"\nrelative gain of the means: {after['ndcg@10'].mean() / before['ndcg@10'].mean() - 1:.3f}")
print(f"mean of per-query relative gains: {relative.mean():.3f}")
print(f"its bm25 ndcg@10: {before.at[largest, 'ndcg@10']:.3f}")
print(f"its relative gain: {relative[largest]:.3f}")
print(f"mean of per-query relative gains without it: {relative.drop(largest).mean():.3f}")
```

Output:

```text
mean difference: 0.087
median difference: 0.057
hybrid better: 17
bm25 better: 7
tied: 6

hybrid's three largest losses:
                             query  difference
query_id
293       wood floor protector mat      -0.072
292        decorative white pillow      -0.069
249        bistro table and chairs      -0.066

largest gain: outdoor light fixtures
its gain: 0.714
its bm25 judged@10: 0.200
share of the mean gain from this query: 0.274

relative gain of the means: 0.120
mean of per-query relative gains: 0.218
its bm25 ndcg@10: 0.286
its relative gain: 2.492
mean of per-query relative gains without it: 0.140
```

The mean gain is 0.087, but the median is 0.057. The hybrid is better on 17 queries, worse on 7 and tied on 6. One query does much of the work: `outdoor light fixtures` gains 0.714, a share of 0.274 of the total gain, and BM25's judged@10 on it is 0.200. [Judged@10](#score-every-test-query) is the share of the top 10 that has a judgment for the query. For this query BM25's top 10 is mostly light bulbs nobody judged, and [chapter 1](#score-every-test-query) argues that their grade of 0 is fair, so the gain holds. For another query, the unjudged products a ranker drops might be good ones. The output also lists the hybrid's three largest losses. Those are the queries where a shopper would see search get worse, and the first ones to read.

Report the difference as an absolute number. The relative gain of the means is 0.120, but the mean of the per-query relative gains is 0.218, because a mean of per-query ratios gives most weight to the queries where BM25 scores low. `outdoor light fixtures`, where BM25 scores 0.286, contributes a relative gain of 2.492 on its own; without it, the mean of relative gains is 0.140. Fuhr shows that the relative change in a mean says nothing reliable about the change per query, and that "for arithmetic mean, only absolute improvements are meaningful" ([Fuhr, 2017, section 2.4](https://sigir.org/wp-content/uploads/2018/01/p032.pdf)).

**Working rule:** For every comparison, print the mean and median difference, the counts of wins, losses and ties, and the queries with the largest losses, then read those queries. Check judged@10 on the queries that move most before you credit the ranker. Report absolute differences of means, not percentages.

## Test a gap with a permutation test {#permutation-test-on-queries}

A gap between two means on a few dozen queries can come from chance alone: with a different sample of queries, the gap would be different. Shallow metrics make this worse. Buckley and Voorhees found that researchers using a measure such as precision at 10 "will need to use many more than 50 queries" to tell systems apart reliably ([Buckley and Voorhees, 2000](https://nist.gov/publications/evaluating-evaluation-measure-stability)). A **significance test** asks how surprising the gap would be if the two rankers were equally good, an assumption called the **null hypothesis**. Its answer is the **p-value**: the probability, under the null hypothesis, of a gap at least as large as the one you measured. By convention, a p-value below 0.05 counts as evidence of a real difference, and [the book's rule](#when-a-difference-is-established) tightens that when a chapter makes several comparisons.

The tests in this book are **paired**: both rankers are scored on the same queries, so each test works on the [per-query differences](#read-per-query-differences), and a hard query's low scores cancel out. A **permutation test** builds the gaps you'd see under the null hypothesis directly. If the two rankers were interchangeable, each query's difference would be as likely to have the opposite sign. So flip each sign at random, recompute the mean, repeat thousands of times, and count how often the flipped mean lands at least as far from 0 as the real one. For n queries there are 2^n sign patterns, 1,073,741,824 for the test queries, so the test samples 9,999 of them, and its p-value is an estimate.

In the store, the hybrid trails semantic retrieval on the test queries, and [chapter 1](#fuse-with-rrf) left open whether that gap is real. Against semantic retrieval, the hybrid's wins, losses and ties over the test queries are 9 / 14 / 7. Before you read the output, predict: will the test find the hybrid's deficit larger than chance?

Example `permutation-test-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np
from scipy.stats import permutation_test

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([LexicalSearch(load_products()).run(queries, k=100), semantic])
after = evaluate(hybrid, judgments)["ndcg@10"].to_numpy()
before = evaluate(semantic, judgments)["ndcg@10"].to_numpy()
difference = after - before                                       # hybrid minus semantic, per test query
print("test queries:", len(difference))
print(f"sign patterns for the test queries: {2 ** len(difference):,}")
print(f"observed mean difference: {difference.mean():.3f}")

# if the two rankers were interchangeable, each query's difference would be as likely to have the other sign
rng = np.random.default_rng(2026)
signs = rng.choice([-1, 1], size=(9999, len(difference)))
flipped = (signs * difference).mean(axis=1)                       # 9,999 mean differences under that assumption
print(f"95% of flipped means are smaller than: {np.quantile(np.abs(flipped), 0.95):.3f}")
print(f"p-value by hand: {np.mean(np.abs(flipped) >= abs(difference.mean())):.3f}")

result = permutation_test((after, before), lambda after_scores, before_scores, axis: np.mean(after_scores - before_scores, axis=axis),
                          permutation_type="samples", rng=np.random.default_rng(2026))
print(f"p-value from scipy: {result.pvalue:.3f}")
print("difference at the 0.05 level:", "larger than chance" if result.pvalue < 0.05 else "within chance")
```

Output:

```text
test queries: 30
sign patterns for the test queries: 1,073,741,824
observed mean difference: -0.018
95% of flipped means are smaller than: 0.022
p-value by hand: 0.117
p-value from scipy: 0.125
difference at the 0.05 level: within chance
```

The observed mean difference is -0.018. Of the 9,999 flipped means, 95% are smaller than 0.022 in size, and the share at least as large as the observed one, the p-value, is 0.117. SciPy's `permutation_test` with `permutation_type="samples"`, the setting its documentation gives for paired tests, returns 0.125 ([SciPy documentation](https://docs.scipy.org/doc/scipy-1.18.0/reference/generated/scipy.stats.permutation_test.html)). The two estimates differ a little because each draws its own random sign patterns. At the 0.05 level, the difference is within chance. If you predicted a real deficit, you trusted the mean over the spread: a few queries swinging the other way would close the gap.

SciPy's resampling functions take their random generator through `rng`, which replaces the `random_state` argument. At 1.18.1 both work, but the documentation says that "only the rng keyword should be used in new code", because calls that use `random_state` will emit warnings after a transition period (SciPy documentation). Every example in this book passes `rng` with a fixed seed.

**Working rule:** Test every gap you intend to act on with a paired permutation test on the per-query differences. The book decides on this test, as [its rule](#when-a-difference-is-established) sets out. Read a p-value above the threshold as "no evidence of a difference", never as "no difference": with this few queries, a test can miss a real gap, and McKechnie et al. argue for measuring such misses alongside false positives ([McKechnie et al., 2025](https://arxiv.org/abs/2507.07924)). Never explain a gap the test can't tell from chance.

## Get the p-value from a paired t-test {#paired-t-test-on-queries}

The paired t-test answers the same question with a formula instead of resampling. It divides the mean of the [per-query differences](#read-per-query-differences) by its **standard error**: the standard deviation of the differences divided by the square root of the number of queries, which estimates how far the mean would move from one sample of queries to another. If the rankers are equally good and the differences are roughly normal, that ratio, t, follows a **t distribution**: a bell-shaped curve with heavier tails than the normal, whose shape depends on its degrees of freedom, here one fewer than the number of queries. The p-value is the probability of a t at least that far from 0 in either direction ([Sakai, 2014, section 3.1.1](https://sigir.org/files/forum/2014J/2014J_sigirforum_Article_TetsuyaSakai.pdf)):

```text
t = mean(d) / (sd(d) / sqrt(n))      d: the per-query differences, n: the number of queries
```

Per-query nDCG differences are bounded between −1 and 1 and have outliers, such as the [gain on `outdoor light fixtures`](#read-per-query-differences), so they aren't normal. In practice the t-test holds up. On TREC runs scored with mean average precision (MAP, another ranking metric) on 50 topics, Smucker et al. found "little practical difference between the randomization, bootstrap, and t tests", where the randomization test is the [permutation test](#permutation-test-on-queries) ([Smucker et al., 2007](https://ciir-publications.cs.umass.edu/getpdf.php?id=744)). In a simulation built from TREC data, with sets of 25, 50 and 100 topics, Urbano et al. found that "both the t-test and the permutation test behave almost identically" ([Urbano et al., 2019](https://arxiv.org/abs/1905.11096)). Both studies advise against the Wilcoxon signed-rank and sign tests for this job. SciPy's `wilcoxon` also drops every query whose difference is exactly 0 by default, with `zero_method='wilcox'` ([SciPy documentation](https://docs.scipy.org/doc/scipy-1.18.0/reference/generated/scipy.stats.wilcoxon.html)), and many queries tie when two runs differ a little.

Compute t by hand for two of the store's gaps from chapter 1, [semantic retrieval against BM25](#search-by-meaning) and [the hybrid against semantic retrieval](#fuse-with-rrf), and compare with SciPy's `ttest_rel`:

Example `paired-t-test-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import math

from scipy.stats import t, ttest_rel

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"bm25": bm25, "semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}
ndcg = {name: evaluate(run, judgments)["ndcg@10"] for name, run in runs.items()}   # per test query

for after, before in [("semantic", "bm25"), ("hybrid", "semantic")]:
    difference = ndcg[after] - ndcg[before]
    n = len(difference)
    standard_error = difference.std(ddof=1) / math.sqrt(n)      # how much the mean would move between samples
    statistic = difference.mean() / standard_error
    p_value = 2 * t.sf(abs(statistic), df=n - 1)               # both tails of the t distribution
    print(f"{after} minus {before}: {difference.mean():.3f}")
    print(f"{after} minus {before} t by hand: {statistic:.3f}")
    print(f"{after} minus {before} p by hand: {p_value:.3f}")
    print(f"{after} minus {before} p from ttest_rel: {ttest_rel(ndcg[after], ndcg[before]).pvalue:.3f}")
```

Output:

```text
semantic minus bm25: 0.105
semantic minus bm25 t by hand: 3.294
semantic minus bm25 p by hand: 0.003
semantic minus bm25 p from ttest_rel: 0.003
hybrid minus semantic: -0.018
hybrid minus semantic t by hand: -1.590
hybrid minus semantic p by hand: 0.123
hybrid minus semantic p from ttest_rel: 0.123
```

For semantic retrieval against BM25, the mean difference of 0.105 gives t = 3.294 and a p-value of 0.003, the same as `ttest_rel` gives: a gap that chance would rarely produce. For the hybrid against semantic retrieval, t = -1.590 and the p-value is 0.123, close to the permutation test's 0.125 for the [same gap](#permutation-test-on-queries).

**Working rule:** Report the paired t-test, `scipy.stats.ttest_rel`, beside the permutation test, as a check that needs no resampling. When the two fall on different sides of the threshold, say so, and let the permutation test decide. Don't use the Wilcoxon or sign test to compare mean scores.

## Report how big the gap is {#report-the-size-of-a-gap}

A p-value says how surprising a gap is, not how big it is. On a large sample, "almost any modification will result in a significant, but tiny difference" ([Fuhr, 2017, section 2.8](https://sigir.org/wp-content/uploads/2018/01/p032.pdf)), and Sakai recommends reporting an effect size and a confidence interval with every p-value ([Sakai, 2014](https://sigir.org/files/forum/2014J/2014J_sigirforum_Article_TetsuyaSakai.pdf)). A **confidence interval** is a range of plausible values for the true mean difference, meaning the mean over all queries like these, scored with these judgments, not over the store's search traffic. A 95% interval comes from a procedure meant to cover that value 95% of the time. The **bootstrap** builds one by resampling. Draw as many queries as you have from the queries you have, with replacement, so that some appear twice and others not at all. Compute the mean difference, repeat thousands of times, and take the middle 95% of those means: the **percentile interval**. The **effect size** of a paired comparison is the mean difference divided by the standard deviation of the differences (Sakai, 2014, section 3.1.2): how large the gap is next to how much it varies from query to query. It isn't Cohen's d, the effect size for unpaired samples, and Sakai warns that the two "should not be compared directly".

In the store, build the percentile interval by hand for semantic retrieval against BM25 and the hybrid against semantic retrieval. Check it with SciPy's `bootstrap` set to `method="percentile"`, then run SciPy's default method:

Example `bootstrap-interval-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np
from scipy.stats import bootstrap

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
runs = {"bm25": bm25, "semantic": semantic, "hybrid": reciprocal_rank_fusion([bm25, semantic])}
ndcg = {name: evaluate(run, judgments)["ndcg@10"] for name, run in runs.items()}   # per test query

for after, before in [("semantic", "bm25"), ("hybrid", "semantic")]:
    difference, name = (ndcg[after] - ndcg[before]).to_numpy(), f"{after} minus {before}"
    resampled = np.random.default_rng(2026).choice(difference, size=(9999, len(difference)))  # 9,999 sets of queries
    low, high = np.percentile(resampled.mean(axis=1), [2.5, 97.5])      # the middle 95% of their means
    print(f"{name}: {difference.mean():.3f}")
    print(f"{name} interval by hand: {low:.3f} to {high:.3f}")
    percentile = bootstrap((difference,), np.mean, method="percentile", rng=np.random.default_rng(2026))
    print(f"{name} percentile interval from scipy: "
          f"{percentile.confidence_interval.low:.3f} to {percentile.confidence_interval.high:.3f}")
    bca = bootstrap((difference,), np.mean, rng=np.random.default_rng(2026)).confidence_interval   # BCa, the default
    print(f"{name} bca low: {bca.low:.3f}\n{name} bca high: {bca.high:.3f}")
    print(f"{name} bca interval and 0: {'includes 0' if bca.low <= 0 <= bca.high else 'excludes 0'}")
    print(f"{name} effect size: {difference.mean() / difference.std(ddof=1):.3f}")
```

Output:

```text
semantic minus bm25: 0.105
semantic minus bm25 interval by hand: 0.049 to 0.172
semantic minus bm25 percentile interval from scipy: 0.049 to 0.172
semantic minus bm25 bca low: 0.055
semantic minus bm25 bca high: 0.185
semantic minus bm25 bca interval and 0: excludes 0
semantic minus bm25 effect size: 0.601
hybrid minus semantic: -0.018
hybrid minus semantic interval by hand: -0.041 to 0.003
hybrid minus semantic percentile interval from scipy: -0.041 to 0.003
hybrid minus semantic bca low: -0.042
hybrid minus semantic bca high: 0.002
hybrid minus semantic bca interval and 0: includes 0
hybrid minus semantic effect size: -0.290
```

SciPy's percentile interval matches the one built by hand: 0.049 to 0.172 and -0.041 to 0.003. Its default method, BCa (bias-corrected and accelerated), reads different percentiles off the same resampled means. It shifts them by how far the resampled means sit off-centre from the observed mean, and stretches them by the skew it estimates by leaving out one query at a time ([SciPy source](https://github.com/scipy/scipy/blob/v1.18.1/scipy/stats/_resampling.py)). The book's [harness](#compare-runs-in-a-harness) reports BCa, which is designed for skewed resampled means like these. For semantic retrieval against BM25, BCa runs from 0.055 to 0.185, so it excludes 0, and the effect size is 0.601. For the hybrid against semantic retrieval, it runs from -0.042 to 0.002, so it includes 0, and the effect size is -0.290. That interval allows anything from a loss of a few hundredths to a gain of at most 0.002: no gain worth having.

A bootstrap interval only approximates its level, and on a few dozen queries it falls short. To check, treat the hybrid's 30 differences against semantic retrieval as if they were every query there is, so the true gap is known. Then draw 1000 new sets of the same size from them, build an interval on each, and count how often it covers the true gap:

Example `interval-coverage-check` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np
from scipy.stats import bootstrap, ttest_1samp

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([LexicalSearch(load_products()).run(queries, k=100), semantic])
population = (evaluate(hybrid, judgments)["ndcg@10"] - evaluate(semantic, judgments)["ndcg@10"]).to_numpy()
true_gap = population.mean()            # known, because these differences stand in for every query there is

rng, trials = np.random.default_rng(2026), 1000
print("trials:", trials)
print(f"standard error of a coverage near 0.95: {(0.95 * 0.05 / trials) ** 0.5:.3f}")
for level in [0.95, round(1 - 0.05 / 3, 4)]:          # the usual level, and the level for three comparisons
    covered = {"bca": 0, "t": 0}
    for _ in range(trials):
        sample = rng.choice(population, size=len(population))      # another set of 30 queries like these
        bca = bootstrap((sample,), np.mean, confidence_level=level, n_resamples=1999, rng=rng).confidence_interval
        t = ttest_1samp(sample, 0).confidence_interval(level)     # the interval that matches the t-test
        covered["bca"] += bca.low <= true_gap <= bca.high
        covered["t"] += t.low <= true_gap <= t.high
    for method, count in covered.items():
        print(f"{method} coverage at {level}: {count / trials:.3f}")
```

Output:

```text
trials: 1000
standard error of a coverage near 0.95: 0.007
bca coverage at 0.95: 0.927
t coverage at 0.95: 0.945
bca coverage at 0.9833: 0.955
t coverage at 0.9833: 0.975
```

At a nominal 95%, BCa covers the true gap 0.927 of the time and the t-test's interval 0.945. At 0.9833, the level [the harness](#compare-runs-in-a-harness) uses, BCa covers 0.955 and the t interval 0.975. Each figure is uncertain by about 0.007 either way. BCa falls short of its level at both, and the t interval comes closer to its own. So a bootstrap interval that barely excludes 0 deserves care. In a simulation, a test built on the same resampling, the bootstrap-shift test, also "shows a systematic bias towards small p-values" ([Urbano et al., 2019](https://arxiv.org/abs/1905.11096)).

Whether a gap matters is a judgment no test makes for you. For precision@10, Fuhr notes, "a difference of 0.02 translates into one more relevant document per five queries" (Fuhr, 2017, section 2.8). For nDCG@10, decide before you test what gap would justify the cost of a change.

**Working rule:** Report every comparison as the mean difference, with its bootstrap interval, its effect size and its p-value. If the interval includes 0, the comparison shows no improvement. If it excludes 0 but lies below the smallest gap worth the change's cost, the difference may be real and still not worth shipping. Use the interval to describe a gap's size, not to decide whether it exists.

## Decide in advance what counts as established {#when-a-difference-is-established}

Every test at 0.05 carries a 5% chance of a false positive when the gap is noise, and a chapter that runs several tests runs that risk several times. Comparing every pair of 10 systems this way gives a probability of about 0.90 of at least one false "significant" result, if every gap is noise and the tests are independent ([Sakai, 2014, section 3](https://sigir.org/files/forum/2014J/2014J_sigirforum_Article_TetsuyaSakai.pdf)). The **Bonferroni correction** is a simple, conservative fix: when you test m hypotheses, test each at 0.05 divided by m ([Fuhr, 2017, section 2.7](https://sigir.org/wp-content/uploads/2018/01/p032.pdf)). It keeps the chance of any false positive at or below 0.05 whether or not the tests are independent. It only works if the m comparisons are fixed before you see the results. Fuhr names the usual way to break that: "it would be incorrect if an author first determines which of the competing methods performs best on his data set, and then compares his own approach only to this one" (Fuhr, 2017, section 2.6).

So the book uses one rule, in every chapter:

1. **List the planned comparisons on the test queries** before reporting any of them.
2. **A difference is established** when its paired [permutation test](#permutation-test-on-queries) gives a p-value below the chapter's Bonferroni threshold: 0.05 divided by the number of planned comparisons.
3. **Report the paired t-test and a bootstrap interval beside it**, the interval at the matching level, 1 minus the threshold. When either disagrees with the permutation test, say so.
4. **A comparison chosen after looking at test results is exploratory.** Label it so, and never call it established.
5. **Comparisons on train queries are for tuning,** not evidence.

We let the permutation test decide because it assumes nothing about the shape of the differences, only that under the null hypothesis each query's sign is a coin flip. Urbano et al. found that it and the t-test "behave almost identically" ([Urbano et al., 2019](https://arxiv.org/abs/1905.11096)), which makes the t-test a good check. Bootstrap intervals on a few dozen queries cover less often than their level ([coverage check](#report-the-size-of-a-gap)), which is why an interval describes a gap but doesn't decide it.

Chapter 1 builds the store's pipeline one stage at a time, and that order alone fixes its planned comparisons: each stage against the one before it. That gives semantic retrieval against BM25, the hybrid against semantic retrieval, and the reranked hybrid against the hybrid, 3 in all. The threshold is 0.0167, and the intervals use a level of 0.9833. Comparing the reranked hybrid with semantic retrieval is exploratory, because semantic retrieval became the ranker to beat by scoring highest on these same test queries.

**Working rule:** Write the list of planned comparisons before you score anything on the test queries, and keep it short, since each one raises the bar for the others. When you need to compare many rankers at once, Bonferroni gets very strict. Sakai recommends an analysis of variance, which tests whether any of the rankers differ at all, followed by the randomised Tukey HSD test, which compares every pair while holding the chance of any false positive at the level (Sakai, 2014).

## Compare runs in an evaluation harness {#compare-runs-in-a-harness}

The book applies [that rule](#when-a-difference-is-established) in an **evaluation harness**, which holds everything fixed except the ranker: the same queries, judgments, metrics and tests, so that two runs differ only in their rankings. `lib.metrics.evaluate` returns one row per query, which is the shape the paired tests need. `compare` in `lib.significance`, a short module that collects this chapter's code, runs the tests on one metric's column from two runs. It returns the mean difference, the bootstrap interval, the permutation and t-test p-values, the effect size, and the wins, losses and ties. Its `verdict` function applies [the book's rule](#when-a-difference-is-established) to a result. Keep the per-query frames, and average only at the end.

In the store, run chapter 1's four rankers through the harness, then the 3 planned comparisons and the exploratory one:

Example `compare-chapter-one-rankers` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.recorded import cross_encoder_scores
from lib.semantic import SemanticSearch
from lib.significance import compare, verdict
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])
score = {(query_id, product_id): value for query_id, product_id, value in cross_encoder_scores().itertuples(index=False)}
reranked = {query_id: sorted(ranking[:50], key=lambda product_id: score[(query_id, product_id)], reverse=True)
            + ranking[50:] for query_id, ranking in hybrid.items()}          # chapter 1's rerank of the top 50

runs = {"bm25": bm25, "semantic": semantic, "hybrid": hybrid, "reranked": reranked}
scores = {name: evaluate(run, judgments) for name, run in runs.items()}       # one row per test query
for name, frame in scores.items():
    print(f"{name} ndcg@10: {frame['ndcg@10'].mean():.3f}\n{name} judged@10: {frame['judged@10'].mean():.3f}")

planned = [("semantic", "bm25"), ("hybrid", "semantic"), ("reranked", "hybrid")]    # each stage against the last
exploratory = [("reranked", "semantic")]                       # chosen after chapter 1 saw the test means
threshold = 0.05 / len(planned)                                # Bonferroni, over the planned comparisons only
print(f"\nplanned comparisons: {len(planned)}\np-value threshold: {threshold:.4f}\ninterval level: {1 - threshold:.4f}")
print(f"chance of a false positive, all gaps noise, tests independent: {1 - 0.95 ** len(planned):.3f}")
established, disagreements = 0, 0
for after, before in planned + exploratory:
    result, name = compare(scores[after]["ndcg@10"], scores[before]["ndcg@10"], confidence=1 - threshold), f"{after} minus {before}"
    checks, kind = verdict(result, threshold), "planned" if (after, before) in planned else "exploratory"
    print(f"\n{name}: {result['mean difference']:.3f}\n{name} kind: {kind}")
    print(f"{name} interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
    print(f"{name} permutation p: {result['permutation p']:.3f}\n{name} t-test p: {result['t-test p']:.3f}")
    print(f"{name} effect size: {result['effect size']:.3f}\n{name} wins, losses, ties: {result['wins']} / {result['losses']} / {result['ties']}")
    print(f"{name} established: {'yes' if checks['established'] and kind == 'planned' else 'no'}")
    for method in ["t-test", "interval"]:
        print(f"{name} {method} agrees: {'yes' if checks[method + ' agrees'] else 'no'}")
    if kind == "planned":
        established += checks["established"]
        disagreements += not (checks["t-test agrees"] and checks["interval agrees"])
print(f"\nplanned comparisons established: {established}\nplanned comparisons with a disagreement: {disagreements}")
```

Output:

```text
bm25 ndcg@10: 0.725
bm25 judged@10: 0.927
semantic ndcg@10: 0.830
semantic judged@10: 0.990
hybrid ndcg@10: 0.812
hybrid judged@10: 0.980
reranked ndcg@10: 0.798
reranked judged@10: 0.980

planned comparisons: 3
p-value threshold: 0.0167
interval level: 0.9833
chance of a false positive, all gaps noise, tests independent: 0.143

semantic minus bm25: 0.105
semantic minus bm25 kind: planned
semantic minus bm25 interval: 0.047 to 0.205
semantic minus bm25 permutation p: 0.001
semantic minus bm25 t-test p: 0.003
semantic minus bm25 effect size: 0.601
semantic minus bm25 wins, losses, ties: 21 / 7 / 2
semantic minus bm25 established: yes
semantic minus bm25 t-test agrees: yes
semantic minus bm25 interval agrees: yes

hybrid minus semantic: -0.018
hybrid minus semantic kind: planned
hybrid minus semantic interval: -0.048 to 0.006
hybrid minus semantic permutation p: 0.125
hybrid minus semantic t-test p: 0.123
hybrid minus semantic effect size: -0.290
hybrid minus semantic wins, losses, ties: 9 / 14 / 7
hybrid minus semantic established: no
hybrid minus semantic t-test agrees: yes
hybrid minus semantic interval agrees: yes

reranked minus hybrid: -0.014
reranked minus hybrid kind: planned
reranked minus hybrid interval: -0.053 to 0.020
reranked minus hybrid permutation p: 0.382
reranked minus hybrid t-test p: 0.375
reranked minus hybrid effect size: -0.165
reranked minus hybrid wins, losses, ties: 11 / 12 / 7
reranked minus hybrid established: no
reranked minus hybrid t-test agrees: yes
reranked minus hybrid interval agrees: yes

reranked minus semantic: -0.032
reranked minus semantic kind: exploratory
reranked minus semantic interval: -0.078 to -0.003
reranked minus semantic permutation p: 0.048
reranked minus semantic t-test p: 0.048
reranked minus semantic effect size: -0.377
reranked minus semantic wins, losses, ties: 9 / 16 / 5
reranked minus semantic established: no
reranked minus semantic t-test agrees: yes
reranked minus semantic interval agrees: no

planned comparisons established: 1
planned comparisons with a disagreement: 0
```

BM25's [judged@10](#score-every-test-query) is 0.927, against 0.990 for semantic retrieval, 0.980 for the hybrid and 0.980 for the reranked hybrid, so unjudged products weigh most on BM25. With 3 tests at 0.05 each, the chance of at least one false positive would be 0.143 if every gap were noise and the tests were independent. Bonferroni keeps it at or below 0.05 either way. On nDCG@10 over the test queries, with intervals at the 0.9833 level:

| Measure | Semantic minus BM25 | Hybrid minus semantic | Reranked minus hybrid | Reranked minus semantic |
| --- | --- | --- | --- | --- |
| Kind | planned | planned | planned | exploratory |
| Mean difference | 0.105 | -0.018 | -0.014 | -0.032 |
| Interval | 0.047 to 0.205 | -0.048 to 0.006 | -0.053 to 0.020 | -0.078 to -0.003 |
| Permutation p | 0.001 | 0.125 | 0.382 | 0.048 |
| t-test p | 0.003 | 0.123 | 0.375 | 0.048 |
| Effect size | 0.601 | -0.290 | -0.165 | -0.377 |
| Wins / losses / ties | 21 / 7 / 2 | 9 / 14 / 7 | 11 / 12 / 7 | 9 / 16 / 5 |
| Established | yes | no | no | no |

Of the 3 planned comparisons, 1 is established: semantic retrieval's lead over BM25, with a permutation p-value of 0.001. The hybrid's deficit against semantic retrieval and the reranker's against the hybrid are not established: on these queries neither change shows an improvement, and neither is shown to be worse. The harness also checks the t-test and the interval against the permutation test, and counts 0 planned comparisons where either one disagrees.

The exploratory column is where the methods part. Its permutation p-value is 0.048, to set against 0.05 without a correction and 0.0167 with one, and its interval runs from -0.078 to -0.003. Asked whether each check agrees with the permutation test, the harness answers yes for the t-test and no for the interval: an interval that excludes 0 beside a p-value above the threshold is the kind of disagreement the [coverage check](#report-the-size-of-a-gap) warns about. Whatever its numbers, this comparison can't be established, because it was chosen after seeing the test means. At most it raises a question for new queries: does this reranker trail semantic retrieval?

Chapter 1's decision stands, by a rule that doesn't depend on which ranker scored highest: the ranker to beat is the simplest pipeline that no planned comparison has shown to be beaten. Semantic retrieval beat BM25, and neither later stage beat the stage before it.

**Working rule:** For every change, report the mean nDCG@10 and judged@10 of each run, then a table like this one, with a column for each comparison and the exploratory ones labelled. A change ships only when it is established against the ranker to beat.

## What goes wrong in production {#measuring-search-in-production}

**One sample of queries can mislead.** Results on held-out queries depend on which queries landed there. Fuhr calls the simple holdout method unreliable, "since the results may be heavily dependent on the split", and asks for cross-validation instead ([Fuhr, 2017, section 2.5](https://sigir.org/wp-content/uploads/2018/01/p032.pdf)). Sakai agrees that "different training/validation/test splits may yield different results" ([Sakai, 2020](https://sigir.org/wp-content/uploads/2020/06/p14.pdf)). The book keeps one fixed split so that every chapter reports on the same test queries. To see how far a gap can move, run the exploratory comparison from [the harness](#compare-runs-in-a-harness) on the train queries too. This is an illustration, not evidence, because train queries are for tuning:

Example `split-changes-the-verdict` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.recorded import cross_encoder_scores
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

lexical, embeddings = LexicalSearch(load_products()), SemanticSearch()
score = {(query_id, product_id): value for query_id, product_id, value in cross_encoder_scores().itertuples(index=False)}

for split in ["test", "train"]:                      # the same comparison on another sample of the store's queries
    queries, judgments = load_queries(split), qrels(split)
    semantic = embeddings.run(queries, k=100)
    hybrid = reciprocal_rank_fusion([lexical.run(queries, k=100), semantic])
    reranked = {query_id: sorted(ranking[:50], key=lambda product_id: score[(query_id, product_id)], reverse=True)
                + ranking[50:] for query_id, ranking in hybrid.items()}
    result = compare(evaluate(reranked, judgments)["ndcg@10"], evaluate(semantic, judgments)["ndcg@10"])
    gap = result["mean difference"]
    print(f"{split} queries:", len(judgments))
    print(f"{split} reranked minus semantic: {gap:.3f}")
    print(f"{split} higher-scoring run:", "reranked" if gap > 0 else "semantic" if gap < 0 else "neither")
    if split == "test":
        print(f"test permutation p: {result['permutation p']:.3f}")
```

Output:

```text
test queries: 30
test reranked minus semantic: -0.032
test higher-scoring run: semantic
test permutation p: 0.048
train queries: 50
train reranked minus semantic: 0.014
train higher-scoring run: reranked
```

On the 30 test queries, the reranked hybrid minus semantic retrieval is -0.032 (permutation p = 0.048). On the 50 train queries it is 0.014. The higher-scoring run is `semantic` on the test queries and `reranked` on the train queries. A p-value this close to 0.05 on one sample is a weak thing to build on. [Chapter 11](#keep-test-queries-held-out) covers keeping test queries out of every choice.

**Reusing the test queries is testing many hypotheses.** Every change you test on the same queries adds a comparison, even across months. Fuhr notes that "collection reuse is also a case of multiple hypothesis testing" ([Fuhr, 2017, section 2.7](https://sigir.org/wp-content/uploads/2018/01/p032.pdf)). Keep a log of the comparisons run on your test queries, and count them when you set the threshold.

**Tied scores make runs non-repeatable.** Two products with the same score can come back in either order, and "the interaction between multi-threaded indexing and score ties during retrieval may yield non-deterministic rankings" ([Lin and Yang, 2019](https://arxiv.org/abs/1807.05798)). Even a repeatable order can be arbitrary: a tie falls to whatever order a library's top-k selection, or the input to a stable sort, happens to leave. So the book's modules break ties by `product_id`. `LexicalSearch` and `lib.fusion` sort equal scores by it, and `SemanticSearch` sorts stably over vectors stored in `product_id` order. With every version pinned, `re-check examples` reruns each example against its recorded output, so a change in any of these orders would show. In your own system, break ties in a fixed order that carries no information, such as by `product_id`, before you score.

**Unjudged products lower a ranker's score.** A ranker that surfaces products nobody judged loses nDCG for them, even when they're good. Check [judged@10](#score-every-test-query) before you test, and have new products judged when it falls.

**Working rule:** Log every comparison you run on the test queries, treat a borderline or exploratory result as a question for new queries, break score ties in a fixed order, and report judged@10 next to every nDCG@10.

## Decisions this chapter made {#measuring-search-decisions}

Each choice below is the book's default from here on. A later chapter changes one only with a reason it states.

- **Headline metric: nDCG@10 with linear gains** (the grades 2, 1 and 0), a log2(i + 1) discount, and an ideal ranking from every judged product. Report precision@10 and MRR beside it. Relevant means exact.
- **Our own metrics are the reference.** The book reports `lib.metrics`, and checks it with scikit-learn's `ndcg_score`, with every judged product in each row.
- **Every comparison shows per-query differences:** mean and median, wins, losses and ties, the largest losses, and judged@10 on the queries that move most.
- **The rule for an established difference:** list the planned comparisons on the test queries first. A difference is established when its permutation test, with 9,999 random sign flips, gives a p-value below 0.05 divided by the number of planned comparisons. Report the paired t-test and a BCa bootstrap interval at the matching level beside it, and say when they disagree. Label comparisons chosen after seeing test results as exploratory, and never call them established. Use train queries for tuning only.
- **Report a gap that isn't established as "no improvement shown",** never as a loss, and never explain it.
- **All resampling uses `rng` with a fixed seed,** through `lib.significance`.
- **Of chapter 1's planned comparisons, semantic retrieval's lead over BM25 is established,** and the other two are not. Semantic retrieval stays the ranker to beat. Every later change is tested in the harness against the ranker it changes, and adopted only if it beats the ranker to beat.
