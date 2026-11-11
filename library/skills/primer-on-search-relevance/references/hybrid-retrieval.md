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

*Example `bm25-semantic-wins-by-query`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/queries-each-retriever-wins*

On average, semantic retrieval scores 0.772 and BM25 0.695. Per query, semantic retrieval is better on 31 queries, BM25 on 15, and 4 are tied. If you could choose the better of the two rankings for each query, the mean would be 0.802. That isn't a ceiling for fusion, which mixes the lists rather than choosing one, but it measures what the two rankings' differences could be worth.

Next, see whether the two lists hold different products, and what share of each query's **exact** products, the ones the judges graded as fully matching it, each list finds:

*Example `overlap-and-union-recall`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/queries-each-retriever-wins*

The two top 10s share 3.7 products on average. BM25's top 100 holds 0.672 of each query's exact products, semantic retrieval's 0.759, and the union of the two lists 0.810. Fusion can't rank a product that neither list holds, so how deep each list goes caps how many exact products fusion can reach: cut each list to its top 20, and the union holds 0.445.

Two train queries show the kinds of failure:

*Example `two-queries-two-winners`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/queries-each-retriever-wins*

For `butcher block island`, BM25's top 10 holds 9 exact products and semantic retrieval's 3. BM25 rewards products whose text contains all three words: kitchen islands with butcher-block tops. Semantic retrieval ranks prep tables and carts with butcher-block tops near the top too, and the judges graded those partial: the right material, but not the island the query asks for. For `7qt slow cooker` it's the other way round: 1 against 7. The catalog has 0 products whose text contains `7qt` and 9 that contain `7 qt`. So BM25 matches only `slow cooker` and ranks cookers of every size, while semantic retrieval puts 7-quart cookers first.

Those are single queries: they show a kind of failure, not how often it happens. [The per-query count](#bm25-semantic-wins-by-query) also lists the 6 train queries where BM25 leads by 0.1 nDCG@10 or more. Most name a specific kind of product in two or more words that all have to match, and one, `malachi sled`, names a product line. [Chapter 1](#search-by-meaning) found BM25 ahead on 2 of the 2 test queries that give a size in inches, yet of the 5 train queries that contain a digit, BM25 wins 1.

**Working rule:** Before you fuse, count per query where each retriever wins on your train queries, and check how many relevant products the union of their lists holds that the better one misses. Consider fusing when each retriever wins a real share of queries and the union holds more relevant products than either list. That is necessary, not sufficient: next, [check each retriever alone](#check-each-retriever-before-fusing), and [test the tuned blend on held-out queries](#report-blends-on-test) before you adopt it.

## Check each retriever before you fuse {#check-each-retriever-before-fusing}

Knowing [where each retriever wins](#queries-each-retriever-wins) isn't enough, because fusion gives each input a say in the final ranking, a weak input included. A study of hybrid search over 11 datasets reports "A “weakest link” phenomenon, where a weak path can substantially degrade overall accuracy, highlighting the need for path-wise quality assessment before fusion" ([Wang et al., PVLDB 2026](https://arxiv.org/abs/2508.01405)). So compare the retrievers' mean nDCG@10, with [judged@10](#unjudged-results), the share of the top 10 that has a judgment, beside it. Then compare them query by query with a **paired test**, which asks how likely a mean difference this large would be if the two were equally good. The book's test is the [permutation test](#permutation-test-on-queries), with the [paired t-test](#paired-t-test-on-queries) beside it. On train queries, these checks shape how you combine the retrievers; they aren't evidence about the store.

In the store, fuse BM25 and semantic retrieval as [chapter 1](#fuse-with-rrf) did, with reciprocal rank fusion (RRF): each product scores 1 / (60 + its rank) in each ranking, summed over the two, so each ranking gets an equal vote. Then split the train queries by which retriever wins, and compare the fused ranking with semantic retrieval alone:

*Example `fusion-gain-by-winning-retriever`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/check-each-retriever-before-fusing*

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

*Example `raw-scores-versus-min-max`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/normalize-scores-before-adding*

For `laundry basket with wheels`, the 125 candidates have BM25 scores from 2.059 to 8.229 and similarities from 0.336 to 0.597. BM25's spread is many times larger, so it decides the order of the raw sum. Over the train queries, the raw sum's top 10 shares 9.6 products with BM25's top 10 on average and 3.9 with semantic retrieval's. Its nDCG@10 of 0.706 is close to [BM25's 0.695](#queries-each-retriever-wins). The weight says "half each", but the ranking is mostly BM25's.

After min-max scaling, the top 10 shares 6.5 products with BM25's and 6.2 with semantic retrieval's, and nDCG@10 is 0.771, with a permutation p-value against the raw sum below 0.001. Both retrievers now have a say. The by-hand version ranks 50 of 50 train queries exactly as `lib.blend.weighted_sum` does.

Raw scores can work with a tuned weight. The authors of DPR, an embedding-based retriever, ranked candidates by BM25 plus 1.1 times DPR's similarity, with the 1.1 chosen on a development set ([Karpukhin et al., 2020](https://arxiv.org/abs/2004.04906)). Normalization gives α the same meaning for every query; without it, BM25's share of the say changes with its range from query to query. Min-max isn't an absolute scale, though. It is relative to the query's candidates, so the best candidate always gets 1, however poor it is.

**Working rule:** Never add raw BM25 and cosine scores with a guessed weight. We recommend per-query min-max as the default, because it needs no knowledge of either scoring function. Use theoretical min-max when you know each score's lowest possible value and want a floor that doesn't move with the candidates. In either case, tune α on train queries.

## Test reciprocal rank fusion's settings on train queries {#rrf-settings-on-train}

Ranks, unlike [scores](#normalize-scores-before-adding), share one scale, so fusing by rank needs no normalization. **Reciprocal rank fusion** (RRF) scores each product by adding, over the rankings that contain it, 1 divided by the sum of a constant k and its rank, as [chapter 1's formula](#fuse-with-rrf) writes it ([Cormack et al., 2009](http://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf)). The price is information: "because RRF is a function of ranks, it disregards the distribution of scores and, as such, discards useful information" ([Bruch et al., 2023](https://arxiv.org/abs/2210.11934)). A product a hair behind the leader and one far behind it get scores set by their ranks alone.

The constant k sets how much the top ranks dominate. RRF's authors fixed k = 60 in a pilot study, and their tests "indicated that k = 60 was near-optimal, but that the choice was not critical". Those pilots fused "30 configurations of Wumpus Search", one search engine, on collections from TREC, a series of shared retrieval evaluations (Cormack et al., 2009). Bruch et al. fused one lexical and one semantic retriever, gave each its own constant, η, and found the results sensitive to the balance between the two constants, which acts as a weight: "where the semantic model already performs strongly, for example, discounting the lexical system by increasing η_Lex leads to better performance". One k shared by both rankings, as here, sets no balance between them.

The depth of each list matters too. A product in one retriever's top 20 but not in the other's earns nothing from the second ranking, although it has a rank there, only a low one. As Bruch et al. put it, "ranks cannot be computed exactly unless the entire collection D is ranked by retrieval system o for every query." In the store, the union of two top-20 lists holds far fewer exact products than the union of two top-100 lists, as [the count of exact products in each list](#queries-each-retriever-wins) shows.

Try six values of k on the store's train queries, fusing BM25 and semantic retrieval from lists 100 deep. One check is planned before running: does the best k on train beat the default, k = 60?

*Example `rrf-k-on-train`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rrf-settings-on-train*

At k = 1, rank 1 earns 5.500 times what rank 10 earns. At k = 60, it earns 1.148 times as much, so a product near the top of both lists beats one at the top of only one. From k = 1 to k = 300, the six settings score 0.753, 0.770, 0.771, 0.774, 0.778 and 0.777. The best, k = 100, leads k = 60 by 0.004, with a permutation p-value of 0.093 and a t-test p-value of 0.103. Its 95% bootstrap interval, 0.001 to 0.011, excludes 0, so it disagrees with both tests. The two settings' rankings differ on only a handful of queries (wins, losses and ties: 6, 3, 41), and the book takes its verdict from the permutation test, which can't tell the gain from chance at 0.05. Which k is best is fragile too: [with BM25's tied products listed the other way](#tuned-weight-stability), k = 300 wins instead. This fits Cormack et al.'s finding that the choice of k is not critical.

**Working rule:** Keep k = 60 as the default, and fuse lists at least 100 deep, because a deeper list can only add candidates. Move off k = 60 only when the best k on train beats it by a margin the permutation test can tell from chance, with p below 0.05. When one retriever is [the stronger one](#check-each-retriever-before-fusing), as in the store, k isn't the setting to change: RRF's equal vote is. Give the rankings weights and [tune them](#tune-blend-on-train).

## Tune the blend's weight on train queries {#tune-blend-on-train}

The chapter's two [blends](#hybrid-retrieval) each take one weight, α, the share given to semantic retrieval. In the [weighted sum](#normalize-scores-before-adding), α multiplies the normalized similarity and 1 − α the normalized BM25 score. In **weighted RRF**, a product scores (1 − α) / (k + its BM25 rank) plus α / (k + its semantic rank). For both, α = 0 is BM25 alone and α = 1 is semantic retrieval alone. For RRF, α = 0.5 is [chapter 1's unweighted fusion](#fuse-with-rrf) with every score halved. Here is the arithmetic for the top product of one train query, with an illustrative α = 0.75:

*Example `weighted-rrf-one-product`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/tune-blend-on-train*

For `laundry basket with wheels`, laundry sorter basket on wheels sits at rank 1 in BM25's ranking and rank 2 in semantic retrieval's, so it scores 0.25 / (60 + 1) + 0.75 / (60 + 2) = 0.01620. The example scores every candidate this way, and its ranking matches `lib.blend.weighted_rrf` in 100 of 100 places.

Tuning means trying a grid of α values on train queries and keeping the one with the best mean nDCG@10. Bruch et al. (2023) report three findings about tuning a [convex combination](#normalize-scores-before-adding), CC: "the learning of a CC fusion is generally agnostic to the choice of score normalization; that CC outperforms RRF in in-domain and out-of-domain settings; and finally, that CC is sample efficient." Sample efficient meant that α converged "with less than 5% of the training data", a fraction of training sets much larger than the store's.

In the store, tune α over 0, 0.1, … 1 for the weighted sum under each of [the three normalizations](#normalize-scores-before-adding), and for weighted RRF with k = 60. Then test, as tuning checks, each normalization against min-max, and the two blends that go to the test queries against semantic retrieval:

*Example `tune-blend-weights-on-train`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/tune-blend-on-train*

The output's second line traces the min-max blend from α = 0 to α = 1. It peaks at α = 0.7 with 0.784, against semantic retrieval's 0.772. Theoretical min-max peaks at α = 0.9 with 0.789, and the z-score at α = 0.7 with 0.787. Against tuned min-max, their permutation p-values are 0.164 and 0.349: at 0.05, the test on train queries can't tell either normalization from min-max, which fits Bruch et al.'s finding that the normalization hardly matters. Weighted RRF peaks at α = 0.6 with 0.787, and against tuned min-max its p-value is 0.776. Bruch et al.'s second finding, that the weighted sum beats RRF, doesn't show here, and these queries can't settle it.

Every tuned blend scores at least as well as semantic retrieval on the train queries, and that is guaranteed: α = 1 is in the grid. Yet even on the queries that chose them, the permutation test can't tell either blend's gain from chance at 0.05. The weighted sum gains 0.013, with a permutation p-value of 0.177, and weighted RRF gains 0.015, with 0.215. Each gain is also the best of 11 tries on the same queries, which flatters it further.

**Working rule:** Tune one weight on train queries over a coarse grid, and keep the normalization at min-max unless another one beats it by a margin the test on train queries can tell from chance, with p below 0.05. Treat the train gain over the best single retriever as optimistic, and expect it to shrink on test queries, a rule of thumb for any setting picked as the best of several. Before you trust the setting, [check that it's stable](#tuned-weight-stability), then [report it on test queries](#report-blends-on-test).

## Check that the tuned weight is stable {#tuned-weight-stability}

The [tuned weights](#tune-blend-on-train) come from a few dozen queries, so they can depend on which queries you happened to have. The **bootstrap** shows how much: draw as many queries from the train set as it holds, with replacement, so some appear twice and others not at all, tune α on that sample, and repeat many times. If the chosen α jumps around, the tuned value reflects the sample more than the store. [Chapter 3](#report-the-size-of-a-gap) uses the same resampling to put intervals around scores.

In the store, resample the train queries 1000 times with a fixed seed, and count how often each α wins for both tuned blends, the weighted sum of min-max scores and weighted RRF, on the same resamples:

*Example `blend-weight-bootstrap`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/tuned-weight-stability*

For the weighted sum, tuned at α = 0.7 on all the train queries, α = 0.7 wins 686 resamples and α = 0.6 wins 171. Semantic retrieval alone, α = 1, wins 45. Weighted RRF, tuned at α = 0.6, is less settled: α = 0.6 wins 513 resamples, α = 0.8 wins 365 and α = 0.7 wins 76. Both weights stay on the side of the grid that favours semantic retrieval, apart from equal weight, α = 0.5, which wins 13 resamples for the weighted sum and 2 for weighted RRF. RRF's weight moves between 0.6 and 0.8.

Resampling isn't the only check. Products with equal BM25 scores have to be listed in some order, and `lib.lexical` lists them by `product_id`, an order that carries no information. Descending `product_id` order carries none either. The weighted sum gives tied products the same BM25 term, so their order hardly matters to it, but RRF gives them consecutive ranks, and so different scores. List BM25's ties by descending `product_id`, and tune the [best RRF k](#rrf-settings-on-train) and both weights again on the train queries:

*Example `tuning-with-ties-reversed`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/tuned-weight-stability*

With the ties reversed, the best k is 300 instead of 100, and weighted RRF's α is 0.8 instead of 0.6. The weighted sum keeps α = 0.7. When an order that carries no information changes a setting, the train queries can't tell the settings apart: RRF's k and weight are fragile, and the weighted sum's weight isn't. The store has no more train queries to settle weighted RRF's weight, and its test comparison was planned with the weight tuned with ties by `product_id`, so α = 0.6 goes to test.

Stability says the train queries agree on a weight, not that the weight improves search on queries it wasn't tuned on: the resamples reuse the same train queries, so they share whatever those queries have in common.

**Working rule:** Bootstrap the train queries and tune on each sample, then tune once more with ties listed in another order that carries no information. If the chosen weight scatters across the grid, use a coarser grid or more train queries, or prefer the simpler setting. If the tie order alone moves it, say so wherever you report it. If it holds steady under both checks, take it to the test queries.

## Report the tuned blends on test queries {#report-blends-on-test}

Only held-out queries show whether a tuned setting helps beyond the queries that chose it. Run each tuned blend once on the test queries, and compare it with semantic retrieval, the best single retriever, query by query, using the harness that [chapter 3](#compare-runs-in-a-harness) builds. The chapter fixed these two comparisons before looking. With the Bonferroni correction, a difference is established when its permutation p-value is below 0.025. The t-test and a bootstrap interval at the matching confidence level, 0.975, stand beside it.

On the store's train queries, the [tuned blends](#tune-blend-on-train) gained 0.013 and 0.015 over semantic retrieval, neither of them a gain the permutation test could tell from chance. Before you read the output, predict: on the test queries, will the weighted sum with α = 0.7 and weighted RRF with α = 0.6 score above semantic retrieval, level with it, or below it?

*Example `tuned-blends-on-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/report-blends-on-test*

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

*Example `exact-products-missing-query-words`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/learned-sparse-splade*

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
