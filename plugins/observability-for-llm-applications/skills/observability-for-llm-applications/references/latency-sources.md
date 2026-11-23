---
title: "Observability for LLM Applications"
chapter: "Find where the latency comes from"
chapter_id: latency-sources
book: observability-for-llm-applications
edition: 2026.11.1
verified: 2026-11-23
edition_code: B95K-8RWR
canonical: https://rollingedition.com/observability-for-llm-applications/latency-sources
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Find where the latency comes from,” chapter 7 of Observability for LLM Applications, Edition 2026.11.1, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/latency-sources. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Find where the latency comes from

By the end of this chapter you can say which step sets a message's time, at the median and in the tail, and print each number with its count and an interval around it. Ambrewick's assistant answers each message in up to five steps, and its traces show every step of a message but not which step sets the message's end. On baseline day 1, the 200 messages this chapter reads, the median message took 8,099.3 ms, and the 95th percentile took 18,351.2 ms. Was that time spent reading articles, writing the reply, or waiting on a tool?

Every time here comes from one recording machine, a 4-vCPU Intel Xeon at 2.10 GHz that ran Qwen3-4B-Instruct-2507 (the 4B). Each time is either a call's recorded time or a sum of them on the virtual clock described in [Replay and the virtual clock](#replay-and-the-virtual-clock). A message's time here is the recorded time of each call it made, plus the modelled time of the in-process tools and the recorded time of the contacts calls, added up on that clock. The recorder also kept the time between calls, and the replay leaves it out. Over the whole day that time totals 651.4 ms, and each section says which of the two its numbers are.

The chapter builds the chain of calls that sets a message's end, the split of each model call into its reading and its writing, and then the tail, with a percentile and its interval for each route.

## The critical path sets the end time {#the-critical-path}

A message's trace is a tree of timed spans, and the root span ends when the reply goes out. Most spans sit inside the root, and most of them do not set that end. To find the ones that do, walk back from the root's end: take the child that ends last, then the child that ends last before that child starts, and keep going until the walk reaches the root's start. The critical path is the chain of spans that sets a message's end time; shortening any other span doesn't end the message sooner. Shorten a span on the chain and the message gets shorter, until another chain becomes the longer one.

Example `critical-path-one-message` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Replay the slowest message of baseline day 1 and list the chain of spans that sets its end time. The replay runs the
calls one after another, so every call is on the chain, and shortening any one of them shortens this message: the point
rests on the path lines and the assert that the path covers the whole message. The recorder's gaps between calls are
not in the replay; the day's total of them is printed beside it. The tool's time is modelled, a few microseconds, so it
prints as 0.0 ms."""
from lib.critical_path import critical_path
from lib.dayrun import DATA, run_day, run_day_traced
from lib.report import fmt_ms, fmt_share

import json

DAY = "2026-12-08"
runs = run_day(DAY)                                                      # all 200 messages, in arrival order
slowest = max(runs, key=lambda run: run.replied_ns - run.arrived_ns)     # the longest of the day; no other message ties with it
traced = run_day_traced(DAY, [slowest.message.message_id], live=False)   # its spans, replayed the same way
by_id = {row["span_id"]: row for row in traced.spans}
path = critical_path(traced.spans)                                       # root first, then the chain in time order
message = by_id[path[0]]
message_time = message["end_ns"] - message["start_ns"]
chain = [by_id[span_id] for span_id in path[1:]]
covered = sum(row["end_ns"] - row["start_ns"] for row in chain)

print("message:", slowest.message.message_id)
print("route:", slowest.outcome.route)
print("message time:", fmt_ms(message_time))
for number, row in enumerate(chain, start=1):
    # The inference spans carry their prompt's name, so the route call and the answer calls read apart.
    name = row["attributes"].get("gen_ai.prompt.name", row["name"])
    print(f"on the path, {number}: {name}, time: {fmt_ms(row['end_ns'] - row['start_ns'])}")
print("share of the message time on the path:", fmt_share(covered, message_time))

# The recorder's own offsets give the gaps the replay does not keep: each message's span minus its calls' times.
rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
gap_ns = 0
for message_id in sorted({row["message_id"] for row in rows}):
    calls = [row for row in rows if row["message_id"] == message_id]
    span = max(c["offset_ns"] + c["total_ns"] for c in calls) - min(c["offset_ns"] for c in calls)
    gap_ns += span - sum(c["total_ns"] for c in calls)
print("gaps between calls, recorded, all messages of the day:", fmt_ms(gap_ns))

# A constructed tree, not the recording: two calls that overlap. The one that ends last sets the end, and the other
# is off the path, since the walk back from the end reaches the later call's start before it reaches the earlier one.
toy = [
    {"span_id": "a", "parent_span_id": None, "start_ns": 0, "end_ns": 10, "span_seq": 1},
    {"span_id": "b", "parent_span_id": "a", "start_ns": 0, "end_ns": 6, "span_seq": 2},
    {"span_id": "c", "parent_span_id": "a", "start_ns": 2, "end_ns": 9, "span_seq": 3},
]
toy_covered = sum(row["end_ns"] - row["start_ns"] for row in toy if row["span_id"] in critical_path(toy)[1:])
print("constructed overlap, span IDs on the path:", ", ".join(critical_path(toy)))
print("constructed overlap, share of the root's time on the path:", fmt_share(toy_covered, toy[0]["end_ns"] - toy[0]["start_ns"]))
assert critical_path(toy) == ["a", "c"]
assert covered == message_time                 # the chain's calls cover the whole message, with no gap
assert len(chain) == len(traced.spans) - 1     # every call of the message is on the path
```

Output:

```text
message: 7055
route: calendar
message time: 24,305.8 ms
on the path, 1: ambrewick.route, time: 1,666.5 ms
on the path, 2: ambrewick.answer, time: 14,993.5 ms
on the path, 3: execute_tool add_event, time: 0.0 ms
on the path, 4: ambrewick.answer, time: 7,645.8 ms
share of the message time on the path: 100.0%
gaps between calls, recorded, all messages of the day: 651.4 ms
constructed overlap, span IDs on the path: a, c
constructed overlap, share of the root's time on the path: 70.0%
```

This run replays message 7055, the longest message of the day, on the calendar route, with its spans kept. The walk gives four links: the route call, an answer call, the `add_event` tool and a second answer call. The output gives each one's time, and the four add up to the message's 24,305.8 ms. The share of that time on the path is 100.0%, and the run asserts that the chain covers the whole message.

A replay can show that share because its calls run one after another, with nothing between them. The recorder's gaps have no span of their own, so a path built from spans would leave them off, and this message's replay has none of the day's gaps. The path covers the model calls, the modelled time of the in-process tools and the recorded time of the contacts calls, and nothing else. The retrieve step gets no time either, since its span starts and ends at one instant.

Overlap is the case a replay cannot show. No recorded message has two calls running at once, so the run builds a small tree by hand. Span a is the root and ends at 10. Span b runs from 0 to 6, and span c from 2 to 9. The walk from the end reaches c first and never returns to b, so the path is a, c. Span b is off the path, and shortening b does not move the end. That holds on this tree only. The path covers 70.0% of the root's time, so the spans on it explain only that much of the time. That is the low share the working rule warns of.

**Working rule:** Walk the critical path before you tune a trace, and change only the spans on it. Read the path's share of the message time first. A low share means the spans you have do not explain the time, and the rest belongs to no span. A replay's path always covers its message, so a replay cannot tell you which of two overlapping calls matters.

## Time to first chunk {#time-to-first-chunk}

The answer calls hold most of the path, so the next question is where inside a call the time goes. Time to first chunk is the time from sending a model call to receiving the first streamed piece of its reply. The conventions at tag 0.1.0 measure that wait with the metric `gen_ai.client.inference.time_to_first_chunk`, which is a [histogram](#totals-from-metrics-not-spans) in seconds, on streaming calls only and only when a chunk arrives. The span attribute `gen_ai.response.time_to_first_chunk` measures from the start of the logical operation, before authentication and the first attempt, so a hosted client's [retries](#retries-under-a-timeout) count toward it. [Chapter 3's name table](#hand-made-against-instrumented) maps the package's name for the metric to the standard's.

The numbers in this section come from the recorder, not from the metric, which these examples do not run. The recorder timed the first stream event of each streamed reply, which this runtime sends together with the first content. A local model has no authentication step to add.

Each median in this section comes with a 95% interval, which [tail percentiles with intervals](#tail-percentiles-with-intervals) defines.

Example `time-to-first-chunk-by-route` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Take each message's last answer call on baseline day 1, the one that writes the reply the user reads, and compare its time
to first chunk with its total time, by route. Fallback replies make no answer call, so they have no first chunk, and each
interval resamples messages, not calls (PL-6)."""

from lib.dayrun import DATA, run_day
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.stats import bootstrap_interval, nearest_rank

import json
from collections import defaultdict

runs = run_day("2026-12-08")
routes = {run.message.message_id: run.outcome.route for run in runs}
rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
# A first chunk comes before the call ends, and the recorder keeps both times for every call.
assert all(row["ttfc_ns"] <= row["total_ns"] for row in rows)
last_answer = {}
for row in sorted(rows, key=lambda r: r["seq"]):          # the sequence numbers give the order the calls were made
    if row["step"] == "answer":
        last_answer[row["message_id"]] = row               # the later call overwrites the earlier one
by_route = defaultdict(list)
for message_id, row in last_answer.items():
    by_route[routes[message_id]].append(row)
assert not any(routes[message_id] == "fallback" for message_id in last_answer)

print("interval method: bootstrap over messages, 2,000 resamples, seed 20261207, 95%")
for route in sorted(by_route):
    calls = by_route[route]
    ttfc = [call["ttfc_ns"] for call in calls]
    total = [call["total_ns"] for call in calls]
    low, high = bootstrap_interval(calls, lambda units: nearest_rank([u["ttfc_ns"] for u in units], 50))
    print(f"{route}, messages with an answer call: {fmt_int(len(calls))}")
    print(f"{route}, time to first chunk, median: {fmt_ms(nearest_rank(ttfc, 50))}")
    print(f"{route}, time to first chunk, 95% interval: {fmt_ms(low)} to {fmt_ms(high)}")
    print(f"{route}, total time of the answer call, median: {fmt_ms(nearest_rank(total, 50))}")
    print(f"{route}, time to first chunk, share of the call's time: {fmt_share(sum(ttfc), sum(total))}")

route_calls = [row for row in rows if row["step"] == "route"]
print("route calls, time to first chunk, median, all messages:", fmt_ms(nearest_rank([c["ttfc_ns"] for c in route_calls], 50)))
print("route calls, n:", fmt_int(len(route_calls)))
print("messages with no answer call:", fmt_int(len(runs) - len(last_answer)))
```

Output:

```text
interval method: bootstrap over messages, 2,000 resamples, seed 20261207, 95%
alarms, messages with an answer call: 16
alarms, time to first chunk, median: 5,985.6 ms
alarms, time to first chunk, 95% interval: 1,514.8 ms to 6,456.4 ms
alarms, total time of the answer call, median: 9,744.4 ms
alarms, time to first chunk, share of the call's time: 49.6%
calendar, messages with an answer call: 27
calendar, time to first chunk, median: 6,818.8 ms
calendar, time to first chunk, 95% interval: 1,120.5 ms to 7,322.9 ms
calendar, total time of the answer call, median: 10,676.0 ms
calendar, time to first chunk, share of the call's time: 48.8%
devices, messages with an answer call: 17
devices, time to first chunk, median: 6,090.0 ms
devices, time to first chunk, 95% interval: 4,377.7 ms to 6,616.4 ms
devices, total time of the answer call, median: 11,326.7 ms
devices, time to first chunk, share of the call's time: 47.7%
lists, messages with an answer call: 13
lists, time to first chunk, median: 8,563.7 ms
lists, time to first chunk, 95% interval: 8,397.1 ms to 8,866.0 ms
lists, total time of the answer call, median: 12,256.8 ms
lists, time to first chunk, share of the call's time: 69.5%
media, messages with an answer call: 31
media, time to first chunk, median: 5,911.4 ms
media, time to first chunk, 95% interval: 5,663.0 ms to 6,128.4 ms
media, total time of the answer call, median: 11,073.2 ms
media, time to first chunk, share of the call's time: 49.8%
messages, messages with an answer call: 7
messages, time to first chunk, median: 9,289.0 ms
messages, time to first chunk, 95% interval: 485.7 ms to 12,842.8 ms
messages, total time of the answer call, median: 13,865.7 ms
messages, time to first chunk, share of the call's time: 59.4%
route calls, time to first chunk, median, all messages: 530.2 ms
route calls, n: 200
messages with no answer call: 89
```

The output takes each message's last answer call, the one that writes the reply the user reads, and sets its time to first chunk beside its total time, by route. Messages routed to the fallback reply make no answer call, which [chapter 1](#where-the-time-went-in-twenty-messages) describes, so the output counts them apart: 89 of them. The 200 route calls, which pick a route, reach their first chunk at a median of 530.2 ms.

Answer calls take longer to produce that first chunk. Leaving aside the messages route, which has 7, lists has the largest median first chunk, 8,563.7 ms, from 13 messages. Its 95% interval, 8,397.1 ms to 8,866.0 ms, sits above every other route's but messages'.

On lists, the first chunk takes 69.5% of the call's time. On the other routes that share runs from 47.7% to 59.4%.

The messages route needs the most care. Its median first chunk is 9,289.0 ms, from 7 messages, and its 95% interval, 485.7 ms to 12,842.8 ms, is the widest in the output.

**Working rule:** Print time to first chunk beside the total time of the same call, and read the two together. An early first chunk means the user sees output early. It does not mean the call was cheap. Compare routes on their intervals and on the share, and do not name a route's first chunk from a handful of messages.

## Prefill against generation {#prefill-against-generation}

The first chunk waits on the prompt, so the next question is how much of that wait is reading the prompt and how much is something else. Prefill is the model reading the prompt; generation is it writing the reply, one token at a time. Serving papers for GPUs make the same split: prefill keeps the compute busy, and each decoding step leaves most of it idle ([Agrawal et al., Sarathi-Serve](https://www.usenix.org/conference/osdi24/presentation/agrawal), OSDI 2024; [Yu et al., Orca](https://www.usenix.org/conference/osdi22/presentation/yu), OSDI 2022, for one output token per iteration).

The counts in this section need no new definition. [Chapter 6](#three-token-counts) says where input and output tokens come from, and [its cached-input section](#cached-prompt-tokens) says how the cached share is derived. The tokens evaluated are what remains of the input once the cached prefix is taken away, which is the input the model actually read.

The counters come from llama-cpp-python, which exposes llama.cpp's counters for each context: the prompt tokens evaluated and the time they took, and the tokens generated and the time they took. The counters only add up, so the recorder takes the difference before and after each call. Its four warm-up calls, made before each process's first recorded message, are outside the split.

Example `prefill-generation-split` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Split the recorded compute of each model call on baseline day 1 into prefill (the prompt the model read) and generation
(the tokens it wrote), from llama.cpp's counters on the recording machine. The split is the method's output: the numbers
belong to that machine, and the method carries to other hardware. The recorder's warm-up call, made before each
process's first recorded message, is not recorded, so it is not in the split. Rates are computed from the recorded counts."""

from lib.dayrun import DATA
from lib.report import fmt_int, fmt_share

import json

rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
for step in ("route", "answer"):
    calls = [row for row in rows if row["step"] == step]
    prefill = sum(call["prefill_ns"] for call in calls)
    generation = sum(call["gen_ns"] for call in calls)
    first_chunk = sum(call["ttfc_ns"] for call in calls)
    evaluated = sum(call["tokens_evaluated"] for call in calls)   # the prompt's tokens the model read, minus cached ones
    written = sum(call["completion_tokens"] for call in calls)
    assert all(call["prefill_ns"] <= call["ttfc_ns"] for call in calls)   # the first chunk waits for the prompt
    print(f"{step} calls: {fmt_int(len(calls))}")
    print(f"{step}, prefill share of prefill plus generation: {fmt_share(prefill, prefill + generation)}")
    print(f"{step}, prefill share of time to first chunk: {fmt_share(prefill, first_chunk)}")
    print(f"{step}, prompt tokens evaluated per second of prefill, computed: {evaluated * 1e9 / prefill:.1f}")
    print(f"{step}, tokens written per second of generation, computed: {written * 1e9 / generation:.1f}")
```

Output:

```text
route calls: 200
route, prefill share of prefill plus generation: 32.8%
route, prefill share of time to first chunk: 72.7%
route, prompt tokens evaluated per second of prefill, computed: 47.6
route, tokens written per second of generation, computed: 7.3
answer calls: 121
answer, prefill share of prefill plus generation: 54.1%
answer, prefill share of time to first chunk: 91.2%
answer, prompt tokens evaluated per second of prefill, computed: 62.3
answer, tokens written per second of generation, computed: 7.0
```

The output splits each step's compute into the two kinds of work, route calls first. The route calls read a fixed instruction and the message, and the answer calls read the message and whatever the route fetched. A route call's first chunk waits for its prompt: prefill is 72.7% of that wait, though only 32.8% of the call's compute. The answer calls wait on the same thing in larger measure. Prefill is 91.2% of their wait for the first chunk, so the first word of a reply is mostly the prompt being read.

Generation on the answer calls runs at 7.0 tokens a second, and prefill reads 62.3 tokens evaluated a second. Those rates are computed from the counts and hold for this machine, for the reason that [Small Open Models](https://rollingedition.com/small-open-models/s/measure-speed-in-a-recording) gives: a small model's speed is measured in a recording on one named machine and never quoted as a rule. Prefill is counted in tokens evaluated, not in input tokens, and the [next section](#retrieved-context-against-prefill) shows why that choice matters.

**Working rule:** Split a model call's time into prefill and generation before you change its prompt or its reply length. Take the split from the counters, on the same machine and the same calls, and read it beside the total. When prefill is most of the time to first chunk, the prompt is where the wait is. When generation is most of the call, the reply's length is.

## Retrieved context against prefill {#retrieved-context-against-prefill}

Retrieval puts articles into the answer call's prompt, so a release that retrieves more should make prefill longer. The question for that release is how much longer, and whether the model reads all of the added input. The top-8 release gives the answer call up to eight articles, where the baseline gives up to three, on the routes that retrieve. Route calls come before retrieval, so their prompts hold no articles in either release.

The comparison uses the same messages under both releases, the paired 60: the messages of baseline day 1 that the top-8 release was also recorded on. The output's r0 is the baseline and r3 is the top-8 release. It sums each release's answer calls over those messages, and that is a sum, not a comparison with an interval. Chapter 10 pairs the same messages and gives the interval on the difference.

Example `context-against-prefill` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Compare the same 60 messages under r0 (the baseline, on baseline day 1) and r3 (the top-8 release): the answer calls'
prefill, tokens and cache, and the route calls' cache. More articles make the prompt longer, and prefill follows the tokens the
model had to evaluate, since a cached prefix is not read again while the cache holds it. The correlations are over all of
baseline day 1's answer calls, computed; the paired interval belongs to chapter 10, so none is printed here."""

from lib.case import load_messages
from lib.dayrun import DATA
from lib.report import fmt_int, fmt_ms

import json
from collections import Counter
from statistics import correlation


def load(folder):
    return [json.loads(line) for line in (DATA / folder / "traces.jsonl").read_text(encoding="utf-8").splitlines()]


def total(rows, step, field):
    return sum(row[field] for row in rows if row["step"] == step)


paired = {message.message_id for message in load_messages("2026-12-08-paired")}   # the 60 messages, same arrivals
base = load("baseline-day-1")
releases = {"r0": [row for row in base if row["message_id"] in paired], "r3": load("release-top-8")}
assert {row["message_id"] for row in releases["r3"]} == paired     # r3 was recorded for exactly these messages
for name, rows in releases.items():
    print(f"{name}, prefill summed over the answer calls:", fmt_ms(total(rows, "answer", "prefill_ns")))
    print(f"{name}, prompt tokens summed over the answer calls:", fmt_int(total(rows, "answer", "prompt_tokens")))
    print(f"{name}, prompt tokens evaluated summed over the answer calls:", fmt_int(total(rows, "answer", "tokens_evaluated")))
    print(f"{name}, cached prompt tokens summed over the answer calls:", fmt_int(total(rows, "answer", "cached_tokens_derived")))
    print(f"{name}, prompt tokens evaluated summed over the route calls:", fmt_int(total(rows, "route", "tokens_evaluated")))
print("prefill, r3 over r0, computed:", f"{total(releases['r3'], 'answer', 'prefill_ns') / total(releases['r0'], 'answer', 'prefill_ns'):.2f}")

# The same answer calls under both releases: sorted by message, then by call, so each pair is one message's n-th answer.
before = sorted((row for row in releases["r0"] if row["step"] == "answer"), key=lambda row: (row["message_id"], row["seq"]))
after = sorted((row for row in releases["r3"] if row["step"] == "answer"), key=lambda row: (row["message_id"], row["seq"]))
assert all(b["message_id"] == a["message_id"] and b["prompt_tokens"] <= a["prompt_tokens"] for b, a in zip(before, after))
gained = sum(a["prompt_tokens"] > b["prompt_tokens"] for b, a in zip(before, after))   # the assert: none loses any
print("paired answer calls, r3 with more prompt tokens than r0:", f"{gained} of {len(before)}")

route = {name: {row["message_id"]: row for row in rows if row["step"] == "route"} for name, rows in releases.items()}
assert all(route["r0"][m]["input_key"] == route["r3"][m]["input_key"]
           and route["r0"][m]["prompt_tokens"] == route["r3"][m]["prompt_tokens"] for m in paired)   # identical route prompts
cached = {name: [row["cached_tokens_derived"] for row in rows if row["step"] == "route"] for name, rows in releases.items()}
instruction = Counter(cached["r0"]).most_common(1)[0][0]        # the cached count most route calls get: the instruction
print("route instruction, cached tokens in most route calls:", fmt_int(instruction))
for name in releases:
    print(f"{name}, route calls that re-read most of the instruction:", sum(c < instruction for c in cached[name]))

answer_calls = [row for row in base if row["step"] == "answer"]
by_prompt = correlation([row["prompt_tokens"] for row in answer_calls], [row["prefill_ns"] for row in answer_calls])
by_evaluated = correlation([row["tokens_evaluated"] for row in answer_calls], [row["prefill_ns"] for row in answer_calls])
print("prefill against prompt tokens, correlation, computed:", f"{by_prompt:.2f}")
print("prefill against tokens evaluated, correlation, computed:", f"{by_evaluated:.2f}")
assert by_evaluated > 0.9 and by_evaluated > by_prompt   # the cached prefix adds to the prompt, not to the prefill
```

Output:

```text
r0, prefill summed over the answer calls: 172,043.5 ms
r0, prompt tokens summed over the answer calls: 20,420
r0, prompt tokens evaluated summed over the answer calls: 10,855
r0, cached prompt tokens summed over the answer calls: 9,565
r0, prompt tokens evaluated summed over the route calls: 827
r3, prefill summed over the answer calls: 289,244.2 ms
r3, prompt tokens summed over the answer calls: 27,326
r3, prompt tokens evaluated summed over the answer calls: 17,813
r3, cached prompt tokens summed over the answer calls: 9,513
r3, prompt tokens evaluated summed over the route calls: 1,209
prefill, r3 over r0, computed: 1.68
paired answer calls, r3 with more prompt tokens than r0: 15 of 33
route instruction, cached tokens in most route calls: 133
r0, route calls that re-read most of the instruction: 1
r3, route calls that re-read most of the instruction: 4
prefill against prompt tokens, correlation, computed: 0.29
prefill against tokens evaluated, correlation, computed: 0.99
```

On the paired messages, the answer calls take 289,244.2 ms of prefill under the top-8 release, against 172,043.5 ms under the baseline: 1.68 times as much. The output also gives two correlations over every answer call of baseline day 1.

The input grows with the articles. Input tokens rise from 20,420 to 27,326, and tokens evaluated, the input the model read, rise from 10,855 to 17,813.

Both releases skip about the same cached prefix, 9,565 tokens under the baseline and 9,513 under the top-8 release, so the model reads the added input. Under the top-8 release, 15 of 33 paired answer calls gained prompt tokens, and none lost any.

The route calls show a gap without any article in their prompts. Under the top-8 release they evaluate 1,209 tokens, against 827 under the baseline, on prompts the example asserts are identical under both releases.

The cause is the recorder's cache. The cache is bounded at 1 GiB and drops its oldest state first, so a route call that runs after enough others finds its instruction gone and reads it again. The recording logs no cache hits, so this follows from the cache's rule and not from a log. The cache holds the instruction, 133 tokens, for most route calls. Under the top-8 release, 4 route calls re-read most of it, against 1 under the baseline.

Prefill follows tokens evaluated rather than input. Across baseline day 1's answer calls, prefill correlates 0.99 with tokens evaluated and 0.29 with input. A prefix the model has read before is not read again while the cache holds it, so input can grow while the work does not, and the tokens a call evaluates depend on the calls before it.

**Working rule:** Measure a prompt's extra prefill on the same messages as the release it changes, and read tokens evaluated beside input tokens. Input tokens say how large the prompt is. Tokens evaluated say how much work the model did, and when a prefix is cached the two counts part company. Act on the work.

## Tail percentiles with intervals {#tail-percentiles-with-intervals}

The medians so far leave out the messages that wait longest, and those are the ones a tail percentile is for. This book uses the nearest rank. The p-th percentile is the value at sorted position ceil(p/100 × n); the tail is the slowest few percent of messages. Sort the n values, count to position ceil(p/100 × n), and take the value there. It always returns a message that occurred.

[Chapter 1](#whats-rough) said that twenty messages cannot support a tail percentile. Two hundred can, with an interval beside it, and every percentile in this chapter states its count, n. A percentile of seven messages is a different kind of number from one of 200, and the output shows which.

The rule has a consequence at the top of the list. On 200 values the 99th percentile is the value at position 198, which is the third largest, not the second. The output prints the rule on the values 1 to 200 so that the position is visible.

Predict before you run it. How many messages does a route need before its 95th percentile is anything but its slowest message? Work it from ceil(0.95 × n), then check the output.

Example `percentiles-by-route` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Print each route's median, p95 and p99 of message time on baseline day 1, every one with its message count n, and a 95%
interval on each p95. Percentiles are nearest rank: the value at position ceil(p/100 x n). The interval is a bootstrap over
messages, 2,000 resamples, seed 20261207. A route with fewer than 20 messages has its p95 at its largest message, which the
example prints and asserts."""

from lib.dayrun import run_day
from lib.report import fmt_int, fmt_ms
from lib.stats import bootstrap_interval, nearest_rank

from collections import defaultdict

runs = run_day("2026-12-08")
by_route = defaultdict(list)
for run in runs:
    by_route[run.outcome.route].append(run.replied_ns - run.arrived_ns)   # the message's time on the virtual clock
times = [run.replied_ns - run.arrived_ns for run in runs]
groups = {"all routes": times, **by_route}
intervals = {}
print("interval method: bootstrap over messages, 2,000 resamples, seed 20261207, 95%")
print("p99 of the values 1 to 200 (n = 200), nearest rank:", nearest_rank(list(range(1, 201)), 99))
assert nearest_rank(list(range(1, 201)), 99) == 198   # the 198th value, the third largest of 200
print("fewest values before the p95 is not the largest, nearest rank:",
      next(n for n in range(1, 201) if nearest_rank(list(range(1, n + 1)), 95) != n))
for name in ["all routes"] + sorted(by_route):
    values = groups[name]
    low, high = bootstrap_interval(values, lambda units: nearest_rank(units, 95))
    intervals[name] = (low, high)
    print(f"{name}, messages (n): {fmt_int(len(values))}")
    print(f"{name}, median: {fmt_ms(nearest_rank(values, 50))}")
    print(f"{name}, p95: {fmt_ms(nearest_rank(values, 95))}")
    print(f"{name}, p95, 95% interval: {fmt_ms(low)} to {fmt_ms(high)}")
    print(f"{name}, p99: {fmt_ms(nearest_rank(values, 99))}")
small = [name for name in sorted(by_route) if len(by_route[name]) < 20]
print("routes under 20 messages, count:", len(small))
print("routes under 20 messages, p95 is their largest message:", ", ".join(small))
for name in small:
    assert nearest_rank(by_route[name], 95) == max(by_route[name])   # ceil(0.95 n) = n for every n up to 19
assert len(times) == len(runs) == 200
# Two routes' p95 intervals overlap, so the largest p95 cannot be told apart from the next one with this many messages.
low_m, high_m = intervals["messages"]
low_c, high_c = intervals["calendar"]
assert low_m <= high_c and low_c <= high_m
```

Output:

```text
interval method: bootstrap over messages, 2,000 resamples, seed 20261207, 95%
p99 of the values 1 to 200 (n = 200), nearest rank: 198
fewest values before the p95 is not the largest, nearest rank: 20
all routes, messages (n): 200
all routes, median: 8,099.3 ms
all routes, p95: 18,351.2 ms
all routes, p95, 95% interval: 16,452.7 ms to 20,909.8 ms
all routes, p99: 22,425.7 ms
alarms, messages (n): 16
alarms, median: 12,159.5 ms
alarms, p95: 22,425.7 ms
alarms, p95, 95% interval: 15,757.0 ms to 22,425.7 ms
alarms, p99: 22,425.7 ms
calendar, messages (n): 27
calendar, median: 12,519.8 ms
calendar, p95: 20,909.8 ms
calendar, p95, 95% interval: 14,623.8 ms to 24,305.8 ms
calendar, p99: 24,305.8 ms
devices, messages (n): 17
devices, median: 12,510.2 ms
devices, p95: 17,417.9 ms
devices, p95, 95% interval: 14,532.9 ms to 17,417.9 ms
devices, p99: 17,417.9 ms
fallback, messages (n): 89
fallback, median: 1,392.0 ms
fallback, p95: 1,726.6 ms
fallback, p95, 95% interval: 1,636.7 ms to 3,108.1 ms
fallback, p99: 3,191.4 ms
lists, messages (n): 13
lists, median: 13,786.6 ms
lists, p95: 17,183.7 ms
lists, p95, 95% interval: 14,842.4 ms to 17,183.7 ms
lists, p99: 17,183.7 ms
media, messages (n): 31
media, median: 12,708.9 ms
media, p95: 16,452.7 ms
media, p95, 95% interval: 14,786.5 ms to 18,351.2 ms
media, p99: 18,351.2 ms
messages, messages (n): 7
messages, median: 19,793.3 ms
messages, p95: 24,253.7 ms
messages, p95, 95% interval: 21,244.6 ms to 24,253.7 ms
messages, p99: 24,253.7 ms
routes under 20 messages, count: 4
routes under 20 messages, p95 is their largest message: alarms, devices, lists, messages
```

The output gives each route's median, 95th and 99th percentile, each with its count, and a 95% interval on each 95th percentile. A route needs at least 20 messages before its 95th percentile is anything but its largest. 4 routes have fewer than 20 messages, alarms, devices, lists, messages, and for each one the 95th percentile is its slowest message.

The messages route's 95th percentile is 24,253.7 ms from 7 messages, with a 95% interval of 21,244.6 ms to 24,253.7 ms whose top is the same value. Its last answer calls are the longest of the answering routes at the median, at 13,865.7 ms. The output does not say why its tail is long.

The all-routes median, 8,099.3 ms, is lower than the median of every route that answered. The reason is the fallback route. 89 of the 200 messages took the fallback reply, which makes one route call and no answer call, and their median is 1,392.0 ms. The all-routes median is the middle value of all the messages, so those messages pull it down.

Example `figure-latency-tail-by-route` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Draw each route's median and p95 of message time on baseline day 1, with a 95% interval on the p95, so the tail's place
in each route shows at a glance. Every value the figure draws is printed first, with its message count n. The interval
is a bootstrap over messages (2,000 resamples, seed 20261207); the route is the one the assistant chose."""

from lib.dayrun import run_day
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int, fmt_ms
from lib.stats import bootstrap_interval, nearest_rank

from collections import defaultdict

runs = run_day("2026-12-08")
times = {"all routes": [run.replied_ns - run.arrived_ns for run in runs]}
for run in runs:
    times.setdefault(run.outcome.route, []).append(run.replied_ns - run.arrived_ns)
names = ["all routes"] + sorted(name for name in times if name != "all routes")
summary = []
for name in names:
    values = times[name]
    low, high = bootstrap_interval(values, lambda units: nearest_rank(units, 95))
    summary.append((name, len(values), nearest_rank(values, 50), nearest_rank(values, 95), low, high))
    print(f"{name}, messages (n): {fmt_int(len(values))}")
    print(f"{name}, median: {fmt_ms(summary[-1][2])}")
    print(f"{name}, p95: {fmt_ms(summary[-1][3])}, interval: {fmt_ms(low)} to {fmt_ms(high)}")

fig, ax = new_figure(height=3.8)
rows = list(range(len(summary)))[::-1]                 # the first row, all routes, at the top
for row, (name, count, median, p95, low, high) in zip(rows, summary):
    ax.hlines(row, low / 1e6, high / 1e6, color=MUTED, linewidth=3, label="95% interval of the p95" if row == rows[0] else None)
    ax.scatter([median / 1e6], [row], facecolors="none", edgecolors=INK, linewidths=1.4, s=52, zorder=3,
               label="median" if row == rows[0] else None)     # a hollow circle, so the two dots differ in shape as well as colour
    ax.scatter([p95 / 1e6], [row], color=ACCENT, marker="D", s=44, zorder=3, label="p95" if row == rows[0] else None)
ax.set_yticks(rows, [f"{name} (n = {count})" for name, count, *_ in summary])
ax.set_xlabel("message time, milliseconds")
ax.set_xlim(0, 30000)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3)   # below the axis, clear of every row
save(fig, "latency-tail-by-route")
```

Output:

```text
all routes, messages (n): 200
all routes, median: 8,099.3 ms
all routes, p95: 18,351.2 ms, interval: 16,452.7 ms to 20,909.8 ms
alarms, messages (n): 16
alarms, median: 12,159.5 ms
alarms, p95: 22,425.7 ms, interval: 15,757.0 ms to 22,425.7 ms
calendar, messages (n): 27
calendar, median: 12,519.8 ms
calendar, p95: 20,909.8 ms, interval: 14,623.8 ms to 24,305.8 ms
devices, messages (n): 17
devices, median: 12,510.2 ms
devices, p95: 17,417.9 ms, interval: 14,532.9 ms to 17,417.9 ms
fallback, messages (n): 89
fallback, median: 1,392.0 ms
fallback, p95: 1,726.6 ms, interval: 1,636.7 ms to 3,108.1 ms
lists, messages (n): 13
lists, median: 13,786.6 ms
lists, p95: 17,183.7 ms, interval: 14,842.4 ms to 17,183.7 ms
media, messages (n): 31
media, median: 12,708.9 ms
media, p95: 16,452.7 ms, interval: 14,786.5 ms to 18,351.2 ms
messages, messages (n): 7
messages, median: 19,793.3 ms
messages, p95: 24,253.7 ms, interval: 21,244.6 ms to 24,253.7 ms
figure: figures/latency-tail-by-route.svg
```

*Figure 7.1. Each route's median and 95th percentile of message time on baseline day 1, with a 95% interval on the 95th percentile.*

![The answering routes' 95th percentiles have mostly overlapping intervals, and the fallback route's is far shorter](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.1/figures/latency-tail-by-route.svg)

Figure 7.1 draws each route's median and 95th percentile, with the interval on the 95th percentile as a bar. The top row is all routes together. Read the answering routes' bars against one another. Most of their intervals overlap, and the messages interval overlaps calendar's, as the example asserts. The 4 routes under 20 messages have bars that end at their own largest message. The fallback bar is far shorter than the rest. So the tail depends on whether the route answers, and the count decides how sure the reader can be of where a route's tail sits.

The interval is a percentile bootstrap, and this is the one place the chapter builds it. An interval says how far a number would move had the day brought other messages drawn the same way; here, the middle 95% of 2,000 bootstrap resamples of messages. The question behind it is whether another day's 95th percentile would be the same. The interval answers that only for a day drawn the same way. A different day, a release or a load lies outside what it covers.

For each route, the code draws as many messages as the route has, with replacement, takes the 95th percentile of that resample, and repeats the draw 2,000 times with the seed 20261207. The interval is the 50th and the 1,950th of the 2,000 results, which bracket 95% of them. [Efron](https://doi.org/10.1214/aos/1176344552) introduced the bootstrap in 1979, and [Evaluating LLM Applications](https://rollingedition.com/evaluating-llm-applications/s/bootstrap-over-items) uses the same method over items. Here the unit is the message, not the span, because the spans of one message are not independent of one another.

The same bootstrap applies to any statistic taken per message, such as the share of the day's cost that the most expensive messages carry in [chapter 6](#the-expensive-tail). Under 20 messages, though, the 95th percentile of every resample is one of the route's own messages, and the largest of them is the top of the interval. The interval cannot reach past the messages it came from. So for each of the 4 routes under 20 messages, the upper end is its own largest message, the upper end and the point estimate are one value, and the interval's width measures the resampling, not what those few messages leave out.

**Working rule:** Print each percentile with its count and its interval, and rank two routes only when their intervals do not overlap. Collect more messages before you name a tail.

## Histogram buckets and what they hide {#histogram-buckets-and-what-they-hide}

A histogram keeps no messages, only counts. A bucket counts the values between two edges, so a percentile read from buckets is known only to within its bucket. The GenAI conventions at tag 0.1.0 say the boundaries SHOULD be these, in seconds, for their duration histograms, the agent's `gen_ai.client.invoke_agent.duration` included. The book uses them for message time, the duration this chapter measures: 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92. A service exports the edges its configuration sets, which may not be these.

Example `bucket-edges-hide-tail` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Count baseline day 1's message times into the buckets the GenAI conventions advise for the agent's duration histogram, then
estimate the p95 from the bucket counts and set it beside the nearest-rank p95 of the raw values. The estimate spreads each
bucket's values evenly across it, and the p95 falls in one bucket, so the buckets can only place the estimate inside it."""

from lib import genai
from lib.dayrun import run_day
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.stats import bucket_counts, nearest_rank

import math

EDGES_S = genai.BUCKETS["gen_ai.client.invoke_agent.duration"]   # the conventions' advised upper bounds, in seconds
print("GenAI conventions version:", genai.REGISTRY_VERSION)
print("bucket boundaries, GenAI conventions, seconds:", ", ".join(str(edge) for edge in EDGES_S))
runs = run_day("2026-12-08")
times = [run.replied_ns - run.arrived_ns for run in runs]
n = len(times)
edges = [round(edge * 1_000_000_000) for edge in EDGES_S]      # integer nanoseconds, as every time here is
counts = bucket_counts(times, edges)                           # a value sits in the bucket whose upper edge it does not exceed
print("messages (n):", fmt_int(n))
for index, count in enumerate(counts):
    low = edges[index - 1] if index else 0                     # a bucket starts at the upper edge of the one before it
    if index < len(edges):
        print(f"bucket above {fmt_ms(low)} up to {fmt_ms(edges[index])}: {fmt_int(count)} messages, {fmt_share(count, n)}")
    else:
        print(f"bucket above {fmt_ms(low)}: {fmt_int(count)} messages, {fmt_share(count, n)}")

exact = nearest_rank(times, 95)
rank = math.ceil(95 * n / 100)                                 # the nearest-rank position of the p95
index = next(i for i, edge in enumerate(edges) if exact <= edge)   # the bucket that holds the exact p95
low = edges[index - 1] if index else 0                         # its lower edge, as above; the first starts at zero
below = sum(counts[:index])                                    # messages in the buckets under it
estimate = low + round((rank - below) * (edges[index] - low) / counts[index])
print("bucket holding the p95, lower edge:", fmt_ms(low))
print("bucket holding the p95, upper edge:", fmt_ms(edges[index]))
print("messages in that bucket:", fmt_int(counts[index]))
print("messages at or below its lower edge:", fmt_int(below))
print("p95, nearest rank of the raw values:", fmt_ms(exact))
print("p95, estimated from the bucket counts:", fmt_ms(estimate))
print("estimate minus the nearest-rank p95:", fmt_ms(estimate - exact))
assert low < exact <= edges[index]                             # the exact p95 lies in the bucket that holds it
assert abs(estimate - exact) > 500_000_000                     # the bucket estimate is more than half a second off
```

Output:

```text
GenAI conventions version: 0.1.0
bucket boundaries, GenAI conventions, seconds: 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92
messages (n): 200
bucket above 0.0 ms up to 10.0 ms: 0 messages, 0.0%
bucket above 10.0 ms up to 20.0 ms: 0 messages, 0.0%
bucket above 20.0 ms up to 40.0 ms: 0 messages, 0.0%
bucket above 40.0 ms up to 80.0 ms: 0 messages, 0.0%
bucket above 80.0 ms up to 160.0 ms: 0 messages, 0.0%
bucket above 160.0 ms up to 320.0 ms: 0 messages, 0.0%
bucket above 320.0 ms up to 640.0 ms: 0 messages, 0.0%
bucket above 640.0 ms up to 1,280.0 ms: 21 messages, 10.5%
bucket above 1,280.0 ms up to 2,560.0 ms: 65 messages, 32.5%
bucket above 2,560.0 ms up to 5,120.0 ms: 3 messages, 1.5%
bucket above 5,120.0 ms up to 10,240.0 ms: 16 messages, 8.0%
bucket above 10,240.0 ms up to 20,480.0 ms: 89 messages, 44.5%
bucket above 20,480.0 ms up to 40,960.0 ms: 6 messages, 3.0%
bucket above 40,960.0 ms up to 81,920.0 ms: 0 messages, 0.0%
bucket above 81,920.0 ms: 0 messages, 0.0%
bucket holding the p95, lower edge: 10,240.0 ms
bucket holding the p95, upper edge: 20,480.0 ms
messages in that bucket: 89
messages at or below its lower edge: 105
p95, nearest rank of the raw values: 18,351.2 ms
p95, estimated from the bucket counts: 20,019.8 ms
estimate minus the nearest-rank p95: 1,668.6 ms
```

The output counts the same messages of baseline day 1 into those buckets, estimates the 95th percentile from the counts, and sets the estimate beside the nearest-rank value of the raw messages. The bucket holding the 95th percentile runs from 10,240.0 ms to 20,480.0 ms. It holds 89 messages, and 105 messages sit at or below its lower edge.

The buckets place the 95th percentile between those edges, and no closer. The estimate spreads the messages in the bucket evenly across it. That is the rule of [Prometheus's percentile estimate from buckets](https://raw.githubusercontent.com/prometheus/prometheus/v2.53.0/promql/quantile.go), which assumes a linear distribution within a bucket. Other backends may interpolate differently, so the estimate moves when the edges move. Here the estimate is 20,019.8 ms and the nearest-rank value of the raw messages is 18,351.2 ms, so the estimate is 1,668.6 ms too high on this day.

Example `figure-bucket-hides-tail` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Draw baseline day 1's message times twice, on one millisecond scale: each message as a point in the upper panel, and the
bucket counts for the same messages in the lower panel, each bucket drawn across the span it covers. The edges are the ones
bucket-edges-hide-tail uses. Every value the figure shows is printed first, and the nearest-rank p95 is drawn as a line."""
from lib import genai
from lib.dayrun import run_day
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.stats import bucket_counts, nearest_rank

EDGES_S = genai.BUCKETS["gen_ai.client.invoke_agent.duration"]  # the conventions' advised upper bounds, in seconds, as there
runs = run_day("2026-12-08")
times = sorted(run.replied_ns - run.arrived_ns for run in runs)
n = len(times)
edges = [round(edge * 1_000_000_000) for edge in EDGES_S]      # integer nanoseconds, as every time here is
counts = bucket_counts(times, edges)
exact = nearest_rank(times, 95)
lows = [0] + edges                                             # each bucket starts at the edge before it
print("messages (n):", fmt_int(n))
for number, count in enumerate(counts):
    if number < len(edges):
        print(f"bucket above {fmt_ms(lows[number])} up to {fmt_ms(edges[number])}: {fmt_int(count)} messages, {fmt_share(count, n)}")
    else:
        print(f"bucket above {fmt_ms(lows[number])}: {fmt_int(count)} messages, {fmt_share(count, n)}")
print("p95, nearest rank of the raw values:", fmt_ms(exact))

fig, (top, bottom) = new_figure(rows=2, height=4.6, sharex=True)
top.scatter([t / 1e6 for t in times], [(i + 1) / n for i in range(n)], s=10, color=INK, label="each message")
for edge in edges:
    top.axvline(edge / 1e6, color=MUTED, linestyle=":", linewidth=0.8)
top.axvline(exact / 1e6, color=ACCENT, linestyle="--", linewidth=1.2, label="p95, nearest rank")
top.set_ylabel("share at or below")
top.legend(loc="lower right")
highs = edges + [edges[-1] + 10_000_000_000]                   # the last bucket is open; drawn 10 s wide, past the axis
centres = [(lo + hi) / 2 / 1e6 for lo, hi in zip(lows, highs)]
widths = [(hi - lo) / 1e6 for lo, hi in zip(lows, highs)]
bars = bottom.bar(centres, counts, width=widths, color=MUTED)
bottom.bar_label(bars, labels=[fmt_int(c) if c else "" for c in counts], padding=2)   # empty buckets carry no label
bottom.set_xticks([e / 1e6 for e in edges], [f"{e / 1e6:,.0f}" if e >= 10_240_000_000 else "" for e in edges])   # the small edges crowd the left
bottom.set_ylabel("messages")
bottom.set_xlim(0, 42000)                                      # set after the ticks, which would widen it
bottom.set_ylim(0, max(counts) * 1.15)
bottom.set_xlabel("message time, milliseconds; bucket edges as ticks")
save(fig, "bucket-hides-tail")
```

Output:

```text
messages (n): 200
bucket above 0.0 ms up to 10.0 ms: 0 messages, 0.0%
bucket above 10.0 ms up to 20.0 ms: 0 messages, 0.0%
bucket above 20.0 ms up to 40.0 ms: 0 messages, 0.0%
bucket above 40.0 ms up to 80.0 ms: 0 messages, 0.0%
bucket above 80.0 ms up to 160.0 ms: 0 messages, 0.0%
bucket above 160.0 ms up to 320.0 ms: 0 messages, 0.0%
bucket above 320.0 ms up to 640.0 ms: 0 messages, 0.0%
bucket above 640.0 ms up to 1,280.0 ms: 21 messages, 10.5%
bucket above 1,280.0 ms up to 2,560.0 ms: 65 messages, 32.5%
bucket above 2,560.0 ms up to 5,120.0 ms: 3 messages, 1.5%
bucket above 5,120.0 ms up to 10,240.0 ms: 16 messages, 8.0%
bucket above 10,240.0 ms up to 20,480.0 ms: 89 messages, 44.5%
bucket above 20,480.0 ms up to 40,960.0 ms: 6 messages, 3.0%
bucket above 40,960.0 ms up to 81,920.0 ms: 0 messages, 0.0%
bucket above 81,920.0 ms: 0 messages, 0.0%
p95, nearest rank of the raw values: 18,351.2 ms
figure: figures/bucket-hides-tail.svg
```

*Figure 7.2. Baseline day 1's messages as points, and as bucket counts, with the 95th percentile as a dashed line.*

![The 95th percentile falls in a bucket, and the bucket counts alone cannot say where in it the messages lie](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.1/figures/bucket-hides-tail.svg)

Figure 7.2 draws the same messages twice on one millisecond scale. The upper panel plots each message at the share of messages at or below it, so the points climb. The dotted lines are the bucket edges, and the dashed line is the nearest-rank 95th percentile. The lower panel shows each bucket's count, drawn across the range the bucket covers. The 95th-percentile line falls inside a wide bucket, and nothing in the lower panel says where in that bucket the messages sit. That is what a bucket loses, and it is why the estimate is off.

**Working rule:** Set bucket edges from the question you will ask, and put an edge near each threshold you alert on. When a percentile falls inside a wide bucket, report the bucket and its count rather than an estimate to the millisecond, and keep the raw values whenever you can. An estimate from buckets is one rule applied to one set of edges, and it moves when the edges move.

## Queueing on recorded service times {#queueing-on-recorded-service-times}

A message's time is not only its own work. When a message arrives while the model is busy with another, it waits, and the wait is part of the time the user sees. A queue shows how that wait grows with load. Each arrival joins a line, the server takes one message at a time, and the load is the share of the server's time that arrivals ask for.

The numbers in this section are computed, not recorded. The code models one server. Its arrivals come at random, at a fixed average rate set by the load, which is a Poisson process: the gaps between arrivals are independent, with an exponential spread. Each message's service time is one of the day's recorded message times, drawn with replacement. Little's law says that the average number in a system equals its arrival rate times the average time each item spends in it, L = λW. [Little's 1961 proof](https://doi.org/10.1287/opre.9.3.383) establishes it, and [MIT's course notes on the M/M/1 queue](https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/927056a1af54772a587fd84ad4951e71_MIT2_854F16_Mm1Queue.pdf) state it in the form used here.

Example `queue-on-service-times` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Queue baseline day 1's recorded message times behind one first-come, first-served server at three loads, with seeded Poisson
arrivals and each message's service drawn from the recorded times. The number in system is walked from the queue's events and
checked against the arrival rate times the time in system, and the last check compares exponential service with the M/M/1 formula."""
from lib.dayrun import run_day
from lib.report import fmt_int, fmt_ms
from lib.stats import nearest_rank

from fractions import Fraction

import numpy as np

SEED, N, CHECK_N = 20261208, 50_000, 200_000                   # one seed; messages per run; the M/M/1 check's run
recorded = [run.replied_ns - run.arrived_ns for run in run_day("2026-12-08")]   # the day's 200 recorded message times
mean_service = sum(recorded) / len(recorded)


recorded_services = lambda rng, n: rng.choice(np.asarray(recorded, dtype=np.int64), n)   # resampled with replacement
exponential_services = lambda rng, n: rng.exponential(mean_service, n).round().astype(np.int64)


def simulate(rng, rho, n, services):
    """Serve n messages arriving at rate rho / mean_service. Returns arrivals, waits, times in system, the last finish
    and the total service time, in ns."""
    arrivals = np.cumsum(rng.exponential(mean_service / rho, n)).round().astype(np.int64).tolist()
    finish, waits, sojourn, busy = 0, [], [], 0
    for arrive, serve in zip(arrivals, services(rng, n).tolist()):
        start = max(arrive, finish)          # the server finishes the message before it, then starts this one
        finish = start + serve
        waits.append(start - arrive)
        sojourn.append(finish - arrive)
        busy += serve
    return arrivals, waits, sojourn, finish, busy


print("mean recorded message time:", fmt_ms(round(mean_service)))
for rho in (0.5, 0.8, 0.9):
    arrivals, waits, sojourn, finish, busy = simulate(np.random.Generator(np.random.PCG64(SEED)), rho, N, recorded_services)
    span = finish - arrivals[0]                                # first arrival to last departure
    # Each arrival adds one to the count in system and each departure takes one away; the area under the count is L times the span.
    area, count, when = 0, 0, arrivals[0]
    for moment, step in sorted([(a, 1) for a in arrivals] + [(a + s, -1) for a, s in zip(arrivals, sojourn)]):
        area, count, when = area + count * (moment - when), count + step, moment
    number, rate_times_time = Fraction(area, span), Fraction(N, span) * Fraction(sum(sojourn), N)   # L, and lambda W
    print(f"load {rho}, utilisation, computed: {busy / span:.2f}")
    print(f"load {rho}, wait before service, computed, p95 (n = {fmt_int(N)}):", fmt_ms(nearest_rank(waits, 95)))
    print(f"load {rho}, number in system, time average, computed: {float(number):.2f}")
    print(f"load {rho}, arrival rate times time in system, computed: {float(rate_times_time):.2f}")
    assert number == rate_times_time     # exact, with no tolerance: the window starts at the first arrival and ends at the last departure

# M/M/1: the mean time in system is 1 / (mu - lambda), which is mean_service / (1 - rho) for exponential service.
sojourn = simulate(np.random.Generator(np.random.PCG64(SEED)), 0.8, CHECK_N, exponential_services)[2]
simulated, formula = sum(sojourn) / CHECK_N, mean_service / (1 - 0.8)
print(f"exponential service, load 0.8, mean time in system, simulated (n = {fmt_int(CHECK_N)}):", fmt_ms(round(simulated)))
print("exponential service, load 0.8, mean time in system, formula:", fmt_ms(round(formula)))
assert abs(simulated - formula) / formula < 0.02
```

Output:

```text
mean recorded message time: 8,019.0 ms
load 0.5, utilisation, computed: 0.50
load 0.5, wait before service, computed, p95 (n = 50,000): 27,983.0 ms
load 0.5, number in system, time average, computed: 0.91
load 0.5, arrival rate times time in system, computed: 0.91
load 0.8, utilisation, computed: 0.80
load 0.8, wait before service, computed, p95 (n = 50,000): 82,817.5 ms
load 0.8, number in system, time average, computed: 3.31
load 0.8, arrival rate times time in system, computed: 3.31
load 0.9, utilisation, computed: 0.90
load 0.9, wait before service, computed, p95 (n = 50,000): 179,463.5 ms
load 0.9, number in system, time average, computed: 7.26
load 0.9, arrival rate times time in system, computed: 7.26
exponential service, load 0.8, mean time in system, simulated (n = 200,000): 40,422.0 ms
exponential service, load 0.8, mean time in system, formula: 40,094.8 ms
```

The output covers loads of 0.5, 0.8 and 0.9, each with the same seed, and then one more check where a formula exists. The mean recorded message time is 8,019.0 ms, the service each message takes on average, and at a load of 0.5 the server's utilisation is 0.50.

The 95th-percentile wait before service is 27,983.0 ms at load 0.5, 82,817.5 ms at 0.8, and 179,463.5 ms at 0.9. The waits climb more steeply than the load.

The number in system follows the same curve. At load 0.8 it averages 3.31, and the arrival rate times the time in system gives 3.31. The code finds the first from the queue's events over time and the second from the arrival rate and the mean time in system, and asserts that they are equal at every load. On a sample path whose window runs from the first arrival to the last departure, Little's law holds exactly, so the assert allows no tolerance.

The M/M/1 formula, the mean time in system for one server with exponential service, is exact only for exponential service times, and the recorded times are not exponential. So the code checks the simulation on its own terms first. With exponential service at load 0.8 over 200,000 messages, the simulated mean time in system is 40,422.0 ms, and the formula gives 40,094.8 ms. The code asserts that the two agree within 2%. M/G/1, a single server with any service distribution, has a mean formula of its own, and this chapter leaves that check out.

This is a model of one server, not of Ambrewick's deployment. Each message's whole recorded time is one service, which is how the queue treats a message, and its arrivals ignore the day's real arrival times. The waits are therefore what one server with this mix of messages would give, and they are not what the day did.

**Working rule:** Read a queue at the load you expect and at a higher one before you accept a tail or add capacity. Use recorded service times when you have them, label every number the simulation computes, and check the simulation against a formula only where the formula's assumptions hold.

## What goes wrong in production {#latency-sources-in-production}

Three things change when these numbers leave the replay. First, production spans leave gaps. The recorder's gaps between calls total 651.4 ms over the day. They are real time in the message, but they belong to no span, so a critical path built from spans can cover less than the message's full time. Read the path's share beside the message time, and treat a low share as a question for the trace, not as an answer.

Second, the histogram a service exports has the edges its configuration sets, which may not be the conventions' advised ones. A percentile read from buckets takes on the [error](#how-a-span-records-failure) of its edges, as the bucket estimate shows on this day's messages. Chapter 9 sets its objectives on these latencies, so the edges belong in that decision as well.

Third, a route with few messages a day gets a 95th percentile with a wide [interval](#tail-percentiles-with-intervals), and a dashboard that shows only the point looks exact. Put the count and the interval on the same panel, or leave the percentile off it.

**Working rule:** Before you publish a latency number from production, print its count and its interval beside it, and say which kind of time it is: a span's time, a bucket's estimate, or a replay's sum. When the path's share or the bucket's edges are unknown, state that with the number instead of letting the number stand alone.

## The decisions this chapter made {#latency-sources-decisions}

Each of these is a judgement we could get wrong. Each gives its reason and the example that tests it.

- We read the critical path from the spans, and we show the overlap case on a constructed tree, because no recorded message has overlapping calls. `critical-path-one-message` checks that the path covers the whole replayed message, and that the constructed tree's span b is off the path.
- We report time to first chunk beside the same call's total time, and we split it with the counters, so that a first chunk is never read alone. `time-to-first-chunk-by-route` and `prefill-generation-split` print both on the same calls.
- We print nearest-rank percentiles with their counts, and an interval on each 95th percentile from seeded bootstrap resamples of messages. `percentiles-by-route` names the routes under 20 messages, whose 95th percentile is their largest message, and checks the one overlap the prose relies on.
- We use the edges the GenAI conventions advise for message time, and we say so, because a service's own edges may differ. `bucket-edges-hide-tail` prints the estimate's error on this day, and `figure-bucket-hides-tail` draws the raw values beside the counts.
- We simulate queues only on recorded service times, and we label every queue number computed. `queue-on-service-times` finds the number in system from the queue's events and checks it against the arrival rate times the time in system at each load, and it checks the M/M/1 formula only with exponential service.
- We rank routes' tails only where their intervals do not overlap, because one day of messages cannot order them. On this day that leaves most of the answering routes unordered, so the firm difference is whether a route answers at all, not which answering route has the worst tail.
