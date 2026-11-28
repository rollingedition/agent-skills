---
title: "Observability for LLM Applications"
chapter: "Set alerts on the assistant's metrics"
chapter_id: alerts-on-metrics
book: observability-for-llm-applications
edition: 2026.11.4
verified: 2026-11-23
edition_code: XFJ3-KNEQ
canonical: https://rollingedition.com/observability-for-llm-applications/alerts-on-metrics
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Set alerts on the assistant's metrics,” chapter 9 of Observability for LLM Applications, Edition 2026.11.4, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/alerts-on-metrics. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Set alerts on the assistant's metrics

By the end of this chapter you can set two alerts on a service's metrics, test each one on a normal day and on an incident day, and say what each one misses. On the incident day, lookups to the contacts team's server start timing out at 13:00 UTC. The 13 messages in the hour to 13:15 all got a reply, although both attempts of each lookup timed out. Beside that, the model's rate limit at 15:30 left 11 of 15 messages in its hour with no reply. Which of those numbers would wake someone, and would the same number wake someone on a normal day? The faults on the incident day were injected, at windows the case sets, so nothing below is a record of an outage or a measure of any real service.

The assistant is Ambrewick's back end, and it records its own metrics as it runs. An alert can read those metrics without reading a single span. A metric is cheap to keep for every minute of a day, because it holds a few numbers for each attribute set ([chapter 6](#totals-from-metrics-not-spans) defines the form) and not one record for each message. That trade has a cost, which the chapter measures as it goes: a metric can say how many messages failed, but not which ones, and not why.

## The metrics the assistant exports {#metrics-the-assistant-exports}

A trace answers what happened to one message. An alert needs a different kind of record: a number for each minute of the day that moves when many messages move. [Chapter 6](#totals-from-metrics-not-spans) defines the metric, counter and histogram that this chapter uses, and reads the token totals from them. This section sets out which instruments the assistant records and what each one counts.

The assistant has a meter, and the meter records each operation as the operation ends. There are three duration histograms, one for each kind of operation. A message is one `invoke_agent` operation, so `gen_ai.invoke_agent.duration` holds one point for each message. A model call is one `chat` operation, and `gen_ai.client.inference.duration` holds one point for each call attempt. A tool attempt is one `execute_tool` operation, and `gen_ai.execute_tool.duration` holds one point for each. The names and units come from the [GenAI conventions' metrics page](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/gen-ai-metrics.md), at version 0.1.0. The model-call and tool histograms are defined on the [client inference](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/client-inference.md) and [execute tool](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/execute-tool.md) pages that the same version publishes. Each duration histogram takes the unit of seconds, and the conventions ask that a failed operation set `error.type`. A message that got no reply therefore carries `error.type` on its point in the message histogram, and the alert counts on that attribute.

The meter also records each model call's tokens, in the counters and per-call histograms that chapter 6 reads. This chapter's alert does not use them, but the same meter writes them, so the export below includes them.

The meter is live. The alert reads it while the day runs, and each point reaches the meter when its operation ends. Each example in this chapter reads the meter in the same process that made the measurements. A production alert reads the same metrics once they leave the process, through whatever pipeline carries them, and that pipeline is outside this book.

Baseline day 1 is a normal day with no injected fault, so it is the right day to check that the meter agrees with the spans. The replay runs the day with the meter attached, and the export is then read back and set beside the spans' own counts.

Example `assistant-metrics-export` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""The metrics the assistant exports, from its live meter (chapter 9, `metrics-the-assistant-exports`).

The assistant records each operation as it ends: a message is one `invoke_agent` operation, a model call one `chat`, a
tool attempt one `execute_tool`, and each model call's tokens go to the token counters and histograms. The names and
units come from the pinned registry (lib.genai.METRICS). The export must not lose what the spans count, so the sums
are checked against the spans' own sums."""
from lib.dayrun import run_day_traced
from lib.genai import METRICS
from lib.metrics import DURATION, USAGE, make_alert_meter_provider, totals
from lib.report import fmt_int
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

DAY = "2026-12-08"
reader = InMemoryMetricReader()
provider = make_alert_meter_provider(reader, service_instance_id=f"{DAY}-export")
traced = run_day_traced(DAY, live=False, meter_provider=provider)   # no faults on this day, so no live contacts server

reader.collect()
series = {}                                        # metric name: its number of series (one per attribute set)
for resource in reader.get_metrics_data().resource_metrics:
    for scope in resource.scope_metrics:
        for metric in scope.metrics:
            series[metric.name] = len(metric.data.data_points)
for name in sorted(series):
    print(f"series, {name}:", fmt_int(series[name]))
    print(f"unit, {name}:", METRICS[name]["unit"])

spans = lambda op: [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == op]
messages, calls, attempts = spans("invoke_agent"), spans("chat"), spans("execute_tool")
print("messages, invoke_agent operations:", fmt_int(len(messages)))
print("model calls, chat operations:", fmt_int(len(calls)))
print("tool attempts, execute_tool operations:", fmt_int(len(attempts)))
sums = totals(reader)
print("input tokens, counter total:", fmt_int(int(sums[USAGE["input"]]["sum"])))
print("input tokens, summed over chat spans:", fmt_int(sum(c["attributes"]["gen_ai.usage.input_tokens"] for c in calls)))
print("message durations, histogram count:", fmt_int(sums[DURATION["invoke_agent"]]["count"]))

assert sums[DURATION["invoke_agent"]]["count"] == len(messages)     # one point per message, none lost
assert sums[DURATION["chat"]]["count"] == len(calls)                # one point per model call attempt
assert sums[DURATION["execute_tool"]]["count"] == len(attempts)     # one point per tool attempt
assert sums[USAGE["input"]]["sum"] == sum(c["attributes"]["gen_ai.usage.input_tokens"] for c in calls)
```

Output:

```text
series, gen_ai.client.inference.duration: 1
unit, gen_ai.client.inference.duration: s
series, gen_ai.client.inference.operation.input_tokens: 1
unit, gen_ai.client.inference.operation.input_tokens: {token}
series, gen_ai.client.inference.operation.output_tokens: 1
unit, gen_ai.client.inference.operation.output_tokens: {token}
series, gen_ai.client.inference.usage.cache_read.input_tokens: 1
unit, gen_ai.client.inference.usage.cache_read.input_tokens: {token}
series, gen_ai.client.inference.usage.input_tokens: 1
unit, gen_ai.client.inference.usage.input_tokens: {token}
series, gen_ai.client.inference.usage.output_tokens: 1
unit, gen_ai.client.inference.usage.output_tokens: {token}
series, gen_ai.execute_tool.duration: 1
unit, gen_ai.execute_tool.duration: s
series, gen_ai.invoke_agent.duration: 1
unit, gen_ai.invoke_agent.duration: s
messages, invoke_agent operations: 200
model calls, chat operations: 321
tool attempts, execute_tool operations: 10
input tokens, counter total: 104,811
input tokens, summed over chat spans: 104,811
message durations, histogram count: 200
```

The sentence to keep is that the export and the spans agree. The counter for input tokens totals 104,811 tokens, and the model calls' spans add up to the same 104,811. The message histogram holds one point for each message the day sent, 200 in all, and the example's assertions check that count against the spans. The histogram holds 1 series on this day, one attribute set for a normal message. The next section explains why that number is the one to watch.

**Working rule:** Take an alert's counts from the meter, which records each operation as it ends. Assert once, in a test, that the meter's sums equal the spans' sums, and after that query the metric every time the alert runs.

## Cardinality {#cardinality}

A metric is stored and queried one series at a time. Every distinct combination of attribute values opens a new series, and a dashboard draws one line for each. An attribute that takes a few values adds a few lines. An attribute that takes a new value for every user adds a line for every user, and that is the case the rest of this section examines.

A metric's **cardinality** is the number of distinct attribute combinations it is recorded with, each a series to store.

The meter keeps five attributes on each point, and no others: the error type, the agent's name, the operation's name, the [prompt version](#release-markers-in-the-spans) and the model's name. The conventions' registry lists these as the metric attributes, and the table below calls them the registry's attributes. So the live meter gives one series on a normal day, as [the previous section](#metrics-the-assistant-exports) printed. The two attributes an operator most often wants, the route and the user, are not on the meter's points. Adding each of them to the message histogram, from the spans of the same messages, shows what each would cost.

Example `cardinality-of-attributes` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""Which attributes may label the assistant's duration metric (chapter 9, `cardinality`).

A metric keeps one series for each distinct set of attribute values, and each series is stored and queried. The
registry's attributes give one series for a message's operation on a normal day. A route gives a few more. A user ID
gives one series per user, so the count grows with the traffic and no dashboard can read it. The assistant's live meter
keeps the registry's attributes only, so its count is the first line. The other two are what the same messages would
give with another attribute added, counted from their spans."""
from lib.dayrun import run_day_traced
from lib.metrics import DURATION, METRIC_ATTRIBUTES, make_alert_meter_provider
from lib.report import fmt_int
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

DAY = "2026-12-08"
reader = InMemoryMetricReader()
provider = make_alert_meter_provider(reader, service_instance_id=f"{DAY}-cardinality")
traced = run_day_traced(DAY, live=False, meter_provider=provider)  # the assistant's live meter, registry attributes only
messages = [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == "invoke_agent"]
users = {row["attributes"]["ambrewick.user.id"] for row in messages}
routes = {row["attributes"]["ambrewick.route"] for row in messages if row["attributes"].get("ambrewick.route")}
print("messages:", fmt_int(len(messages)))
print("distinct users:", fmt_int(len(users)))
print("distinct routes:", fmt_int(len(routes)))


def series(reader, name: str | None = None) -> int:
    """The number of series a reader holds, for one metric when a name is given (one per distinct attribute set)."""
    reader.collect()
    return sum(len(metric.data.data_points) for resource in reader.get_metrics_data().resource_metrics
               for scope in resource.scope_metrics for metric in scope.metrics if name in (None, metric.name))


def series_with(extra: tuple[str, ...]) -> int:
    """The number of series the duration histogram holds when each message carries the registry's attributes and
    the `extra` ones. Values are the messages' real durations; only the count of attribute sets matters here."""
    own = InMemoryMetricReader()
    histogram = make_alert_meter_provider(own, service_instance_id=f"{DAY}-cardinality").get_meter("cardinality") \
        .create_histogram(DURATION["invoke_agent"], unit="s")
    for row in messages:
        attrs = row["attributes"]
        kept = {key: attrs[key] for key in METRIC_ATTRIBUTES + extra if key in attrs}
        histogram.record((row["end_ns"] - row["start_ns"]) / 1_000_000_000, kept)
    return series(own)


registry = series(reader, DURATION["invoke_agent"])
with_route = series_with(("ambrewick.route",))
with_user = series_with(("ambrewick.user.id",))
print("series, registry attributes:", fmt_int(registry))
print("series, registry attributes and route:", fmt_int(with_route))
print("series, registry attributes and user ID:", fmt_int(with_user))
assert registry == 1                       # on a normal day every message is a success with one attribute set
assert with_user == len(users)             # a user ID makes one series per user, and no two users share one
assert with_user > with_route > registry   # each attribute that varies multiplies the series
```

Output:

```text
messages: 200
distinct users: 121
distinct routes: 7
series, registry attributes: 1
series, registry attributes and route: 7
series, registry attributes and user ID: 121
```

The same 200 messages come from 121 distinct users, and they fall into 7 routes. The message histogram's series, for each set of attributes, are these.

| Attributes on the message histogram | Series |
| --- | --- |
| The registry's attributes | 1 |
| The registry's attributes and the route | 7 |
| The registry's attributes and the user ID | 121 |

A route adds a fixed, small number of lines, one for each of the 7 values the book uses. The user adds a line for each person who sent a message. The count grows with the users, and on a service with more of them it passes the SDK's limit, which the next paragraph describes.

The software has a limit as well. The OpenTelemetry metrics SDK stops at a default of 2,000 series for each metric stream in one collection cycle, and any attribute set past that limit falls into a single overflow series ([Metrics SDK, v1.45.0](https://raw.githubusercontent.com/open-telemetry/opentelemetry-specification/v1.45.0/specification/metrics/sdk.md)). The overflow series keeps the total right and hides the detail, so an operator who sees it has lost the lines that would have answered the question.

For that reason the assistant's metric takes no user ID, and this book never adds one. A user's messages are answered in traces, where one message is one record and its user is one attribute among many. A question about one user's latency is a question for a trace. The alert answers the question about the whole assistant's service.

**Working rule:** Label a metric only with values from a set you can list before launch. Count the series with each candidate attribute on a day of real traffic, and reject any attribute whose count grows with the users.

## Service-level objectives {#service-level-objectives}

An alert that says too many messages failed needs a line to measure them against, and a pace at which failing is still acceptable. An objective alone pages no one, so an alert measures how fast the failures use up the share that the objective leaves.

An **objective** is the share of messages that must succeed, or finish within a time, over a period; the **error budget** is the share it lets fail; the **burn rate** is how fast failures spend it, where 1 spends it exactly by the period's end.

The assistant has two objectives. The first is for failed messages. Over 30 days, 99% of messages must get a reply, which leaves an error budget of 1.0%; the period sets the arithmetic and forecasts no traffic. A message fails, for the objective, when its user got no reply; a retry that recovered is not a failure. That is narrower than [chapter 8's error](#how-a-span-records-failure). Under the span rule, a message whose first model request was refused and whose second request got a reply has an error, and so does a message whose lookup timed out on both attempts and whose model replied anyway. This objective counts neither, because the user got a reply in both cases. A [fallback reply](#where-the-time-went-in-twenty-messages) is a reply too, so the objective does not count it either. Whether a fallback reply went to the right scenario is a question for [chapter 8's wrong-route check](#wrong-routes-against-labels).

The second objective is for latency: over 30 days, 95% of messages must finish within 20 seconds, a line set above the slowest messages of a normal day, which leaves a latency budget of 5.0%. The number comes from the tail that [chapter 7](#tail-percentiles-with-intervals) measured on the recordings that [chapter 1](#replay-and-the-virtual-clock) introduces, so every time here is a recorded time on that replay's virtual clock. On baseline day 1 the 95th percentile (p95, by nearest rank) of message times is 18,351.2 ms, over 200 messages, which sits under the 20-second objective. The conventions advise edges for the `invoke_agent` duration histogram, as a SHOULD, from 0.1 to 86,400 s, which puts 12.8 and 25.6 either side of 20 and no edge at 20. The assistant's meter keeps its own edges, 0.5 to 60 s, set by a view, so the 20-second objective sits on one and the count within it is exact. [Chapter 7](#histogram-buckets-and-what-they-hide) shows what an estimate between two edges can do to a tail.

Baseline day 1 shows what the two objectives leave on a normal day.

Example `slo-and-budget` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""The assistant's two objectives, and the error budget each one leaves (chapter 9, `service-level-objectives`).

The error objective: 99% of messages get a reply. A message that ended with no reply has `error.type` on its duration
point, and it spends the budget. The latency objective: 95% of messages finish within 20 seconds, the book's edge
(chapter 7). The edge sits above baseline day 1's p95, so a normal day meets it. Both are read from the metrics that the
alert reads, on the same day. The 30-day period is the arithmetic's period, not a traffic forecast."""
from decimal import Decimal

from lib.dayrun import run_day_traced
from lib.metrics import DayMeter, burn_rate, tallies_by_tick
from lib.report import fmt_burn, fmt_int, fmt_ms, fmt_share
from lib.stats import nearest_rank

DAY = "2026-12-08"
ERROR_SLO, LATENCY_SLO, PERIOD_HOURS = 0.99, 0.95, 30 * 24
meter = DayMeter(DAY)                                  # the assistant's live meter, read after each message
traced = run_day_traced(DAY, live=False, meter_provider=meter.provider, after_message=meter.after)
day = tallies_by_tick(meter.marks, DAY)[-1][1]         # the last tick's cumulative tally is the whole day
durations = sorted(row["end_ns"] - row["start_ns"] for row in traced.spans
                   if row["attributes"].get("gen_ai.operation.name") == "invoke_agent")
p95 = nearest_rank(durations, 95)

print("error objective, share of messages with a reply:", fmt_share(round(ERROR_SLO * 100), 100))
print("error budget, share of messages that may fail:", fmt_share(round((1 - ERROR_SLO) * 100), 100))
print("latency objective, share of messages within 20 s:", fmt_share(round(LATENCY_SLO * 100), 100))
print("latency budget, share of messages that may run over 20 s:", fmt_share(round((1 - LATENCY_SLO) * 100), 100))
print("messages, baseline day 1:", fmt_int(day.requests))
print("messages with no reply:", fmt_int(day.failed), "of", fmt_int(day.requests))
print("messages within 20 s:", fmt_int(day.within), "of", fmt_int(day.requests), "share", fmt_share(day.within, day.requests))
print("messages over 20 s:", fmt_int(day.slow), "of", fmt_int(day.requests))
print("error budget spent over the day, burn:", fmt_burn(burn_rate(day.failed, day.requests, ERROR_SLO)))
print("latency budget spent over the day, burn:", fmt_burn(burn_rate(day.slow, day.requests, LATENCY_SLO)))
print("p95 of message times, nearest rank, n:", fmt_int(len(durations)), "messages")
print("p95 of message times:", fmt_ms(p95))
print("share of the 30-day budget a 1-hour page at burn 14.4 spends:", fmt_share(Decimal("14.4") * 1, PERIOD_HOURS))

assert day.failed == 0                               # a normal day has no message without a reply
assert day.within / day.requests >= LATENCY_SLO      # and meets the latency objective
assert p95 <= 20 * 1_000_000_000                     # the edge sits above the day's p95 (chapter 7, P-24)
```

Output:

```text
error objective, share of messages with a reply: 99.0%
error budget, share of messages that may fail: 1.0%
latency objective, share of messages within 20 s: 95.0%
latency budget, share of messages that may run over 20 s: 5.0%
messages, baseline day 1: 200
messages with no reply: 0 of 200
messages within 20 s: 194 of 200 share 97.0%
messages over 20 s: 6 of 200
error budget spent over the day, burn: 0.0
latency budget spent over the day, burn: 0.6
p95 of message times, nearest rank, n: 200 messages
p95 of message times: 18,351.2 ms
share of the 30-day budget a 1-hour page at burn 14.4 spends: 2.0%
```

Both objectives hold on the normal day, and the code asserts it. Of the day's messages, 0 of 200 got no reply, and 6 of 200 ran over 20 seconds.

Over the whole day the error burn is 0.0, and the latency burn is 0.6. Both sit below 1, which is the pace the objective allows. Those are the burns an alert would read on a quiet day, and the next sections use the same two objectives.

**Working rule:** Set each objective from the numbers of a normal day, and check that the normal day meets it before any alert reads it. Print the objective's error rule beside its count, so a reader can tell it from chapter 8's span rule.

## Burn rate {#burn-rate}

A burn rate is a speed, not a count. Fourteen failures mean little until you know how many messages they came from and how large the [error budget](#service-level-objectives) is. For a window, the burn rate is the window's failed share of messages divided by the error budget. The failed share is a count over a count, so the burn is one more division, and it is a number that can be compared across windows of different sizes.

The windows in this section are on virtual time. The one-hour window and the five-minute window are read at each five-minute tick of the day, and each window's count is the difference between two cumulative reads of the same histogram. A histogram only grows, so a window's messages are what the histogram added between the two reads. The example reads the meter after each message and adds the reads up for each tick. That is how a dashboard reads a rate from a counter that only grows while the process runs.

Run over the incident day's three injected windows, the example below treats each window as one fault: the contacts server's timeouts, the model's rate limit, and the contacts server's error replies. For each window it prints the messages in the hour up to the first tick after the window, how many of them got no reply, and the burns over the hour and over five minutes. The burns are the highest from the window to five minutes after it.

Example `burn-rate-by-window` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""The burn in each window on the incident day (chapter 9, `burn-rate`).

A burn rate is how fast a window spends the error budget. The windows are on virtual time: one hour (the long window)
and five minutes (the short one), each read as the difference between two cumulative reads of the metric at 5-minute
ticks. The live contacts server injects the three incident windows (lib.inject). The counts in each window are checked
against the spans' own counts, so the metric and the spans agree on what happened."""
from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.inject import load_incidents
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, STEP_NS, HOUR_NS = "2026-12-09", 300 * 1_000_000_000, 3600 * 1_000_000_000
MIN_REQUESTS = 10                                     # a burn counts only over an hour with this many messages (alert)
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
traced = run_day_traced(DAY, meter_provider=meter.provider, after_message=meter.after)  # live: faults on virtual time
midnight = VirtualClock(DAY).now_ns
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed")   # objective 99%: budget 1%
slow = alert_verdicts(tallies, slo=0.95, measure="slow")       # objective 95% within 20 s: budget 5%
messages = [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == "invoke_agent"]


def clock(ns: int) -> str:
    """A virtual time as hours, minutes and seconds UTC, from the day's midnight."""
    offset = (ns - midnight) // 1_000_000_000
    return f"{offset // 3600:02d}:{offset % 3600 // 60:02d}:{offset % 60:02d}"


for incident in load_incidents():
    first = -(-(incident.end_ns - midnight) // STEP_NS)     # the first tick at or after the window's end, 1-based
    error, latency = errors[first - 1], slow[first - 1]
    near = [v for v in errors if incident.start_ns < v.tick_ns <= incident.end_ns + STEP_NS]
    counted = {v.tick_ns for v in near if v.long.requests >= MIN_REQUESTS}   # the hours a page could read
    print(f"{incident.incident_id}, window:", f"{clock(incident.start_ns)} to {clock(incident.end_ns)} UTC")
    print(f"{incident.incident_id}, first tick after the window:", clock(error.tick_ns))
    print(f"{incident.incident_id}, messages in the hour to that tick:", fmt_int(error.long.requests))
    print(f"{incident.incident_id}, messages with no reply in that hour:", fmt_int(error.long.bad))
    print(f"{incident.incident_id}, error burn, 1 hour:", fmt_burn(error.long.burn))
    print(f"{incident.incident_id}, error burn, 1 hour, highest from the window to 5 minutes after it:",
          fmt_burn(max(v.long.burn for v in errors if v.tick_ns in counted)))
    print(f"{incident.incident_id}, error burn, 5 minutes, highest from the window to 5 minutes after it:",
          fmt_burn(max(v.short.burn for v in errors if v.tick_ns in counted)))
    print(f"{incident.incident_id}, messages over 20 s in that hour:", fmt_int(latency.long.bad))
    print(f"{incident.incident_id}, latency burn, 1 hour, highest from the window to 5 minutes after it:",
          fmt_burn(max(v.long.burn for v in slow if v.tick_ns in counted)))
    in_hour = [row for row in messages if error.tick_ns - HOUR_NS < row["end_ns"] <= error.tick_ns]
    assert len(in_hour) == error.long.requests                                              # the metric's count
    assert sum("error.type" in row["attributes"] for row in in_hour) == error.long.bad      # the spans' failures
```

Output:

```text
inc-contacts-timeout, window: 13:00:00 to 13:12:00 UTC
inc-contacts-timeout, first tick after the window: 13:15:00
inc-contacts-timeout, messages in the hour to that tick: 13
inc-contacts-timeout, messages with no reply in that hour: 0
inc-contacts-timeout, error burn, 1 hour: 0.0
inc-contacts-timeout, error burn, 1 hour, highest from the window to 5 minutes after it: 0.0
inc-contacts-timeout, error burn, 5 minutes, highest from the window to 5 minutes after it: 0.0
inc-contacts-timeout, messages over 20 s in that hour: 3
inc-contacts-timeout, latency burn, 1 hour, highest from the window to 5 minutes after it: 4.6
inc-rate-limit, window: 15:30:00 to 15:31:30 UTC
inc-rate-limit, first tick after the window: 15:35:00
inc-rate-limit, messages in the hour to that tick: 15
inc-rate-limit, messages with no reply in that hour: 11
inc-rate-limit, error burn, 1 hour: 73.3
inc-rate-limit, error burn, 1 hour, highest from the window to 5 minutes after it: 73.3
inc-rate-limit, error burn, 5 minutes, highest from the window to 5 minutes after it: 91.7
inc-rate-limit, messages over 20 s in that hour: 1
inc-rate-limit, latency burn, 1 hour, highest from the window to 5 minutes after it: 1.3
inc-mcp-error, window: 17:00:00 to 17:10:00 UTC
inc-mcp-error, first tick after the window: 17:10:00
inc-mcp-error, messages in the hour to that tick: 16
inc-mcp-error, messages with no reply in that hour: 0
inc-mcp-error, error burn, 1 hour: 0.0
inc-mcp-error, error burn, 1 hour, highest from the window to 5 minutes after it: 0.0
inc-mcp-error, error burn, 5 minutes, highest from the window to 5 minutes after it: 0.0
inc-mcp-error, messages over 20 s in that hour: 3
inc-mcp-error, latency burn, 1 hour, highest from the window to 5 minutes after it: 4.6
```

The tool attempts in those hours come from the meter's own tool histogram, `gen_ai.execute_tool.duration`, which the next example reads after each message in the same way.

Example `tool-attempts-by-window` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""The tool attempts in each incident window, read from the assistant's meter (chapter 9, `burn-rate-by-window`).

The meter records gen_ai.execute_tool.duration once for each tool attempt. The example reads that histogram after each
message, so a message's attempts count at its reply, as the alert's ticks do. For each incident window it prints the
attempts in the hour up to the first tick after the window, and how many carry error.type. The day's totals are checked
against the spans, so the meter and the spans agree on every attempt."""
from functools import reduce

from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.inject import load_incidents
from lib.metrics import DURATION, DayMeter, Tally, tally
from lib.report import fmt_int

DAY, STEP_NS, HOUR_NS = "2026-12-09", 300 * 1_000_000_000, 3600 * 1_000_000_000
meter, tools, last = DayMeter(DAY), [], [Tally(0, 0, 0)]   # the live meter; attempts by reply time; the last read


def after_message(run) -> None:
    """Read the tool histogram after one message: the attempts it added, keyed by its reply time."""
    now = tally(meter.reader, DURATION["execute_tool"], 20)
    tools.append((run.replied_ns, now - last[0]))
    last[0] = now


traced = run_day_traced(DAY, meter_provider=meter.provider, after_message=after_message)  # live: faults on virtual time
midnight = VirtualClock(DAY).now_ns
calls = [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == "execute_tool"]


def tools_in_hour(tick_ns: int) -> Tally:
    """The tool attempts of the messages that replied in the hour up to a tick."""
    return reduce(Tally.__add__, [added for replied, added in tools if tick_ns - HOUR_NS < replied <= tick_ns],
                  Tally(0, 0, 0))


for incident in load_incidents():
    tick = midnight + -(-(incident.end_ns - midnight) // STEP_NS) * STEP_NS    # the first tick after the window
    attempts = tools_in_hour(tick)
    print(f"{incident.incident_id}, tool attempts in the hour to that tick:", fmt_int(attempts.requests))
    print(f"{incident.incident_id}, tool attempts with error.type in that hour:", fmt_int(attempts.failed))

assert sum(added.requests for _, added in tools) == len(calls)                              # every attempt, as spans
assert sum(added.failed for _, added in tools) == sum("error.type" in row["attributes"] for row in calls)
```

Output:

```text
inc-contacts-timeout, tool attempts in the hour to that tick: 5
inc-contacts-timeout, tool attempts with error.type in that hour: 4
inc-rate-limit, tool attempts in the hour to that tick: 2
inc-rate-limit, tool attempts with error.type in that hour: 0
inc-mcp-error, tool attempts in the hour to that tick: 3
inc-mcp-error, tool attempts with error.type in that hour: 3
```

The table counts each window at the first tick after it, and its burns are the highest from the window to five minutes after it. The counts and the burns come from different ticks, so one row divided by another does not give the burn.

| Measure | Contacts timeout | Model rate limit | Contacts error replies |
| --- | --- | --- | --- |
| Window, UTC | 13:00:00 to 13:12:00 UTC | 15:30:00 to 15:31:30 UTC | 17:00:00 to 17:10:00 UTC |
| Messages in the hour to the first tick after | 13 | 15 | 16 |
| Of those, messages with no reply | 0 | 11 | 0 |
| Tool attempts in that hour | 5 | 2 | 3 |
| Of those, attempts with `error.type` | 4 | 0 | 3 |
| Highest error burn over 1 hour | 0.0 | 73.3 | 0.0 |
| Highest error burn over 5 minutes | 0.0 | 91.7 | 0.0 |
| Messages over 20 s in the hour | 3 | 1 | 3 |
| Highest latency burn over 1 hour | 4.6 | 1.3 | 4.6 |

Only the rate-limit window spends the error budget fast. Its hour holds 11 messages with no reply, and its error burn is 73.3 over the hour and 91.7 over five minutes. The injected rate limit refused those requests, and the refusals outlasted the retry backoff, so those messages ended with no reply.

The other two windows spend no error budget at all, because every message in them got a reply. Their latency burns, in the row for the highest latency burn over 1 hour, are well below 14.4, the burn the [next section](#an-alert-that-stays-quiet) pages at, and they measure slow messages, not failed ones.

The arithmetic gives the scale. A burn of 14.4 would spend the whole 30-day budget in 50 hours, since 720 hours divided by 14.4 is 50. At that pace one hour spends 2.0% of the month's budget, and the page threshold in the next section is 14.4 for that reason.

**Working rule:** Compute each window's burn from the counts inside that window, and print the count beside each burn. A reader who sees 0.0 needs to know whether it means no failures among many messages, or no messages at all.

## One page on the incident day, none on a quiet one {#an-alert-that-stays-quiet}

A burn-rate alert on one window is a poor alert. A long window fires only after the spend has piled up, and it keeps firing for as long as the long window holds the failures. A short window fires on a brief spike, and it clears as soon as the spike ends. The *Site Reliability Workbook* (O'Reilly, 2018) pairs the two in its chapter 5, "Alerting on SLOs", and its Table 5-8 gives a page at a burn of 14.4 over one hour, with a five-minute window for the short check ([the workbook](https://sre.google/workbook/alerting-on-slos/)). The table gives each burn by the share of budget it spends and the window alone, so 14.4 over an hour spends 2% of a 30-day budget. That holds for a 99% objective and for a 99.9% objective alike. Only the failed share that trips it changes, to 14.4% of messages here. The workbook's traffic is not this book's, so its 14.4 is a starting point here and not a measurement the book has made.

The workbook's method pairs slower windows as well: a page at burn 6 over 6 hours with a 30-minute short window, which spends 5% of the budget, and a ticket at burn 1 over 3 days with a 6-hour short window, which spends 10%. Those catch a slow, sustained burn that a one-hour pair misses. One day of traffic cannot test them, which is why this chapter sets only the 1-hour pair.

The book's alert pages when the error burn is at least 14.4 over the hour and at least 14.4 over the last five minutes, and when the hour holds at least 10 messages. The last condition is the book's own. With few messages in an hour, one failure moves the burn a long way, so an hour below the minimum cannot page. The long window makes the page need a sustained spend, the short window lets the page clear once the spend stops, and the minimum keeps both readings meaningful. The workbook has a section for traffic this thin, "Low-Traffic Services and Error Budget Alerting", whose own example is 10 requests an hour. It offers three options: generate artificial traffic, combine small services for monitoring, or change the product. The book's minimum is none of the three. In production we'd take the second: a service this small shares its objective with a larger one before anyone relies on its page.

Next, the alert runs over the incident day at every five-minute tick, for the [error objective](#service-level-objectives) and for the latency objective.

Example `alert-on-incident-day` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""The two-window burn-rate alert, run on the incident day at each 5-minute tick (chapter 9, `an-alert-that-stays-quiet`).

The page fires when the error budget burns at 14.4 or faster over the hour and over the last five minutes, and the hour
holds at least 10 messages, so one failed message in a quiet hour cannot page. 14.4 spends 2% of a 30-day budget in an
hour (chapter 9, `slo-and-budget`). The short window is what lets the page clear once the burn stops. The alert reads the
metric only. It is run for the error objective and for the latency objective, which has the same windows."""
from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.inject import load_incidents
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, STEP_NS, THRESHOLD, MIN_REQUESTS = "2026-12-09", 300 * 1_000_000_000, 14.4, 10
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
run_day_traced(DAY, meter_provider=meter.provider, after_message=meter.after)  # live: the contacts server injects faults
midnight = VirtualClock(DAY).now_ns
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
slow = alert_verdicts(tallies, slo=0.95, measure="slow", threshold=THRESHOLD, min_requests=MIN_REQUESTS)


def clock(ns: int) -> str:
    """A virtual time as hours and minutes UTC, from the day's midnight."""
    offset = (ns - midnight) // 60_000_000_000
    return f"{offset // 60:02d}:{offset % 60:02d}"


pages = [v for v in errors if v.page]
cleared = next(v for v in errors if v.tick_ns > pages[0].tick_ns and not v.page)
print("page threshold, burn over 1 hour and over 5 minutes:", fmt_burn(THRESHOLD))
print("minimum messages in the hour:", fmt_int(MIN_REQUESTS))
print("ticks where the error page fires:", fmt_int(len(pages)), "of", fmt_int(len(errors)))
print("first tick the error page fires:", clock(pages[0].tick_ns))
print("messages in that hour, with no reply:", fmt_int(pages[0].long.bad), "of", fmt_int(pages[0].long.requests))
print("error burn at that tick, 1 hour and 5 minutes:", fmt_burn(pages[0].long.burn), fmt_burn(pages[0].short.burn))
print("first tick the error page is clear again:", clock(cleared.tick_ns))
print("ticks where the latency page fires:", fmt_int(sum(v.page for v in slow)))
print("highest latency burn over an hour, with the minimum met:",
      fmt_burn(max(v.long.burn for v in slow if v.long.requests >= MIN_REQUESTS)))

for incident in load_incidents():
    near = [v for v in errors if incident.start_ns < v.tick_ns <= incident.end_ns + STEP_NS]
    print(f"{incident.incident_id}, ticks in or just after the window:", fmt_int(len(near)))
    print(f"{incident.incident_id}, ticks where the error page fires:", fmt_int(sum(v.page for v in near)))

rate_limit = next(i for i in load_incidents() if i.kind == "rate-limit")
assert pages and all(rate_limit.start_ns < v.tick_ns <= rate_limit.end_ns + STEP_NS for v in pages)
assert sum(v.page for v in slow) == 0                  # the latency objective never pages on this day
for incident in load_incidents():
    if incident.kind != "rate-limit":
        assert not any(v.page for v in errors if incident.start_ns < v.tick_ns <= incident.end_ns + STEP_NS)
```

Output:

```text
page threshold, burn over 1 hour and over 5 minutes: 14.4
minimum messages in the hour: 10
ticks where the error page fires: 1 of 288
first tick the error page fires: 15:35
messages in that hour, with no reply: 11 of 15
error burn at that tick, 1 hour and 5 minutes: 73.3 91.7
first tick the error page is clear again: 15:40
ticks where the latency page fires: 0
highest latency burn over an hour, with the minimum met: 5.0
inc-contacts-timeout, ticks in or just after the window: 3
inc-contacts-timeout, ticks where the error page fires: 0
inc-rate-limit, ticks in or just after the window: 1
inc-rate-limit, ticks where the error page fires: 1
inc-mcp-error, ticks in or just after the window: 3
inc-mcp-error, ticks where the error page fires: 0
```

The alert pages once on the incident day. The first firing is at 15:35 UTC, and the page clears at 15:40. At the first firing the hour held 11 of 15 messages with no reply. Across the day the error page fires at 1 of 288 ticks, and the latency page never fires, as the example asserts.

The page fires for the rate-limit window and for nothing else. The timeout window never pages on this objective. It is the window the case starts at 13:00 UTC, and the error page fires at 0 ticks around it. Each lookup in that window was retried (2 retries), every attempt timed out (4 attempts), and no retry recovered. The model then wrote its reply from the tool's timed-out result. The two messages whose lookups timed out got replies that blamed the name, though the lookup never answered. Every message got a reply, so the error objective counts none.

The messages in that window go slow instead. Its latency burn reaches 4.6, and the highest latency burn over the whole day, with the minimum met, is 5.0. A latency page at 14.4 would need 72% of an hour's messages over 20 seconds, which is 14.4 times the 5.0% budget, and this day never came near that share. A fault the model answers around does not reach the error objective, and the latency objective would need a far larger share of slow messages before it paged. The fault shows in the tool's ERROR attempts, which the table's tool rows count in `gen_ai.execute_tool.duration`.

The contacts server's error replies, the third window, behave the same way on this objective, because the tool's error result went to the model, which answered with no retry (0 retries). Its messages got replies, and the error page fires at 0 ticks around that window.

Example `figure-burn-rate-incident-day` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""Draw the burn rate over the incident day, by window, with the page's threshold (chapter 9, `burn-rate-incident-day`).

A burn rate is a rate of budget use, not a count of errors: 14.4 means the window spends the budget 14.4 times as fast
as the objective allows. The one-hour burn is drawn as a gap wherever the hour holds fewer than the minimum of 10
messages, since a burn over two or three messages is noise. The five-minute burn is drawn as a gap wherever its window
holds no message, since a zero there would read as no failures among many. The page fires where the hour and the five
minutes both reach the threshold. The peaks are printed so a reader can find the spike on the figure."""
import math

from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, THRESHOLD, MIN_REQUESTS = "2026-12-09", 14.4, 10
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
run_day_traced(DAY, meter_provider=meter.provider, after_message=meter.after)  # live: faults on virtual time
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
slow = alert_verdicts(tallies, slo=0.95, measure="slow", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
hours = [(v.tick_ns - VirtualClock(DAY).now_ns) / 3_600_000_000_000 for v in errors]   # hours from the day's midnight
error_hour = [v.long.burn if v.long.requests >= MIN_REQUESTS else math.nan for v in errors]
error_five = [v.short.burn if v.short.requests else math.nan for v in errors]   # no message in five minutes: no burn
latency_hour = [v.long.burn if v.long.requests >= MIN_REQUESTS else math.nan for v in slow]


def peak(series):
    """The highest value of a series and the first tick that reaches it, as hours and minutes UTC."""
    known = [(x, i) for i, x in enumerate(series) if not math.isnan(x)]
    value = max(x for x, _ in known)
    index = min(i for x, i in known if x == value)     # the first tick at the peak, not the last
    minutes = round(hours[index] * 60)
    return fmt_burn(value), f"{minutes // 60:02d}:{minutes % 60:02d}"


print("gaps, one-hour burn at ticks under the minimum:", fmt_int(sum(math.isnan(x) for x in error_hour)))
print("peak error burn, 1 hour:", *peak(error_hour))
print("peak error burn, 5 minutes:", *peak(error_five))
print("peak latency burn, 1 hour:", *peak(latency_hour))
print("page threshold:", fmt_burn(THRESHOLD))

fig, ax = new_figure(height=2.8)
ax.plot(hours, error_hour, color=ACCENT, linewidth=1.8, label="error burn, 1 hour")
ax.plot(hours, error_five, color=INK, linewidth=1.2, marker="o", markersize=2.5, label="error burn, 5 minutes")
ax.plot(hours, latency_hour, color=MUTED, linewidth=1.2, linestyle="--", label="latency burn, 1 hour")
ax.axhline(THRESHOLD, color=INK, linewidth=1, linestyle=":", label="page threshold, 14.4")
ax.set_xlim(0, 24)
ax.set_xticks(range(0, 25, 3), [f"{h:02d}:00" for h in range(0, 25, 3)])
ax.set_ylim(0, 130)                                   # headroom above the 91.7 peak, for the legend
ax.set_yticks(range(0, 101, 20))
ax.set_ylabel("burn rate")
ax.legend(loc="upper left", ncol=2, frameon=False)    # in the headroom above the data, left of the 15:35 spike
save(fig, "burn-rate-incident-day")
```

Output:

```text
gaps, one-hour burn at ticks under the minimum: 253
peak error burn, 1 hour: 84.6 15:55
peak error burn, 5 minutes: 91.7 15:35
peak latency burn, 1 hour: 5.0 13:25
page threshold: 14.4
figure: figures/burn-rate-incident-day.svg
```

Figure 9.1 draws the incident day as an on-call dashboard would: one spike crosses the page threshold, in the rate-limit window, and nothing else comes near it. The error burn over 5 minutes peaks in that window and falls back within minutes, which is why the page clears. The error burn over 1 hour stays above the threshold for longer, because the refusals stay inside its hour after the five-minute burn has fallen. The latency burn over 1 hour never reaches the page threshold, 14.4. The one-hour lines have gaps where their hour holds fewer than the minimum, at 253 ticks of the day. The five-minute line has gaps where its window holds no message.

*Figure 9.1. Burn rate over the incident day, by window, with the page threshold of 14.4.*

![The five-minute error burn crosses the page threshold in the rate-limit window, and the latency burn stays well below it all day](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.4/figures/burn-rate-incident-day.svg)

**Working rule:** Page only when a long window and a short window both reach the threshold, use the short window to clear the page, and let neither window page on an hour with fewer messages than the minimum.

## Test the same alert on a quiet day {#quiet-day-on-baseline-day-two}

A quiet day is the other half of the test. Baseline day 2 has no injected fault, and the same alert should not page on it at any tick, for either objective.

Example `alert-quiet-on-baseline-day-two` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""The same alert on baseline day 2, a normal day with no injected incident (chapter 9, `an-alert-that-stays-quiet`).

It is the alert's quiet day: the page must not fire at any tick, for either objective. The page is quiet here because no
message fails, not because of the hour's minimum. The day has 80 messages, so most hours hold fewer than the minimum,
and the printed count of the ticks that hold the minimum shows how little of the day the error page could read."""
from lib.dayrun import run_day_traced
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, THRESHOLD, MIN_REQUESTS = "2026-12-10", 14.4, 10
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
run_day_traced(DAY, live=False, meter_provider=meter.provider, after_message=meter.after)  # no fault on this day
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
slow = alert_verdicts(tallies, slo=0.95, measure="slow", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
total = tallies[-1][1]

print("messages, baseline day 2:", fmt_int(total.requests))
print("messages with no reply:", fmt_int(total.failed))
print("messages over 20 s:", fmt_int(total.slow))
print("ticks where the hour holds the minimum:", fmt_int(sum(v.long.requests >= MIN_REQUESTS for v in errors)),
      "of", fmt_int(len(errors)))                     # the only ticks a full hour can page on this day
print("highest error burn over an hour:", fmt_burn(max(v.long.burn for v in errors)))
print("highest error burn over 5 minutes:", fmt_burn(max(v.short.burn for v in errors)))
print("highest latency burn over an hour, with the minimum met:",
      fmt_burn(max(v.long.burn for v in slow if v.long.requests >= MIN_REQUESTS)))
print("ticks where the error page fires:", fmt_int(sum(v.page for v in errors)))
print("ticks where the latency page fires:", fmt_int(sum(v.page for v in slow)))

assert total.failed == 0                               # no message on this day ended without a reply
assert not any(v.page for v in errors)                 # the error page stays quiet at every tick
assert not any(v.page for v in slow)                   # and so does the latency page
```

Output:

```text
messages, baseline day 2: 80
messages with no reply: 0
messages over 20 s: 4
ticks where the hour holds the minimum: 21 of 288
highest error burn over an hour: 0.0
highest error burn over 5 minutes: 0.0
highest latency burn over an hour, with the minimum met: 4.0
ticks where the error page fires: 0
ticks where the latency page fires: 0
```

Baseline day 2 has 80 messages, and 0 of them got no reply. Its highest error burn is 0.0 over the hour and 0.0 over five minutes.

Its highest latency burn, with the minimum met, is 4.0, well short of 14.4. The error page fires at 0 ticks, and the code asserts that the page is quiet at every one.

The quiet comes from the messages, not from the minimum. On this day's traffic only 21 of 288 ticks hold the minimum of messages in the hour, and those are the only ticks at which the error page could read a full hour at all. An hour under the minimum cannot page whatever it holds: nine failures out of nine stay silent. The minimum guards against a single failure in a thin hour, and on a thin day it decides most of the verdicts. Whether the alert is sound on a busier service is a question this book's traffic cannot answer.

**Working rule:** Test an alert on two days, one that must page and one that must not, and print the ticks it could not read beside the verdicts it gave.

## Where a burn-rate alert goes blind {#alerts-on-metrics-in-production}

An objective that counts what users got misses every fault the model answers around. In the [timeout window](#an-alert-that-stays-quiet), the model replied without the contact, and the page did not fire. A second objective is the usual answer: one on tool attempts, or one on the latency of the slowest messages by route. The examples in this chapter ship neither. A tool-level page would also read few calls on this traffic, since the meter counts every tool attempt, and baseline day 1 has only 10 of them in a whole day.

The alert sees a message only when the message ends. A message that waits on a retry enters the hour's count late, and its failure, if it has one, reaches the page late as well. An operator who expects the page to fire the moment a fault starts will be disappointed by every message that was still running at the tick.

Real faults carry no label. The windows in this chapter are the case's, so each count can be matched to a window afterwards. A production alert has no such record, and [chapter 8's production section](#find-the-failure-in-production) makes the same point about failure rates. Keep the incident's start and end next to the counts when you review them, and do not let a retrospective match stand as the measure of the alert.

The failed-message rate in this chapter and chapter 8's error rate disagree on purpose. The span rule in chapter 8 counts a recovered message as an error, and the objective here does not. Print both, each with the rule that produced it. Chapter 10's gate counts errors by span status, so chapter 8's error rate is the stricter one, and a release that looks bad to the gate may look fine to the objective. Neither number is wrong, because they answer different questions. A dashboard that shows one under the other's name will mislead.

Every new attribute on a metric multiplies its storage and its query time. Before you add one, count its series on a day of real traffic, as the cardinality example does, and keep the count with the change. The overflow series the SDK writes past its limit is not a fallback that keeps the metric useful. It is a sign that the attribute was the wrong one.

**Working rule:** Recompute the burn on your own traffic before the first page, and set the minimum from the messages an hour actually holds on your service.

## What this chapter decided {#alerts-on-metrics-decisions}

The chapter's lesson is that an objective on what users got pages on the faults users feel and misses the faults the model answers around, so an alert on the assistant's metrics needs a second number to see those.

- The error objective counts messages with no reply, read from the duration histogram. Span errors stay in the traces, under chapter 8's definition, and chapter 10's gate reads them.
- The latency objective is 95% of messages within 20 seconds, set from baseline day 1's tail and read at a bucket's edge.
- The page fires at a burn of 14.4 over one hour and over five minutes, with at least 10 messages in the hour. The pair and the starting number come from the workbook, and the minimum is the book's.
- The metrics carry the registry's attributes only. The route and the user are counted from the spans, to show what they would cost, and they stay out of the meter.
- No tool-level or per-route objective is set in this chapter, so the timeout window stays unpaged on this objective.
- An alert on what users got pages on the faults users feel, and it misses a fault the model answered around. A second objective, on the attempts or on the tail, is what would catch that fault. [Chapter 10's gate](#the-ci-gate) compares releases on message time, input tokens, cost, error rate and route accuracy, on the same messages, and it reads neither the attempts nor the tail.
