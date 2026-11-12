---
title: "Business Intelligence with Agents"
chapter: "Judge answers and catch regressions"
chapter_id: catch-regressions
book: business-intelligence-with-agents
edition: 2026.11.8
verified: 2026-11-12
edition_code: 4VTV-2H9T
canonical: https://rollingedition.com/business-intelligence-with-agents/catch-regressions
license: CC BY 4.0
attribution: "“Judge answers and catch regressions,” chapter 10 of Business Intelligence with Agents, Edition 2026.11.8, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/business-intelligence-with-agents/catch-regressions. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Judge answers and catch regressions

By the end of this chapter, you can score a run of the agent on several measures at once, use a model as a judge only where results can't be compared directly, calibrate that judge against reference labels anyone can recompute, see how much a score moves from one run to the next, and gate a change to prompts, context or metrics in CI on recorded runs.

The shop, the online outdoor-gear shop in three regions that this book follows throughout, has had its agent changed in almost every chapter. [Chapter 4](#layered-context) added context to the prompt, [chapter 6](#metrics-first) moved the agent onto the semantic layer's metrics, and [chapter 8](#say-when-it-cannot) rewrote its prompt so that it declines with a reason. Each change was scored on the dev split of the golden questions, the shop's 48 questions with verified answers, with one run per question. One run is enough to see a large change and not enough to see a small one. Chapter 8's new prompt fixed one dev question and broke another, `gq-008`, total revenue in 2025, and chapter 8 could only say that a single flip like that "may be chance".

This chapter builds the measurements that settle questions like that one. It reports a run on more than accuracy, with an interval that says how far the number can be trusted. It adds a judge, a model call that grades what the golden comparison can't, and measures the judge before trusting it. It runs questions five times to see the variance, and it turns all of that into a gate that a CI job can run on every change, offline, from recordings.

## Score a run on more than accuracy {#score-a-run}

A single accuracy figure answers one question, how often the agent was right, and hides three others that matter as much: what it did when it was wrong, what each answer cost, and how far the figure would move on another sample of questions. An agent that gives a wrong number and one that declines both lose a point of accuracy, but only one of them puts a wrong number in a deck. So a scorecard reports wrong numbers, declines and failures apart, the [decline measures](#measure-declines) from chapter 8, and the cost in model calls and prompt tokens, beside accuracy.

The figure also needs an interval. On a set the size of a golden split, each question is several points, and the interval that most people learn first, the Wald interval, behaves badly for small sets. Brown, Cai and DasGupta recommend "the Wilson interval or the equal-tailed Jeffreys prior interval for small n" ([Brown et al.](https://doi.org/10.1214/ss/1009213286)). In words, Wilson's interval inverts the test of a proportion: it holds every true accuracy that the observed one wouldn't reject at the chosen level, so it never runs below 0 or above 1. For k correct of n, with p = k / n and z = 1.96 for about 95%:

```text
centre   = (p + z² / 2n) / (1 + z² / n)
half     = z × √( p(1 − p) / n + z² / 4n² ) / (1 + z² / n)
interval = centre − half  to  centre + half
```

`wilson()` in `lib/regressions.py` computes it in a few lines. statsmodels implements the same interval as `proportion_confint(method="wilson")` ([statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html)); the book's pins don't include statsmodels, so the example doesn't call it. `replay()` runs one of the book's agents over golden questions from its recordings, and `Scorecard` scores the runs. The example scores three agents on the 21 answer and decline questions of each split: [chapter 3's schema-only SQL](#hold-out-a-test-split), chapter 6's metrics-first agent and chapter 8's declining agent. Forbidden questions are left out, because [chapter 9](#who-may-see-what) decides them below the model.

The test split is held out, and the book scores it only for a number it reports. Chapters 3 and 6 recorded their agents on test once. This chapter recorded the declining agent on test once, in the recording `decline-runs-test`, with chapter 8's prompt unchanged, and changed nothing after it. These are the book's final test numbers for its agents.

Example `scorecard` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.8:

```python
"""Score the book's agents on more than accuracy: dev to compare them, and the held-out test split once, at the end."""
from lib.golden import load_golden
from lib.regressions import Scorecard, replay
from lib.semantic import load
from lib.warehouse import connect

con, layer = connect(), load()
# Answer and decline questions; forbidden questions are decided below the model, by chapter 9's policies.
questions = [q for q in load_golden() if q.kind in ("answer", "decline")]
for split in ("dev", "test"):
    in_split = [q for q in questions if q.split == split]
    print(f"{split} questions: {len(in_split)}")
    runs = {agent: replay(con, layer, agent, in_split) for agent in ("schema-only", "metrics-first", "declining")}
    for agent, agent_runs in runs.items():
        print("\n".join(Scorecard(agent_runs).lines(f"{split} {agent}")))
    for label, was, now in (("fixed", False, True), ("broken", True, False)):
        ids = [a.question.question_id for a, b in zip(runs["metrics-first"], runs["declining"])
               if (a.outcome == "correct") == was and (b.outcome == "correct") == now]
        print(f"{split} {label} by the declining prompt: {', '.join(ids) or 'none'}")
```

Output:

```text
dev questions: 21
dev schema-only correct: 2 of 21
dev schema-only accuracy: 0.10 (95% interval 0.03 to 0.29)
dev schema-only wrong numbers: 11
dev schema-only errors or step limits: 8
dev schema-only decline recall: 0.00
dev schema-only decline precision: no declines
dev schema-only coverage: 0.62
dev schema-only selective risk: 0.85
dev schema-only model calls per question: 1.0
dev schema-only prompt tokens per question: 827
dev metrics-first correct: 15 of 21
dev metrics-first accuracy: 0.71 (95% interval 0.50 to 0.86)
dev metrics-first wrong numbers: 5
dev metrics-first errors or step limits: 1
dev metrics-first decline recall: 0.75
dev metrics-first decline precision: 1.00
dev metrics-first coverage: 0.81
dev metrics-first selective risk: 0.29
dev metrics-first model calls per question: 1.8
dev metrics-first prompt tokens per question: 2,196
dev declining correct: 15 of 21
dev declining accuracy: 0.71 (95% interval 0.50 to 0.86)
dev declining wrong numbers: 4
dev declining errors or step limits: 1
dev declining decline recall: 1.00
dev declining decline precision: 0.80
dev declining coverage: 0.71
dev declining selective risk: 0.27
dev declining model calls per question: 1.9
dev declining prompt tokens per question: 2,602
dev fixed by the declining prompt: gq-020
dev broken by the declining prompt: gq-008
test questions: 21
test schema-only correct: 3 of 21
test schema-only accuracy: 0.14 (95% interval 0.05 to 0.35)
test schema-only wrong numbers: 10
test schema-only errors or step limits: 8
test schema-only decline recall: 0.00
test schema-only decline precision: no declines
test schema-only coverage: 0.62
test schema-only selective risk: 0.77
test schema-only model calls per question: 1.0
test schema-only prompt tokens per question: 829
test metrics-first correct: 9 of 21
test metrics-first accuracy: 0.43 (95% interval 0.24 to 0.63)
test metrics-first wrong numbers: 5
test metrics-first errors or step limits: 1
test metrics-first decline recall: 1.00
test metrics-first decline precision: 0.40
test metrics-first coverage: 0.48
test metrics-first selective risk: 0.50
test metrics-first model calls per question: 1.5
test metrics-first prompt tokens per question: 1,854
test declining correct: 8 of 21
test declining accuracy: 0.38 (95% interval 0.21 to 0.59)
test declining wrong numbers: 4
test declining errors or step limits: 3
test declining decline recall: 0.75
test declining decline precision: 0.33
test declining coverage: 0.43
test declining selective risk: 0.44
test declining model calls per question: 1.9
test declining prompt tokens per question: 2,622
test fixed by the declining prompt: none
test broken by the declining prompt: gq-043
```

On dev, the metrics-first and declining agents both get 15 of 21 right, an accuracy of 0.71 (95% interval 0.50 to 0.86), though not on the same questions: the declining prompt fixed `gq-020` and broke `gq-008`, the two flips chapter 8 found. The other lines are where the agents differ. The declining agent gave 4 wrong numbers against 5, its decline recall is 1.00 against 0.75, and it pays for that in coverage, 0.71 against 0.81, and in tokens, 2,602 prompt tokens a question against 2,196. Schema-only SQL gets 2 of 21, and of the numbers it gives, the share that is wrong, its selective risk, is 0.85.

On test, the declining agent gets 8 of 21, an accuracy of 0.38 (95% interval 0.21 to 0.59), against metrics-first's 9 of 21 and schema-only SQL's 3 of 21. The declining prompt fixed no test question and broke one, `gq-043`, "What was revenue in Q2?", which chapter 6's agent met with a question back and the declining agent ran out of model calls on: `test broken by the declining prompt: gq-043`. Its wrong numbers fell from 5 to 4, because one wrong answer became a run that hit the step limit, not a right one. The intervals of the two agents overlap almost entirely on both splits. Two totals with overlapping intervals can't tell you whether a change helped, which is why [the gate](#gate-a-change) compares the same questions in pairs.

**Working rule:** Report every run as a scorecard: correct with a Wilson interval, wrong numbers, declines and their recall and precision, failures by kind, and calls and tokens per question. Compare agents on the same questions in the same table. Score the test split once, when you report a final number, and say that you did; when two agents' intervals overlap, don't call either better from the totals.

## Judge only what can't be compared {#judge-what-cannot-be-compared}

`results_match()`, the comparison [chapter 3](#compare-results-not-sql) built, grades a number against a golden result. Much of what the agent says isn't a number. A decline's reason, the sentence that tells the person why no number came, has no golden result to match: two good reasons can share no words, and a fluent reason can be false. For text like that, the common tool is a judge, a model call that grades an answer against a rubric and returns a verdict. A judge is cheap and tireless, and it has known biases. Zheng and colleagues, who found that strong judges matched human preferences about as often as humans matched each other, also name "position, verbosity, and self-enhancement biases" ([Zheng et al.](https://arxiv.org/abs/2306.05685)): a judge can favour the answer shown first, the longer answer, and its own. A later study quantified twelve kinds of bias and found that "significant biases persist in certain specific tasks" even for strong judges ([Ye et al.](https://arxiv.org/abs/2410.02736)).

So use a judge only where a result can't be compared directly, and design each call so that a bias would show. The shop's judge is the book's own model, the same one the agent uses, called with a separate prompt, `JUDGE_PAIR` in `lib/prompts.py`. It sees a question and two reasons for declining it, labelled A and B, and names the better one, or a tie, as JSON. The rubric asks for a reason that says accurately why the shop's data can't answer and what the person could ask instead. The cases are every golden question, on either split, that both chapter 6's metrics-first agent and chapter 8's declining agent declined: 8 pairs. Only 3 of them, `gq-021`, `gq-042` and `gq-045`, are decline questions. The other 5, `gq-032`, `gq-033`, `gq-034`, `gq-037` and `gq-041`, are answer questions the warehouse can answer, the [gaps in the layer](#measure-metrics-first) chapter 6 found, and both agents declined them wrongly. On those, the right reply was a number, so the judge compares two wrong declines. Each pair is judged twice, once with each agent's reason first, so a verdict that follows the position rather than the text changes with the order. `parse_verdict()` in `lib/judge.py` reads each reply, and the recording `judge-verdicts` holds every call.

Example `judge-an-explanation` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.8:

```python
"""Judge only what can't be compared: two reasons for declining the same question, shown in both orders."""
import re

from lib.judge import judge_pairs, recorded_cases
from lib.model import RecordedModel
from lib.semantic import load
from lib.warehouse import connect

con, layer = connect(), load()
_, pairs = recorded_cases(con, layer)
results = judge_pairs(RecordedModel("judge-verdicts"), pairs)
GROUPS = {"decline": "decline questions", "answer": "answerable questions both agents declined"}
AGENTS = ("metrics-first", "declining")
BLAMES_DATA = re.compile(r"\bdata (does not|doesn't) (include|contain)")
ALTERNATIVE = ("alternative", "instead", "reframe", "path forward")
for r in results:
    print(f"{r.case.question.question_id} ({r.case.question.kind}): metrics-first first -> {r.first.label}; "
          f"declining first -> {r.second.label}")
n = len(results)
print(f"pairs: {n}")
for group, name in GROUPS.items():
    print(f"pairs on {name}: {sum(r.case.question.kind == group for r in results)}")
print(f"same verdict in both orders: {sum(r.first.label == r.second_as_first for r in results)} of {n}")
print(f"first reason won in both orders: {sum(r.first.label == r.second.label == 'A' for r in results)} of {n}")
print(f"second reason won in both orders: {sum(r.first.label == r.second.label == 'B' for r in results)} of {n}")
for agent in AGENTS:
    print(f"{agent} reason won in both orders: {sum(r.winner == agent for r in results)}")
for group, name in GROUPS.items():
    for agent in AGENTS:
        print(f"{name}, {agent} reason won in both orders: "
              f"{sum(r.winner == agent and r.case.question.kind == group for r in results)}")
print(f"consistent winner was the longer reason: {sum(r.longer_won for r in results)}")
answerable = [r.case for r in results if r.case.question.kind == "answer"]
for agent, reasons in (("metrics-first", [c.first for c in answerable]), ("declining", [c.second for c in answerable])):
    said = sum(bool(BLAMES_DATA.search(x)) for x in reasons)
    print(f"answerable questions, {agent} reasons that say the data lacks it: {said} of {len(answerable)}")
replies = [v for r in results for v in (r.first, r.second)]
suggests = sum(any(w in v.reason.lower() for w in ALTERNATIVE) for v in replies)
print(f"judge replies that suggest an alternative or a reframe: {suggests} of {len(replies)}")
```

Output:

```text
gq-021 (decline): metrics-first first -> A; declining first -> A
gq-032 (answer): metrics-first first -> B; declining first -> A
gq-033 (answer): metrics-first first -> A; declining first -> B
gq-034 (answer): metrics-first first -> A; declining first -> B
gq-037 (answer): metrics-first first -> A; declining first -> B
gq-041 (answer): metrics-first first -> A; declining first -> B
gq-042 (decline): metrics-first first -> B; declining first -> A
gq-045 (decline): metrics-first first -> A; declining first -> B
pairs: 8
pairs on decline questions: 3
pairs on answerable questions both agents declined: 5
same verdict in both orders: 7 of 8
first reason won in both orders: 1 of 8
second reason won in both orders: 0 of 8
metrics-first reason won in both orders: 5
declining reason won in both orders: 2
decline questions, metrics-first reason won in both orders: 1
decline questions, declining reason won in both orders: 1
answerable questions both agents declined, metrics-first reason won in both orders: 4
answerable questions both agents declined, declining reason won in both orders: 1
consistent winner was the longer reason: 6
answerable questions, metrics-first reasons that say the data lacks it: 1 of 5
answerable questions, declining reasons that say the data lacks it: 5 of 5
judge replies that suggest an alternative or a reframe: 9 of 16
```

The judge gave the same verdict in both orders on 7 of 8 pairs. On the other, `gq-021`, the cost of shipping, it chose whichever reason came first, which is position bias in the one place a pair was close: the two reasons say nearly the same thing. Of the consistent verdicts, chapter 6's reason won 5 and chapter 8's 2, and the longer reason won 6 of them. That is what verbosity bias predicts, though 8 pairs can't separate it from longer reasons being better.

The two groups of pairs tell different stories. On the answerable questions, chapter 6's reason won 4 and chapter 8's 1. Chapter 8's reasons say the data doesn't include what was asked (5 of 5), which is false: the warehouse holds `raw.customers.email` for `gq-037` and `fct_orders.discount_eur` for `gq-041`. Chapter 6's reasons say so in 1 of 5; the others say the metrics don't include it, which is true of the semantic layer. So on these pairs the judge may have preferred the more accurate reason, and accuracy and length point the same way. On the decline questions, the case the rubric was written for, chapter 6's reason won 1, chapter 8's 1, and the third changed with the order. That is too few pairs to say whose reasons are better.

Reading the verdicts shows a bigger problem than order. Of the judge's replies, 9 of 16 praise a reason for "offering a constructive path", an alternative, or a way to reframe the question, or fault one for lacking it, and neither agent's reason does that in any of these pairs. For `gq-032`, gross margin, the judge preferred chapter 8's reason for explaining the calculation, and the calculation that reason gives, gross revenue minus net revenue over gross revenue, is not a gross margin: the golden SQL subtracts the products' unit cost from net revenue. The judge rewarded a confident wrong definition. A verdict on text is only as good as the judge's grip on the facts behind it, which is why [the next section](#calibrate-the-judge) measures the judge where the facts are known.

**Working rule:** Use a judge only for what can't be compared with a result, such as reasons, explanations and questions back, and keep `results_match()` for every number. Judge each pair in both orders and count the verdicts that change, record every verdict, and read a sample of the judge's reasons, not only its labels. Don't let a judge's preference between two texts decide a release until you have measured that judge on cases with known answers.

## Calibrate the judge against reference labels {#calibrate-the-judge}

A judge's verdicts on reasons can't be checked against a golden result, so measure the judge first on a task where they can. The shop's golden questions offer one. Ask the same model to grade the agent's answers to answer questions as correct or incorrect, without showing it the golden result, and compare its verdicts with labels that `results_match()` computes from the golden result. Those reference labels are nobody's opinion: anyone can recompute them from `questions.toml` and the recordings, and when one looks wrong, the fix is to the golden question, where it's open to correction like the rest of the book. The comparison measures how often the judge agrees with a check you trust, and in which direction it errs.

Agreement needs a chance correction. If most answers are wrong, a judge that calls everything wrong agrees most of the time and has learned nothing; the survey by Artstein and Poesio calls this the case where "chance-corrected agreement may be low even though Ao is high" ([Artstein and Poesio](https://aclanthology.org/J08-4004.pdf)). Cohen's kappa and Scott's pi both subtract the agreement that chance would give, and differ only in how they estimate it: kappa from each rater's own label shares, pi from the two raters' shares pooled. Thakur and colleagues dropped kappa for pi in a study of judges, because with kappa "the chance agreement adjusts for the observed average differences between raters, which is in fact part of what we intend to measure" ([Thakur et al.](https://arxiv.org/abs/2406.12624)). A judge that says "correct" more often than the reference is exactly what you want the statistic to catch, so we report both, and read the lower. In formulas, with p_o the observed agreement:

```text
p_o          = cases where the judge and the reference agree / cases
chance, κ    = Σ over labels (reference's share of the label × judge's share of the label)
chance, π    = Σ over labels (the label's share of both raters' labels pooled)²
kappa, pi    = (p_o − chance) / (1 − chance)
```

`agreement()` in `lib/judge.py` computes all three; scikit-learn's `cohen_kappa_score` uses the same definition of kappa ([scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)). The prompt, `JUDGE_ANSWER`, gives the judge the shop's glossary, the question, the role, the metric and SQL behind the answer and its result. The cases are every distinct answer with a number that schema-only SQL, the metrics-first agent and the declining agent gave to an answer question, on both splits, from their recordings: 56 in all. The judge prompts were written once, and no verdict changed them. What the judge is shown changed once. Schema-only SQL's query for `gq-009` has no `ORDER BY`, so its rows came back in another order on replay, and the prompt built from them no longer matched its recording. `shown()` in `lib/judge.py` now sorts the rows of any query without `ORDER BY` before the judge sees them. The recording made before that fix was set aside, and every judge call was recorded again from scratch with the fix in place, as the manifest of `judge-verdicts` says. Every reply matched the set-aside recording's, so no number in this chapter moved.

Example `judge-agreement` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.8:

```python
"""Calibrate the judge: its verdicts on the book's recorded answers against labels from results_match()."""
from lib.judge import agreement, answer_messages, kappa_one_verdict, parse_verdict, recorded_cases
from lib.model import RecordedModel
from lib.semantic import load
from lib.warehouse import connect

con, layer = connect(), load()
judge = RecordedModel("judge-verdicts")
cases, _ = recorded_cases(con, layer)          # every distinct answer with a number, with its reference label
judged = {c.case_id: parse_verdict(judge.complete(answer_messages(c.question, c.answer))) for c in cases}
verdicts = {case_id: v.label for case_id, v in judged.items()}
print(f"cases: {len(cases)}")
print(f"reference correct: {sum(c.reference == 'correct' for c in cases)}")
print(f"judge correct: {list(verdicts.values()).count('correct')}")
print(f"judge unparsed: {list(verdicts.values()).count('unparsed')}")
subsets = {"all": cases, "schema-only": [c for c in cases if c.case_id.endswith("schema-only")],
           "metric agents": [c for c in cases if not c.case_id.endswith("schema-only")]}
for name, subset in subsets.items():
    a = agreement([c.reference for c in subset], [verdicts[c.case_id] for c in subset])
    print(f"{name} cases: {a.n}")
    print(f"{name} cases the reference labels correct: {sum(c.reference == 'correct' for c in subset)}")
    print(f"{name} observed agreement: {a.observed:.2f}")
    print(f"{name} Cohen's kappa: {a.kappa:.2f}")
    print(f"{name} Scott's pi: {a.pi:.2f}")
    low, high = kappa_one_verdict([c.reference for c in subset], [verdicts[c.case_id] for c in subset])
    print(f"{name} kappa with any one verdict changed: {low:.2f} to {high:.2f}")
for reference, verdict, label in (("incorrect", "correct", "wrong answers the judge called correct"),
                                  ("correct", "incorrect", "right answers the judge called incorrect")):
    ids = [c.case_id for c in cases if c.reference == reference and verdicts[c.case_id] == verdict]
    print(f"{label}: {len(ids)} of {sum(c.reference == reference for c in cases)}")
    print(f"{label}, cases: {', '.join(ids)}")
# Read the reasons: how many rejections of right answers say a year's filter keeps only its first day?
first_day = [c.case_id for c in cases if c.reference == "correct" and judged[c.case_id].label == "incorrect"
             and any(w in judged[c.case_id].reason for w in ("January 1", "first day"))]
print(f"right answers rejected for reading a year's filter as January 1: {len(first_day)}")
```

Output:

```text
cases: 56
reference correct: 26
judge correct: 20
judge unparsed: 0
all cases: 56
all cases the reference labels correct: 26
all observed agreement: 0.75
all Cohen's kappa: 0.49
all Scott's pi: 0.48
all kappa with any one verdict changed: 0.45 to 0.53
schema-only cases: 23
schema-only cases the reference labels correct: 5
schema-only observed agreement: 0.74
schema-only Cohen's kappa: 0.10
schema-only Scott's pi: 0.09
schema-only kappa with any one verdict changed: -0.14 to 0.31
metric agents cases: 33
metric agents cases the reference labels correct: 21
metric agents observed agreement: 0.76
metric agents Cohen's kappa: 0.51
metric agents Scott's pi: 0.50
metric agents kappa with any one verdict changed: 0.44 to 0.58
wrong answers the judge called correct: 4 of 30
wrong answers the judge called correct, cases: gq-002 schema-only, gq-004 schema-only, gq-018 metrics-first, gq-035 metrics-first
right answers the judge called incorrect: 10 of 26
right answers the judge called incorrect, cases: gq-014 schema-only, gq-016 schema-only, gq-027 schema-only, gq-031 schema-only, gq-003 metrics-first, gq-006 metrics-first, gq-008 metrics-first, gq-015 metrics-first, gq-027 metrics-first, gq-029 metrics-first
right answers rejected for reading a year's filter as January 1: 6
```

The judge agrees with the reference on 0.75 of the cases, with a kappa of 0.49 and a pi of 0.48. Split by agent, the prevalence effect shows. On schema-only SQL's answers, most of them wrong, observed agreement is 0.74 and kappa only 0.10: the judge agreed mostly by calling wrong answers wrong, and rarely picked out the few right ones. On the metric agents' answers, agreement is 0.76 with a kappa of 0.51. These kappas rest on few cases, and the example shows how far one case moves each. Schema-only SQL gave 23 answers, only 5 of them right, and changing any one of the judge's verdicts on them puts kappa anywhere from -0.14 to 0.31. On the 33 metric-agent answers, one verdict moves it within 0.44 to 0.58, and on all 56, within 0.45 to 0.53. Read the first decimal of these kappas, not the second. Kappa and pi barely differ here, because the judge and the reference use each label about as often; when a judge leans hard one way, they part.

The direction of the errors matters more than the totals. The judge called 4 of 30 wrong answers correct, among them `gq-018`, chapter 6's near-miss refund metric. It called 10 of 26 right answers incorrect, and 6 of those rejections say that the SQL keeps only January 1 of the year, a misreading of the semantic layer's `DATE_TRUNC('YEAR', …) = '2025-01-01'`. The others reject schema-only answers that filter on `placed_at` rather than the local order day: the judge grades the method, and on those questions the number happened to come out the same. So the shop's judge leans strict, not lenient, as Thakur and colleagues report of the judges they studied ([Thakur et al.](https://arxiv.org/abs/2406.12624)), and it can't read the compiled SQL it's shown.

The judge is also the model that wrote every answer here. Self-preference, a judge that "scores its own outputs higher than others' while human annotators consider them of equal quality" ([Panickssery et al.](https://arxiv.org/abs/2404.13076)), is a known bias, and familiarity, text that has low perplexity for the judge, is one explanation of it ([Wataoka et al.](https://arxiv.org/abs/2410.21819)). With one model writing every answer, this measurement can't separate self-preference from other errors. It measures the net bias against a check that doesn't depend on the model; it doesn't remove the bias.

**Working rule:** Before you use a judge on text, measure it on cases whose answers a check can label, with labels anyone can recompute. Report observed agreement with Cohen's kappa and Scott's pi, split by the kinds of answer you'll judge, list the errors in each direction, and say how far one case moves kappa when the cases number a few dozen. Thresholds such as 0.8 are conventions, not results ([Artstein and Poesio](https://aclanthology.org/J08-4004.pdf)); at a kappa near 0.5, use the judge to choose what a person reads, never to pass or fail a release on its own.

## Repeat runs to see the variance {#repeat-to-see-variance}

Every score so far came from one run per question, and a run is a sample. The book's recordings sample each reply at Qwen's recommended temperature of 0.7, with one fixed seed reset before every call, so a replay gives the same reply every time, and a different seed can give a different one. A score from one seed is one draw from the scores the agent could get. Miller recommends treating an evaluation as an experiment and "reducing variance by resampling answers" several times per question ([Miller](https://arxiv.org/abs/2411.00640)). The alternative, lowering the temperature until runs agree, measures a different model from the one you serve.

The recording `repeat-runs` holds the same 12 dev questions run under four more seeds, 1 to 4, for both chapter 6's metrics-first agent and chapter 8's declining agent, with the same prompts, tools, sampling settings and four-call limit as their original recordings. With the original runs, made with seed 2718, each question has five runs per agent. `SeededRecording` in `lib/regressions.py` replays one agent's calls for one seed. The 12 questions are every dev answer or decline question that either agent missed in its original run, and the first five others in ID order, so they are harder than the split's average and their flip rates are an upper end. The recording also runs the declining agent once more with seed 2718 itself, to measure something the book has so far assumed: that a run with the same seed replays byte for byte on this runtime.

Example `seed-variance` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.8:

```python
"""Five runs of 12 dev questions per agent, one per seed: how much a score moves, and which questions flip."""
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.regressions import ORIGINAL_SEED, SeededRecording, replay
from lib.semantic import load
from lib.warehouse import connect

con, layer = connect(), load()
QUESTIONS = ("gq-001", "gq-002", "gq-003", "gq-004", "gq-005", "gq-007", "gq-008", "gq-012", "gq-016", "gq-017",
             "gq-018", "gq-020")                         # the 12 questions repeat-runs holds
questions = [q for q in load_golden() if q.question_id in QUESTIONS]
seeds = (ORIGINAL_SEED, 1, 2, 3, 4)                      # 2718 replays the original recordings
for agent in ("metrics-first", "declining"):
    per_question = {q.question_id: 0 for q in questions}
    scores = []
    for seed in seeds:
        runs = replay(con, layer, agent, questions, seed=seed)
        scores.append(sum(r.outcome == "correct" for r in runs))
        for r in runs:
            per_question[r.question.question_id] += r.outcome == "correct"
        print(f"{agent} seed {seed}: {scores[-1]} of {len(questions)} correct")
    spread = f"{min(scores)} to {max(scores)}" if min(scores) < max(scores) else f"{min(scores)} at every seed"
    print(f"{agent} correct across seeds: {spread}")
    flips = [f"{q} ({n} of 5)" for q, n in per_question.items() if 0 < n < 5]
    print(f"{agent} questions that flip: {len(flips)}")
    print(f"{agent} flipping: {', '.join(flips)}")
    print(f"{agent} always correct: {sum(n == 5 for n in per_question.values())}")
    print(f"{agent} never correct: {sum(n == 0 for n in per_question.values())}")

# Does a run replay byte for byte? The declining agent ran again with seed 2718; compare it with decline-runs.
again, original = SeededRecording("declining", ORIGINAL_SEED).calls, RecordedModel("decline-runs").calls
same = sum(key in original and call["reply"] == original[key]["reply"] for key, call in again.items())
print(f"seed {ORIGINAL_SEED} again: {same} of {len(again)} calls identical to decline-runs")
```

Output:

```text
metrics-first seed 2718: 6 of 12 correct
metrics-first seed 1: 6 of 12 correct
metrics-first seed 2: 6 of 12 correct
metrics-first seed 3: 6 of 12 correct
metrics-first seed 4: 5 of 12 correct
metrics-first correct across seeds: 5 to 6
metrics-first questions that flip: 1
metrics-first flipping: gq-008 (4 of 5)
metrics-first always correct: 5
metrics-first never correct: 6
declining seed 2718: 6 of 12 correct
declining seed 1: 6 of 12 correct
declining seed 2: 6 of 12 correct
declining seed 3: 6 of 12 correct
declining seed 4: 6 of 12 correct
declining correct across seeds: 6 at every seed
declining questions that flip: 0
declining flipping:
declining always correct: 6
declining never correct: 6
seed 2718 again: 24 of 24 calls identical to decline-runs
```

The replay check comes first, because everything else rests on it: `seed 2718 again: 24 of 24 calls identical to decline-runs`. On this runtime, llama.cpp on the CPU with one request at a time and the seed reset before each call, the second run with seed 2718 matched the first on every call. That is one agent on 12 questions on one machine, not a guarantee for every runtime, but it shows that the differences between seeds here come from sampling, not from the runtime. That matches the cause one lab found for variation at temperature 0 on served models, results that depend on how requests are batched ([He et al.](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)), which a single local request avoids; a served API gives no such promise.

Across the five seeds, the metrics-first agent got 5 to 6 of the 12 questions right, and the declining agent 6 at every seed. Per question, the runs are steadier than one might fear at a temperature of 0.7. The declining agent's outcome never changed with the seed: 6 questions were always right and 6 never. The metrics-first agent had 1 question that flips, `gq-008 (4 of 5)`: total revenue in 2025. That is the question chapter 8 wondered about, and the repeats answer it. Under the declining prompt, `gq-008` was wrong in every run, so its failure isn't chance: the new prompt moved the model off net revenue on that question, to the gross revenue [chapter 8](#measure-declines) saw in its one run.

We think the steadiness comes from the shop's design. Most of the agent's choices are among a few metric names, and the semantic layer turns each choice into the same SQL every time, so small differences in wording don't reach the result. A model that writes SQL has many more ways to differ. Studies of hosted models found larger swings, "accuracy variations up to 15% across naturally occurring runs" at settings meant to be deterministic ([Atil et al.](https://arxiv.org/abs/2408.04667)), on other tasks and APIs. Five runs of 12 questions is a small sample of the shop, too, chosen from the questions most likely to flip.

**Working rule:** Run each golden question several times at the sampling settings you serve, with seeds pinned in the recording's manifest, and confirm once that a seed replays exactly. Report per-question flips, not only the spread of the total, because a total can stay put while questions trade places. Never lower the temperature to make runs agree, unless that is the setting you will serve.

## Gate a change in CI {#gate-a-change}

A CI job that scores every change on the golden questions turns the measurements so far into a decision: merge or don't. [The scorecard](#score-a-run) showed why it can't rest on totals: the declining prompt left dev accuracy unchanged. Miller recommends "conducting statistical inference on the question-level paired differences" ([Miller](https://arxiv.org/abs/2411.00640)): score both configurations on the same questions and test the mean of the per-question differences. Pairing removes the variation between questions, which is far larger than a change's.

`Comparison` in `lib/regressions.py` takes, for each question, the share of runs correct under the base and under the candidate, and their difference. It reports the mean paired difference with a t interval, the standard error times Student's t for one fewer degrees of freedom than questions, counts the questions fixed and broken, and runs an exact sign test on the questions that changed. Miller's errors assume many questions; on 12, mostly unchanged, the t interval is a rough guide, and only the sign test assumes nothing. `gate()` applies two rules of our choosing: it fails on a stable break, a question the base got right in at least four runs of five and the candidate in at most one, and when the whole interval of the mean difference lies below zero. The first catches one regression an average would hide; the second, many small ones. The example gates chapter 8's prompt against chapter 6's, with one run per question and then with five, on the 12 questions of [`repeat-runs`](#repeat-to-see-variance). They were chosen from the outcomes, so the gate's numbers describe them, not the dev split.

Example `regression-gate` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.8:

```python
"""Gate a prompt change on paired, per-question differences over five recorded runs of each question."""
from lib.golden import load_golden
from lib.regressions import ORIGINAL_SEED, Comparison, gate, replay, smallest_detectable, t_quantile
from lib.semantic import load
from lib.warehouse import connect

con, layer = connect(), load()
QUESTIONS = ("gq-001", "gq-002", "gq-003", "gq-004", "gq-005", "gq-007", "gq-008", "gq-012", "gq-016", "gq-017",
             "gq-018", "gq-020")                         # the 12 questions repeat-runs holds
questions = [q for q in load_golden() if q.question_id in QUESTIONS]
seeds = (ORIGINAL_SEED, 1, 2, 3, 4)
correct = {agent: {q.question_id: [] for q in questions} for agent in ("metrics-first", "declining")}
for agent, runs in correct.items():
    for seed in seeds:
        for run in replay(con, layer, agent, questions, seed=seed):
            runs[run.question.question_id].append(run.outcome == "correct")

# One run each, as a CI job that runs every question once would see it.
once = Comparison({q: r[:1] for q, r in correct["metrics-first"].items()},
                  {q: r[:1] for q, r in correct["declining"].items()})
fixed, broken = once.moved()
print(f"one run: fixed {len(fixed)} ({', '.join(fixed)}), broken {len(broken)} ({', '.join(broken)})")
print(f"one run sign test p: {once.sign_test():.2f}")
print(f"one run stable breaks: {', '.join(once.stable_breaks()) or 'none'}")   # with one run, every flip is "stable"

five = Comparison(correct["metrics-first"], correct["declining"])
for q in five.questions:
    print(f"{q}: metrics-first {sum(five.base[q])} of 5, declining {sum(five.candidate[q])} of 5")
fixed, broken = five.moved()
print(f"five runs: fixed {len(fixed)} ({', '.join(fixed) or 'none'}), broken {len(broken)} ({', '.join(broken) or 'none'})")
low, high = five.interval()
print(f"five runs mean paired difference: {five.mean_difference:+.2f}")
print(f"five runs 95% interval: {low:+.2f} to {high:+.2f}")
print(f"t multiplier, {len(five.questions) - 1} degrees of freedom: {t_quantile(0.975, len(five.questions) - 1):.2f}")
print(f"five runs interval half-width: {five.half_width():.2f}")
k = smallest_detectable(len(five.questions))
print(f"fewest clean flips the mean rule detects: {k} of {len(five.questions)}")
print(f"smallest mean change the mean rule detects: {k / len(five.questions):.2f}")
print(f"five runs sign test p: {five.sign_test():.2f}")
passed, reasons = gate(five)
print(f"gate: {'pass' if passed else 'fail'}")
print("\n".join(f"gate reason: {r}" for r in reasons))
```

Output:

```text
one run: fixed 1 (gq-020), broken 1 (gq-008)
one run sign test p: 1.00
one run stable breaks: gq-008
gq-001: metrics-first 5 of 5, declining 5 of 5
gq-002: metrics-first 5 of 5, declining 5 of 5
gq-003: metrics-first 5 of 5, declining 5 of 5
gq-004: metrics-first 5 of 5, declining 5 of 5
gq-005: metrics-first 5 of 5, declining 5 of 5
gq-007: metrics-first 0 of 5, declining 0 of 5
gq-008: metrics-first 4 of 5, declining 0 of 5
gq-012: metrics-first 0 of 5, declining 0 of 5
gq-016: metrics-first 0 of 5, declining 0 of 5
gq-017: metrics-first 0 of 5, declining 0 of 5
gq-018: metrics-first 0 of 5, declining 0 of 5
gq-020: metrics-first 0 of 5, declining 5 of 5
five runs: fixed 1 (gq-020), broken 1 (gq-008)
five runs mean paired difference: +0.02
five runs 95% interval: -0.23 to +0.26
t multiplier, 11 degrees of freedom: 2.20
five runs interval half-width: 0.25
fewest clean flips the mean rule detects: 4 of 12
smallest mean change the mean rule detects: 0.33
five runs sign test p: 1.00
gate: fail
gate reason: stable break: gq-008
```

With one run each, the change fixed `gq-020` and broke `gq-008`, and the sign test gives p = 1.00. The stable-break rule would fail it (`one run stable breaks: gq-008`), but with one run every flip counts as stable, so the rule needs repeated runs. With five runs, `gq-008` is a stable break (`gq-008: metrics-first 4 of 5, declining 0 of 5`), and the fix to `gq-020` is as steady (`gq-020: metrics-first 0 of 5, declining 5 of 5`). The mean paired difference is +0.02, with a t multiplier of 2.20 and an interval of -0.23 to +0.26, so on average the change did nothing measurable. The gate says `fail`, for the reason `stable break: gq-008`. The prompt fixed one question and reliably broke another, and someone has to choose, or fix it, before it merges.

The gate also has a blind spot. The interval's half-width, 0.25 here, belongs to this comparison, because it depends on how much the differences vary. What the mean rule can detect follows from the rule: the fewest questions that must turn from always wrong to always right, the rest unchanged, for the interval to exclude zero is 4 of 12, a mean change of 0.33. Breaks mirror it. Anything smaller passes the mean rule either way, and only the stable-break rule and a person reading the moved questions stand in its way. A changed prompt fails the gate with `MissingRecording` until it is recorded, which is the moment to record it five times, not once.

**Working rule:** Gate a change to prompts, context or metrics on paired, per-question differences over repeated runs, never on a difference of totals. Fail on any stable break and on a mean difference whose interval lies below zero, write both rules down as your choice, and compute the smallest change they can detect on your set. When the gate fails, read the questions that moved before you touch the rules.

### Catch a schema change before users do {#catch-a-schema-change}

The warehouse changes under the agent too: a column renamed upstream, a table rebuilt, a type narrowed. Three checks catch a schema change without calling a model: every golden question's SQL still runs, every metric in the semantic layer still compiles and runs, and every recorded agent run still replays. The last works because [`RecordedModel`](#ask-for-sql) looks replies up by the hash of the exact messages: when a tool returns an error the model never saw, the next prompt has no recording, and the replay fails loudly with `MissingRecording` instead of passing.

The example applies one migration an upstream team might ship, renaming `analytics.fct_orders.net_revenue_eur` to `net_revenue_ex_tax_eur`, to a new copy of the shop's warehouse, built by `migrated()` in `lib/regressions.py`. `schema_checks()` runs the three checks. Then the example makes the fix, one line in the metric's `expr`, in a copy of the semantic layer's YAML, and runs the checks again.

Example `renamed-column-caught` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.8:

```python
"""An upstream rename of one column, caught by three checks that need no model, and the one-line fix."""
import shutil
import tempfile
from pathlib import Path

from lib.golden import load_golden
from lib.regressions import migrated, schema_checks
from lib.semantic import SEMANTIC_DIR, load

RENAME = "ALTER TABLE analytics.fct_orders RENAME COLUMN net_revenue_eur TO net_revenue_ex_tax_eur"
con = migrated(RENAME)
golden = load_golden()
dev = [q for q in golden if q.split == "dev"]

failed = schema_checks(con, load(), golden)
print(f"golden SQL that fails: {len(failed['golden SQL'])} of {sum(bool(q.golden_sql) for q in golden)}")
print(f"golden questions affected: {', '.join(failed['golden SQL'])}")
print(f"metrics that fail: {', '.join(failed['metrics'])}")
replays = schema_checks(con, load(), dev)["replays"]
print(f"recorded dev runs that no longer replay: {len(replays)} of {sum(q.kind != 'forbidden' for q in dev)}")
print(f"runs that stop: {', '.join(replays)}")

# The fix: the metric's expr names the new column. A copy of the YAML stands in for the commit that changes it.
fixed = Path(tempfile.mkdtemp()) / "semantic"
shutil.copytree(SEMANTIC_DIR, fixed)
metrics = fixed / "metrics.yml"
metrics.write_text(metrics.read_text().replace("expr: net_revenue_eur", "expr: net_revenue_ex_tax_eur"))
after = schema_checks(con, load(fixed), dev)
print(f"after the fix, metrics that fail: {', '.join(after['metrics']) or 'none'}")
print(f"after the fix, recorded dev runs that no longer replay: {len(after['replays'])}")
shutil.rmtree(fixed.parent)
```

Output:

```text
golden SQL that fails: 16 of 34
golden questions affected: gq-001, gq-002, gq-003, gq-006, gq-007, gq-008, gq-009, gq-010, gq-011, gq-012, gq-017, gq-025, gq-026, gq-034, gq-038, gq-040
metrics that fail: net_revenue, average_order_value
recorded dev runs that no longer replay: 8 of 21
runs that stop: gq-001, gq-002, gq-003, gq-006, gq-009, gq-010, gq-011, gq-017
after the fix, metrics that fail: none
after the fix, recorded dev runs that no longer replay: 0
```

Each check catches the rename. 16 of 34 golden queries fail to run. Two metrics fail, `net_revenue, average_order_value`, because the semantic layer's YAML names the old column. And 8 of 21 of the declining agent's recorded dev runs stop with `MissingRecording`: `gq-001, gq-002, gq-003, gq-006, gq-009, gq-010, gq-011, gq-017`. `gq-008` and `gq-012` still replay, because the agent answered them with gross revenue, which the rename doesn't touch. A replay that passes says that nothing the run touched has changed, not that the run is right.

After the fix, no metric fails and every recorded run replays: `after the fix, recorded dev runs that no longer replay: 0`. The agent never sees a column's name, only metrics, so its prompts are the same and the recordings stay valid. The golden SQL names the column directly, so the failing golden queries need the same rename, which is the cost of golden SQL written against tables: it is a second copy of the definitions, and it has to change with them. None of the checks needs the model, so CI can run them on every change to the warehouse's models.

**Working rule:** Run the golden SQL, every metric and every recorded replay in CI on changes to the warehouse as well as to the agent, and treat `MissingRecording` as a failure, never as a reason to skip a question. When a check fails after a schema change, fix the definition in the semantic layer before you record anything again.

## What goes wrong in production {#regressions-in-production}

The shop's measurements run on recordings of one small model and 48 questions. The same measurements on a real agent fail in these ways, and each has a way to notice.

**The judge changes when its model does.** A new model version, a new judge prompt or a new rubric is a new judge, and its agreement with the reference labels has to be measured again. Keep the calibration cases and their labels in the repository beside the judge prompt, and re-run the agreement whenever either changes. A kappa that moves with no change to the agent is the judge moving.

**The judge can't read what it judges.** The shop's judge misread the semantic layer's compiled year filter and rejected right answers for it. A judge shown SQL it can't parse grades the SQL's look, not its meaning. Give a judge what it can check, such as the metric's name and filters rather than compiled SQL, and read the reasons behind its rejections before you read its score.

**Live runs vary in ways replays don't.** A replayed run is the same every time, so CI on recordings is deterministic. A live model isn't, even at temperature 0 on a served API: one study saw "accuracy variations up to 15% across naturally occurring runs" ([Atil et al.](https://arxiv.org/abs/2408.04667)), and one lab traced much of it to a server whose results depend on how many requests share a batch ([He et al.](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)). Record repeated runs when you record, and treat a live score that differs from the recorded one as variance until repeats show otherwise.

**Lowering the temperature hides the variance instead of removing it.** It is tempting to set temperature 0 so that runs agree. Miller advises against it "unless the purpose is to study the model at the new temperature" ([Miller](https://arxiv.org/abs/2411.00640)): the model you measure is then not the one you serve. Measure at the settings you serve, and resample.

**A gate that always fails gets switched off.** With a dozen questions, a strict rule fires on noise, and people learn to merge past it. Set the gate's rules with the people who answer for the numbers, write down what the gate can and can't detect, and review its false alarms each month.

**Re-recording turns into tuning.** Every prompt change needs new recordings, and recording the dev split again and again while tuning makes dev optimistic, as [chapter 6](#measure-metrics-first) recorded. Say in each manifest how many times a split was recorded, and record the test split once, after tuning ends.

**Working rule:** Before a gate guards a production agent, keep its judge's calibration cases beside the judge prompt and re-measure on every change to either, show the judge what it can check, record repeated runs at the settings you serve, agree the gate's rules with the people who answer for the numbers, and count in each manifest how many times a split was recorded.

## Decisions this chapter made {#regressions-decisions}

- **A run is reported as a scorecard,** not an accuracy: correct with a Wilson interval, wrong numbers, failures, chapter 8's decline measures, and model calls and prompt tokens per question, for every agent on the same questions.
- **The test split was scored once for the final numbers.** Chapter 8's declining agent was recorded on test once, in `decline-runs-test`, with its prompt unchanged, beside the test runs chapters 3 and 6 recorded.
- **A judge grades only what `results_match()` can't:** reasons for declining, compared in pairs, each pair in both orders. Numbers are always compared with the golden result.
- **The judge is the book's own model with its own prompts,** and every verdict is recorded in `judge-verdicts`. After `shown()` was fixed to sort unordered rows, the whole recording was made again from scratch.
- **The judge's reference labels come from `results_match()`,** so anyone can recompute them, instead of from a person's grades. They measure whether the number is right, not whether the method is.
- **Agreement is reported as observed agreement, Cohen's kappa and Scott's pi,** overall and split by agent, with the errors in each direction listed. Each kappa rests on a few dozen cases, so the example shows how far one verdict moves it. The judge, at a kappa near 0.5, chooses what a person reads and never passes a release alone.
- **Variance comes from five runs per question,** the original recording and four more seeds, at the sampling settings every recording uses, on 12 dev questions chosen to include every miss.
- **The gate compares configurations in pairs, question by question,** over repeated runs: it fails on a stable break or on a mean paired difference whose t interval lies below zero. Both rules are the book's choice, and on 12 questions the mean rule detects nothing smaller than 4 of 12 questions changing outright.
- **CI also checks the warehouse:** golden SQL runs, every metric compiles and runs, and every recorded run replays, with `MissingRecording` treated as a failure.
