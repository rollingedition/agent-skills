---
title: "Observability for LLM Applications"
chapter: "Send traces to a backend you can run"
chapter_id: send-to-a-backend
book: observability-for-llm-applications
edition: 2026.11.1
verified: 2026-11-23
edition_code: B95K-8RWR
canonical: https://rollingedition.com/observability-for-llm-applications/send-to-a-backend
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Send traces to a backend you can run,” chapter 5 of Observability for LLM Applications, Edition 2026.11.1, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/send-to-a-backend. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Send traces to a backend you can run

By the end of this chapter you can send the spans of both processes to one receiver that you run on one machine, check that it stores the rows the exporter sent, query those rows with SQL, and say what each named backend accepts and what its page does not say. Chapter 4 ended with one message to Ambrewick, split across two places. The assistant's spans sit in its memory, and the contacts server writes its spans to a file that the assistant reads only after the server has exited. Neither place can answer a question about the whole message, and both teams need one place to query them that they can change next year.

Every count in this chapter is printed by an example from a recorded run. The few other numbers come from a probe or a cited page, and the text says which. So this chapter builds one receiver for both processes, checks its rows against the exporter's, and puts MLflow on disk beside it.

## The exporter sends each span over OTLP {#otlp-over-http}

Chapter 1 said that an exporter sends each ended span "to memory, a file or an OTLP endpoint", and left the endpoint for this chapter. OTLP is OpenTelemetry's protocol for sending telemetry to a receiver. A backend stores spans and answers queries over them. A collector is a separate process that receives, processes and exports telemetry, and it is taken up in [Changing the backend](#changing-backends). The protocol itself is written down in the [OTLP specification](https://opentelemetry.io/docs/specs/otlp/), which the docs site gives at version 1.11.1, and we cite it for the path, the content types and the status codes.

For traces, the request goes to the path `/v1/traces`, and its body is either Protocol Buffers, sent as `application/x-protobuf`, or JSON, sent as `application/json`. A successful export gets HTTP 200. The specification says a client should [retry](#retries-under-a-timeout) a request that gets 429, 502, 503 or 504, and must not retry any other 4xx or 5xx code. The Python exporter, `OTLPSpanExporter` in `opentelemetry-exporter-otlp-proto-http` at 1.45.2, follows the same four codes in its source, and it also retries connection failures. It makes up to six attempts with backoff, and a `Retry-After` header replaces the backoff. The whole export, retries included, stops at the exporter's timeout. That timeout is 10 seconds by default (`DEFAULT_TIMEOUT`), and at the default a closed port gets four attempts, not six; six needs a longer timeout. When the last attempt fails, the exporter returns the batch as failed, and the batch is dropped and logged, not kept for later.

Here a dev-day message's three spans go through that exporter to a receiver on loopback, which the next section describes: its agent span, its chat span and its `execute_tool find_contact` span, whose counts come from the recording. Two things about a synchronous processor, the kind the examples use, are checked along the way.

Example `otlp-export-loopback` (Python 3.13.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Export one dev-day message's three spans over OTLP/HTTP to the book's receiver on loopback, and check that a span's
request is in the receiver when its span.end() returns. The stored rows equal the in-memory exporter's rows, so the
protobuf round trip loses nothing the book's rows keep; the request count is printed and the yes lines are asserted."""
from lib.assistant import AGENT, RELEASES
from lib.clock import VirtualClock
from lib.export import spans_to_rows
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.otlp import message_spans, start
from lib.tracing import make_provider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-07", RELEASES["r0"]
receiver = start()                       # the book's receiver on loopback; the port is never printed
memory = InMemorySpanExporter()          # the same spans, kept in memory, to compare with what arrives
clock = VirtualClock(DAY)
provider = make_provider(AGENT, RELEASE.service_version, "otlp-export-loopback", clock, SequentialIds(), memory, SCHEMA_URL)
# SimpleSpanProcessor calls the exporter when each span ends, so the request is sent on the ending thread (O-7)
provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=receiver.endpoint)))
root, chat, tool = message_spans(provider.get_tracer("ambrewick.assistant"), clock)

assert receiver.address == "127.0.0.1"   # bound to loopback only, never to a network address
assert len(receiver.requests()) == 3     # one request per span the processor exported
assert sum(count == 1 for _, count in receiver.requests()) == 3  # each request holds one span
assert receiver.rows() == spans_to_rows(memory)  # the stored rows equal the exporter's own rows

# A span from a provider with only the OTLP exporter: its request must be in the receiver when end() returns.
probe = TracerProvider(resource=Resource.create({"service.name": AGENT, "service.instance.id": "probe"}))
probe.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=receiver.endpoint)))
before = len(receiver.requests())
# 36001 s is an offset on the virtual clock, past the message's spans, so the probe's times do not overlap them
probe.get_tracer("probe").start_span("probe", start_time=clock.at(36001)).end(end_time=clock.at("36001.1"))
assert len(receiver.requests()) == before + 1

print("bound to loopback: yes (asserted)")
print("requests for the message's three spans:", before)
print("spans per request: one in each, for every request (asserted)")
print("content types of the requests:", ", ".join(sorted({kind for kind, _ in receiver.requests()})))
print("stored rows equal the exporter's rows: yes (asserted)")
print("a request is in the receiver when span.end() returns: yes (asserted)")
receiver.stop()
```

Output:

```text
bound to loopback: yes (asserted)
requests for the message's three spans: 3
spans per request: one in each, for every request (asserted)
content types of the requests: application/x-protobuf
stored rows equal the exporter's rows: yes (asserted)
a request is in the receiver when span.end() returns: yes (asserted)
```

The receiver logged 3 requests for the message's three spans, and each request's body was application/x-protobuf. Each of the three spans reached the receiver in a request of its own, and each request was there before its `span.end()` returned, because `SimpleSpanProcessor` calls the exporter on the thread that ends the span. Chapter 1 chose that processor so that every printed span has been exported by the time it is printed. The example asserts these lines, so it stops if one of them is false. The rows the receiver stored equal the rows the exporter built in memory, so the protobuf round trip loses nothing the book's rows keep. The compared rows leave out the status description, links, trace state, flags, scope version, schema URL and the `telemetry.sdk.*` resource values.

The synchronous processor has a [cost](#cost-per-route), and a probe shows it. A probe pointed the exporter at a closed loopback port, at its default 10-second timeout; `span.end()` returned after about 7 seconds, after four attempts, and no exception reached the application.

**Working rule:** Give each process the endpoint of its receiver, and send production spans with the batch processor that chapter 1 recommends, so the request is not made on the thread that ends the span. In production we recommend that processor, because its export runs on its own schedule and not on the thread that ends a span. The trade is the one chapter 1 named: spans still in its queue are lost if the process dies.

## The book's receiver holds both processes' spans {#the-book-receiver}

The receiver is the book's own: an HTTP server from the standard library that decodes requests with OpenTelemetry's protobuf classes, started on loopback by `start()` in the book's `lib/otlp.py`. It decodes a request in either encoding, Protocol Buffers or JSON, and stores each span as a row in the shape the book's export writes to JSON lines. It stores the request before it replies, which is what [the last section's assertion](#otlp-over-http) relied on. It keeps the rows in memory, for one run. That makes it a test receiver for this book, not a store a team would keep for a year. The next section's backend keeps its rows on disk.

Both processes export to it. The assistant's exporter runs in the assistant's own process. The contacts server gets the endpoint from its environment: when `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` or `OTEL_EXPORTER_OTLP_ENDPOINT` names one, the server exports its spans over OTLP itself. When neither is set, it writes the JSON-lines file that [The contacts server is another process](#the-contacts-server) describes. The receiver takes a port that the system chooses, and the examples never print it; the contacts server is still a stdio subprocess and only sends to that port.

Example `two-processes-one-receiver` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Replay baseline day 1's messages that route to the messages tools, with the contacts server live, and send both
processes' spans to one receiver: every server span joins a trace the assistant made. The server's clock is its own,
so the example prints counts only, never a span time from it."""
from lib.assistant import AGENT
from lib.case import load_messages, scenario_to_route
from lib.contacts_server import SERVICE_NAME
from lib.dayrun import run_day_traced
from lib.otlp import start

DAY = "2026-12-08"
receiver = start()                   # the book's receiver on loopback; its port is never printed
ids = {m.message_id for m in load_messages(DAY) if scenario_to_route(m.scenario) == "messages"}  # only these can call a contacts tool
traced = run_day_traced(DAY, message_ids=ids, otlp_endpoint=receiver.endpoint)  # both processes export here
stored = receiver.rows()
mine = [row for row in stored if row["resource"]["service.name"] == AGENT]
theirs = [row for row in stored if row["resource"]["service.name"] == SERVICE_NAME]
mine_ids = {row["span_id"] for row in mine}
find = {row["trace_id"] for row in mine if row["name"] == "execute_tool find_contact"}  # those messages' traces
both = {row["trace_id"] for row in mine} & {row["trace_id"] for row in theirs}

assert mine == traced.spans                    # the stored assistant rows equal export.py's rows
assert find <= {row["trace_id"] for row in theirs}  # each find_contact message has server spans in its trace
assert find <= {row["trace_id"] for row in mine if row["name"].startswith("invoke_agent")}  # and a message root
# every server span whose parent is set names a stored span, from either process: the join crosses no gap
assert all(row["parent_span_id"] in mine_ids | {r["span_id"] for r in theirs} for row in theirs if row["parent_span_id"])

rooted = {row["trace_id"] for row in mine if row["name"].startswith("invoke_agent")}
print("messages replayed:", len(traced.runs))
print("messages that called find_contact:", len(find))
print("assistant traces with a message root:", len(rooted))
print("assistant traces without one (the startup, with its discovery call):", len({row["trace_id"] for row in mine} - rooted))
print("traces with spans from both processes:", len(both))
print("spans from the assistant, in the find_contact messages:", sum(row["trace_id"] in find for row in mine))
print("spans from the contacts server, in the find_contact messages:", sum(row["trace_id"] in find for row in theirs))
print("spans from the assistant, all messages:", len(mine))
print("spans from the contacts server, all messages:", len(theirs))
print("contacts server spans under an assistant span:", sum(row["parent_span_id"] in mine_ids for row in theirs))
print("stored assistant rows equal the exporter's rows: yes (asserted)")
receiver.stop()
```

Output:

```text
messages replayed: 17
messages that called find_contact: 3
assistant traces with a message root: 17
assistant traces without one (the startup, with its discovery call): 1
traces with spans from both processes: 4
spans from the assistant, in the find_contact messages: 22
spans from the contacts server, in the find_contact messages: 7
spans from the assistant, all messages: 70
spans from the contacts server, all messages: 8
contacts server spans under an assistant span: 5
stored assistant rows equal the exporter's rows: yes (asserted)
```

The replay runs the messages from [baseline day 1](#the-contacts-server) that take the `messages` route, which goes to the messages tools: 17 in all, and 3 of them call `find_contact`. The receiver stores the spans of both processes, and the output counts each side. The server's spans sit in the trace of each message that asked for a contact. Of all the traces, 4 hold spans from both processes: the three lookups and the startup.

One trace in the replay answers no message, and that is by design: the contacts server starts once, inside a `contacts startup` span, so its discovery call is a trace of its own. It is the one root expected besides the message roots. A server started outside any span would make its `server/discover` call a [detached root](#lost-context) of its own, and one started per message would make one for every message. This replay follows [chapter 4's one process per run](#the-contacts-server), where a run is the server's whole life, here one replay. The output shows it: 1 assistant trace has no message root, and it is the startup. Every message has its own root, 17 in all, and each lookup joins its message's trace.

The rows the receiver stored equal the rows that `lib/export.py` writes for the same spans. That is the claim the rest of the book depends on. From here on, the book's queries read rows of this shape, and chapter 8 runs its failure queries on the receiver itself, so this check shows that those rows are what a backend would hold, not a copy the book made for its own queries.

The rows checked above are what the queries read, and the example writes them to a JSON Lines file first. `connect()` in `lib/query.py` opens an in-memory DuckDB connection, at 2.0.0, with one view named `spans` over that file.

Example `query-stored-spans` (Python 3.13.16 · bm25s 0.3.16 · duckdb 2.0.0 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Query the receiver's stored rows with DuckDB: the spans each process stored, the join across the process boundary,
and the orphans (spans whose parent names no stored span). Every query orders by its group keys, so the printed order
is the same on every run; the server's own times are never printed."""
import tempfile
from pathlib import Path

from lib.case import load_messages, scenario_to_route
from lib.contacts_server import SERVICE_NAME
from lib.dayrun import run_day_traced
from lib.export import write_jsonl
from lib.otlp import start
from lib.query import connect

DAY = "2026-12-08"
receiver = start()                   # the book's receiver on loopback, as in the example before
ids = {m.message_id for m in load_messages(DAY) if scenario_to_route(m.scenario) == "messages"}
run_day_traced(DAY, message_ids=ids, otlp_endpoint=receiver.endpoint)  # both processes export to the receiver
with tempfile.TemporaryDirectory() as folder:
    rows_file = Path(folder) / "spans.jsonl"          # the stored rows, as a file a query can read
    write_jsonl(rows_file, receiver.rows())
    db = connect(rows_file)
    assert db.execute("SELECT count(*) FROM spans").fetchone()[0] == len(receiver.rows())
    per_service = db.execute("SELECT service, count(*), count(DISTINCT trace_id) FROM spans GROUP BY service "
                             "ORDER BY service").fetchall()
    server_names = db.execute("SELECT name, count(*) FROM spans WHERE service = ? GROUP BY name ORDER BY name",
                              [SERVICE_NAME]).fetchall()
    # a server span whose parent is an assistant span: the join across the process boundary
    joins = db.execute("SELECT c.name, count(*) FROM spans c JOIN spans p ON c.parent_span_id = p.span_id "
                       "WHERE c.service <> p.service GROUP BY c.name ORDER BY c.name").fetchall()
    both = db.execute("SELECT count(*) FROM (SELECT trace_id FROM spans GROUP BY trace_id "
                      "HAVING count(DISTINCT service) = 2 ORDER BY trace_id)").fetchone()[0]
    orphans = db.execute("SELECT count(*) FROM spans c WHERE c.parent_span_id IS NOT NULL AND NOT EXISTS "
                         "(SELECT 1 FROM spans p WHERE p.span_id = c.parent_span_id) ORDER BY 1").fetchone()[0]

for service, count, traces in per_service:
    print(f"stored spans from {service}: {count}, in {traces} traces")
for name, count in server_names:
    print(f"contacts server spans named {name}: {count}")
for name, count in joins:
    print(f"contacts server spans under an assistant span, named {name}: {count}")
print("traces holding both processes' spans:", both)
print("orphans in the stored rows:", orphans)
```

Output:

```text
stored spans from ambrewick-assistant: 70, in 18 traces
stored spans from contacts-server: 8, in 4 traces
contacts server spans named contacts.lookup: 3
contacts server spans named server/discover: 1
contacts server spans named tools/call find_contact: 3
contacts server spans named tools/list: 1
contacts server spans under an assistant span, named server/discover: 1
contacts server spans under an assistant span, named tools/call find_contact: 3
contacts server spans under an assistant span, named tools/list: 1
traces holding both processes' spans: 4
orphans in the stored rows: 0
```

The first two lines count the stored spans by process, the assistant's and the contacts server's. The join is the query that matters. A contacts server span whose parent is an assistant span crossed the process boundary and joined. Three names do that: `tools/call find_contact`, with 3 spans; `server/discover`, the startup's discovery, with 1; and `tools/list`, the tool listing, with 1. The lookup's own span, `contacts.lookup`, is not in that list, because its parent is the server's `tools/call` span. The join is one hop, at the server's entry point.

The last two lines are the checks that the halves joined. 4 traces hold spans from both processes, and 0 orphans are stored. The term is defined in [Context is lost at a thread boundary](#lost-context), and a zero there means every stored parent link resolves. A `GROUP BY` or a join has no defined order in DuckDB, whatever the setting, and DuckDB's [order-preservation page](https://duckdb.org/docs/2.0/sql/dialect/order_preservation) at version 2.0 lists both. So every query in the example orders its rows. A probe at this version, with the setting off, saw a query with no `ORDER BY` return its rows in a different order on another run.

**Working rule:** Send every process's spans to one receiver, and check the join, the detached roots and the orphan count before you read a query over one process. Leave the `contacts startup` span out of the detached-root count by its name. If no server span sits under an assistant span, or any orphan is stored, the halves did not join or a span was lost, and the other queries cannot yet be trusted. For a team, we recommend one receiver for every process, because a trace split over two stores cannot be read whole; the trade is one more place to run and keep.

## MLflow on SQLite takes the same spans {#mlflow-on-sqlite}

The receiver keeps rows in memory. A team needs a backend that stores them on disk and answers queries over them. MLflow 3.18.0 is one the book can run. Its [OpenTelemetry ingest page](https://mlflow.org/docs/3.18.0/genai/tracing/opentelemetry/ingest/) says that OTLP ingest starts at 3.6.0, takes OTLP over HTTP only, with no gRPC, and needs a SQL-based backend store, which the book provides as SQLite. The route at this version declares the `x-mlflow-experiment-id` header as required, in its source (`mlflow/server/otel_api.py`). A probe found that without the header the route answers 422, a code the exporter does not retry, so the batch is dropped. The book's exporter always sends the header.

The book starts the server on loopback with a SQLite file in a temporary folder. It turns telemetry off through environment variables. It stops the server by its process group, since the server starts worker processes of its own and signalling the parent alone leaves them running.

Example `mlflow-search-traces` (Python 3.13.16 · mcp 2.3.0 · mlflow 3.18.0 · mlflow-skinny 3.18.0 · mlflow-tracing 3.18.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Send one message's three spans to MLflow 3.18.0 on SQLite over OTLP/HTTP, and read them back with search_traces. MLflow
returns span IDs base64-encoded, so the example decodes them before comparing. The code reads the trace's total token
usage from its metadata, and MLflow stores no cost, because it has no price for the model the chat span names."""
import tempfile

from lib.assistant import AGENT, RELEASES
from lib.clock import VirtualClock
from lib.export import spans_to_rows
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.mlflow_server import otlp_exporter, running, stored_spans, trace_usage
from lib.otlp import message_spans
from lib.tracing import make_provider

import mlflow
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-07", RELEASES["r0"]
memory = InMemorySpanExporter()
clock = VirtualClock(DAY)
with tempfile.TemporaryDirectory() as folder, running(folder, "ambrewick-sample") as (uri, experiment):
    provider = make_provider(AGENT, RELEASE.service_version, "mlflow-search-traces", clock, SequentialIds(), memory,
                             SCHEMA_URL)
    provider.add_span_processor(SimpleSpanProcessor(otlp_exporter(uri, experiment)))
    message_spans(provider.get_tracer("ambrewick.assistant"), clock)
    found = mlflow.search_traces(locations=[experiment])

spans, usage = stored_spans(found), trace_usage(found)
root = next(span for span in spans if span["parent"] is None)
chat = next(span for span in spans if span["name"].startswith("chat "))
# the trace ID is "tr-" followed by the 32 hex digits of the OpenTelemetry trace ID, 35 characters in all
assert len(found) == 1 and len(found.iloc[0]["trace_id"]) == 35 and found.iloc[0]["trace_id"].startswith("tr-")
assert {span["span"] for span in spans} == {row["span_id"] for row in spans_to_rows(memory)}  # decoded IDs match
assert all(span["parent"] in (None, root["span"]) for span in spans)  # the chat and tool spans sit under the root
assert chat["attributes"]["mlflow.spanType"] == "CHAT_MODEL"  # MLflow's own label, added on the chat span
assert usage["total"] == usage["input"] + usage["output"]  # cache reads are not added again
# MLflow prices a span only when it knows the span's model, and this book's model is not in its table
assert "mlflow.llm.cost" not in chat["attributes"] and "mlflow.trace.cost" not in found.iloc[0]["trace_metadata"]

print("traces found for the experiment:", len(found))
print("spans in the trace:", len(spans))
print("span IDs, decoded from base64, equal the exporter's IDs: yes (asserted)")
print("chat span, MLflow span type:", chat["attributes"]["mlflow.spanType"])
print("chat span, model MLflow recorded:", chat["attributes"]["mlflow.llm.model"])
print("trace token usage, input:", usage["input"])
print("trace token usage, output:", usage["output"])
print("trace token usage, cache read:", usage["cache_read"])
print("trace token usage, total = input + output: yes (asserted)")
print("cost MLflow stored for this model, on the chat span and in the trace: none (asserted)")
```

Output:

```text
traces found for the experiment: 1
spans in the trace: 3
span IDs, decoded from base64, equal the exporter's IDs: yes (asserted)
chat span, MLflow span type: CHAT_MODEL
chat span, model MLflow recorded: qwen3-4b-instruct-2507
trace token usage, input: 331
trace token usage, output: 38
trace token usage, cache read: 192
trace token usage, total = input + output: yes (asserted)
cost MLflow stored for this model, on the chat span and in the trace: none (asserted)
```

MLflow hands back the same three spans, with their IDs in its own encodings. They are the dev-day message from [the exporter section](#otlp-over-http), and they come back through `search_traces(locations=...)`. MLflow returns 1 trace with 3 spans. Its trace ID is `tr-` followed by the 32 hexadecimal digits of the OpenTelemetry trace ID, and its span IDs come back base64-encoded. They are decoded before the check, which asserts that the decoded IDs equal the exporter's, so each span can be matched to its source. `experiment_ids` is deprecated in favour of `locations`, as `@deprecated_parameter("experiment_ids", "locations")` in `mlflow/tracing/fluent.py` shows, so the code passes `locations`. A probe saw a FutureWarning from the old argument.

MLflow marks the chat span with its own attribute, `mlflow.spanType`, and the marked value is CHAT_MODEL. MLflow keeps the span's `gen_ai.usage.*` attributes, adds its own `mlflow.chat.tokenUsage` on the chat span, and sums usage for the trace in its metadata, `mlflow.trace.tokenUsage`. The code reads the trace's total from that metadata: 331 [input tokens](#three-token-counts), 38 [output tokens](#three-token-counts) and 192 cache-read tokens. The total is checked to be the input plus the output, so the cache reads are not added twice.

MLflow priced nothing. At 3.18.0 it prices a span into `mlflow.llm.cost` and the trace into `mlflow.trace.cost` when its price lookup knows the model. It has no price for qwen3-4b-instruct-2507, the model the chat span names, so it stored no cost on either. Chapter 6 prices tokens with the book's own table, because the model is self-hosted and a price has a date.

Example `same-spans-two-receivers` (Python 3.13.16 · mcp 2.3.0 · mlflow 3.18.0 · mlflow-skinny 3.18.0 · mlflow-tracing 3.18.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Send one message's spans, from one provider, to two receivers: the book's receiver and MLflow. Both hold the same span
IDs and the same attributes, and MLflow adds its own attributes under mlflow.*; the book's receiver adds none."""
import tempfile

from lib.assistant import AGENT, RELEASES
from lib.clock import VirtualClock
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.mlflow_server import otlp_exporter, running, stored_spans
from lib.otlp import message_spans, start
from lib.tracing import make_provider

import mlflow
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-07", RELEASES["r0"]
receiver = start()                   # the book's receiver on loopback
clock = VirtualClock(DAY)
with tempfile.TemporaryDirectory() as folder, running(folder, "ambrewick-two-backends") as (uri, experiment):
    provider = make_provider(AGENT, RELEASE.service_version, "same-spans-two-receivers", clock, SequentialIds(),
                             InMemorySpanExporter(), SCHEMA_URL)
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=receiver.endpoint)))
    provider.add_span_processor(SimpleSpanProcessor(otlp_exporter(uri, experiment)))
    message_spans(provider.get_tracer("ambrewick.assistant"), clock)
    found = mlflow.search_traces(locations=[experiment])

book = {row["span_id"]: row for row in receiver.rows()}
other = {span["span"]: span for span in stored_spans(found)}
receiver.stop()
assert len(book) == len(other) == 3 and set(book) == set(other)  # the same spans in both
added = set()
for span_id, row in book.items():
    kept = {key: value for key, value in other[span_id]["attributes"].items() if not key.startswith("mlflow.")}
    assert kept == row["attributes"]  # every attribute the book stored is still there, unchanged
    assert not any(key.startswith("mlflow.") for key in row["attributes"])  # the book's rows hold no mlflow.* keys
    added |= set(other[span_id]["attributes"]) - set(row["attributes"])

print("spans received by the book's receiver:", len(book))
print("spans received by MLflow:", len(other))
print("the same span IDs in both: yes (asserted)")
print("the book's attributes equal in both, on every span: yes (asserted)")
print("attributes MLflow adds, by name:", ", ".join(sorted(added)))
print("mlflow.* attributes in the book's rows: none (asserted)")
```

Output:

```text
spans received by the book's receiver: 3
spans received by MLflow: 3
the same span IDs in both: yes (asserted)
the book's attributes equal in both, on every span: yes (asserted)
attributes MLflow adds, by name: mlflow.chat.tokenUsage, mlflow.llm.model, mlflow.llm.provider, mlflow.spanType, mlflow.traceRequestId
mlflow.* attributes in the book's rows: none (asserted)
```

One provider can carry two processors, so the same spans can reach the receiver and MLflow in one run. The receiver and MLflow hold the same span IDs, and every attribute the receiver stored is in MLflow's copy unchanged, once MLflow's JSON-text values are decoded. MLflow adds mlflow.chat.tokenUsage, mlflow.llm.model, mlflow.llm.provider, mlflow.spanType, mlflow.traceRequestId, all under `mlflow.`, and the receiver's rows hold none of them.

MLflow's docs at this version name no flag for its GenAI conventions, but the code has `MLFLOW_ENABLE_OTEL_GENAI_SEMCONV`. At 3.18.0 the flag is read only by MLflow's own client-side span processor (`mlflow/tracing/processor/otel.py`), before MLflow's SDK exports the spans it made itself. The server's ingest route never reads it. So the flag governs how MLflow's SDK exports its own spans, not what the server stores from the book's exporter, and the book's path never reaches it.

**Working rule:** Give each backend its own exporter, and check its stored span IDs and attributes against the exporter's before you trust its queries. Set the experiment header on the OTLP exporter, search with `locations`, decode the span IDs, and read the trace's total from its metadata. In production we recommend a backend that keeps its rows on disk and is checked against the exporter, because a query is only as good as the rows it reads. The cost is one more service to run and keep.

## What the other backends say {#what-others-do}

MLflow is one backend these spans reach unchanged. Four others are named here as places the same names might go: Langfuse, Arize Phoenix, Jaeger and Datadog. We ran none of them. Each paragraph gives the date or version of the page we read and what that page says. A page's claim is the vendor's, and this book does not rank the four.

Langfuse's [OpenTelemetry integration page](https://langfuse.com/integrations/native/opentelemetry), which is undated, says that it accepts OTLP at a `/api/public/otel` path, over HTTP with JSON or with protobuf, and that it does not support gRPC. It uses Basic authentication with a key pair. It maps some `gen_ai.*` attributes to its own fields, and it says its own `langfuse.*` attributes take precedence. The mapping names `gen_ai.prompt` and `gen_ai.completion`, which are older names than the `gen_ai.input.messages` that chapter 3's [capture switch](#the-capture-switch) writes. The page says Langfuse aims to be compliant with the GenAI conventions, and gives no version for them.

Arize Phoenix's release note of 2026-05-15 says that Phoenix converts incoming `gen_ai.*` attributes to OpenInference attributes when spans arrive. The statements in this paragraph are from arize-phoenix 15.10.0, per that release note. Conversion fills in only what is missing, so an attribute that is already OpenInference wins, and the note names no flag to turn it off or on. Phoenix's own Python setup sends spans with [OpenInference](#two-other-naming-schemes) conventions. Phoenix takes spans at `POST /v1/traces`, in protobuf only, sent as `application/x-protobuf` with gzip or deflate, so unlike Langfuse it takes no JSON. The route is in [`traces.py`](https://raw.githubusercontent.com/Arize-ai/phoenix/arize-phoenix-v22.0.1/src/phoenix/server/api/routers/v1/traces.py) at tag `arize-phoenix-v22.0.1`. Phoenix's [licence](https://raw.githubusercontent.com/Arize-ai/phoenix/arize-phoenix-v22.0.1/LICENSE) begins "Elastic License 2.0 (ELv2)", and that is one reason the book does not depend on it.

Jaeger's documentation at version 2.23 describes Jaeger as a distribution of the OpenTelemetry Collector framework, on its [architecture page](https://www.jaegertracing.io/docs/2.23/architecture/). Its OTLP receiver, in the same documentation, accepts spans sent over OTLP. The storage options on its pages are Badger, Cassandra, ClickHouse, Elasticsearch, Memory and OpenSearch, and Kafka, which sits in front of storage as a persistent queue rather than as a store. The pages we read say nothing about GenAI spans, so this chapter makes no claim about Jaeger and GenAI.

Datadog's [OpenTelemetry ingestion page](https://docs.datadoghq.com/llm_observability/instrumentation/otel_instrumentation/), which is undated, says that it accepts OTLP traces directly, without a Datadog Agent or its Agent Observability SDK, provided conversion is enabled. Conversion is enabled by the resource attribute `dd_llmobs_enabled=true` or by the export header `DD-LLMObs-Enabled: true`. A trace is eligible only when its spans follow the OpenTelemetry GenAI conventions from version 1.37 onward, or OpenInference, and carry one of a short list of attributes. The page does not say whether the GenAI conventions at v0.1.0, which the book writes, count as 1.37 onward. The page says spans can take three to five minutes to appear.

**Working rule:** When a backend says it reads the OpenTelemetry names, find out which names it maps, at what version, and on what date, before a team relies on the claim. When the page gives no version or date, say so beside the claim.

## Changing the backend {#changing-backends}

Neither the receiver nor MLflow needed anything between the exporter and the store, and the OpenTelemetry Collector is what usually sits there. Its [overview](https://opentelemetry.io/docs/collector/) calls it a "vendor-agnostic way to receive, process and export telemetry data", and its [components page](https://opentelemetry.io/docs/collector/components/) lists five kinds of component: receivers, processors, exporters, connectors and extensions. Both pages were opened 2026-11-23 and are unversioned. The Collector's receivers are one of those five kinds of component. They are not the book's receiver, which is a server of the book's own.

The overview also allows a small setup to go without a Collector, and this book follows that. Here spans go straight to the book's receiver or to MLflow, both of which take OTLP directly, and this chapter does not run a Collector.

Changing a backend is therefore a change to the exporter. The two-receiver run in [MLflow on SQLite](#mlflow-on-sqlite) already sent one provider's spans to two receivers, by adding a second processor and leaving the span code as it was. The attributes in both places match. That is the whole move: the instrumentation and the spans stay the same, and the endpoint and header on the exporter say where they go.

The Collector has two jobs in the rest of the book, and the book names each where it arrives. Chapter 11 decides which whole traces to keep, which needs every span of a trace in one place. The tail-sampling processor's README at contrib `v0.140.0` gives the reason: "All spans for a given trace MUST be received by the same collector instance for effective sampling decisions." This book's receiver is where chapter 11 runs that decision in the examples, and a production Collector is what runs it. Chapter 12 removes personal data from spans before they leave the process. The Collector's overview lists [sensitive data filtering](https://opentelemetry.io/docs/collector/) among what a Collector does, so it is a place the same step can run. Chapter 12 places [redaction](#redaction-as-defence-in-depth) in the process first, so the Collector is a second defence, not a replacement.

**Working rule:** Set the endpoint and headers on the exporter, and leave the span code alone, so that changing a backend is a settings change. Add a Collector when a rule has to see whole traces or change data before it leaves, and not before. A small setup can do without one. We add no Collector until a rule needs whole traces, because a Collector is one more hop to run and keep working, and the book pays that cost only when a rule needs it.

## What goes wrong in production {#send-to-a-backend-in-production}

Chapter 1 named the batch processor as the production choice, and this chapter's exporter shows why. With the simple processor, a slow or closed endpoint holds the request that ends a span, for about 7 seconds at the default timeout, in the probe that [The exporter sends each span over OTLP](#otlp-over-http) describes. With the batch processor, the export runs on the processor's own schedule, so the request does not wait. The batch processor's cost is the one chapter 1 named: spans still in its queue are lost if the process dies. A server that writes its spans through a batch must flush them before it exits, as [The contacts server is another process](#the-contacts-server) explains for the contacts server.

The other failure is quieter, and the application never sees it: the exporter logs a lost batch and moves on. A batch larger than the exporter's default request limit of 64 MiB is also dropped whole and not split, according to the package's source. In production, the exporter's log is therefore where a lost batch shows up, and a team that wants to know about losses has to read it or alert on it.

**Working rule:** In production, keep the batch processor, make sure each server flushes before it exits, and read the exporter's log for dropped batches. Do not rely on the application to report a loss, because the exporter does not raise one to it.

## What this chapter decided {#send-to-a-backend-decisions}

- We send each process's spans to a receiver over OTLP/HTTP, and we run no Collector in the book's path. A Collector is not required at this scale, and chapters 11 and 12 can say where one would sit without running one.
- The book's receiver keeps rows in memory for a run, and MLflow keeps them on disk in SQLite. Both hold the exporter's spans, with the same IDs and attributes, and every later query reads the receiver's rows.
- The printed checks run on the simple processor, which hands every span to the exporter as it ends. Production uses the batch processor.
- The join and the orphan count are printed as numbers, not left to a reader's eye, so a change that breaks the join shows up as a count that moves.
- Each backend has its own exporter, and the rows it stores are checked against the exporter's, as the last bullet says.
- The named backends are described from the pages we read, with their dates or versions, and none is run or ranked.
- The MLflow GenAI flag stays off, because it does not apply to the book's path.
- A backend's claim to read the OpenTelemetry names is checked by comparing its stored rows with the exporter's, not read off its page.
