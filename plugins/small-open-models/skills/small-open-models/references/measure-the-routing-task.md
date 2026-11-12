---
title: "Small Open Models"
chapter: "Measure the routing task before you choose a model"
chapter_id: measure-the-routing-task
book: small-open-models
edition: 2026.11.1
verified: 2026-11-12
edition_code: 8J4E-MZEZ
canonical: https://rollingedition.com/small-open-models/measure-the-routing-task
license: CC BY 4.0
attribution: "“Measure the routing task before you choose a model,” chapter 2 of Small Open Models, Edition 2026.11.1, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/measure-the-routing-task. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Measure the routing task before you choose a model

By the end of this chapter, you can say what each of the book's samples is for, compute the three measures the router is scored on with their denominators, and read a baseline that was recorded once and is reused for every comparison.

A bank's support inbox, which this book calls the inbox, sends each message to one of 77 teams. A hosted model picks the team. The book's router is a small open model that the bank would run itself. The question is whether it can match the hosted model on the messages it keeps, and say so when it is not sure of a message. Before any model is compared, the comparison needs fixed data, fixed samples and fixed measures. Otherwise two numbers that look alike may come from different messages, or be divided by different counts.

This book doesn't call a hosted model, so it uses a stand-in. The stand-in is a larger open model, Qwen3-4B-Instruct-2507, in the 4-bit Q4_K_M GGUF conversion that a third party published, at its pinned revision, with its answers limited to the 77 team names. It answers every test message once, in a recording, and the examples read those answers offline, so anyone can reproduce them. [Chapter 1](route-a-message#ask-a-model-for-one-team) introduced the stand-in. A reader's own hosted model will score differently, and [chapter 1](route-a-message#ask-a-model-for-one-team) shows how to record that model's answers the same way.

## The data and its licence {#the-data-and-its-licence}

The router is trained and measured on BANKING77, a public dataset of customer service queries in the banking domain (Casanueva et al., 2020). Each message carries one of 77 labels. The dataset calls its labels intents. This book calls them teams, because that is what the inbox routes to, and the word "team" is used in every chapter from here on.

The paper that introduces the dataset is Casanueva et al. (2020), "Efficient Intent Detection with Dual Sentence Encoders", in the Proceedings of the 2nd Workshop on Natural Language Processing for Conversational AI, pages 38–45 (Anthology ID 2020.nlp4convai-1.5; arXiv 2003.04807). Its abstract describes such a dataset as "a new challenging single-domain intent detection dataset comprising 13,083 annotated examples over 77 intents." The paper's text names the dataset: "a new and challenging intent detection dataset in the banking domain, dubbed BANKING 77". Its section 3 gives the count: "The new BANKING 77 dataset comprises 13,083 customer service queries labeled with 77 intents." The data card that ships beside the files gives the commit the files come from. The two files together hold the same 13,083 messages, which the next section counts.

The data card also states the facts the book relies on. It says that the files are a copy of the source's own train and test split, and that the split is not drawn again. It says that every team appears in both files: "Every label appears in both `train.csv` and `test.csv`." These two statements matter for the rest of the chapter. A router trained on the training file and scored on the test file is scored on the source's own held-out messages, not on a split that the book chose.

The licence is CC BY 4.0. The LICENSE file that sits beside the data begins "Attribution 4.0 International". Under that licence the data may be shared and adapted, provided the source is credited. The book keeps the licence file beside the data and carries the citation in the data card, so a reader who reuses the files has what the licence asks for.

The messages stay as published. No example prints message text, and no chapter quotes a message, so the content of the messages does not reach a page. The examples print counts and rates, and nothing else from the data.

**Working rule:** Keep the licence file beside the data, cite the paper in the data card, and print counts, never message text. If you reuse a dataset of real customer messages, read its card before you print anything from it, and cite the source where the data is documented.

## Dev, test and fixed samples {#dev-test-and-fixed-samples}

The [two files of the source split](#the-data-and-its-licence) are not enough by themselves. A router needs messages to tune on, messages to report on, and a small set that examples can run in seconds. Each one has to be fixed in advance, or a later result can be explained by a different sample rather than by a different model.

The dev split is carved from the training file, never from the test file. For each team, in the order of the categories file, the book draws about a tenth of that team's training messages with a fixed seed, and it commits the row numbers to `examples/data/banking77/samples.json`. The training messages that are not in dev are the ones the models train on. Because the draw is made team by team, each team's share of dev follows its share of the training file, and a team with few training messages keeps a small dev share instead of none.

The test split is the source's own held-out file. The book draws one stratified sample from it, 13 messages for each team, which gives 1001 messages in all. The sample is shuffled once, with the same generator as the dev draw, continuing after it, and the shuffled order is committed. Three prefixes of that order are named. The first 40 messages are `test_40`, the first 200 are `test_200`, and the whole sample is `test_1001`. A prefix of a shuffled sample is a random draw, so a short example does not read the teams in order, and `test_40` is not a sample of the first few teams in the file.

The examples print their own counts from the committed samples, and the book quotes only those. The example also checks that every dev row number is unique and falls inside the training file, so every dev message is a training row. It checks that `test_40` and `test_200` are the first 40 and first 200 of `test_1001`.

The next example runs no model. It reads the training file, the test file and the dev sample, and it counts each split.

Example `count-the-splits` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Count the rows, labels and messages per label in each BANKING77 split. No model runs.

The dev rows come from train.csv only. Test rows are never used for tuning.
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
dev = router_lib.read_sample("dev")

assert len(set(dev)) == len(dev), "dev indices repeat"
assert max(dev) < len(train), "dev indices fall outside train.csv"

train_per_label = Counter(label for _, label in train)
test_per_label = Counter(label for _, label in test)

test_1001 = router_lib.read_sample("test_1001")
test_40 = router_lib.read_sample("test_40")
test_200 = router_lib.read_sample("test_200")
assert test_1001[:40] == test_40, "test_40 is not the first 40 of test_1001"
assert test_1001[:200] == test_200, "test_200 is not the first 200 of test_1001"
sample_per_label = Counter(test[i][1] for i in test_1001)

train_counts = [train_per_label[i] for i in range(len(router_lib.LABELS))]
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

The output has one labelled line per count. The training file holds 10003 messages, and the dev sample holds 1003 of them. The test file holds 3080 messages across 77 teams. The test file is even: the fewest messages for a team is 40 and the most is 40. The training file is not even: its fewest is 35 and its most is 187, which is why the dev draw is made team by team rather than as one random tenth of the file. The last two lines give the fewest and the most for the test sample, which are 13 and 13, so the sample also holds the same number for every team.

The even test file is a property of the source, and the book relies on it. Equal counts per team mean that the test split does not reward a router for being good at the largest team. A router that does well on a sample with uneven counts can look better than it is, because most of its score comes from the teams with the most messages. The stratified test sample keeps that effect out of the measures.

[Chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) chooses the hand-off threshold on dev, and it records the choice in the adapter's manifest. The threshold is chosen on dev. The prompt, the model and the recipe are fixed before any test result is read, and none is changed because of one. The test split is never used to tune, and the test results are read once, to report them, on the fixed samples above.

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

When the denominator of the third measure is zero, the measure is not defined. That happens when every message is handed off, so no message is kept. The book prints "not defined" in that case, as the example in [the baseline section](#the-baseline-from-recorded-answers) shows, and does not print zero, because zero would say that every kept message was wrong when there are no kept messages at all.

These measures score labels. The examples in this chapter, and the measurements in [chapter 1](route-a-message#ask-a-model-for-one-team) and [chapter 4](prompt-and-constrain), return teams only to be scored, and they return nothing to a caller. A router that returns a team to a caller does so through the hand-off rule that [chapter 1](route-a-message) introduces, so that a message below the threshold goes to a person rather than to a team.

In production, the hand-off rate is the measure that changes first. The mix of messages changes with the seasons, with a product launch, or with a fault that floods the inbox with one kind of question. A router whose accuracy holds can still hand off far more messages than the dev split predicted, and the only way to see it is to print the rate with its count on the traffic the router actually receives.

**Working rule:** Print each of the three measures with its count and its denominator, and round every rate to one decimal place. Report accuracy on the messages not handed off beside the hand-off rate, never alone. When no message is kept, print "not defined" rather than zero.

## The baseline from recorded answers {#the-baseline-from-recorded-answers}

A measure means little until something has been scored against it. The baseline is the stand-in's score on `test_1001`, the sample that the final comparison in [chapter 10](when-a-small-model-is-the-wrong-choice) uses. Later chapters score candidates on its prefixes, `test_40` and `test_200`, which are the first 40 and first 200 messages of the same committed order. Each prefix is scored from the same recording, so the baseline on it is the same answers for the same messages. Each candidate is compared with the same messages, counted in the same way, and reported beside the baseline.

The stand-in answered each of the messages in `test_1001` once. The answers are stored in a recording, `examples/data/recorded/standin-baseline/answers.jsonl`, and each answer names a team and gives its log-probability. The recording has a manifest beside it. The manifest names the script that made the recording, the model and its pinned revision, the hash of the prompt, the decoding settings and the seed, and the hash of the answers file. The examples check the answers file against that hash before they read a line, so a changed file fails the run rather than changing a score.

The recording is read, not run. Every example that uses the baseline reads the same answers, so the baseline cannot change from one run to the next, even if the runtime that made the recording is later updated. The reason for recording, rather than calling a model in each example, is the same reason the pins exist. A recording fixes the answers to one model at one revision, so a reader who runs the same example later sees the same numbers. The book never calls a hosted API, because a hosted model's answers are not fixed in the same way. The stand-in is an open model that anyone can run, and its recording is the only route to its answers that the book takes.

The baseline is also not a ceiling. It is the score a candidate has to beat on the same messages, and it says nothing about the hand-off trade-off by itself. A candidate that beats it on accuracy may still hand off more messages than the support staff can read, so the baseline is always read beside the three measures and never as a single number.

The example below scores the stand-in on `test_1001` with the three measures. For the stand-in, confidence is the probability that llama-cpp-python returns for its constrained answer, which is exp of the recorded log-probability. It uses chapter 1's placeholder threshold of 0.5, so its hand-off rate is not the book's final one, and [chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) chooses the real threshold on dev. It also applies a threshold above every confidence, which hands off every message.

Example `baseline-measures` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Score the stand-in's recorded answers on test_1001 with the three measures. No model runs.

The thresholds are chapter 1's placeholder and one above every confidence. The answers' hash is checked first.
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

answers = {row["index"]: row for row in map(json.loads, raw.decode().splitlines())}
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_1001")
golds = [rows[i][1] for i in sample]
preds = [answers[i]["label"] for i in sample]
# Confidence is the probability llama-cpp-python returns for the constrained answer: exp of its log-probability.
confs = [math.exp(answers[i]["logprob"]) for i in sample]

n = len(sample)
first = router_lib.metrics(preds, golds, confs, PLACEHOLDER)
high = router_lib.metrics(preds, golds, confs, ABOVE_ALL)
print(f"messages: {n}")
print(f"placeholder threshold: {PLACEHOLDER}")
print(f"accuracy: {first['correct']}/{n} ({first['accuracy']:.1%})")
print(f"handed off: {first['handed_off']}/{n} ({first['handoff_rate']:.1%})")
m = first["not_handed_off"]
print(f"accuracy on messages not handed off: {first['correct_not_handed_off']}/{m} ({first['accuracy_not_handed_off']:.1%})")
print(f"threshold above every confidence: {ABOVE_ALL}")
print(f"handed off at that threshold: {high['handed_off']}/{n} ({high['handoff_rate']:.1%})")
if high["accuracy_not_handed_off"] is None:
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

The example prints 1001 messages. At the placeholder threshold the accuracy is 560/1001 (55.9%), the hand-off rate is 30/1001 (3.0%), and the accuracy on messages not handed off is 554/971 (57.1%). At a threshold above every confidence, the hand-off rate is 1001/1001 (100.0%), so the accuracy on messages not handed off is not defined (0 messages not handed off).

A reader's own hosted model is a different baseline. It will score differently on the same messages, and the book does not claim that the stand-in's numbers are the inbox's numbers. The reader's own baseline is their model's recorded answers on `test_1001`, scored with the three measures in this chapter. The comparison that matters is between the reader's candidate and that baseline, on the same messages, with the same counts.

The [next section](#where-the-labels-collide) counts the stand-in's wrong answers and shows which teams they fall between. The wrong-answer count is the baseline's first number, and it is the one every later comparison starts from.

**Working rule:** Record the baseline once, on `test_1001`, the committed sample that every candidate's prefixes come from. Store the model's pinned revision, the prompt's hash and the decoding settings in a manifest, and check the answers file against its hash before you read a line. Compare each candidate only with the baseline scored on the same messages, whether that is `test_40`, `test_200` or `test_1001`. When your own hosted model is the baseline, record its answers the same way, and say in the write-up that its scores differ from the stand-in's.

## Where the labels collide {#where-the-labels-collide}

The [baseline's counts](#the-baseline-from-recorded-answers) say how often the stand-in is wrong. They do not say which teams it mixes up, and the mix-ups are what the support staff can act on. A pair of teams that the router confuses might need a clearer team description, a rule for that pair, or more messages for one of the two teams in training. None of those is known from the total count, so the book reads the pairs from the recorded answers rather than assuming which teams are close.

The next example reads the recording, checks it against the manifest, and checks that the recorded messages are exactly the `test_1001` sample. It then counts the wrong answers and the three gold-to-answer pairs that occur most often. Ties break on each team's position in the categories file, so the same pairs are printed in the same order on every run.

Example `confusions-in-the-baseline` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Count the stand-in's wrong answers, confusions and never-answered teams on test_1001. No model runs."""

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
pairs = Counter((test[r["index"]][1], r["label"]) for r in records if r["label"] != test[r["index"]][1])
wrong = sum(pairs.values())
# Ties break on the lower gold label index, then the lower answer index.
top = sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[:3]
never = sorted(team for k, team in enumerate(LABELS) if answered[k] == 0)

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
    count, answer = max(((c, a) for (g, a), c in pairs.items() if g == gold), key=lambda ca: (ca[0], -ca[1]))
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

The example prints 1001 messages, of which 441 were answered with the wrong team. The wrong rate is 44.1% (441 of 1001). With no threshold applied, the error is one minus accuracy, so the wrong rate here and the accuracy in [the baseline section](#the-baseline-from-recorded-answers) add up to 100%.

The three most frequent pairs follow. The first pair is 13 messages whose gold team is Refund_not_showing_up, which the stand-in answered with request_refund: 13/13 of that team's sample messages. The second pair is 13 messages whose gold team is failed_transfer, answered with transfer_not_received_by_recipient: 13/13. The third pair is 12 messages whose gold team is card_arrival, answered with card_delivery_estimate: 12/13.

The first two pairs take all of their gold team's messages in the sample, and the third takes all but one. The team names suggest a reason for each pair: the first concerns a refund, the second a transfer, and the third a card's arrival and its delivery estimate. That is a reading of the names. The chapter does not read the messages, and no example prints them, so the pairs are a reason to look, not a finding about what the messages say.

The example also lists the teams the stand-in never answers. Across the 1,001 messages, its answers never name 4 of the 77 teams, so every message whose gold team is one of those is wrong. The example prints each team's sample count, and for each the team its wrong answers go to most often. For card_arrival that is card_delivery_estimate, which takes 12 of its messages, and for order_physical_card it is get_physical_card, which takes 10 of its messages. The recording does not show why these teams are never given, so the list is a reason to look here too.

The pairs describe the stand-in on this sample. They do not describe the teams, and they do not describe the inbox. A reader's own model will have its own pairs, and a reader should count them from their own recorded answers. When the question is how to fix a pair, the fix has to be chosen and checked on dev. A change that is chosen by reading the pairs on `test_1001` has been tuned on the test split, and its result on that split cannot be reported as a measure of the router.

In production, the same count is the first thing to repeat when hand-offs or complaints rise for one team. Count the pairs again on the inbox's own recorded answers, print each pair with its count, and compare the list with the one from the baseline. A change in the list says where the router's behaviour has moved, even when the overall rate has not.

The chapter's decisions, in short:

- Dev is drawn team by team from the training file, with a fixed seed, and its row numbers are committed.
- The test samples are fixed in order, and they are read only to report.
- Each measure is printed with its count and denominator, and "not defined" replaces a zero denominator.
- The stand-in's recorded answers on `test_1001` are the baseline, read from a manifest-checked file.

[Chapter 3](choose-a-base-model#measure-what-one-message-costs) counts the router prompt's tokens on `test_40` before it chooses a base model. [Chapter 5](fine-tune-with-lora) chooses the hand-off threshold on dev, with the rule stated there. [Chapter 10](when-a-small-model-is-the-wrong-choice) compares the router with the baseline on the same `test_1001` sample.

**Working rule:** Count the wrong answers and the most frequent pairs for every candidate, on the same sample, and print each pair with its count. Read the pairs as a list of where to look. Print the three most frequent pairs rather than only the first, because one pair invites over-reading, and a list shows whether the errors cluster or scatter. Check any fix on the dev split before the test split is read again.
