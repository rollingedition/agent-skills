---
title: "Observability for LLM Applications"
chapter: "Find the step that failed"
chapter_id: find-the-failure
book: observability-for-llm-applications
edition: 2026.11.1
verified: 2026-11-23
edition_code: B95K-8RWR
canonical: https://rollingedition.com/observability-for-llm-applications/find-the-failure
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Find the step that failed,” chapter 8 of Observability for LLM Applications, Edition 2026.11.1, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/find-the-failure. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Find the step that failed

By the end of this chapter you can find which step of a message failed, how often, and why, and print each count with the rows it came from. The case puts the question plainly. A user who got no useful answer cannot tell from the log why. The router may have sent the request to the wrong route, or to the fallback reply. The model may have written a tool call the parser cannot read, or a reply cut off at its token cap. The contacts server may have returned an error, or no answer at all. Which of these happened, and how often?

Baseline day 1 answers the how-often question from its real replies. Of its 200 messages, 41 went to the wrong route, and not one span ended in error. Those are the day's real failures. The incident day needs a second kind of count, because we injected its faults: a window in which the contacts server answers too late, one in which the model refuses every request, and one in which the contacts server returns error results. Each injected fault is labelled, and its counts sit in their own rows, never folded into baseline day 1's rates. Every table that prints an injected count repeats the label, and nothing on the incident day is a real outage.

The replays run on the virtual clock of [Replay and the virtual clock](#replay-and-the-virtual-clock). The case's traffic was generated for this book, so the rates here are the book's own and describe no service.

The chapter builds one query per failure mode, from the status a span records to the wrong route.

## How a span records failure {#how-a-span-records-failure}

A span records its outcome in its status. The conventions ask instrumentation to set the status to `Error` when an operation ends with an error, and to leave it unset when nothing went wrong ([recording errors](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/docs/general/recording-errors.md), v1.45.0). The same page asks for `error.type` on a failed operation.

A span's status is unset, ok or error. `error.type` names the error: the class name the package writes, or a registry value where one exists, so failures can be counted by kind. We invent no registry value.

We use one more word for the same thing. An error is a span whose status is ERROR. A message has an error when any of its spans is ERROR. That is the error chapter 10's [the CI gate](#the-ci-gate) counts. Two other bad outcomes are not errors. A reply cut at its token cap is a quality finding, and so is a route reply that names no route. Both are counted below, and neither sets a span's status.

The registry offers few values to choose from. Its fallback is `_OTHER`, and it has no value for a timeout or for an HTTP 429, which are the two failures this chapter meets most. The registry asks for values that are predictable and [low in cardinality](#cardinality), and it lists `timeout` and `500` as examples, not as defined values ([error.md](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/docs/registry/attributes/error.md), v1.45.0). So we write the class name the package raises: `MCPError` for a read timeout, `RateLimitError` for a refused model request, and `ModelUnavailable` for the assistant's own give-up. We write the short class name, where the registry's examples are fully qualified. Other instrumentation writes the qualified one, such as the openai instrumentation's `openai.RateLimitError`, and the assistant's own `exception.type` on the same span is qualified. The injected 429 raises the book's `RateLimitError`, which stands in for the client's exception of that name. The value is therefore the book's, and a deployment that uses the client's own exception will read a different class name in the same place.

An exception is recorded apart from the status. When the OpenTelemetry Python SDK, 1.45.2 in this book, records an exception, it adds an `exception` event to the span and leaves the status unset. The two helpers that wrap a span, `start_as_current_span` and `use_span`, are the exception to that: when an exception escapes them, they also set the status to ERROR by default. The recording-errors page asks for a different place: it says an exception that fails an operation should be recorded as a log record. We recommend keeping the SDK's event while the receiver holds spans. Every query in this chapter reads spans, and the counts depend on the status. A deployment with a log pipeline can take the other route, as long as the status and `error.type` still reach the spans.

Example `error-status-by-step` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Which spans end with ERROR, and what error.type each carries, on the incident day (injected, labelled) and on baseline
day 1 (real). The point rests on the baseline's zero ERROR spans: a wrong route is not a span error, so the status cannot
find it, and the incident's faults look alike from outside."""
from collections import Counter

from lib.dayrun import run_day_traced
from lib.report import fmt_int

real = run_day_traced("2026-12-08", live=False)  # baseline day 1, replayed: no fault is injected into it
real_errors = [row for row in real.spans if row["status"] == "ERROR"]
print("real ERROR spans, baseline day 1 (4B):", fmt_int(len(real_errors)))
assert not real_errors  # the baseline's failures are wrong routes and fallback replies, which set no span status

live = run_day_traced("2026-12-09")  # live: the contacts server runs the injected faults over stdio
rows = live.spans + live.server
errors = [row for row in rows if row["status"] == "ERROR"]
print("ERROR spans, incident day (injected):", fmt_int(len(errors)))
# Each injected fault labels every span it touches, so the label itself tells an injected error from a real one.
assert all(row["attributes"].get("ambrewick.incident.injected") for row in errors)  # every ERROR span is injected
counts = Counter((row["name"], row["attributes"].get("error.type", "none")) for row in errors)
for (name, error_type), count in sorted(counts.items()):
    print(f"{name}, error.type {error_type}, injected: {count}")
```

Output:

```text
real ERROR spans, baseline day 1 (4B): 0
ERROR spans, incident day (injected): 75
MCP send tools/call find_contact, error.type none, injected: 4
chat qwen3-4b-instruct-2507, error.type RateLimitError, injected: 47
contacts.lookup, error.type none, injected: 3
execute_tool find_contact, error.type MCPError, injected: 4
execute_tool find_contact, error.type tool_error, injected: 3
invoke_agent ambrewick-assistant, error.type ModelUnavailable, injected: 11
tools/call find_contact, error.type tool_error, injected: 3
```

Baseline day 1, replayed, has no ERROR span at all, and that zero is the point: a wrong route sets no status. So the day's real failures are not in this table at all, and the rest of the chapter counts them another way. The incident day runs live, so that the contacts server applies its faults. It has 75 ERROR spans, and the example asserts that every one of them carries the injected label.

Read the rows by status first, and by `error.type` second. Some ERROR spans carry no `error.type` at all. The MCP SDK's client span, `MCP send tools/call find_contact`, for a timed-out call is one kind: there are 4 of those. The contacts server's `contacts.lookup` span for an injected crash is the other: 3 of those. The default described above sets ERROR when the crash escapes the span, and nothing sets `error.type`. A count by `error.type` alone would miss both. The other rows are the kinds the later sections explain. Refused model requests carry `RateLimitError`, 47 of them. Messages that got no reply end with a root span that reads `ModelUnavailable`, 11. The contacts calls that failed appear under three names: `execute_tool find_contact` on the assistant's attempt, `MCP send tools/call find_contact` on the client span, and `tools/call find_contact` on the server's span. The sections on timeouts and error results read each one.

**Working rule:** Count failures by span status, and print each `error.type` beside its count. A span with no `error.type` is still an error, so never filter on the attribute to find failures. Keep real and injected counts in separate rows, and label each injected row where it appears.

## Replies cut at the cap {#replies-cut-at-the-cap}

The status rule in [the first section](#how-a-span-records-failure) catches a failure that raises, and a reply cut at its token cap raises nothing. Some replies stop because the model reached that cap, not because it finished. The assistant records the runtime's finish reason in `gen_ai.response.finish_reasons`, an array with one entry per generation, in the order of the generation's choices. The finish reason says why the model stopped: on its own (`stop`) or at the token cap (`length`). The GenAI conventions, at 0.1.0, define the inference span's values in the same terms: an interrupted generation reports the provider's reason or `interrupted`, and `error` is reported when a reason was expected and not received ([client inference span](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/client-inference.md), note 18). So a `length` reply is not an error, and we do not count it as one. [The agent harnesses' finish reason](https://rollingedition.com/concepts/large-language-models/finish-reason) is the same idea.

Two facts about this runtime shape the check. First, it never reports `tool_calls`. A model's tool call comes back as text inside the reply, and the finish reason stays `stop`, so the finish reason cannot show a tool call. The next section deals with that case. Second, the answer step has a cap of 160 tokens. The cap is the same in every release and recording. It was set once, before any recording this book reads, and no recording was edited to produce a cut.

Example `truncated-replies` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Which model replies the runtime cut at its token cap, read from the finish reason the runtime recorded for each
request: baseline day 1 (the 4B, release r0) and the model swap (the 0.6B, release r2). A cut reply has finish reason
length. The runtime never reports tool_calls, so a reply with a tool call is not found this way (malformed-tool-calls)."""
import json
from collections import Counter

from lib.dayrun import DATA, run_day_traced
from lib.report import fmt_int


def finish_reasons(recording):
    """The finish reason of every model request in one recording, counted by step and reason."""
    rows = [json.loads(line) for line in (DATA / recording / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    return [row for row in rows if row["kind"] == "model"], Counter(
        (row["step"], row["finish_reason"]) for row in rows if row["kind"] == "model")

base_rows, base = finish_reasons("baseline-day-1")
for step in ("route", "answer"):
    print(f"baseline day 1, {step} requests, finish reason stop: {fmt_int(base[(step, 'stop')])}")
    print(f"baseline day 1, {step} requests, finish reason length: {fmt_int(base[(step, 'length')])}")
# The replay answers from the same recording, and its chat spans carry the finish reason in an array.
replayed = run_day_traced("2026-12-08", live=False).spans
chat = [row for row in replayed if row["name"].startswith("chat")]
reasons = Counter(reason for row in chat for reason in row["attributes"]["gen_ai.response.finish_reasons"])
print(f"baseline day 1, chat spans replayed with finish reason stop: {fmt_int(reasons['stop'])}")
assert reasons["length"] == 0 and reasons["stop"] == len(base_rows)  # the replay's spans match the recording

swap_rows, swap = finish_reasons("release-model-swap")
manifest = json.loads((DATA / "release-model-swap" / "manifest.json").read_text(encoding="utf-8"))
for step in ("route", "answer"):
    print(f"model swap (0.6B, release r2), {step} requests, finish reason length: {fmt_int(swap[(step, 'length')])}")
cut = [row for row in swap_rows if row["finish_reason"] == "length"]
print(f"model swap, answer cap in tokens: {manifest['answer_max_tokens']}")
print(f"model swap, cut answer, completion tokens: {cut[0]['completion_tokens']}")
assert len(cut) == 1 and cut[0]["step"] == "answer"  # one cut reply, and it is an answer
assert cut[0]["completion_tokens"] == manifest["answer_max_tokens"]  # cut at the cap, not at a stop token
```

Output:

```text
baseline day 1, route requests, finish reason stop: 200
baseline day 1, route requests, finish reason length: 0
baseline day 1, answer requests, finish reason stop: 121
baseline day 1, answer requests, finish reason length: 0
baseline day 1, chat spans replayed with finish reason stop: 321
model swap (0.6B, release r2), route requests, finish reason length: 0
model swap (0.6B, release r2), answer requests, finish reason length: 1
model swap, answer cap in tokens: 160
model swap, cut answer, completion tokens: 160
```

No reply from the 4B reached the cap. Its 200 route replies and 121 answers all stopped on their own, and the replay's chat spans carry the same reasons: 321 of them, all `stop`.

The model-swap release runs Qwen3-0.6B, and it adds `/no_think` to its prompt, so its differences from baseline day 1 come from the smaller model and the suffix together. Here the cut shows up. None of its route replies was cut, and its answer step cut 1 reply, at 160 tokens, which is the cap.

That cut reply is a quality finding. The span is not an error, and the user receives a reply that stopped short. We file it under quality and read the text before deciding what it means.

**Working rule:** Count the `length` finish reasons for each step on every release, before you call its replies complete, and print the cap beside the count. A zero on one recording says nothing about another. Read a cut reply as a quality finding, and never file it as an error.

## Tool calls that do not parse {#tool-calls-that-do-not-parse}

When the model wants a tool, it writes a `<tool_call>` block into its reply, and the assistant reads the block back. The runtime's finish reason cannot show a bad block, because a reply with a broken block still stops on its own. A malformed call is found only by parsing the reply. A block with no closing tag is malformed. So is a body that is not JSON, a call with no name, or one whose arguments are not an object. Each malformed call is counted once on its message, and the assistant tells the model that the call could not be read and asks it to answer without a tool.

A different failure reaches the tool itself. A call can parse and still fail the argument model of its tool. That is not a malformed reply. The tool attempt ends ERROR, with `error.type` set to the class `ValidationError`, and [the query section](#querying-each-failure-mode) counts those among the tool attempts.

Example `malformed-tool-calls` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Which answer replies carry a tool call the parser cannot read, on baseline day 1 (the 4B) and the model swap (the 0.6B).
A malformed call is found by parsing the reply, because its finish reason is stop either way. The constructed replies
at the end are not recorded and never become spans: they show that the parser rejects what it should."""
import glob
import json
from pathlib import Path

from lib.assistant import MalformedToolCall, parse_tool_call
from lib.dayrun import DATA, run_day_traced
from lib.report import fmt_int


def check_answers(recording):
    """Parse every answer reply in one recording. Returns the reply count, the replies with a tool call, and the
    message IDs whose reply the parser rejects."""
    paths = sorted(glob.glob(str(DATA / recording / "calls" / "*.json")))
    calls = [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]
    answers = sorted((call for call in calls if call["kind"] == "model" and call["step"] == "answer"),
                     key=lambda call: call["seq"])  # the recorder's sequence number, unique per request
    tool_calls, rejected = 0, []
    for call in answers:
        try:
            tool_calls += parse_tool_call(call["text"]) is not None
        except MalformedToolCall:
            rejected.append(call["message_id"])
    return len(answers), tool_calls, rejected


answers, tool_calls, rejected = check_answers("baseline-day-1")
print(f"baseline day 1 (4B), answer replies: {fmt_int(answers)}")
print(f"baseline day 1 (4B), replies with a tool call: {fmt_int(tool_calls)}")
print(f"baseline day 1 (4B), malformed tool calls: {fmt_int(len(rejected))}")
# The replay parses the same recorded texts with the same parser, so its count should agree with the parse above.
replayed = sum(run.outcome.malformed_tool_calls for run in run_day_traced("2026-12-08", live=False).runs)
print(f"baseline day 1 (4B), malformed tool calls in the replay: {fmt_int(replayed)}")
assert not rejected and replayed == 0

answers, tool_calls, rejected = check_answers("release-model-swap")
print(f"model swap (0.6B, release r2), answer replies: {fmt_int(answers)}")
print(f"model swap (0.6B, release r2), replies with a tool call: {fmt_int(tool_calls)}")  # one call tests nothing
print(f"model swap (0.6B, release r2), malformed tool calls: {fmt_int(len(rejected))}")
assert not rejected

# Constructed, not recorded: two replies a model could write, passed straight to the parser.
for label, text in {"unclosed block": '<tool_call>{"name": "find_contact", "arguments": {}',
                    "body is not JSON": "<tool_call>find the contact</tool_call>"}.items():
    try:
        parse_tool_call(text)
        raise AssertionError(f"{label} was not rejected")
    except MalformedToolCall:
        print(f"constructed reply, {label}, rejected by the parser: yes")
```

Output:

```text
baseline day 1 (4B), answer replies: 121
baseline day 1 (4B), replies with a tool call: 10
baseline day 1 (4B), malformed tool calls: 0
baseline day 1 (4B), malformed tool calls in the replay: 0
model swap (0.6B, release r2), answer replies: 57
model swap (0.6B, release r2), replies with a tool call: 1
model swap (0.6B, release r2), malformed tool calls: 0
constructed reply, unclosed block, rejected by the parser: yes
constructed reply, body is not JSON, rejected by the parser: yes
```

No recorded reply on baseline day 1 held a broken block. The 4B wrote 121 answer replies, 10 of which carried a tool call, and the parser rejected 0 of them. The replay's outcome, which counts parse failures and schema rejections together, finds 0, which agrees.

The model-swap release, Qwen3-0.6B with `/no_think` on its prompt, wrote 57 answers, and only 1 of them carried a tool call. That call parsed. One call tests nothing about a small model's tool use, so this section makes no claim about it.

Neither recording holds a broken block. To show what the parser refuses, we pass two replies written for this chapter straight to it, and it rejects both. The replies were never recorded and never become spans, rows or recordings, so they say nothing about the recorded day.

The receiver cannot find a parse failure, though. A malformed reply raises inside the assistant and is counted on the message's outcome, and no span records it as an error. The count above therefore comes from the replies. [The query section](#querying-each-failure-mode) says what the receiver can and cannot show.

**Working rule:** Parse every reply that could carry a tool call, and count malformed replies with the parser's own count, never with a finish reason. Print the replies that carry a call beside that count, so a reader can see how small a sample of tool use it is.

## Retries under a timeout {#retries-under-a-timeout}

The status rule in [the first section](#how-a-span-records-failure) catches a failure that raises, and the first injected fault is one: a timeout raises across the process boundary. The contacts server is a separate process, and `find_contact` runs there, so its failures reach the assistant as the MCP SDK raises them. We injected this fault into the incident day. Between 13:00 and 13:12 UTC, the contacts server answers `find_contact` only after the client's read timeout of 2,000.0 ms, and the client gives up. The tool wrapper waits and tries once more. [Chapter 4](#errors-across-the-boundary) explains how the SDK raises that timeout as an exception and not as a reply.

A retry is another attempt at a failed call, recorded as its own span. We recommend one span per attempt, and we record each attempt of a tool call as its own `execute_tool` span, with an `ambrewick.attempt` number. A failed attempt is therefore an ERROR span, and the call's success appears on the attempt that succeeded. No span describes the whole call. [Chapter 4's choice](#errors-across-the-boundary) gives the reason, and the first attempt's timeout is one of the failures the user's message met, so it counts.

Example `retries-under-incident` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""What each injected window does to the calls it covers, on the incident day, run live so the contacts server applies its
faults. A timed-out find_contact is two attempts that end ERROR with MCP code -32001, the retry starting after the read
timeout and the retry delay; a refused model request is retried on the assistant's backoff. Every line here is labelled
with its window: injected, not a natural rate."""
import tomllib

from lib import inject
from lib.case import CASE_DIR
from lib.dayrun import run_day_traced
from lib.report import fmt_int, fmt_ms
from lib.tools import REQUEST_TIMEOUT_NS, RETRY_DELAY_NS

live = run_day_traced("2026-12-09")
# Spans carry no message ID, so each message is found by its trace: the root spans come in arrival order, as the runs do.
roots = sorted((row for row in live.spans if row["name"].startswith("invoke_agent")), key=lambda row: row["trace_seq"])
message_of = {root["trace_id"]: run.message.message_id for root, run in zip(roots, live.runs, strict=True)}
windows = {incident.incident_id: incident for incident in inject.load_incidents()}
schedule = {row["id"]: row for row in tomllib.loads((CASE_DIR / "incidents.toml").read_text(encoding="utf-8"))["incident"]}
finds = [row for row in live.spans if row["name"] == "execute_tool find_contact"]
refused = [row for row in live.spans if row["attributes"].get("error.type") == "RateLimitError"]


def inside(name, row):
    """Whether a span starts inside the named window (the window's virtual start, inclusive, to its end)."""
    return windows[name].start_ns <= row["start_ns"] < windows[name].end_ns


def say(name, label, value):
    """Print one labelled value for a window."""
    print(f"{name} (injected), {label}: {value}")


TIMEOUT = "inc-contacts-timeout"
# The schedule's stamps read 2026-12-09T13:00:00.000000Z, so characters 11 to 16 hold the UTC clock time.
say(TIMEOUT, "window start (UTC)", schedule[TIMEOUT]["start"][11:16])
say(TIMEOUT, "window end (UTC)", schedule[TIMEOUT]["end"][11:16])
timeouts = sorted((row for row in finds if inside(TIMEOUT, row)
                   and row["attributes"].get("error.type") == "MCPError"), key=lambda row: row["start_ns"])
assert all(row["status"] == "ERROR" and row["attributes"]["ambrewick.mcp.error_code"] == -32001 for row in timeouts)
assert all(row["end_ns"] - row["start_ns"] == REQUEST_TIMEOUT_NS for row in timeouts)  # each attempt waits the read timeout
say(TIMEOUT, "attempts that time out", fmt_int(len(timeouts)))
say(TIMEOUT, "MCP error code", timeouts[0]["attributes"]["ambrewick.mcp.error_code"])
say(TIMEOUT, "read timeout", fmt_ms(REQUEST_TIMEOUT_NS))
pairs = [(a, b) for a, b in zip(timeouts, timeouts[1:]) if a["trace_id"] == b["trace_id"]]
assert all(b["start_ns"] - a["start_ns"] == REQUEST_TIMEOUT_NS + RETRY_DELAY_NS for a, b in pairs)
say(TIMEOUT, "retries", fmt_int(len(pairs)))
say(TIMEOUT, "retry wait", fmt_ms(RETRY_DELAY_NS))
say(TIMEOUT, "retry starts after the first attempt", fmt_ms(pairs[0][1]["start_ns"] - pairs[0][0]["start_ns"]))

errors = [row for row in finds if inside("inc-mcp-error", row)]
say("inc-mcp-error", "retries", fmt_int(sum(row["attributes"]["ambrewick.attempt"] > 1 for row in errors)))

replied = [run for run in live.runs if run.outcome.source == "model" and run.message.message_id in schedule["inc-rate-limit"]["message_ids"]]
retried = [run for run in replied if any(message_of[row["trace_id"]] == run.message.message_id for row in refused)]
say("inc-rate-limit", "messages that got a reply after a refused attempt", fmt_int(len(retried)))
assert len(retried) == len(replied)  # every reply in the window came after a refusal
```

Output:

```text
inc-contacts-timeout (injected), window start (UTC): 13:00
inc-contacts-timeout (injected), window end (UTC): 13:12
inc-contacts-timeout (injected), attempts that time out: 4
inc-contacts-timeout (injected), MCP error code: -32001
inc-contacts-timeout (injected), read timeout: 2,000.0 ms
inc-contacts-timeout (injected), retries: 2
inc-contacts-timeout (injected), retry wait: 500.0 ms
inc-contacts-timeout (injected), retry starts after the first attempt: 2,500.0 ms
inc-mcp-error (injected), retries: 0
inc-rate-limit (injected), messages that got a reply after a refused attempt: 1
```

Here the incident day runs live, so the contacts server applies the fault, and each span is grouped by its window. Every line names its window and says injected. In the timeout window, the timed-out attempts were 4. Each ends ERROR, with `error.type` `MCPError` and the MCP code on `ambrewick.mcp.error_code`. The code is -32001, the SDK's name for a read timeout and not a protocol code, as [chapter 4](#errors-across-the-boundary) says. The retries were 2. Both timed-out messages' retries timed out too, so the tool returned its timed-out reply to the model. Each second attempt starts 2,500.0 ms after its first, which is the read timeout plus the wait before the retry.

The model's window works the same way, but its failures are refusals. Every model request in the window is answered with a 429, and the assistant retries with a backoff. Each refused attempt is a zero-length chat span, ERROR, with `error.type` `RateLimitError`, and the injected window refused 47 requests. Once the backoff runs out, the message ends with no reply: 11 messages did. One message got a reply after a refused attempt, which is 1. By the span rule, that message counts as an error, although its user got the reply. The count follows the spans. [The production section](#find-the-failure-in-production) says what that does to a rate.

**Working rule:** Count a failed attempt as a failure even when the call later succeeds, and name its window before you count it as injected.

## MCP errors {#mcp-errors}

The contacts server has a second way to fail, and it raises nothing. The MCP tools specification says that a tool's own failure comes back as a result with `isError` set, and not as a protocol error ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools), revision 2026-07-28). The MCP Python SDK, 2.3.0 in this book, follows that rule. The injected `mcp-error` window makes every `find_contact` call in its window come back as an error result, and the client hands the result back to the assistant as a reply.

An error result is not an exception, so there is no exception to name. The attempt ends ERROR with `error.type` `tool_error`, the value that the MCP conventions define for an `isError` result ([MCP conventions](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/mcp.md), v0.1.0). Its status description reads "find_contact returned an error result". No exception event is written, and no retry follows.

The incident day's rows show the three records. The assistant recorded 3 attempts as `tool_error`, and the server recorded the same calls as `tool_error` too, 3 of them. The window's retries line reads 0, so none of these attempts was retried. The contacts server's `contacts.lookup` span is also ERROR for these calls, and it carries no `error.type`. The conventions ask for `tool_error` on the client span too, and for `error.type` on any failed client span, the exception's class name for a timeout. The MCP SDK at 2.3.0 departs from both: its client span for an error result stays unset, and its span for a timeout is ERROR with no `error.type`. The only client-side ERROR rows in [the first table](#how-a-span-records-failure) are the 4 timeouts.

One injected fault therefore leaves three ERROR records. A count of spans by status counts it three times. The failure a user's message met is the attempt, because that is the operation the message's own call made. The server's spans are the cause, and they join the message's trace through the context that [chapter 4](#traceparent-in-meta) propagates. The [query section](#querying-each-failure-mode) pairs each error-result attempt with the server span in its trace: 3 pairs.

**Working rule:** Count a failed operation once, on the span the caller made, and read the server's span beside it for the cause. With the MCP SDK at this version, expect the client's span to stay unset for an error result, though the conventions ask for `tool_error`; count by the caller's attempt either way.

## Wrong routes against the labels {#wrong-routes-against-labels}

A wrong route is the one failure with no error anywhere in the trace. The call succeeds, its reply stops on its own, and the answer is a fallback reply, or a tool route the message did not need. To find it, the book needs a source of truth, and the case has one. MASSIVE labels each utterance with a scenario. The scenario table maps each scenario to one route, and the routes are `calendar`, `alarms`, `lists`, `messages`, `devices`, `media` and `fallback`. A scenario goes to the route whose tool or articles resolve it, and to `fallback` only when no tool and no article do. A wrong route is a routed choice that differs from the table's. The router writes its choice on the route span, and the check event on that span holds the table's answer, so the trace records whether the route was right.

The fallback reply is defined in [chapter 1](#where-the-time-went-in-twenty-messages). The table adds the rule for when it is the right answer. It is right for a message that no tool or article resolves, and for no other message. A fallback reply to any other scenario is a wrong route that the user sees as a refusal. The check is code, and it reads the trace, not the reply's text. Judging whether an answer is right is a separate job, and [Evaluating LLM Applications](https://rollingedition.com/concepts/llm-evaluation/code-check) covers the checks that read a reply.

The dev day shows the case in small. Of its 20 messages, 5 were routed wrong, and 3 of those got the fallback reply for a scenario that needed a tool or an article.

Example `wrong-routes-by-label` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""How often the router chose a route other than the scenario table's, on baseline day 1 (the 4B), the same messages under
the 0.6B (the model swap, from its recorded route replies) and the dev day. Each message's check event on its route span
holds the table's answer; the 0.6B's replies are read with the same parser. The interval is a bootstrap over messages."""
import json
from fractions import Fraction

from lib.assistant import parse_route
from lib.case import load_messages, scenario_to_route
from lib.dayrun import DATA, run_day, run_day_traced
from lib.report import fmt_int, fmt_share
from lib.stats import bootstrap_interval


def recorded_routes(recording, day):
    """(expected, chosen) for each route reply in one recording, in order. A reply that names no route is the fallback."""
    messages = {message.message_id: message for message in load_messages(day)}
    paths = sorted((DATA / recording / "calls").glob("*.json"))
    calls = sorted((json.loads(path.read_text(encoding="utf-8")) for path in paths), key=lambda call: call["seq"])
    return [(scenario_to_route(messages[c["message_id"]].scenario), parse_route(c["text"]) or "fallback")
            for c in calls if c["kind"] == "model" and c["step"] == "route"]


traced = run_day_traced("2026-12-08", live=False)
runs = traced.runs
# The check event is on each route span: the trace itself says whether the route was correct.
checks = [event["attributes"] for row in traced.spans for event in row["events"] if event["name"] == "ambrewick.check"]
wrong = [run.outcome.route != run.outcome.expected_route for run in runs]
assert len(checks) == len(runs) and sum(not check["ambrewick.route.correct"] for check in checks) == sum(wrong)
print(f"baseline day 1 (4B), messages: {fmt_int(len(runs))}")
RESAMPLES = 2000
low, high = bootstrap_interval(wrong, lambda units: Fraction(sum(units), len(units)), n=RESAMPLES)
print(f"bootstrap resamples of messages, baseline day 1: {fmt_int(RESAMPLES)}")
print(f"wrong routes, baseline day 1, 95% interval: {fmt_share(low.numerator, low.denominator)} to {fmt_share(high.numerator, high.denominator)}")
for route in sorted({run.outcome.expected_route for run in runs}):
    print(f"{route}, wrong routes of {fmt_int(sum(run.outcome.expected_route == route for run in runs))} messages: "
          f"{fmt_int(sum(run.outcome.route != route for run in runs if run.outcome.expected_route == route))}")
print("fallback replies to a scenario that is not fallback, baseline day 1: "
      f"{fmt_int(sum(run.outcome.route == 'fallback' and run.outcome.expected_route != 'fallback' for run in runs))}")

# The same messages under the 0.6B, from its recorded replies; the 4B's recorded replies must give the replay's count.
base = recorded_routes("baseline-day-1", "2026-12-08")
assert sum(expected != chosen for expected, chosen in base) == sum(wrong)
swap = recorded_routes("release-model-swap", "2026-12-08")
print(f"wrong routes, model swap (0.6B, release r2): {fmt_int(sum(e != c for e, c in swap))} of {fmt_int(len(swap))} messages")
print("fallback replies to a scenario that is not fallback, model swap: "
      f"{fmt_int(sum(c == 'fallback' and e != 'fallback' for e, c in swap))}")

# The dev day's 20 messages, for chapter 1's fallback replies, checked against the same table.
dev = run_day("2026-12-07")
print(f"dev day, messages: {fmt_int(len(dev))}")
print(f"wrong routes, dev day (20 messages): {fmt_int(sum(run.outcome.route != run.outcome.expected_route for run in dev))}")
print(f"fallback replies to a scenario that is not fallback, dev day: {fmt_int(sum(run.outcome.route == 'fallback' and run.outcome.expected_route != 'fallback' for run in dev))}")
```

Output:

```text
baseline day 1 (4B), messages: 200
bootstrap resamples of messages, baseline day 1: 2,000
wrong routes, baseline day 1, 95% interval: 15.0% to 26.5%
alarms, wrong routes of 6 messages: 0
calendar, wrong routes of 42 messages: 16
devices, wrong routes of 17 messages: 1
fallback, wrong routes of 82 messages: 11
lists, wrong routes of 7 messages: 0
media, wrong routes of 29 messages: 3
messages, wrong routes of 17 messages: 10
fallback replies to a scenario that is not fallback, baseline day 1: 18
wrong routes, model swap (0.6B, release r2): 83 of 200 messages
fallback replies to a scenario that is not fallback, model swap: 68
dev day, messages: 20
wrong routes, dev day (20 messages): 5
fallback replies to a scenario that is not fallback, dev day: 3
```

On baseline day 1 the 4B routed 41 of its messages wrong. The 95% interval runs from 15.0% to 26.5%, from 2,000 resamples of messages.

For one day of 200 messages that interval is wide, and the rate should be read with it. Of the wrong routes, 18 were fallback replies to scenarios that needed a tool or an article. The rest went to a tool route.

The routes differ a great deal. Of the messages whose scenario belongs to the messages route, 10 of 17 were wrong, and every one of them was a fallback reply. Calendar was the other large case: 16 of 42 were wrong.

The fallback scenarios show the opposite error. They went to a tool route 11 times, out of 82. The alarms and lists routes had no wrong routes at all, but with 6 and 7 messages, those zeros say little.

The model-swap release routed 83 of 200 messages wrong, and 68 of those were fallback replies to scenarios that needed a tool or an article. The two releases answer the same 200 messages. Its prompt also carries `/no_think`, so the difference from the 4B is the smaller model and the suffix together.

Example `figure-failure-modes-by-route` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Draw, for each scenario route on baseline day 1, how many of its messages the router sent right, to another tool route,
or to the fallback reply. The failing modes are coloured; the modes with no count on this day (truncated replies,
malformed tool calls) are printed as zero and named in the caption. Every value the figure draws is printed first."""
from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int

traced = run_day_traced("2026-12-08", live=False)  # the 4B's real replies, replayed from the recording
runs = traced.runs
malformed = sum(run.outcome.malformed_tool_calls for run in runs)  # calls the parser rejected
truncated = sum("length" in row["attributes"]["gen_ai.response.finish_reasons"]  # replies cut at the cap
                for row in traced.spans if row["name"].startswith("chat"))
assert malformed == 0 and truncated == 0
rows = []
for route in sorted({run.outcome.expected_route for run in runs}):
    group = [run for run in runs if run.outcome.expected_route == route]
    right = sum(run.outcome.route == route for run in group)
    fallback = sum(run.outcome.route == "fallback" and route != "fallback" for run in group)
    other = len(group) - right - fallback
    assert right + fallback + other == len(group)
    rows.append((route, len(group), right, other, fallback))
    print(f"route {route}, messages (n): {fmt_int(len(group))}")
    print(f"route {route}, routed right: {fmt_int(right)}")
    print(f"route {route}, wrong, to another tool route: {fmt_int(other)}")
    print(f"route {route}, wrong, to the fallback reply: {fmt_int(fallback)}")
print(f"truncated replies, baseline day 1: {fmt_int(truncated)}")
print(f"malformed tool calls, baseline day 1: {fmt_int(malformed)}")

fig, ax = new_figure(height=3.4)
ys = list(range(len(rows)))[::-1]  # the first route at the top
for y, (route, n, right, other, fallback) in zip(ys, rows):
    ax.barh(y, right, color=MUTED, alpha=0.35, label="routed right" if y == ys[0] else None)
    ax.barh(y, other, left=right, color=INK, label="wrong, to another tool route" if y == ys[0] else None)
    ax.barh(y, fallback, left=right + other, color=ACCENT, label="wrong, to the fallback reply" if y == ys[0] else None)
ax.set_xlim(0, 1.12 * max(right + other + fallback for _, _, right, other, fallback in rows))   # headroom so the longest bar is not clipped
ax.set_yticks(ys, [f"{route} (n = {n})" for route, n, *_ in rows])
ax.set_xlabel("messages on baseline day 1")
ax.legend(loc="lower right", frameon=False)
save(fig, "failure-modes-by-route")
```

Output:

```text
route alarms, messages (n): 6
route alarms, routed right: 6
route alarms, wrong, to another tool route: 0
route alarms, wrong, to the fallback reply: 0
route calendar, messages (n): 42
route calendar, routed right: 26
route calendar, wrong, to another tool route: 12
route calendar, wrong, to the fallback reply: 4
route devices, messages (n): 17
route devices, routed right: 16
route devices, wrong, to another tool route: 0
route devices, wrong, to the fallback reply: 1
route fallback, messages (n): 82
route fallback, routed right: 71
route fallback, wrong, to another tool route: 11
route fallback, wrong, to the fallback reply: 0
route lists, messages (n): 7
route lists, routed right: 7
route lists, wrong, to another tool route: 0
route lists, wrong, to the fallback reply: 0
route media, messages (n): 29
route media, routed right: 26
route media, wrong, to another tool route: 0
route media, wrong, to the fallback reply: 3
route messages, messages (n): 17
route messages, routed right: 7
route messages, wrong, to another tool route: 0
route messages, wrong, to the fallback reply: 10
truncated replies, baseline day 1: 0
malformed tool calls, baseline day 1: 0
figure: figures/failure-modes-by-route.svg
```

Figure 8.1 draws the same messages by route. Each bar is an expected route from the scenario table, and it holds that route's messages, split into the ones routed right, the ones wrong to another tool route, and the ones wrong to the fallback reply. Most wrong routes sit in the calendar, fallback and messages bars. Two modes count zero on this day, truncated replies and malformed tool calls, and the figure does not draw them. Chapter 7 counts the same day's messages by the route the assistant chose, not the expected one, so its counts differ: 7 messages and 31 media there, against 17 and 29 here.

*Figure 8.1. Each route's messages on baseline day 1: routed right, wrong to a tool route, or wrong to the fallback reply.*

![Horizontal bars for the seven routes on baseline day 1: most messages are routed right, and most wrong routes sit in the calendar, fallback and messages bars, with the fallback scenarios' misroutes going to tool routes](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.1/figures/failure-modes-by-route.svg)

**Working rule:** Check each route against the scenario table on the trace, count fallback replies to other scenarios apart from the other wrong routes, and print every rate with its interval. Compare two releases only on the same messages, and name any suffix or prompt change beside the comparison.

## Querying each failure mode {#querying-each-failure-mode}

Each failure mode gets one query over the receiver's rows, and the receiver keeps each day in its own file. The baseline and the incident day are kept apart, so an injected row never sits in a real count. [The receiver](#the-book-receiver) holds the same rows the assistant's export writes, as chapter 5 shows.

Example `failure-modes-query` (Python 3.13.16 · bm25s 0.3.16 · duckdb 2.0.0 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""One query per failure mode over the stored rows: baseline day 1 (real) and the incident day (injected, labelled), each
kept in its own receiver file. The baseline's real failures are wrong routes and fallback replies; its span errors and
truncated replies print zero. A receiver holds spans only, so no query here counts a parse failure."""
import tempfile

from lib import query
from lib.dayrun import run_day_traced
from lib.export import write_jsonl
from lib.report import fmt_int

folder = tempfile.mkdtemp()
baseline = run_day_traced("2026-12-08", live=False)
write_jsonl(f"{folder}/baseline.jsonl", baseline.spans)
incident = run_day_traced("2026-12-09")  # live: the contacts server's rows go to the incident day's receiver
write_jsonl(f"{folder}/incident.jsonl", incident.spans + incident.server)
base, inc = query.connect(f"{folder}/baseline.jsonl"), query.connect(f"{folder}/incident.jsonl")

# A check event sits in the event list of its route span; the route the span chose is in the span's own attributes.
WRONG = """SELECT count(*) FROM spans, UNNEST(from_json(events, '["json"]')) AS t(e)
  WHERE json_extract_string(e, '$.name') = 'ambrewick.check'
  AND json_extract_string(e, '$.attributes."ambrewick.route.correct"') = 'false'"""
FALLBACK = """SELECT count(*) FROM spans, UNNEST(from_json(events, '["json"]')) AS t(e)
  WHERE json_extract_string(e, '$.name') = 'ambrewick.check'
  AND json_extract_string(e, '$.attributes."ambrewick.route.correct"') = 'false'
  AND json_extract_string(attributes, '$."ambrewick.route"') = 'fallback'
  AND json_extract_string(e, '$.attributes."ambrewick.route.expected"') != 'fallback'"""
TRUNCATED = """SELECT count(*) FROM spans WHERE name LIKE 'chat %'
  AND json_extract_string(attributes, '$."gen_ai.response.finish_reasons"') LIKE '%length%'"""
# Each error-result attempt joined to the contacts server's tools/call span in the same trace: one pair per injected error.
PAIRED = """SELECT count(*) FROM spans AS a JOIN spans AS s ON s.trace_id = a.trace_id
  WHERE a.name LIKE 'execute_tool %' AND s.name LIKE 'tools/call %'
  AND a.status = 'ERROR' AND json_extract_string(a.attributes, '$."error.type"') = 'tool_error'
  AND s.status = 'ERROR' AND json_extract_string(s.attributes, '$."error.type"') = 'tool_error'"""
# Errors on tool attempts and on the contacts server's spans, one row per span name and error.type, with a tie-break.
ERRORS = """SELECT name, json_extract_string(attributes, '$."error.type"') AS error_type, count(*) AS n FROM spans
  WHERE status = 'ERROR' AND (name LIKE 'execute_tool %' OR name LIKE 'tools/call %')
  GROUP BY name, error_type ORDER BY n DESC, name, error_type"""
REFUSED = """SELECT count(*) FROM spans WHERE json_extract_string(attributes, '$."error.type"') = 'RateLimitError'"""

def one(connection, sql):
    return connection.execute(sql).fetchone()[0]


print("wrong routes, baseline day 1 (real):", fmt_int(one(base, WRONG)))
print("wrong routes, incident day (real):", fmt_int(one(inc, WRONG)))
print("fallback replies to a scenario that is not fallback, baseline day 1 (real):", fmt_int(one(base, FALLBACK)))
print("truncated replies, baseline day 1 (real):", fmt_int(one(base, TRUNCATED)))
print("ERROR tool-attempt and server spans, baseline day 1 (real):", fmt_int(sum(n for *_, n in base.execute(ERRORS).fetchall())))
for name, error_type, n in inc.execute(ERRORS).fetchall():
    print(f"{name}, error.type {error_type}, incident day (injected): {fmt_int(n)}")
print("error-result attempts paired with their server span, incident day (injected):", fmt_int(one(inc, PAIRED)))
print("model requests refused, incident day (injected):", fmt_int(one(inc, REFUSED)))
```

Output:

```text
wrong routes, baseline day 1 (real): 41
wrong routes, incident day (real): 13
fallback replies to a scenario that is not fallback, baseline day 1 (real): 18
truncated replies, baseline day 1 (real): 0
ERROR tool-attempt and server spans, baseline day 1 (real): 0
execute_tool find_contact, error.type MCPError, incident day (injected): 4
execute_tool find_contact, error.type tool_error, incident day (injected): 3
tools/call find_contact, error.type tool_error, incident day (injected): 3
error-result attempts paired with their server span, incident day (injected): 3
model requests refused, incident day (injected): 47
```

The baseline's real failures come out as wrong routes, 41, and fallback replies to scenarios that needed a tool or an article, 18. The incident day's 13 wrong routes are real route choices by the model, not injected faults. The injected faults add none: a refused route attempt is retried on the same recorded reply, and a message that gives up has no check event to compare, so the injected windows add no wrong route. This chapter prints no rate for that day.

The other modes come out at zero on the baseline. Truncated replies: 0. The baseline has no cut reply, so this zero is untested here: the query has not been run on a day with the mode. Tool attempts and server spans with ERROR: 0. The true count of malformed tool calls on baseline day 1 is zero, counted from the replies in [the section on tool calls that do not parse](#tool-calls-that-do-not-parse), and the receiver holds nothing to query.

On the incident day, the same tool query finds the injected attempts: 4 timeouts on the attempt, 3 error results on the attempt, and 3 on the contacts server's span for the same calls. The refused model requests come to 47. Each of these is labelled injected in the output, and each sits in the incident day's file.

**Working rule:** Write one query for each failure mode, name the attribute or event it reads, and run it on a day that has the mode before you trust its zero. A query on an attribute that no span carries returns zero on every day, and that zero is a bug in the query, not a rate.

## Failures in production {#find-the-failure-in-production}

Production will not look like the incident day. The faults here are placed by the case, so each one can be matched to a window afterwards. A real fault has no label. A count by window is then a count of times that someone chose after the fact, and it is only as good as the record of the incident's start and end. Keep that record next to the counts, as the case's incidents file does, and say which counts came from it.

Other libraries will set status their own way. A client span can read ERROR with no `error.type`, as the MCP SDK's span does for a timeout in [the first table](#how-a-span-records-failure). Count failures by status first, and treat `error.type` as a label added to each count, not as a condition for being one. Retries inside a client library need care too. The openai client at 3.56.0 retries inside one call by default (`max_retries`), so instrumentation around that call writes one span, and the refusals it retried never become spans, so the span rule cannot count them. To see them, set `max_retries=0` and retry in your own code, as this book does.

Retries in your own code need attributes of their own. The HTTP conventions define `http.request.resend_count` for resent HTTP requests ([HTTP spans](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/docs/http/http-spans.md), v1.45.0). That attribute does not describe an MCP call, so this book's retry carries `ambrewick.attempt`. Choose an attribute that names the attempt in whatever protocol your call uses.

Finally, the span rule counts a message that recovered. A message whose first model request was refused and whose later request got a reply counts as an error, as [the retry section](#retries-under-a-timeout) shows. Chapter 10's gate counts the recovered message as an error. Chapter 9's objective counts what the user saw, so a message that got a reply after a retry is not a failure there ([service-level objectives](#service-level-objectives)). A message whose first tool attempt timed out and whose retry succeeded would count too. On the incident day that case did not occur, since the retries of both timed-out messages timed out as well. If the two numbers would tell different stories in your system, measure both, and print each with the rule that produced it.

**Working rule:** Before you publish a failure rate from production, print its count, the window it covers, and how many of its failures recovered. Name the error type for each kind of failure, and say which kinds carry no type at all. When the number is what users saw, count by message outcome, as chapter 9's objective does.

## What this chapter decided {#find-the-failure-decisions}

A failure is found at the span that records it, so each decision below names the span it reads.

- We define an error as a span with status ERROR, and we count a message by any of its spans. `error-status-by-step` prints the counts that rule gives, and `retries-under-incident` shows the message that recovered and still counts.
- We write the class name the package raises into `error.type`, or the conventions' value where one is defined, such as `tool_error` for an `isError` result. The registry has no value for a timeout or a 429. `error-status-by-step` shows the names, and `retries-under-incident` shows the timeouts.
- We keep the SDK's exception event rather than a log record, because the receiver holds spans and every query here reads them. [Chapter 4's timeout example](#errors-across-the-boundary) shows the event.
- We count each failed attempt as its own error, so the first timeout counts. `retries-under-incident` prints the timed-out attempts and the retries they led to.
- We read a cut reply and a wrong route as quality findings, not errors. `truncated-replies` and `wrong-routes-by-label` print both, with the cap and the scenario table beside them.
- We parse each reply for a tool call, because the finish reason cannot show one. `malformed-tool-calls` prints the parser's counts.
- We keep real and injected failures in separate rows and files, and we label every injected count. `failure-modes-query` reads two receivers, and `error-status-by-step` asserts that every ERROR span on the incident day carries the injected label.
