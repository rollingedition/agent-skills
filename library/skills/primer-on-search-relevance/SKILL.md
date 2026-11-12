---
name: primer-on-search-relevance
description: "Use when evaluating or improving search ranking: grading relevance judgments, scoring rankings with nDCG, precision and MRR, deciding with a permutation test and bootstrap interval whether one ranker beats another, checking LLM relevance judgments against people, tuning BM25, semantic retrieval with embeddings and HNSW, hybrid retrieval with min-max blends or reciprocal rank fusion, query spelling, synonyms, classification and LLM rewrites, learning to rank with LambdaMART, cross-encoder and LLM reranking, evaluating retrieval for RAG answers and agents, and testing a search change before shipping with URisk, A/B tests, power and interleaving. Teaches product search on a public furniture and home-goods product-search dataset, in Python."
license: CC-BY-4.0
compatibility: "The book's examples ran on Python 3.12.15 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "A Primer on Search Relevance"
  edition: "2026.11.6"
  verified: "2026-11-12"
  examples: "132 of 132 examples pass"
  edition-code: "R33J-KWQ9"
  source: "https://rollingedition.com/primer-on-search-relevance"
---

# A Primer on Search Relevance

This agent skill is *A Primer on Search Relevance*, Edition 2026.11.6, from Rolling Edition. Examples passed Nov 12, 2026: 132 of 132 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `primer-on-search-relevance` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `R33J-KWQ9` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/primer-on-search-relevance
- **Credit the book** when you quote it or reuse its code: A Primer on Search Relevance, Edition 2026.11.6, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `primer-on-search-relevance` plugin and the zip on the book's page at rollingedition.ai.

## Grade relevance and prepare judgments

**When:** you are about to evaluate a search system and need to know what its judgments can support.

1. Before blaming a ranker for missing an exact product, check whether any field it reads says what the judges saw ([Judge relevance against the shopper's need](https://rollingedition.com/primer-on-search-relevance/s/relevance-is-a-judgment)).
2. Keep one grade per pair, prefer the lower one, and write down the rule ([Expect judges to disagree on some pairs](https://rollingedition.com/primer-on-search-relevance/s/judges-disagree-on-some-pairs)).
3. Collect graded judgments ([Grade relevance instead of yes or no](https://rollingedition.com/primer-on-search-relevance/s/graded-relevance)). Fix the gains before comparing rankers and report them with every score ([Choose the gains on purpose](https://rollingedition.com/primer-on-search-relevance/s/gains-are-a-choice)).
4. Print each query's label mix before averaging any metric ([Read the label mix of each query](https://rollingedition.com/primer-on-search-relevance/s/label-mix-per-query)).
5. Use judgments, not clicks, as the reference ([Treat clicks as biased evidence](https://rollingedition.com/primer-on-search-relevance/s/clicks-are-not-judgments)), and find out which systems built the judgment pool ([Know where the judgments came from](https://rollingedition.com/primer-on-search-relevance/s/pooled-judgments)).
6. Report judged@10 next to every nDCG@10, and compute condensed scores only as a diagnostic, never as the headline; when two rankers' judged@10 differ, have their unjudged top-10 products judged ([Count unjudged products before you compare scores](https://rollingedition.com/primer-on-search-relevance/s/unjudged-results)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/unjudged-results) and compare its `mean judged@10` line, 0.927, and its check that the hand-built value matches the library: 30 of 30.

**Pitfalls:** judgments go stale, so date them and track judged@10 in production; guidelines shape the whole set; judges may see more than the ranker ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/what-relevance-means-in-production)).

## Score a ranking with nDCG and other metrics

**When:** you need a score per query, and a mean, for a ranking against graded judgments.

1. Use precision@10 for how much of the first page is right; don't make recall@10 a headline when queries have many relevant products ([Count the relevant products in the top k](https://rollingedition.com/primer-on-search-relevance/s/count-relevant-in-top-k)).
2. Use MRR as the headline only when the user needs one right product ([Score the first relevant result with reciprocal rank](https://rollingedition.com/primer-on-search-relevance/s/score-the-first-relevant-result)).
3. Compute nDCG@10 with linear gains, a log2(i + 1) discount and an ideal ranking from every judged product, and state the variant with every number ([Build nDCG from discounted gains](https://rollingedition.com/primer-on-search-relevance/s/build-ndcg-from-dcg)).
4. Check it against scikit-learn's `ndcg_score` with every judged product in each row, after checking each run holds at least k products and, when passing raw scores, breaking ties by product ID ([Match scikit-learn's `ndcg_score`](https://rollingedition.com/primer-on-search-relevance/s/match-scikit-learn-ndcg)).
5. Write down the headline metric, gains and cutoff before comparing, and never change them after seeing which ranker they favour ([Choose a metric before you compare](https://rollingedition.com/primer-on-search-relevance/s/choose-a-ranking-metric)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/match-scikit-learn-ndcg) and compare its `largest difference` line: 0.000.

**Pitfalls:** tied scores make runs non-repeatable; unjudged products lower a ranker's score ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/measuring-search-in-production)).

## Decide whether one ranker beats another

**When:** rankers have per-query scores on the same judged queries, and someone wants to act on the gap.

1. Print the mean and median difference, wins, losses and ties, and the largest losses, then read those queries ([Read per-query differences, not only the mean](https://rollingedition.com/primer-on-search-relevance/s/read-per-query-differences)).
2. List the planned comparisons before reporting any. A difference is established only when its permutation p-value is below the significance level divided by the number of planned comparisons; label later comparisons exploratory ([Decide in advance what counts as established](https://rollingedition.com/primer-on-search-relevance/s/when-a-difference-is-established)).
3. Run a paired permutation test on the per-query differences, and read a p-value above the threshold as "no evidence of a difference" ([Test a gap with a permutation test](https://rollingedition.com/primer-on-search-relevance/s/permutation-test-on-queries)).
4. Report the paired t-test beside it, and say when the two disagree ([Get the p-value from a paired t-test](https://rollingedition.com/primer-on-search-relevance/s/paired-t-test-on-queries)).
5. Report the bootstrap interval and effect size, and decide before testing what gap justifies the change's cost ([Report how big the gap is](https://rollingedition.com/primer-on-search-relevance/s/report-the-size-of-a-gap)).
6. Report each run's nDCG@10 and judged@10, then one column per comparison ([Compare runs in an evaluation harness](https://rollingedition.com/primer-on-search-relevance/s/compare-runs-in-a-harness)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/report-the-size-of-a-gap) and compare its `semantic minus bm25 bca interval and 0` line: excludes 0.

**Pitfalls:** one split can mislead, and reusing test queries is testing many hypotheses, so log every comparison on them ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/measuring-search-in-production)).

## Get judgments from an LLM and check them against people

**When:** you want an LLM to grade query-product pairs, or to trust scores from its grades.

1. Give the LLM the guidelines people use, plus a rule for what it can't see ([Write judging guidelines](https://rollingedition.com/primer-on-search-relevance/s/write-judging-guidelines)).
2. On pairs drawn the way you will use the judge, report kappa with observed agreement ([Measure agreement beyond chance with kappa](https://rollingedition.com/primer-on-search-relevance/s/agreement-beyond-chance)), linear weighted kappa with far misses counted apart ([Give near misses partial credit with weighted kappa](https://rollingedition.com/primer-on-search-relevance/s/weighted-kappa-for-grades)), and the label mix ([Read kappa against the label mix](https://rollingedition.com/primer-on-search-relevance/s/kappa-depends-on-label-mix)).
3. Read the confusion matrix before kappa and name the errors' direction for that pool ([Read the direction of the LLM's errors](https://rollingedition.com/primer-on-search-relevance/s/read-llm-error-direction)); check whether the evidence was in what the LLM saw ([Compare what the LLM saw with what the judges saw](https://rollingedition.com/primer-on-search-relevance/s/what-the-llm-saw)).
4. Record every prompt word for word with the model version, run two prompts, and trust a conclusion only when both give it ([Measure how much the prompt changes the labels](https://rollingedition.com/primer-on-search-relevance/s/prompt-sensitivity)).
5. Fill unjudged pairs with LLM grades only as a diagnostic, beside the human-only score ([Fill unjudged pairs with LLM grades](https://rollingedition.com/primer-on-search-relevance/s/fill-unjudged-with-llm-grades)).
6. When checking whether LLM grades order rankers as people do, report Kendall's tau with the list of swapped pairs, never alone, then test whether the swapped pairs differ at all ([Check whether LLM grades order the rankers the same way](https://rollingedition.com/primer-on-search-relevance/s/system-order-human-versus-llm)).
7. Never ship on LLM grades alone ([Rerun the planned comparisons with LLM grades](https://rollingedition.com/primer-on-search-relevance/s/llm-graded-verdicts)); correct a score from LLM grades with a random human-judged sample of queries ([Correct LLM scores with a human sample](https://rollingedition.com/primer-on-search-relevance/s/calibrate-on-a-human-sample)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/agreement-beyond-chance) and compare its `kappa by hand, short prompt` line, 0.432, with `kappa from scikit-learn, short prompt`: 0.432.

**Pitfalls:** a different model version or prompt is a different judge; systems tuned to the judge score well on it; product text can steer it; choose prompts on train queries ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/judgments-from-people-and-llms-in-production)).

## Build and tune lexical retrieval with BM25

**When:** you are building, debugging or tuning keyword search.

1. Print the terms queries and products become, through one tokenizer ([Split product text into terms](https://rollingedition.com/primer-on-search-relevance/s/split-text-into-terms)), and look up a failing query's terms in the index before changing scoring ([Build an inverted index](https://rollingedition.com/primer-on-search-relevance/s/build-an-inverted-index)).
2. Serve BM25 from a library and check it against a small version of your own, comparing tokenizers before formulas ([Rebuild BM25 by hand to match bm25s](https://rollingedition.com/primer-on-search-relevance/s/bm25-from-scratch)).
3. Stem products and queries alike, and read the products a stem adds ([Stem terms so word forms match](https://rollingedition.com/primer-on-search-relevance/s/stem-word-forms)).
4. Choose each change on train queries and keep it only on an established test gain ([Check stemming on the test queries](https://rollingedition.com/primer-on-search-relevance/s/check-stemming-on-test)); tune `k1` and `b` on train when what you index changes ([Tune BM25's parameters on train queries](https://rollingedition.com/primer-on-search-relevance/s/tune-bm25-parameters)).
5. Weight a field before saturation, with BM25F or by repeating it, not by adding field scores ([Weight the product name above the description](https://rollingedition.com/primer-on-search-relevance/s/weight-the-product-name)). Index attribute values without their names ([Index product attributes as a field](https://rollingedition.com/primer-on-search-relevance/s/index-attributes-as-a-field)), and prefer a measured phrase bonus to a filter ([Match phrases with term positions](https://rollingedition.com/primer-on-search-relevance/s/match-phrases-with-positions)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/bm25-from-scratch) and compare its `same top 100 for every query` line: yes.

**Pitfalls:** index and queries drift apart; sizes and codes don't survive tokenizing; IDF depends on the catalog; a BM25 score has no fixed scale, so cut by rank ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/lexical-retrieval-in-production)).

## Retrieve by meaning with embeddings and HNSW

**When:** you are adding or checking embedding-based retrieval.

1. Embed with the same model, revision and prompts on both sides, recorded with the vectors, and check the longest product fits the input limit ([Turn text into embeddings](https://rollingedition.com/primer-on-search-relevance/s/turn-text-into-embeddings)).
2. Normalize vectors when stored and after any change, then rank by dot product ([Compare embeddings with cosine similarity](https://rollingedition.com/primer-on-search-relevance/s/compare-with-cosine-similarity)).
3. Use exact search while it fits memory and latency; it is the ground truth for any index ([Find the exact nearest neighbours with NumPy](https://rollingedition.com/primer-on-search-relevance/s/exact-nearest-neighbours-numpy)).
4. Tune an HNSW index's `efSearch` on train queries by recall against exact search, choosing by the worst query ([Trade recall for speed with HNSW](https://rollingedition.com/primer-on-search-relevance/s/hnsw-recall-for-speed)), then check it on held-out queries ([Check the index on the test queries](https://rollingedition.com/primer-on-search-relevance/s/hnsw-on-test-queries)).
5. List the queries that hold sizes, quantities or codes and compare both rankers on them ([Check queries that contain digits](https://rollingedition.com/primer-on-search-relevance/s/embeddings-match-digits)); match codes lexically ([Expect a code to carry little weight](https://rollingedition.com/primer-on-search-relevance/s/codes-carry-no-weight)); don't rely on retrieval for negation ([Test embeddings on negation](https://rollingedition.com/primer-on-search-relevance/s/embeddings-on-negation)).
6. Decide between models or vector sizes on your train queries with a paired test ([Truncate dimensions, then test the loss](https://rollingedition.com/primer-on-search-relevance/s/truncate-dimensions-test-loss)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/exact-nearest-neighbours-numpy) and compare its `same top 10 as faiss IndexFlatIP` line: 30 of 30.

**Pitfalls:** a similarity is not a confidence; mismatched vectors fail silently; an index doesn't follow the catalog; long texts are cut short; typos move vectors ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/semantic-retrieval-in-production)).

## Combine lexical and semantic retrieval

**When:** you are considering a hybrid of two retrievers.

1. On train queries, count where each retriever wins and what their union adds ([Find the queries each retriever wins](https://rollingedition.com/primer-on-search-relevance/s/queries-each-retriever-wins)).
2. Check each retriever alone; give a weaker one a tuned weight, not an equal vote ([Check each retriever before you fuse](https://rollingedition.com/primer-on-search-relevance/s/check-each-retriever-before-fusing)).
3. Never add raw scores; normalize per query with min-max and tune α on train ([Normalize scores before you add them](https://rollingedition.com/primer-on-search-relevance/s/normalize-scores-before-adding)).
4. For reciprocal rank fusion, keep k = 60 and fuse lists at least 100 deep ([Test reciprocal rank fusion's settings on train queries](https://rollingedition.com/primer-on-search-relevance/s/rrf-settings-on-train)).
5. Tune one weight on a coarse grid ([Tune the blend's weight on train queries](https://rollingedition.com/primer-on-search-relevance/s/tune-blend-on-train)), then bootstrap and reverse ties to check it holds ([Check that the tuned weight is stable](https://rollingedition.com/primer-on-search-relevance/s/tuned-weight-stability)).
6. Adopt a blend only when it beats the best single retriever on held-out queries ([Report the tuned blends on test queries](https://rollingedition.com/primer-on-search-relevance/s/report-blends-on-test)); start with weighted RRF when you have ranks only ([Decide when hybrid retrieval pays](https://rollingedition.com/primer-on-search-relevance/s/when-hybrid-helps)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/report-blends-on-test) and compare its `weighted sum established` line: False.

**Pitfalls:** two retrievers cost two of everything; short lists drop candidates; min-max is relative; a tuned weight belongs to one pair of retrievers ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/hybrid-retrieval-in-production)).

## Understand and rewrite queries

**When:** you are adding spelling correction, unit rules, synonyms, query classes or LLM rewrites.

1. Correct only words the catalog lexicon doesn't hold, checking each word's neighbours ([Correct spelling against the catalog's words](https://rollingedition.com/primer-on-search-relevance/s/correct-spelling-from-catalog)).
2. Write unit rules from the catalog's text and apply them to products and queries together ([Normalize units the way the catalog writes them](https://rollingedition.com/primer-on-search-relevance/s/normalize-units)).
3. Write each synonym from a failing query and keep it only on a held-out gain ([Expand queries with a synonym list](https://rollingedition.com/primer-on-search-relevance/s/expand-with-synonyms)).
4. Check a query classifier against judged exact products' classes ([Train a query classifier on product text](https://rollingedition.com/primer-on-search-relevance/s/classify-queries-from-products)), and boost the predicted class instead of filtering ([Boost the predicted class instead of filtering](https://rollingedition.com/primer-on-search-relevance/s/boost-predicted-class)).
5. Test an LLM rewrite or HyDE on held-out queries before using it, reading losses for dropped requirements; with HyDE, always average the query's own embedding in ([Rewrite queries with an LLM](https://rollingedition.com/primer-on-search-relevance/s/rewrite-queries-with-llm), [Search with a hypothetical product (HyDE)](https://rollingedition.com/primer-on-search-relevance/s/hyde-hypothetical-products)).
6. Never search a follow-up alone ([Turn a follow-up into a standalone query](https://rollingedition.com/primer-on-search-relevance/s/standalone-follow-ups)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/correct-spelling-from-catalog) and compare its `same as lib.queries.correct_query` line: True.

**Pitfalls:** each rewrite is a model call on the query's path; the lexicon and classifier must follow the catalog; rewrites surface unjudged products ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/understanding-queries-in-production)).

## Learn to rank and rerank

**When:** you are training a learned ranker or adding a cross-encoder or LLM reranker.

1. Compare each feature by grade on train queries, and compute features with one code path ([Describe each candidate with features](https://rollingedition.com/primer-on-search-relevance/s/ranking-features)).
2. Train with a gradient weighted by your metric, as LambdaMART does ([Learn a ranking from pairs of products](https://rollingedition.com/primer-on-search-relevance/s/learn-from-pairs)). In LightGBM, pass `group`, set `label_gain`, stop early on held-out train queries, fix seed and threads, and order candidates by ID ([Train LambdaMART with LightGBM](https://rollingedition.com/primer-on-search-relevance/s/train-lambdamart)).
3. Adopt it only on an established test gain, after reading its gain importance ([Report LambdaMART on the test queries](https://rollingedition.com/primer-on-search-relevance/s/lambdamart-on-test-queries)).
4. Rerank your strongest retrieval at a depth fixed in advance ([Rerank semantic retrieval with a cross-encoder](https://rollingedition.com/primer-on-search-relevance/s/rerank-semantic-with-cross-encoder)).
5. For LLM rerankers, fix the tie-break ([Score each product with an LLM](https://rollingedition.com/primer-on-search-relevance/s/llm-pointwise-reranking)), check each listwise answer for missing or repeated numbers ([Order the 20 products with one LLM prompt](https://rollingedition.com/primer-on-search-relevance/s/llm-listwise-reranking)), and run each query in two orders ([Reverse the input to measure positional bias](https://rollingedition.com/primer-on-search-relevance/s/llm-position-bias)).
6. Set the depth on train queries from calls and characters per query ([Set the rerank depth from a budget](https://rollingedition.com/primer-on-search-relevance/s/rerank-depth-from-budget)); distil only a reranker with an established gain ([Distill the cross-encoder into a small ranker](https://rollingedition.com/primer-on-search-relevance/s/distill-the-cross-encoder)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/llm-position-bias) and compare its `tau between the two answers, mean` line: 0.311.

**Pitfalls:** features drift; row order leaks into training; LLM judges favour LLM rerankers; give each stage a time limit and a fallback ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/ranking-in-production)).

## Evaluate retrieval for RAG answers and agents

**When:** retrieval feeds an LLM's answer or an agent's search tool.

1. Put a few retrieved items in the prompt, choosing how many on train queries ([Put retrieved products in the prompt](https://rollingedition.com/primer-on-search-relevance/s/put-retrieved-products-in-the-prompt)).
2. Score answers by their cited items' human grades, count answers that recommend nothing, and keep a random context as a floor ([Score each answer by the products it cites](https://rollingedition.com/primer-on-search-relevance/s/retrieval-bounds-the-answer)).
3. Check every cited ID is in the context before a user sees it ([Check every citation against the context](https://rollingedition.com/primer-on-search-relevance/s/check-citations-against-context)); calibrate any support check on a human sample ([Check what the cited product supports](https://rollingedition.com/primer-on-search-relevance/s/check-citation-support)).
4. Report the context's precision@k from your judgments, with recall@k beside it ([Measure the context, then the answer](https://rollingedition.com/primer-on-search-relevance/s/measure-the-context)).
5. Index short items whole; chunk long ones with the title in front ([Choose the retrievable unit](https://rollingedition.com/primer-on-search-relevance/s/choose-the-retrievable-unit)).
6. Read an agent's traces and add its searches to your test queries ([Read an agent's searches from its trace](https://rollingedition.com/primer-on-search-relevance/s/read-agent-searches)); test its tool's retriever on its searches and picks ([Compare the retrievers behind the agent's tool](https://rollingedition.com/primer-on-search-relevance/s/retriever-behind-agent-tool)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/check-citations-against-context) and compare its `answers that cite an ID outside their context` line: 0.

**Pitfalls:** model, prompt and context are one system; abstentions move with retrieval; product text reaches the prompt; agent traffic is a different workload ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/retrieval-for-llm-applications-in-production)).

## Test a change before shipping it

**When:** a candidate ranker is ready and you must decide whether to ship it.

1. Diff the candidate against the baseline per query on a regression set nothing is tuned on, and read every loss ([Diff two runs query by query](https://rollingedition.com/primer-on-search-relevance/s/diff-runs-per-query)).
2. Report URisk with α = 1 beside the mean change; don't ship when it is negative ([Weigh losses more than wins with URisk](https://rollingedition.com/primer-on-search-relevance/s/weigh-losses-with-urisk)).
3. Rescore both runs with each side's unjudged products as exact; if the leader changes, judge them ([Judge the products a new ranker surfaces](https://rollingedition.com/primer-on-search-relevance/s/judge-new-results)).
4. Choose every setting on train queries and log each look at the test queries ([Keep the test queries out of every choice](https://rollingedition.com/primer-on-search-relevance/s/keep-test-queries-held-out)).
5. Before an A/B test, fix the metric and guardrails, run an A/A test, check the sample ratio, and read once at the planned size ([Run an A/B test](https://rollingedition.com/primer-on-search-relevance/s/run-an-ab-test)), sized from power ([Size the test with power](https://rollingedition.com/primer-on-search-relevance/s/size-tests-with-power)).
6. To learn which ranking users prefer, use team-draft interleaving ([Interleave two rankings with team draft](https://rollingedition.com/primer-on-search-relevance/s/team-draft-interleaving)); on real traffic, fix the number of searches in advance and decide with a sign test, and never treat simulated verdicts as evidence ([Rehearse interleaving with simulated shoppers](https://rollingedition.com/primer-on-search-relevance/s/simulate-interleaving-with-clicks)).
7. When offline and online disagree, find the cause ([Find the cause when offline and online disagree](https://rollingedition.com/primer-on-search-relevance/s/offline-online-disagree)). Ship only when every checklist item passes ([Decide whether to ship](https://rollingedition.com/primer-on-search-relevance/s/decide-whether-to-ship)).

**Check:** run [the example](https://rollingedition.com/primer-on-search-relevance/s/run-an-ab-test) and compare its `significant on some day, checked daily` line, 0.231, with `significant at the planned end`: 0.053.

**Pitfalls:** the dashboard invites peeking; groups don't match the plan; the regression set wears out; ties move results ([What goes wrong in production](https://rollingedition.com/primer-on-search-relevance/s/testing-changes-in-production)).
