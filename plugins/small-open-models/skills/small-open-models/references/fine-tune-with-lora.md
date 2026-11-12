---
title: "Small Open Models"
chapter: "Fine-tune a classification head with LoRA"
chapter_id: fine-tune-with-lora
book: small-open-models
edition: 2026.11.1
verified: 2026-11-12
edition_code: 8J4E-MZEZ
canonical: https://rollingedition.com/small-open-models/fine-tune-with-lora
license: CC BY 4.0
attribution: "“Fine-tune a classification head with LoRA,” chapter 5 of Small Open Models, Edition 2026.11.1, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/fine-tune-with-lora. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Fine-tune a classification head with LoRA

By the end of this chapter, you can train a classification head on the labelled messages with LoRA, count the parameters that training changes, choose a hand-off threshold on the dev split by a stated rule, and record that threshold beside the results it produced.

The inbox sends each message to one of 77 teams. The messages come from BANKING77, a public dataset whose labels this book calls teams ([chapter 2](measure-the-routing-task#the-data-and-its-licence)). [Chapter 3](choose-a-base-model) chose SmolLM2-135M-Instruct as the base model, and this chapter fine-tunes that model and no other: the 360M stays a comparison, as chapter 3 said. [Chapter 1](route-a-message) gave the router a placeholder threshold of 0.5 and said so in every output. The stand-in is the Qwen3-4B-Instruct-2507 model whose recorded answers chapter 1 reads in place of a hosted model. [Chapter 2](measure-the-routing-task#dev-test-and-fixed-samples) fixed the dev and test samples the router is measured on. This chapter replaces the stand-in's answer with a head that returns a team and a confidence in one forward pass, then chooses the threshold on dev, before any test result is reported.

This chapter does not compare the adapter with the 360M, and it does not distil or quantize anything. Chapters 6, 7 and 9 distil, quantize and version the adapter.

## A head that scores the teams {#a-head-that-scores-the-teams}

The stand-in writes its answer as text, and a grammar limits that text to the 77 team names while it decodes ([chapter 4](prompt-and-constrain#a-token-trie-allows-only-team-names)). A classification head works differently. It keeps the language model's layers and adds one output layer with 77 outputs, one for each team. For each message, the model produces 77 scores. Softmax turns the scores into 77 probabilities that sum to one. The router returns the team with the highest probability, and the confidence is that probability.

The answer is an index into the 77 teams, so it is always one of them. [Chapter 4](prompt-and-constrain) reaches the same guarantee for a prompted model by constraining its text. This head never writes text, so it has nothing to constrain.

A message costs one forward pass: one run of the network from input to scores, with no loop that writes tokens one at a time. The team and the confidence come from that same pass. This matters for the hand-off. The flag that sends a message to a person is computed from the same probabilities as the team it protects, so the two cannot drift apart between two calls.

The confidence here has a narrower meaning than the stand-in's. In chapter 1, a confidence was the probability the stand-in's recorded answer had, which is not a softmax over teams. In this chapter, it is the softmax probability of the chosen team. The two numbers are both called confidence, and both are compared with a threshold, but they are not the same quantity, so a threshold chosen for one is not a threshold for the other.

When two teams tie, `router_lib`'s `classify` function takes the lower label index. That follows from torch's `argmax`, whose documentation says: "If there are multiple maximal values then the indices of the first maximal value are returned." ([torch 2.15.0+cpu documentation](https://docs.pytorch.org/docs/2.15/generated/torch.argmax.html)). A fixed rule for ties keeps the output reproducible.

**Working rule:** Read the team and the confidence from one forward pass, and take the team as the output with the highest probability. Keep both in one function, so that a hand-off decision and the team it protects come from the same answer. Do not set a head's confidence beside a stand-in's as though they measured the same thing.

## Adapters train a small part of the model {#adapters-train-a-small-part-of-the-model}

Full fine-tuning changes every weight in the base model. LoRA takes a different route. It freezes the base weights and trains small matrices added beside some of its layers. The paper that introduced the method, [Hu et al. (2021)](https://arxiv.org/abs/2106.09685), puts it this way in its abstract: LoRA "freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture". The trained matrices are the adapter. The base model stays as it was, and the adapter is the part this book stores, loads and versions.

The rank, `r`, is the inner size of each added matrix, and it is kept small. Peft scales the added update by `lora_alpha` divided by `r` ([peft 0.21.2, `src/peft/tuners/lora/layer.py`](https://raw.githubusercontent.com/huggingface/peft/v0.21.2/src/peft/tuners/lora/layer.py), line 281: `self.scaling[adapter_name] = lora_alpha / r`), so `lora_alpha` sets how strongly the update counts. This book uses a rank of 8, with `lora_alpha` set to 16. The added matrices go in the projection layers named `q_proj` and `v_proj` in each attention block. The abstract does not name those layers, so this choice is the book's, not something the paper prescribes. We recommend it as a starting point, and the recorded adapter below is the test of that recommendation on this task. Other targets are a choice to measure, not a fact about the method.

The head is trained as well. Peft does that for this book's setup: a model built as a sequence classifier lists its `classifier` and `score` layers in `modules_to_save` ([peft 0.21.2, `src/peft/peft_model.py`](https://raw.githubusercontent.com/huggingface/peft/v0.21.2/src/peft/peft_model.py), line 1830: `classifier_module_names = ["classifier", "score"]`), so training moves the 77-output layer and the adapter together. A reader who counts only the adapter's matrices gets a smaller number than the one the code trains, and the difference is the head. The example in the next section prints the split: `460800` in the adapter and `44352` in the head, which together make the total of `505152`.

The adapter's manifest records the base model's revision, so a reader can check that revision against `models.toml` before scoring.

**Working rule:** Set the rank, the scaling and the target layers in one configuration, and count the trainable parameters from the loaded model before training starts. Print the total with the head in it. A count that leaves out the head reports part of what training changes, and it will not match what the optimizer updates.

## Thirty steps are not enough {#thirty-steps-are-not-enough}

Before the book uses a recording, it shows what a short run does with the same recipe. This example trains for 30 steps, at batch size 8 and seed 0, on training rows that are not held back for dev. Then it scores `test_200`, the first 200 entries of the shuffled test sample that [chapter 2](measure-the-routing-task#dev-test-and-fixed-samples) drew. It is a failure, and the book shows it as one.

Example `lora-thirty-steps` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Train LoRA on the classifier for 30 steps, live, then score test_200. Thirty steps are not enough.
The recipe is the recorded run's (batch 8, seed 0, the same shuffled order); the recording runs 1,125 steps."""

import math

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
REPO = "HuggingFaceTB/SmolLM2-135M-Instruct"
STEPS, BATCH, SEED = 30, 8, 0

train, order = router_lib.training_rows(SEED)
tok, model = router_lib.new_classifier(REPO)
lora, head = router_lib.parameter_split(model)
print(f"trainable parameters: {lora + head}")
print(f"LoRA parameters: {lora}")
print(f"head parameters: {head}")

losses = router_lib.train_steps(model, tok, train, order, STEPS, BATCH)
print(f"training steps: {STEPS}")
print(f"batch size: {BATCH}")
print(f"seed: {SEED}")
for step in (10, 20, 30):
    print(f"loss at step {step}: {losses[step - 1]:.2f}")
print(f"loss of a uniform guess over 77 teams: {math.log(77):.2f}")

result = router_lib.score_test_sample(model, tok, "test_200", 0.5)
n = result["n"]
print(f"messages on test_200: {n}")
print(f"accuracy on test_200: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off at placeholder 0.50: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:
    print("accuracy on messages not handed off: not defined (0 messages not handed off)")
else:
    m = result["not_handed_off"]
    print(f"accuracy on messages not handed off: {result['correct_not_handed_off']}/{m} ({result['accuracy_not_handed_off']:.1%})")
```

Output:

```text
trainable parameters: 505152
LoRA parameters: 460800
head parameters: 44352
training steps: 30
batch size: 8
seed: 0
loss at step 10: 4.13
loss at step 20: 6.12
loss at step 30: 4.38
loss of a uniform guess over 77 teams: 4.34
messages on test_200: 200
accuracy on test_200: 5/200 (2.5%)
handed off at placeholder 0.50: 200/200 (100.0%)
accuracy on messages not handed off: not defined (0 messages not handed off)
```

The example prints the trainable count, 505152, and the loss of a uniform guess over the 77 teams, 4.34, for comparison. Then it prints the loss at steps 10, 20 and 30: 4.13, 6.12 and 4.38. Its accuracy on `test_200` is 5/200 (2.5%). At the placeholder threshold of 0.5, every message is handed off: 200/200 (100.0%). Because no message is kept, the accuracy on messages not handed off is not defined, and the example says so. A router that hands off every message gives no message to a team, so the labels it predicts never reach a caller.

The loss does not fall steadily across the three printed steps. Step 20 is higher than step 10, and step 30 is lower than step 20 but higher than step 10. Three points from 30 steps are not a learning curve. The loss at step 30 is close to the uniform guess, so at that point the head is still close to chance. The recording used in the section on the recorded adapter runs the same recipe for far more steps, and its accuracy is the one this book reports.

The example reads `test_200` only to report the failure. It chooses nothing: the recipe is fixed before the run, and the threshold is chosen later on dev. A reader who wants to see whether training works should look at the loss and at the dev measures, not at the test sample, which is the rule chapter 2 set for every sample. A reader who tunes a recipe against the test sample has no clean number left to report, and the sample stops being a test.

**Working rule:** Run a short training to check that the pipeline works from start to finish, and do not route with its head. Judge a fine-tuned head on the dev split, with the measures set in chapter 2, after a run long enough to reach them. Do not read a loss curve of a few points as evidence that the head learns.

## Train on the training rows, never on the test rows {#train-on-the-training-rows-never-on-the-test-rows}

The training file holds labelled messages, and chapter 2 drew the dev split from it, team by team, with a fixed seed. Training uses the training rows that are not held back for dev. The test file is never read during training. The example in [thirty steps are not enough](#thirty-steps-are-not-enough) builds its training order from the rows left after dev is removed, shuffled with seed 0, so the order is the same on every run.

The dev split carries the decisions. Its size is printed by the threshold example: 1003 messages. No training step reads them. They come from `train.csv`, the training file, and they are used only to choose the threshold and to check the calibration in the last section.

The recipe is written into the adapter's manifest, so a reader can see what the adapter was trained on: the base model's pinned revision, the data commit, the batch size, the seed and the number of steps. A reader who wants to repeat the training needs those values, and a reader who wants to know whether a result came from a clean split needs the data commit.

The rule matters most when a result looks good. A training run that reads the test sample has seen the messages it is then scored on, so its test accuracy measures nothing about new messages. Keeping dev and test apart is what makes the test accuracy in the next section a fair report.

**Working rule:** Train only on training rows that are outside dev. Record the seed, the batch size, the step count and the data commit in the manifest. When dev is too small to decide a threshold, draw more messages from the training file, never from the test file, as chapter 2 says.

## Use the recorded adapter {#use-the-recorded-adapter}

The working router uses `banking77-lora-v1`: the adapter from the full recorded run, version 1, written by `recordings/lora_full.py`. That script trained the adapter once, on the recipe in [the section on training rows](#train-on-the-training-rows-never-on-the-test-rows), and wrote its files and a manifest. The manifest holds the base model's revision, the data commit, the threshold, the recipe's hash and the hashes of the output files. The example below loads the adapter offline and scores `test_200` with the threshold from its manifest. It trains nothing.

Take the adapter as it was recorded. A reader who wants a different recipe records a new run, which is named `v2`; the book does not edit the adapter by hand. Keeping the recording fixed is what lets a reader check the numbers in this chapter against the files they downloaded.

Example `lora-recorded-adapter` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Load the recorded adapter banking77-lora-v1 and score test_200 at its recorded hand-off threshold.
Nothing is trained here: the adapter and its threshold come from the recording's manifest."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
manifest = json.loads((RECORDED / "manifest.json").read_text())
threshold = manifest["handoff_threshold"]

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
preds, confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])

result = router_lib.metrics(preds, golds, confs, threshold)
n = result["n"]
print(f"adapter: {manifest['adapter']}")
print(f"handoff threshold from manifest: {threshold:.2f}")
print(f"messages on test_200: {n}")
print(f"accuracy on test_200: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:
    print("accuracy on messages not handed off: not defined (0 messages not handed off)")
else:
    m = result["not_handed_off"]
    print(
        f"accuracy on messages not handed off: {result['correct_not_handed_off']}/{m} "
        f"({result['accuracy_not_handed_off']:.1%})"
    )
```

Output:

```text
adapter: banking77-lora-v1
handoff threshold from manifest: 0.63
messages on test_200: 200
accuracy on test_200: 172/200 (86.0%)
handed off: 33/200 (16.5%)
accuracy on messages not handed off: 156/167 (93.4%)
```

The example prints the adapter's name, its threshold from the manifest, and three measures on `test_200`. Accuracy is 172/200 (86.0%), and a handed-off message counts as wrong when its team is wrong. The hand-off count is 33/200 (16.5%). The accuracy on messages not handed off is 156/167 (93.4%). Each rate is printed with its count and its denominator, as chapter 2 requires. Set beside chapter 4's counts on the same 200 messages, the recorded adapter gets 172/200 (86.0%), against 9/200 (4.5%) for the prompted 135M model. The 30-step run above gets 5/200 (2.5%), below the prompted model too.

The threshold is not chosen on this sample. It came from the manifest, which [the section on choosing the threshold](#choose-the-threshold-on-dev) explains. The example prints it so the reader can see which value each result used: 0.63.

The recorded adapter is the router's model, and the stand-in is the baseline. The two were measured with different thresholds, so their hand-off counts are not the same kind of result. Compare them on the same messages, with each threshold named beside its count. The example below does that for `test_200`, using the stand-in's recorded answers for the same messages.

Example `compare-with-standin` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Compare the stand-in's recorded answers with the recorded adapter's live predictions on test_200.
Both models score the same 200 messages. The stand-in's threshold is chapter 1's placeholder."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import math  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
STANDIN_THRESHOLD = 0.5  # Placeholder from chapter 1. Chapter 5 chooses the threshold on dev.
ADAPTER = router_lib.HERE / "data" / "recorded" / "lora-full"

with open(router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl") as f:
    answers = {row["index"]: row for row in map(json.loads, f)}
threshold = json.loads((ADAPTER / "manifest.json").read_text())["handoff_threshold"]

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
standin_preds = [answers[i]["label"] for i in sample]
standin_confs = [math.exp(answers[i]["logprob"]) for i in sample]

tokenizer, model = router_lib.load_classifier(ADAPTER / "adapter")
adapter_preds, adapter_confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])

standin = router_lib.metrics(standin_preds, golds, standin_confs, STANDIN_THRESHOLD)
adapter = router_lib.metrics(adapter_preds, golds, adapter_confs, threshold)
n = standin["n"]
s_right = [p == g for p, g in zip(standin_preds, golds)]
a_right = [p == g for p, g in zip(adapter_preds, golds)]

print(f"messages on test_200: {n}")
print(f"stand-in correct: {standin['correct']}/{n} ({standin['accuracy']:.1%})")
print(f"adapter banking77-lora-v1 correct: {adapter['correct']}/{n} ({adapter['accuracy']:.1%})")
print(f"stand-in placeholder threshold: {STANDIN_THRESHOLD:.2f}")
print(f"stand-in handed off: {standin['handed_off']}/{n} ({standin['handoff_rate']:.1%})")
print(f"adapter threshold from manifest: {threshold:.2f}")
print(f"adapter handed off: {adapter['handed_off']}/{n} ({adapter['handoff_rate']:.1%})")
print(f"right for the adapter, wrong for the stand-in: {sum(a and not s for a, s in zip(a_right, s_right))}/{n}")
print(f"right for the stand-in, wrong for the adapter: {sum(s and not a for a, s in zip(a_right, s_right))}/{n}")
```

Output:

```text
messages on test_200: 200
stand-in correct: 109/200 (54.5%)
adapter banking77-lora-v1 correct: 172/200 (86.0%)
stand-in placeholder threshold: 0.50
stand-in handed off: 9/200 (4.5%)
adapter threshold from manifest: 0.63
adapter handed off: 33/200 (16.5%)
right for the adapter, wrong for the stand-in: 69/200
right for the stand-in, wrong for the adapter: 6/200
```

The example reads the stand-in's recorded answers for the 200 messages and runs the adapter live on the same 200. It prints both models' correct counts out of 200, both hand-off counts at their thresholds, and the count of messages each model gets right that the other gets wrong. The stand-in's confidence is the probability its recorded answer had, from the recording's log-probability. The stand-in's threshold is chapter 1's placeholder, 0.50, and the example prints it as a placeholder. Its hand-off count says what that placeholder does to the stand-in, and nothing about the stand-in's own threshold, which was never chosen on dev.

The output reads: 109/200 (54.5%) correct for the stand-in and 172/200 (86.0%) for the adapter. The stand-in hands off 9/200 (4.5%) at its placeholder. The adapter hands off 33/200 (16.5%) at 0.63. The count for messages the adapter gets right and the stand-in gets wrong is 69/200, and the count for the reverse is 6/200. Two accuracies can be equal while the two models miss different messages, and these two counts show where that happens.

The comparison is one sample of 200 messages. [Chapter 1](route-a-message#score-the-router-on-a-fixed-sample) said that its small sample can show that a router fails, but cannot tell two routers apart with confidence. Chapter 1's sample was smaller. The discordant counts here, 69/200 against 6/200, are stronger evidence than that sample could give, though they are still one sample. A reader who wants a firmer claim should run the same comparison on the full `test_1001` sample, which the stand-in's recording also covers.

**Working rule:** Compare two models only on the same messages, and name the threshold each one used beside its count. When one threshold is a placeholder, say so beside its count, and do not read its hand-off count as the model's own result.

## Choose the threshold on dev {#choose-the-threshold-on-dev}

The threshold is the cut that sends a message to a person. Chapter 2 set its measures, and chapter 1 left it as a placeholder. The book's rule chooses it on the dev split only: the lowest confidence threshold, on a grid of 0.01, at which accuracy on messages not handed off is at least the target. The rule is written in the manifest with its value, so a reader can see the rule as well as the number it produced. The test sample is never read to choose the threshold.

Example `choose-threshold-on-dev` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Choose the hand-off threshold on the dev split: the lowest one on a 0.01 grid whose messages not handed off
are at least 0.90 accurate. Then show the trade-off at three thresholds. Dev only; test_200 is never used here."""

import json

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
manifest_threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
TARGET = 0.90

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
rows = router_lib.read_rows("train")
dev = router_lib.read_sample("dev")
golds = [rows[i][1] for i in dev]
preds, confs = router_lib.classify_by_length(model, tokenizer, [rows[i][0] for i in dev])
n = len(dev)
chosen = router_lib.choose_threshold(preds, golds, confs, TARGET)

print(f"dev messages: {n}")
print(f"target accuracy on messages not handed off: {TARGET:.2f}")
print(f"chosen threshold: {chosen:.2f}")
print(f"threshold in manifest: {manifest_threshold:.2f}")
print(f"chosen threshold matches manifest: {'yes' if chosen == manifest_threshold else 'no'}")
for t in sorted({0.50, chosen, 0.90}):
    r = router_lib.metrics(preds, golds, confs, t)
    print(f"threshold {t:.2f} handed off: {r['handed_off']}/{n} ({r['handoff_rate']:.1%})")
    print(f"threshold {t:.2f} accuracy on messages not handed off: {r['correct_not_handed_off']}/{r['not_handed_off']} ({r['accuracy_not_handed_off']:.1%})")
```

Output:

```text
dev messages: 1003
target accuracy on messages not handed off: 0.90
chosen threshold: 0.63
threshold in manifest: 0.63
chosen threshold matches manifest: yes
threshold 0.50 handed off: 80/1003 (8.0%)
threshold 0.50 accuracy on messages not handed off: 811/923 (87.9%)
threshold 0.63 handed off: 148/1003 (14.8%)
threshold 0.63 accuracy on messages not handed off: 770/855 (90.1%)
threshold 0.90 handed off: 352/1003 (35.1%)
threshold 0.90 accuracy on messages not handed off: 620/651 (95.2%)
```

The example scores the dev split with the recorded adapter, applies the rule, and prints the chosen value. The dev messages are 1003, the target accuracy on messages not handed off is 0.90, and the chosen threshold is 0.63. The example then checks that the manifest holds the same value, and it prints yes. A mismatch would mean the manifest and the rule disagree, and the example would say so.

The example prints three thresholds, so a reader can see the trade-off. The rule picks the lowest threshold that meets the target, and raising the threshold never hands off fewer messages. The table sets the three rows side by side, with each count and rate.

| Threshold | Handed off, on dev | Accuracy on messages not handed off, on dev |
| --- | --- | --- |
| 0.50 | 80/1003 (8.0%) | 811/923 (87.9%) |
| 0.63, chosen | 148/1003 (14.8%) | 770/855 (90.1%) |
| 0.90 | 352/1003 (35.1%) | 620/651 (95.2%) |

At 0.50, the router keeps more messages, but its kept messages are less accurate, and the target is missed. At 0.90, the kept messages are the most accurate of the three, but the most dev messages go to a person. The chosen value is the lowest of the three thresholds that meets the target, so it hands off more messages than 0.50 and fewer than 0.90. The table shows what it costs in hand-offs and what it buys in accuracy. The rule does not decide whether that trade is worth making. The book's target is 90% accuracy on kept messages. A bank that runs its own router sets its target from this table, since the table is the trade that target buys.

What goes wrong in production is a change in the messages, not in the model. Suppose a product problem sends many messages about one team in one week. The threshold was chosen on the dev mix, so the hand-off rate can move while the adapter stays exactly the same. A rise in hand-offs with no change to the adapter is the sign to check the mix of messages first. Moving the threshold by eye until the hand-off rate looks right gives up the property the rule was chosen for: at least the target accuracy on the dev messages the router keeps.

The confidence is not a probability that the team is right. [Guo et al. (2017)](https://arxiv.org/abs/1706.04599) report that their networks are "poorly calibrated", meaning their confidence does not match how often they are right. This book checks its own adapter on dev. The example below groups the dev messages into five confidence bands. For each band it prints the count, the accuracy and the mean confidence, the two quantities Guo et al. compare when they measure calibration.

Example `calibration-bands-on-dev` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Group the dev messages by the recorded adapter's confidence into five bands. For each band it prints the count,
the accuracy and the mean confidence, the two quantities Guo et al. (2017) compare for calibration. Dev only."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
BANDS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
rows = router_lib.read_rows("train")
dev = router_lib.read_sample("dev")
golds = [rows[i][1] for i in dev]
preds, confs = router_lib.classify_by_length(model, tokenizer, [rows[i][0] for i in dev])

print(f"dev messages: {len(dev)}")
counted = 0
for lo, hi in BANDS:
    last = hi == 1.0
    members = [i for i, c in enumerate(confs) if lo <= c < hi or (last and c == 1.0)]
    counted += len(members)
    name = f"band {lo:.1f}-{hi:.1f}"
    print(f"{name} messages: {len(members)}")
    if members:
        correct = sum(preds[i] == golds[i] for i in members)
        print(f"{name} correct: {correct}/{len(members)} ({correct / len(members):.1%})")
        print(f"{name} mean confidence: {sum(confs[i] for i in members) / len(members):.1%}")
    else:
        print(f"{name} correct: not defined (0 messages)")
        print(f"{name} mean confidence: not defined (0 messages)")
print(f"messages in bands: {counted}")
```

Output:

```text
dev messages: 1003
band 0.0-0.2 messages: 1
band 0.0-0.2 correct: 1/1 (100.0%)
band 0.0-0.2 mean confidence: 19.9%
band 0.2-0.4 messages: 41
band 0.2-0.4 correct: 10/41 (24.4%)
band 0.2-0.4 mean confidence: 32.9%
band 0.4-0.6 messages: 92
band 0.4-0.6 correct: 49/92 (53.3%)
band 0.4-0.6 mean confidence: 51.0%
band 0.6-0.8 messages: 123
band 0.6-0.8 correct: 84/123 (68.3%)
band 0.6-0.8 mean confidence: 70.6%
band 0.8-1.0 messages: 746
band 0.8-1.0 correct: 693/746 (92.9%)
band 0.8-1.0 mean confidence: 96.4%
messages in bands: 1003
```

The output reads: 1003 dev messages in all. The top band, from 0.8 to 1.0, holds 746 messages, 693/746 (92.9%) correct, and its mean confidence is 96.4%. The band from 0.6 to 0.8 holds 123 messages, 84/123 (68.3%) correct, with a mean confidence of 70.6%. The band from 0.4 to 0.6 holds 92 messages, 49/92 (53.3%) correct, with a mean confidence of 51.0%. The band from 0.2 to 0.4 holds 41 messages, 10/41 (24.4%) correct, with a mean confidence of 32.9%. The bottom band, from 0.0 to 0.2, holds 1 message, and its accuracy says nothing about low confidence.

Four of the five bands have an accuracy inside their range, and the bottom band is the one exception, with its single message. From the second band up, accuracy rises. In the two middle bands the accuracy and the mean confidence sit close together. In the top band the mean confidence is above the accuracy, and the top band holds most of the dev messages. In the band from 0.2 to 0.4 the mean confidence is well above the accuracy. So on dev the confidence orders the messages usefully, but in the top band it runs above the accuracy.

The bands cannot show more. The bottom band has one message, and the band from 0.2 to 0.4 has 41. All of these numbers come from the one dev sample that also chose the threshold, so they do not show how calibrated the adapter will be on new messages.

The router the rule chooses is an empirical cut on dev, recorded with its rule and data. A reader takes its hand-off rate and accuracy on kept messages as the router's result, and re-checks the dev rule when the mix of messages moves.

**Working rule:** Choose the threshold on the dev split by the stated rule, and write its value and the rule into the adapter's manifest. Report the hand-off rate beside accuracy on the messages kept, each with its count, and show at least one setting either side of the chosen value. Check calibration on dev before you trust the confidence as a cut, and when the mix of messages changes, choose the threshold again on a fresh dev draw from the training file, never on the test sample.
