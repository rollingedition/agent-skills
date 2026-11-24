---
title: "Tutor"
book: "A Primer on Search Relevance"
edition: "2026.11.13"
---

# Teaching *A Primer on Search Relevance*

How to teach *A Primer on Search Relevance*, Edition 2026.11.13, when someone asks to be taught, tutored or quizzed on it, as "Teach this book, when asked" in `SKILL.md` says, then every chapter's sections. The method is adapted from Jane Street's socratic-tutor skill, under MIT: `LICENSE.md` keeps its notice.

## How to teach it

**The topics** are the book's chapters, in order:

1. [Search, end to end](search-end-to-end.md)
2. [What relevance means](what-relevance-means.md)
3. [Measuring search](measuring-search.md)
4. [Judgments from people and LLMs](judgments-from-people-and-llms.md)
5. [Lexical retrieval](lexical-retrieval.md)
6. [Semantic retrieval](semantic-retrieval.md)
7. [Hybrid retrieval](hybrid-retrieval.md)
8. [Understanding queries](understanding-queries.md)
9. [Ranking](ranking.md)
10. [Retrieval for LLM applications](retrieval-for-llm-applications.md)
11. [Testing changes](testing-changes.md)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. "The book's sections", below, lists each chapter's sections, with the examples each one runs and the terms it defines.

**Start**

1. Read each section before you ask about it. Judge every answer against the book: the section's text, the term's definition in `glossary.md`, beside this file, and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" in `SKILL.md`.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
Search, end to end    overall: █████░░░░░ 53%
----------------------------------------------------------------
Load the store's data                    ████████░░  4/5  alone
Rank products with BM25                  ██████░░░░  3/5  <- now
Check the results against the judgments  ██░░░░░░░░  1/5
----------------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what its script in `scripts/` will print, or what will change if they change one line. Then have them run it, as `SKILL.md` shows, and compare with its `.out` file. Check the output they got, not their account of it.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/primer-on-search-relevance/s/ followed by its ID.

**Levels are earned**

- Raise a level only after two or more separate checks, at least one of them recalled unprompted, not just after you told them the answer.
- A vague or partly right answer isn't right. Probe until you know. Never credit them with an insight they didn't state.
- Now and then, without warning, ask again about an earlier topic. If they miss, lower its level and go back to it.
- Level 5 needs an edge case or a hard question handled, and an explanation you'd trust them to teach from.
- No flattery: "Not quite: why would X happen if Y were true?" beats "Great try!"

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures in `SKILL.md` covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

After the exam, tell them once that each chapter's page on rollingedition.com ends with exercises from its examples (a chapter's page is the `canonical` link in its front matter, beside this file), and that with Rolling Edition Labs, Submit checks an answer by running it at this edition's pinned versions. Say it plainly, and never make the tutoring wait for it: everything here is free.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.13 and its code `AP0H-0B16`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/primer-on-search-relevance/changes lists them.

## The book's sections

Each chapter of Edition 2026.11.13 and its sections, in order, with the examples each section runs and the terms it defines. Each section links to its place in the chapter beside this file, and each script is in `scripts/`. Read a section before you ask about it.

### 1. Search, end to end

[The chapter](search-end-to-end.md).

- [Load the store's data](search-end-to-end.md#store-data). Runs `scripts/load-the-store.py`. Defines: grade, judgment, relevant.
- [Rank products with BM25](search-end-to-end.md#rank-with-bm25). Runs `scripts/first-bm25-search.py`. Defines: BM25, ranking, retrieval.
- [Check the results against the judgments](search-end-to-end.md#check-against-judgments). Runs `scripts/judge-first-results.py`.
- [Score one ranking with nDCG@10](search-end-to-end.md#score-one-ranking). Runs `scripts/ndcg-for-one-query.py`.
- [Score every test query](search-end-to-end.md#score-every-test-query). Runs `scripts/bm25-test-scores.py`, `scripts/figure-bm25-test-query-scores.py`. Defines: run.
- [Search by meaning with embeddings](search-end-to-end.md#search-by-meaning). Runs `scripts/first-semantic-search.py`, `scripts/compare-lexical-semantic.py`. Defines: embedding, semantic retrieval.
- [Fuse two rankings with reciprocal rank fusion](search-end-to-end.md#fuse-with-rrf). Runs `scripts/hybrid-rrf.py`.
- [Rerank the top 50 with a cross-encoder](search-end-to-end.md#rerank-with-cross-encoder). Runs `scripts/cross-encoder-rerank.py`, `scripts/rerank-one-query.py`. Defines: cross-encoder, large language model, reranking.
- [What goes wrong in production](search-end-to-end.md#search-end-to-end-in-production). Runs `scripts/tokenizer-drops-terms.py`.
- [Decisions this chapter made](search-end-to-end.md#search-end-to-end-decisions).

### 2. What relevance means

[The chapter](what-relevance-means.md).

- [Judge relevance against the shopper's need](what-relevance-means.md#relevance-is-a-judgment). Runs `scripts/word-match-versus-judgment.py`. Defines: information need.
- [Expect judges to disagree on some pairs](what-relevance-means.md#judges-disagree-on-some-pairs). Runs `scripts/conflicting-judgments.py`.
- [Read intent as a product and its modifiers](what-relevance-means.md#intent-in-product-search). Runs `scripts/predicted-class-check.py`. Defines: intent, modifier, target entity.
- [Grade relevance instead of yes or no](what-relevance-means.md#graded-relevance). Runs `scripts/binary-labels-hide-partial.py`. Defines: binary label, gain, graded label.
  - [Choose the gains on purpose](what-relevance-means.md#gains-are-a-choice). Runs `scripts/gain-choice-changes-ndcg.py`.
- [Read the label mix of each query](what-relevance-means.md#label-mix-per-query). Runs `scripts/count-labels-per-query.py`, `scripts/figure-label-mix-per-query.py`.
- [Treat clicks as biased evidence](what-relevance-means.md#clicks-are-not-judgments). Runs `scripts/cascade-clicks.py`. Defines: cascade model, position bias, presentation bias.
- [Know where the judgments came from](what-relevance-means.md#pooled-judgments). Runs `scripts/trundle-daybeds-unjudged.py`. Defines: pool, unjudged.
- [Count unjudged products before you compare scores](what-relevance-means.md#unjudged-results). Runs `scripts/unjudged-in-bm25-top-10.py`, `scripts/condensed-ndcg.py`. Defines: condensed list, Judged@k.
- [What goes wrong in production](what-relevance-means.md#what-relevance-means-in-production).
- [Decisions this chapter made](what-relevance-means.md#what-relevance-means-decisions).

### 3. Measuring search

[The chapter](measuring-search.md).

- [Count the relevant products in the top k](measuring-search.md#count-relevant-in-top-k). Runs `scripts/precision-recall-by-hand.py`. Defines: Precision at k, Recall at k.
- [Score the first relevant result with reciprocal rank](measuring-search.md#score-the-first-relevant-result). Runs `scripts/reciprocal-rank-by-hand.py`. Defines: Mean reciprocal rank, Reciprocal rank.
- [Build nDCG from discounted gains](measuring-search.md#build-ndcg-from-dcg). Runs `scripts/ndcg-from-scratch.py`. Defines: Discounted cumulative gain, Normalized DCG.
- [Match scikit-learn's `ndcg_score`](measuring-search.md#match-scikit-learn-ndcg). Runs `scripts/ndcg-matches-scikit-learn.py`.
- [Choose a metric before you compare](measuring-search.md#choose-a-ranking-metric). Runs `scripts/metric-choice-on-train.py`.
- [Read per-query differences, not only the mean](measuring-search.md#read-per-query-differences). Runs `scripts/per-query-hybrid-versus-bm25.py`. Defines: per-query differences.
- [Test a gap with a permutation test](measuring-search.md#permutation-test-on-queries). Runs `scripts/permutation-test-by-hand.py`, `scripts/figure-permutation-null.py`. Defines: null hypothesis, p-value, paired test, permutation test, significance test.
- [Get the p-value from a paired t-test](measuring-search.md#paired-t-test-on-queries). Runs `scripts/paired-t-test-by-hand.py`. Defines: standard error, t distribution.
- [Report how big the gap is](measuring-search.md#report-the-size-of-a-gap). Runs `scripts/bootstrap-interval-by-hand.py`, `scripts/interval-coverage-check.py`. Defines: bootstrap, confidence interval, effect size, percentile interval.
- [Decide in advance what counts as established](measuring-search.md#when-a-difference-is-established). Defines: Bonferroni correction.
- [Compare runs in an evaluation harness](measuring-search.md#compare-runs-in-a-harness). Runs `scripts/compare-chapter-one-rankers.py`. Defines: evaluation harness.
- [What goes wrong in production](measuring-search.md#measuring-search-in-production). Runs `scripts/split-changes-the-verdict.py`.
- [Decisions this chapter made](measuring-search.md#measuring-search-decisions).

### 4. Judgments from people and LLMs

[The chapter](judgments-from-people-and-llms.md).

- [Write judging guidelines](judgments-from-people-and-llms.md#write-judging-guidelines). Runs `scripts/print-judging-guidelines.py`. Defines: judge, Judging guidelines.
- [Measure agreement beyond chance with kappa](judgments-from-people-and-llms.md#agreement-beyond-chance). Runs `scripts/kappa-by-hand.py`. Defines: Cohen's kappa, observed agreement.
- [Give near misses partial credit with weighted kappa](judgments-from-people-and-llms.md#weighted-kappa-for-grades). Runs `scripts/weighted-kappa-by-hand.py`. Defines: linear weights, Weighted kappa.
- [Read kappa against the label mix](judgments-from-people-and-llms.md#kappa-depends-on-label-mix). Runs `scripts/kappa-under-two-label-mixes.py`.
- [Read the direction of the LLM's errors](judgments-from-people-and-llms.md#read-llm-error-direction). Runs `scripts/llm-confusion-matrix.py`. Defines: confusion matrix.
- [Compare what the LLM saw with what the judges saw](judgments-from-people-and-llms.md#what-the-llm-saw). Runs `scripts/llm-grades-follow-written-words.py`.
- [Measure how much the prompt changes the labels](judgments-from-people-and-llms.md#prompt-sensitivity). Runs `scripts/prompt-disagreement.py`.
- [Fill unjudged pairs with LLM grades](judgments-from-people-and-llms.md#fill-unjudged-with-llm-grades). Runs `scripts/fill-unjudged-pairs.py`.
- [Check whether LLM grades order the rankers the same way](judgments-from-people-and-llms.md#system-order-human-versus-llm). Runs `scripts/kendall-tau-four-rankers.py`. Defines: concordant pair, discordant pair, Kendall's tau.
- [Rerun the planned comparisons with LLM grades](judgments-from-people-and-llms.md#llm-graded-verdicts). Runs `scripts/planned-comparisons-llm-grades.py`.
- [Correct LLM scores with a human sample](judgments-from-people-and-llms.md#calibrate-on-a-human-sample). Runs `scripts/correct-llm-scores-with-humans.py`. Defines: Prediction-powered inference.
- [What goes wrong in production](judgments-from-people-and-llms.md#judgments-from-people-and-llms-in-production).
- [Decisions this chapter made](judgments-from-people-and-llms.md#judgments-from-people-and-llms-decisions).

### 5. Lexical retrieval

[The chapter](lexical-retrieval.md). Defines: Lexical retrieval.

- [Split product text into terms](lexical-retrieval.md#split-text-into-terms). Runs `scripts/tokenize-product-text.py`. Defines: probe query, stop word, term, token, vocabulary.
- [Build an inverted index](lexical-retrieval.md#build-an-inverted-index). Runs `scripts/inverted-index-by-hand.py`. Defines: document frequency, inverted index, postings, term frequency.
- [Weight terms with TF-IDF](lexical-retrieval.md#weight-terms-with-tf-idf). Runs `scripts/tf-idf-by-hand.py`. Defines: inverse document frequency, TF-IDF.
- [Rebuild BM25 by hand to match bm25s](lexical-retrieval.md#bm25-from-scratch). Runs `scripts/figure-bm25-term-saturation.py`, `scripts/bm25-by-hand.py`. Defines: length normalization, saturation.
- [Stem terms so word forms match](lexical-retrieval.md#stem-word-forms). Runs `scripts/stemmer-merges-word-forms.py`, `scripts/bm25s-with-a-stemmer.py`. Defines: stem, Stemming.
- [Check stemming on the test queries](lexical-retrieval.md#check-stemming-on-test). Runs `scripts/measure-stemming.py`.
- [Tune BM25's parameters on train queries](lexical-retrieval.md#tune-bm25-parameters). Runs `scripts/sweep-k1-and-b.py`.
- [Weight the product name above the description](lexical-retrieval.md#weight-the-product-name). Runs `scripts/fields-scored-apart.py`, `scripts/repeat-the-name-field.py`. Defines: BM25F, field.
- [Index product attributes as a field](lexical-retrieval.md#index-attributes-as-a-field). Runs `scripts/add-attributes-field.py`. Defines: attribute.
- [Match phrases with term positions](lexical-retrieval.md#match-phrases-with-positions). Runs `scripts/phrase-positions-by-hand.py`, `scripts/phrase-bonus-train-and-test.py`. Defines: phrase match, positional index.
- [What goes wrong in production](lexical-retrieval.md#lexical-retrieval-in-production).
- [Decisions this chapter made](lexical-retrieval.md#lexical-retrieval-decisions).

### 6. Semantic retrieval

[The chapter](semantic-retrieval.md).

- [Turn text into embeddings](semantic-retrieval.md#turn-text-into-embeddings). Runs `scripts/inspect-recorded-embeddings.py`. Defines: bi-encoder, dimension, encoder, token.
- [Compare embeddings with cosine similarity](semantic-retrieval.md#compare-with-cosine-similarity). Runs `scripts/cosine-by-hand.py`. Defines: Cosine similarity, dot product, normalizing.
- [Find the exact nearest neighbours with NumPy](semantic-retrieval.md#exact-nearest-neighbours-numpy). Runs `scripts/exact-search-numpy.py`, `scripts/exact-search-memory.py`. Defines: exact search, nearest-neighbour search.
- [Trade recall for speed with HNSW](semantic-retrieval.md#hnsw-recall-for-speed). Runs `scripts/hnsw-efsearch-sweep.py`. Defines: approximate nearest-neighbour index, HNSW, recall@k against exact search.
- [Check the index on the test queries](semantic-retrieval.md#hnsw-on-test-queries). Runs `scripts/hnsw-test-recall.py`, `scripts/hnsw-index-memory.py`.
- [Check queries that contain digits](semantic-retrieval.md#embeddings-match-digits). Runs `scripts/digits-in-queries.py`, `scripts/hood-query-digits.py`, `scripts/probe-pair-overlap.py`.
  - [Expect a code to carry little weight](semantic-retrieval.md#codes-carry-no-weight). Runs `scripts/code-probes.py`.
- [Test embeddings on negation](semantic-retrieval.md#embeddings-on-negation). Runs `scripts/negation-probes.py`.
- [Choose an embedding model](semantic-retrieval.md#choose-embedding-model).
  - [Read benchmarks as a shortlist](semantic-retrieval.md#benchmarks-as-a-shortlist).
  - [Truncate dimensions, then test the loss](semantic-retrieval.md#truncate-dimensions-test-loss). Runs `scripts/truncate-embeddings.py`, `scripts/truncation-paired-test.py`. Defines: Matryoshka training.
- [What goes wrong in production](semantic-retrieval.md#semantic-retrieval-in-production). Runs `scripts/similarity-scale.py`, `scripts/figure-similarity-by-grade.py`, `scripts/spelling-probes.py`.
- [Decisions this chapter made](semantic-retrieval.md#semantic-retrieval-decisions).

### 7. Hybrid retrieval

[The chapter](hybrid-retrieval.md). Defines: blend.

- [Find the queries each retriever wins](hybrid-retrieval.md#queries-each-retriever-wins). Runs `scripts/bm25-semantic-wins-by-query.py`, `scripts/overlap-and-union-recall.py`, `scripts/two-queries-two-winners.py`. Defines: fusion, hybrid retrieval.
- [Check each retriever before you fuse](hybrid-retrieval.md#check-each-retriever-before-fusing). Runs `scripts/fusion-gain-by-winning-retriever.py`.
- [Normalize scores before you add them](hybrid-retrieval.md#normalize-scores-before-adding). Runs `scripts/raw-scores-versus-min-max.py`, `scripts/figure-score-scales.py`. Defines: candidate set, convex combination, per-query min-max scaling, score normalization, theoretical min-max, z-score.
- [Test reciprocal rank fusion's settings on train queries](hybrid-retrieval.md#rrf-settings-on-train). Runs `scripts/rrf-k-on-train.py`. Defines: reciprocal rank fusion.
- [Tune the blend's weight on train queries](hybrid-retrieval.md#tune-blend-on-train). Runs `scripts/weighted-rrf-one-product.py`, `scripts/tune-blend-weights-on-train.py`, `scripts/figure-blend-weight-curve.py`. Defines: weighted RRF.
- [Check that the tuned weight is stable](hybrid-retrieval.md#tuned-weight-stability). Runs `scripts/blend-weight-bootstrap.py`, `scripts/tuning-with-ties-reversed.py`.
- [Report the tuned blends on test queries](hybrid-retrieval.md#report-blends-on-test). Runs `scripts/tuned-blends-on-test.py`.
- [Learn sparse term weights with SPLADE](hybrid-retrieval.md#learned-sparse-splade). Runs `scripts/exact-products-missing-query-words.py`. Defines: expansion terms, learned sparse retrieval, SPLADE.
- [Match token by token with ColBERT](hybrid-retrieval.md#late-interaction-colbert). Defines: ColBERT, late interaction, MaxSim.
- [Decide when hybrid retrieval pays](hybrid-retrieval.md#when-hybrid-helps).
- [What goes wrong in production](hybrid-retrieval.md#hybrid-retrieval-in-production).
- [Decisions this chapter made](hybrid-retrieval.md#hybrid-retrieval-decisions).

### 8. Understanding queries

[The chapter](understanding-queries.md). Defines: query understanding.

- [Correct spelling against the catalog's words](understanding-queries.md#correct-spelling-from-catalog). Runs `scripts/catalog-spelling-corrector.py`, `scripts/spelling-context-counts.py`, `scripts/measure-spelling-corrections.py`. Defines: edit distance, lexicon, noisy channel model, real-word error.
- [Normalize units the way the catalog writes them](understanding-queries.md#normalize-units). Runs `scripts/normalize-units-both-sides.py`. Defines: normalization.
- [Expand queries with a synonym list](understanding-queries.md#expand-with-synonyms). Runs `scripts/synonym-expansion-train-and-test.py`. Defines: pseudo-relevance feedback, query drift, query expansion.
- [Train a query classifier on product text](understanding-queries.md#classify-queries-from-products). Runs `scripts/query-classes-by-hand.py`. Defines: naive Bayes, query classification.
- [Boost the predicted class instead of filtering](understanding-queries.md#boost-predicted-class). Runs `scripts/class-boost-train-and-test.py`. Defines: boost, filter.
- [Rewrite queries with an LLM](understanding-queries.md#rewrite-queries-with-llm). Runs `scripts/llm-rewrites-on-train.py`, `scripts/llm-rewrites-on-test.py`, `scripts/rewrite-largest-changes.py`. Defines: query rewriting.
- [Search with a hypothetical product (HyDE)](understanding-queries.md#hyde-hypothetical-products). Runs `scripts/hyde-train-and-test.py`. Defines: HyDE, hypothetical document, relevance feedback.
- [Turn a follow-up into a standalone query](understanding-queries.md#standalone-follow-ups). Runs `scripts/follow-up-refinements.py`. Defines: conversational query rewriting, standalone query.
- [What goes wrong in production](understanding-queries.md#understanding-queries-in-production).
- [Decisions this chapter made](understanding-queries.md#understanding-queries-decisions).

### 9. Ranking

[The chapter](ranking.md).

- [Describe each candidate with features](ranking.md#ranking-features). Runs `scripts/ranking-features-by-grade.py`. Defines: candidate, feature, query-dependent feature, query-independent feature.
- [Learn a ranking from pairs of products](ranking.md#learn-from-pairs). Runs `scripts/lambdas-for-one-query.py`, `scripts/lambdas-match-lightgbm.py`. Defines: gradient-boosted trees, LambdaMART, learning to rank, listwise model, pairwise model, pointwise model.
- [Train LambdaMART with LightGBM](ranking.md#train-lambdamart). Runs `scripts/lambdamart-tree-size-on-train.py`, `scripts/lambdamart-choices-on-train.py`. Defines: cross-validation, early stopping.
- [Report LambdaMART on the test queries](ranking.md#lambdamart-on-test-queries). Runs `scripts/lambdamart-on-test.py`. Defines: feature importance.
- [Rerank semantic retrieval with a cross-encoder](ranking.md#rerank-semantic-with-cross-encoder). Runs `scripts/cross-encoder-on-semantic.py`.
- [Score each product with an LLM](ranking.md#llm-pointwise-reranking). Runs `scripts/llm-pointwise-rerank.py`. Defines: listwise LLM reranking, pairwise LLM reranking, pointwise LLM reranking.
- [Order the 20 products with one LLM prompt](ranking.md#llm-listwise-reranking). Runs `scripts/llm-listwise-rerank.py`. Defines: sliding window.
- [Reverse the input to measure positional bias](ranking.md#llm-position-bias). Runs `scripts/listwise-position-bias.py`. Defines: positional bias.
- [Set the rerank depth from a budget](ranking.md#rerank-depth-from-budget). Runs `scripts/reranker-prompt-sizes.py`, `scripts/rerank-depth-on-train.py`. Defines: rerank depth.
- [Distill the cross-encoder into a small ranker](ranking.md#distill-the-cross-encoder). Runs `scripts/distillation-on-train.py`, `scripts/distilled-ranker-on-test.py`. Defines: distillation, student, teacher.
- [What goes wrong in production](ranking.md#ranking-in-production).
- [Decisions this chapter made](ranking.md#ranking-decisions).

### 10. Retrieval for LLM applications

[The chapter](retrieval-for-llm-applications.md). Defines: agent.

- [Put retrieved products in the prompt](retrieval-for-llm-applications.md#put-retrieved-products-in-the-prompt). Runs `scripts/catalog-against-the-context.py`. Defines: context, context window, prompt, Retrieval-augmented generation.
- [Score each answer by the products it cites](retrieval-for-llm-applications.md#retrieval-bounds-the-answer). Runs `scripts/rag-answers-by-context.py`. Defines: citation, distractor.
- [Check every citation against the context](retrieval-for-llm-applications.md#check-citations-against-context). Runs `scripts/citations-inside-the-context.py`. Defines: attribution, Grounding.
- [Check what the cited product supports](retrieval-for-llm-applications.md#check-citation-support). Runs `scripts/faithful-but-partial.py`. Defines: Faithfulness.
- [Measure the context, then the answer](retrieval-for-llm-applications.md#measure-the-context). Runs `scripts/context-measures-by-hand.py`, `scripts/context-measures-against-answers.py`. Defines: context precision, context recall, Spearman's rank correlation.
- [Choose the retrievable unit](retrieval-for-llm-applications.md#choose-the-retrievable-unit). Runs `scripts/retrievable-unit-on-train.py`. Defines: chunking, retrievable unit.
- [Read an agent's searches from its trace](retrieval-for-llm-applications.md#read-agent-searches). Runs `scripts/agent-searches-in-traces.py`, `scripts/agent-later-searches.py`. Defines: agent loop, tool, tool call, trace.
- [Compare the retrievers behind the agent's tool](retrieval-for-llm-applications.md#retriever-behind-agent-tool). Runs `scripts/agent-picks-by-tool.py`.
- [What goes wrong in production](retrieval-for-llm-applications.md#retrieval-for-llm-applications-in-production).
- [Decisions this chapter made](retrieval-for-llm-applications.md#retrieval-for-llm-applications-decisions).

### 11. Testing changes

[The chapter](testing-changes.md).

- [Diff two runs query by query](testing-changes.md#diff-runs-per-query). Runs `scripts/diff-semantic-against-bm25.py`. Defines: baseline, candidate ranker, regression set.
- [Weigh losses more than wins with URisk](testing-changes.md#weigh-losses-with-urisk). Runs `scripts/urisk-of-two-candidates.py`. Defines: risk-sensitive evaluation, URisk.
- [Judge the products a new ranker surfaces](testing-changes.md#judge-new-results). Runs `scripts/unjudged-score-range.py`. Defines: sensitivity check.
- [Keep the test queries out of every choice](testing-changes.md#keep-test-queries-held-out). Runs `scripts/tuning-on-test-inflates.py`.
- [Run an A/B test](testing-changes.md#run-an-ab-test). Runs `scripts/aa-tests-with-peeking.py`, `scripts/figure-peeking-false-positives.py`. Defines: A/A test, A/B test, control, peeking, sample ratio mismatch, treatment.
- [Size the test with power](testing-changes.md#size-tests-with-power). Runs `scripts/sample-size-from-power.py`, `scripts/queries-needed-for-power.py`, `scripts/figure-power-curve.py`. Defines: power.
- [Interleave two rankings with team draft](testing-changes.md#team-draft-interleaving). Runs `scripts/team-draft-one-query.py`. Defines: Interleaving, Team draft.
- [Rehearse interleaving with simulated shoppers](testing-changes.md#simulate-interleaving-with-clicks). Runs `scripts/one-simulated-shopper.py`, `scripts/simulated-interleaving-verdict.py`. Defines: click model.
- [Find the cause when offline and online disagree](testing-changes.md#offline-online-disagree). Runs `scripts/clicks-per-search-misleads.py`.
- [Decide whether to ship](testing-changes.md#decide-whether-to-ship).
- [What goes wrong in production](testing-changes.md#testing-changes-in-production).
- [Decisions this chapter made](testing-changes.md#testing-changes-decisions).
