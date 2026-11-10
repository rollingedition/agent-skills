---
title: "A Primer on Search Relevance"
chapter: "Retrieval for LLM applications"
chapter_id: retrieval-for-llm-applications
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/retrieval-for-llm-applications
license: CC BY 4.0
attribution: "“Retrieval for LLM applications,” chapter 10 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/retrieval-for-llm-applications. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Retrieval for LLM applications

By the end of this chapter you can measure the retrieval behind an LLM that answers from it: score an answer by the products it cites, check each citation against what retrieval returned, measure the products the LLM reads, choose what to index as one retrievable unit, and read an agent's searches from the record of its tool calls.

The store, an online furniture and home-goods retailer and this book's case study ([chapter 1](#store-data)), shows shoppers a ranked list. A shopping assistant answers in words instead: a shopper writes what they want, and a **large language model** (LLM), a model trained on large amounts of text to generate text in response to a prompt, recommends a few products and cites each one by its ID. The prompt tells the LLM to recommend only the products that search puts in front of it, so the assistant can be no better than its retrieval. The same holds for an **agent**, an LLM that runs the searches itself and decides how many to run. This chapter measures both with the store's human judgments.

The store's LLM is the open model `gemma4:12b-it-q4_K_M`. We chose it because it is open and runs locally, so anyone can rerun the **recordings**: `recordings/rag_answers.py` and `recordings/agent_trace.py` made each model call once, at temperature 0 with a fixed seed and thinking off ([chapter 9](#ranking)), and saved the replies, which the examples read through `lib.recorded`. Each recording's **manifest**, the file that describes it, gives the model's licence as Apache-2.0. For an answer, the LLM read each product's name, class, category, description and attributes as text, and the agent's search tool shows it less. The human judges also saw each product's image and web page ([what the LLM saw](#what-the-llm-saw)). [Semantic retrieval](#search-by-meaning) ranks by the recorded embeddings of `Snowflake/snowflake-arctic-embed-m-v1.5`, and [BM25](#rank-with-bm25) is the book's unstemmed baseline, `lib.lexical`. Every finding about the LLM holds for this model, these prompts and the 30 [test queries](#store-data), not for LLMs in general.

Before reading any test result, the chapter fixes 2 planned comparisons on the test queries, both of semantic retrieval against BM25:

1. behind the recorded answers, on the share of each answer's cited products that people judged exact ([Score each answer](#retrieval-bounds-the-answer))
2. behind the agent's search tool, on precision@3 of the products it picks ([Compare the retrievers](#retriever-behind-agent-tool))

By [the book's rule](#when-a-difference-is-established), a difference is established when its paired [permutation test](#permutation-test-on-queries) gives a p-value below 0.025, 0.05 divided by the number of planned comparisons. The [paired t-test](#paired-t-test-on-queries) and a [bootstrap interval](#report-the-size-of-a-gap) at the 97.5% level stand beside it. Anything else on the test queries is a description, or labelled exploratory.

## Put retrieved products in the prompt {#put-retrieved-products-in-the-prompt}

**Retrieval-augmented generation** (RAG), the design behind a shopping assistant, pairs an LLM with a retriever. For each request, the retriever finds a few texts in an index, and the LLM writes its answer from them. In Lewis et al.'s RAG models, the "non-parametric memory is a dense vector index of Wikipedia, accessed with a pre-trained neural retriever". The authors note two open problems of language models on their own: "providing provenance for their decisions and updating their world knowledge remain open research problems" ([Lewis et al., 2020](https://arxiv.org/abs/2005.11401)). A store has both problems: its catalog changes, and an answer should say which products it recommends. The retrieved text goes into the **prompt**, the input the model reads, and that text is the **context**. A model reads at most a fixed number of [tokens](#turn-text-into-embeddings), the word pieces of its own vocabulary. That limit is its **context window**.

Why not put the whole catalog in the prompt and skip retrieval? It has to fit, and even when it fits, models don't read a long prompt evenly. Liu et al. found that "performance is often highest when relevant information occurs at the beginning or end of the input context", and that it "significantly degrades when models must access relevant information in the middle of long contexts" ([Liu et al., 2024](https://aclanthology.org/2024.tacl-1.9/)). A later study found that this lost-in-the-middle effect, "the LiM effect", "is strongest when inputs occupy up to 50% of a model's context window", and that near the limit it gives way to a bias toward the end ([Veseli et al., 2025](https://arxiv.org/abs/2508.07479)). More passages aren't always better either. As Jin et al. gave long-context LLMs more retrieved passages, "the quality of generated output initially improves first, but then subsequently declines", and they identify retrieved hard negatives, passages that look relevant but aren't, as a key contributor to the decline ([Jin et al., 2024](https://arxiv.org/abs/2410.05983)). One vendor's engineering post suggests the opposite for small collections: "If your knowledge base is smaller than 200,000 tokens (about 500 pages of material)," put all of it in the prompt ([Anthropic, 2024](https://www.anthropic.com/news/contextual-retrieval)). That is a vendor's rule of thumb, not a measurement.

In the store, the recording of answers ([Score each answer](#retrieval-bounds-the-answer)) put five products in each prompt, after these instructions: "You help shoppers at an online furniture and home-goods store. Using only the products listed below, answer the shopper. Recommend up to three products that fit, cite each one by its ID, and say plainly if none of them fit. Don't mention products that aren't listed." Count the words of the whole catalog as the LLM would read it, and compare:

Example `catalog-against-the-context` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from statistics import median

from lib.agreement import as_the_llm_saw
from lib.recorded import manifest, rag_answers
from lib.store import load_products

recording = manifest("rag-answers")
window = recording["options"]["num_ctx"]
print("model:", recording["model"])
print("licence in the manifest:", recording["model_licence"])
print("instructions:", recording["prompts"].split("\n")[0])
print("context window the recording set, in tokens:", window)

products = load_products()
words = {product_id: len(f"ID: {product_id}\n{as_the_llm_saw(product)}".split())    # each product as the LLM read it
         for product_id, product in products.iterrows()}
instructions = len(recording["prompts"].split())                  # the prompt's own words, without the query
prompts = [instructions + sum(words[p] for p in ids) for ids in rag_answers()["context_ids"]]
catalog = sum(words.values())
print(f"words in the catalog as the LLM reads it: {catalog:,}")
print(f"words in one prompt with five products, median: {median(prompts):,.0f}")
print(f"the catalog against one prompt: {catalog / median(prompts):,.0f} times")
print(f"the catalog against the recording's window, at one token per word: {catalog / window:,.0f} times")
print(f"the catalog against 200,000 tokens, at one token per word: {catalog / 200_000:.1f} times")
```

Output:

```text
model: gemma4:12b-it-q4_K_M
licence in the manifest: Apache-2.0
instructions: You help shoppers at an online furniture and home-goods store. Using only the products listed below, answer the shopper. Recommend up to three products that fit, cite each one by its ID, and say plainly if none of them fit. Don't mention products that aren't listed.
context window the recording set, in tokens: 8192
words in the catalog as the LLM reads it: 1,091,544
words in one prompt with five products, median: 536
the catalog against one prompt: 2,035 times
the catalog against the recording's window, at one token per word: 133 times
the catalog against 200,000 tokens, at one token per word: 5.5 times
```

Even with the book's sample cutting descriptions to about 400 characters ([data card](https://github.com/rollingedition/book-primer-on-search-relevance/blob/975f0c078e472eb1d3e9202a4a5feaddae27d052/examples/data/wands/README.md)), the catalog holds 1,091,544 words, and a prompt with five products holds a median of 536: the catalog is 2,035 times larger. The examples have no tokenizer for this model, so they count words. The recording set a context window of 8192 tokens. If every word were a single token, the catalog would fill that window 133 times over, and the vendor's 200,000 tokens 5.5 times over. The store has to retrieve.

**Working rule:** Put a few retrieved items in the prompt, not the collection, and choose how many by measuring answers on train queries at several sizes, because more context can help or hurt. The store's recording answered only the test queries, five products each, so five is a fixed setting here, not a measured one. Consider sending the whole collection only when it fits well inside the window, and then test it against retrieval on the same queries.

## Score each answer by the products it cites {#retrieval-bounds-the-answer}

An LLM told to answer from a [context](#put-retrieved-products-in-the-prompt) should recommend only what the context holds, and [the ID check](#check-citations-against-context) tests that it does. If no exact product is in the context, no prompt makes a grounded answer recommend one. Retrieval sets a ceiling on the answer, and what else the context holds matters too. Cuconasu et al. found that the retriever's "highest-scoring documents that are not directly relevant to the query (e.g., do not contain the answer)" hurt answers, while, "Even more surprising, we discovered that adding random documents in the prompt improves the LLM accuracy by up to 35%" ([Cuconasu et al., 2024](https://arxiv.org/abs/2401.14887)). Products that look right but aren't are **distractors**, the store's version of those passages. In question answering, Joren et al. found a related pattern: when the context lacked what was needed, the larger models they tested, Gemini 1.5 Pro, GPT 4o and Claude 3.5, "often output incorrect answers instead of abstaining", while smaller ones, Mistral 3 and Gemma 2 among them, often hallucinated or abstained even when the context was sufficient ([Joren et al., 2024](https://arxiv.org/abs/2411.06037)).

A **citation** here is the ID an answer gives for a product it recommends. With judgments, you can score an answer without reading it: look up each cited product's grade. The **exact share** of an answer is the share of its cited products that people judged [exact](#store-data). An answer that cites nothing scores 0, because it gives the shopper nothing that fits, whether or not that was the right call. A separate count of answers that recommend nothing covers that case.

```text
exact share = (cited products judged exact) / (products cited),   0 when the answer cites nothing
```

The store's recording answered each test query three times, as "I'm looking for" followed by the query. Each answer came from a different context of five products: semantic retrieval's top 5, BM25's top 5, or five products drawn at random with a fixed seed. The random context is a floor, a context no retriever chose. The model, the prompt and the query stay the same, so the answers differ only because their contexts do. The examples read each context as the recording stored it, in the order the LLM read it. The BM25 contexts keep tied products in bm25s's own order, not by `product_id` as `lib.lexical` does, so 7 of the 30 differ from what `lib.lexical` returns, 6 only in order. The recording asked for JSON with the answer and the cited IDs in separate fields. `score_answers` in `lib.generation` scores each answer on the human grades. The example then makes the first of the chapter's [two planned comparisons](#retrieval-for-llm-applications), established if its permutation p-value is below 0.025.

Before you run it, predict what the LLM does with the random context, where the prompt tells it to "say plainly if none of them fit". Of the 30 answers, how many will recommend nothing?

Example `rag-answers-by-context` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.generation import PLANNED_TEST_COMPARISONS, THRESHOLD, report_planned, score_answers
from lib.lexical import LexicalSearch
from lib.recorded import rag_answers
from lib.store import load_products, load_queries, qrels

answers = rag_answers()
stored = answers[answers["context"] == "bm25"].set_index("query_id")["context_ids"]   # as the LLM read them
rerun = LexicalSearch(load_products()).run(load_queries("test"), k=5)                 # ties by product_id
differ = [q for q in stored.index if stored[q] != rerun[q]]
print("bm25 contexts that differ from lib.lexical:", len(differ))
print("bm25 contexts that differ from lib.lexical only in order:", sum(set(stored[q]) == set(rerun[q]) for q in differ))

scores = score_answers(answers, qrels("test"))            # one row per test query and context, on human grades
for context, rows in scores.groupby("context", sort=False):
    held, nothing = rows["exact in context"] > 0, rows["cited"] == 0
    print(f"{context}, unjudged products in the contexts: {rows['unjudged in context'].sum()}")
    print(f"{context}, contexts with an exact product: {held.sum()}")
    print(f"{context}, answers that cite an exact product: {(rows['exact cited'] > 0).sum()}")
    print(f"{context}, products cited: {rows['cited'].sum()}")
    print(f"{context}, cited products that are exact: {rows['exact cited'].sum()}")
    print(f"{context}, mean exact share: {rows['exact share'].mean():.3f}")
    print(f"{context}, answers that recommend nothing: {nothing.sum()}")
    print(f"{context}, recommend nothing, with an exact product in the context: {(nothing & held).sum()}")
    print(f"{context}, recommend something, with no exact product in the context: {(~nothing & ~held).sum()}")
    near = rows[~held]                                    # answers whose context held no exact product
    print(f"{context}, products cited with no exact product in the context: {near['cited'].sum()}")
    print(f"{context}, of those, partial: {near['partial cited'].sum()}")
    print(f"{context}, unjudged products cited: {rows['unjudged cited'].sum()}")
print("answers that cite more exact products than their context holds:",
      (scores["exact cited"] > scores["exact in context"]).sum())

print("planned test comparisons:", len(PLANNED_TEST_COMPARISONS))
print(f"p-value threshold: {THRESHOLD:.3f}")
share = scores.pivot(index="query_id", columns="context", values="exact share")
report_planned("answers, semantic over bm25", share["semantic"], share["bm25"])
```

Output:

```text
bm25 contexts that differ from lib.lexical: 7
bm25 contexts that differ from lib.lexical only in order: 6
semantic, unjudged products in the contexts: 0
semantic, contexts with an exact product: 25
semantic, answers that cite an exact product: 22
semantic, products cited: 80
semantic, cited products that are exact: 60
semantic, mean exact share: 0.658
semantic, answers that recommend nothing: 2
semantic, recommend nothing, with an exact product in the context: 1
semantic, recommend something, with no exact product in the context: 4
semantic, products cited with no exact product in the context: 11
semantic, of those, partial: 11
semantic, unjudged products cited: 0
bm25, unjudged products in the contexts: 10
bm25, contexts with an exact product: 24
bm25, answers that cite an exact product: 23
bm25, products cited: 73
bm25, cited products that are exact: 52
bm25, mean exact share: 0.639
bm25, answers that recommend nothing: 3
bm25, recommend nothing, with an exact product in the context: 0
bm25, recommend something, with no exact product in the context: 3
bm25, products cited with no exact product in the context: 7
bm25, of those, partial: 7
bm25, unjudged products cited: 1
random, unjudged products in the contexts: 147
random, contexts with an exact product: 1
random, answers that cite an exact product: 1
random, products cited: 1
random, cited products that are exact: 1
random, mean exact share: 0.033
random, answers that recommend nothing: 29
random, recommend nothing, with an exact product in the context: 0
random, recommend something, with no exact product in the context: 0
random, products cited with no exact product in the context: 0
random, of those, partial: 0
random, unjudged products cited: 0
answers that cite more exact products than their context holds: 0
planned test comparisons: 2
p-value threshold: 0.025
answers, semantic over bm25, mean difference: 0.019
answers, semantic over bm25, wins, losses, ties: 4, 5, 21
answers, semantic over bm25, permutation p: 0.765
answers, semantic over bm25, established at 0.025: no
answers, semantic over bm25, t-test p: 0.715
answers, semantic over bm25, t-test agrees: yes
answers, semantic over bm25, 97.5% interval: -0.078 to 0.161
answers, semantic over bm25, interval agrees: yes
```

| Measure | Semantic | BM25 | Random |
| --- | --- | --- | --- |
| Contexts with an exact product | 25 | 24 | 1 |
| Answers that cite an exact product | 22 | 23 | 1 |
| Products cited | 80 | 73 | 1 |
| Cited products that are exact | 60 | 52 | 1 |
| Mean exact share | 0.658 | 0.639 | 0.033 |
| Answers that recommend nothing | 2 | 3 | 29 |

Given random products, the LLM recommends nothing in 29 of the 30 answers. Its only citation is an exact product that the random draw happened to include. The random contexts hold 147 products nobody judged, which count as not exact. We expect few of them to fit, but no judgment says so. If you predicted that the LLM would force a recommendation, this model and prompt didn't, for random products.

The ceiling holds: the number of answers that cite more exact products than their context holds is 0. Near misses are another matter. Where the context held no exact product, the answer still recommended something 4 times with semantic retrieval and 3 times with BM25, rather than say that no product fits exactly. Every product those answers cite is partial: 11 of 11 with semantic retrieval and 7 of 7 with BM25, the right kind of product with a modifier wrong. Whether that is a failure depends on whether the shopper wants near matches. The reverse failure is rarer: the answers that recommend nothing although the context held an exact product number 1 for semantic retrieval and 0 for BM25. BM25's contexts hold 10 unjudged products and semantic retrieval's 0. The score reads only cited products, and BM25's answers cite 1 unjudged product, which counts as not exact.

Semantic retrieval's lead on [nDCG@10](#score-one-ranking) is established ([chapter 3](#compare-runs-in-a-harness)), but on the first planned comparison its difference from BM25 of 0.019 in mean exact share isn't, at a permutation p-value of 0.765 ([both comparisons](#retrieval-for-llm-applications-decisions)).

**Working rule:** Score every answer by its cited products' human grades, and report beside it how many answers recommend nothing, split by whether the context held an exact product. Keep a random context as a floor whenever you change the model or the prompt: an answer that recommends something from random products has invented a fit. Test a retriever's gain on the answers too, because a gain in ranking needn't carry through.

## Check every citation against the context {#check-citations-against-context}

**Grounding** means that an answer rests on the context it was given, as [the exact share](#retrieval-bounds-the-answer) assumes, not on what the model remembers or invents. Citations make grounding checkable, and **attribution** asks whether a cited source supports the statement it is attached to. Audits find that citations often don't. In a 2023 audit of generative search engines, "a mere 51.5% of generated sentences are fully supported by citations" and "only 74.5% of citations support their associated sentence" ([Liu et al., 2023](https://arxiv.org/abs/2304.09848)). On ELI5, the ALCE benchmark's long-form questions from the Reddit forum Explain Like I'm Five, with 2023's models, "even the best models lack complete citation support 50% of the time" ([Gao et al., 2023](https://arxiv.org/abs/2305.14627)).

Check citations at two levels, cheapest first. The first is exact and needs no model: every cited ID must be one the context held. An ID from outside the context names a product the model remembered or made up, and either way the answer isn't grounded. The second level asks whether the cited product's text supports what the answer says about it, which needs a reader ([Check what the cited product supports](#check-citation-support)).

In the store, the answer recording's schema asked for the cited IDs as a list of integers in a field of their own (`schemas` in the manifest). The schema describes the field's form; it says nothing about which IDs go in it, or how many. The example checks each of the [recorded answers](#retrieval-bounds-the-answer) against its context, and compares the field with the context IDs written in the answer's text. The text can't reveal an ID from outside the context, which would look like any other number an answer writes, such as a size. That is why the IDs belong in a field:

Example `citations-inside-the-context` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.generation import ids_in_text
from lib.recorded import rag_answers

answers = rag_answers()
outside = answers.apply(lambda a: [p for p in a["cited"] if p not in a["context_ids"]], axis=1)
repeated = answers["cited"].map(lambda cited: len(cited) != len(set(cited)))
written = answers.apply(lambda a: ids_in_text(a["answer"], a["context_ids"]), axis=1)   # IDs the text writes out
print("answers:", len(answers))
print("answers that cite an ID outside their context:", (outside.map(len) > 0).sum())
print("answers that cite one ID twice:", repeated.sum())
print("answers that cite nothing:", (answers["cited"].map(len) == 0).sum())
print("answers that cite more than three products:", (answers["cited"].map(len) > 3).sum())
print("answers whose text and cited IDs differ:", (written != answers["cited"].map(set)).sum())
```

Output:

```text
answers: 90
answers that cite an ID outside their context: 0
answers that cite one ID twice: 0
answers that cite nothing: 34
answers that cite more than three products: 3
answers whose text and cited IDs differ: 0
```

Of the 90 answers, the check counts 0 that cite an ID outside their context, 0 that cite one ID twice, and 0 whose text and field disagree. The answers that cite nothing number 34. The instruction the answers do break is how many to recommend: 3 cite more than three products, though the prompt says "Recommend up to three".

On this recording, the ID check finds no ungrounded citation. That is the result you want, and no reason to drop the check: it costs a set lookup per answer, and a different model, prompt or context length can fail it. Passing it says only that each recommended product was in front of the model, not that it fits.

**Working rule:** Run the ID check on every answer, offline and before a shopper sees it, and treat an ID outside the context as a failed answer: drop it or retry, and never show it. Ask for citations in a field of their own so that the check doesn't parse prose, and check that the text and the field agree. Count the instructions the answers break, such as the number of recommendations, and enforce in code the ones that matter.

## Check what the cited product supports {#check-citation-support}

The [second level of checking](#check-citations-against-context) asks whether the cited text supports the claim. **Faithfulness** is the share of an answer's claims that the context supports. In the Ragas documentation's words (its pages name no version; the ones opened were dated 2025-12-09), "A response is considered **faithful** if all its claims can be supported by the retrieved context" ([Ragas documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)). Checking it takes a reader. ALCE uses a model for natural language inference (NLI), the task of deciding whether one text entails another: "a T5-11B … model fine-tuned on a collection of natural language inference (NLI) datasets". A statement's citation recall is 1 only when its citations together entail it ([Gao et al., 2023, sections 3.2 and 3.3](https://arxiv.org/html/2305.14627)). An LLM can judge support too, with limits. In the 2024 RAG track of TREC, the Text REtrieval Conference's shared evaluations, Thakur et al. found that "human and GPT-4o predictions match perfectly (on a three-level scale)" on 56% of judgments made from scratch, "increasing to 72% in the manual with post-editing condition". They also found that "an independent human judge correlates better with GPT-4o than a human judge", so part of the disagreement is between people ([Thakur et al., 2025](https://arxiv.org/abs/2504.15205)).

Support isn't relevance. A citation can be faithful to the product's text and still recommend the wrong product: the text says what the answer claims, and the product isn't what the shopper asked for. Only the judgments catch that.

Read one of the store's answers by hand first: the one for the test query `medium size chandelier`, from the semantic context. Then count the human grades of every product cited in the [recorded answers](#retrieval-bounds-the-answer) from the semantic and BM25 contexts:

Example `faithful-but-partial` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from collections import Counter

from lib.agreement import LABELS
from lib.recorded import rag_answers
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
answers = rag_answers().set_index(["query_id", "context"])

chandelier, claim = 58, "medium-sized"                     # one answer, read by hand
answer, judged = answers.loc[(chandelier, "semantic")], judgments[chandelier]
cited = answer["cited"][0]
print("query:", queries.at[chandelier, "query"])
print("answer:", answer["answer"])
print("cited product:", products.at[cited, "name"])
print(f"the cited product's text says {claim}:", "yes" if claim in products.at[cited, "description"] else "no")
print("the judges' label:", LABELS[judged[cited]])
print("exact products in this answer's context:", sum(judged.get(p, 0) == 2 for p in answer["context_ids"]))

retrieved = answers.drop("random", level="context")        # every citation from the two retrievers' contexts
labels = Counter(LABELS.get(judgments[query_id].get(p), "unjudged")
                 for (query_id, _), cited_ids in retrieved["cited"].items() for p in cited_ids)
print("cited products, semantic and bm25 contexts:", sum(labels.values()))
for label in ["exact", "partial", "irrelevant", "unjudged"]:
    print(f"cited products, {label}:", labels[label])
```

Output:

```text
query: medium size chandelier
answer: I recommend the sybil 12 - light unique / statement classic / traditional chandelier with antler accents (ID: 8171), as it is specifically described as a perfect medium-sized lighting fixture.
cited product: sybil 12 - light unique / statement classic / traditional chandelier with antler accents
the cited product's text says medium-sized: yes
the judges' label: partial
exact products in this answer's context: 2
cited products, semantic and bm25 contexts: 153
cited products, exact: 112
cited products, partial: 40
cited products, irrelevant: 0
cited products, unjudged: 1
```

The answer recommends one chandelier, saying it "is specifically described as a perfect medium-sized lighting fixture". The cited product's description does say `medium-sized` (yes), so a support check would pass the claim. The store's judges called the product partial: by [WANDS's definition](#store-data), the right kind of product, missing a modifier the shopper asked for. They saw its image and product page, which the LLM didn't. Its context held 2 exact products, and the answer recommended neither. For this answer, the citation is faithful, and the recommendation still misses.

Across both retrievers' answers, the 153 cited products break down as 112 exact, 40 partial, 0 irrelevant and 1 unjudged. Every cited product that isn't exact is partial, apart from the 1 nobody judged: the kind of product the shopper asked for, with a modifier wrong by the judges' reading.

**Working rule:** Score answers on your judgments first, because they say whether a recommendation fits. Add a support check for the claims an answer makes about each product, by an NLI model or an LLM judge. Calibrate that judge on a human sample, as [chapter 4 does](#calibrate-on-a-human-sample) and as ARES does: "To mitigate potential prediction errors," it uses "a small set of human-annotated datapoints for prediction-powered inference (PPI)", a method that corrects the judge's estimate with the human labels ([Saad-Falcon et al., 2024](https://arxiv.org/abs/2311.09476)). For queries you have no judgments for, a support check is all you have, so say so when you report it.

## Measure the context, then the answer {#measure-the-context}

A RAG system can fail at retrieval or at generation, so measure the context as well as [the answers](#retrieval-bounds-the-answer). Ragas, a framework for evaluating RAG, scores several measures without reference answers, among them "the ability of the retrieval system to identify relevant and focused context passages", faithfulness and the answer's relevance; its context recall needs a reference ([Es et al., 2024](https://aclanthology.org/2024.eacl-demo.16/)). Its context measures carry [chapter 3's metrics](#count-relevant-in-top-k) over, with an LLM as the judge. **Context precision** is rank-aware: "It is calculated as the mean of the precision@k for each chunk in the context", over the positions that hold a relevant chunk ([Ragas documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)). **Context recall** is the share of a reference answer's claims that the context supports, and an ID-based variant compares the retrieved IDs with reference IDs ([Ragas documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/)). With judgments in hand, the reference is the set of exact products, and the ID-based context recall is [recall@k](#count-relevant-in-top-k).

```text
context recall@k    = (exact products in the top k) / (exact products judged for the query)
context precision@k = mean of precision@i over the positions i ≤ k that hold an exact product
```

Which measure tracks the answers? Salemi and Zamani found that relevance labels show "a small correlation with the RAG system's downstream performance", and they score each retrieved passage by the answer the LLM gives from it instead ([Salemi and Zamani, 2024](https://arxiv.org/abs/2404.13781)). **Spearman's rank correlation** answers the question for one recording: it is the correlation between two measures' ranks rather than their values, 1 when they order the cases the same way and near 0 when the orders are unrelated.

In the store, take every context that a retriever built for the [recorded answers](#retrieval-bounds-the-answer), two per test query. The first example builds context recall and context precision by hand, checks them against `lib.metrics.recall_at_k` and the copies in `lib.generation`, and works through one context:

Example `context-measures-by-hand` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib import generation
from lib.generation import EXACT
from lib.metrics import precision_at_k, recall_at_k
from lib.recorded import rag_answers
from lib.store import load_queries, qrels


def context_precision(context, judged, k=5):
    """Ragas's context precision, with the judges as the reference: mean precision@i over exact positions i."""
    hits = [i for i, p in enumerate(context[:k], start=1) if judged.get(p, 0) == EXACT]
    return sum(precision_at_k(context, judged, i) for i in hits) / len(hits) if hits else 0.0


def context_recall(context, judged, k=5):
    """Ragas's ID-based context recall: the share of the reference IDs that the context holds."""
    reference = {p for p, grade in judged.items() if grade == EXACT}
    return len(reference & set(context[:k])) / len(reference)


judgments, queries = qrels("test"), load_queries("test")
answers = rag_answers().query("context != 'random'")             # the two retrievers' contexts for each test query
contexts = [(answer.context_ids, judgments[answer.query_id]) for answer in answers.itertuples()]
print("contexts:", len(contexts))
same = {"recall_at_k": all(context_recall(c, j) == recall_at_k(c, j, 5) for c, j in contexts),
        "lib.generation": all(context_precision(c, j) == generation.context_precision(c, j) for c, j in contexts)}
print("context recall equals recall_at_k every time:", "yes" if same["recall_at_k"] else "no")
print("context precision equals lib.generation's every time:", "yes" if same["lib.generation"] else "no")

first = answers.iloc[0]                                          # one context, worked through
context, judged = first["context_ids"], judgments[first["query_id"]]
print(f"grades in order, {queries.at[first['query_id'], 'query']}, {first['context']}:", *[judged.get(p, 0) for p in context])
print(f"context precision@5: {context_precision(context, judged):.3f}")
print(f"precision@5: {precision_at_k(context, judged, 5):.3f}")
exact = sorted(sum(grade == EXACT for grade in grades.values()) for grades in judgments.values())
print(f"exact products judged per test query: {exact[0]} to {exact[-1]}")
print(f"highest recall@5 possible for the query with the most: {5 / exact[-1]:.3f}")
```

Output:

```text
contexts: 60
context recall equals recall_at_k every time: yes
context precision equals lib.generation's every time: yes
grades in order, door jewelry organizer, semantic: 1 1 2 2 2
context precision@5: 0.478
precision@5: 0.600
exact products judged per test query: 4 to 170
highest recall@5 possible for the query with the most: 0.029
```

Over the 60 contexts, context recall equals `recall_at_k` every time (yes), and context precision equals `lib.generation`'s (yes). For the semantic context of `door jewelry organizer`, the grades in order are 1 1 2 2 2. Precision@5 is 0.600, and context precision is 0.478, lower because the exact products come last.

The second example correlates each measure with the answer's [exact share](#retrieval-bounds-the-answer), the share of its cited products judged exact. It computes Spearman's correlation by hand, as Pearson's correlation of the ranks, and checks it against SciPy's `spearmanr`:

Example `context-measures-against-answers` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import pandas as pd
from scipy import stats

from lib.generation import context_precision, context_recall, exact_share
from lib.metrics import precision_at_k
from lib.recorded import rag_answers
from lib.store import qrels

judgments = qrels("test")
answers = rag_answers().query("context != 'random'")             # the two retrievers' contexts for each test query
rows = pd.DataFrame([{"recall@5": context_recall(a.context_ids, judgments[a.query_id]),
                      "precision@5": precision_at_k(a.context_ids, judgments[a.query_id], 5),
                      "context precision@5": context_precision(a.context_ids, judgments[a.query_id]),
                      "exact share": exact_share(a.cited, judgments[a.query_id])} for a in answers.itertuples()])
print("contexts:", len(rows))

ranks, spearman = rows.rank(), {}                                # Spearman: Pearson's correlation of the ranks
for measure in ["recall@5", "precision@5", "context precision@5"]:
    spearman[measure] = ranks[measure].corr(ranks["exact share"])
    print(f"spearman with the exact share, {measure}: {spearman[measure]:.3f}")
matches = all(round(value, 9) == round(stats.spearmanr(rows[measure], rows["exact share"]).statistic, 9)
              for measure, value in spearman.items())
print("matches scipy's spearmanr:", "yes" if matches else "no")
print("weakest with the exact share:", min(spearman, key=spearman.get))
```

Output:

```text
contexts: 60
spearman with the exact share, recall@5: 0.540
spearman with the exact share, precision@5: 0.797
spearman with the exact share, context precision@5: 0.808
matches scipy's spearmanr: yes
weakest with the exact share: recall@5
```

The hand-built Spearman matches SciPy's (yes). With the exact share, recall@5 correlates at 0.540, precision@5 at 0.797 and context precision at 0.808. The weakest is recall@5, and its denominator shows why. The test queries have 4 to 170 exact products judged, so for the query with the most, a context of five exact products scores 0.029. The answer needs only three to recommend, whatever the number judged. Precision@5 counts how many of the five fit, and context precision also rewards putting them first.

Read these correlations as a description of one recording, not a test. Both sides use the same judgments, and an answer can cite only what its context holds, so some correlation is built in. The contexts also come in pairs, semantic and BM25, from the same queries.

**Working rule:** For a context of fixed size, report the context's precision@k or context precision from your judgments, with recall@k beside it. Use recall when an answer must cover every relevant item, such as every part that fits one appliance. Without judgments, Ragas's LLM-judged versions estimate similar quantities; calibrate them on a human sample before you trust them. Choose k by measuring answers on train queries at several values of k, which takes answers recorded for those queries.

## Choose the retrievable unit {#choose-the-retrievable-unit}

A **retrievable unit** is the piece of text that retrieval scores and returns, and that a [context](#measure-the-context) holds: a whole document, a passage or a sentence. A long document gets cut into **chunks**, and **chunking** is the rule that cuts it, such as a fixed number of tokens, sentences, paragraphs, or breaks chosen by meaning. Chen et al. note that "an often-overlooked design choice is the retrieval unit in which the corpus is indexed", and in their study, indexing propositions, short self-contained statements, beat indexing passages ([Chen et al., 2023](https://arxiv.org/abs/2312.06648)). Beyond that, the studies disagree. One finds that the best size depends on the questions and the embedding model: "smaller chunks (64-128 tokens) are optimal for datasets with concise, fact-based answers", while 512 to 1,024 tokens suit questions that need broader context ([Bhat et al., 2025](https://arxiv.org/abs/2505.21700)). Another finds that "the computational costs associated with semantic chunking are not justified by consistent performance gains" ([Qu et al., 2024](https://arxiv.org/abs/2410.13070)). A comparison of 36 methods ranks chunking by groups of paragraphs first, and reports that "simple fixed-size character chunking as baselines performed poorly" ([Shaukat et al., 2026](https://arxiv.org/abs/2603.06976)).

A small unit can also lose what it is about. A vendor's engineering post reports that adding chunk-specific context to each chunk before embedding it "reduced the top-20-chunk retrieval failure rate by 35%", a vendor's claim about its own method ([Anthropic, 2024](https://www.anthropic.com/news/contextual-retrieval)).

The store's products are short, partly because the book's sample cuts every description to about 400 characters ([data card](https://github.com/rollingedition/book-primer-on-search-relevance/blob/975f0c078e472eb1d3e9202a4a5feaddae27d052/examples/data/wands/README.md)). Of the descriptions, 5,933 end in that cut, and 1,568 products have none. Non-empty descriptions run to a median of 68 words, and the whole text that search reads runs to at most 140 words per product. The store's full product pages would be longer. Even so, each product is a short text about one thing, so cutting it into chunks isn't the store's question. Its question is which part of each product to index. A sentence from a description shows the risk: the last sentence of the chandelier's description from [the support check](#check-citation-support) reads `the antler 's durability and beauty will last a lifetime .`, which never says what the product is.

The recorded embeddings cover each product's whole text, so the example tries other units with BM25 only. Choosing a unit is tuning, so it uses the 50 train queries. It indexes five units: the whole product (the text `lib.lexical` indexes), the name alone, the description alone, each of the 35,061 description sentences on its own, and each sentence with the product's name, class and category in front, a simple form of adding context to each chunk. The last sentence of a cut description is a fragment. The sentences with the other fields keep every field the whole product has. A product with no description gets one unit of those fields, the same as its whole text, so the two units differ only in cutting the description. `UnitSearch` in `lib.generation` ranks each product by its best-scoring unit, so the run still lists products. The example reports the precision@5 and recall@5 that a five-product context would have, with judged@5, the share of the top 5 with a judgment. `UnitSearch` orders equal scores by `product_id`, so the example also reverses that rule and counts the train queries whose top 5 changes:

Example `retrievable-unit-on-train` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.generation import UnitSearch, sentences
from lib.metrics import judged_at_k, precision_at_k, recall_at_k
from lib.store import load_products, load_queries, product_text, qrels

products = load_products()
lengths = products["description"].str.split().str.len()
print(f"products with no description: {(lengths == 0).sum():,}")
print(f"descriptions the sample cut short: {products['description'].str.endswith(' ...').sum():,}")
print(f"description words, median of the others: {lengths[lengths > 0].median():.0f}")
print(f"product text words per product, most: {product_text(products).str.split().str.len().max()}")

header = products["name"] + ". " + products["product_class"] + ". " + products["category"] + ". "   # the other fields
pieces = [(p, piece) for p, text in products["description"].items() for piece in sentences(text) or [""]]
print(f"description sentences: {sum(piece != '' for _, piece in pieces):,}")
print("last sentence of product 8171:", sentences(products.at[8171, "description"])[-1])
units = {                                              # unit name: (texts to index, the product each belongs to)
    "whole product": (product_text(products), products.index),
    "name only": (products["name"], products.index),
    "description only": (products["description"], products.index),
    "sentences": ([piece for _, piece in pieces], [p for p, _ in pieces]),
    "sentences with the other fields": ([header[p] + piece for p, piece in pieces], [p for p, _ in pieces]),
}
train, judgments = load_queries("train"), qrels("train")      # choosing a unit is tuning: train queries only
scores = {}
for name, (texts, owners) in units.items():
    run = UnitSearch(list(texts), list(owners)).run(train, k=5)                    # equal scores by product_id
    for metric in [precision_at_k, recall_at_k, judged_at_k]:
        scores[name, metric] = np.mean([metric(run[q], judgments[q], 5) for q in train.index])
        print(f"{name}, train {metric.__name__.replace('_at_k', '')}@5: {scores[name, metric]:.3f}")
    flipped = UnitSearch(list(texts), [-p for p in owners]).run(train, k=5)        # negated owners: ties go to the highest ID
    changed = sum(set(run[q]) != {-p for p in flipped[q]} for q in train.index)
    print(f"{name}, train queries whose top 5 changes with ties reversed: {changed}")
print("highest train precision@5:", max(units, key=lambda name: scores[name, precision_at_k]))
for metric in [precision_at_k, recall_at_k]:
    gap = scores["whole product", metric] - scores["sentences with the other fields", metric]
    print(f"whole product minus sentences with the other fields, train {metric.__name__.replace('_at_k', '')}@5: {gap:.3f}")
```

Output:

```text
products with no description: 1,568
descriptions the sample cut short: 5,933
description words, median of the others: 68
product text words per product, most: 140
description sentences: 35,061
last sentence of product 8171: the antler 's durability and beauty will last a lifetime .
whole product, train precision@5: 0.464
whole product, train recall@5: 0.124
whole product, train judged@5: 0.940
whole product, train queries whose top 5 changes with ties reversed: 4
name only, train precision@5: 0.368
name only, train recall@5: 0.091
name only, train judged@5: 0.960
name only, train queries whose top 5 changes with ties reversed: 28
description only, train precision@5: 0.304
description only, train recall@5: 0.049
description only, train judged@5: 0.828
description only, train queries whose top 5 changes with ties reversed: 4
sentences, train precision@5: 0.272
sentences, train recall@5: 0.034
sentences, train judged@5: 0.732
sentences, train queries whose top 5 changes with ties reversed: 18
sentences with the other fields, train precision@5: 0.428
sentences with the other fields, train recall@5: 0.106
sentences with the other fields, train judged@5: 0.944
sentences with the other fields, train queries whose top 5 changes with ties reversed: 8
highest train precision@5: whole product
whole product minus sentences with the other fields, train precision@5: 0.036
whole product minus sentences with the other fields, train recall@5: 0.018
```

| Unit | precision@5 | recall@5 | judged@5 | Top 5 changes with ties reversed |
| --- | --- | --- | --- | --- |
| Whole product | 0.464 | 0.124 | 0.940 | 4 |
| Name only | 0.368 | 0.091 | 0.960 | 28 |
| Description only | 0.304 | 0.049 | 0.828 | 4 |
| Sentences | 0.272 | 0.034 | 0.732 | 18 |
| Sentences with the other fields | 0.428 | 0.106 | 0.944 | 8 |

The highest train precision@5 goes to the whole product. The fair comparison is with the sentences that carry the other fields: the same fields, the same products within reach, and judged@5 of 0.944 against 0.940. Cutting the description into sentences costs 0.036 in train precision@5 and 0.018 in recall@5. Ties decide part of those gaps: where products tie across the fifth place, the tie rule picks which reach the context, and reversing it changes the top 5 for 8 train queries with the sentences with the other fields and 4 with the whole product. Read a gap of a few hundredths here as rough. The other units also drop fields. The description alone can never return the products that have no description, and bare sentences surface many products nobody judged, so their precision is partly a guess. These are train numbers and untested: they inform a choice and prove nothing.

**Working rule:** When your items are short, index each whole item as one unit, as the store does. When they are long, chunk them, put the item's title in front of every chunk, and choose the chunk size on train queries by the context measures of [the previous section](#measure-the-context). Pass the LLM the whole item, or the chunk with its title, so it knows what it is reading. Before you trust a small gap, count the queries whose top k changes when ties break the other way.

## Read an agent's searches from its trace {#read-agent-searches}

Unlike the [recorded answers](#retrieval-bounds-the-answer), an agent searches for itself: it is an LLM that runs in a loop and acts. A **tool** is a function the program offers the model, described by a name, a description and its parameters. A **tool call** is the model's request to run a tool with arguments. The program runs it, sends back the result, and the model decides what to do next. That is the **agent loop**, and in Ollama, which ran the store's model, "An agent loop allows the model to decide when to invoke tools and incorporate their results into its replies" ([Ollama documentation](https://docs.ollama.com/capabilities/tool-calling)). `recordings/agent_trace.py` is such a loop. ReAct agents "generate both reasoning traces and task-specific actions in an interleaved manner", and on question answering (HotpotQA) and fact verification (Fever), with a Wikipedia API as the tool, ReAct "overcomes issues of hallucination and error propagation prevalent in chain-of-thought reasoning" ([Yao et al., 2023](https://arxiv.org/abs/2210.03629)). The **trace** is the record of every call and its result.

An agent's searches are queries, and they need not look like a shopper's. In a log of 14 million agent search requests, "over 90% of multi-turn sessions contain at most ten steps", and "On average, 54% of newly introduced query terms appear in the accumulated evidence context" ([Ning et al., 2026](https://arxiv.org/abs/2601.17617)): the agent picks up words from what it has read.

In the store, the agent's recording gave it each test query as the shopper's request, and one tool, `search`, described as "Search the store's catalog. Returns the top 5 products: ID, name, class and attributes." It may search up to 3 times, with any wording, then reply with three product IDs. The tool returns no description. The recording ran twice, with the same model and prompt: once with BM25 behind the tool, and once with semantic retrieval, which embedded the agent's search text with the same embedding model as the products. As with [the answers' contexts](#retrieval-bounds-the-answer), the traces store each BM25 search's results in bm25s's own tie order, so 7 of the 32 searches get results that differ from what `lib.lexical` returns, 6 only in order. The example reads the traces:

Example `agent-searches-in-traces` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.recorded import agent_traces, manifest, rag_answers
from lib.store import load_products, load_queries

recording, queries = manifest("agent-trace"), load_queries("test")
print("tool description:", recording["prompts"]["tool"]["function"]["description"])
print("searches allowed:", recording["max_searches"])
traces = {(t["retriever"], t["query_id"]): t for t in agent_traces()}
print("traces:", len(traces))
first = {key: t["searches"][0]["query"] for key, t in traces.items()}
print("first searches the same under both tools:", sum(first[("bm25", q)] == first[("semantic", q)] for q in queries.index))
print("first searches that keep the query as typed:", sum(first[("bm25", q)] == queries.at[q, "query"] for q in queries.index))
for q in queries.index:
    if first[("bm25", q)] != queries.at[q, "query"]:
        print(f"first search for {queries.at[q, 'query']}: {first[('bm25', q)]}")
context = {(a.context, a.query_id): a.context_ids for a in rag_answers().itertuples()}
print("traces whose first search returns the answer recording's context:",
      sum(t["searches"][0]["results"] == context[key] for key, t in traces.items()))
for tool in ["bm25", "semantic"]:
    mine = [t for (retriever, _), t in traces.items() if retriever == tool]
    print(f"{tool}, searches: {sum(len(t['searches']) for t in mine)}")
    print(f"{tool}, traces with one search: {sum(len(t['searches']) == 1 for t in mine)}")

lexical, shown = LexicalSearch(load_products()), recording["results_shown"]
stored = [s for (tool, _), t in traces.items() if tool == "bm25" for s in t["searches"]]   # what the agent saw
rerun = [lexical.search(s["query"], shown).index.tolist() for s in stored]                  # ties by product_id
differ = [(s["results"], r) for s, r in zip(stored, rerun) if s["results"] != r]
print("bm25 searches whose results differ from lib.lexical:", len(differ))
print("bm25 searches whose results differ from lib.lexical only in order:", sum(set(a) == set(b) for a, b in differ))
```

Output:

```text
tool description: Search the store's catalog. Returns the top 5 products: ID, name, class and attributes.
searches allowed: 3
traces: 60
first searches the same under both tools: 30
first searches that keep the query as typed: 26
first search for 48" sliding single track , barn door for laundry: 48" sliding single track barn door laundry
first search for counter top one cup hot water dispenser: counter top hot water dispenser one cup
first search for refrigerator with ice an water in door: refrigerator with ice and water in door
first search for tye dye duvet cover: tie dye duvet cover
traces whose first search returns the answer recording's context: 55
bm25, searches: 32
bm25, traces with one search: 29
semantic, searches: 35
semantic, traces with one search: 27
bm25 searches whose results differ from lib.lexical: 7
bm25 searches whose results differ from lib.lexical only in order: 6
```

The first search is the same under both tools for 30 queries, as expected: the agent writes it before the tool has returned anything, from the same prompt and tool description, at temperature 0. It keeps the query as typed for 26. Of the others, one fixes a misspelling, `tye dye duvet cover` becoming `tie dye duvet cover`, and one the real-word error that [chapter 8's corrector](#correct-spelling-from-catalog) misses, in `refrigerator with ice and water in door`. Both `an` and `and` are stop words for BM25 ([chapter 5](#split-text-into-terms)), so only semantic retrieval sees that change. The other two become `48" sliding single track barn door laundry` and `counter top hot water dispenser one cup`. In 55 of the 60 traces, the first search returns exactly the five products that the [answer recording](#retrieval-bounds-the-answer) put in its context.

The agent rarely looks again. With BM25 it makes 32 searches in all, and 29 traces stop after one. With semantic retrieval it makes 35, and 27 stop after one. Where do the words of a later search come from? The second example compares each later search with the words already searched, and with the names, classes and attributes the tool had shown:

Example `agent-later-searches` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.generation import shown, words
from lib.recorded import agent_traces
from lib.store import load_products, load_queries

products, queries = load_products(), load_queries("test")
for tool in ["bm25", "semantic"]:
    later = new = from_results = 0
    for trace in (t for t in agent_traces() if t["retriever"] == tool):
        asked, seen = words(queries.at[trace["query_id"], "query"]), set()
        for number, search in enumerate(trace["searches"]):
            if number > 0:                                    # a later search: the words it adds, and where from
                added = words(search["query"]) - asked
                later, new, from_results = later + 1, new + len(added), from_results + len(added & seen)
            asked |= words(search["query"])
            seen |= words(shown(search["results"], products))   # name, class and attributes, as the tool showed them
    print(f"{tool}, later searches: {later}")
    print(f"{tool}, words that later searches add: {new}")
    print(f"{tool}, of those, words the tool had shown: {from_results}")
```

Output:

```text
bm25, later searches: 2
bm25, words that later searches add: 2
bm25, of those, words the tool had shown: 1
semantic, later searches: 5
semantic, words that later searches add: 4
semantic, of those, words the tool had shown: 4
```

Under BM25, 2 later searches add 2 words, 1 of them shown by the tool before. Under semantic retrieval, 5 later searches add 4, 4 of them shown before. Counts this small describe these traces; they are not a rate to compare with Ning et al.'s.

**Working rule:** Read the traces before you score an agent. Count its searches per task, compare each search with the shopper's words, and find where added words come from. Add the agent's searches to the queries you test your retriever on, scored with the judgments for the shopper's request or judged afresh, because a retriever tuned on people's queries hasn't been tested on an agent's. Expect an agent that mostly passes the shopper's words through to be bounded by the same retrieval as a RAG answer.

## Compare the retrievers behind the agent's tool {#retriever-behind-agent-tool}

An agent that can search again might seem to make the retriever matter less. One benchmark measured otherwise. BrowseComp-Plus fixes the collection that agents search, so that retrievers can be swapped inside one agent. With BM25, "the GPT-5 achieves 55.9%", and "Integrating the GPT-5 with the Qwen3-Embedding-8B retriever further enhances its accuracy to 70.1%", with fewer search calls on average, 21.74 against 23.23 ([Chen et al., 2025, Table 1](https://arxiv.org/abs/2508.06600)). Shopping is a classic task for agents. WebShop holds "1.18 million real-world products", and its authors' best model, in 2022, "achieves a task success rate of 29%", against 59% for human experts ([Yao et al., 2022](https://arxiv.org/abs/2207.01206)). On WebMall, four simulated shops, its authors report "best-performing agents achieving task completion rates below 65%" on searches for the cheapest product and for vaguely described ones ([Peeters et al., 2025](https://arxiv.org/abs/2508.13024)).

An agent told to pick from its search results should pick only what they return, and its trace shows whether it did. Its picks are then bounded by retrieval, as a RAG answer is.

The store's [recorded agent](#read-agent-searches) searches the catalog up to 3 times with one tool, then picks three products. The second of the chapter's [two planned comparisons](#retrieval-for-llm-applications), established if its permutation p-value is below 0.025, scores those picks under each tool by [precision@3](#count-relevant-in-top-k): exact picks divided by 3, so a missing pick counts as a miss. The example counts, for each tool, the traces with fewer than three picks, picks the tool never returned, picks nobody judged, traces whose searches never returned an exact product, and traces that saw an exact product and picked none. As an exploratory check, it compares the picks with the tool's own top 3 for the first search:

Example `agent-picks-by-tool` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import pandas as pd

from lib.generation import EXACT, report_planned
from lib.metrics import precision_at_k
from lib.recorded import agent_traces
from lib.significance import compare
from lib.store import qrels

judgments, picks, top_three, below = qrels("test"), {}, {}, 0
for tool in ["bm25", "semantic"]:
    traces = [t for t in agent_traces() if t["retriever"] == tool]
    returned = [{p for search in t["searches"] for p in search["results"]} for t in traces]
    seen = [sum(judgments[t["query_id"]].get(p, 0) == EXACT for p in r) for t, r in zip(traces, returned)]
    picked = [sum(judgments[t["query_id"]].get(p, 0) == EXACT for p in t["picked"]) for t in traces]
    print(f"{tool}, picks the tool never returned: {sum(len(set(t['picked']) - r) for t, r in zip(traces, returned))}")
    print(f"{tool}, picks nobody judged: {sum(p not in judgments[t['query_id']] for t in traces for p in t['picked'])}")
    print(f"{tool}, traces with fewer than three picks: {sum(len(t['picked']) < 3 for t in traces)}")
    print(f"{tool}, traces whose searches returned no exact product: {sum(s == 0 for s in seen)}")
    print(f"{tool}, traces that saw an exact product and picked none: {sum(s > 0 and k == 0 for s, k in zip(seen, picked))}")
    picks[tool] = pd.Series({t["query_id"]: precision_at_k(t["picked"], judgments[t["query_id"]], 3) for t in traces})
    top_three[tool] = pd.Series({t["query_id"]: precision_at_k(t["searches"][0]["results"], judgments[t["query_id"]], 3)
                                 for t in traces})               # the tool's own top 3 for the first search
    print(f"{tool}, precision@3 of the picks: {picks[tool].mean():.3f}")
    print(f"{tool}, precision@3 of the first search's top 3: {top_three[tool].mean():.3f}")
    p_value = compare(picks[tool], top_three[tool])["permutation p"]
    print(f"{tool}, picks against the top 3, exploratory permutation p: {p_value:.3f}")
    below += p_value < 0.05

print(f"picks against the top 3, p-values below 0.05 uncorrected: {below} of 2")
report_planned("agent picks, semantic over bm25", picks["semantic"], picks["bm25"])
```

Output:

```text
bm25, picks the tool never returned: 0
bm25, picks nobody judged: 3
bm25, traces with fewer than three picks: 2
bm25, traces whose searches returned no exact product: 5
bm25, traces that saw an exact product and picked none: 6
bm25, precision@3 of the picks: 0.567
bm25, precision@3 of the first search's top 3: 0.500
bm25, picks against the top 3, exploratory permutation p: 0.152
semantic, picks the tool never returned: 0
semantic, picks nobody judged: 0
semantic, traces with fewer than three picks: 0
semantic, traces whose searches returned no exact product: 5
semantic, traces that saw an exact product and picked none: 2
semantic, precision@3 of the picks: 0.622
semantic, precision@3 of the first search's top 3: 0.633
semantic, picks against the top 3, exploratory permutation p: 1.000
picks against the top 3, p-values below 0.05 uncorrected: 0 of 2
agent picks, semantic over bm25, mean difference: 0.056
agent picks, semantic over bm25, wins, losses, ties: 5, 4, 21
agent picks, semantic over bm25, permutation p: 0.422
agent picks, semantic over bm25, established at 0.025: no
agent picks, semantic over bm25, t-test p: 0.305
agent picks, semantic over bm25, t-test agrees: yes
agent picks, semantic over bm25, 97.5% interval: -0.033 to 0.209
agent picks, semantic over bm25, interval agrees: yes
```

Picks the tool never returned number 0 under BM25 and 0 under semantic retrieval, so the bound holds. In 5 traces under BM25 and 5 under semantic retrieval, no search returned an exact product, and no pick could be exact. The agent saw an exact product and picked none in 6 traces under BM25 and 2 under semantic retrieval. Under BM25, 3 picks are unjudged and count as misses, against 0 under semantic retrieval. Traces with fewer than three picks number 2 under BM25 and 0 under semantic retrieval, and their missing picks count as misses too.

The picks score a precision@3 of 0.622 with semantic retrieval and 0.567 with BM25. With this model, prompt and these test queries, the two tools show no established difference in the picks, with a permutation p-value of 0.422 ([both comparisons](#retrieval-for-llm-applications-decisions)). That isn't evidence that the retriever doesn't matter, only that these queries don't show a difference.

The exploratory check reads the same way. The tool's own top 3 for the first search scores 0.500 under BM25 and 0.633 under semantic retrieval, and the permutation p-values for picks against that top 3 are 0.152 and 1.000: 0 of 2 fall below an uncorrected 0.05. We chose the check after seeing test results, so it is never established.

**Working rule:** Test the retriever behind an agent's tool as you test it for people, on the agent's own searches and on its final picks, scored with human judgments. Check that every pick came from a tool result. Count the tasks where the tool never returned a relevant product, because no agent can fix those and only retrieval can.

## What goes wrong in production {#retrieval-for-llm-applications-in-production}

A live assistant answers every shopper with a fresh model call, on a context that retrieval builds for that request.

**The model, the prompt and the context are one system.** A different model version, a reworded prompt, another context size or a different order of products can change every answer. The store's manifests pin the model's digest, the prompts, the answer and tool schemas and the context window. Change any of them and score the answers again, against the same judgments and [the random floor](#retrieval-bounds-the-answer). Keep the raw replies and each context, as the recordings do.

**The citation check belongs on the answer's path.** [The ID check](#check-citations-against-context) is cheap, so run it on every answer before the shopper sees it, and log each failure with the answer and its context.

**Abstentions move with retrieval.** Track the share of answers that recommend nothing. On the store's random contexts, 29 of the 30 answers recommend nothing, so a rise in that share can mean that retrieval or the catalog changed. Read those answers before you assume the model did.

**Product text reaches the prompt.** Product descriptions may come from outside your team, and the LLM reads them as part of its input. [Chapter 4](#judgments-from-people-and-llms-in-production) cites a study in which words and instructions planted in a text misled LLM judges. Test the assistant on products whose text contains instructions before you trust it with a catalog you don't write.

**Longer contexts change the answer.** Raising k lengthens the context and brings in more distractors, and both can hurt ([Liu et al., 2024](https://aclanthology.org/2024.tacl-1.9/); [Jin et al., 2024](https://arxiv.org/abs/2410.05983)). Measure answers at each setting on train queries.

**Agent traffic is a different workload.** In the logs [Ning et al.](#read-agent-searches) studied, agents send many machine-written queries per task, while the store's agent mostly sent one. One study warns that with agent traffic, "caching may lose effectiveness, query pre-processing may add overhead without improving results" ([Pezzuti et al., 2026](https://arxiv.org/abs/2602.17518)). Log agents' searches apart from people's, and test the retriever on both.

**Working rule:** Version the model, prompt and context settings with the answers, check citations on every answer, track abstentions, and keep agents' searches in a test set of their own.

## Decisions this chapter made {#retrieval-for-llm-applications-decisions}

Only an established planned comparison on the test queries could change the store's retriever.

- **The context: five whole products from semantic retrieval,** the [ranker to beat](#compare-runs-in-a-harness). Five is the recording's fixed, untested setting. The answers show no established difference between semantic retrieval and BM25, so the retriever rests on chapter 3's established lead in nDCG@10.
- **Answers scored on human grades:** the exact share of what each answer cites, with the answers that recommend nothing counted beside it and a random context as a floor.
- **Citations checked by ID on every answer.** The recording passes the check, and it stays. Support checks, by NLI model or LLM judge, count only when calibrated on a human sample.
- **The context measured by precision@5 and context precision from the judgments,** with recall@5 beside them, because the recall@5 of a five-product context can't reach 1 when a query has more than five exact products.
- **The retrievable unit: the whole product.** It has the highest train precision@5, and cutting descriptions into sentences, even with the other fields in front, costs 0.036.
- **The agent's tool: the same retrievers, tested on the agent's searches and picks.** The picks show no established difference between the tools, and every pick came from what the tool returned.
- **Scope: one model, two prompts, the test queries.** Every finding about the LLM is about `gemma4:12b-it-q4_K_M` with the recorded prompts. A different model or prompt is a change to score again, as a change of retriever is.

The chapter's 2 planned comparisons, semantic retrieval minus BM25 on the test queries, established below 0.025:

| Measure | [Answers](#retrieval-bounds-the-answer), mean exact share | [Agent picks](#retriever-behind-agent-tool), precision@3 |
| --- | --- | --- |
| Semantic | 0.658 | 0.622 |
| BM25 | 0.639 | 0.567 |
| Mean difference | 0.019 | 0.056 |
| Wins / losses / ties | 4, 5, 21 | 5, 4, 21 |
| Permutation p | 0.765 | 0.422 |
| Established | no | no |
| t-test p | 0.715 | 0.305 |
| 97.5% interval | -0.078 to 0.161 | -0.033 to 0.209 |
| t-test agrees | yes | yes |
| Interval agrees | yes | yes |
