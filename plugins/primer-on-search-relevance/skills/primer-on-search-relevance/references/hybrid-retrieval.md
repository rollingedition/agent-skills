---
title: "A Primer on Search Relevance"
chapter: "Hybrid retrieval"
chapter_id: hybrid-retrieval
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/hybrid-retrieval
license: CC BY 4.0
attribution: "“Hybrid retrieval,” chapter 7 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/hybrid-retrieval. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Hybrid retrieval

By the end of this chapter you can combine a lexical and a semantic ranking into one, either by adding normalized scores or by reciprocal rank fusion, tune how much each ranking counts on train queries, and decide with a paired test on test queries whether the combination beats the better of its two inputs.

The store, the online furniture and home-goods retailer this book follows as its case study ([chapter 1](#store-data)), has 50 train queries for tuning, 30 test queries for reporting, and two retrievers. [BM25](#rank-with-bm25) matches the query's words; it is the book's baseline, `lib.lexical` at bm25s's defaults, without stemming. [Semantic retrieval](#search-by-meaning) compares the embeddings of the query and of each product, which the open model `Snowflake/snowflake-arctic-embed-m-v1.5` computed in advance. Industry search systems commonly pair the two. One semantic product-search model was built "to complement a lexical search engine in ad hoc product retrieval" ([Nigam et al., 2019](https://arxiv.org/abs/1907.00937)), and a social network's search engine scores documents with "both embedding-based retrieval and term matching based retrieval" ([Huang et al., 2020](https://arxiv.org/abs/2006.11632)). When chapter 1 [fused the two rankings into one](#fuse-with-rrf), the result didn't beat semantic retrieval alone: it scored 0.812 [nDCG@10](#score-one-ranking) on the test queries against 0.830, a gap that [chapter 3's tests](#compare-runs-in-a-harness) don't establish either way. So the store needs to know whether a better mix of the two can beat semantic retrieval, its best ranker so far and so the one to beat.

This chapter finds the queries each retriever wins and checks each retriever alone. It then builds two **blends**, ways to fuse the rankings with a weight that sets how much each one counts, and tunes that weight. Every analysis and every tuning step runs on the train queries. Comparisons there guide the tuning; they aren't evidence. The chapter plans two comparisons on the test queries, made once, at the end: each tuned blend, the [weighted sum](#normalize-scores-before-adding) and [weighted reciprocal rank fusion](#tune-blend-on-train), against semantic retrieval. Following [chapter 3](#compare-runs-in-a-harness), a difference counts as established only when its paired permutation test gives a p-value below 0.05 divided by the number of planned comparisons, here 0.025.

## Find the queries each retriever wins {#queries-each-retriever-wins}

**Hybrid retrieval** combines the rankings of a lexical and a semantic retriever into one ranking. Combining rankings is called **fusion**. Fusion can only help if the two retrievers fail on different queries: if both put poor products first for the same query, no mix of their rankings fixes it. Published studies find that they do. Embeddings miss rare entities and selective keywords that BM25 matches ([chapter 6](#codes-carry-no-weight)), and on a dataset built to test the limits of one embedding per text, BM25 finds what embeddings miss but loses most of its score when words are replaced with synonyms ([chapter 1](#search-by-meaning)). So the first check is per query, not on average.

Score both of the store's retrievers by [nDCG@10](#score-one-ranking) on every [train query](#store-data), keeping each one's top 100 products.

Example `bm25-semantic-wins-by-query` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
bm25_scores, semantic_scores = evaluate(bm25, judgments)["ndcg@10"], evaluate(semantic, judgments)["ndcg@10"]

print("train queries:", len(queries))
print(f"bm25 ndcg@10: {bm25_scores.mean():.3f}")
print(f"semantic ndcg@10: {semantic_scores.mean():.3f}")
lead = (bm25_scores - semantic_scores).round(3)              # per train query; above 0 means BM25 wins
print("bm25 better:", (lead > 0).sum())
print("semantic better:", (lead < 0).sum())
print("tied:", (lead == 0).sum())
print(f"better of the two, chosen per query: {np.maximum(bm25_scores, semantic_scores).mean():.3f}")
has_digit = queries["query"].str.contains(r"\d")
print("queries with a digit:", has_digit.sum())
print("queries with a digit, bm25 better:", (lead[has_digit] > 0).sum())
print()
print("queries where bm25 leads by 0.1 or more:", (lead >= 0.1).sum())
print(queries.loc[lead[lead >= 0.1].index, "query"].to_string())
```

Output:

```text
train queries: 50
bm25 ndcg@10: 0.695
semantic ndcg@10: 0.772
bm25 better: 15
semantic better: 31
tied: 4
better of the two, chosen per query: 0.802
queries with a digit: 5
queries with a digit, bm25 better: 1

queries where bm25 leads by 0.1 or more: 6
query_id
44     chrome shower head and valve
146          laundry vanity cabinet
277             barstool patio sets
313                    malachi sled
359                  french molding
432            butcher block island
```

On average, semantic retrieval scores 0.772 and BM25 0.695. Per query, semantic retrieval is better on 31 queries, BM25 on 15, and 4 are tied. If you could choose the better of the two rankings for each query, the mean would be 0.802. That isn't a ceiling for fusion, which mixes the lists rather than choosing one, but it measures what the two rankings' differences could be worth.

Next, see whether the two lists hold different products, and what share of each query's **exact** products, the ones the judges graded as fully matching it, each list finds:

Example `overlap-and-union-recall` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import recall_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)

shared = [len(set(bm25[query_id][:10]) & set(semantic[query_id][:10])) for query_id in queries.index]
print(f"products in both top 10s, mean: {np.mean(shared):.1f}")


def share_retrieved(run):
    """The share of each query's exact products that the run's list holds, averaged over queries."""
    shares = [recall_at_k(ranking, judgments[query_id], k=len(ranking)) for query_id, ranking in run.items()]
    return np.mean(shares)


for depth in [100, 20]:
    lists = {"bm25": {query_id: ranking[:depth] for query_id, ranking in bm25.items()},
             "semantic": {query_id: ranking[:depth] for query_id, ranking in semantic.items()}}
    lists["union"] = {query_id: list(dict.fromkeys(lists["bm25"][query_id] + lists["semantic"][query_id]))
                      for query_id in queries.index}
    for name, run in lists.items():
        print(f"{name} top {depth}, share of exact products retrieved: {share_retrieved(run):.3f}")
```

Output:

```text
products in both top 10s, mean: 3.7
bm25 top 100, share of exact products retrieved: 0.672
semantic top 100, share of exact products retrieved: 0.759
union top 100, share of exact products retrieved: 0.810
bm25 top 20, share of exact products retrieved: 0.297
semantic top 20, share of exact products retrieved: 0.353
union top 20, share of exact products retrieved: 0.445
```

The two top 10s share 3.7 products on average. BM25's top 100 holds 0.672 of each query's exact products, semantic retrieval's 0.759, and the union of the two lists 0.810. Fusion can't rank a product that neither list holds, so how deep each list goes caps how many exact products fusion can reach: cut each list to its top 20, and the union holds 0.445.

Two train queries show the kinds of failure:

Example `two-queries-two-winners` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}
products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=10)
semantic = SemanticSearch().run(queries, k=10)
text = product_text(products)
print("products containing 7qt:", text.str.contains(r"\b7qt\b", case=False).sum())
print("products containing 7 qt:", text.str.contains(r"\b7 qt\b", case=False).sum())

for query_id in [432, 62]:                                   # butcher block island, 7qt slow cooker
    query = queries.at[query_id, "query"]
    for name, run in [("bm25", bm25), ("semantic", semantic)]:
        grades = [judgments[query_id].get(product_id) for product_id in run[query_id]]
        print()
        print(f"exact in {name} top 10 for {query}: {grades.count(2)}")
        for product_id, grade in list(zip(run[query_id], grades))[:5]:
            print(f"  {LABELS.get(grade, 'unjudged'):<10}  {products.at[product_id, 'name'][:55]}")
```

Output:

```text
products containing 7qt: 0
products containing 7 qt: 9

exact in bm25 top 10 for butcher block island: 9
  exact       carol kitchen island with butcher block top
  exact       brunton kitchen island with butcher block top
  partial     brunton kitchen cart butcher block top
  exact       janigian kitchen island with butcher block
  exact       avelar kitchen island with butcher block

exact in semantic top 10 for butcher block island: 3
  partial     boosblock® prep table with butcher block top
  partial     boosblock® butcher block
  partial     prep table
  partial     pro chef kitchen cart with butcher block top
  exact       brunton kitchen island with butcher block top

exact in bm25 top 10 for 7qt slow cooker: 1
  partial     cuisinart 6.5 quart programmable slow cooker
  partial     midea 6.5 qt . slow cooker
  partial     delonghi cks1660d livenza programmable 6 qt . slow cook
  partial     nesco 1.5 qt . analog slow cooker
  partial     360 cookware gourmet slow cooker

exact in semantic top 10 for 7qt slow cooker: 7
  exact       7-qt . stay or go slow cooker
  exact       crock-pot 7 qt . slow cooker
  exact       zing 7 qt . digital slow cooker
  exact       black + decker 7 qt . digital slow cooker
  exact       crock-pot 7 qt . slow cooker
```

For `butcher block island`, BM25's top 10 holds 9 exact products and semantic retrieval's 3. BM25 rewards products whose text contains all three words: kitchen islands with butcher-block tops. Semantic retrieval ranks prep tables and carts with butcher-block tops near the top too, and the judges graded those partial: the right material, but not the island the query asks for. For `7qt slow cooker` it's the other way round: 1 against 7. The catalog has 0 products whose text contains `7qt` and 9 that contain `7 qt`. So BM25 matches only `slow cooker` and ranks cookers of every size, while semantic retrieval puts 7-quart cookers first.

Those are single queries: they show a kind of failure, not how often it happens. [The per-query count](#bm25-semantic-wins-by-query) also lists the 6 train queries where BM25 leads by 0.1 nDCG@10 or more. Most name a specific kind of product in two or more words that all have to match, and one, `malachi sled`, names a product line. [Chapter 1](#search-by-meaning) found BM25 ahead on 2 of the 2 test queries that give a size in inches, yet of the 5 train queries that contain a digit, BM25 wins 1.

**Working rule:** Before you fuse, count per query where each retriever wins on your train queries, and check how many relevant products the union of their lists holds that the better one misses. Consider fusing when each retriever wins a real share of queries and the union holds more relevant products than either list. That is necessary, not sufficient: next, [check each retriever alone](#check-each-retriever-before-fusing), and [test the tuned blend on held-out queries](#report-blends-on-test) before you adopt it.

## Check each retriever before you fuse {#check-each-retriever-before-fusing}

Knowing [where each retriever wins](#queries-each-retriever-wins) isn't enough, because fusion gives each input a say in the final ranking, a weak input included. A study of hybrid search over 11 datasets reports "A “weakest link” phenomenon, where a weak path can substantially degrade overall accuracy, highlighting the need for path-wise quality assessment before fusion" ([Wang et al., PVLDB 2026](https://arxiv.org/abs/2508.01405)). So compare the retrievers' mean nDCG@10, with [judged@10](#unjudged-results), the share of the top 10 that has a judgment, beside it. Then compare them query by query with a **paired test**, which asks how likely a mean difference this large would be if the two were equally good. The book's test is the [permutation test](#permutation-test-on-queries), with the [paired t-test](#paired-t-test-on-queries) beside it. On train queries, these checks shape how you combine the retrievers; they aren't evidence about the store.

In the store, fuse BM25 and semantic retrieval as [chapter 1](#fuse-with-rrf) did, with reciprocal rank fusion (RRF): each product scores 1 / (60 + its rank) in each ranking, summed over the two, so each ranking gets an equal vote. Then split the train queries by which retriever wins, and compare the fused ranking with semantic retrieval alone:

Example `fusion-gain-by-winning-retriever` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])           # k = 60 and equal votes, as in chapter 1
bm25_scores, semantic_scores, hybrid_scores = (evaluate(run, judgments) for run in (bm25, semantic, hybrid))

print(f"bm25 judged@10: {bm25_scores['judged@10'].mean():.3f}")
print(f"semantic judged@10: {semantic_scores['judged@10'].mean():.3f}")
for name, after, before in [("semantic minus bm25", semantic_scores, bm25_scores),
                            ("hybrid minus semantic", hybrid_scores, semantic_scores)]:
    result = compare(after["ndcg@10"], before["ndcg@10"])                    # paired by query
    print(f"{name}, mean ndcg@10: {result['mean difference']:.3f}")
    print(f"{name}, permutation p: {result['permutation p']:.3f}")
    print(f"{name}, t-test p: {result['t-test p']:.3f}")
print()

change = (hybrid_scores["ndcg@10"] - semantic_scores["ndcg@10"]).round(3)   # fusion against semantic alone
lead = (bm25_scores["ndcg@10"] - semantic_scores["ndcg@10"]).round(3)       # above 0 means BM25 wins
for name, group in [("bm25 wins", lead > 0), ("semantic wins", lead < 0)]:
    print(f"{name}, queries: {group.sum()}")
    print(f"{name}, fusion better than semantic: {(change[group] > 0).sum()}")
    print(f"{name}, fusion worse than semantic: {(change[group] < 0).sum()}")
    print(f"{name}, mean change in ndcg@10: {change[group].mean():.3f}")
```

Output:

```text
bm25 judged@10: 0.930
semantic judged@10: 0.964
semantic minus bm25, mean ndcg@10: 0.077
semantic minus bm25, permutation p: 0.003
semantic minus bm25, t-test p: 0.004
hybrid minus semantic, mean ndcg@10: 0.002
hybrid minus semantic, permutation p: 0.863
hybrid minus semantic, t-test p: 0.872

bm25 wins, queries: 15
bm25 wins, fusion better than semantic: 12
bm25 wins, fusion worse than semantic: 2
bm25 wins, mean change in ndcg@10: 0.101
semantic wins, queries: 31
semantic wins, fusion better than semantic: 5
semantic wins, fusion worse than semantic: 25
semantic wins, mean change in ndcg@10: -0.045
```

BM25's judged@10 is 0.930 against 0.964 for semantic retrieval, so BM25's top 10s hold a few more products nobody judged, and [chapter 2](#unjudged-results) shows how those can lower a score. Semantic retrieval leads by 0.077 nDCG@10, with a permutation p-value of 0.003 and a t-test p-value of 0.004. On the test queries, [chapter 3](#compare-runs-in-a-harness) establishes the same lead. So the store has a strong retriever and a weaker one.

On the 15 train queries where BM25 wins, the fused ranking beats semantic retrieval on 12 and loses on 2, with a mean change of 0.101. On the 31 where semantic retrieval wins, the fused ranking is worse on 25 and better on 5, with a mean change of -0.045. The split is built to show this pattern: grouping queries by the winner means almost any mix of the two helps where BM25 wins and hurts where it loses. What matters is the net change over all the train queries. The fused ranking differs from semantic retrieval by 0.002 on average, with a permutation p-value of 0.863: on these queries, equal votes gain nothing measurable.

The split uses the judgments to decide which retriever wins, so it is a diagnosis: you can't use it to choose a retriever for a live query, which has no judgments.

**Working rule:** Check each retriever alone on train queries, with judged@10 and a paired test, before you fuse. When one is weaker and wins fewer queries, don't give it an equal vote: weight it and [tune the weight](#tune-blend-on-train), or leave it out. Equal votes suit two retrievers of about the same quality.

## Normalize scores before you add them {#normalize-scores-before-adding}

The most direct way to give the weaker retriever, BM25 in the store, [a smaller say](#check-each-retriever-before-fusing) is to add the two retrievers' scores with a weight: α times the semantic score plus (1 − α) times the BM25 score. A sum whose weights add up to 1 is a **convex combination**, or weighted sum. It only works if the scores are on comparable scales, and here they aren't: a [BM25](#rank-with-bm25) score has no fixed range and grows with the number and rarity of the query's words, while semantic retrieval's score, a cosine similarity, lies between −1 and 1. **Score normalization** rescales each retriever's scores for each query before adding them. Per-query min-max scaling maps the lowest score among the products ranked for the query to 0 and the highest to 1. A study of fusion functions calls it "the de facto method in the literature" and tests two alternatives ([Bruch et al., 2023](https://arxiv.org/abs/2210.11934)). **Theoretical min-max** uses each score's lowest possible value instead of the lowest one seen: 0 for BM25 and −1 for cosine. The **z-score** subtracts the mean and divides by the standard deviation. The examples' shared module `lib/blend.py` writes each in a few lines.

```text
min-max(s) = (s − lowest score among the query's candidates) / (highest − lowest)
blend      = α · min-max(similarity) + (1 − α) · min-max(BM25)
```

A sum needs both scores for every product it ranks. The **candidate set** for a query is the union of both retrievers' top 100, and `lib.blend.candidates` looks up both scores for every product in it: the BM25 score, which is 0 when the product shares no word with the query, and the cosine similarity.

Start with the store's raw scores, added with α = 0.5 on the train queries. Then do the same after min-max scaling, written out in the example and checked against `lib.blend.weighted_sum`:

Example `raw-scores-versus-min-max` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.blend import candidates, weighted_sum
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
lexical, semantic = LexicalSearch(products), SemanticSearch()
tables = candidates(lexical, semantic, queries)              # both scores for each query's candidates

table = tables[36]                                           # laundry basket with wheels
print("candidates for laundry basket with wheels:", len(table))
print(f"bm25 range: {table['bm25'].min():.3f} to {table['bm25'].max():.3f}")
print(f"similarity range: {table['similarity'].min():.3f} to {table['similarity'].max():.3f}")


def min_max(scores):
    return (scores - scores.min()) / (scores.max() - scores.min())


def blend(normalize, alpha=0.5):
    run = {}
    for query_id, table in tables.items():
        score = alpha * normalize(table["similarity"]) + (1 - alpha) * normalize(table["bm25"])
        run[query_id] = list(score.sort_values(ascending=False, kind="stable").index[:100])
    return run


top_10s = {"bm25": lexical.run(queries, k=10), "semantic": semantic.run(queries, k=10)}
per_query = {}
for name, normalize in [("raw", lambda scores: scores), ("min-max", min_max)]:
    run = blend(normalize)
    per_query[name] = evaluate(run, judgments)["ndcg@10"]
    print(f"{name} sum ndcg@10: {per_query[name].mean():.3f}")
    for other, top in top_10s.items():
        shared = [len(set(run[query_id][:10]) & set(top[query_id])) for query_id in queries.index]
        print(f"{name} sum, products shared with the {other} top 10: {sum(shared) / len(shared):.1f}")
by_hand, library = blend(min_max), weighted_sum(tables, 0.5)
matches = sum(by_hand[query_id] == library[query_id] for query_id in tables)
print(f"train queries ranked as lib.blend.weighted_sum ranks them: {matches} of {len(tables)}")
p_value = compare(per_query["min-max"], per_query["raw"])["permutation p"]          # a tuning check on train
print("min-max minus raw, permutation p:", "below 0.001" if p_value < 0.001 else f"{p_value:.3f}")
```

Output:

```text
candidates for laundry basket with wheels: 125
bm25 range: 2.059 to 8.229
similarity range: 0.336 to 0.597
raw sum ndcg@10: 0.706
raw sum, products shared with the bm25 top 10: 9.6
raw sum, products shared with the semantic top 10: 3.9
min-max sum ndcg@10: 0.771
min-max sum, products shared with the bm25 top 10: 6.5
min-max sum, products shared with the semantic top 10: 6.2
train queries ranked as lib.blend.weighted_sum ranks them: 50 of 50
min-max minus raw, permutation p: below 0.001
```

For `laundry basket with wheels`, the 125 candidates have BM25 scores from 2.059 to 8.229 and similarities from 0.336 to 0.597. BM25's spread is many times larger, so it decides the order of the raw sum. Over the train queries, the raw sum's top 10 shares 9.6 products with BM25's top 10 on average and 3.9 with semantic retrieval's. Its nDCG@10 of 0.706 is close to [BM25's 0.695](#queries-each-retriever-wins). The weight says "half each", but the ranking is mostly BM25's.

After min-max scaling, the top 10 shares 6.5 products with BM25's and 6.2 with semantic retrieval's, and nDCG@10 is 0.771, with a permutation p-value against the raw sum below 0.001. Both retrievers now have a say. The by-hand version ranks 50 of 50 train queries exactly as `lib.blend.weighted_sum` does.

Raw scores can work with a tuned weight. The authors of DPR, an embedding-based retriever, ranked candidates by BM25 plus 1.1 times DPR's similarity, with the 1.1 chosen on a development set ([Karpukhin et al., 2020](https://arxiv.org/abs/2004.04906)). Normalization gives α the same meaning for every query; without it, BM25's share of the say changes with its range from query to query. Min-max isn't an absolute scale, though. It is relative to the query's candidates, so the best candidate always gets 1, however poor it is.

**Working rule:** Never add raw BM25 and cosine scores with a guessed weight. We recommend per-query min-max as the default, because it needs no knowledge of either scoring function. Use theoretical min-max when you know each score's lowest possible value and want a floor that doesn't move with the candidates. In either case, tune α on train queries.

## Test reciprocal rank fusion's settings on train queries {#rrf-settings-on-train}

Ranks, unlike [scores](#normalize-scores-before-adding), share one scale, so fusing by rank needs no normalization. **Reciprocal rank fusion** (RRF) scores each product by adding, over the rankings that contain it, 1 divided by the sum of a constant k and its rank, as [chapter 1's formula](#fuse-with-rrf) writes it ([Cormack et al., 2009](http://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf)). The price is information: "because RRF is a function of ranks, it disregards the distribution of scores and, as such, discards useful information" ([Bruch et al., 2023](https://arxiv.org/abs/2210.11934)). A product a hair behind the leader and one far behind it get scores set by their ranks alone.

The constant k sets how much the top ranks dominate. RRF's authors fixed k = 60 in a pilot study, and their tests "indicated that k = 60 was near-optimal, but that the choice was not critical". Those pilots fused "30 configurations of Wumpus Search", one search engine, on collections from TREC, a series of shared retrieval evaluations (Cormack et al., 2009). Bruch et al. fused one lexical and one semantic retriever, gave each its own constant, η, and found the results sensitive to the balance between the two constants, which acts as a weight: "where the semantic model already performs strongly, for example, discounting the lexical system by increasing η_Lex leads to better performance". One k shared by both rankings, as here, sets no balance between them.

The depth of each list matters too. A product in one retriever's top 20 but not in the other's earns nothing from the second ranking, although it has a rank there, only a low one. As Bruch et al. put it, "ranks cannot be computed exactly unless the entire collection D is ranked by retrieval system o for every query." In the store, the union of two top-20 lists holds far fewer exact products than the union of two top-100 lists, as [the count of exact products in each list](#queries-each-retriever-wins) shows.

Try six values of k on the store's train queries, fusing BM25 and semantic retrieval from lists 100 deep. One check is planned before running: does the best k on train beat the default, k = 60?

Example `rrf-k-on-train` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)

for k in [1, 60]:
    print(f"rank 1 over rank 10 at k={k}: {(1 / (k + 1)) / (1 / (k + 10)):.3f}")
scores = {k: evaluate(reciprocal_rank_fusion([bm25, semantic], k=k), judgments)["ndcg@10"]
          for k in [1, 10, 30, 60, 100, 300]}
for k, per_query in scores.items():
    print(f"k={k} ndcg@10: {per_query.mean():.3f}")

best = max(scores, key=lambda k: scores[k].mean())           # ties go to the smaller k
print("best k on train:", best)
result = compare(scores[best], scores[60])                     # the planned check: best k against the default
print(f"best k minus k=60: {result['mean difference']:.3f}")
print(f"best k minus k=60, permutation p: {result['permutation p']:.3f}")
print(f"best k minus k=60, t-test p: {result['t-test p']:.3f}")
print(f"best k minus k=60, 95% interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
print(f"best k minus k=60, wins, losses, ties: {result['wins']}, {result['losses']}, {result['ties']}")
```

Output:

```text
rank 1 over rank 10 at k=1: 5.500
rank 1 over rank 10 at k=60: 1.148
k=1 ndcg@10: 0.753
k=10 ndcg@10: 0.770
k=30 ndcg@10: 0.771
k=60 ndcg@10: 0.774
k=100 ndcg@10: 0.778
k=300 ndcg@10: 0.777
best k on train: 100
best k minus k=60: 0.004
best k minus k=60, permutation p: 0.093
best k minus k=60, t-test p: 0.103
best k minus k=60, 95% interval: 0.001 to 0.011
best k minus k=60, wins, losses, ties: 6, 3, 41
```

At k = 1, rank 1 earns 5.500 times what rank 10 earns. At k = 60, it earns 1.148 times as much, so a product near the top of both lists beats one at the top of only one. From k = 1 to k = 300, the six settings score 0.753, 0.770, 0.771, 0.774, 0.778 and 0.777. The best, k = 100, leads k = 60 by 0.004, with a permutation p-value of 0.093 and a t-test p-value of 0.103. Its 95% bootstrap interval, 0.001 to 0.011, excludes 0, so it disagrees with both tests. The two settings' rankings differ on only a handful of queries (wins, losses and ties: 6, 3, 41), and the book takes its verdict from the permutation test, which can't tell the gain from chance at 0.05. Which k is best is fragile too: [with BM25's tied products listed the other way](#tuned-weight-stability), k = 300 wins instead. This fits Cormack et al.'s finding that the choice of k is not critical.

**Working rule:** Keep k = 60 as the default, and fuse lists at least 100 deep, because a deeper list can only add candidates. Move off k = 60 only when the best k on train beats it by a margin the permutation test can tell from chance, with p below 0.05. When one retriever is [the stronger one](#check-each-retriever-before-fusing), as in the store, k isn't the setting to change: RRF's equal vote is. Give the rankings weights and [tune them](#tune-blend-on-train).

## Tune the blend's weight on train queries {#tune-blend-on-train}

The chapter's two [blends](#hybrid-retrieval) each take one weight, α, the share given to semantic retrieval. In the [weighted sum](#normalize-scores-before-adding), α multiplies the normalized similarity and 1 − α the normalized BM25 score. In **weighted RRF**, a product scores (1 − α) / (k + its BM25 rank) plus α / (k + its semantic rank). For both, α = 0 is BM25 alone and α = 1 is semantic retrieval alone. For RRF, α = 0.5 is [chapter 1's unweighted fusion](#fuse-with-rrf) with every score halved. Here is the arithmetic for the top product of one train query, with an illustrative α = 0.75:

Example `weighted-rrf-one-product` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.blend import weighted_rrf
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries

alpha, k = 0.75, 60                                          # an illustrative weight; tuning picks one on train
products, queries = load_products(), load_queries("train")
bm25 = LexicalSearch(products).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
query_id = 36                                                # laundry basket with wheels


def part(ranking, weight, product_id):
    """weight / (k + rank) from one ranking, or 0 when the product isn't in it."""
    return weight / (k + ranking.index(product_id) + 1) if product_id in ranking else 0.0


candidates = dict.fromkeys(bm25[query_id] + semantic[query_id])   # the union, in the order first seen
score = {product_id: part(bm25[query_id], 1 - alpha, product_id) + part(semantic[query_id], alpha, product_id)
         for product_id in candidates}
ranking = sorted(score, key=lambda product_id: (-score[product_id], product_id))   # ties by product_id
first = ranking[0]
print("first product:", products.at[first, "name"])
print("its bm25 rank:", bm25[query_id].index(first) + 1)
print("its semantic rank:", semantic[query_id].index(first) + 1)
print(f"its weighted rrf score: {score[first]:.5f}")
library = weighted_rrf(bm25, semantic, alpha)[query_id]          # the top 100
matches = sum(mine == theirs for mine, theirs in zip(ranking, library))
print(f"places that match lib.blend.weighted_rrf: {matches} of {len(library)}")
```

Output:

```text
first product: laundry sorter basket on wheels
its bm25 rank: 1
its semantic rank: 2
its weighted rrf score: 0.01620
places that match lib.blend.weighted_rrf: 100 of 100
```

For `laundry basket with wheels`, laundry sorter basket on wheels sits at rank 1 in BM25's ranking and rank 2 in semantic retrieval's, so it scores 0.25 / (60 + 1) + 0.75 / (60 + 2) = 0.01620. The example scores every candidate this way, and its ranking matches `lib.blend.weighted_rrf` in 100 of 100 places.

Tuning means trying a grid of α values on train queries and keeping the one with the best mean nDCG@10. Bruch et al. (2023) report three findings about tuning a [convex combination](#normalize-scores-before-adding), CC: "the learning of a CC fusion is generally agnostic to the choice of score normalization; that CC outperforms RRF in in-domain and out-of-domain settings; and finally, that CC is sample efficient." Sample efficient meant that α converged "with less than 5% of the training data", a fraction of training sets much larger than the store's.

In the store, tune α over 0, 0.1, … 1 for the weighted sum under each of [the three normalizations](#normalize-scores-before-adding), and for weighted RRF with k = 60. Then test, as tuning checks, each normalization against min-max, and the two blends that go to the test queries against semantic retrieval:

Example `tune-blend-weights-on-train` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.blend import ALPHAS, NORMALIZATIONS, best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
lexical, semantic = LexicalSearch(products), SemanticSearch()
tables = candidates(lexical, semantic, queries)
bm25, semantic_run = lexical.run(queries, k=100), semantic.run(queries, k=100)

per_query = {}                                               # nDCG@10 per query (rows) and alpha (columns)
for name in NORMALIZATIONS:
    per_query[name] = scores_by_alpha(lambda alpha: weighted_sum(tables, alpha, name), judgments)
per_query["weighted rrf"] = scores_by_alpha(lambda alpha: weighted_rrf(bm25, semantic_run, alpha), judgments)
semantic_alone = per_query["min-max"][1.0]                   # alpha = 1 is semantic retrieval in either blend
print("alphas tried:", len(ALPHAS))
print("min-max ndcg@10 for alpha 0 to 1:", " ".join(f"{mean:.3f}" for mean in per_query["min-max"].mean()))
print(f"semantic alone ndcg@10: {semantic_alone.mean():.3f}")
print(f"unweighted rrf (alpha 0.5) ndcg@10: {per_query['weighted rrf'][0.5].mean():.3f}")

best = {name: frame[best_alpha(frame)] for name, frame in per_query.items()}
for name, frame in per_query.items():
    print(f"{name} best alpha: {best_alpha(frame)}")
    print(f"{name} best ndcg@10: {best[name].mean():.3f}")
for name in ["theoretical min-max", "z-score", "weighted rrf"]:          # each tuned, against tuned min-max
    print(f"{name} against min-max, permutation p: {compare(best[name], best['min-max'])['permutation p']:.3f}")
for name in ["min-max", "weighted rrf"]:                                 # the two blends that go to test
    gain = compare(best[name], semantic_alone)
    print(f"{name} gain over semantic: {gain['mean difference']:.3f}")
    print(f"{name} gain over semantic, permutation p: {gain['permutation p']:.3f}")
    print(f"{name} gain over semantic, t-test p: {gain['t-test p']:.3f}")
```

Output:

```text
alphas tried: 11
min-max ndcg@10 for alpha 0 to 1: 0.695 0.709 0.736 0.746 0.758 0.771 0.781 0.784 0.777 0.778 0.772
semantic alone ndcg@10: 0.772
unweighted rrf (alpha 0.5) ndcg@10: 0.774
min-max best alpha: 0.7
min-max best ndcg@10: 0.784
theoretical min-max best alpha: 0.9
theoretical min-max best ndcg@10: 0.789
z-score best alpha: 0.7
z-score best ndcg@10: 0.787
weighted rrf best alpha: 0.6
weighted rrf best ndcg@10: 0.787
theoretical min-max against min-max, permutation p: 0.164
z-score against min-max, permutation p: 0.349
weighted rrf against min-max, permutation p: 0.776
min-max gain over semantic: 0.013
min-max gain over semantic, permutation p: 0.177
min-max gain over semantic, t-test p: 0.161
weighted rrf gain over semantic: 0.015
weighted rrf gain over semantic, permutation p: 0.215
weighted rrf gain over semantic, t-test p: 0.205
```

The output's second line traces the min-max blend from α = 0 to α = 1. It peaks at α = 0.7 with 0.784, against semantic retrieval's 0.772. Theoretical min-max peaks at α = 0.9 with 0.789, and the z-score at α = 0.7 with 0.787. Against tuned min-max, their permutation p-values are 0.164 and 0.349: at 0.05, the test on train queries can't tell either normalization from min-max, which fits Bruch et al.'s finding that the normalization hardly matters. Weighted RRF peaks at α = 0.6 with 0.787, and against tuned min-max its p-value is 0.776. Bruch et al.'s second finding, that the weighted sum beats RRF, doesn't show here, and these queries can't settle it.

Every tuned blend scores at least as well as semantic retrieval on the train queries, and that is guaranteed: α = 1 is in the grid. Yet even on the queries that chose them, the permutation test can't tell either blend's gain from chance at 0.05. The weighted sum gains 0.013, with a permutation p-value of 0.177, and weighted RRF gains 0.015, with 0.215. Each gain is also the best of 11 tries on the same queries, which flatters it further.

**Working rule:** Tune one weight on train queries over a coarse grid, and keep the normalization at min-max unless another one beats it by a margin the test on train queries can tell from chance, with p below 0.05. Treat the train gain over the best single retriever as optimistic, and expect it to shrink on test queries, a rule of thumb for any setting picked as the best of several. Before you trust the setting, [check that it's stable](#tuned-weight-stability), then [report it on test queries](#report-blends-on-test).

## Check that the tuned weight is stable {#tuned-weight-stability}

The [tuned weights](#tune-blend-on-train) come from a few dozen queries, so they can depend on which queries you happened to have. The **bootstrap** shows how much: draw as many queries from the train set as it holds, with replacement, so some appear twice and others not at all, tune α on that sample, and repeat many times. If the chosen α jumps around, the tuned value reflects the sample more than the store. [Chapter 3](#report-the-size-of-a-gap) uses the same resampling to put intervals around scores.

In the store, resample the train queries 1000 times with a fixed seed, and count how often each α wins for both tuned blends, the weighted sum of min-max scores and weighted RRF, on the same resamples:

Example `blend-weight-bootstrap` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np
import pandas as pd

from lib.blend import best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")
lexical, semantic = LexicalSearch(products), SemanticSearch()
tables = candidates(lexical, semantic, queries)
bm25, semantic_run = lexical.run(queries, k=100), semantic.run(queries, k=100)
blends = {"weighted sum": scores_by_alpha(lambda alpha: weighted_sum(tables, alpha), judgments),
          "weighted rrf": scores_by_alpha(lambda alpha: weighted_rrf(bm25, semantic_run, alpha), judgments)}

resamples = 1000
print("resamples:", resamples)
rng = np.random.default_rng(2026)
draws = [rng.integers(0, len(queries), len(queries)) for _ in range(resamples)]   # the same draws for both
for name, per_query in blends.items():                       # per_query: train queries x alphas
    print(f"{name} alpha tuned on all train queries: {best_alpha(per_query)}")
    chosen = pd.Series([per_query.iloc[draw].mean().idxmax() for draw in draws])  # best alpha per resample
    for alpha, count in chosen.value_counts().sort_index().items():
        print(f"{name} resamples choosing alpha {alpha}: {count}")
```

Output:

```text
resamples: 1000
weighted sum alpha tuned on all train queries: 0.7
weighted sum resamples choosing alpha 0.5: 13
weighted sum resamples choosing alpha 0.6: 171
weighted sum resamples choosing alpha 0.7: 686
weighted sum resamples choosing alpha 0.8: 11
weighted sum resamples choosing alpha 0.9: 74
weighted sum resamples choosing alpha 1.0: 45
weighted rrf alpha tuned on all train queries: 0.6
weighted rrf resamples choosing alpha 0.5: 2
weighted rrf resamples choosing alpha 0.6: 513
weighted rrf resamples choosing alpha 0.7: 76
weighted rrf resamples choosing alpha 0.8: 365
weighted rrf resamples choosing alpha 0.9: 26
weighted rrf resamples choosing alpha 1.0: 18
```

For the weighted sum, tuned at α = 0.7 on all the train queries, α = 0.7 wins 686 resamples and α = 0.6 wins 171. Semantic retrieval alone, α = 1, wins 45. Weighted RRF, tuned at α = 0.6, is less settled: α = 0.6 wins 513 resamples, α = 0.8 wins 365 and α = 0.7 wins 76. Both weights stay on the side of the grid that favours semantic retrieval, apart from equal weight, α = 0.5, which wins 13 resamples for the weighted sum and 2 for weighted RRF. RRF's weight moves between 0.6 and 0.8.

Resampling isn't the only check. Products with equal BM25 scores have to be listed in some order, and `lib.lexical` lists them by `product_id`, an order that carries no information. Descending `product_id` order carries none either. The weighted sum gives tied products the same BM25 term, so their order hardly matters to it, but RRF gives them consecutive ranks, and so different scores. List BM25's ties by descending `product_id`, and tune the [best RRF k](#rrf-settings-on-train) and both weights again on the train queries:

Example `tuning-with-ties-reversed` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.blend import best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels


class TiesReversed(LexicalSearch):
    """BM25 with equal scores in descending product_id order, an order as arbitrary as ascending."""

    def search(self, query, k=100):
        scores = super().search(query, k=len(self.ids))           # every match, so the cut at k can move too
        order = np.lexsort((-scores.index.to_numpy(), -scores.to_numpy()))
        return scores.iloc[order[:k]]


products, queries, judgments = load_products(), load_queries("train"), qrels("train")
semantic = SemanticSearch()
semantic_run = semantic.run(queries, k=100)
for ties, lexical in [("ties by product_id", LexicalSearch(products)), ("ties reversed", TiesReversed(products))]:
    bm25 = lexical.run(queries, k=100)
    by_k = {k: evaluate(reciprocal_rank_fusion([bm25, semantic_run], k=k), judgments)["ndcg@10"].mean()
            for k in [1, 10, 30, 60, 100, 300]}
    print(f"best rrf k, {ties}: {max(by_k, key=by_k.get)}")                # ties go to the smaller k
    rrf = scores_by_alpha(lambda alpha: weighted_rrf(bm25, semantic_run, alpha), judgments)
    print(f"weighted rrf alpha, {ties}: {best_alpha(rrf)}")
    tables = candidates(lexical, semantic, queries)
    total = scores_by_alpha(lambda alpha: weighted_sum(tables, alpha), judgments)
    print(f"weighted sum alpha, {ties}: {best_alpha(total)}")
```

Output:

```text
best rrf k, ties by product_id: 100
weighted rrf alpha, ties by product_id: 0.6
weighted sum alpha, ties by product_id: 0.7
best rrf k, ties reversed: 300
weighted rrf alpha, ties reversed: 0.8
weighted sum alpha, ties reversed: 0.7
```

With the ties reversed, the best k is 300 instead of 100, and weighted RRF's α is 0.8 instead of 0.6. The weighted sum keeps α = 0.7. When an order that carries no information changes a setting, the train queries can't tell the settings apart: RRF's k and weight are fragile, and the weighted sum's weight isn't. The store has no more train queries to settle weighted RRF's weight, and its test comparison was planned with the weight tuned with ties by `product_id`, so α = 0.6 goes to test.

Stability says the train queries agree on a weight, not that the weight improves search on queries it wasn't tuned on: the resamples reuse the same train queries, so they share whatever those queries have in common.

**Working rule:** Bootstrap the train queries and tune on each sample, then tune once more with ties listed in another order that carries no information. If the chosen weight scatters across the grid, use a coarser grid or more train queries, or prefer the simpler setting. If the tie order alone moves it, say so wherever you report it. If it holds steady under both checks, take it to the test queries.

## Report the tuned blends on test queries {#report-blends-on-test}

Only held-out queries show whether a tuned setting helps beyond the queries that chose it. Run each tuned blend once on the test queries, and compare it with semantic retrieval, the best single retriever, query by query, using the harness that [chapter 3](#compare-runs-in-a-harness) builds. The chapter fixed these two comparisons before looking. With the Bonferroni correction, a difference is established when its permutation p-value is below 0.025. The t-test and a bootstrap interval at the matching confidence level, 0.975, stand beside it.

On the store's train queries, the [tuned blends](#tune-blend-on-train) gained 0.013 and 0.015 over semantic retrieval, neither of them a gain the permutation test could tell from chance. Before you read the output, predict: on the test queries, will the weighted sum with α = 0.7 and weighted RRF with α = 0.6 score above semantic retrieval, level with it, or below it?

Example `tuned-blends-on-test` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.blend import best_alpha, candidates, scores_by_alpha, weighted_rrf, weighted_sum
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

lexical, semantic = LexicalSearch(load_products()), SemanticSearch()


def blends(queries):
    tables, bm25, semantic_run = candidates(lexical, semantic, queries), lexical.run(queries), semantic.run(queries)
    return {"weighted sum": lambda alpha: weighted_sum(tables, alpha),          # each blend's run at a given alpha
            "weighted rrf": lambda alpha: weighted_rrf(bm25, semantic_run, alpha)}


train, test = blends(load_queries("train")), blends(load_queries("test"))
threshold = 0.05 / len(test)                                 # two planned comparisons, Bonferroni-corrected
semantic_scores = evaluate(semantic.run(load_queries("test")), qrels("test"))
print("test queries:", len(semantic_scores))
print(f"semantic ndcg@10: {semantic_scores['ndcg@10'].mean():.3f}")
unweighted = evaluate(test["weighted rrf"](0.5), qrels("test"))          # alpha 0.5 is chapter 1's fusion
print(f"unweighted rrf ndcg@10: {unweighted['ndcg@10'].mean():.3f}")
print(f"p-value threshold for each comparison: {threshold:.3f}")
print(f"confidence level of each interval: {1 - threshold:.3f}")
judged = [semantic_scores["judged@10"].mean()]
for name, blend in test.items():
    alpha = best_alpha(scores_by_alpha(train[name], qrels("train")))       # train only
    scores = evaluate(blend(alpha), qrels("test"))
    judged.append(scores["judged@10"].mean())
    result = compare(scores["ndcg@10"], semantic_scores["ndcg@10"], confidence=1 - threshold)
    print(f"{name} alpha chosen on train: {alpha}")
    print(f"{name} ndcg@10: {scores['ndcg@10'].mean():.3f}")
    print(f"{name} minus semantic: {result['mean difference']:.3f}")
    print(f"{name} permutation p: {result['permutation p']:.3f}")
    print(f"{name} t-test p: {result['t-test p']:.3f}")
    print(f"{name} interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
    print(f"{name} established: {result['permutation p'] < threshold}")
print(f"lowest judged@10: {min(judged):.3f}")
print(f"highest judged@10: {max(judged):.3f}")
```

Output:

```text
test queries: 30
semantic ndcg@10: 0.830
unweighted rrf ndcg@10: 0.812
p-value threshold for each comparison: 0.025
confidence level of each interval: 0.975
weighted sum alpha chosen on train: 0.7
weighted sum ndcg@10: 0.816
weighted sum minus semantic: -0.014
weighted sum permutation p: 0.229
weighted sum t-test p: 0.221
weighted sum interval: -0.042 to 0.008
weighted sum established: False
weighted rrf alpha chosen on train: 0.6
weighted rrf ndcg@10: 0.825
weighted rrf minus semantic: -0.005
weighted rrf permutation p: 0.650
weighted rrf t-test p: 0.643
weighted rrf interval: -0.029 to 0.016
weighted rrf established: False
lowest judged@10: 0.980
highest judged@10: 0.990
```

Semantic retrieval scores 0.830, the weighted sum of min-max scores 0.816, and weighted RRF 0.825. The three [runs](#score-every-test-query)' judged@10 values lie between 0.980 and 0.990, so missing judgments weigh about equally on all of them.

Neither blend beats semantic retrieval. The weighted sum differs from it by -0.014, with a permutation p-value of 0.229, a t-test p-value of 0.221 and an interval from -0.042 to 0.008. Weighted RRF differs by -0.005, with p-values of 0.650 and 0.643 and an interval from -0.029 to 0.016. Both intervals contain 0, and the tests agree with them. The example prints its verdict for each comparison, whether the permutation p-value falls below the threshold: False for the weighted sum and False for weighted RRF. So the finding is "no improvement", not "worse". For weighted RRF, it is the finding for α = 0.6, a weight that [the order of BM25's ties can move](#tuned-weight-stability).

If you predicted "above", you trusted a train gain that the permutation test couldn't tell from chance even on the queries that chose it, and that was the best of several tries.

**Working rule:** Adopt a blend only when it beats the best single retriever on held-out queries, with a permutation p-value below a threshold corrected for the number of planned comparisons. When it doesn't, keep the simpler system. For the store, that leaves semantic retrieval alone as the ranker to beat. Keep the tuned weights and the code, and test the blends again when a retriever or the catalog changes.

## Learn sparse term weights with SPLADE {#learned-sparse-splade}

Instead of fusing two retrievers, you can change one so that it misses less. BM25 only matches words that appear in a product's text. **Learned sparse retrieval** keeps BM25's machinery, an [inverted index](#build-an-inverted-index) of terms, but has a neural model choose each product's terms and their weights. SPLADE is one such model ([Formal et al., 2021](https://arxiv.org/abs/2107.05720)). A language model of the BERT family, a transformer that reads text as subword tokens, reads the product's text and, at each token i, gives every term j in its vocabulary a raw score w_ij. ReLU sets the negative scores to 0, and the original paper sums a logarithm of what's left over the text's tokens:

```text
weight of term j = sum over the text's tokens i of  log(1 + ReLU(w_ij))
```

The logarithm is a saturation, like BM25's: in the authors' words, it "prevents some terms to dominate and naturally ensures sparsity in representations". SPLADE v2 replaced the sum with the maximum over the tokens, and the authors made max pooling "the default configuration for SPLADE" ([Formal et al., 2021, SPLADE v2](https://arxiv.org/abs/2109.10086)). A SPLADE vector has one dimension per vocabulary entry, 30,522 for a BERT vocabulary, and typically more than 99% of them are zero ([Sentence Transformers](https://sbert.net/docs/sparse_encoder/usage/usage.html)). The nonzero terms include **expansion terms**: words the text doesn't contain but the model weights anyway, so a product can match a query word it never uses.

Expansion terms target one of BM25's failures in the store. Count, on the train queries, how many [exact](#queries-each-retriever-wins) products lack at least one of the query's words, as BM25's tokenizer sees them:

Example `exact-products-missing-query-words` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from collections import Counter

import bm25s

from lib.store import load_products, load_queries, product_text, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")


def words(texts):
    """The tokens BM25 matches on: bm25s's default tokenizer with English stopwords, as in lib.lexical."""
    tokenized = bm25s.tokenize(texts, stopwords="en", return_ids=False, show_progress=False)
    return [set(tokens) for tokens in tokenized]


product_words = dict(zip(products.index, words(product_text(products).tolist())))
query_words = dict(zip(queries.index, words(queries["query"].tolist())))
exact_pairs = [(query_id, product_id) for query_id in queries.index
               for product_id, grade in judgments[query_id].items() if grade == 2]
missed = Counter(word for query_id, product_id in exact_pairs
                 for word in query_words[query_id] - product_words[product_id])
missing = sum(not query_words[query_id] <= product_words[product_id] for query_id, product_id in exact_pairs)
print("exact train pairs:", len(exact_pairs))
print("exact pairs missing a query word:", missing)
print(f"share missing a query word: {missing / len(exact_pairs):.3f}")
print("most often missing:", ", ".join(f"{word} ({count})" for word, count in missed.most_common(8)))

exact = [product_id for query_id, product_id in exact_pairs if query_id == 453]   # midcentury tv unit
print("exact products for midcentury tv unit:", len(exact))
for word in ["midcentury", "unit", "stand"]:
    print(f"exact products containing {word}:", sum(word in product_words[product_id] for product_id in exact))
mid_century = product_text(products)[exact].str.contains("mid-century")
print("exact products whose text says mid-century:", mid_century.sum())
```

Output:

```text
exact train pairs: 1937
exact pairs missing a query word: 1454
share missing a query word: 0.751
most often missing: ligth (193), decorative (134), modern (102), freestanding (78), floats (58), queen (57), dining (56), infant (43)
exact products for midcentury tv unit: 25
exact products containing midcentury: 0
exact products containing unit: 0
exact products containing stand: 25
exact products whose text says mid-century: 20
```

Of 1937 exact (query, product) pairs, 1454 miss at least one query word, a share of 0.751. The output lists the words missed most often. Some are typos, which [chapter 8's corrector](#correct-spelling-from-catalog) targets, and plural forms, which [chapter 5 stems](#stem-word-forms); others are descriptive words the product text leaves out, or different words for one thing. For `midcentury tv unit`, of the 25 exact products, 0 contain `midcentury` and 0 contain `unit`. 20 say `mid-century` instead, and 25 say `stand`. Expansion terms are aimed at gaps like these, though whether a given model learns that a TV stand is a TV unit is something you'd measure.

The SPLADE authors' own technical report gives SPLADE-v3 an MRR@10 above 0.40 on the MS MARCO development set, a passage-ranking benchmark where [MRR@10](#score-the-first-relevant-result) measures how high the first relevant passage lands, and describes it as "comparing well to cross-encoder re-rankers" ([Lassance et al., 2024](https://arxiv.org/abs/2403.06789)). The book doesn't run SPLADE. The reference checkpoints, [`naver/splade-cocondenser-ensembledistil`](https://huggingface.co/naver/splade-cocondenser-ensembledistil) and [`naver/splade-v3`](https://huggingface.co/naver/splade-v3), are licensed CC-BY-NC-SA-4.0, which rules out commercial use. An Apache-2.0 model, [`opensearch-neural-sparse-encoding-doc-v3-distill`](https://huggingface.co/opensearch-project/opensearch-neural-sparse-encoding-doc-v3-distill), runs its neural model on products only, and encodes queries with a tokenizer and a table of weights.

**Working rule:** Consider learned sparse retrieval when BM25's misses are mostly vocabulary misses and you want to keep an inverted index. Check the model's licence first, and measure it like any retriever: alone, per query, on train queries, then on test.

## Match token by token with ColBERT {#late-interaction-colbert}

Where [SPLADE](#learned-sparse-splade) changes lexical retrieval, late interaction changes semantic retrieval. The store's semantic retrieval is **single-vector**: one embedding per product and one per query, compared once. **Late interaction** keeps one vector per token instead, so it is also called **multi-vector** retrieval. ColBERT encodes the query and the product separately, as an embedding model does, and compares them only at the end. For each query token it finds the most similar product token, and it sums those maxima, an operation called MaxSim ([Khattab and Zaharia, 2020](https://arxiv.org/abs/2004.12832)):

```text
score(query, product) = sum over query tokens q of  max over product tokens d of  cosine(q, d)
```

Because products are encoded without the query, their token vectors are computed once, ahead of time, which a [cross-encoder](#rerank-with-cross-encoder) can't do: it reads both texts as one input. The ColBERT paper reports effectiveness "competitive with existing BERT-based models" that read the query and passage together, at speeds "two orders-of-magnitude faster". The price is storage: one vector per token rather than per product. ColBERTv2 compresses them, "reducing the space footprint of late interaction models by 6–10×" ([Santhanam et al., 2022](https://arxiv.org/abs/2112.01488)).

In the store, take `midcentury tv unit` again, the query whose exact products [say `stand`, never `unit`](#learned-sparse-splade). A single vector has to fold the whole query into one direction, and the whole product text into another. With late interaction, the query's `unit` is compared with each of the product's tokens, `stand` among them, and its best match counts on its own. Token-level matching helps on some hard cases. On NevIR, a negation benchmark where random choice scores 25%, ColBERTv1 scored 19.7% and ColBERTv2 13.0%, above every single-vector model tested (12% or less), though still below chance ([Weller et al., 2024](https://arxiv.org/abs/2305.07614)). In BEIR, a benchmark that tests models zero-shot, on datasets they weren't trained for, rerankers and late-interaction models "on average achieve the best zero-shot performances", at a high computational cost ([Thakur et al., 2021](https://arxiv.org/abs/2104.08663)). Open tooling exists, such as the PyLate library and the Apache-2.0 model [`lightonai/GTE-ModernColBERT-v1`](https://huggingface.co/lightonai/GTE-ModernColBERT-v1) ([Chaffin and Sourty, 2025](https://arxiv.org/abs/2508.03555)). The book doesn't run ColBERT either.

**Working rule:** Consider late interaction when single-vector retrieval misses details that hang on one word, and you can afford a vector per token. For a catalog the size of the store's, we recommend testing a reranker on a shortlist first ([chapter 9](#rerank-semantic-with-cross-encoder)): it reads the same details at query time and needs no new index, though none of chapter 9's rerankers shows an established gain over the store's semantic retrieval.

## Decide when hybrid retrieval pays {#when-hybrid-helps}

Whether fusion helps depends on the retrievers you fuse, and published studies point both ways. Lexical and dense retrieval, dense meaning embedding-based, can complement each other even when the dense model is the weaker one: out of domain, a zero-shot hybrid gained "an average of 20.4% relative gain over the deep retrieval model" across three datasets ([T. Chen et al., 2022](https://arxiv.org/abs/2201.10582)). The lexical baseline matters. The authors of DPR, a dense retriever, found little gain from a hybrid, and a replication with a stronger BM25 found "statistically significant gains" ([Ma et al., 2021](https://arxiv.org/abs/2104.05740)). The strength of the semantic retriever matters too. On BRIGHT, a benchmark of reasoning-heavy queries, fusing BM25 by a weighted sum of min-max scores at α = 0.5 added 3.5 to 4.9 points of nDCG@10 to mid-tier dense retrievers and cost the two strongest 2.0 to 2.9. "However, fusion can harm already-strong retrievers", the authors write, because "the fused list promotes lexically similar but semantically irrelevant documents" ([Abdallah et al., 2026](https://arxiv.org/abs/2604.03676)).

Production reports usually compare a hybrid with lexical search alone. A retailer's preprint reports that hybrid lexical and vector search beat lexical search alone in an online A/B test, raising click-through by 0.97% and conversion by 0.98% ([Sonagara et al., 2026](https://arxiv.org/abs/2609.31498)). That is evidence for adding semantic retrieval to a lexical system, not for adding lexical retrieval to a strong semantic one, which is the store's question.

The store sits in the strong-retriever case: on the test queries, [chapter 3](#compare-runs-in-a-harness) establishes semantic retrieval's lead over BM25, and [neither tuned blend beats it](#report-blends-on-test). The store's BM25 is the book's unstemmed baseline. [Chapter 5](#stem-word-forms) builds a stronger one, and Ma et al.'s replication is a reason to test the blends again with it.

Fusing scores isn't the only kind of hybrid. A search engine can also use lexical matches as a filter on semantic retrieval: one engine adds an embedding operator to its query language, so that "hybrid retrieval expressions, with arbitrary combinations of embeddings and terms" run as one query (Huang et al., 2020). For the store, that could mean requiring a size such as `48` to match exactly, then ranking the matches by embedding. That is a hypothesis to test, not a result, and a naive filter fails on `7qt slow cooker`, whose spelling [no product uses](#queries-each-retriever-wins). Deciding when a query carries such a constraint is query understanding ([chapter 8](#classify-queries-from-products)), and chapter 8 [tries such a filter](#standalone-follow-ups) on a shopper's follow-up messages that name a color, shape, size or finish. Choosing a weight per query is query understanding too, and this book doesn't build it. Picking the better ranking for each train query would score 0.802, and a per-query weight, which mixes the lists, isn't bound by that figure. One per-query method asks an LLM, a large language model, to judge each retriever's top result and sets α from that ([Hsu and Tzeng, 2025](https://arxiv.org/abs/2503.23013)). The BRIGHT study found a score-based variant of it unstable (Abdallah et al., 2026).

**Working rule:** We recommend trying a hybrid when your two retrievers are close in quality, when your embedding model works outside the domain it was trained for, or when many queries depend on exact terms your embeddings miss. Start with weighted RRF: it needs ranks only, and on the store's train queries the permutation test couldn't tell it from the weighted sum. Move to a weighted sum of normalized scores when both engines give you scores for every candidate: two studies found it ahead of RRF on their data (Bruch et al., 2023; Abdallah et al., 2026), and on the store's train queries its weight was [the more stable](#tuned-weight-stability). When one retriever is established as the stronger on held-out queries and no tuned blend beats it there, use it alone, keep the other as a baseline, and test a lexical filter for queries with exact constraints. That is the store's case.

## What goes wrong in production {#hybrid-retrieval-in-production}

**Two retrievers cost two of everything.** The examples here score a sample of the catalog offline, but a live hybrid search keeps two indexes up to date and runs two searches on every query. They can run in parallel, but the slower one sets the response time, and a failure in either degrades the result. Count that cost against the gain you measured.

**Short lists drop candidates.** Fusion can't rank a product neither retriever returned. On the store's train queries, the union of two top-100 lists holds 0.810 of each query's exact products, and the union of two top-20 lists 0.445. A depth limit in one engine's configuration can cut candidates without anyone noticing.

**Missing scores need a rule.** When each retriever returns only its top k, a product in one list but not the other has no score from the second. The DPR replication assigns it "the minimum dense retrieval score among the retrieved documents", and the reverse for BM25 ([Ma et al., 2021](https://arxiv.org/abs/2104.05740)). Bruch et al. compute the missing score exactly instead, as `lib.blend.candidates` does, which a production engine may not let you do ([Bruch et al., 2023](https://arxiv.org/abs/2210.11934)).

**Min-max is relative.** The best candidate for a query always gets 1, even when every candidate is poor. A query that shares no word with any product in the catalog gives every candidate a BM25 score of 0. Plain min-max then divides by zero, and `lib.blend` returns zeros, so the blend silently becomes semantic retrieval alone. No store query does this; a live search box will.

**A fused score isn't a confidence.** Retrieval scores are poorly calibrated: "Confidence calibration is consistently weak across model families" ([Abdallah et al., 2026](https://arxiv.org/abs/2604.03676)). Don't set a threshold on a fused score to decide that a query has no good results.

**A tuned weight belongs to one pair of retrievers.** The store's α fits these BM25 settings, this embedding model and this catalog. Change any of them, and re-tune on train queries before you trust the old weight. A tuned RRF "generalizes poorly to out-of-domain datasets" ([Bruch et al., 2023](https://arxiv.org/abs/2210.11934)).

**Working rule:** Log both retrievers' ranks next to the fused result, check the list depth in every engine's configuration, and re-tune α whenever a retriever changes.

## Decisions this chapter made {#hybrid-retrieval-decisions}

Each choice below is a default for the store, and each has a reason a later change would need to beat.

- **Tune on train, report on test.** Every analysis and every tuned setting uses the 50 train queries, and comparisons there are tuning checks, not evidence. The chapter reads the test queries once, to report.
- **Two planned test comparisons,** each tuned blend against semantic retrieval, decided by the permutation test at 0.05 divided by 2, with the t-test and a bootstrap interval beside it.
- **Check each retriever before fusing,** with judged@10 and a paired test, and count per query where each one wins.
- **Candidates: the union of both retrievers' top 100,** with both scores looked up for every candidate, so no product's score is missing.
- **Normalization: per-query min-max.** The permutation test on train can't tell the other two normalizations from it at 0.05, and min-max needs no knowledge of either scoring function.
- **RRF: k = 60, with lists 100 deep.** The best k on train gains nothing over 60 that the permutation test can tell from chance at 0.05, and it changes with the order of BM25's ties. A deeper list can only add candidates.
- **One weight, α, tuned over 0 to 1 in steps of 0.1** for both blends, chosen by mean nDCG@10 on train, then bootstrapped and tuned again with BM25's ties reversed. The weighted sum's α holds under both checks; weighted RRF's doesn't.
- **Adopt a blend only if it beats the best single retriever on test.** Neither tuned blend does, so the store's ranker to beat stays semantic retrieval alone, with BM25, unstemmed, kept as the baseline.
- **SPLADE and ColBERT are described, not recorded,** because neither is needed to answer the store's question.
