---
title: "A Primer on Search Relevance"
chapter: "Understanding queries"
chapter_id: understanding-queries
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/understanding-queries
license: CC BY 4.0
attribution: "“Understanding queries,” chapter 8 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/understanding-queries. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Understanding queries

By the end of this chapter you can change a shopper's query before retrieval: correct its spelling, write its units one way, expand it with synonyms, predict its product class, rewrite it with a large language model, search with a product that model imagines, and turn a follow-up into a standalone query. You can also decide, from human judgments, whether each change helps the retriever it feeds.

The store whose search this book follows, an online seller of furniture and home goods ([chapter 1](#store-data)), gets short queries, and some of them can't match the products the shopper wants. `ligth bulb` misspells a word. `7qt slow cooker` writes its size as a term that 0 products contain. For `midcentury tv unit`, [chapter 7 counts](#learned-sparse-splade) 25 [exact](#store-data) products, of which 0 contain `midcentury` and 0 contain `unit`. A shopper who types `in white` after a search for a desk means a white desk, but the words alone don't say so. **Query understanding** is everything a search system does to a query before retrieval to close gaps like these: it corrects, normalizes, expands, classifies and rewrites. Chapters 5 to 7 changed the retrievers. This chapter changes the query and keeps the retrievers fixed: [BM25](#rank-with-bm25), the book's unstemmed baseline in `lib.lexical`, and [semantic retrieval](#search-by-meaning), which compares the query's embedding with each product's, both computed in advance by `Snowflake/snowflake-arctic-embed-m-v1.5`.

Three of the techniques use a **large language model** (LLM), a model trained on large amounts of text to generate text in response to a prompt. The store's LLM is `gemma4:12b-it-q4_K_M`, an open model that Google publishes under the Apache 2.0 licence ([model card](https://ai.google.dev/gemma/docs/core/model_card_4)). The examples never call it. Two scripts, `recordings/llm_rewrites.py` and `recordings/llm_conversations.py`, ran it once, at temperature 0 with a fixed seed, and saved its outputs as **recordings**, which the examples read through `lib.recorded`. Each recording's `manifest.json` holds the full prompts. We chose the model because anyone can download it and run it on their own machine, so anyone can rerun the recordings. The LLM sees only the shopper's words, never a product. Every score in the chapter uses the human judgments.

Every setting is chosen on the 50 [train queries](#store-data), and the 30 test queries are kept for reporting. Before reading any test result, the chapter fixes 5 planned comparisons on the test queries, each against the same retriever on the query as typed:

1. BM25 with a [synonym list](#expand-with-synonyms)
2. semantic retrieval with a [boost for the predicted class](#boost-predicted-class)
3. BM25 on the [LLM's rewrite](#rewrite-queries-with-llm)
4. semantic retrieval on the LLM's rewrite
5. semantic retrieval with [HyDE](#hyde-hypothetical-products), which averages the query's embedding with that of a product the LLM imagines

By [the book's rule](#when-a-difference-is-established), a difference is established when its paired [permutation test](#permutation-test-on-queries) gives a p-value below 0.01, 0.05 divided by the number of planned comparisons. The [paired t-test](#paired-t-test-on-queries) and a 99% [bootstrap interval](#report-the-size-of-a-gap) stand beside it. Spelling correction, unit normalization and follow-up rewriting each touch too few queries to test, so their sections are diagnoses, not tests.

## Correct spelling against the catalog's words {#correct-spelling-from-catalog}

The first gap is a typo, as in `ligth bulb`. In [BM25](#rank-with-bm25), a misspelled word matches only products with the same misspelling, and it can move the query's embedding away from the products it means, as [chapter 6 shows](#semantic-retrieval-in-production). Search queries hold many such errors: one study of web search reports that "Roughly 10-15% of the queries sent to search engines contain errors" ([Cucerzan and Brill, 2004](https://aclanthology.org/W04-3238/)). The classic corrector is the **noisy channel** model: for a typed word t, choose the correction c that maximizes P(c) × P(t | c) ([Kernighan et al., 1990](https://aclanthology.org/C90-2036/)). P(c) says how common the candidate word is. P(t | c), the error model, says how likely a shopper who meant c is to type t. Kernighan et al. take as candidates the words one edit from the typo: a deletion, an insertion, a replacement or a swap of two neighbouring letters. The number of insertions, deletions and replacements that turn one string into another is their **edit distance** ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/edit-distance-1.html)), and the corrector here also counts a swap as one edit. A textbook states the two principles in plain terms: of the correct spellings, choose the nearest, and between near ties, choose the more common ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/implementing-spelling-correction-1.html)). Norvig writes such a corrector in a few lines ([Norvig](https://norvig.com/spell-correct.html)).

```text
correction(t) = argmax over candidates c of  P(c) × P(t | c)
```

The **lexicon**, the list of words that count as correct, decides what gets corrected. Web search engines take it from their query logs, choosing "the correction that is most common among queries typed in by other users" (Manning et al.). The store has no log, so its lexicon comes from the catalog's text. Where the lexicon comes from matters for brand names: in product search, a corrector "must distinguish genuine misspellings from novel brand names that use unconventional spelling" ([Guo et al., 2024](https://arxiv.org/abs/2410.11655)).

In the store, build the corrector with the crudest error model: a word in the lexicon stays, one edit beats two, and P(c), how common each candidate is, breaks ties between candidates the same number of edits away. Run it on all 80 queries:

*Example `catalog-spelling-corrector`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/correct-spelling-from-catalog*

The catalog uses 19,680 distinct words. The corrector changes 4 queries, and the shared function `lib.queries.correct_query` makes the same corrections. Of those, 3 are [train queries](#store-data), and the corrector spells each one as [chapter 6's spelling probes](#semantic-retrieval-in-production) do: the correctly spelled copies of the typo queries that chapter 6 wrote for the book. The corrector leaves the brands alone, because the catalog uses them: `kohler` 71 times and `whitehaven` 60. Some of the words it keeps are rare, such as `malachi`, used 5 times, and `luau`, used 4. A lexicon that left out rare words would treat both as typos.

The corrector's failures are in test queries. `tye dye duvet cover` becomes `the dye duvet cover`: `tye` is one edit from `tie` (45 times in the catalog) and from `the` (20389), and P(c) picks the common word. And `refrigerator with ice an water in door` keeps its `an`. That is a **real-word error**: every word is spelled right, as in "flew form Heathrow" ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/context-sensitive-spelling-correction-1.html)). Both need context. For `tye` and for `an`, count how often each catalog word within one edit of it comes right before the next word of the query, `dye` or `water`:

*Example `spelling-context-counts`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/correct-spelling-from-catalog*

Before `dye`, the catalog's text has `tie` 18 times, and the corrector's choice, `the`, 0. Before `water`, it has `and` 59 times, ahead of `a` at 20, and `an` 0. For these two queries, a corrector that scored each candidate with its neighbouring word would pick `tie` and `and`. Now measure each corrected query on its own judgments:

*Example `measure-spelling-corrections`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/correct-spelling-from-catalog*

For the train query `foutains with brick look`, BM25's nDCG@10 goes from 0.356 to 0.507 and semantic retrieval from 0.353 to 0.645. For `twin over full bunk beds cool desins`, only semantic retrieval moves, from 0.565 to 0.616, and for `ligth bulb` neither does. For `refrigerator with ice an water in door`, the corrector changes nothing, and a correct fix couldn't help BM25 either. Of the typed `an` and the correct `and`, bm25s drops `an, and` as stop words, and chapter 6's copy of the query spelled with `and` scores 0.501, the same as the query as typed. For `tye dye duvet cover`, BM25 scores 0.953 either way, because `the` is a stop word and `tye` matches no product, so both versions search the same terms. Semantic retrieval can't be scored on the corrected text, because the recordings hold no embedding of it. The store has 4 typo queries, 1 of them a test query, and the smallest two-sided permutation p-value that so few could give is 0.125.

**Working rule:** Build the lexicon from your catalog, and from your query log once you have one, and correct only words it doesn't hold, so that brand names survive. Before you correct a word, check its neighbours: a corrector without context turns variant spellings into common words and misses real-word errors. Score each correction on the typo queries' own judgments, and collect many more typo queries than the store has before you test a corrector.

## Normalize units the way the catalog writes them {#normalize-units}

A typo has one right spelling; a size, as in `7qt slow cooker`, often has several. **Normalization** maps the different ways of writing one thing to a single form, on the products and on the query alike. In the store, sizes need it. [Chapter 5](#split-text-into-terms) found that `7qt` and `7 qt` never match each other, because the tokenizer drops the one-character `7`. A normalizer that joins each number to its unit, written one way, turns both into one term, `7qt`. It has to run on the product text when you build the index, and on every query. It also has to produce terms the tokenizer keeps whole. The tokenizer splits words at a decimal point, so `3.7qt` would become `7qt`. To prevent that, the shared function `lib.queries.normalize_units` writes the point as an underscore, which the tokenizer keeps inside a word. It also leaves `in` alone when a number or `one` follows, as in `3 in 1`.

In the store, a rule written from the queries would cover `qt`, `in`, `inch` and `"`. Before you trust it, count how the catalog writes inches. The example counts them, prints the terms that the tokenizer makes of a few normalized texts, then builds BM25 three times: over the text as written, normalized by that first rule, and normalized by `normalize_units`, which also handles the catalog's two apostrophes, `''`, for inches. It scores every query, train or test, that gives a number with a unit:

*Example `normalize-units-both-sides`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/normalize-units*

The catalog writes a number followed by two apostrophes in 3014 products, by `"` in 65 and by `inch` in 215. The tokenizer reads `3.7-quart slow cooker`, normalized, as `3_7qt slow cooker`, and `3 in 1 sofa bed` as `sofa bed`. `normalize_units` still misreads `1 in twin` as `1in twin`, which is why the terms are worth printing.

For the train query `7qt slow cooker`, normalizing takes BM25's nDCG@10 from 0.554 to 0.930, and the first rule gives 0.930. The test query `48 inch kitchen hood` shows what the first rule loses by missing the two apostrophes: it scores 1.000 as written and 0.824 under the first rule. The query becomes `48in`, while the first rule leaves a hood written `48 ''` as `48 range hood`, and the full rule makes it `48in range hood`. With the full rule, the hood query scores 1.000. The other train query, `48 in entry table with side by side drawer`, scores 0.569 as written and 0.569 normalized, and the test query about a barn door 0.592 and 0.592. That makes 4 queries with a unit, 2 of them [test queries](#store-data): too few for a test, so this is a diagnosis.

**Working rule:** Write normalization rules from the catalog's text, not from the queries, by counting every way it writes each unit. Print the terms the tokenizer makes of the normalized text, because a rule that looks right can produce terms that match the wrong products. Apply the same rules to products and queries in one release, and rebuild the index. When the catalog keeps sizes in fields, such as the width in `attributes`, match the size against the field instead, as [chapter 6 suggests](#codes-carry-no-weight).

## Expand queries with a synonym list {#expand-with-synonyms}

Some gaps are neither typos nor units but different words for one thing, as when the exact products for `midcentury tv unit` say `stand`. **Query expansion** adds terms to a query so that it can match products that use other words for the same thing. "Use of query expansion generally increases recall" ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/query-expansion-1.html)), the share of the relevant products that a search finds. It can cost precision, the share of found products that are relevant: "query expansion may also significantly decrease precision, particularly when the query contains ambiguous terms" ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/automatic-thesaurus-generation-1.html)). An added word can match products the shopper didn't ask for, and move the query away from its meaning, which is called **query drift**. Expansion terms can come from a hand-built list of synonyms, or from the results. **Pseudo-relevance feedback** assumes the top results are relevant and adds their terms to the query, which makes drift its known risk ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/pseudo-relevance-feedback-1.html)).

In the store, `lib.queries.SYNONYMS` holds 14 groups of interchangeable words, such as `stand` and `unit`, written by reading the train queries whose exact products miss a query word. When a query contains a word or phrase from a group, `expand` appends the group's other members, and BM25 searches the result. Measure it on the train queries, then make the first of the chapter's [five planned comparisons](#understanding-queries) on the test queries, which counts as established if p is below 0.01:

*Example `synonym-expansion-train-and-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/expand-with-synonyms*

The list changes 14 train queries. Mean [nDCG@10](#score-one-ranking) goes from 0.695 to 0.722, and [judged@10](#score-every-test-query), the share of the top 10 with a judgment, from 0.930 to 0.944. The numbers of changed queries that score better and worse are 6, 5, and one query carries a share of 0.473 of the net gain: `midcentury tv unit`, which gains +0.632 with `stand mid century` added. The list was written from these queries, so even these numbers flatter it. The largest loss, -0.176, shows drift: `wire basket with dividers` gets `hamper`, and 4 products whose names contain `hamper` enter its top 10. 4 of them are unjudged, so the metric counts them as irrelevant, which for hampers is a fair guess.

On the test queries, the list changes 1 query, `indoor multi tiered plant stand`, by adding `unit`. Judged@10 stays at 0.927, and the difference isn't established ([planned comparisons](#understanding-queries-decisions)). On the queries it was written from, the list helped about as many queries as it hurt, and queries it wasn't written for rarely contain its words.

**Working rule:** Keep a synonym list for vocabulary gaps you have seen, write each entry from a failing query, and read the products each entry adds before you keep it. Never report a list's gain on the queries you wrote it from, and keep an entry only if a test on held-out queries shows a gain. Test any expansion of semantic retrieval first: the LLM's rewrites, which add synonyms and also broaden and drop words, [hurt it](#rewrite-queries-with-llm). When the gaps are too many to list, try [stemming](#stem-word-forms) or [learned sparse retrieval](#learned-sparse-splade) instead.

## Train a query classifier on product text {#classify-queries-from-products}

Instead of changing a query's words, a system can predict what kind of product the query asks for. **Query classification** assigns a query to a class in the store's taxonomy, such as `Range Hoods`. In product search, "mapping a query to a pre-defined product taxonomy is an important step in e-commerce query understanding pipeline" ([Skinner and Kallumadi, 2019](https://ceur-ws.org/Vol-2410/paper37.pdf)): a predicted class can steer retrieval toward the right part of the catalog. Training a classifier usually takes labelled queries. Skinner and Kallumadi report that "an existing product-taxonomy mapping can improve query classification, and reduce the need for labeled data": they pretrain on product titles, whose classes are known, then fine-tune on fewer labelled queries.

The store goes further and uses no labelled queries, because it has none. WANDS gives each query a `query_class`, "category to which the query falls under" ([WANDS](https://github.com/wayfair/WANDS)), but [chapter 2](#intent-in-product-search) shows that it is a prediction, and some values are wrong. And the book's sample of WANDS holds at most one query per class (`examples/data/wands/README.md`), so no class has two queries to learn from. So train on the products, which carry `product_class`, and apply the classifier to the queries.

A **naive Bayes** classifier can learn classes from product text in a few lines. In words: a class is likely for a query when the class is common among products, and when the query's words are common in that class's product text. It treats words as independent, which is the "naive" part. Each count gets 1 added, so that a word never seen in a class doesn't rule the class out:

```text
predicted class = argmax over classes c of  log P(c) + sum over the query's words w of  log P(w | c)
P(w | c)        = (count of w in class c's text + 1) / (number of words in class c's text + vocabulary size)
```

In the store, build it by hand from word counts of the product text, check it against scikit-learn's `MultinomialNB` at 1.9.1, then compare its predictions with `query_class` and with the classes of each query's exact products:

*Example `query-classes-by-hand`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/classify-queries-from-products*

The products use 410 classes. 800 products have none and are left out, and 620 have several, so each of those is one training row per class. The hand-built classifier makes the same prediction as `MultinomialNB` for 80 of 80 queries. Its prediction equals `query_class` for 60, but `query_class` is a guess too. Against the judgments, the two guesses tie: for 63 queries most exact products carry the predicted class, and for 63 they carry `query_class`. Three of its predictions show how it reads a query by its words alone: `outdoor light fixtures` becomes `Light Bulbs`, `desk and chair set` becomes `Desks`, and `pool floats` becomes `Deck Boxes`.

The sample's design limits what this check can show. Each class is tested by at most one query, so no per-class accuracy can be measured, and 80 queries cover only part of the 410 classes, so the counts say nothing about the rest. A query classifier can't be trained on these queries at all, and two classifiers can only be compared on whether each gets these few queries right. And 1 query class, `Crock Pots & Slow Cookers`, names no product class at all, so no classifier trained on products can predict it.

**Working rule:** When you have no labelled queries, train a query classifier on your products' classes and check it against the classes of judged exact products, not against another classifier's guesses. Once your logs give you labelled queries, train on those. Treat the predicted class as a hint for ranking, never as a label.

## Boost the predicted class instead of filtering {#boost-predicted-class}

In the store, the predicted class comes from [the naive Bayes classifier](#classify-queries-from-products) trained on product text. A predicted class can act on retrieval in two ways. A **filter** keeps only products in the class. A **boost** adds a fixed amount to their scores, so that they move up without anything else being removed. A filter is only as good as the classifier: every relevant product outside the predicted class disappears.

The store's train judgments show how much a filter would cost: for the train queries, 501 of 1937 exact products lie outside their query's predicted class. The example adds a boost to the similarities of semantic retrieval, the store's best ranker and so its [ranker to beat](#compare-runs-in-a-harness), and tries five boost weights and a filter on the train queries. It takes the best boost to the test queries for the second of the chapter's [five planned comparisons](#understanding-queries), which counts as established if p is below 0.01:

*Example `class-boost-train-and-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/boost-predicted-class*

On the train queries, the filter takes [nDCG@10](#score-one-ranking) from 0.772 to 0.675, and [judged@10](#score-every-test-query) from 0.964 to 0.866, so its top 10s also fill with products nobody judged. The boosts score from 0.773 at 0.01 and 0.774 at 0.02 down to 0.692 at 0.2, and the output lists the rest. The best boost on train is 0.02, with judged@10 of 0.966.

On the test queries, judged@10 is 0.990 without the boost and 0.993 with it, and the boost's gain isn't established ([planned comparisons](#understanding-queries-decisions)).

**Working rule:** Don't filter on a predicted class. Boost it with a weight tuned on train queries, and keep the boost only if its planned test comparison is established. The store's isn't, so its semantic retrieval stays unboosted. We recommend a class filter only when the shopper chose the class, for example by clicking a category.

## Rewrite queries with an LLM {#rewrite-queries-with-llm}

**Query rewriting** replaces the query with a text written to retrieve better. Where the corrector, the unit rules and the synonym list each fix one kind of gap, an LLM can fix spelling, expand abbreviations and add synonyms in one step, with no list to maintain. In rewrite-retrieve-read, the rewritten query goes to the retriever in place of the original ([Ma et al., 2023](https://arxiv.org/abs/2305.14283)). Studies report gains. With query2doc, which appends an LLM-written passage, a **pseudo-document**, to the query, BM25 improved "by 3% to 15% on ad-hoc IR datasets", with text-davinci-003 writing the passages for MS MARCO and TREC DL queries ([Wang et al., 2023](https://arxiv.org/abs/2303.07678)). Other studies report failures. A comparison of 11 expansion methods, 12 datasets and 24 retrievers found that "expansion improves scores for weaker models, but generally harms stronger models" ([Weller et al., 2024](https://arxiv.org/abs/2309.08541)). Another study found that LLM-based expansion "can significantly degrade the retrieval effectiveness when knowledge in the LLM is insufficient or query ambiguity is high" ([Abe et al., 2025](https://arxiv.org/abs/2505.12694)).

The rewrites that the examples read were recorded with the store's LLM, the open model named in [the chapter's opening](#understanding-queries), run locally on each query alone. The prompt's instruction is: "Rewrite this search query from an online furniture and home-goods store so that a search engine finds what the shopper wants. Fix spelling, expand abbreviations and add common synonyms for the product type, but keep every requirement the shopper stated and add none of your own. Return a single line." The rest of the prompt gives the query and asks for JSON, and the recording's manifest holds it in full. The recording script embedded each rewrite as a query, with the same embedding model as the products. BM25 searches the rewrite's text, and semantic retrieval its embedding. Look at the train queries first:

*Example `llm-rewrites-on-train`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rewrite-queries-with-llm*

The rewrites fix spelling, `fountains with brick look, brick style water features, masonry fountains, faux brick fountains`, and keep codes, `Ines shag rug w003096809 area rug carpet`. For `malachi sled`, a product line, the LLM guessed a sofa: it wrote `Malachi sled sofa couch settee loveseat`, while the exact products are `malachi sled end table; malachi 44 '' console table; malachi sled coffee table`. On the train queries, BM25's nDCG@10 goes from 0.695 to 0.646, and semantic retrieval's from 0.772 to 0.759. [Judged@10](#score-every-test-query) falls for both, from 0.930 to 0.868 and from 0.964 to 0.924, so the rewrites surface products nobody judged, and part of each fall in nDCG@10 may come from them. The numbers of queries that score better and worse are 23, 24 for BM25 and 18, 25 for semantic retrieval. BM25's largest loss is `malachi sled`, at -0.644, and semantic retrieval's is `wall design shelf`, at -0.653.

These train numbers shape expectations and prove nothing. The third and fourth of the chapter's [five planned comparisons](#understanding-queries) were fixed in advance, so they go to the test queries whatever the train queries show, and each counts as established if p is below 0.01. Before you run them, predict: on the test queries, will the rewrite help BM25, the weaker retriever, hurt semantic retrieval, the stronger one, or neither?

*Example `llm-rewrites-on-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rewrite-queries-with-llm*

For BM25, judged@10 falls from 0.927 to 0.903, and [nDCG@10](#score-one-ranking) from 0.725 to 0.669, a difference that isn't established ([planned comparisons](#understanding-queries-decisions)).

For semantic retrieval, judged@10 falls from 0.990 to 0.947, and nDCG@10 from 0.830 to 0.749, an established loss, with a permutation p-value that rounds to 0.000.

Because judged@10 fell, the example repeats both comparisons on [condensed](#unjudged-results) lists, which drop unjudged products before scoring. That check was chosen after seeing the drop, so it is exploratory and can't establish anything. For semantic retrieval, condensed nDCG@10 goes from 0.834 to 0.791, a difference of -0.043 with a permutation p of 0.002 and a 99% interval from -0.079 to -0.014. So the loss doesn't rest on unjudged products alone. For BM25, condensed nDCG@10 goes from 0.778 to 0.725, with a permutation p of 0.044, a question for new queries rather than a finding.

If you predicted that the rewrite would help BM25, the test doesn't show it, on these queries with this LLM and prompt: BM25 moved the other way from what Weller et al. and query2doc report, though not by an established amount. If you predicted harm to semantic retrieval, you predicted what Weller et al. found for strong retrievers, here with this model, this prompt and these queries.

The queries that move most show what a rewrite does. Read them with the number of unjudged products in each rewritten top 10, which the metric counts as irrelevant:

*Example `rewrite-largest-changes`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/rewrite-queries-with-llm*

BM25's largest loss, -0.471 for `fold in half table`, comes from `folding table, collapsible table, drop leaf table, gateleg table`, which drops `in half` and adds other kinds of table; 3 of its top 10 are unjudged. Semantic retrieval's largest loss, -0.304 for `pull out sleeper loveseat`, comes from `pull out sleeper loveseat sofa couch convertible sofa sofa bed`, which widens a loveseat to any sofa; 4 of its top 10 are unjudged. BM25's largest gain, +0.159 for `refrigerator with ice an water in door`, comes from `refrigerator with ice and water in door, fridge with door dispenser, refrigerator with external water and ice dispenser`. The rewrite fixes `an`, but with only that fix BM25 scores 0.501, the same as the query as typed, 0.501, because both spellings are stop words. The gain comes from the words the rewrite adds. Semantic retrieval's largest gain is +0.055, for `nautical platters`, rewritten as `nautical platters serving trays seafood platters maritime serving boards`.

**Working rule:** Don't put an LLM rewrite in front of a strong retriever without a planned test on held-out queries. Read the per-query losses for dropped requirements and broadened products, which the prompt's "keep every requirement" doesn't prevent. For the store, semantic retrieval, the ranker to beat, keeps searching the query as typed.

## Search with a hypothetical product (HyDE) {#hyde-hypothetical-products}

Where a [rewrite](#rewrite-queries-with-llm) asks the LLM for a better query, HyDE, short for hypothetical document embeddings, asks it for the document it imagines would answer the query. An encoder embeds that **hypothetical document**, and "This vector identifies a neighborhood in the corpus embedding space" where real documents lie ([Gao et al., 2023](https://aclanthology.org/2023.acl-long.99/)). The made-up details needn't be true: the authors argue that the encoder's "dense bottleneck" filters out "the hallucinations", which is their argument, not a measurement. Their main results use InstructGPT (text-davinci-003), sampling at temperature 0.7. On TREC DL19, a passage-ranking benchmark, HyDE raised the nDCG@10 of Contriever, an embedding model trained without relevance labels, from 44.5 to 61.3 on a 0 to 100 scale (Gao et al., Table 1). With a Contriever fine-tuned on labels, the result depended on the LLM. The smaller ones lowered nDCG@10 slightly, since "less powerful instruction LMs can negatively impact the overall performance of the fine-tuned retriever", while InstructGPT raised it, most on DL19, from 62.1 to 67.4 (Table 4).

Several expansion methods keep the original query in the mix. HyDE averages the embeddings of the hypothetical documents together with the query's own (Gao et al., section 3.2). **Relevance feedback** improves a query from judgments of its first results, and Rocchio's version moves the query vector toward the results judged relevant while keeping the original vector in its sum ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/the-rocchio71-algorithm-1.html)). For BM25, query2doc repeats the query five times before the generated passage, so that the original terms keep their weight ([Wang et al., 2023](https://arxiv.org/abs/2303.07678)).

For the store, the HyDE recording holds one hypothetical product per query, which the store's LLM wrote from the query alone: a name, a class and a description, embedded as a product. The example's `hyde` function averages it with the query's embedding and scales the result back to length 1, as [chapter 6 advises after any averaging](#compare-with-cosine-similarity). The two embeddings differ in one way: the query's carries the embedding model's query prompt, and the product's has none, as for every product.

```text
hyde(query) = (embedding(hypothetical product) + embedding(query)) / 2,  then scaled to length 1
```

On the train queries, the example also tries the hypothetical product's embedding alone, and, for BM25, the hypothetical product's text alone and with the query repeated five times before it, as query2doc weights it. Then it makes the last of the chapter's [five planned comparisons](#understanding-queries), which counts as established if p is below 0.01:

*Example `hyde-train-and-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/hyde-hypothetical-products*

On the train queries, the hypothetical product alone takes semantic retrieval's nDCG@10 from 0.772 to 0.704, with [judged@10](#score-every-test-query) from 0.964 to 0.890, and the numbers of queries that score better and worse are 13, 29. Averaged with the query, it scores 0.769, with judged@10 of 0.946. BM25 behaves the same way: 0.695 on the query, 0.644 on the hypothetical text alone, and 0.694 with the query repeated five times before it, with judged@10 of 0.930, 0.854 and 0.912. Keeping the query recovers what the hypothetical product loses, and on the train queries, for either retriever, the combination adds nothing over the query alone. Train numbers guide the design; only the planned test comparison is evidence.

On the test queries, judged@10 goes from 0.990 to 0.970, and HyDE shows no established difference from semantic retrieval ([planned comparisons](#understanding-queries-decisions)). This result belongs to one hypothetical product per query, from a 12-billion-parameter model run at temperature 0. Gao et al. sampled from a far larger LLM, and only that one raised their fine-tuned retriever.

**Working rule:** When you try HyDE, always average the query's own embedding in. Expect the largest gains with an encoder trained without labels; with a fine-tuned encoder, Gao et al. saw gains only from their largest LLM, and the store, with its model, prompt and encoder, saw none. On an encoder like the store's, which [already beats BM25](#compare-runs-in-a-harness) on these queries, test HyDE before you pay for an LLM call per query. The store doesn't use it.

## Turn a follow-up into a standalone query {#standalone-follow-ups}

The last gap from [the chapter's opening](#understanding-queries) comes from conversation: a shopper's next message often depends on the last one, as `in white` refines a search for a desk. Retrieval sees one text, so the follow-up has to become a **standalone query**, one that keeps what the shopper still wants. Conversational query rewriting is the task of turning "a context-dependent into a self-contained question with the same answer", and the CANARD dataset holds 40,527 such rewrites ([Elgohary et al., 2019](https://aclanthology.org/D19-1605/)). In TREC CAsT 2019, a conversational search evaluation, people's rewrites beat the best automatic system, "a 35% relative improvement of manual rewrites over the best automatic system" ([Dalton et al., 2020](https://arxiv.org/abs/2003.13624)). Later work with prompted LLMs found that "informative query rewrites can yield substantially improved retrieval performance compared to human rewrites, especially with sparse retrievers" ([Ye et al., 2023](https://arxiv.org/abs/2310.09716)), and in TREC iKAT 2025, CAsT's successor, "Most of the runs leveraged LLMs in their pipelines, for single or multiple query rewriting" ([TREC iKAT 2025 overview](https://trec.nist.gov/pubs/trec34/papers/Overview_ikat.pdf)).

WANDS has no conversations, so we wrote the store's conversations for the book: 12 follow-ups, each refining a test query by one attribute, a color, shape, size or finish. The store's LLM, which saw only the two turns, rewrote each to stand alone. For example, after `coat rack for bedroom` comes `something in black`, rewritten as `black coat rack for bedroom`. The judgments grade products for the first query, not for the refined one, so nDCG can't score the follow-up. Instead, count three kinds of product in each top 10: those that keep the refinement, because their `attributes` or text contain the value, such as `black` (the example also prints the count from `attributes` alone); those of the right kind, which the judges graded [exact or partial](#store-data) for the first query; and those that are both. The example compares the follow-up alone, the two turns joined and the standalone query, each embedded as a query, with the first query as a baseline. It adds a filter on the standalone query's top 100 that keeps products stating the value, taking the value from the recorded conversation; a live system would have to extract it from the follow-up.

*Example `follow-up-refinements`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/standalone-follow-ups*

The follow-up alone keeps the refinement in 0.950 of its top 10, but only 0.058 are the right kind of product. Any form that carries the first query finds the right kind of product: 0.933 for the joined turns and 0.958 for the standalone query. On these conversations, the joined turns and the standalone query both keep the refinement more often than the first query, which never asked for it: 0.383 and 0.392, against 0.200. Counted in `attributes` alone, the shares are lower, 0.208, 0.200 and 0.125, because many products state the value only in their text, which is all the embeddings read. The conclusions below rest on the text-or-attributes count, which can overcount, since a product that mentions `round legs` counts as round.

The LLM's rewrite does no better than joining the turns: against the joined turns, the standalone query keeps more, fewer or the same number of refined products in 5, 4, 3 conversations, and products of the right kind that also keep the refinement make up 0.350 of the standalone query's top 10s, against 0.325 for the joined turns. The filter raises that share to 0.675, but it leaves 3 conversations with fewer than 10 products. These 12 conversations are ours, not shoppers', so the counts are a diagnosis, not a test.

**Working rule:** Never search a follow-up alone. Join it to the earlier turns at least, or rewrite it to stand alone. When the refinement names a value the catalog states, extract it and boost or filter on it, and fall back to the unfiltered list when too few products remain. Measure on conversations from your own logs before you trust any of it.

## What goes wrong in production {#understanding-queries-in-production}

**Every LLM rewrite is a model call on the query's path.** The examples read rewrites recorded once, offline, but a live search box calls the model on every query while the shopper waits. query2doc's authors note that it "requires running inference with LLMs which can be considerably slower" ([Wang et al., 2023](https://arxiv.org/abs/2303.07678)), and the longer query also slows the BM25 search. A rule of thumb, not a measurement: rewrite frequent queries offline and cache the results, and call the model online only for queries where a test shows a gain.

**A rewrite belongs to one model and one prompt.** Another model version or a reworded prompt can change any rewrite. The manifests of the store's recordings hold the model's digest and each prompt verbatim, and a change to either means measuring again.

**The lexicon must follow the catalog.** A corrector built from last month's catalog can treat this month's brand names as typos. Rebuild the lexicon with the index, and log every query the corrector changes next to the original, so that you can find over-corrections such as `tye` → `the`. In machine-translated queries, misspellings change which products a search returns ([Hanneman et al., 2024](https://aclanthology.org/2024.acl-long.750/)), so expect an error the corrector misses to show up as unstable results for one query.

**A classifier follows its taxonomy.** When product classes are renamed, split or merged, retrain the classifier. A query class that names no product class, such as `Crock Pots & Slow Cookers`, can never be predicted; for `7qt slow cooker` the classifier predicts `Slow Cookers` instead.

**Rewritten queries surface unjudged products.** Every LLM-based change in this chapter that was scored with nDCG@10 lowered [judged@10](#score-every-test-query). Before you adopt a rewrite, have the unjudged products in its top 10s judged, or check condensed scores as [chapter 2](#unjudged-results) does.

**Working rule:** Log the query as typed and as rewritten, cache LLM rewrites, version the model and prompt with the outputs, and rebuild the lexicon and the classifier whenever the catalog changes.

## Decisions this chapter made {#understanding-queries-decisions}

Every setting below was chosen on the train queries. The table holds the chapter's 5 planned comparisons on the test queries, one per column: a retriever with one change, against the same retriever on the query as typed. A difference is established when its permutation p-value is below 0.01.

| Measure | [BM25, synonyms](#expand-with-synonyms) | [Semantic, class boost](#boost-predicted-class) | [BM25, LLM rewrite](#rewrite-queries-with-llm) | [Semantic, LLM rewrite](#rewrite-queries-with-llm) | [Semantic, HyDE](#hyde-hypothetical-products) |
| --- | --- | --- | --- | --- | --- |
| Mean difference | 0.000 | 0.005 | -0.056 | -0.081 | -0.031 |
| Wins, losses, ties | 0, 0, 30 | 7, 4, 19 | 13, 15, 2 | 7, 19, 4 | 8, 14, 8 |
| Permutation p | 1.000 | 0.174 | 0.060 | 0.000 | 0.108 |
| Established | no | no | no | yes | no |
| t-test p | 1.000 | 0.164 | 0.060 | 0.000 | 0.121 |
| 99% interval | 0.000 to 0.000 | -0.002 to 0.017 | -0.143 to 0.005 | -0.132 to -0.035 | -0.115 to 0.001 |
| t-test agrees | yes | yes | yes | yes | yes |
| Interval agrees | yes | yes | yes | yes | yes |

- **Spelling: correct only words the catalog doesn't use.** The corrector fixes the store's train typos, but the typo queries are too few to test it, and it needs context before it handles `tye dye` or `ice an water`. The store doesn't run it yet.
- **Units: one written form for products and queries, from the catalog's own spellings,** with decimals kept whole. The size queries are too few to test it, so the baseline BM25 stays as it is.
- **Synonyms: a list for gaps seen in train queries,** for BM25 only. It changed 1 test query and showed no established difference, so the baseline doesn't expand.
- **Query classes: naive Bayes trained on product text,** because the sample has at most one query per class. The predicted class is a hint. A filter loses on train, and the best boost isn't established on test, so semantic retrieval stays unboosted.
- **LLM rewrites: not used.** The loss for semantic retrieval is established, and BM25's change isn't.
- **HyDE: not used.** Averaged with the query, it shows no established difference, and the hypothetical product alone loses on train.
- **Follow-ups: never searched alone.** Joining the turns does about as well as the LLM's standalone query. A filter on the refined value is the next step, and it needs an extracted value and a fallback.
- **The ranker to beat stays semantic retrieval on the query as typed,** with BM25, unstemmed, as the baseline.
