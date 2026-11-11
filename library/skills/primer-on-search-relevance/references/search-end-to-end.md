---
title: "A Primer on Search Relevance"
chapter: "Search, end to end"
chapter_id: search-end-to-end
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/search-end-to-end
license: CC BY 4.0
attribution: "“Search, end to end,” chapter 1 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/search-end-to-end. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Search, end to end

By the end of this chapter you can build a rough but complete search pipeline for a product catalog, from a shopper's query to an ordered list of products, and measure with one number whether a change to that pipeline helps. Each later chapter takes one part of this pipeline and makes it solid.

This book follows one case study throughout: an online furniture and home-goods store, which we call the store. Shoppers type queries such as `clear shower curtain` or `48 inch kitchen hood` into its search box, and the store wants to know how good its search is and whether a change makes it better. You'll face the same two questions with any search system, so the book tries every method on the store, where you can see what it does to real queries. The store has what it needs to answer them: its catalog, a set of real queries, and people's judgments of which products match which query. In this chapter you search the catalog three ways (by matching words, by matching meaning, and by combining the two), reorder the best results with a slower model, and score each version against those judgments. Not every stage improves the score, and that is the chapter's main lesson: measure every change.

## Load the store's data {#store-data}

Before you can improve a search system, you need three things: the items it searches, the queries people type, and judgments that say which items match which query. Search engines call the items documents. In this book they are products. A **judgment** is a person's label for one pair of a query and a product, and a **grade** is the number that stands for the label. Without judgments, you can look at results and form opinions, but you can't tell a fix from a regression.

The store's data, which the book's examples search and score, is real. It is a sample of WANDS, a public product-search dataset that Wayfair published with a paper at ECIR 2022 ([Chen et al., 2022](https://easychair.org/publications/preprint/wm4R)), under the MIT licence ([licence](https://github.com/wayfair/WANDS/blob/main/LICENSE)). The full dataset has 42,994 products, 480 queries and 233,448 judgments ([repository](https://github.com/wayfair/WANDS)). The queries are a stratified sample of real shopper queries from a quarter's search log in 2021, and each label is the majority vote of up to three trained annotators (Chen et al., sections 4.1 and 5). The script `prep/wands_sample.py` draws the book's sample, and the sample's data card, `examples/data/wands/README.md`, says how. Setup code that many examples need lives in the book's shared modules, short files in `examples/lib/` that you can open and read. The examples load the sample through one of them, `lib.store`:

*Example `load-the-store`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/store-data*

The sample has 12,000 products and 80 queries. It splits the queries once, before any ranker runs: 50 train queries for tuning and 30 test queries for reporting. Every score in this book is reported on the test queries, and nothing is tuned on them. A score on queries you tuned on measures how well you fit those queries, not how well search works.

WANDS judged some pairs more than once. The sample keeps one row per pair, 13,077 in all. When a pair's labels differ, it keeps the lower grade and lists the pair in `label_conflicts.csv`, which holds 7 pairs. Code that scores a ranking reads the judgments through `lib.store.qrels`, which returns them as `{query_id: {product_id: grade}}`. [Chapter 2](#what-relevance-means) reads the judgments closely.

Each judgment is one of three labels, defined by the dataset's authors. Exact: "The surfaced product fully matches the search query." Partial: "It only matches the target entity of the query, but does not satisfy the modifiers for the query." Irrelevant: "The product is not relevant to the query." (Chen et al., section 3.2). The book's grades are 2, 1 and 0. Of the judged pairs, 3,252 are exact, 7,972 partial and 1,853 irrelevant. In this book, **relevant** means exact unless a sentence says otherwise.

Three warnings come with the store's data. First, each query's `query_class` is WANDS's predicted class for it, not a judgment (Chen et al., Table 1): `foutains with brick look` is classed as `Wallpaper`. Treat it as a hint. Second, nobody judged every product for every query. That would have taken about 60 million judgments, so WANDS judged candidates gathered from products shoppers clicked or added to their carts and from several search systems, and stopped when few new exact matches turned up (Chen et al., sections 4.2 and 4.3). A product without a judgment for a query is **unjudged**: unknown, not irrelevant. Third, nearly every product in the sample, 11,917 of 12,000, is judged for at least one of its queries, so the sample holds fewer distractors than a full catalog would: products that compete for a query's top places without matching it.

**Working rule:** Split your queries into train and test before you change anything. Read test results to understand a ranker, but choose and tune every change on train queries, and report on test. Treat unjudged products as unknown. If you have no judgments yet, collect some before you change the ranking.

## Rank products with BM25 {#rank-with-bm25}

Searching the store's catalog takes two jobs. **Retrieval** finds the products that might match a query, out of the whole catalog. **Ranking** puts them in order, best first. The lexical approach does both by comparing the words of the query with the words of each product's text, and scoring the overlap.

BM25 is a lexical scoring function with three parts. A product scores higher when it contains the query's words, and more so for rare words, because a word that appears in few products says more about them. Repeating a word adds less and less, up to a cap, which the BM25 literature calls saturation. And a long text is discounted against a short one, so it can't win by containing more words; the parameter `b` sets how much, from 0 (no discount) to 1 (full) ([Robertson and Zaragoza, 2009](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)). [Chapter 5](#bm25-from-scratch) builds the formula by hand.

The examples use bm25s 0.3.16, a Python library for BM25. By default, it scores with the variant of BM25 used by the Lucene search library, with `k1=1.5` (the saturation setting) and `b=0.75` ([bm25s source](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/__init__.py)). Its scores differ a little from the textbook formula, but a reproducibility study on three newswire collections found no significant differences in effectiveness between BM25's variants ([Kamphuis et al., 2020](https://cs.uwaterloo.ca/~jimmylin/publications/Kamphuis_etal_ECIR2020_preprint.pdf)). Before scoring, bm25s splits text into tokens: it lowercases, keeps words of two or more characters, removes English stopwords such as `and`, and doesn't reduce words to a common stem ([bm25s tokenizer](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/tokenization.py)). The book's BM25 ranker, `lib.lexical.LexicalSearch`, indexes each product's name, class, category and description, joined into one text.

In the store, take the test query `clear shower curtain`. A shopper who types it wants a transparent curtain, and the catalog holds many curtains that aren't clear, plus accessories that share the words. Here are BM25's top 10 products:

*Example `first-bm25-search`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rank-with-bm25*

Most of the ten are shower curtains or liners, but the last few are shower curtain hooks. BM25 found the words "shower curtain" in the hooks' names and scored them almost as high as the curtains, because it matches words, not things: it has no idea that a hook isn't a curtain. Whether the curtains are clear, the output can't tell you. For that you need the store's judgments.

**Working rule:** Start with BM25 at the library's defaults as your baseline. It needs no training data and no model, and when it goes wrong you can see which words caused it. Leave its parameters alone until you can measure a change on [train queries](#store-data). When shoppers and products use different words for the same thing, add semantic retrieval.

## Check the results against the judgments {#check-against-judgments}

A ranking means little until you know what the shopper wanted. Judgments supply that, one pair at a time. They are better evidence than clicks for this purpose: WANDS's authors note that "User behavior log data suffer from positional biases and would favor the rankings similar to the production system" (Chen et al., section 3.1). A shopper clicks what is shown first, so clicks mostly confirm the ranking you already have.

For the store's query `clear shower curtain`, put each of BM25's top 10 products next to its judgment. A product nobody judged for this query shows as `unjudged`:

*Example `judge-first-results`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/check-against-judgments*

The top 10 holds 4 exact products, 3 partial ones, 3 irrelevant ones (the hooks) and 0 unjudged ones. The first result is partial: by [the dataset's definition](#store-data), it matches the thing the shopper asked for, a shower curtain, but not the modifier, clear.

The judgments also tell you what the best possible top 10 would hold. The judges labelled 253 products for this query, 12 of them exact. So an ideal ranking could fill all ten places with exact products, and BM25 filled 4. That gap is what a metric has to measure.

Reading results this way shows you the kind of mistake a ranker makes. Here, BM25 matched the words of an accessory and missed a modifier. An average over many queries hides that, and the mistakes you see are the ones you can fix.

**Working rule:** Before you compute any metric, read the top results of five or ten queries next to their judgments. Look for patterns: accessories, missed modifiers, wrong sizes. When several top results are unjudged, have them judged before you trust a score for that query.

## Score one ranking with nDCG@10 {#score-one-ranking}

To compare rankings, you need one number per ranking. It should reward matching products, and exact ones more than partial ones, and count a product near the top more than one near the bottom, because shoppers read from the top. **Normalized discounted cumulative gain at 10**, nDCG@10, does all three.

In words: each of the top 10 results earns a gain equal to its [grade](#store-data): 2 for exact, 1 for partial, 0 for irrelevant. The gain is divided by a discount that grows with position: log2 of the position plus one, so the first result counts in full and the third counts half. Adding up the discounted gains gives the discounted cumulative gain, DCG. Dividing by the DCG of the best possible top 10 for that query, the ideal DCG, puts the score between 0 and 1, where 1 means no better top 10 exists. An unjudged product earns 0.

```text
DCG@10  = sum over positions i from 1 to 10 of  grade(i) / log2(i + 1)
nDCG@10 = DCG@10 / ideal DCG@10
```

The WANDS paper scores search with nDCG@10 too, with gains of 1.0, 0.5 and 0 for exact, partial and irrelevant (Chen et al., section 6). The book's grades are twice those gains, which doubles both DCG and ideal DCG, so nDCG doesn't change.

Take [BM25's ranking of `clear shower curtain`](#check-against-judgments): a partial product first, then exact and partial curtains, then three irrelevant hooks. Compute DCG, the ideal DCG and their ratio by hand, then compare with `lib.metrics`, the shared module that holds the book's metrics:

*Example `ndcg-for-one-query`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/score-one-ranking*

The ranking earns a DCG of 5.586. The best possible top 10 holds only exact products and earns 9.087. Their ratio, 0.615, matches `ndcg_at_k` from `lib.metrics`, which gives 0.615. The partial product at position 1 costs the most of any single result, because it holds the place with no discount. Each hook costs less, because it sits lower, but together the hooks cost more.

That one number sums up what the judgments showed: a ranking that found the right kind of product and made two kinds of mistake. You can compute it for any ranking of any judged query, and compare.

**Working rule:** We recommend nDCG@10 as your headline metric when your judgments are graded and the first page of results matters most, as it does in a store's search. When you have only yes-or-no labels, or when shoppers look at one result only, another metric fits better. [Chapter 3](#choose-a-ranking-metric) builds the alternatives and says when to choose each.

## Score every test query {#score-every-test-query}

One query is an anecdote. To judge a ranker, score it on a fixed set of queries and average: in this book, the test queries. The rankings for every query in a set form a **run**, written as `{query_id: [product_id, ...]}`, best first. `lib.metrics.evaluate` scores a run against the judgments and returns one row per query.

Next to nDCG@10, `evaluate` reports **judged@10**: the share of the top 10 that has any judgment for the query. Because unjudged products count as grade 0, a low judged@10 means the score is partly a guess. It can't tell an irrelevant product from a relevant one that nobody judged.

In the store, run [BM25](#rank-with-bm25) on every test query, keeping the top 100 products for each, and score the run:

*Example `bm25-test-scores`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/score-every-test-query*

Over 30 test queries, BM25 averages an nDCG@10 of 0.725, with a mean judged@10 of 0.927. That average is the store's first measured result, and every later ranker is compared with it.

The average hides a wide spread. Scores run from 0.212 to 1.000, with a median of 0.687, and 4 queries score a perfect 1. The lowest-scoring query, `beach blue headboard`, has a judged@10 of 0.500. Another low scorer, `outdoor light fixtures`, has a judged@10 of 0.200: BM25's top 5 holds an exact outdoor light, then light bulbs that share the query's words and that nobody judged for this query. A bulb isn't a light fixture, so here the grade of 0 is probably fair. But the metric can't know that, and for another ranker or another query, unjudged products may be good ones.

**Working rule:** Report the mean nDCG@10 over the test queries with mean judged@10 beside it, and read the lowest-scoring queries every time you score a run. When one ranker's judged@10 is lower than another's, find out why before you compare their nDCG: the gap may come from missing judgments, not worse results.

## Search by meaning with embeddings {#search-by-meaning}

Lexical retrieval fails when the shopper's words and the product's words differ, or when shared words mean different things, as with [the hooks that BM25 ranks](#rank-with-bm25) for `clear shower curtain`. **Semantic retrieval** compares meanings instead. It rests on embeddings. An **embedding** is a list of numbers, a vector, that a neural network computes for a piece of text. The network is trained so that texts with similar meanings get vectors pointing in similar directions. You embed every product once, ahead of time. At search time, you embed the query and return the products whose vectors are closest to it. With every vector scaled to length 1, closeness is the dot product of two vectors, which equals the cosine of the angle between them.

Embedding the products ahead of time is what makes this fast. In the paper that introduced Sentence-BERT, finding the most similar pair among 10,000 sentences took about 65 hours on a V100 GPU when BERT read every pair. Embedding each sentence once and comparing the embeddings took about 5 seconds, almost all of it spent computing the embeddings: the comparison itself took about 0.01 seconds ([Reimers and Gurevych, 2019](https://arxiv.org/abs/1908.10084)).

The store's embeddings come from the open model `Snowflake/snowflake-arctic-embed-m-v1.5`. Examples never call a model, so that every example runs offline and gives the same output each time. Instead, a **recording**, here the script `recordings/embeddings.py`, runs the model once and saves its vectors, and the examples read them offline through `lib.recorded`. We chose this model because it is open and under the Apache 2.0 licence, so anyone can download the pinned version and rerun the recording. The recording adds to each query the instruction that the model's card asks for ("Represent this sentence for searching relevant passages:") and embeds products as they are ([model card](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v1.5)). The book's semantic ranker, `lib.semantic.SemanticSearch`, multiplies every product vector by the query vector and sorts the results. [Chapter 6](#exact-nearest-neighbours-numpy) builds it step by step.

For `clear shower curtain`, semantic search returns:

*Example `first-semantic-search`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/search-by-meaning*

Each product is a vector of 768 numbers. The top 10 holds 5 exact products, against [BM25's 4](#check-against-judgments), and 0 irrelevant ones. Its nDCG@10 is 0.793, against [BM25's 0.615](#score-one-ranking). Notice how close the similarities are: the first and the tenth differ by 0.035. Semantic search always returns something, ranked by small differences.

One query can mislead, so compare the two rankers on every test query:

*Example `compare-lexical-semantic`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/search-by-meaning*

Semantic retrieval averages 0.830 against BM25's 0.725. Its judged@10 of 0.990 is higher than BM25's 0.927, so part of BM25's deficit could come from products nobody judged. For [`outdoor light fixtures`](#score-every-test-query), at least, those products are light bulbs, and a score of 0 is fair. Semantic retrieval is better on 21 queries, BM25 on 7, and 2 are tied. The test set has only 30 queries, so [chapter 3](#compare-runs-in-a-harness) tests whether a gap like this one is larger than chance.

BM25 is better on 2 of the 2 test queries that give a size in inches. Exact tokens such as sizes and model numbers may favour matching words, but a count this small can't show a pattern. On the train queries that contain a digit, BM25 is better on 1 of 5 ([Find the queries each retriever wins](#queries-each-retriever-wins)), and the embedding model matches digits too, as text ([Check queries that contain digits](#embeddings-match-digits)). A theoretical result shows a limit of single vectors: Weller et al. prove that an embedding's dimension limits which combinations of top results a single vector can return. On LIMIT, a dataset they built to test that limit, BM25 finds 93.6% of the relevant items in its top 100, and the best single-vector model 18.9%. On a variant of LIMIT with words replaced by synonyms, BM25's score drops by more than 89% ([Weller et al., 2025](https://arxiv.org/abs/2508.21038)). Lexical and semantic retrieval fail in different places.

**Working rule:** Add semantic retrieval when shoppers describe what they want in their own words. Don't assume lexical retrieval wins on exact terms such as sizes, brands and model numbers: before you rely on it there, count which retriever wins the train queries that contain them. On this data, semantic retrieval alone scores highest so far, so it is the ranker to beat.

## Fuse two rankings with reciprocal rank fusion {#fuse-with-rrf}

Because lexical and semantic retrieval fail in different places, **hybrid retrieval** combines a ranking from each, here BM25's and semantic retrieval's, hoping to keep the strengths of both. Their scores can't be added directly: a BM25 score has no fixed range and depends on the query's words, while a cosine similarity lies between -1 and 1, so a sum would mostly follow whichever is larger. Reciprocal rank fusion (RRF) avoids the problem by using ranks only. Each product scores, for every ranking that contains it, 1 divided by the sum of a constant and its rank, and the scores add up:

```text
RRF(product) = sum over rankings r of  1 / (k + rank of product in r),   with k = 60
```

The constant k flattens the top: with k = 60, rank 1 earns 1/61 and rank 10 earns 1/70. So a product near the top of both rankings beats one at the very top of only one. The authors fixed k = 60 in a pilot study and found that "the choice was not critical" ([Cormack et al., 2009](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)). They fused two kinds of runs: submissions to TREC, the Text REtrieval Conference's shared evaluations, and 30 configurations of one search system. In those experiments, RRF beat the best individual run by 4% to 5% on average in mean average precision (MAP), which averages, over queries, the precision at the position of each relevant result. That's a different setting from fusing one lexical and one semantic ranking, and a later study of hybrid search found that a tuned weighted sum of normalized scores beats RRF ([Bruch et al., 2023](https://arxiv.org/abs/2210.11934)). [Chapter 7](#tune-blend-on-train) tunes both on train queries. Here, RRF runs untuned.

RRF is short enough to write by hand, as two functions: `rrf_scores` scores one query's products, and `reciprocal_rank_fusion` orders them for every query, putting products with equal scores in `product_id` order so that neither ranking wins ties by being passed first. The example fuses BM25's and semantic retrieval's top 100 for every test query, checks the scores of the two products that `clear shower curtain` puts first, and scores the hybrid run.

Before you read the output, predict the hybrid's mean nDCG@10. [BM25 scores 0.725 and semantic retrieval 0.830](#search-by-meaning). Will their fusion score above semantic retrieval, between the two, or below BM25?

*Example `hybrid-rrf`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/fuse-with-rrf*

The first fused product, `woolley vinyl solid color single shower curtain`, is at rank 3 in BM25's ranking and rank 1 in semantic retrieval's, so by hand its score is 1/(60 + 3) + 1/(60 + 1) = 0.03227, the same as `rrf_scores` gives. The second, `woolley vinyl single shower curtain`, is at rank 2 in BM25's ranking and rank 2 in semantic retrieval's, and scores 0.03226, so it comes second.

The hybrid run scores 0.812: above BM25, and below semantic retrieval alone. It beats semantic retrieval on 9 queries, loses on 14 and ties on 7, and its judged@10 is 0.980. On 30 test queries, a gap this small may be noise, and [chapter 3](#compare-runs-in-a-harness) tests whether it is. So the finding is that fusion didn't improve on semantic retrieval here, not that it made search worse. Why it didn't help is a question for chapter 7, which [checks each retriever before fusing](#check-each-retriever-before-fusing) and [tunes the blend on train queries](#tune-blend-on-train).

If you predicted "above semantic retrieval", notice that combining two rankings doesn't guarantee a gain. Fusion is a change like any other, and it has to be measured.

**Working rule:** Measure each retriever alone before you fuse them. Use RRF with k = 60 as an untuned default, and keep the fused ranking only if it beats the best single retriever on held-out queries. When one retriever is much weaker, try weighting the rankings or tuning k on train queries instead of accepting equal votes. Chapter 7 tries both on the store's data, and none of the tuned blends it reports on the test queries beats semantic retrieval ([Report the tuned blends on test queries](#report-blends-on-test)).

## Rerank the top 50 with a cross-encoder {#rerank-with-cross-encoder}

Every stage so far has been retrieval, which has to score every product in the catalog for every query and so must be cheap. **Reranking** reorders a short list from retrieval with a slower model, one that can afford to look at the query and each product together because it only sees a few dozen products.

One kind of reranking model is a **cross-encoder**. It reads the query and the product text together, as one input, and outputs one relevance score for the pair, scoring each pair independently ([Nogueira and Cho, 2019](https://arxiv.org/abs/1901.04085)). An embedding model reads the product alone, so its vectors can be computed ahead of time. A cross-encoder needs the query, so it can't compute anything ahead of time, and running it on every pair costs time: the slow side of [the Sentence-BERT comparison](#search-by-meaning) was BERT reading every pair of sentences as a cross-encoder. So a cross-encoder reranks a shortlist that a cheaper first stage retrieves (Nogueira and Cho, section 2; [Retrieve & Re-Rank](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)). In return for that cost, it can relate every word of the query to every word of the product through attention, the part of the model that lets each word draw on the others in its input. In the words of [Reimers and Gurevych (2019, section 4.3)](https://arxiv.org/abs/1908.10084), "BERT is able to use attention to compare directly both sentences". In 2019, on the MS MARCO passage benchmark, reranking BM25's top 1,000 passages this way improved MRR@10, a measure of how high the first relevant passage lands, by 27% relative to the best earlier result (Nogueira and Cho).

A cross-encoder is a language model, but not a **large language model (LLM)**. An LLM is a model trained on large amounts of text to generate text in response to a prompt. Later chapters use LLMs to judge, rewrite and rerank. A cross-encoder generates nothing: it outputs one number.

The store's cross-encoder is the open model `Alibaba-NLP/gte-reranker-modernbert-base`, chosen for the same reason as [the embedding model](#search-by-meaning): it is open and under the Apache 2.0 licence, so anyone can rerun the recording. Its recording, `recordings/cross_encoder.py`, saves the model's scores once, for every product in the union of BM25's and semantic retrieval's top 100 for each query, so every product in the hybrid's top 50 has a score. The example reorders the top 50 of [the hybrid run](#fuse-with-rrf), BM25 and semantic retrieval fused with RRF, by those scores, keeps the rest in place, and scores the result:

*Example `cross-encoder-rerank`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rerank-with-cross-encoder*

Reranking scores 0.798, against 0.812 for the hybrid run it started from. It improves 11 queries and hurts 12. As with fusion, a gap this small on 30 test queries may be noise, which [chapter 3](#compare-runs-in-a-harness) tests: the finding is that this reranker didn't improve the ranking here. Across the chapter, on the test queries:

| Ranker | nDCG@10 | judged@10 |
| --- | --- | --- |
| BM25 | 0.725 | 0.927 |
| Semantic | 0.830 | 0.990 |
| Hybrid (RRF, k = 60) | 0.812 | 0.980 |
| Hybrid, top 50 reranked | 0.798 | 0.980 |

To see what reranking does to a single query, look at one where it lowered the score, `refrigerator with ice an water in door`:

*Example `rerank-one-query`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rerank-with-cross-encoder*

For this query, the reranked top 5 are refrigerators whose names say `ice maker` or `water dispenser`, and the judges marked them partial: they match the thing asked for, a refrigerator, but not the modifier, ice and water in the door. The first exact product in the hybrid run, a French-door refrigerator, gets the lowest cross-encoder score of the hybrid's top 5. After reranking, the first exact product sits at rank 9 instead of 3, and nDCG@10 for this query drops from 0.660 to 0.533.

The judges marked that refrigerator exact, so by the dataset's definition it fully matches the query. Yet its text says nothing about ice or water, so no model that reads only the text could rank it on that modifier. WANDS's judges saw each product's image and web page as well as its name ([annotation guidelines](https://github.com/wayfair/WANDS/raw/main/Product%20Search%20Relevance%20Annotation%20Guidelines.pdf)), which probably let them see what the text doesn't say. A general-purpose reranker has never seen this store's judgments. [Chapter 9](#train-lambdamart) trains rankers on the train queries' judgments.

**Working rule:** Rerank a shortlist, here 50 products, because the cost grows with every pair. Adopt a reranker only when it beats the best retrieval alone on held-out queries. This one didn't improve on the hybrid run or on semantic retrieval, so the store's best pipeline so far is semantic retrieval alone. Before you give up on reranking, try a different depth, or a ranker trained on your own judgments. Chapter 9 tries both on the store's data, and neither shows an improvement over semantic retrieval on the test queries ([Set the rerank depth from a budget](#rerank-depth-from-budget), [Report LambdaMART on the test queries](#lambdamart-on-test-queries)).

## What goes wrong in production {#search-end-to-end-in-production}

**The tokenizer drops words without telling you.** bm25s's default tokenizer keeps only tokens of two or more characters and doesn't stem words ([bm25s tokenizer](https://raw.githubusercontent.com/xhluca/bm25s/0.3.15/bm25s/tokenization.py)). Run it on a train query and a test query, and count the products it can't match:

*Example `tokenizer-drops-terms`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/search-end-to-end-in-production*

The `4.5` in `ge top loading washer 4.5` disappears, because `4` and `5` are one character each, so that number plays no part in the ranking. And `chairs` matches only products that say `chairs`: 895 products do, while 359 say `chair` and never `chairs`, and none of those can match that word of `bistro table and chairs`. Neither case raises an error. [Chapter 5](#split-text-into-terms) shows both problems and [adds stemming](#stem-word-forms).

**Unjudged results look like failures.** A ranker that surfaces products nobody judged gets lower scores than it may deserve, and a ranker that surfaces the judged ones gets an advantage. Report [judged@10](#score-every-test-query) with every score, and have new products judged when it drops.

**Scores from a sample are probably optimistic.** The sample keeps 12,000 products, nearly all judged for some query. The full WANDS catalog has 42,994 ([repository](https://github.com/wayfair/WANDS)), and a store's catalog may be far larger, with more near misses competing for the top 10. Nothing in this chapter measures that, but expect lower scores on a full catalog. Don't compare the scores here with the WANDS paper's either: it ran the BM25 of Solr, a search server, over product titles and descriptions (Chen et al.).

**Model outputs belong to one model version.** Product and query embeddings must come from the same model at the same version, or their similarities aren't comparable. Change the model and you re-embed the whole catalog. Each folder in `examples/data/recorded/` has a `manifest.json` that pins the model and its version.

**Reranking costs time on every query.** Product embeddings are computed once. A cross-encoder runs on every pair, for every query, while the shopper waits. In this chapter, a recording script computes the scores ahead of time on a GPU, which hides that cost. Chapter 9 counts what each rerank depth costs ([Set the rerank depth from a budget](#rerank-depth-from-budget)).

**Working rule:** Check the tokens your queries become, track judged@10, and record the model version next to every vector you store.

## Decisions this chapter made {#search-end-to-end-decisions}

Each choice below has a reason, and each is a default that a later chapter tests on the train queries before changing it.

- **Report on test, tune on train.** Every score in this chapter is on the 30 test queries. This chapter tunes nothing; later chapters tune on the 50 train queries only.
- **Headline metric: nDCG@10, with judged@10 beside it.** The grades serve as gains, unjudged products count as grade 0, and judged@10 shows when that assumption carries weight.
- **Baseline: BM25 at bm25s's defaults,** `k1=1.5` and `b=0.75`, over each product's name, class, category and description. Tuning waits until it can be measured on train queries.
- **Semantic retrieval from recorded embeddings** of one open model, compared by dot product of unit-length vectors, so every example runs offline and gives the same output each time. Choosing between models is a later question.
- **Hybrid retrieval: RRF with k = 60 and equal weights, untuned,** as its authors used it.
- **Rerank depth: the hybrid's top 50,** scored by a recorded cross-encoder, so every reranked product has a recorded score. In a live store, depth is a cost decision as much as a quality one.
- **The ranker to beat is semantic retrieval alone,** because on this data neither fusion nor this reranker improved on it. [Chapter 3](#compare-runs-in-a-harness) tests whether gaps like these are larger than chance, in an evaluation harness. Every later change is tested in that harness against the ranker it changes, and adopted only if it beats the ranker to beat.
