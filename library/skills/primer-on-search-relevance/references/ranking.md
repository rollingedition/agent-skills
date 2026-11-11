---
title: "A Primer on Search Relevance"
chapter: "Ranking"
chapter_id: ranking
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/ranking
license: CC BY 4.0
attribution: "“Ranking,” chapter 9 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/ranking. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Ranking

By the end of this chapter you can describe each product that retrieval returns with features, train a learning-to-rank model with LightGBM on your own judgments, rerank the top of the list with a cross-encoder or an LLM, measure an LLM reranker's positional bias, set the rerank depth by counting its costs, and distil a slow reranker into a fast one. You can also decide, with a planned test on held-out queries, whether any of them beats your retrieval.

The store, the online furniture and home-goods retailer this book follows as its case study ([chapter 1](#store-data)), has one ranker to beat: [semantic retrieval](#search-by-meaning) alone. It ranks products by embeddings from `Snowflake/snowflake-arctic-embed-m-v1.5`, and scores 0.830 [nDCG@10](#score-one-ranking) on the 30 [test queries](#store-data). No change in chapters 5 to 8 has beaten it by an established margin. This chapter asks whether a second stage can: a model trained on the store's own judgments, a reranker that reads the query and the product together, or an LLM. [Chapter 1's cross-encoder](#rerank-with-cross-encoder), a reranker of the second kind, reranked the hybrid run, not semantic retrieval, and had never seen the store's judgments.

**Reranking** reorders the top of retrieval's list with a slower model. The store's rerankers are **recorded**: each ran once and saved its outputs, which the examples read. The cross-encoder is the open model `Alibaba-NLP/gte-reranker-modernbert-base`, whose **manifest**, the file saved with its recording, gives its licence as Apache-2.0. `recordings/cross_encoder.py` scored the union of BM25's and semantic retrieval's top 100 for every query (for two queries, its semantic list differs from `lib.semantic`'s by a near-tie at the 100th place). A **large language model** (LLM) is a model trained on large amounts of text to generate text in response to a prompt. The store's LLM is the open model `gemma4:12b-it-q4_K_M`, licensed Apache-2.0. It ran locally with a fixed seed and three settings: temperature 0, so it takes its likeliest next word every time; thinking off, so it answers without writing out reasoning; and a JSON schema, a machine-readable description of the answer's shape. We chose both models because anyone can download them and rerun the recordings. `recordings/llm_rerank.py` reranked semantic retrieval's top 20 for the test queries only, so nothing about the LLM rerankers can be tuned. Every score uses the human judgments, because in one study LLM judges ranked LLM rerankers too high ([What goes wrong in production](#ranking-in-production)). Every finding about the LLM holds for this model, its two prompts and these test queries, not for LLMs in general.

Before reading any test result, the chapter fixes 5 planned comparisons on the test queries, each against semantic retrieval's run on nDCG@10:

1. [LambdaMART](#lambdamart-on-test-queries), a learned ranker trained on the train queries' judgments, ordering each query's candidate products
2. the [cross-encoder](#rerank-semantic-with-cross-encoder) reranking semantic retrieval's top 20
3. the LLM scoring each of the top 20 [on its own](#llm-pointwise-reranking)
4. the LLM ordering the top 20 [in one prompt](#llm-listwise-reranking)
5. a small [distilled ranker](#distill-the-cross-encoder) trained on the cross-encoder's scores

By [the book's rule](#when-a-difference-is-established), a difference is established when its paired [permutation test](#permutation-test-on-queries) gives a p-value below 0.01, 0.05 divided by the number of planned comparisons. The [paired t-test](#paired-t-test-on-queries) and a 99% [bootstrap interval](#report-the-size-of-a-gap) stand beside it. Numbers on the 50 train queries guide design choices; they are not evidence.

## Describe each candidate with features {#ranking-features}

A learned ranker, the first of the chapter's [planned comparisons](#ranking), doesn't read text. It scores each pair of a query and a product from a list of numbers, its **features**, and learns from judgments how to weigh them. A **query-dependent** feature describes the pair, such as a BM25 score. A **query-independent** feature describes the product alone, such as how many shoppers rated it. Feature sets for web search mix both: LETOR 4.0, a benchmark for learning to rank, has 46 features, among them "BM25 of title", "PageRank" and "Number of slash in URL" ([Qin and Liu, 2013](https://arxiv.org/abs/1306.2597)). A ranker scores only **candidates**, the products a cheaper retrieval stage returns, so its features can be expensive.

In the store, a query's candidates are the products the cross-encoder's recording scored: the union of BM25's top 100 and [semantic retrieval](#search-by-meaning)'s top 100. `lib.ranking.feature_table` gives each candidate 8 features:

- `bm25`: the [BM25](#rank-with-bm25) score from `lib.lexical`, the book's unstemmed baseline, and 0 for a product that shares no term with the query
- `similarity`: the cosine similarity of the query's and the product's embeddings
- `cross_encoder`: the recorded cross-encoder score
- `name_match` and `attribute_match`: the share of the query's terms, [tokenized as chapter 5 does](#split-text-into-terms), found in the product's name and in its [attributes](#index-attributes-as-a-field)
- `rating_count`, `average_rating` and `review_count`, which the store's data gives each product

2632 of the catalog's products have no rating, and their three rating features stay missing. The table also holds each candidate's human grade, or a gap when nobody judged it. Build the table for the [train queries](#store-data), look at one query, then compare each feature across the grades:

*Example `ranking-features-by-grade`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/ranking-features*

The train queries have 6896 candidates, a median of 131 per query, and nobody judged a share of 0.286 of them. `laundry basket with wheels` has 125 candidates. The six that the cross-encoder scores highest include 6 [exact](#store-data) products. Their `attribute_match` is 0, because attributes hold colours, materials and sizes, not words such as `wheels`.

Across the train candidates, the mean cross-encoder score falls from 2.191 for exact products to 1.513 for partial and 1.159 for irrelevant ones, and `bm25`, `similarity` and `name_match` fall the same way. `average_rating` and `attribute_match` barely move. The mean `rating_count` falls from 466.879 to 385.454 and 246.781, but the medians are 43.0, 31.0 and 35.5: a few heavily rated products set the means. Unjudged candidates average a cross-encoder score of 1.050, and on 4 of 4 features that fall with the grade, their mean sits nearer the irrelevant products' than the partial ones'. That matters for what an unjudged candidate should teach a model.

**Working rule:** Start with the features you already compute: each retriever's score, a reranker's score if you have one, matches on fields such as the name, and popularity signals. Compare each feature by grade on train queries before you train, with means for scores and medians for skewed counts. A feature that doesn't move with the grade has little to teach the model. Compute features with the same code when you train and when you serve.

## Learn a ranking from pairs of products {#learn-from-pairs}

**Learning to rank** trains a model on judged queries to order candidates by their [features](#ranking-features). Its methods fall into three families: "the pointwise, pairwise, and listwise approaches" ([Liu, 2009](https://doi.org/10.1561/1500000016)). A **pointwise** model predicts each product's grade on its own, as a regression. A **pairwise** model learns which of two products should rank higher. A **listwise** model scores a whole ranking. On the LETOR benchmark, Liu's comparison "seems to suggest that the listwise approach be the most effective one", a result from 2009. The obstacle for all three is the metric: nDCG changes only when two products swap places, so ranking metrics "are everywhere either discontinuous or flat, so gradient descent appears to be problematic" ([Burges, 2010](https://www.microsoft.com/en-us/research/publication/from-ranknet-to-lambdarank-to-lambdamart-an-overview/)).

RankNet, a pairwise method, works around it with a smooth loss on pairs. For two products where i should rank above j, its gradient is large when the model scores them the wrong way round or nearly level, and small when it already has them well apart. LambdaRank keeps that gradient and multiplies it by how much nDCG would change if the two products swapped places (Burges, 2010, section 4.1). Burges writes the gradient with a minus sign, as the slope of a cost; here a positive λ pushes i up:

```text
λ_ij    = σ / (1 + exp(σ · (s_i − s_j))) · |ΔnDCG_ij|      s: the model's scores, σ = 1
ΔnDCG_ij = (g_i − g_j) · (1 / log2(1 + r_i) − 1 / log2(1 + r_j)) / ideal DCG      g: grades, r: positions
```

A product's total is its λ summed over the pairs where it should rank higher, minus those where it should rank lower. "The λ's can also be interpreted as forces" (Burges, 2010), pushing products up and down the list. **LambdaMART** uses these λ as the gradients for **gradient-boosted trees**, which add small decision trees one at a time, each fitted to the gradients of the trees before it: "LambdaMART is the boosted tree version of LambdaRank, which is based on RankNet". An ensemble of LambdaMART rankers won Track 1 of the Learning to Rank Challenge that Yahoo ran in 2010 (Burges, 2010).

In the store, take the train query `outdoor waterproof chest`, and let semantic similarity be the model's scores so far. Compute every pair's λ in its top 10 by hand, check each |ΔnDCG| by swapping the pair and recomputing nDCG with `lib.metrics`, and add up the forces:

*Example `lambdas-for-one-query`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/learn-from-pairs*

The top 10's grades, from the top, are 1 2 2 0 1 2 0 2 0 0; an unjudged product counts as 0, as it does in the metric. The top 10 holds 32 pairs with different grades, and for 32 of them the formula's |ΔnDCG| matches the change from swapping the pair. RankNet's factor in λ stays between 0.472 and 0.525, because the similarities lie close together, so |ΔnDCG| decides almost everything. The strongest push up goes to position 2, an exact product, with +0.159. The strongest push down goes to position 10, an irrelevant product, with -0.111. The partial product at position 1 gets +0.013: the irrelevant products below push it up, the exact ones push it down.

That example simplifies: it takes the ideal DCG from every judged product, as `lib.metrics` does, and looks at ten products. LightGBM takes the ideal from the query's training rows, and at 4.7.0 two defaults change the λ. `lambdarank_truncation_level` is 30, so it "controls the number of top-results to focus on during training": only pairs with a product in the current top 30 get a λ. `lambdarank_norm` is true, to "normalize the lambdas for different queries"; set it to false "to enforce the original lambdarank algorithm" ([Parameters](https://lightgbm.readthedocs.io/en/v4.7.0/Parameters.html)). In the source, normalizing divides each pair's |ΔnDCG| by the gap between its scores plus 0.01, then rescales each query's λ ([`rank_objective.hpp`](https://github.com/microsoft/LightGBM/blob/v4.7.0/src/objective/rank_objective.hpp)). To check the formula against the library, write it as a custom LightGBM objective, grow five small trees on this query's candidates, and grow them again with LightGBM's lambdarank, with and without those defaults:

*Example `lambdas-match-lightgbm`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/learn-from-pairs*

Over the query's 180 candidates, LightGBM without normalization or truncation scores every product within 0.000006 of the custom objective's scores. The gap is rounding, since LightGBM reads its sigmoid from a precomputed table (`rank_objective.hpp`). At its defaults, scores differ by up to 0.595667.

**Working rule:** Train rankers with a gradient that weighs each pair by the metric you report, as LambdaMART does, rather than regressing on grades. Know which defaults of your library change that gradient, and check on train queries that it beats a pointwise model on your data, because the families' order in a benchmark doesn't transfer by itself.

## Train LambdaMART with LightGBM {#train-lambdamart}

LightGBM trains [LambdaMART](#learn-from-pairs) with `LGBMRanker` and `objective="lambdarank"`. Four settings need care, and each is documented for 4.7.0:

- **Rows are grouped by query.** "data should be ordered by the query", and `group` holds the number of rows of each query in that order, not query IDs: "sum(group) = n_samples" ([Parameters](https://lightgbm.readthedocs.io/en/v4.7.0/Parameters.html); [`LGBMRanker`](https://lightgbm.readthedocs.io/en/v4.7.0/pythonapi/lightgbm.LGBMRanker.html)).
- **Gains are exponential by default.** `label_gain` defaults to `0,1,3,7,15,31,63,...`, so "the gain of label `2` is `3`", and every label must be smaller than the number of gains (Parameters). That is Burges's DCG, with gain 2^grade − 1. The book's nDCG uses [linear gains](#gains-are-a-choice), so set `label_gain=[0, 1, 2]`.
- **nDCG is evaluated at positions 1 to 5 by default.** Set `eval_at=[10]` to stop on nDCG@10, and report the final score with `lib.metrics` anyway.
- **Validation data goes in `eval_X` and `eval_y`.** In 4.7.0, `eval_set` is "Deprecated since version 4.7.0", with the note "Use eval_X and eval_y instead" (`LGBMRanker`; [release notes](https://github.com/microsoft/LightGBM/releases/tag/v4.7.0)). The examples pass `eval_X`, `eval_y` and `eval_group`.

**Early stopping** scores held-out train queries after every tree, and keeps the trees up to the best score once 30 more bring no gain. So that training repeats exactly, the examples use one thread, a fixed seed and `deterministic=True`, which "should ensure the stable results when using the same data" (Parameters), with `force_row_wise=True`, which the same entry asks for "to avoid potential instability due to numerical issues". `lib.ranking` holds these settings, and its `fit` applies the grouping and early stopping.

Row order matters too. Before the first tree every score is 0, so LightGBM takes the rows' order as the starting ranking for the first λ, and equal scores need a tie-break. The cross-encoder's recording lists each query's [candidates](#ranking-features) best first, which would hand the model the cross-encoder's ranking before it learned anything. So `feature_table` sorts candidates by `product_id`, and `lib.ranking.ranked` breaks ties by `product_id`.

Choose the tree size by **cross-validation** on the train queries: split them into five folds, rank each fold with a model fitted on three others and stopped early on the fifth, and score every query once. Try eight settings, from 3 to 31 leaves at two learning rates, counting unjudged candidates as grade 0 as the metric does:

*Example `lambdamart-tree-size-on-train`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/train-lambdamart*

Of 8 settings, the best is 3 leaves, learning rate 0.1, at 0.798; LightGBM's default of 31 leaves at 0.1 (`LGBMRanker`) scores 0.737. The best of eight tries flatters itself, so expect less on held-out queries.

One choice depends on the store's judgments. Nobody judged a share of 0.286 of the train candidates. A model can count them as grade 0, or learn from judged candidates only; [unjudged isn't irrelevant](#unjudged-results), but the model will rank them at query time either way. Compare both by cross-validation at the chosen tree size, with a pointwise regression on the grades beside them:

*Example `lambdamart-choices-on-train`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/train-lambdamart*

Counting unjudged candidates as 0 scores 0.798. Leaving them out scores 0.733, a difference of -0.064 with a permutation p-value of 0.005. A model that never sees an unjudged candidate in training still has to rank them, and [the features](#ranking-features) say they look like irrelevant products. Pointwise regression scores 0.769, a difference of -0.029 (p = 0.007), so on the store's train queries the [check against a pointwise model](#learn-from-pairs) favours LambdaMART. These are tuning checks on train queries, not evidence. Against semantic retrieval's 0.772, the chosen setup differs by 0.026, with a permutation p-value of 0.242: even on the queries that chose it, it shows no gain the train queries can tell from chance.

**Working rule:** Sort rows by query and pass `group`, set `label_gain` to the gains your metric uses, stop early on held-out train queries through `eval_X` and `eval_y`, and fix the seed and thread count. Put each query's candidates in an order that carries no information, such as by product ID, and break score ties the same way. Count unjudged candidates as grade 0 unless cross-validation on train queries says otherwise. With few judged queries, try small trees.

## Report LambdaMART on the test queries {#lambdamart-on-test-queries}

A model tuned on train queries is reported once on the test queries, by a comparison planned before looking. **Feature importance** shows what it learned: LightGBM's `"gain"` importance is the "total gains of splits which use the feature" ([`Booster`](https://lightgbm.readthedocs.io/en/v4.7.0/pythonapi/lightgbm.Booster.html)), so a feature with no gain plays no part in the score.

In the store, fit the setup [chosen on train](#train-lambdamart): [LambdaMART](#learn-from-pairs) on all the [features](#ranking-features), with 3 leaves at a learning rate of 0.1, unjudged candidates as grade 0, and candidates in `product_id` order. Fit on 40 train queries, and stop early on 10 others. Rank each test query's candidates with it, and make the first of the chapter's [planned comparisons](#ranking), established below p = 0.01:

*Example `lambdamart-on-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/lambdamart-on-test-queries*

Of 243 trees tried, early stopping keeps 213. On the queries held out for stopping, LightGBM's own nDCG@10, whose ideal comes from their candidates alone, rises from 0.568 after the first tree to 0.794 at the trees kept. The trees use 8 of 8 features. The cross-encoder takes a share of 0.641 of the gain, `similarity` 0.172, `name_match` 0.097 and `bm25` 0.043. The model leans on the cross-encoder, so serving it means a cross-encoder call for every candidate.

On test, [judged@10](#score-every-test-query), the share of the top 10 that has a judgment, is 0.990 for LambdaMART and 0.990 for semantic retrieval. LambdaMART scores 0.817 against semantic retrieval's 0.830. No improvement shown, with a permutation p-value of 0.260 ([all five comparisons](#ranking-decisions)).

**Working rule:** Adopt a learned ranker only when its planned test comparison is established. Read its gain importance before you trust it, because the features it leans on are the ones you'll pay for at query time. Early stopping on a few held-out queries keeps very different numbers of trees from one split to the next, from 99, 20, 8, 43, 38 across the cross-validation folds to 213 here. A rule of thumb, not a measurement: with this few queries, judge more queries before you tune further, and treat any one stopping point as noise.

## Rerank semantic retrieval with a cross-encoder {#rerank-semantic-with-cross-encoder}

[Semantic retrieval](#search-by-meaning) uses an embedding model, also called a **bi-encoder**, which reads the query and each product separately, so product embeddings are computed ahead of time. A **cross-encoder** reads the query and one product together and outputs one score ([Nogueira and Cho, 2019](https://arxiv.org/abs/1901.04085)). It can relate every query word to every product word, and it pays for that: it is "Often slower than a Sentence Transformer model, as it requires computation for each pair rather than each text", and so "Cross Encoders are often used to re-rank the top-k results" ([Sentence Transformers](https://sbert.net/docs/cross_encoder/usage/usage.html)). The store's cross-encoder, named in [the chapter's opening](#ranking), is small for a language model, with 149M parameters ([model card](https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base)).

[Chapter 1](#rerank-with-cross-encoder) reranked the hybrid run. Here the cross-encoder reranks the ranker to beat, semantic retrieval's top 20: the same products the [LLM rerankers](#llm-pointwise-reranking) read, so the chapter's three rerankers start from identical lists. The chapter fixed that depth before reading any test result, and doesn't tune it. Reorder the top 20 by the recorded scores, keep the rest in place, and make the second of the chapter's [planned comparisons](#ranking), established below p = 0.01:

*Example `cross-encoder-on-semantic`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rerank-semantic-with-cross-encoder*

The top 20 holds the products the LLM rerankers saw for 30 of 30 test queries. The reranker changes the first product for 23 test queries. [Judged@10](#score-every-test-query) falls from 0.990 to 0.983: the unjudged places across the test queries' top 10s go from 3 to 5. The rerank scores 0.813 against 0.830. No improvement shown, with a permutation p-value of 0.178 ([all five comparisons](#ranking-decisions)).

On the train queries, the same rerank scores 0.802 against semantic retrieval's 0.772 ([depth sweep](#rerank-depth-from-budget)). That is another sample, not evidence, and it repeats what [chapter 3](#split-changes-the-verdict) found: two close rankers' order can flip between sets of queries.

**Working rule:** Rerank your strongest retrieval, at a depth fixed before you look at test results, and adopt the reranker only on an established gain on held-out queries. For the store, the general-purpose cross-encoder stays out of the pipeline.

## Score each product with an LLM {#llm-pointwise-reranking}

An LLM can rerank too, in three ways. **Pointwise**, it judges each product alone and returns a label or a score. **Pairwise**, it says which of two products fits the query better. **Listwise**, it orders a whole list in one answer ([Qin et al., 2024](https://arxiv.org/abs/2306.17563)). In one study, on eight datasets from BEIR, a collection of retrieval benchmarks used to test models on data they weren't trained for, pointwise prompts did better with graded answers than with yes or no, because "the lack of intermediate relevance label options may cause the LLM to provide noisy or biased answers" ([Zhuang et al., 2024a](https://arxiv.org/abs/2310.14122)).

The store's LLM, the open model named in [the chapter's opening](#ranking), saw the query and one product at a time: name, class, category, description and attributes ([what the LLM saw](#what-the-llm-saw)). The prompt asks for a label, `exact`, `partial` or `irrelevant`, and "a score from 0 to 100 for how well it matches". Reorder [semantic retrieval](#search-by-meaning)'s top 20 by that score; when two products tie, they keep semantic retrieval's order, a rule fixed with the recording. This is the third of the chapter's [planned comparisons](#ranking), established below p = 0.01:

*Example `llm-pointwise-rerank`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/llm-pointwise-reranking*

The recording made 20 calls per query, and the number of answers without a score is 0. The scores are coarse: the median query gets 4 distinct scores for its 20 products, and a share of 0.390 of all products score 100. In 30 queries, most of the reranked top 10 shares its score with another product, so the tie-break, semantic retrieval's order, decides much of the list. The LLM labels 251 products exact, 345 partial and 4 irrelevant. People judged 310 of the same products exact, 265 partial and 7 irrelevant, and nobody judged 18. So on these lists, with this prompt, the LLM calls fewer products exact than people did. [Chapter 4](#read-llm-error-direction) shows that the direction of an LLM's disagreement with people changes with the pairs judged and the prompt, so don't carry this one elsewhere.

On test, [judged@10](#score-every-test-query) falls from 0.990 to 0.983, with unjudged places in the top 10s going from 3 to 5. The pointwise rerank scores 0.837 against 0.830. No improvement shown with this LLM, prompt and these queries, at a permutation p-value of 0.241 ([all five comparisons](#ranking-decisions)).

**Working rule:** If you rerank pointwise with an LLM, ask for a graded label or a score, count the distinct scores it gives per query, and decide the tie-break in advance: retrieval's order is a safe default. Score the result with human judgments, never with the same LLM's grades.

## Order the 20 products with one LLM prompt {#llm-listwise-reranking}

The third way, a [listwise](#llm-pointwise-reranking) prompt, numbers the candidates and asks the LLM to return the numbers in order of relevance. RankGPT introduced this as permutation generation ([Sun et al., 2023](https://arxiv.org/abs/2304.09542)). A prompt can hold only so many products, so a long list is reranked in a **sliding window**: RankGPT reranks BM25's top 100 with "a window size of 20 and step size of 10", from the bottom of the list up (sections 3.2 and 6.1). The answer has to be a valid ordering, and that can fail: with LLMs of 2023, such as the 20-billion-parameter Flan-UL2, "listwise prompting almost always fails on moderate LLMs", through missing, repeated or refused rankings ([Qin et al., 2024](https://arxiv.org/abs/2306.17563)).

The store's LLM, the open model named in [the chapter's opening](#ranking), saw 20 products per prompt, one window. The prompt shows each product as a short line: name, class, attributes and the first 160 characters of the description. Its last instruction reads: "Order all 20 products from the best match for the query to the worst. Return the product numbers, each exactly once, in JSON." The JSON schema requires exactly 20 numbers, but not 20 different ones, so the recording repairs any answer with a repeated or missing number and flags it. Reorder [semantic retrieval](#search-by-meaning)'s top 20 by the answer the LLM gave when shown them in semantic order, and make the fourth of the chapter's [planned comparisons](#ranking), established below p = 0.01:

*Example `llm-listwise-rerank`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/llm-listwise-reranking*

The recording made 60 listwise calls, two per test query, and the number of answers that needed repair is 0. The rerank changes the first product for 19 queries. [Judged@10](#score-every-test-query) falls from 0.990 to 0.983, with unjudged places in the top 10s going from 3 to 5. The rerank scores 0.819 against 0.830. No improvement shown with this LLM, prompt and these queries, at a permutation p-value of 0.580 ([all five comparisons](#ranking-decisions)).

**Working rule:** Check every listwise answer before you use it: count missing, repeated and unknown numbers, and log how many answers needed repair. Constrain the answer's shape with a schema when your runtime supports one. Fix the window, the step and the order you show the products in before you measure, because the order changes the answer, as the [next check](#llm-position-bias) shows.

## Reverse the input to measure positional bias {#llm-position-bias}

A [listwise answer](#llm-listwise-reranking) can suffer from **positional bias**: an LLM's tendency to let a product's place in the prompt affect its rank, not the click [position bias](#clicks-are-not-judgments) of shoppers. "Large language models (LLMs) exhibit positional bias in how they use context, which especially complicates listwise ranking" ([Tang et al., 2024](https://arxiv.org/abs/2310.07712)). On TREC DL19, the 2019 queries of TREC's Deep Learning track, a passage-ranking benchmark, gpt-3.5-turbo reranked BM25's top 100 to an nDCG@10 of 65.80 when shown BM25's order, 32.77 when shown it reversed and 25.17 when shown a random order ([Sun et al., 2023, Table 5](https://arxiv.org/abs/2304.09542)). The direct check is to show the same products in two orders and compare the answers. **Kendall's tau** measures how alike two orderings are, from 1 for the same order to −1 for the reverse, by counting the pairs they put the same way round ([chapter 4](#system-order-human-versus-llm)).

The recording ran the store's LLM, the open model named in [the chapter's opening](#ranking), on each test query's listwise prompt twice: with [semantic retrieval](#search-by-meaning)'s top 20 in semantic order, as the [listwise rerank](#llm-listwise-reranking) used, and reversed. Before you run the comparison, predict: for how many of the 30 test queries will the LLM put the same product first both times?

*Example `listwise-position-bias`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/llm-position-bias*

The same product comes first for 13 queries. The two answers agree with a mean tau of 0.311, and per query it runs from -0.484 to 0.811. Their top 10s share 6.967 products on average, and as few as 3. The answers also lean toward the order shown. Each answer's tau against its own input order is 0.414 for the semantic order and 0.045 for the reversed one. An LLM that ignored the order would give the same answer both times, so its reversed answer would have a tau of -0.414 against the reversed input. The reversed answer sits far nearer its own input order than that: positional bias, for this model, prompt and these queries. The reversed answer scores 0.826 nDCG@10; it is not a planned comparison, so the chapter doesn't test it.

If you predicted that a capable model reads the products and finds the same best match whichever way they come, notice that it did so for a share of 0.433 of the queries.

Three remedies exist. Pairwise ranking prompting asks about each pair twice: "for each pair of documents, we will inquire the LLM twice by swapping their order", and it counts a disagreement as a tie ([Qin et al., 2024](https://arxiv.org/abs/2306.17563)). Permutation self-consistency reranks several shuffled orders and aggregates the answers, which improved scores "by up to 7-18% for GPT-3.5 and 8-16% for LLaMA v2 (70B)" (Tang et al., 2024). And rerankers fine-tuned for listwise ranking, such as the open RankZephyr, are reported to be "resilient against variations in initial document ordering" ([Pradeep et al., 2023](https://arxiv.org/abs/2312.02724)); the store didn't record one.

**Working rule:** Before you trust a listwise LLM reranker, run each query in at least two orders and report how much the answers agree. When agreement is low, aggregate several orders or ask each pair in both orders, and count those calls against [your budget](#rerank-depth-from-budget). In production, show the products in retrieval's order every time, so that the same list at least gets the same answer.

## Set the rerank depth from a budget {#rerank-depth-from-budget}

A search pipeline runs in stages, each slower and given fewer candidates than the last, and every reranker in this chapter adds one. Multi-stage rankers offer "the ability to trade off quality against latency by controlling the admission of candidates into each pipeline stage" ([Nogueira et al., 2019](https://arxiv.org/abs/1910.14424)). So the **rerank depth**, how many products the reranker reads per query, is a budget decision. Timings "depend on hardware and running-time choices" ([Peng et al., 2025](https://arxiv.org/abs/2507.06223)), so this section counts what drives them instead: model calls and the text they read, per query, multiplied by the model's size. The store's cross-encoder has 149M parameters ([model card](https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base)), and its LLM about 12 billion ([model card](https://ai.google.dev/gemma/docs/core/model_card_4)), some 80 times as many.

In the store, count calls and characters per test query for each reranker at depth 20, from the products' text and the recorded prompts, plus the calls two designs the store didn't record would need:

*Example `reranker-prompt-sizes`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rerank-depth-from-budget*

| Reranker, top 20 | Model calls per query | Characters read per query |
| --- | --- | --- |
| Cross-encoder | 20 | 9,911 |
| LLM, pointwise | 20 | 17,864 |
| LLM, listwise | 1 | 5,973 |

Pointwise repeats the instructions and shows each product in full, so it reads the most text, in independent calls. Listwise reads the least, in one call, but must write out 20 numbers in order. Pairwise prompting over all pairs in both orders would take 380 calls per query, and RankGPT's sliding window over a top 100 would take 9. In one published measurement on [TREC DL19](#llm-position-bias), reranking BM25's top 100 with Flan-T5-XL on one RTX A6000 GPU, pointwise yes-or-no prompting scored 0.650 nDCG@10 at 1.5 seconds per query, and pairwise prompting over all pairs 0.713 at 254.9 seconds, with 9,900 LLM calls ([Zhuang et al., 2024b](https://arxiv.org/abs/2310.09497)). [LambdaMART](#lambdamart-on-test-queries) with the cross-encoder as a feature needs a cross-encoder score for every candidate, a median of 131 pairs per query.

For the cross-encoder, cost grows in step with depth, so the question is where quality stops growing. Sweep the depth on the train queries:

*Example `rerank-depth-on-train`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rerank-depth-from-budget*

From semantic retrieval's 0.772, reranking the top 5 gives 0.782 and the top 20 0.802. The top 30 adds +0.002 for half as many pairs again. Deeper, it falls: 0.793 at 50 and 0.788 at 75. The curve flattens between 20 and 30, near the depth fixed to match the LLM recording. On test, [the depth-20 rerank](#rerank-semantic-with-cross-encoder) showed no improvement, so for the store the cheapest reranker, none, is also the one to keep.

**Working rule:** For each reranker you consider, count calls and characters per query at each depth, and set the depth on train queries. A rule of thumb, not a measurement: rerank only as deep as the depth where train nDCG@10 stops improving, because every product past it costs the same and adds nothing. Then time that configuration on your own hardware and traffic, and keep the stage only if it fits the latency budget.

## Distill the cross-encoder into a small ranker {#distill-the-cross-encoder}

A reranker too slow for [the budget](#rerank-depth-from-budget) can teach a fast one. **Distillation** trains a small model, the **student**, to imitate a large one, the **teacher**. Hinton et al. call it "distilling the knowledge in an ensemble of models into a single model" ([Hinton et al., 2015](https://arxiv.org/abs/1503.02531)). In ranking, the teacher's scores become the student's labels. When the two models' scores have different scales, because "different ranking architectures tend to produce output scores in different magnitudes", the student can learn the margin between two products' scores instead, with a loss called Margin-MSE ([Hofstätter et al., 2020](https://arxiv.org/abs/2010.02666)). Distillation also runs from LLMs down: in RankGPT, "a distilled 440M model outperforms a 3B supervised model on the BEIR benchmark" ([Sun et al., 2023](https://arxiv.org/abs/2304.09542); [BEIR](#llm-pointwise-reranking)), and in one product-search study of queries with superlatives, where "direct LLM-based reranking faces prohibitive latency", lightweight models took over the LLM's interpretations ([Zhu et al., 2025](https://arxiv.org/abs/2511.13994)). The teacher needs no human labels and labels every candidate.

In the store, the teacher is the cross-encoder. The student is a LightGBM regression on the 7 [features](#ranking-features) that need no model call beyond the one retrieval already makes: everything but `cross_encoder`. Its label is the teacher's raw score, which a tree regression can match on the teacher's own scale. It ranks the same [candidates](#ranking-features), in `product_id` order, with trees the size [chosen for LambdaMART](#train-lambdamart). First, compare the student with a LambdaMART model trained on human grades with the same features, by cross-validation on the train queries:

*Example `distillation-on-train`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/distill-the-cross-encoder*

The student scores 0.791, and the teacher's own order of the candidates 0.785. The model trained on human grades scores 0.747, below semantic retrieval's 0.772, and the student minus it is 0.044, with a permutation p-value of 0.002. That is a tuning check on train queries, not evidence. On these queries, with these features, the teacher's labels on every candidate trained a better ranker than people's grades with unjudged candidates counted as 0.

Then fit the student on the train queries, with early stopping on the same held-out train queries as [LambdaMART](#lambdamart-on-test-queries), and make the last of the chapter's [planned comparisons](#ranking), established below p = 0.01:

*Example `distilled-ranker-on-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/distill-the-cross-encoder*

The teacher labels all 6896 train candidates, 1975 of them judged by nobody. Early stopping keeps 202 trees. The student leans on `similarity`, which takes a share of 0.812 of the gain, ahead of `name_match` at 0.126 and `bm25` at 0.055. On the test candidates, its scores agree with semantic similarity at a mean tau of 0.753 per query, and with the teacher's at 0.466. So the student learned mostly semantic retrieval's order, nudged toward the teacher's by name and BM25 matches.

On test, [judged@10](#score-every-test-query) is 0.987 for the student and 0.990 for semantic retrieval, with 4 and 3 unjudged places in the top 10s. The distilled ranker scores 0.826 against semantic retrieval's 0.830. No improvement shown, with a permutation p-value of 0.720 ([all five comparisons](#ranking-decisions)). The teacher's own order of the test candidates scores 0.782, which the chapter didn't plan to test.

**Working rule:** Distil when a reranker earns an established gain but costs too much per query: label every candidate of your train queries with the teacher, train the student on features you can compute without the teacher, and test the student against your retrieval on held-out queries. Read the student's gain importance: when retrieval's own score dominates it, the student is mostly your retrieval. Use margins between pairs when the student can't match the teacher's scale. The store has no teacher that beats semantic retrieval yet, so it keeps the code and doesn't ship the student.

## What goes wrong in production {#ranking-in-production}

A live ranker computes features and calls models while the shopper waits, with code and model versions that can drift from those it was trained and tested with.

**Features drift between training and serving.** If the live system tokenizes differently, rescales BM25 or upgrades the embedding model, the learned weights meet different numbers, and nothing raises an error. Compute features with one shared code path, and log them with each served ranking.

**Row order leaks into training.** LightGBM's lambdarank starts from the order of its input rows, and a ranking breaks ties somehow. A file sorted by a reranker's score hands the model that reranker's ranking. Sort candidates by an ID, or shuffle them with a fixed seed, before every fit and every scoring.

**Judgments come from a pool.** WANDS judged the products that shoppers' clicks, a lexical engine, a neural retriever and a query classifier put forward ([chapter 2](#pooled-judgments)). Counting unjudged candidates as irrelevant teaches a model to demote whatever those systems didn't find. Check [judged@10](#score-every-test-query) for every ranker you add, and have its unjudged products judged before you trust a gain.

**LLM judges favour LLM rerankers.** In one study, "the system rankings obtained by LLM assessors overestimate LLM-based re-rankers by 9 to 17 positions on average" ([Fröbe et al., 2025](https://eprints.gla.ac.uk/352747)), and using LLMs both to rank and to judge is circular, "illustrating how reliance on LLM-based assessments can distort system rankings" ([Clarke and Dietz, 2024](https://arxiv.org/abs/2412.17156)). Score LLM rerankers with human judgments, as this chapter does.

**An LLM reranker belongs to one model version and one prompt.** A different digest (the hash that identifies the exact weights), quantization (the precision the weights are stored at) or prompt wording can change every answer, and with [positional bias](#llm-position-bias), so can a change in retrieval's order. The LLM recording's manifest records the digest and both prompts verbatim; re-measure whenever either changes.

**Unfamiliar queries can do worse.** A comparison of 22 reranking methods found that LLM rerankers do better on familiar queries, while "their generalization ability to novel queries varies" ([Abdallah et al., 2025](https://arxiv.org/abs/2508.16757)). Watch queries about products and styles newer than the model's training data.

**Every reranker adds a call on the shopper's path.** Count calls and text per query, as in [the budget](#rerank-depth-from-budget), set a timeout, and fall back to retrieval's order when the reranker doesn't answer in time.

**Working rule:** Log features and model versions with every ranking, put candidates in an order that carries no information, score on human judgments, check judged@10, and give each reranking stage a time limit and a fallback.

## Decisions this chapter made {#ranking-decisions}

The chapter made each choice below on the train queries, and only an established planned comparison on the test queries could change the store's search.

- **5 planned test comparisons** against semantic retrieval, on human judgments, established below 0.01.
- **Candidates: the union of BM25's and semantic retrieval's top 100,** in `product_id` order, with score ties broken by `product_id`.
- **LambdaMART: `label_gain=[0, 1, 2]`, unjudged candidates as grade 0, 3 leaves at a learning rate of 0.1,** chosen by cross-validation on train, with early stopping on held-out train queries through `eval_X` and `eval_y`. No improvement shown on test, so it isn't used.
- **Rerank depth: semantic retrieval's top 20,** fixed to match the LLM recording; on train, the cross-encoder's curve flattens between 20 and 30. No reranker shows an improvement on test, so none is used.
- **LLM rerankers are scored on human judgments only,** and the listwise one is checked in two input orders. Its answer depends on the order it is shown.
- **Costs are counted, not timed:** calls and characters per query.
- **Distillation: a LightGBM student on the cross-encoder's scores,** with no model call beyond retrieval's. It learns mostly semantic retrieval's order, shows no improvement, and isn't used.
- **The ranker to beat stays semantic retrieval alone,** with BM25, unstemmed, as the baseline.

The 5 planned comparisons, each on nDCG@10 against semantic retrieval's 0.830 on the test queries, established below 0.01:

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
