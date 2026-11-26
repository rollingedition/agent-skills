---
title: "Agent Harnesses"
chapter: "One interface for scripted, replayed, local and hosted models"
chapter_id: model-adapters
book: agent-harnesses
edition: 2026.11.8
verified: 2026-11-22
edition_code: 7VH3-TBZX
canonical: https://rollingedition.com/agent-harnesses/model-adapters
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“One interface for scripted, replayed, local and hosted models,” chapter 4 of Agent Harnesses, Edition 2026.11.8, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/model-adapters. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# One interface for scripted, replayed, local and hosted models

By the end of this chapter you can run the same loop on a scripted model, a replayed run, a local model and an OpenAI-compatible endpoint, without changing the loop. You can also say what each adapter keeps from a reply, and what it reads out of the reply's text.

Chapter 1 ran the maintenance agent for `unitcraft` on a scripted model, then on a stored run, and the loop took both without a change. The next question is what a model has to hand over for that to work. For T-01, the issue that `format_quantity` drops trailing zeros, so `3.5 kg` prints as `3.5 kg` where the default of two places gives `3.50 kg`, every step needs the same three things back: the model's text, the tool calls the harness can read from that text, and the counts of tokens the request and the reply used. A scripted list of strings can supply all three. So can a file on disk, a model loaded in memory, or an HTTP endpoint. The adapter is the code that makes each source, from a scripted list of strings to an HTTP endpoint, look the same to the loop, and the rest of this chapter takes the four adapters in the order the loop meets them.

## Ask every model the same question {#model-protocol}

The loop needs one thing from a model: given the messages so far and the tool schemas from [the schema chapter](#schema-says), return what the model said. A Python `Protocol` names that contract. Every adapter in this book has the same method, and every adapter returns the same kind of value.

```python
class Model(Protocol):
    def reply(self, messages: list[dict], tools: list[dict]) -> Reply: ...
```

The `Reply` is a small dataclass. It holds the model's raw `text`, the tool calls the adapter read from that text, any malformed blocks it could not read, the prompt and completion token counts, and the finish reason, which says why the model stopped, such as on its own or because it ran out of tokens. A [token](#token-counts) here is the unit that [chapter 1](#what-goes-wrong) counts, from the pinned model's own tokenizer, so the counts belong to that model and mean nothing for another. The adapter never edits `text`. The loop acts on the calls, but the transcript keeps the text as the model wrote it, so a reader can see what the model actually said.

Keeping both the text and the calls matters because parsing can fail. A reply may hold a `<tool_call>` block whose JSON does not parse, or a block that is never closed. The adapter cannot quietly turn such a reply into a call, and it cannot throw the reply away, because the loop has to tell the model what went wrong. So the parse leaves the text as it is, records a short reason for each bad block beside it, and lets the loop decide what the model sees next. [The local model section](#local-model) shows the parser at work.

A `Protocol` looks like an interface, but Python checks it by shape. [Python's typing documentation](https://docs.python.org/3.12/library/typing.html) says that a `runtime_checkable` protocol "will check only the presence of the required methods or attributes, not their type signatures or types." So `isinstance` can confirm that an object has a `reply` method, and nothing more: a class whose method is written `reply(self, prompt)` passes, and a class with no `reply` fails. The book's own `Model` is not decorated with `runtime_checkable`, and the same documentation says `isinstance` on such a protocol raises a `TypeError`. No example in this book calls `isinstance` on `Model`, so both claims are the documentation's and not run here.

**Working rule:** Test each adapter by calling `reply()` with the messages and tool schemas the loop sends, and check the fields of the `Reply` that come back. Use `isinstance` only to see that a method exists, never to show that its signature is right.

## Script the replies, or replay a stored run {#scripted-and-replayed}

Two adapters need no model at all. [Chapter 1's scripted run](#scripted-run) used a scripted model, and [its replayed run](#replayed-run) used a stored one. Both work for the same reason: the loop is the thing under test, and a fixed list of replies keeps the model out of it. This section says what the adapters add to that.

`ScriptedModel` takes strings or `Reply` objects. A string is parsed into a `Reply` for you, and its tool calls are read from the `<tool_call>` blocks in the text. A `Reply` object is passed through unchanged. That second form lets a test set the token counts or a malformed entry directly, instead of writing JSON that must fail in exactly the right way. If the loop asks for more replies than the script holds, the model raises an `IndexError`, so a short script fails loudly rather than returning nothing. The script also keeps a test readable. The reply that causes a behaviour sits in the test beside the assertion about it, and the reader does not have to open a recording to find it.

`ReplayModel` reads one run's rows from the recording's `replies.jsonl`, in step order. Each row holds the request's hash as it was sent, the reply's text and the token counts. When the loop asks for a step, `ReplayModel` hashes the request it was given, the sha256 of its messages and tool schemas as JSON with sorted keys, no spaces and ASCII escapes, and compares that hash with the row's. A difference raises `ReplayMismatch`, which names the step. The counts come from the stored row, so a replay never tokenizes again.

The rows come from a logger, not from a script. `LoggedModel` wraps a live model and appends each reply to a JSON-lines file before the loop sees it. A run that stops partway leaves its rows on disk, and the recording script removes them before it resumes.

Chapter 1's T-01 run goes through the loop twice in the first example: once on a `ScriptedModel` that holds the stored reply texts, and once on the `ReplayModel` for the same run. The scripted replies are read from the stored file, so both runs start from the same source.

Example `same-loop-two-models` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.4), passing in Edition 2026.11.8:

```python
"""Chapter-1-t01 runs through the loop twice: once with a ScriptedModel holding the stored reply texts, once with a
ReplayModel. The assert compares the two runs' step lines, and the lines printed below are the replayed run's."""
import json

from lib.case import load_tasks
from lib.loop import run_task
from lib.models import RECORDED, ReplayModel, ScriptedModel
from lib.tools import CH1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]
rows = [json.loads(line) for line in (RECORDED / "chapter-1-t01" / "replies.jsonl").read_text(encoding="utf-8").splitlines()]


def run_once(model):
    run = run_task(model, task, CH1, max_steps=CH1.step_cap, ids=IdCounter())  # counter-based IDs, never random (P-3)
    try:
        return list(run.trace.lines()), run.steps, run.ended
    finally:
        run.close()


scripted = run_once(ScriptedModel([row["text"] for row in rows]))
replayed = run_once(ReplayModel("chapter-1-t01", "T-01"))
assert scripted == replayed, "the two adapters gave the loop different steps"
lines, steps, ended = replayed
for line in lines:
    print(line)
print(f"steps: {steps}")
print(f"ended: {ended}")
```

Output:

```text
step 1: read_file: 23 lines
step 2: run_tests: 8 failed, 22 passed
step 3: malformed: error: malformed call
step 4: malformed: error: malformed call
step 5: malformed: error: malformed call
step 6: malformed: error: malformed call
step 7: malformed: error: malformed call
step 8: malformed: error: malformed call
steps: 8
ended: step_cap
```

The loop made the same calls both times, and the example stops if the two runs differ in any step line. The run is the one that [hit the step cap](#what-goes-wrong) in chapter 1: it ended as `step_cap` after `8` steps. The loop cannot tell the two adapters apart, so whatever the loop does with a reply, it does the same for either source.

The second example checks the recording itself, against its manifest, and then replays it.

Example `replay-byte-for-byte` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.4), passing in Edition 2026.11.8:

```python
"""The stored chapter-1 run is the recording its manifest describes, and replaying it hands the loop each stored reply text
exactly. The prompt and the check hash to the manifest's values, the first request hashes to the reply row stored with it,
and the stored replies add up to the manifest's counts. The run is then replayed through the loop, which refuses any request
that differs from its recorded hash, and each replayed text is compared with its stored text. No model file is loaded."""
from contextlib import closing

from lib.case import load_tasks
from lib.loop import run_task
from lib.models import RECORDED_SAMPLING, ReplayModel, TextCapture, first_step, load_recording, request_hash, same_texts, stored_totals
from lib.prompts import prompt_sha256
from lib.tasks import check_sha256
from lib.tools import CH1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]
manifest, rows = load_recording("chapter-1-t01")
messages, tools = first_step(task, CH1)
assert manifest["prompt_sha256"] == prompt_sha256(CH1.system, CH1.descriptions()), "the prompt changed since recording"
assert manifest["check_sha256"] == check_sha256(task), "the check changed since recording"
assert rows[0]["request_sha256"] == request_hash(messages, tools), "the first request differs from the stored reply row"
assert len(rows) == manifest["steps"], "the stored replies and the manifest disagree on the step count"
prompt_tokens, completion_tokens = stored_totals(manifest, rows)
assert manifest["sampling"] == RECORDED_SAMPLING, "the recording's sampling differs from the settings the adapters send"

capture = TextCapture(ReplayModel("chapter-1-t01", "T-01"))
with closing(run_task(capture, task, CH1, max_steps=CH1.step_cap, ids=IdCounter())) as run:
    steps, ended = run.steps, run.ended
compared = same_texts(rows, capture.texts)
assert steps == manifest["steps"] and ended == manifest["ended"], "the replay did not end as the manifest records"
print(f"stored replies: {len(rows)}")
print(f"prompt tokens: {prompt_tokens}")
print(f"completion tokens: {completion_tokens}")
for key in ("temperature", "top_k", "seed"):
    print(f"{key}: {manifest['sampling'][key]}")
print(f"reply texts compared exactly: {compared}")
print(f"steps: {steps}")
print(f"ended: {ended}")
```

Output:

```text
stored replies: 8
prompt tokens: 13009
completion tokens: 2128
temperature: 0
top_k: 1
seed: 4217
reply texts compared exactly: 8
steps: 8
ended: step_cap
```

Here the manifest is the reference, and the example makes four checks. The prompt's hash and the check's hash are compared with the manifest's values, where the check is the hidden test, H-01, that [chapter 1](#tools-and-a-loop) grades T-01 with. The first request's hash is compared with the one stored in its reply row in `replies.jsonl`, because the manifest holds no request hash. The stored replies must match the manifest's step count and token totals, and the sampling settings are printed from the manifest and compared with `RECORDED_SAMPLING` in the library, the values `loopback_model` sends. The stored run has 8 replies, 13009 prompt tokens and 2128 completion tokens. The example prints its sampling settings on their own lines, so a reader sees the temperature, the top k and the seed the recording used.

Then the run goes through the loop. `ReplayModel` refuses any step whose request hash differs from its row, and the example compares each replayed text with its stored text, exactly. It prints the count it compared, 8, and the run ends as the manifest says. The manifest holds no hash for each reply, so the stored texts are not checked against an independent value. The check shows that replay hands the loop each stored text unchanged. The prompt hash covers the system message and the tool descriptions together, so a changed tool description changes the recording's identity as surely as a changed line of code does.

**Working rule:** Replay a recorded run only with the prompt and the check it was recorded with. When either changes, its hash in the manifest no longer matches, the example fails, and the run has to be recorded again. Changing a stored reply to make the example pass hides the change that caused the failure.

## A local model, and why its settings are fixed {#local-model}

`LlamaModel` runs a local model. It loads a GGUF file, the single-file format llama.cpp reads, through llama-cpp-python. The adapter imports the library only when a model is built, so the examples never load it. No example loads the GGUF file, and the book has no test of `LlamaModel`. The recording used it, and the examples read the replies that recording stored. Its `reply()` calls `create_chat_completion` with the messages and the tools, and it reads the text and the usage from the answer.

The library's defaults are not the book's. At the pinned release, [llama-cpp-python's `create_chat_completion`](https://raw.githubusercontent.com/abetlen/llama-cpp-python/v0.3.36/llama_cpp/llama.py) defaults to a temperature of 0.2 and a top k of 40. An adapter that leaves those alone samples differently from this one. `LlamaModel` passes `temperature=0` and `top_k=1` on every call, so the sampling is written in the code rather than inherited from the library.

What comes back is text. The recording's server ran the pinned llama-cpp-python as `python -m llama_cpp.server` on the same model file, and it returned the first step's tool call inside the message content. The stored body from [the endpoint recording](#openai-compatible) has that content and no `tool_calls` field at all:

```
<tool_call>
{"name": "read_file", "arguments": {"path": "unitcraft/format.py"}}
</tool_call>
```

So the library's reply carries the call as text, and `LlamaModel` does not read a structured field from it. It parses the text.

Parsing is one function, `parse_tool_calls`. It finds each `<tool_call>` block, reads it as JSON with a `name` and an `arguments` object, and keeps the call. A block that does not parse becomes a malformed entry with a short reason. The loop shows that entry to the model as a tool error, so a bad call is recorded as a step and not dropped. Chapter 1's T-01 run, in [what goes wrong](#what-goes-wrong), shows this: after its first two steps, every step is `error: malformed call`.

The finish reason matters to the loop. `stop` means the model ended its answer, and `length` means the reply reached the token limit the adapter set. A `length` reply can stop in the middle of a `<tool_call>` block, which is why the parser also reports an unclosed block as malformed rather than reading it as complete.

The counts are the library's own. `LlamaModel` copies the prompt and completion token counts that llama-cpp-python reports into the `Reply`, and the recording stores them. They describe the tokenizer of the pinned file, so a different file gives different counts for the same messages, and a count from one model cannot be compared with a count from another.

The constructor takes the file's path, the context size, the thread count, the seed and the token limit, and nothing else about the model. The recording reads its values from `recordings/local_model.py`, so a reader who wants to load a different file changes the path and those settings together, and records again. The sampling is a choice, and the model card recommends another. The [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) says, "We suggest using `Temperature=0.7`, `TopP=0.8`, `TopK=20`, and `MinP=0`." Those settings suit answers that vary from one run to the next. This book records a run once and checks later runs against the stored replies, so it uses temperature 0, top k 1 and a fixed seed, 4217, as the manifests record. Those settings give a re-recording its best chance of matching, but temperature 0 does not guarantee that output repeats, so the book claims no more than its examples show. [The endpoint example](#openai-compatible) checks that two requests on one recording gave the same text. Replay does not depend on sampling at all, because it reads the stored text.

**Working rule:** Record with the sampling the manifest names, and keep the model file's hash in the manifest beside it. If you change a setting, the replies change with it, so record the run again rather than compare it with the old one.

## A hosted-style endpoint, tested on loopback {#openai-compatible}

A server that accepts OpenAI's chat-completions request shape can be reached by one adapter, given a base URL and, where the host asks for one, a key. `OpenAICompatibleModel` posts the messages, the tool schemas and the sampling settings to `/chat/completions`. It uses the standard library's `urllib` and no SDK. Without an SDK, nothing hides the request: `request_body()` returns the body the adapter serialises and sends, and a test can compare it with what was recorded. The `top_k` field is sent only when the adapter was given a value for it. The adapter refuses two things when it is built, before any request: a URL that is not `http` or `https`, and a key sent over plain `http` to any host but loopback. It also never follows a redirect. A redirect raises an error, so a key is never sent to a second URL.

The response has the tool call in one of two places. [OpenAI's reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) describes a tool call's `function.arguments` as a string that the model generates in JSON, and tells the caller to "Validate the arguments in your code before calling your function." The adapter parses that string when the reply has a structured `tool_calls` field. When the field is missing, it falls back to the `<tool_call>` text, as the local model does. `parse_chat_body` keeps `message.content` as the server sent it, reads a missing content as empty text, and copies the usage counts into the `Reply`, so a stored body parses to the same `Reply` every time. Either way, the arguments reach the loop as a dictionary, and the dictionary is not yet checked. The tool's argument model from [the schema chapter](#schema-says) does that check.

No example in this book sends a request that returns a structured `tool_calls` field, so the first branch exists as code and is not run by any example. The book does not show what other providers return in that field, and this chapter says no more about it than the OpenAI reference does.

The recording used the same file and the same sampling as the local model. It ran the pinned llama-cpp-python's own server on loopback, and sent T-01's first step through the adapter twice. The stored file holds each request as sent and each raw response body. A loopback `http.server` serves those bodies in order, and it answers `409` to any request whose body differs from the recorded one. The stub compares the request body, every message and every setting. It does not compare the path, the method or the headers, so a change to the endpoint's path or to the `Authorization` header would pass. If a change to the adapter alters the body it sends, the request fails before any reply is read. The stored bodies keep the server's own `id` and `created` fields. Nothing compares or prints them. Because no model is loaded, the adapter's HTTP and parsing code runs every time the book's examples are checked.

Example `openai-compatible-loopback` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.4), passing in Edition 2026.11.8:

```python
"""The OpenAI-compatible adapter, run live against a loopback stub that serves the bodies recorded from llama.cpp's own
server. The line that matters is "raw text": the server put the call in the message content as text, with no tool_calls
field, so the adapter parses the text, and the tool's own model accepts the arguments. Needs
recordings/openai_compatible.py to have been run; until then this raises."""
import json

from lib.case import load_tasks
from lib.models import first_step, loopback_model, serve_recorded
from lib.tools import CH1

task = load_tasks(only=["T-01"])[0]
messages, tools = first_step(task, CH1)
bodies: list[str] = []
with serve_recorded("openai-compatible") as base_url:
    model = loopback_model(base_url, on_body=bodies.append)
    first = model.reply(messages, tools)
    second = model.reply(messages, tools)
assert first.text.lstrip().startswith("<tool_call>"), "the server should return the call as text"
assert "tool_calls" not in json.loads(bodies[0])["choices"][0]["message"], "the recorded body has a structured tool_calls field"
assert len(first.tool_calls) == 1 and first.tool_calls[0]["name"] == "read_file", "the first step is one read_file call"
assert not first.malformed, "the call should parse"
CH1.get("read_file").args.model_validate(first.tool_calls[0]["arguments"])  # raises if the arguments do not fit the tool
assert first.text == second.text, "the two recorded responses differ"
print(f"requests: {len(bodies)}")
print("raw text:", json.dumps(first.text))
print("structured tool_calls field: absent")
print(f"tool calls: {len(first.tool_calls)}")
print("call:", first.tool_calls[0]["name"], json.dumps(first.tool_calls[0]["arguments"], sort_keys=True))
print(f"malformed: {len(first.malformed)}")
print(f"prompt tokens: {first.prompt_tokens}")
print(f"completion tokens: {first.completion_tokens}")
print(f"finish reason: {first.finish_reason}")
```

Output:

```text
requests: 2
raw text: "<tool_call>\n{\"name\": \"read_file\", \"arguments\": {\"path\": \"unitcraft/format.py\"}}\n</tool_call>"
structured tool_calls field: absent
tool calls: 1
call: read_file {"path": "unitcraft/format.py"}
malformed: 0
prompt tokens: 501
completion tokens: 22
finish reason: stop
```

The adapter gets back one `read_file` call, as text. Checking its arguments against the tool's model falls to the caller, and that check is this section's whole point, so the example makes it explicit. The reply carries 1 tool call and 0 malformed blocks, and the request used 501 prompt tokens. The reply stops with `stop`, which means the model finished its answer on its own and did not run out of tokens.

The helper that builds the adapter for the recordings and the example, `loopback_model`, fixes the model alias the server was started with, a limit of 1024 tokens for each reply, temperature 0 and top_k 1. A caller that wants other settings builds `OpenAICompatibleModel` directly, and the request body it sends then differs, which the stub will refuse.

The proxy works as it does for any `urllib` request, except for loopback hosts, `127.0.0.1`, `::1` and `localhost`, which are reached directly. A remote `http` URL goes through the proxy the environment names. A stub stands in for the proxy in the refusal example, and it shows both halves: the loopback requests never reach it, and the remote request arrives with its full URL.

Example `adapter-refuses-unsafe-endpoints` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.8:

```python
"""The OpenAI-compatible adapter refuses a redirect, a key over plain http to a remote host, and a non-http scheme. It sends
a remote URL through the environment's proxy and a loopback URL around it. Every request goes to a stub on 127.0.0.1, which
stands in for both the endpoint and the proxy, so no network is used. Each refusal prints one labelled line."""
from lib.models import OpenAICompatibleModel, proxy_env, refusal, stub_endpoint

REMOTE = "http://remote-host.invalid/v1"
MESSAGES = [{"role": "user", "content": "ping"}]

with stub_endpoint(200) as proxy, stub_endpoint(302) as target, proxy_env(proxy):
    loopback = f"{target.url}/v1"
    model = OpenAICompatibleModel(loopback, "model", max_tokens=8, api_key="DUMMY-KEY")
    reason = refusal(lambda: model.reply(MESSAGES, []))
    assert target.seen == ["/v1/chat/completions"], "a redirect was followed"
    print("redirect 302 on loopback:", reason)
    target.code = 307
    reason = refusal(lambda: model.reply(MESSAGES, []))
    print("redirect 307 on loopback:", reason)
    assert target.seen == ["/v1/chat/completions"] * 2, "a redirect was followed"
    print(f"requests to the redirect target: {target.seen.count('/collect')}")
    print(f"loopback requests through the proxy: {len(proxy.seen)}")

    remote = OpenAICompatibleModel(REMOTE, "model", max_tokens=8)
    reply = remote.reply(MESSAGES, [])
    assert reply.text == "ok" and proxy.seen == ["http://remote-host.invalid/v1/chat/completions"]
    print("remote request through the proxy:", proxy.seen[0])
    print("remote reply text:", reply.text)

    reason = refusal(lambda: OpenAICompatibleModel(REMOTE, "model", max_tokens=8, api_key="DUMMY-KEY"))
    print("key over plain http to a remote host:", reason)
    assert len(proxy.seen) == 1, "a request was made for the refused key"
    OpenAICompatibleModel("https://remote-host.invalid/v1", "model", max_tokens=8, api_key="DUMMY-KEY")
    print("key over https to a remote host: accepted, no request made")
    OpenAICompatibleModel(loopback, "model", max_tokens=8, api_key="DUMMY-KEY")
    print("key over http to loopback: accepted")
    reason = refusal(lambda: OpenAICompatibleModel("file:///v1", "model", max_tokens=8))
    print("file URL:", reason)
```

Output:

```text
redirect 302 on loopback: the endpoint answered 302 with a redirect, and the adapter does not follow redirects
redirect 307 on loopback: the endpoint answered 307 with a redirect, and the adapter does not follow redirects
requests to the redirect target: 0
loopback requests through the proxy: 0
remote request through the proxy: http://remote-host.invalid/v1/chat/completions
remote reply text: ok
key over plain http to a remote host: the adapter sends an API key over https, or over http to a loopback host only
key over https to a remote host: accepted, no request made
key over http to loopback: accepted
file URL: the scheme 'file' is not http or https
```

The example also shows each refusal: a redirect, a key over plain `http` to a remote host, and a file address. The redirect's target receives no request, and the other two are refused before any connection is made. Each refusal prints the rule that caused it.

This chapter calls no hosted provider. If you point the adapter at one, use `https`, which a key needs anyway, and bring your own account and key. The book supplies neither, and its examples never call a model or a remote host.

**Working rule:** Parse `function.arguments` as JSON, check the result against the tool's argument model, and send a failure back to the model as a tool result. An endpoint that enforces a strict schema makes such a failure rarer, but the check still runs.

## One loop, several models {#one-loop}

The loop does not change between adapters. It calls `reply()`, reads the calls from the `Reply`, runs the first one, and writes the result into the next step. The adapters differ in where the reply comes from and in what they do with its text, and the loop sees only the `Reply` each one returns.

| Adapter | Where the reply comes from | Calls are read from | Shown by |
| --- | --- | --- | --- |
| `ScriptedModel` | strings written in the code | the text | `same-loop-two-models` |
| `ReplayModel` | the stored replies of one run | the text | `same-loop-two-models`, `replay-byte-for-byte` |
| `LlamaModel` | a local GGUF file, through llama-cpp-python | the text | none; see [the local model](#local-model) |
| `OpenAICompatibleModel` | an HTTP endpoint, on loopback in this book | the structured field if present, else the text | `openai-compatible-loopback`, `adapter-refuses-unsafe-endpoints` |

Each row says what an adapter does, and the last column names the examples that run it. Two examples drive `ScriptedModel` and `ReplayModel` through the loop, and two call `OpenAICompatibleModel`'s `reply()` directly.

Production breaks an adapter in three places, and the reader should know which one they are looking at. The first is the transport. `urllib` raises on an error status, and the adapter does not catch that. The adapter refuses redirects on purpose, so a redirect raises as well. Either way no `Reply` exists for that step, and the run stops with the error. The second is the reply's shape: a reply can parse and still name a tool the loop does not have, and [the name check](#one-name) in chapter 3 refuses it as a tool error. The third is the stored run. If the prompt changes, `replay-byte-for-byte` fails at its first assertion, before any step runs. If a later version of the loop asks a different question at some step, `ReplayModel` raises `ReplayMismatch` at that step, and the message names the step. A malformed tool call from a live model is different again: it is an expected event, and the loop counts it and shows it to the model.

What holds the loop steady is one parser and one `Reply`. Every adapter, live or stored, hands the loop the same fields, the text stays as the model wrote it, and a request hash stored with each reply makes a changed question fail at the step where it changed. The endpoint adapter is the one that touches a network, and its rules are the ones to re-check before it points at a real host: no redirects, no key over plain http, and the proxy for remote URLs only.

Adding a fifth adapter takes three steps. Write a class with a `reply()` method that takes the loop's messages and tools. Build its `Reply` with the same parser the others use, `make_reply` for text or `parse_chat_body` for a response body, so every adapter reads tool calls the same way. Then give it the test that [the protocol section](#model-protocol) describes. The loop does not change, and neither does any other adapter.

**Working rule:** An adapter keeps the raw text and the counts, reads the tool calls in one place, and returns a `Reply`. It never hands the loop an SDK object. Give each adapter a test that calls `reply()` with the loop's arguments, and treat a changed prompt or a changed request as a reason to record again.
