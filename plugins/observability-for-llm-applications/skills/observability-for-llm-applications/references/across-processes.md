---
title: "Observability for LLM Applications"
chapter: "Follow a request across processes"
chapter_id: across-processes
book: observability-for-llm-applications
edition: 2026.11.2
verified: 2026-11-23
edition_code: W9DX-M10H
canonical: https://rollingedition.com/observability-for-llm-applications/across-processes
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Follow a request across processes,” chapter 4 of Observability for LLM Applications, Edition 2026.11.2, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/across-processes. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Follow a request across processes

By the end of this chapter you can make a span that another team's server writes join the trace of the message that caused it, check that it has joined, and find the spans that have not. The problem starts with one request. Message 16297 on baseline day 1, a recorded day of 200 messages, asks about a contact, so the router sends it to the `messages` route, which calls `find_contact`. That tool runs on the contacts team's MCP server, a separate process that the assistant starts and talks to over stdio, and the server writes its own spans. Until those spans carry the message's trace ID and name the call that asked for them, the trace stops at the tool step, and nothing says which message the lookup served.

The lookup is replayed on the recording machine, a 4-vCPU Intel Xeon at 2.10 GHz, with the virtual clock from [Replay and the virtual clock](#replay-and-the-virtual-clock). So this chapter makes the server's spans join the message's trace, and builds the counts that find the ones that don't.

## The contacts server is another process {#the-contacts-server}

The assistant does not run `find_contact` itself. The contacts team owns the server, and the mcp package at 2.3.0 starts it as a subprocess and sends it requests over standard input and output, the transport the specification calls stdio. Because the server is its own process, its spans never enter the assistant's memory: it writes them to a JSON-lines file of its own, which the assistant reads once the process has exited. The MCP SDK makes a span for each request it sends, and [Trace calls with OpenTelemetry](https://rollingedition.com/model-context-protocol-in-practice/s/trace-with-opentelemetry) covers those spans in depth. The join is what ties the server's spans to the message. A request that loses its header leaves the server's work in the file with no link to the question that caused it.

The other tools in the case do not have this problem. The calendar, alarm and list tools run inside the assistant's own process, so their spans are made in the same memory, and they join the trace by the ordinary parent link that [One message, one trace](#one-message-one-trace) showed.

This chapter calls the contacts server's life a run, not a session. The [2026-07-28 revision of the Model Context Protocol specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/index) says that an open connection, such as a stdio process, is not a conversation or a session, and a server must not treat it as one. The replay starts one process for each run, inside a `contacts startup` span, and every message the run answers reuses it, so a run has one process and one span file, read after the run ends. Nothing carries over from one run to the next, because each run starts its own process. That is the replay's choice, as the MCP specification's statelessness section recommends. In production, a client should not tie the process's life to one task, thread or conversation. Start one process per run and reuse it across messages, as `propagate-into-the-tool` does with its two calls. A server that outlives a run cannot be read at exit, so it needs a flush or a receiver, which [The book's receiver](#the-book-receiver) provides.

The recording shows the failure this section is about. Baseline day 1 was recorded with a client that had no tracer provider, so the client sent no context. The example reads that recording.

Example `server-span-without-context` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.2:

```python
"""Read baseline day 1's recorded contacts-server spans for message 16297. The recorder's client sent no context, so the
server's lookup span has no parent and starts a trace of its own: a detached root. The prose's two counts rest on the
printed lines, and the assert backs the parent count."""
from lib.dayrun import DATA
import json

rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "contacts-spans.jsonl").read_text(encoding="utf-8").splitlines()]
lookups = [r for r in rows if r["name"] == "tools/call find_contact"]
with_parent = [r for r in lookups if r["parent_span_id"] is not None]
lookup = next(r for r in rows if r["name"] == "contacts.lookup")
call = lookups[0]
assert with_parent == [] and lookup["parent_span_id"] == call["span_id"] and lookup["trace_id"] == call["trace_id"]
print("tools/call find_contact spans in the contacts server:", len(lookups))
print("of them with a parent:", len(with_parent))
print("contacts.lookup under it, in its trace: yes")
```

Output:

```text
tools/call find_contact spans in the contacts server: 3
of them with a parent: 0
contacts.lookup under it, in its trace: yes
```

The file holds 3 `tools/call find_contact` spans, and 0 of them have a parent. The lookup's own span still sits under its call in the server's file. But a call with no parent is a detached root (defined in [Context is lost at a thread boundary](#lost-context)), so nothing ties it to the message.

**Working rule:** Give each server process its own tracer provider and exporter, and read its span file only after the process has exited. The server uses `SimpleSpanProcessor`, which hands each span to the exporter when the span ends, so a file read after exit holds every span the server made. A `BatchSpanProcessor` keeps spans in a queue until a flush or a shutdown, so with one, the file is complete only after one of those.

## The MCP SDK writes traceparent into _meta {#traceparent-in-meta}

For a server span to join the trace, the request has to carry the trace's identity, and MCP gives each request a `_meta` object beside its arguments for that. The field that holds the identity is defined by [W3C Trace Context](https://www.w3.org/TR/2021/REC-trace-context-1-20211123/), a Recommendation of 23 November 2021. Its `traceparent` header has four fields joined by hyphens: a version, a trace ID, a parent span ID and flags. The trace ID is 32 hexadecimal digits and the parent ID 16; all-zero values of either are invalid. The flags carry the sampled decision, which chapter 11 uses in [parent-based sampling](#parent-based-sampling).

Context propagation carries the context, the span's identity and any [baggage](#what-goes-in-baggage), to the next process; `traceparent` is the W3C field for the span's part: the trace ID, the parent's span ID and the trace flags, of which the sampled flag is the only one defined. A span's context has more in it, the trace state among other things, but those three are the part a server needs to attach its span under the right parent.

The first thing to try is to write the header yourself, and see what the server does with it. Below, one call carries a header that names a trace this assistant never made, and a second call asks for a tool the server does not have.

Example `propagate-into-the-tool` (Python 3.13.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.2:

```python
"""Write a traceparent into one call to the contacts server, then ask for a tool the server does not have. The prose's claim
that the SDK replaces the header rests on the second printed line, and its claim about the unknown tool on the third."""
from lib.clock import VirtualClock
from lib.contacts_server import SPANS_ENV
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.tracing import make_provider
import asyncio, json, sys, tempfile
from pathlib import Path
from mcp import Client, StdioServerParameters
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

HAND_WRITTEN = "00-" + "ab" * 16 + "-" + "cd" * 8 + "-01"  # a traceparent this app never made
CALLS = [("find_contact", {"user_id": "U0161", "name": "jake"}, {"traceparent": HAND_WRITTEN}), ("no_such_tool", {}, None)]
clock, exporter = VirtualClock("2026-12-08"), InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", "1.0.0", "propagate-example", clock, SequentialIds(), exporter, SCHEMA_URL)
trace.set_tracer_provider(provider)  # the SDK injects its header only when a provider is configured


async def make_calls(params):
    """Make each call inside its own tool span, which is current while the call waits for its reply."""
    replies = []
    async with Client(params) as client:
        for number, (name, arguments, meta) in enumerate(CALLS):
            app = provider.get_tracer("ambrewick.assistant").start_span(f"execute_tool {name}", start_time=clock.at(number))
            with trace.use_span(app, end_on_exit=False):  # ended below, with a virtual end time
                replies.append((app, await client.call_tool(name, arguments, meta=meta)))
            app.end(end_time=clock.at(number + 1))
    return replies


with tempfile.TemporaryDirectory() as folder:
    spans_file = Path(folder) / "spans.jsonl"  # the server's spans; read once the server has exited
    params = StdioServerParameters(command=sys.executable, args=["-m", "lib.contacts_server"],
                                   cwd=str(Path(__file__).resolve().parent), env={SPANS_ENV: str(spans_file)})
    replies = asyncio.run(make_calls(params))
    server = [json.loads(line) for line in spans_file.read_text(encoding="utf-8").splitlines()]

(app, _), (_, unknown) = replies
client = next(s for s in exporter.get_finished_spans()  # the SDK's client span, child of the tool span
              if s.name.startswith("MCP send tools/call") and s.parent and s.parent.span_id == app.context.span_id)
span = next(r for r in server if r["parent_span_id"] == format(client.context.span_id, "016x"))
assert span["trace_id"] == format(app.context.trace_id, "032x") != "ab" * 16  # joined the app's trace, not the header's
assert unknown.is_error and unknown.content[0].text == "Unknown tool: no_such_tool"
print("find_contact, hand-written traceparent: server span joins the app's trace: yes")
print("find_contact, hand-written traceparent kept: no")
print("no_such_tool, reply is an error result: yes")
```

Output:

```text
find_contact, hand-written traceparent: server span joins the app's trace: yes
find_contact, hand-written traceparent kept: no
no_such_tool, reply is an error result: yes
```

With an OpenTelemetry tracer provider configured, the header in `_meta` is replaced before the request leaves the client. The server's span still joins the assistant's trace, and the header the code wrote does not survive, as the second printed line states. The third line shows how this server answers an unknown tool: with an [error](#how-a-span-records-failure) result, `isError` set, which the client hands back as a reply. The specification asks for a different reply, covered in [A timeout is raised, not returned](#errors-across-the-boundary). The yes lines rest on asserts, so the example stops if the server's span joins the header's trace instead.

The specification's 2026-07-28 revision reserves three `_meta` keys for trace context, `traceparent`, `tracestate` and `baggage`, and requires the W3C formats for their values. The proposal behind that reservation, SEP-414, came before the revision. The [GenAI conventions' MCP page](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/mcp.md) says that an instrumentation should inject through the configured propagators, and write the three keys without a prefix. That page links the earlier 2025-11-25 revision, so the two pages name different revisions, and we follow the later one.

**Working rule:** With an OpenTelemetry tracer provider configured, let the MCP SDK write `traceparent`, and never put `traceparent`, `tracestate` or `baggage` into `_meta` by hand. The SDK replaces a hand-written `traceparent`, but a hand-written `tracestate` or `baggage` survives beside the SDK's, so the server reads a value the SDK did not make. Write the header yourself only in code that runs without the SDK, and there the server reads it as written.

## The server span joins the trace {#joining-the-trace}

With the header written by the MCP SDK, as [The MCP SDK writes traceparent into _meta](#traceparent-in-meta) showed, the server's span lands under the right parent. Replaying message 16297 with the live server shows the parent links from the assistant's tool span down to the server's own lookup.

Example `server-span-joins` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.2:

```python
"""Replay baseline day 1's message 16297 with the real contacts server over stdio, and check that the server's span joins
the assistant's trace under the SDK's client span. The prose's counts rest on the two count lines; the server's clock is
its own, so only counts are printed."""
from lib.assistant import RELEASES, Assistant
from lib.bm25 import Retriever
from lib.case import load_articles, load_messages, load_tool_durations
from lib.clock import VirtualClock
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.replay import Replay
from lib.tools import LiveContacts, Tools
from lib.tracing import make_provider
import json, tempfile
from pathlib import Path
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-08", RELEASES["r0"]  # baseline day 1, and the release its recording was made with
exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "baseline-day-1-replay", VirtualClock(DAY),
                         SequentialIds(), exporter, SCHEMA_URL)
trace.set_tracer_provider(provider)  # the SDK makes its client span with the global provider, so it must be this one

message = next(m for m in load_messages(DAY) if m.message_id == "16297")
clock = VirtualClock(DAY, start_ns=message.arrival_ns)  # the message's clock starts at its arrival
with tempfile.TemporaryDirectory() as folder:
    spans_file = Path(folder) / "contacts-spans.jsonl"  # the server writes here; it is read once the server has exited
    contacts = LiveContacts(clock, spans_file)
    outcome = Assistant(Replay(Path(__file__).resolve().parent / "data" / "recorded" / "baseline-day-1"), Retriever(load_articles(), RELEASE.top_k),
                        Tools(load_tool_durations(), contacts), clock, provider.get_tracer("ambrewick.assistant"), RELEASE).handle(message)
    contacts.close()
    server = [json.loads(line) for line in spans_file.read_text(encoding="utf-8").splitlines()]

mine = exporter.get_finished_spans()
app = next(s for s in mine if s.name == "execute_tool find_contact")
client = next(s for s in mine if s.name == "MCP send tools/call find_contact")
call = next(r for r in server if r["name"] == "tools/call find_contact")
lookup = next(r for r in server if r["name"] == "contacts.lookup")
trace_id = format(app.context.trace_id, "032x")
assert client.parent.span_id == app.context.span_id and call["trace_id"] == trace_id  # tool span, client span, same trace
assert call["parent_span_id"] == format(client.context.span_id, "016x")  # the server's span is under the client span
assert lookup["parent_span_id"] == call["span_id"] and lookup["trace_id"] == trace_id  # and its lookup under that

print("route chosen:", outcome.route)
print("spans in the message's trace, assistant:", sum(s.context.trace_id == app.context.trace_id for s in mine))
print("spans in the message's trace, contacts server:", sum(r["trace_id"] == trace_id for r in server))
print("contacts server span under the SDK's client span, in the same trace: yes")
```

Output:

```text
route chosen: messages
spans in the message's trace, assistant: 8
spans in the message's trace, contacts server: 3
contacts server span under the SDK's client span, in the same trace: yes
```

The chain has four spans and three links. The assistant's `execute_tool find_contact` span is the parent of `MCP send tools/call find_contact`, which the SDK makes as a CLIENT span for the request it sends. That client span is the parent of `tools/call find_contact` on the server, a SERVER span, and the server's `contacts.lookup` is the child of that. All four share one trace ID. The assistant holds 8 spans of the message's trace, and the server writes 3 more, in the same trace.

The client span is the one the assistant does not write. Its name, `MCP send tools/call find_contact`, does not follow the pattern the GenAI conventions' MCP page gives for spans, `{mcp.method.name} {target}`. We keep the MCP SDK's name, as chapter 3 keeps the names its package emits, because a span's name should match the code that made it.

The figure draws the same trace as a tree. Dots are the assistant's spans and squares are the server's, and a dashed line marks each parent link that crosses from one process to the other. The layout puts each span by its depth, not its time, because the server's clock is its own, and no time in this chapter comes from a server span: the figure and the output carry structure and parent links only.

Example `figure-cross-process-tree` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.2:

```python
"""Draw baseline day 1's message 16297 as one trace across the assistant and the contacts server, replayed with the live
server. The parent-links line rests on the printed count: two server spans have an SDK client span in the assistant as
their parent. Spans sit by depth, not time, since the server's clock is its own, so the figure shows structure only."""
from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save

traced = run_day_traced("2026-12-08", ["16297"])  # baseline day 1, with the live contacts server
# One row per span of the trace, from both processes. Span IDs link the rows and are never printed.
rows = [dict(r, process="assistant") for r in traced.spans] + [dict(r, process="contacts server") for r in traced.server]
trace_id = next(r["trace_id"] for r in rows if r["name"] == "execute_tool find_contact")
rows = [dict(r, id=r["span_id"], parent=r["parent_span_id"]) for r in rows if r["trace_id"] == trace_id]
by_id = {r["id"]: r for r in rows}
order = []  # depth-first: a span sits just below its parent, and its depth is its indent in the figure


def walk(row, depth):
    row.update(y=len(order), x=depth)
    order.append(row)
    for child in (r for r in rows if r["parent"] == row["id"]):
        walk(child, depth + 1)


for root in (r for r in rows if r["parent"] not in by_id):
    walk(root, 0)

fig, ax = new_figure(height=3.6, sharex=False)
for row in order:
    parent = by_id.get(row["parent"])
    if parent:  # an elbow from the parent's row down, then across; dashed where the link crosses the boundary
        cross = parent["process"] != row["process"]
        ax.plot([parent["x"], parent["x"], row["x"]], [parent["y"], row["y"], row["y"]], linewidth=1.2, zorder=1,
                color=ACCENT if cross else MUTED, linestyle="--" if cross else "-")
    server_row = row["process"] == "contacts server"  # squares for the server, dots for the assistant: shape, not colour alone
    ax.scatter(row["x"], row["y"], s=30, zorder=3, marker="s" if server_row else "o", color=ACCENT if server_row else INK)
    ax.text(row["x"] + 0.14, row["y"], f"{row['name']} ({row['process']})", va="center", fontsize=8, color=INK)
ax.invert_yaxis()
ax.set_xlim(-0.3, 6.4)
ax.axis("off")

cross = [r for r in rows if r["parent"] in by_id and by_id[r["parent"]]["process"] != r["process"]]
print("spans in the message's trace, assistant:", sum(r["process"] == "assistant" for r in rows))
print("spans in the message's trace, contacts server:", sum(r["process"] == "contacts server" for r in rows))
print("parent links across the boundary:", len(cross))
for r in cross:  # the SDK's client span is the parent; the server's span is the child
    print(f"{r['name']} in the contacts server, parent in the assistant:", by_id[r["parent"]]["name"])
assert sorted(r["name"] for r in cross) == ["tools/call find_contact", "tools/list"]  # the two links, and no other
save(fig, "cross-process-tree")
```

Output:

```text
spans in the message's trace, assistant: 8
spans in the message's trace, contacts server: 3
parent links across the boundary: 2
tools/call find_contact in the contacts server, parent in the assistant: MCP send tools/call find_contact
tools/list in the contacts server, parent in the assistant: MCP send tools/list
figure: figures/cross-process-tree.svg
```

*Figure 4.1. The spans of message 16297 as one trace, by depth; dashed links cross between the two processes.*

![One trace drawn as an indented tree: the assistant's spans, as dots, lead down to `execute_tool find_contact`, whose two SDK client spans each have one contacts-server span, as a square, joined by a dashed link; the server's `contacts.lookup` sits under its `tools/call` span](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.2/figures/cross-process-tree.svg)

Figure 4.1 has two dashed links, and the printed count agrees: 2. One is the server's `tools/call find_contact`, whose parent is the client span for the lookup. The other is the server's `tools/list`, whose parent is the client span for the request the SDK sends for the server's tool list. The MCP SDK lists a server's tools after the first successful reply from a tool it has not listed yet, so that it can check the reply against the tool's output schema (`src/mcp/client/session.py`, `call_tool` and `validate_tool_result`, at mcp 2.3.0). This message's lookup succeeded, which is why it has that second link.

**Working rule:** After any call that crosses a process, check that each server span names a client span from the caller's trace as its parent, and count the links that cross. A link count of zero on a call you expected to cross means the header did not reach the server, so look at the request before you look at the server.

## Context is lost at a thread boundary {#lost-context}

The join works because the SDK's call runs in the same context as the tool span that made it. Python keeps the current span in a `ContextVar`, and each thread and each asyncio task has its own value of it. Three common ways of moving work lose that value: `threading.Thread(target=...)`, `executor.submit` and `loop.run_in_executor` each start the function with an empty context, so a span made there finds no parent. `asyncio.to_thread` and `asyncio.run_coroutine_threadsafe` copy the context, and that is why the book's `LiveContacts`, which sends each call to the client's thread with `run_coroutine_threadsafe`, keeps `find_contact`'s span in the message's trace.

A span that starts a trace of its own this way is a detached root: a span whose context was lost, so it starts a new trace and sits outside the message's trace. An orphan is a different failure. An orphan is a span whose parent ID names a span the store does not hold. It keeps the message's trace ID and stays in the message's trace. The two look different in the store. An orphan shows as a gap, a parent with no span behind it. A detached root looks like a healthy one-span trace, so nothing marks what it lost. [Spans by hand](#spans-by-hand) shows the other way a parent goes missing, when a process crashes partway through a message.

The example makes one span on each of four workers, all started inside one tool span, and shows which of them find its context.

Example `orphan-span-demo` (Python 3.13.16 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0), passing in Edition 2026.11.2:

```python
"""Make one span on each of four workers started inside one tool span, and show which ones find its context: a plain pool
thread, the same thread with carry(), an asyncio task, and the loop's executor. The prose's counts of detached roots rest
on the asserts, which compare each span's parent with the tool span."""
from lib.clock import VirtualClock
from lib.context import carry, new_task
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.tracing import make_provider, span
from opentelemetry import trace
import asyncio
from concurrent.futures import ThreadPoolExecutor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

clock, exporter = VirtualClock("2026-12-08"), InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", "1.0.0", "orphan-example", clock, SequentialIds(), exporter, SCHEMA_URL)
tracer = provider.get_tracer("ambrewick.assistant")


def retrieve(name):
    """The worker's work: one span, made on whichever thread runs this. Its times are fixed, as every span's are."""
    span(tracer, f"retrieve {name}", clock.at(1), clock.at(2))  # no parent given: the span takes the current one


async def from_task():
    retrieve("task")  # runs in its own task, which asyncio gave a copy of the tool span's context


async def main():
    """Runs as a task inside the tool span, starts a second task, and hands one worker to the loop's executor."""
    await new_task(from_task())
    await asyncio.get_running_loop().run_in_executor(None, retrieve, "executor")  # copies no context


app = tracer.start_span("execute_tool retrieve", start_time=clock.at(0))
with trace.use_span(app, end_on_exit=False):  # current while the workers run, so their spans can find it
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(retrieve, "plain").result()  # the pool's thread starts with an empty context
        pool.submit(carry(retrieve), "carried").result()  # carry() runs the work in a copy of this context
    asyncio.run(main())
app.end(end_time=clock.at(3))

spans = {s.name: s for s in exporter.get_finished_spans()}
joined = {name: spans[name].parent is not None and spans[name].parent.span_id == app.context.span_id for name in spans}
assert joined == {"retrieve plain": False, "retrieve carried": True, "retrieve task": True, "retrieve executor": False,
                  "execute_tool retrieve": False}
assert all(spans[n].context.trace_id != app.context.trace_id for n in ["retrieve plain", "retrieve executor"])  # own traces
print("retrieve on a plain thread, joins the tool span: no")
print("retrieve on a thread with carry(), joins the tool span: yes")
print("retrieve in an asyncio task, joins the tool span: yes")
print("retrieve through run_in_executor, joins the tool span: no")
print("detached roots without the helper:", sum(not joined[n] for n in ["retrieve plain", "retrieve executor"]))
print("detached roots with the helper:", sum(not joined[n] for n in ["retrieve carried"]))
print("detached root's trace differs from the tool span's: yes")
```

Output:

```text
retrieve on a plain thread, joins the tool span: no
retrieve on a thread with carry(), joins the tool span: yes
retrieve in an asyncio task, joins the tool span: yes
retrieve through run_in_executor, joins the tool span: no
detached roots without the helper: 2
detached roots with the helper: 0
detached root's trace differs from the tool span's: yes
```

The plain thread's span is a detached root, and the first printed line says it did not join the tool span. The wrapped thread's span joins, and so does the task's, because asyncio gives a task a copy of the context that was current when the task was made. The executor worker loses the context like the plain thread, so its span is a detached root too. The counts make the [cost](#cost-per-route) plain: 2 detached roots without the helper, and 0 with it. The last line states that a detached root's trace differs from the tool span's, which is the test for one: a trace ID other than the one its work belongs to.

The fix is `carry()`, from the book's shared module `lib/context.py`, which wraps a function so it runs in a copy of the caller's context. `new_task()` starts an asyncio task with an explicit copy of the context. asyncio copies it anyway, and the helper makes the copy visible in code. Two standard alternatives exist. `opentelemetry-instrumentation-threading` patches `Thread` and `ThreadPoolExecutor` so they carry the context, and `asyncio.to_thread` copies it for the work it starts. We recommend `carry()` in code the team owns, because the copy is visible at the call site and nothing is patched. The instrumentation is for libraries whose own thread pools the team cannot change.

**Working rule:** Wrap every function that a thread, a thread pool or `run_in_executor` runs in `carry()`, and start asyncio tasks with `new_task()`, so each one starts from a copy of the caller's context. A span that finds no parent raises no error and changes no status, so the context has to be carried at every hand-off.

## What goes in baggage {#what-goes-in-baggage}

A trace ID and a parent ID say where a span belongs, and a server often needs one more value to label its own spans: which release and which [prompt version](#release-markers-in-the-spans) made the call. Baggage is the mechanism for that. The standard for it is the [W3C Baggage specification](https://www.w3.org/TR/2024/CR-baggage-20240530/), a Candidate Recommendation Snapshot of 30 May 2024. It is not yet a Recommendation, and we cite it at that status.

Baggage is a set of key-value pairs that travels with the context into every later process when every process along the way propagates it. The specification warns that baggage may carry sensitive information, advises that no proprietary or confidential information goes in it, and says that its keys and values can be passed on to other systems. Those warnings decide what we put there. Only the release and the prompt version go in, under the keys `ambrewick.release` and `ambrewick.prompt.version`. A release has the form `MAJOR.MINOR.PATCH` in digits, and a prompt version is `p` followed by digits. Running the example below shows the allowed list, the keys a call carries, and the refusals.

Example `baggage-keys` (Python 3.13.16 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0), passing in Edition 2026.11.2:

```python
"""Put the release and the prompt version in baggage, and carry them as an MCP call would: the global propagator writes the
`baggage` entry that the SDK sends in `_meta`. A user identifier is refused under an unknown key and under an allowed one.
The prose rests on the last two printed lines, which the asserts back."""
from lib.context import ALLOWED_BAGGAGE_KEYS, baggage_context
from opentelemetry import baggage, propagate


def refused(values):
    """True when baggage_context refuses these values."""
    try:
        baggage_context(values)
    except ValueError:
        return True
    return False


ctx = baggage_context({"ambrewick.release": "1.0.0", "ambrewick.prompt.version": "p1"})
carrier = {}
propagate.inject(carrier, context=ctx)  # the same global propagator the SDK uses for `_meta`
carried = sorted(baggage.get_all(ctx))
assert carried == sorted(ALLOWED_BAGGAGE_KEYS)  # nothing else is carried
assert carrier["baggage"] == "ambrewick.prompt.version=p1,ambrewick.release=1.0.0"
assert refused({"ambrewick.user.id": "U0161"})  # a key that is not allowed
assert refused({"ambrewick.release": "U0161"})  # a user identifier under an allowed key, which is not in its form

print("allowed baggage keys:", ", ".join(sorted(ALLOWED_BAGGAGE_KEYS)))
print("baggage keys carried on a call:", ", ".join(carried))
print("baggage entry sent in _meta:", carrier["baggage"])
print("user identifier refused: yes")
print("user identifier under an allowed key refused: yes")
```

Output:

```text
allowed baggage keys: ambrewick.prompt.version, ambrewick.release
baggage keys carried on a call: ambrewick.prompt.version, ambrewick.release
baggage entry sent in _meta: ambrewick.prompt.version=p1,ambrewick.release=1.0.0
user identifier refused: yes
user identifier under an allowed key refused: yes
```

Only the two allowed keys leave the process: the propagator writes them into one `baggage` entry, and the SDK sends that entry in `_meta` beside `traceparent`. The helper refuses a key outside the allowed list, and a value outside its key's form, so a user identifier is refused even under an allowed key. The last two lines report those refusals.

`baggage_context` does not see two cases. It starts from the current context, so baggage that arrived from upstream passes through it unchecked, and a direct call to `opentelemetry.baggage.set_baggage` skips it altogether. We recommend that code calls `baggage_context` and never `set_baggage` directly.

A user identifier does not go into baggage, and we do not put one there in any form. The keyed pseudonym we use for users is in [Keyed user pseudonyms](#keyed-user-pseudonyms), where chapter 12 explains why it is safe to put in a span.

**Working rule:** Put a value in baggage only when a process downstream needs it to label its own spans, and only under a key on the allowed list. A value that identifies a person stays out, however short or harmless it looks in one message.

## A timeout is raised, not returned {#errors-across-the-boundary}

The lookup can fail in more than one way, and the failures arrive differently at the caller. A tool that the server does not have comes back as an error result from this server. A conforming server built by another team fails differently: the [specification's tools page](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) makes an unknown tool a protocol error, a JSON-RPC error with code -32602, which the client raises as `MCPError`. A read timeout does not come back from any server at all. The SDK raises it as an `MCPError`, with the code -32001.

The specification assigns no code to errors that are purely local to an implementation, such as a request timeout raised inside an SDK. So -32001 is not an MCP code. The client made it itself, and no server sent it. The specification puts -32001 in its legacy range, -32000 to -32019, where new implementations should not use codes and receivers must not assume a meaning, and it asks that a local error never be mistaken for a peer's. mcp raises the timeout as the same `MCPError` class it uses for a server's errors, so a query over `ambrewick.mcp.error_code` must not count -32001 as the server's error. We call -32001 the SDK's code for a read timeout, and [chapter 8](#retries-under-a-timeout) reads these timeouts across the incident day under the same name.

This section uses an injected incident, `inc-contacts-timeout`, which makes the contacts server answer too slowly for a window of the incident day. The injection is labelled as one in the spans it touches, and the example's first printed line names it.

Example `contacts-timeout-live` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.2:

```python
"""Replay incident-day message 16297 with the live contacts server, inside the injected timeout window. Each attempt of
find_contact is its own execute_tool span. The first raises MCPError with code -32001, the SDK's code for a read timeout,
which the MCP spec does not assign: that span ends ERROR, with error.type MCPError and an exception event. The retry starts
2.5 s later, times out too, and the tool step gives up."""
from lib.dayrun import run_day_traced
from lib.tools import TIMEOUT_CODE

traced = run_day_traced("2026-12-09", ["16297"])  # the incident day, with the live server inside its window
outcome = traced.runs[0].outcome
attempts = sorted((r for r in traced.spans if r["name"] == "execute_tool find_contact"),
                  key=lambda r: r["attributes"]["ambrewick.attempt"])
injected = [r for r in traced.server if r["name"] == "tools/call find_contact" and "ambrewick.incident.id" in r["attributes"]]
first, second = attempts
assert len(attempts) == 2 and outcome.source == "model"  # the retry times out too, and the answer comes from the model
assert all(a["status"] == "ERROR" and a["attributes"]["error.type"] == "MCPError" for a in attempts)
assert first["attributes"]["ambrewick.mcp.error_code"] == TIMEOUT_CODE
assert len(injected) == 2 and all(r["attributes"]["ambrewick.incident.injected"] is True for r in injected)
print("injected incident, ID:", injected[0]["attributes"]["ambrewick.incident.id"])
print("attempts of find_contact:", len(attempts))
print("attempt 1, status and error.type:", first["status"], first["attributes"]["error.type"])
print("attempt 1, error code:", first["attributes"]["ambrewick.mcp.error_code"])
print("attempt 1, exception event:", first["events"][0]["attributes"]["exception.type"].rsplit(".", 1)[-1])
print("attempt 1, time:", f"{(first['end_ns'] - first['start_ns']) / 1e9:.1f} s")  # the 2.0 s timeout
print("attempt 2 starts after attempt 1:", f"{(second['start_ns'] - first['start_ns']) / 1e9:.1f} s")  # 2.0 s + 0.5 s
print("tool step, time:", f"{(second['end_ns'] - first['start_ns']) / 1e9:.1f} s")
```

Output:

```text
injected incident, ID: inc-contacts-timeout
attempts of find_contact: 2
attempt 1, status and error.type: ERROR MCPError
attempt 1, error code: -32001
attempt 1, exception event: MCPError
attempt 1, time: 2.0 s
attempt 2 starts after attempt 1: 2.5 s
tool step, time: 4.5 s
```

Message 16297 on the incident day runs with the live server inside the injected window. The first attempt times out, and the printed lines show its status, its [error type](#how-a-span-records-failure) and its code, which is -32001. The attempt takes 2.0 s on the virtual clock, which is the timeout the client is configured with. The second attempt starts 2.5 s after the first, also times out, and the tool step gives up after 4.5 s in all.

Each attempt is its own `execute_tool` span, and we count each one as its own operation. A failed attempt is therefore ERROR, with `error.type` set to the class the caller received, `MCPError`, not the inner `TimeoutError` that the SDK caught underneath it. The code goes on `ambrewick.mcp.error_code`, not on `rpc.status_code`: the conventions define that attribute as the error code from the JSON-RPC response, and a local timeout has no response. The retry does not turn the first attempt into a success. The conventions' [recording-errors page](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.45.0/docs/general/recording-errors.md) says that retried errors stay off the span, but that rule covers an operation that succeeds on retry, and here each attempt is one operation that failed. The alternative reading would hide the first attempt's timeout, and chapter 8 needs that timeout to count the failures a message met.

**Working rule:** Record each attempt of a call as its own span, with its own status and error type, and never let one error span stand for a call whose earlier attempts also failed. Read the error type from the exception the caller receives, and read the code from the error the client raises.

## What goes wrong in production {#across-processes-in-production}

The failures in this chapter raise no error. A hand-written header that the SDK replaces passes silently, and a server span with no parent is exported like any other span. Three queries find them, and each needs a place where the spans of both processes sit together, which chapter 5 provides. One counts the cross-process links: the parent links that cross from one process to the other. One counts detached roots: root spans other than the agent span `invoke_agent ambrewick-assistant`, in either process, and a server span that arrived with no `traceparent` is one too. The last counts orphans: spans whose parent ID names no stored span. Without the queries, nothing in the process fails, so the counts are the only signal.

Two more things go wrong in production. Libraries that run work on their own thread pools lose the context unless they were written to copy it, and a team's `carry()` cannot reach a pool it does not own, so a span that looks like it belongs to a message can start a trace of its own. Baggage goes wherever the request goes, to every process the call reaches, so a value that was harmless in one process can become a leak in the next. The helper checks only what the book sends. Baggage that arrives from upstream passes through unchecked, which is the limit [What goes in baggage](#what-goes-in-baggage) describes.

The trace's two halves now sit in two places, the assistant's spans in its memory and the server's in its file, and [The book's receiver](#the-book-receiver) is where chapter 5 puts them together.

**Working rule:** Run the cross-process link count and the detached-root and orphan counts after any change to tool or worker code, and on every release. Treat a change in any of them as a broken join until someone has explained it.

## The decisions this chapter made {#across-processes-decisions}

Each decision below is a judgement we could be wrong about, so each gives its reason and the example that checks it.

- We let the MCP SDK write `traceparent` whenever a tracer provider is configured, and we keep hand-written trace keys out of `_meta`. The header the server reads is the one the SDK writes, so a second copy in the code would never reach the server. `propagate-into-the-tool` checks it, where the hand-written header is replaced.
- We treat each server process as one run and read its span file once the process has exited. A run starts and ends as one unit, and the file holds every span only after the process has finished writing. `server-span-joins` checks the join, and `server-span-without-context` shows the recording where it is missing.
- We carry the context into every thread, pool and asyncio task that makes spans, with `carry()` and `new_task()`. A detached root raises nothing, so the context has to be carried at every hand-off. `orphan-span-demo` checks it, where the plain thread's span and the executor's are the detached roots.
- We put only the release and the prompt version in baggage, and we refuse every other key and every value outside its form. Baggage travels to every process a call reaches, and the specification warns about what it may carry. `baggage-keys` checks it, where a user identifier is refused under an unknown key and under an allowed one.
- We record each attempt of a tool call as its own span, and we name -32001 as the SDK's code, not an MCP code. Chapter 8 counts the failures a message met, and the first attempt's timeout is one of them, so one span for the whole call would hide it. `contacts-timeout-live` shows both attempts as ERROR spans.
