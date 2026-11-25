---
title: "Small Open Models"
chapter: "Version the router, watch its hand-offs and fall back to people"
chapter_id: version-watch-and-fall-back
book: small-open-models
edition: 2026.11.16
verified: 2026-11-23
edition_code: ND69-JQ1D
canonical: https://rollingedition.com/small-open-models/version-watch-and-fall-back
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Version the router, watch its hand-offs and fall back to people,” chapter 9 of Small Open Models, Edition 2026.11.16, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/version-watch-and-fall-back. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Version the router, watch its hand-offs and fall back to people

By the end of this chapter, you can name a router by the parts that make its answers, check those parts before the route loads them, count the hand-off rate for each window of messages against a stated baseline, and say where each handed-off message goes.

[Chapter 8](serve-the-router-on-a-cpu) put the router behind a route, and each answer carries a team or a flag that sends the message to a person. A route that takes the bank's support messages for months raises three questions that the route cannot answer by itself. Which model is answering? Are its files the ones that were checked? Are the messages it hands off becoming more or fewer? This chapter gives each question a control and a printed count. The controls are the book's own.

This chapter covers what running your own model adds: versions, a fallback to people and retraining. Watching a service in general, with its dashboards, logs and alerts, is ground for a book on production monitoring. This chapter does not repeat it.

## Name the router by its parts {#name-the-router-by-its-parts}

A router is more than its model. It is the base model, the adapter trained on that base, the threshold that sends a message to a person, and the data and recipe that produced the adapter. Two routers that differ in any one of these can answer the same message differently. A log line that says only "the router" cannot tell them apart.

The adapter's files do not include the base model. The [PEFT checkpoint guide](https://raw.githubusercontent.com/huggingface/peft/v0.21.2/docs/source/developer_guides/checkpoint.md) says the saved weights hold only the adapter module's parameters, nothing from the base. The adapter therefore has to name the base it was trained on, and the name has to be exact. This book names the base by its commit, the pin in `examples/models.toml`, because a short commit hash will not do. The [Hugging Face download guide, at v2.4.0](https://huggingface.co/docs/huggingface_hub/v2.4.0/en/guides/download) requires the full-length hash whenever a commit is given. With no revision named, the download takes whatever the `main` branch holds. A branch name therefore moves with the branch, and it is not a pin. Chapter 5 recorded the base revision in the adapter's manifest, next to the threshold, the data commit and the recipe hash.

A version is written into the name. `banking77-lora-v1` is the recorded LoRA adapter, trained for one epoch on the training rows outside the dev split, version one. A new recording of the same recipe is `v2`, and it gets its own name and its own manifest. The manifest has no separate version field. The name is the version, and [chapter 8](serve-the-router-on-a-cpu#one-route-that-returns-the-hand-off)'s route reports the version as the suffix of the adapter's name. For `banking77-lora-v1` that suffix is `v1`. The int8 copy from [chapter 7](quantize-and-measure) is a different model, `banking77-lora-v1-int8`, and this route does not serve it. Its suffix would read `int8`, so a copy served by name needs a version field of its own.

The first check reads the manifest and compares its base revision with the pin. It prints the adapter's name first, followed by the comparison:

Example `adapter-manifest-check` (Python 3.12.15 · fastapi 0.165.0 · peft 0.22.0 · pydantic 2.14.4 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Show what the adapter check does before a route loads an adapter, and what it does to two edited copies.
The point rests on the "route may load" line and on the two "refused by make_app" lines."""
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import tempfile  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
# check_adapter hashes the manifest, the outputs and the LoRA settings; pinned is the manifest's digest matching its pin
manifest, s_ok, s_n, f_ok, f_n, pinned = router_lib.check_adapter(RECORDED)
# the base pin in models.toml, compared with the manifest's base revision
base = router_lib.pinned_revision(manifest["model"]) == manifest["model_version"]
print(f"adapter: {manifest['adapter']}")
print(f"base revision matches pin: {'yes' if base else 'no'}")
print(f"manifest matches pin: {'yes' if pinned else 'no'}")
print(f"settings matching: {s_ok}/{s_n}")
print(f"files matching: {f_ok}/{f_n}")
print("route may load: " + ("yes" if base and pinned and s_ok == s_n and f_ok == f_n else "no"))
with tempfile.TemporaryDirectory() as tmp:
    # changes a manifest field that is neither a LoRA setting nor an output file, so only the manifest digest sees it
    threshold = router_lib.edited_copy(RECORDED, Path(tmp) / "threshold", "manifest.json", "handoff_threshold", 0.0)
    # adds a key that LoraConfig does not know, to the config the settings are read from
    extra = router_lib.edited_copy(RECORDED, Path(tmp) / "extra", "adapter/adapter_config.json", "future_key", 1)
    for label, folder in [("threshold copy", threshold), ("extra-key copy", extra)]:
        _, s_ok, s_n, f_ok, f_n, pinned = router_lib.check_adapter(folder)
        print(f"{label}: manifest matches pin {'yes' if pinned else 'no'}, settings {s_ok}/{s_n}, files {f_ok}/{f_n}")
        print(f"{label} refused by make_app: {'yes' if router_lib.refused_by_make_app(folder) else 'no'}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        router_lib.load_classifier(extra / "adapter")
    named = [w for w in caught if "future_key" in str(w.message)]  # only the warning about the extra key
    print(f"warnings naming the extra key while PEFT loads the copy: {len(named)}")
    # the warning's first sentence: the text up to the first ". " in its message
    print(f"that warning: {named[0].category.__name__}: {str(named[0].message).split('. ')[0]}.")
```

Output:

```text
adapter: banking77-lora-v1
base revision matches pin: yes
manifest matches pin: yes
settings matching: 3/3
files matching: 3/3
route may load: yes
threshold copy: manifest matches pin no, settings 3/3, files 3/3
threshold copy refused by make_app: yes
extra-key copy: manifest matches pin yes, settings 3/3, files 2/3
extra-key copy refused by make_app: yes
warnings naming the extra key while PEFT loads the copy: 1
that warning: UserWarning: Unexpected keyword arguments ['future_key'] for class LoraConfig, these are ignored.
```

The name carries the version, banking77-lora-v1, and the base revision matches the pin (yes). These are the two parts a reader can check against the pins before any file is read.

**Working rule:** Name a router by its base revision, its adapter's name with the version in that name, its data commit, its threshold and its recipe hash, and write all five into the adapter's manifest before the route serves it. Compare the base revision in the manifest with the pin in `examples/models.toml` each time you load the adapter. A pin that has moved means a different base model, and the adapter needs a new check before it serves.

## Check the adapter's files against its manifest {#check-the-adapters-files-against-its-manifest}

A load is not a version check. The [PEFT checkpoint guide](https://raw.githubusercontent.com/huggingface/peft/v0.21.2/docs/source/developer_guides/checkpoint.md) notes that most entries in a LoRA config are not needed to load the model, so a load can succeed with a config that someone has changed by hand. A successful load does not show that the adapter is the pinned one. The extra-key copy below still loads, and that load raises a warning naming the extra key. A mismatched base does fail at load, with a state-dict error, in the research probe; this example does not print that case.

So the check compares the adapter with its manifest, in three parts. It computes the SHA-256 of `manifest.json` itself, and compares it with the digest pinned for the adapter's name in `examples/adapter-pins.json`. The pin covers every field the manifest holds, including the threshold, the base revision and the output digests. It computes the SHA-256 of each output file the manifest lists, and compares it with the digest the manifest records. It also reads the three LoRA settings in the config, the rank, the alpha that sets the scaling and the target layers, and compares them with the manifest. The printed lines give how many of each agree, and whether the route may load the folder.

For the recorded adapter, the manifest matches its pin (yes), 3/3 settings and 3/3 files agree, so the route may load it.

The check also runs on two edited copies, and each one gets its own line. The first has its `handoff_threshold` changed to 0 in the manifest, and its line is manifest matches pin no, settings 3/3, files 3/3. Its settings and files still agree, because the threshold is not a setting and no output file changed. Only the manifest's own digest sees the change, so the copy is refused. The second has one extra key added to its config, and its line is manifest matches pin yes, settings 3/3, files 2/3. Its settings still agree, and the file check refuses it, because the config file's hash no longer matches. PEFT loads that copy anyway, and of the warnings the load raises, 1 names the extra key. In full, it reads UserWarning: Unexpected keyword arguments ['future_key'] for class LoraConfig, these are ignored. The load returns a model with the key ignored, and that warning is all PEFT says about it. A warning is not a refusal. The check is what refuses the copy.

The route in [chapter 8](serve-the-router-on-a-cpu#load-the-model-once-at-startup) runs this check. Its `make_app` calls `check_adapter` before it loads the model, and it also compares the manifest's base revision with the pin. It raises an error on any mismatch, so a copy that fails is refused before the model is in memory. The threshold copy is refused by `make_app` (yes), and so is the extra-key copy (yes). The check trusts the repository. Its pinned digest sits in `examples/adapter-pins.json`, next to the code, so a reader who edits the folder and not the pins file is refused, and a reader who edits both is not. The pins file is therefore reviewed like any other code.

**Working rule:** Run the check before any route loads an adapter. Pin the SHA-256 of the manifest with the code, count the matching settings and files, print each count with its total, and refuse the load when any count falls short or the manifest digest does not match. Take the hashes from the files on disk, and check and load from the same files, with nothing writing to them in between.

## Watch the hand-off rate {#watch-the-hand-off-rate}

The hand-off rate is the number of messages below the threshold divided by all the messages in a window. [Chapter 2](measure-the-routing-task#three-measures-each-with-its-denominator) defined it, and this chapter watches it over time. A watch needs three things, a window, a baseline and a rule for when a window has moved too far from the baseline.

The baseline is the hand-off rate on the dev split at the adapter's threshold. `dev_handed_off` computes it by routing all the dev messages once and counting the hand-offs, which comes to 148/1003 (14.8%). The threshold example in [chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) prints the same count, 148/1003 (14.8%). The two agree, so the baseline is the one that chapter chose the threshold on.

A baseline from dev is not a forecast for the inbox. The dev split is drawn from training rows, team by team. The test sample is drawn from the test split. Neither is a sample of the inbox's traffic, and the mix of teams in live messages is not known. A gap between a window and the baseline is therefore a question to ask, and it does not answer the question itself.

The drift rule is this book's choice, not a figure from a source. A window's hand-off rate drifts when it is more than a stated number of points from the baseline, in either direction. The rule as printed reads more than 10 points from the baseline. Whoever runs the watch should choose a number of their own and write it down before reading the windows.

The committed test sample, `test_1001`, has no dates, so the windows are cut from its first 100 messages. The first two windows, of 25 messages each, are the first messages of the sample, in sample order. Weeks 3 and 4 are a replay, not new traffic. For those two weeks, the example takes the sample's next messages, sorts them by the router's confidence from lowest to highest, and splits the sorted list in two. The example marks the replay as simulated in its printed line, simulated replay of sample messages 51 to 100. The replay is built to produce a spread of confidences, so it shows what the rule does with a skewed window, and like the baseline it says nothing about the inbox.

Example `handoff-windows` (Python 3.12.15 · peft 0.22.0 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Watch the router's hand-off rate week by week on a fixed, ordered sample of test_1001, against the dev baseline.
The point rests on the "drift" lines and on the "lowest confidence" and "right" lines of weeks 3 and 4, which the output
labels as a simulated replay."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
# the threshold is read from the manifest, not typed here
threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")

handed_dev, n_dev = router_lib.dev_handed_off(model, tokenizer, threshold)
base = 100 * handed_dev / n_dev
print(f"dev hand-off rate (baseline): {handed_dev}/{n_dev} ({base:.1f}%)")
print(f"drift rule: more than {router_lib.DRIFT_POINTS:.0f} points from the baseline")
print("weeks 3 and 4: simulated replay of sample messages 51 to 100")
test = router_lib.read_rows("test")
# simulated=True (the default) adds weeks 3 and 4: messages 51 to 100, lowest confidence first, ties by position
for w, (rows, preds, confs) in enumerate(router_lib.watch_weeks(model, tokenizer, threshold), 1):
    n = len(rows)
    handed = sum(router_lib.handoff(c, threshold) for c in confs)
    rate = 100 * handed / n
    # the messages the router keeps, each with its gold team: test row i holds (text, gold team)
    kept = [(p, test[i][1]) for i, p, c in zip(rows, preds, confs) if not router_lib.handoff(c, threshold)]
    right = sum(p == g for p, g in kept)
    print(f"week {w} messages: {n}")
    print(f"week {w} handed off: {handed}/{n} ({rate:.1f}%)")
    # abs makes the rule two-sided, so a fall in the rate drifts as a rise does
    print(f"week {w} drift: {'yes' if abs(rate - base) > router_lib.DRIFT_POINTS else 'no'}")
    print(f"week {w} lowest confidence: {min(confs):.3f}")
    print(f"week {w} right among messages not handed off: {right}/{len(kept)}")
```

Output:

```text
dev hand-off rate (baseline): 148/1003 (14.8%)
drift rule: more than 10 points from the baseline
weeks 3 and 4: simulated replay of sample messages 51 to 100
week 1 messages: 25
week 1 handed off: 6/25 (24.0%)
week 1 drift: no
week 1 lowest confidence: 0.479
week 1 right among messages not handed off: 17/19
week 2 messages: 25
week 2 handed off: 4/25 (16.0%)
week 2 drift: no
week 2 lowest confidence: 0.378
week 2 right among messages not handed off: 19/21
week 3 messages: 25
week 3 handed off: 9/25 (36.0%)
week 3 drift: yes
week 3 lowest confidence: 0.246
week 3 right among messages not handed off: 16/16
week 4 messages: 25
week 4 handed off: 0/25 (0.0%)
week 4 drift: yes
week 4 lowest confidence: 0.981
week 4 right among messages not handed off: 25/25
```

The windows are small because the sample is small, with four windows of 25 messages each. In a window this size, one message is 4 points of the rate, so one message can move a window across the rule's line. A watch on a real inbox needs windows large enough that one message does not decide the flag. The window size belongs in the report, stated before the windows are read.

Weeks 1 and 2 stay inside the rule, and the replay drifts in both directions. The four windows come out like this, each with its count and its flag.

- Week 1 hands off 6/25 (24.0%), and its drift flag is no.
- Week 2 hands off 4/25 (16.0%), and its drift flag is no.
- Week 3 hands off 9/25 (36.0%), and its drift flag is yes.
- Week 4 hands off 0/25 (0.0%), and its drift flag is yes.

Week 4 is the case a reader should look at closely. A rate that falls to zero drifts under this rule, because the rule treats a fall as a change in the same way it treats a rise. The rate is zero since the lowest confidence in week 4 is 0.981, above the threshold, so no message in the window is handed off. The router was right on 25/25 of the messages it kept. The window is one of confident, correct answers, and the drift flag reports that its hand-off rate has moved, not that the router has made mistakes.

Week 3 is the other kind of window. Its lowest confidence is 0.246, its hand-offs rise to 9/25 (36.0%), and the router is right on 16/16 of the messages it keeps. A rise in hand-offs means more messages reach a person. It does not, by itself, show which cause produced the rise, whether a change in the messages, in the teams that appear or in the model. The route cannot say which, because its answers carry no record of the messages, and [chapter 8](serve-the-router-on-a-cpu#what-goes-wrong-in-production) says the same about the rate it returns.

**Working rule:** Count the hand-offs in each window of the same size, print each count with its denominator, and compare each rate with the dev baseline at the adapter's threshold. Set the drift rule, and its number of points, before you read the windows, and write it into your report. Treat a drifting window as a reason to read its messages and their teams, not as a verdict on the router.

## Sample handed-off messages for people {#sample-handed-off-messages-for-people}

The [hand-off watch](#watch-the-hand-off-rate) counts how many messages go to a person. It leaves two questions open, whether the router was right on the messages it handed off and whether it was right on the messages it kept. This section describes how the first would be answered. It is a next step. This chapter draws no sample, reports no labels and gives no number for it.

A person would label a sample of the handed-off messages, drawn with a fixed seed, and the labels would say which team the person chooses for each. Set against the team the router's model would have chosen, they would show how often the two differ on the messages the router was unsure of. A router that is unsure about a message is the one whose choices people should check most, so this sample is the one to draw first. A reader who builds it can use the gold labels of a public dataset as a stand-in for a person's labels, and should say so in the report.

A sample of handed-off messages does not say how the router does on the messages it keeps. The keeps are the messages whose teams the route returned, and the hand-off never sends them to a person. Their accuracy can be estimated only when people check some of them too, after the route has already answered them. The check on kept messages is a second sample, drawn in the same way, and it is not a by-product of the sample of handed-off messages. The measure is accuracy on the messages not handed off, with its count and its denominator, as [chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) set it.

**Working rule:** When you build the sample, draw it with a fixed seed, print how many messages were labelled, and report how often the router's team and the person's team agree, with its count. Label a sample of kept messages on the same schedule, and read the router's accuracy on kept messages only from that sample. Never read the kept rate off the handed-off sample.

## Fall back to a person {#fall-back-to-a-person}

The route returns a flag and no team for a handed-off message, as [chapter 8](serve-the-router-on-a-cpu#one-route-that-returns-the-hand-off) built it. Something must still happen to that message. The rule in this chapter is that a handed-off message always goes to a person. The recorded answer of the stand-in, Qwen3-4B-Instruct-2507, may travel with a handed-off message as a suggestion, labelled as the stand-in's, and the person decides whether to use it. The stand-in's answers on `test_1001` are recorded in `standin-baseline` ([chapter 2](measure-the-routing-task#the-baseline-from-recorded-answers)). The router's team is never returned for a handed-off message.

The route's JSON has `team`, `confidence`, `handed_off`, `adapter` and `version`, and it has no field that says who answered. A fallback answer must therefore never go out in that shape. A reader who wants a suggestion in the response adds a field of their own, on purpose, and says in the response what the field is.

The book does not teach a call to a hosted model as the fallback, and it sets no threshold for the stand-in. Its answers come from a recording, which the fallback script reads. That script measures how often the suggestion is right, and it does not decide anything from that measure.

Example `fallback-to-larger-model` (Python 3.12.15 · peft 0.22.0 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Hand each handed-off message to a person, with the stand-in's recorded answer as a labelled suggestion.
The point rests on the "team returned for a handed-off message" line and the "suggestions right" line."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
# the threshold is read from the manifest, not typed here
threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
test = router_lib.read_rows("test")
standin = router_lib.standin_rows()  # a dict from test row index to the stand-in's answer, for the rows it answered
rows, handed = [], []
# simulated=False keeps weeks 1 and 2 only: the replay belongs to the watch, not to this example
for weekly_rows, _, confs in router_lib.watch_weeks(model, tokenizer, threshold, simulated=False):
    rows += weekly_rows
    handed += [i for i, c in zip(weekly_rows, confs) if router_lib.handoff(c, threshold)]

# the list of records stands in for the person's queue, which the book does not build
# the suggestion is None where the stand-in has no recorded answer, and the team is always None
queue = [{"index": i, "team": None, "suggestion": standin[i]["label"] if i in standin else None} for i in handed]
suggested = [r for r in queue if r["suggestion"] is not None]
right = sum(r["suggestion"] == test[r["index"]][1] for r in suggested)  # index 1 of a test row is its gold team

print(f"messages routed: {len(rows)}")
print(f"handed off by the router: {len(handed)}/{len(rows)} ({100 * len(handed) / len(rows):.1f}%)")
print(f"sent to a person: {len(queue)}/{len(handed)}")
print(f"suggestions attached: {len(suggested)}/{len(handed)}")
print(f"suggestions right: {right}/{len(suggested)}")
print(f"team returned for a handed-off message: {sum(r['team'] is not None for r in queue)}")
```

Output:

```text
messages routed: 50
handed off by the router: 10/50 (20.0%)
sent to a person: 10/10
suggestions attached: 10/10
suggestions right: 4/10
team returned for a handed-off message: 0
```

The example routes the first two windows, 50 messages in all, and the router hands off 10/50 (20.0%) of them. Each handed-off message gets one record, and the output counts the records sent to a person. Where the stand-in has a recorded answer, the record carries it as a suggestion. Of the records, 10/10 carry a suggestion, and the count of teams returned for a handed-off message is 0. The list of records stands in for the person's queue. The book does not build that queue, and a reader who builds one should keep each record with its message.

The suggestions are right on 4/10 of the handed-off messages that carry one. That is fewer than half, and it is the reason the suggestion is shown to a person and never used as the answer. The fallback script does not measure the stand-in on messages the router keeps. Every handed-off message in this sample carries a suggestion, and the chapter does not claim the same for the inbox.

**Working rule:** Send each handed-off message to a person. A recorded answer from the stand-in may come with it, labelled as a suggestion. Never return a team for it, and never put a suggestion in the route's response shape without a field that says who answered. Count the suggestions that are right, with the count and its denominator, before a reader decides how much weight to give them.

## Retrain on a trigger {#retrain-on-a-trigger}

A drifting window is a signal to look, and it does not on its own start a retraining. The book sets three triggers, and this section states each one. The first is drift, the rule in this chapter's watch applied to consecutive windows. The book retrains when two consecutive windows drift, a number no source gives, and you may choose another, provided you state it in advance. The second trigger is a team added to the 77 the router returns. The router has no training rows for it, and people's labels would show it as a team outside the 77. The third is a rise in wrong teams on messages the router keeps, confirmed in the kept-message sample from the previous section. It is not the sample of handed-off messages, whose teams are never returned, so wrong teams there are expected and do no harm. The retrain script below exercises only the first. The recorded data holds no added team and no person's labels, so the second and third are rules without a test here.

Example `retrain-trigger` (Python 3.12.15 · peft 0.22.0 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Decide whether to retrain, as a rule over the weekly drift flags from handoff-windows. The rule is the book's choice,
not a sourced threshold: retrain when two consecutive weeks drift, that is, their hand-off rate is more than
router_lib.DRIFT_POINTS from the dev baseline. The point rests on the "retrain trigger" line."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
# the threshold is read from the manifest, not typed here
threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
tokenizer, model = router_lib.load_classifier(RECORDED / "adapter")
handed_dev, n_dev = router_lib.dev_handed_off(model, tokenizer, threshold)
base = 100 * handed_dev / n_dev

drifting, run, longest = [], 0, 0
# the default simulated=True: weeks 3 and 4 are the replay, the same four windows the watch reads
for rows, _, confs in router_lib.watch_weeks(model, tokenizer, threshold):
    rate = 100 * sum(router_lib.handoff(c, threshold) for c in confs) / len(rows)
    flag = abs(rate - base) > router_lib.DRIFT_POINTS  # two-sided, as in the watch
    drifting.append(flag)
    run = run + 1 if flag else 0
    longest = max(longest, run)
    print(f"week {len(drifting)} drift: {'yes' if flag else 'no'}")

print(f"weeks drifting: {sum(drifting)}/{len(drifting)}")
print(f"longest run of drifting weeks: {longest}")
print("rule: retrain when two consecutive weeks drift")
print("retrain trigger: " + ("fired" if longest >= 2 else "not fired"))
```

Output:

```text
week 1 drift: no
week 2 drift: no
week 3 drift: yes
week 4 drift: yes
weeks drifting: 2/4
longest run of drifting weeks: 2
rule: retrain when two consecutive weeks drift
retrain trigger: fired
```

The retrain script applies the drift rule to the same four windows as the watch, in order, and finds 2/4 windows that drift, with a longest run of 2. Weeks 3 and 4 drive that result, since they are the replay from the watch. The trigger fired because of how the replay was built, so the run shows the rule working as stated, not anything the inbox did.

When a retraining does start, it follows the same path as the first adapter. It is a recording in `recordings/`, as `banking77-lora-v1` was, written by a script there, and it writes a manifest with the same fields. It is named as the next version of the same recipe, so the retrained adapter is `v2`. Its threshold is chosen again on the dev split by the rule in [chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev), never on the test sample. The retrained folder then needs its manifest's digest added to `examples/adapter-pins.json`, as a change to the repository that someone reviews. Until then, `make_app` refuses to build the app from it. The old adapter stays in place until `make_app` builds an app from the new folder.

**Working rule:** Retrain when the trigger you stated is met, and not on one drifting window. Write the trigger, its number and the rule beside the windows that met it. A retrained adapter is a recording named as the next version, with its manifest digest pinned and its threshold chosen again on dev. Keep the previous adapter until the new one passes the check in `make_app`.

## What goes wrong in production {#failures-in-production}

- **A manifest is edited by hand.** The manifest's digest is pinned, so the check refuses it. A check that trusts the repository can be defeated only by editing the pins file too, which is a change someone reviews.
- **A pin moves.** The base pin in `examples/models.toml` can change under an adapter whose manifest still names the old revision. `make_app` compares the two and refuses the build.
- **A fallback routes on the wrong scale.** A confidence from a model that was never calibrated to the threshold is not a gate. The book's fallback therefore never routes, and the suggestion travels only with a person's message.
- **The window is too small.** In a window of 25 messages, one message is 4 points. A flag then reflects one or two messages, and a reader who acts on it has acted on noise.
- **The rate moves and nothing explains it.** The route's answers carry no record of the messages, so the rate's movement is a question to answer from the messages and their teams, with the samples this chapter describes as next steps.

You notice the first kind of failure when the app is built. A refused folder raises an error at startup, so a deployment that builds the app when it starts sees a bad folder before any message fails. The other failures show in the counts. A moved hand-off rate shows in a window's count, and the drift rule reports it. A fallback that answers the wrong messages shows in the suggestion count, and a sample of people's labels shows the rest.

**Working rule:** Print each control's count where a reader can see it at startup and in each window, and keep the counts that would reveal a failure in the same report as the rate they explain.

## The decisions this chapter made {#the-decisions-this-chapter-made}

- A handed-off message always goes to a person. The stand-in's answer, when there is one, is a labelled suggestion, and the chapter counts how often it is right.
- The version check pins the SHA-256 of each adapter's `manifest.json` in `examples/adapter-pins.json`, checks the output files and LoRA settings against the manifest, and `make_app` refuses to build on any mismatch or a moved base pin.
- The drift rule is 10 points from the dev baseline, in either direction, on windows of 25 messages.
- A retrain is due when two consecutive windows drift. The second and third triggers are stated rules, not tested here.

[Chapter 10](when-a-small-model-is-the-wrong-choice) uses the same measures as this chapter.

All four are the book's choices; see [the drift rule](#watch-the-hand-off-rate). Together the controls check which model answers, count what it hands off and send each handed-off message to a person. The fallback rule follows the rule from [chapter 1](route-a-message#what-the-router-returns) that a flagged message goes to a person. The pin rule trades a review of the repository for a check that a load alone cannot make.

**Working rule:** Write each decision above into the report with its number and whether it is the book's choice or a sourced figure. Change a decision only by changing the rule it names, and rerun the examples that print its counts.
