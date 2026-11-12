---
title: "A Primer on Search Relevance"
chapter: "Testing changes"
chapter_id: testing-changes
book: primer-on-search-relevance
edition: 2026.11.6
verified: 2026-11-12
edition_code: R33J-KWQ9
canonical: https://rollingedition.com/primer-on-search-relevance/testing-changes
license: CC BY 4.0
attribution: "“Testing changes,” chapter 11 of A Primer on Search Relevance, Edition 2026.11.6, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/primer-on-search-relevance/testing-changes. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Testing changes

By the end of this chapter you can decide whether a change to search should ship: diff two rankers' results query by query, keep your test queries from flattering a change, size an A/B test, and compare two rankers by interleaving their results.

The store, the online furniture and home-goods retailer that is this book's running case ([chapter 1](#store-data)), still runs [BM25](#rank-with-bm25) in its search box, as its baseline. The offline work of the earlier chapters made [semantic retrieval](#search-by-meaning) the ranker to beat, with an established lead ([chapter 3](#compare-runs-in-a-harness)). Switching is a change, and so is every tweak that follows: a cheaper embedding, a blend weight, a reranker. Each raises the same four questions. Did the average go up, by more than noise? Which queries got worse? Can the judgments score the new results at all? Will shoppers behave the way the judgments predict? This chapter answers them in that order. The store's 30 test queries become its regression set, the fixed queries every change is tested on, and every choice is made on its 50 train queries. The store has no click logs, so the online sections simulate shoppers, with each simulation's assumptions stated beside it.

The chapter plans one comparison on the test queries: semantic retrieval against BM25. Following [chapter 3](#compare-runs-in-a-harness), a difference counts as established when its paired permutation test gives a p-value below 0.05 divided by the number of planned comparisons, so below 0.05 here. Every other score on the test queries in this chapter is a demonstration, and says so.

## Diff two runs query by query {#diff-runs-per-query}

The first two questions, whether the average went up and which queries got worse, are answered on a **regression set**: a fixed set of queries, with judgments, that every change runs against before it ships. The ranker the store runs today is the **baseline**, and the change is the **candidate** ranker. Each produces a [run](#score-every-test-query): its rankings for every query in the set. Comparing the runs' means isn't enough, because a change can raise the average and still make some queries worse. TREC, the Text REtrieval Conference's shared evaluations of search systems, built a whole task around that risk in its 2013 Web track, scoring each system's wins and losses per query against a baseline ([Collins-Thompson et al., 2014](https://trec.nist.gov/pubs/trec22/papers/WEB.OVERVIEW.pdf)). So diff the two runs: one row per query, with the baseline's score, the candidate's score and the change. Then count the wins, losses and ties, and read the losses.

In the store, the baseline is BM25 and the candidate is semantic retrieval, both scored with [nDCG@10](#score-one-ranking) on the test queries. This is the chapter's one planned comparison. The example builds the diff with pandas, and takes the tests from `lib.significance`, which [chapter 3](#compare-runs-in-a-harness) builds by hand: the [permutation test](#permutation-test-on-queries), the [paired t-test](#paired-t-test-on-queries) and the [bootstrap interval](#report-the-size-of-a-gap), at the confidence level that matches the threshold. The bootstrap and the permutation test resample at random, so `lib.significance` seeds SciPy with `rng` ([chapter 3](#permutation-test-on-queries)).

Example `diff-semantic-against-bm25` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

PLANNED_COMPARISONS = 1                      # this chapter's tests on the test queries
threshold = 0.05 / PLANNED_COMPARISONS       # Bonferroni: one comparison keeps 0.05

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
baseline = evaluate(LexicalSearch(products).run(queries, k=100), judgments)      # what the store runs
candidate = evaluate(SemanticSearch().run(queries, k=100), judgments)            # the change

diff = pd.DataFrame({"query": queries["query"], "bm25": baseline["ndcg@10"], "semantic": candidate["ndcg@10"]})
diff["change"] = (diff["semantic"] - diff["bm25"]).round(3)        # one row per test query

print(f"bm25 ndcg@10: {diff['bm25'].mean():.3f}")
print(f"semantic ndcg@10: {diff['semantic'].mean():.3f}")
result = compare(candidate["ndcg@10"], baseline["ndcg@10"], confidence=1 - threshold)    # chapter 3's comparison
print(f"mean change: {result['mean difference']:.3f}")
print(f"threshold: {threshold:g}")
print(f"permutation test p: {result['permutation p']:.3f}")
print(f"paired t-test p: {result['t-test p']:.3f}")
print(f"{(1 - threshold) * 100:g}% interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
print("established:", "yes" if result["permutation p"] < threshold else "no")
print("wins:", (diff["change"] > 0).sum())
print("losses:", (diff["change"] < 0).sum())
print("ties:", (diff["change"] == 0).sum())
print(f"largest loss: {diff['change'].min():.3f}")
print()
print(diff[diff["change"] < 0].sort_values("change").round(3).to_string())
```

Output:

```text
bm25 ndcg@10: 0.725
semantic ndcg@10: 0.830
mean change: 0.105
threshold: 0.05
permutation test p: 0.001
paired t-test p: 0.003
95% interval: 0.055 to 0.185
established: yes
wins: 21
losses: 7
ties: 2
largest loss: -0.092

                                                     query   bm25  semantic  change
query_id
292                                decorative white pillow  0.467     0.375  -0.092
293                               wood floor protector mat  0.653     0.568  -0.084
482                                   48 inch kitchen hood  1.000     0.921  -0.079
63                                        monthly calendar  1.000     0.931  -0.069
285       48" sliding single track , barn door for laundry  0.592     0.555  -0.037
72                                      fold in half table  1.000     0.965  -0.035
94                kohler whitehaven farmhouse kitchen sink  0.694     0.690  -0.004
```

The mean rises from 0.725 to 0.830, a change of 0.105. Against the threshold of 0.05, the permutation test gives 0.001, which settles whether the change is established: yes. Beside it, the t-test gives 0.003 and the 95% interval runs from 0.055 to 0.185. Semantic retrieval wins on 21 queries, loses on 7 and ties on 2.

The losses are where you learn something. The largest is -0.092, and two of them give a size in inches, `48 inch kitchen hood` and `48" sliding single track , barn door for laundry`: two queries, not a pattern. [Chapter 6](#embeddings-match-digits) tests the pattern on every query with a digit.

**Working rule:** Keep a regression set of judged queries that nothing is ever tuned on, and run every candidate against the baseline on it. List your planned comparisons first, and report each with its permutation p-value, its t-test and its interval. Count wins, losses and ties, and read every loss before you ship. When the losses seem to share a pattern, check it on train queries before you act on it, then fix that kind of query or send it to the baseline.

## Weigh losses more than wins with URisk {#weigh-losses-with-urisk}

[The per-query diff](#diff-runs-per-query) counts the losses, but the mean change still treats a query that got worse by 0.1 and one that got better by 0.1 as cancelling out. A store may not see it that way: a shopper who found a product yesterday and can't find it today has met a regression, and a slightly better ranking elsewhere doesn't repay them. Risk-sensitive evaluation counts losses more heavily than wins.

The risk-sensitive measure of the [TREC 2013 Web track](https://trec.nist.gov/pubs/trec22/papers/WEB.OVERVIEW.pdf) is URisk. For each query q, let Δ(q) be the candidate's score minus the baseline's. Add up the gains on the queries that improved, subtract the losses on the queries that got worse, counted α + 1 times, and divide by the number of queries N:

```text
URisk = (1 / N) × [ sum of Δ(q) over improved queries  −  (α + 1) × sum of |Δ(q)| over hurt queries ]
```

The track describes this as "weighting losses α + 1 times as heavily as successes", and α = 0 gives the plain average change (Collins-Thompson et al., section 4.3). The track's overview prints the loss term with Δ(q) itself, which is negative on a hurt query. We use its size, |Δ(q)|, the only reading under which α = 0 gives the average, as the overview says. α is a choice, not a fact. We use α = 1, so each loss counts double.

Compare two of the store's candidates against BM25. The first is full semantic retrieval, with all 768 numbers of each [embedding](#search-by-meaning) from `Snowflake/snowflake-arctic-embed-m-v1.5`. The second keeps only the first 128 numbers, a sixth of the memory. That is below the 256 dimensions the model's card documents, and [chapter 6](#truncate-dimensions-test-loss) rejected 128 on the train queries. We use it because on the test queries it trades gains on some queries for losses on others, which is what URisk is for. Chosen for how it behaves on test, it is a demonstration, not a planned comparison. The example writes URisk as a short function:

Example `urisk-of-two-candidates` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

ALPHA = 1                                   # each loss counts alpha + 1 times: here, double


def urisk(change, alpha):
    """Mean change per query, with every loss counted alpha + 1 times (TREC 2013 Web track)."""
    wins, losses = change.clip(lower=0).sum(), -change.clip(upper=0).sum()
    return (wins - (alpha + 1) * losses) / len(change)


products, queries, judgments = load_products(), load_queries("test"), qrels("test")
baseline = evaluate(LexicalSearch(products).run(queries, k=100), judgments)
candidates = {"semantic": SemanticSearch(), "semantic 128": SemanticSearch(dims=128)}   # all 768 numbers, or the first 128

print(f"bm25 judged@10: {baseline['judged@10'].mean():.3f}")
evaluated = {name: evaluate(search.run(queries, k=100), judgments) for name, search in candidates.items()}
for name, scores in evaluated.items():
    change = (scores["ndcg@10"] - baseline["ndcg@10"]).round(3)
    print(f"{name} judged@10: {scores['judged@10'].mean():.3f}")
    print(f"{name} mean change: {change.mean():.3f}")
    print(f"{name} wins: {(change > 0).sum()}")
    print(f"{name} losses: {(change < 0).sum()}")
    print(f"{name} largest loss: {change.min():.3f}")
    print(f"{name} urisk with alpha {ALPHA}: {urisk(change, ALPHA):.3f}")

# a demonstration, chosen for how it behaves on test: its tests describe it, and it is never established
result = compare(evaluated["semantic 128"]["ndcg@10"], baseline["ndcg@10"], confidence=0.95)
print(f"semantic 128 permutation test p: {result['permutation p']:.3f}")
print(f"semantic 128 paired t-test p: {result['t-test p']:.3f}")
print(f"semantic 128 interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
```

Output:

```text
bm25 judged@10: 0.927
semantic judged@10: 0.990
semantic mean change: 0.105
semantic wins: 21
semantic losses: 7
semantic largest loss: -0.092
semantic urisk with alpha 1: 0.092
semantic 128 judged@10: 0.920
semantic 128 mean change: 0.017
semantic 128 wins: 15
semantic 128 losses: 13
semantic 128 largest loss: -0.253
semantic 128 urisk with alpha 1: -0.033
semantic 128 permutation test p: 0.592
semantic 128 paired t-test p: 0.597
semantic 128 interval: -0.036 to 0.088
```

Full semantic retrieval's mean change is 0.105, and its URisk is 0.092. Its 7 losses are small, the largest -0.092, so doubling them costs little. The cheaper ranker's mean change is 0.017, with a permutation p-value of 0.592, a t-test p-value of 0.597 and a 95% interval from -0.036 to 0.088, which describe it and establish nothing. It wins 15 queries and loses 13, and its largest loss is -0.253. With losses counted double, its URisk is -0.033. Its mean hides the trade it makes: better results on some queries, paid for with worse results on others.

Its [judged@10](#score-every-test-query) is 0.920, against 0.927 for BM25 and 0.990 for full semantic retrieval, so some of its losses may be products nobody judged. [The next section](#judge-new-results) checks.

URisk describes risk without testing it. Dinçer et al. define a related measure, TRisk, that "is a linear transformation of the t statistic", so it can be tested like the [paired t-test](#paired-t-test-on-queries) ([Dinçer et al., 2014](https://eprints.gla.ac.uk/95215)).

**Working rule:** Report URisk with α = 1 next to the mean change for every candidate. Don't ship a candidate whose URisk is negative, whatever its mean, and read its losses to find out why. Raise α when failures are expensive, and report URisk separately on the store's most frequent queries. Use α = 0 only when a loss on one query is no worse than a gain on another.

## Judge the products a new ranker surfaces {#judge-new-results}

A new ranker's losses, such as the cheaper ranker's in [the URisk demonstration](#weigh-losses-with-urisk), may come from gaps in the judgments, which cover only the products that earlier systems found. WANDS, the source of the store's judgments, chose what to judge from products shoppers clicked or added to their carts, from a lexical engine, from a neural retriever and from a query classifier ([chapter 2](#pooled-judgments)). A ranker that differs from those surfaces products nobody judged, and the metrics give each one [grade](#store-data) 0, so its score may be too low, or exactly right. You can't tell which until someone judges them. The WANDS authors argue that "incompleteness in Product Search dataset does negatively impact the discriminative power of the evaluation" ([Chen et al., 2022](https://easychair.org/publications/preprint/wm4R)).

[Chapter 2](#unjudged-results) counts unjudged products with judged@10, the share of the top 10 that has a judgment. For testing a change, one more step helps: a sensitivity check. Rescore both runs under two scenarios, one favouring each side. In one, every unjudged product in the baseline's top 10s is exact; in the other, every unjudged product in the candidate's. Both runs are scored with the same judgments in each scenario, because nDCG's ideal ranking is built from every judgment for the query: a product judged exact raises the ideal, and so lowers the score of every run that doesn't show it. The scenarios aren't bounds, since the true judgments could mix the two. If the leader changes between them, the judgments can't decide yet.

The cheaper semantic ranker from [the URisk demonstration](#weigh-losses-with-urisk), which keeps 128 of each embedding's 768 numbers, lost 13 of the store's test queries against BM25. Before you read anything into those losses, run the check:

Example `unjudged-score-range` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np

from lib.lexical import LexicalSearch
from lib.metrics import ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(products).run(queries, k=100),
        "semantic 128": SemanticSearch(dims=128).run(queries, k=100),
        "semantic": SemanticSearch().run(queries, k=100)}


def unjudged(run):
    """(query_id, product_id) pairs in a run's top 10 that nobody judged."""
    return {(query_id, product_id) for query_id in judgments for product_id in run[query_id][:10]
            if product_id not in judgments[query_id]}


def score(run, exact=()):
    """Mean nDCG@10 with the given unjudged pairs judged exact, for every run alike: the ideal moves too."""
    scenario = {query_id: dict(grades) for query_id, grades in judgments.items()}
    for query_id, product_id in exact:
        scenario[query_id][product_id] = 2
    return np.mean([ndcg_at_k(run[query_id], scenario[query_id], 10) for query_id in scenario])


for name in ["bm25", "semantic 128"]:
    print(f"unjudged pairs in the top 10, {name}: {len(unjudged(runs[name]))}")
scenarios = {"as judged": set(), **{f"{name}'s unjudged exact": unjudged(runs[name]) for name in runs}}
scores = {(scenario, name): score(run, exact) for scenario, exact in scenarios.items() for name, run in runs.items()}
for scenario, name in [("as judged", "bm25"), ("as judged", "semantic 128"), ("bm25's unjudged exact", "bm25"),
                       ("bm25's unjudged exact", "semantic 128"), ("bm25's unjudged exact", "semantic"),
                       ("semantic 128's unjudged exact", "bm25"), ("semantic 128's unjudged exact", "semantic 128")]:
    print(f"{scenario}, {name}: {scores[scenario, name]:.3f}")
for candidate in ["semantic 128", "semantic"]:
    leaders = {scores[s, candidate] > scores[s, "bm25"] for s in scenarios}
    print(f"leader changes, {candidate} against bm25:", "yes" if len(leaders) > 1 else "no")
print("pairs to judge, semantic 128 against bm25:", len(unjudged(runs["bm25"]) | unjudged(runs["semantic 128"])))
```

Output:

```text
unjudged pairs in the top 10, bm25: 22
unjudged pairs in the top 10, semantic 128: 24
as judged, bm25: 0.725
as judged, semantic 128: 0.742
bm25's unjudged exact, bm25: 0.788
bm25's unjudged exact, semantic 128: 0.738
bm25's unjudged exact, semantic: 0.829
semantic 128's unjudged exact, bm25: 0.718
semantic 128's unjudged exact, semantic 128: 0.807
leader changes, semantic 128 against bm25: yes
leader changes, semantic against bm25: no
pairs to judge, semantic 128 against bm25: 46
```

BM25 has 22 unjudged products in its top 10s, and the cheaper ranker 24. As judged, the cheaper ranker leads, 0.742 to 0.725. If BM25's unjudged products were exact, BM25 would lead, 0.788 to 0.738. If the cheaper ranker's were, it would lead, 0.807 to 0.718. The leader changes: yes. The comparison waits on 46 judgments, a small bill next to the cost of shipping the wrong ranker.

Don't guess what the judges will say. On an old TREC collection, Voorhees et al. judged new pools of documents from neural and BM25 runs, and found that "the vast majority of those documents were not relevant" ([Voorhees et al., 2022](https://arxiv.org/abs/2201.11086)). But that collection was pooled deeply from many systems, and WANDS was built differently. Human judgments are the reference. Judgments from a large language model (LLM) are cheaper. [Chapter 4](#fill-unjudged-with-llm-grades) fills the store's unjudged pairs with them as a diagnostic, and has people judge the pairs whenever the filled grades change a verdict or the order of two rankers. Thomas et al. add a warning for testing changes: "LLM-generated labels may also show bias towards rankers that themselves incorporate LLMs" ([Thomas et al., 2024](https://arxiv.org/abs/2309.10621)).

**Working rule:** For every candidate, compute judged@10 for both runs and rescore them under the two scenarios. When the leader changes, judge the unjudged pairs before you compare, and add the new judgments to the regression set for good, so that it covers every ranker you have tested. When the leader holds in both scenarios, the unjudged products are unlikely to reverse the comparison.

## Keep the test queries out of every choice {#keep-test-queries-held-out}

The test queries in [the regression set](#diff-runs-per-query) are held out, and held-out queries give an honest score only if nothing was chosen by looking at them. Training on test queries is the obvious mistake. Choosing on them is the subtle one: try several settings, keep the one that scores best on the test queries, and report that score. The winner is partly the best setting and partly the luckiest on those particular queries, so its score is too high. Dwork et al. state the risk: "Reusing a holdout set adaptively multiple times can easily lead to overfitting to the holdout set itself" ([Dwork et al., 2015](https://arxiv.org/abs/1506.02629)). The damage can be smaller than feared. When ImageNet's test set was rebuilt, classifiers lost accuracy, but Recht et al.'s results suggest that "the accuracy drops are not caused by adaptivity": the new images were harder ([Recht et al., 2019](https://arxiv.org/abs/1902.10811)). In our judgement, a set of 30 queries leaves little room, and every look counts.

In the store, the change is a blend of BM25 and semantic retrieval with one weight, the share given to semantic retrieval. [Chapter 7](#tune-blend-on-train) calls it α, a different α from URisk's, and tunes it on the train queries with weighted reciprocal rank fusion, over 0, 0.1, … 1. Here, choose the semantic weight both ways, the right way on train queries and the wrong way on test queries, and report each choice on the test queries. These test scores are a demonstration of the bias, not a planned comparison. Then measure how much choosing on the reported queries inflates their score, without touching the test queries again: split the train queries at random, 1,000 times, into 30 to choose on and 20 to report on, and compare the 20's score when the weight is chosen on the 30 with their score when it is chosen on the 20 themselves.

Example `tuning-on-test-inflates` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np

from lib.blend import best_alpha, scores_by_alpha, weighted_rrf
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries(), qrels()                  # all 80 queries, train and test
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
per_query = scores_by_alpha(lambda weight: weighted_rrf(bm25, semantic, weight), judgments)   # nDCG@10, a column per weight
train = per_query.loc[load_queries("train").index]
test = per_query.loc[load_queries("test").index]

chosen_on_train, chosen_on_test = best_alpha(train), best_alpha(test)
print("settings tried:", per_query.shape[1])
print(f"semantic alone, test ndcg@10: {test[1.0].mean():.3f}")
print("semantic weight chosen on train:", chosen_on_train)
print(f"test ndcg@10, weight chosen on train: {test[chosen_on_train].mean():.3f}")
print("semantic weight chosen on test:", chosen_on_test)
print(f"test ndcg@10, weight chosen on test: {test[chosen_on_test].mean():.3f}")

# How much does choosing on the queries you report inflate the score? Split the train queries
# at random, 30 to choose on and 20 to report on, and compare the two ways of choosing.
rng = np.random.default_rng(2026)
scores = train.to_numpy()
inflation = []
for _ in range(1000):
    order = rng.permutation(len(scores))
    choose, report = scores[order[:30]].mean(axis=0), scores[order[30:]].mean(axis=0)
    inflation.append(report.max() - report[choose.argmax()])
print(f"average inflation, 20 reported queries: {np.mean(inflation):.3f}")
```

Output:

```text
settings tried: 11
semantic alone, test ndcg@10: 0.830
semantic weight chosen on train: 0.6
test ndcg@10, weight chosen on train: 0.825
semantic weight chosen on test: 0.8
test ndcg@10, weight chosen on test: 0.835
average inflation, 20 reported queries: 0.007
```

Semantic retrieval alone scores 0.830. Chosen on train, the semantic weight is 0.6, and the blend scores 0.825 on the test queries. Chosen on test, the weight is 0.8, and the blend scores 0.835. Only the first is a fair estimate of how the blend does on queries it wasn't chosen on. [Chapter 7](#report-blends-on-test) tests the train-chosen blend against semantic retrieval and finds no improvement.

The random splits put a number on the bias. On report sets of 20 queries, choosing on the queries you report adds 0.007 to nDCG@10 on average, with 11 settings to choose from. That gain appears in the report and nowhere else. Each extra setting you try is another chance for a lucky winner.

**Working rule:** Choose every setting on train queries, including which candidate to take forward. Look at the test queries once per decision, and log each look: what you compared and what you chose. When a test set has guided many decisions, move it to the train side and judge a fresh set of test queries.

## Run an A/B test {#run-an-ab-test}

Offline tests measure rankings against judgments, but the store earns from shoppers. An **A/B test**, or controlled experiment, assigns users at random to the current system, the **control**, or to the change, the **treatment**, and compares a metric chosen before the test starts ([Kohavi et al., 2009](https://exp-platform.com/Documents/controlledExperimentDMKD.pdf)).

Three checks make the result trustworthy. First, an **A/A test**, in which both groups get the same system: "the Null hypothesis should be rejected about 5% of the time when a 95% confidence level is used" (Kohavi et al., 2009). Far more than 5% points to a broken setup. Second, read the result once, at the size you planned. Stopping a test the moment it looks significant, called **peeking**, "significantly inflates the type-I error rates" ([Kohavi et al., 2022](https://exp-platform.com/abtestingintuitionbusters/)). Third, check that the groups came out the size you planned. A **sample ratio mismatch** (SRM) means users went missing from one group or were added to it unevenly, and "Ignoring the SRM without knowing the root cause may result in a bad product modification appearing to be good" ([Fabijan et al., 2019](https://www.microsoft.com/en-us/research/?p=651990)).

For a conversion metric, the share of shoppers who buy, the test compares two proportions. With rates p_A and p_B over n shoppers in each group, and p̄ their average:

```text
z = (p_B − p_A) / sqrt( p̄ × (1 − p̄) × 2 / n ),   p-value = 2 × P(Z > |z|)
```

In the store, simulate 2,000 A/A tests under stated assumptions: 2,000 shoppers a day in each group, 5% of them buy, and each test is planned for 14 days. Test each one at the end, and also every day, stopping at the first p-value below 0.05. Then check one split for a mismatch.

Example `aa-tests-with-peeking` (Python 3.12.15 · numpy 2.5.4 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
from scipy import stats

# Assumptions for the simulation, not the store's data: 2,000 shoppers a day in each group,
# 5% of them buy, and the test is planned to run 14 days. Both groups get the same search (an A/A test).
TESTS, DAYS, SHOPPERS_PER_DAY, CONVERSION = 2000, 14, 2000, 0.05

rng = np.random.default_rng(2026)
buyers = rng.binomial(SHOPPERS_PER_DAY, CONVERSION, size=(TESTS, DAYS, 2)).cumsum(axis=1)   # running totals
shoppers = SHOPPERS_PER_DAY * np.arange(1, DAYS + 1)[None, :]                               # per group, by day
rate_a, rate_b = buyers[..., 0] / shoppers, buyers[..., 1] / shoppers
pooled = (rate_a + rate_b) / 2
z = (rate_b - rate_a) / np.sqrt(pooled * (1 - pooled) * 2 / shoppers)    # two-proportion z-test, every day
p_value = 2 * stats.norm.sf(np.abs(z))

print(f"simulated A/A tests: {TESTS:,}")
print(f"significant at the planned end: {(p_value[:, -1] < 0.05).mean():.3f}")
print(f"significant on some day, checked daily: {(p_value < 0.05).any(axis=1).mean():.3f}")

# A sample ratio mismatch: the split was planned 50/50, but the groups came out unequal.
control, treatment = 28_000, 27_100
p = stats.binomtest(treatment, control + treatment).pvalue
print(f"sample ratio mismatch p: {p:.3f}" if p >= 0.001 else "sample ratio mismatch p: below 0.001")
```

Output:

```text
simulated A/A tests: 2,000
significant at the planned end: 0.053
significant on some day, checked daily: 0.231
sample ratio mismatch p: below 0.001
```

Read at the planned end, the share of A/A tests that come out significant is 0.053, close to the 0.05 the threshold promises. Checked daily, the share that look significant on some day rises to 0.231, though neither group's search changed. For a split planned 50/50 that comes out 28,000 to 27,100, a binomial test of 27,100 out of 55,100 shoppers against one half gives a p-value below 0.001: chance almost never produces a gap that size.

A p-value is often misread. A p-value of 0.05 doesn't mean a 5% chance that the result is a false positive; Kohavi et al. (2022) call that "a very common misunderstanding". It is the chance of data at least this extreme if the change did nothing.

**Working rule:** Before the test, choose the primary metric and the guardrails that must not get worse, and size the test ([with power](#size-tests-with-power)). Run an A/A test on the same setup first. Check the sample ratio before you read any result, and read the result once, at the planned size. If you must watch a test as it runs, use a sequential method built for continuous monitoring, such as always-valid p-values ([Johari et al., 2015](https://arxiv.org/abs/1512.04922)).

## Size the test with power {#size-tests-with-power}

Reading [an A/B test](#run-an-ab-test) once, at its planned size, means planning that size first, from the test's **power**: the chance that it detects a real change of a given size. A test with too little power misses real changes, and when it does come out significant, it tends to exaggerate: "a statistically significant finding with low power is likely to highly exaggerate the size of the effect" ([Kohavi et al., 2022](https://exp-platform.com/abtestingintuitionbusters/)). So decide the size before the test starts, from two numbers: how much the metric varies between users, and the smallest change worth detecting. More variance needs more users. A smaller change needs many more, because the change enters squared.

For two groups, 95% confidence and 80% power, Kohavi et al. give a rule of thumb, with σ² the metric's variance and Δ the change to detect ([Kohavi et al., 2009](https://exp-platform.com/Documents/controlledExperimentDMKD.pdf)):

```text
users per group ≈ 16 × σ² / Δ²
```

The 16 comes from the normal distribution: 2 × (z for 97.5% + z for 80%)², about 2 × (1.96 + 0.84)². For 90% power, they replace 16 with 21. The example computes the coefficient with SciPy, then checks the rule against their two worked examples: revenue per user with a mean of $3.75 and a standard deviation of $30, and a conversion rate of 5%, each with a 5% relative change to detect. The store's data, from WANDS, has no sales figures, so for the store the example assumes a 5% conversion rate too.

Example `sample-size-from-power` (Python 3.12.15 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
from scipy import stats

SIGNIFICANCE, POWER = 0.05, 0.80
z = stats.norm.ppf(1 - SIGNIFICANCE / 2) + stats.norm.ppf(POWER)    # 1.96 + 0.84
print(f"coefficient for two groups: {2 * z ** 2:.1f}")                # rounds to the 16 of the rule of thumb


def users_per_group(variance, change):
    """Kohavi et al.'s rule of thumb: about 16 * variance / change**2 users in each group."""
    return 16 * variance / change ** 2


# Their worked examples: revenue per user (mean $3.75, standard deviation $30), and a 5% conversion rate,
# each with a 5% relative change to detect.
print(f"users per group, revenue: {users_per_group(30 ** 2, 0.05 * 3.75):,.0f}")
print(f"users per group, conversion: {users_per_group(0.05 * 0.95, 0.05 * 0.05):,.0f}")

# The store, assuming a 5% conversion rate like theirs: smaller changes need far more users.
for relative in [0.02, 0.01]:
    print(f"users per group for a {relative:.0%} change: {users_per_group(0.05 * 0.95, 0.05 * relative):,.0f}")
```

Output:

```text
coefficient for two groups: 15.7
users per group, revenue: 409,600
users per group, conversion: 121,600
users per group for a 2% change: 760,000
users per group for a 1% change: 3,040,000
```

The coefficient is 15.7. The revenue example needs 409,600 users per group, and the conversion example 121,600, matching the paper's "over 409,000" and "under 122,000". For the store, detecting a 2% change in conversion takes 760,000 users per group, and a 1% change 3,040,000: halve the change and you need four times the users.

The same arithmetic says what the [regression set](#diff-runs-per-query) can detect. Both rankers score the same queries, so the test works on one sample of per-query differences instead of two groups, and the coefficient halves, to 7.8. Take σ as the spread of those differences between two close rankers: semantic retrieval and the [hybrid run](#fuse-with-rrf) that fuses it with BM25.

Example `queries-needed-for-power` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
from scipy import stats

from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

SIGNIFICANCE, POWER = 0.05, 0.80
queries, judgments = load_queries("test"), qrels("test")
bm25 = LexicalSearch(load_products()).run(queries, k=100)
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])
change = evaluate(hybrid, judgments)["ndcg@10"] - evaluate(semantic, judgments)["ndcg@10"]
spread = change.std()                                     # of the per-query differences

z = stats.norm.ppf(1 - SIGNIFICANCE / 2) + stats.norm.ppf(POWER)
print(f"spread of per-query changes: {spread:.3f}")
print(f"coefficient for paired queries: {z ** 2:.1f}")     # one sample of differences, so half of 16
detectable = z * spread / np.sqrt(len(change))
print(f"smallest change 30 queries detect: {detectable:.3f}")
print(f"queries needed for a change of 0.01: {z ** 2 * spread ** 2 / 0.01 ** 2:.0f}")

# Check the arithmetic by simulation: draw 30 normally distributed changes with that mean and spread,
# 10,000 times, and test each. The real differences aren't normal, so this checks the formula, not the data.
rng = np.random.default_rng(2026)
power = stats.power(stats.ttest_1samp, lambda size: rng.normal(detectable, spread, size=size), (len(change),),
                    significance=SIGNIFICANCE, kwargs={"popmean": 0})
print(f"simulated power at that change: {power.power.item():.3f}")
print("simulated power below the planned 0.8:", "yes" if power.power.item() < POWER else "no")
```

Output:

```text
spread of per-query changes: 0.062
coefficient for paired queries: 7.8
smallest change 30 queries detect: 0.032
queries needed for a change of 0.01: 300
simulated power at that change: 0.779
simulated power below the planned 0.8: yes
```

The spread is 0.062, so 30 test queries detect a change of 0.032 in nDCG@10 with 80% power. A change of 0.01 would need 300 queries. `scipy.stats.power` checks the arithmetic by simulation, drawing normally distributed differences: at that change, the paired t-test has a simulated power of 0.779. Below the planned 0.8: yes, because the formula uses the normal distribution where the t-test, on 30 queries, uses the wider t-distribution. The real differences aren't normal, so the simulation checks the formula, not the data. When you add queries, add many and judge each shallowly: Webber et al. found that "greater statistical power is achieved for the same relevance assessment effort by evaluating a large number of topics shallowly than a small number deeply", where topics are what information retrieval research calls queries ([Webber et al., 2008](https://people.eng.unimelb.edu.au/ammoffat/abstracts/wmz08cikm.html)).

**Working rule:** Size every A/B test before it starts. If it needs more users than the store sees in a few weeks, test a bigger change, use a metric that varies less, or adjust the metric with each user's data from before the test. On Bing's experiments, Deng et al. report that this "can reduce variance by about 50%" ([Deng et al., 2013](https://exp-platform.com/cuped/)); how much it saves depends on how well a user's past behaviour predicts the metric. Offline, compute the smallest change your regression set can detect, and add queries when your changes are smaller. Fix the number in advance: adding queries until a power estimate says you have enough biases you toward finding significance (Webber et al.).

## Interleave two rankings with team draft {#team-draft-interleaving}

An [A/B test](#run-an-ab-test) shows each group a different ranking, so differences between shoppers add noise. **Interleaving** shows each shopper one list that mixes the two rankers' results. Joachims designed it so that "the combined ranking gives (almost) equal presentation bias to both search engines" ([Joachims, 2003](https://cs.cornell.edu/~tj/publications/joachims_02b.pdf)): neither ranker's products sit systematically higher. The ranker whose products draw more clicks wins that search. Interleaving answers a narrower question than an A/B test: which of two rankings users prefer, not an absolute number for either ([Hofmann et al., 2016](https://www.microsoft.com/en-us/research/publication/online-evaluation-information-retrieval/)).

**Team draft** mixes the lists like picking teams for a game ([Radlinski et al., 2008](https://cs.cornell.edu/~tj/publications/radlinski_etal_08b.pdf), Algorithm 2). The team with fewer picks goes next, and a coin flip decides when both have the same number. Each pick is the team's highest-ranked product that isn't shown yet. A click counts for the team that picked the product. Radlinski et al. show that under team draft, "a randomly clicking user will always produce equally many preferences for A as for B in expectation", which an earlier method didn't guarantee.

Interleave the store's semantic retrieval and BM25 for the test query `clear shower curtain`. The example writes team draft in a few lines, with a seeded random generator for the coin flips, and checks that `lib.experiments` gives the same list:

Example `team-draft-one-query` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np

from lib import experiments
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}


def team_draft(ranking_a, ranking_b, rng, length=10):
    """Like picking teams: the team with fewer picks goes next, a coin flip decides when they're level,
    and each team adds its best product that isn't shown yet."""
    shown, teams = [], []
    while len(shown) < length:
        picks_a, picks_b = teams.count("a"), teams.count("b")
        a_picks = picks_a < picks_b or (picks_a == picks_b and rng.random() < 0.5)
        ranking, team = (ranking_a, "a") if a_picks else (ranking_b, "b")
        shown.append(next(p for p in ranking if p not in shown))
        teams.append(team)
    return shown, teams


products, queries, judgments = load_products(), load_queries("test"), qrels("test")[246]   # clear shower curtain
semantic = list(SemanticSearch().search(246, k=100).index)
bm25 = list(LexicalSearch(products).search(queries.at[246, "query"], k=100).index)

shown, teams = team_draft(semantic, bm25, np.random.default_rng(7))
for position, (product_id, team) in enumerate(zip(shown, teams), start=1):
    name = {"a": "semantic", "b": "bm25"}[team]
    print(f"{position:>2}  {name:<8}  {LABELS.get(judgments.get(product_id), 'unjudged'):<10}  {products.at[product_id, 'name'][:45]}")
print("same list from lib.experiments:", "yes" if experiments.team_draft(semantic, bm25, np.random.default_rng(7)) == (shown, teams) else "no")
```

Output:

```text
 1  bm25      partial     rodas vinyl shower curtain
 2  semantic  exact       woolley vinyl solid color single shower curta
 3  bm25      exact       woolley vinyl single shower curtain
 4  semantic  partial     newburg check 3d vinyl single shower curtain
 5  bm25      exact       siniard single shower curtain
 6  semantic  partial     71 '' x71 '' 4pcs shower curtain sets beach t
 7  semantic  exact       almazan lightweight single shower curtain
 8  bm25      exact       simmon vinyl single shower curtain liner
 9  semantic  partial     vinyl striped shower curtain set
10  bm25      irrelevant  gilded pineapple shower curtain hooks
same list from lib.experiments: yes
```

Team draft always gives each ranker half of a ten-place list, 5 places each; the coin flips decide which places. A product that both rankers place high appears once, credited to whichever team took it first, so neither ranker gets credit twice for the same product. For this query, one of the shower curtain hooks that BM25 ranks ([chapter 1](#rank-with-bm25)) enters, at the bottom, as BM25's last pick. A shopper's clicks on semantic retrieval's picks count for semantic retrieval, clicks on BM25's picks count for BM25, and the team with more clicks wins the search.

**Working rule:** Use team-draft interleaving to compare two rankers online when you need to know which one users prefer, with fewer searches than an A/B test. Use an A/B test instead when you need an absolute number, such as revenue, or when the change isn't in the ranking. By our reasoning, an interleaved list can't show the effect of latency, page layout or a different number of results.

## Rehearse interleaving with simulated shoppers {#simulate-interleaving-with-clicks}

WANDS, the source of the store's data, has no clicks, so the store can't run [team-draft interleaving](#team-draft-interleaving) on real shoppers, but it can rehearse with simulated ones. A **click model** is a probabilistic model of how users scan and click a result list, used both to build metrics and to simulate users ([Chuklin et al., 2015](https://staff.fnwi.uva.nl/m.derijke/wp-content/papercite-data/pdf/chuklin-introduction-2015.pdf)). The **cascade model** says users read from the top and "leave as soon as they see a worthwhile document" ([Craswell et al., 2008](https://www.microsoft.com/en-us/research/?p=156688); see [chapter 2](#clicks-are-not-judgments)). The standard simulation follows it: draw a query uniformly at random, walk down its list, click each product with a probability that depends on its grade, and after a click, leave with another probability that depends on the grade ([Oosterhuis and de Rijke, 2018](https://arxiv.org/abs/1809.08415)). Research on interleaving tests its methods this way, with clicks simulated from labelled data ([Hofmann et al., 2011](https://dare.uva.nl/id/628c8aaf-9dec-4c98-a3d8-b6bbf3962581)).

The probabilities are assumptions. Oosterhuis and de Rijke's Table 2 gives a "navigational" user for five grades, one looking for a single highly relevant result. We map irrelevant, partial and exact to that user's lowest, middle and highest grades, count unjudged products as irrelevant, as the metrics do, and draw every query equally often. The values live in one place, `lib.experiments`: the shopper clicks an exact product with probability 0.95 and then leaves with probability 0.9; a partial product gets 0.5 and 0.5, and an irrelevant one 0.05 and 0.2. Send one such shopper down the team-draft list for `clear shower curtain`, by hand:

Example `one-simulated-shopper` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np

from lib.experiments import NAVIGATIONAL, cascade_clicks, team_draft
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}
products, queries, judgments = load_products(), load_queries("test"), qrels("test")[246]   # clear shower curtain
semantic = list(SemanticSearch().search(246, k=100).index)
bm25 = list(LexicalSearch(products).search(queries.at[246, "query"], k=100).index)
shown, teams = team_draft(semantic, bm25, np.random.default_rng(7))       # the team-draft example's list
team_names = {"a": "semantic", "b": "bm25"}

rng = np.random.default_rng(2026)
clicks = []
for position, product_id in enumerate(shown):
    grade = judgments.get(product_id, 0)                                  # unjudged counts as 0
    clicked = rng.random() < NAVIGATIONAL["click"][grade]
    leaves = clicked and rng.random() < NAVIGATIONAL["stop"][grade]        # only a click can end the visit
    label = LABELS.get(judgments.get(product_id), "unjudged")
    print(f"{position + 1:>2}  {team_names[teams[position]]:<8}  {label:<10}  {'clicks' if clicked else '':<6}  {'leaves' if leaves else ''}")
    if clicked:
        clicks.append(position)
    if leaves:
        break

credited = [team_names[teams[position]] for position in clicks]       # each click counts for the team that picked it
for_semantic, for_bm25 = credited.count("semantic"), credited.count("bm25")
print("clicks for semantic:", for_semantic)
print("clicks for bm25:", for_bm25)
print("this search goes to:", "semantic" if for_semantic > for_bm25 else "bm25" if for_bm25 > for_semantic else "neither, a tie")
print("same clicks from lib.experiments:", "yes" if cascade_clicks(shown, judgments, np.random.default_rng(2026)) == clicks else "no")
```

Output:

```text
 1  bm25      partial     clicks
 2  semantic  exact       clicks  leaves
clicks for semantic: 1
clicks for bm25: 1
this search goes to: neither, a tie
same clicks from lib.experiments: yes
```

The shopper's clicks count 1 for semantic retrieval and 1 for BM25, so this search goes to neither, a tie. Now simulate 10,000 interleaved searches, with a fixed seed, for two pairs: semantic retrieval against BM25, and the [hybrid run](#fuse-with-rrf) against semantic retrieval. A sign test asks whether wins outnumber losses by more than chance; [Radlinski et al.](https://cs.cornell.edu/~tj/publications/radlinski_etal_08b.pdf) use "a binomial sign test", leaving ties out. Read the verdict at 100, 1,000 and 10,000 searches:

Example `simulated-interleaving-verdict` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
from scipy import stats

from lib.experiments import NAVIGATIONAL, simulate_interleaving
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

for grade, label in [(2, "exact"), (1, "partial"), (0, "irrelevant")]:      # the assumptions, from lib.experiments
    print(f"{label} click probability: {NAVIGATIONAL['click'][grade]}")
    print(f"{label} stop probability: {NAVIGATIONAL['stop'][grade]}")

def ties_reversed(scores):              # BM25's ranking, with equal scores in descending product_id order instead
    return scores.index[np.lexsort((-scores.index.to_numpy(), -scores.to_numpy()))].tolist()


queries, judgments = load_queries("test"), qrels("test")
lexical = LexicalSearch(load_products())
bm25 = lexical.run(queries, k=100)                                        # equal scores by product_id
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])
bm25_reversed = {q: ties_reversed(lexical.search(query, k=100)) for q, query in queries["query"].items()}

pairs = {"semantic against bm25": (semantic, bm25), "hybrid against semantic": (hybrid, semantic),
         "hybrid with bm25 ties reversed against semantic": (reciprocal_rank_fusion([bm25_reversed, semantic]), semantic)}
below = {}
for name, (run_a, run_b) in pairs.items():
    outcomes = simulate_interleaving(run_a, run_b, judgments, 10_000, np.random.default_rng(2026))
    for searches in [100, 1_000, 10_000]:
        wins, losses = (outcomes[:searches] == 1).sum(), (outcomes[:searches] == -1).sum()
        p = stats.binomtest(wins, wins + losses).pvalue                  # sign test; ties left out
        below[name, searches] = p < 0.05
        shown = f"{p:.3f}" if p >= 0.001 else "below 0.001"
        print(f"{name}, {searches:,} searches: {wins} wins, {losses} losses, p {shown}")
changes = below["hybrid against semantic", 100] != below["hybrid with bm25 ties reversed against semantic", 100]
print("hybrid against semantic, verdict at 100 searches changes with bm25 ties reversed:", "yes" if changes else "no")
```

Output:

```text
exact click probability: 0.95
exact stop probability: 0.9
partial click probability: 0.5
partial stop probability: 0.5
irrelevant click probability: 0.05
irrelevant stop probability: 0.2
semantic against bm25, 100 searches: 51 wins, 36 losses, p 0.133
semantic against bm25, 1,000 searches: 519 wins, 347 losses, p below 0.001
semantic against bm25, 10,000 searches: 5222 wins, 3552 losses, p below 0.001
hybrid against semantic, 100 searches: 32 wins, 51 losses, p 0.048
hybrid against semantic, 1,000 searches: 413 wins, 447 losses, p 0.260
hybrid against semantic, 10,000 searches: 4180 wins, 4593 losses, p below 0.001
hybrid with bm25 ties reversed against semantic, 100 searches: 35 wins, 48 losses, p 0.187
hybrid with bm25 ties reversed against semantic, 1,000 searches: 410 wins, 463 losses, p 0.078
hybrid with bm25 ties reversed against semantic, 10,000 searches: 4174 wins, 4560 losses, p below 0.001
hybrid against semantic, verdict at 100 searches changes with bm25 ties reversed: yes
```

For semantic retrieval against BM25, a large gap offline, the verdict reads 51 wins, 36 losses, p 0.133 at 100 searches, and 519 wins, 347 losses, p below 0.001 at 1,000. For the hybrid against semantic retrieval, it reads 32 wins, 51 losses, p 0.048 at 100 searches and 413 wins, 447 losses, p 0.260 at 1,000: small samples swing, which is why you fix the number of searches before the test starts. At 10,000 it reads 4180 wins, 4593 losses, p below 0.001. That doesn't overturn [chapter 3](#compare-runs-in-a-harness)'s finding of no established difference: with ever more simulated clicks on the same 30 queries, the sign test measures only click noise, so any fixed gap becomes significant.

The hybrid's verdict at 100 searches also rests on a detail that carries no information. The hybrid fuses BM25, and `lib.lexical` orders equal BM25 scores by `product_id`. Order them the other way, an equally arbitrary rule, and the same seed reads 35 wins, 48 losses, p 0.187 at 100 searches. The verdict at 0.05 changes: yes. Reversing BM25's ties changes some of the hybrid's lists, so the simulated shoppers see other products, and every random draw after the first changed list can shift. A verdict that a tie rule can flip is luck, not a finding about the rankers.

Three limits keep this a rehearsal. The clicks come from the same grades nDCG@10 uses, so interleaving tends to agree with nDCG@10; it adds no evidence about the rankers. Every search comes from the same 30 queries, so the sign test speaks for these queries only. And real shoppers aren't this model. Deffayet et al. studied what happens when the ranker that produced a click log changes, and found that "click models are sensitive to it" ([Deffayet et al., 2023](https://dare.uva.nl/id/4f8740ca-2677-4a9a-bb04-9475ceafb007)). On real traffic at three search engines, interleaving agreed with expert judgments whenever both were significant, and needed "approximately 1–2 orders of magnitude less data than absolute metrics" ([Chapelle et al., 2012](https://www.cs.cornell.edu/people/tj/publications/chapelle_etal_12a.pdf)). By our reasoning, the simulation can't show that advantage, because its shoppers all behave alike.

**Working rule:** Rehearse an interleaving test in simulation to check your code and your sign test. Treat any count of searches it suggests as only as good as the assumed shopper, and rerun a simulated verdict with ties broken the other way before you read anything into it. Never report a simulated verdict as evidence about a ranker. On real traffic, fix the number of searches in advance and decide with a sign test.

## Find the cause when offline and online disagree {#offline-online-disagree}

[Simulated shoppers](#simulate-interleaving-with-clicks) click by the same grades nDCG@10 uses, so they tend to agree with it; real shoppers need not. Offline metrics sometimes predict online results well. In one e-commerce study of 36 offline metrics, the best agreed with online results under a business metric about which of two ranking models was better "up to 97% of times" ([Wang et al., 2023](https://www.amazon.science/publications/how-well-do-offline-metrics-predict-online-performance-of-product-ranking-models)). Another e-commerce team found that offline ranking metrics "can show significant inconsistency with online performance, and can even be misleading" ([Huzhang et al., 2020](https://arxiv.org/abs/2003.11941)). Both are industry studies on their own traffic, which nobody outside can reproduce. When two systems perform about equally, "disagreements between different metrics are common" ([Hofmann et al., 2016](https://www.microsoft.com/en-us/research/publication/online-evaluation-information-retrieval/)).

Disagreements have causes you can check. The judgments may miss products the online winner shows, which [the sensitivity check](#judge-new-results) looks for. The change may act outside the ranking, on speed or layout. Or the online metric may measure something other than success. On an academic search engine, [Radlinski et al. (2008)](https://cs.cornell.edu/~tj/publications/radlinski_etal_08b.pdf) found that clicks per query, like seven other absolute usage metrics, didn't reliably reflect retrieval quality at the sample sizes they studied.

In the store, run a simulated A/B test with the navigational shopper from [the interleaving rehearsal](#simulate-interleaving-with-clicks): 5,000 searches on BM25 as the control and 5,000 on semantic retrieval as the treatment, all on test queries. Measure clicks per search, and the share of searches with a click on an exact product. Then repeat with Table 2's "perfect" user, mapped the same way, who reads all ten results, clicks every exact product and never leaves early. Before you run it, predict: which ranker gets more clicks per search?

Example `clicks-per-search-misleads` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.4 · pandas 3.1.1 · scipy 1.18.1), passing in Edition 2026.11.6:

```python
import numpy as np
from scipy import stats

from lib.experiments import SHOPPERS, simulate_searches
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
arms = {"bm25": LexicalSearch(load_products()).run(queries, k=100),     # control
        "semantic": SemanticSearch().run(queries, k=100)}               # treatment
metrics = {"clicks per search": "clicks", "share of searches with an exact click": "exact_click"}

significant_leaders = {label: set() for label in metrics}      # rankers ahead at p below 0.05
for shopper_name, shopper in SHOPPERS.items():                         # navigational, then perfect
    rng = np.random.default_rng(2026)
    searches = {name: simulate_searches(run, judgments, 5_000, rng, shopper) for name, run in arms.items()}
    for label, column in metrics.items():
        means = {name: table[column].mean() for name, table in searches.items()}
        for name, mean in means.items():
            print(f"{shopper_name} shopper, {name} {label}: {mean:.3f}")
        p = stats.ttest_ind(searches["semantic"][column].astype(float), searches["bm25"][column].astype(float)).pvalue
        print(f"{shopper_name} shopper, {label} p: " + (f"{p:.3f}" if p >= 0.001 else "below 0.001"))
        if p < 0.05:
            significant_leaders[label].add(max(means, key=means.get))
for label in metrics:
    print(f"{label} reverses between shoppers:", "yes" if len(significant_leaders[label]) > 1 else "no")
```

Output:

```text
navigational shopper, bm25 clicks per search: 1.362
navigational shopper, semantic clicks per search: 1.269
navigational shopper, clicks per search p: below 0.001
navigational shopper, bm25 share of searches with an exact click: 0.695
navigational shopper, semantic share of searches with an exact click: 0.799
navigational shopper, share of searches with an exact click p: below 0.001
perfect shopper, bm25 clicks per search: 6.443
perfect shopper, semantic clicks per search: 7.451
perfect shopper, clicks per search p: below 0.001
perfect shopper, bm25 share of searches with an exact click: 0.898
perfect shopper, semantic share of searches with an exact click: 0.895
perfect shopper, share of searches with an exact click p: 0.646
clicks per search reverses between shoppers: yes
share of searches with an exact click reverses between shoppers: no
```

For the navigational shopper, BM25 gets 1.362 clicks per search and semantic retrieval 1.269, with a p-value below 0.001. A shopper who finds an exact product near the top clicks it and usually leaves, while one shown partial products clicks several, still looking. For the perfect shopper, semantic retrieval gets 7.451 against BM25's 6.443. Clicks per search reverses between shoppers: yes. Its sign depends on how shoppers behave, so on its own it can't measure success. The share of searches with an exact click favours semantic retrieval for the navigational shopper, 0.799 against 0.695. It reverses between shoppers: no. For the perfect shopper it shows no clear difference, with a p-value of 0.646: that shopper clicks an exact product in 0.898 of BM25's searches and 0.895 of semantic retrieval's, whenever the top 10 holds one.

If you predicted one answer for every shopper, you treated clicks as a measure of quality. They measure behaviour, and behaviour varies.

**Working rule:** When offline and online results disagree, find the cause before you trust either. Check that the online metric measures success, such as a purchase, and not activity. Check judged@10 on the online winner's results, and judge what is missing. Then decide on the online result of the metric you chose in advance, and add queries or judgments to the regression set so that it predicts better next time.

## Decide whether to ship {#decide-whether-to-ship}

A decision to ship combines the offline and online checks. Write the checklist down before you see any result, so that no single number can talk you into a change. We recommend these items, each with the section that shows it:

1. **An established offline gain on the regression set,** by the planned-comparison rule, with its t-test and interval ([per-query diff](#diff-runs-per-query)), against the strongest system you have. Armstrong et al. found that over a decade of published gains on TREC collections, "Baselines are generally weak, often being below the median original TREC system" ([Armstrong et al., 2009](https://people.eng.unimelb.edu.au/ammoffat/abstracts/amwz09cikm.html)).
2. **Losses read,** and URisk with α = 1 not negative ([URisk](#weigh-losses-with-urisk)).
3. **Judgments that cover both runs:** a leader that holds when either run's unjudged products count as exact, or new judgments where it doesn't ([unjudged products](#judge-new-results)).
4. **Human grades for the headline scores** of LLM-based rankers ([chapter 4](#llm-graded-verdicts)).
5. **Latency and cost within budget** ([chapter 9](#rerank-depth-from-budget)).
6. **Every setting chosen on train queries,** with each look at the test queries logged ([held-out queries](#keep-test-queries-held-out)).
7. **An online plan written in advance:** the primary metric and guardrails, the size from a [power calculation](#size-tests-with-power), an A/A test, a sample ratio check and no peeking ([A/B test](#run-an-ab-test)). Interleaving can screen candidates first ([team draft](#team-draft-interleaving)).

For the store's switch from BM25 to semantic retrieval, here are the first three items. Item 1, an established gain: yes, with a mean change of 0.105 and a 95% interval of 0.055 to 0.185. Item 2, URisk with α = 1: 0.092. Item 3, judgments that cover both runs: if BM25's unjudged products were all exact, BM25 would score 0.788 and semantic retrieval 0.829, and the leader changes: no. The online items wait for traffic.

**Working rule:** Ship when every offline item passes and the online test, sized in advance, shows a significant gain on the primary metric with no guardrail worse. When an offline item fails, fix it before going online, because online tests spend shoppers' time. When the online test is inconclusive at its planned size, keep the baseline.

## What goes wrong in production {#testing-changes-in-production}

A store tests change after change on live traffic, with real shoppers in place of simulated ones and the same regression set at every step.

**The dashboard invites peeking.** An experiment platform shows results every day, and a team that stops the first time a result looks significant gets far more than 5% false positives, as the [A/A simulation](#run-an-ab-test) shows. Fix the size in advance, or use a sequential method.

**The groups don't match the plan.** [Fabijan et al.](https://www.microsoft.com/en-us/research/?p=651990) collected the causes of sample ratio mismatches from several companies into a taxonomy. Check the split before you read any result, and don't trust the result until you know why the split is off.

**The regression set wears out.** Every decision made by looking at the test queries spends some of their independence ([Dwork et al., 2015](https://arxiv.org/abs/1506.02629)). Log each look, and refresh the test set with new queries and judgments when the log grows long.

**An LLM judge becomes the gate.** LLM judgments are cheap enough to score every candidate. Otero et al. found that significance tests on LLM judgments showed "an exceedingly high rate of false positives regarding statistical differences" ([Otero et al., 2025](https://arxiv.org/abs/2411.13212)). Before you ship on an LLM-judged gain, confirm it on human judgments ([chapter 4](#llm-graded-verdicts)).

**Ties move results.** Products with equal scores come back in whatever order a library's selection leaves them ([chapter 3](#measuring-search-in-production)), so a change that touches no score can still move a result. Reversed BM25 ties change the store's [100-search interleaving verdict](#simulate-interleaving-with-clicks): yes. Break ties by an ID in every ranker, and rerun a result near its threshold with ties reversed before you act on it.

**Interleaving can't see the whole page.** By our reasoning, a ranker that is slower, or that changes how many results appear, can win an interleaved test and still lose shoppers. Run an A/B test for changes like these.

**Working rule:** Automate the A/A test, the sample ratio check and the fixed test size in the experiment platform, keep a log of every look at the test queries, break ties by an ID, and confirm LLM-judged gains on human judgments.

## Decisions this chapter made {#testing-changes-decisions}

Each choice below is a default, with its reason in the section it links to.

- **The regression set is the 30 test queries with their judgments,** and every choice uses the 50 train queries ([held-out queries](#keep-test-queries-held-out)).
- **One planned comparison on the test queries,** semantic retrieval against BM25, established only by a permutation p-value below 0.05, with the t-test and a 95% interval beside it ([per-query diff](#diff-runs-per-query)). The 128-dimension ranker is a demonstration, chosen for how it behaves on test ([URisk](#weigh-losses-with-urisk)).
- **Every candidate gets a per-query diff,** and its losses are read by hand.
- **URisk uses α = 1,** so each loss counts double. It is a judgement about how much a regression costs, and a store with expensive failures should raise it ([URisk](#weigh-losses-with-urisk)).
- **When the leader changes between the two unjudged scenarios, judge before you compare,** and keep the new judgments in the regression set ([unjudged products](#judge-new-results)).
- **Test queries are looked at once per decision,** and each look is logged ([held-out queries](#keep-test-queries-held-out)).
- **A/B tests are sized with 16σ²/Δ² before they start,** read once at that size, and preceded by an A/A test and a sample ratio check ([power](#size-tests-with-power)).
- **Interleaving uses team draft and a sign test** ([team draft](#team-draft-interleaving)).
- **Simulated shoppers follow a navigational cascade model mapped onto three grades,** with uniform query frequency, probabilities stated as assumptions in `lib.experiments` and a fixed seed for every simulation. Their verdicts rehearse a method and never count as evidence ([rehearsal](#simulate-interleaving-with-clicks)).
- **Clicks per search is not a success metric on its own.** Use a measure of success, such as a purchase ([offline and online](#offline-online-disagree)).
