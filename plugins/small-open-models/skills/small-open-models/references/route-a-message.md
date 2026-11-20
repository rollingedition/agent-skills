---
title: "Small Open Models"
chapter: "Build a router for the bank's inbox that hands off when unsure"
chapter_id: route-a-message
book: small-open-models
edition: 2026.11.7
verified: 2026-11-20
edition_code: M9KG-ZM42
canonical: https://rollingedition.com/small-open-models/route-a-message
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Build a router for the bank's inbox that hands off when unsure,” chapter 1 of Small Open Models, Edition 2026.11.7, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/route-a-message. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Build a router for the bank's inbox that hands off when unsure

By the end of this chapter, you can build a router that returns a team, a confidence and a hand-off flag for one message, score it on a fixed sample by three measures, and see why an untrained small model, prompted as it stands, can't be the router's first version.

Customer messages to a bank land in one support queue, which this book calls the inbox. A router sends each message in the inbox to one of 77 teams. A router that picks a team for every message will sometimes pick the wrong one. A wrong team costs the customer time, and it costs support staff a step to pass the message on. This chapter builds a router that says when it is unsure.

A team is a label the router can return, such as `card_arrival`, and it is never a group of people. The people who read messages are the bank's support staff, and a message the router cannot send on goes to one of them.

The messages and their teams come from BANKING77, a public dataset of customer messages to a bank, published under [CC BY 4.0](https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/57ec275d8078af65b7731c2a98be812d844a6d6b/LICENSE). BANKING77 calls each label an intent. This book calls it a team from here on, and the labels are written as they appear in the dataset.

The router is the whole system: a model, a prompt, a threshold and the code that sends a message on. This chapter builds a rough router. It is rough because its threshold is a placeholder and its model is a stand-in, and it is a working router because it returns an answer for every message and can be scored on every output.
You need Python and one call to a hosted model's API, which you may already have written. This chapter does not ask you to know how a transformer works inside. Where an internal matters, it gets one sentence.

Two shared pieces come first. The first is a recording of a stand-in model's answers to the test messages, which [the section on asking a model](#ask-a-model-for-one-team) introduces. Most examples read those answers offline, and one runs a small model live, in [the section that shows its failure](#show-what-a-small-model-does-first). The second is `router_lib`, a shared module in the book's `examples` folder. It holds the team labels, the router prompt, the hand-off rule and the measures. Every example imports it, so a function means the same thing in every chapter.

## What the router returns {#what-the-router-returns}

For one message, the router returns three things. The team is one of the labels, written as the label itself. The confidence is a number from zero to one that says how sure the router is of that team. The hand-off flag is true when the confidence is too low to send the message on, and a person takes the message instead.

In this chapter, the confidence has a narrow meaning. It is the probability llama-cpp-python returns for the constrained answer, and the recording keeps it as a log-probability. In plain terms, it is how much probability the model gives the team it wrote. In formula form, confidence = exp(sum of log p(token)), the product of the probabilities of the answer's tokens. A token is a piece of text the model reads and writes. This is not a softmax over the teams, which chapter 5 uses. It is a score, not a calibrated probability, and nothing in this chapter shows that a confidence of a given size matches how often the team is right. Chapter 5 checks calibration on the dev split, the training messages held back for choosing settings ([chapter 2](measure-the-routing-task#dev-test-and-fixed-samples)): it groups the messages into confidence bands and prints each band's count and accuracy.

| Output | What it is | What uses it |
| --- | --- | --- |
| Team | One label from the banking set | The destination the message is sent to, when the flag is false |
| Confidence | The probability llama-cpp-python returns for the constrained answer, as a score | The hand-off rule |
| Hand-off flag | True when the confidence is below the threshold | The person who takes the message |

The flag matters most, and the reason is operational. A router that always returns a team sends every message somewhere, including the messages it has no basis to route. A hand-off gives the message to a person who can route it, and a router that says when it is unsure makes that person's work visible. We recommend that every router return the flag in every answer, true or false, so that each measure in the sections below can be computed from the output alone.

This idea has a name in the research literature: selective classification, or the reject option. [Geifman and El-Yaniv's 2017 preprint on deep networks](https://arxiv.org/abs/1705.08500) describes the trade. A classifier that declines some inputs covers fewer of them, and the techniques can potentially and significantly improve a deep network's predictions on the inputs it keeps, by giving up coverage. Their method also lets a user set a target level of risk. The hand-off rule in this book does not do that. It picks a threshold on held-out data, and it gives no guarantee about the risk that remains.

The measurements in this chapter return teams only to be scored. The one-message example, in [the hand-off section](#hand-off-the-unsure-messages), returns a team only when the flag is false.

**Working rule:** Return the flag with every team, and send a message to a person whenever the flag is true. Return the team to the caller only when the flag is false. Keep the flag even when removing it would make a router look more complete, because the hand-off measure counts it.

## Ask a model for one team {#ask-a-model-for-one-team}

The router's team comes from a model, and the model is steered by a prompt. The prompt is the part of the router that the bank changes most often, so we fix it in one place. `router_prompt` builds one prompt for one message. The prompt asks for one team and gives the model the name of every team, the message, and the word `Team:` at the end, for the model to complete. It holds the team names and the one message being routed, and nothing else, so no other message from the sample reaches the model with it.

Every live and recorded run uses the same prompt text, from `router_lib.router_prompt`, so the words are the same in every run. What the model reads is not always the same. The recording wraps those words in the stand-in's chat template, and the live run in [the section on a small model](#show-what-a-small-model-does-first) gives the small model the raw text, without a template. A changed prompt is a different recording, so its scores can't be compared with the old ones. A prompt is part of the router's version, and a reader who changes it should record the change, the same way the book records a change of model.

The bank is the only name this book uses for the organisation. The bank's own router is a hosted model that it calls for each message. We have no access to one, and this book never calls a hosted model. In its place we use the stand-in, Qwen3-4B-Instruct-2507, a larger open model, and every router in the book is measured against the stand-in's answers. A reader's own hosted model will answer some messages differently, and score differently for that reason.

We chose the stand-in because anyone can reproduce its answers. Its licence is Apache-2.0, as [the model card of the GGUF repository](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/raw/a06e946bb6b655725eafa393f4a9745d460374c9/README.md) declares for the file at the revision this book pins. The file is `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`, a quantized build that the llama-cpp-python library runs on a CPU. Its recording manifest names the file's SHA-256, so a reader who downloads the file can check it before anything runs.

The stand-in answered every message of `test_1001`, a fixed sample of 1,001 test messages, once, and `test_40` is its first 40 messages. The recording used greedy decoding, which takes the most likely token at each step, and a fixed seed. It also used a grammar that allowed only the team names, so every recorded answer is one of the 77 labels. That grammar is why the recorded answers are always team names. Chapter 4 explains it, since it is the same idea that fixes the failure in [the section on a small model](#show-what-a-small-model-does-first).

A reader who has a model of their own can record its answers the same way. You write one function, `call_model`. It takes one message and returns the team and the log-probability of the answer, which is the sum of the answer's token log-probabilities, as the stand-in's recording stores it. The function `record_answers` calls it for every message in the sample, writes one line per message in the stand-in's format, and raises an error if the function returns a name that is not one of the teams. Everything else is the same for every model, so two recordings on the same sample can be compared line by line.

Example `record-your-own-answers` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.23.0), passing in Edition 2026.11.7:

```python
"""Write a model's team answers in the stand-in's JSONL shape, then check record_answers against the stand-in's recording.
The line to read is the last one printed, which counts the lines that match the recording. The stand-in here replays
that recording, so no model runs."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import tempfile  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()


def record_answers(call_model, messages, path):
    """Write one JSONL line per (index, text); call_model(text) returns (team, logprob)."""
    with open(path, "w") as out:
        for index, text in messages:
            team, logprob = call_model(text)
            if team not in router_lib.LABELS:
                raise ValueError("the model returned a name that is not a team")
            label = router_lib.LABELS.index(team)  # stored as the label, the same encoding as the gold labels
            row = {"index": index, "label": label, "team": team, "logprob": logprob}
            out.write(json.dumps(row) + "\n")


RECORDING = router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl"
rows = router_lib.read_rows("test")  # each row is (text, gold label)
sample = router_lib.read_sample("test_40")
messages = [(i, rows[i][0]) for i in sample]  # element 0 of a row is its text, which the model reads
with open(RECORDING) as f:
    recording_lines = f.read().splitlines()
recorded = {json.loads(line)["index"]: json.loads(line) for line in recording_lines}  # keyed by message index
by_text = {rows[i][0]: (recorded[i]["team"], recorded[i]["logprob"]) for i in sample}  # keyed by text, not index


def standin(text):
    """Stand in for a model: return the recorded team and logprob for this message."""
    return by_text[text]


with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "answers.jsonl")
    record_answers(standin, messages, path)
    with open(path) as f:
        written = f.read().splitlines()

matching = sum(line in recording_lines for line in written)  # a line matches when it equals a recorded line exactly
print(f"messages written: {len(written)}")
print(f"lines matching the recording: {matching}/{len(written)}")
```

Output:

```text
messages written: 40
lines matching the recording: 40/40
```

Before you trust your own recording, check `record_answers` on the stand-in's answers. Here the stand-in function replays the recording, so the check tests `record_answers` and not a model. Every line it writes matches the recording, all 40 of them. When you swap that function for a call to your own model, the same check shows whether your recording has the same shape as the stand-in's.

**Working rule:** Score every model on the same fixed sample, and record its answers with `record_answers` before you compare it with the stand-in. Say which sample each score is on, and set two scores side by side only when their samples match.

## Hand off the unsure messages {#hand-off-the-unsure-messages}

[The stand-in](#ask-a-model-for-one-team)'s answers give each message a confidence, and this section turns that confidence into the hand-off flag.

The hand-off rule is one comparison. `handoff(confidence, threshold)` returns true when the confidence is below the threshold, and false when it is equal to the threshold or above it. A message that is handed off goes to a person. A message that is not handed off goes to the team the router named. Every route in this book that returns a team to a caller uses this function, so no caller can receive a team without the decision having been made.

The rule is simple to read, and the work is in choosing the number. This chapter uses a placeholder threshold, 0.5, and every output that uses it says so. A placeholder has no rule behind it. It is a number that lets the rule run.

Chapter 5 chooses the threshold on the dev split, by a rule stated there. It records the chosen value in the adapter's manifest, so a reader can see which threshold a result used and what it was chosen on. The test sample is never used to choose it. Until then, the placeholder is the only threshold this chapter has, and its results are for teaching the measures, not for judging the router.

The hand-off rate is the share of messages that go to a person, and it moves with the threshold. Raise the threshold and more messages go to people; lower it and more go straight to a team. The trade-off is the reason the choice is a measured one. Chapter 5 shows the trade-off on the dev split, at more than one setting, before it picks one.

Example `route-one-message` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.23.0), passing in Edition 2026.11.7:

```python
"""Route the first message of test_40 from the stand-in's recorded answer, at the placeholder threshold.
The prose reads the printed team and the hand-off line. No model runs here, and the message's text is never printed."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import math  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

THRESHOLD = 0.5  # Placeholder. Chapter 5 chooses the threshold on the dev split.
RECORDING = router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl"


def route(row):
    """Return (team, confidence, handed off) for one recorded answer. The team is None when handed off."""
    confidence = math.exp(row["logprob"])  # the recording stores a log-probability; exp gives a probability
    flag = router_lib.handoff(confidence, THRESHOLD)  # True below THRESHOLD, and for a NaN; equal to THRESHOLD is kept
    return (None if flag else row["team"]), confidence, flag


with open(RECORDING) as f:
    recorded = {r["index"]: r for r in map(json.loads, f)}  # keyed by message index, as the sample lists them

first = router_lib.read_sample("test_40")[0]  # the first of the sample's 40 message indexes
team, confidence, flag = route(recorded[first])
assert not flag  # the prose states this message is kept; a change that hands it off fails the run
print(f"team: {team or 'none (handed off)'}")
print(f"confidence: {confidence:.2f}")
print(f"handed off: {'yes' if flag else 'no'}")
```

Output:

```text
team: top_up_reverted
confidence: 1.00
handed off: no
```

Follow one message through the whole route, from the recorded answer to a printed team. The example takes the first message of `test_40`, reads the stand-in's recorded answer for it, and routes it through `handoff` at the placeholder threshold. It prints the team, the confidence rounded to two places and whether the message was handed off, and it never prints the message's text. This message's confidence is 1.00, which clears the placeholder, so the router keeps the message and returns its team, top_up_reverted. The script asserts that the message is not handed off. One message shows the shape of the output. It can't show how often the router is right.

**Working rule:** Choose the threshold on the dev split, never on the test sample, and report the hand-off rate beside accuracy every time. While the threshold is a placeholder, say so in each output, and keep its accuracy out of any claim about the router's result.

## Score the router on a fixed sample {#score-the-router-on-a-fixed-sample}

A router is scored on messages whose team is already known. This chapter uses `test_40`, a fixed sample of 40 test messages, so that every reader scores the same messages in the same order. [Chapter 2](measure-the-routing-task#dev-test-and-fixed-samples) explains how the samples were drawn, which split is used to choose settings, and why the test sample is kept out of that choice. The numbers below describe this sample only.

The router is measured by three numbers, and each one has its count beside it.

- **Accuracy** is the messages whose team equals the gold label, divided by all the messages in the sample. A message that is handed off counts in the denominator, and it is wrong if its team is wrong.
- **Hand-off rate** is the messages whose confidence is below the threshold, divided by all the messages.
- **Accuracy on messages not handed off** is the correct messages among those the router keeps, divided by the messages it keeps. It is reported as not defined when the router keeps none.

Each measure answers a different question. Accuracy asks how often the router is right overall. The hand-off rate asks how much of the work goes to people. The accuracy on kept messages asks whether the messages the router keeps can go straight to a team. Accuracy alone does not separate the two kinds of error. A wrong team that was handed off counts against accuracy, and so does a wrong team that reached a team unchecked. Only the third measure isolates the second kind, and that is the kind support staff feel directly.

Example `route-recorded-answers` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.23.0), passing in Edition 2026.11.7:

```python
"""Score the stand-in's recorded answers on test_40, with a placeholder hand-off threshold.
The last printed line, accuracy on messages not handed off, is the one the prose reads against the others: it is the
accuracy of the messages a team receives. No model runs here, and the answers come from the recording."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402
import math  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

THRESHOLD = 0.5  # Placeholder. Chapter 5 chooses the threshold on the dev split.
RECORDING = router_lib.HERE / "data" / "recorded" / "standin-baseline" / "answers.jsonl"

answers = {}
with open(RECORDING) as f:
    for line in f:
        row = json.loads(line)
        answers[row["index"]] = row

rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40")

golds = [rows[i][1] for i in sample]  # element 1 of a test row is its gold label; element 0 is its text
preds = [answers[i]["label"] for i in sample]  # the recorded label is the team's position in LABELS, as the gold is
confs = [math.exp(answers[i]["logprob"]) for i in sample]  # exp turns each recorded log-probability into a confidence

# metrics applies the hand-off rule at THRESHOLD; accuracy's denominator still includes handed-off messages
result = router_lib.metrics(preds, golds, confs, THRESHOLD)
n = result["n"]

print(f"messages: {n}")
print(f"placeholder threshold: {THRESHOLD}")
print(f"accuracy: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:  # None when the router keeps no message, so the measure is undefined
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
messages: 40
placeholder threshold: 0.5
accuracy: 20/40 (50.0%)
handed off: 2/40 (5.0%)
accuracy on messages not handed off: 20/38 (52.6%)
```

Here are the three measures on the sample, at [the placeholder threshold](#hand-off-the-unsure-messages). The example reads the recorded answers, applies the threshold to their confidences, and prints each measure with its count. The line to watch is the accuracy on messages not handed off, because it is the accuracy of the messages a team actually receives.

Read together, the three measures say that the placeholder does not protect the teams. The router is right on 20/40 (50.0%) of the sample, which no team should accept on its own. The threshold hands off only 2/40 (5.0%) of the messages, so most of the sample reaches a team. Those kept messages are routed right at 20/38 (52.6%), only a little above the accuracy on the whole sample. A router that returns a team for every message is not yet one the bank can use.

A sample this small can show that a router fails, and it can show how the measures move. It cannot tell two routers apart with confidence. Chapter 2 sets out the larger samples, and chapter 5 measures its chosen threshold on the same kind of sample.

**Working rule:** Report accuracy, the hand-off rate and the accuracy on messages not handed off together, each with its count, on the same fixed sample, and compare two routers only when both were measured on that sample.

## Show what a small model does first {#show-what-a-small-model-does-first}

The obvious shortcut is to drop [the stand-in](#ask-a-model-for-one-team) and ask a small model directly. SmolLM2-135M-Instruct is the smallest model in the family that this book keeps, and it is the core model for the rest of the book. It runs on a CPU and loads offline from its pinned revision. If it answered with a team name, the router would need no recording at all, so the shortcut is worth testing before anything else is built on it.

The test asks the model the same question the router would ask. The model gets the router prompt for the first 20 messages of the sample, with no constraint on its answer and a cap of a few tokens. Make a guess first: how many of those answers will be team names, with nothing holding the model to the list? Then count them.

Example `unconstrained-first-try` (Python 3.12.15 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.7:

```python
"""Ask the 135M model for a team with the raw router prompt and no constraint, on the first 20 messages of test_40.
Look at the last printed line, which counts the answers that are exactly a team name. The answers stay in this file
and are never returned to a caller."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

tokenizer, model = router_lib.load_model(SMALL)
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40", n=20)  # the first 20, to keep the run short
teams = set(router_lib.LABELS)

answers = []
with torch.no_grad():
    for i in sample:
        # the raw prompt: no chat template and no grammar, so the model may write anything
        inputs = tokenizer(router_lib.router_prompt(rows[i][0]), return_tensors="pt")
        # at most 10 new tokens, and greedy: the most likely token at each step
        out = model.generate(
            **inputs, max_new_tokens=10, do_sample=False, pad_token_id=tokenizer.eos_token_id
        )
        # the output starts with the prompt, so skip its tokens and keep only the answer
        new_tokens = out[0, inputs["input_ids"].shape[1] :]
        answers.append(tokenizer.decode(new_tokens, skip_special_tokens=True).strip())

print(f"messages: {len(answers)}")
# an answer counts only when it is exactly a team name, with no extra words around it
print(f"answers that are a team name: {sum(a in teams for a in answers)}/{len(answers)}")
```

Output:

```text
messages: 20
answers that are a team name: 0/20
```

None of the model's answers is a team name, so the router has nothing to send to a team. The measurement keeps its answers and never returns them to a caller.

This failure does not show that a small model can never route. It shows that this model, asked this way, does not return a team. There are two different fixes, and we take them in order. Chapter 4 constrains the answer, so the model can only write a team name. Chapter 5 trains a head on the model, so each team gets a score from a single forward pass. This chapter does neither, which is why its router runs on the stand-in's recorded answers.

**Working rule:** Before a model routes anything, count its answers that are team names on a fixed sample, and compare the count with the sample's size. If the model does not return a team for every message, do not route with it as it stands. Constrain its answer to the teams, or train it for the task. A hand-off rule placed on an answer that is not a team protects a team that does not exist.

## Where a rough router breaks {#where-a-rough-router-breaks}

A rough router breaks in four ways in production, and each one leaves a sign that support staff can see.

The first is a team name that does not exist. A free-text model can write a team that is not on the list, or a sentence, and a router that sends that text on has sent the message to nobody. [The stand-in](#ask-a-model-for-one-team)'s recording cannot do this, because its grammar allows only the labels, but a reader's model can. The sign is an answer that is not a team name, and [the unconstrained test](#show-what-a-small-model-does-first) counts the answers that are team names. A router should treat such an answer as an error, count it, and send the message to a person. `record_answers` already raises an error for that case, and the router must do the same.

The second is drift. The stand-in's answers hold only for the file, the prompt and the sample they were recorded with. The recording's manifest names the file's SHA-256, the prompt's hash, the decoding and the sample, so a change to any one of them is a different recording. A reader who sees a score move with no change to the code should compare the manifest first, and then the prompt.

The third is a threshold that stops fitting. A threshold chosen on one dev split can stop fitting when the mix of messages changes. The sign is a shift in the hand-off rate, or in accuracy on the messages kept, when the router is measured on new dev messages. Chapter 5 records the threshold with the dev split it was chosen on, so the bank can see what the number was fitted to, and [chapter 9](version-watch-and-fall-back#watch-the-hand-off-rate) watches for the shift.

The fourth is cost and the load on people. A hosted model bills each call. A router that the bank runs bills in compute on its own machine, and [chapter 3](choose-a-base-model#measure-what-one-message-costs) counts what one message costs in tokens and forward passes, while [chapter 10](when-a-small-model-is-the-wrong-choice#count-the-bill-and-the-machine) turns a recorded speed into a bill. Each hand-off is work for a person, and the hand-off rate is the share of that work. We recommend putting the hand-off rate on every report about the router, beside accuracy, so the cost of the flag is never left out.

A router that cannot say when it is unsure hides its mistakes, and the flag makes them countable. The chapter made these decisions. Later chapters keep them, or change them and say why:

- The router returns a team, a confidence and a hand-off flag, and every route that returns a team goes through `handoff`.
- The threshold is a placeholder until chapter 5 chooses it on the dev split.
- Every router is scored by accuracy, the hand-off rate and accuracy on messages not handed off, on the same fixed sample, with counts beside each.
- The stand-in is the baseline, and its answers are recorded. A reader's own model records its answers the same way, with `record_answers`.
- A model that does not return a team for every message is not yet a router.
