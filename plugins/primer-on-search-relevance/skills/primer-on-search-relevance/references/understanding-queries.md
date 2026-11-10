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

Example `catalog-spelling-corrector` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import re
from collections import Counter

from lib.queries import correct_query
from lib.store import load_products, load_queries, product_text

texts = product_text(load_products()).str.lower()
counts = Counter(re.findall(r"[a-z]+", " ".join(texts)))       # the lexicon, and how common each word is


def edits1(word):
    """Every string one edit away: a deletion, a swap of two neighbouring letters, a replacement or an insertion."""
    splits = [(word[:cut], word[cut:]) for cut in range(len(word) + 1)]
    letters = "abcdefghijklmnopqrstuvwxyz"
    return ({left + right[1:] for left, right in splits if right}
            | {left + right[1] + right[0] + right[2:] for left, right in splits if len(right) > 1}
            | {left + letter + right[1:] for left, right in splits if right for letter in letters}
            | {left + letter + right for left, right in splits for letter in letters})


def correct(word):
    """Keep a word the catalog uses. Otherwise take the commonest catalog word one edit away, else two."""
    if not word.isalpha() or word in counts:
        return word
    candidates = {edit for edit in edits1(word) if edit in counts} or {
        two for edit in edits1(word) for two in edits1(edit) if two in counts}
    return max(sorted(candidates), key=counts.get) if candidates else word


queries = load_queries()
corrected = queries["query"].map(lambda query: " ".join(correct(word) for word in query.lower().split()))
changed = queries[corrected != queries["query"].str.lower()]
print(f"catalog words: {len(counts):,}")
print("queries changed:", len(changed))
print("of them, train queries:", (changed["split"] == "train").sum())
for query_id, query in changed["query"].items():
    print(f"  {query} ({changed.at[query_id, 'split']}), corrected: {corrected[query_id]}")
same = corrected.equals(queries["query"].map(lambda query: correct_query(query, counts)))
print("same as lib.queries.correct_query:", same)
for word in ["tye", "tie", "the", "kohler", "whitehaven", "malachi", "luau"]:      # P(c), as counts
    print(f"catalog count of {word}:", counts[word])
```

Output:

```text
catalog words: 19,680
queries changed: 4
of them, train queries: 3
  foutains with brick look (train), corrected: fountains with brick look
  twin over full bunk beds cool desins (train), corrected: twin over full bunk beds cool designs
  ligth bulb (train), corrected: light bulb
  tye dye duvet cover (test), corrected: the dye duvet cover
same as lib.queries.correct_query: True
catalog count of tye: 0
catalog count of tie: 45
catalog count of the: 20389
catalog count of kohler: 71
catalog count of whitehaven: 60
catalog count of malachi: 5
catalog count of luau: 4
```

The catalog uses 19,680 distinct words. The corrector changes 4 queries, and the shared function `lib.queries.correct_query` makes the same corrections. Of those, 3 are [train queries](#store-data), and the corrector spells each one as [chapter 6's spelling probes](#semantic-retrieval-in-production) do: the correctly spelled copies of the typo queries that chapter 6 wrote for the book. The corrector leaves the brands alone, because the catalog uses them: `kohler` 71 times and `whitehaven` 60. Some of the words it keeps are rare, such as `malachi`, used 5 times, and `luau`, used 4. A lexicon that left out rare words would treat both as typos.

The corrector's failures are in test queries. `tye dye duvet cover` becomes `the dye duvet cover`: `tye` is one edit from `tie` (45 times in the catalog) and from `the` (20389), and P(c) picks the common word. And `refrigerator with ice an water in door` keeps its `an`. That is a **real-word error**: every word is spelled right, as in "flew form Heathrow" ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/context-sensitive-spelling-correction-1.html)). Both need context. For `tye` and for `an`, count how often each catalog word within one edit of it comes right before the next word of the query, `dye` or `water`:

Example `spelling-context-counts` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import re
from collections import Counter

from lib.queries import correct_word, edits1, word_counts
from lib.store import load_products, product_text

texts = product_text(load_products()).str.lower()
counts = word_counts(texts)                                   # the corrector's lexicon
words_per_product = [re.findall(r"[a-z]+", text) for text in texts]
pairs = Counter(pair for words in words_per_product for pair in zip(words, words[1:]))      # neighbouring words

# tye in "tye dye duvet cover", an in "refrigerator with ice an water in door": each word, the word after it
for word, after in [("tye", "dye"), ("an", "water")]:
    options = sorted(((pairs[(edit, after)], edit) for edit in edits1(word) | {word} if edit in counts), reverse=True)
    for count, edit in options[:3]:
        print(f"catalog count of {edit} {after}:", count)
    choice = correct_word(word, counts)                        # what the corrector without context picks
    print(f"the corrector's choice for {word}: {choice}")
    print(f"catalog count of {choice} {after}, the corrector's choice:", pairs[(choice, after)])
```

Output:

```text
catalog count of tie dye: 18
catalog count of type dye: 0
catalog count of tyke dye: 0
the corrector's choice for tye: the
catalog count of the dye, the corrector's choice: 0
catalog count of and water: 59
catalog count of a water: 20
catalog count of in water: 9
the corrector's choice for an: an
catalog count of an water, the corrector's choice: 0
```

Before `dye`, the catalog's text has `tie` 18 times, and the corrector's choice, `the`, 0. Before `water`, it has `and` 59 times, ahead of `a` at 20, and `an` 0. For these two queries, a corrector that scored each candidate with its neighbouring word would pick `tie` and `and`. Now measure each corrected query on its own judgments:

Example `measure-spelling-corrections` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.queries import correct_query, word_counts
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

products, queries, judgments = load_products(), load_queries(), qrels()
counts = word_counts(product_text(products))
bm25, semantic = LexicalSearch(products), SemanticSearch()
probe_queries, probe_vectors = probes()      # recorded embeddings of the four typo queries, spelled correctly
spelling = probe_queries[probe_queries["kind"] == "spelling"]
spelled = {row["query"]: probe_vectors[index] for index, row in spelling.iterrows()}
typo_queries = spelling["of_query_id"].astype(int).tolist()
print("typo queries:", len(typo_queries))
print("of them, test queries:", (queries.loc[typo_queries, "split"] == "test").sum())

for query_id in typo_queries + [459]:        # the typo queries, then the one variant spelling, tye dye
    typed = queries.at[query_id, "query"]
    corrected = correct_query(typed, counts)
    label = f"{query_id} ({queries.at[query_id, 'split']})"
    print(f"{label}: {typed} -> {corrected}")
    for name, text in [("typed", typed), ("corrected", corrected)]:
        ranking = list(bm25.search(text, k=10).index)
        print(f"{label}, bm25 ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
    if corrected == typed.lower():
        print(f"{label}: the corrector changes nothing")
    elif corrected in spelled:
        for name, vector in [("typed", semantic.query_vectors[query_id]), ("corrected", spelled[corrected])]:
            ranking = list(semantic.search_vector(vector, k=10).index)
            print(f"{label}, semantic ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
    else:
        print(f"{label}: no recorded embedding of the corrected text")
```

Output:

```text
typo queries: 4
of them, test queries: 1
305 (train): ligth bulb -> light bulb
305 (train), bm25 ndcg@10 typed: 0.945
305 (train), bm25 ndcg@10 corrected: 0.945
305 (train), semantic ndcg@10 typed: 1.000
305 (train), semantic ndcg@10 corrected: 1.000
20 (train): foutains with brick look -> fountains with brick look
20 (train), bm25 ndcg@10 typed: 0.356
20 (train), bm25 ndcg@10 corrected: 0.507
20 (train), semantic ndcg@10 typed: 0.353
20 (train), semantic ndcg@10 corrected: 0.645
224 (train): twin over full bunk beds cool desins -> twin over full bunk beds cool designs
224 (train), bm25 ndcg@10 typed: 0.488
224 (train), bm25 ndcg@10 corrected: 0.488
224 (train), semantic ndcg@10 typed: 0.565
224 (train), semantic ndcg@10 corrected: 0.616
406 (test): refrigerator with ice an water in door -> refrigerator with ice an water in door
406 (test), bm25 ndcg@10 typed: 0.501
406 (test), bm25 ndcg@10 corrected: 0.501
406 (test): the corrector changes nothing
459 (test): tye dye duvet cover -> the dye duvet cover
459 (test), bm25 ndcg@10 typed: 0.953
459 (test), bm25 ndcg@10 corrected: 0.953
459 (test): no recorded embedding of the corrected text
```

For the train query `foutains with brick look`, BM25's nDCG@10 goes from 0.356 to 0.507 and semantic retrieval from 0.353 to 0.645. For `twin over full bunk beds cool desins`, only semantic retrieval moves, from 0.565 to 0.616, and for `ligth bulb` neither does. For `refrigerator with ice an water in door`, the corrector changes nothing, and a correct fix couldn't help BM25 either. Of the typed `an` and the correct `and`, bm25s drops `an, and` as stop words, and chapter 6's copy of the query spelled with `and` scores 0.501, the same as the query as typed. For `tye dye duvet cover`, BM25 scores 0.953 either way, because `the` is a stop word and `tye` matches no product, so both versions search the same terms. Semantic retrieval can't be scored on the corrected text, because the recordings hold no embedding of it. The store has 4 typo queries, 1 of them a test query, and the smallest two-sided permutation p-value that so few could give is 0.125.

**Working rule:** Build the lexicon from your catalog, and from your query log once you have one, and correct only words it doesn't hold, so that brand names survive. Before you correct a word, check its neighbours: a corrector without context turns variant spellings into common words and misses real-word errors. Score each correction on the typo queries' own judgments, and collect many more typo queries than the store has before you test a corrector.

## Normalize units the way the catalog writes them {#normalize-units}

A typo has one right spelling; a size, as in `7qt slow cooker`, often has several. **Normalization** maps the different ways of writing one thing to a single form, on the products and on the query alike. In the store, sizes need it. [Chapter 5](#split-text-into-terms) found that `7qt` and `7 qt` never match each other, because the tokenizer drops the one-character `7`. A normalizer that joins each number to its unit, written one way, turns both into one term, `7qt`. It has to run on the product text when you build the index, and on every query. It also has to produce terms the tokenizer keeps whole. The tokenizer splits words at a decimal point, so `3.7qt` would become `7qt`. To prevent that, the shared function `lib.queries.normalize_units` writes the point as an underscore, which the tokenizer keeps inside a word. It also leaves `in` alone when a number or `one` follows, as in `3 in 1`.

In the store, a rule written from the queries would cover `qt`, `in`, `inch` and `"`. Before you trust it, count how the catalog writes inches. The example counts them, prints the terms that the tokenizer makes of a few normalized texts, then builds BM25 three times: over the text as written, normalized by that first rule, and normalized by `normalize_units`, which also handles the catalog's two apostrophes, `''`, for inches. It scores every query, train or test, that gives a number with a unit:

Example `normalize-units-both-sides` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · pystemmer 3.1.0 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.lexical_by_hand import tokenize
from lib.metrics import ndcg_at_k
from lib.queries import INCH_SPELLINGS, normalize_units, unit_rules
from lib.store import load_products, load_queries, product_text, qrels

products, queries, judgments = load_products(), load_queries(), qrels()
text = product_text(products).str.lower()
for name, unit in [("''", r"''"), ('"', r"\""), ("inch", r"-?inch")]:
    print(f"products that write a number then {name}:", text.str.contains(rf"\d\s*{unit}").sum())

first_try = unit_rules([spelling for spelling in INCH_SPELLINGS if spelling != "''"])   # written from queries
rules = {"as written": None, "first try": first_try, "normalized": unit_rules()}
checks = [("3.7-quart slow cooker", "normalized"), ("3 in 1 sofa bed", "normalized"), ("1 in twin", "normalized"),
          ("48 '' range hood", "first try"), ("48 '' range hood", "normalized")]
for example, name in checks:                                                   # what the tokenizer reads
    print(f"terms of {example}, {name}:", " ".join(tokenize(normalize_units(example, rules[name]))))

searches = {}
for name, rule in rules.items():
    rewritten = products.copy()
    if rule is not None:
        for column in ["name", "product_class", "category", "description"]:   # the columns product_text joins
            rewritten[column] = rewritten[column].map(lambda value: normalize_units(value, rule))
    searches[name] = LexicalSearch(rewritten)

with_units = queries[queries["query"].str.contains(r"\d\s*(?:qt|in\b|inch|\")")]
print("queries with a unit:", len(with_units))
print("of them, test queries:", (with_units["split"] == "test").sum())
for query_id, query in with_units["query"].items():
    label = f"{query_id} ({queries.at[query_id, 'split']})"
    print(f"{label}: {query} -> {normalize_units(query)}")
    for name, rule in rules.items():
        typed = query if rule is None else normalize_units(query, rule)
        ranking = list(searches[name].search(typed, k=10).index)
        print(f"{label}, bm25 ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
```

Output:

```text
products that write a number then '': 3014
products that write a number then ": 65
products that write a number then inch: 215
terms of 3.7-quart slow cooker, normalized: 3_7qt slow cooker
terms of 3 in 1 sofa bed, normalized: sofa bed
terms of 1 in twin, normalized: 1in twin
terms of 48 '' range hood, first try: 48 range hood
terms of 48 '' range hood, normalized: 48in range hood
queries with a unit: 4
of them, test queries: 2
62 (train): 7qt slow cooker -> 7qt slow cooker
62 (train), bm25 ndcg@10 as written: 0.554
62 (train), bm25 ndcg@10 first try: 0.930
62 (train), bm25 ndcg@10 normalized: 0.930
101 (train): 48 in entry table with side by side drawer -> 48in entry table with side by side drawer
101 (train), bm25 ndcg@10 as written: 0.569
101 (train), bm25 ndcg@10 first try: 0.569
101 (train), bm25 ndcg@10 normalized: 0.569
285 (test): 48" sliding single track , barn door for laundry -> 48in sliding single track , barn door for laundry
285 (test), bm25 ndcg@10 as written: 0.592
285 (test), bm25 ndcg@10 first try: 0.592
285 (test), bm25 ndcg@10 normalized: 0.592
482 (test): 48 inch kitchen hood -> 48in kitchen hood
482 (test), bm25 ndcg@10 as written: 1.000
482 (test), bm25 ndcg@10 first try: 0.824
482 (test), bm25 ndcg@10 normalized: 1.000
```

The catalog writes a number followed by two apostrophes in 3014 products, by `"` in 65 and by `inch` in 215. The tokenizer reads `3.7-quart slow cooker`, normalized, as `3_7qt slow cooker`, and `3 in 1 sofa bed` as `sofa bed`. `normalize_units` still misreads `1 in twin` as `1in twin`, which is why the terms are worth printing.

For the train query `7qt slow cooker`, normalizing takes BM25's nDCG@10 from 0.554 to 0.930, and the first rule gives 0.930. The test query `48 inch kitchen hood` shows what the first rule loses by missing the two apostrophes: it scores 1.000 as written and 0.824 under the first rule. The query becomes `48in`, while the first rule leaves a hood written `48 ''` as `48 range hood`, and the full rule makes it `48in range hood`. With the full rule, the hood query scores 1.000. The other train query, `48 in entry table with side by side drawer`, scores 0.569 as written and 0.569 normalized, and the test query about a barn door 0.592 and 0.592. That makes 4 queries with a unit, 2 of them [test queries](#store-data): too few for a test, so this is a diagnosis.

**Working rule:** Write normalization rules from the catalog's text, not from the queries, by counting every way it writes each unit. Print the terms the tokenizer makes of the normalized text, because a rule that looks right can produce terms that match the wrong products. Apply the same rules to products and queries in one release, and rebuild the index. When the catalog keeps sizes in fields, such as the width in `attributes`, match the size against the field instead, as [chapter 6 suggests](#codes-carry-no-weight).

## Expand queries with a synonym list {#expand-with-synonyms}

Some gaps are neither typos nor units but different words for one thing, as when the exact products for `midcentury tv unit` say `stand`. **Query expansion** adds terms to a query so that it can match products that use other words for the same thing. "Use of query expansion generally increases recall" ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/query-expansion-1.html)), the share of the relevant products that a search finds. It can cost precision, the share of found products that are relevant: "query expansion may also significantly decrease precision, particularly when the query contains ambiguous terms" ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/automatic-thesaurus-generation-1.html)). An added word can match products the shopper didn't ask for, and move the query away from its meaning, which is called **query drift**. Expansion terms can come from a hand-built list of synonyms, or from the results. **Pseudo-relevance feedback** assumes the top results are relevant and adds their terms to the query, which makes drift its known risk ([Manning et al., 2008](https://nlp.stanford.edu/IR-book/html/htmledition/pseudo-relevance-feedback-1.html)).

In the store, `lib.queries.SYNONYMS` holds 14 groups of interchangeable words, such as `stand` and `unit`, written by reading the train queries whose exact products miss a query word. When a query contains a word or phrase from a group, `expand` appends the group's other members, and BM25 searches the result. Measure it on the train queries, then make the first of the chapter's [five planned comparisons](#understanding-queries) on the test queries, which counts as established if p is below 0.01:

Example `synonym-expansion-train-and-test` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.queries import PLANNED_TEST_COMPARISONS, SYNONYMS, THRESHOLD, expand, report_planned
from lib.store import load_products, load_queries, qrels

products, judgments = load_products(), qrels()
bm25 = LexicalSearch(products)
print("synonym groups:", len(SYNONYMS))
scores = {}
for split in ["train", "test"]:
    queries = load_queries(split)
    expanded = queries.assign(query=queries["query"].map(expand))
    changed = queries.index[expanded["query"] != queries["query"]]
    print(f"{split} queries the list changes:", len(changed))
    for name, frame in [("typed", queries), ("expanded", expanded)]:
        scores[split, name] = evaluate(bm25.run(frame), qrels(split))
        print(f"{split} ndcg@10 {name}: {scores[split, name]['ndcg@10'].mean():.3f}")
        print(f"{split} judged@10 {name}: {scores[split, name]['judged@10'].mean():.3f}")
for query in queries.loc[changed, "query"]:                   # the test queries the list changes
    print(f"test query changed: {query}")
    print(f"words the list adds to it: {expand(query)[len(query) + 1:]}")

change = (scores["train", "expanded"]["ndcg@10"] - scores["train", "typed"]["ndcg@10"]).round(3)
print(f"train queries better, worse: {(change > 0).sum()}, {(change < 0).sum()}")       # for choosing, not evidence
print(f"share of the net train gain from the largest gain: {change.max() / change.sum():.3f}")
for kind, query_id in [("gain", change.idxmax()), ("loss", change.idxmin())]:
    query = load_queries().at[query_id, "query"]
    added = expand(query)[len(query) + 1:]
    print(f"largest train {kind}: {query}")
    print(f"largest train {kind}, words added: {added}")
    print(f"largest train {kind}, change: {change[query_id]:+.3f}")
named = [product_id for product_id in bm25.search(expand(query), k=10).index if added in products.at[product_id, "name"]]
print(f"largest train loss, top 10 names with {added}:", len(named))      # query and added: the largest loss's
print("largest train loss, of those, unjudged:", sum(product_id not in judgments[query_id] for product_id in named))

print("\nplanned test comparisons:", len(PLANNED_TEST_COMPARISONS))
print(f"p-value threshold: {THRESHOLD:.2f}")
report_planned("synonyms, bm25", scores["test", "expanded"]["ndcg@10"], scores["test", "typed"]["ndcg@10"])
```

Output:

```text
synonym groups: 14
train queries the list changes: 14
train ndcg@10 typed: 0.695
train judged@10 typed: 0.930
train ndcg@10 expanded: 0.722
train judged@10 expanded: 0.944
test queries the list changes: 1
test ndcg@10 typed: 0.725
test judged@10 typed: 0.927
test ndcg@10 expanded: 0.725
test judged@10 expanded: 0.927
test query changed: indoor multi tiered plant stand
words the list adds to it: unit
train queries better, worse: 6, 5
share of the net train gain from the largest gain: 0.473
largest train gain: midcentury tv unit
largest train gain, words added: stand mid century
largest train gain, change: +0.632
largest train loss: wire basket with dividers
largest train loss, words added: hamper
largest train loss, change: -0.176
largest train loss, top 10 names with hamper: 4
largest train loss, of those, unjudged: 4

planned test comparisons: 5
p-value threshold: 0.01
synonyms, bm25, mean difference: 0.000
synonyms, bm25, wins, losses, ties: 0, 0, 30
synonyms, bm25, permutation p: 1.000
synonyms, bm25, established at 0.01: no
synonyms, bm25, t-test p: 1.000
synonyms, bm25, t-test agrees: yes
synonyms, bm25, 99% interval: 0.000 to 0.000
synonyms, bm25, interval agrees: yes
```

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

Example `query-classes-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.queries import class_rows, train_classifier
from lib.store import load_labels, load_products, load_queries, product_text

products, queries, labels = load_products(), load_queries(), load_labels()
rows = class_rows(products)                     # one row per (product, class) for products with a class
vectorizer, model = train_classifier(products)  # the same, by scikit-learn's MultinomialNB
words = vectorizer.transform(product_text(rows))  # word counts: one row per (product, class), one column per word
classes = np.array(sorted(rows["label"].unique()))
print("product classes:", len(classes))
print("products without a class:", (products["product_class"] == "").sum())
print("products with several classes:", products["product_class"].str.contains("|", regex=False).sum())
missing = queries["query_class"].dropna()[lambda names: ~names.isin(classes)]
print("query classes that no product has:", len(missing))
print("query classes that no product has, names:", "; ".join(missing))

# Naive Bayes: log P(class) + sum over the query's words of log P(word | class), each word count smoothed by 1
word_counts = np.vstack([np.asarray(words[(rows["label"] == name).to_numpy()].sum(axis=0)) for name in classes])
log_prior = np.log(rows["label"].value_counts()[classes].to_numpy() / len(rows))
log_likelihood = np.log((word_counts + 1) / (word_counts.sum(axis=1, keepdims=True) + word_counts.shape[1]))
query_words = vectorizer.transform(queries["query"])
predicted = classes[np.asarray(query_words @ log_likelihood.T + log_prior).argmax(axis=1)]
print("same predictions as MultinomialNB:", (predicted == model.predict(query_words)).sum(), "of", len(queries))

queries = queries.assign(predicted=predicted)
print("predicted class equals query_class:", (queries["predicted"] == queries["query_class"]).sum())
exact = labels[labels["grade"] == 2].join(products["product_class"].str.split("|"), on="product_id")
for column, name in [("predicted", "predicted class"), ("query_class", "query_class")]:
    share = [exact.loc[exact["query_id"] == query_id, "product_class"].apply(lambda names: label in names).mean()
             for query_id, label in queries[column].items()]
    print(f"queries where most exact products have the {name}:", (np.array(share) > 0.5).sum())
for query_id in [133, 255, 410]:
    query, split, label = queries.loc[query_id, ["query", "split", "predicted"]]
    print(f"{query_id} ({split}): {query} -> {label}"
          f" (query_class: {queries.at[query_id, 'query_class']})")
print("predicted class for 7qt slow cooker:", queries.at[62, "predicted"])       # its query_class has no products
```

Output:

```text
product classes: 410
products without a class: 800
products with several classes: 620
query classes that no product has: 1
query classes that no product has, names: Crock Pots & Slow Cookers
same predictions as MultinomialNB: 80 of 80
predicted class equals query_class: 60
queries where most exact products have the predicted class: 63
queries where most exact products have the query_class: 63
133 (test): outdoor light fixtures -> Light Bulbs (query_class: Outdoor Wall Lights)
255 (test): desk and chair set -> Desks (query_class: Office Chairs)
410 (train): pool floats -> Deck Boxes (query_class: Lawn Games)
predicted class for 7qt slow cooker: Slow Cookers
```

The products use 410 classes. 800 products have none and are left out, and 620 have several, so each of those is one training row per class. The hand-built classifier makes the same prediction as `MultinomialNB` for 80 of 80 queries. Its prediction equals `query_class` for 60, but `query_class` is a guess too. Against the judgments, the two guesses tie: for 63 queries most exact products carry the predicted class, and for 63 they carry `query_class`. Three of its predictions show how it reads a query by its words alone: `outdoor light fixtures` becomes `Light Bulbs`, `desk and chair set` becomes `Desks`, and `pool floats` becomes `Deck Boxes`.

The sample's design limits what this check can show. Each class is tested by at most one query, so no per-class accuracy can be measured, and 80 queries cover only part of the 410 classes, so the counts say nothing about the rest. A query classifier can't be trained on these queries at all, and two classifiers can only be compared on whether each gets these few queries right. And 1 query class, `Crock Pots & Slow Cookers`, names no product class at all, so no classifier trained on products can predict it.

**Working rule:** When you have no labelled queries, train a query classifier on your products' classes and check it against the classes of judged exact products, not against another classifier's guesses. Once your logs give you labelled queries, train on those. Treat the predicted class as a hint for ranking, never as a label.

## Boost the predicted class instead of filtering {#boost-predicted-class}

In the store, the predicted class comes from [the naive Bayes classifier](#classify-queries-from-products) trained on product text. A predicted class can act on retrieval in two ways. A **filter** keeps only products in the class. A **boost** adds a fixed amount to their scores, so that they move up without anything else being removed. A filter is only as good as the classifier: every relevant product outside the predicted class disappears.

The store's train judgments show how much a filter would cost: for the train queries, 501 of 1937 exact products lie outside their query's predicted class. The example adds a boost to the similarities of semantic retrieval, the store's best ranker and so its [ranker to beat](#compare-runs-in-a-harness), and tries five boost weights and a filter on the train queries. It takes the best boost to the test queries for the second of the chapter's [five planned comparisons](#understanding-queries), which counts as established if p is below 0.01:

Example `class-boost-train-and-test` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.metrics import evaluate
from lib.queries import THRESHOLD, class_boost_run, in_class, report_planned, train_classifier
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries = load_products(), load_queries()
vectorizer, model = train_classifier(products)               # trained on product text, never on queries
predicted = dict(zip(queries.index, model.predict(vectorizer.transform(queries["query"]))))
semantic = SemanticSearch()
train, train_judgments = load_queries("train"), qrels("train")

exact, outside = 0, 0
for query_id, judged in train_judgments.items():
    member = in_class(products, predicted[query_id])
    exact += sum(grade == 2 for grade in judged.values())
    outside += sum(grade == 2 and not member[product_id] for product_id, grade in judged.items())
print(f"exact train products outside the predicted class: {outside} of {exact}")

base = evaluate(semantic.run(train), train_judgments)
print(f"train ndcg@10 semantic: {base['ndcg@10'].mean():.3f}")
print(f"train judged@10 semantic: {base['judged@10'].mean():.3f}")
train_scores = {}
for weight in [None, 0.01, 0.02, 0.05, 0.1, 0.2]:                          # None: keep only the predicted class
    train_scores[weight] = evaluate(class_boost_run(semantic, train.index, predicted, products, weight), train_judgments)
    name = "filter" if weight is None else f"boost {weight}"
    print(f"train ndcg@10 {name}: {train_scores[weight]['ndcg@10'].mean():.3f}")
boosts = [weight for weight in train_scores if weight is not None]
best = max(boosts, key=lambda weight: train_scores[weight]["ndcg@10"].mean())
for name, weight in [("filter", None), ("best boost", best)]:
    print(f"train judged@10 {name}: {train_scores[weight]['judged@10'].mean():.3f}")
print("best boost on train:", best)

print(f"\nthe planned test comparison, threshold {THRESHOLD:.2f}:")
test, test_judgments = load_queries("test"), qrels("test")
boosted = evaluate(class_boost_run(semantic, test.index, predicted, products, best), test_judgments)
plain = evaluate(semantic.run(test), test_judgments)
print(f"test judged@10 semantic: {plain['judged@10'].mean():.3f}")
print(f"test judged@10 boosted: {boosted['judged@10'].mean():.3f}")
report_planned("class boost, semantic", boosted["ndcg@10"], plain["ndcg@10"])
```

Output:

```text
exact train products outside the predicted class: 501 of 1937
train ndcg@10 semantic: 0.772
train judged@10 semantic: 0.964
train ndcg@10 filter: 0.675
train ndcg@10 boost 0.01: 0.773
train ndcg@10 boost 0.02: 0.774
train ndcg@10 boost 0.05: 0.768
train ndcg@10 boost 0.1: 0.742
train ndcg@10 boost 0.2: 0.692
train judged@10 filter: 0.866
train judged@10 best boost: 0.966
best boost on train: 0.02

the planned test comparison, threshold 0.01:
test judged@10 semantic: 0.990
test judged@10 boosted: 0.993
class boost, semantic, mean difference: 0.005
class boost, semantic, wins, losses, ties: 7, 4, 19
class boost, semantic, permutation p: 0.174
class boost, semantic, established at 0.01: no
class boost, semantic, t-test p: 0.164
class boost, semantic, t-test agrees: yes
class boost, semantic, 99% interval: -0.002 to 0.017
class boost, semantic, interval agrees: yes
```

On the train queries, the filter takes [nDCG@10](#score-one-ranking) from 0.772 to 0.675, and [judged@10](#score-every-test-query) from 0.964 to 0.866, so its top 10s also fill with products nobody judged. The boosts score from 0.773 at 0.01 and 0.774 at 0.02 down to 0.692 at 0.2, and the output lists the rest. The best boost on train is 0.02, with judged@10 of 0.966.

On the test queries, judged@10 is 0.990 without the boost and 0.993 with it, and the boost's gain isn't established ([planned comparisons](#understanding-queries-decisions)).

**Working rule:** Don't filter on a predicted class. Boost it with a weight tuned on train queries, and keep the boost only if its planned test comparison is established. The store's isn't, so its semantic retrieval stays unboosted. We recommend a class filter only when the shopper chose the class, for example by clicking a category.

## Rewrite queries with an LLM {#rewrite-queries-with-llm}

**Query rewriting** replaces the query with a text written to retrieve better. Where the corrector, the unit rules and the synonym list each fix one kind of gap, an LLM can fix spelling, expand abbreviations and add synonyms in one step, with no list to maintain. In rewrite-retrieve-read, the rewritten query goes to the retriever in place of the original ([Ma et al., 2023](https://arxiv.org/abs/2305.14283)). Studies report gains. With query2doc, which appends an LLM-written passage, a **pseudo-document**, to the query, BM25 improved "by 3% to 15% on ad-hoc IR datasets", with text-davinci-003 writing the passages for MS MARCO and TREC DL queries ([Wang et al., 2023](https://arxiv.org/abs/2303.07678)). Other studies report failures. A comparison of 11 expansion methods, 12 datasets and 24 retrievers found that "expansion improves scores for weaker models, but generally harms stronger models" ([Weller et al., 2024](https://arxiv.org/abs/2309.08541)). Another study found that LLM-based expansion "can significantly degrade the retrieval effectiveness when knowledge in the LLM is insufficient or query ambiguity is high" ([Abe et al., 2025](https://arxiv.org/abs/2505.12694)).

The rewrites that the examples read were recorded with the store's LLM, the open model named in [the chapter's opening](#understanding-queries), run locally on each query alone. The prompt's instruction is: "Rewrite this search query from an online furniture and home-goods store so that a search engine finds what the shopper wants. Fix spelling, expand abbreviations and add common synonyms for the product type, but keep every requirement the shopper stated and add none of your own. Return a single line." The rest of the prompt gives the query and asks for JSON, and the recording's manifest holds it in full. The recording script embedded each rewrite as a query, with the same embedding model as the products. BM25 searches the rewrite's text, and semantic retrieval its embedding. Look at the train queries first:

Example `llm-rewrites-on-train` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.recorded import llm_rewrites, manifest
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

recording = manifest("llm-rewrites")
print("model:", recording["model"])
print("embedding model:", recording["embedding_model"])
print("rewrite prompt, first line:", recording["prompts"]["rewrite"].split("\n")[0])
table, rewrite_vectors, _ = llm_rewrites()
rewrites = table.set_index("query_id")["rewrite"]
row = {query_id: position for position, query_id in enumerate(table["query_id"])}
for query_id in [20, 205, 313]:
    print(f"rewrite of {load_queries().at[query_id, 'query']}: {rewrites[query_id]}")

queries, judgments = load_queries("train"), qrels("train")
products = load_products()
exact = [product_id for product_id, grade in judgments[313].items() if grade == 2]
print("exact products for malachi sled:", "; ".join(products.loc[exact, "name"]))
bm25, semantic = LexicalSearch(products), SemanticSearch()
runs = {"bm25, typed": bm25.run(queries),
        "bm25, rewrite": bm25.run(queries.assign(query=rewrites[queries.index].to_numpy())),
        "semantic, typed": semantic.run(queries),
        "semantic, rewrite": {query_id: list(semantic.search_vector(rewrite_vectors[row[query_id]]).index)
                              for query_id in queries.index}}
scores = {name: evaluate(run, judgments) for name, run in runs.items()}
for name, frame in scores.items():
    print(f"train ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
    print(f"train judged@10 {name}: {frame['judged@10'].mean():.3f}")
for retriever in ["bm25", "semantic"]:                       # for choosing, not evidence
    change = (scores[f"{retriever}, rewrite"]["ndcg@10"] - scores[f"{retriever}, typed"]["ndcg@10"]).round(3)
    print(f"train queries better, worse, {retriever}: {(change > 0).sum()}, {(change < 0).sum()}")
    print(f"largest train loss, {retriever}: {queries.at[change.idxmin(), 'query']}")
    print(f"largest train loss, {retriever}, change: {change.min():+.3f}")
```

Output:

```text
model: gemma4:12b-it-q4_K_M
embedding model: Snowflake/snowflake-arctic-embed-m-v1.5
rewrite prompt, first line: Rewrite this search query from an online furniture and home-goods store so that a search engine finds what the shopper wants. Fix spelling, expand abbreviations and add common synonyms for the product type, but keep every requirement the shopper stated and add none of your own. Return a single line.
rewrite of foutains with brick look: fountains with brick look, brick style water features, masonry fountains, faux brick fountains
rewrite of ines shag rug w003096809: Ines shag rug w003096809 area rug carpet
rewrite of malachi sled: Malachi sled sofa couch settee loveseat
exact products for malachi sled: malachi sled end table; malachi 44 '' console table; malachi sled coffee table
train ndcg@10 bm25, typed: 0.695
train judged@10 bm25, typed: 0.930
train ndcg@10 bm25, rewrite: 0.646
train judged@10 bm25, rewrite: 0.868
train ndcg@10 semantic, typed: 0.772
train judged@10 semantic, typed: 0.964
train ndcg@10 semantic, rewrite: 0.759
train judged@10 semantic, rewrite: 0.924
train queries better, worse, bm25: 23, 24
largest train loss, bm25: malachi sled
largest train loss, bm25, change: -0.644
train queries better, worse, semantic: 18, 25
largest train loss, semantic: wall design shelf
largest train loss, semantic, change: -0.653
```

The rewrites fix spelling, `fountains with brick look, brick style water features, masonry fountains, faux brick fountains`, and keep codes, `Ines shag rug w003096809 area rug carpet`. For `malachi sled`, a product line, the LLM guessed a sofa: it wrote `Malachi sled sofa couch settee loveseat`, while the exact products are `malachi sled end table; malachi 44 '' console table; malachi sled coffee table`. On the train queries, BM25's nDCG@10 goes from 0.695 to 0.646, and semantic retrieval's from 0.772 to 0.759. [Judged@10](#score-every-test-query) falls for both, from 0.930 to 0.868 and from 0.964 to 0.924, so the rewrites surface products nobody judged, and part of each fall in nDCG@10 may come from them. The numbers of queries that score better and worse are 23, 24 for BM25 and 18, 25 for semantic retrieval. BM25's largest loss is `malachi sled`, at -0.644, and semantic retrieval's is `wall design shelf`, at -0.653.

These train numbers shape expectations and prove nothing. The third and fourth of the chapter's [five planned comparisons](#understanding-queries) were fixed in advance, so they go to the test queries whatever the train queries show, and each counts as established if p is below 0.01. Before you run them, predict: on the test queries, will the rewrite help BM25, the weaker retriever, hurt semantic retrieval, the stronger one, or neither?

Example `llm-rewrites-on-test` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.queries import THRESHOLD, condensed, report_planned, rewrite_runs
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")             # scored on the human judgments
runs = rewrite_runs(queries, LexicalSearch(load_products()), SemanticSearch())

print(f"the planned test comparisons, threshold {THRESHOLD:.2f}:")
for retriever, (rewritten, typed) in runs.items():
    name = f"llm rewrite, {retriever}"
    after, before = evaluate(rewritten, judgments), evaluate(typed, judgments)
    for form, frame in [("typed", before), ("rewrite", after)]:
        print(f"{name}, test ndcg@10 {form}: {frame['ndcg@10'].mean():.3f}")
        print(f"{name}, test judged@10 {form}: {frame['judged@10'].mean():.3f}")
    report_planned(name, after["ndcg@10"], before["ndcg@10"])

    # Exploratory, never established: the same comparison on condensed runs, which drop unjudged products
    after, before = (evaluate(condensed(run, judgments), judgments)["ndcg@10"] for run in (rewritten, typed))
    result = compare(after, before, confidence=1 - THRESHOLD)
    print(f"{name}, condensed ndcg@10 typed: {before.mean():.3f}")
    print(f"{name}, condensed ndcg@10 rewrite: {after.mean():.3f}")
    print(f"{name}, condensed, exploratory mean difference: {result['mean difference']:.3f}")
    print(f"{name}, condensed, exploratory permutation p: {result['permutation p']:.3f}")
    low, high = result["ci low"], result["ci high"]
    print(f"{name}, condensed, exploratory {1 - THRESHOLD:.0%} interval: {low:.3f} to {high:.3f}")
```

Output:

```text
the planned test comparisons, threshold 0.01:
llm rewrite, bm25, test ndcg@10 typed: 0.725
llm rewrite, bm25, test judged@10 typed: 0.927
llm rewrite, bm25, test ndcg@10 rewrite: 0.669
llm rewrite, bm25, test judged@10 rewrite: 0.903
llm rewrite, bm25, mean difference: -0.056
llm rewrite, bm25, wins, losses, ties: 13, 15, 2
llm rewrite, bm25, permutation p: 0.060
llm rewrite, bm25, established at 0.01: no
llm rewrite, bm25, t-test p: 0.060
llm rewrite, bm25, t-test agrees: yes
llm rewrite, bm25, 99% interval: -0.143 to 0.005
llm rewrite, bm25, interval agrees: yes
llm rewrite, bm25, condensed ndcg@10 typed: 0.778
llm rewrite, bm25, condensed ndcg@10 rewrite: 0.725
llm rewrite, bm25, condensed, exploratory mean difference: -0.053
llm rewrite, bm25, condensed, exploratory permutation p: 0.044
llm rewrite, bm25, condensed, exploratory 99% interval: -0.150 to -0.002
llm rewrite, semantic, test ndcg@10 typed: 0.830
llm rewrite, semantic, test judged@10 typed: 0.990
llm rewrite, semantic, test ndcg@10 rewrite: 0.749
llm rewrite, semantic, test judged@10 rewrite: 0.947
llm rewrite, semantic, mean difference: -0.081
llm rewrite, semantic, wins, losses, ties: 7, 19, 4
llm rewrite, semantic, permutation p: 0.000
llm rewrite, semantic, established at 0.01: yes
llm rewrite, semantic, t-test p: 0.000
llm rewrite, semantic, t-test agrees: yes
llm rewrite, semantic, 99% interval: -0.132 to -0.035
llm rewrite, semantic, interval agrees: yes
llm rewrite, semantic, condensed ndcg@10 typed: 0.834
llm rewrite, semantic, condensed ndcg@10 rewrite: 0.791
llm rewrite, semantic, condensed, exploratory mean difference: -0.043
llm rewrite, semantic, condensed, exploratory permutation p: 0.002
llm rewrite, semantic, condensed, exploratory 99% interval: -0.079 to -0.014
```

For BM25, judged@10 falls from 0.927 to 0.903, and [nDCG@10](#score-one-ranking) from 0.725 to 0.669, a difference that isn't established ([planned comparisons](#understanding-queries-decisions)).

For semantic retrieval, judged@10 falls from 0.990 to 0.947, and nDCG@10 from 0.830 to 0.749, an established loss, with a permutation p-value that rounds to 0.000.

Because judged@10 fell, the example repeats both comparisons on [condensed](#unjudged-results) lists, which drop unjudged products before scoring. That check was chosen after seeing the drop, so it is exploratory and can't establish anything. For semantic retrieval, condensed nDCG@10 goes from 0.834 to 0.791, a difference of -0.043 with a permutation p of 0.002 and a 99% interval from -0.079 to -0.014. So the loss doesn't rest on unjudged products alone. For BM25, condensed nDCG@10 goes from 0.778 to 0.725, with a permutation p of 0.044, a question for new queries rather than a finding.

If you predicted that the rewrite would help BM25, the test doesn't show it, on these queries with this LLM and prompt: BM25 moved the other way from what Weller et al. and query2doc report, though not by an established amount. If you predicted harm to semantic retrieval, you predicted what Weller et al. found for strong retrievers, here with this model, this prompt and these queries.

The queries that move most show what a rewrite does. Read them with the number of unjudged products in each rewritten top 10, which the metric counts as irrelevant:

Example `rewrite-largest-changes` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from bm25s.stopwords import STOPWORDS_EN

from lib.lexical import LexicalSearch
from lib.metrics import evaluate, ndcg_at_k
from lib.queries import rewrite_runs
from lib.recorded import llm_rewrites, probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products())
rewrites = llm_rewrites()[0].set_index("query_id")["rewrite"]
largest = {}
for retriever, (rewritten, typed) in rewrite_runs(queries, bm25, SemanticSearch()).items():
    change = evaluate(rewritten, judgments)["ndcg@10"] - evaluate(typed, judgments)["ndcg@10"]
    for kind, query_id in [("loss", change.idxmin()), ("gain", change.idxmax())]:
        label, largest[(retriever, kind)] = f"{retriever}, largest {kind}", query_id
        print(f"{label}: {queries.at[query_id, 'query']}")
        print(f"{label}, change: {change[query_id]:+.3f}")
        print(f"{label}, rewrite: {rewrites[query_id]}")
        unjudged = sum(product_id not in judgments[query_id] for product_id in rewritten[query_id][:10])
        print(f"{label}, unjudged products in the rewrite's top 10: {unjudged}")

# BM25's largest gain: score the query with only its spelling fixed (chapter 6's probe), apart from the added words
query_id = largest[("bm25", "gain")]
spelled = probes()[0].dropna(subset=["of_query_id"]).set_index("of_query_id")["query"]
if query_id in spelled.index:
    for name, text in [("typed", queries.at[query_id, "query"]), ("spelling fixed only", spelled[query_id])]:
        ranking = list(bm25.search(text, k=10).index)
        print(f"bm25, largest gain, ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
    print("bm25 stop words among an and and:", ", ".join(word for word in ["an", "and"] if word in STOPWORDS_EN))
```

Output:

```text
bm25, largest loss: fold in half table
bm25, largest loss, change: -0.471
bm25, largest loss, rewrite: folding table, collapsible table, drop leaf table, gateleg table
bm25, largest loss, unjudged products in the rewrite's top 10: 3
bm25, largest gain: refrigerator with ice an water in door
bm25, largest gain, change: +0.159
bm25, largest gain, rewrite: refrigerator with ice and water in door, fridge with door dispenser, refrigerator with external water and ice dispenser
bm25, largest gain, unjudged products in the rewrite's top 10: 1
semantic, largest loss: pull out sleeper loveseat
semantic, largest loss, change: -0.304
semantic, largest loss, rewrite: pull out sleeper loveseat sofa couch convertible sofa sofa bed
semantic, largest loss, unjudged products in the rewrite's top 10: 4
semantic, largest gain: nautical platters
semantic, largest gain, change: +0.055
semantic, largest gain, rewrite: nautical platters serving trays seafood platters maritime serving boards
semantic, largest gain, unjudged products in the rewrite's top 10: 0
bm25, largest gain, ndcg@10 typed: 0.501
bm25, largest gain, ndcg@10 spelling fixed only: 0.501
bm25 stop words among an and and: an, and
```

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

Example `hyde-train-and-test` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.queries import THRESHOLD, report_planned
from lib.recorded import llm_rewrites
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

table, _, hypothetical_vectors = llm_rewrites()
hypothetical, vectors = table.set_index("query_id")["hypothetical"], dict(zip(table["query_id"], hypothetical_vectors))
bm25, semantic = LexicalSearch(load_products()), SemanticSearch()


def hyde(query_id):
    """Gao et al.'s average of the hypothetical product's embedding and the query's, scaled back to length 1."""
    average = (vectors[query_id] + semantic.query_vectors[query_id]) / 2
    return average / np.linalg.norm(average)


def runs(queries):
    ids, typed = queries.index, queries["query"]
    return {"semantic": semantic.run(queries),
            "hypothetical alone": {query_id: list(semantic.search_vector(vectors[query_id]).index) for query_id in ids},
            "hyde": {query_id: list(semantic.search_vector(hyde(query_id)).index) for query_id in ids},
            "bm25": bm25.run(queries),
            "bm25, hypothetical alone": bm25.run(queries.assign(query=ids.map(hypothetical))),
            "bm25, query five times plus hypothetical": bm25.run(queries.assign(           # query2doc's weighting
                query=[" ".join([typed[query_id]] * 5 + [hypothetical[query_id]]) for query_id in ids]))}


train = {name: evaluate(run, qrels("train")) for name, run in runs(load_queries("train")).items()}
for name, frame in train.items():
    print(f"train ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
    print(f"train judged@10 {name}: {frame['judged@10'].mean():.3f}")
change = (train["hypothetical alone"]["ndcg@10"] - train["semantic"]["ndcg@10"]).round(3)    # for choosing, not evidence
print(f"train queries better, worse, hypothetical alone: {(change > 0).sum()}, {(change < 0).sum()}")

print(f"\nthe planned test comparison, threshold {THRESHOLD:.2f}:")
test = {name: evaluate(run, qrels("test")) for name, run in runs(load_queries("test")).items()
        if name in ["semantic", "hyde"]}
for name, frame in test.items():
    print(f"test judged@10 {name}: {frame['judged@10'].mean():.3f}")
report_planned("hyde, semantic", test["hyde"]["ndcg@10"], test["semantic"]["ndcg@10"])
```

Output:

```text
train ndcg@10 semantic: 0.772
train judged@10 semantic: 0.964
train ndcg@10 hypothetical alone: 0.704
train judged@10 hypothetical alone: 0.890
train ndcg@10 hyde: 0.769
train judged@10 hyde: 0.946
train ndcg@10 bm25: 0.695
train judged@10 bm25: 0.930
train ndcg@10 bm25, hypothetical alone: 0.644
train judged@10 bm25, hypothetical alone: 0.854
train ndcg@10 bm25, query five times plus hypothetical: 0.694
train judged@10 bm25, query five times plus hypothetical: 0.912
train queries better, worse, hypothetical alone: 13, 29

the planned test comparison, threshold 0.01:
test judged@10 semantic: 0.990
test judged@10 hyde: 0.970
hyde, semantic, mean difference: -0.031
hyde, semantic, wins, losses, ties: 8, 14, 8
hyde, semantic, permutation p: 0.108
hyde, semantic, established at 0.01: no
hyde, semantic, t-test p: 0.121
hyde, semantic, t-test agrees: yes
hyde, semantic, 99% interval: -0.115 to 0.001
hyde, semantic, interval agrees: yes
```

On the train queries, the hypothetical product alone takes semantic retrieval's nDCG@10 from 0.772 to 0.704, with [judged@10](#score-every-test-query) from 0.964 to 0.890, and the numbers of queries that score better and worse are 13, 29. Averaged with the query, it scores 0.769, with judged@10 of 0.946. BM25 behaves the same way: 0.695 on the query, 0.644 on the hypothetical text alone, and 0.694 with the query repeated five times before it, with judged@10 of 0.930, 0.854 and 0.912. Keeping the query recovers what the hypothetical product loses, and on the train queries, for either retriever, the combination adds nothing over the query alone. Train numbers guide the design; only the planned test comparison is evidence.

On the test queries, judged@10 goes from 0.990 to 0.970, and HyDE shows no established difference from semantic retrieval ([planned comparisons](#understanding-queries-decisions)). This result belongs to one hypothetical product per query, from a 12-billion-parameter model run at temperature 0. Gao et al. sampled from a far larger LLM, and only that one raised their fine-tuned retriever.

**Working rule:** When you try HyDE, always average the query's own embedding in. Expect the largest gains with an encoder trained without labels; with a fine-tuned encoder, Gao et al. saw gains only from their largest LLM, and the store, with its model, prompt and encoder, saw none. On an encoder like the store's, which [already beats BM25](#compare-runs-in-a-harness) on these queries, test HyDE before you pay for an LLM call per query. The store doesn't use it.

## Turn a follow-up into a standalone query {#standalone-follow-ups}

The last gap from [the chapter's opening](#understanding-queries) comes from conversation: a shopper's next message often depends on the last one, as `in white` refines a search for a desk. Retrieval sees one text, so the follow-up has to become a **standalone query**, one that keeps what the shopper still wants. Conversational query rewriting is the task of turning "a context-dependent into a self-contained question with the same answer", and the CANARD dataset holds 40,527 such rewrites ([Elgohary et al., 2019](https://aclanthology.org/D19-1605/)). In TREC CAsT 2019, a conversational search evaluation, people's rewrites beat the best automatic system, "a 35% relative improvement of manual rewrites over the best automatic system" ([Dalton et al., 2020](https://arxiv.org/abs/2003.13624)). Later work with prompted LLMs found that "informative query rewrites can yield substantially improved retrieval performance compared to human rewrites, especially with sparse retrievers" ([Ye et al., 2023](https://arxiv.org/abs/2310.09716)), and in TREC iKAT 2025, CAsT's successor, "Most of the runs leveraged LLMs in their pipelines, for single or multiple query rewriting" ([TREC iKAT 2025 overview](https://trec.nist.gov/pubs/trec34/papers/Overview_ikat.pdf)).

WANDS has no conversations, so we wrote the store's conversations for the book: 12 follow-ups, each refining a test query by one attribute, a color, shape, size or finish. The store's LLM, which saw only the two turns, rewrote each to stand alone. For example, after `coat rack for bedroom` comes `something in black`, rewritten as `black coat rack for bedroom`. The judgments grade products for the first query, not for the refined one, so nDCG can't score the follow-up. Instead, count three kinds of product in each top 10: those that keep the refinement, because their `attributes` or text contain the value, such as `black` (the example also prints the count from `attributes` alone); those of the right kind, which the judges graded [exact or partial](#store-data) for the first query; and those that are both. The example compares the follow-up alone, the two turns joined and the standalone query, each embedded as a query, with the first query as a baseline. It adds a filter on the standalone query's top 100 that keeps products stating the value, taking the value from the recorded conversation; a live system would have to extract it from the follow-up.

Example `follow-up-refinements` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.queries import mentions
from lib.recorded import llm_conversations
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

products, judgments, semantic = load_products(), qrels("test"), SemanticSearch()
attributes, text = products["attributes"], product_text(products)        # the embeddings read only the text
conversations, vectors = llm_conversations()                 # follow-ups we wrote for the book, not shoppers'
print("conversations:", len(conversations))
example = conversations.iloc[4]
print(f"first query: {load_queries().at[example['query_id'], 'query']}")
print(f"follow-up: {example['follow_up']}")
print(f"standalone: {example['standalone']}")

shares, filtered_lengths = {}, []                            # shares: (top 10, measure) -> one share per conversation
for row, (first, value) in enumerate(zip(conversations["query_id"], conversations["value"])):
    standalone = semantic.search_vector(vectors["standalone"][row], k=100).index
    stated = mentions(standalone, value, attributes) | mentions(standalone, value, text)
    tops = {"first query": semantic.search(first, k=10).index,
            "follow-up alone": semantic.search_vector(vectors["follow_up"][row], k=10).index,
            "turns joined": semantic.search_vector(vectors["joined"][row], k=10).index,
            "standalone": standalone[:10],
            "standalone, filtered": standalone[stated][:10]}         # given the value, which a live system extracts
    filtered_lengths.append(len(tops["standalone, filtered"]))
    for name, top in tops.items():
        in_attributes = mentions(top, value, attributes)
        in_either = in_attributes | mentions(top, value, text)
        right_kind = np.array([judgments[first].get(product_id, 0) >= 1 for product_id in top], dtype=bool)
        for measure, hits in [("refinement in attributes", in_attributes), ("refinement in text or attributes", in_either),
                              ("right kind", right_kind), ("right kind with the refinement", in_either & right_kind)]:
            shares.setdefault((name, measure), []).append(hits.sum() / 10)     # empty places count as misses
for (name, measure), values in shares.items():
    print(f"{name}, {measure}: {np.mean(values):.3f}")

kept = np.subtract(shares["standalone", "refinement in text or attributes"], shares["turns joined", "refinement in text or attributes"])
print(f"standalone against turns joined, more, fewer, same: {(kept > 0).sum()}, {(kept < 0).sum()}, {(kept == 0).sum()}")
print("conversations the filter leaves with fewer than 10 products:", sum(length < 10 for length in filtered_lengths))
```

Output:

```text
conversations: 12
first query: coat rack for bedroom
follow-up: something in black
standalone: black coat rack for bedroom
first query, refinement in attributes: 0.125
first query, refinement in text or attributes: 0.200
first query, right kind: 0.958
first query, right kind with the refinement: 0.175
follow-up alone, refinement in attributes: 0.433
follow-up alone, refinement in text or attributes: 0.950
follow-up alone, right kind: 0.058
follow-up alone, right kind with the refinement: 0.058
turns joined, refinement in attributes: 0.208
turns joined, refinement in text or attributes: 0.383
turns joined, right kind: 0.933
turns joined, right kind with the refinement: 0.325
standalone, refinement in attributes: 0.200
standalone, refinement in text or attributes: 0.392
standalone, right kind: 0.958
standalone, right kind with the refinement: 0.350
standalone, filtered, refinement in attributes: 0.583
standalone, filtered, refinement in text or attributes: 0.900
standalone, filtered, right kind: 0.675
standalone, filtered, right kind with the refinement: 0.675
standalone against turns joined, more, fewer, same: 5, 4, 3
conversations the filter leaves with fewer than 10 products: 3
```

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
