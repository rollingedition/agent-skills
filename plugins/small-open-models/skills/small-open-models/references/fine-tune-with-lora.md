---
title: "Small Open Models"
chapter: "Fine-tune a classification head with LoRA"
chapter_id: fine-tune-with-lora
book: small-open-models
edition: 2026.11.4
verified: 2026-11-17
edition_code: PTNR-ZYMP
canonical: https://rollingedition.com/small-open-models/fine-tune-with-lora
license: CC BY 4.0
attribution: "“Fine-tune a classification head with LoRA,” chapter 5 of Small Open Models, Edition 2026.11.4, examples passed Nov 17, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/fine-tune-with-lora. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Fine-tune a classification head with LoRA

By the end of this chapter, you can train a classification head on the labelled messages with LoRA, count the parameters that training changes, choose a hand-off threshold on the dev split by a stated rule, and record that threshold beside the results it produced.

The router so far runs the [stand-in](route-a-message#ask-a-model-for-one-team), which writes its answer as text in place of a hosted model, on a placeholder threshold, 0.5, that no one chose and every output labels as one. The answer has to be a team, and the threshold has to be chosen, so this chapter replaces that answer with a head that returns a team and a confidence in one forward pass, and it chooses the threshold on dev before any test result is reported. Training needs labelled messages for the router's teams, and these come from [BANKING77](measure-the-routing-task#the-data-and-its-licence), a public dataset. [Chapter 3](choose-a-base-model) chose SmolLM2-135M-Instruct as the base model, and this chapter fine-tunes that model and no other: the 360M stays a comparison, as chapter 3 said. The router is measured on the [samples](measure-the-routing-task#dev-test-and-fixed-samples) that chapter 2 fixed.

This chapter does not compare the adapter with the 360M, and it does not distill or quantize anything. Chapters 6, 7 and 9 distill, quantize and version the adapter.

## A head that scores the teams {#a-head-that-scores-the-teams}

The stand-in writes its answer as text, and a grammar limits that text to the 77 team names while it decodes ([chapter 4](prompt-and-constrain#a-token-trie-allows-only-team-names)). A classification head works differently. It keeps the language model's layers and adds one output layer with 77 outputs, one for each team. For each message, the model produces 77 scores. Softmax turns the scores into 77 probabilities that sum to one. The router returns the team with the highest probability, and the confidence is that probability.

The answer is an index into the 77 teams, so it is always one of them. [Chapter 4](prompt-and-constrain) reaches the same guarantee for a prompted model by constraining its text. This head never writes text, so it has nothing to constrain.

A message costs one forward pass: one run of the network from input to scores, with no loop that writes tokens one at a time. The team and the confidence come from that same pass. This matters for the hand-off. The flag that sends a message to a person is computed from the same probabilities as the team it protects, so the two cannot drift apart between two calls. A separate scoring call would need its own check that the two agree.

The confidence here has a narrower meaning than the stand-in's. In chapter 1, a confidence was the probability the stand-in's recorded answer had, which is not a softmax over teams. In this chapter, it is the softmax probability of the chosen team. The two numbers are both called confidence, and both are compared with a threshold, but they are not the same quantity, so a threshold chosen for one is not a threshold for the other.

When two teams tie, `router_lib`'s `classify` function takes the lower label index. That follows from torch's `argmax`, whose documentation says: "If there are multiple maximal values then the indices of the first maximal value are returned." ([torch 2.15.0+cpu documentation](https://docs.pytorch.org/docs/2.15/generated/torch.argmax.html)). A fixed rule for ties keeps the output reproducible.

**Working rule:** Read the team and the confidence from one forward pass, and take the team as the output with the highest probability. Keep both in one function, so that a hand-off decision and the team it protects come from the same answer. Do not set a head's confidence beside a stand-in's as though they measured the same thing.

## Adapters train a small part of the model {#adapters-train-a-small-part-of-the-model}

Full fine-tuning changes every weight in the base model. LoRA takes a different route. The paper that introduced the method, [Hu et al. (2021)](https://arxiv.org/abs/2106.09685), says it freezes the pre-trained weights and injects trainable low-rank matrices into the layers of the Transformer, and the trained matrices are the adapter. The base model stays as it was, and the adapter is the part this book stores, loads and versions.

The rank, `r`, is the inner size of each added matrix, and it is kept small. Peft scales the added update by `lora_alpha` divided by `r` ([peft 0.21.3, `src/peft/tuners/lora/layer.py`](https://raw.githubusercontent.com/huggingface/peft/v0.21.2/src/peft/tuners/lora/layer.py), line 281: `self.scaling[adapter_name] = lora_alpha / r`), so `lora_alpha` sets how strongly the update counts. This book uses a rank of 8, with `lora_alpha` set to 16. The added matrices go in the projection layers named `q_proj` and `v_proj` in each attention block. The abstract does not name those layers, so this choice is the book's, not something the paper prescribes. We recommend it as a starting point, and the recorded adapter below is the test of that recommendation on this task. Other targets are a choice to measure, not a fact about the method.

The head is trained as well. Peft does that for this book's setup: a model built as a sequence classifier lists its `classifier` and `score` layers in `modules_to_save` ([peft 0.21.3, `src/peft/peft_model.py`](https://raw.githubusercontent.com/huggingface/peft/v0.21.2/src/peft/peft_model.py), line 1830: `classifier_module_names = ["classifier", "score"]`), so training moves the 77-output layer and the adapter together. Count only the adapter's matrices and you get a smaller number than the one the code trains, and the difference is the head. The next section's run counts the split from the loaded model: `460800` in the adapter and `44352` in the head, which together make `505152`.

The adapter's manifest records the base model's revision, so a reader can check that revision against `models.toml` before scoring.

**Working rule:** Set the rank, the scaling and the target layers in one configuration, and count the trainable parameters from the loaded model before training starts. Print the total with the head in it. A count that leaves out the head reports part of what training changes, and it will not match what the optimizer updates.

## Thirty steps are not enough {#thirty-steps-are-not-enough}

Before the book uses a recording, it shows what a short run does with the same recipe. The run below takes 30 steps, at batch size 8 and seed 0, on the training rows outside dev, and then scores `test_200`, the first 200 entries of the [fixed sample](measure-the-routing-task#dev-test-and-fixed-samples) that chapter 2 drew. It is a failure, and the book shows it as one. The short run checks that the pipeline works from start to finish, and that is its only job here.

Example `lora-thirty-steps` (Python 3.12.15 · peft 0.21.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.4:

```python
"""Train for 30 steps on the recorded recipe, then score test_200 at the placeholder threshold of 0.5.
Read the three step losses against the uniform-guess loss, then the hand-off line at that threshold. The recording runs 1,125 steps."""

import math

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
REPO = "HuggingFaceTB/SmolLM2-135M-Instruct"
STEPS, BATCH, SEED = 30, 8, 0

train, order = router_lib.training_rows(SEED)  # the seed sets the shuffled order of the training rows, the one the recording used
tok, model = router_lib.new_classifier(REPO)  # SmolLM2 with a 77-way head, LoRA rank 8, lora_alpha 16, on q_proj and v_proj
lora, head = router_lib.parameter_split(model)  # LoRA tensors have "lora_" in their names; every other trainable tensor is the head
print(f"trainable parameters: {lora + head}")
print(f"LoRA parameters: {lora}")
print(f"head parameters: {head}")

losses = router_lib.train_steps(model, tok, train, order, STEPS, BATCH)  # AdamW at learning rate 1e-3, router_lib's default
print(f"training steps: {STEPS}")
print(f"batch size: {BATCH}")
print(f"seed: {SEED}")
for step in (10, 20, 30):
    print(f"loss at step {step}: {losses[step - 1]:.2f}")  # train_steps returns one loss per step, from step 1 at index 0, so step 10 is index 9
print(f"loss of a uniform guess over 77 teams: {math.log(77):.2f}")

result = router_lib.score_test_sample(model, tok, "test_200", 0.5)  # 0.5 is chapter 1's placeholder; this run chooses no threshold
n = result["n"]
print(f"messages on test_200: {n}")
print(f"accuracy on test_200: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off at placeholder 0.50: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:  # None when no message is kept, so there is no accuracy to print
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

Thirty steps are not enough to route with. The head this run trains gets 5/200 (2.5%) right on `test_200`, and at the placeholder threshold it hands every message to a person: 200/200 (100.0%). A router that hands off every message gives no message to a team, so the labels it predicts never reach a caller. Because no message is kept, the accuracy on messages not handed off is not defined, as the output says.

The loss does not fall steadily across the three printed steps: it is 4.13 at step 10, 6.12 at step 20, and 4.38 at step 30. Step 20 is higher than step 10, and step 30 is lower than step 20 but higher than step 10. Three points from 30 steps are not a learning curve. The loss at step 30 sits close to the uniform guess of 4.34, so at that point the head is still close to chance. A uniform guess gives each team the same probability, one in 77, so its loss is the natural log of 77. The recording used in the section on the recorded adapter runs the same recipe for far more steps, and its accuracy is the one this book reports.

Scoring `test_200` here only reports the failure, and nothing is chosen from it: the recipe is fixed before the run, and the threshold is chosen later on dev. To see whether training works, read the loss and the dev measures, not the test sample, which is the rule chapter 2 set for every sample. Tuning a recipe against the test sample leaves no clean number to report, and the sample stops being a test.

**Working rule:** Run a short training to check that the pipeline works from start to finish, and do not route with its head. Judge a fine-tuned head on the dev split, with the measures set in chapter 2, after a run long enough to reach them. Do not read a loss curve of a few points as evidence that the head learns.

## Train on the training rows, never on the test rows {#train-on-the-training-rows-never-on-the-test-rows}

The training file holds labelled messages, and chapter 2 drew the dev split from it, team by team, with a fixed seed. Training uses the training rows that are not held back for dev. The test file is never read during training. The training order in [thirty steps are not enough](#thirty-steps-are-not-enough) is built from the rows left after dev is removed, shuffled with seed 0, so it is the same on every run.

The dev split carries the decisions. It holds 1003 messages from `train.csv`, the training file. No training step reads them, and they are used only to choose the threshold and to check the calibration in the last section.

The recipe is written into the adapter's manifest, so a reader can see what the adapter was trained on: the base model's pinned revision, the data commit, the batch size, the seed and the number of steps. Repeating the training takes those values, and checking that a result came from a clean split takes the data commit.

The rule matters most when a result looks good. A training run that reads the test sample has seen the messages it is then scored on, so its test accuracy measures nothing about new messages. Keeping dev and test apart is what makes the test accuracy in the next section a fair report.

**Working rule:** Train only on training rows that are outside dev. Record the seed, the batch size, the step count and the data commit in the manifest. When dev is too small to decide a threshold, draw more messages from the training file, never from the test file, as chapter 2 says.

## Use the recorded adapter {#use-the-recorded-adapter}

The working router uses `banking77-lora-v1`: the adapter from the full recorded run, version 1, written by `recordings/lora_full.py`. That script trained the adapter once, on the recipe in [the section on training rows](#train-on-the-training-rows-never-on-the-test-rows), and wrote its files and a manifest. The manifest holds the base model's revision, the data commit, the threshold, the recipe's hash and the hashes of the output files. Offline, the adapter loads and scores `test_200` at the threshold from its manifest, and nothing is trained.

Take the adapter as it was recorded. A different recipe becomes a new run, named `v2`; the book does not edit the adapter by hand. Keeping the recording fixed is what lets a reader check the numbers in this chapter against the files they downloaded.

Example `lora-recorded-adapter` (Python 3.12.15 · peft 0.21.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.4:

```python
"""Load the recorded adapter banking77-lora-v1 and score test_200 at the threshold in its manifest; no training runs here.
Read the accuracy line with the two hand-off lines printed under it."""

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
threshold = manifest["handoff_threshold"]  # the threshold the recording chose on dev; this script chooses none

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")  # the base model comes from the adapter's config, at its revision in models.toml
test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
preds, confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])  # a tie goes to the lower label index

result = router_lib.metrics(preds, golds, confs, threshold)  # a message is handed off when its confidence is below the threshold
n = result["n"]
print(f"adapter: {manifest['adapter']}")
print(f"handoff threshold from manifest: {threshold:.2f}")
print(f"messages on test_200: {n}")
print(f"accuracy on test_200: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:  # None when no message is kept, so there is no accuracy to print
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

The recorded adapter is right on 172/200 (86.0%) of the messages, against 9/200 (4.5%) for the prompted 135M model that [chapter 4](prompt-and-constrain) measured on the same 200. The 30-step run, at 5/200 (2.5%), falls below the prompted model. A handed-off message counts as wrong when its team is wrong. The output beside this paragraph gives the hand-off count and the accuracy on messages not handed off, each with its count and denominator, as chapter 2 requires.

The threshold is not chosen on this sample. It came from the manifest, which [the section on choosing the threshold](#choose-the-threshold-on-dev) explains. It is the threshold the recorded adapter's hand-off counts on `test_200` use: 0.63. Reading it from the manifest keeps the choice on dev, where the rule made it.

The recorded adapter is the router's model, and the stand-in is the baseline. The two were measured with different thresholds, so their hand-off counts are not the same kind of result. Compare them on the same messages, with each threshold named beside its count. The comparison below does that for `test_200`, reading the stand-in's recorded answers for the same messages.

Example `compare-with-standin` (Python 3.12.15 · peft 0.21.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.4:

```python
"""Set the stand-in's recorded answers beside the recorded adapter's live predictions on the same 200 test messages.
The last two lines count where the models disagree."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import math  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
STANDIN_THRESHOLD = 0.5  # chapter 1's placeholder; the stand-in's own threshold is never chosen on dev
ADAPTER = router_lib.HERE / "data" / "recorded" / "lora-full"

with open(router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl") as f:
    answers = {row["index"]: row for row in map(json.loads, f)}  # keyed by the test-row index that read_sample returns
threshold = json.loads((ADAPTER / "manifest.json").read_text())["handoff_threshold"]

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
standin_preds = [answers[i]["label"] for i in sample]
standin_confs = [math.exp(answers[i]["logprob"]) for i in sample]  # the recording stores log-probabilities; exp turns one back into the probability its answer had

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

Matching the two models message by message shows which messages each one misses. The stand-in's answers come from its recording, and the adapter runs live on the same 200 messages. The stand-in's confidence is the probability its recorded answer had, from the recording's log-probability. The stand-in's threshold is chapter 1's placeholder, 0.50, and the output labels it as one. Its hand-off count, 9/200 (4.5%), says what that placeholder does to the stand-in, and nothing about the stand-in's own threshold, which was never chosen on dev. The adapter hands off 33/200 (16.5%) at 0.63.

The adapter is right on 172/200 (86.0%) of these messages, the stand-in on 109/200 (54.5%). Where the two disagree, the adapter alone is right on 69/200, and the stand-in alone on 6/200. Two accuracies can be equal while the two models miss different messages, and the disagreement counts show where that happens.

The comparison is one sample of 200 messages. [Chapter 1](route-a-message#score-the-router-on-a-fixed-sample) said that its small sample can show that a router fails, but cannot tell two routers apart with confidence. Chapter 1's sample was smaller. The discordant counts here, 69/200 against 6/200, are stronger evidence than that sample could give. For a firmer claim, run the same comparison on the full `test_1001` sample, which the stand-in's recording also covers.

**Working rule:** Compare two models only on the same messages, and name the threshold each one used beside its count. When one threshold is a placeholder, say so beside its count, and do not read its hand-off count as the model's own result.

## Choose the threshold on dev {#choose-the-threshold-on-dev}

The threshold is the cut that sends a message to a person. Chapter 2 set its measures, and chapter 1 left it as a placeholder. The book's rule chooses it on the dev split only: the lowest confidence threshold, on a grid of 0.01, at which accuracy on messages not handed off is at least the target of 0.90. The rule is written in the manifest with its value, so a reader can see the rule as well as the number it produced. The test sample plays no part, [as chapter 2 requires](measure-the-routing-task#dev-test-and-fixed-samples).

Example `choose-threshold-on-dev` (Python 3.12.15 · peft 0.21.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.4:

```python
"""Find the hand-off threshold on dev by the manifest's rule, then check it against the manifest's value.
Read the chosen threshold beside the three threshold lines. test_200 is not read here."""

import json

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
manifest_threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
TARGET = 0.90  # the book's target accuracy on messages not handed off: a choice the book makes, not one the data sets

tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
rows = router_lib.read_rows("train")
dev = router_lib.read_sample("dev")
golds = [rows[i][1] for i in dev]
preds, confs = router_lib.classify_by_length(model, tokenizer, [rows[i][0] for i in dev])  # batches by length to pad less; results come back in dev order
n = len(dev)
chosen = router_lib.choose_threshold(preds, golds, confs, TARGET)  # the rule lives in router_lib: the lowest 0.01 grid value that meets TARGET; None if no value meets it, and the prints below would then fail

print(f"dev messages: {n}")
print(f"target accuracy on messages not handed off: {TARGET:.2f}")
print(f"chosen threshold: {chosen:.2f}")
print(f"threshold in manifest: {manifest_threshold:.2f}")
print(f"chosen threshold matches manifest: {'yes' if chosen == manifest_threshold else 'no'}")  # both come from the same 0.01 grid, so equal means the same threshold
for t in sorted({0.50, chosen, 0.90}):  # 0.50 is chapter 1's placeholder; a set drops the chosen value if it is one of the other two
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

Scoring dev with the recorded adapter and applying the rule gives a threshold of 0.63. The check against the manifest's value prints yes, and a mismatch would mean the manifest and the rule disagree.

Three thresholds show the trade-off, and the table below sets them side by side, with each count and rate. Raising the threshold never hands off fewer messages, and the rule picks the lowest value that meets the target. Each row is the same adapter on the same dev messages, so only the threshold changes.

| Threshold | Handed off, on dev | Accuracy on messages not handed off, on dev |
| --- | --- | --- |
| 0.50 | 80/1003 (8.0%) | 811/923 (87.9%) |
| 0.63, chosen | 148/1003 (14.8%) | 770/855 (90.1%) |
| 0.90 | 352/1003 (35.1%) | 620/651 (95.2%) |

At 0.50, the router keeps more messages, but its kept messages are less accurate, and the target is missed. At 0.90, the kept messages are the most accurate of the three, but the most dev messages go to a person. The chosen value is the lowest of the three thresholds that meets the target, so it hands off more messages than 0.50 and fewer than 0.90. The table shows what it costs in hand-offs and what it buys in accuracy. Where to set the target is a business choice the rule cannot make. The book uses 0.90 accuracy on kept messages, and a bank running its own router would read its own target off this trade.

The adapter stays the same in production, but the messages it sees do not. Suppose a product problem sends many messages about one team in one week. The threshold was chosen on the dev mix of messages, so the hand-off rate can move on its own while the adapter stays exactly the same. A rise in hand-offs with no change to the adapter is the sign to check the mix of messages first. Moving the threshold by eye until the hand-off rate looks right gives up the property the rule was chosen for: at least the target accuracy on the dev messages the router keeps.

The confidence is not a probability that the team is right. [Guo et al. (2017)](https://arxiv.org/abs/1706.04599) report that their networks are "poorly calibrated", meaning their confidence does not match how often they are right. This book checks its own adapter on dev. The dev messages fall into five confidence bands, and each band gets a count, an accuracy and a mean confidence, the two quantities Guo et al. compare when they measure calibration. Grouping dev by confidence shows whether a 0.9 means nine in ten.

Example `calibration-bands-on-dev` (Python 3.12.15 · peft 0.21.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.4:

```python
"""Group the dev messages into five bands by the adapter's confidence, and print each band's count, accuracy and mean confidence.
Read the top band's mean confidence against its accuracy. Only dev is read."""

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
preds, confs = router_lib.classify_by_length(model, tokenizer, [rows[i][0] for i in dev])  # results come back in dev order, so index i matches golds[i]

print(f"dev messages: {len(dev)}")
counted = 0
for lo, hi in BANDS:
    last = hi == 1.0
    members = [i for i, c in enumerate(confs) if lo <= c < hi or (last and c == 1.0)]  # lower edges are in, upper edges out; the top band also takes 1.0, so each message is counted once
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

Most dev messages fall in the top band, from 0.8 to 1.0, which holds 746 of them. The bottom band, from 0.0 to 0.2, holds 1, too few for its accuracy to say anything about low confidence.

On dev the confidence orders the messages usefully, but at the top it runs above the accuracy: the top band's mean confidence is 96.4%, against an accuracy of 693/746 (92.9%). Four of the five bands have an accuracy inside their range, and the bottom band is the one exception, with its single message. From the second band up, accuracy rises. In the two middle bands, accuracy and mean confidence sit close together, while in the band from 0.2 to 0.4 the mean confidence is well above the accuracy.

The bands cannot show more: the band from 0.2 to 0.4 holds 41 messages. Every number here comes from the one dev sample that also chose the threshold, so none of them shows how calibrated the adapter will be on new messages.

The router the rule chooses is an empirical cut on dev, recorded with its rule and data. It is a cut, not a model of the messages, so its numbers describe the dev mix. A reader takes its hand-off rate and accuracy on kept messages as the router's result, and re-checks the dev rule when the mix of messages moves.

**Working rule:** Choose the threshold on the dev split by the stated rule, and write its value and the rule into the adapter's manifest. Report the hand-off rate beside accuracy on the messages kept, each with its count, and show at least one setting either side of the chosen value. Check calibration on dev before you trust the confidence as a cut, and when the mix of messages changes, choose the threshold again on a fresh dev draw from the training file.
