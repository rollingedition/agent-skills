---
title: "A Primer on Search Relevance"
chapter: "Judgments from people and LLMs"
chapter_id: judgments-from-people-and-llms
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/judgments-from-people-and-llms
license: CC BY 4.0
attribution: "“Judgments from people and LLMs,” chapter 4 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/judgments-from-people-and-llms. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Judgments from people and LLMs

By the end of this chapter you can write judging guidelines, measure how well two judges agree with kappa and weighted kappa, read an LLM judge's errors from a confusion matrix, and decide where LLM judgments can stand in for people's and where they can't.

Every score in this book rests on human judgments for [the store](#store-data), the online furniture and home-goods retailer whose search this book studies: WANDS's labels, each the majority vote of up to three trained annotators. Those judgments have holes: on the [test queries](#store-data), BM25's top 10s hold 22 products nobody judged ([Count unjudged products](#unjudged-results)). They also take people's time, and the agreement among WANDS's annotators rose over four months of calibration ([Expect judges to disagree](#judges-disagree-on-some-pairs)). A **large language model** (LLM), a model trained on large amounts of text to generate text in response to a prompt, can grade any query and product it is shown. Before the store lets one judge, it needs to know how often the LLM agrees with the store's judges, and whether LLM grades would lead to the same decisions about its rankers.

The LLM's grades come from a **recording**: the script `recordings/llm_judgments.py` ran the open model `gemma4:12b-it-q4_K_M` once, locally, at temperature 0 with a fixed seed, and saved its answers, so the examples read the grades through `lib.recorded.llm_judgments()` without calling the model. We chose the model because it is open, under the Apache 2.0 licence, and runs locally, so anyone can rerun the recording. A JSON schema limits every answer to one of the three labels. The recording graded each pair with two prompts, `short` and `guidelines` ([Write judging guidelines](#write-judging-guidelines)), and took its pairs from two sets, which this chapter calls pools. The **train pool**, for measuring agreement, holds pairs that people judged for the train queries, drawn evenly by label: up to 4 of each label per query, 550 pairs in all. The **test pool** holds the pairs an LLM would grade to score the store's rankers: every product in the top 10 of [chapter 1's four rankers](#search-end-to-end-decisions) for each test query, judged by people or not, 590 pairs. The four are BM25, semantic retrieval on embeddings from `Snowflake/snowflake-arctic-embed-m-v1.5`, the hybrid of the two, and the hybrid reranked by the cross-encoder `Alibaba-NLP/gte-reranker-modernbert-base`. A measurement of the LLM judge holds for the pool it is taken on, so each one in this chapter names its pool.

The scores that decide between rankers stay on human grades. The chapter's planned comparisons on the test queries are [chapter 3's three](#when-a-difference-is-established), rescored with each prompt's LLM grades at chapter 3's threshold of 0.0167: semantic retrieval against BM25, the hybrid against semantic retrieval, and the reranked hybrid against the hybrid.

## Write judging guidelines {#write-judging-guidelines}

A **judgment** is a judge's label for one pair of a query and a product, and a **grade** is the number that stands for it. [Chapter 1](#store-data) defines a judgment as a person's label; this chapter widens it to an LLM's label too. Judgments depend on the instructions behind them. **Judging guidelines** say what each grade means, how to choose between grades, and what to do with the cases that fall between them.

WANDS published the guidelines its annotators used, eight pages under the MIT licence ([annotation guidelines](https://github.com/wayfair/WANDS/raw/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/Product%20Search%20Relevance%20Annotation%20Guidelines.pdf)). They list what a judge sees for each pair: the query, and the product's ID, name, image and web page. They define the three grades and add two notes. One asks the judge to understand the query first: "Strongly recommend google it first". The other covers misspellings: "please ignore the mis-spellings and proceed to annotate the example as-is". Then they teach by example, with a query, a product and a reason for each grade. A wire basket without dividers is partial for `wire basket with dividers`, one of the store's own train queries. A salon anti-fatigue mat is irrelevant to `salon chair`: "the customer looks for a salon chair, not a mat. This product is irrelevant to the query." Guidelines also change as judges use them. WANDS's authors report that their annotators' agreement rose over four months, and among their reasons they list a "Daily routine to discuss the conflicting annotations" and this one: "With the input from annotators, we refine and fine-tune annotation guidelines" ([Chen et al., 2022, section 5](https://easychair.org/publications/preprint/wm4R)). One web search engine's rater guidelines do the same at 182 pages, in their version of September 11, 2025 ([Search Quality Rater Guidelines](https://guidelines.raterhub.com/searchqualityevaluatorguidelines.pdf)).

In the store, the two prompts of [the recording](#judgments-from-people-and-llms) are guidelines for the LLM. `short` gives WANDS's three definitions and nothing else. `guidelines` adds five rules. Print it as the recording sent it:

*Example `print-judging-guidelines`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/write-judging-guidelines*

The `guidelines` prompt runs to 206 words, against 59 for `short`. Finding the entity first, then the modifiers, spells out WANDS's definition of partial. The rule on accessories settles a case on which WANDS's own labels split: for `clear shower curtain`, WANDS lists one set of shower curtain hooks twice, once partial and once irrelevant ([Expect judges to disagree](#judges-disagree-on-some-pairs)). The rule on misspellings follows WANDS's note. The last rule has no counterpart in WANDS's guidelines: the store's data has no images, so the recording shows the LLM text only. Neither prompt has worked examples, which WANDS's guidelines rely on.

**Working rule:** Write guidelines as definitions, a procedure, a worked example with a reason for each grade, and a rule for each case your judges have disagreed on. Log disagreements and revise the guidelines when one kind keeps coming back. Give an LLM judge the same guidelines as people, plus a rule for what it can't see, and then measure what it does, because a rule you write isn't a rule the judge follows.

## Measure agreement beyond chance with kappa {#agreement-beyond-chance}

Before you trust a second judge, measure how often it agrees with the first. The share of pairs on which two judges give the same grade, the **observed agreement**, is the obvious number, and it flatters. Two judges who guessed independently would agree on some pairs by chance, and on more of them when both use one label often. **Cohen's kappa** corrects for that. It compares the observed agreement with the agreement expected if each judge kept its own label shares but chose independently of the other. A kappa of 1 means complete agreement, and 0 means "no agreement beyond what would be expected by chance" ([scikit-learn documentation](https://scikit-learn.org/1.9/modules/generated/sklearn.metrics.cohen_kappa_score.html)):

```text
kappa    = (observed - expected) / (1 - expected)
expected = sum over grades g of  (share of pairs judge A gives g) × (share of pairs judge B gives g)
```

Measure how often the LLM of [the recording](#judgments-from-people-and-llms) grades a pair as the store's judges did. Use the train pool, pairs people judged for train queries and drawn evenly by label, and the [`short` prompt](#write-judging-guidelines), WANDS's three definitions alone. Build the 3×3 table of counts by hand, compute kappa, and check it against scikit-learn's `cohen_kappa_score`:

*Example `kappa-by-hand`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/agreement-beyond-chance*

The LLM and the store's judges give the same grade to a share of 0.624 of the pairs. Chance alone would produce 0.337, so kappa is 0.432, the same as scikit-learn's 0.432. The `guidelines` prompt agrees on 0.633 of the pairs, a kappa of 0.454.

Is that good? Scales that call a kappa "moderate" or "substantial" are conventions from particular fields, and Artstein and Poesio's survey concludes that "deciding what counts as an adequate level of agreement for a specific purpose is still little more than a black art" ([Artstein and Poesio, 2008](https://aclanthology.org/J08-4004/)). Published figures give context, not a bar: WANDS's annotators agreed with each other at a kappa of 0.467 in their first two months and 0.826 in their fourth ([Chen et al., 2022, Table 2](https://easychair.org/publications/preprint/wm4R)). On a stratified sample of pairs from TREC, the Text REtrieval Conference's shared evaluations, Thomas et al. found that GPT-4's kappa against the assessors varied "from as low as 0.20 ... to 0.64" with the prompt, while "two groups of trained human assessors" reached 0.52 on TREC ad hoc documents judged a second time (Cormack et al., 1998, as reported by [Thomas et al., 2024](https://arxiv.org/abs/2309.10621)). Each figure comes from a different sample, and [kappa depends on the sample's label mix](#kappa-depends-on-label-mix).

**Working rule:** Report kappa, with observed agreement beside it, never observed agreement alone. Measure it on pairs people judged for train queries, and label any threshold you use as a rule of thumb. With more than two judges or missing labels, use Krippendorff's alpha, which compares observed with chance disagreement and handles "Any number of observers, not just two" and "Incomplete or missing data" ([Krippendorff, 2011](https://www.asc.upenn.edu/sites/default/files/2021-03/Computing%20Krippendorff%27s%20Alpha-Reliability.pdf)).

## Give near misses partial credit with weighted kappa {#weighted-kappa-for-grades}

[Kappa](#agreement-beyond-chance) counts every disagreement the same. The store's grades are ordered, exact above partial above irrelevant, and calling an exact product partial is a smaller error than calling it irrelevant. In nDCG@10 ([Score one ranking](#score-one-ranking)) it costs half as much gain: one grade instead of two. **Weighted kappa** gives each disagreement a weight by its distance and compares the weighted disagreement with the weighted disagreement expected by chance ([Artstein and Poesio, 2008, section 2.6](https://aclanthology.org/J08-4004/)). With **linear** weights, a disagreement one grade apart weighs 0.5 and one two grades apart weighs 1:

```text
weighted kappa = 1 - (sum of weight × observed count) / (sum of weight × count expected by chance)
```

With every disagreement weighted 1, the formula gives plain kappa. scikit-learn's `cohen_kappa_score` computes all three kinds this way: weight 1 by default, the distance between grades with `weights="linear"`, and its square with `weights="quadratic"` ([scikit-learn source](https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.9.1/sklearn/metrics/_classification.py)). Scaling the weights doesn't change the result.

In the store, compute linear weighted kappa by hand for both [prompts](#write-judging-guidelines) on the train pool, the evenly drawn pairs that [Measure agreement beyond chance](#agreement-beyond-chance) uses, and check it against scikit-learn:

*Example `weighted-kappa-by-hand`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/weighted-kappa-for-grades*

For `short`, weighting raises kappa from 0.432 to 0.523, and for `guidelines` from 0.454 to 0.531. Both match scikit-learn. Weighting raises both because more of the disagreements sit one grade apart than chance would put there: a share of 0.942 against 0.742 for `short`, and 0.851 against 0.664 for `guidelines`. The prompts differ in their far misses: 12 pairs for `short` and 30 for `guidelines`. Whether either prompt agrees better is a question for [an interval](#prompt-sensitivity).

**Working rule:** For ordered grades, report linear weighted kappa next to plain kappa, and count the far misses separately. Weight each disagreement by the gap in gain it costs. With the book's linear gains, that's linear weights. With exponential gains of 0, 1 and 3 ([Choose a metric](#choose-a-ranking-metric)), the gaps are 1, 2 and 3, which neither of scikit-learn's options gives, so build that matrix as the example builds the linear one.

## Read kappa against the label mix {#kappa-depends-on-label-mix}

[Kappa's](#agreement-beyond-chance) correction depends on how often each judge uses each label, so the same judge gets a different kappa on a sample with a different mix of labels. When one label dominates, observed agreement can be high while kappa stays low. Artstein and Poesio call this the prevalence problem: "coders may agree on a high proportion of items while producing annotations that are indeed correct to a high degree, yet the reliability coefficients remain low" ([Artstein and Poesio, 2008](https://aclanthology.org/J08-4004/)).

[The recording](#judgments-from-people-and-llms) drew the store's train pool evenly, up to 4 pairs of each label per train query, so it holds more exact and irrelevant pairs than the store's judgments do. Weight each pair so that the pool has the label mix of all the train queries' judgments, and measure again:

*Example `kappa-under-two-label-mixes`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/kappa-depends-on-label-mix*

Partial makes up 0.364 of the pool as drawn, against 0.613 of the train judgments. In the judgments' mix, the `short` prompt's observed agreement goes from 0.624 to 0.635, while its kappa goes from 0.432 to 0.370. For `guidelines`, observed agreement goes from 0.633 to 0.573, and kappa from 0.454 to 0.345. The prompt with the higher kappa is `guidelines` as drawn and `short` in the judgments' mix.

Published numbers carry their mix with them. The one study of LLM judges on WANDS we found "sampled 5000 Q-P pairs evenly across the three class labels" and reports accuracy from 0.726 for the best open model, with 70 billion parameters, to 0.837 for the best closed one, each in its best setting, with 16 worked examples retrieved for every pair ([Sachdev et al., 2025, Table 3](https://arxiv.org/html/2502.15990)). The store's prompts have no worked examples. That accuracy is observed agreement on a balanced sample, as the train pool's is, and neither number transfers to the label mix of the store's judgments.

The pairs the store will ask an LLM to judge are the products its rankers put in their top 10s, the test pool. Of its judged pairs, a share of 0.543 are exact, 0.427 partial and 0.030 irrelevant. That is a third mix, and a different kind of pair, which [Read the direction of the LLM's errors](#read-llm-error-direction) measures.

**Working rule:** Report the label mix with every kappa, and never compare kappas from samples with different mixes, your own or published ones. We recommend drawing the agreement sample the way you'll use the judge: if it will grade your rankers' top 10s, sample pairs from top 10s on train queries.

## Read the direction of the LLM's errors {#read-llm-error-direction}

[Kappa](#agreement-beyond-chance) says how much two judges agree, not how they differ. A **confusion matrix** does: a table of counts with one row for each of the store's grades and one column for each of the LLM's, both in the order exact, partial, irrelevant. Above the diagonal, the LLM gave a lower grade than the store's judges; below it, a higher one. A judge whose errors fall mostly below is **lenient**, and mostly above, **strict**. Several studies find LLM judges lenient. At TREC 2024's RAG track, which evaluates retrieval-augmented generation (answers written from retrieved text), "Overall, human assessors appear to be stricter than UMBRELA in applying relevance criteria", UMBRELA being an open-source LLM judge ([Upadhyay et al., 2024a](https://arxiv.org/abs/2411.08275)). Arabzadeh and Clarke report that UMBRELA, built on GPT-4o ([Upadhyay et al., 2024b](https://arxiv.org/abs/2406.06519)), labelled "over 26% more documents as perfectly relevant (3,063 vs. 2,429)" than people did across TREC's Deep Learning tracks of 2019 to 2021 ([Arabzadeh and Clarke, 2025a](https://arxiv.org/abs/2504.12558)), and Yu et al. report LLM judges that "consistently assign inflated relevance scores" ([Yu et al., 2026](https://arxiv.org/abs/2602.17170)). Not every study agrees. With one of their 32 prompts, on a sample stratified by label, Thomas et al. found that "the LLM is more likely to say ‘not relevant’ than were TREC assessors (44% vs 33%)" ([Thomas et al., 2024](https://arxiv.org/abs/2309.10621)).

In the store, build the matrix for both prompts on both [pools](#judgments-from-people-and-llms): the train pool, drawn evenly by label, and the judged pairs of the test pool, the top 10s of [chapter 1's four rankers](#search-end-to-end-decisions) that an LLM would grade to score them. The test-pool matrices are a report on test queries, not a choice of prompt:

*Example `llm-confusion-matrix`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/read-llm-error-direction*

On the train pool, is the LLM stricter than the store's judges? With `short`: yes. With `guidelines`: yes. With `short`, its grade is lower than the judges' on 140 pairs and higher on 67; with `guidelines`, lower on 150 and higher on 52. The largest error is exact called partial (85) with `short`, and partial called irrelevant (72) with `guidelines`.

On the test pool, the answer is no with `short` and no with `guidelines`. With `short`, the LLM's grade is higher on 65 pairs and lower on 61; with `guidelines`, higher on 83 and lower on 77. Its mean grade is 1.521 with `short` and 1.521 with `guidelines`, against 1.512 for the judges. The largest error is partial called exact (57) with `short` and partial called exact (76) with `guidelines`. Kappa is 0.571 and 0.470, against 0.432 and 0.454 on the train pool. The direction, the largest error and kappa all change with the pool, as [the label mix](#kappa-depends-on-label-mix) warns. [Compare what the LLM saw](#what-the-llm-saw) finds one pattern that fits both pools.

Nor does the direction of the errors say what happens to a ranker's score. A lenient judge counts more products as relevant, which raises precision@10 ([Count the relevant products](#count-relevant-in-top-k)). nDCG@10 divides by an ideal top 10 built from the same grades ([Score one ranking](#score-one-ranking)), so raising grades can raise the ideal too, and the net effect can go either way and differ by ranker. [The check of the rankers' order](#system-order-human-versus-llm) measures it on the test pool.

**Working rule:** Read the confusion matrix before you read kappa, on pairs drawn the way you'll use the judge, and name the direction and the largest error for that pool. Don't carry a direction from one pool to another, and don't predict a ranker's nDCG@10 from it. Compare rankers with each other under the same grades, and never compare a score under LLM grades with a score under human grades.

## Compare what the LLM saw with what the judges saw {#what-the-llm-saw}

A judge can grade only the evidence it is shown. WANDS's judges saw, for each pair, the query and the product's ID, name, image and web page, and the guidelines told them to understand the query first: "Strongly recommend google it first" ([annotation guidelines](https://github.com/wayfair/WANDS/raw/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/Product%20Search%20Relevance%20Annotation%20Guidelines.pdf)). The recording showed the LLM each product's name, class, category, description and attributes, as `lib.agreement.as_the_llm_saw` writes them out. The store's sample cuts descriptions to about 400 characters ([data card](https://github.com/rollingedition/book-primer-on-search-relevance/blob/975f0c078e472eb1d3e9202a4a5feaddae27d052/examples/data/wands/README.md)) and holds no images, so the recording sent the LLM text only. Some disagreement may come from this gap rather than from how well the LLM judges; that is our inference. One consequence can be tested: if the LLM grades what is written, it should give a lower grade to exact products whose text doesn't say what the query asks for, and a higher grade to partial products whose text does.

Take one of the store's train pairs, then the test query `clear shower curtain`, then every judged exact and partial pair in both pools ([the recording](#judgments-from-people-and-llms)). The example looks for each query word in what the LLM saw, split into lowercase words as [chapter 2's check](#relevance-is-a-judgment) does:

*Example `llm-grades-follow-written-words`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/what-the-llm-saw*

For `dual monitor stand`, a train query, the store's judges called `abramowski monitor stand` exact. Its grades from the judges, `short` and `guidelines`, in that order, are 2 1 1, and nothing the LLM saw says the stand holds two monitors. For `clear shower curtain`, of the 9 test-pool products that never say `clear` anywhere the LLM could read, the store's judges called 1 exact, `short` 0 and `guidelines` 0. Of the 9 that say it, the judges called 5 exact, `short` 7 and `guidelines` 7. For this query, the LLM's exact grades follow the word.

Counted over the pools, the pattern holds. With `short`, exact pairs whose text misses a query word get a lower grade from the LLM at a share of 0.584 on the train pool and 0.305 on the test pool, against 0.149 and 0.084 for exact pairs whose text has every word. On the test pool, partial pairs whose text has every query word get a higher grade at a share of 0.548, against 0.171 for those that miss a word. On the test pool, `guidelines` splits the same way: 0.281 against 0.051 for exact pairs, and 0.667 against 0.241 for partial ones.

The pools differ in which case is common. The train pool holds 149 exact pairs that miss a word and 8 partial pairs that have every word. The test pool holds 128 and 42. By our reading, that is why [the error direction](#read-llm-error-direction) differs between the pools. The check is rough: a plural or a misspelling counts as a missing word too. The `guidelines` prompt asks for the demotions: "If a modifier isn't mentioned, decide from what is written, and don't assume it is met." The `short` prompt has no such rule, and demotes as well.

**Working rule:** Give an LLM judge every field your judges relied on that you can turn into text, such as attributes and the full description, and write down what it can't see. Before you count a disagreement against the LLM, check whether the evidence was in what it saw. When your judges' evidence is visual, measure whether the LLM grades exact products lower, as this one does on both pools, or give it the images if your model accepts them.

## Measure how much the prompt changes the labels {#prompt-sensitivity}

An LLM judge is a model and a prompt together. Across 42 paraphrases of one prompt, Thomas et al. found "a large range, from mean κ = 0.50 (moderate agreement) to mean κ = 0.72", and warn that one prompt's result "should be taken as a single sample from a wider range of potential performance" ([Thomas et al., 2024](https://arxiv.org/abs/2309.10621)). Across three LLMs and 72 prompts on TREC's Deep Learning collections, Arabzadeh and Clarke found that "Binary and pairwise methods exhibit the least sensitivity to input prompts", while "graded relevance judgments are highly sensitive to prompt variations", the store's kind. Prompts varied between LLMs, "with no single prompt consistently excelling across all models", though "for graded assessments, UMBRELA consistently demonstrated high performance across different LLMs" ([Arabzadeh and Clarke, 2025b](https://arxiv.org/abs/2504.12408)).

In the store, the two prompts share their definitions, and `guidelines` adds five rules ([Write judging guidelines](#write-judging-guidelines)). Count their disagreements on each pool ([the recording](#judgments-from-people-and-llms)), and ask whether the train pool can tell which prompt agrees better with the store's judges. Pairs from the same query aren't independent, so the example's interval resamples whole train queries, as [chapter 3's bootstrap](#report-the-size-of-a-gap) resamples queries:

*Example `prompt-disagreement`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/prompt-sensitivity*

The prompts disagree on 122 of 550 train pairs and on 93 of 590 test pairs. Their kappa with each other is 0.668 on the train pool and 0.712 on the test pool: a second prompt is a second judge. The largest disagreement differs by pool. On the train pool it is partial under short, irrelevant under guidelines (75); on the test pool, the rankers' top 10s, it is partial under short, exact under guidelines (42). Of the train pairs that `short` calls partial and `guidelines` irrelevant, the store's judges called 26 irrelevant, siding with `guidelines`, 31 partial, siding with `short`, and 18 exact. Among the products the example lists are a sofa bed for `toddler couch fold out` and window curtains for `70s inspired furniture`. The recording keeps labels, not reasons, so from names like these we infer that the move comes from the `guidelines` rule that calls the wrong kind of product irrelevant.

On kappa with the store's judges, `guidelines` leads `short` by 0.022, and the 95% interval over resampled train queries, from -0.042 to 0.086, includes 0. The train pool can't tell the prompts apart, so the store keeps both.

**Working rule:** Treat the prompt as part of the judge. Record every prompt word for word with the model version, as the recording's manifest does, and the settings and answer schema too, which this recording keeps in its script. Treat a change of prompt as a different judge whose agreement you measure again. Run at least two prompts, and trust a conclusion from LLM grades only when both give it. Choose one prompt over another on train pairs, and only when the interval for their difference excludes 0.

## Fill unjudged pairs with LLM grades {#fill-unjudged-with-llm-grades}

We consider filling the holes in the human judgments the least risky use of an LLM judge. Keep every human grade, and use the LLM only for pairs nobody judged, which a metric would otherwise count as grade 0 ([Count unjudged products](#unjudged-results)). The LLM then decides only what was a guess before.

The store's test pool, every product in the top 10 of [chapter 1's four rankers](#search-end-to-end-decisions) for each test query, holds 590 pairs, of which 26 are unjudged. BM25's top 10s hold 22 of them, against 3 for semantic retrieval and 6 for the hybrid. Fill them under each [prompt](#write-judging-guidelines), rescore the four rankers on nDCG@10 ([Score one ranking](#score-one-ranking)), and rerun [chapter 3's planned comparisons](#when-a-difference-is-established) on the filled grades:

*Example `fill-unjudged-pairs`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/fill-unjudged-with-llm-grades*

The prompts disagree about the unjudged pairs. Counted as exact, partial and irrelevant, `short` grades them 4, 17, 5, and `guidelines` 5, 9, 12. They part on the unjudged products for `outdoor light fixtures` in BM25's top 10 ([Score every test query](#score-every-test-query)). Of those 8, 8 have `bulb` in their names, and `guidelines` calls 7 of them irrelevant and `short` 0. Chapter 1 argued that a bulb isn't a light fixture. Which reading the store's judges would take, nobody knows until they judge the bulbs.

With the holes filled, BM25 scores 0.754 with `short` and 0.745 with `guidelines`, against 0.725 on human grades alone, and semantic retrieval scores 0.833 and 0.834, against 0.830. The order of the four rankers on human grades alone is `semantic > hybrid > reranked > bm25`. The rankers that change place when `short` fills the holes are none, and when `guidelines` does, none. The verdicts of the planned comparisons that change are none with `short` and none with `guidelines`. Under human grades, the rankers' mean judged@10, the share of each top 10 that people judged, runs from 0.927 for BM25 to 0.990 for semantic retrieval ([Compare runs in a harness](#compare-runs-in-a-harness)); filled, every product in a top 10 has a grade.

How far can the filled grades be trusted? The judged pairs of the same pool are the closest evidence: there, the LLM's kappa with the store's judges is 0.571 for `short` and 0.470 for `guidelines`. Its grade is lower than the judges' on 61 pairs and higher on 65 with `short`, and lower on 77 and higher on 83 with `guidelines` ([Read the direction of the LLM's errors](#read-llm-error-direction)).

**Working rule:** Fill the unjudged pairs in your rankers' top 10s with LLM grades as a diagnostic, under every prompt you run, and report the filled score beside the human-only one with the number of pairs filled. If filling changes the order of two rankers or a verdict, have people judge those pairs. Never let a filled grade replace a human one.

## Check whether LLM grades order the rankers the same way {#system-order-human-versus-llm}

Two sets of judgments can disagree on many labels and still rank systems alike. Voorhees scored TREC runs with different sets of relevance judgments and found that "Very high correlations were found among the rankings of systems produced using different relevance judgment sets" ([Voorhees, 1998](https://people.eng.unimelb.edu.au/ammoffat/sigir98/abstracts/voorhees.html)). LLM judges show the same split. Across 42 sets of LLM labels for TREC's 2023 Deep Learning track, kappa ran from about 0.06 to 0.29 while the correlation of system rankings stayed between about 0.83 and 0.95 ([Rahmani et al., 2025, Table 3](https://arxiv.org/abs/2502.13908)).

That correlation is **Kendall's tau**. For every pair of systems, ask whether two orderings put them the same way round: **concordant** if they do, **discordant** if not. Tau is the difference between the two counts divided by the number of pairs, from 1 for the same order to −1 for the reverse. SciPy's `kendalltau` computes τ_b, a form that also handles ties ([SciPy documentation](https://docs.scipy.org/doc/scipy-1.18.0/reference/generated/scipy.stats.kendalltau.html)). Rankings with a tau of 0.9 or more "are often considered ‘effectively equivalent’ ... at least empirically", in Yilmaz et al.'s words ([Yilmaz et al., 2008](https://www.ccs.neu.edu/home/jaa/tmp/RankCorrelation.pdf)), and Sanderson and Soboroff found that "basing decisions on such thresholds is not as reliable as has been assumed" ([Sanderson and Soboroff, 2007](https://eprints.whiterose.ac.uk/id/eprint/4589/)).

In the store, score [chapter 1's four rankers](#search-end-to-end-decisions) on nDCG@10 under human grades and under each [prompt's](#write-judging-guidelines) LLM grades. The LLM judged only the test pool, the products in those rankers' top 10s, so as a control, the example also scores them with human grades for the pool's pairs only. With four rankers there are 6 pairs, so one swapped pair moves tau by 0.333, and tau can take only seven values. That is crude. Before you run it, predict: will LLM grades put the four rankers in the same order as human grades?

*Example `kendall-tau-four-rankers`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/system-order-human-versus-llm*

Human grades give `semantic > hybrid > reranked > bm25`. The control keeps that order, with a tau of 1.000, so limiting the grades to the pool moves no ranker. It raises every score, BM25's from 0.725 to 0.795, because the ideal top 10 can only hold pooled products. `short` gives `reranked > semantic > hybrid > bm25`, and `guidelines` gives `reranked > semantic > hybrid > bm25`. These pairs swap under `short`: semantic and reranked; hybrid and reranked. Tau for `short` is 0.333 by hand and 0.333 from SciPy, and for `guidelines`, 0.333.

Against the control, LLM grades don't move the four rankers by the same amount, or in the same direction. With `short`, BM25 changes by +0.037, semantic retrieval by -0.001, the hybrid by +0.016 and the reranked hybrid by +0.037. With `guidelines`, the changes are +0.010, -0.026, -0.008 and +0.017. The judge raises some rankers and lowers others, and that moves them past each other.

Under `short`, semantic retrieval, the hybrid and the reranked hybrid nearly tie, at 0.903, 0.900 and 0.906. Tau ignores how far apart two rankers score, so a swap between near-ties counts as much as one between the best ranker and the worst. It also weighs a swap at the top the same as one at the bottom: "Kendall’s τ equally penalizes errors that occur at any part of the list" ([Yilmaz et al., 2008](https://www.ccs.neu.edu/home/jaa/tmp/RankCorrelation.pdf)). Yilmaz et al. note of the TREC runs they compared that the systems "have very similar performance. Hence, the Kendall’s τ statistic may be affected by these systems" ([Yilmaz et al., 2012](https://static.aminer.org/pdf/20170130/pdfs/sigir/jcmbhoqtt46bhqr5xegf9zy7snars82a.pdf)). These rankers keep their place under every set of grades: `bm25`. If you predicted the same order, notice where the orders differ: among the three rankers that human grades score 0.830, 0.812 and 0.798, gaps that no planned comparison establishes ([Rerun the planned comparisons](#llm-graded-verdicts)).

**Working rule:** Report tau with the list of swapped pairs, never alone. With a handful of rankers, where one swap moves tau by 0.333, don't read it against 0.9. Then test whether the swapped pairs differ at all, with [the planned comparisons under each set of grades](#llm-graded-verdicts).

## Rerun the planned comparisons with LLM grades {#llm-graded-verdicts}

Decisions come from verdicts, not from the [orderings that tau compares](#system-order-human-versus-llm). A difference is established when its paired [permutation test](#permutation-test-on-queries) p-value falls below the chapter's Bonferroni threshold, with the t-test and a bootstrap interval beside it ([Decide in advance what counts as established](#when-a-difference-is-established)). Would LLM grades have given the store the same verdicts? Expect trouble near the top: Otero et al. found that "LLM-based judgements are unfair at ranking top-performing systems", with "an exceedingly high rate of false positives regarding statistical differences" ([Otero et al., 2025](https://arxiv.org/abs/2411.13212)).

The store's planned comparisons are chapter 3's three, at 0.0167, with intervals at the 0.9833 level. The example runs each under human grades and under each [prompt's](#write-judging-guidelines) grades on the test pool, and adds chapter 3's exploratory comparison of the reranked hybrid with semantic retrieval:

*Example `planned-comparisons-llm-grades`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/llm-graded-verdicts*

| Measure | Grades | Semantic minus BM25 | Hybrid minus semantic | Reranked minus hybrid |
| --- | --- | --- | --- | --- |
| Mean difference | Human | 0.105 | -0.018 | -0.014 |
| Mean difference | `short` | 0.070 | -0.002 | 0.006 |
| Mean difference | `guidelines` | 0.073 | -0.001 | 0.010 |
| Interval | Human | 0.047 to 0.205 | -0.048 to 0.006 | -0.053 to 0.020 |
| Interval | `short` | 0.016 to 0.146 | -0.029 to 0.036 | -0.029 to 0.042 |
| Interval | `guidelines` | 0.006 to 0.183 | -0.045 to 0.037 | -0.024 to 0.076 |
| Permutation p | Human | 0.001 | 0.125 | 0.382 |
| Permutation p | `short` | 0.010 | 0.851 | 0.727 |
| Permutation p | `guidelines` | 0.045 | 0.929 | 0.657 |
| t-test p | Human | 0.003 | 0.123 | 0.375 |
| t-test p | `short` | 0.014 | 0.861 | 0.714 |
| t-test p | `guidelines` | 0.057 | 0.945 | 0.609 |
| Established | Human | yes | no | no |
| Established | `short` | yes | no | no |
| Established | `guidelines` | no | no | no |

Under `short`, the verdicts that differ from the human ones are none; under `guidelines`, `semantic minus bm25`, the one result chapter 3 established. The planned comparisons where the t-test or the interval disagrees with the permutation test number 0 under human grades, 0 under `short` and 1 under `guidelines`; for semantic retrieval minus BM25 under `guidelines`, the check that disagrees is the interval. So whether the store's one established result survives LLM grades depends on the prompt.

[Comparing the rankers' order](#system-order-human-versus-llm) found two swapped pairs. One, the reranked hybrid against the hybrid, is a planned comparison, and the table shows it established under no set of grades. The other, the reranked hybrid against semantic retrieval, is the exploratory comparison. Under human grades, the reranked hybrid minus semantic retrieval is -0.032 (permutation p 0.048). Under LLM grades it is 0.003 with `short` and 0.009 with `guidelines`. Chapter 3 chose it after seeing the test means, so it establishes nothing either way.

LLM judges can also favour rankers that use LLMs: Balog et al. report "the first empirical evidence of LLM judges exhibiting significant bias towards LLM-based rankers" ([Balog et al., 2025](https://arxiv.org/abs/2503.19092)). Chapter 1's rankers use no LLM, so this chapter can't measure that bias. The book scores the LLM-based rankers of [chapter 8](#rewrite-queries-with-llm) and [chapter 9](#llm-pointwise-reranking) on human grades.

**Working rule:** Never ship a change on a verdict from LLM grades alone. Use LLM grades to decide which candidates are worth judging, and decide on human grades. When two prompts give different verdicts, the LLM can't settle the comparison, and people must.

## Correct LLM scores with a human sample {#calibrate-on-a-human-sample}

A middle path uses both kinds of grades: grade every query with the LLM, have people judge a random sample of queries, and use the sample to correct the LLM's error. **Prediction-powered inference** makes this rigorous, with confidence intervals that hold "without making any assumptions on the machine-learning algorithm that supplies the predictions" ([Angelopoulos et al., 2023](https://arxiv.org/abs/2301.09633)). A simple form of the idea, for a mean, takes the LLM's mean over every query and adds the human sample's average of human minus LLM:

```text
corrected = mean over all queries of the LLM score + mean over the human sample of (human score − LLM score)
```

In search evaluation, Oosterhuis et al. build metric intervals this way, warning that "generated relevance annotations are not immune to (systematic) errors" ([Oosterhuis et al., 2024](https://arxiv.org/abs/2407.02464)); Takehi et al. let the LLM pick which pairs people judge under a budget, then calibrate it on them ([Takehi et al., 2025](https://arxiv.org/abs/2411.06877)).

Suppose the store could afford human judgments for 10 of 30 test queries. The example draws 2,000 random sets of that size and, for each, corrects the LLM's estimate, under each [prompt](#write-judging-guidelines), of two gaps between [chapter 1's rankers](#search-end-to-end-decisions): semantic retrieval minus BM25, and the hybrid minus semantic retrieval. It compares the corrected estimate with the human sample alone. **Spread** is an estimate's standard deviation over the draws. The simulation chooses nothing:

*Example `correct-llm-scores-with-humans`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/calibrate-on-a-human-sample*

For semantic retrieval minus BM25, the LLM alone estimates 0.070 with `short`, against 0.105 on human grades. Corrected, the estimate averages 0.104 over the draws, so the correction removes the LLM's bias. Its spread is 0.036, against 0.045 for the human sample alone: the LLM's grades for the other queries add information, because its per-query gaps correlate with the human ones at 0.641.

For the hybrid minus semantic retrieval, the corrected spread is 0.023, against 0.016 for the human sample alone, with a correlation of 0.168. Is the corrected spread smaller than the human sample's? For this gap: no with `short` and no with `guidelines`. For semantic retrieval minus BM25: yes and yes. The correction fixes the level of a score, but narrows the uncertainty only where the LLM's per-query scores track the human ones, and here they track them least on the closer of the two gaps.

**Working rule:** Whenever you report a score from LLM grades, have people judge a random sample of queries and report the corrected estimate. On that sample, check how well the LLM's per-query gaps correlate with the human ones. When they correlate weakly, spend the budget on judging more queries.

## What goes wrong in production {#judgments-from-people-and-llms-in-production}

**The judge changes without notice.** A store that judges with an LLM runs it again and again, and a different model version, a different quantization (the precision at which the model's weights are stored) or a reworded prompt is a different judge. The recording's `manifest.json` pins the model's digest and both prompts word for word. The answer schema and the context length live in `recordings/llm.py` and `recordings/llm_judgments.py`, so record those too. Rerun the agreement check on the same human sample whenever any of them changes.

**Systems tuned to the judge score well on it.** Clarke and Dietz built a run that exploits an LLM judge, and it ranked "significantly higher under automatic assessment (5th) than under manual assessment (28th)" ([Clarke and Dietz, 2024](https://arxiv.org/abs/2412.17156)). A ranker tuned on LLM grades, or built on the same LLM, needs its headline score on human grades.

**Product text can steer the judge.** Alaofi et al. found that LLM judges can be misled by query words planted in an irrelevant text, and by instructions written into it ([Alaofi et al., 2024](https://arxiv.org/abs/2501.17969)). Product descriptions may come from outside your team. Keep a human sample in every evaluation, so that a judge led astray shows up as a falling agreement.

**Calibrating on test is tuning on test.** Rewording a prompt until it matches the human grades on test queries makes agreement there meaningless. Choose prompts on train queries, and report agreement on test.

**Human grades aren't the truth either.** On the TREC Podcast track, where an LLM and a TREC assessor disagreed most, Mansour et al. found that experts re-judging the pairs more often sided with the LLM ([Mansour et al., 2026](https://arxiv.org/abs/2601.05603)). Treat human grades as the reference you chose, and read disagreements before you blame either side.

**Working rule:** Pin the judge, keep a human sample in every evaluation, rerun agreement when anything changes, and never score a ranker with the judge you tuned it on.

## Decisions this chapter made {#judgments-from-people-and-llms-decisions}

Each choice below is a default. Later chapters keep it unless they state a reason.

- **Human grades for every headline score.** LLM grades are a diagnostic: filling holes, screening candidates and checking verdicts. The LLM-based rankers of [chapter 8](#rewrite-queries-with-llm) and [chapter 9](#llm-pointwise-reranking) are scored on human grades.
- **Every finding about the judge names its pool.** Kappa and linear weighted kappa, with observed agreement, the far misses and the label mix beside them, are measured on train pairs people judged, and reported for the test pool's judged pairs too. The direction of errors and the largest error are read on each pool, and only the rankers' top 10s speak to ranker scores.
- **Two prompts, recorded word for word.** The train pool can't tell them apart, so the store keeps both, and a conclusion from LLM grades counts only when both prompts give it.
- **Unjudged pairs filled with LLM grades as a diagnostic,** reported beside the human-only score. On the test queries, filling changes no ranker's place and no verdict.
- **Compare scores only under the same grades.** On the same pool, LLM grades don't move every ranker's nDCG@10 by the same amount or in the same direction, so a score under LLM grades never meets one under human grades.
- **Tau with its swapped pairs, then the planned comparisons at chapter 3's threshold.** With four rankers tau is crude, and the verdicts decide.
- **A score from LLM grades comes with a human sample** of queries that corrects it, and the correlation that says whether the LLM helped.
