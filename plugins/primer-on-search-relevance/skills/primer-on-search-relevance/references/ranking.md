---
title: "A Primer on Search Relevance"
chapter: "Ranking"
chapter_id: ranking
book: primer-on-search-relevance
edition: 2026.11.8
verified: 2026-11-13
edition_code: W7B6-3VSA
canonical: https://rollingedition.com/primer-on-search-relevance/ranking
license: CC BY 4.0
attribution: "“Ranking,” chapter 9 of A Primer on Search Relevance, Edition 2026.11.8, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/ranking. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Ranking

By the end of this chapter you can describe each product that retrieval returns with features, train a learning-to-rank model with LightGBM on your own judgments, rerank the top of the list with a cross-encoder or an LLM, measure an LLM reranker's positional bias, set the rerank depth by counting its costs, and distil a slow reranker into a fast one. You can also decide, with a planned comparison on the test queries, whether any of them beats your retrieval.

[Semantic retrieval](#search-by-meaning) alone is still the ranker to beat at [the store](#store-data), where every search is ordered by one embedding score and nothing else. It ranks products by embeddings from `Snowflake/snowflake-arctic-embed-m-v1.5`, and scores 0.830 [nDCG@10](#score-one-ranking) on the 30 [test queries](#store-data). No change in chapters 5 to 8 has beaten it by an established margin. This chapter asks whether a second stage can: a model trained on the store's own judgments, a reranker that reads the query and the product together, or an LLM. [Chapter 1's cross-encoder](#rerank-with-cross-encoder) reranked the hybrid run, not semantic retrieval, and never saw the store's judgments.

So this chapter tries all three on semantic retrieval's top results, each scored against the store's judgments. **Reranking** reorders the top of retrieval's list with a slower model. The store's rerankers are **recorded**: each ran once and saved its outputs, which the examples read.

The store's LLM is the open model `gemma4:12b-it-q4_K_M`, licensed Apache-2.0. It ran locally with chapter 4's settings, which make it take its likeliest next word every time, plus thinking off, so it answers without writing out reasoning, and a JSON schema, a machine-readable description of the answer's shape. `recordings/llm_rerank.py` reranked semantic retrieval's top 20 for the test queries only, so nothing about the LLM rerankers can be tuned. Every score uses the human judgments, because in one study LLM judges ranked LLM rerankers too high ([What goes wrong in production](#ranking-in-production)). These results describe one model and two prompts, so treat them as the store's, not as a verdict on LLM rerankers.

The chapter fixed its 5 planned comparisons on the test queries before it read any test result. Each sets one method against semantic retrieval's run on nDCG@10:

1. [LambdaMART](#lambdamart-on-test-queries), a learned ranker trained on the train queries' judgments, ordering each query's candidate products
2. the [cross-encoder](#rerank-semantic-with-cross-encoder) reranking semantic retrieval's top 20
3. the LLM scoring each of the top 20 [on its own](#llm-pointwise-reranking)
4. the LLM ordering the top 20 [in one prompt](#llm-listwise-reranking)
5. a small [distilled ranker](#distill-the-cross-encoder) trained on the cross-encoder's scores

The bar is [the book's rule](#when-a-difference-is-established): 5 planned comparisons split its 0.05, so each needs a paired [permutation test](#permutation-test-on-queries) p-value below 0.01. The [paired t-test](#paired-t-test-on-queries) and a 99% [bootstrap interval](#report-the-size-of-a-gap) stand beside it.

## Describe each candidate with features {#ranking-features}

A learned ranker, the first of the chapter's [planned comparisons](#ranking), doesn't read text. It scores each pair of a query and a product from a list of numbers, its **features**, and learns from judgments how to weigh them. A **query-dependent** feature describes the pair, such as a BM25 score. A **query-independent** feature describes the product alone, such as how many shoppers rated it. Feature sets for web search mix both: LETOR 4.0, a benchmark for learning to rank, has 46 features, among them "BM25 of title", "PageRank" and "Number of slash in URL" ([Qin and Liu, 2013](https://arxiv.org/abs/1306.2597)). A ranker scores only **candidates**, the products a cheaper retrieval stage returns, so its features can be expensive.

The candidates for each of the store's queries are the products the cross-encoder's recording scored: the union of BM25's top 100 and [semantic retrieval](#search-by-meaning)'s top 100. `lib.ranking.feature_table` gives each candidate 8 features:

- `bm25`: the [BM25](#rank-with-bm25) score from `lib.lexical`, the book's unstemmed baseline, and 0 for a product that shares no term with the query
- `similarity`: the cosine similarity of the query's and the product's embeddings
- `cross_encoder`: the recorded cross-encoder score
- `name_match` and `attribute_match`: the share of the query's terms, [tokenized as chapter 5 does](#split-text-into-terms), found in the product's name and in its [attributes](#index-attributes-as-a-field)
- `rating_count`, `average_rating` and `review_count`, which the store's data gives each product

2632 of the catalog's products have no rating, and their three rating features stay missing. The table also holds each candidate's human grade, or a gap when nobody judged it. Build the table for the [train queries](#store-data), look at one query, then compare each feature across the grades:

Example `ranking-features-by-grade` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Builds the feature table for the train queries, shows one query's candidates, and compares each feature's mean across
the human grades. The prose's point rests on the mean cross_encoder line for each grade and the mean of each feature by grade."""
import pandas as pd

from lib.ranking import FEATURES, feature_table
from lib.store import load_products, load_queries

products, queries = load_products(), load_queries("train")      # train queries: features are design work
table = feature_table(products, queries)
print(f"features: {len(FEATURES)}")
print(f"train candidates: {len(table)}")
print(f"train candidates per query, median: {table.groupby('query_id').size().median():.0f}")
print(f"share of train candidates nobody judged: {table['grade'].isna().mean():.3f}")

query_id = queries.index[queries["query"] == "laundry basket with wheels"][0]
one = table[table["query_id"] == query_id].sort_values("cross_encoder", ascending=False)
one = one.assign(name=products.loc[one["product_id"], "name"].str[:38].to_numpy())
pd.set_option("display.width", 200)
print(f"\ncandidates for laundry basket with wheels: {len(one)}")
print(one[["name", "bm25", "similarity", "cross_encoder", "name_match", "attribute_match", "rating_count", "grade"]]
      .head(6).round(3).to_string(index=False))
print(f"top 6 by cross-encoder, exact: {(one['grade'].head(6) == 2).sum()}")

# grades 2, 1 and 0 are exact, partial and irrelevant; a missing grade means nobody judged the pair
label = table["grade"].map({2: "exact", 1: "partial", 0: "irrelevant"}).fillna("unjudged")
means = table[FEATURES].groupby(label).mean().loc[["exact", "partial", "irrelevant", "unjudged"]]
print("\nmean of each feature by grade, train candidates:")
print(means.round(3).to_string())
for grade in means.index:
    print(f"mean cross_encoder, {grade}: {means.at[grade, 'cross_encoder']:.3f}")
relevance = ["bm25", "similarity", "cross_encoder", "name_match"]
nearer = [name for name in relevance if abs(means.at["unjudged", name] - means.at["irrelevant", name])
          < abs(means.at["unjudged", name] - means.at["partial", name])]
print(f"relevance features where unjudged sits nearer irrelevant than partial: {len(nearer)} of {len(relevance)}")
medians = table[["rating_count", "review_count"]].groupby(label).median().loc[means.index]  # counts are skewed
for grade in ["exact", "partial", "irrelevant"]:
    print(f"rating_count, {grade}, mean: {means.at[grade, 'rating_count']:.3f}")
    print(f"rating_count, {grade}, median: {medians.at[grade, 'rating_count']:.1f}")
print(f"products with no rating: {products['rating_count'].isna().sum()}")
```

Output:

```text
features: 8
train candidates: 6896
train candidates per query, median: 131
share of train candidates nobody judged: 0.286

candidates for laundry basket with wheels: 125
                                  name  bm25  similarity  cross_encoder  name_match  attribute_match  rating_count  grade
       laundry sorter basket on wheels 8.229       0.597          3.433       1.000              0.0           NaN    2.0
                vintage laundry basket 6.270       0.572          2.995       0.667              0.0         638.0    2.0
         rolling wicker laundry basket 5.494       0.588          2.974       0.667              0.0         110.0    2.0
aluminum frame laundry basket can be f 4.739       0.524          2.941       0.667              0.0          14.0    2.0
    rebrilliant rolling laundry hamper 5.537       0.558          2.804       0.333              0.0          17.0    2.0
4-bag laundry hamper sorter cart baske 6.012       0.543          2.739       0.667              0.0           NaN    2.0
top 6 by cross-encoder, exact: 6

mean of each feature by grade, train candidates:
             bm25  similarity  cross_encoder  name_match  attribute_match  rating_count  average_rating  review_count
grade
exact       4.317       0.517          2.191       0.562            0.024       466.879           4.537       333.589
partial     3.936       0.454          1.513       0.461            0.030       385.454           4.539       288.779
irrelevant  2.760       0.360          1.159       0.404            0.006       246.781           4.552       159.052
unjudged    2.323       0.369          1.050       0.140            0.018       339.904           4.520       237.027
mean cross_encoder, exact: 2.191
mean cross_encoder, partial: 1.513
mean cross_encoder, irrelevant: 1.159
mean cross_encoder, unjudged: 1.050
relevance features where unjudged sits nearer irrelevant than partial: 4 of 4
rating_count, exact, mean: 466.879
rating_count, exact, median: 43.0
rating_count, partial, mean: 385.454
rating_count, partial, median: 31.0
rating_count, irrelevant, mean: 246.781
rating_count, irrelevant, median: 35.5
products with no rating: 2632
```

The train queries have 6896 candidates, a median of 131 per query, and nobody judged a share of 0.286 of them.

`laundry basket with wheels` has 125 candidates. The top six by cross-encoder score include 6 [exact](#store-data) products. Their `attribute_match` is 0, because attributes hold colours, materials and sizes, not words such as `wheels`.

Across the train candidates, the mean cross-encoder score falls from 2.191 for exact products to 1.513 for partial and 1.159 for irrelevant ones, and `bm25`, `similarity` and `name_match` fall the same way. `average_rating` and `attribute_match` barely move.

The means of `rating_count` fall with the grade, but the medians don't: a few heavily rated products set the means.

| Grade | Mean rating count | Median rating count |
| --- | --- | --- |
| exact | 466.879 | 43.0 |
| partial | 385.454 | 31.0 |
| irrelevant | 246.781 | 35.5 |

Unjudged candidates average a cross-encoder score of 1.050, and on 4 of 4 features that fall with the grade, their mean sits nearer the irrelevant products' than the partial ones'. That matters for what an unjudged candidate should teach a model.

**Working rule:** Start with the features you already compute: each retriever's score, a reranker's score if you have one, matches on fields such as the name, and popularity signals. Compare each feature by grade on train queries before you train, with means for scores and medians for skewed counts. A feature that doesn't move with the grade has little to teach the model. Compute features with the same code when you train and when you serve.

## Learn a ranking from pairs of products {#learn-from-pairs}

**Learning to rank** trains a model on judged queries to order candidates by their [features](#ranking-features). Its methods fall into three families, pointwise, pairwise and listwise ([Liu, 2009](https://doi.org/10.1561/1500000016)). A **pointwise** model predicts each product's grade on its own, as a regression. A **pairwise** model learns which of two products should rank higher. A **listwise** model scores a whole ranking. Liu's 2009 comparison on the LETOR benchmark favoured the listwise approach, though tentatively. The obstacle for all three is the metric: nDCG changes only when two products swap places, so ranking metrics "are everywhere either discontinuous or flat, so gradient descent appears to be problematic" ([Burges, 2010](https://www.microsoft.com/en-us/research/publication/from-ranknet-to-lambdarank-to-lambdamart-an-overview/)).

RankNet, a pairwise method, works around it with a smooth loss on pairs. For two products where i should rank above j, its gradient is large when the model scores them the wrong way round or nearly level, and small when it already has them well apart. LambdaRank keeps that gradient and multiplies it by how much nDCG would change if the two products swapped places (Burges, 2010, section 4.1). Burges writes the gradient with a minus sign, as the slope of a cost; here a positive λ pushes i up:

```text
λ_ij    = σ / (1 + exp(σ · (s_i − s_j))) · |ΔnDCG_ij|      s: the model's scores, σ = 1
ΔnDCG_ij = (g_i − g_j) · (1 / log2(1 + r_i) − 1 / log2(1 + r_j)) / ideal DCG      g: grades, r: positions
```

A product's total is its λ summed over the pairs where it should rank higher, minus those where it should rank lower. Burges (2010) also reads the λ's as forces, pushing products up and down the list.

**LambdaMART** uses these λ as the gradients for **gradient-boosted trees**, which add small decision trees one at a time, each fitted to the gradients of the trees before it: "LambdaMART is the boosted tree version of LambdaRank, which is based on RankNet". An ensemble of LambdaMART rankers won Track 1 of the Learning to Rank Challenge that Yahoo ran in 2010 (Burges, 2010).

One train query, `outdoor waterproof chest`, shows the arithmetic. Let semantic similarity be the model's scores so far, compute every pair's λ in its top 10 by hand, check each |ΔnDCG| by swapping the pair and recomputing nDCG with `lib.metrics`, and add up the forces:

Example `lambdas-for-one-query` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.8:

```python
"""Works out LambdaRank's λ for every pair in one train query's top 10 by hand, and checks each pair's |ΔnDCG| against
swapping the pair in the metric. The prose's point rests on the strongest push up and down, and on the count of pairs
whose formula matches swapping."""
import math
from itertools import combinations

from lib.metrics import dcg_at_k, ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")
query_id = queries.index[queries["query"] == "outdoor waterproof chest"][0]
judged = judgments[query_id]
scores = SemanticSearch().search(query_id, k=10)       # the model so far: semantic similarity
ranking, similarity = list(scores.index), scores.to_numpy()
# an unjudged product counts as grade 0, as it does in the metric
grades = [judged.get(product_id, 0) for product_id in ranking]
# the ideal DCG takes every judged product, as lib.metrics does; sigma is 1, LightGBM's default sigmoid
ideal, sigma = dcg_at_k(sorted(judged.values(), reverse=True), 10), 1.0
print("grades from the top:", " ".join(map(str, grades)))

force, checks, pulls = [0.0] * len(ranking), [], []
for i, j in combinations(range(len(ranking)), 2):      # i is above j
    if grades[i] == grades[j]:
        continue
    better, worse = (i, j) if grades[i] > grades[j] else (j, i)
    ranknet = 1 / (1 + math.exp(sigma * (similarity[better] - similarity[worse])))      # RankNet's pull
    # i and j count from 0, so position p is i + 1 and its discount is 1 / log2(p + 1), which is 1 / log2(i + 2)
    delta = abs((grades[i] - grades[j]) * (1 / math.log2(i + 2) - 1 / math.log2(j + 2))) / ideal
    swapped = ranking.copy()
    swapped[i], swapped[j] = swapped[j], swapped[i]
    checks.append(math.isclose(delta, abs(ndcg_at_k(swapped, judged, 10) - ndcg_at_k(ranking, judged, 10))))
    pulls.append(ranknet)
    pair_lambda = sigma * ranknet * delta                         # LambdaRank: scaled by |delta nDCG|
    force[better], force[worse] = force[better] + pair_lambda, force[worse] - pair_lambda

print(f"pairs with different grades: {len(checks)}")
print(f"pairs where delta ndcg by formula matches swapping the pair: {sum(checks)}")
for position, push in enumerate(force, start=1):
    print(f"force at position {position}: {push:+.3f}")
# list indexes count from 0 and positions from 1, hence the + 1
print(f"strongest push up, position: {force.index(max(force)) + 1}")
print(f"strongest push down, position: {force.index(min(force)) + 1}")
print(f"ranknet's pull, lowest: {min(pulls):.3f}\nranknet's pull, highest: {max(pulls):.3f}")
```

Output:

```text
grades from the top: 1 2 2 0 1 2 0 2 0 0
pairs with different grades: 32
pairs where delta ndcg by formula matches swapping the pair: 32
force at position 1: +0.013
force at position 2: +0.159
force at position 3: +0.104
force at position 4: -0.083
force at position 5: -0.010
force at position 6: +0.063
force at position 7: -0.092
force at position 8: +0.063
force at position 9: -0.105
force at position 10: -0.111
strongest push up, position: 2
strongest push down, position: 10
ranknet's pull, lowest: 0.472
ranknet's pull, highest: 0.525
```

The formula's |ΔnDCG| matches the change from swapping the pair for 32 of the 32 pairs in the top 10 with different grades. The top 10's grades, from the top, are 1 2 2 0 1 2 0 2 0 0; an unjudged product counts as 0, as it does in the metric.

The strongest push up goes to position 2, an exact product, with +0.159; the strongest push down goes to position 10, an irrelevant product, with -0.111. The partial product at position 1 gets a net push of +0.013: the irrelevant products below push it up, and the exact ones push it down.

RankNet's factor in λ stays between 0.472 and 0.525, because the similarities lie close together, so |ΔnDCG| decides almost everything.

That example simplifies. It takes the ideal DCG from every judged product, as `lib.metrics` does, and looks at ten products. LightGBM takes the ideal from the query's training rows, and at 4.7.0 two defaults change the λ. `lambdarank_truncation_level` is 30, which limits training to the top 30 results: only pairs with a product in the current top 30 get a λ. `lambdarank_norm` is true, which normalizes the lambdas across queries; set it to false to get the original lambdarank algorithm ([Parameters](https://lightgbm.readthedocs.io/en/v4.7.0/Parameters.html)). Normalizing, as LightGBM's source does it, divides each pair's |ΔnDCG| by the gap between its scores plus 0.01, then rescales each query's λ ([`rank_objective.hpp`](https://github.com/lightgbm-org/LightGBM/blob/v4.7.0/src/objective/rank_objective.hpp)). To check the formula against the library, write it as a custom LightGBM objective, grow five small trees on this query's candidates, and grow them again with LightGBM's lambdarank, with and without those defaults:

Example `lambdas-match-lightgbm` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Writes LambdaRank's gradients by hand as a custom LightGBM objective, then checks them against LightGBM's own lambdarank
on one query, with and without its defaults. The prose's point rests on the two printed differences: a rounding-sized gap
without the defaults, and a large one at them."""
import numpy as np
from lightgbm import LGBMRanker

from lib.ranking import DETERMINISTIC, FEATURES, feature_table
from lib.store import load_products, load_queries

queries = load_queries("train")
one = queries[queries["query"] == "outdoor waterproof chest"]
rows = feature_table(load_products(), one)                  # one query's candidates, in product_id order
# unjudged candidates count as grade 0, as in the metric
grades = rows["grade"].fillna(0).astype(int).to_numpy()
SIGMA = 1.0                                                   # LightGBM's default sigmoid


def lambdas(y_true, y_pred, weight, group):
    """The chapter's lambda for every pair with different grades, as gradients and second derivatives."""
    rank = np.empty(len(y_pred), dtype=int)
    rank[np.argsort(-y_pred, kind="stable")] = np.arange(len(y_pred))   # LightGBM's stable sort on score
    # rank counts from 0, so the product at position rank + 1 has the discount 1 / log2(rank + 2)
    discount, ideal = 1 / np.log2(rank + 2), np.sum(np.sort(y_true)[::-1] / np.log2(np.arange(len(y_true)) + 2))
    gradient, hessian = np.zeros(len(y_pred)), np.zeros(len(y_pred))
    for i in range(len(y_true)):
        for j in np.flatnonzero(y_true < y_true[i]):                      # i should rank above j
            delta = (y_true[i] - y_true[j]) * abs(discount[i] - discount[j]) / ideal
            pull = 1 / (1 + np.exp(SIGMA * (y_pred[i] - y_pred[j])))
            gradient[i], gradient[j] = gradient[i] - SIGMA * pull * delta, gradient[j] + SIGMA * pull * delta
            hessian[[i, j]] += SIGMA ** 2 * pull * (1 - pull) * delta
    return gradient, hessian


# five small trees; min_child_samples is 5 where LightGBM's default is 20, so the trees can split this query's candidates
tree = {"n_estimators": 5, "num_leaves": 3, "min_child_samples": 5, **DETERMINISTIC}
# turns off normalization and sets truncation to every candidate, so every pair gets a λ, as the formula has it
plain = {"lambdarank_norm": False, "lambdarank_truncation_level": len(rows)}   # LightGBM's lambdas, untouched
models = {"by hand": LGBMRanker(objective=lambdas, **tree),
          "lightgbm, no normalization or truncation": LGBMRanker(objective="lambdarank", label_gain=[0, 1, 2], **plain, **tree),
          "lightgbm at its defaults": LGBMRanker(objective="lambdarank", label_gain=[0, 1, 2], **tree)}
# raw scores: the values the gradients act on, before any sigmoid
scores = {name: model.fit(rows[FEATURES], grades, group=[len(rows)]).predict(rows[FEATURES], raw_score=True)
          for name, model in models.items()}
print(f"candidates: {len(rows)}")
for name in list(models)[1:]:
    difference = np.abs(scores[name] - scores["by hand"]).max()
    print(f"{name}, largest difference from the lambdas by hand after 5 trees: {difference:.6f}")
```

Output:

```text
candidates: 180
lightgbm, no normalization or truncation, largest difference from the lambdas by hand after 5 trees: 0.000006
lightgbm at its defaults, largest difference from the lambdas by hand after 5 trees: 0.595667
```

Over the query's 180 candidates, LightGBM without normalization or truncation scores every product within 0.000006 of the custom objective's scores. The gap is rounding, since LightGBM reads its sigmoid from a precomputed table (`rank_objective.hpp`). At its defaults, scores differ by up to 0.595667.

**Working rule:** Train rankers with a gradient that weighs each pair by the metric you report, as LambdaMART does, rather than regressing on grades. Know which defaults of your library change that gradient, and check on train queries that it beats a pointwise model on your data, because the families' order in a benchmark doesn't transfer by itself.

## Train LambdaMART with LightGBM {#train-lambdamart}

LightGBM trains [LambdaMART](#learn-from-pairs) with `LGBMRanker` and `objective="lambdarank"`. Four settings need care, and each is documented for 4.7.0:

- **Rows are grouped by query.** "data should be ordered by the query", and `group` holds the number of rows of each query in that order, not query IDs, so its sizes sum to the number of rows (`sum(group) = n_samples`; [Parameters](https://lightgbm.readthedocs.io/en/v4.7.0/Parameters.html); [`LGBMRanker`](https://lightgbm.readthedocs.io/en/v4.7.0/pythonapi/lightgbm.LGBMRanker.html)).
- **Gains are exponential by default.** `label_gain` defaults to `0,1,3,7,15,31,63,...`, so "the gain of label `2` is `3`", and every label must be smaller than the number of gains (Parameters). That is Burges's DCG, with gain 2^grade − 1. The book's nDCG uses [linear gains](#gains-are-a-choice), so set `label_gain=[0, 1, 2]`.
- **nDCG is evaluated at positions 1 to 5 by default.** Set `eval_at=[10]` to stop on nDCG@10, and report the final score with `lib.metrics` anyway.
- **Validation data goes in `eval_X` and `eval_y`.** In 4.7.0, `eval_set` is "Deprecated since version 4.7.0", and `eval_X` and `eval_y` replace it (`LGBMRanker`; [release notes](https://github.com/lightgbm-org/LightGBM/releases/tag/v4.7.0)). The examples pass `eval_X`, `eval_y` and `eval_group`.

**Early stopping** scores held-out train queries after every tree, and keeps the trees up to the best score once 30 more bring no gain. So that training repeats exactly, the examples use one thread, a fixed seed and `deterministic=True`, which "should ensure the stable results when using the same data" (Parameters), with `force_row_wise=True`, which the same entry recommends, to avoid potential instability from numerical issues. `lib.ranking` holds these settings, and its `fit` applies the grouping and early stopping.

Row order matters too. Before the first tree every score is 0, so LightGBM takes the rows' order as the starting ranking for the first λ, and equal scores need a tie-break. The cross-encoder's recording lists each query's [candidates](#ranking-features) best first, which would hand the model the cross-encoder's ranking before it learned anything. So `feature_table` sorts candidates by `product_id`, and `lib.ranking.ranked` breaks ties by `product_id`.

Choose the tree size by **cross-validation** on the train queries: split them into five folds, rank each fold with a model fitted on three others and stopped early on the fifth, and score every query once. Try eight settings, from 3 to 31 leaves at two learning rates, counting unjudged candidates as grade 0 as the metric does:

Example `lambdamart-tree-size-on-train` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Cross-validates LambdaMART on the train queries over eight tree sizes and learning rates, and names the best. The prose's
point rests on the best setting's score, and on the score beside it for LightGBM's default of 31 leaves at 0.1."""
from lightgbm import LGBMRanker

from lib.metrics import evaluate
from lib.ranking import DETERMINISTIC, FEATURES, LAMBDARANK, TREE_GRID, TREES, cross_validate, feature_table
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # tuning: train queries only
candidates = feature_table(load_products(), queries)
candidates["grade or 0"] = candidates["grade"].fillna(0).astype(int)  # unjudged counts as irrelevant, as in nDCG
print(f"train queries: {len(queries)}")
print(f"semantic, train ndcg@10: {evaluate(SemanticSearch().run(queries, k=100), judgments)['ndcg@10'].mean():.3f}")

results = {}
for setting in TREE_GRID:                                            # LightGBM's default is 31 leaves at 0.1
    name = f"{setting['num_leaves']} leaves, learning rate {setting['learning_rate']}"
    # up to 500 trees; early stopping inside cross_validate keeps fewer
    model = lambda: LGBMRanker(**LAMBDARANK, n_estimators=500, **setting, **DETERMINISTIC)
    # one nDCG@10 per train query, each ranked by a model that never saw that query
    results[name] = cross_validate(model, candidates, candidates, "grade or 0", FEATURES, judgments)
    print(f"{name}, cross-validated ndcg@10: {results[name].mean():.3f}")
    # the trees early stopping kept in each fold
    print(f"{name}, trees kept per fold: {', '.join(map(str, results[name].attrs['trees']))}")
best = max(results, key=lambda name: results[name].mean())
print(f"settings tried: {len(results)}")
print(f"best setting: {best}")
print(f"lib.ranking.TREES holds it: {'yes' if best == f'{TREES['num_leaves']} leaves, learning rate {TREES['learning_rate']}' else 'no'}")
```

Output:

```text
train queries: 50
semantic, train ndcg@10: 0.772
3 leaves, learning rate 0.05, cross-validated ndcg@10: 0.780
3 leaves, learning rate 0.05, trees kept per fold: 18, 27, 52, 20, 85
3 leaves, learning rate 0.1, cross-validated ndcg@10: 0.798
3 leaves, learning rate 0.1, trees kept per fold: 99, 20, 8, 43, 38
7 leaves, learning rate 0.05, cross-validated ndcg@10: 0.744
7 leaves, learning rate 0.05, trees kept per fold: 2, 28, 30, 39, 55
7 leaves, learning rate 0.1, cross-validated ndcg@10: 0.772
7 leaves, learning rate 0.1, trees kept per fold: 80, 12, 13, 7, 20
15 leaves, learning rate 0.05, cross-validated ndcg@10: 0.720
15 leaves, learning rate 0.05, trees kept per fold: 4, 37, 175, 44, 120
15 leaves, learning rate 0.1, cross-validated ndcg@10: 0.728
15 leaves, learning rate 0.1, trees kept per fold: 19, 68, 136, 48, 53
31 leaves, learning rate 0.05, cross-validated ndcg@10: 0.679
31 leaves, learning rate 0.05, trees kept per fold: 15, 8, 91, 8, 22
31 leaves, learning rate 0.1, cross-validated ndcg@10: 0.737
31 leaves, learning rate 0.1, trees kept per fold: 11, 75, 166, 96, 58
settings tried: 8
best setting: 3 leaves, learning rate 0.1
lib.ranking.TREES holds it: yes
```

Of 8 settings, the best is 3 leaves, learning rate 0.1, at 0.798; LightGBM's default of 31 leaves at 0.1 (`LGBMRanker`) scores 0.737. The best of all the settings flatters itself, so expect less on held-out queries.

One choice depends on the store's judgments. Nobody judged a share of 0.286 of the train candidates. A model can count them as grade 0, or learn from judged candidates only; [unjudged isn't irrelevant](#unjudged-results), but the model will rank them at query time either way. Compare both by cross-validation at the chosen tree size, with a pointwise regression on the grades beside them:

Example `lambdamart-choices-on-train` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Compares three ways of training on the train queries, each by cross-validation: LambdaRank with unjudged candidates as 0,
LambdaRank on judged candidates only, and pointwise regression. The prose's point rests on the differences and the
permutation p-values printed under each setup."""
from lightgbm import LGBMRanker, LGBMRegressor

from lib.metrics import evaluate
from lib.ranking import DETERMINISTIC, FEATURES, LAMBDARANK, TREES, cross_validate, feature_table
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # tuning: train queries only
candidates = feature_table(load_products(), queries)
candidates["grade or 0"] = candidates["grade"].fillna(0).astype(int)  # unjudged counts as irrelevant
# the rows the model learns from when unjudged candidates are left out; it still ranks every candidate at query time
judged_only = candidates.dropna(subset=["grade"]).astype({"grade": int})

setups = {                                                          # (model, rows it learns from, label)
    "lambdarank, unjudged as 0": (lambda: LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), candidates, "grade or 0"),
    "lambdarank, unjudged left out": (lambda: LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), judged_only, "grade"),
    "pointwise regression, unjudged as 0": (lambda: LGBMRegressor(**TREES, **DETERMINISTIC), candidates, "grade or 0"),
}
semantic = evaluate(SemanticSearch().run(queries, k=100), judgments)["ndcg@10"]
print(f"semantic, train ndcg@10: {semantic.mean():.3f}")
scores = {name: cross_validate(model, rows, candidates, label, FEATURES, judgments)
          for name, (model, rows, label) in setups.items()}
chosen = scores["lambdarank, unjudged as 0"]
for name, per_query in scores.items():
    print(f"{name}, cross-validated ndcg@10: {per_query.mean():.3f}")
    if name != "lambdarank, unjudged as 0":
        # the mean difference is the first argument minus the second, tested by permutation over the queries
        result = compare(per_query, chosen)
        print(f"{name}, minus the first: {result['mean difference']:.3f}")
        print(f"{name}, minus the first, permutation p: {result['permutation p']:.3f}")
result = compare(chosen, semantic)
print(f"first setup minus semantic: {result['mean difference']:.3f}")
print(f"first setup minus semantic, permutation p: {result['permutation p']:.3f}")
```

Output:

```text
semantic, train ndcg@10: 0.772
lambdarank, unjudged as 0, cross-validated ndcg@10: 0.798
lambdarank, unjudged left out, cross-validated ndcg@10: 0.733
lambdarank, unjudged left out, minus the first: -0.064
lambdarank, unjudged left out, minus the first, permutation p: 0.005
pointwise regression, unjudged as 0, cross-validated ndcg@10: 0.769
pointwise regression, unjudged as 0, minus the first: -0.029
pointwise regression, unjudged as 0, minus the first, permutation p: 0.007
first setup minus semantic: 0.026
first setup minus semantic, permutation p: 0.242
```

Counting unjudged candidates as 0 scores higher than leaving them out, 0.798 against 0.733, a difference of -0.064 with a permutation p-value of 0.005. A model that never sees an unjudged candidate in training still has to rank them, and [the features](#ranking-features) say they look like irrelevant products.

Pointwise regression scores 0.769, a difference of -0.029 (p = 0.007), so on the store's train queries a [tuning check against a pointwise model](#learn-from-pairs) favours LambdaMART.

Against semantic retrieval's 0.772, the chosen setup differs by 0.026, with a permutation p-value of 0.242: even on the queries that chose it, it shows no gain the train queries can tell from chance.

**Working rule:** Sort rows by query and pass `group`, set `label_gain` to the gains your metric uses, stop early on held-out train queries through `eval_X` and `eval_y`, and fix the seed and thread count. Order each query's candidates by product ID, as chapter 3 advises, and break score ties the same way. Count unjudged candidates as grade 0 unless cross-validation on train queries says otherwise. With few judged queries, try small trees.

## Report LambdaMART on the test queries {#lambdamart-on-test-queries}

A model tuned on train queries is reported once on the test queries, by a comparison planned before looking. **Feature importance** shows what it learned: LightGBM's `"gain"` importance is the "total gains of splits which use the feature" ([`Booster`](https://lightgbm.readthedocs.io/en/v4.7.0/pythonapi/lightgbm.Booster.html)), so a feature with no gain plays no part in the score.

The first [planned comparison](#ranking) uses the setup [chosen on train](#train-lambdamart): [LambdaMART](#learn-from-pairs) on all the [features](#ranking-features), with 3 leaves at a learning rate of 0.1, unjudged candidates as grade 0, and candidates in `product_id` order. It fits on 40 train queries, stops early on 10 others, and ranks each test query's candidates. A gain needs a permutation p-value below 0.01:

Example `lambdamart-on-test` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Fits LambdaMART on the train queries with the chosen setup, reports its early stopping and gain shares, then reports its
planned comparison on the test queries against semantic retrieval. The prose's point rests on that comparison's permutation
p-value, printed last, against the threshold printed first."""
from lightgbm import LGBMRanker

from lib.metrics import evaluate
from lib.ranking import (DETERMINISTIC, FEATURES, LAMBDARANK, PLANNED_TEST_COMPARISONS, THRESHOLD, TREES, feature_table,
                         fit, ranked, report_planned, stopping_split)
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, train, test = load_products(), load_queries("train"), load_queries("test")
print(f"planned test comparisons: {len(PLANNED_TEST_COMPARISONS)}")
print(f"p-value threshold: {THRESHOLD:.2f}")

table = feature_table(products, train)
table["grade or 0"] = table["grade"].fillna(0).astype(int)            # the setup chosen on train
# 10 train queries are held out, at random with a fixed seed, to stop on
fit_ids, stop_ids = stopping_split(train.index)
model = fit(LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), table, "grade or 0", FEATURES, fit_ids, stop_ids)
print(f"queries fitted: {len(fit_ids)}\nqueries held out for stopping: {len(stop_ids)}")
curve = model.evals_result_["valid_0"]["ndcg@10"]                     # LightGBM's nDCG@10, one value per tree
print(f"trees tried: {len(curve)}\ntrees kept by early stopping: {model.best_iteration_}")
print(f"stopping queries' ndcg@10, first tree: {curve[0]:.3f}")
# best_iteration_ counts trees from 1 and the curve from 0, so the last tree kept is at index best_iteration_ - 1
print(f"stopping queries' ndcg@10, trees kept: {curve[model.best_iteration_ - 1]:.3f}")
gain = model.booster_.feature_importance(importance_type="gain")      # total gain of the splits on each feature
# a feature with no gain was never split on, so it plays no part in the score
print(f"features the trees use: {(gain > 0).sum()} of {len(FEATURES)}")
for name, share in sorted(zip(FEATURES, gain / gain.sum()), key=lambda pair: -pair[1]):
    print(f"share of gain, {name}: {share:.3f}")

candidates, judgments = feature_table(products, test), qrels("test")   # test queries: read once, to report
after = evaluate(ranked(candidates, model.predict(candidates[FEATURES])), judgments)
before = evaluate(SemanticSearch().run(test, k=100), judgments)
for name, frame in [("semantic", before), ("lambdamart", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    # each query's top 10 is 10 places, so (1 - judged@10) times 10 counts its unjudged places
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
report_planned("lambdamart", after["ndcg@10"], before["ndcg@10"])
```

Output:

```text
planned test comparisons: 5
p-value threshold: 0.01
queries fitted: 40
queries held out for stopping: 10
trees tried: 243
trees kept by early stopping: 213
stopping queries' ndcg@10, first tree: 0.568
stopping queries' ndcg@10, trees kept: 0.794
features the trees use: 8 of 8
share of gain, cross_encoder: 0.641
share of gain, similarity: 0.172
share of gain, name_match: 0.097
share of gain, bm25: 0.043
share of gain, review_count: 0.021
share of gain, rating_count: 0.021
share of gain, attribute_match: 0.002
share of gain, average_rating: 0.001
semantic, test ndcg@10: 0.830
semantic, test judged@10: 0.990
semantic, unjudged places in the test top 10s: 3
lambdamart, test ndcg@10: 0.817
lambdamart, test judged@10: 0.990
lambdamart, unjudged places in the test top 10s: 3
lambdamart, mean difference: -0.012
lambdamart, wins, losses, ties: 14, 12, 4
lambdamart, permutation p: 0.260
lambdamart, established at 0.01: no
lambdamart, t-test p: 0.278
lambdamart, t-test agrees: yes
lambdamart, 99% interval: -0.044 to 0.011
lambdamart, interval agrees: yes
```

Of 243 trees tried, early stopping keeps 213. On the queries held out for stopping, LightGBM's own nDCG@10, whose ideal comes from their candidates alone, rises from 0.568 after the first tree to 0.794 at the trees kept.

The trees use 8 of 8 features, but they lean on the cross-encoder, which takes a share of 0.641 of the gain, ahead of `similarity` at 0.172, `name_match` at 0.097 and `bm25` at 0.043. So serving the model means a cross-encoder call for every candidate.

LambdaMART doesn't establish a gain on the test queries: it scores 0.817 nDCG@10, against semantic retrieval's 0.830, at a permutation p-value of 0.260 ([all five comparisons](#ranking-decisions)). [Judged@10](#score-every-test-query) is 0.990 for LambdaMART and 0.990 for semantic retrieval.

**Working rule:** Adopt a learned ranker only when its planned test comparison is established. Read its gain importance before you trust it, because the features it leans on are the ones you'll pay for at query time. Early stopping on a few held-out queries keeps very different numbers of trees from one split to the next, from 99, 20, 8, 43, 38 across the cross-validation folds to 213 here. A rule of thumb, not a measurement: with this few queries, judge more queries before you tune further, and treat any one stopping point as noise.

## Rerank semantic retrieval with a cross-encoder {#rerank-semantic-with-cross-encoder}

[Semantic retrieval](#search-by-meaning) uses an embedding model, also called a **bi-encoder**, which reads the query and each product separately, so product embeddings are computed ahead of time. A **cross-encoder** reads the query and one product together and outputs one score ([Nogueira and Cho, 2019](https://arxiv.org/abs/1901.04085)). It can relate every query word to every product word, and it pays for that. It is often slower than a Sentence Transformer model, because it computes for each pair rather than each text, and so "Cross Encoders are often used to re-rank the top-k results" ([Sentence Transformers](https://sbert.net/docs/cross_encoder/usage/usage.html)). The store's cross-encoder ([see the opening](#ranking)) is small for a language model, with 149M parameters ([model card](https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base)). It is the open model `Alibaba-NLP/gte-reranker-modernbert-base`, whose **manifest**, the file saved with its recording, gives its licence as Apache-2.0. We chose it because anyone can download it and rerun the recording. `recordings/cross_encoder.py` scored the union of BM25's and semantic retrieval's top 100 for every query (for two queries, its semantic list differs from `lib.semantic`'s by a near-tie at the 100th place).

[Chapter 1](#rerank-with-cross-encoder) reranked the hybrid run. Here the cross-encoder reranks the ranker to beat, semantic retrieval's top 20: the same products the [LLM rerankers](#llm-pointwise-reranking) read, so the chapter's three rerankers start from identical lists. The chapter fixed that depth before any test result, and doesn't tune it. Reorder the top 20 by the recorded scores and keep the rest in place. That is the second [planned comparison](#ranking), which needs a p-value below 0.01:

Example `cross-encoder-on-semantic` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Reranks semantic retrieval's top 20 with the recorded cross-encoder scores, and compares the two on the test queries.
The prose's point rests on the planned comparison's permutation p-value, and on the judged@10 lines, which show what the
rerank does to the judgments it can score."""
from lib.metrics import evaluate
from lib.ranking import DEPTH, rerank, report_planned
from lib.recorded import cross_encoder_scores, llm_listwise, manifest
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")       # scored on the human judgments
semantic = SemanticSearch().run(queries, k=100)
recorded = cross_encoder_scores()
# the recorded score of each (query, product) pair
score = dict(zip(zip(recorded["query_id"], recorded["product_id"]), recorded["score"]))
print("cross-encoder model:", manifest("cross-encoder")["model"])
print("licence in the manifest:", manifest("cross-encoder")["model_licence"])

# the set of products the LLM was shown for each query, from the listwise recording
shown = llm_listwise().groupby("query_id")["product_id"].apply(set)  # what the LLM rerankers saw
same = sum(set(semantic[query_id][:DEPTH]) == shown[query_id] for query_id in queries.index)
print(f"rerank depth: {DEPTH}")
print(f"queries whose top {DEPTH} holds the products the llm rerankers saw: {same} of {len(queries)}")

reranked = rerank(semantic, score, DEPTH)                       # top 20 reordered, the rest in place
before, after = evaluate(semantic, judgments), evaluate(reranked, judgments)
for name, frame in [("semantic", before), ("cross-encoder", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
# index 0 is the first place
moved = sum(reranked[query_id][0] != semantic[query_id][0] for query_id in queries.index)
print(f"queries whose first product changes: {moved}")
report_planned("cross-encoder", after["ndcg@10"], before["ndcg@10"])
```

Output:

```text
cross-encoder model: Alibaba-NLP/gte-reranker-modernbert-base
licence in the manifest: Apache-2.0
rerank depth: 20
queries whose top 20 holds the products the llm rerankers saw: 30 of 30
semantic, test ndcg@10: 0.830
semantic, test judged@10: 0.990
semantic, unjudged places in the test top 10s: 3
cross-encoder, test ndcg@10: 0.813
cross-encoder, test judged@10: 0.983
cross-encoder, unjudged places in the test top 10s: 5
queries whose first product changes: 23
cross-encoder, mean difference: -0.016
cross-encoder, wins, losses, ties: 11, 12, 7
cross-encoder, permutation p: 0.178
cross-encoder, established at 0.01: no
cross-encoder, t-test p: 0.171
cross-encoder, t-test agrees: yes
cross-encoder, 99% interval: -0.058 to 0.006
cross-encoder, interval agrees: yes
```

Reranking the top 20 doesn't establish a gain: the rerank scores 0.813 against 0.830, with a permutation p-value of 0.178 (see [the decisions table](#ranking-decisions)). The top 20 holds the products the LLM rerankers saw for 30 of 30 test queries, and the reranker changes the first product for 23 of them.

[Judged@10](#score-every-test-query) falls from 0.990 to 0.983, and the unjudged places in the test top 10s go from 3 to 5.

On the train queries, the same rerank scores 0.802 against semantic retrieval's 0.772 ([depth sweep](#rerank-depth-from-budget)). The train queries are another sample, and their verdict repeats what [chapter 3](#split-changes-the-verdict) found: two close rankers' order can flip between sets of queries.

**Working rule:** Rerank your strongest retrieval, at a depth fixed before you look at test results, and adopt the reranker only on an established gain on held-out queries. The store's general-purpose cross-encoder stays out of the pipeline.

## Score each product with an LLM {#llm-pointwise-reranking}

An LLM can rerank too, in three ways. **Pointwise**, it judges each product alone and returns a label or a score. **Pairwise**, it says which of two products fits the query better. **Listwise**, it orders a whole list in one answer ([Qin et al., 2024](https://arxiv.org/abs/2306.17563)). In one study, on eight datasets from BEIR, a collection of retrieval benchmarks used to test models on data they weren't trained for, pointwise prompts did better with graded answers than with yes or no, because "the lack of intermediate relevance label options may cause the LLM to provide noisy or biased answers" ([Zhuang et al., 2024a](https://arxiv.org/abs/2310.14122)).

The store's LLM, the open model named in [the chapter's opening](#ranking), saw the query and one product at a time: name, class, category, description and attributes ([what the LLM saw](#what-the-llm-saw)). The prompt asks for a label, `exact`, `partial` or `irrelevant`, and "a score from 0 to 100 for how well it matches". Reorder [semantic retrieval](#search-by-meaning)'s top 20 by that score; when two products tie, they keep semantic retrieval's order, a rule fixed with the recording. That reorder is the third [planned comparison](#ranking), held to a p-value below 0.01:

Example `llm-pointwise-rerank` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Reads the pointwise LLM's answers for the test queries, one call per product, and reranks semantic retrieval's top 20 by
their scores. The prose's point rests on the distinct-scores line, which shows how coarse the scores are, and on the
planned comparison's p-value."""
from lib.metrics import evaluate
from lib.ranking import DEPTH, rerank, report_planned
from lib.recorded import llm_pointwise, manifest
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")       # scored on the human judgments, not the LLM's
semantic = SemanticSearch().run(queries, k=100)
answers = llm_pointwise()                                       # one call per product: a label and a score
print("llm:", manifest("llm-rerank")["model"])
print("licence in the manifest:", manifest("llm-rerank")["model_licence"])
print(f"calls per query: {len(answers) // answers['query_id'].nunique()}")
print(f"answers without a score: {answers['score'].isna().sum()}")
print(f"distinct scores per query, median: {answers.groupby('query_id')['score'].nunique().median():.0f}")
print(f"share of products scored 100: {(answers['score'] == 100).mean():.3f}")
# each answered product's human grade, or missing when nobody judged it
people = answers.apply(lambda row: judgments[row["query_id"]].get(row["product_id"]), axis=1)
# grades 2, 1 and 0 are exact, partial and irrelevant, the labels the LLM was asked for
for label, grade in [("exact", 2), ("partial", 1), ("irrelevant", 0)]:
    print(f"products the llm labels {label}: {(answers['label'] == label).sum()}")
    print(f"products people judged {label}: {(people == grade).sum()}")
print(f"products nobody judged: {people.isna().sum()}")

score = dict(zip(zip(answers["query_id"], answers["product_id"]), answers["score"]))
reranked = rerank(semantic, score, DEPTH)                       # equal scores keep semantic retrieval's order
counts = answers.groupby("query_id")["score"].value_counts()          # products per score, for each query
shared = {query_id: sum(counts[(query_id, score[(query_id, product_id)])] > 1 for product_id in reranked[query_id][:10])
          for query_id in queries.index}                                # top-10 products that share their score
# more than 5 of the top 10 share a score: most of the list is decided by the tie-break
print(f"queries where most of the reranked top 10 shares its score: {sum(n > 5 for n in shared.values())}")
before, after = evaluate(semantic, judgments), evaluate(reranked, judgments)
for name, frame in [("semantic", before), ("llm pointwise", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
report_planned("llm pointwise", after["ndcg@10"], before["ndcg@10"])
```

Output:

```text
llm: gemma4:12b-it-q4_K_M
licence in the manifest: Apache-2.0
calls per query: 20
answers without a score: 0
distinct scores per query, median: 4
share of products scored 100: 0.390
products the llm labels exact: 251
products people judged exact: 310
products the llm labels partial: 345
products people judged partial: 265
products the llm labels irrelevant: 4
products people judged irrelevant: 7
products nobody judged: 18
queries where most of the reranked top 10 shares its score: 30
semantic, test ndcg@10: 0.830
semantic, test judged@10: 0.990
semantic, unjudged places in the test top 10s: 3
llm pointwise, test ndcg@10: 0.837
llm pointwise, test judged@10: 0.983
llm pointwise, unjudged places in the test top 10s: 5
llm pointwise, mean difference: 0.008
llm pointwise, wins, losses, ties: 11, 8, 11
llm pointwise, permutation p: 0.241
llm pointwise, established at 0.01: no
llm pointwise, t-test p: 0.244
llm pointwise, t-test agrees: yes
llm pointwise, 99% interval: -0.007 to 0.026
llm pointwise, interval agrees: yes
```

The recording made 20 calls per query, and 0 answers came back without a score. The scores are coarse. The median query gets 4 distinct scores for its 20 products, and a share of 0.390 of all products score 100. In 30 queries, most of the reranked top 10 shares its score with another product, so the tie-break, semantic retrieval's order, decides much of the list.

With this prompt, on these lists, the LLM calls fewer products exact than people did:

| Label | LLM | People |
| --- | --- | --- |
| exact | 251 | 310 |
| partial | 345 | 265 |
| irrelevant | 4 | 7 |
| nobody judged | – | 18 |

On these lists that holds, but [chapter 4](#read-llm-error-direction) shows that the direction of an LLM's disagreement with people changes with the pairs judged and the prompt, so don't carry this one elsewhere.

The pointwise rerank doesn't establish a gain either: it scores 0.837 against 0.830, at a permutation p-value of 0.241 (see [the decisions table](#ranking-decisions)).

The LLM's order puts more unjudged products into the top 10s: 5 places instead of 3, and [judged@10](#score-every-test-query) falls from 0.990 to 0.983.

**Working rule:** If you rerank pointwise with an LLM, ask for a graded label or a score, count the distinct scores it gives per query, and decide the tie-break in advance: retrieval's order is a safe default. Score the result with human judgments, never with the same LLM's grades.

## Order the 20 products with one LLM prompt {#llm-listwise-reranking}

The third way, a [listwise](#llm-pointwise-reranking) prompt, numbers the candidates and asks the LLM to return the numbers in order of relevance. RankGPT introduced this as permutation generation ([Sun et al., 2023](https://arxiv.org/abs/2304.09542)). A prompt can hold only so many products, so a long list is reranked in a **sliding window**: RankGPT reranks BM25's top 100 with "a window size of 20 and step size of 10", from the bottom of the list up (sections 3.2 and 6.1). The answer has to be a valid ordering, and that can fail: with moderate LLMs of 2023, such as the 20-billion-parameter Flan-UL2, listwise prompts nearly always fail, through missing, repeated or refused rankings ([Qin et al., 2024](https://arxiv.org/abs/2306.17563)).

The store's [LLM](#ranking) saw 20 products per prompt, one window. The prompt shows each product as a short line: name, class, attributes and the first 160 characters of the description. Its last instruction reads: "Order all 20 products from the best match for the query to the worst. Return the product numbers, each exactly once, in JSON." The JSON schema requires exactly 20 numbers, but not 20 different ones, so the recording repairs any answer with a repeated or missing number and flags it. Reorder [semantic retrieval](#search-by-meaning)'s top 20 by the answer the LLM gave when shown them in semantic order. That rerank is the fourth [planned comparison](#ranking), held to a p-value below 0.01:

Example `llm-listwise-rerank` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Reads the listwise LLM's answers for the test queries, in both orders, and reranks semantic retrieval's top 20 by the
answer given in semantic order. The prose's point rests on the planned comparison's p-value, and on the repair count,
which shows how many answers needed a fix."""
from lib.metrics import evaluate
from lib.ranking import DEPTH, report_planned
from lib.recorded import llm_listwise, manifest
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")       # scored on the human judgments, not the LLM's
semantic = SemanticSearch().run(queries, k=100)
answers = llm_listwise()                                        # one call per query and order shown
# the answers hold one row per product, so keep one row per call: one call per query and order
calls = answers.drop_duplicates(["query_id", "order"])
print(f"listwise calls, both orders: {len(calls)}")
# valid is false where the recording repaired a repeated or missing number
print(f"answers that needed repair: {(~calls['valid']).sum()}")
print(f"products per call: {answers.groupby(['query_id', 'order']).size().max()}")
print("prompt asks for:", manifest("llm-rerank")["prompts"]["listwise"].splitlines()[-1].replace("{n}", str(DEPTH)))

shown_in_semantic_order = answers[answers["order"] == "semantic"].sort_values(["query_id", "position"])
order = shown_in_semantic_order.groupby("query_id")["product_id"].apply(list)
# the reranked top 20, then the rest of semantic retrieval's list in place: ranking[DEPTH:] starts at the 21st product
reranked = {query_id: order[query_id] + ranking[DEPTH:] for query_id, ranking in semantic.items()}
before, after = evaluate(semantic, judgments), evaluate(reranked, judgments)
for name, frame in [("semantic", before), ("llm listwise", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
moved = sum(reranked[query_id][0] != semantic[query_id][0] for query_id in queries.index)
print(f"queries whose first product changes: {moved}")
report_planned("llm listwise", after["ndcg@10"], before["ndcg@10"])
```

Output:

```text
listwise calls, both orders: 60
answers that needed repair: 0
products per call: 20
prompt asks for: Order all 20 products from the best match for the query to the worst. Return the product numbers, each exactly once, in JSON.
semantic, test ndcg@10: 0.830
semantic, test judged@10: 0.990
semantic, unjudged places in the test top 10s: 3
llm listwise, test ndcg@10: 0.819
llm listwise, test judged@10: 0.983
llm listwise, unjudged places in the test top 10s: 5
queries whose first product changes: 19
llm listwise, mean difference: -0.010
llm listwise, wins, losses, ties: 12, 12, 6
llm listwise, permutation p: 0.580
llm listwise, established at 0.01: no
llm listwise, t-test p: 0.498
llm listwise, t-test agrees: yes
llm listwise, 99% interval: -0.070 to 0.016
llm listwise, interval agrees: yes
```

The recording made 60 listwise calls, two per test query, and 0 answers needed repair. The rerank changes the first product for 19 queries.

The listwise rerank's gain isn't established: it scores 0.819 against 0.830, at a permutation p-value of 0.580 ([all five comparisons](#ranking-decisions)).

[Judged@10](#score-every-test-query) falls here too, from 0.990 to 0.983, with 5 unjudged places where semantic retrieval has 3.

**Working rule:** Check every listwise answer before you use it: count missing, repeated and unknown numbers, and log how many answers needed repair. Constrain the answer's shape with a schema when your runtime supports one. Fix the window, the step and the order you show the products in before you measure, because the order changes the answer, as the [next check](#llm-position-bias) shows.

## Reverse the input to measure positional bias {#llm-position-bias}

A [listwise answer](#llm-listwise-reranking) can suffer from **positional bias**: an LLM's tendency to let a product's place in the prompt affect its rank, not the click [position bias](#clicks-are-not-judgments) of shoppers. "Large language models (LLMs) exhibit positional bias in how they use context, which especially complicates listwise ranking" ([Tang et al., 2024](https://arxiv.org/abs/2310.07712)). On TREC DL19, the 2019 queries of TREC's Deep Learning track, a passage-ranking benchmark, gpt-3.5-turbo reranked BM25's top 100 to an nDCG@10 of 65.80 when shown BM25's order, 32.77 when shown it reversed and 25.17 when shown a random order ([Sun et al., 2023, Table 5](https://arxiv.org/abs/2304.09542)). The direct check is to show the same products in two orders and compare the answers. **Kendall's tau** measures how alike two orderings are, from 1 for the same order to −1 for the reverse, by counting the pairs they put the same way round ([chapter 4](#system-order-human-versus-llm)).

The recording sent each test query's listwise prompt to the [same LLM](#ranking) twice. The first prompt showed [semantic retrieval](#search-by-meaning)'s top 20 in semantic order, as the [listwise rerank](#llm-listwise-reranking) used; the second showed them reversed. Out of the 30 test queries, how often will the LLM put the same product first both times? Write your number down.

Example `listwise-position-bias` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Shows the listwise LLM the same test products in two orders, and measures how far its answers agree and how far each
answer follows the order it was shown. The prose's point rests on the mean tau between the two answers, and on the two
taus between each answer and its own input order."""
import numpy as np
from scipy.stats import kendalltau

from lib.metrics import evaluate
from lib.ranking import DEPTH
from lib.recorded import llm_listwise
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
semantic = SemanticSearch().run(queries, k=DEPTH)               # the order the first prompt showed
answers = llm_listwise().sort_values(["query_id", "order", "position"])
# the products in the order the LLM returned them, for each query and each order shown
answer = {key: list(group["product_id"]) for key, group in answers.groupby(["query_id", "order"])}

def tau(first: list, second: list) -> float:
    """Kendall's tau between two orderings of the same products."""
    place = {product_id: rank for rank, product_id in enumerate(second)}    # each product's place in the second ordering
    # the first ordering's positions, against where the second ordering puts each product
    return kendalltau(range(len(first)), [place[product_id] for product_id in first]).statistic

between, shown_semantic, shown_reversed, overlap, same_first = [], [], [], [], 0
for query_id, shown in semantic.items():
    forward, backward = answer[(query_id, "semantic")], answer[(query_id, "reversed")]
    between.append(tau(forward, backward))
    shown_semantic.append(tau(forward, shown))
    shown_reversed.append(tau(backward, shown[::-1]))     # the reversed input, as the second prompt showed it
    overlap.append(len(set(forward[:10]) & set(backward[:10])))
    same_first += forward[0] == backward[0]               # index 0 is the first place
print(f"test queries: {len(semantic)}")
print(f"tau between the two answers, mean: {np.mean(between):.3f}")
print(f"tau between the two answers, lowest: {min(between):.3f}\ntau between the two answers, highest: {max(between):.3f}")
print(f"top-10 products in common, mean: {np.mean(overlap):.3f}")
print(f"top-10 products in common, fewest: {min(overlap)}")
print(f"queries with the same first product: {same_first}")
print(f"share of queries with the same first product: {same_first / len(semantic):.3f}")
print(f"tau between the order shown and the answer, semantic order: {np.mean(shown_semantic):.3f}")
print(f"tau between the order shown and the answer, reversed order: {np.mean(shown_reversed):.3f}")
# an answer that ignored the order would repeat itself, so its tau with the reversed input is minus its tau with the semantic order
print(f"the same, if the order shown made no difference: {-np.mean(shown_semantic):.3f}")
reversed_run = {query_id: answer[(query_id, "reversed")] for query_id in semantic}
print(f"reversed answer, test ndcg@10, not a planned comparison: {evaluate(reversed_run, judgments)['ndcg@10'].mean():.3f}")
```

Output:

```text
test queries: 30
tau between the two answers, mean: 0.311
tau between the two answers, lowest: -0.484
tau between the two answers, highest: 0.811
top-10 products in common, mean: 6.967
top-10 products in common, fewest: 3
queries with the same first product: 13
share of queries with the same first product: 0.433
tau between the order shown and the answer, semantic order: 0.414
tau between the order shown and the answer, reversed order: 0.045
the same, if the order shown made no difference: -0.414
reversed answer, test ndcg@10, not a planned comparison: 0.826
```

The same product comes first for 13 of the 30 queries, so the expectation that a capable model finds the same best match whichever way the list comes holds for only a share of 0.433 of the queries.

The two answers agree with a mean tau of 0.311, and per query the tau runs from -0.484 to 0.811. Their top 10s share 6.967 products on average, as few as 3.

The answers also lean toward the order shown. Each answer's tau against its own input order is 0.414 for the semantic order and 0.045 for the reversed one. An LLM that ignored the order would give the same answer both times, so its reversed answer would have a tau of -0.414 against the reversed input. The reversed answer sits far nearer its own input order than that: positional bias, for this model, prompt and these queries. The reversed answer scores 0.826 nDCG@10; it is not a planned comparison, so the chapter doesn't test it.

Three remedies exist. Pairwise ranking prompting asks the LLM about each pair twice, once in each order, and counts a disagreement as a tie ([Qin et al., 2024](https://arxiv.org/abs/2306.17563)). Permutation self-consistency reranks several shuffled orders and aggregates the answers, which raised scores by up to 7 to 18% for GPT-3.5 and 8 to 16% for LLaMA v2 (70B) (Tang et al., 2024). And rerankers fine-tuned for listwise ranking, such as the open RankZephyr, are reported to be "resilient against variations in initial document ordering" ([Pradeep et al., 2023](https://arxiv.org/abs/2312.02724)); the store didn't record one.

**Working rule:** Before you trust a listwise LLM reranker, run each query in at least two orders and report how much the answers agree. When agreement is low, aggregate several orders or ask each pair in both orders, and count those calls against [your budget](#rerank-depth-from-budget). In production, show the products in retrieval's order every time, so that the same list at least gets the same answer.

## Set the rerank depth from a budget {#rerank-depth-from-budget}

A search pipeline runs in stages, each slower and given fewer candidates than the last, and every reranker in this chapter adds one. Multi-stage rankers offer "the ability to trade off quality against latency by controlling the admission of candidates into each pipeline stage" ([Nogueira et al., 2019](https://arxiv.org/abs/1910.14424)). So the **rerank depth**, how many products the reranker reads per query, is a budget decision. Timings vary with hardware and running-time choices ([Peng et al., 2025](https://arxiv.org/abs/2507.06223)), so this section counts what drives them instead: model calls and the text they read, per query, multiplied by the model's size. The store's cross-encoder has 149M parameters ([model card](https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base)), and its LLM about 12 billion ([model card](https://ai.google.dev/gemma/docs/core/model_card_4)), some 80 times as many.

At depth 20, count each reranker's model calls and the characters it reads per test query, from the products' text and the recorded prompts, plus the calls two designs the store didn't record would need:

Example `reranker-prompt-sizes` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Counts the characters each reranker reads per test query at depth 20, from the products' text and the recorded prompts,
and the model calls each design makes. The prose's point rests on the characters and calls lines, and on the two designs
the store didn't record."""
import numpy as np

from lib.agreement import as_the_llm_saw
from lib.ranking import DEPTH, listwise_line
from lib.recorded import manifest
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text

products, queries = load_products(), load_queries("test")
semantic = SemanticSearch().run(queries, k=DEPTH)                # the 20 products each reranker reads
prompts, text = manifest("llm-rerank")["prompts"], product_text(products)

cross_encoder, pointwise, listwise = [], [], []                  # characters read per query
for query_id, query in queries["query"].items():
    shown = products.loc[semantic[query_id]]
    # one call per product, each reading the query and that product's text together
    cross_encoder.append(sum(len(query) + len(text[product_id]) for product_id in semantic[query_id]))
    # the pointwise prompt, filled in with the query and the product as the LLM saw it
    pointwise.append(sum(len(prompts["pointwise"].format(query=query, product=as_the_llm_saw(product)))
                         for _, product in shown.iterrows()))
    # products numbered from 1, as the listwise prompt shows them
    lines = "\n".join(f"[{number}] {listwise_line(product)}" for number, (_, product) in enumerate(shown.iterrows(), 1))
    listwise.append(len(prompts["listwise"].format(query=query, products=lines, n=DEPTH)))

# the cross-encoder and the pointwise LLM make one call per product; the listwise LLM makes one call per query
for name, calls, characters in [("cross-encoder", DEPTH, cross_encoder), ("llm pointwise", DEPTH, pointwise),
                                ("llm listwise", 1, listwise)]:
    print(f"{name}, model calls per query: {calls}")
    print(f"{name}, characters read per query, mean: {np.mean(characters):,.0f}")
print(f"llm pairwise, every pair in both orders, calls per query: {DEPTH * (DEPTH - 1)}")
# a sliding window of 20 products, moved 10 at a time: its starts are list positions 0, 10, ..., 80
window, step, depth = 20, 10, 100                                # a sliding window over a deeper list
print(f"llm listwise over the top {depth}, window {window}, step {step}, calls per query: {(depth - window) // step + 1}")
```

Output:

```text
cross-encoder, model calls per query: 20
cross-encoder, characters read per query, mean: 9,911
llm pointwise, model calls per query: 20
llm pointwise, characters read per query, mean: 17,864
llm listwise, model calls per query: 1
llm listwise, characters read per query, mean: 5,973
llm pairwise, every pair in both orders, calls per query: 380
llm listwise over the top 100, window 20, step 10, calls per query: 9
```

| Reranker, top 20 | Model calls per query | Characters read per query |
| --- | --- | --- |
| Cross-encoder | 20 | 9,911 |
| LLM, pointwise | 20 | 17,864 |
| LLM, listwise | 1 | 5,973 |

Pointwise repeats the instructions and shows each product in full, so it reads the most text, in independent calls. Listwise reads the least, in one call, but must write out 20 numbers in order. Pairwise prompting over all pairs in both orders would take 380 calls per query, and RankGPT's sliding window over a top 100 would take 9. In one published measurement on [TREC DL19](#llm-position-bias), reranking BM25's top 100 with Flan-T5-XL on one RTX A6000 GPU, pointwise yes-or-no prompting scored 0.650 nDCG@10 at 1.5 seconds per query, and pairwise prompting over all pairs 0.713 at 254.9 seconds, with 9,900 LLM calls ([Zhuang et al., 2024b](https://arxiv.org/abs/2310.09497)). [LambdaMART](#lambdamart-on-test-queries) with the cross-encoder as a feature needs a cross-encoder score for every candidate, a median of 131 pairs per query.

For the cross-encoder, cost grows in step with depth, so the question is where quality stops growing. Sweep the depth on the train queries:

Example `rerank-depth-on-train` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Reranks semantic retrieval's top 5 to 75 with the recorded cross-encoder scores, on the train queries, and prints nDCG@10
at each depth. The prose's point rests on the change from the depth before, which shows where the gain flattens and then
falls."""
from lib.metrics import evaluate
from lib.ranking import rerank
from lib.recorded import cross_encoder_scores
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")      # choosing a depth is tuning: train queries
semantic = SemanticSearch().run(queries, k=100)
recorded = cross_encoder_scores()
# the recorded cross-encoder score of each (query, product) pair
score = dict(zip(zip(recorded["query_id"], recorded["product_id"]), recorded["score"]))
train_pairs = recorded[recorded["query_id"].isin(queries.index)]

print(f"depth 0 (semantic alone), train ndcg@10: {evaluate(semantic, judgments)['ndcg@10'].mean():.3f}")
previous = round(evaluate(semantic, judgments)["ndcg@10"].mean(), 3)     # changes between the printed values
for depth in [5, 10, 20, 30, 50, 75]:
    mean = round(evaluate(rerank(semantic, score, depth), judgments)["ndcg@10"].mean(), 3)
    print(f"depth {depth}, train ndcg@10: {mean:.3f}")
    print(f"depth {depth}, change from the depth before: {mean - previous:+.3f}")
    previous = mean
# every candidate needs its own cross-encoder score, so this counts the recorded pairs per query
print(f"pairs per query to score every candidate, median: {train_pairs.groupby('query_id').size().median():.0f}")
```

Output:

```text
depth 0 (semantic alone), train ndcg@10: 0.772
depth 5, train ndcg@10: 0.782
depth 5, change from the depth before: +0.010
depth 10, train ndcg@10: 0.784
depth 10, change from the depth before: +0.002
depth 20, train ndcg@10: 0.802
depth 20, change from the depth before: +0.018
depth 30, train ndcg@10: 0.804
depth 30, change from the depth before: +0.002
depth 50, train ndcg@10: 0.793
depth 50, change from the depth before: -0.011
depth 75, train ndcg@10: 0.788
depth 75, change from the depth before: -0.005
pairs per query to score every candidate, median: 131
```

The cross-encoder's gain flattens between 20 and 30, near the depth fixed to match the LLM recording. From semantic retrieval's 0.772, reranking the top 5 gives 0.782 and the top 20 0.802. The top 30 adds +0.002 for half as many pairs again. Deeper, it falls: 0.793 at 50 and 0.788 at 75.

On test, [the depth-20 rerank](#rerank-semantic-with-cross-encoder) didn't establish a gain, so for the store the cheapest reranker, none, is also the one to keep.

**Working rule:** For each reranker you consider, count calls and characters per query at each depth, and set the depth on train queries. A rule of thumb, not a measurement: rerank only as deep as the depth where train nDCG@10 stops improving, because every product past it costs the same and adds nothing. Then time that configuration on your own hardware and traffic, and keep the stage only if it fits the latency budget.

## Distill the cross-encoder into a small ranker {#distill-the-cross-encoder}

A reranker too slow for [the budget](#rerank-depth-from-budget) can teach a fast one. **Distillation** trains a small model, the **student**, to imitate a large one, the **teacher**. Hinton et al. describe it as distilling an ensemble's knowledge into a single model ([Hinton et al., 2015](https://arxiv.org/abs/1503.02531)). In ranking, the teacher's scores become the student's labels. When the two models' scores differ in size, as scores from different architectures often do, the student can learn the margin between two products' scores instead, with a loss called Margin-MSE ([Hofstätter et al., 2020](https://arxiv.org/abs/2010.02666)). Distillation also runs from LLMs down. RankGPT reports a distilled 440M model outperforming a 3B supervised model on the BEIR benchmark ([Sun et al., 2023](https://arxiv.org/abs/2304.09542); [BEIR](#llm-pointwise-reranking)). In one product-search study of queries with superlatives, lightweight models took over an LLM's interpretations, where reranking with the LLM directly has a prohibitive latency ([Zhu et al., 2025](https://arxiv.org/abs/2511.13994)). The teacher needs no human labels and labels every candidate.

The teacher is the cross-encoder. The student is a LightGBM regression on the 7 [features](#ranking-features) that need no model call beyond the one retrieval already makes: everything but `cross_encoder`. Its label is the teacher's raw score, which a tree regression can match on the teacher's own scale. It ranks the same [candidates](#ranking-features), in `product_id` order, with trees the size [chosen for LambdaMART](#train-lambdamart). First, compare the student with a LambdaMART model trained on human grades with the same features, by cross-validation on the train queries:

Example `distillation-on-train` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Trains a student LightGBM regression on the cross-encoder's scores, and a LambdaMART model on human grades with the same
features, both by cross-validation on the train queries. The prose's point rests on the student's score, and on its
difference from the human-graded ranker."""
from lightgbm import LGBMRanker, LGBMRegressor

from lib.metrics import evaluate
from lib.ranking import CHEAP_FEATURES, DETERMINISTIC, LAMBDARANK, TREES, cross_validate, feature_table, ranked
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # design work: train queries only
candidates = feature_table(load_products(), queries)
# unjudged candidates count as grade 0, as in the metric
candidates["grade or 0"] = candidates["grade"].fillna(0).astype(int)

student = cross_validate(lambda: LGBMRegressor(**TREES, **DETERMINISTIC), candidates, candidates,
                         "cross_encoder", CHEAP_FEATURES, judgments)          # labels from the teacher
human = cross_validate(lambda: LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), candidates, candidates,
                       "grade or 0", CHEAP_FEATURES, judgments)               # labels from people
# the teacher's own order of the candidates, ties broken by product_id
teacher = evaluate(ranked(candidates, candidates["cross_encoder"]), judgments)["ndcg@10"]
semantic = evaluate(SemanticSearch().run(queries, k=100), judgments)["ndcg@10"]
for name, scores in [("semantic", semantic), ("teacher", teacher), ("student, teacher's labels", student),
                     ("lambdarank, human grades, same features", human)]:
    print(f"{name}, train ndcg@10: {scores.mean():.3f}")
# the student's score minus the human-graded ranker's, per query, tested by permutation
result = compare(student, human)
print(f"student minus the human-graded ranker: {result['mean difference']:.3f}")
print(f"student minus the human-graded ranker, permutation p: {result['permutation p']:.3f}")
```

Output:

```text
semantic, train ndcg@10: 0.772
teacher, train ndcg@10: 0.785
student, teacher's labels, train ndcg@10: 0.791
lambdarank, human grades, same features, train ndcg@10: 0.747
student minus the human-graded ranker: 0.044
student minus the human-graded ranker, permutation p: 0.002
```

On these train queries, with these features, the teacher's labels on every candidate trained a better ranker than people's grades did, with unjudged candidates counted as 0. The student scores 0.791, and the teacher's own order of the candidates 0.785.

The model trained on human grades scores 0.747, below semantic retrieval's 0.772, and the student minus it is 0.044, with a permutation p-value of 0.002. That is a tuning check on train queries, not evidence.

Then fit the student on the train queries, with early stopping on the same held-out train queries as [LambdaMART](#lambdamart-on-test-queries), and run the last [planned comparison](#ranking), at the same threshold of 0.01:

Example `distilled-ranker-on-test` (Python 3.12.15 · bm25s 0.3.16 · lightgbm 4.7.0 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.8:

```python
"""Fits a student LightGBM regression on the teacher's scores for the train queries, then reports its gain shares, how
closely its order follows similarity and the teacher, and its planned comparison on the test queries. The prose's point
rests on that comparison and on the taus printed for each ranking."""
import numpy as np
from lightgbm import LGBMRegressor
from scipy.stats import kendalltau

from lib.metrics import evaluate
from lib.ranking import CHEAP_FEATURES, DETERMINISTIC, TREES, feature_table, fit, ranked, report_planned, stopping_split
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, train, test = load_products(), load_queries("train"), load_queries("test")
table = feature_table(products, train)                       # the teacher's score is the label: no human grades
print(f"train candidates the teacher labels: {len(table)}")
print(f"of them, judged by nobody: {table['grade'].isna().sum()}")
print(f"student features: {len(CHEAP_FEATURES)}")
# early stopping on the same 10 held-out train queries that LambdaMART stops on
student = fit(LGBMRegressor(**TREES, **DETERMINISTIC), table, "cross_encoder", CHEAP_FEATURES, *stopping_split(train.index))
print(f"trees kept by early stopping: {student.best_iteration_}")

candidates, judgments = feature_table(products, test), qrels("test")       # test queries: read once, to report
predicted = student.predict(candidates[CHEAP_FEATURES])
gain = student.booster_.feature_importance(importance_type="gain")
# the three features with the most gain
for name, share in sorted(zip(CHEAP_FEATURES, gain / gain.sum()), key=lambda pair: -pair[1])[:3]:
    print(f"student's share of gain, {name}: {share:.3f}")
for name in ["cross_encoder", "similarity"]:                   # whose order does the student follow?
    # candidates has a default index, so group.index picks this query's rows out of predicted
    tau = [kendalltau(group[name], predicted[group.index]).statistic for _, group in candidates.groupby("query_id")]
    print(f"tau between student and {name}, mean over test queries: {np.mean(tau):.3f}")
teacher = evaluate(ranked(candidates, candidates["cross_encoder"]), judgments)
print(f"teacher's own order of the candidates, test ndcg@10, not a planned comparison: {teacher['ndcg@10'].mean():.3f}")
after = evaluate(ranked(candidates, predicted), judgments)
before = evaluate(SemanticSearch().run(test, k=100), judgments)
for name, frame in [("semantic", before), ("distilled", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    # each query's top 10 is 10 places, so (1 - judged@10) times 10 counts its unjudged places
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
report_planned("distilled", after["ndcg@10"], before["ndcg@10"])
```

Output:

```text
train candidates the teacher labels: 6896
of them, judged by nobody: 1975
student features: 7
trees kept by early stopping: 202
student's share of gain, similarity: 0.812
student's share of gain, name_match: 0.126
student's share of gain, bm25: 0.055
tau between student and cross_encoder, mean over test queries: 0.466
tau between student and similarity, mean over test queries: 0.753
teacher's own order of the candidates, test ndcg@10, not a planned comparison: 0.782
semantic, test ndcg@10: 0.830
semantic, test judged@10: 0.990
semantic, unjudged places in the test top 10s: 3
distilled, test ndcg@10: 0.826
distilled, test judged@10: 0.987
distilled, unjudged places in the test top 10s: 4
distilled, mean difference: -0.004
distilled, wins, losses, ties: 10, 13, 7
distilled, permutation p: 0.720
distilled, established at 0.01: no
distilled, t-test p: 0.694
distilled, t-test agrees: yes
distilled, 99% interval: -0.034 to 0.017
distilled, interval agrees: yes
```

The teacher labels all 6896 train candidates, 1975 of them judged by nobody, and early stopping keeps 202 trees.

The student leans on `similarity`, which takes a share of 0.812 of the gain, ahead of `name_match` at 0.126 and `bm25` at 0.055. On the test candidates, its scores agree with semantic similarity at a mean tau of 0.753 per query, and with the teacher's at 0.466. So the student learned mostly semantic retrieval's order, nudged toward the teacher's by name and BM25 matches.

The student doesn't establish a gain: the distilled ranker scores 0.826 nDCG@10 against semantic retrieval's 0.830, at a permutation p-value of 0.720 (see [the decisions table](#ranking-decisions)). The teacher's own order of the test candidates, which the chapter didn't plan to test, scores 0.782.

[Judged@10](#score-every-test-query) is 0.987 for the student against 0.990 for semantic retrieval, and the student's top 10s hold 4 unjudged places where semantic retrieval has 3.

**Working rule:** Distil when a reranker earns an established gain but costs too much per query: label every candidate of your train queries with the teacher, train the student on features you can compute without the teacher, and test the student against your retrieval on held-out queries. Read the student's gain importance: when retrieval's own score dominates it, the student is mostly your retrieval. Use margins between pairs when the student can't match the teacher's scale. The store has no teacher that beats semantic retrieval yet, so it keeps the code and doesn't ship the student.

## What goes wrong in production {#ranking-in-production}

A live ranker computes features and calls models while the shopper waits, with code and model versions that can drift from those it was trained and tested with.

**Features drift between training and serving.** If the live system tokenizes differently, rescales BM25 or upgrades the embedding model, the learned weights meet different numbers, and nothing raises an error. Compute features with one shared code path, and log them with each served ranking.

**Row order leaks into training.** LightGBM's lambdarank starts from the order of its input rows, and a ranking breaks ties somehow. A file sorted by a reranker's score hands the model that reranker's ranking. Sort candidates by an ID, or shuffle them with a fixed seed, before every fit and every scoring.

**Judgments come from a pool.** WANDS judged only the products its own systems put forward ([chapter 2](#pooled-judgments)). Counting unjudged candidates as irrelevant teaches a model to demote whatever those systems didn't find. Check [judged@10](#score-every-test-query) for every ranker you add, and have its unjudged products judged before you trust a gain.

**LLM judges favour LLM rerankers.** In one study, rankings built from LLM assessors place LLM-based rerankers 9 to 17 positions too high on average ([Fröbe et al., 2025](https://eprints.gla.ac.uk/352747)), and using LLMs both to rank and to judge is circular, "illustrating how reliance on LLM-based assessments can distort system rankings" ([Clarke and Dietz, 2024](https://arxiv.org/abs/2412.17156)). Score LLM rerankers with human judgments, as this chapter does.

**An LLM reranker belongs to one model version and one prompt.** A different digest (the hash that identifies the exact weights), quantization (the precision the weights are stored at) or prompt wording can change every answer, and with [positional bias](#llm-position-bias), so can a change in retrieval's order. The LLM recording's manifest records the digest and both prompts verbatim; re-measure whenever either changes.

**Unfamiliar queries can do worse.** A comparison of 22 reranking methods found that LLM rerankers do better on familiar queries, while "their generalization ability to novel queries varies" ([Abdallah et al., 2025](https://arxiv.org/abs/2508.16757)). Watch queries about products and styles newer than the model's training data.

**Every reranker adds a call on the shopper's path.** Count calls and text per query, as in [the budget](#rerank-depth-from-budget), set a timeout, and fall back to retrieval's order when the reranker doesn't answer in time.

**Working rule:** Log features and model versions with every ranking, put candidates in an order that carries no information, score on human judgments, check judged@10, and give each reranking stage a time limit and a fallback.

## Decisions this chapter made {#ranking-decisions}

The chapter made each choice in the list below on the train queries, and only an established planned comparison on the test queries could change the store's search.

The 5 planned comparisons, each on nDCG@10 against semantic retrieval's 0.830, established below 0.01:


| Measure | [LambdaMART](#lambdamart-on-test-queries) | [Cross-encoder](#rerank-semantic-with-cross-encoder) | [LLM pointwise](#llm-pointwise-reranking) | [LLM listwise](#llm-listwise-reranking) | [Distilled](#distill-the-cross-encoder) |
| --- | --- | --- | --- | --- | --- |
| nDCG@10 | 0.817 | 0.813 | 0.837 | 0.819 | 0.826 |
| Mean difference | -0.012 | -0.016 | 0.008 | -0.010 | -0.004 |
| Wins / losses / ties | 14, 12, 4 | 11, 12, 7 | 11, 8, 11 | 12, 12, 6 | 10, 13, 7 |
| Permutation p | 0.260 | 0.178 | 0.241 | 0.580 | 0.720 |
| Established | no | no | no | no | no |
| t-test p | 0.278 | 0.171 | 0.244 | 0.498 | 0.694 |
| 99% interval | -0.044 to 0.011 | -0.058 to 0.006 | -0.007 to 0.026 | -0.070 to 0.016 | -0.034 to 0.017 |
| t-test agrees | yes | yes | yes | yes | yes |
| Interval agrees | yes | yes | yes | yes | yes |

- **5 planned comparisons** against semantic retrieval, on human judgments, established below 0.01.
- **Candidates: the union of BM25's and semantic retrieval's top 100,** in `product_id` order, with score ties broken by `product_id`.
- **LambdaMART: `label_gain=[0, 1, 2]`, unjudged candidates as grade 0, 3 leaves at a learning rate of 0.1,** chosen by cross-validation on train, with early stopping on held-out train queries through `eval_X` and `eval_y`. Its gain isn't established on test, so it isn't used.
- **Rerank depth: semantic retrieval's top 20,** fixed to match the LLM recording; on train, the cross-encoder's curve flattens between 20 and 30. No reranker's gain is established on test, so none is used.
- **LLM rerankers are scored on human judgments only,** and the listwise one is checked in two input orders. Its answer depends on the order shown.
- **Costs are counted, not timed:** calls and characters per query.
- **Distillation: a LightGBM student on the cross-encoder's scores,** with no model call beyond retrieval's. It learns mostly semantic retrieval's order, shows no established gain, and isn't used.
- **The ranker to beat stays semantic retrieval alone,** with BM25, unstemmed, as the baseline.
- **What the chapter showed:** no second stage earned its place; none shows an established gain.
