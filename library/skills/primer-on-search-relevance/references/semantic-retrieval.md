---
title: "A Primer on Search Relevance"
chapter: "Semantic retrieval"
chapter_id: semantic-retrieval
book: primer-on-search-relevance
edition: 2026.11.5
verified: 2026-11-10
edition_code: CKSM-TBXZ
canonical: https://rollingedition.com/primer-on-search-relevance/semantic-retrieval
license: CC BY 4.0
attribution: "“Semantic retrieval,” chapter 6 of A Primer on Search Relevance, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/semantic-retrieval. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Semantic retrieval

By the end of this chapter you can build semantic retrieval for a catalog from stored embeddings: compare vectors by cosine similarity, find a query's nearest products exactly with NumPy, switch to an approximate index when a catalog outgrows exact search and measure what the index misses, and find the queries where embeddings go wrong. You can also choose a vector size by testing it on your own judgments, and compare models the same way.

For [the store](#store-data), the online retailer of furniture and home goods whose search this book improves chapter by chapter, [semantic retrieval](#search-by-meaning) became the ranker to beat in the first pipeline, which [chapter 1](#search-end-to-end) builds. On the [test queries](#store-data) it scored a mean [nDCG@10](#score-one-ranking) of 0.830, against [BM25](#rank-with-bm25)'s 0.725, a lead that [chapter 3 establishes](#compare-runs-in-a-harness). It ran as one class, `lib.semantic.SemanticSearch`, over vectors that one model computed once, ahead of time. Before the store depends on it, you need to know what those vectors hold, what searching them would cost for a far larger catalog, and which queries they get wrong. This chapter builds exact search by hand, measures an approximate index against it, and tests both on the store's queries and judgments.

On the test queries, the chapter plans 2 comparisons, both in [the section on testing the index](#hnsw-on-test-queries). Each sets exact search, which compares a query with every product, against HNSW, an approximate index that compares it with only a fraction of them: once at faiss's default setting, and once at the setting chosen on the train queries. Under [the book's rule](#when-a-difference-is-established), a difference is established when its paired permutation p-value is below 0.025. Every other look at a test query in this chapter is an exploratory diagnosis.

## Turn text into embeddings {#turn-text-into-embeddings}

An **embedding** is a list of numbers, a vector, that a trained model computes for a piece of text. The model is an **encoder**, trained so that texts with similar meanings get vectors that point in similar directions, whether or not they share words. Every text gets the same count of numbers, the embedding's **dimension**, whether it's a three-word query or a product's whole description. One number means nothing on its own; only comparisons between whole vectors do.

Search uses the encoder as a **bi-encoder**: it encodes each product by itself, once, ahead of time, and each query by itself when the shopper types it. Comparing a query with a product is then arithmetic on two vectors rather than a run of the model, which is what makes it cheap enough to compare one query with a whole catalog. [Chapter 1](#search-by-meaning) gives the size of the difference from the Sentence-BERT paper: about 65 hours for BERT to read every pair of 10,000 sentences, against about 5 seconds to embed each sentence once and compare. A model that reads a query and a product together is a cross-encoder, and [chapter 1](#rerank-with-cross-encoder) uses one to rerank a shortlist.

The store's encoder is `Snowflake/snowflake-arctic-embed-m-v1.5`, an open model with 109 million parameters under the Apache-2.0 licence ([model card](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v1.5)). Its family's training kept only documents "primarily identified as English" ([Merrick et al., 2024](https://arxiv.org/abs/2405.05374)). We chose it because anyone may use it commercially, it's small, and it was trained so that its vectors can be shortened, which [the section on dimensions](#truncate-dimensions-test-loss) tests. The examples never run the model. They read a **recording**: vectors that the script `recordings/embeddings.py` computed once, at a pinned revision, and saved at unit length, so every example sees the same numbers. The model card asks you to "use the query prefix below (just on the query)", so the script adds that prefix to each query and embeds products as they are. Examples read the vectors through `lib.recorded.embeddings()`:

*Example `inspect-recorded-embeddings`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/turn-text-into-embeddings*

Each of the 12,000 products is a vector of 768 numbers. Product 1's begins -0.033, 0.051, 0.111, -0.012, and none of those numbers means anything alone. The recording stores each number as a `float16`, in 2 bytes, and `lib.recorded` widens them to 32-bit floats when it loads them. That rounding moves the stored lengths slightly off 1: they run from 0.99994 to 1.00006. So `lib.recorded` also scales each vector back to length 1, and the lengths it returns run from 1.00000 to 1.00000. The model reads text as **tokens**, word pieces from its own vocabulary, not the terms of [chapter 5's tokenizer](#split-text-into-terms). The longest product text is 201 tokens, inside the model's limit of 512, so the model read every product in full.

The comparison of queries at the end of the output shows what the vectors capture. The median similarity between two of the store's queries is 0.291, on a scale where 1 means two vectors point the same way ([cosine similarity](#compare-with-cosine-similarity)). The nearest query to `whimsical solar lights` is `outdoor light fixtures`, at 0.637, though they share 0 words: `lights` and `light` are different strings. The nearest to `wall design shelf` is `kitchen storage shelves`, at 0.679, with 0 words in common. The store's baseline BM25 doesn't stem words, so it sees nothing shared in either pair. [Chapter 5's stemming](#stem-word-forms) would match `lights` with `light`, but not `shelves` with `shelf`.

**Working rule:** Embed products ahead of time and queries at search time, with the same model at the same revision, and follow the model card on prompts: here, a prefix on queries only. Record the model, revision and prompts next to the vectors, as each `manifest.json` in `examples/data/recorded/` does. Check that your longest product fits the model's input limit before you trust its embedding.

## Compare embeddings with cosine similarity {#compare-with-cosine-similarity}

To rank products for a query, you need one number per pair that says how alike two vectors are. **Cosine similarity** is the cosine of the angle between them: 1 when they point the same way, 0 at right angles and −1 when they point in opposite directions. It ignores how long the vectors are. The **dot product** multiplies two vectors number by number and adds up the results, so it equals the cosine times both lengths. Scaling every vector to length 1 is called **normalizing**, and after it the two are the same number: "Dot product on normalized embeddings is equivalent to cosine similarity" ([Sentence Transformers](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)). The dot product is then the cheaper choice, because it skips computing the lengths.

```text
dot(q, d)    = q1 × d1 + q2 × d2 + ... + qn × dn
length(q)    = √(q1² + q2² + ... + qn²)
cosine(q, d) = dot(q, d) / (length(q) × length(d))
```

In the store, every query is compared with every product this way. For the test query `clear shower curtain`, compute the dot product and the cosine by hand for its most similar product, and check the cosine with scikit-learn 1.9.1. Then see what happens when vectors aren't unit length. Keep the first 256 of each vector's 768 numbers, a shortcut that [the section on dimensions](#truncate-dimensions-test-loss) tests, but skip the rescaling, and rank every query's products both ways:

*Example `cosine-by-hand`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/compare-with-cosine-similarity*

For the store's unit-length vectors, the dot product is 0.577, the cosine by hand is 0.577 and scikit-learn's `cosine_similarity` gives 0.577. The shortened vectors have lengths from 0.706 to 0.778, and now the two measures disagree. For 61 of the 80 queries, ranking by dot product gives a different top 10 from ranking by cosine. A query's own length scales all of its scores by the same factor, so it can't change their order. A product's length can: it multiplies that product's score for every query, a boost that has nothing to do with what the shopper asked for.

Some libraries report a distance instead of a similarity. faiss's L2 indexes return the squared Euclidean distance, and its inner product "is not by itself cosine similarity, unless the vectors are normalized" ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances)). For unit vectors, the squared distance is 2 − 2 × cosine, so it ranks products in the same order as cosine, smallest distance first.

**Working rule:** Normalize every vector once, when you store it, and rank by dot product. Normalize again after anything that changes a vector, such as shortening it or averaging several. If a model's documentation says it was trained for the dot product of unnormalized vectors, follow the documentation instead, and never mix the two in one index.

## Find the exact nearest neighbours with NumPy {#exact-nearest-neighbours-numpy}

Retrieval by embeddings is a **nearest-neighbour search**: find the k products whose vectors are most similar to the query's. **Exact** search compares the query with every product and keeps the best k, so it never misses one. With [unit-length vectors](#compare-with-cosine-similarity), comparing one query with every product is one matrix–vector product, and comparing many queries is one matrix product, with a row per query and a column per product. What's left is to find the k highest scores in each row. Sorting every row does more work than needed. NumPy's `argpartition` moves the k highest to one side without ordering either side ("The order of all elements in the partitions is undefined", [NumPy documentation](https://numpy.org/doc/stable/reference/generated/numpy.argpartition.html)), so you sort only those k.

In the store, [chapter 1's semantic search](#search-by-meaning) took its rankings from `lib.semantic.SemanticSearch`. Build its core by hand for the 30 test queries with NumPy 2.5.4, then check it twice: against `lib.semantic`, and against faiss's `IndexFlatIP`, which computes the inner product with every vector. With `IndexFlatL2`, it is one of the two faiss indexes that "can guarantee exact results" ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)):

*Example `exact-search-numpy`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/exact-nearest-neighbours-numpy*

One matrix product computes 360,000 similarities, 12,000 per query. The hand-built search returns the same top 10 as `lib.semantic` for 30 of 30 test queries, and the same as faiss for 30 of 30, so its run scores the same mean nDCG@10, 0.830. The book's shared module for vectors, `lib.vectors`, keeps this `top_k` for later examples and wraps it in `exact_search`.

What decides whether exact search is enough is its cost. Its work grows in step with the catalog: one similarity per product, for every query. Its memory is the vectors themselves:

*Example `exact-search-memory`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/exact-nearest-neighbours-numpy*

Each product takes 3,072 bytes as 32-bit floats, the store's catalog 36.9 MB, and a million products would take 3.1 GB. The faiss authors advise deciding first "whether indexing is needed at all: indeed, in some cases a direct brute force search is the best option" ([Douze et al., 2024](https://arxiv.org/abs/2401.08281)). In our judgement, the store's catalog is such a case.

**Working rule:** We recommend exact search until it no longer fits in memory or meets your latency budget, measured with your own catalog on your own hardware. It has no settings to tune and never misses a neighbour, so it is also the ground truth for any approximate index. Store the normalized vectors as one 32-bit matrix, take the top k with `argpartition`, and sort only those.

## Trade recall for speed with HNSW {#hnsw-recall-for-speed}

When [exact search](#exact-nearest-neighbours-numpy) costs too much, an **approximate nearest-neighbour** (ANN) index skips most of its comparisons, and in return may miss some of the true nearest neighbours. Its quality is its **recall@k against exact search**: the share of exact search's top k that it also returns. That isn't the [recall@k of chapter 3](#count-relevant-in-top-k), which compares a ranking with judgments. An index with perfect recall against exact search returns what exact search returns, good or bad.

**HNSW**, short for hierarchical navigable small world, is a graph index. Each product is a node linked to some of its nearest neighbours, in a stack of layers: the bottom layer holds every product, and each layer above holds fewer. A search starts at the top, moves to whichever linked node is nearest the query, steps down a layer when it gets no closer, and at the bottom explores a list of candidates before it returns the best k ([Malkov and Yashunin, 2018](https://arxiv.org/abs/1603.09320)). In faiss, `M` sets the links per node, and more links find more true neighbours but use more memory ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)). `efConstruction`, the "expansion factor at construction time", sets how many candidates the build considers, and `efSearch`, the "expansion factor at search time", how many a search considers. faiss 1.15.1 defaults them to 40 and 16, and its graph build is deterministic: "This is the only graph build that add() uses" ([`HNSW.h`](https://raw.githubusercontent.com/facebookresearch/faiss/v1.15.1/faiss/impl/HNSW.h); [changelog](https://raw.githubusercontent.com/facebookresearch/faiss/v1.15.1/CHANGELOG.md)). So the outputs here repeat exactly. Timings differ from machine to machine, so the examples count work instead: faiss records the "number of distances computed" in each search (`HNSW.h`), which for this index are similarities. The count leaves out following links and reading memory, so treat it as a guide to speed, not a measure of it.

The store doesn't need an index, but a store with millions of products would, and a catalog small enough to check every answer is the place to learn the trade-off. Build HNSW over the store's 12,000 products with `hnsw_index(product_vectors, links=32)`, `lib.vectors`'s name for `M = 32`. Then sweep `efSearch` from 16 to 256 on the [train queries](#store-data):

*Example `hnsw-efsearch-sweep`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/hnsw-recall-for-speed*

The layers hold 12,000, 369 and 10 products. At the default `efSearch` of 16, a query computes 282 similarities instead of 12,000, and mean recall@10 against exact search is 0.934. The mean hides a failure: 2 train queries get none of their true top 10. They are foutains with brick look, sheffield home bath set. For `foutains with brick look`, HNSW returns a cushion, a wall decor set and an ivy branch, while exact search's top 3 are brick-look tiles: for this query, the search ended in a part of the graph far from its true neighbours.

The smallest `efSearch` in the sweep at which no train query is at 0 is 96, but the example's table shows that its worst query still misses most of its true top 10. So choose by a stricter rule: the smallest `efSearch` at which every train query finds at least 9 of its true top 10. That is 144, with a mean recall of 0.998 and 835 similarities per query.

**Working rule:** Use an ANN index only when exact search is too slow or too large. Tune it on train queries by its recall against exact search, at the k your pipeline uses, and choose by the worst query, not the mean. We recommend the smallest `efSearch` at which every query keeps at least 9 of its true top 10, with `M = 32`. This chapter tunes only `efSearch`; `M` and `efConstruction` change the graph itself, and deserve the same sweep on a large catalog. Very different ANN methods "yield comparable quality-performance trade-offs" ([Aumüller et al., 2018](https://arxiv.org/abs/1807.05614)), so measure on your own data rather than choosing a method by reputation.

## Check the index on the test queries {#hnsw-on-test-queries}

An index tuned on train queries still has to be checked on queries it hasn't seen, by its [recall against exact search](#hnsw-recall-for-speed) and by its effect on the judged scores. In the store, these are the chapter's 2 planned test comparisons: the HNSW index at faiss's default `efSearch` of 16, and at the setting chosen on the train queries, each against exact search. A difference is established when its paired [permutation test](#permutation-test-on-queries) gives p below 0.025, with the [t-test and an interval](#when-a-difference-is-established) at the matching level beside it. The example also asks for `k = 100`, because [hybrid retrieval](#fuse-with-rrf) fuses each retriever's top 100:

*Example `hnsw-test-recall`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/hnsw-on-test-queries*

At the chosen `efSearch` of 144, recall@10 against exact search is 1.000, the nDCG@10 of 0 queries changes, and the mean nDCG@10 is 0.830, as for exact search (0.830). At the default, 2 test queries get none of their true top 10: liberty hardware francisco, 48" sliding single track , barn door for laundry. The mean nDCG@10 falls to 0.791. Only 3 queries change score, and the fall isn't established: the permutation test gives p = 0.256, and the t-test agrees with p = 0.154. The 97.5% interval, from -0.1544 to -0.0006, excludes 0, so it disagrees with the tests. With so few queries carrying the difference, the finding is the recall lost against exact search, not a measured loss of quality. Asking for more results doesn't make up for a small `efSearch`: at the default, recall@100 is 0.849, against 0.994 at the chosen setting.

The graph also costs memory, on top of the vectors:

*Example `hnsw-index-memory`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/hnsw-on-test-queries*

Each product has 32 links on the upper layers and 64 on the bottom one, twice `M`. faiss estimates 4d + 8M bytes per vector ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)): 4 bytes for each of the d numbers, and 4 bytes for each of the 2M links on the bottom layer, 3,328 here. The saved index takes 3,344 bytes per product, against 3,072 for the exact index.

**Working rule:** Check a tuned index on held-out queries by its recall against exact search, and read the queries that lose their whole top k before the mean score. Treat a fall in nDCG@10 that rests on a handful of queries as unproven until a paired test establishes it. Budget memory for the links as well as the vectors.

## Check queries that contain digits {#embeddings-match-digits}

[An index](#hnsw-on-test-queries) can only return what the embeddings put near a query, so the next question is which queries the embeddings themselves get wrong. An encoder squeezes a whole query into one vector, so a short token that changes the meaning, such as a size, a model number or a "not", may move that vector very little. A study of 13 embedding models measured this for numbers, on synthetic financial text: their accuracy at telling texts apart by a number "is merely 0.54, slightly above random guessing (0.5)", and four-digit numbers were at the level of guessing ([Deng et al., 2026](https://aclanthology.org/2026.findings-eacl.289/)). Products aren't financial reports, so check the store's own queries.

In the store, few queries hold a digit. Compare BM25 and semantic retrieval on each of them, from both splits. This is an exploratory diagnosis: nothing is tuned on it, and a handful of queries can't establish anything:

*Example `digits-in-queries`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/embeddings-match-digits*

Of the 7 queries with a digit, semantic retrieval scores higher on 4 and BM25 on 3, and 2 of the gaps are under 0.03, so neither ranker wins them all. For `7qt slow cooker`, BM25 fails: 0 products contain the word `7qt`, while 8 write `7 qt`. For the test query `48 inch kitchen hood`, BM25 scores higher. Here is semantic retrieval's top 10 for it:

*Example `hood-query-digits`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/embeddings-match-digits*

In semantic retrieval's top 10, 8 hoods have a width of 48. The others are a 36-inch hood from a series named `ws-48` and a 30-inch hood rated at 480 cfm, cubic feet per minute, the airflow of its fan. Both contain the digits 48, neither is 48 wide, and the judges marked both [partial](#store-data). Of BM25's top 10, 10 have a width of 48. For this query, the embedding matched the digits as text, not the width they stand for. The example reads each hood's width from the `attributes` column, curated fields from WANDS's product features such as width, shape and material. `product_text`, the text the model embedded, leaves that column out, so the embeddings never saw it, and a size the shopper types can be checked against it exactly.

One query can't show a pattern. To see how the model handles sizes in general, use **probe queries**: pairs of queries written for the book that differ only in a size, a code or a negation, which `recordings/probes.py` embeds with the same model. One of them repeats the test query `48 inch kitchen hood` word for word. Probes have no judgments, so the example counts what their top 10s hold and never scores them. The right size comes from the width in `attributes` for the hoods, and from the name for the rest:

*Example `probe-pair-overlap`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/embeddings-match-digits*

For these probes, the model mostly finds the right size. The two hood probes share 0 products, and their top 10s hold 8 and 8 hoods of the right width. The slow-cooker probes find 6 and 7 of the right capacity, and the bed probes 10 and 10. Where the catalog has no number to match, the digit takes over. The number of product names that give a seat count is 0, and the top 10 for `2 seat sofa` holds 4 products that share only the digit, two-piece sets and "2 in 1" kids' sofas, and 0 of the catalog's 14 loveseats.

### Expect a code to carry little weight {#codes-carry-no-weight}

A product code should match one product exactly. To an encoder, it's a rare string of letters and digits. Two pairs of the [probe queries](#embeddings-match-digits) test codes: one built on a code no product holds, taken from the train query `ines shag rug w003096809`, and one built on a screen resolution that exactly one product's text holds:

*Example `code-probes`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/codes-carry-no-weight*

Changing the last digits of the unknown code leaves the two queries at a similarity of 0.967, and their top 10s share 10 products: a code that matches nothing changes nothing, and BM25 has nothing to match either. The resolution `1920x1080p` appears only in the text of the `5000 portable transmissive projector`. The embedding puts it at rank 1 for `1920x1080p projector`, at a similarity of 0.562 against 0.496 for the next product. For `2560x1440p projector` it still puts it at rank 1, at 0.509 against 0.508. The matching code widens the product's lead over the next one, but the product is one of only 4 projectors and ranks first either way. BM25 puts it at rank 1 with its code; without it, the product is not in the top 100. The code decides the lexical ranking and nudges the semantic one. In one study of questions about rare entities, dense (embedding-based) retrievers "drastically underperform sparse methods" ([Sciavolino et al., 2021](https://arxiv.org/abs/2109.08535)), while BM25 is "sensitive to highly selective keywords and phrases" ([Karpukhin et al., 2020](https://arxiv.org/abs/2004.04906)).

**Working rule:** List the queries in your log that hold sizes, quantities or codes, and compare both rankers on them before you trust either. When a code matters, match it lexically. When an exact size matters, match it against a product field such as the width in `attributes`, or lexically once the tokenizer keeps digits and units are written one way ([chapter 5](#split-text-into-terms), [chapter 8](#normalize-units)). Leave the rest of the query to semantic retrieval. [Chapter 7](#when-hybrid-helps) tests combining the two.

## Test embeddings on negation {#embeddings-on-negation}

Negation reverses what a shopper wants with one short word: a rug that is *not* round. An embedding of the whole query can stay close to the same query without that word. NevIR, a benchmark of document pairs that differ by a negation, found that "No bi-encoder architecture scores higher than 12% paired accuracy", where ranking at random scores 25% ([Weller et al., 2024](https://arxiv.org/abs/2305.07614)). In a 2025 reproduction, one 7-billion-parameter bi-encoder, GritLM-7B, reached 39.0%, other bi-encoders tested improved little, and "only cross-encoders and listwise LLM re-rankers achieve reasonable performance across both negation tasks" ([van den Elsen et al., 2025](https://arxiv.org/abs/2502.13506)).

In the store, 0 of the queries contain "no", "not", "without" or "non", so the judgments can't test negation. The example uses 3 pairs of [probe queries](#embeddings-match-digits) instead, each a query and its negation, and counts what each top 10 holds. The catalog could satisfy each negated probe: it has 42 products named armless, 62 coffee tables that never mention glass, and 90 area rugs not named round.

Before you run it, predict: how many of semantic retrieval's top 10 for `rug that is not round` are named round?

*Example `negation-probes`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/embeddings-on-negation*

Semantic retrieval's top 10 for `rug that is not round` holds 10 products named round, and its top 10 for `round rug` holds 10. For `coffee table not glass`, 10 of the top 10 mention glass, against 10 for `coffee table with glass top`. In both probes, the embedding kept the attribute and lost the "not". `sofa without arms` goes the other way: 8 of its top 10 are named armless, against 1 for `sofa with arms`. The catalog has one word for that negation, armless, and the model places "without arms" near it. BM25 does no better on these probes. Its tokenizer drops "not", "that" and "is" as [stop words](#split-text-into-terms), so it searches `rug that is not round` as `rug round`, and its top 10s hold 10 round rugs and 0 armless sofas.

If you predicted fewer, you expected the model to read "not" the way a shopper means it. These probes are a few pairs, not a measurement, and the sofa pair goes the other way, but the other two agree with NevIR: the query vector stays near the attribute the query names.

**Working rule:** Don't rely on a first-stage retriever, lexical or semantic, to handle negation. When shoppers exclude an attribute your catalog stores, such as shape, material or arms, detect the exclusion and filter on the attribute. Otherwise, rerank: in van den Elsen et al.'s reproduction, cross-encoders and LLM rerankers handled negation far better. Chapter 9 reranks the store's semantic retrieval with [a cross-encoder](#rerank-semantic-with-cross-encoder) and [LLMs](#llm-listwise-reranking), and none of its rerankers beats semantic retrieval on the store's judged queries, which can't test negation. Keep probes like these as a check to rerun whenever you change models or add a reranker.

## Choose an embedding model {#choose-embedding-model}

The model decides what the vectors can know, and changing it later means embedding the whole catalog again. Public benchmarks narrow the field. The store's own judgments decide.

### Read benchmarks as a shortlist {#benchmarks-as-a-shortlist}

MTEB, the Massive Text Embedding Benchmark, scores models on many tasks, and its authors found that "no particular text embedding method dominates across all tasks". Its averages "are biased towards tasks with many datasets, notably retrieval, classification and clustering", so read the scores for the task you have ([Muennighoff et al., 2023](https://aclanthology.org/2023.eacl-main.148/)). Public scores can also overstate how a model does on data it hasn't seen: the makers of RTEB, a retrieval benchmark, describe "a gap ... between their reported scores and their actual performance on new, unseen data" ([Liu et al., 2025](https://huggingface.co/blog/rteb)). RTEB keeps 28 of its 48 datasets private. Its ranking of models correlates only ρ = 0.38 with their rankings on MTEB and on BEIR, an earlier benchmark of retrieval across many domains ([Thakur et al., 2021](https://arxiv.org/abs/2104.08663)), where ρ is a rank correlation and 1 means the same order ([Verma et al., 2026](https://neurips.cc/virtual/2026/poster/139103)). Size isn't quality either. In MMTEB, MTEB's multilingual successor, "the best-performing publicly available model is multilingual-e5-large-instruct with only 560 million parameters" ([Enevoldsen et al., 2025](https://arxiv.org/abs/2502.13595)).

The store considered four open models, and none of their cards reports results on WANDS: [the store's encoder](#turn-text-into-embeddings), `Qwen/Qwen3-Embedding-0.6B` ([card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)), `BAAI/bge-base-en-v1.5` ([card](https://huggingface.co/BAAI/bge-base-en-v1.5)) and `ibm-granite/granite-embedding-english-r2` ([card](https://huggingface.co/ibm-granite/granite-embedding-english-r2)). Product-search benchmarks such as [ESCI](#gains-are-a-choice), which labels query–product pairs as exact, substitute, complement or irrelevant and holds about 130,000 queries and 2.6 million judgments ([Reddy et al., 2022](https://arxiv.org/abs/2206.06588)), are closer to the store's task, but they still aren't its catalog. So the store's shortlist rests on checks a leaderboard can't make: a licence that allows commercial use, English, a size that runs without special hardware, and documented support for shorter vectors. The card of the store's choice reports 55.14 nDCG@10 on MTEB's retrieval tasks, a vendor's measurement on general text, not on products ([model card](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v1.5)). To choose between candidates, record each one on the same product text and queries, score each on the train queries, and compare them with [the book's paired tests](#when-a-difference-is-established), as [the next subsection](#truncate-dimensions-test-loss) does for one model at several sizes.

### Truncate dimensions, then test the loss {#truncate-dimensions-test-loss}

Every dimension costs 4 bytes per product as a 32-bit float, and every similarity multiplies all of them, so a shorter vector is cheaper to store and to search. **Matryoshka** training teaches a model to put the most useful information in its first dimensions, so that the start of a vector works as a smaller embedding on its own. In the original paper, it gave "up to 14x smaller embedding size for ImageNet-1K classification at the same level of accuracy" ([Kusupati et al., 2022](https://arxiv.org/abs/2205.13147)). Shortening saves storage and search, not encoding: a Matryoshka model "is not faster" to run ([Sentence Transformers](https://sbert.net/examples/sentence_transformer/training/matryoshka/README.html)). Only models trained this way are built to survive it, and a shortened vector isn't unit length, so [normalize it again](#compare-with-cosine-similarity), as the model card's own example does.

The model card of the store's encoder ([Turn text into embeddings](#turn-text-into-embeddings)) documents shortening to 256 dimensions. `lib.recorded.embeddings(dims=...)` keeps the first `dims` numbers of each vector and normalizes again. Score each length on the train queries:

*Example `truncate-embeddings`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/truncate-dimensions-test-loss*

At 256 dimensions a product takes 1,024 bytes instead of 3,072, and mean nDCG@10 moves from 0.772 to 0.762. At 128 it is 0.680, with [judged@10](#score-every-test-query) at 0.874 against 0.964, so part of that fall could come from products nobody judged. Is the change real, or noise among 50 queries? Test it with `lib.significance.compare`, which runs [chapter 3's permutation test](#permutation-test-on-queries), its [paired t-test](#paired-t-test-on-queries) and its [bootstrap interval](#report-the-size-of-a-gap). These comparisons use train queries, so they tune the vector size; they aren't evidence about the test queries:

*Example `truncation-paired-test`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/truncate-dimensions-test-loss*

For 128 dimensions, the mean difference is -0.092, 33 train queries get worse, the permutation test gives p below 0.001, and the 95% interval, from -0.1569 to -0.0565, excludes 0: a clear loss. For 256, the mean difference is -0.010, the permutation test gives p = 0.076 and the t-test p = 0.080, yet the interval, from -0.0211 to -0.0002, excludes 0 by a hair. The tests and the interval disagree, so the evidence of a loss at 256 is borderline. The [effect size](#report-the-size-of-a-gap), -0.253 against -0.547 at 128, says any loss is the smaller of the two.

For the store, the decision follows from its size, not from the test. Its full vectors take [36.9 MB](#exact-nearest-neighbours-numpy), so there is little to save, and it keeps all 768 dimensions; its test score doesn't change. A catalog of hundreds of millions of products would weigh a saving of two-thirds against a loss that this many train queries can't pin down, and would judge more queries before it decided.

**Working rule:** Shortlist models on licence, language, size and domain, and treat benchmark ranks as a hint. Decide between models, or between vector sizes, on your own train queries with a paired test, and read the interval as well as the p-value. Shorten vectors only for a model trained for it, normalize after shortening, and only when memory or search time requires it.

## What goes wrong in production {#semantic-retrieval-in-production}

**A similarity is not a confidence.** It's tempting to show nothing when the best similarity is low. But similarities aren't on one scale across queries:

*Example `similarity-scale`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/semantic-retrieval-in-production*

On the test queries, `liberty hardware francisco` has the weakest best match, at 0.436, yet its top 10 holds 5 exact products. `kohler whitehaven farmhouse kitchen sink` has the most similar 10th match, at 0.647. A cutoff of 0.5 would keep 0 products for the first query and 103 for the second, and nothing for 2 test queries. Nor does semantic search ever come back empty: a [code that no product holds](#codes-carry-no-weight) still gets a full top 10. Decide that a query has no match some other way, for example when lexical retrieval finds none of its rare terms.

**Mismatched vectors fail silently.** Query and product vectors must come from the same model, revision and prompts. Vectors from two models are numbers in different spaces, and when the two have the same dimension, comparing them raises no error. Sentence Transformers adds a model's query prompt when you call `encode_query`, which uses "a predefined “query” prompt, if available" ([API reference](https://sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html)). Make sure the code that embeds live queries does what the indexing code did.

**An index doesn't follow the catalog by itself.** faiss's HNSW "does not support removing vectors from the index" ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)), so a discontinued product stays in the graph until you filter it out of results or rebuild. "Faiss is not a database": it has no concurrent writes, sharding or transactions ([Douze et al., 2024](https://arxiv.org/abs/2401.08281)). Recall against exact search belongs to one catalog and one set of settings, so measure it again after every rebuild.

**Long texts are cut short.** The model reads at most 512 tokens, and Sentence Transformers says "Longer inputs will be truncated" ([API reference](https://sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html)). The store's longest product is 201 tokens, but in a catalog with long descriptions the model never reads what falls past the limit. Count tokens before you embed, as `recordings/embeddings.py` does.

**Typos move vectors.** For BERT-based retrievers not trained on misspellings, "typos can lead to a significant drop in retrieval and ranking effectiveness" ([Zhuang and Zuccon, 2021](https://arxiv.org/abs/2108.12139)). 4 of the store's queries contain a typo, and the probes include each one spelled correctly. A corrected probe asks for the same thing as its query, so the example scores it with that query's judgments:

*Example `spelling-probes`: its code, the versions it ran on and its output are on the book's page: https://rollingedition.com/primer-on-search-relevance/s/semantic-retrieval-in-production*

For the train query `foutains with brick look`, the corrected spelling changes the whole semantic top 10, with 0 products shared, and nDCG@10 goes from 0.353 to 0.645; BM25 goes from 0.356 to 0.507. For the others, the scores move less. The one test query among them, `refrigerator with ice an water in door`, goes from 0.807 to 0.829, an exploratory look at one query. These queries can't establish a pattern: with 4 of them, the smallest two-sided permutation p-value possible is 0.125.

**Working rule:** Don't filter on a fixed similarity. Record the model, revision and prompts with every vector, and check them where queries are embedded. Rebuild and re-measure the index as the catalog changes, count tokens before you embed, and correct spelling before you embed a query when your log shows typos, with a corrector that checks each word's neighbours ([chapter 8](#correct-spelling-from-catalog)).

## Decisions this chapter made {#semantic-retrieval-decisions}

Each choice below is a default, measured on the train queries where it could be.

- **Model:** `Snowflake/snowflake-arctic-embed-m-v1.5`, which `recordings/embeddings.py` records once at a pinned revision. It is open, under Apache-2.0, small, and trained for shorter vectors. Queries get the prefix its card asks for; products don't.
- **Similarity:** the dot product of unit-length vectors, which is cosine similarity. Vectors are normalized once, and again after any change.
- **Search:** exact, with NumPy, through `lib.vectors.exact_search`, because the store's vectors take 36.9 MB. It is also the ground truth for any index.
- **If the catalog outgrows exact search:** faiss HNSW with `M = 32` and an `efSearch` of 144, the smallest setting in the train sweep at which every query keeps at least 9 of its true top 10. On the test queries, its recall@10 against exact search is 1.000.
- **An index's recall is measured against exact search,** on train queries, at the k the pipeline uses, reading the worst queries as well as the mean.
- **Dimensions:** all 768. Shortening to 256 would save two-thirds of the memory at a cost the train queries can't pin down, and the store has little to save.
- **Probe queries test what the judgments can't,** such as negation, codes and spelling. They are compared by their top 10s and kept apart from the judged queries; only a corrected spelling, which asks what its query asks, is scored with that query's judgments.
- **Known weak spots go to other stages:** codes to lexical retrieval; exact sizes to attribute fields, or to lexical retrieval once the tokenizer keeps digits ([chapter 5](#split-text-into-terms), [chapter 8](#normalize-units)); for both, a filter to test rather than a blend ([chapter 7](#when-hybrid-helps)); negation to attribute filters and reranking.
