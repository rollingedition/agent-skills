---
title: "Model Context Protocol in Practice"
chapter: "Test a server and watch it run"
chapter_id: test-and-observe
book: model-context-protocol-in-practice
edition: 2026.11.11
verified: 2026-11-14
edition_code: 2VMD-DEEC
canonical: https://rollingedition.com/model-context-protocol-in-practice/test-and-observe
license: CC BY 4.0
attribution: "“Test a server and watch it run,” chapter 11 of Model Context Protocol in Practice, Edition 2026.11.11, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/model-context-protocol-in-practice/test-and-observe. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Test a server and watch it run

By the end of this chapter you can test a Model Context Protocol server's tools in memory and over HTTP, catch a schema change that would break clients before it ships, replay a recorded host run as a regression test, trace tool calls with OpenTelemetry, measure how often a model chooses the right tool, and retire a tool without breaking the clients that use it. Protocol claims here hold for revision 2026-07-28 of the specification, and SDK claims for the Python SDK, `mcp` 2.3.0.

[Build a host that works through tickets](#build-a-host) ended with the host that [the shop](#the-shop)'s support team uses, `lib.ticket_host`, working all 48 of the shop's tickets against two servers, the shop's and the partner's parcel-tracking server, with the model's replies taken from the recording `ticket-runs`. A recording is a saved model output under `examples/data/recorded/`, so the run replays the same way on every machine with no model call.

That run left two problems. The host chose the right first tool for 36 of 48 tickets, and nothing said which ones it got wrong or why. On the refund tickets, the model wrote to customers as if their refunds were done, while 0 of 7 of the tickets asking for a refund ever reached `issue_refund`. The shop's server and host keep changing: a description is reworded, a field is renamed, a tool is replaced. Any of those can break a client without failing a single call on the server's side.

To build checks on, a team gets a few things from the Model Context Protocol (MCP): typed schemas for every tool, trace context in every request's `_meta`, and change notifications for the tool list. This chapter builds the shop's checks on them. Three new modules hold the setup. `lib.testing` runs a pytest module and prints one stable line per test. `lib.contract` compares two releases of a tool's schemas. `lib.queue_replay` replays chapter 10's queue run and checks what each reply promises against the calls the host made. Two of this chapter's examples replay the recording `ticket-runs`, the others use no model, and the chapter makes no model calls of its own.

## Test tools in memory {#in-memory-tests}

A test of a server's tools should run with no port and no subprocess, so that it can run on every change. The Python SDK's `Client` gives you that: passed a server object instead of a URL or launch parameters, it connects to the server in the same process. The SDK's testing guide calls this the way to test a server, with the line "No subprocess. No port. Nothing on a wire" ([testing](https://py.sdk.modelcontextprotocol.io/v2/get-started/testing/index.md)). In the default `mode="auto"`, the connection is a pair of `DirectDispatcher`s, which hand each request to the server's handler as a Python object, with no streams, no JSON-RPC framing and no initialize handshake (`mcp/client/client.py`, `_connect_inproc`; `mcp/shared/direct_dispatcher.py`).

Two details matter in a test. `raise_exceptions=True` makes a failure outside a tool's body, such as a bug in a handler, come back with its real message instead of a sanitised "Internal server error". It doesn't change what a tool's own exception does: that is still a result with `is_error=True`, as it is for any client ([testing](https://py.sdk.modelcontextprotocol.io/v2/get-started/testing/index.md)). The SDK also stamps the server's identity into each result's `_meta`, so a test that compares whole results has to clear `result.meta` first (same page). Asserting on the fields a test is about avoids both the stamp and the SDK guide's snapshot library, `inline-snapshot`, which the book doesn't pin. Async tests need no extra plugin: anyio, which the SDK depends on, ships a pytest plugin that runs any test marked `pytest.mark.anyio` ([AnyIO testing](https://anyio.readthedocs.io/en/stable/testing.html)).

What the in-memory path skips matters as much as what it covers. With no HTTP layer, an in-memory test never meets the checks a Streamable HTTP server makes on headers, `Origin` and `Host`, never sees a server-sent event, and never carries trace context, as [Trace calls with OpenTelemetry](#trace-with-opentelemetry) shows. The SDK's documentation adds that the in-process path doesn't deliver standalone notifications, such as a change to the tool list ([client caching](https://py.sdk.modelcontextprotocol.io/v2/client/caching/index.md)). A suite that is all in memory can pass while every HTTP client fails.

The shop's tests run against chapter 3's server, `lib.shop_tools`, from [Design tools a model can use](#design-tools), with the shop's API on loopback for each test, served by the fixture `shop_api_env` from `lib.testing`. Three tests run in memory: an order's status comes back as structured fields, an unknown order comes back as a [tool execution error](#tool-errors) that names `find_orders`, and an order ID in the wrong form is refused before the tool runs. The fourth serves the same tools over Streamable HTTP on loopback and sends a `tools/call` whose `Mcp-Name` header names a different tool from its body: a request the SDK's client never sends, and one an in-memory client can't express. Run as a script, the file runs its own tests with pytest 9.2.0.

Example `test-tools-in-memory` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pytest 9.2.0 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Four pytest tests of the shop's tools: three through the SDK's in-process client, and one over Streamable HTTP on
loopback, which reaches a check an in-memory test never makes. The prose's point rests on the unknown-order test's
line and on the last line, which counts the passes."""
import pytest
from mcp import Client

from lib import http_mcp, loopback, shop_tools
from lib.testing import anyio_backend, run, shop_api_env

pytestmark = pytest.mark.anyio                            # runs the async tests on anyio's pytest plugin


async def test_order_status_fields(shop_api_env):        # shop_api_env serves the shop's API on loopback for this test
    # raise_exceptions=True: a bug outside a tool's body raises here, with its own message
    async with Client(shop_tools.create_server(), raise_exceptions=True) as client:
        result = await client.call_tool("get_order_status", {"order_id": "O-1873"})
    assert not result.is_error
    assert result.structured_content["order_id"] == "O-1873"
    assert result.structured_content["status"] == "delivered"


async def test_unknown_order_is_a_tool_error(shop_api_env):
    async with Client(shop_tools.create_server(), raise_exceptions=True) as client:
        result = await client.call_tool("quote_refund", {"order_id": "O-7144"})
    assert result.is_error                                    # raise_exceptions doesn't make it raise
    assert "find_orders" in result.content[0].text            # the model is told what to do instead


async def test_malformed_order_id_is_refused(shop_api_env):
    async with Client(shop_tools.create_server(), raise_exceptions=True) as client:
        result = await client.call_tool("get_order_status", {"order_id": "1873"})
    assert result.is_error
    text = result.content[0].text                             # only argument validation writes this error:
    assert "order_id" in text and "string_pattern_mismatch" in text   # the field and pydantic's pattern check


def test_http_refuses_a_mismatched_header(shop_api_env):
    with loopback.serve(shop_tools.create_server().streamable_http_app()) as base_url:
        # the header names check_stock while the body calls get_order_status: the mismatch the server must refuse
        reply = http_mcp.post(base_url + "/mcp", "tools/call", {"name": "get_order_status",
                              "arguments": {"order_id": "O-1873"}}, headers={"Mcp-Name": "check_stock"})
    assert reply.status_code == 400
    assert reply.json()["error"]["code"] == -32020        # the JSON-RPC code the server returns for the mismatch


if __name__ == "__main__":
    run(__file__)
```

Output:

```text
test_order_status_fields: passed
test_unknown_order_is_a_tool_error: passed
test_malformed_order_id_is_refused: passed
test_http_refuses_a_mismatched_header: passed
tests passed: 4 of 4
```

A failing tool is a result a model can act on. The run reports 4 of 4, and the unknown order's test passed with `raise_exceptions=True` on: the tool raised `ToolError`, and the client got an ordinary result with the error flag set and the server's advice in its text, which is what a model needs to correct itself ([Report failures as tool results](#tool-errors)).

The malformed ID never reached the tool. The test asserts that the error names `order_id` and pydantic's `string_pattern_mismatch`, which only argument validation writes. The SDK validated the arguments against the tool's parameter model, which its input schema is generated from, before calling the tool (`mcp/server/mcpserver/server.py`, `_handle_call_tool`). The HTTP test covers the layer the others skip: the server refused the mismatched header with status 400 and the JSON-RPC error -32020, as [Read one HTTP exchange](#http-on-the-wire) describes, before any tool code ran.

**Working rule:** Test each tool in memory with `Client(server, raise_exceptions=True)`, and assert on `structured_content` fields and `is_error`, not on whole results. Keep at least one test per transport you ship that goes over it on loopback, for the header, origin and streaming checks an in-memory test can't reach, and put the tests of trace propagation and list changes there too.

## Check schemas as a contract {#schema-contract-tests}

The in-memory tests from [the previous section](#in-memory-tests) check that a tool does what its own release says. They don't check that the release still fits the clients using the last one. A client depends on a tool through its schemas: it sends arguments that its copy of the `inputSchema` accepts, and it reads the fields that its copy of the `outputSchema` promises. When a tool declares an output schema, the server **MUST** return structured content that conforms to it, and clients **SHOULD** validate it ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md), "Structured Content").

The Python SDK's client does validate, and it validates against its own copy. It keeps one compiled validator per tool, built from the output schema in the last `tools/list` it absorbed, and replaces it only when a later listing brings a different schema (`mcp/client/session.py`, `_output_schema_validator` and `_absorb_tool_listing`). A non-error result that doesn't match raises `RuntimeError` in the caller (`mcp/client/session.py`, `validate_tool_result`). So a server that renames an output field breaks every connected client that listed its tools before the release, at the moment each one next calls the tool, and the server sees nothing wrong.

In the shop's case, release 2 of the server renames the per-warehouse `on_hand` field of `check_stock` to `count`. To see the break, a client connects to release 1 in memory and lists the tools. It keeps its connection while the server swaps `check_stock` for release 2's version, as a rolling deploy would. Then the client calls the tool, lists again and calls once more. Last, a contract test runs the two checks it makes before a release ships: `lib.contract.breaking_changes`, a diff of the two releases' schemas, and a validation of release 2's real result against release 1's published output schema with `jsonschema`, the library the client uses.

Example `schema-change-breaks-a-client` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pytest 9.2.0 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""What a client connected before a release sees when the release renames check_stock's on_hand to count, and what
the contract checks report about the same change. The prose's point rests on the client's error line, which names
the missing field, and on the contract check's line."""
import asyncio

from mcp import Client
from pydantic import BaseModel

from lib import confirmations, contract, shop_tools
from lib.testing import shop_api_here


class Warehouse(BaseModel):
    warehouse: str
    count: int                                            # release 1 called it on_hand
    last_counted: str


class StockReport(BaseModel):
    sku: str
    available: int
    warehouses: list[Warehouse]


def check_stock(sku: shop_tools.Sku) -> StockReport:
    report = confirmations.chapter3_tools()["check_stock"].fn(sku)       # release 1's tool does the reading
    return StockReport(sku=sku, available=report.available, warehouses=[Warehouse(
        warehouse=w.warehouse, count=w.on_hand, last_counted=str(w.last_counted)) for w in report.warehouses])


async def main() -> None:
    server = shop_tools.create_server()
    with shop_api_here():                                  # the server's tools run in this process
        async with Client(server) as client:
            listing = await client.list_tools()
            print("release 1's tools/list cache hint:", f"ttlMs {listing.ttl_ms}")
            server.remove_tool("check_stock")                                  # the release, swapped in while connected
            server.add_tool(check_stock, description=shop_tools.DESCRIPTIONS["check_stock"])
            try:
                await client.call_tool("check_stock", {"sku": "KG-1031"})
            except RuntimeError as error:
                print("client that listed before the release:", error.args[0].splitlines()[0])  # the message's first line
            new = next(tool for tool in (await client.list_tools()).tools if tool.name == "check_stock")  # the release 2 schema
            result = await client.call_tool("check_stock", {"sku": "KG-1031"})
            print("client after listing again:", "result" if not result.is_error else "tool error")
    old = next(tool for tool in listing.tools if tool.name == "check_stock")
    print("contract check:", "; ".join(contract.breaking_changes(old, new)) or "no breaking change")
    validator = contract.validator(old.output_schema)(old.output_schema)    # by the dialect the schema declares
    print("validator for release 1's schema:", type(validator).__name__ + ", as it declares",
          old.output_schema.get("$schema", "no $schema"))
    # the first error the schema finds in release 2's real result
    print("release 2's result against release 1's schema:", next(validator.iter_errors(result.structured_content)).message)


asyncio.run(main())
```

Output:

```text
release 1's tools/list cache hint: ttlMs 0
client that listed before the release: Invalid structured content returned by tool check_stock: 'on_hand' is a required property
client after listing again: result
contract check: output warehouses[].on_hand: removed
validator for release 1's schema: Draft202012Validator, as it declares no $schema
release 2's result against release 1's schema: 'on_hand' is a required property
```

Release 1's tool list carried the SDK's default cache hint, `ttlMs 0`, so the list was stale the moment it arrived, and the client still validated against it. The call after the release failed inside the client: "Invalid structured content returned by tool check_stock: 'on_hand' is a required property". The server had returned a correct release 2 result. After the client listed the tools again, the same call came back as a result. A zero TTL doesn't protect a connected client, because the validator follows the last listing, not the cache: a client that lists once at startup holds that schema for as long as it runs.

Both contract checks caught the change without a client. The schema diff reported `output warehouses[].on_hand: removed`, and validating release 2's result against release 1's schema failed with the client's own message: "'on_hand' is a required property". The diff is a reviewer's aid: it compares field paths, types and required inputs, and its docstring lists what it leaves out, such as patterns and enums. The validation is the test to keep, because it checks the server's real output against the exact schema that clients hold.

Breaking changes aren't symmetric. On the output side, removing, renaming or retyping a field breaks clients, and adding an optional field doesn't. On the input side, adding a required argument breaks old callers, and removing one breaks them quietly, because the SDK's server drops arguments it doesn't know without an error, as [Treat ticket text as untrusted data](#untrusted-tool-output) shows. The pinned revision allows any JSON Schema 2020-12 keyword in both schemas, and reads a schema with no `$schema` as 2020-12 ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md)). A schema may name another dialect in `$schema`, and clients and servers **MUST** validate by the declared dialect, or by 2020-12 when none is declared ([base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic/index.md), "JSON Schema Usage"). So choose the validator from the schema, as the SDK's client does with `jsonschema`'s `validator_for` (`mcp/client/session.py`, `_output_schema_validator`). `lib.contract.validator` does the same for the shop's checks, with 2020-12 as the default. pydantic writes no `$schema`, so release 1's schema got `Draft202012Validator, as it declares no $schema`.

**Working rule:** Keep the last release's `tools/list` in the repository, and in CI validate every structured result your tests produce against it as well as against the new schema, each by the dialect it declares and by 2020-12 when it declares none. Treat a removed, renamed or retyped output field and a new required input as a breaking change: add the new field beside the old one, or add a new tool, and retire the old shape through a window ([Change tools without breaking clients](#change-tools-safely)). Don't rely on a short TTL to protect clients that are already connected.

## Replay recorded host runs {#replay-host-runs}

Tool tests and contract tests cover the server. The support host from [Build a host that works through tickets](#build-a-host) has logic of its own between the model and the servers: it routes names, asks for consent, sends results back and caps turns, and a change there can make every ticket go wrong without any tool failing. A replay covers that layer. It runs the real host against the real servers, with the model's replies taken from a recording, so a test can assert on what the host did for each ticket.

A replay tests the host and the servers against fixed model outputs. It doesn't test the model: a different model, or the same one with other sampling, needs a new recording. And it holds only while the messages stay as recorded. `ReplayModel` from `lib.host` looks each reply up by the SHA-256 of the exact messages, which include every tool definition and every tool result so far, and raises `RecordingMismatch` when they differ ([Run the host loop](#run-the-host-loop)). So a replay doubles as a tripwire: any change to what the model would see stops it, and a team then decides whether to record again.

The replay also gives the queue's results a second reading. [Work through the ticket queue](#work-the-queue) found that the model told customers their refunds were on the way for orders it never refunded. A reply is the model's claim, and the host's call log is the record of what happened, so the host can compare them before a reply reaches a customer. `lib.queue_replay` holds a small version of that check, built on the phrase check chapter 10 counted with, `ticket_host.promises_refund`, which looks for phrases such as "will be refunded" or "we'll refund". Reusing it keeps this chapter's counts and chapter 10's the same measurement. Its `unbacked_refund` is true when a run's last reply makes that promise and no `issue_refund` call in the run returned a result. The phrase list is a rule of thumb written against this recording's replies, not a classifier, and the module's docstring says what it misses.

`queue_replay.replay_queue` replays the whole queue, with the support host set up exactly as chapter 10's `work-the-ticket-queue` sets it up. The run prints one ticket's tool sequence, counts the refunds and the replies that promise one, and replays the first ticket after one sentence has been added to `quote_refund`'s description.

Example `replay-ticket-runs` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Replay chapter 10's queue run, the recording ticket-runs, through the support host, and check each reply's promise
against the host's call log. The prose's point rests on the refund lines, which compare refunds issued with replies
that promise one, and on the last line, which shows what a one-sentence rewording does to the replay."""
import asyncio

from lib import queue_replay, shop_tools, ticket_host
from lib.host import RecordingMismatch
from lib.shop_data import load_shop


def reword_quote_refund(host) -> None:              # the server's next release adds a sentence to one description
    changed = {**shop_tools.DESCRIPTIONS}
    changed["quote_refund"] += " Quotes are in the order's currency."
    host.listed["shop"] = shop_tools.with_descriptions(host.listed["shop"], changed)


async def main() -> None:
    tickets = {ticket.ticket_id: ticket for ticket in load_shop().tickets}
    runs = await queue_replay.replay_queue()
    print("tickets replayed:", len(runs))
    print("T-0009 tools:", " then ".join(turn.tool for turn in runs["T-0009"].calls))   # its calls, in order
    print("refunds issued:", sum(queue_replay.refunded(run) for run in runs.values()))
    # the phrase check from chapter 10, a rule of thumb: see the module's docstring for what it misses
    promised = [ticket_id for ticket_id, run in runs.items() if ticket_host.promises_refund(run.answer)]
    # a promise with no refund behind it: no issue_refund call in the run returned a result
    unbacked = [ticket_id for ticket_id in promised if queue_replay.unbacked_refund(runs[ticket_id])]
    print("replies that promise a refund:", len(promised))
    print("of which no call made:", len(unbacked))
    for tag in ("issue_refund", "quote_refund"):           # the tickets tagged with each refund tool
        group = [t for t in tickets.values() if t.expected_tool == tag]
        print(f"{tag} tickets flagged:", f"{sum(t.ticket_id in unbacked for t in group)} of {len(group)}")
    print("flagged:", ", ".join(unbacked))
    try:
        await queue_replay.replay_queue(change=reword_quote_refund, tickets=[tickets["T-0001"]])
    except RecordingMismatch:
        print("after rewording quote_refund, T-0001 replays:", "no, RecordingMismatch")


asyncio.run(main())
```

Output:

```text
tickets replayed: 48
T-0009 tools: shop.quote_refund then shop.find_orders
refunds issued: 0
replies that promise a refund: 11
of which no call made: 11
issue_refund tickets flagged: 6 of 7
quote_refund tickets flagged: 5 of 9
flagged: T-0007, T-0020, T-0029, T-0034, T-0036, T-0037, T-0040, T-0042, T-0045, T-0046, T-0048
after rewording quote_refund, T-0001 replays: no, RecordingMismatch
```

All 48 tickets replayed, and ticket T-0009 took the path it took in chapter 10: `shop.quote_refund then shop.find_orders`. An assertion on that sequence is a regression test for the host. If a change to routing or error handling sent the first tool execution error back differently, the model's second turn would no longer match the recording, and the replay would stop.

`lib.queue_replay` flags the promises that no call backs, and a host should send those replies to a person instead of to the customer. The host issued 0 refunds, yet 11 replies promise one, and 11 of them have no refund behind them.

Of the tickets asking for a refund, 6 of 7 are flagged, and of the tickets asking only what a refund would be, 5 of 9 are, each reply telling the customer the money was on its way. The one refund request not flagged, T-0024, ended with the model asking which product the customer meant, which promises nothing. The flagged tickets are T-0007, T-0020, T-0029, T-0034, T-0036, T-0037, T-0040, T-0042, T-0045, T-0046, T-0048.

The rewording at the end shows the tripwire. After one sentence was added to one description, the first ticket's replay gave `no, RecordingMismatch`. Every ticket's prompt holds every tool's description, so changing any description changes every prompt. That is the cost of replays, and also their use: a reworded description is the change that can alter what the model chooses, and the replay won't let it through unmeasured.

**Working rule:** Replay a recorded run of the whole queue in CI, assert on each ticket's tool sequence, and run a check that compares each reply's promises with the calls that returned a result. Keep generated IDs and clocks fixed in the servers a replay runs against, or it stops for reasons that aren't changes. Then treat `RecordingMismatch` as a signal, not as a flaky test: when you change a description, a prompt or a tool's output, record again with the recording script and compare the new run's scores with the old run's before you ship.

## Trace calls with OpenTelemetry {#trace-with-opentelemetry}

Tests run before a release; traces show what a server does after it. OpenTelemetry is the common way to get them: an application creates spans, each a named, timed operation with attributes and a parent, and an exporter sends them to a tracing backend. MCP adds one thing of its own. At the pinned revision, the `_meta` keys `traceparent`, `tracestate` and `baggage` are reserved for trace context, and their values **MUST** follow the W3C Trace Context and Baggage formats ([base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic/index.md)). That is how a client's trace and a server's trace join into one, whatever the transport.

The Python SDK traces with no setup in your server's code. Every server installs `OpenTelemetryMiddleware`, which wraps each inbound message in a `SERVER` span and does nothing until an OpenTelemetry SDK and exporter are installed (`mcp/server/lowlevel/server.py`; [OpenTelemetry](https://py.sdk.modelcontextprotocol.io/v2/run/opentelemetry/index.md)). The source marks the middleware provisional, so its details may change in a 2.x minor release. On the client side, the JSON-RPC paths, which are URLs, stdio and the legacy in-memory mode, open a `CLIENT` span named `MCP send {method} {target}` and inject `traceparent` into the request's `_meta`, and the server extracts it as the parent of its span (`mcp/shared/jsonrpc_dispatcher.py`, `mcp/shared/_otel.py`). The in-process path from [Test tools in memory](#in-memory-tests) sends no JSON-RPC, so it creates no client span and injects nothing.

The shop wants a trace for each tool call, findable by tool name and showing whether it failed. The script installs OpenTelemetry's SDK, `opentelemetry-sdk` 1.45.2, with an `InMemorySpanExporter`, which keeps finished spans in a list that a test can read (`opentelemetry/sdk/trace/export/in_memory_span_exporter.py`). The script serves chapter 3's tools from [Design tools a model can use](#design-tools) over Streamable HTTP on loopback in the same process, so the client's and the server's spans land in the same list. It calls `find_orders` and then `quote_refund` for an order that doesn't exist. Then it makes the same `find_orders` call in memory twice, the second time inside a span of the test's own.

Example `trace-a-tool-call` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · opentelemetry-api 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · pydantic 2.14.3 · pytest 9.2.0 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""The OpenTelemetry spans the SDK emits for the shop's tool calls, over Streamable HTTP on loopback and in memory.
The prose's point rests on two printed lines: the HTTP server span, which shows the trace context crossing the wire,
and the in-memory server span parents, which show what happens without it."""
import asyncio

from mcp import Client
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv._incubating.attributes.mcp_attributes import McpMethodNameValues

from lib import loopback, shop_tools
from lib.testing import shop_api_here

spans = InMemorySpanExporter()
trace.set_tracer_provider(provider := TracerProvider())
provider.add_span_processor(SimpleSpanProcessor(spans))      # each span, as it ends, into memory


def finished(name: str) -> list:                 # every finished span with this name, in the order they ended
    return [span for span in spans.get_finished_spans() if span.name == name]


def parent(span) -> str:
    return next((s.name for s in spans.get_finished_spans() if span.parent and s.context.span_id ==
                 span.parent.span_id), "none")      # "none" for a span with no parent, or whose parent never finished


async def main() -> None:
    server = shop_tools.create_server()
    with shop_api_here(), loopback.serve(server.streamable_http_app()) as base_url:
        async with Client(base_url + "/mcp") as client:
            await client.call_tool("find_orders", {"customer_id": "C-0127"})
            await client.call_tool("quote_refund", {"order_id": "O-7144"})            # a tool error
        print("HTTP spans:", ", ".join(sorted(span.name for span in spans.get_finished_spans())))
        # the test makes one call of each, so the first finished span of each name is the call's
        call, error = finished("tools/call find_orders")[0], finished("tools/call quote_refund")[0]
        print("HTTP server span:", call.name, f"({call.kind.name}), parent: {parent(call)}")
        for key in sorted(set(call.attributes) - {"jsonrpc.request.id"}):   # the request ID changes on every run
            print(f"attribute {key}:", call.attributes[key])
        print("tool error span status:", error.status.status_code.name)
        print("tool error span error.type:", error.attributes["error.type"])
        spans.clear()
        async with Client(server) as client:
            await client.call_tool("find_orders", {"customer_id": "C-0127"})
            # a span of the test's own, which the in-memory server falls back to as the parent
            with trace.get_tracer("shop-tests").start_as_current_span("test find_orders"):
                await client.call_tool("find_orders", {"customer_id": "C-0127"})
        print("in-memory spans:", ", ".join(sorted(span.name for span in spans.get_finished_spans())))
        print("in-memory server span parents:", ", ".join(parent(s) for s in finished("tools/call find_orders")))
    # the pinned conventions predate the pinned revision, and this list has no server/discover
    assert "server/discover" not in {m.value for m in McpMethodNameValues}


asyncio.run(main())
```

Output:

```text
HTTP spans: MCP send server/discover, MCP send tools/call find_orders, MCP send tools/call quote_refund, MCP send tools/list, server/discover, tools/call find_orders, tools/call quote_refund, tools/list
HTTP server span: tools/call find_orders (SERVER), parent: MCP send tools/call find_orders
attribute gen_ai.operation.name: execute_tool
attribute gen_ai.tool.name: find_orders
attribute mcp.method.name: tools/call
attribute mcp.protocol.version: 2026-07-28
tool error span status: ERROR
tool error span error.type: tool_error
in-memory spans: server/discover, test find_orders, tools/call find_orders, tools/call find_orders, tools/list
in-memory server span parents: none, test find_orders
```

Over HTTP the spans came in pairs, each server span paired with a client span of the same method: MCP send server/discover, MCP send tools/call find_orders, MCP send tools/call quote_refund, MCP send tools/list, server/discover, tools/call find_orders, tools/call quote_refund, tools/list. The client listed the tools before its first call, because it validates the result against the output schema. The trace shows the server's span for the call, tools/call find_orders (SERVER), parent: MCP send tools/call find_orders, so the trace context crossed in `_meta`.

Its attributes name the method, `tools/call`, the operation, `execute_tool`, the tool, `find_orders`, and the revision (`mcp/server/_otel.py`).

The failed quote's span has the status ERROR and the `error.type` `tool_error`, although the call returned a result and not a JSON-RPC error, so a tracing backend can count tool execution errors without reading result bodies.

A test of trace propagation needs HTTP or stdio, because in memory the server has nothing to extract. In memory there were no client spans, only the server's spans and the test's own `test find_orders`: server/discover, test find_orders, tools/call find_orders, tools/call find_orders, tools/list. The two server spans' parents were none, test find_orders, in that order. With nothing to extract, the server falls back to whatever span is current, and only the test's own span gave it one (`mcp/shared/_otel.py`, `extract_trace_context`).

The names a server emits are the part to treat with care. OpenTelemetry's semantic conventions for MCP have the status Development; they recommend span names of the form `{mcp.method.name} {target}` and define metrics such as `mcp.server.operation.duration` ([MCP semantic conventions](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/mcp.md), read 2026-10-31). They have also moved: the page the MCP specification links to shows a notice that the GenAI conventions moved to a repository of their own, which has no tagged release ([moved notice](https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/)). The SDK's server spans follow the recommended naming. Its client span name, `MCP send …`, doesn't, and the SDK emits no metrics: the source of `mcp` 2.3.0 never creates a meter. The pinned conventions package, `opentelemetry-semantic-conventions` 0.66b2, predates the pinned revision. Its list of method names has `initialize` and `logging/setLevel`, it still defines `mcp.session.id`, and it has no `server/discover` (`opentelemetry/semconv/_incubating/attributes/mcp_attributes.py`).

For logs, the pinned revision deprecates MCP's own Logging messages, `notifications/message`, and points servers to standard error on stdio and to OpenTelemetry otherwise ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog.md)). [Replace sampling, roots and logging](#replace-deprecated-features) covers the move.

**Working rule:** Install an OpenTelemetry SDK and exporter in every server and host you run, and let the SDK's middleware make the server spans. Build dashboards on the attributes the SDK emits, `mcp.method.name`, `gen_ai.tool.name` and `error.type`, and label them as following a Development-status convention at a named version, because the names may change. Don't validate method names against the pinned conventions package. Test propagation over a real transport, and wrap in-memory calls in a span of your own when a test needs a parent.

## Measure how often the right tool is chosen {#tool-selection-accuracy}

The replay in [Replay recorded host runs](#replay-host-runs) asks whether the host still does what it did. A second question is how often the model chooses well with the tools and descriptions the shop gives it. The usual first measure is tool-selection accuracy: the share of cases in which the model's first call uses the tool a correct agent would use, often called top-1 accuracy. Benchmarks also score the arguments. The Berkeley Function Calling Leaderboard, for example, checks each call's name and arguments together against the expected ones by matching their abstract syntax trees ([BFCL](https://proceedings.mlr.press/v267/patil25a.html)).

A number from a fixed recording measures something narrow: the shop's tool names and descriptions, against one model, Qwen3-4B-Instruct-2507, quantized as Q4_K_M and sampled at temperature 0.7 ([Work through the ticket queue](#work-the-queue)), with the book's one prompt and one seed, over the 48 tickets the book wrote.

It is one draw from that setup, and the groups are small: the smallest has 8 tickets, so one ticket is a large share of its score. It says nothing about models in general, and a change to any description needs a new recording before the number means anything, which the replay's `RecordingMismatch` enforces. Each ticket carries the tool a correct agent calls first. The script scores with `ticket_host.expected_first_tool`, as chapter 10 does: a refund request counts as right when it starts with `quote_refund`, because `issue_refund` needs a quote first.

To score the replay, the script takes each ticket's first tool call and prints the accuracy overall, per expected tool and for each confusion. For the right calls that name an order, it also scores the `order_id` argument two ways: against the ID as the ticket wrote it, and against the order the customer meant. The two differ for the 5 tickets where a customer mistyped the number.

Example `tool-choice-accuracy` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Score the first tool call of every ticket in chapter 10's queue run against the tool each ticket is tagged with,
overall, per tag and by confusion, and check the order IDs of the right calls. The prose's point rests on the
accuracy lines, the per-tag line for refunds, and the two order-ID lines, which differ."""
import asyncio
from collections import Counter

from lib import queue_replay, ticket_host
from lib.shop_data import load_shop


async def main() -> None:
    tickets = load_shop().tickets
    runs = await queue_replay.replay_queue()
    scored = []                                            # (ticket, expected tool, first tool called)
    for ticket in tickets:
        calls = runs[ticket.ticket_id].calls
        # the first call, or None when the host made none; a refund ticket expects quote_refund first
        scored.append((ticket, ticket_host.expected_first_tool(ticket), calls[0] if calls else None))
    right = [(t, call) for t, expected, call in scored if call and call.tool == expected]
    print("first tool right:", f"{len(right)} of {len(scored)}")
    print("top-1 accuracy:", f"{len(right) / len(scored):.2f}")
    for expected, count in sorted(Counter(expected for _, expected, _ in scored).items()):
        hits = sum(1 for t, e, call in scored if e == expected and call and call.tool == expected)
        print(f"expected {expected}:", f"{hits} of {count}")
    confusions = Counter((expected, call.tool if call else "no tool") for _, expected, call in scored
                         if not call or call.tool != expected)
    for (expected, chosen), count in confusions.most_common():
        print(f"expected {expected}, called {chosen}:", count)
    with_order = [(t, call) for t, call in right if t.order_id and "order_id" in call.arguments]  # right calls naming an order
    as_written = sum(call.arguments["order_id"] == t.cited_order_id for t, call in with_order)   # the ID the ticket gave
    meant = sum(call.arguments["order_id"] == t.order_id for t, call in with_order)              # the customer's order
    print("right tool, order ID as the ticket wrote it:", f"{as_written} of {len(with_order)}")
    print("right tool, order the customer meant:", f"{meant} of {len(with_order)}")
    # tickets whose cited ID isn't the order the customer meant
    typos = [(t, e, call) for t, e, call in scored if t.cited_order_id and t.cited_order_id != t.order_id]
    print("tickets with a mistyped order ID:", len(typos))
    print("of which the right tool was called:", sum(1 for _, e, call in typos if call and call.tool == e))
    for t, _, call in [(t, e, call) for t, e, call in typos if not call or call.tool != e]:
        print(f"mistyped {t.ticket_id}, first tool:", call.tool if call else "no tool")
    print("smallest expected-tool group, tickets:", min(Counter(e for _, e, _ in scored).values()))
    manifest = queue_replay.manifest()
    print("recorded model:", manifest["model"].split("/")[-1])   # the model's name, without its publisher's path
    print("recorded quantization:", manifest["quantization"])


asyncio.run(main())
```

Output:

```text
first tool right: 36 of 48
top-1 accuracy: 0.75
expected shop.check_stock: 10 of 10
expected shop.find_orders: 8 of 8
expected shop.get_order_status: 12 of 14
expected shop.quote_refund: 6 of 16
expected shop.quote_refund, called shop.get_order_status: 8
expected shop.get_order_status, called partner.track_parcel: 2
expected shop.quote_refund, called shop.find_orders: 2
right tool, order ID as the ticket wrote it: 18 of 18
right tool, order the customer meant: 14 of 18
tickets with a mistyped order ID: 5
of which the right tool was called: 4
mistyped T-0042, first tool: shop.get_order_status
smallest expected-tool group, tickets: 8
recorded model: Qwen3-4B-Instruct-2507
recorded quantization: Q4_K_M
```

The first tool was right for 36 of 48 tickets, a top-1 accuracy of 0.75, the same 36 of 48 that chapter 10 counted.

The overall figure hides where the errors are. Stock questions scored 10 of 10 and order searches 8 of 8, but refund tickets only 6 of 16, and most of the misses, 8, went to `get_order_status`, although its description says to use `quote_refund` for a refund and `quote_refund`'s says to call it first. That pair of descriptions is the one to work on next, and the queue is the ticket set to record again once they change. The two status questions that went to `partner.track_parcel` are chapter 10's tracking-number case ([Work through the ticket queue](#work-the-queue)).

The arguments show why the reference matters. With the right tool, the model used the order ID as the ticket wrote it in 18 of 18 calls, and the order the customer meant in 14 of 18 calls.

The misses are customers' typos. Of the mistyped tickets, 4 reached the right tool and are scored here, and the other, T-0042, went first to `shop.get_order_status`, so it counts among the wrong tools instead. No model can see through a typo without looking the customer's orders up. Scored against what the customer meant, the model looks careless; scored against what it was given, it is faithful. The gap belongs to the host's flow, which should check an order against the ticket's customer before acting on it.

Published benchmarks point the same way. One preprint, RAG-MCP, reports that retrieving a shortlist of tools before the model chooses raised selection accuracy from 13.62% to 43.13% on its benchmark tasks, scored by a model acting as judge ([RAG-MCP](https://arxiv.org/abs/2505.03275)). MCP-Bench, over 28 live servers and 250 tools, reports persistent challenges on tasks whose instructions don't name the tool ([MCP-Bench](https://arxiv.org/abs/2508.20453)). Each is a single preprint on its own tasks, and neither says anything about the shop's numbers.

**Working rule:** Score every recorded run on the first tool per tag, not only overall, and score arguments separately, against what the ticket gave the model and against the truth. Work on the descriptions behind the largest confusion first, record again, and compare per-tag scores between the two recordings. State the model, the prompt and the ticket set beside every score, and never compare scores across different setups.

## Change tools without breaking clients {#change-tools-safely}

The contract test in [Check schemas as a contract](#schema-contract-tests) says when a change breaks clients; it doesn't say how to make the change. The specification doesn't either. A tool definition has no deprecation field, and nothing in the pinned revision marks a tool as on its way out ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md)). What follows is practice: the book's recommendation, built from parts the specification does define, not a protocol feature.

There are three such parts. A client asks for tool list changes with `subscriptions/listen` and hears about each one on that stream ([subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)), as [Tell clients when a resource changes](#resource-change-notifications) shows for resources. A `tools/list` result carries a cache hint, `ttlMs`, and a change notification invalidates a cached list that is still fresh; clients **MAY** re-fetch early when a call fails as if the tool changed, for example with an unknown method or invalid parameters ([caching](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching.md)). And a tool execution error is what clients **SHOULD** give the model so it can correct itself ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md), "Error Handling"). From those parts, the book recommends this procedure: add the new tool beside the old one; mark the old one "Deprecated: use …" in its description; announce the change; shorten the TTL while the change is under way; keep the old tool working through a window; and after the window, answer it with an execution error that names the replacement.

The shop is replacing `find_orders` with `find_orders_v2`, which can also filter by SKU. To walk through the three releases, the script serves chapter 3's tools from [Design tools a model can use](#design-tools) over Streamable HTTP on loopback, with a TTL of one minute on the tool list, and connects two clients: one that listens for list changes, and one that only caches. Release 2 adds `find_orders_v2` and rewords `find_orders`, and the server publishes the change. Release 3 replaces `find_orders` with a function that raises `ToolError`. An in-memory client wouldn't do here, because the in-process path doesn't deliver list changes ([Test tools in memory](#in-memory-tests)).

Example `deprecate-a-tool` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pytest 9.2.0 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Retire find_orders in favour of find_orders_v2 over three releases, watched by a listening client and a caching
client. The prose's point rests on the caching client's list and on the last line, the error the old name returns
after the window."""
import asyncio

from mcp import Client
from mcp.server.caching import CacheHint
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.subscriptions import InMemorySubscriptionBus, ToolsListChanged

from lib import confirmations, loopback, shop_tools
from lib.testing import shop_api_here

bus, tools = InMemorySubscriptionBus(), confirmations.chapter3_tools()
server = MCPServer("shop-support", version="0.11.0", tools=list(tools.values()), subscriptions=bus,
                   cache_hints={"tools/list": CacheHint(ttl_ms=60_000, scope="public")})   # a minute: short while a change is under way
old = tools["find_orders"]


def find_orders_v2(customer_id: shop_tools.CustomerId, sku: shop_tools.Sku | None = None) -> shop_tools.OrderList:
    """Search one customer's orders, newest first, optionally only those with one product's SKU."""
    found = old.fn(customer_id, limit=50)
    return found.model_copy(update={"orders": [o for o in found.orders if sku is None or sku in o.skus]})


def retired(customer_id: shop_tools.CustomerId) -> shop_tools.OrderList:
    raise ToolError("find_orders was retired. Call find_orders_v2 with the same customer_id.")


async def replace_find_orders(fn, description: str) -> None:
    server.remove_tool("find_orders")
    server.add_tool(fn, name="find_orders", title=old.title, description=description, annotations=old.annotations)
    await bus.publish(ToolsListChanged())                     # to every client listening for list changes


async def main() -> None:
    with shop_api_here(), loopback.serve(server.streamable_http_app()) as base_url:
        async with Client(base_url + "/mcp") as listening, Client(base_url + "/mcp") as cached:
            listing, _ = await cached.list_tools(), await listening.list_tools()     # both cache release 1's list
            print("release 1:", f"{len(listing.tools)} tools, ttlMs {listing.ttl_ms}")
            async with listening.listen(tools_list_changed=True) as changes:   # a stream that carries list-change events
                server.add_tool(find_orders_v2)                                       # release 2: the replacement first
                await replace_find_orders(old.fn, "Deprecated: use find_orders_v2. " + old.description)
                print("event:", type(await anext(changes)).__name__)
            print("listening client sees:", ", ".join(t.name for t in (await listening.list_tools()).tools))
            print("cached client sees:", ", ".join(t.name for t in (await cached.list_tools()).tools))
            during = await cached.call_tool("find_orders", {"customer_id": "C-0127"})
            print("find_orders during the window:", "tool error" if during.is_error else "result")
            await replace_find_orders(retired, "Retired: use find_orders_v2.")         # release 3: the old name now errors
            after = await cached.call_tool("find_orders", {"customer_id": "C-0127"})
            print("find_orders after the window:", after.content[0].text)


asyncio.run(main())
```

Output:

```text
release 1: 5 tools, ttlMs 60000
event: ToolsListChanged
listening client sees: get_order_status, quote_refund, issue_refund, check_stock, find_orders_v2, find_orders
cached client sees: find_orders, get_order_status, quote_refund, issue_refund, check_stock
find_orders during the window: result
find_orders after the window: Error executing tool find_orders: find_orders was retired. Call find_orders_v2 with the same customer_id.
```

Release 1 listed 5 tools, ttlMs 60000. When release 2 shipped, the listening client received `ToolsListChanged`. The SDK drops a cached list before it hands the client such an event (`mcp/client/client.py`), so the listening client's next listing showed both tools: get_order_status, quote_refund, issue_refund, check_stock, find_orders_v2, find_orders.

The caching client heard nothing and served release 1's list from its cache: find_orders, get_order_status, quote_refund, issue_refund, check_stock. Its call to `find_orders` during the window still returned a result. A model behind a caching client doesn't learn about `find_orders_v2` until the TTL runs out or the client re-fetches, which is why the TTL should be short while a change is under way, and why the old tool has to keep working.

After release 3, the caching client's call to `find_orders` came back as an execution error the model can act on: "Error executing tool find_orders: find_orders was retired. Call find_orders_v2 with the same customer_id.". A removed tool would have produced the SDK's unknown-tool error instead, which tells the model the name was wrong but not what to call ([Report failures as tool results](#tool-errors)). The SDK returns that error as a tool execution error, although the specification makes an unknown tool a protocol error (`mcp/server/mcpserver/tools/tool_manager.py`; [tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md), "Error Handling").

The listening client's list also shows a side effect: `find_orders` moved to the end. `MCPServer` lists tools in the order they were added, so the release's live swap, which removes the tool and adds it back, moves it ([Cache list results](#cache-list-results)). A changed order changes the start of every prompt that renders the list, which is what a model provider's prompt cache matches on. A server that restarts with the new code lists tools in the order its code registers them, so add new tools at the end and leave the existing ones where they are.

**Working rule:** Retire a tool in three releases: add the replacement and mark the old tool deprecated in its description, keep both working through a window you announce, then answer the old name with an execution error that names the replacement. Shorten `ttlMs` on `tools/list` while the change is under way, publish a list change at each release, and open a `subscriptions/listen` stream in every host you control. Say in your changelog that the window is your policy, since the protocol defines none.

## What goes wrong in production {#test-and-observe-in-production}

The checks here run against one process on one machine. In production the same signals come from many replicas and clients, and each can mislead you in its own way.

**Spans multiply past what a backend can index.** The SDK names a server span after the method and the tool, which keeps the number of distinct names as small as the tool list. An order ID, a resource URI or a customer ID in a span name makes one name per value; the MCP conventions keep the resource URI in an attribute for that reason ([MCP semantic conventions](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/mcp.md)). The sign is a tracing bill that grows with traffic rather than with features.

**Traces carry the shop's data.** The SDK records no tool arguments or results in its spans (`mcp/server/_otel.py`), and the conventions mark `gen_ai.tool.call.arguments` as opt-in (same source). The shop's arguments hold customer and order IDs, and an argument says only what the caller sent. To record who acted, take the verified token's subject, which at the support host is the member of staff, with the customer from the ticket record the server checked ([Keep the server from acting as a confused deputy](#confused-deputy)). Add arguments to spans only behind a setting, and keep them out of any backend that the shop's data-handling policy doesn't cover.

**The conventions move under your dashboards.** The MCP conventions have Development status and have changed repository once ([moved notice](https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/)), and the SDK's middleware is marked provisional (`mcp/server/lowlevel/server.py`). An SDK release that renames an attribute empties a dashboard without an error. Keep the attribute names in one place in your configuration, and check them at each SDK upgrade, as you would any update trigger.

**Replicas disagree during a deploy.** In a rolling deploy, one replica serves release 1's schema while the next serves release 2's, and a client that listed from one and calls the other gets the `RuntimeError` from [Check schemas as a contract](#schema-contract-tests). The sign is client-side validation errors that rise during a deploy and fall when it ends. Ship additive changes first, and remove the old shape only once every replica serves the new one and the window has passed.

**The recording ages.** A replay keeps passing while the model behind the production host changes, so scores from the recording drift away from what customers see. Record again at each model change, as [Work through the ticket queue](#work-the-queue) recommends, and run the same unbacked-promise check on a sample of production runs, since a replay can't find a failure the recorded model never made.

**Working rule:** Before you rely on a trace or a score, check what it covers: which transport, which model, and which release of each schema. Keep span names bounded and arguments out of spans by default, pin the attribute names your dashboards use to a named convention version, and run the contract test and the replay against every release before it reaches a replica.

## Decisions this chapter made {#test-and-observe-decisions}

- **Tools are tested in memory** with `Client(server, raise_exceptions=True)`, asserting on fields, with one loopback test per transport for what the in-process path skips.
- **pytest runs with anyio's own plugin,** and without `inline-snapshot`, which the book doesn't pin. `lib.testing` prints one line per test so the output is stable.
- **The last release's schemas are the contract.** CI validates new results against them with the validator for each schema's declared dialect, 2020-12 by default, and `lib.contract` diffs the schemas for review.
- **Chapter 10's recording `ticket-runs` is replayed, not recorded again.** A `RecordingMismatch` after a description change means record again.
- **The host checks replies against its call log.** A reply that promises a refund no call made goes to a person; the keyword check in `lib.queue_replay` is a rule of thumb.
- **Traces come from the SDK's middleware,** with the attributes it emits labelled as a Development-status convention, and propagation is tested over HTTP.
- **Tool choice is scored per tag, and arguments separately,** with `expected_first_tool`, as chapter 10 scores. Order IDs are scored both against the ticket's text and against the order the customer meant.
- **Tools are retired in three releases,** with a short TTL and a list change at each, and an execution error that names the replacement after the window. The procedure is the book's practice, not the specification's.
