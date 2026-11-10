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

Example `inspect-recorded-embeddings` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
import re

import numpy as np

from lib.recorded import RECORDED, embeddings, manifest
from lib.store import load_queries

product_ids, product_vectors, query_ids, query_vectors = embeddings()
recording = manifest("embeddings")
print("embedding model:", recording["model"])
print("query prompt:", recording["prompts"]["query"])
print(f"products embedded: {len(product_ids):,}")
print("dimensions:", product_vectors.shape[1])
print("stored as:", recording["dtype"])
print("longest product text, tokens:", recording["longest_product_tokens"])
print("model's input limit, tokens:", recording["max_seq_length"])
print(f"product {product_ids[0]}, first four numbers:", ", ".join(f"{x:.3f}" for x in product_vectors[0, :4]))
stored = np.load(RECORDED / "embeddings" / "products.npy").astype(np.float32)   # as saved, before lib.recorded
stored_lengths, lengths = np.linalg.norm(stored, axis=1), np.linalg.norm(product_vectors, axis=1)
print(f"stored vector lengths: {stored_lengths.min():.5f} to {stored_lengths.max():.5f}")
print(f"lengths after lib.recorded rescales: {lengths.min():.5f} to {lengths.max():.5f}")

# How close are two shopper queries? Compare every query with every other one.
queries = load_queries().loc[query_ids, "query"].tolist()
similarity = query_vectors @ query_vectors.T
np.fill_diagonal(similarity, np.nan)               # leave out each query's similarity to itself
print(f"median similarity of two queries: {np.nanmedian(similarity):.3f}")
for query in ["whimsical solar lights", "wall design shelf"]:
    row = queries.index(query)
    nearest = int(np.nanargmax(similarity[row]))
    shared = set(re.findall(r"\w+", query)) & set(re.findall(r"\w+", queries[nearest]))
    print()
    print(f"{query}, nearest other query:", queries[nearest])
    print(f"{query}, similarity: {similarity[row, nearest]:.3f}")
    print(f"{query}, words in common:", len(shared))
```

Output:

```text
embedding model: Snowflake/snowflake-arctic-embed-m-v1.5
query prompt: Represent this sentence for searching relevant passages:
products embedded: 12,000
dimensions: 768
stored as: float16
longest product text, tokens: 201
model's input limit, tokens: 512
product 1, first four numbers: -0.033, 0.051, 0.111, -0.012
stored vector lengths: 0.99994 to 1.00006
lengths after lib.recorded rescales: 1.00000 to 1.00000
median similarity of two queries: 0.291

whimsical solar lights, nearest other query: outdoor light fixtures
whimsical solar lights, similarity: 0.637
whimsical solar lights, words in common: 0

wall design shelf, nearest other query: kitchen storage shelves
wall design shelf, similarity: 0.679
wall design shelf, words in common: 0
```

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

Example `cosine-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · scikit-learn 1.9.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from lib.recorded import embeddings
from lib.store import load_products

products = load_products()
product_ids, product_vectors, query_ids, query_vectors = embeddings()
query = query_vectors[list(query_ids).index(246)]           # clear shower curtain
best = int(np.argmax(product_vectors @ query))
product = product_vectors[best]
print("product:", products.at[product_ids[best], "name"])

# cosine = dot product / (length of q * length of d)
dot = query @ product
cosine = dot / (np.linalg.norm(query) * np.linalg.norm(product))
print(f"dot product: {dot:.3f}")
print(f"cosine by hand: {cosine:.3f}")
print(f"cosine from scikit-learn: {cosine_similarity([query], [product])[0, 0]:.3f}")

# Keep the first 256 numbers of each vector and don't rescale: the lengths are no longer 1.
short_products, short_queries = product_vectors[:, :256], query_vectors[:, :256]
lengths = np.linalg.norm(short_products, axis=1)
print(f"shortened product lengths: {lengths.min():.3f} to {lengths.max():.3f}")
by_dot = np.argsort(-(short_queries @ short_products.T), axis=1, kind="stable")[:, :10]
by_cosine = np.argsort(-(short_queries @ (short_products / lengths[:, None]).T), axis=1, kind="stable")[:, :10]
changed = sum(set(dot_top) != set(cosine_top) for dot_top, cosine_top in zip(by_dot, by_cosine))
print("queries:", len(query_ids))
print("queries whose top 10 changes:", changed)
```

Output:

```text
product: woolley vinyl solid color single shower curtain
dot product: 0.577
cosine by hand: 0.577
cosine from scikit-learn: 0.577
shortened product lengths: 0.706 to 0.778
queries: 80
queries whose top 10 changes: 61
```

For the store's unit-length vectors, the dot product is 0.577, the cosine by hand is 0.577 and scikit-learn's `cosine_similarity` gives 0.577. The shortened vectors have lengths from 0.706 to 0.778, and now the two measures disagree. For 61 of the 80 queries, ranking by dot product gives a different top 10 from ranking by cosine. A query's own length scales all of its scores by the same factor, so it can't change their order. A product's length can: it multiplies that product's score for every query, a boost that has nothing to do with what the shopper asked for.

Some libraries report a distance instead of a similarity. faiss's L2 indexes return the squared Euclidean distance, and its inner product "is not by itself cosine similarity, unless the vectors are normalized" ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances)). For unit vectors, the squared distance is 2 − 2 × cosine, so it ranks products in the same order as cosine, smallest distance first.

**Working rule:** Normalize every vector once, when you store it, and rank by dot product. Normalize again after anything that changes a vector, such as shortening it or averaging several. If a model's documentation says it was trained for the dot product of unnormalized vectors, follow the documentation instead, and never mix the two in one index.

## Find the exact nearest neighbours with NumPy {#exact-nearest-neighbours-numpy}

Retrieval by embeddings is a **nearest-neighbour search**: find the k products whose vectors are most similar to the query's. **Exact** search compares the query with every product and keeps the best k, so it never misses one. With [unit-length vectors](#compare-with-cosine-similarity), comparing one query with every product is one matrix–vector product, and comparing many queries is one matrix product, with a row per query and a column per product. What's left is to find the k highest scores in each row. Sorting every row does more work than needed. NumPy's `argpartition` moves the k highest to one side without ordering either side ("The order of all elements in the partitions is undefined", [NumPy documentation](https://numpy.org/doc/stable/reference/generated/numpy.argpartition.html)), so you sort only those k.

In the store, [chapter 1's semantic search](#search-by-meaning) took its rankings from `lib.semantic.SemanticSearch`. Build its core by hand for the 30 test queries with NumPy 2.5.4, then check it twice: against `lib.semantic`, and against faiss's `IndexFlatIP`, which computes the inner product with every vector. With `IndexFlatL2`, it is one of the two faiss indexes that "can guarantee exact results" ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)):

Example `exact-search-numpy` (Python 3.12.15 · faiss-cpu 1.15.1 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
import faiss
import numpy as np

from lib.metrics import evaluate
from lib.recorded import embeddings
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

product_ids, product_vectors, query_ids, query_vectors = embeddings()
test = load_queries("test").index
rows = np.isin(query_ids, test)


def top_k(scores, k):
    """Column indices of the k highest scores in each row, best first."""
    candidates = np.argpartition(-scores, k - 1, axis=1)[:, :k]          # the top k, in no order
    order = np.argsort(-np.take_along_axis(scores, candidates, axis=1), axis=1, kind="stable")
    return np.take_along_axis(candidates, order, axis=1)


scores = query_vectors[rows] @ product_vectors.T      # one row per test query, one column per product
top = top_k(scores, 10)
print("similarities computed:", f"{scores.size:,}")
print("similarities per query:", f"{scores.shape[1]:,}")

semantic = SemanticSearch()
same = sum(list(product_ids[found]) == list(semantic.search(query_id, 10).index)
           for query_id, found in zip(query_ids[rows], top))
print("same top 10 as lib.semantic:", same, "of", rows.sum())

flat = faiss.IndexFlatIP(product_vectors.shape[1])     # faiss's exact index: inner product with every product
flat.add(product_vectors)
_, found = flat.search(query_vectors[rows], 10)
print("same top 10 as faiss IndexFlatIP:", (found == top).all(axis=1).sum(), "of", rows.sum())
run = {query_id: list(product_ids[row]) for query_id, row in zip(query_ids[rows], top)}
print(f"ndcg@10 of the exact run: {evaluate(run, qrels('test'))['ndcg@10'].mean():.3f}")
```

Output:

```text
similarities computed: 360,000
similarities per query: 12,000
same top 10 as lib.semantic: 30 of 30
same top 10 as faiss IndexFlatIP: 30 of 30
ndcg@10 of the exact run: 0.830
```

One matrix product computes 360,000 similarities, 12,000 per query. The hand-built search returns the same top 10 as `lib.semantic` for 30 of 30 test queries, and the same as faiss for 30 of 30, so its run scores the same mean nDCG@10, 0.830. The book's shared module for vectors, `lib.vectors`, keeps this `top_k` for later examples and wraps it in `exact_search`.

What decides whether exact search is enough is its cost. Its work grows in step with the catalog: one similarity per product, for every query. Its memory is the vectors themselves:

Example `exact-search-memory` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
from lib.recorded import embeddings

# Exact search keeps every product vector in memory, as 32-bit floats.
product_ids, product_vectors, _, _ = embeddings()
print(f"products: {len(product_ids):,}")
print(f"float32 bytes per product: {product_vectors[0].nbytes:,}")
print(f"product vectors in memory, MB: {product_vectors.nbytes / 1e6:.1f}")
print(f"the same for 1,000,000 products, GB: {1_000_000 * product_vectors[0].nbytes / 1e9:.1f}")
```

Output:

```text
products: 12,000
float32 bytes per product: 3,072
product vectors in memory, MB: 36.9
the same for 1,000,000 products, GB: 3.1
```

Each product takes 3,072 bytes as 32-bit floats, the store's catalog 36.9 MB, and a million products would take 3.1 GB. The faiss authors advise deciding first "whether indexing is needed at all: indeed, in some cases a direct brute force search is the best option" ([Douze et al., 2024](https://arxiv.org/abs/2401.08281)). In our judgement, the store's catalog is such a case.

**Working rule:** We recommend exact search until it no longer fits in memory or meets your latency budget, measured with your own catalog on your own hardware. It has no settings to tune and never misses a neighbour, so it is also the ground truth for any approximate index. Store the normalized vectors as one 32-bit matrix, take the top k with `argpartition`, and sort only those.

## Trade recall for speed with HNSW {#hnsw-recall-for-speed}

When [exact search](#exact-nearest-neighbours-numpy) costs too much, an **approximate nearest-neighbour** (ANN) index skips most of its comparisons, and in return may miss some of the true nearest neighbours. Its quality is its **recall@k against exact search**: the share of exact search's top k that it also returns. That isn't the [recall@k of chapter 3](#count-relevant-in-top-k), which compares a ranking with judgments. An index with perfect recall against exact search returns what exact search returns, good or bad.

**HNSW**, short for hierarchical navigable small world, is a graph index. Each product is a node linked to some of its nearest neighbours, in a stack of layers: the bottom layer holds every product, and each layer above holds fewer. A search starts at the top, moves to whichever linked node is nearest the query, steps down a layer when it gets no closer, and at the bottom explores a list of candidates before it returns the best k ([Malkov and Yashunin, 2018](https://arxiv.org/abs/1603.09320)). In faiss, `M` sets the links per node, and more links find more true neighbours but use more memory ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)). `efConstruction`, the "expansion factor at construction time", sets how many candidates the build considers, and `efSearch`, the "expansion factor at search time", how many a search considers. faiss 1.15.1 defaults them to 40 and 16, and its graph build is deterministic: "This is the only graph build that add() uses" ([`HNSW.h`](https://raw.githubusercontent.com/facebookresearch/faiss/v1.15.1/faiss/impl/HNSW.h); [changelog](https://raw.githubusercontent.com/facebookresearch/faiss/v1.15.1/CHANGELOG.md)). So the outputs here repeat exactly. Timings differ from machine to machine, so the examples count work instead: faiss records the "number of distances computed" in each search (`HNSW.h`), which for this index are similarities. The count leaves out following links and reading memory, so treat it as a guide to speed, not a measure of it.

The store doesn't need an index, but a store with millions of products would, and a catalog small enough to check every answer is the place to learn the trade-off. Build HNSW over the store's 12,000 products with `hnsw_index(product_vectors, links=32)`, `lib.vectors`'s name for `M = 32`. Then sweep `efSearch` from 16 to 256 on the [train queries](#store-data):

Example `hnsw-efsearch-sweep` (Python 3.12.15 · faiss-cpu 1.15.1 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
import faiss
import numpy as np

from lib.recorded import embeddings
from lib.store import load_products, load_queries
from lib.vectors import EF_SEARCH_GRID, WORST_RECALL, exact_search, hnsw_index, hnsw_search, recall_against_exact

product_ids, product_vectors, query_ids, query_vectors = embeddings()
names = load_products().loc[product_ids, "name"].str[:36].to_numpy()   # by row number, cut to 36 characters
rows = np.isin(query_ids, load_queries("train").index)                 # tune on train queries only
queries = load_queries().loc[query_ids[rows], "query"].to_numpy()

index = hnsw_index(product_vectors, links=32)          # M = 32, and faiss's default efConstruction of 40
levels = faiss.vector_to_array(index.hnsw.levels)      # how many layers each product reaches
for layer in range(1, levels.max() + 1):
    print(f"products in layer {layer}: {(levels >= layer).sum():,}")

exact = exact_search(query_vectors[rows], product_vectors, 10)
print("\nefSearch  mean recall@10  worst  queries at 0  similarities per query")
sweep = {}
for ef_search in EF_SEARCH_GRID:
    found, similarities = hnsw_search(index, query_vectors[rows], 10, ef_search)
    recall = recall_against_exact(found, exact)
    sweep[ef_search] = (recall, similarities)
    print(f"{ef_search:>8}  {recall.mean():>14.3f}  {recall.min():>5.1f}  {(recall == 0).sum():>12}  {similarities:>22.0f}")

recall, similarities = sweep[16]                       # faiss's default
print(f"\nefSearch 16, recall@10 against exact: {recall.mean():.3f}")
print(f"efSearch 16, similarities computed per query: {similarities:.0f}")
print(f"efSearch 16, train queries with recall@10 of 0: {(recall == 0).sum()}")
print("efSearch 16, those queries:", ", ".join(queries[recall == 0]))
print("smallest efSearch with no query at 0:", min(ef for ef, (r, _) in sweep.items() if r.min() > 0))
chosen = min(ef for ef, (r, _) in sweep.items() if r.min() >= WORST_RECALL)
print(f"smallest efSearch with every query at {WORST_RECALL} or more:", chosen)
print(f"chosen efSearch, recall@10 against exact: {sweep[chosen][0].mean():.3f}")
print(f"chosen efSearch, similarities computed per query: {sweep[chosen][1]:.0f}\n")

found, _ = hnsw_search(index, query_vectors[rows], 3, 16)
row = list(queries).index("foutains with brick look")
for rank, (approximate, nearest) in enumerate(zip(found[row], exact[row]), start=1):
    print(f"{rank}  hnsw: {names[approximate]:<36}  exact: {names[nearest]}")
```

Output:

```text
products in layer 1: 12,000
products in layer 2: 369
products in layer 3: 10

efSearch  mean recall@10  worst  queries at 0  similarities per query
      16           0.934    0.0             2                     282
      32           0.936    0.0             2                     346
      48           0.940    0.0             2                     404
      64           0.940    0.0             2                     463
      80           0.956    0.0             1                     530
      96           0.978    0.3             0                     611
     112           0.980    0.3             0                     682
     128           0.994    0.8             0                     767
     144           0.998    0.9             0                     835
     160           0.998    0.9             0                     924
     176           0.998    0.9             0                    1020
     192           0.998    0.9             0                    1115
     208           0.998    0.9             0                    1191
     224           1.000    1.0             0                    1271
     240           1.000    1.0             0                    1349
     256           1.000    1.0             0                    1441

efSearch 16, recall@10 against exact: 0.934
efSearch 16, similarities computed per query: 282
efSearch 16, train queries with recall@10 of 0: 2
efSearch 16, those queries: foutains with brick look, sheffield home bath set
smallest efSearch with no query at 0: 96
smallest efSearch with every query at 0.9 or more: 144
chosen efSearch, recall@10 against exact: 0.998
chosen efSearch, similarities computed per query: 835

1  hnsw: dayse outdoor square cushion with fi  exact: tribeca 2 '' x 10 '' porcelain brick
2  hnsw: 3 piece wall decor set                exact: barbados 5 '' x 10 '' ceramic brick
3  hnsw: rustic autumn ivy branch              exact: kimary 0.75 '' x 1.5 '' glass brick
```

The layers hold 12,000, 369 and 10 products. At the default `efSearch` of 16, a query computes 282 similarities instead of 12,000, and mean recall@10 against exact search is 0.934. The mean hides a failure: 2 train queries get none of their true top 10. They are foutains with brick look, sheffield home bath set. For `foutains with brick look`, HNSW returns a cushion, a wall decor set and an ivy branch, while exact search's top 3 are brick-look tiles: for this query, the search ended in a part of the graph far from its true neighbours.

The smallest `efSearch` in the sweep at which no train query is at 0 is 96, but the example's table shows that its worst query still misses most of its true top 10. So choose by a stricter rule: the smallest `efSearch` at which every train query finds at least 9 of its true top 10. That is 144, with a mean recall of 0.998 and 835 similarities per query.

**Working rule:** Use an ANN index only when exact search is too slow or too large. Tune it on train queries by its recall against exact search, at the k your pipeline uses, and choose by the worst query, not the mean. We recommend the smallest `efSearch` at which every query keeps at least 9 of its true top 10, with `M = 32`. This chapter tunes only `efSearch`; `M` and `efConstruction` change the graph itself, and deserve the same sweep on a large catalog. Very different ANN methods "yield comparable quality-performance trade-offs" ([Aumüller et al., 2018](https://arxiv.org/abs/1807.05614)), so measure on your own data rather than choosing a method by reputation.

## Check the index on the test queries {#hnsw-on-test-queries}

An index tuned on train queries still has to be checked on queries it hasn't seen, by its [recall against exact search](#hnsw-recall-for-speed) and by its effect on the judged scores. In the store, these are the chapter's 2 planned test comparisons: the HNSW index at faiss's default `efSearch` of 16, and at the setting chosen on the train queries, each against exact search. A difference is established when its paired [permutation test](#permutation-test-on-queries) gives p below 0.025, with the [t-test and an interval](#when-a-difference-is-established) at the matching level beside it. The example also asks for `k = 100`, because [hybrid retrieval](#fuse-with-rrf) fuses each retriever's top 100:

Example `hnsw-test-recall` (Python 3.12.15 · faiss-cpu 1.15.1 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.metrics import evaluate
from lib.recorded import embeddings
from lib.significance import compare, verdict
from lib.store import load_queries, qrels
from lib.vectors import as_run, choose_ef_search, exact_search, hnsw_index, hnsw_search, recall_against_exact

# Planned before scoring: HNSW at faiss's default efSearch, and at the setting chosen on train, each against exact.
PLANNED = 2
threshold = 0.05 / PLANNED
product_ids, product_vectors, query_ids, query_vectors = embeddings()
rows = np.isin(query_ids, load_queries("test").index)
index = hnsw_index(product_vectors, links=32)
chosen = choose_ef_search(index, query_vectors[np.isin(query_ids, load_queries("train").index)], product_vectors)
exact = exact_search(query_vectors[rows], product_vectors, 100)
exact_ndcg = evaluate(as_run(exact, query_ids[rows], product_ids), qrels("test"))["ndcg@10"]
print("planned test comparisons:", PLANNED)
print(f"p-value threshold: {threshold:.3f}")
print("efSearch chosen on train queries:", chosen)
print(f"exact ndcg@10: {exact_ndcg.mean():.3f}")

for name, ef_search in [("default", 16), ("chosen", chosen)]:
    found, _ = hnsw_search(index, query_vectors[rows], 100, ef_search)
    recall = recall_against_exact(found[:, :10], exact[:, :10])
    ndcg = evaluate(as_run(found, query_ids[rows], product_ids), qrels("test"))["ndcg@10"]
    result = compare(ndcg, exact_ndcg, confidence=1 - threshold)
    print(f"\n{name}, recall@10 against exact: {recall.mean():.3f}")
    print(f"{name}, queries with recall@10 of 0: {(recall == 0).sum()}")
    print(f"{name}, those queries:", ", ".join(load_queries().loc[query_ids[rows][recall == 0], "query"]) or "none")
    print(f"{name}, recall@100 against exact: {recall_against_exact(found, exact).mean():.3f}")
    print(f"{name}, hnsw ndcg@10: {ndcg.mean():.3f}")
    print(f"{name}, queries whose ndcg@10 changes: {result['wins'] + result['losses']}")
    print(f"{name}, permutation p: {result['permutation p']:.3f}")
    print(f"{name}, t-test p: {result['t-test p']:.3f}")
    print(f"{name}, {1 - threshold:.1%} interval: {result['ci low']:.4f} to {result['ci high']:.4f}")
    for check, passed in verdict(result, threshold).items():      # established, t-test agrees, interval agrees
        print(f"{name}, {check}: {'yes' if passed else 'no'}")
```

Output:

```text
planned test comparisons: 2
p-value threshold: 0.025
efSearch chosen on train queries: 144
exact ndcg@10: 0.830

default, recall@10 against exact: 0.930
default, queries with recall@10 of 0: 2
default, those queries: liberty hardware francisco, 48" sliding single track , barn door for laundry
default, recall@100 against exact: 0.849
default, hnsw ndcg@10: 0.791
default, queries whose ndcg@10 changes: 3
default, permutation p: 0.256
default, t-test p: 0.154
default, 97.5% interval: -0.1544 to -0.0006
default, established: no
default, t-test agrees: yes
default, interval agrees: no

chosen, recall@10 against exact: 1.000
chosen, queries with recall@10 of 0: 0
chosen, those queries: none
chosen, recall@100 against exact: 0.994
chosen, hnsw ndcg@10: 0.830
chosen, queries whose ndcg@10 changes: 0
chosen, permutation p: 1.000
chosen, t-test p: 1.000
chosen, 97.5% interval: 0.0000 to 0.0000
chosen, established: no
chosen, t-test agrees: yes
chosen, interval agrees: yes
```

At the chosen `efSearch` of 144, recall@10 against exact search is 1.000, the nDCG@10 of 0 queries changes, and the mean nDCG@10 is 0.830, as for exact search (0.830). At the default, 2 test queries get none of their true top 10: liberty hardware francisco, 48" sliding single track , barn door for laundry. The mean nDCG@10 falls to 0.791. Only 3 queries change score, and the fall isn't established: the permutation test gives p = 0.256, and the t-test agrees with p = 0.154. The 97.5% interval, from -0.1544 to -0.0006, excludes 0, so it disagrees with the tests. With so few queries carrying the difference, the finding is the recall lost against exact search, not a measured loss of quality. Asking for more results doesn't make up for a small `efSearch`: at the default, recall@100 is 0.849, against 0.994 at the chosen setting.

The graph also costs memory, on top of the vectors:

Example `hnsw-index-memory` (Python 3.12.15 · faiss-cpu 1.15.1 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
import faiss

from lib.recorded import embeddings
from lib.vectors import hnsw_index

product_ids, product_vectors, _, _ = embeddings()
dimensions = product_vectors.shape[1]
flat = faiss.IndexFlatIP(dimensions)                    # exact search: the vectors only
flat.add(product_vectors)
index = hnsw_index(product_vectors, links=32)           # the vectors, plus the graph's links

print("links per product, upper layers:", index.hnsw.nb_neighbors(1))
print("links per product, bottom layer:", index.hnsw.nb_neighbors(0))
print(f"faiss's estimate, 4d + 8M bytes per product: {4 * dimensions + 8 * 32:,}")
for name, built in [("exact index", flat), ("hnsw index", index)]:
    print(f"bytes per product, {name}: {faiss.serialize_index(built).nbytes / len(product_ids):,.0f}")
```

Output:

```text
links per product, upper layers: 32
links per product, bottom layer: 64
faiss's estimate, 4d + 8M bytes per product: 3,328
bytes per product, exact index: 3,072
bytes per product, hnsw index: 3,344
```

Each product has 32 links on the upper layers and 64 on the bottom one, twice `M`. faiss estimates 4d + 8M bytes per vector ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)): 4 bytes for each of the d numbers, and 4 bytes for each of the 2M links on the bottom layer, 3,328 here. The saved index takes 3,344 bytes per product, against 3,072 for the exact index.

**Working rule:** Check a tuned index on held-out queries by its recall against exact search, and read the queries that lose their whole top k before the mean score. Treat a fall in nDCG@10 that rests on a handful of queries as unproven until a paired test establishes it. Budget memory for the links as well as the vectors.

## Check queries that contain digits {#embeddings-match-digits}

[An index](#hnsw-on-test-queries) can only return what the embeddings put near a query, so the next question is which queries the embeddings themselves get wrong. An encoder squeezes a whole query into one vector, so a short token that changes the meaning, such as a size, a model number or a "not", may move that vector very little. A study of 13 embedding models measured this for numbers, on synthetic financial text: their accuracy at telling texts apart by a number "is merely 0.54, slightly above random guessing (0.5)", and four-digit numbers were at the level of guessing ([Deng et al., 2026](https://aclanthology.org/2026.findings-eacl.289/)). Products aren't financial reports, so check the store's own queries.

In the store, few queries hold a digit. Compare BM25 and semantic retrieval on each of them, from both splits. This is an exploratory diagnosis: nothing is tuned on it, and a handful of queries can't establish anything:

Example `digits-in-queries` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

products, queries = load_products(), load_queries()
with_digit = queries[queries["query"].str.contains(r"\d")]       # both splits: a diagnosis, nothing is tuned
judgments = {query_id: grades for query_id, grades in qrels().items() if query_id in with_digit.index}
scores = pd.DataFrame({
    "split": with_digit["split"],
    "bm25": evaluate(LexicalSearch(products).run(with_digit, k=100), judgments)["ndcg@10"],
    "semantic": evaluate(SemanticSearch().run(with_digit, k=100), judgments)["ndcg@10"],
    "query": with_digit["query"],
}).round(3)

print("queries with a digit:", len(scores))
print(scores.to_string())
print("semantic better:", (scores["semantic"] > scores["bm25"]).sum())
print("bm25 better:", (scores["bm25"] > scores["semantic"]).sum())
print("gaps under 0.03:", ((scores["semantic"] - scores["bm25"]).abs() < 0.03).sum())

text = product_text(products).str.lower()
print("products whose text has the word 7qt:", text.str.contains(r"\b7qt\b").sum())
print("products whose text has 7 qt:", text.str.contains(r"(?<![\d.])7 qt\b").sum())
```

Output:

```text
queries with a digit: 7
          split   bm25  semantic                                             query
query_id
45        train  0.288     0.316                            70s inspired furniture
62        train  0.554     0.930                                   7qt slow cooker
101       train  0.569     0.770        48 in entry table with side by side drawer
203       train  0.606     0.740                         ge top loading washer 4.5
205       train  0.935     0.930                          ines shag rug w003096809
285        test  0.592     0.555  48" sliding single track , barn door for laundry
482        test  1.000     0.921                              48 inch kitchen hood
semantic better: 4
bm25 better: 3
gaps under 0.03: 2
products whose text has the word 7qt: 0
products whose text has 7 qt: 8
```

Of the 7 queries with a digit, semantic retrieval scores higher on 4 and BM25 on 3, and 2 of the gaps are under 0.03, so neither ranker wins them all. For `7qt slow cooker`, BM25 fails: 0 products contain the word `7qt`, while 8 write `7 qt`. For the test query `48 inch kitchen hood`, BM25 scores higher. Here is semantic retrieval's top 10 for it:

Example `hood-query-digits` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}
products = load_products()
query_id = 482
query = load_queries().at[query_id, "query"]
judgments = qrels()[query_id]
# The width sits in the attributes column, which the embeddings never saw: product_text leaves it out.
width = products["attributes"].str.extract(r"\bwidth: ([\d.]+)", expand=False).astype(float)

semantic = SemanticSearch().search(query_id, k=10).index
bm25 = LexicalSearch(products).search(query, k=10).index
print("query:", query)
print("     judgment   width  name")
for rank, product_id in enumerate(semantic, start=1):
    label = LABELS.get(judgments.get(product_id), "unjudged")
    print(f"{rank:>2}   {label:<10} {width[product_id]:>5g}  {products.at[product_id, 'name'][:50]}")

print()
for name, top in [("semantic", semantic), ("bm25", bm25)]:
    print(f"{name}, width 48 in the top 10:", (width[top] == 48).sum())
    print(f"{name}, exact in the top 10:", sum(judgments.get(product_id) == 2 for product_id in top))
```

Output:

```text
query: 48 inch kitchen hood
     judgment   width  name
 1   exact         48  48 '' 1200 cfm ducted wall mount range hood in bru
 2   exact         48  48 '' 400 cfm ducted wall mount range hood in brus
 3   exact         48  48 '' 400 cfm convertible wall mount range hood
 4   partial    35.75  36 '' ws-48 series 500 cfm ducted under cabinet ra
 5   exact         48  48 '' hand crafted designer wood island hood serie
 6   exact         48  48 '' island range hood
 7   exact         48  48 inch wall mount chimney range hood with 600 cfm
 8   exact         48  48 '' ducted island range hood
 9   exact         48  48 '' professional 900cfm ducted island range hood
10   partial     29.8  30 '' 480 cfm convertible under cabinet range hood

semantic, width 48 in the top 10: 8
semantic, exact in the top 10: 8
bm25, width 48 in the top 10: 10
bm25, exact in the top 10: 10
```

In semantic retrieval's top 10, 8 hoods have a width of 48. The others are a 36-inch hood from a series named `ws-48` and a 30-inch hood rated at 480 cfm, cubic feet per minute, the airflow of its fan. Both contain the digits 48, neither is 48 wide, and the judges marked both [partial](#store-data). Of BM25's top 10, 10 have a width of 48. For this query, the embedding matched the digits as text, not the width they stand for. The example reads each hood's width from the `attributes` column, curated fields from WANDS's product features such as width, shape and material. `product_text`, the text the model embedded, leaves that column out, so the embeddings never saw it, and a size the shopper types can be checked against it exactly.

One query can't show a pattern. To see how the model handles sizes in general, use **probe queries**: pairs of queries written for the book that differ only in a size, a code or a negation, which `recordings/probes.py` embeds with the same model. One of them repeats the test query `48 inch kitchen hood` word for word. Probes have no judgments, so the example counts what their top 10s hold and never scores them. The right size comes from the width in `attributes` for the hoods, and from the name for the rest:

Example `probe-pair-overlap` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products

# Probe queries written for the book, embedded by the same model. They have no judgments,
# so this example counts what each top 10 holds; it doesn't score anything.
probe_queries, probe_vectors = probes()
products = load_products()
names = products["name"]
width = products["attributes"].str.extract(r"\bwidth: ([\d.]+)", expand=False).astype(float)
semantic = SemanticSearch()


def states(size, unit):
    """Names that state this size, such as "7 qt" or "7-quart", but not "3.7 qt"."""
    return names.str.contains(rf"(?<![\d.]){size}[ -]?(?:{unit})")


RIGHT_SIZE = {                       # the size each probe asks for: the width attribute, or the name
    "36 inch kitchen hood": (width - 36).abs() <= 0.5, "48 inch kitchen hood": (width - 48).abs() <= 0.5,
    "4 qt slow cooker": states(4, "qt|quart"), "7 qt slow cooker": states(7, "qt|quart"),
    "twin bed": names.str.contains(r"\btwin\b"), "king bed": names.str.contains(r"\bking\b"),
    "2 seat sofa": names.str.contains(r"\bloveseat\b"),        # a two-seat sofa is a loveseat
}
DIGIT_ONLY = {"2 seat sofa": states(2, " in 1| piece"), "4 seat sofa": states(4, " in 1| piece")}

for pair in ["hood", "cooker", "bed", "seats"]:
    first, second = probe_queries.index[probe_queries["pair"] == pair]
    tops = {row: semantic.search_vector(probe_vectors[row], k=10).index for row in (first, second)}
    print(f"{pair}, similarity of the two queries: {probe_vectors[first] @ probe_vectors[second]:.3f}")
    print(f"{pair}, products in both top 10s:", len(set(tops[first]) & set(tops[second])))
    for row, top in tops.items():
        query = probe_queries.at[row, "query"]
        if query in RIGHT_SIZE:
            print(f"{query}, right size in the top 10:", RIGHT_SIZE[query][top].sum())
        if query in DIGIT_ONLY:
            print(f"{query}, same digit but a piece count or 2 in 1:", DIGIT_ONLY[query][top].sum())
    print()
print("catalog names that give a seat count:", (states(2, "seat") | states(4, "seat")).sum())
print("catalog products named loveseat:", names.str.contains(r"\bloveseat\b").sum())
```

Output:

```text
hood, similarity of the two queries: 0.795
hood, products in both top 10s: 0
36 inch kitchen hood, right size in the top 10: 8
48 inch kitchen hood, right size in the top 10: 8

cooker, similarity of the two queries: 0.841
cooker, products in both top 10s: 1
4 qt slow cooker, right size in the top 10: 6
7 qt slow cooker, right size in the top 10: 7

bed, similarity of the two queries: 0.697
bed, products in both top 10s: 0
twin bed, right size in the top 10: 10
king bed, right size in the top 10: 10

seats, similarity of the two queries: 0.759
seats, products in both top 10s: 1
2 seat sofa, right size in the top 10: 0
2 seat sofa, same digit but a piece count or 2 in 1: 4
4 seat sofa, same digit but a piece count or 2 in 1: 4

catalog names that give a seat count: 0
catalog products named loveseat: 14
```

For these probes, the model mostly finds the right size. The two hood probes share 0 products, and their top 10s hold 8 and 8 hoods of the right width. The slow-cooker probes find 6 and 7 of the right capacity, and the bed probes 10 and 10. Where the catalog has no number to match, the digit takes over. The number of product names that give a seat count is 0, and the top 10 for `2 seat sofa` holds 4 products that share only the digit, two-piece sets and "2 in 1" kids' sofas, and 0 of the catalog's 14 loveseats.

### Expect a code to carry little weight {#codes-carry-no-weight}

A product code should match one product exactly. To an encoder, it's a rare string of letters and digits. Two pairs of the [probe queries](#embeddings-match-digits) test codes: one built on a code no product holds, taken from the train query `ines shag rug w003096809`, and one built on a screen resolution that exactly one product's text holds:

Example `code-probes` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, product_text

# Probe queries written for the book, embedded by the same model; no judgments, so nothing is scored.
probe_queries, probe_vectors = probes()
products = load_products()
text = product_text(products).str.lower()
semantic, bm25 = SemanticSearch(), LexicalSearch(products)

# A code no product holds: does changing it change the results?
first, second = probe_queries.index[probe_queries["pair"] == "code"]
tops = [set(semantic.search_vector(probe_vectors[row], k=10).index) for row in (first, second)]
print("products whose text contains w003096809:", text.str.contains("w003096809").sum())
print(f"code, similarity of the two queries: {probe_vectors[first] @ probe_vectors[second]:.3f}")
print("code, products in both top 10s:", len(tops[0] & tops[1]))

# A code one product holds: where does that product rank, with its code and with another?
holder = text.index[text.str.contains("1920x1080p")]
print()
print("products whose text contains 1920x1080p:", len(holder))
print("that product:", products.at[holder[0], "name"])
print("products in the Projectors class:", (products["product_class"] == "Projectors").sum())
for row in probe_queries.index[probe_queries["pair"] == "resolution"]:
    query = probe_queries.at[row, "query"]
    ranked = semantic.search_vector(probe_vectors[row], k=len(products))
    lexical = list(bm25.search(query, k=100).index)
    print(f"{query}, its semantic rank: {list(ranked.index).index(holder[0]) + 1}")
    print(f"{query}, its similarity: {ranked[holder[0]]:.3f}")
    print(f"{query}, similarity of the next product: {ranked.drop(holder[0]).iloc[0]:.3f}")
    print(f"{query}, its bm25 rank:", lexical.index(holder[0]) + 1 if holder[0] in lexical else "not in the top 100")
```

Output:

```text
products whose text contains w003096809: 0
code, similarity of the two queries: 0.967
code, products in both top 10s: 10

products whose text contains 1920x1080p: 1
that product: 5000 portable transmissive projector
products in the Projectors class: 4
1920x1080p projector, its semantic rank: 1
1920x1080p projector, its similarity: 0.562
1920x1080p projector, similarity of the next product: 0.496
1920x1080p projector, its bm25 rank: 1
2560x1440p projector, its semantic rank: 1
2560x1440p projector, its similarity: 0.509
2560x1440p projector, similarity of the next product: 0.508
2560x1440p projector, its bm25 rank: not in the top 100
```

Changing the last digits of the unknown code leaves the two queries at a similarity of 0.967, and their top 10s share 10 products: a code that matches nothing changes nothing, and BM25 has nothing to match either. The resolution `1920x1080p` appears only in the text of the `5000 portable transmissive projector`. The embedding puts it at rank 1 for `1920x1080p projector`, at a similarity of 0.562 against 0.496 for the next product. For `2560x1440p projector` it still puts it at rank 1, at 0.509 against 0.508. The matching code widens the product's lead over the next one, but the product is one of only 4 projectors and ranks first either way. BM25 puts it at rank 1 with its code; without it, the product is not in the top 100. The code decides the lexical ranking and nudges the semantic one. In one study of questions about rare entities, dense (embedding-based) retrievers "drastically underperform sparse methods" ([Sciavolino et al., 2021](https://arxiv.org/abs/2109.08535)), while BM25 is "sensitive to highly selective keywords and phrases" ([Karpukhin et al., 2020](https://arxiv.org/abs/2004.04906)).

**Working rule:** List the queries in your log that hold sizes, quantities or codes, and compare both rankers on them before you trust either. When a code matters, match it lexically. When an exact size matters, match it against a product field such as the width in `attributes`, or lexically once the tokenizer keeps digits and units are written one way ([chapter 5](#split-text-into-terms), [chapter 8](#normalize-units)). Leave the rest of the query to semantic retrieval. [Chapter 7](#when-hybrid-helps) tests combining the two.

## Test embeddings on negation {#embeddings-on-negation}

Negation reverses what a shopper wants with one short word: a rug that is *not* round. An embedding of the whole query can stay close to the same query without that word. NevIR, a benchmark of document pairs that differ by a negation, found that "No bi-encoder architecture scores higher than 12% paired accuracy", where ranking at random scores 25% ([Weller et al., 2024](https://arxiv.org/abs/2305.07614)). In a 2025 reproduction, one 7-billion-parameter bi-encoder, GritLM-7B, reached 39.0%, other bi-encoders tested improved little, and "only cross-encoders and listwise LLM re-rankers achieve reasonable performance across both negation tasks" ([van den Elsen et al., 2025](https://arxiv.org/abs/2502.13506)).

In the store, 0 of the queries contain "no", "not", "without" or "non", so the judgments can't test negation. The example uses 3 pairs of [probe queries](#embeddings-match-digits) instead, each a query and its negation, and counts what each top 10 holds. The catalog could satisfy each negated probe: it has 42 products named armless, 62 coffee tables that never mention glass, and 90 area rugs not named round.

Before you run it, predict: how many of semantic retrieval's top 10 for `rug that is not round` are named round?

Example `negation-probes` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
import bm25s

from lib.lexical import LexicalSearch
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text

# Probe queries written for the book, with no judgments: count what the top 10 holds, never score it.
probe_queries, probe_vectors = probes()
products = load_products()
names, text = products["name"].str.lower(), product_text(products).str.lower()
semantic, bm25 = SemanticSearch(), LexicalSearch(products)
FEATURES = {"arms": ("armless", names), "glass": ("glass", text), "round": ("round", names)}

negated = load_queries()["query"].str.contains(r"\b(?:no|not|without|non)\b")
print("store queries with no, not, without or non:", negated.sum())
tokens = bm25s.tokenize(["rug that is not round"], stopwords="en", return_ids=False, show_progress=False)
print("bm25 terms of rug that is not round:", " ".join(tokens[0]))
print("products named armless:", names.str.contains(r"\barmless\b").sum())
coffee_tables = products["product_class"] == "Coffee & Cocktail Tables"
area_rugs = products["product_class"] == "Area Rugs"
print("coffee tables that never mention glass:", (coffee_tables & ~text.str.contains(r"\bglass\b")).sum())
print("area rugs not named round:", (area_rugs & ~names.str.contains(r"\bround\b")).sum())

negation = probe_queries[probe_queries["kind"] == "negation"]
print("negation probe pairs:", negation["pair"].nunique())
for row, probe in negation.iterrows():
    word, field = FEATURES[probe["pair"]]
    has_feature = field.str.contains(rf"\b{word}\b")
    semantic_top = semantic.search_vector(probe_vectors[row], k=10).index
    bm25_top = bm25.search(probe["query"], k=10).index
    print()
    print(f"{probe['query']}, semantic top 10 with {word}:", has_feature[semantic_top].sum())
    print(f"{probe['query']}, bm25 top 10 with {word}:", has_feature[bm25_top].sum())
```

Output:

```text
store queries with no, not, without or non: 0
bm25 terms of rug that is not round: rug round
products named armless: 42
coffee tables that never mention glass: 62
area rugs not named round: 90
negation probe pairs: 3

sofa with arms, semantic top 10 with armless: 1
sofa with arms, bm25 top 10 with armless: 0

sofa without arms, semantic top 10 with armless: 8
sofa without arms, bm25 top 10 with armless: 0

coffee table with glass top, semantic top 10 with glass: 10
coffee table with glass top, bm25 top 10 with glass: 9

coffee table not glass, semantic top 10 with glass: 10
coffee table not glass, bm25 top 10 with glass: 10

round rug, semantic top 10 with round: 10
round rug, bm25 top 10 with round: 10

rug that is not round, semantic top 10 with round: 10
rug that is not round, bm25 top 10 with round: 10
```

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

Example `truncate-embeddings` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

train, judgments = load_queries("train"), qrels("train")       # choose on train queries

# dims keeps the first dims numbers of every vector and rescales each to length 1 (lib.recorded).
for dims in [768, 256, 128]:
    semantic = SemanticSearch(dims=dims)
    scores = evaluate(semantic.run(train, k=100), judgments)
    print(f"{dims} dimensions, float32 bytes per product: {semantic.products[0].nbytes:,}")
    print(f"{dims} dimensions, ndcg@10: {scores['ndcg@10'].mean():.3f}")
    print(f"{dims} dimensions, judged@10: {scores['judged@10'].mean():.3f}")
    print()
```

Output:

```text
768 dimensions, float32 bytes per product: 3,072
768 dimensions, ndcg@10: 0.772
768 dimensions, judged@10: 0.964

256 dimensions, float32 bytes per product: 1,024
256 dimensions, ndcg@10: 0.762
256 dimensions, judged@10: 0.952

128 dimensions, float32 bytes per product: 512
128 dimensions, ndcg@10: 0.680
128 dimensions, judged@10: 0.874
```

At 256 dimensions a product takes 1,024 bytes instead of 3,072, and mean nDCG@10 moves from 0.772 to 0.762. At 128 it is 0.680, with [judged@10](#score-every-test-query) at 0.874 against 0.964, so part of that fall could come from products nobody judged. Is the change real, or noise among 50 queries? Test it with `lib.significance.compare`, which runs [chapter 3's permutation test](#permutation-test-on-queries), its [paired t-test](#paired-t-test-on-queries) and its [bootstrap interval](#report-the-size-of-a-gap). These comparisons use train queries, so they tune the vector size; they aren't evidence about the test queries:

Example `truncation-paired-test` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_queries, qrels

# Train queries: these comparisons tune the vector size. They are not evidence about the test queries.
train, judgments = load_queries("train"), qrels("train")


def ndcg(dims):
    return evaluate(SemanticSearch(dims=dims).run(train, k=100), judgments)["ndcg@10"]


def p_value(p):
    return "below 0.001" if p < 0.001 else f"{p:.3f}"


full = ndcg(768)
for dims in [256, 128]:
    result = compare(ndcg(dims), full)                    # paired by train query: shortened minus full
    print(f"{dims} vs 768, mean difference in ndcg@10: {result['mean difference']:.3f}")
    print(f"{dims} vs 768, queries worse: {result['losses']}")
    print(f"{dims} vs 768, permutation test p: {p_value(result['permutation p'])}")
    print(f"{dims} vs 768, paired t-test p: {p_value(result['t-test p'])}")
    print(f"{dims} vs 768, 95% bootstrap interval: {result['ci low']:.4f} to {result['ci high']:.4f}")
    print(f"{dims} vs 768, interval excludes 0: {'yes' if result['ci high'] < 0 or result['ci low'] > 0 else 'no'}")
    print(f"{dims} vs 768, effect size: {result['effect size']:.3f}")
    print()
```

Output:

```text
256 vs 768, mean difference in ndcg@10: -0.010
256 vs 768, queries worse: 24
256 vs 768, permutation test p: 0.076
256 vs 768, paired t-test p: 0.080
256 vs 768, 95% bootstrap interval: -0.0211 to -0.0002
256 vs 768, interval excludes 0: yes
256 vs 768, effect size: -0.253

128 vs 768, mean difference in ndcg@10: -0.092
128 vs 768, queries worse: 33
128 vs 768, permutation test p: below 0.001
128 vs 768, paired t-test p: below 0.001
128 vs 768, 95% bootstrap interval: -0.1569 to -0.0565
128 vs 768, interval excludes 0: yes
128 vs 768, effect size: -0.547
```

For 128 dimensions, the mean difference is -0.092, 33 train queries get worse, the permutation test gives p below 0.001, and the 95% interval, from -0.1569 to -0.0565, excludes 0: a clear loss. For 256, the mean difference is -0.010, the permutation test gives p = 0.076 and the t-test p = 0.080, yet the interval, from -0.0211 to -0.0002, excludes 0 by a hair. The tests and the interval disagree, so the evidence of a loss at 256 is borderline. The [effect size](#report-the-size-of-a-gap), -0.253 against -0.547 at 128, says any loss is the smaller of the two.

For the store, the decision follows from its size, not from the test. Its full vectors take [36.9 MB](#exact-nearest-neighbours-numpy), so there is little to save, and it keeps all 768 dimensions; its test score doesn't change. A catalog of hundreds of millions of products would weigh a saving of two-thirds against a loss that this many train queries can't pin down, and would judge more queries before it decided.

**Working rule:** Shortlist models on licence, language, size and domain, and treat benchmark ranks as a hint. Decide between models, or between vector sizes, on your own train queries with a paired test, and read the interval as well as the p-value. Shorten vectors only for a model trained for it, normalize after shortening, and only when memory or search time requires it.

## What goes wrong in production {#semantic-retrieval-in-production}

**A similarity is not a confidence.** It's tempting to show nothing when the best similarity is low. But similarities aren't on one scale across queries:

Example `similarity-scale` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.5:

```python
import numpy as np

from lib.recorded import embeddings
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

product_ids, product_vectors, query_ids, query_vectors = embeddings()
test = load_queries("test")
rows = np.isin(query_ids, test.index)
similarity = np.sort(query_vectors[rows] @ product_vectors.T, axis=1)[:, ::-1]   # best first, per query
queries = test.loc[query_ids[rows], "query"].to_numpy()

weakest = similarity[:, 0].argmin()                    # the query whose best match is least similar
strongest = similarity[:, 9].argmax()                  # the query whose 10th match is most similar
print("first query, lowest best similarity:", queries[weakest])
print(f"its best similarity: {similarity[weakest, 0]:.3f}")
judgments = qrels()[query_ids[rows][weakest]]
top = SemanticSearch().search(query_ids[rows][weakest], k=10).index
print("exact products in its top 10:", sum(judgments.get(product_id) == 2 for product_id in top))
print("second query, highest 10th similarity:", queries[strongest])
print(f"its 10th similarity: {similarity[strongest, 9]:.3f}")

cutoff = 0.5
print()
print(f"products above {cutoff} for the first query:", (similarity[weakest] > cutoff).sum())
print(f"products above {cutoff} for the second query:", (similarity[strongest] > cutoff).sum())
print(f"test queries with no product above {cutoff}:", (similarity[:, 0] <= cutoff).sum())
```

Output:

```text
first query, lowest best similarity: liberty hardware francisco
its best similarity: 0.436
exact products in its top 10: 5
second query, highest 10th similarity: kohler whitehaven farmhouse kitchen sink
its 10th similarity: 0.647

products above 0.5 for the first query: 0
products above 0.5 for the second query: 103
test queries with no product above 0.5: 2
```

On the test queries, `liberty hardware francisco` has the weakest best match, at 0.436, yet its top 10 holds 5 exact products. `kohler whitehaven farmhouse kitchen sink` has the most similar 10th match, at 0.647. A cutoff of 0.5 would keep 0 products for the first query and 103 for the second, and nothing for 2 test queries. Nor does semantic search ever come back empty: a [code that no product holds](#codes-carry-no-weight) still gets a full top 10. Decide that a query has no match some other way, for example when lexical retrieval finds none of its rare terms.

**Mismatched vectors fail silently.** Query and product vectors must come from the same model, revision and prompts. Vectors from two models are numbers in different spaces, and when the two have the same dimension, comparing them raises no error. Sentence Transformers adds a model's query prompt when you call `encode_query`, which uses "a predefined “query” prompt, if available" ([API reference](https://sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html)). Make sure the code that embeds live queries does what the indexing code did.

**An index doesn't follow the catalog by itself.** faiss's HNSW "does not support removing vectors from the index" ([faiss wiki](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)), so a discontinued product stays in the graph until you filter it out of results or rebuild. "Faiss is not a database": it has no concurrent writes, sharding or transactions ([Douze et al., 2024](https://arxiv.org/abs/2401.08281)). Recall against exact search belongs to one catalog and one set of settings, so measure it again after every rebuild.

**Long texts are cut short.** The model reads at most 512 tokens, and Sentence Transformers says "Longer inputs will be truncated" ([API reference](https://sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html)). The store's longest product is 201 tokens, but in a catalog with long descriptions the model never reads what falls past the limit. Count tokens before you embed, as `recordings/embeddings.py` does.

**Typos move vectors.** For BERT-based retrievers not trained on misspellings, "typos can lead to a significant drop in retrieval and ranking effectiveness" ([Zhuang and Zuccon, 2021](https://arxiv.org/abs/2108.12139)). 4 of the store's queries contain a typo, and the probes include each one spelled correctly. A corrected probe asks for the same thing as its query, so the example scores it with that query's judgments:

Example `spelling-probes` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.5:

```python
from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

# Each spelling probe is the correctly spelled text of one store query (of_query_id), embedded by the same
# model. It asks for the same thing, so it is scored with that query's judgments. A diagnosis, not a test.
probe_queries, probe_vectors = probes()
products, queries, judgments = load_products(), load_queries(), qrels()
semantic, bm25 = SemanticSearch(), LexicalSearch(products)

spelling = probe_queries[probe_queries["kind"] == "spelling"]
for row, probe in spelling.iterrows():
    query_id, pair = int(probe["of_query_id"]), probe["pair"]
    typed, corrected = semantic.search(query_id, k=10).index, semantic.search_vector(probe_vectors[row], k=10).index
    print(f"{pair}: {queries.at[query_id, 'query']} | {probe['query']} ({queries.at[query_id, 'split']} query)")
    print(f"{pair}, similarity of the two spellings: {semantic.query_vectors[query_id] @ probe_vectors[row]:.3f}")
    print(f"{pair}, products in both semantic top 10s:", len(set(typed) & set(corrected)))
    print(f"{pair}, semantic ndcg@10 as typed: {ndcg_at_k(list(typed), judgments[query_id], 10):.3f}")
    print(f"{pair}, semantic ndcg@10 corrected: {ndcg_at_k(list(corrected), judgments[query_id], 10):.3f}")
    for name, text in [("as typed", queries.at[query_id, "query"]), ("corrected", probe["query"])]:
        print(f"{pair}, bm25 ndcg@10 {name}: {ndcg_at_k(list(bm25.search(text, k=10).index), judgments[query_id], 10):.3f}")
    print()
print("spelling probes:", len(spelling))
print(f"smallest two-sided permutation p-value possible with {len(spelling)} queries: {2 / 2 ** len(spelling):.3f}")
```

Output:

```text
ligth: ligth bulb | light bulb (train query)
ligth, similarity of the two spellings: 0.710
ligth, products in both semantic top 10s: 5
ligth, semantic ndcg@10 as typed: 1.000
ligth, semantic ndcg@10 corrected: 1.000
ligth, bm25 ndcg@10 as typed: 0.945
ligth, bm25 ndcg@10 corrected: 0.945

foutains: foutains with brick look | fountains with brick look (train query)
foutains, similarity of the two spellings: 0.668
foutains, products in both semantic top 10s: 0
foutains, semantic ndcg@10 as typed: 0.353
foutains, semantic ndcg@10 corrected: 0.645
foutains, bm25 ndcg@10 as typed: 0.356
foutains, bm25 ndcg@10 corrected: 0.507

desins: twin over full bunk beds cool desins | twin over full bunk beds cool designs (train query)
desins, similarity of the two spellings: 0.829
desins, products in both semantic top 10s: 6
desins, semantic ndcg@10 as typed: 0.565
desins, semantic ndcg@10 corrected: 0.616
desins, bm25 ndcg@10 as typed: 0.488
desins, bm25 ndcg@10 corrected: 0.488

ice-an: refrigerator with ice an water in door | refrigerator with ice and water in door (test query)
ice-an, similarity of the two spellings: 0.975
ice-an, products in both semantic top 10s: 9
ice-an, semantic ndcg@10 as typed: 0.807
ice-an, semantic ndcg@10 corrected: 0.829
ice-an, bm25 ndcg@10 as typed: 0.501
ice-an, bm25 ndcg@10 corrected: 0.501

spelling probes: 4
smallest two-sided permutation p-value possible with 4 queries: 0.125
```

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
