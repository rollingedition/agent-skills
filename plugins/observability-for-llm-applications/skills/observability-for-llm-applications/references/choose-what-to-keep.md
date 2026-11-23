---
title: "Observability for LLM Applications"
chapter: "Choose which traces to keep"
chapter_id: choose-what-to-keep
book: observability-for-llm-applications
edition: 2026.11.1
verified: 2026-11-23
edition_code: B95K-8RWR
canonical: https://rollingedition.com/observability-for-llm-applications/choose-what-to-keep
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Choose which traces to keep,” chapter 11 of Observability for LLM Applications, Edition 2026.11.1, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/choose-what-to-keep. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Choose which traces to keep

By the end of this chapter you can choose which traces a backend keeps, say what each choice drops, and scale a total from the traces it kept, with an interval around the result. You'll write a rule that keeps the traces an engineer needs most, and check it against the incident day.

Ambrewick keeps one trace for every message, and [chapter 1](#one-message-one-trace) kept every one. At the book's scale of 200 messages a day, that is simple to manage. A service that answers messages all day writes far more, and a backend that holds every trace for a year pays for each of them. A sampler keeps some traces and drops the rest, so the decision that matters is which ones. The incident day shows the problem. Its errors are rare, and the engineer who opens the traces after an alert needs those errors and the slow messages more than any typical message. A sampler that picks traces without reading them keeps the rare ones at the same share as everything else.

This chapter builds the three kinds of decision that trace sampling makes, and the estimate a total needs when only some traces are kept. Here trace sampling means deciding which traces the backend keeps. It has nothing to do with token sampling, which chooses the next word a model writes. The examples run on two recorded days: baseline day 1, which has no injected faults, and the incident day from [chapter 9](#an-alert-that-stays-quiet). Both were recorded on the recording machine, a 4-vCPU Intel Xeon at 2.10 GHz, which ran Qwen3-4B-Instruct-2507, and both are replayed on the [virtual clock](#replay-and-the-virtual-clock).

## Head sampling decides before the trace runs {#head-sampling}

Head sampling decides whether to keep a trace when it starts, before any span has run. The kind this chapter uses keeps a fixed share by the trace ID, so it cannot know whether the message will fail and cannot aim at failures. The ratio is the share of traces kept, and the sample is keyed on the [trace ID](#one-message-one-trace).

The SDK's ratio sampler compares the trace ID with the ratio. It reads the low 64 bits of the trace ID as a number, and it keeps the trace when that number falls below the ratio's share of the whole range ([the sampler in the Python SDK](https://raw.githubusercontent.com/open-telemetry/opentelemetry-python/v1.45.2/opentelemetry-sdk/src/opentelemetry/sdk/trace/sampling.py), pinned here at 1.45.2). The decision depends on the ID alone, so every span of a trace agrees with the others, and the same trace gets the same answer on every run. The book's trace IDs count up from 1, and small counts all fall under any ratio above zero, so the book hashes each count to 128 bits before the sampler reads it. The specification deprecates `TraceIdRatioBased` in favour of `ProbabilitySampler`, which decides from the 56 bits of randomness that W3C Trace Context Level 2 specifies ([the trace SDK specification at v1.50.0](https://raw.githubusercontent.com/open-telemetry/opentelemetry-specification/v1.50.0/specification/trace/sdk.md)). The pinned SDK has no `ProbabilitySampler`, so the book uses the ratio sampler at the root.

The replay runs every message first and makes the head decision afterward. The decision is applied to the completed traces, and it is the same decision the assistant's own sampler would make at the source, because the trace ID alone settles it. The example's last lines check that claim: at each ratio it uses, a provider with the same sampler starts a root span for every trace ID of the day, and the example asserts that the two decisions agree.

Example `head-sample-ratio` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Head sampling on baseline day 1: the share of messages each ratio keeps, and the rule that a larger ratio keeps every
message a smaller one kept. The decision is the SDK's TraceIdRatioBased on each message's trace ID, as its root would
make it, so the same messages stay kept as the ratio grows. A live provider samples the same trace IDs at the source, and
the replayed and the live decisions must agree."""
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.dayrun import run_day_traced
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share
from lib.sampling import head_ratio, head_sample, live_provider, message_traces, only_messages

MODEL = "Qwen3-4B-Instruct-2507"
DAY = "2026-12-08"                                  # baseline day 1: no injected faults
RATIOS = (0.01, 0.1, 0.5, 1.0)                      # 1.0 keeps everything, the check that the ratio is read as a share
traces = only_messages(message_traces(run_day_traced(DAY, live=False).spans, DAY, MODEL, PriceTable()))
print("messages on baseline day 1, of all messages:", fmt_int(len(traces)))
kept = {}                                           # ratio -> the sequential trace IDs it keeps
for ratio in RATIOS:
    kept[ratio] = {t.seq for t in head_sample(traces, ratio)}
    print(f"messages kept at ratio {ratio}, of {len(traces)}:", fmt_int(len(kept[ratio])))
    print(f"share of messages kept at ratio {ratio}:", fmt_share(len(kept[ratio]), len(traces)))
    # The source's own decision: a provider with the same sampler makes one root per trace ID, counting from 1.
    provider = live_provider(head_ratio(ratio), InMemorySpanExporter())
    tracer = provider.get_tracer("ambrewick.assistant")
    live = set()
    for seq in range(1, len(traces) + 1):
        root = tracer.start_span("invoke_agent probe")
        if root.is_recording():
            live.add(seq)
        root.end()
    differ = len(live ^ kept[ratio])
    print(f"trace IDs where the replayed and the live decision differ at ratio {ratio}, of {len(traces)}:", fmt_int(differ))
    assert differ == 0
# A trace kept at a small ratio is kept at every larger one: the decision compares one fixed value with the ratio.
assert kept[0.01] <= kept[0.1] <= kept[0.5] <= kept[1.0]
assert len(kept[1.0]) == len(traces)
```

Output:

```text
messages on baseline day 1, of all messages: 200
messages kept at ratio 0.01, of 200: 5
share of messages kept at ratio 0.01: 2.5%
trace IDs where the replayed and the live decision differ at ratio 0.01, of 200: 0
messages kept at ratio 0.1, of 200: 21
share of messages kept at ratio 0.1: 10.5%
trace IDs where the replayed and the live decision differ at ratio 0.1, of 200: 0
messages kept at ratio 0.5, of 200: 96
share of messages kept at ratio 0.5: 48.0%
trace IDs where the replayed and the live decision differ at ratio 0.5, of 200: 0
messages kept at ratio 1.0, of 200: 200
share of messages kept at ratio 1.0: 100.0%
trace IDs where the replayed and the live decision differ at ratio 1.0, of 200: 0
```

A larger ratio keeps every message that a smaller one kept, and the example checks that first. At 0.1 the backend keeps 21 of the day's 200 messages. The ratio describes the share over many traces, and a single day can land a little above or below it, so the count is the day's and not the ratio's.

**Working rule:** Pick a head ratio only for traffic whose rare cases you can afford to lose. Run the ratio sampler at the root only, under `ParentBased`, and leave every other service on the default sampler or another parent-based one. The [trace SDK specification](https://raw.githubusercontent.com/open-telemetry/opentelemetry-specification/v1.50.0/specification/trace/sdk.md) recommends the ratio sampler "only for root spans", since different SDKs, and different versions of one SDK, can give inconsistent results for the same input. Print the kept share beside its count, as the example does, and never read the share as a count.

## Children follow the root's decision {#parent-based-sampling}

A trace crosses a process boundary, and the contacts server is the second process. [Chapter 4](#traceparent-in-meta) put the trace's identity into each request as `traceparent`, and one of that header's flags is the sampled flag (Trace Context Level 1, the version the book pins). Parent-based sampling makes each span follow its parent's decision. A root span asks the head sampler, and every span below it reads its parent's flag instead of running a ratio of its own. That matters across processes, because the server never sees the assistant's ratio, only the flag.

The contacts server sets no sampler of its own. Its tracer provider takes the SDK's default, with `OTEL_TRACES_SAMPLER` unset, which follows a remote parent's sampled flag: when the flag is set the server samples the span, and when it is not set the server drops it. The probe below turns the assistant's sampler on at the source, at a ratio of 0.5, and counts what the server records under each root.

Example `parent-based-follows-root` (Python 3.13.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""A parent-based sampler at the assistant decides each message's trace once, at its root, and the contacts server follows
that decision through the traceparent. The point rests on the server's count: no span reaches the receiver from a
trace the assistant did not sample."""
import json
import tempfile
from collections import Counter
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.clock import VirtualClock
from lib.report import fmt_int, fmt_share
from lib.sampling import head_ratio, live_provider
from lib.tools import LiveContacts

DAY, PROBES, RATIO = "2026-12-09", 40, 0.5
exporter = InMemorySpanExporter()
provider = live_provider(head_ratio(RATIO), exporter)  # the assistant's provider: its roots sampled at 0.5, children follow
trace.set_tracer_provider(provider)                    # the MCP client span is made by the process's global provider
tracer = provider.get_tracer("ambrewick.assistant")
recorded = {}                                          # trace ID -> whether the assistant's root was recorded
with tempfile.TemporaryDirectory() as folder:
    spans_file = Path(folder) / "contacts-spans.jsonl"  # the server writes here, and the file is read after it exits
    with LiveContacts(VirtualClock(DAY), spans_file) as contacts:
        for number in range(PROBES):
            with tracer.start_as_current_span(f"invoke_agent probe {number}") as root:
                recorded[format(root.get_span_context().trace_id, "032x")] = root.is_recording()
                contacts.find("U0028", "Ana")          # one tool call, inside this root, so its traceparent carries the root's flag
    server = [json.loads(line) for line in spans_file.read_text(encoding="utf-8").splitlines()]
per_trace = Counter(row["trace_id"] for row in server)
sampled = [t for t, yes in recorded.items() if yes]
unsampled = [t for t, yes in recorded.items() if not yes]
print("probes, one assistant root each:", fmt_int(PROBES))
print(f"roots sampled at ratio {RATIO}, of {PROBES}:", fmt_int(len(sampled)))
print(f"share of roots sampled at ratio {RATIO}:", fmt_share(len(sampled), PROBES))
print("contacts server spans under sampled roots:", fmt_int(sum(per_trace[t] for t in sampled)))
print("contacts server spans under unsampled roots:", fmt_int(sum(per_trace[t] for t in unsampled)))
print("unsampled roots with any server span, of the unsampled:", fmt_int(sum(per_trace[t] > 0 for t in unsampled)))
print("sampled roots with any server span, of the sampled:", fmt_int(sum(per_trace[t] > 0 for t in sampled)))
assert all(t in recorded for t in per_trace)  # every server span belongs to a probe's trace
assert not any(per_trace[t] for t in unsampled)     # the server records nothing for an unsampled trace
assert all(per_trace[t] for t in sampled)           # and everything for a sampled one
```

Output:

```text
probes, one assistant root each: 40
roots sampled at ratio 0.5, of 40: 19
share of roots sampled at ratio 0.5: 47.5%
contacts server spans under sampled roots: 39
contacts server spans under unsampled roots: 0
unsampled roots with any server span, of the unsampled: 0
sampled roots with any server span, of the sampled: 19
```

The contacts server made no decision of its own, so a trace was recorded on both sides or on neither. Under the unsampled roots the server recorded 0 spans. Of the 40 probe roots, the assistant sampled 19, and every one of those had server spans, which the example asserts.

**Working rule:** Sample at the root only, and leave every other service on the default sampler or another parent-based one. Two halves of one trace survive apart when another service runs its own ratio, algorithm or SDK version, since two identical samplers at one ratio agree. We would not give a server its own ratio.

## Tail sampling reads the whole trace {#tail-sampling}

Head sampling decides before the message runs, and the failure happens while it runs. Tail sampling decides once the whole trace is in, by what it holds. The rule in this chapter keeps three kinds of trace, in this order. It keeps a trace whose message has an error, in the sense [chapter 8](#how-a-span-records-failure) defines. It keeps a trace whose message ran past the latency objective from [chapter 9](#service-level-objectives), which is 20,000.0 ms. And it keeps a trace whose model calls cost more than the 99th percentile of baseline day 1, which is $0.000115 per message, the costly tail that [chapter 6](#the-expensive-tail) counts. Each kept trace is kept whole, with every span from both processes, and the rule stops once its span budget is spent.

The rule is this book's own code, `TailRule` in `lib/sampling.py`, and it runs at the receiver once a trace's root has arrived. In every trace of the incident day the root is the last span to end, so a trace is whole when its root arrives. That is by end time. Spans can arrive over a network in another order, so a receiver should also wait.

The rule reads each whole trace, so the errors it keeps are the ones it found, not the ones a ratio happened to pick. The timeout window is part of this count. [Chapter 9](#an-alert-that-stays-quiet) showed that a lookup timeout writes ERROR attempts while the user still gets a reply, so those messages have an error in chapter 8's sense. The engineer needs their cause even though no user complained, and the rule keeps them for that reason.

Before the first run, make a prediction. The incident day has messages with an error, and a 10% head sample decides for each of them before anything runs. Predict how many of those messages the head sample keeps: all of them, about a tenth of them, or none. Write the number down, then run the example.

Example `tail-rule-keeps-errors` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""The incident day's failed messages, kept by a 10 percent head sample and by the tail rule. A message failed when a span
in its trace ends with ERROR (chapter 8). The head sample decides before anything runs, so the count it keeps is chance;
the tail rule reads each whole trace and keeps every failed one. A detached root is judged as a trace of its own."""
from lib.clock import NS_PER_SECOND
from lib.dayrun import run_day_traced
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_ms, fmt_share, fmt_usd
from lib.sampling import TailRule, head_sample, message_traces, only_messages
from lib.stats import nearest_rank

MODEL = "Qwen3-4B-Instruct-2507"
BASE, INCIDENT = "2026-12-08", "2026-12-09"
SLOW_NS = 20 * NS_PER_SECOND                        # chapter 9's latency objective: a message over 20 s is slow
price = PriceTable()
# The expensive threshold is baseline day 1's 99th percentile of message cost (nearest rank, PL-5): the incident is
# judged by the day before it, not by itself.
expensive = nearest_rank([t.cost for t in only_messages(message_traces(run_day_traced(BASE, live=False).spans, BASE, MODEL, price))], 99)
live = run_day_traced(INCIDENT)                     # live: the contacts server runs the injected faults over stdio
traces = message_traces(live.spans + live.server, INCIDENT, MODEL, price)  # each trace whole, the server's spans included
messages = only_messages(traces)
failed = [t for t in messages if t.error]
head = head_sample(messages, 0.1)
kept = TailRule(keep_error=True, slow_ns=SLOW_NS, expensive=expensive, budget=sum(len(t.rows) for t in traces)).keep(traces)
print("latency threshold, the 20 s objective:", fmt_ms(SLOW_NS))
print("cost threshold, baseline day 1's 99th percentile per message:", fmt_usd(expensive))
print("messages on the incident day:", fmt_int(len(messages)))
print("detached roots, traces of their own with no message, incident day:", fmt_int(len(traces) - len(messages)))
print("messages with an error, of all messages:", fmt_int(len(failed)))
print("share of messages with an error:", fmt_share(len(failed), len(messages)))
print(f"messages with an error kept by a 10% head sample, of {len(failed)}:", fmt_int(sum(t.error for t in head)))
print("share of messages with an error kept by a 10% head sample:", fmt_share(sum(t.error for t in head), len(failed)))
print(f"messages with an error kept by the tail rule, of {len(failed)}:", fmt_int(sum(t.seq in kept for t in failed)))
print("share of messages with an error kept by the tail rule:", fmt_share(sum(t.seq in kept for t in failed), len(failed)))
assert all(t.seq in kept for t in failed)           # the tail rule keeps every failed message
assert sum(t.error for t in head) < len(failed)     # the head sample loses most of them
assert all(max(r["end_ns"] for r in t.rows if r["parent_span_id"] is None) == max(r["end_ns"] for r in t.rows)
           for t in traces)                         # the root ends last, so a trace is whole when its root arrives (B-83)
```

Output:

```text
latency threshold, the 20 s objective: 20,000.0 ms
cost threshold, baseline day 1's 99th percentile per message: $0.000115
messages on the incident day: 60
detached roots, traces of their own with no message, incident day: 4
messages with an error, of all messages: 17
share of messages with an error: 28.3%
messages with an error kept by a 10% head sample, of 17: 2
share of messages with an error kept by a 10% head sample: 11.8%
messages with an error kept by the tail rule, of 17: 17
share of messages with an error kept by the tail rule: 100.0%
```

The incident day has 60 messages, and 17 of them have an error.

The head sample loses most of those errors. It keeps 2 of them, which is 11.8%. The guess of about a tenth came close here, but the head sample had no way to aim at the errors, so its count was a matter of chance.

The tail rule loses none. It keeps all 17 of them.

A rule that keeps every error can still cost too much, so the book's rule also takes a budget of spans for the day. Spans are what the backend stores, and a trace with many model calls holds many of them. Next, the rule is given a budget that the incident day cannot fit whole: 120 spans against a day of 276.

Example `tail-rule-span-budget` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""The tail rule under a span budget on the incident day: errors first, then the slowest messages, then the costliest, each
kept whole until the budget is spent. The budget of 120 spans is below the 127 the rule would keep with none, so it has
to drop something; the point rests on every error being kept and the slow message with no error being dropped."""
from lib.clock import NS_PER_SECOND
from lib.dayrun import run_day_traced
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.sampling import TailRule, message_traces, only_messages, retained_bytes
from lib.stats import nearest_rank

MODEL = "Qwen3-4B-Instruct-2507"
BASE, INCIDENT = "2026-12-08", "2026-12-09"
BUDGET, SLOW_NS = 120, 20 * NS_PER_SECOND
price = PriceTable()
base = only_messages(message_traces(run_day_traced(BASE, live=False).spans, BASE, MODEL, price))
expensive = nearest_rank([t.cost for t in base], 99)  # the baseline day's 99th percentile of cost, as in the last example
live = run_day_traced(INCIDENT)                     # live: the contacts server runs the injected faults over stdio
traces = message_traces(live.spans + live.server, INCIDENT, MODEL, price)  # each trace whole, the server's rows included
messages = only_messages(traces)
spans = sum(len(t.rows) for t in messages)
kept = TailRule(True, SLOW_NS, expensive, BUDGET).keep(traces)
no_budget = TailRule(True, SLOW_NS, expensive, sum(len(t.rows) for t in traces)).keep(traces)
kept_spans = sum(len(t.rows) for t in traces if t.seq in kept)
dropped = [t for t in messages if t.duration_ns > SLOW_NS and not t.error and t.seq not in kept]
print("spans in the incident day's messages:", fmt_int(spans))
print("spans in messages with an error:", fmt_int(sum(len(t.rows) for t in messages if t.error)))
print("span budget:", fmt_int(BUDGET))
print("spans the tail rule keeps with no budget, incident day:", fmt_int(sum(len(t.rows) for t in traces if t.seq in no_budget)))
print("spans kept under the budget, of all spans:", fmt_int(kept_spans))
print("share of spans kept under the budget:", fmt_share(kept_spans, spans))
for reason in ("error", "slow", "expensive"):
    print(f"messages kept for {reason}, under the budget:", fmt_int(sum(v == reason for v in kept.values())))
print("slow messages with no error, dropped for the budget:", fmt_int(len(dropped)))
print("time of the slowest message dropped for the budget:", fmt_ms(max(t.duration_ns for t in dropped)))
print("messages over the expensive threshold with no error or slow time, incident day:",
      fmt_int(sum(t.cost > expensive and not t.error and t.duration_ns <= SLOW_NS for t in messages)))
print("messages over the expensive threshold with no error or slow time, baseline day 1:",
      fmt_int(sum(t.cost > expensive and not t.error and t.duration_ns <= SLOW_NS for t in base)))
# Retention: bytes per message without content, in the JSON-lines export (capture is off until chapter 12).
per_message, kept_bytes, day_bytes = retained_bytes(base, messages, kept)
print("bytes per message without content, baseline day 1:", fmt_int(per_message))
print("bytes kept under the budget, of the incident day's bytes:", fmt_share(kept_bytes, day_bytes))
assert all(t.seq in kept for t in messages if t.error)  # the budget leaves every error in
assert kept_spans <= BUDGET
assert sum(len(t.rows) for t in traces if t.seq in no_budget) > BUDGET
```

Output:

```text
spans in the incident day's messages: 276
spans in messages with an error: 116
span budget: 120
spans the tail rule keeps with no budget, incident day: 127
spans kept under the budget, of all spans: 116
share of spans kept under the budget: 42.0%
messages kept for error, under the budget: 17
messages kept for slow, under the budget: 0
messages kept for expensive, under the budget: 0
slow messages with no error, dropped for the budget: 1
time of the slowest message dropped for the budget: 22,622.1 ms
messages over the expensive threshold with no error or slow time, incident day: 0
messages over the expensive threshold with no error or slow time, baseline day 1: 0
bytes per message without content, baseline day 1: 2,831
bytes kept under the budget, of the incident day's bytes: 42.6%
```

The budget keeps 116 spans, which is 42.0% of the day's. Those are the spans of the 17 messages with an error, and the rule keeps no slow message and no costly one.

Errors are ranked first, so they take their spans before anything else is considered, and the remainder of the budget is what is left for a slow message. The slow message without an error, which took 22,622.1 ms, holds more spans than that remainder, so the budget drops it. Two assertions in the code hold the rule to this: every error is kept, and the budget binds, since with no budget the rule keeps 127 spans, more than the budget allows.

The budget of 120 spans is the book's choice, not a rule of the method. It is above the spans that the errors take, so every error survives. The messages with an error hold 116 spans between them, so a budget below that would drop one of them, and the rule exists to keep them. A larger budget would also keep the slow message, at the cost of its spans.

The expensive class keeps nothing extra on either day. The number of messages above the expensive threshold with neither an error nor a slow time is 0 on the incident day and 0 on baseline day 1. Every costly message on both recorded days was also an error or a slow message, so the class does no work on them. We keep it in the rule because a costly message with neither mark is possible, and the rule should keep it when one comes. Neither recorded day shows one. The errors this rule keeps are also the traces that chapter 12 scans for personal data, so the rule also decides what that scan reads.

**Working rule:** Keep errors first, and set the budget above the spans they take on a day you have measured, not from a guess. Count the messages that are costly but neither erroneous nor slow before you trust a cost class, and say what a smaller budget would drop.

## Estimate the day's totals from a sample {#estimating-totals-from-a-sample}

Sampling thins spans, so a total summed from the kept spans is smaller than the day, and sampling does not thin the counters. [Chapter 6](#totals-from-metrics-not-spans) showed that summing spans double counts, so the book reads totals from the counters, which the assistant's meter adds to as each model call ends. [Chapter 9](#metrics-the-assistant-exports) reads its alerts from the same meter, so sampling never thins a total or an alert. An estimate from a sample is for a split that the counters cannot make, and a split is only as good as each part's kept count.

Scaling a head sample's total by the inverse of its ratio estimates the whole, because every trace has the same chance of being kept: the kept total, times the inverse of the ratio, estimates the day. The interval is the estimate plus or minus 1.96 standard errors, with the standard error taken from the sampled traces alone. A tail rule keeps some traces whatever the ratio, so its kept set is not a fixed share of the day. Once the head ratio and the tail rule run together ([the decisions below](#choose-what-to-keep-decisions)), the backend holds their union, which is not a head sample, so mark each trace with the reason it was kept and scale only the head sample's traces. This section scales head samples only.

Scaling one 10% sample of baseline day 1 by ten gives an estimate that can be set against the day's full count and against the token counter.

Example `estimate-totals-error` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Estimate baseline day 1's total tokens and cost from a 10 percent head sample, scaled by one over the ratio, with the 95
percent interval (the estimate plus or minus 1.96 standard errors). The estimate is set against the full count, summed over
every message, and against the token counter's total for the day. The point is coverage: over 2,000 independent samples the
interval holds the full count in only some of them, and the printed count says how many."""
from decimal import Decimal

from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from lib.dayrun import RELEASE, run_day_traced
from lib.metrics import USAGE, make_meter_provider, totals
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share, fmt_usd
from lib.sampling import draws_holding, estimate_total, head_sample, message_traces, only_messages

MODEL = "Qwen3-4B-Instruct-2507"
DAY, RATIO, DRAWS, SEED = "2026-12-08", 0.1, 2000, 20261207  # SEED is PL-6's; each draw salts the trace IDs with its number
reader = InMemoryMetricReader()
provider = make_meter_provider(reader, service_instance_id=f"{DAY}-metrics", service_version=RELEASE.service_version)
traced = run_day_traced(DAY, live=False, meter_provider=provider)  # the assistant's live meter counts each call's tokens
traces = only_messages(message_traces(traced.spans, DAY, MODEL, PriceTable()))
counter = totals(reader)
counter_tokens = int(counter[USAGE["input"]]["sum"]) + int(counter[USAGE["output"]]["sum"])
sample = head_sample(traces, RATIO)
full_tokens = sum(t.tokens for t in traces)
full_cost = sum((t.cost for t in traces), Decimal(0))
print(f"messages kept at ratio {RATIO}, of {len(traces)}:", fmt_int(len(sample)))
tokens, tokens_interval = estimate_total([t.tokens for t in sample], RATIO)
print("full count of tokens, all messages:", fmt_int(full_tokens))
print("token counter total for the day, input plus output:", fmt_int(counter_tokens))
print(f"estimated tokens, ratio {RATIO}:", fmt_int(int(tokens)))
print("estimate as a share of the full count, tokens:", fmt_share(tokens, full_tokens))
print("interval as shares of the full count, tokens, low end:", fmt_share(tokens_interval[0], full_tokens))
print("interval as shares of the full count, tokens, high end:", fmt_share(tokens_interval[1], full_tokens))
cost, cost_interval = estimate_total([t.cost for t in sample], RATIO)
print("full cost of the day, Qwen3-4B-Instruct-2507 at the book's rates:", fmt_usd(full_cost))
print(f"estimated cost, ratio {RATIO}:", fmt_usd(cost))
print("estimate as a share of the full cost:", fmt_share(cost, full_cost))
print("interval as shares of the full cost, low end:", fmt_share(cost_interval[0], full_cost))
print("interval as shares of the full cost, high end:", fmt_share(cost_interval[1], full_cost))
assert counter_tokens == full_tokens          # the counter reads each call once, so it matches the root spans
print("samples of the same day, drawn independently:", fmt_int(DRAWS))
held_tokens, held_cost = draws_holding(traces, RATIO, DRAWS, SEED)
print(f"intervals that hold the full count, of {fmt_int(DRAWS)} samples at ratio {RATIO}, tokens:", fmt_int(held_tokens))
print(f"intervals that hold the full count, of {fmt_int(DRAWS)} samples at ratio {RATIO}, cost:", fmt_int(held_cost))
```

Output:

```text
messages kept at ratio 0.1, of 200: 21
full count of tokens, all messages: 109,807
token counter total for the day, input plus output: 109,807
estimated tokens, ratio 0.1: 98,090
estimate as a share of the full count, tokens: 89.3%
interval as shares of the full count, tokens, low end: 38.7%
interval as shares of the full count, tokens, high end: 140.0%
full cost of the day, Qwen3-4B-Instruct-2507 at the book's rates: $0.007563
estimated cost, ratio 0.1: $0.005524
estimate as a share of the full cost: 73.0%
interval as shares of the full cost, low end: 29.6%
interval as shares of the full cost, high end: 116.5%
samples of the same day, drawn independently: 2,000
intervals that hold the full count, of 2,000 samples at ratio 0.1, tokens: 1,843
intervals that hold the full count, of 2,000 samples at ratio 0.1, cost: 1,854
```

The estimate starts from the 10% head sample of baseline day 1, which keeps 21 of the day's messages, and scales their tokens by ten. The full count is 109,807 tokens, and the day's token counter, which [chapter 6](#totals-from-metrics-not-spans) reads for totals, adds up to the same figure: 109,807.

One sample gives one estimate, and the interval says where the day's full count could lie given how the sample was drawn. This interval is built from the sample's own standard error, and it is not [chapter 7's bootstrap interval](#tail-percentiles-with-intervals). The token estimate from that one sample is 98,090 tokens.

The 95% interval runs from 38.7% to 140.0% of the full count, and it is too wide to act on: a sample of 21 messages leaves the total anywhere across that range.

The interval is also short of its label. Of 2,000 samples of the same day, drawn independently, 1,843 have an interval that holds the full count, against the 95% the interval is built for.

The cost estimate is a separate sum over the same sample. It is $0.005524, against a full cost of $0.007563 for the day, priced at the book's table `book-2026-11-02`.

Its interval runs from 29.6% to 116.5% of the full cost, and 1,854 of the same samples hold it.

Varying the ratio shows how the error depends on how much is kept.

Example `figure-sampling-error-by-ratio` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Draw the error of a head sample's estimate of baseline day 1's total tokens against the sampling ratio, with the 95 percent
interval (chapter 11, `estimating-totals-from-a-sample`). The interval narrows as the ratio rises, and at ratio 1.0 every message
is kept, so the interval has no width. The points the prose names are printed, so a reader can read them off the lines."""
import math

from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share
from lib.sampling import estimate_total, head_sample, message_traces, only_messages

MODEL = "Qwen3-4B-Instruct-2507"
DAY = "2026-12-08"
RATIOS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)
traces = only_messages(message_traces(run_day_traced(DAY, live=False).spans, DAY, MODEL, PriceTable()))
full = sum(t.tokens for t in traces)
points = []                                         # (ratio, estimate share, interval low share, interval high share)
for ratio in RATIOS:
    sample = head_sample(traces, ratio)
    estimate, (low, high) = estimate_total([t.tokens for t in sample], ratio)
    points.append((ratio, 100 * estimate / full, 100 * low / full, 100 * high / full))
    if ratio in (0.01, 0.1, 0.5):
        print(f"messages kept at ratio {ratio}, of {len(traces)}:", fmt_int(len(sample)))
        print(f"estimate as a share of the full count, ratio {ratio}:", fmt_share(estimate, full))
        print(f"interval low end as a share of the full count, ratio {ratio}:", fmt_share(low, full))
        print(f"interval high end as a share of the full count, ratio {ratio}:", fmt_share(high, full))
print("full count of tokens, all messages:", fmt_int(full))
xs, estimate_share, low, high = zip(*points)
fig, ax = new_figure(height=2.8)
ax.fill_between(xs, low, high, color=MUTED, alpha=0.35, linewidth=0, label="95% interval")
ax.plot(xs, estimate_share, color=ACCENT, linewidth=1.8, marker="o", markersize=3, label="estimate, head sample")
ax.axhline(100, color=INK, linewidth=1, linestyle=":", label="full count")
ax.set_xscale("log")
ax.set_xticks(RATIOS, [f"{r:g}" for r in RATIOS])
ax.set_xlabel("sampling ratio (log scale)")
ax.set_ylabel("estimate, % of full count")
bottom, top = float(min(low)), float(max(high))      # the axis starts at the lowest interval end, not at zero
pad = 0.1 * (top - bottom)
ax.set_ylim(bottom - pad, top + 2 * pad)            # headroom above the widest interval, where the legend sits
ax.legend(loc="upper right", ncol=3, frameon=False)
save(fig, "sampling-error-by-ratio")
assert all(math.isclose(p[1], 100) for p in points if p[0] == 1.0)   # at ratio 1 every message is kept, so no error
assert all(math.isclose(p[2], p[3]) for p in points if p[0] == 1.0)  # and the interval has no width
```

Output:

```text
messages kept at ratio 0.01, of 200: 5
estimate as a share of the full count, ratio 0.01: 251.5%
interval low end as a share of the full count, ratio 0.01: -4.4%
interval high end as a share of the full count, ratio 0.01: 507.5%
messages kept at ratio 0.1, of 200: 21
estimate as a share of the full count, ratio 0.1: 89.3%
interval low end as a share of the full count, ratio 0.1: 38.7%
interval high end as a share of the full count, ratio 0.1: 140.0%
messages kept at ratio 0.5, of 200: 96
estimate as a share of the full count, ratio 0.5: 97.5%
interval low end as a share of the full count, ratio 0.5: 79.4%
interval high end as a share of the full count, ratio 0.5: 115.5%
full count of tokens, all messages: 109,807
figure: figures/sampling-error-by-ratio.svg
```

Figure 11.1 draws the same estimate at eight ratios, and its band closes as the ratio reaches 1.0. At the left, 5 messages are kept, and the estimate is 251.5% of the full count. Its interval runs from -4.4% to 507.5%, so the low end falls below zero, where the normal approximation fails with so few kept traces.

At 0.1, 21 messages are kept, the estimate is 89.3% of the full count, and the interval runs from 38.7% to 140.0%.

Ratio 0.5 keeps 96 messages, and the estimate is 97.5% of the full count, with an interval from 79.4% to 115.5%. At ratio 1.0 every message is kept, so the estimate is exact and the interval has no width, which the example asserts.

*Figure 11.1. The token estimate from a head sample, as a share of the full count, at eight sampling ratios, with its 95% interval.*

![A line of the estimated token total, as a share of the full count, against the sampling ratio on a log scale, with a shaded 95% interval; the band narrows overall as the ratio rises and closes at ratio 1.0](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.1/figures/sampling-error-by-ratio.svg)

The interval measures the sampling's chance on this one day. Whether another day would give the same total is a different question, and this interval does not answer it.

**Working rule:** Scale only the traces the head ratio kept, by the inverse of its ratio, print the interval beside the estimate, and check the estimate against the counter total for the same day when one exists. Use a sampled estimate only for a split that the counters cannot make, and never for a total the counters already hold.

## What a kept trace costs to hold {#retention}

Retention is how long the backend keeps each kind of telemetry. [Data Governance as Code](https://rollingedition.com/concepts/data-governance/retention) states the same idea for a platform's data: how long each kind of data is kept. This chapter applies it to telemetry only, and it sets no period. The period depends on how far back an engineer must look after an incident and on what the storage costs, and both belong to the team that runs the backend.

A period is paid for in bytes, so the [tail-rule example](#tail-sampling) that prints the kept share also measures what a message's trace takes. On baseline day 1 a message's span rows take 2,831 bytes in the JSON-lines export, with capture off, and the count holds span rows only. The kept traces of the incident day hold 42.6% of that day's bytes, against 42.0% of its spans. Here the bytes follow the spans closely, so the kept share of spans is a fair guide to the kept share of bytes on this day.

The count leaves content out. Capture is off until chapter 12, which turns it on for one named purpose and measures what prompts and replies add to this same export path. That byte count is therefore a lower bound for a message's trace. Sampling also decides only which spans reach the backend. It does not settle what the process does with the spans it drops, and chapter 12 shows what the upload hook does with content in those spans.

**Working rule:** Measure bytes per message on your own export, without content and then with any content you plan to keep, before you set a period. Keep the period beside the bytes it multiplies, and name what the bytes leave out.

## Where sampling goes wrong in production {#choose-what-to-keep-in-production}

A head ratio does what its share says and nothing more. It keeps the same expected share on a quiet day and on a day with a new failure, because its decision never reads a message. The kept set of the [tail rule](#tail-sampling) moves with the failures, which is why this chapter uses both. A head sample still has a use. It keeps a sample of ordinary traces, so the typical message can be read, and its decision needs no look at the message.

The two thresholds of the [tail rule](#tail-sampling) come from other parts of the book, and they move. The latency line is chapter 9's objective. The expensive line is the baseline day's 99th percentile of cost, which a release that changes cost moves with it. The expensive line is therefore read again after each release that changes what a message costs, and not kept from the first baseline.

The rule needs whole traces, and it judges the trace it has. A [detached root](#lost-context) starts a trace of its own, and the rule judges that trace by what it holds. On the incident day the example counts 4 such traces, each an MCP `notifications/cancelled` span sent after a timed-out lookup with no context current, and each judged alone. The rest of its message sits in another trace, which the rule may keep or drop on other grounds. The check covers the shape of the book's traces alone, and production may hold other shapes that it does not show.

**Working rule:** Judge a rule by what it keeps on the days that went wrong, not on a quiet day, and read each threshold again after a release that changes what it measures.

## The decisions this chapter made {#choose-what-to-keep-decisions}

The decisions below follow from one fact the examples show: a sampler's share is set before the message is known, so keeping the messages an engineer needs takes a rule that reads each whole trace.

- We keep the head ratio and the tail rule together. The head sample alone kept 2 of the 17 messages with an error, and the tail rule keeps all of them.
- The tail rule keeps errors first, then slow messages, then costly ones, under a budget of 120 spans. The budget sits above the spans the errors take, and one below them would drop an error.
- Every service samples with parent-based sampling, and only the root's service makes the decision. The contacts server follows the assistant's flag and runs no ratio of its own.
- [Chapter 6's rule for totals](#tokens-and-cost-decisions) holds here. A sampled estimate, printed with its interval, is for a split the counters cannot make, and it is only as good as each part's kept count.
- The retention period belongs to the team. We measure the bytes per message first, without content, and chapter 12 adds what content costs.

Two of these are judgements that the examples cannot settle. The budget of 120 spans is one, because it is the book's number and not a measured limit. Parent-based sampling is the other. The probe checks the SDK's default sampler on one server, and it says nothing about services that this book does not run. A reader who copies the rule should measure their own day first: the spans their errors take, the bytes per message, and the messages that are costly but neither erroneous nor slow. Only then should any number in this chapter become a setting.

What the chapter learned is narrower than a rule about sampling. A head sampler's share is fixed by the trace ID before the message runs, so only a rule that reads each whole trace keeps the messages an engineer needs. A total from the kept traces is an estimate, and it carries its interval wherever it is printed.

**Working rule:** Before you copy a sampling setting, run its example on a day you have recorded yourself, and keep each setting with the example that tests it.
