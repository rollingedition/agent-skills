---
title: "Small Open Models"
chapter: "Distill a larger model's answers into a small one"
chapter_id: distill-a-larger-model
book: small-open-models
edition: 2026.11.11
verified: 2026-11-20
edition_code: 2BZS-KAEW
canonical: https://rollingedition.com/small-open-models/distill-a-larger-model
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Distill a larger model's answers into a small one,” chapter 6 of Small Open Models, Edition 2026.11.11, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/distill-a-larger-model. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Distill a larger model's answers into a small one

By the end of this chapter, you can train a small student on the labels a larger teacher gives your training rows, measure how often those labels agree with the gold labels, and decide from the same messages whether the student is worth using beside a student trained on gold labels.

A router learns to name the team from labelled messages. This chapter asks whether a larger model can do that labelling for the training rows, so that a small model learns from its answers. The gold labels come from [BANKING77](measure-the-routing-task#the-data-and-its-licence). [Chapter 5](fine-tune-with-lora) trained a head on the gold labels of the training rows, and the adapter it saved, `banking77-lora-v1`, is the human-labelled adapter. Its test result is the bar for everything in this chapter, and its threshold is the one its manifest records, chosen on dev by the rule [chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) gave.

Gold labels cost people time to make, and distillation is the attempt to get around that: a larger model's answers stand in for the gold labels. The larger model here is the [stand-in](route-a-message#ask-a-model-for-one-team). It is larger than SmolLM2-135M-Instruct, the base model this book's router is built on, and it answers the same question the router asks.

## What distillation copies {#what-distillation-copies}

Distillation trains a small model to reproduce a large one. Hinton, Vinyals and Dean's paper, which gave distillation its name, proposed training a small model on the probabilities that a large model gives every class, as soft targets ([Hinton et al., 2015, arXiv:1503.02531](https://arxiv.org/pdf/1503.02531)). Those probabilities carry more information than a single label, the paper argues, and a small model trained this way can often learn from far less data than the large model needs. That is the paper's own claim, from its own experiments, and it is not a rule about every task.

This chapter does not use soft targets. The stand-in returns one team for each message, the team it judges most likely, and the student sees only that team. Kim and Rush used the same simplification for translation, where they replaced the teacher's distribution with its most likely output: "Our simplest approximation is to replace the teacher distribution q with its mode" ([Kim and Rush, 2016, arXiv:1606.07947](https://arxiv.org/pdf/1606.07947)). Their setting is translation, not classification. We borrow the simplification, and we measure it on this task instead of assuming it carries over. Here the teacher's greedy answer plays the part of the mode: it is the one team the teacher returns for each message.

Two things follow from training on one label per message. A student learns the teacher's errors along with its correct answers, because the training loop treats a wrong label as a label, the same as a right one. And the student's errors can differ from the teacher's, which is the reason to measure the student against gold labels as well as against the teacher.

**Working rule:** Before you train a student on a teacher's answers, measure how often the teacher's answer matches the gold label on rows that you have labelled, and read some of the disagreements. Expect the student to reproduce the teacher's errors, and count them on messages the student has not trained on.

## A teacher whose terms allow it {#a-teacher-whose-terms-allow-it}

The teacher has to be a model whose terms allow training on its outputs. The stand-in's GGUF build in this book is the repository `unsloth/Qwen3-4B-Instruct-2507-GGUF`, file `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`, at the revision the teacher's manifest records. The model is Qwen3-4B-Instruct-2507, from Qwen, and the build is by unsloth. We credit both. The model card of the build declares `license: apache-2.0` and names `Qwen/Qwen3-4B-Instruct-2507` as its base model ([model card at the pinned revision](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/raw/a06e946bb6b655725eafa393f4a9745d460374c9/README.md)). The base model's licence, at [a pinned commit](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/resolve/cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE), is Apache License 2.0. The Apache License 2.0, in its second section, grants the right "to reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute the Work and such Derivative Works" ([Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt)).

We read Apache-2.0 as placing no restriction on using a model's outputs. Its text governs the Work and such Derivative Works, as section 2 above sets out, and it does not mention outputs. This is our reading of the licence, not a quotation from it, and it holds for this model's licence only. The adapters this book ships are distributed under Apache-2.0, and [the notice](https://github.com/rollingedition/book-small-open-models/blob/d7e71c0b15e91bbe1fea526b3939eb916bb541ce/examples/data/recorded/NOTICE.md) beside them gives the licence and the attribution.

Licences differ. An open-weights licence such as Apache-2.0 governs the model's files; a hosted model is governed by its provider's terms of service, which can forbid using the service or its outputs to train a competing model. Terms change, so read the current terms of any model you would train on, on the day you use it. This book never uses a hosted model as a teacher.

The stand-in is an open model, so its licence can be read and its file can be fixed by a hash, which the teacher's manifest records. A hosted model's answers can change when its provider changes the model, and its terms may forbid this use. Those are reasons to prefer an open teacher whose file is fixed, even before its terms are read.

**Working rule:** Read the teacher's licence and its terms of use on the day you train. Name the teacher, its licence and its revision in the chapter, and point the student's manifest to the teacher's recording. Do not train on the outputs of a model whose terms forbid it. A licence that places no restriction on outputs answers the question for that licence, so read its text before you assume the answer for another model.

## Label training rows with the teacher {#label-training-rows-with-the-teacher}

The teacher labels training rows only. Dev rows are kept for choosing thresholds, and test rows are kept for reporting, as [chapter 2](measure-the-routing-task#dev-test-and-fixed-samples) set out. The rows to label are drawn from the training file, outside dev. The labelled rows are the first 1,000 of a seeded random draw of 2,000 such rows, a random subset of them, and the recording sorts them by index before labelling. The labelling run was planned for all 2,000, but it could not finish that many within its time limit, so the book reports the 1,000 rows it labelled.

The draw is seeded. Labels already saved for a chosen row are kept and not labelled again, so a run that stops and continues adds only the rows it has not labelled. We did not test whether a resumed run gives the same labels as one full run.

The stand-in answers each message with the router prompt from [chapter 1](route-a-message). It decodes greedily, at temperature zero. In a probe on 40 test messages, two runs gave identical answers, and that probe is the only check we made of repeatability. Its answer is constrained by a grammar to the 77 team names, so each label is a real team.

Example `teacher-agreement` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.23.0), passing in Edition 2026.11.11:

```python
"""Measure how often the teacher's label matches gold on the training rows it labelled, and its accuracy on test_200
from its recorded answers. The point rests on the agreement line; the example reads recorded answers only."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded"

train = router_lib.read_rows("train")
teacher_rows = [json.loads(line) for line in (RECORDED / "teacher-labels" / "labels.jsonl").read_text().splitlines()]
# row["index"] is the row's position in the training file; field 1 of a row is its gold team
agree = sum(row["label"] == train[row["index"]][1] for row in teacher_rows)
n = len(teacher_rows)
print(f"training rows labelled by the teacher: {n}")
print(f"teacher agrees with gold on training rows: {agree}/{n} ({agree / n:.1%})")
print(f"teacher disagrees with gold on training rows: {n - agree}/{n} ({(n - agree) / n:.1%})")

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
standin = router_lib.standin_answers()
# sample holds test row positions; field 1 of a test row is its gold team, field 0 its text
golds = [test[i][1] for i in sample]
teacher_preds = [standin[i] for i in sample]
correct = sum(p == g for p, g in zip(teacher_preds, golds))
print(f"messages on test_200 with a teacher answer: {sum(i in standin for i in sample)}/{len(sample)}")
print(f"teacher accuracy on test_200: {correct}/{len(sample)} ({correct / len(sample):.1%})")
```

Output:

```text
training rows labelled by the teacher: 1000
teacher agrees with gold on training rows: 549/1000 (54.9%)
teacher disagrees with gold on training rows: 451/1000 (45.1%)
messages on test_200 with a teacher answer: 200/200
teacher accuracy on test_200: 109/200 (54.5%)
```

The teacher's label matches the gold label on 549/1000 (54.9%) of the 1000 training rows it labelled, and it disagrees on 451/1000 (45.1%). A student trained on those disagreeing rows learns the wrong label as the answer to each one. The last two lines of the output come from the stand-in's recorded answers on `test_200`, the 200 test messages this chapter reports on. There the teacher is right on 109/200 (54.5%) messages.

Read the line `teacher agrees with gold on training rows` before any student is trained. The line `teacher accuracy on test_200` is the teacher's own accuracy on messages no one has used for training, and it is the reference for every copy measure below.

Counts do not show what the disagreements look like. Three training rows, each labelled `card_arrival` in the gold file, show the pattern. Each message is about a card that has not arrived, described here without its text, since messages are never quoted in this book. The teacher named `card_delivery_estimate` for two of them and `lost_or_stolen_card` for the third, so the teacher names a different team from the gold label each time.

**Working rule:** Measure the teacher's agreement with gold on a labelled sample of rows before you train a student on the labels. Label only rows outside dev and test, and record the teacher's model, its version and its settings in the teacher's recording manifest, and point the student's manifest to it, so each label can be traced.

## Train the student on the teacher's labels {#train-the-student-on-the-teachers-labels}

The student uses the recipe of [chapter 5](fine-tune-with-lora). It has the same base model, the same LoRA targets, the same head, the same seed and the same batch size. Its labels come from the teacher instead of the gold file. The rows and steps differ from chapter 5 as well: the student trains on 1000 rows for 125 steps, and the human-labelled adapter trained on 9000 rows for 1125 steps. The control in [the agreement section](#measure-agreement-not-only-accuracy) keeps the student's rows and steps and changes only the labels. The student's adapter is `banking77-distilled-v1`. Its manifest records its settings and points to the teacher's recording, `teacher-labels/manifest.json`, which names the teacher's model and version, its settings and the rows it labelled, so anyone can trace where each label came from.

The recipe is held fixed on purpose. If the student changed its recipe and its labels at once, a gap in the results could come from either, and a reader could not say which. Keeping the recipe fixed makes the labels the only difference that the results can point to.

A student's threshold is chosen on dev by the same rule as the human-labelled adapter's. The rule takes the lowest threshold, on a grid of hundredths, at which the messages not handed off are at least 0.90 accurate on dev. The rule has a fallback for a student that cannot reach that target. The fallback takes the threshold with the highest accuracy on the messages not handed off, the lowest of any tie, and it skips any threshold that hands off every message. The output says that the fallback was used. This is the book's rule for a result that misses, so it is reported as a fallback and not as a student that met the target. A fallback threshold is chosen from the messages a threshold keeps on dev, and at a high threshold that can be a handful of messages. Treat a fallback value as provisional, and report it with the hand-off rate it costs on test, as this chapter does.

The student's threshold is chosen on part of the dev split, 500 of 1003 messages, because a run over every dev message did not fit the time budget of two CPU cores. Both student examples use that same part, and the control uses it for its own threshold, so the two thresholds are chosen on the same dev messages. The human-labelled adapter's threshold, from chapter 5, was chosen on all 1,003 dev messages.

**Working rule:** Choose a student's threshold on dev by the same rule as the human-labelled adapter, and when no threshold reaches the target, say that the threshold is the fallback. Report the hand-off rate the threshold costs beside accuracy, with both counts, before you compare the student with anything.

## Measure agreement, not only accuracy {#measure-agreement-not-only-accuracy}

Three measures run through this chapter, and each answers its own question. The teacher against gold on the training rows asks whether the teacher is right on the rows it labels, and it is the one [above](#label-training-rows-with-the-teacher). The student against the teacher on `test_200` asks how much of the teacher the student copies. The student against gold on `test_200` asks how often the student names the right team, which is the figure a router would be judged on. Each is printed with its denominator: the first is read on the 1,000 training rows, and the other two on the same 200 test messages.

Agreement and accuracy answer different questions. Agreement with the teacher says how much of the teacher the student has learned, whether the teacher is right or wrong. Accuracy against gold says how often the student names the right team. A student can agree with a wrong teacher and be wrong, and it can disagree with a wrong teacher and be right. Printing both lets a reader see which of the two is happening, instead of inferring it from one figure.

Example `student-recorded-adapter` (Python 3.12.15 · peft 0.21.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.11:

```python
"""Score the distilled student banking77-distilled-v1 on test_200 beside the human-labelled adapter, with the student's
threshold chosen on dev. The point rests on the student's accuracy line and its copy lines; both adapters are loaded
and scored live, and nothing is trained."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded"

tokenizer, student = router_lib.load_classifier(RECORDED / "distill-student" / "adapter")
DEV_N = 500  # the first 500 of the 1,003 dev messages: the run's time budget under two CPUs
# reached is False when no threshold meets the target, and the threshold returned is then the fallback
threshold, reached = router_lib.dev_threshold(student, tokenizer, target=0.90, n=DEV_N)
print(f"dev messages used: {DEV_N} of {len(router_lib.read_sample('dev'))}")
print(f"dev threshold reaching 0.90 accuracy not handed off: {'yes' if reached else 'no'}")
print(f"student threshold chosen on dev: {threshold:.2f}")

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
# sample holds test row positions; field 1 of a test row is its gold team, field 0 its text
golds = [test[i][1] for i in sample]
texts = [test[i][0] for i in sample]
student_preds, student_confs = router_lib.classify(student, tokenizer, texts)
router_lib.print_copy_report("banking77-distilled-v1", student_preds, student_confs, golds, threshold)

# chapter 5 chose the adapter's threshold on dev, and its manifest records the value used here
lora = json.loads((RECORDED / "lora-full" / "manifest.json").read_text())
_, lora_model = router_lib.load_classifier(RECORDED / "lora-full" / "adapter")
lora_preds, lora_confs = router_lib.classify(lora_model, tokenizer, texts)
router_lib.print_copy_report("banking77-lora-v1", lora_preds, lora_confs, golds, lora["handoff_threshold"])

teacher = router_lib.standin_answers()
teacher_preds = [teacher[i] for i in sample]
matches = sum(s == t for s, t in zip(student_preds, teacher_preds))
# positions within sample where the student's answer is not the gold team
wrong = [k for k in range(len(sample)) if student_preds[k] != golds[k]]
wrong_like_teacher = sum(student_preds[k] == teacher_preds[k] for k in wrong)
print(f"student answers equal to teacher answers on test_200: {matches}/{len(sample)} ({matches / len(sample):.1%})")
print(f"student errors on test_200: {len(wrong)}/{len(sample)} ({len(wrong) / len(sample):.1%})")
print(f"student errors equal to the teacher's answer: {wrong_like_teacher}/{len(wrong)}")
```

Output:

```text
dev messages used: 500 of 1003
dev threshold reaching 0.90 accuracy not handed off: no
student threshold chosen on dev: 0.68
banking77-distilled-v1 accuracy on test_200: 69/200 (34.5%)
banking77-distilled-v1 handed off: 150/200 (75.0%)
banking77-distilled-v1 accuracy on messages not handed off: 28/50 (56.0%)
banking77-lora-v1 accuracy on test_200: 172/200 (86.0%)
banking77-lora-v1 handed off: 33/200 (16.5%)
banking77-lora-v1 accuracy on messages not handed off: 156/167 (93.4%)
student answers equal to teacher answers on test_200: 100/200 (50.0%)
student errors on test_200: 131/200 (65.5%)
student errors equal to the teacher's answer: 36/131
```

The student is well behind the human-labelled adapter, and the gap is not only in hand-offs, as the overall figures below show. On `test_200`, the student is right on 69/200 (34.5%) messages and hands off 150/200 (75.0%), while the adapter is right on 172/200 (86.0%) messages and hands off 33/200 (16.5%). The student's threshold is the [fallback described above](#train-the-student-on-the-teachers-labels). Each run's accuracy on the messages it keeps is at its own threshold, and the output gives both beside this paragraph.

The copy measures come next. The student's answer equals the teacher's on 100/200 (50.0%) messages, and the teacher itself is right on 109/200 (54.5%). A student that copies the teacher closely therefore copies the teacher's wrong answers too. The student makes 131/200 (65.5%) errors on `test_200`. Of those errors, 36/131 repeat the teacher's answer. The rest differ from it, so a student's mistakes are not only the teacher's mistakes.

The comparison with the adapter alone mixes two things. The adapter learned from the gold labels of the full training split, and the student learned from the teacher's labels on a smaller set of rows. A gap between them could come from the labels, from the number of rows or from both. To separate them, the book records the same recipe on the same rows with gold labels. The control, `banking77-gold-1000-v1`, is the student's recipe trained on gold labels, and its rows are the rows the teacher labelled.

Example `student-vs-gold-control` (Python 3.12.15 · peft 0.21.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.11:

```python
"""Put the student banking77-distilled-v1 beside its control banking77-gold-1000-v1, which has the same recipe and the
same 1,000 training rows but gold labels, on the same test_200 messages. The point rests on the two counts of messages
each adapter gets right that the other gets wrong, which need no threshold; both adapters are scored live, and nothing
is trained."""

import json
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded"
DEV_N = 500  # the first 500 of the dev messages, as student-recorded-adapter uses: the time budget under two CPUs
print(f"dev messages used: {DEV_N} of {len(router_lib.read_sample('dev'))}")

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
# sample holds test row positions; field 1 of a test row is its gold team, field 0 its text
golds = [test[i][1] for i in sample]
texts = [test[i][0] for i in sample]

runs = {}
for name, folder in [("banking77-distilled-v1", "distill-student"), ("banking77-gold-1000-v1", "gold-same-rows")]:
    tokenizer, model = router_lib.load_classifier(RECORDED / folder / "adapter")
    threshold, reached = router_lib.dev_threshold(model, tokenizer, target=0.90, n=DEV_N)
    print(f"{name} dev threshold reaching 0.90 accuracy not handed off: {'yes' if reached else 'no'}")
    print(f"{name} threshold chosen on dev: {threshold:.2f}")
    preds, confs = router_lib.classify(model, tokenizer, texts)
    router_lib.print_copy_report(name, preds, confs, golds, threshold)
    runs[name] = [p == g for p, g in zip(preds, golds)]

# dict order is insertion order: the student first, then the control
student, control = runs.values()
n = len(golds)
print(f"test_200 messages the student gets right and the control gets wrong: {sum(s and not c for s, c in zip(student, control))}/{n}")
print(f"test_200 messages the control gets right and the student gets wrong: {sum(c and not s for s, c in zip(student, control))}/{n}")

# Recipe sizes from the recorded manifests: the student and its control share rows and steps;
# the human-labelled adapter does not. Its manifest names its row count train_rows, not rows, which is why rows_key differs.
for name, folder, rows_key in [
    ("banking77-distilled-v1", "distill-student", "rows"),
    ("banking77-gold-1000-v1", "gold-same-rows", "rows"),
    ("banking77-lora-v1", "lora-full", "train_rows"),
]:
    settings = json.loads((RECORDED / folder / "manifest.json").read_text())["settings"]
    print(f"{name} training rows: {settings[rows_key]}")
    print(f"{name} training steps: {settings['steps']}")
```

Output:

```text
dev messages used: 500 of 1003
banking77-distilled-v1 dev threshold reaching 0.90 accuracy not handed off: no
banking77-distilled-v1 threshold chosen on dev: 0.68
banking77-distilled-v1 accuracy on test_200: 69/200 (34.5%)
banking77-distilled-v1 handed off: 150/200 (75.0%)
banking77-distilled-v1 accuracy on messages not handed off: 28/50 (56.0%)
banking77-gold-1000-v1 dev threshold reaching 0.90 accuracy not handed off: no
banking77-gold-1000-v1 threshold chosen on dev: 0.97
banking77-gold-1000-v1 accuracy on test_200: 77/200 (38.5%)
banking77-gold-1000-v1 handed off: 197/200 (98.5%)
banking77-gold-1000-v1 accuracy on messages not handed off: 3/3 (100.0%)
test_200 messages the student gets right and the control gets wrong: 24/200
test_200 messages the control gets right and the student gets wrong: 32/200
banking77-distilled-v1 training rows: 1000
banking77-distilled-v1 training steps: 125
banking77-gold-1000-v1 training rows: 1000
banking77-gold-1000-v1 training steps: 125
banking77-lora-v1 training rows: 9000
banking77-lora-v1 training steps: 1125
```

The control also has no threshold that meets the dev target, so it uses the fallback too, and its threshold is provisional for that reason. It hands off 197/200 (98.5%) of `test_200`, and it is right on 3/3 (100.0%) of the messages it keeps. Three messages are not a measure. Overall accuracy needs no threshold, because it counts every message whatever the threshold, so the control's 77/200 (38.5%) sits directly beside the student's 69/200 (34.5%).

The fair comparison is on the answers themselves, and it needs no threshold, because it compares the teams. The control is right and the student wrong on 32/200 messages, and the student is right and the control wrong on 24/200. The control holds no margin over the student that this sample can settle, so we judge 200 messages too few to call one label source better than the other.

The adapter trained on 9000 rows for 1125 steps, while the control and the student share the 1000 rows and 125 steps, so the difference between the control and the adapter mixes row count and steps with anything else the two runs differ in, and this chapter does not separate them.

**Working rule:** Compare two adapters only on the same messages and the same rows. Count the messages each one gets right that the other gets wrong, and print both counts with their denominator. Do not set accuracies taken at different thresholds side by side as though they were the same measure.

## When the teacher is wrong {#when-the-teacher-is-wrong}

A student trained on one label per message learns the labels it is given. Where the teacher is wrong on a row, the student has been shown the wrong team for that row, and it has no way to know otherwise. The teacher's agreement with gold on the training rows, [measured above](#label-training-rows-with-the-teacher), is the share of the teacher's training labels that are right. The student is measured on test messages and not on its training rows, because its figures on rows it trained on would show what it memorised rather than what it learned.

On this task, the student that learns from the stand-in's labels is not the one to ship, as the [figures above](#measure-agreement-not-only-accuracy) show. [Chapter 7](quantize-and-measure) quantizes `banking77-lora-v1`, the human-labelled adapter, and not the student.

Read the copy measure next to accuracy. If the student copies the teacher on most messages and the teacher is wrong on many, the student inherits those errors, and its accuracy against gold falls with the teacher's. If the student disagrees with the teacher on many messages and is still wrong, it is learning something other than the labels, and the first suspect is the number of training rows. That is a rule of thumb from this book's own figures, and this chapter does not test it.

Distilling is worth its cost in some cases. We recommend trying it when gold labels are scarce, when the teacher is strong on your task, and when a sample of gold labels shows that the teacher agrees with them often enough to make the student's errors acceptable. When you already have gold labels for your training rows, train on them, and use a teacher only to check them. A teacher model also changes. Treat a new version of the teacher as a new recording: its labels change, so the student's manifest, its threshold and its measures have to be made again.

In production the failure is quiet. A student that copies its teacher returns a steady stream of teams and a steady hand-off rate, and neither alarms anyone. Check the student against gold labels on a sample of messages that a person has labelled, on a fixed schedule. [Chapter 9](version-watch-and-fall-back#sample-handed-off-messages-for-people) describes the same kind of sample for the adapter's hand-offs as a next step, and this book does not build it. Compare the student's answers with those labels, not with the teacher's, because agreement with the teacher says nothing about the team a message belongs to.

The decisions this chapter made are these:

- The teacher labels training rows only, never dev or test rows.
- The teacher is the stand-in, Qwen3-4B-Instruct-2507, under Apache-2.0, and no hosted model is used.
- The student is trained with the same recipe as the human-labelled adapter, and its threshold follows the same rule, with the fallback reported as a fallback.
- The student is compared with a control trained on gold labels for the same rows, on the same messages, and the two share their rows, so a difference between them comes from the labels and not from the rows.

A teacher's labels carry its mistakes into the student, so agreement with gold decides whether distilling is worth it.

**Working rule:** Train a student on a teacher's labels only when you have too few gold labels for the task and a sample of gold labels shows that the teacher agrees with them well enough. Compare the student with the human-labelled adapter, and with the same recipe on gold labels, on the same messages, before you choose it. When the student loses, ship the adapter and say so in the write-up.
