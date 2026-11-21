---
title: "Evaluating LLM Applications"
chapter: "Put the evaluation in CI, and compare variants on traffic"
chapter_id: keep-the-evaluation-running
book: evaluating-llm-applications
edition: 2026.11.5
verified: 2026-11-21
edition_code: ZZQG-NPXH
canonical: https://rollingedition.com/evaluating-llm-applications/keep-the-evaluation-running
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Put the evaluation in CI, and compare variants on traffic,” chapter 11 of Evaluating LLM Applications, Edition 2026.11.5, examples passed Nov 21, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/keep-the-evaluation-running. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Put the evaluation in CI, and compare variants on traffic

By the end of this chapter you can put the evaluation into a gate that blocks a change only when the change is measurably worse. You can also say what a live comparison of two variants can show, and what it cannot.

The sablefile assistant answers from the tool's docs, and a team changes its prompt, its retrieval or its model from week to week. The team wants to know before a change merges whether the assistant got worse. A gate that fails on any drop in the pass rate looks like the safe choice, and it is not. With 80 dev items, one item moves a pass rate by about 1.3 points, so a gate on the raw rates would block on a difference of one or two items. A team that is blocked on noise often learns to override the gate, and then the gate protects nothing.

[Chapter 1](measure-before-you-change) ran the whole evaluation for the first time: the test set, the checks, the judge and the replayed answers. This chapter keeps that run in place. It takes three parts in turn: a gate that respects the interval, the items whose verdicts change between samples, and the tests of the evaluation's own code. Then it maps the same parts onto an evaluation framework's words, and it ends with what a comparison of variants on live traffic can and cannot show.

## A gate that respects the interval {#a-gate-that-respects-the-interval}

A gate is a rule that stops a change from merging. For this book, the rule rests on one number: the paired difference in pass rate between a candidate and the baseline, over the same dev items. The comparison is paired, as [Chapter 8](intervals-and-sample-size#paired-comparisons) defines it. For each item, the candidate's verdict minus the baseline's verdict, averaged over the items, with the interval bootstrapped over items. Because both runs answer the same questions, the items on which both runs agree cancel out of the difference.

The gate has one rule. It fails only when the upper bound of the interval is below minus the threshold. The upper bound is the least negative reading the data still allows, so the gate fails when even the most optimistic reading of the data shows a drop bigger than the threshold. A naive gate would fail whenever the point estimate of the difference is below minus the threshold, and it would fail on noise. The price of the book's rule is that it passes some real drops the data cannot yet prove, which is why a pass is read with its width, as the next paragraphs explain.

The threshold is five points. The example's comment says it is a choice for this book, not a standard. With the dev set at this size, one item is about 1.3 points, so five points is four items net.

The first run is a large drop, as this judge measures it. The second model, Qwen3-0.6B, is smaller than the 4B baseline, and it answered the same dev items. The judge is Qwen3-4B-Instruct-2507, the baseline's own model, so the gap can't separate a weaker assistant from self-preference. [Self-preference](when-the-judge-stops-being-reliable#self-preference) explains why this book cannot test that. Read the decision last, since it follows from the interval.

Example `gate-real-drop` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.5:

```python
"""Runs the gate on second-model against the baseline over the eighty dev items: both pass rates with their counts, the paired
difference, its interval, the threshold and the decision. The gate fails only when the upper bound of the interval is below
minus the threshold, so a drop that the interval cannot rule out below the threshold does not fail it."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.gate import FAIL, gate
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import interval_points, pct
from lib.testset import load_items

BASELINE = "judge-answers-baseline"
CANDIDATE = "judge-answers-second-model"
# Five points is this gate's threshold, chosen for the book, not a standard. With eighty dev items one item moves a rate
# by 1.25 points, so five points is four items net: a smaller threshold would ask the gate to see drops the interval
# cannot resolve at this size.
THRESHOLD_POINTS = 5.0

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
baseline_found, baseline_unreadable = readable_verdicts(BASELINE, items, REF_SHA256)
candidate_found, candidate_unreadable = readable_verdicts(CANDIDATE, items, REF_SHA256)
for label, unreadable in (("baseline", baseline_unreadable), ("second-model", candidate_unreadable)):
    details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
    print(f"unreadable verdicts, {label}: {len(unreadable)}{details}")
# An item the judge did not give a readable verdict on, under either run, is left out of both sides: a paired
# difference needs the same items under both runs.
excluded = {item_id for item_id, _ in baseline_unreadable + candidate_unreadable}
kept = [item_id for item_id in items if item_id not in excluded]
first = passed({item_id: baseline_found[item_id] for item_id in kept})  # 1.0 or 0.0 per item, in id order
second = passed({item_id: candidate_found[item_id] for item_id in kept})

result = gate(first, second, threshold_points=THRESHOLD_POINTS)
print(f"dev items compared (n): {result.n}")
print(f"baseline pass rate: {pct(int(first.sum()), result.n)}")
print(f"second-model pass rate: {pct(int(second.sum()), result.n)}")
print(f"difference, second-model minus baseline: {100 * result.difference:+.1f} points")
print(f"{100 * result.level:.0f}% interval of the difference: {interval_points(result.lo, result.hi)}")
print(f"upper bound of the interval: {100 * result.hi:+.1f} points")
print(f"threshold: {THRESHOLD_POINTS:.1f} points")
if result.decision == FAIL:
    print(f"decision: fail, since the upper bound {100 * result.hi:+.1f} is below {-THRESHOLD_POINTS:+.1f}")
else:
    print(f"decision: pass, since the upper bound {100 * result.hi:+.1f} is not below {-THRESHOLD_POINTS:+.1f}")
```

Output:

```text
unreadable verdicts, baseline: 1 (q-0043, "VERDICT: PARTIAL")
unreadable verdicts, second-model: 0
dev items compared (n): 79
baseline pass rate: 78.5% (62 of 79)
second-model pass rate: 40.5% (32 of 79)
difference, second-model minus baseline: -38.0 points
95% interval of the difference: [-48.1, -26.6] points
upper bound of the interval: -26.6 points
threshold: 5.0 points
decision: fail, since the upper bound -26.6 is below -5.0
```

The gate fails, and the reason is in the interval, not in the point estimates. The baseline passes 78.5% (62 of 79). The second model passes 40.5% (32 of 79).

The comparison covers 79 items, not all of the dev items, because an item whose baseline verdict was unreadable is left out of both runs. A paired difference needs the same items under both. The difference, second model minus baseline, is -38.0 points, and its 95% interval is [-48.1, -26.6] points.

The upper bound is -26.6 points, and the threshold is 5.0 points, so even the upper bound sits well below the threshold. This drop is not one the interval can explain away, so the gate is built to fail on a drop of this kind, as this judge measures it. The decision reads: fail, since the upper bound -26.6 is below -5.0.

A smaller change gives a different result. Suppose the change drops the pass rate by less, or the set is smaller and the interval widens, so that the upper bound reaches above minus five points. The gate then passes. It has found no drop larger than the threshold, and it has not shown that the candidate is as good as the baseline. A pass with a wide interval is a weak pass, so the width of the interval is the reason to read it, not only the decision. How wide an interval gets at a given size, and how many items a small paired difference needs before it resolves, is what [Chapter 8](intervals-and-sample-size#how-many-questions) works through.

The gate's limit is its size. On 79 items, the upper bound has to fall well below minus the threshold before the gate fails, so small drops pass. [Chapter 8](intervals-and-sample-size#how-many-questions) estimates, at the disagreement it assumes, that 79 items are enough to show a ten-point difference with 80% power, and a five-point difference needs 316. The gate is a stricter test than that power calculation, so a real ten-point drop can still pass. The threshold and the set size have to be chosen together.

Some gates check more than one metric. Each extra metric is another chance for noise to look like a drop, so the gate takes a count of comparisons. With m metrics, each interval is taken at the level 1 minus 0.05 divided by m: 97.5% for two metrics and about 98.3% for three. Together the checks keep the chance of a false fail at or below five percent. The adjusted level is the one [Chapter 8](intervals-and-sample-size#many-comparisons) gives, and the gate uses the same one. The resample count stays at 2,000, and the seed stays fixed, so a rerun gives the same interval.

The gate runs on the dev items for every change, because a gate has to run each time and the team may have tuned on those items. Held-out is run once per release decision, against rules fixed before the run, as [Held-out, once](intervals-and-sample-size#held-out-once) explains. A fresh held-out set is needed after that.

To put the gate in CI, a job computes the gate on the candidate's recording and fails the build when the decision is fail. The gate reads only the per-item values, so the job needs no other state. A job that fails to run counts as a failed gate, because a skipped gate would look like a pass. The gate's own tests check the rule above. They run with the rest of the evaluation's tests in [the evaluation's own tests](#the-evaluations-own-tests).

**Working rule:** Report every paired difference with its interval and its n, and let the decision follow from the upper bound. Don't call a change better or worse from a point estimate, and don't read a pass with a wide interval as proof that the candidate matches the baseline.

## Flag flaky items, never edit them {#flaky-cases}

An item [flips](#variance-within-one-item) when its sampled replies get different verdicts. Each dev item has five verdicts from the variance set, and an item is flaky when they are not all the same. The variance set and the flip rate, the share of items that flip, are introduced in [Variance within one item](intervals-and-sample-size#variance-within-one-item). A team watches the flip rate to see how far the verdicts move when the assistant's replies do.

Each flagged item comes with its PASS count out of five, in id order, and the rule it is held to is printed beside the list.

Example `flaky-items` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.5:

```python
"""The dev items flagged as flaky: the judge's verdict differs across their five variance samples. Each flagged item prints its
PASS count out of five, sorted by id, and the count matches the flip rate in flip-rate.py, since both read the same per-item
counts. A flagged item is kept as it is, so the rule printed last is the whole policy: flagged, never edited or deleted."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.testset import load_items
from lib.variance import VARIANCE_SAMPLES, item_pass_counts

VARIANCE = "judge-answers-variance"
SAMPLES = len(VARIANCE_SAMPLES)

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
counts = item_pass_counts(VARIANCE, items)
for row in counts:
    if not row.complete:  # an unreadable sample is not a FAIL: the item is named here and not flagged
        samples = ", ".join(str(sample) for sample in row.unreadable)
        print(f"left out, unreadable verdict, {row.item_id}: samples {samples}")
flagged = [row for row in counts if row.flaky]
for row in flagged:
    print(f"{row.item_id}: {row.passes} of {SAMPLES} PASS")
print(f"flagged items: {len(flagged)}")
print(f"dev items compared (n): {sum(1 for row in counts if row.complete)}")
print("rule: flagged, never edited or deleted")
```

Output:

```text
left out, unreadable verdict, q-0043: samples 1, 4
q-0047: 4 of 5 PASS
q-0058: 1 of 5 PASS
flagged items: 2
dev items compared (n): 79
rule: flagged, never edited or deleted
```

Few items flip on this set. The flagged items come to 2 of the 79 dev items compared. Both flagged items are worth reading.

On q-0047, the verdicts across its five replies are 4 of 5 PASS, so most of its replies passed. On q-0058, the verdicts are 1 of 5 PASS, so most of its replies failed.

One item is set aside rather than used. The item q-0043 is left out, since its verdict was unreadable in samples 1, 4. An unreadable sample is not a fail. It is a sample the example cannot read, so the item is neither flagged nor counted on that basis.

The rule is that a flagged item stays flagged, never edited or deleted. It stays in the set with the verdicts the judge gave. Editing it until the judge agrees more often would hide the very signal the flag exists to show. Deleting it would shrink the set and make the pass rate look steadier than it is. The flag does its work when someone reads it. A flagged item with one PASS in five is a question about the item, the rubric, the judge or the assistant's replies, and it should be looked at before the next change is judged on it.

The count is small, and it describes this assistant, this judge and these dev items. It shows that few items flip in this set. It does not show that other assistants, sampling settings or judges flip as rarely. A team that changes any of them should run the variance set again before it trusts a low flip rate.

A flagged item can also move a paired difference from one run to the next. When a gate fails on a difference that depends on a flagged item, read the flag before the change.

**Working rule:** Flag an item whose verdicts differ across its samples, print its count beside the flag, and leave the item as it is. Report the flip rate with its denominator, and say that a low rate holds for this assistant, this judge and this set only.

## The evaluation's own tests {#the-evaluations-own-tests}

The evaluation is code, and its code can be wrong in ways that look like a result. A bug in the bootstrap, the verdict reader or the paired difference moves a number in the same way a change in the assistant would. So the evaluation has tests of its own, in a tests folder inside the book's library, and each module that the book adds brings its tests with it. The tests check the scoring code. They do not check the assistant. A passing test says that the code counts what it says it counts. It says nothing about whether the assistant answers well.

Those tests run in one process, and the outcomes are counted module by module. The example then prints pytest's exit code, from 9.2.0. The [exit-code reference](https://raw.githubusercontent.com/pytest-dev/pytest/9.2.0/doc/en/reference/exit-codes.rst) lists 0 as every test collected and passed, and 5 as no tests collected. So a run that tests nothing shows up as 5, not as a silent pass.

Example `own-tests-run` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · pytest 9.2.0 · typing-extensions 4.16.0), passing in Edition 2026.11.5:

```python
"""Runs the book's own tests, lib/tests, in this process and prints how many passed and failed in each module, then pytest's
exit code. Exit code 0 means every test was collected and passed. Exit code 5 means nothing was collected, so the example
prints the code it got rather than a silent pass. No paths and no timings are printed: they vary from run to run."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter
from pathlib import Path

import pytest

TESTS = Path(lib.__file__).resolve().parent / "tests"  # read here, never printed


class Outcomes:
    """Counts each test's outcome by module. A failed setup or teardown counts as a failure of its test."""

    def __init__(self) -> None:
        self.passed = Counter()
        self.failed = Counter()

    def pytest_runtest_logreport(self, report) -> None:
        # The node id starts with the file's path; keep only the module's name, so no path is printed.
        module = Path(report.nodeid.split("::")[0]).stem
        if report.when == "call" and report.passed:
            self.passed[module] += 1
        elif report.failed:
            self.failed[module] += 1


collector = Outcomes()
# -p no:terminal turns off pytest's own printing, which carries timings. That also removes the -q option, which belongs to
# the terminal reporter, so it is not passed. -p no:cacheprovider keeps .pytest_cache out of the working copy.
exit_code = pytest.main(
    [str(TESTS), "-p", "no:terminal", "-p", "no:cacheprovider"],
    plugins=[collector],
)

modules = sorted(path.stem for path in TESTS.glob("test_*.py"))  # every module, even one with no failures
print("tests by module (passed, failed):")
for module in modules:
    print(f"  {module}: {collector.passed[module]} passed, {collector.failed[module]} failed")
print(f"total: {sum(collector.passed.values())} passed, {sum(collector.failed.values())} failed")
print(f"pytest exit code: {int(exit_code)}")
```

Output:

```text
tests by module (passed, failed):
  test_bench: 11 passed, 0 failed
  test_bias: 14 passed, 0 failed
  test_both_orders: 14 passed, 0 failed
  test_calibration: 9 passed, 0 failed
  test_calibration_bootstrap: 8 passed, 0 failed
  test_contract: 5 passed, 0 failed
  test_gate: 11 passed, 0 failed
  test_guard: 4 passed, 0 failed
  test_judging: 3 passed, 0 failed
  test_stats: 10 passed, 0 failed
  test_support_verdict: 5 passed, 0 failed
  test_testset: 5 passed, 0 failed
  test_variance: 15 passed, 0 failed
total: 114 passed, 0 failed
pytest exit code: 0
```

The table gives the outcome for each module, with what the module tests beside it.

| Module | What it tests | Result |
| --- | --- | --- |
| test_bench | The benchmark loaders and scorers | 11 passed, 0 failed |
| test_bias | The length bands, unreadable verdicts, the flip direction and the band gap | 14 passed, 0 failed |
| test_both_orders | The pairwise reader and both orders: the mapping back to the replies, and the four kinds | 14 passed, 0 failed |
| test_calibration | Judge-against-human counts, agreement, kappa, TPR, TNR and the corrected pass rate | 9 passed, 0 failed |
| test_calibration_bootstrap | The crossover point and the bootstrap interval of the corrected pass rate | 8 passed, 0 failed |
| test_contract | The reply and verdict formats that the judge and the assistant must keep | 5 passed, 0 failed |
| test_gate | The gate's rule: a fail only when the upper bound is below minus the threshold | 11 passed, 0 failed |
| test_guard | The decline guard's rule and its threshold, on hand-made rows | 4 passed, 0 failed |
| test_judging | Reading judge verdicts, and the paired difference type | 3 passed, 0 failed |
| test_stats | The printing helpers and the seeded bootstrap | 10 passed, 0 failed |
| test_support_verdict | The faithfulness verdict reader: SUPPORTED or UNSUPPORTED on the first line | 5 passed, 0 failed |
| test_testset | Loading the test set, and the rules that look across items | 5 passed, 0 failed |
| test_variance | Per-item verdict counts over the variance set | 15 passed, 0 failed |

The totals come last: 114 passed, 0 failed, and the exit code is 0, the code for a run in which every collected test passed.

Read the table as a check on the instruments, not on the assistant. Run these tests first in the gate job, so that a broken scorer stops the job before it reads a pass rate. Nothing that varies between runs is printed: no timings and no paths. A reader can rerun the code and compare the output line for line.

**Working rule:** Run the evaluation's own tests before any run that reads a number, and treat exit code 5 as a failure, not a pass. A failing test in the scoring code means the numbers are not yet trustworthy, whatever they say.

## Running it as a framework task {#running-it-as-a-framework-task}

Teams that already use an evaluation framework can map the parts of this book onto its words, and it helps to see the mapping once. In Inspect AI 0.3.291, dated 17 November 2026 in [its changelog](https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_ai/0.3.291/CHANGELOG.md), a task is the recipe for an evaluation, made minimally of a dataset, a solver and a scorer, as [the framework's documentation at that version](https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_ai/0.3.291/docs/tasks.qmd) describes. On that reading, the test set is the dataset, with one sample per item. The assistant's path of retrieving and then answering is the solver, and the checks and the judge make up the scorer. The book does not run that mapping, and it does not claim to. Instead, the book keeps one example environment: one set of files that every chapter's examples import, pinned to the same versions, so the replay model, the checks and the gate are the same code in every chapter. This chapter describes where each part would go, so that a reader on a framework can move the parts over while the book's examples stay as they are.

**Working rule:** When you map an evaluation onto a framework, name the framework's version and the date of its documentation. Keep the test set, the checks and the replay model as the files the book's examples run, and treat the map as a reading of the documentation until someone runs it.

## Variants on traffic {#variants-on-traffic}

Offline, the test set and the replayed answers can say which variant is better on the items the team wrote. Once the assistant is live, a team may want to compare two variants on real questions, such as two prompts or two models, each sent to a share of users. That is a comparison, and it is only as good as the way users were assigned to the variants. If the people who see one variant are the ones who ask harder questions, the difference reflects them and not the variant. Random assignment, and an interval read the way the rest of this chapter reads one, are what turn a live comparison into a test. Kohavi and colleagues' guide, which [chapter 10](declining-when-the-docs-dont-say#what-to-accept) cites, recommends deciding the power and the effect to detect, and estimating the variability, before the test starts. Without that, a live comparison is a list of who saw which variant.

The feedback table in this section is not traffic. Its rows are generated. Each dev item's vote is drawn from a stated model with a fixed seed. An answer is right with probability 0.85. A user who sees a wrong answer gives a thumbs-down with probability 0.5 and a thumbs-up with 0.05. A user who sees a right answer gives a thumbs-down with 0.03 and a thumbs-up with 0.15. Most items get no vote at all. Whether each answer was right is drawn and then dropped, as it would be in a real log, so the table holds only the votes. It is a teaching device, and its figures are what the stated model produces. They say nothing about this assistant.

Example `feedback-table` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.5:

```python
"""A generated table of thumbs-up and thumbs-down rows over the eighty dev items, with what such a table can show and what it
can't. The rows are generated from a stated model with a fixed seed, not taken from users, so the table is a teaching
device only.

The model: an answer is right with probability 0.85. A user who sees a wrong answer gives thumbs-down with probability 0.5 and
thumbs-up with 0.05; one who sees a right answer gives thumbs-down with 0.03 and thumbs-up with 0.15. Most items get no vote.
The table keeps the votes only: whether each answer was right is drawn and then dropped, as it would be in a real log."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import numpy as np

from lib import SEED
from lib.stats import pct
from lib.testset import load_items

P_RIGHT = 0.85
P_DOWN_WRONG, P_UP_WRONG = 0.50, 0.05
P_DOWN_RIGHT, P_UP_RIGHT = 0.03, 0.15

rng = np.random.default_rng(SEED)  # one generator for the whole table, so the same seed gives the same rows
items = [item.id for item in load_items(split="dev")]
rows = []  # (item id, vote) for each item that got a vote
for item_id in items:
    right = rng.random() < P_RIGHT  # hidden: the table has no column for it
    draw = rng.random()
    down, up = (P_DOWN_RIGHT, P_UP_RIGHT) if right else (P_DOWN_WRONG, P_UP_WRONG)
    if draw < down:
        rows.append((item_id, "thumbs-down"))
    elif draw < down + up:
        rows.append((item_id, "thumbs-up"))

print("generated rows from a stated model, not user feedback (seed 0)")
print("item    vote")
for item_id, vote in rows:
    print(f"{item_id}  {vote}")

ups = sum(vote == "thumbs-up" for _, vote in rows)
downs = sum(vote == "thumbs-down" for _, vote in rows)
voted = len({item_id for item_id, _ in rows})
print(f"dev items: {len(items)}")
print(f"items with a vote: {voted}")
print(f"items nobody voted on: {len(items) - voted}")
print(f"thumbs-down among those who voted: {pct(downs, ups + downs)}")
print(f"thumbs-up among those who voted: {pct(ups, ups + downs)}")
print("what the table can show: the share of each kind of vote, among the votes cast, with its n.")
print("what it can't show: anything about the items nobody voted on; whether a thumbs-up answer was right.")
```

Output:

```text
generated rows from a stated model, not user feedback (seed 0)
item    vote
q-0002  thumbs-down
q-0006  thumbs-down
q-0007  thumbs-down
q-0008  thumbs-up
q-0009  thumbs-up
q-0011  thumbs-up
q-0020  thumbs-down
q-0027  thumbs-down
q-0028  thumbs-up
q-0030  thumbs-up
q-0035  thumbs-up
q-0040  thumbs-down
q-0056  thumbs-down
q-0057  thumbs-down
q-0059  thumbs-down
q-0060  thumbs-up
q-0064  thumbs-down
q-0070  thumbs-down
q-0072  thumbs-up
q-0079  thumbs-down
q-0080  thumbs-down
dev items: 80
items with a vote: 21
items nobody voted on: 59
thumbs-down among those who voted: 61.9% (13 of 21)
thumbs-up among those who voted: 38.1% (8 of 21)
what the table can show: the share of each kind of vote, among the votes cast, with its n.
what it can't show: anything about the items nobody voted on; whether a thumbs-up answer was right.
```

Under the stated model, only 21 of the 80 dev items get a vote, and 59 get none. So the table says little about the other items.

A vote is not a correctness label, and this table shows why. Under the stated model, answers are right 85% of the time, yet most votes are thumbs-down, because a wrong answer draws a vote far more often. Among the votes cast, thumbs-down is 61.9% (13 of 21). Thumbs-up is 38.1% (8 of 21).

A table of votes can show the share of each kind of vote, among the votes cast, with the count beside it, and the example's last lines say exactly that. It cannot show whether a thumbs-up answer was right, since the table has no column for correctness. It says nothing about the items nobody voted on, and a vote comes from someone who chose to vote on what they chose to read.

Joachims and colleagues studied clicks on search results in 2005 and found them informative but biased, so a click is not an absolute judgment of relevance. They report that relative preferences derived from clicks are reasonably accurate on average, [in their paper on interpreting clickthrough data](https://www.sigir.org/wp-content/uploads/2017/06/p003.pdf). This book uses that finding as an analogy only, and it is the book's own reading. A thumbs-up is a vote, not a label. A right answer can still draw a thumbs-down, and the table has no way to tell which votes those are.

Two groups of users are compared differently from the paired items above. Each user sees one variant, so the two groups are separate, and the interval for their difference is a different calculation from the paired one this chapter uses. [Chapter 8](intervals-and-sample-size#paired-comparisons) covers the paired comparison this chapter uses. It does not cover an interval for two separate groups.

A vote table also cannot compare variants unless each vote is tied to the variant the user saw. This table has no variant column, so it cannot compare anything. A live comparison would need that column, the random assignment above, and an interval. If few items get a vote, as in this generated table, the interval would be wide, and most items would have no vote to compare.

Before a real vote table could be trusted, it would need three things. Each vote would need to be tied to the variant the user saw. The share of items that get a vote would need to be reported with its count, since a table of votes speaks only to the items that were voted on. And a sample of its votes would need checking against correctness, so that a thumbs-up or a thumbs-down can be read against what it is meant to measure.

The book's parts add up to an evaluation for a feature of your own. A labelled test set comes first ([chapter 3](build-the-test-set)), then checks in code ([chapter 4](checks-in-code)). A judge with a rubric and a measured error follows ([chapter 5](a-judge-with-a-rubric), [chapter 6](calibrate-the-judge)). A comparison reports its interval and n ([chapter 8](intervals-and-sample-size)), and the gate in CI reads all of it. [Chapter 7](when-the-judge-stops-being-reliable) says where the judge stops being reliable. [Chapter 9](grounded-answers) and [chapter 10](declining-when-the-docs-dont-say) apply the same counts to grounding and declining.

The book leaves three subjects to others. [*A Primer on Search Relevance*](https://rollingedition.com/primer-on-search-relevance/) covers ranking metrics. [*Agent Harnesses*](https://rollingedition.com/agent-harnesses/) covers tasks that take several steps. *Observability for LLM Applications* covers tracing one request through retrieval and the model, and counting what each request costs. It is planned, so it is named here and not linked.

**Working rule:** Don't compare variants from traffic without random assignment and the variant recorded beside each vote or reply. Read a vote table as a share of the votes cast, with its count, and never as a measure of correctness.
