---
title: "A Primer on Search Relevance"
chapter: "What relevance means"
chapter_id: what-relevance-means
book: primer-on-search-relevance
edition: 2026.11.6
verified: 2026-11-12
edition_code: R33J-KWQ9
canonical: https://rollingedition.com/primer-on-search-relevance/what-relevance-means
license: CC BY 4.0
attribution: "“What relevance means,” chapter 2 of A Primer on Search Relevance, Edition 2026.11.6, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/what-relevance-means. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# What relevance means

By the end of this chapter you can read a set of relevance judgments critically: say what each grade claims about a product, find where the judgments came from and where they have holes, and decide how far to trust a score computed from them.

In [chapter 1](#search-end-to-end), the store this book follows, [an online furniture and home-goods retailer](#store-data), scores its rankers against 13,077 judgments and treats every grade as fact: on the [test queries](#store-data), [BM25](#rank-with-bm25) averages an nDCG@10 ([Score one ranking](#score-one-ranking)) of 0.725, and [semantic retrieval](#search-by-meaning) 0.830. Each of those numbers rests on choices the judgments make without saying so: whose idea of relevance they record, how much a near miss is worth, and what happens to the products nobody judged. This chapter reads the store's judgments closely. It changes no ranker, so it reads [train and test queries](#store-data) alike: reading judgments isn't tuning, and every fix in this book is still chosen on train queries only. The few tests it runs on the test queries are exploratory: they describe the judgments, and none establishes a difference ([the book's rule](#when-a-difference-is-established)). [Chapter 3](#compare-runs-in-a-harness) tests the gap between BM25 and semantic retrieval as a planned comparison.

## Judge relevance against the shopper's need {#relevance-is-a-judgment}

A search system returns products that match a query in the way the system defines a match: shared words for lexical retrieval, nearby vectors for semantic retrieval. Information science calls that *system* relevance and separates it from *topical* relevance, whether a product is about the subject of the query, and *situational* relevance, whether it helps with the task at hand ([Saracevic, 2007](https://tefkos.rutgers-sci.domains/Saracevic%20relevance%20pt%20II%20JASIST%20%2707.pdf)). To the argument that system relevance is always perfect, because the system retrieved what the query asked for, Saracevic answers: "Not so."

A **judgment** is a person's label for one pair of a query and a product, their verdict on it, and a **grade** is the number that stands for the label. The store's judgments come from WANDS, a public product-search dataset, through a sample of its queries and products ([Load the store's data](#store-data)). WANDS's judges label each pair exact, partial or irrelevant, which the book grades 2, 1 and 0. Exact means the product is the kind of thing the query asks for and has every attribute the query names; partial means it is the right kind of thing but misses an attribute; irrelevant means it isn't the kind of thing asked for ([Read intent as a product and its modifiers](#intent-in-product-search)). The judge doesn't grade the product against the query's words but against the **information need** behind them, the thing the shopper wanted: "A document is relevant if it addresses the stated information need", and not because it happens to contain the query's words ([Manning et al., 2008, chapter 8](https://nlp.stanford.edu/IR-book/html/htmledition/information-retrieval-system-evaluation-1.html)). Evaluation then makes a bargain. It fixes a set of documents, a set of need statements and their judgments, and abstracts away the real users ([Voorhees, 2007](https://cs.uwaterloo.ca/~brecht/courses/854-Experimental-Performance-Evaluation-2017/readings/trec-cacm-2007.pdf)). In the store, the judgments stand in for shoppers, and every score in this book inherits that bargain.

If matching words were the same as relevance, a product whose text holds every word of the query would be exact. Test that on every judged pair in the store. The example checks whether each product's text, its name, class, category and description, contains every word of its query. The sample cuts descriptions to about 400 characters.

Before you run it, predict: of the judged pairs whose text holds every query word, what share did the judges call exact?

Example `word-match-versus-judgment` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.6:

```python
import re

from lib.store import load_labels, load_products, load_queries, product_text


def words(text):
    """Lowercase word tokens: a rough stand-in for what lexical search matches."""
    return set(re.findall(r"\w+", text.lower()))


products, queries, labels = load_products(), load_queries(), load_labels()
text_words = {product_id: words(text) for product_id, text in product_text(products).items()}
attribute_words = {product_id: words(text) for product_id, text in products["attributes"].items()}
query_words = {query_id: words(query) for query_id, query in queries["query"].items()}
pairs = list(zip(labels["query_id"], labels["product_id"]))
labels["in text"] = [query_words[query_id] <= text_words[product_id] for query_id, product_id in pairs]
labels["in text or attributes"] = [query_words[query_id] <= text_words[product_id] | attribute_words[product_id]
                                   for query_id, product_id in pairs]

matched = labels[labels["in text"]]
print(f"exact share of all judged pairs: {(labels['label'] == 'exact').mean():.3f}")
print(f"judged pairs whose text has every query word: {len(matched):,}")
for label in ["exact", "partial", "irrelevant"]:
    print(f"of them {label}: {(matched['label'] == label).mean():.3f}")

exact = labels[labels["label"] == "exact"]
print(f"exact pairs: {len(exact):,}")
print(f"exact pairs whose text misses a query word: {(~exact['in text']).sum():,}")
print(f"of them, still missing one with attributes added: {(~exact['in text or attributes']).sum():,}")

curtains = list(exact.loc[exact["query_id"] == 246, "product_id"])                 # clear shower curtain
unsaid = [product_id for product_id in curtains if "clear" not in text_words[product_id]]
print("exact products for clear shower curtain:", len(curtains))
print("of them without the word clear in their text:", len(unsaid))
print("of those, with clear in their attributes:", sum("clear" in attribute_words[product_id] for product_id in unsaid))
```

Output:

```text
exact share of all judged pairs: 0.249
judged pairs whose text has every query word: 1,177
of them exact: 0.777
of them partial: 0.211
of them irrelevant: 0.012
exact pairs: 3,252
exact pairs whose text misses a query word: 2,337
of them, still missing one with attributes added: 2,251
exact products for clear shower curtain: 12
of them without the word clear in their text: 8
of those, with clear in their attributes: 4
```

Of the 1,177 pairs with a full word match, 0.777 are exact, 0.211 partial and 0.012 irrelevant. A full match is a strong signal: over all judged pairs, the exact share is 0.249. But it doesn't settle the question: the words can be present without the product being what the shopper meant. If you predicted a share close to 1, you treated matching words as relevance. The judges didn't.

The other direction is more striking. Of the 3,252 exact pairs, 2,337 have a product text that misses at least one word of the query. Some misses are word forms and spelling, such as `chairs` against `chair` ([chapter 1](#search-end-to-end-in-production)), or the query `ligth bulb`; [chapter 5](#stem-word-forms) and [chapter 8](#correct-spelling-from-catalog) take those up. Others are attributes the text doesn't state. WANDS records attributes such as color, material and size apart from the text ([Chen et al., 2022, Table 1](https://easychair.org/publications/preprint/wm4R)), and the store keeps a few of them in an `attributes` column, for example `color: clear; material: vinyl` ([data card](https://github.com/rollingedition/book-primer-on-search-relevance/blob/d8bc0cbbe2485ee8945a1dd5960c81f99adca561/examples/data/wands/README.md)). The text that the store's search reads, `lib.store.product_text`, leaves that column out. Adding the attributes to the text leaves 2,251 of those exact pairs still missing a query word, so attributes explain few misses overall. For some queries, though, the attributes hold the answer. For `clear shower curtain`, 8 of the 12 exact products never say `clear` in their text, and 4 of those carry `clear` in their attributes, where the store's text search never looks. Chapter 5 tests adding them to lexical search ([Index product attributes as a field](#index-attributes-as-a-field)). For the other exact curtains, neither the text nor the attributes say `clear`. The judges had more to go on: WANDS's annotation guidelines show them each product's name, image and web page ([guidelines](https://github.com/wayfair/WANDS/raw/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/Product%20Search%20Relevance%20Annotation%20Guidelines.pdf)). The photo or the page may be what told them, but that is our guess: the data doesn't record which evidence a judge used.

**Working rule:** Treat a judgment as a person's verdict about a need, not a property of the product. Before you blame a ranker for missing an exact product, check whether any field the ranker reads says what the judges saw, and look at the fields it doesn't read, such as attributes. When your judges see more than your ranker does, give the ranker the same evidence where you can, or accept that some exact products will rank low for reasons no change to the ranking can fix.

## Expect judges to disagree on some pairs {#judges-disagree-on-some-pairs}

Because a judgment is a verdict, two people can reach different ones. Each WANDS label is already the majority vote of up to three annotators ([Chen et al., 2022, section 5](https://easychair.org/publications/preprint/wm4R)), and the annotators started with moderate agreement and converged with training. Cohen's kappa, a measure of agreement that discounts the agreement expected by chance, rose from 0.467 in their first two months to 0.664 in the third and 0.826 in the fourth (Table 2). [Chapter 4](#agreement-beyond-chance) computes kappa.

WANDS's file lists some of the store's pairs more than once, each row a majority vote, and for a few the votes differ. The store's sample keeps one row per pair, graded 2 for exact, 1 for partial and 0 for irrelevant, and where the rows differ it keeps the lower grade ([Load the store's data](#store-data)). List the pairs whose rows differ:

Example `conflicting-judgments` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.6:

```python
import pandas as pd

from lib.store import DATA, load_labels, load_products, load_queries

GRADES = {"exact": 2, "partial": 1, "irrelevant": 0}

products, queries, labels = load_products(), load_queries(), load_labels()
conflicts = pd.read_csv(DATA / "label_conflicts.csv")       # pairs WANDS lists more than once, with different labels
kept = labels.set_index(["query_id", "product_id"])["label"]

for row in conflicts.itertuples():
    print(f"{queries.at[row.query_id, 'query']:<32} {products.at[row.product_id, 'name'][:40]:<41} "
          f"{row.labels:<19} kept: {kept[(row.query_id, row.product_id)]}")

pairs = conflicts["labels"].str.split("|")
spread = pairs.apply(lambda both: max(GRADES[label] for label in both) - min(GRADES[label] for label in both))
print()
print("pairs with conflicting labels:", len(conflicts))
print("exact against partial:", (pairs.apply(frozenset) == frozenset(["exact", "partial"])).sum())
print("partial against irrelevant:", (pairs.apply(frozenset) == frozenset(["partial", "irrelevant"])).sum())
print(f"conflicts between neighbouring grades: {(spread == 1).sum()} of {len(conflicts)}")
```

Output:

```text
whimsical solar lights           solar powered led pathway light pack      exact|partial       kept: partial
indoor multi tiered plant stand  taranto multi-tiered plant stand          exact|partial       kept: partial
clear shower curtain             shower curtain hooks                      irrelevant|partial  kept: irrelevant
breakfast bar table              counter height dining table               exact|partial       kept: partial
wood floor protector mat         hard floor straight rectangular chair ma  exact|partial       kept: partial
malachi sled                     sled coffee table                         irrelevant|partial  kept: irrelevant
kohler purist brushed bronze     purist widespread bathroom faucet with d  exact|partial       kept: partial

pairs with conflicting labels: 7
exact against partial: 5
partial against irrelevant: 2
conflicts between neighbouring grades: 7 of 7
```

Of the judged pairs, 7 conflict: 5 are exact against partial and 2 partial against irrelevant. Of those conflicts, 7 of 7 sit between neighbouring grades. Whether a `counter height dining table` fully matches `breakfast bar table` is a fair question about a modifier, not a sign that one vote misread the task. Conflicts like these show where the line between grades is soft.

**Working rule:** Keep one grade per pair and write down the rule that chose it. We recommend the lower grade, as the sample does: it errs against the ranker that ranks the product, not in its favour. When judges disagree across two grades, exact against irrelevant, reread the guidelines with them, because they don't share a definition.

## Read intent as a product and its modifiers {#intent-in-product-search}

Every judgment starts from a reading of what the query asks for. A shopper's **intent** is what they want to do. A widely cited taxonomy of web search splits intent into navigational (reach a particular site), informational (find information) and transactional (do something on the web). Its author cautions that "there is no assumption here that this intent can be inferred with any certitude from the query" ([Broder, 2002](https://sigir.org/files/forum/F2002/broder.pdf)). Product search reshapes these kinds. In product search, Tsagkias et al. write, navigational queries are "product serial numbers or names", and informational queries "typically map to a leaf in the inventory taxonomy or seek information about specific product attributes". They add that "there is no single taxonomy for eCommerce customer intent", because it depends on the store's business and inventory ([Tsagkias et al., 2020, section 2](https://sigir.org/wp-content/uploads/2020/06/p04.pdf)).

WANDS writes intent into its labels. A query names a *target entity*, the kind of product, plus *modifiers*, the attributes the shopper asked for. Exact satisfies both. Partial "only matches the target entity of the query, but does not satisfy the modifiers" ([Chen et al., 2022, section 3.2](https://easychair.org/publications/preprint/wm4R)). The guidelines' worked example is a query for a kids' chair: "The product is a chair but not for kids", so it is partial ([guidelines](https://github.com/wayfair/WANDS/raw/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/Product%20Search%20Relevance%20Annotation%20Guidelines.pdf)). Even with that rule, a broad query can be hard to judge: the authors' example is a shopper who wants an induction cooktop and types `cooktop` (Chen et al., section 1).

The store's queries cover the range. `ines shag rug w003096809` and `kohler whitehaven farmhouse kitchen sink` name a product line or a model, which makes them navigational. `outdoor light fixtures` names a category. `clear shower curtain` and `48 inch kitchen hood` add a modifier to an entity. The store's queries also carry `query_class`, WANDS's *predicted* class for each query (Chen et al., Table 1). It is a guess at the entity, says nothing about modifiers, and isn't a judgment. Check how often it agrees with the products the judges called exact:

Example `predicted-class-check` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.6:

```python
import pandas as pd

from lib.store import load_labels, load_products, load_queries

products, queries, labels = load_products(), load_queries(), load_labels()
exact = labels[labels["label"] == "exact"].join(products["product_class"], on="product_id")

rows = []
for query_id, group in exact.groupby("query_id"):
    predicted = queries.at[query_id, "query_class"]
    classes = group["product_class"].str.split("|")                 # a product can have several classes
    rows.append({"query": queries.at[query_id, "query"], "query_class": predicted,
                 "share of exact products in it": classes.apply(lambda names: predicted in names).mean(),
                 "commonest class of exact products": group["product_class"].value_counts().index[0] or "(none)"})
check = pd.DataFrame(rows)

print("queries:", len(check))
print("queries without a query_class:", check["query_class"].isna().sum())
print("queries where most exact products have the query_class:",
      (check["share of exact products in it"] > 0.5).sum())
missed = check[(check["share of exact products in it"] == 0) & check["query_class"].notna()]
print("queries where no exact product has the query_class:", len(missed))
print()
print(missed.drop(columns="share of exact products in it").to_string(index=False))
```

Output:

```text
queries: 80
queries without a query_class: 1
queries where most exact products have the query_class: 63
queries where no exact product has the query_class: 6

                   query               query_class commonest class of exact products
foutains with brick look                 Wallpaper                         Fountains
  70s inspired furniture                  Wall Art                            (none)
         7qt slow cooker Crock Pots & Slow Cookers                      Slow Cookers
 sheffield home bath set          Bath Rugs & Mats                          Vanities
      luau string lights             String Lights                  Holiday Lighting
             rustic twig     Faux Plants and Trees             Wall & Accent Mirrors
```

For 63 of the 80 queries, most exact products carry the predicted class. For 6, none does, and 1 query has no class at all. Read the queries the example lists before you count them as errors. `foutains with brick look` is classed as `Wallpaper`, while its exact products are fountains: the classifier went wrong. `7qt slow cooker` is a naming mismatch instead: the query classes and the product classes use different names for the same thing.

**Working rule:** Read each query as an entity plus modifiers, and check that your ranker gets the entity right before you tune it for modifiers. Use `query_class` as a hint, for a feature or a filter you check against the judgments, and never as a label. When intent is ambiguous, as with `cooktop`, judge against the guidelines' reading and write that reading down.

## Grade relevance instead of yes or no {#graded-relevance}

A binary label says relevant or not. A graded label, such as WANDS's exact, partial or irrelevant, says how relevant. The case for grades is that results differ in how useful they are: "Since all documents are not of equal relevance to their users, highly relevant documents should be identified and ranked first for presentation" ([Järvelin and Kekäläinen, 2002](https://www.fi.muni.cz/~xkohout7/Research/clanky_cizi/evaluation/p422-jarvelin.pdf)). In a store, a near miss is often a fair second choice. A shower curtain that isn't clear, which WANDS grades partial because it is the right kind of product without the attribute asked for ([Read intent as a product and its modifiers](#intent-in-product-search)), is closer to what the shopper wanted than a shower curtain hook. Binary labels force one line through the grades: count only exact as relevant, and the near miss is worth as little as the hook; count exact and partial, and it is worth as much as the clear curtain.

Show both failures on the store's query `clear shower curtain`. The example builds three top-10 rankings from the query's judgments: ten exact products, ten shower curtains judged partial, and ten shower curtain hooks judged irrelevant. It scores each with nDCG@10 ([Score one ranking](#score-one-ranking)) under three labelings: binary with exact as relevant, binary with exact or partial as relevant, and the book's grades, 2 for exact, 1 for partial and 0 for irrelevant, used as gains. A **gain** is what a result at a given position adds to the score before the position discount.

Example `binary-labels-hide-partial` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.6:

```python
from lib.metrics import ndcg_at_k
from lib.store import load_products, qrels

classes = load_products()["product_class"]
judgments = qrels()[246]                                     # clear shower curtain: {product_id: grade}


def first_ten(grade, product_class=None):
    """Ten products judged with this grade for the query, in product_id order."""
    return [product_id for product_id in sorted(judgments) if judgments[product_id] == grade
            and product_class in (None, classes[product_id])][:10]


rankings = {"clear curtains": first_ten(2),                                   # exact
            "other curtains": first_ten(1, "Shower Curtains"),               # partial: not clear
            "hooks": first_ten(0, "Shower Curtain Hooks and Accessories")}   # irrelevant
labelings = {"exact only": {2: 1, 1: 0, 0: 0},              # binary: relevant means exact
             "exact or partial": {2: 1, 1: 1, 0: 0},        # binary: relevant means exact or partial
             "grades": {2: 2, 1: 1, 0: 0}}                  # graded: the book's grades as gains

print("exact products for this query:", sum(grade == 2 for grade in judgments.values()))
print("exact products in the ideal top 10:", sorted(judgments.values(), reverse=True)[:10].count(2))
for labeling, gain in labelings.items():
    gains = {product_id: gain[grade] for product_id, grade in judgments.items()}
    for name, ranking in rankings.items():
        print(f"{name}, {labeling}: {ndcg_at_k(ranking, gains, 10):.3f}")
```

Output:

```text
exact products for this query: 12
exact products in the ideal top 10: 10
clear curtains, exact only: 1.000
other curtains, exact only: 0.000
hooks, exact only: 0.000
clear curtains, exact or partial: 1.000
other curtains, exact or partial: 1.000
hooks, exact or partial: 0.000
clear curtains, grades: 1.000
other curtains, grades: 0.500
hooks, grades: 0.000
```

With exact-only labels, the other curtains and the hooks score the same, 0.000 and 0.000. With exact-or-partial labels, the other curtains score 1.000, the same as the clear ones at 1.000. Only the grades separate all three: 1.000, 0.500 and 0.000. When the ideal top 10 is all exact, as it is here with 10 exact products in it, a ranking of ten partial products scores the ratio of the partial gain to the exact gain.

**Working rule:** We recommend graded judgments for product search, so a metric can credit a near miss without mistaking it for a match. Collect grades even if you report a binary metric too: you can always collapse grades to yes or no, but not the reverse. Use binary labels when a near miss is worthless to the user, as when the query is a model number and only that model will do.

### Choose the gains on purpose {#gains-are-a-choice}

Grades are labels. Gains are what each label is worth in a metric, and that is a choice. This book uses each grade as its gain, so partial is worth half of exact. WANDS's own paper weights exact, partial and irrelevant as 1.0, 0.5 and 0 ([Chen et al., 2022, Table 3](https://easychair.org/publications/preprint/wm4R)), the same ratio and so the same nDCG. The Shopping Queries Dataset, known as ESCI, with "130 thousand unique queries and 2.6 million manually labeled (query,product) relevance judgements", grades differently. It separates a *substitute*, an item that "can be used as a functional substitute (e.g., fleece for a 'sweater' query)", from a *complement*, an item that "could be used in combination with an exact item", and sets "gain values of 1.0, 0.1, 0.01, and 0.0" for exact, substitute, complement and irrelevant ([Reddy et al., 2022, section 3.1](https://arxiv.org/abs/2206.06588)). WANDS's partial isn't the same as ESCI's substitute, but it is the nearest equivalent.

Score the store's two test runs from chapter 1, [BM25](#rank-with-bm25)'s and semantic retrieval's rankings for every test query, under four schemes: the two binary labelings from [Grade relevance instead of yes or no](#graded-relevance), the book's grades, and a partial gain of 0.1 in the spirit of ESCI. The example also runs [chapter 3's permutation test](#permutation-test-on-queries) and [paired t-test](#paired-t-test-on-queries) on semantic retrieval's lead under each scheme, and prints both p-values. They are exploratory, so they describe each lead and establish none ([the book's rule](#when-a-difference-is-established)). The semantic run reads the recorded embeddings of the open model `Snowflake/snowflake-arctic-embed-m-v1.5` ([Search by meaning](#search-by-meaning)).

Example `gain-choice-changes-ndcg` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(load_products()).run(queries, k=100), "semantic": SemanticSearch().run(queries, k=100)}

for name, run in runs.items():
    grades = [judgments[query_id].get(product_id) for query_id, ranking in run.items() for product_id in ranking[:10]]
    print(f"partial share of the {name} top 10: {grades.count(1) / len(grades):.3f}")

schemes = {"exact only": {2: 1, 1: 0, 0: 0},
           "exact or partial": {2: 1, 1: 1, 0: 0},
           "grades 2, 1, 0": {2: 2, 1: 1, 0: 0},       # the book's choice; WANDS's 1, 0.5, 0 gives the same nDCG
           "partial gain 0.1": {2: 1, 1: 0.1, 0: 0}}   # close to the gains ESCI chose for its substitutes
leads = 0
for scheme, gain in schemes.items():
    gains = {query_id: {product_id: gain[grade] for product_id, grade in per_query.items()}
             for query_id, per_query in judgments.items()}
    scores = {name: evaluate(run, gains)["ndcg@10"] for name, run in runs.items()}
    test = compare(scores["semantic"], scores["bm25"])  # exploratory paired tests (chapter 3): no planned comparisons
    print(f"bm25, {scheme}: {scores['bm25'].mean():.3f}")
    print(f"semantic, {scheme}: {scores['semantic'].mean():.3f}")
    print(f"semantic minus bm25, {scheme}: {test['mean difference']:.3f}")
    print(f"permutation p, {scheme}: {test['permutation p']:.3f}")
    print(f"t-test p, {scheme}: {test['t-test p']:.3f}")
    print(f"tied queries, {scheme}: {test['ties']}")
    leads += test["mean difference"] > 0
print(f"schemes where semantic leads: {leads} of {len(schemes)}")
```

Output:

```text
partial share of the bm25 top 10: 0.403
partial share of the semantic top 10: 0.380
bm25, exact only: 0.519
semantic, exact only: 0.648
semantic minus bm25, exact only: 0.130
permutation p, exact only: 0.000
t-test p, exact only: 0.002
tied queries, exact only: 3
bm25, exact or partial: 0.903
semantic, exact or partial: 0.983
semantic minus bm25, exact or partial: 0.080
permutation p, exact or partial: 0.010
t-test p, exact or partial: 0.026
tied queries, exact or partial: 19
bm25, grades 2, 1, 0: 0.725
semantic, grades 2, 1, 0: 0.830
semantic minus bm25, grades 2, 1, 0: 0.105
permutation p, grades 2, 1, 0: 0.001
t-test p, grades 2, 1, 0: 0.003
tied queries, grades 2, 1, 0: 2
bm25, partial gain 0.1: 0.564
semantic, partial gain 0.1: 0.688
semantic minus bm25, partial gain 0.1: 0.125
permutation p, partial gain 0.1: 0.000
t-test p, partial gain 0.1: 0.002
tied queries, partial gain 0.1: 2
schemes where semantic leads: 4 of 4
```

Partial products fill 0.403 of BM25's top-10 places and 0.380 of semantic retrieval's, so the partial gain moves both scores a long way. BM25 scores 0.519 with exact-only labels and 0.903 with exact-or-partial labels. With the ESCI-like partial gain of 0.1, BM25 scores 0.564 and semantic retrieval 0.688. Semantic retrieval leads under 4 of 4 schemes, but the size of the lead changes with the choice: 0.130 with exact-only labels, 0.125 with ESCI-like gains, 0.105 with the grades and 0.080 with exact-or-partial labels. The example doesn't test the differences between those leads, so on 30 test queries treat them as possibly noise. Exact-or-partial labels also saturate, so they separate the rankers on fewer queries: 19 test queries tie under them, against 2 under the grades.

**Working rule:** We recommend linear gains, the grades 2, 1 and 0, as a default for product search. Choose a lower partial gain when a near miss is worth little to your shoppers. Whatever you choose, fix it before you compare rankers, report it with every score, and never compare nDCG computed with different gains.

## Read the label mix of each query {#label-mix-per-query}

Gains set what each grade is worth, but not how many grades of each kind a query has. A judgment set isn't one population: each query has its own pool of judged products and its own mix of grades, and the mix decides what a perfect ranking looks like for that query. A broad query, one that names a category many products satisfy, has many exact products. A specific query, one with several modifiers, may have only a handful. An average over queries mixes these different problems, so read the mix before you average anything.

The store's queries aren't a random draw from WANDS. Each was chosen to have 60 to 300 judged products, at least 3 exact and 20 partial judgments, and a predicted class no other chosen query has ([data card](https://github.com/rollingedition/book-primer-on-search-relevance/blob/d8bc0cbbe2485ee8945a1dd5960c81f99adca561/examples/data/wands/README.md)). Those limits set the floor and the ceiling of the counts that follow, which describe the sample, not WANDS as a whole: queries outside the limits never reach the store. Count the labels for each of the 80 queries, and group the queries by their share of exact products:

Example `count-labels-per-query` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.6:

```python
import pandas as pd

from lib.store import load_labels, load_queries

queries, labels = load_queries(), load_labels()
counts = pd.crosstab(labels["query_id"], labels["label"])[["exact", "partial", "irrelevant"]]
shares = counts.div(counts.sum(axis=1), axis=0).join(queries[["query", "split"]])

print(f"partial share of all judgments: {(labels['label'] == 'partial').mean():.3f}")
print(f"median exact share: {shares['exact'].median():.3f}")
print(f"median irrelevant share: {shares['irrelevant'].median():.3f}")
for label, which in [("exact", "lowest"), ("exact", "highest"), ("irrelevant", "highest")]:
    query_id = shares[label].idxmin() if which == "lowest" else shares[label].idxmax()
    print(f"{which} {label} share: {shares.at[query_id, label]:.3f}")
    print(f"query with the {which} {label} share: {shares.at[query_id, 'query']}")
print("queries with no irrelevant judgment:", (counts["irrelevant"] == 0).sum())
print("fewest exact products for a query:", counts["exact"].min())
print("most exact products for a query:", counts["exact"].max())
few = counts["exact"] < 10
print("queries with fewer than 10 exact products:", few.sum())
print("test queries with fewer than 10 exact products:", (few & (shares["split"] == "test")).sum())

print("queries with an exact share of 0.1 or less:", (shares["exact"] <= 0.1).sum())
print()
print("exact share  queries")
bins = pd.cut(shares["exact"], [tenth / 10 for tenth in range(11)])     # no share is 0: each query has 3 or more exact
for interval, number in bins.value_counts(sort=False).items():
    print(f"{interval.left:.1f} to {interval.right:.1f}  {number:>3}  {'#' * number}".rstrip())
```

Output:

```text
partial share of all judgments: 0.610
median exact share: 0.207
median irrelevant share: 0.060
lowest exact share: 0.014
query with the lowest exact share: 48 in entry table with side by side drawer
highest exact share: 0.749
query with the highest exact share: outdoor light fixtures
highest irrelevant share: 0.776
query with the highest irrelevant share: podium with locking cabinet
queries with no irrelevant judgment: 9
fewest exact products for a query: 3
most exact products for a query: 193
queries with fewer than 10 exact products: 23
test queries with fewer than 10 exact products: 7
queries with an exact share of 0.1 or less: 29

exact share  queries
0.0 to 0.1   29  #############################
0.1 to 0.2   10  ##########
0.2 to 0.3   12  ############
0.3 to 0.4   11  ###########
0.4 to 0.5    9  #########
0.5 to 0.6    1  #
0.6 to 0.7    7  #######
0.7 to 0.8    1  #
0.8 to 0.9    0
0.9 to 1.0    0
```

Partial is the commonest label: 0.610 of all judgments. The likely reason is how WANDS gathered its candidates, which [Know where the judgments came from](#pooled-judgments) covers. The exact share varies widely from query to query. The output's histogram is tallest at the low end: 29 queries have an exact share of 0.1 or less. The share runs from 0.014 for `48 in entry table with side by side drawer` to 0.749 for `outdoor light fixtures`, with a median of 0.207. The irrelevant share has a median of 0.060 but reaches 0.776 for `podium with locking cabinet`, and 9 queries have no irrelevant judgment at all. The number of exact products per query runs from 3, the sampling rule's floor, to 193.

That spread changes what nDCG@10 ([Score one ranking](#score-one-ranking)) measures. Of the queries, 23 have fewer than 10 exact products, 7 of them test queries. For those, the ideal top 10 includes partial products, so a ranking can reach a perfect 1 with partial products in its top 10. For a broad query such as `outdoor light fixtures`, a perfect score needs ten exact products. The same nDCG@10 means a different thing for each.

**Working rule:** Print the label mix per query before you average any metric, and look at both ends. Read a low score on a query with few exact products as a different problem from a low score on a broad query. Keep per-query scores next to every mean; [chapter 3](#read-per-query-differences) shows what averages hide.

## Treat clicks as biased evidence {#clicks-are-not-judgments}

A store logs every click, and clicks cost nothing to collect, so they look like free judgments. They aren't. A click says that a shopper chose to look at a product. It doesn't say the product met the need, and whether the shopper clicks at all depends on where and how the product was shown.

The evidence on how clicks mislead comes from web search. In a two-phase study, Joachims et al. tracked the eyes and clicks of Cornell undergraduates answering ten set questions with Google: 34 in the first phase, and 22 in the second, where some saw the top two results swapped or the whole list reversed. They concluded that "clicks are informative but biased" ([Joachims et al., 2005](https://www.cs.cornell.edu/people/tj/publications/joachims_etal_05a.pdf)). The first bias is **position bias**: people click higher-ranked results more, partly because they trust the ranking. The authors call it "a 'trust bias' which leads to more clicks on links ranked highly by Google, even if those abstracts are less relevant than other abstracts the user viewed". They also found that relative preferences, such as a clicked result over a skipped one above it, "are reasonably accurate on average". In a large experiment that reordered results on a web search engine, Craswell et al. found that a **cascade model** best explained position bias in the top ranks: users "view results from top to bottom" and leave at the first worthwhile document ([Craswell et al., 2008](https://www.microsoft.com/en-us/research/?p=156688)). **Presentation bias** goes beyond position. On a portion of Google's web search traffic, results with more attractive titles, meaning more of the query's words in bold, drew more clicks, even after controlling for position and for relevance as judged by people ([Yue et al., 2010](https://archives.iw3c2.org/www2010/proceedings/www/p1011.pdf)). In a store, images and prices are the nearest analogue to titles. That is our inference, not a measured result.

WANDS has no click data, so the store can't measure these biases. You can still see what a click log would record. Take the store's judgments for `clear shower curtain`, and apply the cascade model in its strictest form: a shopper reads from the top, clicks the first exact product and leaves. This is a thought experiment with one fixed rule, not a model of real shoppers; [chapter 11](#simulate-interleaving-with-clicks) simulates clicks with probabilities.

Example `cascade-clicks` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, qrels

products = load_products()
judgments = qrels()[246]                                     # clear shower curtain: {product_id: grade}
rankings = {"bm25": list(LexicalSearch(products).search("clear shower curtain", k=10).index),
            "semantic": list(SemanticSearch().search(246, k=10).index)}

for name, ranking in rankings.items():
    grades = [judgments.get(product_id, 0) for product_id in ranking]
    rank = grades.index(2) + 1             # cascade: read from the top, click the first exact product, stop
    print(f"{name} grades, ranks 1 to 10: {' '.join(map(str, grades))}")
    print(f"{name} clicked rank: {rank}")
    print(f"{name} clicked product: {products.at[ranking[rank - 1], 'name']}")
    print(f"{name} exact products shown below the click: {grades[rank:].count(2)}")
```

Output:

```text
bm25 grades, ranks 1 to 10: 1 2 2 2 2 1 1 0 0 0
bm25 clicked rank: 2
bm25 clicked product: woolley vinyl single shower curtain
bm25 exact products shown below the click: 3
semantic grades, ranks 1 to 10: 2 2 1 1 2 1 2 2 1 1
semantic clicked rank: 1
semantic clicked product: woolley vinyl solid color single shower curtain
semantic exact products shown below the click: 4
```

Under [BM25](#rank-with-bm25)'s ranking, the shopper clicks rank 2, `woolley vinyl single shower curtain`, and never reaches the 3 exact products below it. In the click log, those exact products look the same as BM25's ranks 8 to 10, shower curtain hooks judged irrelevant ([Rank products with BM25](#rank-with-bm25)), which nobody clicked either. Under [semantic retrieval](#search-by-meaning)'s ranking, the click lands at rank 1, on `woolley vinyl solid color single shower curtain`. Two rankings from the same catalog produce two click logs that credit different products. A click log records what the ranker showed first as much as what the shopper wanted. WANDS's authors give the same reason, positional bias, for not building their dataset from logs ([Check the results against the judgments](#check-against-judgments)). Clicks still carry information. In WANDS, 62.47% of the candidates taken from click logs were judged exact, against 30.95% of those taken from open-source ranking systems ([Chen et al., 2022, Table 4](https://easychair.org/publications/preprint/wm4R)).

Correcting clicks for bias is a research field of its own, unbiased learning to rank. On a large search dataset released by Baidu, those methods improved click prediction but "struggle to consistently improve ranking performance" as judged by experts ([Hager et al., 2024](https://arxiv.org/abs/2404.02543)).

**Working rule:** Use judgments, not clicks, as the reference for offline evaluation. Use clicks as relative evidence, a clicked product over a skipped one ranked above it, and never read a missing click as a sign that a product is irrelevant. If you train on clicks, check the result against judgments.

## Know where the judgments came from {#pooled-judgments}

Nobody judges every product for every query. Test collections judge a **pool** instead. In TREC, the Text REtrieval Conference's shared evaluations, the pool for a topic is "the union of the set of X top-retrieved documents for that topic by each participant (where X is usually set at 100)", and every document outside it counts as not relevant. Voorhees argues that "retrieval systems can be compared fairly by assuming that all unjudged documents are not relevant", because pools hold enough of the relevant documents, and notes that pooling "cannot produce reusable test collections for arbitrarily large document sets" ([Voorhees, 2007](https://cs.uwaterloo.ca/~brecht/courses/854-Experimental-Performance-Evaluation-2017/readings/trec-cacm-2007.pdf)). Zobel tested the fairness claim: with pooled judgments, "the measured relative performance of systems appears to be reliable, but that recall is overestimated: it is likely that many relevant documents have not been found" ([Zobel, 1998](https://www.cs.cornell.edu/courses/cs574/2002fa/assignments.org/zobel-sigir98.pdf)).

WANDS built its pool in two steps ([Chen et al., 2022, sections 4.2 and 4.3](https://easychair.org/publications/preprint/wm4R)). The first took the products shoppers had clicked or added to their carts, plus the results of an open-source lexical search engine, Solr, and of a neural retrieval system. The second mined the whole catalog again with the same two systems, and added every product in the class that a query classification model predicted for the query. The second step produced most of WANDS's labels, and mostly near misses: 4.12% of its labels were exact and 63.99% partial (Table 5). Partial is the commonest label in the store's sample too ([Read the label mix](#label-mix-per-query)). The authors argue that completeness matters for product search, because "incompleteness in Product Search dataset does negatively impact the discriminative power of the evaluation" (section 3.1).

A pool belongs to a query. A product without a judgment for a query is **unjudged** for it, and a product judged for one query can be unjudged for a similar one. The store has two such queries: the train query `trundle daybed` and the test query `full bed with trundle`. Count the products judged exact for the first that have no judgment for the second, and see how the judges graded the ones that do:

Example `trundle-daybeds-unjudged` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.6:

```python
from collections import Counter

from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries(), qrels()
LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}

daybeds = sorted(product_id for product_id, grade in judgments[433].items() if grade == 2)
full_bed = judgments[436]                                    # {product_id: grade} for "full bed with trundle"
print(f"433: {queries.at[433, 'query']} ({queries.at[433, 'split']})")
print(f"436: {queries.at[436, 'query']} ({queries.at[436, 'split']})")
print("exact for trundle daybed:", len(daybeds))

unjudged = [product_id for product_id in daybeds if product_id not in full_bed]
print("of them unjudged for full bed with trundle:", len(unjudged))
print("of them judged for full bed with trundle:", len(daybeds) - len(unjudged))
judged = Counter(LABELS[full_bed[product_id]] for product_id in daybeds if product_id in full_bed)
for label in LABELS.values():
    print(f"judged {label}: {judged[label]}")

print("first unjudged daybed:", products.at[unjudged[0], "name"])
print("second unjudged daybed:", products.at[unjudged[1], "name"])
```

Output:

```text
433: trundle daybed (train)
436: full bed with trundle (test)
exact for trundle daybed: 113
of them unjudged for full bed with trundle: 77
of them judged for full bed with trundle: 36
judged exact: 5
judged partial: 31
judged irrelevant: 0
first unjudged daybed: daybed with trundle
second unjudged daybed: pattonsburg daybed with trundle
```

Of the 113 products judged exact for `trundle daybed`, 77 have no judgment for `full bed with trundle`, among them `daybed with trundle` and `pattonsburg daybed with trundle`. Of the 36 that do, the judges called 5 exact, 31 partial and 0 irrelevant. By our reading of the guidelines' rule, a daybed with a trundle is often the right kind of bed without the size the query asks for. If the unjudged daybeds resemble the judged ones, most of them would be partial too, yet a metric gives each one grade 0.

Zobel warns that pooled judgments can "underestimate the performance of systems that did not contribute to the pool" (Zobel, 1998). That makes judgments fairest to rankers like the systems that built the pool: for WANDS, shoppers' clicks, a lexical engine, a neural retriever and a query classifier. It is a tendency, not a law. In the store, BM25, the ranker most like WANDS's lexical engine, has the lower judged@10 of the two rankers ([Count unjudged products](#unjudged-results)). Our guess is that the store's BM25 reads different fields than the pool's engine did, so it ranks different products high.

**Working rule:** Find out where your pool came from before you trust a comparison. When you evaluate a ranker unlike the systems that built it, expect it to surface products nobody judged, and plan to judge them.

## Count unjudged products before you compare scores {#unjudged-results}

A product nobody judged for a query is [unjudged](#pooled-judgments): its grade is unknown, not 0. Standard metrics can't tell the difference. They "make no distinction in pooled collections between documents that are explicitly judged as nonrelevant and documents that are assumed to be nonrelevant because they are unjudged", and they become unreliable when judgments are very incomplete ([Buckley and Voorhees, 2004](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=150469)). Two diagnostics are standard in evaluation tools ([ir-measures](https://ir-measur.es/en/latest/measures.html)). **Judged@k** is the share of the top k that has a judgment of any grade:

```text
judged@k = (number of the top k products that have a judgment for the query) / k
```

The second drops the unjudged products before scoring, so the judged ones move up: ir-measures offers it as the `judged_only` option, and we call the result a **condensed** list. Buckley and Voorhees's bpref measure works in the same spirit: it uses judged documents only, and they found it more robust to incomplete judgments.

In [chapter 1](#score-every-test-query), [BM25](#rank-with-bm25)'s mean judged@10 on the test queries is 0.927, against 0.990 for [semantic retrieval](#search-by-meaning). One property of the store's data keeps those numbers high: its catalog is almost all judged products, 11,917 of 12,000 judged for at least one query ([Load the store's data](#store-data)). Expect a full catalog to put more unjudged products in the top 10s. Build judged@10 by hand, check it against `lib.metrics`, and list where BM25's unjudged products are:

Example `unjudged-in-bm25-top-10` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
run = LexicalSearch(products).run(queries, k=100)


def judged_at_k(ranking, judged, k):
    """The share of the top k that has a judgment of any grade."""
    return sum(product_id in judged for product_id in ranking[:k]) / k


rows = []
for query_id, ranking in run.items():
    unjudged = [product_id for product_id in ranking[:10] if product_id not in judgments[query_id]]
    rows.append({"query": queries.at[query_id, "query"], "judged@10": judged_at_k(ranking, judgments[query_id], 10),
                 "unjudged": len(unjudged), "first unjudged product": products.at[unjudged[0], "name"][:45] if unjudged else ""})
table = pd.DataFrame(rows)

print(f"mean judged@10: {table['judged@10'].mean():.3f}")
library = evaluate(run, judgments)["judged@10"]
agree = sum(abs(row["judged@10"] - library[query_id]) < 1e-12 for query_id, row in zip(run, rows))
print(f"queries where the hand-built judged@10 equals lib.metrics: {agree} of {len(rows)}")
print("unjudged products in the top 10s:", table["unjudged"].sum())
print("test queries with an unjudged product in the top 10:", (table["judged@10"] < 1).sum())
sleeper = list(judgments[244].values())                      # pull out sleeper loveseat
print("judgments for pull out sleeper loveseat:", len(sleeper))
print("irrelevant judgments for pull out sleeper loveseat:", sleeper.count(0))
print()
print(table[table["judged@10"] < 1].sort_values("judged@10").to_string(index=False))
```

Output:

```text
mean judged@10: 0.927
queries where the hand-built judged@10 equals lib.metrics: 30 of 30
unjudged products in the top 10s: 22
test queries with an unjudged product in the top 10: 7
judgments for pull out sleeper loveseat: 143
irrelevant judgments for pull out sleeper loveseat: 0

                    query  judged@10  unjudged                        first unjudged product
   outdoor light fixtures        0.2         8  60 watt equivalent e12 led candle light bulb
     beach blue headboard        0.5         5 lemon frosting indoor/outdoor , removable cov
pull out sleeper loveseat        0.6         4    country oxford 87.75 '' rolled arm sleeper
    full bed with trundle        0.8         2 abel staircase twin over full bunk bed with t
   whimsical solar lights        0.9         1 luciole 0.12-watt led solar power dusk to daw
  bistro table and chairs        0.9         1              drayton patio 5 piece bistro set
     wooden chair outdoor        0.9         1 osterley 31.5 '' w writing desk and chair set
```

The hand-built judged@10 equals `lib.metrics` on 30 of 30 test queries, with a mean of 0.927. Unjudged products fill 22 of BM25's top-10 places, spread over 7 queries. By our reading, some are plainly irrelevant: light bulbs for `outdoor light fixtures`, an outdoor pillow for `beach blue headboard`. Others look like near misses or matches: a bunk bed with a trundle for `full bed with trundle`, a bistro set for `bistro table and chairs`, a sleeper sofa for `pull out sleeper loveseat`, which by the entity-and-modifier rule is probably a near miss. For that last query, 0 of the 143 judged products are irrelevant. Now score both rankers with condensed lists:

Example `condensed-ndcg` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(load_products()).run(queries, k=100), "semantic": SemanticSearch().run(queries, k=100)}

standard, condensed = {}, {}
for name, run in runs.items():
    # condensed: drop every unjudged product, so the judged ones move up into the top 10
    judged_only = {query_id: [product_id for product_id in ranking if product_id in judgments[query_id]]
                   for query_id, ranking in run.items()}
    standard[name] = evaluate(run, judgments)["ndcg@10"]
    condensed[name] = evaluate(judged_only, judgments)["ndcg@10"]
    print(f"{name} ndcg@10: {standard[name].mean():.3f}")
    print(f"{name} condensed ndcg@10: {condensed[name].mean():.3f}")

gain = condensed["bm25"] - standard["bm25"]                   # bm25's change, per test query
print(f"bm25 ndcg@10 for outdoor light fixtures: {standard['bm25'][133]:.3f}")
print(f"bm25 condensed ndcg@10 for outdoor light fixtures: {condensed['bm25'][133]:.3f}")
print(f"share of bm25's gain from outdoor light fixtures and beach blue headboard: {gain[[133, 46]].sum() / gain.sum():.3f}")

lead, condensed_lead = standard["semantic"] - standard["bm25"], condensed["semantic"] - condensed["bm25"]
change = compare(condensed_lead, lead)                       # is the change in the lead more than noise? (exploratory)
print(f"semantic minus bm25: {lead.mean():.3f}")
print(f"semantic minus bm25, condensed: {condensed_lead.mean():.3f}")
print(f"change in the lead: {change['mean difference']:.3f}")
print(f"95% interval for the change: {change['ci low']:.3f} to {change['ci high']:.3f}")
print(f"t-test p for the change: {change['t-test p']:.3f}")
print(f"permutation p for the change: {change['permutation p']:.3f}")
condensed_test = compare(condensed["semantic"], condensed["bm25"])   # the condensed lead itself (exploratory)
print(f"t-test p for the condensed lead: {condensed_test['t-test p']:.3f}")
print(f"permutation p for the condensed lead: {condensed_test['permutation p']:.3f}")
```

Output:

```text
bm25 ndcg@10: 0.725
bm25 condensed ndcg@10: 0.778
semantic ndcg@10: 0.830
semantic condensed ndcg@10: 0.834
bm25 ndcg@10 for outdoor light fixtures: 0.286
bm25 condensed ndcg@10 for outdoor light fixtures: 1.000
share of bm25's gain from outdoor light fixtures and beach blue headboard: 0.612
semantic minus bm25: 0.105
semantic minus bm25, condensed: 0.056
change in the lead: -0.049
95% interval for the change: -0.138 to -0.015
t-test p for the change: 0.073
permutation p for the change: 0.036
t-test p for the condensed lead: 0.011
permutation p for the condensed lead: 0.009
```

Condensed, BM25 goes from 0.725 to 0.778 and semantic retrieval from 0.830 to 0.834, so semantic retrieval's lead goes from 0.105 to 0.056. Of BM25's gain, a share of 0.612 comes from the two queries whose unjudged products are plainly irrelevant, `outdoor light fixtures` and `beach blue headboard`. For `outdoor light fixtures`, BM25 goes from 0.286 to 1.000: once the bulbs drop out, the judged lights below them move up. So much of BM25's gain comes from forgiving bad results, not from undoing a penalty on good ones.

Whether the change in the lead is more than noise is unsettled, and both checks here are exploratory, so neither establishes anything ([the book's rule](#when-a-difference-is-established)). For the change, [chapter 3's paired t-test](#paired-t-test-on-queries) gives p = 0.073, its [permutation test](#permutation-test-on-queries) gives 0.036, and the 95% [bootstrap interval](#report-the-size-of-a-gap) runs from -0.138 to -0.015. With the change carried by a few queries, treat it as possibly noise. For the condensed lead itself, the permutation test gives p = 0.009 and the t-test 0.011. Neither score is the truth. The standard score punishes unjudged products that may be good, and the condensed score hides unjudged products that are bad.

**Working rule:** Report judged@10 next to every nDCG@10, and compute condensed scores as a diagnostic, never as the headline. When two rankers' judged@10 differ, have the unjudged products in their top 10s judged before you compare them. That is the dependable cure, and on this sample it is a small job: 22 judgments for BM25's test run. On a full catalog, expect more.

## What goes wrong in production {#what-relevance-means-in-production}

**Judgments go stale.** A store's catalog and shoppers keep changing, and relevance depends on more than the query: Tsagkias et al. name user, time, query and context, and note that "The query jacket has a different set of relevant documents in winter than summer" ([Tsagkias et al., 2020, section 3.1.1](https://sigir.org/wp-content/uploads/2020/06/p04.pdf)). Products enter the catalog unjudged, and products that leave it stay in the judgment set. Track [judged@10](#unjudged-results) for your production ranker over time, and judge again when it falls.

**Click labels confirm the ranking you have.** A ranker trained on clicks logged under the current ranking learns that ranking's order along with the shoppers' preferences. Keep human judgments as the reference that clicks are checked against ([Treat clicks as biased evidence](#clicks-are-not-judgments)).

**Guidelines shape the judgments.** WANDS's annotators needed four months to reach near-perfect agreement ([Chen et al., 2022, Table 2](https://easychair.org/publications/preprint/wm4R)). Small choices in the guidelines shape the whole set. WANDS told annotators to "ignore the mis-spellings and proceed to annotate the example as-is" ([guidelines](https://github.com/wayfair/WANDS/raw/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/Product%20Search%20Relevance%20Annotation%20Guidelines.pdf)), so its judgments assume a reader who understands `ligth bulb`. A ranker that can't will score low on such queries, which is fair to the shopper. [Chapter 8](#correct-spelling-from-catalog) builds a spelling corrector and shows what it still gets wrong.

**Your ranker sees less than your judges.** The judges saw images and product pages. The store's rankers read text without the attributes ([chapter 5 tests adding them](#index-attributes-as-a-field)); any large language model (LLM) asked to judge from the same text sees the same. Some disagreement between such a system and the human judgments comes from that gap, not from the system. Check which fields hold the attributes your judges rewarded before you blame the ranker.

**Filling holes with a model still needs human judgments.** Gienapp et al. fine-tune a small classifier for each query on that query's human judgments and use it to judge the unjudged products. On TREC Robust04 and the TREC Deep Learning collections of 2019 and 2020, they report that "As little as 128 initial human judgments per topic suffice to improve the comparability of models", with more reliability than prompted LLM judges ([Gienapp et al., 2025](https://arxiv.org/abs/2510.04633)). Soboroff's advice on LLMs is blunter: "don't use LLMs to create relevance judgments for TREC-style evaluations" ([Soboroff, 2025](https://arxiv.org/abs/2409.15133)). [Chapter 4](#read-llm-error-direction) measures LLM judgments against the store's human ones before trusting them.

**Working rule:** Date your judgments, track judged@10 in production, and budget for judging again.

## Decisions this chapter made {#what-relevance-means-decisions}

Each choice below has a reason, and each is a default that later chapters keep unless a measurement on train queries says otherwise.

- **Human judgments are the reference.** Every headline score in this book is computed on them, including scores for rankers built with LLMs. Clicks are evidence about shoppers, biased by position and presentation, and never serve as labels.
- **Grades 2, 1 and 0 are the gains,** so partial is worth half of exact, the same ratio as WANDS's own 1.0, 0.5 and 0. Binary metrics count exact only, so **relevant** means exact unless a sentence says otherwise.
- **One grade per pair.** When WANDS lists a pair more than once with different labels, the sample keeps the lower grade, which errs against the ranker.
- **`query_class` is a hint,** never a label and never a measure of intent. Some of its values are wrong.
- **Unjudged counts as grade 0, with judged@10 beside every nDCG@10.** Condensed scores are a diagnostic only. The cure for unjudged products in a top 10 is to have them judged.
- **Rankers read the product text, not the attributes.** [Chapter 5](#index-attributes-as-a-field) tests adding them as a field and keeps them out of the BM25 text. The judges also saw images and product pages, so some exact products give a text-only ranker little to match.
- **Read any judgment, tune on train.** Reading test judgments changes no ranker; choosing a fix from them would.
