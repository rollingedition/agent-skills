---
title: "Glossary"
book: "A Primer on Search Relevance"
edition: "2026.11.10"
canonical: "https://rollingedition.com/primer-on-search-relevance/glossary"
---

# Glossary of *A Primer on Search Relevance*

The 184 terms this book defines, as Edition 2026.11.10 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/primer-on-search-relevance/glossary

## A/A test

an A/A test, in which both groups get the same system

- Also: A/A tests
- Defined in: [Run an A/B test](testing-changes.md#run-an-ab-test)
- Address: https://rollingedition.com/concepts/search-and-recommendation/aa-test

## A/B test

An A/B test, or controlled experiment, assigns users at random to the current system or to the change, and compares a metric chosen before the test starts

- Also: A/B tests, controlled experiment
- Defined in: [Run an A/B test](testing-changes.md#run-an-ab-test)
- Address: https://rollingedition.com/concepts/search-and-recommendation/ab-test

## agent

an agent, an LLM that runs the searches itself and decides how many to run

- Also: agents
- A kind of: large language model
- Defined in: [Retrieval for LLM applications](retrieval-for-llm-applications.md)
- Address: https://rollingedition.com/concepts/search-and-recommendation/agent

## agent loop

In the agent loop, the program runs each tool call, sends back the result, and the model decides what to do next.

- Defined in: [Read an agent's searches from its trace](retrieval-for-llm-applications.md#read-agent-searches)
- Address: https://rollingedition.com/concepts/search-and-recommendation/agent-loop

## approximate nearest-neighbour index

When exact search costs too much, an approximate nearest-neighbour (ANN) index skips most of its comparisons, and in return may miss some of the true nearest neighbours.

- Also: ANN, ANN index
- A kind of: nearest-neighbour search
- Contrasts with: exact search
- Defined in: [Trade recall for speed with HNSW](semantic-retrieval.md#hnsw-recall-for-speed)
- Address: https://rollingedition.com/concepts/search-and-recommendation/approximate-nearest-neighbour-index

## attribute

a catalog often keeps facts about a product as structured attributes, such as color: clear or material: glass

- Defined in: [Index product attributes as a field](lexical-retrieval.md#index-attributes-as-a-field)
- Address: https://rollingedition.com/concepts/search-and-recommendation/attribute

## attribution

attribution asks whether a cited source supports the statement it is attached to

- Defined in: [Check every citation against the context](retrieval-for-llm-applications.md#check-citations-against-context)
- Address: https://rollingedition.com/concepts/search-and-recommendation/attribution

## baseline

The ranker the store runs today is the baseline

- Contrasts with: candidate ranker
- Defined in: [Diff two runs query by query](testing-changes.md#diff-runs-per-query)
- Address: https://rollingedition.com/concepts/search-and-recommendation/baseline

## bi-encoder

Search uses the encoder as a bi-encoder: it encodes each product by itself, once, ahead of time, and each query by itself when the shopper types it.

- Contrasts with: cross-encoder
- Defined in: [Turn text into embeddings](semantic-retrieval.md#turn-text-into-embeddings)
- Address: https://rollingedition.com/concepts/search-and-recommendation/bi-encoder

## binary label

A binary label says relevant or not.

- Contrasts with: graded label
- Defined in: [Grade relevance instead of yes or no](what-relevance-means.md#graded-relevance)
- Address: https://rollingedition.com/concepts/search-and-recommendation/binary-label

## blend

blends, ways to fuse a lexical and a semantic ranking with a weight that sets how much each counts

- Kinds: convex combination
- Kinds: weighted RRF
- Defined in: [Hybrid retrieval](hybrid-retrieval.md)
- Address: https://rollingedition.com/concepts/search-and-recommendation/blend

## BM25

BM25 is a lexical scoring function with three parts.

- Computed from: term frequency
- Computed from: inverse document frequency
- Implemented by: bm25s 0.3.16
- Defined in: [Rank products with BM25](search-end-to-end.md#rank-with-bm25)
- Address: https://rollingedition.com/concepts/search-and-recommendation/bm25

## BM25F

Combining a term's weighted frequencies across fields before saturating the total is BM25F.

- Computed from: term frequency
- Defined in: [Weight the product name above the description](lexical-retrieval.md#weight-the-product-name)
- Address: https://rollingedition.com/concepts/search-and-recommendation/bm25f

## Bonferroni correction

The Bonferroni correction is a simple, conservative fix: when you test m hypotheses, test each at 0.05 divided by m

- Also: Bonferroni
- Defined in: [Decide in advance what counts as established](measuring-search.md#when-a-difference-is-established)
- Address: https://rollingedition.com/concepts/search-and-recommendation/bonferroni-correction

## boost

A boost adds a fixed amount to the scores of products in the predicted class, so that they move up without anything else being removed.

- Contrasts with: filter
- Defined in: [Boost the predicted class instead of filtering](understanding-queries.md#boost-predicted-class)
- Address: https://rollingedition.com/concepts/search-and-recommendation/boost

## bootstrap

The bootstrap builds a confidence interval by resampling.

- Comes before: percentile interval
- Implemented by: scipy 1.18.1
- Defined in: [Report how big the gap is](measuring-search.md#report-the-size-of-a-gap)
- Address: https://rollingedition.com/concepts/search-and-recommendation/bootstrap

## candidate

A ranker scores only candidates, the products a cheaper retrieval stage returns

- Also: candidates
- Defined in: [Describe each candidate with features](ranking.md#ranking-features)
- Address: https://rollingedition.com/concepts/search-and-recommendation/ranking-candidate

## candidate ranker

the ranker with the change is the candidate ranker

- Defined in: [Diff two runs query by query](testing-changes.md#diff-runs-per-query)
- Address: https://rollingedition.com/concepts/search-and-recommendation/candidate-ranker

## candidate set

The candidate set for a query is the union of BM25's top 100 and semantic retrieval's top 100

- Comes before: convex combination
- Defined in: [Normalize scores before you add them](hybrid-retrieval.md#normalize-scores-before-adding)
- Address: https://rollingedition.com/concepts/search-and-recommendation/candidate-set

## cascade model

In the cascade model, users read results from top to bottom and leave at the first worthwhile document

- Defined in: [Treat clicks as biased evidence](what-relevance-means.md#clicks-are-not-judgments)
- Address: https://rollingedition.com/concepts/search-and-recommendation/cascade-model

## chunking

chunking is the rule that cuts a document, such as a fixed number of tokens, sentences, paragraphs, or breaks chosen by meaning

- Defined in: [Choose the retrievable unit](retrieval-for-llm-applications.md#choose-the-retrievable-unit)
- Address: https://rollingedition.com/concepts/search-and-recommendation/chunking

## citation

A citation here is the ID an answer gives for a product it recommends.

- Also: citations
- Defined in: [Score each answer by the products it cites](retrieval-for-llm-applications.md#retrieval-bounds-the-answer)
- Address: https://rollingedition.com/concepts/search-and-recommendation/citation

## click model

A click model is a probabilistic model of how users scan and click a result list, used both to build metrics and to simulate users

- Also: click models
- Defined in: [Rehearse interleaving with simulated shoppers](testing-changes.md#simulate-interleaving-with-clicks)
- Address: https://rollingedition.com/concepts/search-and-recommendation/click-model

## Cohen's kappa

Cohen's kappa corrects the observed agreement for chance by comparing it with the agreement expected if each judge kept its own label shares but chose independently of the other.

- Also: kappa
- Formula: `kappa = (observed - expected) / (1 - expected)`
- Computed from: observed agreement
- Implemented by: scikit-learn 1.9.1
- Defined in: [Measure agreement beyond chance with kappa](judgments-from-people-and-llms.md#agreement-beyond-chance)
- Address: https://rollingedition.com/concepts/search-and-recommendation/cohens-kappa

## ColBERT

ColBERT encodes the query and the product separately, as an embedding model does, and compares them only at the end.

- Contrasts with: cross-encoder
- Defined in: [Match token by token with ColBERT](hybrid-retrieval.md#late-interaction-colbert)
- Address: https://rollingedition.com/concepts/search-and-recommendation/colbert

## concordant pair

A pair of systems is concordant when two orderings put it the same way round

- Also: concordant
- Contrasts with: discordant pair
- Defined in: [Check whether LLM grades order the rankers the same way](judgments-from-people-and-llms.md#system-order-human-versus-llm)
- Address: https://rollingedition.com/concepts/search-and-recommendation/concordant-pair

## condensed list

the condensed list, a ranking with its unjudged products dropped before scoring, so the judged ones move up

- Also: condensed
- Defined in: [Count unjudged products before you compare scores](what-relevance-means.md#unjudged-results)
- Address: https://rollingedition.com/concepts/search-and-recommendation/condensed-list

## confidence interval

A confidence interval is a range of plausible values for the true mean difference

- Defined in: [Report how big the gap is](measuring-search.md#report-the-size-of-a-gap)
- Address: https://rollingedition.com/concepts/search-and-recommendation/confidence-interval

## confusion matrix

A confusion matrix shows how two judges differ: a table of counts with one row for each of the store's grades and one column for each of the LLM's, both in the order exact, partial, irrelevant.

- Contrasts with: Cohen's kappa
- Defined in: [Read the direction of the LLM's errors](judgments-from-people-and-llms.md#read-llm-error-direction)
- Address: https://rollingedition.com/concepts/search-and-recommendation/confusion-matrix

## context

the retrieved text in a prompt is the context

- Part of: prompt
- Defined in: [Put retrieved products in the prompt](retrieval-for-llm-applications.md#put-retrieved-products-in-the-prompt)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/context

## context precision

Ragas's context precision is the rank-aware one of its context measures, the mean of precision@k over the positions that hold a relevant chunk

- Also: context precision@k
- Formula: `context precision@k = mean of precision@i over the positions i ≤ k that hold an exact product`
- Computed from: Precision at k
- Contrasts with: context recall
- Defined in: [Measure the context, then the answer](retrieval-for-llm-applications.md#measure-the-context)
- Address: https://rollingedition.com/concepts/search-and-recommendation/context-precision

## context recall

context recall is the share of a reference answer's claims that the context supports

- Also: context recall@k
- Formula: `context recall@k = (exact products in the top k) / (exact products judged for the query)`
- Defined in: [Measure the context, then the answer](retrieval-for-llm-applications.md#measure-the-context)
- Address: https://rollingedition.com/concepts/search-and-recommendation/context-recall

## context window

A model's context window is the most tokens it can read, a fixed number of the word pieces in its own vocabulary.

- Defined in: [Put retrieved products in the prompt](retrieval-for-llm-applications.md#put-retrieved-products-in-the-prompt)
- Address: https://rollingedition.com/concepts/search-and-recommendation/context-window

## control

The current system is the control

- Part of: A/B test
- Contrasts with: treatment
- Defined in: [Run an A/B test](testing-changes.md#run-an-ab-test)
- Address: https://rollingedition.com/concepts/search-and-recommendation/control

## conversational query rewriting

Conversational query rewriting turns a context-dependent question into a self-contained one with the same answer

- Defined in: [Turn a follow-up into a standalone query](understanding-queries.md#standalone-follow-ups)
- Address: https://rollingedition.com/concepts/search-and-recommendation/conversational-query-rewriting

## convex combination

A sum whose weights add up to 1 is a convex combination, or weighted sum.

- Also: weighted sum, CC
- Contrasts with: reciprocal rank fusion
- Defined in: [Normalize scores before you add them](hybrid-retrieval.md#normalize-scores-before-adding)
- Address: https://rollingedition.com/concepts/search-and-recommendation/convex-combination

## Cosine similarity

Cosine similarity is the cosine of the angle between two vectors: 1 when they point the same way, 0 at right angles and −1 when they point in opposite directions.

- Also: cosine
- Formula: `cosine(q, d) = dot(q, d) / (length(q) × length(d))`
- Computed from: dot product
- Implemented by: scikit-learn 1.9.1
- Defined in: [Compare embeddings with cosine similarity](semantic-retrieval.md#compare-with-cosine-similarity)
- Address: https://rollingedition.com/concepts/search-and-recommendation/cosine-similarity

## cross-encoder

One kind of reranking model is a cross-encoder, which reads the query and the product text together, as one input, and outputs one relevance score for the pair, scoring each pair independently

- A kind of: reranking
- Contrasts with: large language model
- Defined in: [Rerank the top 50 with a cross-encoder](search-end-to-end.md#rerank-with-cross-encoder)
- Address: https://rollingedition.com/concepts/search-and-recommendation/cross-encoder

## cross-validation

Choose the tree size by cross-validation on the train queries: split them into five folds, rank each fold with a model fitted on three others and stopped early on the fifth, and score every query once.

- Defined in: [Train LambdaMART with LightGBM](ranking.md#train-lambdamart)
- Address: https://rollingedition.com/concepts/search-and-recommendation/cross-validation

## dimension

Every text gets the same count of numbers, the embedding's dimension, whether it's a three-word query or a product's whole description.

- Part of: embedding
- Defined in: [Turn text into embeddings](semantic-retrieval.md#turn-text-into-embeddings)
- Address: https://rollingedition.com/concepts/search-and-recommendation/dimension

## discordant pair

A pair of systems is concordant when two orderings put it the same way round, and discordant when two orderings put it opposite ways round.

- Also: discordant
- Defined in: [Check whether LLM grades order the rankers the same way](judgments-from-people-and-llms.md#system-order-human-versus-llm)
- Address: https://rollingedition.com/concepts/search-and-recommendation/discordant-pair

## Discounted cumulative gain

Each result contributes its grade as a gain, shrunk by a discount that grows with its position, and the sum is the discounted cumulative gain (DCG).

- Also: DCG, DCG@k
- Formula: `DCG@k = sum over positions i from 1 to k of grade(i) / log2(i + 1)`
- Computed from: gain
- Defined in: [Build nDCG from discounted gains](measuring-search.md#build-ndcg-from-dcg)
- Address: https://rollingedition.com/concepts/search-and-recommendation/dcg

## distillation

Distillation trains a small model, the student, to imitate a large model, the teacher.

- Defined in: [Distill the cross-encoder into a small ranker](ranking.md#distill-the-cross-encoder)
- Address: https://rollingedition.com/concepts/search-and-recommendation/distillation

## distractor

Products that look right but aren't are distractors

- Also: distractors
- Defined in: [Score each answer by the products it cites](retrieval-for-llm-applications.md#retrieval-bounds-the-answer)
- Address: https://rollingedition.com/concepts/search-and-recommendation/distractor

## document frequency

The number of products in a term's postings is its document frequency

- Computed from: postings
- Defined in: [Build an inverted index](lexical-retrieval.md#build-an-inverted-index)
- Address: https://rollingedition.com/concepts/search-and-recommendation/document-frequency

## dot product

The dot product multiplies two vectors number by number and adds up the results, so it equals the cosine times both lengths.

- Formula: `dot(q, d) = q1 × d1 + q2 × d2 + ... + qn × dn`
- Defined in: [Compare embeddings with cosine similarity](semantic-retrieval.md#compare-with-cosine-similarity)
- Address: https://rollingedition.com/concepts/search-and-recommendation/dot-product

## early stopping

Early stopping scores held-out train queries after every tree, and keeps the trees up to the best score once 30 more bring no gain.

- Defined in: [Train LambdaMART with LightGBM](ranking.md#train-lambdamart)
- Address: https://rollingedition.com/concepts/search-and-recommendation/early-stopping

## edit distance

The number of insertions, deletions and replacements that turn one string into another is their edit distance

- Comes before: noisy channel model
- Defined in: [Correct spelling against the catalog's words](understanding-queries.md#correct-spelling-from-catalog)
- Address: https://rollingedition.com/concepts/search-and-recommendation/edit-distance

## effect size

The effect size of a paired comparison is the mean difference divided by the standard deviation of the differences

- Computed from: per-query differences
- Contrasts with: p-value
- Defined in: [Report how big the gap is](measuring-search.md#report-the-size-of-a-gap)
- Address: https://rollingedition.com/concepts/search-and-recommendation/effect-size

## embedding

An embedding is a list of numbers, a vector, that a neural network computes for a piece of text.

- Comes before: semantic retrieval
- Defined in: [Search by meaning with embeddings](search-end-to-end.md#search-by-meaning)
- Address: https://rollingedition.com/concepts/semantic-search/embedding

## encoder

The model that computes an embedding is an encoder, trained so that texts with similar meanings get vectors that point in similar directions, whether or not they share words.

- Comes before: bi-encoder
- Defined in: [Turn text into embeddings](semantic-retrieval.md#turn-text-into-embeddings)
- Address: https://rollingedition.com/concepts/search-and-recommendation/encoder

## evaluation harness

an evaluation harness, which holds everything fixed except the ranker: the same queries, judgments, metrics and tests, so that two runs differ only in their rankings

- Defined in: [Compare runs in an evaluation harness](measuring-search.md#compare-runs-in-a-harness)
- Address: https://rollingedition.com/concepts/search-and-recommendation/evaluation-harness

## exact search

Exact search compares the query with every product and keeps the best k, so it never misses one.

- A kind of: nearest-neighbour search
- Implemented by: numpy 2.5.5
- Implemented by: faiss-cpu 1.16.0
- Defined in: [Find the exact nearest neighbours with NumPy](semantic-retrieval.md#exact-nearest-neighbours-numpy)
- Address: https://rollingedition.com/concepts/search-and-recommendation/exact-search

## expansion terms

The nonzero terms of a SPLADE vector include expansion terms: words the text doesn't contain but the model weights anyway, so a product can match a query word it never uses.

- Part of: SPLADE
- Defined in: [Learn sparse term weights with SPLADE](hybrid-retrieval.md#learned-sparse-splade)
- Address: https://rollingedition.com/concepts/search-and-recommendation/expansion-terms

## Faithfulness

Faithfulness is the share of an answer's claims that the context supports.

- Also: faithful
- Defined in: [Check what the cited product supports](retrieval-for-llm-applications.md#check-citation-support)
- Address: https://rollingedition.com/concepts/search-and-recommendation/faithfulness

## feature

A learned ranker scores each pair of a query and a product from a list of numbers, its features, and learns from judgments how to weigh them.

- Also: features, ranking feature
- Comes before: learning to rank
- Defined in: [Describe each candidate with features](ranking.md#ranking-features)
- Address: https://rollingedition.com/concepts/search-and-recommendation/feature

## feature importance

Feature importance shows what a model learned: LightGBM's "gain" importance is the "total gains of splits which use the feature"

- Also: gain importance
- True for: lightgbm 4.7.0
- Implemented by: lightgbm 4.7.0
- Defined in: [Report LambdaMART on the test queries](ranking.md#lambdamart-on-test-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/feature-importance

## field

A product's text has parts, called fields

- Comes before: BM25F
- Defined in: [Weight the product name above the description](lexical-retrieval.md#weight-the-product-name)
- Address: https://rollingedition.com/concepts/search-and-recommendation/field

## filter

A filter keeps only products in the predicted class.

- Defined in: [Boost the predicted class instead of filtering](understanding-queries.md#boost-predicted-class)
- Address: https://rollingedition.com/concepts/search-and-recommendation/filter

## fusion

Combining rankings is called fusion.

- Defined in: [Find the queries each retriever wins](hybrid-retrieval.md#queries-each-retriever-wins)
- Address: https://rollingedition.com/concepts/search-and-recommendation/fusion

## gain

A gain is what a result at a given position adds to the score before the position discount.

- Also: gains
- Part of: Discounted cumulative gain
- Defined in: [Grade relevance instead of yes or no](what-relevance-means.md#graded-relevance)
- Address: https://rollingedition.com/concepts/search-evaluation/gain

## grade

a grade is the number that stands for a judgment's label.

- Defined in: [Load the store's data](search-end-to-end.md#store-data)
- Address: https://rollingedition.com/concepts/search-and-recommendation/grade

## graded label

A graded label, such as WANDS's exact, partial or irrelevant, says how relevant.

- Also: graded judgments
- Defined in: [Grade relevance instead of yes or no](what-relevance-means.md#graded-relevance)
- Address: https://rollingedition.com/concepts/search-and-recommendation/graded-label

## gradient-boosted trees

gradient-boosted trees, which add small decision trees one at a time, each fitted to the gradients of the trees before it

- Comes before: LambdaMART
- Defined in: [Learn a ranking from pairs of products](ranking.md#learn-from-pairs)
- Address: https://rollingedition.com/concepts/search-and-recommendation/gradient-boosted-trees

## Grounding

Grounding means that an answer rests on the context it was given, as the exact share assumes, not on what the model remembers or invents.

- Also: grounded
- Defined in: [Check every citation against the context](retrieval-for-llm-applications.md#check-citations-against-context)
- Address: https://rollingedition.com/concepts/search-and-recommendation/grounding

## HNSW

HNSW, short for hierarchical navigable small world, is a graph index.

- Also: hierarchical navigable small world
- A kind of: approximate nearest-neighbour index
- Implemented by: faiss-cpu 1.16.0
- Defined in: [Trade recall for speed with HNSW](semantic-retrieval.md#hnsw-recall-for-speed)
- Address: https://rollingedition.com/concepts/search-and-recommendation/hnsw

## hybrid retrieval

Hybrid retrieval combines the rankings of a lexical and a semantic retriever into one ranking.

- A kind of: fusion
- Defined in: [Find the queries each retriever wins](hybrid-retrieval.md#queries-each-retriever-wins)
- Address: https://rollingedition.com/concepts/search-and-recommendation/hybrid-retrieval

## HyDE

Where a rewrite asks the LLM for a better query, HyDE, short for hypothetical document embeddings, asks it for the document it imagines would answer the query.

- Also: hypothetical document embeddings
- Formula: `hyde(query) = (embedding(hypothetical product) + embedding(query)) / 2, then scaled to length 1`
- Contrasts with: query rewriting
- Computed from: hypothetical document
- Defined in: [Search with a hypothetical product (HyDE)](understanding-queries.md#hyde-hypothetical-products)
- Address: https://rollingedition.com/concepts/search-and-recommendation/hyde

## hypothetical document

hypothetical document, written by an LLM to answer the query

- Defined in: [Search with a hypothetical product (HyDE)](understanding-queries.md#hyde-hypothetical-products)
- Address: https://rollingedition.com/concepts/search-and-recommendation/hypothetical-document

## information need

The judge grades the product against the information need behind the query's words, the thing the shopper wanted, not against the words.

- Comes before: judgment
- Defined in: [Judge relevance against the shopper's need](what-relevance-means.md#relevance-is-a-judgment)
- Address: https://rollingedition.com/concepts/search-and-recommendation/information-need

## intent

A shopper's intent is what they want to do.

- Defined in: [Read intent as a product and its modifiers](what-relevance-means.md#intent-in-product-search)
- Address: https://rollingedition.com/concepts/search-and-recommendation/intent

## Interleaving

Interleaving shows each shopper one list that mixes two rankers' results.

- Contrasts with: A/B test
- Defined in: [Interleave two rankings with team draft](testing-changes.md#team-draft-interleaving)
- Address: https://rollingedition.com/concepts/search-and-recommendation/interleaving

## inverse document frequency

the inverse document frequency, IDF: the logarithm of the number of products divided by the term's document frequency, high for a rare term and low for a common one

- Also: IDF
- Formula: `idf(t) = ln(N / df(t))`
- Computed from: document frequency
- Defined in: [Weight terms with TF-IDF](lexical-retrieval.md#weight-terms-with-tf-idf)
- Address: https://rollingedition.com/concepts/search-and-recommendation/inverse-document-frequency

## inverted index

An inverted index turns the texts around: for each term, it keeps the list of products that contain the term

- Defined in: [Build an inverted index](lexical-retrieval.md#build-an-inverted-index)
- Address: https://rollingedition.com/concepts/search-and-recommendation/inverted-index

## judge

This chapter calls whoever gives a judgment, person or LLM, a judge

- Defined in: [Write judging guidelines](judgments-from-people-and-llms.md#write-judging-guidelines)
- Address: https://rollingedition.com/concepts/search-and-recommendation/judge

## Judged@k

Judged@k is the share of the top k that has a judgment of any grade

- Also: judged@10
- Formula: `judged@k = (number of the top k products that have a judgment for the query) / k`
- Measured from: judgment
- Defined in: [Count unjudged products before you compare scores](what-relevance-means.md#unjudged-results)
- Address: https://rollingedition.com/concepts/search-and-recommendation/judged-at-k

## Judging guidelines

Judging guidelines say what each grade means, how to choose between grades, and what to do with the cases that fall between them.

- Defined in: [Write judging guidelines](judgments-from-people-and-llms.md#write-judging-guidelines)
- Address: https://rollingedition.com/concepts/search-and-recommendation/judging-guidelines

## judgment

A judgment is a person's label for one pair of a query and a product

- Comes before: grade
- Defined in: [Load the store's data](search-end-to-end.md#store-data)
- Address: https://rollingedition.com/concepts/search-and-recommendation/judgment

## Kendall's tau

Tau is concordant pairs minus discordant pairs, divided by all pairs, from 1 for the same order to −1 for the reverse.

- Also: tau
- Computed from: concordant pair
- Computed from: discordant pair
- Implemented by: scipy 1.18.1
- Defined in: [Check whether LLM grades order the rankers the same way](judgments-from-people-and-llms.md#system-order-human-versus-llm)
- Address: https://rollingedition.com/concepts/search-and-recommendation/kendalls-tau

## LambdaMART

LambdaMART uses LambdaRank's λ as the gradients for gradient-boosted trees

- A kind of: learning to rank
- Contrasts with: pointwise model
- Implemented by: lightgbm 4.7.0
- Defined in: [Learn a ranking from pairs of products](ranking.md#learn-from-pairs)
- Address: https://rollingedition.com/concepts/search-and-recommendation/lambdamart

## large language model

An LLM is a model trained on large amounts of text to generate text in response to a prompt.

- Also: LLM
- Defined in: [Rerank the top 50 with a cross-encoder](search-end-to-end.md#rerank-with-cross-encoder)
- Address: https://rollingedition.com/concepts/search-and-recommendation/large-language-model

## late interaction

Late interaction keeps one vector per token instead of one per text, so it is also called multi-vector retrieval.

- Also: multi-vector retrieval
- Kinds: ColBERT
- Defined in: [Match token by token with ColBERT](hybrid-retrieval.md#late-interaction-colbert)
- Address: https://rollingedition.com/concepts/search-and-recommendation/late-interaction

## learned sparse retrieval

Learned sparse retrieval keeps BM25's machinery, an inverted index of terms, but has a neural model choose each product's terms and their weights.

- Kinds: SPLADE
- Defined in: [Learn sparse term weights with SPLADE](hybrid-retrieval.md#learned-sparse-splade)
- Address: https://rollingedition.com/concepts/search-and-recommendation/learned-sparse-retrieval

## learning to rank

Learning to rank trains a model on judged queries to order candidates by their features.

- Computed from: feature
- Defined in: [Learn a ranking from pairs of products](ranking.md#learn-from-pairs)
- Address: https://rollingedition.com/concepts/search-and-recommendation/learning-to-rank

## length normalization

With length normalization, a long text, which has more chances to contain any term, gets its term frequencies discounted.

- Part of: BM25
- Defined in: [Rebuild BM25 by hand to match bm25s](lexical-retrieval.md#bm25-from-scratch)
- Address: https://rollingedition.com/concepts/search-and-recommendation/length-normalization

## Lexical retrieval

Lexical retrieval finds and ranks products by the words they share with the query.

- Defined in: [Lexical retrieval](lexical-retrieval.md)
- Address: https://rollingedition.com/concepts/search-and-recommendation/lexical-retrieval

## lexicon

The lexicon, the list of words that count as correct, decides what gets corrected.

- Defined in: [Correct spelling against the catalog's words](understanding-queries.md#correct-spelling-from-catalog)
- Address: https://rollingedition.com/concepts/search-and-recommendation/lexicon

## linear weights

With linear weights, a disagreement one grade apart weighs 0.5 and one two grades apart weighs 1

- Part of: Weighted kappa
- Defined in: [Give near misses partial credit with weighted kappa](judgments-from-people-and-llms.md#weighted-kappa-for-grades)
- Address: https://rollingedition.com/concepts/search-and-recommendation/linear-weights

## listwise LLM reranking

Listwise, an LLM orders a whole list in one answer

- A kind of: reranking
- Defined in: [Score each product with an LLM](ranking.md#llm-pointwise-reranking)
- Address: https://rollingedition.com/concepts/search-and-recommendation/listwise-llm-reranking

## listwise model

A listwise model scores a whole ranking.

- A kind of: learning to rank
- Defined in: [Learn a ranking from pairs of products](ranking.md#learn-from-pairs)
- Address: https://rollingedition.com/concepts/search-and-recommendation/listwise-model

## Matryoshka training

Matryoshka training teaches a model to put the most useful information in its first dimensions, so that the start of a vector works as a smaller embedding on its own.

- Also: Matryoshka
- Defined in: [Truncate dimensions, then test the loss](semantic-retrieval.md#truncate-dimensions-test-loss)
- Address: https://rollingedition.com/concepts/search-and-recommendation/matryoshka-training

## MaxSim

For each query token ColBERT finds the most similar product token, and it sums those maxima, an operation called MaxSim

- Formula: `score(query, product) = sum over query tokens q of max over product tokens d of cosine(q, d)`
- Part of: ColBERT
- Defined in: [Match token by token with ColBERT](hybrid-retrieval.md#late-interaction-colbert)
- Address: https://rollingedition.com/concepts/search-and-recommendation/maxsim

## Mean reciprocal rank

the mean of RR over queries is the mean reciprocal rank (MRR)

- Also: MRR
- Computed from: Reciprocal rank
- Defined in: [Score the first relevant result with reciprocal rank](measuring-search.md#score-the-first-relevant-result)
- Address: https://rollingedition.com/concepts/search-and-recommendation/mean-reciprocal-rank

## modifier

the query's modifiers are the attributes the shopper asked for.

- Also: modifiers
- Defined in: [Read intent as a product and its modifiers](what-relevance-means.md#intent-in-product-search)
- Address: https://rollingedition.com/concepts/search-and-recommendation/modifier

## naive Bayes

In words, naive Bayes finds a class likely for a query when the class is common among products, and when the query's words are common in that class's product text.

- Formula: `predicted class = argmax over classes c of log P(c) + sum over the query's words w of log P(w | c)`
- Implemented by: scikit-learn 1.9.1
- Defined in: [Train a query classifier on product text](understanding-queries.md#classify-queries-from-products)
- Address: https://rollingedition.com/concepts/search-and-recommendation/naive-bayes

## nearest-neighbour search

Retrieval by embeddings is a nearest-neighbour search: find the k products whose vectors are most similar to the query's.

- Defined in: [Find the exact nearest neighbours with NumPy](semantic-retrieval.md#exact-nearest-neighbours-numpy)
- Address: https://rollingedition.com/concepts/search-and-recommendation/nearest-neighbour-search

## noisy channel model

The classic corrector is the noisy channel model: for a typed word t, choose the correction c that maximizes P(c) × P(t | c)

- Also: noisy channel
- Formula: `correction(t) = argmax over candidates c of P(c) × P(t | c)`
- Defined in: [Correct spelling against the catalog's words](understanding-queries.md#correct-spelling-from-catalog)
- Address: https://rollingedition.com/concepts/search-and-recommendation/noisy-channel-model

## normalization

Normalization maps the different ways of writing one thing to a single form, on the products and on the query alike.

- Also: unit normalization
- Defined in: [Normalize units the way the catalog writes them](understanding-queries.md#normalize-units)
- Address: https://rollingedition.com/concepts/search-and-recommendation/text-normalization

## Normalized DCG

Normalized DCG (nDCG) divides a ranking's DCG by the DCG of the ideal ranking.

- Also: nDCG, nDCG@k, nDCG@10
- Formula: `nDCG@k = DCG@k / DCG@k of the ideal ranking`
- Computed from: Discounted cumulative gain
- Implemented by: scikit-learn 1.9.1
- Defined in: [Build nDCG from discounted gains](measuring-search.md#build-ndcg-from-dcg)
- Address: https://rollingedition.com/concepts/search-and-recommendation/ndcg

## normalizing

Scaling every vector to length 1, called normalizing

- Defined in: [Compare embeddings with cosine similarity](semantic-retrieval.md#compare-with-cosine-similarity)
- Address: https://rollingedition.com/concepts/search-and-recommendation/normalizing

## null hypothesis

the null hypothesis, the assumption that the rankers are equally good

- Comes before: significance test
- Comes before: p-value
- Defined in: [Test a gap with a permutation test](measuring-search.md#permutation-test-on-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/null-hypothesis

## observed agreement

The share of pairs on which two judges give the same grade, the observed agreement

- Defined in: [Measure agreement beyond chance with kappa](judgments-from-people-and-llms.md#agreement-beyond-chance)
- Address: https://rollingedition.com/concepts/search-and-recommendation/observed-agreement

## p-value

p-value: the probability, under the null hypothesis, of a gap at least as large as the one you measured

- Part of: significance test
- Defined in: [Test a gap with a permutation test](measuring-search.md#permutation-test-on-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/p-value

## paired test

The tests in this book are paired: both rankers are scored on the same queries, so each test works on the per-query differences, and a hard query's low scores cancel out.

- Also: paired
- A kind of: significance test
- Computed from: per-query differences
- Defined in: [Test a gap with a permutation test](measuring-search.md#permutation-test-on-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/paired-test

## pairwise LLM reranking

Pairwise, an LLM says which of two products fits the query better.

- A kind of: reranking
- Defined in: [Score each product with an LLM](ranking.md#llm-pointwise-reranking)
- Address: https://rollingedition.com/concepts/search-and-recommendation/pairwise-llm-reranking

## pairwise model

A pairwise model learns which of two products should rank higher.

- A kind of: learning to rank
- Defined in: [Learn a ranking from pairs of products](ranking.md#learn-from-pairs)
- Address: https://rollingedition.com/concepts/search-and-recommendation/pairwise-model

## peeking

Stopping a test the moment it looks significant, called peeking

- Defined in: [Run an A/B test](testing-changes.md#run-an-ab-test)
- Address: https://rollingedition.com/concepts/search-and-recommendation/peeking

## per-query differences

per-query differences: one number per query, the new ranker's score minus the old one's

- Defined in: [Read per-query differences, not only the mean](measuring-search.md#read-per-query-differences)
- Address: https://rollingedition.com/concepts/search-and-recommendation/per-query-differences

## per-query min-max scaling

Per-query min-max scaling maps the lowest score among the query's ranked products to 0 and the highest to 1.

- Also: min-max, per-query min-max
- Formula: `min-max(s) = (s − lowest score among the query's candidates) / (highest − lowest)`
- Contrasts with: theoretical min-max
- Defined in: [Normalize scores before you add them](hybrid-retrieval.md#normalize-scores-before-adding)
- Address: https://rollingedition.com/concepts/search-and-recommendation/min-max-scaling

## percentile interval

The percentile interval is the middle 95% of the resampled means.

- A kind of: confidence interval
- Defined in: [Report how big the gap is](measuring-search.md#report-the-size-of-a-gap)
- Address: https://rollingedition.com/concepts/search-and-recommendation/percentile-interval

## permutation test

A permutation test builds the gaps you'd see under the null hypothesis directly.

- A kind of: paired test
- Implemented by: scipy 1.18.1
- Defined in: [Test a gap with a permutation test](measuring-search.md#permutation-test-on-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/permutation-test

## phrase match

A phrase match needs the terms next to each other and in order

- Defined in: [Match phrases with term positions](lexical-retrieval.md#match-phrases-with-positions)
- Address: https://rollingedition.com/concepts/search-and-recommendation/phrase-match

## pointwise LLM reranking

Pointwise, an LLM judges each product alone and returns a label or a score.

- A kind of: reranking
- Defined in: [Score each product with an LLM](ranking.md#llm-pointwise-reranking)
- Address: https://rollingedition.com/concepts/search-and-recommendation/pointwise-llm-reranking

## pointwise model

A pointwise model predicts each product's grade on its own, as a regression.

- A kind of: learning to rank
- Defined in: [Learn a ranking from pairs of products](ranking.md#learn-from-pairs)
- Address: https://rollingedition.com/concepts/search-and-recommendation/pointwise-model

## pool

Nobody judges every product for every query, so test collections judge a pool instead, a set of candidates gathered for each query.

- Comes before: unjudged
- Defined in: [Know where the judgments came from](what-relevance-means.md#pooled-judgments)
- Address: https://rollingedition.com/concepts/search-and-recommendation/pool

## position bias

position bias: people click higher-ranked results more, partly because they trust the ranking.

- Defined in: [Treat clicks as biased evidence](what-relevance-means.md#clicks-are-not-judgments)
- Address: https://rollingedition.com/concepts/search-and-recommendation/position-bias

## positional bias

A listwise answer can suffer from positional bias: an LLM's tendency to let a product's place in the prompt affect its rank, not the click position bias of shoppers.

- Contrasts with: position bias
- Defined in: [Reverse the input to measure positional bias](ranking.md#llm-position-bias)
- Address: https://rollingedition.com/concepts/search-and-recommendation/positional-bias

## positional index

A positional index stores, for each term and product, the positions where the term occurs, so that a phrase becomes a check on positions

- Defined in: [Match phrases with term positions](lexical-retrieval.md#match-phrases-with-positions)
- Address: https://rollingedition.com/concepts/search-and-recommendation/positional-index

## postings

the list of products that contain the term, called the term's postings

- Part of: inverted index
- Defined in: [Build an inverted index](lexical-retrieval.md#build-an-inverted-index)
- Address: https://rollingedition.com/concepts/search-and-recommendation/postings

## power

the test's power: the chance that it detects a real change of a given size

- Also: statistical power
- Defined in: [Size the test with power](testing-changes.md#size-tests-with-power)
- Address: https://rollingedition.com/concepts/search-and-recommendation/power

## Precision at k

Precision at k, written precision@k, is the share of the top k results that are relevant.

- Also: precision@k, precision@10
- Measured from: judgment
- Contrasts with: Recall at k
- Defined in: [Count the relevant products in the top k](measuring-search.md#count-relevant-in-top-k)
- Address: https://rollingedition.com/concepts/search-and-recommendation/precision-at-k

## Prediction-powered inference

Prediction-powered inference rigorously corrects a model's predictions with a human sample, with confidence intervals that hold "without making any assumptions on the machine-learning algorithm that supplies the predictions"

- Formula: `corrected = mean over all queries of the LLM score + mean over the human sample of (human score − LLM score)`
- Defined in: [Correct LLM scores with a human sample](judgments-from-people-and-llms.md#calibrate-on-a-human-sample)
- Address: https://rollingedition.com/concepts/search-and-recommendation/prediction-powered-inference

## presentation bias

Presentation bias goes beyond position: clicks depend on how a result is shown, not only on where.

- Contrasts with: position bias
- Defined in: [Treat clicks as biased evidence](what-relevance-means.md#clicks-are-not-judgments)
- Address: https://rollingedition.com/concepts/search-and-recommendation/presentation-bias

## probe query

a probe query: one written for this chapter to test a behaviour, not one of the store's queries

- Defined in: [Split product text into terms](lexical-retrieval.md#split-text-into-terms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/probe-query

## prompt

The retrieved text goes into the prompt, the input the model reads

- Defined in: [Put retrieved products in the prompt](retrieval-for-llm-applications.md#put-retrieved-products-in-the-prompt)
- Address: https://rollingedition.com/concepts/search-and-recommendation/prompt

## pseudo-relevance feedback

Pseudo-relevance feedback assumes the top results are relevant and adds their terms to the query

- A kind of: query expansion
- Defined in: [Expand queries with a synonym list](understanding-queries.md#expand-with-synonyms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/pseudo-relevance-feedback

## query classification

Query classification assigns a query to a class in the store's taxonomy

- Defined in: [Train a query classifier on product text](understanding-queries.md#classify-queries-from-products)
- Address: https://rollingedition.com/concepts/search-and-recommendation/query-classification

## query drift

A word that expansion adds can match products the shopper didn't ask for, and move the query away from its meaning, which is called query drift.

- Defined in: [Expand queries with a synonym list](understanding-queries.md#expand-with-synonyms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/query-drift

## query expansion

Query expansion adds terms to a query so that it can match products that use other words for the same thing.

- Defined in: [Expand queries with a synonym list](understanding-queries.md#expand-with-synonyms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/query-expansion

## query rewriting

Query rewriting replaces the query with a text written to retrieve better.

- Defined in: [Rewrite queries with an LLM](understanding-queries.md#rewrite-queries-with-llm)
- Address: https://rollingedition.com/concepts/search-and-recommendation/query-rewriting

## query understanding

Query understanding is everything a search system does to a query before retrieval

- Kinds: query expansion
- Kinds: query classification
- Kinds: query rewriting
- Defined in: [Understanding queries](understanding-queries.md)
- Address: https://rollingedition.com/concepts/search-and-recommendation/query-understanding

## query-dependent feature

A query-dependent feature describes the query and the product together, such as a BM25 score.

- A kind of: feature
- Defined in: [Describe each candidate with features](ranking.md#ranking-features)
- Address: https://rollingedition.com/concepts/search-and-recommendation/query-dependent-feature

## query-independent feature

A query-independent feature describes the product alone, such as how many shoppers rated it.

- A kind of: feature
- Contrasts with: query-dependent feature
- Defined in: [Describe each candidate with features](ranking.md#ranking-features)
- Address: https://rollingedition.com/concepts/search-and-recommendation/query-independent-feature

## ranking

Ranking puts the retrieved products in order, best first.

- Contrasts with: retrieval
- Defined in: [Rank products with BM25](search-end-to-end.md#rank-with-bm25)
- Address: https://rollingedition.com/concepts/search-and-recommendation/ranking

## real-word error

real-word error, a typo in which every word is spelled right, as in "flew form Heathrow"

- Defined in: [Correct spelling against the catalog's words](understanding-queries.md#correct-spelling-from-catalog)
- Address: https://rollingedition.com/concepts/search-and-recommendation/real-word-error

## Recall at k

Recall at k, recall@k, is the share of all relevant products that appear in the top k.

- Also: recall@k, recall@10
- Measured from: judgment
- Defined in: [Count the relevant products in the top k](measuring-search.md#count-relevant-in-top-k)
- Address: https://rollingedition.com/concepts/search-and-recommendation/recall-at-k

## recall@k against exact search

An ANN index's quality is its recall@k against exact search: the share of exact search's top k that it also returns.

- Also: recall against exact search
- Measured from: exact search
- Contrasts with: Recall at k
- Defined in: [Trade recall for speed with HNSW](semantic-retrieval.md#hnsw-recall-for-speed)
- Address: https://rollingedition.com/concepts/search-and-recommendation/recall-at-k-against-exact-search

## Reciprocal rank

Reciprocal rank (RR) scores a query as 1 divided by the position of the first relevant result, or 0 if there is none

- Also: RR
- Measured from: judgment
- Defined in: [Score the first relevant result with reciprocal rank](measuring-search.md#score-the-first-relevant-result)
- Address: https://rollingedition.com/concepts/search-and-recommendation/reciprocal-rank

## reciprocal rank fusion

Reciprocal rank fusion (RRF) scores each product by adding, over the rankings that contain it, 1 divided by the sum of a constant k and its rank

- Also: RRF
- A kind of: fusion
- Defined in: [Test reciprocal rank fusion's settings on train queries](hybrid-retrieval.md#rrf-settings-on-train)
- Address: https://rollingedition.com/concepts/search-and-recommendation/reciprocal-rank-fusion

## regression set

regression set: fixed queries, with judgments, that every change runs against before it ships

- Defined in: [Diff two runs query by query](testing-changes.md#diff-runs-per-query)
- Address: https://rollingedition.com/concepts/search-and-recommendation/regression-set

## relevance feedback

Relevance feedback improves a query from judgments of its first results

- Defined in: [Search with a hypothetical product (HyDE)](understanding-queries.md#hyde-hypothetical-products)
- Address: https://rollingedition.com/concepts/search-and-recommendation/relevance-feedback

## relevant

In this book, a relevant product is one judged exact for the query, unless a sentence says otherwise.

- Measured from: judgment
- Defined in: [Load the store's data](search-end-to-end.md#store-data)
- Address: https://rollingedition.com/concepts/search-and-recommendation/relevant

## rerank depth

the rerank depth, how many products the reranker reads per query, is a budget decision

- Defined in: [Set the rerank depth from a budget](ranking.md#rerank-depth-from-budget)
- Address: https://rollingedition.com/concepts/search-and-recommendation/rerank-depth

## reranking

Reranking reorders a short list from retrieval with a slower model, one that can afford to look at the query and each product together because it only sees a few dozen products.

- Defined in: [Rerank the top 50 with a cross-encoder](search-end-to-end.md#rerank-with-cross-encoder)
- Address: https://rollingedition.com/concepts/search-and-recommendation/reranking

## retrievable unit

A retrievable unit is the piece of text that retrieval scores and returns, and that a context holds: a whole document, a passage or a sentence.

- Also: retrieval unit
- Part of: context
- Defined in: [Choose the retrievable unit](retrieval-for-llm-applications.md#choose-the-retrievable-unit)
- Address: https://rollingedition.com/concepts/search-and-recommendation/retrievable-unit

## retrieval

Retrieval finds the products that might match a query, out of the whole catalog.

- Comes before: ranking
- Comes before: reranking
- Defined in: [Rank products with BM25](search-end-to-end.md#rank-with-bm25)
- Address: https://rollingedition.com/concepts/search-and-recommendation/retrieval

## Retrieval-augmented generation

Retrieval-augmented generation (RAG), the design behind a shopping assistant, pairs an LLM with a retriever.

- Also: RAG
- Defined in: [Put retrieved products in the prompt](retrieval-for-llm-applications.md#put-retrieved-products-in-the-prompt)
- Address: https://rollingedition.com/concepts/search-and-recommendation/retrieval-augmented-generation

## risk-sensitive evaluation

Risk-sensitive evaluation counts losses more heavily than wins.

- Defined in: [Weigh losses more than wins with URisk](testing-changes.md#weigh-losses-with-urisk)
- Address: https://rollingedition.com/concepts/search-and-recommendation/risk-sensitive-evaluation

## run

The rankings for every query in a set form a run, written as {query_id: [product_id, ...]}, best first.

- Defined in: [Score every test query](search-end-to-end.md#score-every-test-query)
- Address: https://rollingedition.com/concepts/search-and-recommendation/run

## sample ratio mismatch

A sample ratio mismatch (SRM) means users went missing from one group or were added to it unevenly

- Also: SRM
- Defined in: [Run an A/B test](testing-changes.md#run-an-ab-test)
- Address: https://rollingedition.com/concepts/search-and-recommendation/sample-ratio-mismatch

## saturation

With saturation, each repeat of a term adds less than the one before, and no number of repeats can push the term's contribution past a ceiling

- Part of: BM25
- Defined in: [Rebuild BM25 by hand to match bm25s](lexical-retrieval.md#bm25-from-scratch)
- Address: https://rollingedition.com/concepts/search-and-recommendation/saturation

## score normalization

Score normalization rescales each retriever's scores for each query before adding them.

- Kinds: per-query min-max scaling
- Kinds: theoretical min-max
- Kinds: z-score
- Comes before: convex combination
- Defined in: [Normalize scores before you add them](hybrid-retrieval.md#normalize-scores-before-adding)
- Address: https://rollingedition.com/concepts/search-and-recommendation/score-normalization

## semantic retrieval

Semantic retrieval compares the meanings of the query and the product instead of their words.

- A kind of: retrieval
- Contrasts with: Lexical retrieval
- Comes before: hybrid retrieval
- Defined in: [Search by meaning with embeddings](search-end-to-end.md#search-by-meaning)
- Address: https://rollingedition.com/concepts/search-and-recommendation/semantic-retrieval

## sensitivity check

a sensitivity check, which rescores both runs under two scenarios, one favouring each side

- Computed from: unjudged
- Defined in: [Judge the products a new ranker surfaces](testing-changes.md#judge-new-results)
- Address: https://rollingedition.com/concepts/search-and-recommendation/sensitivity-check

## significance test

A significance test asks how surprising a gap between two rankers would be under the null hypothesis

- Defined in: [Test a gap with a permutation test](measuring-search.md#permutation-test-on-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/significance-test

## sliding window

A prompt can hold only so many products, so a long list is reranked in a sliding window: RankGPT reranks BM25's top 100 with "a window size of 20 and step size of 10", from the bottom of the list up

- Part of: listwise LLM reranking
- Defined in: [Order the 20 products with one LLM prompt](ranking.md#llm-listwise-reranking)
- Address: https://rollingedition.com/concepts/search-and-recommendation/sliding-window

## Spearman's rank correlation

Spearman's rank correlation is the correlation between two measures' ranks rather than their values, 1 when they order the cases the same way and near 0 when the orders are unrelated

- Also: Spearman
- Defined in: [Measure the context, then the answer](retrieval-for-llm-applications.md#measure-the-context)
- Address: https://rollingedition.com/concepts/search-and-recommendation/spearmans-rank-correlation

## SPLADE

SPLADE is one learned sparse retrieval model

- Formula: `weight of term j = sum over the text's tokens i of log(1 + ReLU(w_ij))`
- Defined in: [Learn sparse term weights with SPLADE](hybrid-retrieval.md#learned-sparse-splade)
- Address: https://rollingedition.com/concepts/search-and-recommendation/splade

## standalone query

standalone query, one that reads without the earlier turns and keeps what the shopper still wants

- Defined in: [Turn a follow-up into a standalone query](understanding-queries.md#standalone-follow-ups)
- Address: https://rollingedition.com/concepts/search-and-recommendation/standalone-query

## standard error

standard error: the standard deviation of the differences divided by the square root of the number of queries, which estimates how far the mean would move from one sample of queries to another

- Computed from: per-query differences
- Defined in: [Get the p-value from a paired t-test](measuring-search.md#paired-t-test-on-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/standard-error

## stem

the forms of a word share one term, its stem

- Defined in: [Stem terms so word forms match](lexical-retrieval.md#stem-word-forms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/stem

## Stemming

Stemming cuts common endings off words, so that the forms of a word share one term

- Comes before: stem
- Implemented by: pystemmer 3.1.0
- Defined in: [Stem terms so word forms match](lexical-retrieval.md#stem-word-forms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/stemming

## stop word

stop words, very common words such as the and with

- Defined in: [Split product text into terms](lexical-retrieval.md#split-text-into-terms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/stop-word

## student

a small model, the student, to imitate a large model

- Part of: distillation
- Defined in: [Distill the cross-encoder into a small ranker](ranking.md#distill-the-cross-encoder)
- Address: https://rollingedition.com/concepts/search-and-recommendation/student-model

## t distribution

t distribution: bell-shaped, with heavier tails than the normal, and a shape set by its degrees of freedom, here one fewer than the number of queries

- Defined in: [Get the p-value from a paired t-test](measuring-search.md#paired-t-test-on-queries)
- Address: https://rollingedition.com/concepts/search-and-recommendation/t-distribution

## target entity

A query names a target entity, the kind of product

- Contrasts with: modifier
- Defined in: [Read intent as a product and its modifiers](what-relevance-means.md#intent-in-product-search)
- Address: https://rollingedition.com/concepts/search-and-recommendation/target-entity

## teacher

to imitate a large model, the teacher

- Part of: distillation
- Defined in: [Distill the cross-encoder into a small ranker](ranking.md#distill-the-cross-encoder)
- Address: https://rollingedition.com/concepts/search-and-recommendation/teacher-model

## Team draft

Team draft interleaves two rankers' lists like picking teams for a game

- Also: team-draft interleaving
- A kind of: Interleaving
- Defined in: [Interleave two rankings with team draft](testing-changes.md#team-draft-interleaving)
- Address: https://rollingedition.com/concepts/search-and-recommendation/team-draft

## term

Removing stop words, very common words such as the and with, leaves the terms that search compares

- Part of: vocabulary
- Defined in: [Split product text into terms](lexical-retrieval.md#split-text-into-terms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/term

## term frequency

With each product, the postings store the term frequency, the number of times the term occurs in that product's text.

- Also: tf
- Part of: postings
- Defined in: [Build an inverted index](lexical-retrieval.md#build-an-inverted-index)
- Address: https://rollingedition.com/concepts/search-and-recommendation/term-frequency

## TF-IDF

TF-IDF multiplies tf and IDF for each query term and adds them up

- Formula: `tf-idf(q, d) = sum over query terms t of tf(t, d) × idf(t)`
- Computed from: term frequency
- Computed from: inverse document frequency
- Contrasts with: BM25
- Defined in: [Weight terms with TF-IDF](lexical-retrieval.md#weight-terms-with-tf-idf)
- Address: https://rollingedition.com/concepts/search-and-recommendation/tf-idf

## theoretical min-max

Theoretical min-max uses each score's lowest possible value instead of the lowest one seen: 0 for BM25 and −1 for cosine.

- Defined in: [Normalize scores before you add them](hybrid-retrieval.md#normalize-scores-before-adding)
- Address: https://rollingedition.com/concepts/search-and-recommendation/theoretical-min-max

## token

Splitting the text into pieces gives tokens.

- Comes before: term
- Defined in: [Split product text into terms](lexical-retrieval.md#split-text-into-terms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/token

## token

The store's encoder reads text as tokens, word pieces from its own vocabulary, not the terms of chapter 5's tokenizer.

- Contrasts with: term
- Defined in: [Turn text into embeddings](semantic-retrieval.md#turn-text-into-embeddings)
- Address: https://rollingedition.com/concepts/semantic-search/token

## tool

A tool is a function the program offers the model, described by a name, a description and its parameters.

- Also: tools
- Comes before: tool call
- Defined in: [Read an agent's searches from its trace](retrieval-for-llm-applications.md#read-agent-searches)
- Address: https://rollingedition.com/concepts/search-and-recommendation/tool

## tool call

A tool call is the model's request to run a tool with arguments.

- Also: tool calls
- Part of: agent loop
- Part of: trace
- Defined in: [Read an agent's searches from its trace](retrieval-for-llm-applications.md#read-agent-searches)
- Address: https://rollingedition.com/concepts/search-and-recommendation/tool-call

## trace

The trace is the record of every tool call and its result.

- Also: traces
- Defined in: [Read an agent's searches from its trace](retrieval-for-llm-applications.md#read-agent-searches)
- Address: https://rollingedition.com/concepts/search-and-recommendation/trace

## treatment

the changed system is the treatment

- Part of: A/B test
- Defined in: [Run an A/B test](testing-changes.md#run-an-ab-test)
- Address: https://rollingedition.com/concepts/search-and-recommendation/treatment

## unjudged

A product without a judgment for a query is unjudged for it

- Defined in: [Know where the judgments came from](what-relevance-means.md#pooled-judgments)
- Address: https://rollingedition.com/concepts/search-and-recommendation/unjudged

## URisk

The risk-sensitive measure of the TREC 2013 Web track is URisk.

- Formula: `URisk = (1 / N) × [ sum of Δ(q) over improved queries − (α + 1) × sum of |Δ(q)| over hurt queries ]`
- A kind of: risk-sensitive evaluation
- Computed from: baseline
- Computed from: candidate ranker
- Defined in: [Weigh losses more than wins with URisk](testing-changes.md#weigh-losses-with-urisk)
- Address: https://rollingedition.com/concepts/search-and-recommendation/urisk

## vocabulary

all the terms in the catalog form its vocabulary

- Defined in: [Split product text into terms](lexical-retrieval.md#split-text-into-terms)
- Address: https://rollingedition.com/concepts/search-and-recommendation/vocabulary

## Weighted kappa

Weighted kappa gives each disagreement a weight by its distance and compares the weighted disagreement with the weighted disagreement expected by chance

- Formula: `weighted kappa = 1 - (sum of weight × observed count) / (sum of weight × count expected by chance)`
- Contrasts with: Cohen's kappa
- Implemented by: scikit-learn 1.9.1
- Defined in: [Give near misses partial credit with weighted kappa](judgments-from-people-and-llms.md#weighted-kappa-for-grades)
- Address: https://rollingedition.com/concepts/search-and-recommendation/weighted-kappa

## weighted RRF

In weighted RRF, a product scores (1 − α) / (k + its BM25 rank) plus α / (k + its semantic rank).

- Also: weighted reciprocal rank fusion
- A kind of: reciprocal rank fusion
- Defined in: [Tune the blend's weight on train queries](hybrid-retrieval.md#tune-blend-on-train)
- Address: https://rollingedition.com/concepts/search-and-recommendation/weighted-rrf

## z-score

The z-score subtracts the mean of a query's scores and divides by their standard deviation.

- Defined in: [Normalize scores before you add them](hybrid-retrieval.md#normalize-scores-before-adding)
- Address: https://rollingedition.com/concepts/search-and-recommendation/z-score
