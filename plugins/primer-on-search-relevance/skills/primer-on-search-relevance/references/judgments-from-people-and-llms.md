---
title: "A Primer on Search Relevance"
chapter: "Judgments from people and LLMs"
chapter_id: judgments-from-people-and-llms
book: primer-on-search-relevance
edition: 2026.11.6
verified: 2026-11-12
edition_code: R33J-KWQ9
canonical: https://rollingedition.com/primer-on-search-relevance/judgments-from-people-and-llms
license: CC BY 4.0
attribution: "“Judgments from people and LLMs,” chapter 4 of A Primer on Search Relevance, Edition 2026.11.6, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/judgments-from-people-and-llms. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
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

Example `print-judging-guidelines` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.6:

```python
from lib.recorded import manifest

recording = manifest("llm-judgments")             # the recording's model, settings and both prompts, verbatim
short, guidelines = recording["prompts"]["short"], recording["prompts"]["guidelines"]

print("model:", recording["model"])
print("what the model saw:", recording["sees"])
print("words in the short prompt:", len(short.split()))
print("words in the guidelines prompt:", len(guidelines.split()))
print()
print(guidelines)
```

Output:

```text
model: gemma4:12b-it-q4_K_M
what the model saw: lib.store text plus attributes; no images
words in the short prompt: 59
words in the guidelines prompt: 206

You judge product search results for an online furniture and home-goods store. A shopper typed the query and was shown the product. Decide how well the product matches what the shopper asked for.

Exact: the product fully matches the search query.
Partial: the product only matches the target entity of the query, but does not satisfy the modifiers for the query.
Irrelevant: the product is not relevant to the query.

Guidelines:
- First find the target entity: the kind of product the query asks for (a sofa, a lamp, a rug).
- Then find the modifiers: everything else the query asks for, such as colour, size, material, style, brand or a feature.
- Exact needs the right kind of product and every modifier. Partial is the right kind of product with at least one modifier missing or contradicted. Irrelevant is the wrong kind of product, even when it shares words with the query, such as an accessory for the product asked for.
- Read misspelled queries as the shopper meant them.
- Judge only from the product's text and attributes. If a modifier isn't mentioned, decide from what is written, and don't assume it is met.

Query: {query}

Product:
{product}

Answer with the label in JSON.
```

The `guidelines` prompt runs to 206 words, against 59 for `short`. Finding the entity first, then the modifiers, spells out WANDS's definition of partial. The rule on accessories settles a case on which WANDS's own labels split: for `clear shower curtain`, WANDS lists one set of shower curtain hooks twice, once partial and once irrelevant ([Expect judges to disagree](#judges-disagree-on-some-pairs)). The rule on misspellings follows WANDS's note. The last rule has no counterpart in WANDS's guidelines: the store's data has no images, so the recording shows the LLM text only. Neither prompt has worked examples, which WANDS's guidelines rely on.

**Working rule:** Write guidelines as definitions, a procedure, a worked example with a reason for each grade, and a rule for each case your judges have disagreed on. Log disagreements and revise the guidelines when one kind keeps coming back. Give an LLM judge the same guidelines as people, plus a rule for what it can't see, and then measure what it does, because a rule you write isn't a rule the judge follows.

## Measure agreement beyond chance with kappa {#agreement-beyond-chance}

Before you trust a second judge, measure how often it agrees with the first. The share of pairs on which two judges give the same grade, the **observed agreement**, is the obvious number, and it flatters. Two judges who guessed independently would agree on some pairs by chance, and on more of them when both use one label often. **Cohen's kappa** corrects for that. It compares the observed agreement with the agreement expected if each judge kept its own label shares but chose independently of the other. A kappa of 1 means complete agreement, and 0 means "no agreement beyond what would be expected by chance" ([scikit-learn documentation](https://scikit-learn.org/1.9/modules/generated/sklearn.metrics.cohen_kappa_score.html)):

```text
kappa    = (observed - expected) / (1 - expected)
expected = sum over grades g of  (share of pairs judge A gives g) × (share of pairs judge B gives g)
```

Measure how often the LLM of [the recording](#judgments-from-people-and-llms) grades a pair as the store's judges did. Use the train pool, pairs people judged for train queries and drawn evenly by label, and the [`short` prompt](#write-judging-guidelines), WANDS's three definitions alone. Build the 3×3 table of counts by hand, compute kappa, and check it against scikit-learn's `cohen_kappa_score`:

Example `kappa-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
from sklearn.metrics import cohen_kappa_score

from lib.agreement import graded_pairs

pairs = graded_pairs("train")                     # up to 4 human-judged pairs per label per train query
human, llm = pairs["human"].astype(int), pairs["short"].astype(int)
grades = [2, 1, 0]                                # exact, partial, irrelevant
counts = np.array([[((human == row) & (llm == column)).sum() for column in grades] for row in grades])
print("pairs:", counts.sum())
print("rows are the human grades 2, 1, 0 and columns the LLM's, short prompt")
print(counts)

observed = np.trace(counts) / counts.sum()                          # the share of pairs on the diagonal
human_share, llm_share = counts.sum(axis=1) / counts.sum(), counts.sum(axis=0) / counts.sum()
expected = (human_share * llm_share).sum()                          # agreement if the two judged independently
kappa = (observed - expected) / (1 - expected)
print(f"observed agreement, short prompt: {observed:.3f}")
print(f"agreement expected by chance, short prompt: {expected:.3f}")
print(f"kappa by hand, short prompt: {kappa:.3f}")
print(f"kappa from scikit-learn, short prompt: {cohen_kappa_score(human, llm):.3f}")

other = pairs["guidelines"].astype(int)
print(f"observed agreement, guidelines prompt: {(human == other).mean():.3f}")
print(f"kappa from scikit-learn, guidelines prompt: {cohen_kappa_score(human, other):.3f}")
```

Output:

```text
pairs: 550
rows are the human grades 2, 1, 0 and columns the LLM's, short prompt
[[102  85   9]
 [ 22 132  46]
 [  3  42 109]]
observed agreement, short prompt: 0.624
agreement expected by chance, short prompt: 0.337
kappa by hand, short prompt: 0.432
kappa from scikit-learn, short prompt: 0.432
observed agreement, guidelines prompt: 0.633
kappa from scikit-learn, guidelines prompt: 0.454
```

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

Example `weighted-kappa-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from lib.agreement import PROMPTS, graded_pairs

pairs = graded_pairs("train")                     # up to 4 human-judged pairs per label per train query
grades = [2, 1, 0]                                # exact, partial, irrelevant
cost = np.abs(np.subtract.outer(grades, grades)) / 2    # 0 on the diagonal, 0.5 one grade apart, 1 two apart
print("disagreement weights, rows and columns 2, 1, 0")
print(cost)

for prompt in PROMPTS:
    human, llm = pairs["human"].astype(int), pairs[prompt].astype(int)
    counts = confusion_matrix(human, llm, labels=grades)                       # rows human, columns LLM
    expected = np.outer(counts.sum(axis=1), counts.sum(axis=0)) / counts.sum()   # counts if independent
    weighted = 1 - (cost * counts).sum() / (cost * expected).sum()
    near = cost == 0.5                                                         # cells one grade apart
    print()
    print(f"pairs two grades apart, {prompt} prompt: {counts[0, 2] + counts[2, 0]}")
    print(f"disagreements one grade apart, share, {prompt} prompt: {counts[near].sum() / counts[cost > 0].sum():.3f}")
    print(f"one grade apart, share expected by chance, {prompt} prompt: {expected[near].sum() / expected[cost > 0].sum():.3f}")
    print(f"kappa, {prompt} prompt: {cohen_kappa_score(human, llm):.3f}")
    print(f"linear weighted kappa by hand, {prompt} prompt: {weighted:.3f}")
    print(f"linear weighted kappa from scikit-learn, {prompt} prompt: "
          f"{cohen_kappa_score(human, llm, weights='linear'):.3f}")
```

Output:

```text
disagreement weights, rows and columns 2, 1, 0
[[0.  0.5 1. ]
 [0.5 0.  0.5]
 [1.  0.5 0. ]]

pairs two grades apart, short prompt: 12
disagreements one grade apart, share, short prompt: 0.942
one grade apart, share expected by chance, short prompt: 0.742
kappa, short prompt: 0.432
linear weighted kappa by hand, short prompt: 0.523
linear weighted kappa from scikit-learn, short prompt: 0.523

pairs two grades apart, guidelines prompt: 30
disagreements one grade apart, share, guidelines prompt: 0.851
one grade apart, share expected by chance, guidelines prompt: 0.664
kappa, guidelines prompt: 0.454
linear weighted kappa by hand, guidelines prompt: 0.531
linear weighted kappa from scikit-learn, guidelines prompt: 0.531
```

For `short`, weighting raises kappa from 0.432 to 0.523, and for `guidelines` from 0.454 to 0.531. Both match scikit-learn. Weighting raises both because more of the disagreements sit one grade apart than chance would put there: a share of 0.942 against 0.742 for `short`, and 0.851 against 0.664 for `guidelines`. The prompts differ in their far misses: 12 pairs for `short` and 30 for `guidelines`. Whether either prompt agrees better is a question for [an interval](#prompt-sensitivity).

**Working rule:** For ordered grades, report linear weighted kappa next to plain kappa, and count the far misses separately. Weight each disagreement by the gap in gain it costs. With the book's linear gains, that's linear weights. With exponential gains of 0, 1 and 3 ([Choose a metric](#choose-a-ranking-metric)), the gaps are 1, 2 and 3, which neither of scikit-learn's options gives, so build that matrix as the example builds the linear one.

## Read kappa against the label mix {#kappa-depends-on-label-mix}

[Kappa's](#agreement-beyond-chance) correction depends on how often each judge uses each label, so the same judge gets a different kappa on a sample with a different mix of labels. When one label dominates, observed agreement can be high while kappa stays low. Artstein and Poesio call this the prevalence problem: "coders may agree on a high proportion of items while producing annotations that are indeed correct to a high degree, yet the reliability coefficients remain low" ([Artstein and Poesio, 2008](https://aclanthology.org/J08-4004/)).

[The recording](#judgments-from-people-and-llms) drew the store's train pool evenly, up to 4 pairs of each label per train query, so it holds more exact and irrelevant pairs than the store's judgments do. Weight each pair so that the pool has the label mix of all the train queries' judgments, and measure again:

Example `kappa-under-two-label-mixes` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
from sklearn.metrics import cohen_kappa_score

from lib.agreement import LABELS, PROMPTS, graded_pairs
from lib.store import load_labels, load_queries

pairs = graded_pairs("train")                     # drawn evenly: up to 4 pairs per label per train query
drawn = pairs["human"].value_counts(normalize=True)
labels = load_labels()
natural = labels[labels["query_id"].isin(load_queries("train").index)]["grade"].value_counts(normalize=True)
top = graded_pairs("test")["human"].dropna().value_counts(normalize=True)    # the rankers' top 10s, judged pairs
for grade, label in LABELS.items():
    print(f"{label} share, as drawn: {drawn[grade]:.3f}")
    print(f"{label} share, in the train judgments: {natural[grade]:.3f}")
    print(f"{label} share, judged test-pool pairs: {top[grade]:.3f}")

weight = pairs["human"].map(natural / drawn).astype(float)            # count each pair as if drawn in that mix
kappas = {}
for prompt in PROMPTS:
    human, llm = pairs["human"].astype(int), pairs[prompt].astype(int)
    print()
    print(f"observed agreement, {prompt} prompt, as drawn: {(human == llm).mean():.3f}")
    print(f"kappa, {prompt} prompt, as drawn: {cohen_kappa_score(human, llm):.3f}")
    print(f"observed agreement, {prompt} prompt, train judgments' mix: {np.average(human == llm, weights=weight):.3f}")
    kappas[prompt] = cohen_kappa_score(human, llm), cohen_kappa_score(human, llm, sample_weight=weight)
    print(f"kappa, {prompt} prompt, train judgments' mix: {kappas[prompt][1]:.3f}")
print()
for position, mix in enumerate(["as drawn", "train judgments' mix"]):
    print(f"higher kappa, {mix}: {max(PROMPTS, key=lambda prompt: kappas[prompt][position])}")
```

Output:

```text
exact share, as drawn: 0.356
exact share, in the train judgments: 0.234
exact share, judged test-pool pairs: 0.543
partial share, as drawn: 0.364
partial share, in the train judgments: 0.613
partial share, judged test-pool pairs: 0.427
irrelevant share, as drawn: 0.280
irrelevant share, in the train judgments: 0.153
irrelevant share, judged test-pool pairs: 0.030

observed agreement, short prompt, as drawn: 0.624
kappa, short prompt, as drawn: 0.432
observed agreement, short prompt, train judgments' mix: 0.635
kappa, short prompt, train judgments' mix: 0.370

observed agreement, guidelines prompt, as drawn: 0.633
kappa, guidelines prompt, as drawn: 0.454
observed agreement, guidelines prompt, train judgments' mix: 0.573
kappa, guidelines prompt, train judgments' mix: 0.345

higher kappa, as drawn: guidelines
higher kappa, train judgments' mix: short
```

Partial makes up 0.364 of the pool as drawn, against 0.613 of the train judgments. In the judgments' mix, the `short` prompt's observed agreement goes from 0.624 to 0.635, while its kappa goes from 0.432 to 0.370. For `guidelines`, observed agreement goes from 0.633 to 0.573, and kappa from 0.454 to 0.345. The prompt with the higher kappa is `guidelines` as drawn and `short` in the judgments' mix.

Published numbers carry their mix with them. The one study of LLM judges on WANDS we found "sampled 5000 Q-P pairs evenly across the three class labels" and reports accuracy from 0.726 for the best open model, with 70 billion parameters, to 0.837 for the best closed one, each in its best setting, with 16 worked examples retrieved for every pair ([Sachdev et al., 2025, Table 3](https://arxiv.org/html/2502.15990)). The store's prompts have no worked examples. That accuracy is observed agreement on a balanced sample, as the train pool's is, and neither number transfers to the label mix of the store's judgments.

The pairs the store will ask an LLM to judge are the products its rankers put in their top 10s, the test pool. Of its judged pairs, a share of 0.543 are exact, 0.427 partial and 0.030 irrelevant. That is a third mix, and a different kind of pair, which [Read the direction of the LLM's errors](#read-llm-error-direction) measures.

**Working rule:** Report the label mix with every kappa, and never compare kappas from samples with different mixes, your own or published ones. We recommend drawing the agreement sample the way you'll use the judge: if it will grade your rankers' top 10s, sample pairs from top 10s on train queries.

## Read the direction of the LLM's errors {#read-llm-error-direction}

[Kappa](#agreement-beyond-chance) says how much two judges agree, not how they differ. A **confusion matrix** does: a table of counts with one row for each of the store's grades and one column for each of the LLM's, both in the order exact, partial, irrelevant. Above the diagonal, the LLM gave a lower grade than the store's judges; below it, a higher one. A judge whose errors fall mostly below is **lenient**, and mostly above, **strict**. Several studies find LLM judges lenient. At TREC 2024's RAG track, which evaluates retrieval-augmented generation (answers written from retrieved text), "Overall, human assessors appear to be stricter than UMBRELA in applying relevance criteria", UMBRELA being an open-source LLM judge ([Upadhyay et al., 2024a](https://arxiv.org/abs/2411.08275)). Arabzadeh and Clarke report that UMBRELA, built on GPT-4o ([Upadhyay et al., 2024b](https://arxiv.org/abs/2406.06519)), labelled "over 26% more documents as perfectly relevant (3,063 vs. 2,429)" than people did across TREC's Deep Learning tracks of 2019 to 2021 ([Arabzadeh and Clarke, 2025a](https://arxiv.org/abs/2504.12558)), and Yu et al. report LLM judges that "consistently assign inflated relevance scores" ([Yu et al., 2026](https://arxiv.org/abs/2602.17170)). Not every study agrees. With one of their 32 prompts, on a sample stratified by label, Thomas et al. found that "the LLM is more likely to say ‘not relevant’ than were TREC assessors (44% vs 33%)" ([Thomas et al., 2024](https://arxiv.org/abs/2309.10621)).

In the store, build the matrix for both prompts on both [pools](#judgments-from-people-and-llms): the train pool, drawn evenly by label, and the judged pairs of the test pool, the top 10s of [chapter 1's four rankers](#search-end-to-end-decisions) that an LLM would grade to score them. The test-pool matrices are a report on test queries, not a choice of prompt:

Example `llm-confusion-matrix` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from lib.agreement import LABELS, PROMPTS, graded_pairs

order = list(LABELS.values())                     # rows: the store's grades; columns: the LLM's; both exact first
for pool in ["train", "test"]:
    pairs = graded_pairs(pool).dropna(subset=["human"])                    # in the test pool, the pairs people judged
    human = pairs["human"].astype(int)
    print(f"\njudged pairs, {pool} pool: {len(pairs)}\nmean human grade, {pool} pool: {human.mean():.3f}")
    for prompt in PROMPTS:
        llm, name = pairs[prompt].astype(int), f"{pool} pool, {prompt} prompt"
        table = pd.crosstab(human.map(LABELS).rename("human"), llm.map(LABELS).rename(f"llm, {name}"))
        table = table.reindex(index=order, columns=order, fill_value=0)
        errors = {f"{row} called {column}": table.at[row, column] for row in order for column in order if row != column}
        largest = max(errors, key=errors.get)
        print(table)
        print(f"kappa, {name}: {cohen_kappa_score(human, llm):.3f}\nmean llm grade, {name}: {llm.mean():.3f}")
        print(f"llm grade higher than human, {name}: {(llm > human).sum()}")
        print(f"llm grade lower than human, {name}: {(llm < human).sum()}")
        print(f"stricter than the store's judges, {name}: {'yes' if (llm < human).sum() > (llm > human).sum() else 'no'}")
        print(f"largest error, {name}: {largest} ({errors[largest]})")
```

Output:

```text

judged pairs, train pool: 550
mean human grade, train pool: 1.076
llm, train pool, short prompt  exact  partial  irrelevant
human
exact                            102       85           9
partial                           22      132          46
irrelevant                         3       42         109
kappa, train pool, short prompt: 0.432
mean llm grade, train pool, short prompt: 0.933
llm grade higher than human, train pool, short prompt: 67
llm grade lower than human, train pool, short prompt: 140
stricter than the store's judges, train pool, short prompt: yes
largest error, train pool, short prompt: exact called partial (85)
llm, train pool, guidelines prompt  exact  partial  irrelevant
human
exact                                 118       53          25
partial                                30       98          72
irrelevant                              5       17         132
kappa, train pool, guidelines prompt: 0.454
mean llm grade, train pool, guidelines prompt: 0.862
llm grade higher than human, train pool, guidelines prompt: 52
llm grade lower than human, train pool, guidelines prompt: 150
stricter than the store's judges, train pool, guidelines prompt: yes
largest error, train pool, guidelines prompt: partial called irrelevant (72)

judged pairs, test pool: 564
mean human grade, test pool: 1.512
llm, test pool, short prompt  exact  partial  irrelevant
human
exact                           252       53           1
partial                          57      177           7
irrelevant                        2        6           9
kappa, test pool, short prompt: 0.571
mean llm grade, test pool, short prompt: 1.521
llm grade higher than human, test pool, short prompt: 65
llm grade lower than human, test pool, short prompt: 61
stricter than the store's judges, test pool, short prompt: no
largest error, test pool, short prompt: partial called exact (57)
llm, test pool, guidelines prompt  exact  partial  irrelevant
human
exact                                261       41           4
partial                               76      133          32
irrelevant                             3        4          10
kappa, test pool, guidelines prompt: 0.470
mean llm grade, test pool, guidelines prompt: 1.521
llm grade higher than human, test pool, guidelines prompt: 83
llm grade lower than human, test pool, guidelines prompt: 77
stricter than the store's judges, test pool, guidelines prompt: no
largest error, test pool, guidelines prompt: partial called exact (76)
```

On the train pool, is the LLM stricter than the store's judges? With `short`: yes. With `guidelines`: yes. With `short`, its grade is lower than the judges' on 140 pairs and higher on 67; with `guidelines`, lower on 150 and higher on 52. The largest error is exact called partial (85) with `short`, and partial called irrelevant (72) with `guidelines`.

On the test pool, the answer is no with `short` and no with `guidelines`. With `short`, the LLM's grade is higher on 65 pairs and lower on 61; with `guidelines`, higher on 83 and lower on 77. Its mean grade is 1.521 with `short` and 1.521 with `guidelines`, against 1.512 for the judges. The largest error is partial called exact (57) with `short` and partial called exact (76) with `guidelines`. Kappa is 0.571 and 0.470, against 0.432 and 0.454 on the train pool. The direction, the largest error and kappa all change with the pool, as [the label mix](#kappa-depends-on-label-mix) warns. [Compare what the LLM saw](#what-the-llm-saw) finds one pattern that fits both pools.

Nor does the direction of the errors say what happens to a ranker's score. A lenient judge counts more products as relevant, which raises precision@10 ([Count the relevant products](#count-relevant-in-top-k)). nDCG@10 divides by an ideal top 10 built from the same grades ([Score one ranking](#score-one-ranking)), so raising grades can raise the ideal too, and the net effect can go either way and differ by ranker. [The check of the rankers' order](#system-order-human-versus-llm) measures it on the test pool.

**Working rule:** Read the confusion matrix before you read kappa, on pairs drawn the way you'll use the judge, and name the direction and the largest error for that pool. Don't carry a direction from one pool to another, and don't predict a ranker's nDCG@10 from it. Compare rankers with each other under the same grades, and never compare a score under LLM grades with a score under human grades.

## Compare what the LLM saw with what the judges saw {#what-the-llm-saw}

A judge can grade only the evidence it is shown. WANDS's judges saw, for each pair, the query and the product's ID, name, image and web page, and the guidelines told them to understand the query first: "Strongly recommend google it first" ([annotation guidelines](https://github.com/wayfair/WANDS/raw/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/Product%20Search%20Relevance%20Annotation%20Guidelines.pdf)). The recording showed the LLM each product's name, class, category, description and attributes, as `lib.agreement.as_the_llm_saw` writes them out. The store's sample cuts descriptions to about 400 characters ([data card](https://github.com/rollingedition/book-primer-on-search-relevance/blob/d8bc0cbbe2485ee8945a1dd5960c81f99adca561/examples/data/wands/README.md)) and holds no images, so the recording sent the LLM text only. Some disagreement may come from this gap rather than from how well the LLM judges; that is our inference. One consequence can be tested: if the LLM grades what is written, it should give a lower grade to exact products whose text doesn't say what the query asks for, and a higher grade to partial products whose text does.

Take one of the store's train pairs, then the test query `clear shower curtain`, then every judged exact and partial pair in both pools ([the recording](#judgments-from-people-and-llms)). The example looks for each query word in what the LLM saw, split into lowercase words as [chapter 2's check](#relevance-is-a-judgment) does:

Example `llm-grades-follow-written-words` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import re

from lib.agreement import PROMPTS, as_the_llm_saw, graded_pairs
from lib.store import load_products, load_queries


def words(text):
    """Lowercase word tokens, as chapter 2 matches query words against product text."""
    return set(re.findall(r"\w+", text.lower()))


products, queries = load_products(), load_queries()
print("query:", queries.at[163, "query"])                              # a train query
print(as_the_llm_saw(products.loc[20718]))
print("grades from people, short, guidelines:", *graded_pairs("train").set_index(["query_id", "product_id"]).loc[(163, 20718)])

curtains = graded_pairs("test").query("query_id == 246")      # clear shower curtain: every product in a top 10
says = curtains["product_id"].map(lambda product_id: "clear" in words(as_the_llm_saw(products.loc[product_id])))
for kind, group in [("say clear", curtains[says]), ("never say clear", curtains[~says])]:
    print(f"\nclear shower curtain products that {kind}: {len(group)}")
    for column, judge in [("human", "people"), ("short", "the short prompt"), ("guidelines", "the guidelines prompt")]:
        print(f"products that {kind}, graded exact by {judge}: {(group[column] == 2).sum()}")

for pool in ["train", "test"]:
    pairs = graded_pairs(pool).dropna(subset=["human"])                     # in the test pool, the pairs people judged
    pairs["every word"] = [words(queries.at[query_id, "query"]) <= words(as_the_llm_saw(products.loc[product_id]))
                           for query_id, product_id in zip(pairs["query_id"], pairs["product_id"])]
    for label, grade, every_word, direction in [("exact", 2, False, "lower"), ("exact", 2, True, "lower"),
                                                ("partial", 1, True, "higher"), ("partial", 1, False, "higher")]:
        group = pairs[(pairs["human"] == grade) & (pairs["every word"] == every_word)]
        kind = f"{label} {pool} pairs {'with every query word' if every_word else 'missing a query word'}"
        print(f"\n{kind}: {len(group)}")
        for prompt in PROMPTS:
            moved = group[prompt] < grade if direction == "lower" else group[prompt] > grade
            print(f"share graded {direction}, {prompt} prompt, {kind}: {moved.mean():.3f}")
```

Output:

```text
query: dual monitor stand
Name: abramowski monitor stand
Class: Desktop Organizers & Desk Pads
Category:
Description: the monitor stand riser can help !
Attributes: color: white; material: wood; style: modern; width: 23.5; height: 4.64; depth: 9.2
grades from people, short, guidelines: 2 1 1

clear shower curtain products that say clear: 9
products that say clear, graded exact by people: 5
products that say clear, graded exact by the short prompt: 7
products that say clear, graded exact by the guidelines prompt: 7

clear shower curtain products that never say clear: 9
products that never say clear, graded exact by people: 1
products that never say clear, graded exact by the short prompt: 0
products that never say clear, graded exact by the guidelines prompt: 0

exact train pairs missing a query word: 149
share graded lower, short prompt, exact train pairs missing a query word: 0.584
share graded lower, guidelines prompt, exact train pairs missing a query word: 0.483

exact train pairs with every query word: 47
share graded lower, short prompt, exact train pairs with every query word: 0.149
share graded lower, guidelines prompt, exact train pairs with every query word: 0.128

partial train pairs with every query word: 8
share graded higher, short prompt, partial train pairs with every query word: 0.875
share graded higher, guidelines prompt, partial train pairs with every query word: 0.875

partial train pairs missing a query word: 192
share graded higher, short prompt, partial train pairs missing a query word: 0.078
share graded higher, guidelines prompt, partial train pairs missing a query word: 0.120

exact test pairs missing a query word: 128
share graded lower, short prompt, exact test pairs missing a query word: 0.305
share graded lower, guidelines prompt, exact test pairs missing a query word: 0.281

exact test pairs with every query word: 178
share graded lower, short prompt, exact test pairs with every query word: 0.084
share graded lower, guidelines prompt, exact test pairs with every query word: 0.051

partial test pairs with every query word: 42
share graded higher, short prompt, partial test pairs with every query word: 0.548
share graded higher, guidelines prompt, partial test pairs with every query word: 0.667

partial test pairs missing a query word: 199
share graded higher, short prompt, partial test pairs missing a query word: 0.171
share graded higher, guidelines prompt, partial test pairs missing a query word: 0.241
```

For `dual monitor stand`, a train query, the store's judges called `abramowski monitor stand` exact. Its grades from the judges, `short` and `guidelines`, in that order, are 2 1 1, and nothing the LLM saw says the stand holds two monitors. For `clear shower curtain`, of the 9 test-pool products that never say `clear` anywhere the LLM could read, the store's judges called 1 exact, `short` 0 and `guidelines` 0. Of the 9 that say it, the judges called 5 exact, `short` 7 and `guidelines` 7. For this query, the LLM's exact grades follow the word.

Counted over the pools, the pattern holds. With `short`, exact pairs whose text misses a query word get a lower grade from the LLM at a share of 0.584 on the train pool and 0.305 on the test pool, against 0.149 and 0.084 for exact pairs whose text has every word. On the test pool, partial pairs whose text has every query word get a higher grade at a share of 0.548, against 0.171 for those that miss a word. On the test pool, `guidelines` splits the same way: 0.281 against 0.051 for exact pairs, and 0.667 against 0.241 for partial ones.

The pools differ in which case is common. The train pool holds 149 exact pairs that miss a word and 8 partial pairs that have every word. The test pool holds 128 and 42. By our reading, that is why [the error direction](#read-llm-error-direction) differs between the pools. The check is rough: a plural or a misspelling counts as a missing word too. The `guidelines` prompt asks for the demotions: "If a modifier isn't mentioned, decide from what is written, and don't assume it is met." The `short` prompt has no such rule, and demotes as well.

**Working rule:** Give an LLM judge every field your judges relied on that you can turn into text, such as attributes and the full description, and write down what it can't see. Before you count a disagreement against the LLM, check whether the evidence was in what it saw. When your judges' evidence is visual, measure whether the LLM grades exact products lower, as this one does on both pools, or give it the images if your model accepts them.

## Measure how much the prompt changes the labels {#prompt-sensitivity}

An LLM judge is a model and a prompt together. Across 42 paraphrases of one prompt, Thomas et al. found "a large range, from mean κ = 0.50 (moderate agreement) to mean κ = 0.72", and warn that one prompt's result "should be taken as a single sample from a wider range of potential performance" ([Thomas et al., 2024](https://arxiv.org/abs/2309.10621)). Across three LLMs and 72 prompts on TREC's Deep Learning collections, Arabzadeh and Clarke found that "Binary and pairwise methods exhibit the least sensitivity to input prompts", while "graded relevance judgments are highly sensitive to prompt variations", the store's kind. Prompts varied between LLMs, "with no single prompt consistently excelling across all models", though "for graded assessments, UMBRELA consistently demonstrated high performance across different LLMs" ([Arabzadeh and Clarke, 2025b](https://arxiv.org/abs/2504.12408)).

In the store, the two prompts share their definitions, and `guidelines` adds five rules ([Write judging guidelines](#write-judging-guidelines)). Count their disagreements on each pool ([the recording](#judgments-from-people-and-llms)), and ask whether the train pool can tell which prompt agrees better with the store's judges. Pairs from the same query aren't independent, so the example's interval resamples whole train queries, as [chapter 3's bootstrap](#report-the-size-of-a-gap) resamples queries:

Example `prompt-disagreement` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from lib.agreement import LABELS, graded_pairs
from lib.store import load_products, load_queries


def kappa_gap(sample):
    """Kappa with people under the guidelines prompt, minus kappa under the short prompt."""
    human = sample["human"].astype(int)
    return cohen_kappa_score(human, sample["guidelines"].astype(int)) - cohen_kappa_score(human, sample["short"].astype(int))


order = list(LABELS.values())                     # exact, partial, irrelevant
for pool in ["train", "test"]:
    pairs = graded_pairs(pool)
    print(f"\n{pool} pairs where the prompts disagree: {(pairs['short'] != pairs['guidelines']).sum()} of {len(pairs)}\n"
          f"kappa between the prompts, {pool} pool: {cohen_kappa_score(pairs['short'], pairs['guidelines']):.3f}")
    table = pd.crosstab(pairs["short"].map(LABELS).rename(f"short, {pool}"), pairs["guidelines"].map(LABELS).rename("guidelines"))
    table = table.reindex(index=order, columns=order, fill_value=0)
    cells = {f"{row} under short, {column} under guidelines": table.at[row, column] for row in order for column in order if row != column}
    print(f"{table}\nlargest disagreement, {pool} pool: {max(cells, key=cells.get)} ({max(cells.values())})")

pairs, products, queries = graded_pairs("train"), load_products(), load_queries()
moved = pairs[(pairs["short"] == 1) & (pairs["guidelines"] == 0)]          # partial under one prompt, irrelevant under the other
print("\n".join(f"moved train pairs judged {label} by people: {(moved['human'] == grade).sum()}" for grade, label in LABELS.items()))
for query_id, product_id in moved[["query_id", "product_id"]].drop_duplicates("query_id").head(5).itertuples(index=False):
    print(f"  {queries.at[query_id, 'query']:<28} {products.at[product_id, 'name'][:50]}")

rng, train_queries = np.random.default_rng(2026), pairs["query_id"].unique()
by_query = {query_id: group for query_id, group in pairs.groupby("query_id")}
gaps = [kappa_gap(pd.concat([by_query[query_id] for query_id in rng.choice(train_queries, len(train_queries))]))
        for _ in range(2000)]                                               # resample whole train queries
low, high = np.percentile(gaps, [2.5, 97.5])
print(f"kappa with people, guidelines minus short: {kappa_gap(pairs):.3f}\n95% interval over resampled train queries: {low:.3f} to {high:.3f}")
```

Output:

```text

train pairs where the prompts disagree: 122 of 550
kappa between the prompts, train pool: 0.668
guidelines    exact  partial  irrelevant
short, train
exact           122        4           1
partial          31      153          75
irrelevant        0       11         153
largest disagreement, train pool: partial under short, irrelevant under guidelines (75)

test pairs where the prompts disagree: 93 of 590
kappa between the prompts, test pool: 0.712
guidelines   exact  partial  irrelevant
short, test
exact          303       11           1
partial         42      174          37
irrelevant       0        2          20
largest disagreement, test pool: partial under short, exact under guidelines (42)
moved train pairs judged exact by people: 18
moved train pairs judged partial by people: 31
moved train pairs judged irrelevant by people: 26
  toddler couch fold out       eulah 79 '' cotton rolled arm sofa bed
  70s inspired furniture       angels moroccan window curtains , oriental wavy cu
  7qt slow cooker              berghoff international eclipse 7 qt non-stick cove
  gnome fairy garden           fairy house tea pot fairy garden
  wall sconce with usb port    2 piece wall sconce set
kappa with people, guidelines minus short: 0.022
95% interval over resampled train queries: -0.042 to 0.086
```

The prompts disagree on 122 of 550 train pairs and on 93 of 590 test pairs. Their kappa with each other is 0.668 on the train pool and 0.712 on the test pool: a second prompt is a second judge. The largest disagreement differs by pool. On the train pool it is partial under short, irrelevant under guidelines (75); on the test pool, the rankers' top 10s, it is partial under short, exact under guidelines (42). Of the train pairs that `short` calls partial and `guidelines` irrelevant, the store's judges called 26 irrelevant, siding with `guidelines`, 31 partial, siding with `short`, and 18 exact. Among the products the example lists are a sofa bed for `toddler couch fold out` and window curtains for `70s inspired furniture`. The recording keeps labels, not reasons, so from names like these we infer that the move comes from the `guidelines` rule that calls the wrong kind of product irrelevant.

On kappa with the store's judges, `guidelines` leads `short` by 0.022, and the 95% interval over resampled train queries, from -0.042 to 0.086, includes 0. The train pool can't tell the prompts apart, so the store keeps both.

**Working rule:** Treat the prompt as part of the judge. Record every prompt word for word with the model version, as the recording's manifest does, and the settings and answer schema too, which this recording keeps in its script. Treat a change of prompt as a different judge whose agreement you measure again. Run at least two prompts, and trust a conclusion from LLM grades only when both give it. Choose one prompt over another on train pairs, and only when the interval for their difference excludes 0.

## Fill unjudged pairs with LLM grades {#fill-unjudged-with-llm-grades}

We consider filling the holes in the human judgments the least risky use of an LLM judge. Keep every human grade, and use the LLM only for pairs nobody judged, which a metric would otherwise count as grade 0 ([Count unjudged products](#unjudged-results)). The LLM then decides only what was a guess before.

The store's test pool, every product in the top 10 of [chapter 1's four rankers](#search-end-to-end-decisions) for each test query, holds 590 pairs, of which 26 are unjudged. BM25's top 10s hold 22 of them, against 3 for semantic retrieval and 6 for the hybrid. Fill them under each [prompt](#write-judging-guidelines), rescore the four rankers on nDCG@10 ([Score one ranking](#score-one-ranking)), and rerun [chapter 3's planned comparisons](#when-a-difference-is-established) on the filled grades:

Example `fill-unjudged-pairs` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from lib.agreement import LABELS, PLANNED, PROMPTS, chapter_one_runs, fill_unjudged, graded_pairs, llm_qrels, planned_verdicts
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels


def order(scores):
    """Rankers by mean nDCG@10 over the test queries, best first."""
    return sorted(scores, key=lambda name: scores[name].mean(), reverse=True)


products, queries, people = load_products(), load_queries("test"), qrels("test")
runs = chapter_one_runs(products, queries)
pairs = graded_pairs("test")                      # every product in the top 10 of the four runs, per test query
unjudged = pairs[pairs["human"].isna()]
print(f"pairs in the test pool: {len(pairs)}\nof them, unjudged: {len(unjudged)}")
for name, run in runs.items():
    missing = sum(product_id not in people[query_id] for query_id, ranking in run.items() for product_id in ranking[:10])
    print(f"unjudged products in the top 10s, {name}: {missing}")
lights = unjudged[unjudged["query_id"] == 133]                             # outdoor light fixtures
print(f"unjudged products for outdoor light fixtures: {len(lights)}\n"
      f"of them, with bulb in the name: {lights['product_id'].map(products['name']).str.contains('bulb').sum()}")
threshold = 0.05 / len(PLANNED)                                            # chapter 3's rule
human = {name: evaluate(run, people)["ndcg@10"] for name, run in runs.items()}            # per-query scores
print(f"order, people's grades only: {' > '.join(order(human))}")

for prompt in PROMPTS:
    counts = ", ".join(str((unjudged[prompt] == grade).sum()) for grade in LABELS)        # grades 2, 1 and 0
    print(f"\nunjudged pairs graded exact, partial, irrelevant, {prompt} prompt: {counts}")
    print(f"unjudged bulbs graded irrelevant, {prompt} prompt: {(lights[prompt] == 0).sum()}")
    filled = {name: evaluate(run, fill_unjudged(people, llm_qrels(prompt)))["ndcg@10"] for name, run in runs.items()}
    print("\n".join(f"{name} ndcg@10, filled by the {prompt} prompt: {filled[name].mean():.3f}" for name in runs))
    print(f"order, filled by the {prompt} prompt: {' > '.join(order(filled))}")
    moved = [name for name, place in zip(order(filled), order(human)) if name != place]
    print(f"rankers that change place when filled, {prompt} prompt: {', '.join(moved) or 'none'}")
    changed = [pair for pair, established in planned_verdicts(filled, threshold).items()
               if established != planned_verdicts(human, threshold)[pair]]
    print(f"verdicts that change when filled, {prompt} prompt: {'; '.join(' minus '.join(pair) for pair in changed) or 'none'}")
```

Output:

```text
pairs in the test pool: 590
of them, unjudged: 26
unjudged products in the top 10s, bm25: 22
unjudged products in the top 10s, semantic: 3
unjudged products in the top 10s, hybrid: 6
unjudged products in the top 10s, reranked: 6
unjudged products for outdoor light fixtures: 8
of them, with bulb in the name: 8
order, people's grades only: semantic > hybrid > reranked > bm25

unjudged pairs graded exact, partial, irrelevant, short prompt: 4, 17, 5
unjudged bulbs graded irrelevant, short prompt: 0
bm25 ndcg@10, filled by the short prompt: 0.754
semantic ndcg@10, filled by the short prompt: 0.833
hybrid ndcg@10, filled by the short prompt: 0.821
reranked ndcg@10, filled by the short prompt: 0.813
order, filled by the short prompt: semantic > hybrid > reranked > bm25
rankers that change place when filled, short prompt: none
verdicts that change when filled, short prompt: none

unjudged pairs graded exact, partial, irrelevant, guidelines prompt: 5, 9, 12
unjudged bulbs graded irrelevant, guidelines prompt: 7
bm25 ndcg@10, filled by the guidelines prompt: 0.745
semantic ndcg@10, filled by the guidelines prompt: 0.834
hybrid ndcg@10, filled by the guidelines prompt: 0.821
reranked ndcg@10, filled by the guidelines prompt: 0.813
order, filled by the guidelines prompt: semantic > hybrid > reranked > bm25
rankers that change place when filled, guidelines prompt: none
verdicts that change when filled, guidelines prompt: none
```

The prompts disagree about the unjudged pairs. Counted as exact, partial and irrelevant, `short` grades them 4, 17, 5, and `guidelines` 5, 9, 12. They part on the unjudged products for `outdoor light fixtures` in BM25's top 10 ([Score every test query](#score-every-test-query)). Of those 8, 8 have `bulb` in their names, and `guidelines` calls 7 of them irrelevant and `short` 0. Chapter 1 argued that a bulb isn't a light fixture. Which reading the store's judges would take, nobody knows until they judge the bulbs.

With the holes filled, BM25 scores 0.754 with `short` and 0.745 with `guidelines`, against 0.725 on human grades alone, and semantic retrieval scores 0.833 and 0.834, against 0.830. The order of the four rankers on human grades alone is `semantic > hybrid > reranked > bm25`. The rankers that change place when `short` fills the holes are none, and when `guidelines` does, none. The verdicts of the planned comparisons that change are none with `short` and none with `guidelines`. Under human grades, the rankers' mean judged@10, the share of each top 10 that people judged, runs from 0.927 for BM25 to 0.990 for semantic retrieval ([Compare runs in a harness](#compare-runs-in-a-harness)); filled, every product in a top 10 has a grade.

How far can the filled grades be trusted? The judged pairs of the same pool are the closest evidence: there, the LLM's kappa with the store's judges is 0.571 for `short` and 0.470 for `guidelines`. Its grade is lower than the judges' on 61 pairs and higher on 65 with `short`, and lower on 77 and higher on 83 with `guidelines` ([Read the direction of the LLM's errors](#read-llm-error-direction)).

**Working rule:** Fill the unjudged pairs in your rankers' top 10s with LLM grades as a diagnostic, under every prompt you run, and report the filled score beside the human-only one with the number of pairs filled. If filling changes the order of two rankers or a verdict, have people judge those pairs. Never let a filled grade replace a human one.

## Check whether LLM grades order the rankers the same way {#system-order-human-versus-llm}

Two sets of judgments can disagree on many labels and still rank systems alike. Voorhees scored TREC runs with different sets of relevance judgments and found that "Very high correlations were found among the rankings of systems produced using different relevance judgment sets" ([Voorhees, 1998](https://people.eng.unimelb.edu.au/ammoffat/sigir98/abstracts/voorhees.html)). LLM judges show the same split. Across 42 sets of LLM labels for TREC's 2023 Deep Learning track, kappa ran from about 0.06 to 0.29 while the correlation of system rankings stayed between about 0.83 and 0.95 ([Rahmani et al., 2025, Table 3](https://arxiv.org/abs/2502.13908)).

That correlation is **Kendall's tau**. For every pair of systems, ask whether two orderings put them the same way round: **concordant** if they do, **discordant** if not. Tau is the difference between the two counts divided by the number of pairs, from 1 for the same order to −1 for the reverse. SciPy's `kendalltau` computes τ_b, a form that also handles ties ([SciPy documentation](https://docs.scipy.org/doc/scipy-1.18.0/reference/generated/scipy.stats.kendalltau.html)). Rankings with a tau of 0.9 or more "are often considered ‘effectively equivalent’ ... at least empirically", in Yilmaz et al.'s words ([Yilmaz et al., 2008](https://www.ccs.neu.edu/home/jaa/tmp/RankCorrelation.pdf)), and Sanderson and Soboroff found that "basing decisions on such thresholds is not as reliable as has been assumed" ([Sanderson and Soboroff, 2007](https://eprints.whiterose.ac.uk/id/eprint/4589/)).

In the store, score [chapter 1's four rankers](#search-end-to-end-decisions) on nDCG@10 under human grades and under each [prompt's](#write-judging-guidelines) LLM grades. The LLM judged only the test pool, the products in those rankers' top 10s, so as a control, the example also scores them with human grades for the pool's pairs only. With four rankers there are 6 pairs, so one swapped pair moves tau by 0.333, and tau can take only seven values. That is crude. Before you run it, predict: will LLM grades put the four rankers in the same order as human grades?

Example `kendall-tau-four-rankers` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from itertools import combinations

from scipy.stats import kendalltau

from lib.agreement import chapter_one_runs, llm_qrels
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

products, queries, people = load_products(), load_queries("test"), qrels("test")
runs = chapter_one_runs(products, queries)
short, guidelines = llm_qrels("short"), llm_qrels("guidelines")
pooled = {query_id: {product_id: grade for product_id, grade in people[query_id].items() if product_id in short[query_id]}
          for query_id in people}                 # people's grades for the pairs the LLM judged, and no others
judgment_sets = {"people": people, "people on the LLM's pairs": pooled, "the short prompt": short,
                 "the guidelines prompt": guidelines}
means = {name: {ranker: evaluate(run, judgments)["ndcg@10"].mean() for ranker, run in runs.items()}
         for name, judgments in judgment_sets.items()}
for name, scores in means.items():
    print(f"order under {name}: {' > '.join(sorted(scores, key=scores.get, reverse=True))}")
    for ranker, score in scores.items():
        print(f"{ranker} ndcg@10 under {name}: {score:.3f}")

orders = [sorted(scores, key=scores.get, reverse=True) for scores in means.values()]
steady = [ranker for position, ranker in enumerate(orders[0]) if all(order[position] == ranker for order in orders)]
print(f"rankers in the same place under every set of grades: {', '.join(steady) or 'none'}")
control = means["people on the LLM's pairs"]                              # the same pool, human grades
for name in ["the short prompt", "the guidelines prompt"]:
    print("\n".join(f"{ranker}, {name} minus people on the LLM's pairs: {means[name][ranker] - control[ranker]:+.3f}" for ranker in runs))
pairs, reference = list(combinations(runs, 2)), means["people"]
print(f"\npairs of rankers: {len(pairs)}\nchange in tau from one swapped pair: {2 / len(pairs):.3f}")
for name, scores in list(means.items())[1:]:
    swapped = [(first, second) for first, second in pairs                # discordant: opposite signs
               if (reference[first] - reference[second]) * (scores[first] - scores[second]) < 0]
    print(f"swapped under {name}: {'; '.join(f'{first} and {second}' for first, second in swapped) or 'none'}")
    print(f"tau by hand, people against {name}: {(len(pairs) - 2 * len(swapped)) / len(pairs):.3f}")
    print(f"tau from scipy, people against {name}: {kendalltau(list(reference.values()), list(scores.values())).statistic:.3f}")
```

Output:

```text
order under people: semantic > hybrid > reranked > bm25
bm25 ndcg@10 under people: 0.725
semantic ndcg@10 under people: 0.830
hybrid ndcg@10 under people: 0.812
reranked ndcg@10 under people: 0.798
order under people on the LLM's pairs: semantic > hybrid > reranked > bm25
bm25 ndcg@10 under people on the LLM's pairs: 0.795
semantic ndcg@10 under people on the LLM's pairs: 0.904
hybrid ndcg@10 under people on the LLM's pairs: 0.885
reranked ndcg@10 under people on the LLM's pairs: 0.869
order under the short prompt: reranked > semantic > hybrid > bm25
bm25 ndcg@10 under the short prompt: 0.832
semantic ndcg@10 under the short prompt: 0.903
hybrid ndcg@10 under the short prompt: 0.900
reranked ndcg@10 under the short prompt: 0.906
order under the guidelines prompt: reranked > semantic > hybrid > bm25
bm25 ndcg@10 under the guidelines prompt: 0.805
semantic ndcg@10 under the guidelines prompt: 0.878
hybrid ndcg@10 under the guidelines prompt: 0.876
reranked ndcg@10 under the guidelines prompt: 0.886
rankers in the same place under every set of grades: bm25
bm25, the short prompt minus people on the LLM's pairs: +0.037
semantic, the short prompt minus people on the LLM's pairs: -0.001
hybrid, the short prompt minus people on the LLM's pairs: +0.016
reranked, the short prompt minus people on the LLM's pairs: +0.037
bm25, the guidelines prompt minus people on the LLM's pairs: +0.010
semantic, the guidelines prompt minus people on the LLM's pairs: -0.026
hybrid, the guidelines prompt minus people on the LLM's pairs: -0.008
reranked, the guidelines prompt minus people on the LLM's pairs: +0.017

pairs of rankers: 6
change in tau from one swapped pair: 0.333
swapped under people on the LLM's pairs: none
tau by hand, people against people on the LLM's pairs: 1.000
tau from scipy, people against people on the LLM's pairs: 1.000
swapped under the short prompt: semantic and reranked; hybrid and reranked
tau by hand, people against the short prompt: 0.333
tau from scipy, people against the short prompt: 0.333
swapped under the guidelines prompt: semantic and reranked; hybrid and reranked
tau by hand, people against the guidelines prompt: 0.333
tau from scipy, people against the guidelines prompt: 0.333
```

Human grades give `semantic > hybrid > reranked > bm25`. The control keeps that order, with a tau of 1.000, so limiting the grades to the pool moves no ranker. It raises every score, BM25's from 0.725 to 0.795, because the ideal top 10 can only hold pooled products. `short` gives `reranked > semantic > hybrid > bm25`, and `guidelines` gives `reranked > semantic > hybrid > bm25`. These pairs swap under `short`: semantic and reranked; hybrid and reranked. Tau for `short` is 0.333 by hand and 0.333 from SciPy, and for `guidelines`, 0.333.

Against the control, LLM grades don't move the four rankers by the same amount, or in the same direction. With `short`, BM25 changes by +0.037, semantic retrieval by -0.001, the hybrid by +0.016 and the reranked hybrid by +0.037. With `guidelines`, the changes are +0.010, -0.026, -0.008 and +0.017. The judge raises some rankers and lowers others, and that moves them past each other.

Under `short`, semantic retrieval, the hybrid and the reranked hybrid nearly tie, at 0.903, 0.900 and 0.906. Tau ignores how far apart two rankers score, so a swap between near-ties counts as much as one between the best ranker and the worst. It also weighs a swap at the top the same as one at the bottom: "Kendall’s τ equally penalizes errors that occur at any part of the list" ([Yilmaz et al., 2008](https://www.ccs.neu.edu/home/jaa/tmp/RankCorrelation.pdf)). Yilmaz et al. note of the TREC runs they compared that the systems "have very similar performance. Hence, the Kendall’s τ statistic may be affected by these systems" ([Yilmaz et al., 2012](https://static.aminer.org/pdf/20170130/pdfs/sigir/jcmbhoqtt46bhqr5xegf9zy7snars82a.pdf)). These rankers keep their place under every set of grades: `bm25`. If you predicted the same order, notice where the orders differ: among the three rankers that human grades score 0.830, 0.812 and 0.798, gaps that no planned comparison establishes ([Rerun the planned comparisons](#llm-graded-verdicts)).

**Working rule:** Report tau with the list of swapped pairs, never alone. With a handful of rankers, where one swap moves tau by 0.333, don't read it against 0.9. Then test whether the swapped pairs differ at all, with [the planned comparisons under each set of grades](#llm-graded-verdicts).

## Rerun the planned comparisons with LLM grades {#llm-graded-verdicts}

Decisions come from verdicts, not from the [orderings that tau compares](#system-order-human-versus-llm). A difference is established when its paired [permutation test](#permutation-test-on-queries) p-value falls below the chapter's Bonferroni threshold, with the t-test and a bootstrap interval beside it ([Decide in advance what counts as established](#when-a-difference-is-established)). Would LLM grades have given the store the same verdicts? Expect trouble near the top: Otero et al. found that "LLM-based judgements are unfair at ranking top-performing systems", with "an exceedingly high rate of false positives regarding statistical differences" ([Otero et al., 2025](https://arxiv.org/abs/2411.13212)).

The store's planned comparisons are chapter 3's three, at 0.0167, with intervals at the 0.9833 level. The example runs each under human grades and under each [prompt's](#write-judging-guidelines) grades on the test pool, and adds chapter 3's exploratory comparison of the reranked hybrid with semantic retrieval:

Example `planned-comparisons-llm-grades` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from lib.agreement import PLANNED, PROMPTS, chapter_one_runs, llm_qrels   # PLANNED: chapter 3's, each stage against the last
from lib.metrics import evaluate
from lib.significance import compare, verdict
from lib.store import load_products, load_queries, qrels

EXPLORATORY = [("reranked", "semantic")]                                           # chosen after seeing test means
threshold = 0.05 / len(PLANNED)                   # chapter 3's threshold, so that a verdict means the same either way
print(f"planned comparisons: {len(PLANNED)}\np-value threshold: {threshold:.4f}\ninterval level: {1 - threshold:.4f}")

runs = chapter_one_runs(load_products(), load_queries("test"))
judgment_sets = {"people": qrels("test"), **{f"{prompt} prompt": llm_qrels(prompt) for prompt in PROMPTS}}
established, disagreements = {}, {judges: 0 for judges in judgment_sets}
for judges, judgments in judgment_sets.items():
    ndcg = {ranker: evaluate(run, judgments)["ndcg@10"] for ranker, run in runs.items()}
    for after, before in PLANNED + EXPLORATORY:
        result, name = compare(ndcg[after], ndcg[before], confidence=1 - threshold), f"{after} minus {before}, {judges}"
        print(f"\n{name}: {result['mean difference']:.3f}\n{name}, permutation p: {result['permutation p']:.3f}")
        if (after, before) in PLANNED:
            print(f"{name}, t-test p: {result['t-test p']:.3f}\n{name}, interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
            checks = verdict(result, threshold)
            established[(judges, after, before)] = checks["established"]
            disagree = [check for check in ["t-test", "interval"] if not checks[f"{check} agrees"]]
            disagreements[judges] += bool(disagree)
            print(f"{name}, established: {'yes' if checks['established'] else 'no'}\n"
                  f"{name}, disagrees with the permutation test: {' and '.join(disagree) or 'neither'}")

print()
for judges, count in disagreements.items():
    print(f"planned comparisons where the t-test or interval disagrees, {judges}: {count}")
for prompt in PROMPTS:
    differ = [pair for pair in PLANNED if established[(f"{prompt} prompt", *pair)] != established[("people", *pair)]]
    print(f"verdicts that differ from people's, {prompt} prompt: {'; '.join(f'{after} minus {before}' for after, before in differ) or 'none'}")
```

Output:

```text
planned comparisons: 3
p-value threshold: 0.0167
interval level: 0.9833

semantic minus bm25, people: 0.105
semantic minus bm25, people, permutation p: 0.001
semantic minus bm25, people, t-test p: 0.003
semantic minus bm25, people, interval: 0.047 to 0.205
semantic minus bm25, people, established: yes
semantic minus bm25, people, disagrees with the permutation test: neither

hybrid minus semantic, people: -0.018
hybrid minus semantic, people, permutation p: 0.125
hybrid minus semantic, people, t-test p: 0.123
hybrid minus semantic, people, interval: -0.048 to 0.006
hybrid minus semantic, people, established: no
hybrid minus semantic, people, disagrees with the permutation test: neither

reranked minus hybrid, people: -0.014
reranked minus hybrid, people, permutation p: 0.382
reranked minus hybrid, people, t-test p: 0.375
reranked minus hybrid, people, interval: -0.053 to 0.020
reranked minus hybrid, people, established: no
reranked minus hybrid, people, disagrees with the permutation test: neither

reranked minus semantic, people: -0.032
reranked minus semantic, people, permutation p: 0.048

semantic minus bm25, short prompt: 0.070
semantic minus bm25, short prompt, permutation p: 0.010
semantic minus bm25, short prompt, t-test p: 0.014
semantic minus bm25, short prompt, interval: 0.016 to 0.146
semantic minus bm25, short prompt, established: yes
semantic minus bm25, short prompt, disagrees with the permutation test: neither

hybrid minus semantic, short prompt: -0.002
hybrid minus semantic, short prompt, permutation p: 0.851
hybrid minus semantic, short prompt, t-test p: 0.861
hybrid minus semantic, short prompt, interval: -0.029 to 0.036
hybrid minus semantic, short prompt, established: no
hybrid minus semantic, short prompt, disagrees with the permutation test: neither

reranked minus hybrid, short prompt: 0.006
reranked minus hybrid, short prompt, permutation p: 0.727
reranked minus hybrid, short prompt, t-test p: 0.714
reranked minus hybrid, short prompt, interval: -0.029 to 0.042
reranked minus hybrid, short prompt, established: no
reranked minus hybrid, short prompt, disagrees with the permutation test: neither

reranked minus semantic, short prompt: 0.003
reranked minus semantic, short prompt, permutation p: 0.847

semantic minus bm25, guidelines prompt: 0.073
semantic minus bm25, guidelines prompt, permutation p: 0.045
semantic minus bm25, guidelines prompt, t-test p: 0.057
semantic minus bm25, guidelines prompt, interval: 0.006 to 0.183
semantic minus bm25, guidelines prompt, established: no
semantic minus bm25, guidelines prompt, disagrees with the permutation test: interval

hybrid minus semantic, guidelines prompt: -0.001
hybrid minus semantic, guidelines prompt, permutation p: 0.929
hybrid minus semantic, guidelines prompt, t-test p: 0.945
hybrid minus semantic, guidelines prompt, interval: -0.045 to 0.037
hybrid minus semantic, guidelines prompt, established: no
hybrid minus semantic, guidelines prompt, disagrees with the permutation test: neither

reranked minus hybrid, guidelines prompt: 0.010
reranked minus hybrid, guidelines prompt, permutation p: 0.657
reranked minus hybrid, guidelines prompt, t-test p: 0.609
reranked minus hybrid, guidelines prompt, interval: -0.024 to 0.076
reranked minus hybrid, guidelines prompt, established: no
reranked minus hybrid, guidelines prompt, disagrees with the permutation test: neither

reranked minus semantic, guidelines prompt: 0.009
reranked minus semantic, guidelines prompt, permutation p: 0.581

planned comparisons where the t-test or interval disagrees, people: 0
planned comparisons where the t-test or interval disagrees, short prompt: 0
planned comparisons where the t-test or interval disagrees, guidelines prompt: 1
verdicts that differ from people's, short prompt: none
verdicts that differ from people's, guidelines prompt: semantic minus bm25
```

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

Example `correct-llm-scores-with-humans` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
import pandas as pd

from lib.agreement import PROMPTS, chapter_one_runs, llm_qrels
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

JUDGED, DRAWS = 10, 2000                          # test queries people judge in each draw, and the number of draws
runs = chapter_one_runs(load_products(), load_queries("test"))
people = pd.DataFrame({ranker: evaluate(run, qrels("test"))["ndcg@10"] for ranker, run in runs.items()})
rng = np.random.default_rng(2026)
draws = [rng.choice(people.index, JUDGED, replace=False) for _ in range(DRAWS)]    # which queries people judge
print(f"queries judged by people in each draw: {JUDGED} of {len(people)}\ndraws: {DRAWS:,}")

for after, before in [("semantic", "bm25"), ("hybrid", "semantic")]:
    gap_people = people[after] - people[before]                        # per-query gaps under people's grades
    print(f"\n{after} minus {before}, people, all queries: {gap_people.mean():.3f}")
    alone = np.std([gap_people[judged].mean() for judged in draws])                # the human sample used alone
    print(f"{after} minus {before}, human sample alone, spread: {alone:.3f}")
    for prompt in PROMPTS:
        llm = {ranker: evaluate(run, llm_qrels(prompt))["ndcg@10"] for ranker, run in runs.items()}
        gap_llm, name = llm[after] - llm[before], f"{after} minus {before}, {prompt} prompt"
        corrected = [gap_llm.mean() + (gap_people[judged] - gap_llm[judged]).mean() for judged in draws]
        print(f"{name}, LLM only: {gap_llm.mean():.3f}")
        print(f"{name}, corrected, mean over draws: {np.mean(corrected):.3f}")
        print(f"{name}, corrected, spread: {np.std(corrected):.3f}")
        print(f"{name}, corrected spread smaller than the human sample's: {'yes' if np.std(corrected) < alone else 'no'}")
        print(f"{name}, correlation of per-query gaps with people's: {np.corrcoef(gap_llm, gap_people)[0, 1]:.3f}")
```

Output:

```text
queries judged by people in each draw: 10 of 30
draws: 2,000

semantic minus bm25, people, all queries: 0.105
semantic minus bm25, human sample alone, spread: 0.045
semantic minus bm25, short prompt, LLM only: 0.070
semantic minus bm25, short prompt, corrected, mean over draws: 0.104
semantic minus bm25, short prompt, corrected, spread: 0.036
semantic minus bm25, short prompt, corrected spread smaller than the human sample's: yes
semantic minus bm25, short prompt, correlation of per-query gaps with people's: 0.641
semantic minus bm25, guidelines prompt, LLM only: 0.073
semantic minus bm25, guidelines prompt, corrected, mean over draws: 0.104
semantic minus bm25, guidelines prompt, corrected, spread: 0.039
semantic minus bm25, guidelines prompt, corrected spread smaller than the human sample's: yes
semantic minus bm25, guidelines prompt, correlation of per-query gaps with people's: 0.692

hybrid minus semantic, people, all queries: -0.018
hybrid minus semantic, human sample alone, spread: 0.016
hybrid minus semantic, short prompt, LLM only: -0.002
hybrid minus semantic, short prompt, corrected, mean over draws: -0.017
hybrid minus semantic, short prompt, corrected, spread: 0.023
hybrid minus semantic, short prompt, corrected spread smaller than the human sample's: no
hybrid minus semantic, short prompt, correlation of per-query gaps with people's: 0.168
hybrid minus semantic, guidelines prompt, LLM only: -0.001
hybrid minus semantic, guidelines prompt, corrected, mean over draws: -0.017
hybrid minus semantic, guidelines prompt, corrected, spread: 0.024
hybrid minus semantic, guidelines prompt, corrected spread smaller than the human sample's: no
hybrid minus semantic, guidelines prompt, correlation of per-query gaps with people's: 0.342
```

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
