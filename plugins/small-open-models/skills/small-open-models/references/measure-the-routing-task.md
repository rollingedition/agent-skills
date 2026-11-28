---
title: "Small Open Models"
chapter: "Measure the routing task before you choose a model"
chapter_id: measure-the-routing-task
book: small-open-models
edition: 2026.11.17
verified: 2026-11-23
edition_code: 9CXG-7DRH
canonical: https://rollingedition.com/small-open-models/measure-the-routing-task
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Measure the routing task before you choose a model,” chapter 2 of Small Open Models, Edition 2026.11.17, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/measure-the-routing-task. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Measure the routing task before you choose a model

By the end of this chapter, you can say what each of the book's samples is for, compute the three measures the router is scored on with their denominators, and read a baseline that was recorded once and is reused for every comparison.

Today a hosted model routes the messages that reach the bank's support inbox. The book's router is a small open model that the bank would run itself, and the question is whether it can match that hosted model on the messages it keeps, and say so when it is not sure of a message. Before any model is compared, the comparison needs fixed data, fixed samples and fixed measures. Otherwise two numbers that look alike may come from different messages, or be divided by different counts.

This book doesn't call a hosted model, so it uses a stand-in, a larger open model: Qwen3-4B-Instruct-2507. Its answers come from the 4-bit Q4_K_M GGUF conversion that a third party published, at its pinned revision, with its answers limited to the 77 team names. It answers every test message once, in a recording, and the examples read those answers offline, so anyone can reproduce them. A reader with a model of their own can record its answers the same way, as [chapter 1](route-a-message#ask-a-model-for-one-team) shows.

## The data and its licence {#the-data-and-its-licence}

The router is trained and measured on BANKING77, a public dataset of customer service queries in the banking domain (Casanueva et al., 2020). Each message carries one of 77 labels. BANKING77 calls its labels intents; they are the inbox's teams ([chapter 1](route-a-message)).

Casanueva et al. (2020) introduce the dataset in *[Efficient Intent Detection with Dual Sentence Encoders](https://arxiv.org/abs/2003.04807)*, in the Proceedings of the 2nd Workshop on Natural Language Processing for Conversational AI, pages 38–45 (Anthology ID 2020.nlp4convai-1.5; arXiv 2003.04807). Their abstract describes it as a hard dataset from one domain, with 13,083 labelled examples over 77 intents, and their section 3 gives the same count for the banking-domain set, which they name BANKING 77. The data card gives the commit the files come from. The two files together hold the same 13,083 messages, which the next section counts.

The data card also states the facts the book relies on. It says that the files are a copy of the source's own train and test split, which is not drawn again, and that every team appears in both files. A router trained on the training file and scored on the test file is scored on the source's own held-out messages, not on a split that the book chose.

The licence is CC BY 4.0. The LICENSE file that sits beside the data begins "Attribution 4.0 International". Under that licence the data may be shared and adapted, provided the source is credited. The book keeps the licence file beside the data and carries the citation in the data card, so a reader who reuses the files has what the licence asks for.

The messages stay as published. No example prints message text, and no chapter quotes one, so the content of the messages does not reach a page. Everything the examples print from the data is a count or a rate.

**Working rule:** Keep the licence file beside the data, cite the paper in the data card, and print counts, never message text. If you reuse a dataset of real customer messages, read its card before you print anything from it, and cite the source where the data is documented.

## Dev, test and fixed samples {#dev-test-and-fixed-samples}

The [two files of the source split](#the-data-and-its-licence) are not enough by themselves. A router needs messages to tune on, messages to report on, and a small set that examples can run in seconds. Each one has to be fixed in advance, or a later result can be explained by a different sample rather than by a different model.

The dev split is carved from the training file, never from the test file. For each team, in the order of the categories file, the book draws about a tenth of that team's training messages with a fixed seed, and it commits the row numbers to `examples/data/banking77/samples.json`. The training messages that are not in dev are the ones the models train on. Because the draw is made team by team, each team's share of dev follows its share of the training file, and a team with few training messages keeps a small dev share instead of none.

The test split is the source's own held-out file. The book draws one stratified sample from it, 13 messages for each team, which gives 1001 messages in all. The sample is shuffled once, with the same generator as the dev draw, continuing after it, and the shuffled order is committed. Three prefixes of that order are named. The first 40 messages of the shuffled test sample are `test_40`, the first 200 are `test_200`, and the whole sample is `test_1001`. A prefix of a shuffled sample is a random draw, so `test_40` does not read the teams in order.

The counts come from the committed samples, and the book quotes only those. The first of them, count-the-splits, also checks that every dev row number is unique and falls inside the training file, so every dev message is a training row, and that `test_40` and `test_200` are the first 40 and first 200 of `test_1001`.

The first thing to see is how big each split is and how unevenly the teams are spread across them. Counting needs no model, so the reader can run it first. It reads the training file, the test file and the dev sample, and counts each split:

Example `count-the-splits` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.24.1), passing in Edition 2026.11.17:

```python
"""Count each BANKING77 split and its messages per team, and check the committed samples; no model runs.

The prose's point rests on the four "per label" lines for the test and training files.
"""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from collections import Counter  # noqa: E402

router_lib.setup_runtime()

train = router_lib.read_rows("train")
test = router_lib.read_rows("test")
dev = router_lib.read_sample("dev")  # dev row numbers index train.csv, never test.csv

assert len(set(dev)) == len(dev), "dev indices repeat"
assert max(dev) < len(train), "dev indices fall outside train.csv"

train_per_label = Counter(label for _, label in train)
test_per_label = Counter(label for _, label in test)

test_1001 = router_lib.read_sample("test_1001")  # committed order: prefixes are the first n of it
test_40 = router_lib.read_sample("test_40")
test_200 = router_lib.read_sample("test_200")
# test_40 and test_200 are prefixes of the shuffled order, not new draws
assert test_1001[:40] == test_40, "test_40 is not the first 40 of test_1001"
assert test_1001[:200] == test_200, "test_200 is not the first 200 of test_1001"
sample_per_label = Counter(test[i][1] for i in test_1001)  # rows are (text, label index); [1] is the label

train_counts = [train_per_label[i] for i in range(len(router_lib.LABELS))]  # one entry per team, so a team with no rows counts 0
test_counts = [test_per_label[i] for i in range(len(router_lib.LABELS))]
sample_counts = [sample_per_label[i] for i in range(len(router_lib.LABELS))]

print(f"train rows: {len(train)}")
print(f"dev rows: {len(dev)}")
print(f"test rows: {len(test)}")
print(f"labels: {len(router_lib.LABELS)}")
print(f"test per label min: {min(test_counts)}")
print(f"test per label max: {max(test_counts)}")
print(f"train per label min: {min(train_counts)}")
print(f"train per label max: {max(train_counts)}")
print(f"test_1001 per label min: {min(sample_counts)}")
print(f"test_1001 per label max: {max(sample_counts)}")
```

Output:

```text
train rows: 10003
dev rows: 1003
test rows: 3080
labels: 77
test per label min: 40
test per label max: 40
train per label min: 35
train per label max: 187
test_1001 per label min: 13
test_1001 per label max: 13
```

The test file is even, with the same count for every team, and the training file is not: its teams run from 35 messages to 187. That spread is why the dev draw is made team by team rather than as one random tenth of the file. The test file's own fewest and most, 40 and 40, are equal.

Figure 2.1 ranks the teams from the most training rows to the fewest, with the test file's count per team as the dashed line. The bars step down from left to right. 76 of the 77 teams have more training rows than the test file gives each team; the other is the smallest team. The median team has 127 training messages.

*Figure 2.1. Training rows per team, ranked, against the test file's count per team.*

![Training rows per team, ranked, stand above the test file's flat dashed count for every team but the smallest.](https://rollingedition.ai/books/small-open-models/2026.11.17/figures/train-rows-per-team.svg)

Example `figure-train-rows-per-team` (Python 3.12.15 · matplotlib 3.11.2 · torch 2.15.0+cpu · transformers 5.24.1), passing in Edition 2026.11.17:

```python
"""Rank the training file's rows per team and draw them against the test file's count per team; no model runs.

The prose's point rests on the median training count, and on how many teams have more training rows than the test file's count, which is the same for every team.
"""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from collections import Counter  # noqa: E402
from statistics import median  # noqa: E402

router_lib.setup_runtime()

from lib.figures import ACCENT, INK, new_figure, save  # noqa: E402

train = router_lib.read_rows("train")
test = router_lib.read_rows("test")
train_per_label = Counter(label for _, label in train)
test_per_label = Counter(label for _, label in test)
train_counts = sorted((train_per_label[i] for i in range(len(router_lib.LABELS))), reverse=True)
test_counts = [test_per_label[i] for i in range(len(router_lib.LABELS))]

assert min(train_counts) == 35 and max(train_counts) == 187, "train counts differ from count-the-splits"  # its lines
assert min(test_counts) == max(test_counts) == 40, "the test file is not even"

print(f"labels: {len(router_lib.LABELS)}")
print(f"train per label min: {min(train_counts)}")
print(f"train per label max: {max(train_counts)}")
print(f"train per label median: {median(train_counts)}")
print(f"test per label: {test_counts[0]}")
print(f"teams with more training rows than the test count: {sum(c > test_counts[0] for c in train_counts)}")
print("test file even across teams: yes")

fig, ax = new_figure()
ax.bar(range(1, len(train_counts) + 1), train_counts, color=ACCENT, label="training file: rows per team, ranked")
ax.axhline(test_counts[0], color=INK, linestyle="--", label="test file: rows per team, the same for every team")
ax.set_xlabel("team, ranked from most to fewest training rows")
ax.set_ylabel("messages per team")
ax.set_xlim(0, len(train_counts) + 1)
ax.set_ylim(0, max(train_counts) + 20)
ax.legend(loc="upper right")
save(fig, "train-rows-per-team")
```

Output:

```text
labels: 77
train per label min: 35
train per label max: 187
train per label median: 127
test per label: 40
teams with more training rows than the test count: 76
test file even across teams: yes
figure: figures/train-rows-per-team.svg
```

The stratified sample is even as well, at 13 to 13 messages a team.

The even test file is a property of the source, and the book relies on it. Equal counts per team mean that the test split does not reward a router for being good at the largest team. A router that does well on a sample with uneven counts can look better than it is, because most of its score comes from the teams with the most messages.

[Chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) chooses the hand-off threshold on dev, and it records the choice in the adapter's manifest. The rule behind that choice is to tune on dev, never on test. The prompt, the model and the recipe are fixed before any test result is read, and none is changed because of one, and the test results are read once, to report them, on the fixed samples above.

In production the same rule holds for the inbox. Keep a dev set drawn from messages the inbox already has, and keep a test set that nobody reads while the router is being tuned. A test set that is read during tuning still looks like a test set, but it stops measuring anything new, and a router that is later measured on it will look better than it will be on the traffic that follows.

**Working rule:** Draw dev from training rows only, team by team, with a fixed seed, and commit its row numbers. Draw each test sample once, commit its order, and read it only to report. Choose every threshold, prompt and setting on dev. When dev is too small to decide, draw more dev messages from the training file, never from the test file.

## Three measures, each with its denominator {#three-measures-each-with-its-denominator}

The [samples](#dev-test-and-fixed-samples) say which messages to score. The measures say what to count. A router that returns a team, a confidence and a hand-off flag can be scored three ways, and each way answers a different question for the bank that runs it.

Accuracy asks how often the router's team is the right one. The hand-off rate asks how often a person has to read a message. Accuracy on the messages not handed off asks how often the router is right on the messages it keeps. Each question has its own denominator, and the book keeps the three apart in every output line. Confidence is the probability the router gives its team, and the threshold is the value below which a message is handed off, as [chapter 1](route-a-message#hand-off-the-unsure-messages) defines them.

| Measure | Counts | Divided by |
| --- | --- | --- |
| Accuracy | Messages whose team equals the gold team | All messages in the sample |
| Hand-off rate | Messages whose confidence is below the threshold | All messages in the sample |
| Accuracy on messages not handed off | Correct messages among those not handed off | Messages not handed off |

As formulas, with N messages in the sample: accuracy = correct / N; hand-off rate = handed off / N; accuracy on messages not handed off = correct among kept / kept, where kept = N minus handed off.

Two rules make these measures comparable across candidates. The first is that a handed-off message counts in the accuracy denominator, as wrong when its team is wrong. Accuracy alone does not reward a hand-off, because a handed-off message scores as correct only when its team is right. Accuracy on the messages not handed off, taken alone, hides the cost of the hand-off, because it leaves out exactly the messages that went to people. The hand-off rate shows that cost. The three numbers have to be read together, and a router that is better on one of them alone has not yet shown it is better.

The second rule is about printing. Every rate is rounded to one decimal place as a percentage, and it is printed beside its count, so a reader can check a rate by dividing by hand. A rate with no count beside it cannot be checked, and a rate that is printed without its denominator can be quoted in a way that hides its sample.

When the denominator of the third measure is zero, the measure is not defined. That happens when every message is handed off, so no message is kept. The book prints "not defined" in that case, as the [baseline section](#the-baseline-from-recorded-answers) shows, and does not print zero, because zero would say that every kept message was wrong when there are no kept messages at all.

These measures score labels. The scripts in this chapter, and the measurements in [chapter 1](route-a-message#ask-a-model-for-one-team) and [chapter 4](prompt-and-constrain), return teams only to be scored, and they return nothing to a caller. A router that returns a team to a caller does so through the hand-off rule that [chapter 1](route-a-message) introduces, so that a message below the threshold goes to a person rather than to a team.

In production, the hand-off rate is the measure that changes first. The mix of messages changes with the seasons, with a product launch, or with a fault that floods the inbox with one kind of question. A router whose accuracy holds can still hand off far more messages than the dev split predicted, and the only way to see it is to print the rate with its count on the traffic the router actually receives.

**Working rule:** Print each of the three measures with its count and its denominator, and round every rate to one decimal place. Report accuracy on the messages not handed off beside the hand-off rate, never alone. When no message is kept, print "not defined" rather than zero.

## The baseline from recorded answers {#the-baseline-from-recorded-answers}

A measure means little until something has been scored against it. The baseline is the stand-in's score on `test_1001`, the sample that the final comparison in [chapter 10](when-a-small-model-is-the-wrong-choice) uses. Later chapters score candidates on its prefixes, `test_40` and `test_200`, which are the first 40 and first 200 messages of the same fixed sample. Each prefix is scored from the same recording, so the baseline on it is the same answers for the same messages.

The stand-in answered each of the messages in `test_1001` once. The answers are stored in a recording, `examples/data/recorded/standin-baseline/answers.jsonl`, and each answer names a team and gives its log-probability. The recording has a manifest beside it. The manifest names the script that made the recording, the model and its pinned revision, the hash of the prompt, the decoding settings and the seed, and the hash of the answers file. The code checks the answers file against that hash before it reads a line, so a changed file fails the run rather than changing a score.

The recording is read, not run. Every example that uses the baseline reads the same answers, so the baseline cannot change from one run to the next, even if the runtime that made the recording is later updated. The reason for recording, rather than calling a model in each example, is the same reason the pins exist. A recording fixes the answers to one model at one revision, one prompt and one sample, so a reader who runs the same example later sees the same numbers. The book never calls a hosted API, because a hosted model's answers are not fixed in the same way. The stand-in is an open model that anyone can run, and its recording is the only route to its answers that the book takes.

The baseline is also not a ceiling. It is the score a candidate has to beat on the same messages, and it says nothing about the hand-off trade-off by itself. A candidate that beats it on accuracy may still hand off more messages than the support staff can read, so the baseline is always read beside the three measures and never as a single number.

What does the placeholder threshold cost? Scored with the three measures on `test_1001`, the stand-in shows how many messages a threshold of 0.5 hands off, and how often it is right on the rest. Its confidence is the probability that llama-cpp-python returns for its constrained answer, which is exp of the recorded log-probability. That threshold is chapter 1's placeholder, so its hand-off rate is not the book's final one, and [chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) chooses the real threshold on dev. The example also applies a threshold above every confidence, which hands off every message.

Example `baseline-measures` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.24.1), passing in Edition 2026.11.17:

```python
"""Score the stand-in's recorded answers on test_1001 with the three measures, at chapter 1's placeholder threshold and at one above every confidence; no model runs. The point rests on the accuracy and hand-off lines, and the answers' hash is checked first.
"""

import hashlib, json, math, os

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

PLACEHOLDER = 0.5  # Chapter 5 chooses the real threshold on the dev split.
ABOVE_ALL = 1.01  # Confidence is at most 1.0, so this hands off every message.
RECORDED = router_lib.HERE / "data" / "recorded" / "standin-baseline"
manifest = json.loads((RECORDED / "manifest.json").read_text())
raw = (RECORDED / "answers.jsonl").read_bytes()
assert hashlib.sha256(raw).hexdigest() == manifest["output_sha256"]["answers.jsonl"]

answers = {row["index"]: row for row in map(json.loads, raw.decode().splitlines())}  # keyed by test.csv row, not by sample position
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_1001")
golds = [rows[i][1] for i in sample]  # in the sample's committed order, so position k of each list is one message
preds = [answers[i]["label"] for i in sample]
# Confidence is the probability llama-cpp-python returns for the constrained answer: exp of its log-probability.
confs = [math.exp(answers[i]["logprob"]) for i in sample]

n = len(sample)
first = router_lib.metrics(preds, golds, confs, PLACEHOLDER)  # one call returns the counts and rates of all three measures
high = router_lib.metrics(preds, golds, confs, ABOVE_ALL)
print(f"messages: {n}")
print(f"placeholder threshold: {PLACEHOLDER}")
print(f"accuracy: {first['correct']}/{n} ({first['accuracy']:.1%})")
print(f"handed off: {first['handed_off']}/{n} ({first['handoff_rate']:.1%})")
m = first["not_handed_off"]
print(f"accuracy on messages not handed off: {first['correct_not_handed_off']}/{m} ({first['accuracy_not_handed_off']:.1%})")
print(f"threshold above every confidence: {ABOVE_ALL}")
print(f"handed off at that threshold: {high['handed_off']}/{n} ({high['handoff_rate']:.1%})")
if high["accuracy_not_handed_off"] is None:  # None means no message is kept, so the measure has no denominator
    print("accuracy on messages not handed off at that threshold: not defined (0 messages not handed off)")
else:
    print(f"accuracy on messages not handed off at that threshold: {high['correct_not_handed_off']}/{high['not_handed_off']}")
```

Output:

```text
messages: 1001
placeholder threshold: 0.5
accuracy: 560/1001 (55.9%)
handed off: 30/1001 (3.0%)
accuracy on messages not handed off: 554/971 (57.1%)
threshold above every confidence: 1.01
handed off at that threshold: 1001/1001 (100.0%)
accuracy on messages not handed off at that threshold: not defined (0 messages not handed off)
```

At the placeholder threshold, the stand-in gets 560/1001 (55.9%) right and hands off 30/1001 (3.0%). On the messages it keeps, its accuracy is 554/971 (57.1%).

At a threshold above every confidence, the hand-off rate is 1001/1001 (100.0%), so the accuracy on messages not handed off is not defined (0 messages not handed off).

Figure 2.2 sweeps the threshold from 0 to 1 in steps of 0.01 and draws two curves against it, named in its legend: the share of messages handed off, dashed, and the accuracy on the messages not handed off, solid. The trade-off is what to see: at each printed threshold, a higher threshold hands off more messages, and the messages kept are more often right.

Raised from the placeholder 0.5 to 0.9, the threshold hands off 143/1001 (14.3%), and the stand-in is right on 522/858 (60.8%) of the messages it keeps.

*Figure 2.2. The hand-off threshold swept from 0 to 1, with the share handed off and the accuracy on the messages not handed off.*

![A higher hand-off threshold hands off more messages, and at the printed thresholds the messages kept are more often right; the share handed off climbs steeply at the right edge.](https://rollingedition.ai/books/small-open-models/2026.11.17/figures/baseline-handoff-tradeoff.svg)

Example `figure-baseline-handoff-tradeoff` (Python 3.12.15 · matplotlib 3.11.2 · torch 2.15.0+cpu · transformers 5.24.1), passing in Edition 2026.11.17:

```python
"""Sweep the hand-off threshold over the stand-in's recorded answers on test_1001 and draw both measures; no model runs.

The printed lines at 0.5 equal baseline-measures' lines, which the assert checks. The lines at 0.9, 0.99 and 1.0 give more points on the curves, and the counts of confidences at 1.0 and in the last step explain the curves' right edge.
"""

import os

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")

import torch  # noqa: E402

torch.set_num_threads(2)

import json, math, router_lib  # noqa: E402

router_lib.setup_runtime()

from lib.figures import ACCENT, INK, MUTED, new_figure, save  # noqa: E402

RECORDED = router_lib.HERE / "data" / "recorded" / "standin-baseline"
answers = {row["index"]: row for row in map(json.loads, (RECORDED / "answers.jsonl").read_text().splitlines())}
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_1001")
golds = [rows[i][1] for i in sample]
preds = [answers[i]["label"] for i in sample]
confs = [math.exp(answers[i]["logprob"]) for i in sample]  # the probability the stand-in gave its answer
at = lambda threshold: router_lib.metrics(preds, golds, confs, threshold)  # noqa: E731
thresholds = [k / 100 for k in range(101)]
sweep = [at(t) for t in thresholds]
handed = [100 * m["handoff_rate"] for m in sweep]
kept = [100 * m["accuracy_not_handed_off"] if m["accuracy_not_handed_off"] is not None else math.nan for m in sweep]

assert (at(0.5)["handed_off"], at(0.5)["correct_not_handed_off"], at(0.5)["not_handed_off"]) == (30, 554, 971), "not baseline-measures"
for t in (0.5, 0.9, 0.99, 1.0):
    m = at(t)
    print(f"handed off at {t}: {m['handed_off']}/{len(sample)} ({m['handoff_rate']:.1%})")
    print(f"accuracy on messages not handed off at {t}: {m['correct_not_handed_off']}/{m['not_handed_off']} ({m['accuracy_not_handed_off']:.1%})")
print("matches baseline-measures at 0.5: yes")
exactly_one = sum(c == 1.0 for c in confs)
last_step = at(1.0)["handed_off"] - at(0.99)["handed_off"]
assert at(1.0)["handed_off"] + exactly_one == len(sample), "a confidence of 1.0 is handed off at 1.0"  # strictly below: 1.0 is kept
print(f"messages with confidence at least 0.99 and below 1.0: {last_step}")
print(f"messages with confidence exactly 1.0: {exactly_one}")

fig, ax = new_figure()
ax.plot(thresholds, handed, color=INK, linestyle="--", label="handed off, share of all messages")
ax.plot(thresholds, kept, color=ACCENT, label="accuracy on messages not handed off")
ax.axvline(0.5, color=MUTED, linestyle=":", label="placeholder threshold 0.5")
ax.set_xlabel("hand-off threshold: a confidence below it goes to a person")
ax.set_ylabel("percent")
ax.set_xlim(0, 1)
ax.set_ylim(0, 100)
ax.legend(loc="upper right")
save(fig, "baseline-handoff-tradeoff")
```

Output:

```text
handed off at 0.5: 30/1001 (3.0%)
accuracy on messages not handed off at 0.5: 554/971 (57.1%)
handed off at 0.9: 143/1001 (14.3%)
accuracy on messages not handed off at 0.9: 522/858 (60.8%)
handed off at 0.99: 263/1001 (26.3%)
accuracy on messages not handed off at 0.99: 481/738 (65.2%)
handed off at 1.0: 515/1001 (51.4%)
accuracy on messages not handed off at 1.0: 351/486 (72.2%)
matches baseline-measures at 0.5: yes
messages with confidence at least 0.99 and below 1.0: 252
messages with confidence exactly 1.0: 486
figure: figures/baseline-handoff-tradeoff.svg
```

The curve turns steep at the right edge because of the last step, from 0.99 to 1.0. Those 252 messages are handed off at 1.0, since a message is handed off only when its confidence is strictly below the threshold. The 486 messages whose confidence is exactly 1.0 are kept even at 1.0, so at 1.0 the stand-in hands off 515/1001 (51.4%), and only a threshold above 1.0 hands them off too.

A reader's own hosted model is a different baseline. It will score differently on the same messages, and the book does not claim that the stand-in's numbers are the inbox's numbers. The reader's baseline is their model's recorded answers on `test_1001`, scored with the three measures in this chapter. The comparison that matters is between the reader's candidate and that baseline, on the same messages, with the same counts.

The [next section](#where-the-labels-collide) counts the stand-in's wrong answers and shows which teams they fall between. The wrong-answer count is the baseline's first number.

**Working rule:** Record the baseline once, on `test_1001`, the fixed sample that every candidate's prefixes come from. Store the model's pinned revision, the prompt's hash and the decoding settings in a manifest, and check the answers file against its hash before you read a line. Compare each candidate only with the baseline scored on the same messages, whether that is `test_40`, `test_200` or `test_1001`. When your own hosted model is the baseline, record its answers the same way, and say in the write-up that its scores differ from the stand-in's.

## Where the labels collide {#where-the-labels-collide}

The [baseline's counts](#the-baseline-from-recorded-answers) say how often the stand-in is wrong. They do not say which teams it mixes up, and the mix-ups are what the support staff can act on. A pair of teams that the router confuses might need a clearer team description, a rule for that pair, or more messages for one of the two teams in training. None of those is known from the total count, so the book reads the pairs from the recorded answers rather than assuming which teams are close.

Counting the wrong answers needs the recording itself, so the next example reads it, checks it against the manifest, checks that it holds exactly the messages of `test_1001`, and then counts the wrong answers and the three gold-to-answer pairs that occur most often. Ties break on each team's position in the categories file, so the same pairs print in the same order on every run.

Example `confusions-in-the-baseline` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.24.1), passing in Edition 2026.11.17:

```python
"""Count the stand-in's wrong answers, its three most frequent gold-to-answer pairs and the teams it never answers, on test_1001; no model runs. The point rests on the "pair" and "never answered" lines.
"""

import hashlib, json, os

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from collections import Counter  # noqa: E402

router_lib.setup_runtime()

RECORDED = router_lib.HERE / "data" / "recorded" / "standin-baseline"
manifest = json.loads((RECORDED / "manifest.json").read_text())
raw = (RECORDED / "answers.jsonl").read_bytes()
assert hashlib.sha256(raw).hexdigest() == manifest["output_sha256"]["answers.jsonl"]

records = [json.loads(line) for line in raw.decode().splitlines()]
sample = router_lib.read_sample("test_1001")
assert sorted(r["index"] for r in records) == sorted(sample), "recorded rows differ from test_1001"
assert all(router_lib.LABELS[r["label"]] == r["team"] for r in records), "label and team disagree"
test, LABELS = router_lib.read_rows("test"), router_lib.LABELS

gold_totals = Counter(test[i][1] for i in sample)
answered = Counter(r["label"] for r in records)
pairs = Counter((test[r["index"]][1], r["label"]) for r in records if r["label"] != test[r["index"]][1])  # (gold, answer); [1] is the gold label
wrong = sum(pairs.values())
# Ties break on the lower gold label index, then the lower answer index.
top = sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[:3]
never = sorted(team for k, team in enumerate(LABELS) if answered[k] == 0)  # sorted by name, so uppercase names print first

print(f"messages: {len(sample)}")
print(f"wrong answers: {wrong}")
print(f"wrong rate: {100 * wrong / len(sample):.1f}% ({wrong} of {len(sample)})")
for rank, ((gold, answer), count) in enumerate(top, start=1):
    print(f"pair {rank} count: {count}")
    print(f"pair {rank} gold: {LABELS[gold]}")
    print(f"pair {rank} answer: {LABELS[answer]}")
    print(f"pair {rank} of gold team: {count}/{gold_totals[gold]}")
print(f"teams never answered: {len(never)}")
for rank, team in enumerate(never, start=1):
    gold = LABELS.index(team)
    count, answer = max(((c, a) for (g, a), c in pairs.items() if g == gold), key=lambda ca: (ca[0], -ca[1]))  # most frequent wrong answer; ties go to the lower answer index
    print(f"never answered {rank} team: {team}")
    print(f"never answered {rank} messages: {gold_totals[gold]}")
    print(f"never answered {rank} most often as: {LABELS[answer]}")
    print(f"never answered {rank} most often count: {count}")
```

Output:

```text
messages: 1001
wrong answers: 441
wrong rate: 44.1% (441 of 1001)
pair 1 count: 13
pair 1 gold: Refund_not_showing_up
pair 1 answer: request_refund
pair 1 of gold team: 13/13
pair 2 count: 13
pair 2 gold: failed_transfer
pair 2 answer: transfer_not_received_by_recipient
pair 2 of gold team: 13/13
pair 3 count: 12
pair 3 gold: card_arrival
pair 3 answer: card_delivery_estimate
pair 3 of gold team: 12/13
teams never answered: 4
never answered 1 team: Refund_not_showing_up
never answered 1 messages: 13
never answered 1 most often as: request_refund
never answered 1 most often count: 13
never answered 2 team: card_arrival
never answered 2 messages: 13
never answered 2 most often as: card_delivery_estimate
never answered 2 most often count: 12
never answered 3 team: failed_transfer
never answered 3 messages: 13
never answered 3 most often as: transfer_not_received_by_recipient
never answered 3 most often count: 13
never answered 4 team: order_physical_card
never answered 4 messages: 13
never answered 4 most often as: get_physical_card
never answered 4 most often count: 10
```

The stand-in is wrong on 44.1% (441 of 1001). Whatever the threshold, the error is one minus accuracy, so that wrong rate and the accuracy in [the baseline section](#the-baseline-from-recorded-answers) add up to 100%.

Each of the three most frequent pairs takes all or nearly all of its gold team's sample messages. The first pair takes 13/13, the second 13/13, and the third 12/13, so the first two take every message of their gold team and the third all but one. The team names suggest a reason for each pair: the first concerns a refund, the second a transfer, and the third a card's arrival and its delivery estimate. That is a reading of the names. The chapter does not read the messages, and no example prints them, so the pairs are a reason to look, not a finding about what the messages say.

The stand-in never names 4 of the 77 teams, so every message whose gold team is one of those is wrong. For card_arrival, one of those teams, the most common wrong answer is card_delivery_estimate, which takes 12 of its messages.

For order_physical_card, another of them, the most common wrong answer is get_physical_card, which takes 10 of its messages. The recording does not show why these teams are never given, so the list is a reason to look.

The pairs describe the stand-in on this sample, not the teams or the inbox. A reader's own model will have its own pairs, and a reader should count them from their own recorded answers. When the question is how to fix a pair, the fix has to be chosen and checked on dev, as [the dev and test section](#dev-test-and-fixed-samples) requires. A change that is chosen by reading the pairs on `test_1001` has been tuned on the test split, and its result on that split cannot be reported as a measure of the router.

When hand-offs or complaints rise for one team in production, repeat this count first. Count the pairs again on the inbox's own recorded answers, print each pair with its count, and compare the list with the one from the baseline. A change in the list says where the router's behaviour has moved, even when the overall rate has not.

The chapter's decisions, in short:

- Dev is drawn team by team from the training file, with a fixed seed, and its row numbers are committed.
- The test samples are fixed in order, and they are read only to report.
- Each measure is printed with its count and denominator, and "not defined" replaces a zero denominator.
- The stand-in's recorded answers on `test_1001` are the baseline, read from a manifest-checked file.

The baseline's three numbers, read together, are the score a candidate has to beat on the same messages. [Chapter 3](choose-a-base-model#measure-what-one-message-costs) counts the router prompt's tokens on `test_40` before it chooses a base model. [Chapter 5](fine-tune-with-lora) chooses the hand-off threshold on dev, with the rule stated there. [Chapter 10](when-a-small-model-is-the-wrong-choice) compares the router with the baseline on the same `test_1001` sample.

**Working rule:** Count the wrong answers and the most frequent pairs for every candidate, on the same sample, and print each pair with its count. Read the pairs as a list of where to look. Print the three most frequent pairs rather than only the first, because one pair invites over-reading, and a list shows whether the errors cluster or scatter. Check any fix on the dev split before the test split is read again.
