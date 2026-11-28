---
title: "Observability for LLM Applications"
chapter: "Name spans the way the standard does"
chapter_id: name-spans
book: observability-for-llm-applications
edition: 2026.11.4
verified: 2026-11-23
edition_code: XFJ3-KNEQ
canonical: https://rollingedition.com/observability-for-llm-applications/name-spans
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Name spans the way the standard does,” chapter 2 of Observability for LLM Applications, Edition 2026.11.4, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/name-spans. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Name spans the way the standard does

By the end of this chapter you can give each span in the assistant's traces the name, the kind and the attributes that OpenTelemetry's GenAI conventions expect for its step. You can say which software made the span and which schema version its names follow, and you can run a check that fails when a span drifts from the registry.

Ambrewick's on-call engineers, who run the assistant whose traces this book builds ([one message, one trace](#one-message-one-trace)), want those traces in the tools they already run. Those tools know one vocabulary: the names the conventions give a model call, a retrieval, a tool run and an agent's turn. [Chapter 1's names](#spans-by-hand) mean nothing there. The validator, the check this chapter builds, compares each span with the registry's rules. Run on message 809, a devices question with a retrieval, its 4 spans draw 4 findings, one per span, and each says the span has no known span type. The SDK raised none of them, because the SDK accepts any name. So this chapter gives each span the standard's name and kind, records who made it, and builds the check that keeps the names right. Chapter 3 then measures a client library's spans against these names.

## The standard at a Development version {#the-standard-at-v0-1-0}

A [backend](#otlp-over-http) answers a question about a span by its name. A question such as how long the model calls took this week only has one answer if every backend agrees which spans are model calls, and the standard is that agreement. A semantic convention is a published name, type and meaning for a span, attribute or [metric](#totals-from-metrics-not-spans), so that any backend reads the same name the same way. The standard is OpenTelemetry's GenAI semantic conventions.

The GenAI names first lived in OpenTelemetry's core semantic conventions repository. That repository deprecated its names under the `gen_ai` prefix in its release 1.42.0, and they moved to a repository of their own ([changelog](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.42.0/CHANGELOG.md)). This book follows that repository's first standalone release, GenAI conventions, version 0.1.0 ([changelog](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/CHANGELOG.md)).

The conventions come in two forms: pages for people to read, and the registry, a YAML model of the span types, their kinds and their attributes that a program can read. The book's validator reads the registry at the pinned version, so the names it checks are the ones the registry lists.

Every page of the GenAI conventions, version 0.1.0, is Development: its names may change in any release. The specification defines Development for its own components, and its status page says of such a component: "The component MAY be removed without prior notice. The component SHOULD NOT be used in production." ([status page](https://raw.githubusercontent.com/open-telemetry/opentelemetry-specification/v1.52.0/specification/document-status.md)). The GenAI pages carry the same status, and their changelog shows the names moving. The first standalone release renamed the [inference span](#span-types-for-each-step) type from `gen_ai.inference.client` to `gen_ai.client.inference`. The book's names follow that release, so a later release can rename them.

**Working rule:** Pin the conventions' version beside every name you publish. A dashboard built on a Development name needs a check that runs when the name changes.

## Span types for each step {#span-types-for-each-step}

The registry sorts spans into span types, and each type has a name pattern, a [span kind](#span-kind-follows-the-process) and the attributes it requires. [Chapter 1's steps](#spans-by-hand) fall into four of them. An inference span is the span of one client call to a generative model that answers the prompt or asks for a tool call. A retrieval span is the span of one run of the application's retrieval step, which returns the documents relevant to a query. A tool-execution span is the span of one run of a tool, named for the tool. An agent-invocation span is the span of one invocation of an agent. The book's agent runs in the assistant's process, so its span is the in-process type, which also covers workflows. A remote agent's span is a CLIENT span of its own type. The route and answer steps are model calls, the retrieve step is a search, the tool runs are tool runs, and each message's root is one agent run.

| Span type | Name pattern | Kind | Operation name |
| --- | --- | --- | --- |
| Inference | `{operation} {model}` | CLIENT, or INTERNAL in process | `chat` |
| Retrieval | `{operation}` | INTERNAL | `retrieval` |
| Tool execution | `execute_tool {tool}` | INTERNAL | `execute_tool` |
| Agent invocation | `invoke_agent {agent}` | INTERNAL in process; CLIENT for a remote agent | `invoke_agent` |

Example `inference-span-names` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""Print the span name each step gets from the assistant, beside the registry's pattern for that span type. The names are
the spans', the patterns are the registry's, and each assert checks one span's name against its pattern.

The point rests on the four name lines: the inference, tool and agent names from message 11159 (a route, an answer, a
tool call and a second answer), and the retrieval name from message 809."""
from lib.assistant import Assistant
from lib.bm25 import Retriever
from lib.case import load_articles, load_messages, load_tool_durations
from lib.clock import VirtualClock
from lib.dayrun import DAY, RECORDING, RELEASE
from lib.export import spans_to_rows
from lib.genai import REGISTRY_VERSION, SCHEMA_URL, SPAN_OPERATIONS, SPAN_TYPES
from lib.ids import SequentialIds
from lib.replay import Replay, ReplayContacts
from lib.tools import Tools
from lib.tracing import make_provider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

replay = Replay(RECORDING)
retriever, tools = Retriever(load_articles(), RELEASE.top_k), Tools(load_tool_durations(), ReplayContacts(replay))
rows = {}
for message in (m for m in load_messages(DAY) if m.message_id in ("809", "11159")):
    clock, exporter = VirtualClock(DAY, start_ns=message.arrival_ns), InMemorySpanExporter()  # one exporter per message
    tracer = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", clock, SequentialIds(),
                           exporter, SCHEMA_URL).get_tracer("ambrewick.assistant", schema_url=SCHEMA_URL)
    Assistant(replay, retriever, tools, clock, tracer, RELEASE).handle(message)
    rows[message.message_id] = spans_to_rows(exporter)
agent = next(row for row in rows["11159"] if row["parent_span_id"] is None)  # the root is the agent's invocation
inference = next(row for row in rows["11159"] if row["attributes"].get("gen_ai.operation.name") == "chat")
tool = next(row for row in rows["11159"] if row["attributes"].get("gen_ai.operation.name") == "execute_tool")
retrieval = next(row for row in rows["809"] if row["attributes"].get("gen_ai.operation.name") == "retrieval")
print("GenAI conventions version:", REGISTRY_VERSION)
print("inference span name:", inference["name"])
print("retrieval span name:", retrieval["name"])
print("tool span name:", tool["name"])
print("agent span name:", agent["name"])
print("inference provider name:", inference["attributes"]["gen_ai.provider.name"])
print("inference prompt name:", inference["attributes"]["gen_ai.prompt.name"])
print("inference prompt version:", inference["attributes"]["gen_ai.prompt.version"])
# Model spans are `{operation} {model}`, retrieval is its operation alone, tools are `execute_tool {tool}`, the agent is
# `invoke_agent {agent}`. Each assert checks one span against its pattern.
assert inference["name"] == f"chat {RELEASE.model}" and retrieval["name"] == "retrieval"
assert tool["name"] == f"execute_tool {tool['attributes']['gen_ai.tool.name']}"
assert agent["name"] == f"invoke_agent {agent['attributes']['gen_ai.agent.name']}"
for span_type in sorted(SPAN_OPERATIONS):  # the operation names the registry defines, per span type
    print(f"operation names, {span_type}:", ", ".join(SPAN_OPERATIONS[span_type]))
for span_type in sorted(SPAN_TYPES):  # the attributes the validator requires, per span type
    print(f"required attributes, {span_type}:", len(SPAN_TYPES[span_type]["required"]))
```

Output:

```text
GenAI conventions version: 0.1.0
inference span name: chat qwen3-4b-instruct-2507
retrieval span name: retrieval
tool span name: execute_tool remove_item
agent span name: invoke_agent ambrewick-assistant
inference provider name: openai
inference prompt name: ambrewick.route
inference prompt version: p1
operation names, gen_ai.client.inference: chat, generate_content, realtime_inference, text_completion
operation names, gen_ai.execute_tool: execute_tool
operation names, gen_ai.invoke_agent.internal: invoke_agent
operation names, gen_ai.retrieval: retrieval
required attributes, gen_ai.client.inference: 2
required attributes, gen_ai.execute_tool: 2
required attributes, gen_ai.invoke_agent.internal: 1
required attributes, gen_ai.retrieval: 1
required attributes, mcp.client: 1
required attributes, mcp.server: 1
```

The model span changes most. Its name is the operation, a space, and the model's name, so a reader scanning a trace sees which model answered each call. Message 11159, a lists request with one tool call, has its first model call named `chat qwen3-4b-instruct-2507`. The registry gives one list of well-known values for `gen_ai.operation.name` on an inference span, and a custom value MAY be used beyond it ([registry attributes](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/registry/attributes/gen-ai.md)). The validator maps each value to a span type through a map the book makes, and that map gives the inference type `chat, generate_content, realtime_inference, text_completion`. The assistant writes `chat` for each of its calls. The example asserts the model span's name against the operation and the model the run used, and it builds the tool and agent names from the attributes their spans carry, so a drift in either one fails the run.

The retrieval span is named by its operation alone, `retrieval`. The registry's pattern leaves no room for the index it searched, so the knowledge base's name stays out of the span name. A tool run is named for its tool, `execute_tool remove_item`, the run of the list tool that removed an item in message 11159. The root is named `invoke_agent ambrewick-assistant`, and it replaces chapter 1's `message` span. We keep `invoke_agent` rather than `invoke_workflow`, because the model chooses the route and whether to call a tool. The model drives the control flow through tool calls, which is the case the registry's agent type describes.

One attribute the registry leaves open is the provider. In the book, the inference span's `gen_ai.provider.name` is `openai`, and that value is our judgement. The registry's well-known values for the attribute include no value for llama.cpp, and a provider the list lacks may take a custom value ([registry](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/model/gen-ai/registry.yaml)). The attribute's general note says it "SHOULD be set based on the instrumentation's best knowledge and may differ from the actual upstream provider" ([client inference](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/client-inference.md)). We record `openai` because Ambrewick's client speaks OpenAI's API to its endpoint, and the official package records `openai` for that call, as chapter 3 shows. A reader whose model is served another way should choose by the same rule and say so.

Of the spans the assistant makes, the fallback span is the only one the registry does not name. The book keeps it, the validator flags it, and the [validation section](#validating-against-the-registry) says why that flag is the right answer.

**Working rule:** Name each span from its registry pattern, not from the function that made it, and take the operation name from the registry's well-known values. Where the registry gives no value for something you run, use the value the client and its official instrumentation would write, and say that it's a judgement.

## The span kind follows the process {#span-kind-follows-the-process}

A span's kind says where its work ran: CLIENT for a call out of the process, SERVER for one received, INTERNAL for work inside (two more, PRODUCER and CONSUMER, mark work handed to a queue). The model call is the hard case. The registry says "It's RECOMMENDED to use `CLIENT` kind when the GenAI system being instrumented usually runs in a different process than its client or when the GenAI call happens over instrumented protocol such as HTTP" ([client inference](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/client-inference.md)). A model behind an endpoint is reached by a call that leaves the assistant's process, so its span is CLIENT. The registry also allows INTERNAL for a model running in the same process, which is why the kind is a judgement at all. The book applies the rule with a test a span can show: whether the call names a server. A call that names a server is CLIENT, and a call that names none can be INTERNAL.

Example `span-kinds-by-process` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""Give one model call two kinds: CLIENT when the model sits behind an endpoint, as the trace shows it, and INTERNAL
when the same assistant runs the model in process. Then run the validator on both.

The point rests on the two model-call kind lines and on the zero findings: the registry allows INTERNAL for an
in-process model (it says MAY), and the validator accepts it when the call names no server. An endpoint span marked
INTERNAL is flagged, because it names one."""
from lib.dayrun import DAY, RECORDING, run_day_traced
from lib.genai import REGISTRY_VERSION, validate
from lib.replay import Replay


class InProcess:
    """The recorded model, run as if it shared the assistant's process: the same answers, and no endpoint."""

    in_process = True

    def __init__(self, replay):
        self._replay = replay

    def reply(self, request):
        return self._replay.reply(request)


rows = run_day_traced(DAY, ["809"], live=False).spans  # a devices message: a route and an answer call, behind an endpoint
local = run_day_traced(DAY, ["809"], backend=InProcess(Replay(RECORDING)), live=False).spans  # the same model in process
endpoint = next(row for row in rows if row["name"].startswith("chat "))
in_process = next(row for row in local if row["name"].startswith("chat "))
retrieval = next(row for row in rows if row["name"] == "retrieval")
root = next(row for row in rows if row["parent_span_id"] is None)
marked = dict(endpoint, kind="INTERNAL")  # the endpoint's span, wrongly marked as in process

print("GenAI conventions version:", REGISTRY_VERSION)
print("model call kind, behind an endpoint:", endpoint["kind"])
print("model call kind, in process:", in_process["kind"])
address, port = endpoint["attributes"]["server.address"], endpoint["attributes"]["server.port"]
print("server the endpoint span names:", f"{address}:{port}")
print("findings on the in-process span:", len(validate(in_process)))
print("findings on the endpoint span marked INTERNAL:", len(validate(marked)))
print("retrieval span kind:", retrieval["kind"])
print("agent span kind:", root["kind"])
assert validate(endpoint) == [] and validate(in_process) == []  # both kinds are the registry's
assert "server.address" not in in_process["attributes"]  # an in-process model names no server
assert len(validate(marked)) == 1 and "kind is INTERNAL" in validate(marked)[0]
assert validate(retrieval) == [] and validate(root) == []  # INTERNAL is the registry's kind for these two types
```

Output:

```text
GenAI conventions version: 0.1.0
model call kind, behind an endpoint: CLIENT
model call kind, in process: INTERNAL
server the endpoint span names: localhost:8000
findings on the in-process span: 0
findings on the endpoint span marked INTERNAL: 1
retrieval span kind: INTERNAL
agent span kind: INTERNAL
```

Running message 809's model calls both ways shows the rule at work. Message 809 is a devices question with a route and an answer call. Behind the endpoint the span's kind is `CLIENT`, and the same calls run in process give `INTERNAL`. The endpoint's span names a server, and the in-process span names none. The validator reports `0` findings on the in-process span, which the example asserts. Marked INTERNAL, the endpoint's span still names a server, and the validator reports `1` finding on it. The finding's text is asserted to name the kind, `kind is INTERNAL`, and only its count is printed. That finding is the failure the rule prevents.

The [dev-day](#replay-and-the-virtual-clock) traces in this book are all CLIENT, because the recorded model calls were served over an endpoint. The in-process case is the same model called from the assistant's own code, and the book runs it only in this example. A reader who moves a model into the process should expect the kind to change with it, and should expect the validator to say so if the span still names a server.

The retrieval span and the agent span are both INTERNAL, which the example asserts for each, because their work runs inside the assistant. The printed kinds are `INTERNAL` for the retrieval span and `INTERNAL` for the agent span. The registry gives both kinds ([registry](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/model/gen-ai/spans.yaml)), and the validator checks them.

**Working rule:** Give a model span CLIENT when the call goes to a server, even one on the same machine. Give it INTERNAL only when the model runs in your process and the span names no server, and let the validator check each kind you set.

## Which attributes a span must carry {#requirement-levels}

A name tells a backend what a span is. The requirement level tells it which attributes that span must carry. A requirement level says when an attribute must appear: required, conditionally required, recommended or opt-in ([requirement levels](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/docs/general/attribute-requirement-level.md)). A required attribute appears on every span of its type. A conditionally required one appears when its condition holds, and the registry writes the condition beside it. A recommended attribute says what a good span carries, and an opt-in one appears only when something switches it on.

The registry also says which attributes each span type must carry. The book's module, `lib.genai`, holds every requirement level from the registry, so the requirement levels and kinds that the [validator](#validating-against-the-registry) checks are the registry's, not a list someone typed. The validator checks the kind and the required attributes, and nothing else, so a span can pass it and still lack what the registry asks for in a conditional case. The validator's counts, as the inference-span-names example prints them, show how many each span type requires: `2` on an inference span, `2` on a tool-execution span, `1` on the retrieval span and `1` on the agent span. Its required attributes are its operation name and its provider name, so the [provider judgement](#span-types-for-each-step) is not optional. A span without either one fails the check.

Opt-in attributes are the ones to watch for privacy. The message contents of a model call are opt-in, so the book's spans carry none of them unless a switch asks for them, and chapter 3 says what that switch does.

Conditional requirements are the ones the validator does not read. `gen_ai.prompt.version` is conditionally required on the inference span when the span carries `gen_ai.prompt.name` and a version is available. `gen_ai.prompt.name` is conditionally required when a named prompt template is used ([registry](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/model/gen-ai/spans.yaml)). The assistant's prompts are named and versioned, so its inference spans carry both: `ambrewick.route` and `p1` on the route call in message 11159. Chapter 10 queries that pair to tell releases apart. The validator reads only required attributes, so it would not report a span that lacks either one, and a gap in a conditional attribute is a gap it will not report.

**Working rule:** Read a span's requirement levels before you read its name. A missing required attribute is a defect in the span. A missing conditionally required attribute is a defect only when its condition holds, so read the condition in the registry before you file it.

## Who made the span {#who-made-the-span}

A span says what it measured, and two other places say who measured it: the [resource](#spans-by-hand) and the instrumentation scope. The instrumentation scope names the unit of code that made a span, usually an [instrumentation library](#a-call-through-the-client), and here the assistant's own module. A schema URL names a published telemetry schema, a release of the semantic conventions, that the telemetry follows. The prose never types a schema URL; each one here is printed by its example.

The resource carries three attributes the book sets itself. `service.name` is `ambrewick-assistant`. `service.version` is `1.0.0`, and it marks the release, which chapter 10 reads to split traces by release. `service.instance.id` is `dev-day-replay`. The [replay](#replay-and-the-virtual-clock) sets the instance ID itself, so a rerun names the same instance and its traces can be compared run to run. A process that restarts keeps its instance ID only if one was set, and a query that follows one instance through a restart needs the ID to stay put.

Example `resource-and-schema` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""Print the resource and the instrumentation scope of the renamed spans, with the schema URL each one carries, beside
chapter 1's stamp.

The point rests on the schema lines: chapter 1's resource said 1.44.0, the renamed spans say 1.45.0, and the SDK's
constants have no 1.45.0 schema, which the assert checks. The book takes that URL from the registry's manifest
(genai.SCHEMA_URL), and make_provider puts it on the tracer as well as the resource."""
from lib.dayrun import RELEASE
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.tracing import make_provider, span
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.schemas import Schemas

CHAPTER_1_SCHEMA = "https://opentelemetry.io/schemas/1.44.0"


def version_key(url):
    """Sort key for a schema URL: its version as numbers, so 1.9 sorts before 1.44."""
    return tuple(int(part) for part in url.rsplit("/", 1)[1].split("."))


exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", None, SequentialIds(),
                         exporter)
tracer = provider.get_tracer("ambrewick.assistant")  # no schema given: the tracer carries the provider's
span(tracer, "resource probe", 1, 2)  # one ended span, so the scope's schema can be read from it
scope = exporter.get_finished_spans()[0].instrumentation_scope
chapter_1 = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", None, SequentialIds(),
                          InMemorySpanExporter(), CHAPTER_1_SCHEMA)  # the resource chapter 1 built, read back from it
known = {schema.value for schema in Schemas}  # what opentelemetry-semantic-conventions 0.66b2 can stamp
print("chapter 1's resource schema URL:", chapter_1.resource.schema_url)
print("renamed spans' resource schema URL:", provider.resource.schema_url)
print("renamed spans' scope schema URL:", scope.schema_url)
print("instrumentation scope name:", scope.name)
print("highest schema in the SDK's constants:", max(known, key=version_key))
print("service.name:", provider.resource.attributes["service.name"])
print("service.version:", provider.resource.attributes["service.version"])
print("service.instance.id:", provider.resource.attributes["service.instance.id"])
assert SCHEMA_URL not in known  # the constants stop at 1.44.0, so the book takes its 1.45.0 from the registry
assert provider.resource.schema_url == scope.schema_url == SCHEMA_URL
assert provider.resource.attributes["service.instance.id"] == "dev-day-replay"  # set, not drawn at random
```

Output:

```text
chapter 1's resource schema URL: https://opentelemetry.io/schemas/1.44.0
renamed spans' resource schema URL: https://opentelemetry.io/schemas/1.45.0
renamed spans' scope schema URL: https://opentelemetry.io/schemas/1.45.0
instrumentation scope name: ambrewick.assistant
highest schema in the SDK's constants: https://opentelemetry.io/schemas/1.44.0
service.name: ambrewick-assistant
service.version: 1.0.0
service.instance.id: dev-day-replay
```

The schema URL moved in this chapter, and the example prints both values. [Chapter 1's resource](#spans-by-hand) said `https://opentelemetry.io/schemas/1.44.0`. That was the newest schema the pinned semantic-conventions package carries, `0.66b2`, and its highest schema is `https://opentelemetry.io/schemas/1.44.0`. Chapter 1's names followed no convention, so that stamp described nothing the book's spans said. The renamed spans stamp `https://opentelemetry.io/schemas/1.45.0`, which is the core semantic-conventions release that GenAI conventions v0.1.0 depend on. The GenAI conventions publish no schema URL of their own at v0.1.0. Core deprecated its `gen_ai.*` names in 1.42.0, when they moved to their own repository. So the stamp says which core release the resource's `service.*` names follow, and the GenAI version travels beside the check, `0.1.0`. The book's generated module takes that URL from the registry's manifest, and the example asserts that the SDK's constants do not contain it. The constants stop at their own release. Of the `service.*` attributes, the release that URL names deprecates only `service.peer.name` and `service.peer.namespace` ([changelog](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/CHANGELOG.md)), so the three the resource sets read the same under either URL.

The instrumentation scope of the renamed spans is `ambrewick.assistant`, and its schema URL is the same as the resource's, which the example asserts. The official client library writes a scope of its own.

**Working rule:** Set `service.name` and `service.version` on the resource yourself, and give `service.instance.id` a value unique to the instance, as the production section explains. Then give the tracer the schema URL of the core release your conventions depend on, from the registry's manifest and not from the SDK's constants, which can lag behind the conventions. Pin the GenAI conventions' version beside the validator, because at v0.1.0 they have no schema URL to stamp.

## Validating against the registry {#validating-against-the-registry}

A name is a claim about the registry, and the validator makes that claim testable. It finds each span's type from `gen_ai.operation.name`, or, for an MCP span, from its method. MCP is the Model Context Protocol, the protocol a tool server speaks. The validator then checks the span's kind and required attributes against the registry's rules. A span whose type it cannot find gets a finding that says so, and each finding names its span, so the output reads as a list of what to fix.

The validator cannot name [chapter 1's spans](#one-message-one-trace), because they carry no `gen_ai.operation.name`, the attribute it reads to find a span's type. Message 809's 4 spans are `message`, `route`, `retrieve` and `answer`, and the check prints one finding for each: `no known span type for this row`. The finding gives the reason. Once the root is renamed, `message` becomes `invoke_agent ambrewick-assistant`, and that span is checked against its own type.

Example `validate-the-spans` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""Run the validator over chapter 1's rough spans for message 809: every span fails, because none names a registry span
type.

The point rests on the count of findings, one per span, and on the text of each: "no known span type" means the span
carries neither `gen_ai.operation.name` nor an MCP method, which is how the validator finds a registry span's type."""
from lib.dayrun import RELEASE, run_dev_day
from lib.export import spans_to_rows
from lib.genai import REGISTRY_VERSION, validate
from lib.ids import SequentialIds
from lib.report import fmt_int
from lib.tracing import make_provider, span
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# Chapter 1 stamped this schema; kept so the spans are the ones chapter 1 printed.
CHAPTER_1_SCHEMA = "https://opentelemetry.io/schemas/1.44.0"

(run,) = run_dev_day(["809"])  # message 809: a route call, a retrieval, and an answer call
outcome = run.outcome
exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", run.clock, SequentialIds(),
                         exporter, CHAPTER_1_SCHEMA)
tracer = provider.get_tracer("ambrewick.assistant")
# Chapter 1's names: the root is the message, each step is named by its step, and no kind is set (INTERNAL).
root = span(tracer, "message", run.arrived_ns, run.replied_ns,
            attributes={"ambrewick.route": outcome.route, "ambrewick.reply.source": outcome.source})
for step in outcome.steps:
    attributes = {"ambrewick.step": step.step}
    if step.step in ("route", "answer"):  # model calls carry their token counts, under the book's own keys
        attributes |= {"ambrewick.tokens.input": step.prompt_tokens, "ambrewick.tokens.cached": step.cached_tokens,
                       "ambrewick.tokens.output": step.completion_tokens}
    span(tracer, step.step, step.start_ns, step.end_ns, parent=root, attributes=attributes)

rows = spans_to_rows(exporter)  # sorted by (trace, start, span), so the findings print in the same order every run
findings = [finding for row in rows for finding in validate(row)]
print("GenAI conventions version:", REGISTRY_VERSION)
print("spans checked:", fmt_int(len(rows)))
for finding in findings:
    print("finding:", finding)
print("findings, no known span type:", fmt_int(sum("no known span type" in finding for finding in findings)))
print("findings, all:", fmt_int(len(findings)))
assert all(len(validate(row)) == 1 for row in rows)  # each span fails once, and only once
```

Output:

```text
GenAI conventions version: 0.1.0
spans checked: 4
finding: message: no known span type for this row
finding: route: no known span type for this row
finding: retrieve: no known span type for this row
finding: answer: no known span type for this row
findings, no known span type: 4
findings, all: 4
```

Renamed, the spans pass. Across all 20 dev-day messages the example checks 74 spans, and it finds 0 problems on any span the registry defines. A single assertion holds that count at zero, so a change that breaks a name fails the run instead of printing a new number.

Example `validate-the-renamed-spans` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.4:

```python
"""Run the validator over every span of the dev day's twenty messages: no finding on any span the registry defines, and
one on each of the book's own fallback spans, which the registry does not define.

The point rests on the line "findings on registry spans: 0", which is asserted, and on the fallback count, which
equals the fallback replies."""
from lib.assistant import Assistant
from lib.bm25 import Retriever
from lib.case import load_articles, load_messages, load_tool_durations
from lib.clock import VirtualClock
from lib.dayrun import DAY, RECORDING, RELEASE
from lib.export import spans_to_rows
from lib.genai import REGISTRY_VERSION, SCHEMA_URL, validate
from lib.ids import SequentialIds
from lib.replay import Replay, ReplayContacts
from lib.report import fmt_int
from lib.tools import Tools
from lib.tracing import make_provider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from collections import Counter

replay = Replay(RECORDING)
retriever, tools = Retriever(load_articles(), RELEASE.top_k), Tools(load_tool_durations(), ReplayContacts(replay))
messages, fallback_replies, rows = load_messages(DAY), 0, []
for message in messages:  # arrival order, as the replay needs; each message gets its own clock, exporter and trace
    clock = VirtualClock(DAY, start_ns=message.arrival_ns)
    exporter = InMemorySpanExporter()  # one per message, so each message's IDs start from 1
    tracer = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", clock, SequentialIds(),
                           exporter, SCHEMA_URL).get_tracer("ambrewick.assistant", schema_url=SCHEMA_URL)
    fallback_replies += Assistant(replay, retriever, tools, clock, tracer, RELEASE).handle(message).source == "fallback"
    rows += spans_to_rows(exporter)

book = [row for row in rows if row["name"] == "ambrewick.fallback"]
# The book's own fallback span is not a registry span, so it is checked apart from the others.
registry_findings = [finding for row in rows if row["name"] != "ambrewick.fallback" for finding in validate(row)]
book_findings = [finding for row in book for finding in validate(row)]
# A span with no gen_ai.operation.name is counted under its own name, which is how the fallback span appears.
operations = Counter(row["attributes"].get("gen_ai.operation.name", row["name"]) for row in rows)
print("GenAI conventions version:", REGISTRY_VERSION)
print("messages:", fmt_int(len(messages)))
print("spans checked:", fmt_int(len(rows)))
for operation in sorted(operations):
    print(f"spans, {operation}:", fmt_int(operations[operation]))
print("findings on registry spans:", fmt_int(len(registry_findings)))
print("fallback replies:", fmt_int(fallback_replies))
print("findings on the book's fallback span:", fmt_int(len(book_findings)))
assert not registry_findings  # zero findings on every span the registry defines
assert len(book_findings) == len(book) == fallback_replies  # one per fallback span, and each span is a fallback reply
assert all("no known span type" in finding for finding in book_findings)
```

Output:

```text
GenAI conventions version: 0.1.0
messages: 20
spans checked: 74
spans, ambrewick.fallback: 6
spans, chat: 37
spans, execute_tool: 3
spans, invoke_agent: 20
spans, retrieval: 8
findings on registry spans: 0
fallback replies: 6
findings on the book's fallback span: 6
```

The validator does flag other spans. The 6 [fallback replies](#where-the-time-went-in-twenty-messages) each have an `ambrewick.fallback` span, and the check flags all 6 of them, each with `no known span type`. That is correct, and it is not a failure of the conventions. The registry defines the types it names, and a span outside them has no type. The book's own spans and attributes sit in the `ambrewick.` namespace, which is the book's, and the naming rules ask that names sit in a namespace ([naming rules](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/docs/general/naming.md)). A finding that says a span is outside the registry says the span is the book's own. Each flag is asserted to be that finding and no other, so a registry span that gained a flag would fail the run.

**Working rule:** Read a finding on a registry span as a defect. Read a finding on a span in your own namespace as the registry's answer that the span is yours.

## Name spans in production {#name-spans-in-production}

The validator here runs on recorded spans, inside examples. In production the same check has to run on the spans a service actually exports, and three things make it fail quietly. A fourth decides whether the instance ID means anything. We recommend using a Development name in production when it's pinned and validated, because the validator's first run after an upgrade shows what moved.

The first is the name's content. The specification asks that a span name be "the most general string" for its class of spans, and it marks `get_account/42` as too specific ([span API](https://raw.githubusercontent.com/open-telemetry/opentelemetry-specification/v1.52.0/specification/trace/api.md)). The model span's name carries the model, from a short fixed list, which is general enough. A name built from a user's ID would be a new name for each user, and the registry's pattern has no room for one. A reviewer who sees an identifier in a span name should treat it as a defect, whatever the validator says.

The second is the SDK. It does not stop a wrong name. [Chapter 1's rough names](#spans-by-hand) went through unchanged, and a misspelled registry name would too. Only the validator reads the registry, so a pipeline that exports spans without running it has no check at all. We recommend running the validator in the pipeline that exports spans, not only in tests.

The third is upgrades. A Development name can change in any release, and the validator's first run after an upgrade lists what moved. Read that list before you change the pinned version, and change the names in the same pull request as the version. Spans from another package that writes older names may also reach the same backend. A backend holding those and this book's spans sees two vocabularies for one step.

The fourth is the instance ID. The `service.namespace`, `service.name` and `service.instance.id` triplet MUST be globally unique ([service registry](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/model/service/registry.yaml)). The SDK's default is a new random UUID in each process. In production, keep that random UUID, or derive a UUIDv5 from an ID unique to the instance, and never share one value across replicas. The replay's fixed instance ID is right for a replay and wrong to copy.

When you add a span, write its registry type first, then its name, then its kind. We recommend this order because the type fixes the name pattern and the kind.

**Working rule:** Run the validator in the pipeline that exports your spans, and fail the build on a finding. Pin the conventions' version beside the check, and read the changelog before you raise it.

## What this chapter decided {#name-spans-decisions}

The registry will move, and the names will move with it. What this chapter fixes is which version the book's spans follow, and a check that reports when they stop following it. Each choice below is one the rest of the book relies on, and an example asserts each one it can.

- The book's names follow GenAI conventions 0.1.0, and the version is pinned beside the validator, because the registry is Development.
- The retrieval span is named by its operation alone, `retrieval`, because the registry's pattern has no place for anything else.
- The provider value is `openai`. That is our judgement, quoted beside the registry's guidance, and the validator cannot check it, because the registry has no value for llama.cpp to check it against.
- The assistant's prompts are named and versioned, so an inference span carries `gen_ai.prompt.name` with `gen_ai.prompt.version`, which the registry makes conditionally required.
- A model span's kind follows the process: CLIENT behind a server, and INTERNAL only in process, when the span names no server.
- The book's resource and tracer carry the schema URL of the core release the registry depends on, not the SDK's newest constant.
- The validator reports a finding on a registry span as a defect, and the book's own fallback spans get findings of their own, which are not defects.
