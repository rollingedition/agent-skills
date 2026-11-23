---
title: "Observability for LLM Applications"
chapter: "Let the client library instrument the calls"
chapter_id: client-library-instrumentation
book: observability-for-llm-applications
edition: 2026.11.1
verified: 2026-11-23
edition_code: B95K-8RWR
canonical: https://rollingedition.com/observability-for-llm-applications/client-library-instrumentation
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Let the client library instrument the calls,” chapter 3 of Observability for LLM Applications, Edition 2026.11.1, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/client-library-instrumentation. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Let the client library instrument the calls

By the end of this chapter you can read what the official OpenAI instrumentation writes for one chat call, say which of its names differ from the GenAI conventions version 0.1.0 that this book follows, and name the variable that decides whether prompts and replies are recorded, with its default. Chapter 1 wrote the model spans by hand. Chapter 2, "Name spans the way the standard does", gave them the standard's names. This chapter asks whether a library can write those spans instead, and where its spans come out different.

Ambrewick's assistant calls its model through the `openai` client library, and that library has packages that wrap the client and write a span for each call. The model calls are the only steps with recorded times in chapter 1, so a package that writes them correctly would spare the book a large part of its hand-made spans. A package that writes them differently changes every query in the chapters after this one, because those chapters read the names. The question is concrete: for one real call, what does the package emit, and where does it differ from what the book would write by hand?

## A call through the client {#a-call-through-the-client}

There are two ways to get a span for a model call. Manual instrumentation is spans your code makes; automatic instrumentation collects telemetry with no change to the application's source code. Chapter 1 used the first kind. This section uses an instrumentation library. An instrumentation library is a package that makes the telemetry for another library's calls: one call in the start-up code installs it, and the zero-code agent, `opentelemetry-instrument`, loads the same package with no change to the calls.

Example `instrumented-chat-call` (Python 3.13.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.56.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""One chat call through the openai client, instrumented by the official package and answered from the recording. The
point rests on three printed facts: the call makes one client span, named for its operation and model; that span is a
child of the message's span; and it holds the usage the reply reported. The metrics are named and counted here, never
valued, since their durations use real time."""
from lib.http_replay import client, route_body    # lib first: threads and seeds are fixed before anything else

import opentelemetry.sdk.trace as sdk_trace
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.assistant import RELEASES
from lib.case import load_messages
from lib.clock import VirtualClock
from lib.ids import SequentialIds
from lib.names_map import name_map
from lib.report import fmt_int
from lib.tracing import make_provider

clock = VirtualClock("2026-12-07")
# The SDK reads span times from its trace module's time_ns, so patching that name gives every span, the package's included,
# virtual times.
sdk_trace.time_ns = lambda: clock.advance(1_000_000)
exporter, reader = InMemorySpanExporter(), InMemoryMetricReader()
provider = make_provider("ambrewick-assistant", RELEASES["r0"].service_version, "example", clock, SequentialIds(),
                         exporter, "https://opentelemetry.io/schemas/1.45.0")
OpenAIInstrumentor().instrument(tracer_provider=provider, meter_provider=MeterProvider(metric_readers=[reader]))

with provider.get_tracer("ambrewick-assistant").start_as_current_span("invoke_agent ambrewick-assistant"):
    reply = client().chat.completions.create(**route_body(load_messages("2026-12-07")[0]))

call, root = exporter.get_finished_spans()                  # the call ends before the message's span does
metrics = reader.get_metrics_data().resource_metrics[0].scope_metrics[0].metrics
print("spans in the trace:", len(exporter.get_finished_spans()))
print("instrumented span, name:", call.name)
print("instrumented span, kind:", call.kind.name)
print("instrumented span, scope schema URL:", call.instrumentation_scope.schema_url)
print("attributes on the span:", ", ".join(sorted(call.attributes)))
print("gen_ai.provider.name on the span:", call.attributes["gen_ai.provider.name"])
print("server.address on the span:", call.attributes["server.address"])
print("server.port on the span:", call.attributes["server.port"])
print("input count on the span:", fmt_int(call.attributes["gen_ai.usage.input_tokens"]))
print("output count on the span:", fmt_int(call.attributes["gen_ai.usage.output_tokens"]))
for metric in metrics: print(f"metric {metric.name}, unit {metric.unit.strip('{}')}, data points: {len(metric.data.data_points)}")
types = {p.attributes["gen_ai.token.type"] for m in metrics if m.name == "gen_ai.client.token.usage" for p in m.data.data_points}
print("token types on the usage metric:", ", ".join(sorted(types)))
# The call is a child of the message's span, and its usage is the reply's. Every name it makes is in the table.
assert call.parent.span_id == root.context.span_id
assert (call.attributes["gen_ai.usage.input_tokens"], call.attributes["gen_ai.usage.output_tokens"]) == (
    reply.usage.prompt_tokens, reply.usage.completion_tokens)
assert {m.name for m in metrics} | set(call.attributes) | {"gen_ai.token.type"} <= set(name_map())
```

Output:

```text
spans in the trace: 2
instrumented span, name: chat qwen3-4b-instruct-2507
instrumented span, kind: CLIENT
instrumented span, scope schema URL: https://opentelemetry.io/schemas/1.37.0
attributes on the span: gen_ai.operation.name, gen_ai.provider.name, gen_ai.request.max_tokens, gen_ai.request.model, gen_ai.request.seed, gen_ai.request.temperature, gen_ai.response.finish_reasons, gen_ai.response.id, gen_ai.response.model, gen_ai.usage.input_tokens, gen_ai.usage.output_tokens, server.address, server.port
gen_ai.provider.name on the span: openai
server.address on the span: localhost
server.port on the span: 8000
input count on the span: 142
output count on the span: 6
metric gen_ai.client.operation.duration, unit s, data points: 1
metric gen_ai.client.token.usage, unit token, data points: 2
token types on the usage metric: input, output
```

The run sends one route request through the `openai` client: the route call for the dev day's first message, which `load_messages(...)[0]` replays. The client does not reach a model. Its HTTP exchange is a recording, served by the mock transport of `httpx` from `lib/http_replay.py`. The transport answers every request, so no socket opens even though the URL names the model server. The recorded server sends usage only on a non-streamed reply, so the recording keeps that reply, and a span takes its [token counts](#three-token-counts) from usage. The run also patches the `time_ns` in the SDK's trace module, which the package's spans take their times from, so the call's span gets the virtual times the replay gives. [Replay and the virtual clock](#replay-and-the-virtual-clock) explains the rest. The package's duration [metrics](#totals-from-metrics-not-spans) are not patched, and [what the package emits](#what-the-package-emits) says why.

The trace holds 2 spans: the message's root, `invoke_agent ambrewick-assistant`, and the call. The package marks the call CLIENT, as the book marks its own model calls, because the model runs behind a server. The call's span is named `chat qwen3-4b-instruct-2507`, the operation followed by the model, which is the registry's pattern for an inference span.

The call's usage reads 142 [input tokens](#three-token-counts) and 6 [output tokens](#three-token-counts). These are the usage counts the llama-cpp-python server reported in its reply, which the package copied onto the span. They are not the book's recorded counts, which re-tokenize the prompt. The attribute's name, `gen_ai.usage.input_tokens`, says what the value counts, not where it came from.

The book's code makes only the root; the package makes the call's span inside it. The script asserts that the call's parent is the root, and that its two usage counts equal the reply's, so a change in either fails the run.

**Working rule:** Wrap the client once, at start-up, and make your own spans only for work the library cannot see, such as the message's root, its tool calls and its fallback reply. When no package wraps a client, or the one that does writes names the table can't map, make the call's span by hand, as chapter 1 did. Then check the call's parent in a test, as the script does, because the parent is what places the call in its message's trace.

## What the package emits {#what-the-package-emits}

The package writes one span per call, named for the operation and the model, and the output lists the attribute names on that span in sorted order. The ones this book reads are `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.response.finish_reasons`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `server.address` and `server.port`. The provider value is openai, the value chapter 2 gives the book's own spans for an `openai` client.

One difference from the book's own spans shows in that list: content. No attribute holds a prompt or a reply, because content capture is off. [The capture switch](#the-capture-switch) says what that switch is and what its default is. The package takes `server.port` from the client's base URL, and leaves it out when that port is implicit or is 443 (`opentelemetry/instrumentation/genai/openai/utils.py` at 1.3b0).

The call makes two metrics, and the output gives their names, units and point counts. `gen_ai.client.operation.duration`, in seconds, has 1 data point. `gen_ai.client.token.usage`, in tokens, has 2 data points, one for input and one for output. The points are split by `gen_ai.token.type`, which is the older conventions' name for that split. It is still a deprecated constant in `opentelemetry-semantic-conventions` 0.66b2, and v0.1.0 replaced it with the two token histograms. In this chapter, "metric" and "[histogram](#totals-from-metrics-not-spans)" name the package's instruments only. Chapter 6 defines both.

A streamed call adds two more instruments, `gen_ai.client.operation.time_to_first_chunk` and `gen_ai.client.operation.time_per_output_chunk`, and one span attribute, `gen_ai.response.time_to_first_chunk`. This chapter's example does not stream, so its output prints none of them. The name table holds all three stream names, which the generator observed from the streamed reply it builds, as [hand-made spans against the instrumented ones](#hand-made-against-instrumented) explains.

The chapter prints each instrument's name, unit and point count, and no value, for one reason. The package takes its span times from the clock the script patches, but its duration and chunk instruments read a monotonic timer that the patch does not reach. Their values are therefore the recording machine's real timings, and they change on every run. The token values are fixed, because they are the reply's usage, and they print as counts so that every instrument prints the same way.

**Working rule:** Count a package's spans and its instruments in a test, and read each name, unit and point count from its output. Do not assert a value from an instrument whose timer your tests do not control, because the count holds on every run and the value does not.

## Hand-made spans against the instrumented ones {#hand-made-against-instrumented}

Chapter 2 checks the book's own spans against the registry, and this section measures the package the same way. The names are observed from the package's output, and the mapping to v0.1.0 is the book's judgement, written once in the generator, `examples/data/genai/build_names_map.py`, and checked against the registry. The output came from the recorded call, from a streamed reply that the generator builds for the names a stream adds, and from a call with content events on, which gives the name of the event. One entry comes from the package's source rather than from a run: `gen_ai.usage.cache_read.input_tokens`. The package writes it only when a reply carries cached prompt tokens, and the recorded replies carry none.

Example `diff-hand-and-instrumented` (Python 3.13.16 · numpy 2.5.5), passing in Edition 2026.11.1:

```python
"""The names the official package emits, set against the GenAI conventions v0.1.0 names this book uses. The table is
examples/lib/names_map.py, which examples/data/genai/build_names_map.py writes by running the package on the recorded
call, on a streamed reply it constructs (for the names a stream adds) and on a call with content events on (for the
event's name). The point rests on
the last printed count: five names differ from v0.1.0, and each one is named here. instrumented-chat-call checks that
the names a live call makes are in the same table."""
from lib.names_map import REGISTRY_VERSION, name_map          # lib first: threads and seeds are fixed before anything else
from importlib.metadata import version

table = name_map()


def status(name, targets):
    """Same when the name is its own v0.1.0 name, or the chat span's type; the two named exceptions get their own
    labels, and the rest are renamed, split or absent."""
    if targets == (name,) or (name == "chat {model}" and targets == ("gen_ai.client.inference",)):
        return "same"
    if name == "gen_ai.client.operation.duration":
        return "wrong instrument for inference"
    if name == "gen_ai.token.type":
        return "replaced by the two token histograms"
    if not targets:
        return "no v0.1.0 name"
    return "split into two" if len(targets) == 2 else "renamed"


statuses = {name: status(name, targets) for name, targets in table.items()}
print("registry version:", REGISTRY_VERSION)
print("package version:", version("opentelemetry-instrumentation-genai-openai"))
print("names the package emits, in the table:", len(table))
print("names the same in v0.1.0:", sum(value == "same" for value in statuses.values()))
for name in sorted(table):
    if statuses[name] != "same":
        print(f"{statuses[name]}, {name}:", " and ".join(table[name]) or "none")
print("names that differ from v0.1.0:", sum(value != "same" for value in statuses.values()))
assert {name for name, value in statuses.items() if value != "same"} == {
    "gen_ai.client.operation.duration", "gen_ai.client.token.usage", "gen_ai.client.operation.time_to_first_chunk",
    "gen_ai.client.operation.time_per_output_chunk", "gen_ai.token.type"}
```

Output:

```text
registry version: 0.1.0
package version: 1.3b0
names the package emits, in the table: 25
names the same in v0.1.0: 20
wrong instrument for inference, gen_ai.client.operation.duration: gen_ai.client.inference.duration
renamed, gen_ai.client.operation.time_per_output_chunk: gen_ai.client.inference.time_per_output_chunk
renamed, gen_ai.client.operation.time_to_first_chunk: gen_ai.client.inference.time_to_first_chunk
split into two, gen_ai.client.token.usage: gen_ai.client.inference.operation.input_tokens and gen_ai.client.inference.operation.output_tokens
replaced by the two token histograms, gen_ai.token.type: none
names that differ from v0.1.0: 5
```

The table holds 25 names that the package emits. Of those, 20 are the same in v0.1.0, and 5 differ. Each of the five that differ is printed with what it became in v0.1.0.

Four of the five differences are in metrics. The registry's metrics file says `gen_ai.client.operation.duration` SHOULD NOT be reported for inference, and it names the inference duration `gen_ai.client.inference.duration`. The token metric is the one that splits: where the package writes one histogram with a `gen_ai.token.type` point attribute, the registry has two histograms, one for input and one for output. The fifth, `gen_ai.token.type`, is the name the older conventions gave that split, and v0.1.0 replaced it with the two token histograms, so a query written from the registry cannot select the package's input points with it.

Because chapter 2 checked the book's own spans against the registry, every gap in this table belongs to the package. The table is what chapters 6 and 7 use when they read a package's output. The first uses are [`totals-from-metrics-not-spans`](#totals-from-metrics-not-spans) in chapter 6 and [`time-to-first-chunk`](#time-to-first-chunk) in chapter 7.

**Working rule:** Keep one table of the names a package emits, generated from its output and checked against the registry, and read the package's data through it. A query for a name the table lacks should fail in the test, as the book's examples fail, and not return nothing in production. Regenerate the table when the package's version changes, not when a chart goes quiet.

## Three packages called openai {#the-three-openai-packages}

Three packages called `openai` instrument the client, and they differ on names and on content. Their names, as PyPI spells them, are `opentelemetry-instrumentation-genai-openai`, `opentelemetry-instrumentation-openai-v2` and `opentelemetry-instrumentation-openai`. The first two are OpenTelemetry's. The third is Traceloop's. Only the first is installed here, at the version the pins hold. The other two are neither installed nor pinned, so this section reads their published wheels, at the versions and dates the table gives, and does not run them. Their versions are written as text for that reason: the pins file does not hold them, and no example prints them.

Example `three-openai-packages` (Python 3.13.16 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0), passing in Edition 2026.11.1:

```python
"""Three packages called openai instrument the client, and they disagree on names and on content. Two are OpenTelemetry's
and differ in naming scheme; the third is Traceloop's and captures content by default. Only the first is installed in the
pinned environment, so the point rests on that one: its version is printed, and the module that reads its content switch
names the switch the table gives. The other two are not importable here, so their names and defaults are the source
readings the chapter cites, printed as wheel readings and not as runs."""
import lib  # lib first: threads and seeds are fixed before anything else

import importlib.util
from importlib.metadata import version

# Name as PyPI spells it; the module it imports; its project; the naming its source gives; its content switch and that
# switch's default, both from the source reading in notes/research/client-library-instrumentation.md (S2, S6, S7).
PACKAGES = (
    ("opentelemetry-instrumentation-genai-openai", "opentelemetry.instrumentation.genai.openai", "OpenTelemetry",
     "GenAI conventions, latest experimental, unconditionally", "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
     "NO_CONTENT"),
    ("opentelemetry-instrumentation-openai-v2", "opentelemetry.instrumentation.openai_v2", "OpenTelemetry",
     "GenAI conventions v1.30.0 unless the experimental opt-in is set", "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
     "false"),
    ("opentelemetry-instrumentation-openai", "opentelemetry.instrumentation.openai", "Traceloop",
     "its own names, from opentelemetry-semantic-conventions-ai 0.5.1", "TRACELOOP_TRACE_CONTENT", "true"),
)
installed = [row for row in PACKAGES if importlib.util.find_spec(row[1]) is not None]
assert [row[0] for row in installed] == ["opentelemetry-instrumentation-genai-openai"]
source = importlib.util.find_spec("opentelemetry.util.genai.utils").origin
assert installed[0][4] in open(source, encoding="utf-8").read()     # the module that reads the switch names it

print("packages importable in this environment:", len(installed))
print("installed version:", version(installed[0][0]))
for name, module, project, naming, switch, default in PACKAGES:
    print(f"{name}, evidence:", "installed source" if name == installed[0][0] else "wheel reading")
    print(f"{name}, project:", project)
    print(f"{name}, naming:", naming)
    print(f"{name}, content switch:", switch)
    print(f"{name}, content switch default:", default)
```

Output:

```text
packages importable in this environment: 1
installed version: 1.3b0
opentelemetry-instrumentation-genai-openai, evidence: installed source
opentelemetry-instrumentation-genai-openai, project: OpenTelemetry
opentelemetry-instrumentation-genai-openai, naming: GenAI conventions, latest experimental, unconditionally
opentelemetry-instrumentation-genai-openai, content switch: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT
opentelemetry-instrumentation-genai-openai, content switch default: NO_CONTENT
opentelemetry-instrumentation-openai-v2, evidence: wheel reading
opentelemetry-instrumentation-openai-v2, project: OpenTelemetry
opentelemetry-instrumentation-openai-v2, naming: GenAI conventions v1.30.0 unless the experimental opt-in is set
opentelemetry-instrumentation-openai-v2, content switch: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT
opentelemetry-instrumentation-openai-v2, content switch default: false
opentelemetry-instrumentation-openai, evidence: wheel reading
opentelemetry-instrumentation-openai, project: Traceloop
opentelemetry-instrumentation-openai, naming: its own names, from opentelemetry-semantic-conventions-ai 0.5.1
opentelemetry-instrumentation-openai, content switch: TRACELOOP_TRACE_CONTENT
opentelemetry-instrumentation-openai, content switch default: true
```

The output gives each package's project, its naming, its content switch and that switch's default, and it says for each package whether those lines come from the installed source or from a wheel reading. The script checks that `opentelemetry.util.genai.utils`, the module that reads the switch, names the first package's switch.

| Package, version and date | Project | Names | Content switch, default |
| --- | --- | --- | --- |
| `opentelemetry-instrumentation-genai-openai`, 1.3b0, 23 October 2026 | OpenTelemetry | GenAI conventions, experimental set | `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, `NO_CONTENT` |
| `opentelemetry-instrumentation-openai-v2`, 2.4b0, 1 May 2026 | OpenTelemetry | GenAI conventions v1.30.0, unless opted in | `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, `false` |
| `opentelemetry-instrumentation-openai`, 0.63.1, 16 November 2026 | Traceloop | its own names, from `opentelemetry-semantic-conventions-ai` 0.5.1 | `TRACELOOP_TRACE_CONTENT`, `true` |

The first package's page calls its version a pre-release, and its description says, "The latest experimental features may introduce breaking changes in future releases." The page also says that it uses the experimental GenAI conventions unconditionally, with no opt-in and no version named. The page names no conventions version, but the scope stamps https://opentelemetry.io/schemas/1.37.0, beside the book's 1.45.0. The table names no version of the conventions for the first package, because the package states none, and [the earlier section](#hand-made-against-instrumented) measures it against v0.1.0, the version the book follows.

The second package keeps the older naming by default, and its switch has two meanings. On its legacy path the variable takes `true`, and the default is `false`. On its experimental path the variable takes `span_only`, `event_only` or `span_and_event`. Which meaning applies depends on the experimental opt-in, so a team reads the package's version and its opt-in together before it sets the variable. Both OpenTelemetry packages read the same variable, with different values, so a team that moves from the second and keeps `true` gets `NO_CONTENT` from the first, with only a warning in the log.

Traceloop's package names its span `openai.chat`, not the operation and the model, and it writes prompts and completions into the span by default. Its switch is `TRACELOOP_TRACE_CONTENT`, and it stays on unless someone sets it to `false`. Any value other than `true`, `1`, `yes` or `on` turns it off, and a context value, `override_enable_content_tracing`, turns it back on. That is the reverse of the OpenTelemetry package, and it is the difference that matters most in this chapter. A team that adds Traceloop's package to a service that sends private text to a model has changed what its telemetry holds, and it has not set any variable to do so.

For this book we use the first package. It is the one the pins hold, and its names are the registry's, bar the five differences in [the earlier section](#hand-made-against-instrumented). We would choose the second only for a [backend](#otlp-over-http) that reads its older names and nothing else, and the third only for the names its own project defines. Either choice needs its content switch read at the version pinned, with content capture off unless someone turned it on for a stated purpose.

**Working rule:** Read each instrumentation package's content switch and its default from that package's own source or documentation at the version you pin, and not from the spec alone. The defaults differ between packages, so a service that adds a second package changes what its telemetry can hold.

## The capture switch {#the-capture-switch}

Content capture is the instrumentation's switch for recording prompts and replies themselves, and it is off, `NO_CONTENT`, unless set. The first package's default is `NO_CONTENT` and the second's is `false`; Traceloop's 0.63.1 wheel turns it on ([Three packages called openai](#the-three-openai-packages)).

The GenAI conventions v0.1.0 spans page says the switch MUST be named `OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT`, and the first package departs from that MUST. It reads a different variable, `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, and reads the spec's name nowhere. The next run shows what that does. It sets the spec's name to `SPAN_ONLY` and makes one call. Then it does the same with the package's own name, as a control, and counts the content attributes each call's span holds.

Example `capture-switch-names` (Python 3.13.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.56.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""The content switch: whether the official package's span holds the prompt and the reply. The package reads one variable,
and the spec's name for the same switch is read nowhere in the package. The point rests on three counts. With the spec's
name set to SPAN_ONLY, one call's span holds no content. With the package's own name set to SPAN_ONLY, a control call's
span holds two, so the count can rise and the package does read its name. And the package's parser gives NO_CONTENT when
its variable is unset and when it holds a value that is not a mode. The control records content for one call, and this
example prints only how many content attributes that span holds, never their values."""
import lib  # lib first: threads and seeds are fixed before anything else

import os

import opentelemetry.sdk.trace as sdk_trace
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.util.genai.utils import ContentCapturingMode, get_content_capturing_mode

from lib.assistant import RELEASES
from lib.case import load_messages
from lib.clock import VirtualClock
from lib.http_replay import client, route_body
from lib.ids import SequentialIds
from lib.tracing import make_provider

PACKAGE_VARIABLE = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"
SPEC_VARIABLE = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT"
print("the package reads:", PACKAGE_VARIABLE, "| the spec's name for the switch:", SPEC_VARIABLE)
print("values the package parses:", ", ".join(mode.name for mode in ContentCapturingMode))
os.environ.pop(PACKAGE_VARIABLE, None)
print("mode, package variable unset:", get_content_capturing_mode().name)
os.environ[PACKAGE_VARIABLE] = "not a mode"                   # the parser logs this and falls back, it does not raise
print("mode, value that is not a mode:", get_content_capturing_mode().name)
os.environ.pop(PACKAGE_VARIABLE)


# Instrument afresh with the variable set to SPAN_ONLY, make one call, and print how many content attributes its span
# holds. The package reads its mode when it is instrumented, so the variable is set before that and removed after.
def content_attributes(variable: str, label: str, expected: int) -> None:
    os.environ[variable] = "SPAN_ONLY"
    clock = VirtualClock("2026-12-07")
    sdk_trace.time_ns = lambda: clock.advance(1_000_000)      # virtual span times, as in instrumented-chat-call
    exporter = InMemorySpanExporter()
    provider = make_provider("ambrewick-assistant", RELEASES["r0"].service_version, "example", clock, SequentialIds(),
                             exporter, "https://opentelemetry.io/schemas/1.45.0")
    instrumentor = OpenAIInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    client().chat.completions.create(**route_body(load_messages("2026-12-07")[0]))
    instrumentor.uninstrument()
    os.environ.pop(variable)
    call = exporter.get_finished_spans()[0]
    count = len([key for key in call.attributes if key.startswith(("gen_ai.input.messages", "gen_ai.output.messages"))])
    print(f"content attributes on the span, {label}:", count)
    assert count == expected


content_attributes(SPEC_VARIABLE, "spec variable set", 0)     # set, and read by nothing in the package
content_attributes(PACKAGE_VARIABLE, "package variable set", 2)   # the control: the package's own name, one call
```

Output:

```text
the package reads: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT | the spec's name for the switch: OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT
values the package parses: NO_CONTENT, SPAN_ONLY, EVENT_ONLY, SPAN_AND_EVENT
mode, package variable unset: NO_CONTENT
mode, value that is not a mode: NO_CONTENT
content attributes on the span, spec variable set: 0
content attributes on the span, package variable set: 2
```

The point is the difference between two counts: the spec's name gives 0 content attributes, where the package's own name gives 2, and nothing reports the difference. A team that sets the spec's name gets the output it would get with no setting at all, and that is the failure to guard against. It is quiet, and it looks like success until someone asks for a prompt and finds none.

The package parses four values: `NO_CONTENT`, `SPAN_ONLY`, `EVENT_ONLY` and `SPAN_AND_EVENT`. The package's source at 1.3b0 (`opentelemetry/util/genai/utils.py`) upper-cases the value before it matches a mode, so the match ignores letter case. For anything else it logs a warning and returns `NO_CONTENT`. The output shows both fallbacks. With the package's variable unset, the mode is NO_CONTENT. With a value that is not a mode, it is NO_CONTENT.

Chapter 12, in [What leaks when capture is on](#what-leaks-when-capture-is-on), says what each of the four modes writes and leaks. Here one call records content as a control, and that example prints only how many content attributes its span holds. Every other example in this chapter runs with capture off, and the book keeps it off until chapter 12 turns it on for a stated purpose.

A second switch, `OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK`, can upload content to files and write references to them. The package writes those references as `gen_ai.input.messages_ref` and `gen_ai.output.messages_ref`, the registry's names; only the instrumentation's docstring spells them with dots. No run in this chapter emits either one, because the hook also needs `OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH` set, and no run here sets it. Chapter 12 meets the hook.

**Working rule:** Set a package's content variable by the name its own source reads, at the version you pin, and check the setting in a test that asserts the span holds content exactly when the variable names a mode that records it. Leave content capture off in any service that has not named a purpose for it, and read the default of every package the service loads.

## Two other naming schemes {#two-other-naming-schemes}

Two more naming schemes describe the same facts as the GenAI conventions: OpenInference, which Arize publishes, with its own `openinference-instrumentation-openai` package as a fourth package for the client, and OpenLLMetry, the project behind Traceloop's package. We describe both so that a reader who meets their names knows what they stand for. The book emits neither.

OpenInference's module, at its pinned version `0.1.46`, names the model, the provider, the token counts, the span kind and the messages in its own constants. The script reads those constants and sets each one beside the GenAI name for the same fact.

Example `openinference-mapping` (Python 3.13.16 · numpy 2.5.5 · openinference-semantic-conventions 0.1.46), passing in Edition 2026.11.1:

```python
"""OpenInference, a naming scheme the book does not emit, at its pinned version. Its module names the facts a model call
carries (the model, the provider, the token counts, the span kind, the messages) in its own words. The point rests on
the table: each name is one the pinned module defines, and each maps to a GenAI conventions name the book's registry or
its name table holds. The mapping is written here by hand, and checked against both."""
import lib  # lib first: threads and seeds are fixed before anything else

from importlib.metadata import version

from openinference.semconv.trace import OpenInferenceLLMSystemValues, OpenInferenceSpanKindValues, SpanAttributes

from lib import genai
from lib.names_map import NAMES

# OpenInference's constant and the GenAI name for the same fact. OpenInference's span kind has no GenAI attribute: the
# operation name carries the same meaning, chat for a model call.
MAPPING = (
    (SpanAttributes.LLM_MODEL_NAME, "gen_ai.request.model"),
    (SpanAttributes.LLM_SYSTEM, "gen_ai.provider.name"),
    (SpanAttributes.LLM_TOKEN_COUNT_PROMPT, "gen_ai.usage.input_tokens"),
    (SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, "gen_ai.usage.output_tokens"),
    (SpanAttributes.LLM_TOKEN_COUNT_PROMPT_DETAILS_CACHE_READ, "gen_ai.usage.cache_read.input_tokens"),
    (SpanAttributes.OPENINFERENCE_SPAN_KIND, "gen_ai.operation.name"),
    (SpanAttributes.LLM_INPUT_MESSAGES, "gen_ai.input.messages"),
    (SpanAttributes.LLM_OUTPUT_MESSAGES, "gen_ai.output.messages"),
)
known = set(genai.ATTR) | {name for names in NAMES.values() for name in names}
print("openinference-semantic-conventions version:", version("openinference-semantic-conventions"))
for openinference, conventions in MAPPING:
    print(f"{openinference} -> {conventions}")
    assert conventions in known
print("span kind for a model call:", OpenInferenceSpanKindValues.LLM.value)
print(f"{SpanAttributes.LLM_SYSTEM} for an OpenAI client:", OpenInferenceLLMSystemValues.OPENAI.value)
```

Output:

```text
openinference-semantic-conventions version: 0.1.46
llm.model_name -> gen_ai.request.model
llm.system -> gen_ai.provider.name
llm.token_count.prompt -> gen_ai.usage.input_tokens
llm.token_count.completion -> gen_ai.usage.output_tokens
llm.token_count.prompt_details.cache_read -> gen_ai.usage.cache_read.input_tokens
openinference.span.kind -> gen_ai.operation.name
llm.input_messages -> gen_ai.input.messages
llm.output_messages -> gen_ai.output.messages
span kind for a model call: LLM
llm.system for an OpenAI client: openai
```

The example prints each OpenInference name beside its GenAI name, and the run checks every pair against the name table, so a constant that moves at the next pin fails the run. The token counts are the pairs a reader meets first: `llm.token_count.prompt` pairs with `gen_ai.usage.input_tokens`, and `llm.token_count.completion` with `gen_ai.usage.output_tokens`.

The script asserts that each GenAI name is one the book's [name table](#hand-made-against-instrumented) holds, so a mapping that names a missing name fails the run. OpenInference's span kind has no GenAI attribute of its own. The output records that a model call is `LLM` in OpenInference, and the operation name carries the same meaning in the GenAI names, as `chat`. Its OpenAI provider value is `openai`, the same string the first OpenTelemetry package writes for an `openai` client.

OpenLLMetry's names come from `opentelemetry-semantic-conventions-ai`, version 0.5.1, released 26 March 2026, which Traceloop's 0.63.1 package uses. The caveat about these readings is in [Three packages called openai](#the-three-openai-packages). Four of OpenLLMetry's names have a registry name that does the same job: `gen_ai.client.operation.duration` for `gen_ai.client.inference.duration`, `gen_ai.client.token.usage` for the input and output histograms, `gen_ai.usage.cache_creation.input_tokens` for `gen_ai.usage.cache_write.input_tokens`, and `gen_ai.usage.reasoning_tokens` for `gen_ai.usage.reasoning.output_tokens`.

We recommend the OpenTelemetry names throughout this book. The backends that chapter 5, [What others do](#what-others-do), describes say they ingest those names, and each claim is given there with its version and date. Choose a scheme for another reason only when a backend you run reads that scheme and nothing else. Do not mix schemes in one trace. A query for `gen_ai.usage.input_tokens` finds no span that writes `llm.token_count.prompt`, and its total comes out short, with no [error](#how-a-span-records-failure) to say so.

**Working rule:** Map each scheme's names onto the registry's once, in a table in code, and fail the run for any name the table does not hold, as the mapping example above does. Choose one scheme for a service's spans before the first span is sent, and keep the names of the others out of its traces.

## What goes wrong in production {#client-library-instrumentation-in-production}

Four things go wrong with the package in production.

- **The pre-release.** The first package is at a pre-release version, and its page warns that its experimental features may change without notice. The pin holds one version. A team that upgrades takes whatever names the next release writes, so the name table must be regenerated, and the run must fail on a name it does not hold.
- **The switch in the wrong place.** The spec's name does nothing with this package, and no error says so. The opposite mistake is worse. A team that adds Traceloop's package and sets nothing has turned prompt capture on, because that package's default is on, in its 0.63.1 wheel, and a context override can turn it back on even when the variable is `false`.
- **Dashboards on the registry's names.** A chart that reads `gen_ai.client.inference.duration` from this package finds no points, since the package writes `gen_ai.client.operation.duration`. [The earlier section](#hand-made-against-instrumented) lists each name that differs.
- **Two packages on one client.** A service that loads a second instrumentation package for the same client may write each call's span twice, under two sets of names. No example here loads two, so this is not shown; a test that counts spans per call would show it.

## The decisions this chapter made {#client-library-instrumentation-decisions}

A package's names lag the standard, and each choice below says how the book lives with that:

- The model calls are wrapped by the OpenTelemetry package pinned at 1.3b0, and the book's own spans wrap only the work the package cannot see.
- The five names that the package writes differently from the registry are mapped once, in a generated table, and the rest of the book reads the package's output through that table.
- Content capture is off in every example in this chapter except one control, which records content for one call and prints only its count. Chapter 12 turns it on, on purpose, and says what it leaks.
- Metrics are printed by name, unit and point count, and never by value, because their duration instruments use real time.
- The book uses the OpenTelemetry names because they are the ones the backends in [chapter 5](#what-others-do) say they ingest, so [changing the backend](#changing-backends) is a change of settings, not of spans.
- The three package names are given exactly, and only the first is run. The other two are wheel readings, as [the section on the three packages](#the-three-openai-packages) explains.

**Working rule:** Pin the instrumentation package at its exact version, generate its name table from its own output, and read its content switch from its source at that version before you trust the content a span holds. A package that changes its names or its defaults changes what your traces hold, and its version and its scopes' schema URL are the signals you get that it has.
