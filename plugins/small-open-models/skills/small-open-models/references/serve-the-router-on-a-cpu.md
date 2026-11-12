---
title: "Small Open Models"
chapter: "Serve the router on a CPU, with the hand-off inside the route"
chapter_id: serve-the-router-on-a-cpu
book: small-open-models
edition: 2026.11.1
verified: 2026-11-12
edition_code: 8J4E-MZEZ
canonical: https://rollingedition.com/small-open-models/serve-the-router-on-a-cpu
license: CC BY 4.0
attribution: "“Serve the router on a CPU, with the hand-off inside the route,” chapter 8 of Small Open Models, Edition 2026.11.1, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/serve-the-router-on-a-cpu. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Serve the router on a CPU, with the hand-off inside the route

By the end of this chapter, you can serve the router as one `POST /route` endpoint that returns a team, a confidence and a hand-off flag for each message. You can also test that the route never returns a team for a message it has handed off.

The inbox sends each message to one of 77 teams, as [chapter 1](route-a-message) set out. [Chapter 5](fine-tune-with-lora) built a head that gives a team and a confidence in one forward pass, and it chose the threshold that decides when a message goes to a person. This chapter puts that model behind an HTTP route, so that the inbox's software can send a message and read back a team or a hand-off.

The route is where the hand-off rule either holds or fails. If a caller can get a team from the route for a message the router has flagged, the flag does nothing, however carefully chapter 5 chose its threshold. So the route computes the flag itself, from the same answer as the team, and it returns a team only when the flag is false. Nothing else in the chapter is as important as that rule.

This chapter serves the float32 adapter that [chapter 5](fine-tune-with-lora#use-the-recorded-adapter) took from the recording as it was. [Chapter 7](quantize-and-measure) makes a weight-only int8 copy, `banking77-lora-v1-int8`, and measures the copy. This chapter does not. It also measures nothing about speed. That comparison comes from a recording in [chapter 10](when-a-small-model-is-the-wrong-choice), and nothing in this chapter predicts it.

## One route that returns the hand-off {#one-route-that-returns-the-hand-off}

A route is a function that a web framework calls when a request arrives at a path with a method. The framework here is FastAPI, pinned at 0.162.5 in `examples/requirements.txt`. The router has one route, `POST /route`. A caller sends a JSON object with one field, `message`, which holds the text of one inbox message. The route answers with a JSON object of five fields: `team`, `confidence`, `handed_off`, `adapter` and `version`.

Each field has one source, and that matters for the hand-off. The `confidence` is the softmax probability of the team the model chose, which is the meaning [chapter 5 gave it](fine-tune-with-lora#a-head-that-scores-the-teams). The `handed_off` flag is the result of `handoff(confidence, threshold)`, which is true when the confidence is below the threshold. The comparison is written as `not confidence >= threshold`, so a confidence that is not a number, NaN included, is handed off too. The threshold is not typed into the route. The route reads it from the adapter's manifest, where chapter 5 wrote the value it chose on the dev split, so the route and the chapter cannot disagree about the number. The `team` is `None` when `handed_off` is true, and it is the team's label otherwise. The `adapter` and `version` fields tell the caller which model answered. The manifest has no field for the adapter's version, so the version is the suffix of the adapter's name: `banking77-lora-v1` reports `v1`.

The route calls the classifier once per request. One forward pass gives the team and the confidence together, and the flag is computed from that same confidence. The two cannot come from two different calls and drift apart. A reader who opens the module will find one route of its own, and one path to a team, the answer the route builds after the flag is set. FastAPI adds its documentation pages, which return no team. We recommend that a router keep this shape: one route, one model call, one flag, and the team read only after the flag. A second route that skips the flag would be the quickest way to undo the work of chapter 5, and it would be hard to notice, because it would still return correct teams for the messages it does not hand off.

The example below builds the route and sends it the messages of `test_40`, a committed sample of 40 messages that the book uses for quick checks. The example prints counts and never the text of a message.

Example `serve-route-testclient` (Python 3.12.15 · fastapi 0.162.5 · peft 0.21.2 · pydantic 2.14.3 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Serve banking77-lora-v1 with one POST /route and call it on test_40 through TestClient.
TestClient runs the app in-process: no server process and no socket. Nothing is trained here."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

from fastapi.testclient import TestClient  # noqa: E402

import router_lib  # noqa: E402

router_lib.setup_runtime()
client = TestClient(router_lib.make_app(router_lib.HERE / "data" / "recorded" / "lora-full"))

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40")
replies = [client.post("/route", json={"message": test[i][0]}) for i in sample]
bodies = [r.json() for r in replies]
gold = [test[i][1] for i in sample]

print(f"responses: {len(replies)}")
print(f"status codes: {sorted({r.status_code for r in replies})}")
print(f"response keys: {sorted(bodies[0])}")
print(f"handed off: {sum(b['handed_off'] for b in bodies)}/{len(bodies)}")
print(f"team names outside the list: {sum(b['team'] is not None and b['team'] not in router_lib.LABELS for b in bodies)}")

sure = [k for k, b in enumerate(bodies) if not b["handed_off"]]
unsure = [k for k, b in enumerate(bodies) if b["handed_off"]]
print(f"not handed off, team is the gold label: {sum(bodies[k]['team'] == router_lib.LABELS[gold[k]] for k in sure)}/{len(sure)}")
print(f"handed off, team is None: {sum(bodies[k]['team'] is None for k in unsure)}/{len(unsure)}")
print(f"adapter: {bodies[0]['adapter']}")
print(f"version: {bodies[0]['version']}")

bad = client.post("/route", json={})
print(f"status on an empty body: {bad.status_code}")
print(f"detail is a list: {isinstance(bad.json()['detail'], list)}")
```

Output:

```text
responses: 40
status codes: [200]
response keys: ['adapter', 'confidence', 'handed_off', 'team', 'version']
handed off: 8/40
team names outside the list: 0
not handed off, team is the gold label: 30/32
handed off, team is None: 8/8
adapter: banking77-lora-v1
version: v1
status on an empty body: 422
detail is a list: True
```

The route answered 40 requests. The hand-off count is 8/40, which is the number of messages the route flagged. Every one of those flagged messages came back without a team: 8/8. The example also counts the messages the route kept. Of those, 30/32 have the team that the dataset gives them, the labelled team this book calls the gold label. The kept count is the measure [chapter 2](measure-the-routing-task#three-measures-each-with-its-denominator) calls accuracy on the messages not handed off: the correct messages among those the route did not flag. A handed-off message has no team to score, so it is not in that count. The last count checks the label set: the number of team names outside the 77 is 0.

The example's output shows the shape of the rule. A flagged message has no team, and a kept message has one. It shows this for 40 messages, and that is a sample, not a proof about every request. The proof is in the code, and the example is the check that the code does what the rule says on a sample the reader can rerun.

**Working rule:** Compute the flag in the route, from the same confidence as the team, with `handoff`, and return a team only when the flag is false. Do not add a second route, a field or an option that returns a team for a message the flag has marked. If a caller needs a team for every message, the answer is a person for the messages the flag marks, not a team from the route.

## Load the model once at startup {#load-the-model-once-at-startup}

A route that loaded the model for each request would repeat the same work on every message. The route in this chapter does not, and the reason is where the code sits. Before it loads anything, the function `make_app` checks the adapter's files against its manifest, and it checks the base model's revision against the pin that the manifest records. It raises an error and builds no app on any mismatch. The check is [chapter 9](version-watch-and-fall-back#check-the-adapters-files-against-its-manifest)'s, and this chapter relies on it. After the check, `make_app` reads the manifest, then loads the tokenizer and the model with `load_classifier`, and only then does it define the route. The route function itself only calls `classify` and then `handoff`. So the model is loaded when the app is built, and each request uses the model that is already in memory.

The example builds the app once and then sends all 40 messages to that one app, so the 40 requests share one load. The loading is part of building the app. It is not a step a caller takes, and a caller cannot make the route load a second copy by sending a request.

Threads are the other setting that belongs at startup. `make_app` takes the thread count as its `threads` argument, which defaults to two. It calls `torch.set_num_threads` with that count before it loads the model, so every process that builds the app sets its threads before the first model call. The PyTorch documentation for the call says that it "Sets the number of threads used for intraop parallelism on CPU," and it adds a warning: "To ensure that the correct number of threads is used, set_num_threads must be called before running eager, JIT or autograd code" ([torch 2.15.0+cpu documentation](https://docs.pytorch.org/docs/2.15/generated/torch.set_num_threads.html)). The setting therefore has to come before the first model call, and `make_app` makes that call first.

The setting covers the threads used inside one operation, the intra-op threads the documentation names. Two threads is the book's choice, not a measured best. The book's examples have a budget of two vCPUs, so the book sets two threads for them, and a reader on a different machine should choose a count and measure it. The choice is labelled as the book's, because no output in this chapter compares one thread count with another.

**Working rule:** Build the app once per process, with the thread count that process should use, and before the first request. On a two-vCPU budget, as this book uses, keep the default of two threads, and choose another count only after you have measured your own machine with your own messages.

## Know what the route cannot score {#reject-what-the-route-cannot-score}

Two kinds of request cannot be scored, and the route handles them differently. The first is a request that lacks the field the route needs. The route declares its body as a model with one required field, `message`. A body without that field gets status 422. The example's last lines send a body with no `message`, and its output shows that the reply's `detail` field is a list (True). A caller that receives a 422 has no answer to read, and it should not look for a team in that body.

The second kind of request is a message too long to read in full. The model reads a message as tokens, which are pieces of text, and a long message has more of them. The function `classify` calls the tokenizer with truncation on and `max_length` set to 128. A message longer than 128 tokens is cut at 128 before the model reads it. The route does not check the length, and its answer does not say that a cut happened. The same 128 was used in training: the script that recorded `banking77-lora-v1`, `recordings/lora_full.py`, trains with `max_length` set to 128. So the cut at serving is the cut the model was trained with, and that is the reason the route uses it.

A shorter cut, at 64 tokens, is a common choice, and the count below shows what it would touch on the test sample of 200 messages, the sample that [chapter 5](fine-tune-with-lora) compared models on. The example prints how many of the 200 messages are longer than each cut. Only the tokenizer loads here, and no model runs.

Example `truncation-count` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Count the test_200 messages longer than 64 tokens, and longer than the 128 that classify() cuts at.
Only the tokenizer loads here: no model runs and no message text is printed."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

from transformers import AutoTokenizer  # noqa: E402

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
repo = json.loads((RECORDED / "adapter" / "adapter_config.json").read_text())["base_model_name_or_path"]
tokenizer = AutoTokenizer.from_pretrained(repo, revision=router_lib.pinned_revision(repo))

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
lengths = [len(tokenizer(test[i][0]).input_ids) for i in sample]
n = len(lengths)
print(f"messages over 64 tokens: {sum(x > 64 for x in lengths)}/{n}")
print(f"messages over 128 tokens where classify() cuts: {sum(x > 128 for x in lengths)}/{n}")

# The cut itself: repeat the text of the first test_200 message until it is longer than 128 tokens,
# then tokenize it with classify()'s settings (truncation on, max_length 128).
long_text = test[sample[0]][0]
while len(tokenizer(long_text).input_ids) <= 128:
    long_text = long_text + " " + test[sample[0]][0]
before = len(tokenizer(long_text).input_ids)
after = len(tokenizer(long_text, truncation=True, max_length=128).input_ids)
print(f"repeated message tokens before the cut: {before}")
print(f"repeated message tokens after the cut: {after}")
print(f"truncation side: {tokenizer.truncation_side}")
```

Output:

```text
messages over 64 tokens: 1/200
messages over 128 tokens where classify() cuts: 0/200
repeated message tokens before the cut: 132
repeated message tokens after the cut: 128
truncation side: right
```

The count of messages over 64 tokens is 1/200. The count over 128 tokens, the cut that `classify` applies, is 0/200. On this sample, a cut at 64 tokens would touch 1/200 messages, and the cut at 128 tokens would touch 0/200. That is one sample. It does not say how often long messages occur in a different inbox, and that rate has to be counted on the reader's own messages.

The second part of the example shows what the cut does to a message that is long. It repeats the text of the first `test_200` message until the text is longer than 128 tokens, then tokenizes it with the settings `classify` uses. The message reaches the model as 128 tokens, down from 132. The tokenizer's truncation side is right, so the cut drops the end of the text and keeps its start.

A reader whose messages run longer than this sample has to count them before serving, and the route will not count them for the reader. The route does not reject a long message. It cuts the message, scores what is left, and returns a team when the flag is false, and nothing in the answer shows that a cut happened. So the check belongs before the route, in the caller's hands. We recommend treating a message the route would cut as a message for a person, outside the route, and not as a message to guess. A guessed team would look like a routed message and carry no flag, so no one would know to check it. A message the cut touches is scored on its beginning only, and the caller is not told. That is a quiet failure, and the reader should decide what happens to such messages before the route takes them. The safe outcome, which this book recommends, is that a long message goes to a person, outside the route, with the count reported beside the rest of the results.

**Working rule:** Count the messages longer than the cut before you serve a set of messages, with the tokenizer of the adapter's base model and the same cut the route uses. The route cuts a longer message at 128 tokens and scores only what is left, so when the count is above zero, send those messages to a person outside the route, and report the count with the hand-off rate.

## Test the route in the same process {#test-the-route-without-a-socket}

The route's rule, a team only when the flag is false, has to be checked on real answers, and FastAPI's test client lets a test do that without starting a server. The FastAPI testing tutorial says, of its test client, "Use the `TestClient` object the same way as you do with `httpx`," and it adds that "the calls to the client are also normal calls, not using `await`" ([FastAPI 0.162.5 testing tutorial](https://raw.githubusercontent.com/fastapi/fastapi/0.162.5/docs/en/docs/tutorial/testing.md)). In other words, a test is an ordinary Python loop, and each call returns an answer the test can read.

The example uses that test client. It builds the route from the recorded folder, sends it each of the 40 messages of `test_40`, and reads back the JSON of every answer. It does not start uvicorn, and it does not print message text. Every answer came back with status 200, and the example prints the keys of the first answer, which are the five fields listed in [the first section](#one-route-that-returns-the-hand-off). The counts it prints are the ones the route's rule predicts: the handed-off count, the number of flagged messages with no team, the number of kept messages with the gold team, and the number of team names outside the list. The example also sends a body with no `message`, and it prints that reply's status and whether its `detail` field is a list.

The example does not start a server, and that is a choice. A server started inside an example would need a free port, a wait for start-up and a clean shutdown, and each of those can fail for reasons that have nothing to do with the hand-off rule. A reader who wants a check against a running server can send the same 40 messages to that server and compare its counts with these. The example's output is the same on every run. The seeds are fixed, the algorithms are required to be deterministic, and the default type is float32, all by `setup_runtime`, which the example calls before it builds the route. A reader who runs the example again and gets different counts has found a change in the model, the data or the environment, and the reader should stop and find out which before trusting the route.

The test shows the hand-off rule on the sample, and it shows the rule on each answer in the sample: a flagged answer has no team, and a kept answer has one. A test that checked only the status code would pass a route that returned a team for every message, and it would miss the flag altogether. So the test checks the flag and the team together, and it prints both counts.

**Working rule:** Test the route through the test client on a committed sample, and print the counts that tie the flag to the team: the number of handed-off messages, the number of those with no team, and the number of team names outside the list. A test that checks only the status code does not show that the hand-off rule holds. Each claim the test makes should have a printed line behind it, because a line is what the book can quote and a reader can rerun. A claim without a line is a claim the reader has to take on trust.

## What goes wrong in production {#what-goes-wrong-in-production}

A route that passes its test can still fail once it runs under a server, and the test does not show these failures. The test runs once, on a committed sample, with the code as it stands. Production runs for as long as the service does, on messages nobody has sampled, and often under more than one process. Each of the failures below is a way the sample can be right while the service is wrong. The first is the copies of the model. The deployment page for uvicorn, the server this chapter's route is meant to run under, says that "Unlike gunicorn, uvicorn does not use pre-fork, but uses spawn" ([uvicorn 0.54.0 deployment guide](https://raw.githubusercontent.com/encode/uvicorn/0.54.0/docs/deployment/index.md)). A spawned worker is a new Python process. The module below builds the app when uvicorn imports it, so each worker that imports it loads its own copy of the model. We read the spawn quote as meaning that, and the chapter does not measure the memory a copy costs. A reader should count the copies: the number of worker processes, times the model's footprint on their own machine, before choosing how many workers to run.

Run from the examples folder, where `router_lib` and `data` are, the module that uvicorn imports is one line of setup and one line of app:

```python
# serve_route.py
import router_lib

app = router_lib.make_app("data/recorded/lora-full", threads=2)
```

The command is `uvicorn serve_route:app`. uvicorn takes its application as `"<module>:<attribute>"`, and its [settings page at the same tag](https://raw.githubusercontent.com/encode/uvicorn/0.54.0/docs/settings.md) gives `APP` in that form.

The second is a conflict between two options. The same page says, "The `--reload` and `--workers` arguments are mutually exclusive." A reader who develops with automatic reloading cannot run several workers in the same command. A reader who runs several workers is running without reload, so a change to the code needs a restart. Both facts come from the server's own page, and both should be in the reader's runbook.

The third is threads. Each worker process sets the thread count its `make_app` call asks for, so the total number of threads grows with the number of workers. On the two vCPUs this book budgets for, two threads per worker means one worker. We recommend that a reader count the total threads before adding a worker, and keep the total at or below the cores the machine has. That is a rule of thumb. This chapter does not measure what happens when the total goes above the core count, and it does not claim a number for it.

The fourth is the hand-off rate. The flag depends on the threshold that chapter 5 chose on the dev split, and on the messages the inbox sends. The route returns the flag on every answer, so the rate of flagged messages can be counted from the route's own output. If the rate moves, the route cannot say why. Its answers do not show whether the inbox's messages changed, whether the model changed, or whether the threshold was edited. [Chapter 9](version-watch-and-fall-back) watches this rate, and it adds versions and a fallback to people.

The fifth is the long messages, which [the section on what the route cannot score](#reject-what-the-route-cannot-score) covers. The cut at 128 tokens does not announce itself, so the count above has to be taken again on the messages the route actually receives.

The sixth is the lack of a record. A route that returns the flag but logs only the status code cannot show, after a change, how the hand-off rate moved. We recommend that each answer be logged with its flag, its adapter and its version, so that the rate can be counted from the logs as well as from the test.

The chapter's decisions, in short, are these:

- The route returns the flag in every answer, and a team only when the flag is false.
- The route serves `banking77-lora-v1` in float32, with the threshold read from its manifest.
- Before it loads the model, `make_app` checks the adapter's files and its base pin against the manifest, and it builds no app on a mismatch ([chapter 9](version-watch-and-fall-back#check-the-adapters-files-against-its-manifest)).
- The route cuts each message at 128 tokens, the length the model was trained with.
- Each worker process holds one model and builds it with two threads, the book's choice for a two-vCPU budget.
- The version the route reports is the suffix of the adapter's name.

**Working rule:** Run one model per worker process, built with the thread count you have measured for your machine. Keep two threads per worker, as this book does, until your own measurement says otherwise. Count the worker processes before you count the model's memory on the machine, and keep `--reload` and `--workers` apart. Watch the hand-off rate the route returns, beside its errors, from the first day the route serves messages.
