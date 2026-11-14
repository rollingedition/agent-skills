---
title: "Model Context Protocol in Practice"
chapter: "Serve over Streamable HTTP"
chapter_id: streamable-http
book: model-context-protocol-in-practice
edition: 2026.11.11
verified: 2026-11-14
edition_code: 2VMD-DEEC
canonical: https://rollingedition.com/model-context-protocol-in-practice/streamable-http
license: CC BY 4.0
attribution: "“Serve over Streamable HTTP,” chapter 6 of Model Context Protocol in Practice, Edition 2026.11.11, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/model-context-protocol-in-practice/streamable-http. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Serve over Streamable HTTP

By the end of this chapter you can serve the shop's Model Context Protocol server over Streamable HTTP, read what each request and response carries, stream progress from a long call and cancel it, run the server as replicas behind one address with no sticky sessions, and refuse requests that a browser was tricked into sending. What this chapter says holds at revision 2026-07-28 of the specification and at version 2.3.0 of the Python SDK, `mcp`.

Until this chapter, every host launched `shop-support`, [the shop](#the-shop)'s server, as a subprocess and talked to it over stdio, which works for one person on one machine. The shop's support team now works tickets from many hosts. The server has to reach the shop's API from inside the shop's network. And the team wants a slow job on the server: `recount_stock`, which recounts every product in both warehouses and takes minutes in the real shop. A subprocess per host can't be shared, scaled or watched from one place.

For a server that many hosts share, the Model Context Protocol (MCP) defines a second transport, **Streamable HTTP**. The server listens at one HTTP endpoint, and each message a client sends is a POST of its own, as the specification's [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) describes. The rest of MCP stays as it is: the JSON-RPC messages, the `_meta` on every request and the same tools.

Four small shared modules in `examples/lib/` carry this chapter's setup, so each example shows only its idea:

- `lib.http_mcp` starts a server example as its own process on a free loopback port, sends hand-written requests with the headers the pinned revision asks for, and loads the server object an earlier example defines.
- `lib.wire`, the trace printer from [Read the messages on the wire](#read-the-messages), gains `record_http`, which wraps a server's HTTP app and logs each exchange: headers, body, status and every message in the response.
- `lib.recount` holds the shop's recount, its SKUs and one API call per product.
- `lib.shared_state` keeps state in one SQLite file that several server processes open, for the replicas in [Run replicas without sticky sessions](#scale-without-sessions).

Most examples serve the server's HTTP app in their own process, through [`lib.loopback`](#the-shop), chapter 1's helper for an app on a free loopback port, so the recorder sees the server side. The first and replicas examples are the exceptions, running the server as separate processes, as a deployment does. Everything binds to 127.0.0.1.

## Move the server from stdio to HTTP {#stdio-to-http}

A server on stdio has exactly one client, the host that launched it. A server on Streamable HTTP has an address, and any client that can reach that address can use it. At the pinned revision that costs the server little, because the protocol keeps no state between requests. The [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) records that the revision removed the `initialize` handshake and the `Mcp-Session-Id` header, and that each request carries its own protocol version and client capabilities in `_meta`. A request over HTTP is therefore self-contained, like a call to the shop's own API: one POST in, one response out.

A server answers each request in one of two forms: a single JSON object (`Content-Type: application/json`), or a Server-Sent Events stream (`text/event-stream`) that belongs to that one request. The client must accept both, as the transport specification says. The stream exists so that the server can send notifications, such as progress, before the result, which [Stream progress on a long call](#stream-progress) relies on.

In the Python SDK the change is one argument. `MCPServer.run(transport="streamable-http")` serves the server under uvicorn, by default on 127.0.0.1, port 8000, at the path `/mcp` (`mcp/server/mcpserver/server.py`). On the client side, `Client` takes a URL where it took `StdioServerParameters`, and connects with the SDK's Streamable HTTP client (`mcp/client/client.py`). The shop's server keeps chapter 3's five tools unchanged, and only the last lines of its file change. The port comes from `http_mcp.port()`, not 8000, so it never collides with anything else.

Example `serve-on-loopback` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Serves chapter 3's five tools over Streamable HTTP in a process of its own, then calls one from a client that has only
the endpoint's URL. The point rests on the protocol revision and O-1873 status lines: the client settles on the pinned
revision and gets the order's status back."""
import asyncio
import sys
from urllib.parse import urlsplit

from mcp import Client

from lib import http_mcp, loopback, shop_api, shop_tools

server = shop_tools.create_server(version="0.6.0")      # chapter 3's tools, unchanged


async def main() -> None:
    with loopback.serve(shop_api.create_app()) as api_url:
        with http_mcp.launch(__file__, env=shop_api.server_env(api_url)) as url:   # runs this file again with --serve, as its own process
            async with Client(url) as client:                                # no handshake: the client needs only the URL
                print("endpoint host:", urlsplit(url).hostname)
                print("endpoint path:", urlsplit(url).path)
                print("protocol revision:", client.protocol_version)
                print("server:", client.server_info.name, client.server_info.version)
                print("tools:", len((await client.list_tools()).tools))
                result = await client.call_tool("get_order_status", {"order_id": "O-1873"})
                print("O-1873 status:", result.structured_content["status"])


if "--serve" in sys.argv:
    server.run(transport="streamable-http", port=http_mcp.port())   # 127.0.0.1, path /mcp
else:
    asyncio.run(main())
```

Output:

```text
endpoint host: 127.0.0.1
endpoint path: /mcp
protocol revision: 2026-07-28
server: shop-support 0.6.0
tools: 5
O-1873 status: delivered
```

The client reached the server at the SDK's defaults, `127.0.0.1` at `/mcp`.

It settled on revision 2026-07-28 and found 5 tools on `shop-support 0.6.0`. Order O-1873 came back delivered, as it does over stdio. The server process got the shop's API address and key in its environment, as the stdio servers did, and nothing else changed.

The SDK's `streamable_http_app()` also takes a `stateless_http` flag, At 2.3.0, the app routes each request by its `MCP-Protocol-Version` header, and a request at the pinned revision goes to a handler that serves one exchange and never sets `Mcp-Session-Id`, whatever the flag says. The flag only changes how clients on a 2025 revision are served (`mcp/server/streamable_http_manager.py`). The older HTTP+SSE transport, with its separate event endpoint, has been deprecated since revision 2025-03-26. Its earliest removal is three months after the specification's feature-lifecycle proposal, SEP-2596, reaches Final ([deprecated features](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)). [Move from HTTP+SSE to Streamable HTTP](#move-off-http-sse) ports a server off it.

**Working rule:** Serve over Streamable HTTP with `MCPServer.run(transport="streamable-http")` and its loopback default while you develop, and give clients the endpoint's URL. Leave `stateless_http` alone unless you also serve clients on a 2025 revision, where it decides whether they get sessions. Keep stdio for servers that a host launches for one user, as [Choose stdio or Streamable HTTP](#stdio-or-http) explains.

## Read one HTTP exchange {#http-on-the-wire}

The client in [Move the server from stdio to HTTP](#stdio-to-http) hid all of this, but when a call fails behind a proxy or a gateway, the exchange is what you read, so it pays to know what a correct one looks like. At the pinned revision, every POST carries headers that copy parts of its body. `MCP-Protocol-Version` repeats the version, `Mcp-Method` the JSON-RPC method, and `Mcp-Name` the tool, prompt or resource for `tools/call`, `prompts/get` and `resources/read`. The copies exist so that load balancers, gateways and monitoring can route and inspect a request without parsing its body, as the specification's [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) explains.

The body stays the source of truth. A server MUST reject a request whose headers disagree with its body, with `400 Bad Request` and the JSON-RPC error -32020, `HeaderMismatch`. That rule is what makes the headers safe to route on. A gateway that sends `Mcp-Name: check_stock` to the stock replicas can trust that the body names `check_stock` too, because a server would refuse the request otherwise.

Recording one `get_order_status` call with the SDK's client shows a correct exchange. Two requests the SDK's client never sends, through `lib.http_mcp.post`, show what the server refuses: a `tools/call` whose `Mcp-Name` says `check_stock` while its body names `get_order_status`, and a GET.

Example `trace-an-http-exchange` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Records the HTTP exchanges behind one tool call, then sends two requests the SDK's client never would. The point rests
on the request headers and response status lines of the tool call, and on the mismatched and GET lines, which show what
the server refuses."""
import asyncio
import os

import httpx2
from mcp import Client

from lib import http_mcp, loopback, shop_api, wire

SHOWN = ("content-type", "accept", "mcp-protocol-version", "mcp-method", "mcp-name")


async def main() -> None:
    server = http_mcp.load_server("serve-on-loopback.py")        # chapter 3's five tools
    app = wire.record_http(server.streamable_http_app(), log="http.jsonl")   # logs each exchange as the app saw it
    with loopback.serve(shop_api.create_app()) as api_url, loopback.serve(app) as base_url:
        os.environ.update(shop_api.server_env(api_url))           # the server runs in this process, so it reads the API address here
        async with Client(base_url + "/mcp") as client:
            await client.call_tool("get_order_status", {"order_id": "O-1873"})
        exchanges = wire.read_http_trace("http.jsonl")
        # the recorder keeps header names in lower case
        print("POSTs:", ", ".join(e["request_headers"]["mcp-method"] for e in exchanges))
        call = next(e for e in exchanges if e["request_headers"]["mcp-method"] == "tools/call")
        for name in SHOWN:
            print(f"request {name}:", call["request_headers"][name])
        print("request _meta keys:", ", ".join(call["request"]["params"]["_meta"]))
        print("response status:", call["status"])
        print("response content-type:", call["response_headers"]["content-type"])
        print("response mcp-session-id:", call["response_headers"].get("mcp-session-id", "none"))

        # the body names get_order_status, so this Mcp-Name header disagrees with it
        wrong = http_mcp.post(base_url + "/mcp", "tools/call", {"name": "get_order_status",
                              "arguments": {"order_id": "O-1873"}}, headers={"Mcp-Name": "check_stock"})
        print("mismatched Mcp-Name status:", wrong.status_code)
        print("mismatched Mcp-Name error:", wrong.json()["error"]["code"], wrong.json()["error"]["message"])
        # a GET marked with the pinned revision, which the app refuses rather than serving its 2025 stream
        stream = httpx2.get(base_url + "/mcp", headers={"MCP-Protocol-Version": http_mcp.VERSION})
        print("GET status:", stream.status_code)
        print("GET allow:", stream.headers["allow"])


asyncio.run(main())
```

Output:

```text
POSTs: server/discover, tools/call, tools/list
request content-type: application/json
request accept: application/json, text/event-stream
request mcp-protocol-version: 2026-07-28
request mcp-method: tools/call
request mcp-name: get_order_status
request _meta keys: io.modelcontextprotocol/protocolVersion, io.modelcontextprotocol/clientInfo, io.modelcontextprotocol/clientCapabilities
response status: 200
response content-type: application/json
response mcp-session-id: none
mismatched Mcp-Name status: 400
mismatched Mcp-Name error: -32020 mcp-name header does not match the request body's 'name' parameter
GET status: 405
GET allow: POST
```

The client made three POSTs for that one call: server/discover, tools/call, tools/list. The first asks the server what it supports, since there is no handshake. The last is the SDK's client fetching the tool list after the call, so that it can check the structured result against the tool's output schema (`mcp/client/session.py`, `validate_tool_result`). The `tools/call` POST carried:

- `MCP-Protocol-Version: 2026-07-28`
- `Mcp-Method: tools/call`
- `Mcp-Name: get_order_status`
- `Accept: application/json, text/event-stream`, because the client must take either form of response

Its body's `_meta` held the same three keys that it holds over stdio: io.modelcontextprotocol/protocolVersion, io.modelcontextprotocol/clientInfo, io.modelcontextprotocol/clientCapabilities. The response came back 200 as `application/json`, and it set no session header (`mcp-session-id`: none).

The response was plain JSON because the tool sent nothing before its result. The SDK doesn't commit to an event stream until the handler sends a notification or 15 seconds pass, so a handler that finishes silently inside that window gets a JSON response (`mcp/server/_streamable_http_modern.py`). That 15-second limit belongs to a detail of that private module and may change between releases.

The server refused the mismatched request before the tool ran, with 400 and error -32020 mcp-name header does not match the request body's 'name' parameter. The SDK's own client recovers from -32020 by fetching the tool list again and resending once, because at the pinned revision a tool can mark parameters with `x-mcp-header`, which clients copy into `Mcp-Param-{Name}` headers, and a stale listing gets those headers wrong (`mcp/client/client.py`, `call_tool`).

The GET was refused too: 405, with `Allow: POST`. A server that supports only the pinned revision SHOULD answer GET and DELETE with `405 Method Not Allowed`, because that revision has no stream a client opens with GET ([the transport specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)). The SDK's app also serves the 2025 revisions, and sends a GET without the pinned version in `MCP-Protocol-Version` to its 2025 handler, which serves it and refuses only a GET marked with the pinned revision, as this one was (`mcp/server/streamable_http_manager.py`).

**Working rule:** When an HTTP call fails, read the exchange first: the three routing headers, `_meta` in the body, the status and the content type. Route in a gateway on `Mcp-Method` and `Mcp-Name` if you need to, and never rewrite a body without rewriting its headers to match, because the server will refuse the pair with -32020. On a server that supports only the pinned revision, a 405 means an older client is opening a GET stream; the SDK's app serves those clients instead.

## Stream progress on a long call {#stream-progress}

The exchange in [Read one HTTP exchange](#http-on-the-wire) returned in milliseconds. A call that takes minutes leaves the person at the host seeing nothing, and the host can't tell slow from stuck. **Progress** is MCP's answer. A client that wants progress puts a `progressToken` in the request's `_meta`. The server MAY then send `notifications/progress` with that token, each carrying a `progress` value that MUST increase with every notification, and optionally a `total` and a `message` ([progress](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/progress)). Over Streamable HTTP, these notifications travel only on the response stream of the request they belong to ([Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)).

In the SDK, a tool reports with `await ctx.report_progress(progress, total=..., message=...)`. A client asks for reports on a call with `call_tool(..., progress_callback=...)`, which also puts the token in `_meta`. When the caller didn't ask, `report_progress` does nothing (`mcp/server/_streamable_http_modern.py`, `progress`), so a tool can always call it.

The shop's API has an endpoint, `POST /stock/{sku}/recount`, which recounts one product in both warehouses and takes a few seconds per product in the real shop. `recount_stock` calls it for each of the shop's 64 SKUs and reports after each one. In the examples, `lib.recount` asks the API to take 0.02 seconds per product, so a full recount takes a few seconds. The same server runs twice: once with the SDK's default, which can stream, and once with `json_response=True`, which makes every response a single JSON object.

Example `progress-on-stock-recount` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Runs recount_stock with progress reports, once with the SDK's streaming responses and once with JSON-only responses. The
point rests on the content-type and progress report lines: a JSON-only server drops every report, though the recount still
counts the same units."""
import asyncio
import os

from mcp import Client
from mcp.server.mcpserver import Context, MCPServer
from mcp.types import ToolAnnotations

from lib import loopback, recount, shop_api, wire

server = MCPServer("shop-support", version="0.6.0")


@server.tool(title="Recount stock", annotations=ToolAnnotations(read_only_hint=False, idempotent_hint=True))
async def recount_stock(ctx: Context) -> recount.Recount:
    """Recount every product's stock in both warehouses. Slow: reports progress per product."""
    units = 0
    async with recount.api() as api:
        for n, sku in enumerate(recount.SKUS, 1):                       # counts from 1, so the last report is the total
            units += await recount.one(api, sku)                        # lib.recount has the API take 0.02 seconds per product unless told otherwise
            await ctx.report_progress(n, total=len(recount.SKUS), message=f"recounted {sku}")
    return recount.Recount(skus=len(recount.SKUS), units=units)


async def run(mode: str, json_response: bool) -> None:
    # json_response=True sends every response as one JSON object, with no stream for reports to travel on
    app = wire.record_http(server.streamable_http_app(json_response=json_response), log=f"{mode}.jsonl")
    reports = []

    async def on_progress(progress: float, total: float | None, message: str | None) -> None:
        reports.append((progress, total, message))

    with loopback.serve(app) as base_url:
        async with Client(base_url + "/mcp") as client:
            result = await client.call_tool("recount_stock", progress_callback=on_progress)
    call = next(e for e in wire.read_http_trace(f"{mode}.jsonl") if e["request"]["method"] == "tools/call")
    print(f"{mode} content-type:", call["response_headers"]["content-type"].split(";")[0])
    print(f"{mode} progress reports:", len(reports))
    print(f"{mode} last report:", "{:g} of {:g}, {}".format(*reports[-1]) if reports else "none")
    print(f"{mode} units counted:", result.structured_content["units"])


async def main() -> None:
    with loopback.serve(shop_api.create_app()) as api_url:
        os.environ.update(shop_api.server_env(api_url))          # the servers run in this process
        await run("sse", json_response=False)
        await run("json", json_response=True)


asyncio.run(main())
```

Output:

```text
sse content-type: text/event-stream
sse progress reports: 64
sse last report: 64 of 64, recounted KG-1064
sse units counted: 6969
json content-type: application/json
json progress reports: 0
json last report: none
json units counted: 6969
```

With the default, the host saw the recount move. The response came back as `text/event-stream`, and the client received 64 reports, the last of them 64 of 64, recounted KG-1064. The first progress notification is what committed the response to an event stream, so nobody had to wait out the SDK's 15-second window. The recount counted 6969 units.

With `json_response=True`, the host got nothing until the end. The response was `application/json`, and the client received 0 reports. The recount still ran and counted 6969 units, and nothing failed. The SDK's JSON path has nowhere to send a notification, so `report_progress` returns without sending, and neither side logs it (`mcp/server/_streamable_http_modern.py`). The specification allows that, because progress is optional for the server. The person at the host would have waited the whole recount with no sign of life.

Streaming also has to survive intermediaries, since a proxy that buffers responses holds progress back until the end. The [transport specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) says servers SHOULD send `X-Accel-Buffering: no` on event streams to stop that, and the SDK sends it, with `Cache-Control: no-cache, no-transform` (`mcp/server/_streamable_http_modern.py`, `_SSE_HEADERS`).

**Working rule:** Report progress from any tool that can run longer than a few seconds, with a `total` when you know it and a message a person can read. Keep the SDK's default response mode. Use `json_response=True` only for a server whose every tool is quick, and know that it drops every progress report and every cancellation without telling anyone.

## Cancel a call the client no longer needs {#cancel-a-call}

The recount in [Stream progress on a long call](#stream-progress) ran to the end because the client waited for it. Often, though, the host stops needing the answer partway through: the person closes the ticket, or the host's own deadline passes. A call that keeps running after that wastes the shop's API and holds whatever the tool holds.

On Streamable HTTP, a client cancels a request by closing that request's response stream. The [cancellation](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation) pattern in the specification calls the closed stream "the cancellation signal", says the server MUST treat a client disconnect as cancelling that request, and says no `notifications/cancelled` message is "required or expected". That differs from stdio, where a client still sends `notifications/cancelled`, and from the 2025 revisions, where HTTP clients sent it too. The SDK implements both halves. Its client aborts the POST when the awaiting task is cancelled or its read timeout passes, and sends nothing else (`mcp/client/streamable_http.py`). Its server watches for the disconnect and cancels the task that runs the handler (`mcp/server/_streamable_http_modern.py`, `watch_disconnect`).

Inside an `async def` tool, cancellation arrives as anyio's cancellation exception at the next `await`. The tool may record where it stopped, but it must re-raise. Cleanup that has to await something needs a shielded scope, such as `anyio.move_on_after(5, shield=True)`, or the cancellation cancels the cleanup too. A plain `def` tool runs in a worker thread and stops only if it calls `anyio.from_thread.check_cancelled()`. One that never calls it runs to the end, and its result is thrown away. The [SDK's cancellation guide](https://py.sdk.modelcontextprotocol.io/v2/handlers/cancellation/) and `mcp/server/_streamable_http_modern.py` (`watch_disconnect`) describe both cases.

To watch that path end to end, the host cancels the call at the fifth progress report, the way a host would when its person closes the ticket. Each product takes 0.1 seconds here, so the server is still inside the sixth product's recount when the stream closes. `recount_stock` records how each run ended, and the recorder logs what crossed the wire.

Example `cancel-the-stock-recount` (Python 3.12.15 · anyio 4.16.0 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Cancels recount_stock after five progress reports by closing its response stream, and records where the server stopped.
The `server saw` and `tools/call stream` lines are the ones the prose's point rests on: they show where the tool
stopped and how the client ended the call."""
import os

import anyio
from mcp import Client
from mcp.server.mcpserver import Context, MCPServer

from lib import loopback, recount, shop_api, wire

server = MCPServer("shop-support", version="0.6.0")
runs: list = []                           # how a recount ended, and how many recounts it asked the API for


@server.tool(title="Recount stock")
async def recount_stock(ctx: Context) -> recount.Recount:
    """Recount every product's stock in both warehouses. Slow: reports progress per product."""
    done = units = 0
    async with recount.api() as api:
        try:
            for asked, sku in enumerate(recount.SKUS, 1):      # counted before each request to the API
                units += await recount.one(api, sku, seconds=0.1)       # 0.1 seconds per product keeps the server inside the sixth one
                done += 1
                await ctx.report_progress(done, total=len(recount.SKUS), message=f"recounted {sku}")
        except anyio.get_cancelled_exc_class():
            runs.extend([f"cancelled with {done} of {len(recount.SKUS)} recounted", asked])
            raise                         # always re-raise; cleanup that awaits goes under a shielded scope
    return recount.Recount(skus=done, units=units)


async def main() -> None:
    app = wire.record_http(server.streamable_http_app(), log="cancel.jsonl")
    with loopback.serve(shop_api.create_app()) as api_url, loopback.serve(app) as base_url:
        os.environ.update(shop_api.server_env(api_url))
        async with Client(base_url + "/mcp") as client:
            with anyio.CancelScope() as scope:
                async def on_progress(progress, total, message):
                    if progress >= 5:                                   # the threshold: the host cancels after the fifth report
                        scope.cancel()    # the host no longer needs the answer
                await client.call_tool("recount_stock", progress_callback=on_progress)
            await anyio.sleep(0.5)        # give the server time to see the closed stream
        print(f"server saw: {runs[0]}\nrecounts asked of the API: {runs[1]}")
    exchanges = wire.read_http_trace("cancel.jsonl")
    print("POSTs:", ", ".join(e["request"]["method"] for e in exchanges))
    kinds = [m.get("method", "result") for m in exchanges[-1]["messages"]]   # a response has no method, so it counts as the result
    print("tools/call stream:", "finished" if exchanges[-1]["complete"] else "closed by the client")
    print("tools/call messages:", kinds.count("notifications/progress"), "progress,", kinds.count("result"), "result")


anyio.run(main)
```

Output:

```text
server saw: cancelled with 5 of 64 recounted
recounts asked of the API: 6
POSTs: server/discover, tools/call
tools/call stream: closed by the client
tools/call messages: 5 progress, 0 result
```

The tool stopped when the stream closed. The server saw the call cancelled with 5 of 64 recounted, and the tool had asked the shop's API for 6 recounts. Cancellation reached the tool while it waited for the sixth, so the remaining products never went to the API.

On the wire there were two POSTs, server/discover, tools/call, so no cancellation message crossed it. The tool call's stream was closed by the client, and it carried 5 progress, 0 result. The client gets no result for a cancelled call, and the server sends none.

Two things undo this. With `json_response=True`, the SDK's JSON path has no disconnect watcher, so a closed connection never reaches the handler, and the handler runs to the end (`mcp/server/_streamable_http_modern.py`). And a stream that breaks for any other reason, such as a proxy timing it out, cancels the request in the same way. Streams can't be resumed at the pinned revision, so the client MUST send the request again with a new request ID ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)). A tool that a broken stream can interrupt must be safe to run twice, and the recount is, because counting again gives the same count. For a recount that must survive the client going away, [Start a task instead of waiting](#start-a-task) moves it into a task.

Timeouts sit on top of cancellation. The [cancellation](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation) pattern says a sender SHOULD set a timeout for each request, MAY reset it when progress arrives, and SHOULD always enforce a maximum. `Client(read_timeout_seconds=...)`, and the same argument on `call_tool`, give that limit, and running out of time cancels the call by closing its stream (`mcp/client/streamable_http.py`).

**Working rule:** Cancel a call over Streamable HTTP by cancelling the task that awaits it, or with a timeout, and let the SDK close the stream. Write long tools as `async def`, re-raise cancellation, and put any awaited cleanup under a shielded scope. Make every tool that runs for long safe to retry, because a broken stream loses the call and the client sends it again.

## Run replicas without sticky sessions {#scale-without-sessions}

Every example so far, including the cancelled recount in [Cancel a call the client no longer needs](#cancel-a-call), ran one server process. The support team needs more than one, so that a restart or a slow recount doesn't stop every host. A load balancer in front of two replicas sends each request wherever it likes. With 2025-era sessions, that required **sticky sessions**, which route every request carrying the same `Mcp-Session-Id` to the replica that held the session. The pinned revision has no sessions, so any replica can serve any request. A server that needs state across calls mints an explicit handle instead, and the client passes it back as an ordinary argument ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)).

The protocol keeping no state doesn't mean the application keeps none. The shop's server holds three kinds of state that a second replica doesn't see:

- **The key that seals `requestState`.** The refund confirmation from [Return an input request instead of a result](#return-an-input-request) sends the client a sealed `requestState` and opens it on the retry. By default `MCPServer` seals with a key that each process makes when it starts, and the state also names the server's name as its audience (`mcp/server/request_state.py`).
- **The handles the tools mint.** Chapter 3's quote store keeps each `quote_id` in the memory of the process that made it, as [What goes wrong in production](#design-tools-in-production) in chapter 3 warned.
- **The record of answered confirmations.** `confirmations.OnceOnly`, from [Keep round-trip state tamper-proof](#round-trip-state), remembers each answered `requestState` in one process's memory.

One refund, asked for on replica a and confirmed on replica b, touches all three kinds of state. Two replicas of chapter 5's refund server, each a process on its own port with one shop API behind both, run it. `lib.http_mcp.load_server` loads the server that `refund-asks-to-confirm.py` defines, and each replica runs it over HTTP. One client connects to each replica, and both read order O-1873. Then the client on replica a quotes a refund for order O-2289, whose amount is above the policy's limit, and replica a asks for confirmation. The retry with the support lead's yes goes to replica b, as a load balancer might send it. The sequence runs three times, fixing one kind of state each time:

1. each replica makes its own key;
2. both replicas read one key from `SHOP_REQUEST_STATE_KEY`, through `confirmations.state_security()`;
3. both also keep their quotes and their answered confirmations in one shared store, a SQLite file named by `SHOP_STATE_STORE`, and the client then sends the same answer a second time, to replica a.

The shared store is `lib.shared_state`. Its `SharedMap` and `SharedSet` keep entries in a SQLite file that every process on the machine opens, and each carries a lock on a file beside it, so that one replica's check-then-write can't interleave with another's. `shop_tools.create_server(quotes=...)` and `confirmations.OnceOnly(seen=...)` take any such container, and fall back to process memory without one, so chapters 3 and 5 run as before. Rows hold JSON, not pickles, and a quote's expiry is stored as a wall-clock time, because a monotonic deadline means nothing on another host. A SQLite file reaches only processes on one machine. A deployment puts the same two tables in a database its replicas share.

Example `two-replicas-one-client` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Runs two replicas of chapter 5's refund server through three kinds of shared state, and replays one confirmation across them.
The point rests on the retry and replay lines: each shared kind of state removes one way the second replica fails."""
import asyncio
import re
import sys
import tempfile

from mcp import Client, MCPError

from lib import confirmations, http_mcp, loopback, shared_state, shop_api

SHARED_KEY = "chapter-6-test-key-not-a-secret-0123456789"             # at least 32 bytes; a deployment reads its own
YES = {"action": "accept", "content": {"release": True}}              # the support lead's answer, as on the wire


async def outcome(call) -> str:                                       # refund status, tool error or protocol error
    try:
        result = await call
    except MCPError as error:
        return f"error {error.error.code} {error.error.message}"
    # keeps only the error's first sentence, which names the cause
    text = result.content[0].text.split(". ")[0] if result.is_error else result.structured_content["status"]
    return re.sub(r"Q-[0-9a-f]{10}", "Q-…", text)                    # quote IDs are random


async def refund_across(label: str, env: dict) -> None:
    with http_mcp.launch(__file__, env=env) as url_a, http_mcp.launch(__file__, env=env) as url_b:
        async with Client(url_a, elicitation_callback=confirmations.say_yes) as on_a, \
                Client(url_b, elicitation_callback=confirmations.say_yes) as on_b:
            print(f"{label} reads on a and b:", ", ".join([(await c.call_tool("get_order_status", {
                "order_id": "O-1873"})).structured_content["status"] for c in (on_a, on_b)]))
            quoted = await on_a.call_tool("quote_refund", {"order_id": "O-2289"})       # above the policy's limit
            args = {"quote_id": quoted.structured_content["quote_id"]}
            # allow_input_required lets the server answer with an input request, not a result, when it needs confirmation
            first = await on_a.session.call_tool("issue_refund", args, allow_input_required=True)   # asks on a
            # the answer goes back with the request state the server sealed, which the retry must open
            answer = dict(input_responses={"confirm": YES}, request_state=first.request_state)
            print(f"{label} retry on b:", await outcome(on_b.session.call_tool("issue_refund", args, **answer)))
            if shared_state.STORE_VARIABLE in env:                    # only the shared-store run sends the answer a second time
                print(f"{label} replay on a:", await outcome(on_a.session.call_tool("issue_refund", args, **answer)))


async def main() -> None:
    with loopback.serve(shop_api.create_app()) as api_url, tempfile.TemporaryDirectory() as shared:
        env = shop_api.server_env(api_url)                            # one shop API behind both replicas
        keyed = {**env, confirmations.STATE_KEY_VARIABLE: SHARED_KEY}
        await refund_across("own keys", env)                          # each process makes its own key
        await refund_across("shared key", keyed)
        await refund_across("shared store", {**keyed, shared_state.STORE_VARIABLE: f"{shared}/state.db"})


if "--serve" in sys.argv:                                             # one replica: chapter 5's server, over HTTP
    http_mcp.load_server("refund-asks-to-confirm.py").run(transport="streamable-http", port=http_mcp.port())
else:
    asyncio.run(main())
```

Output:

```text
own keys reads on a and b: delivered, delivered
own keys retry on b: error -32602 Invalid or expired requestState
shared key reads on a and b: delivered, delivered
shared key retry on b: Error executing tool issue_refund: There is no quote Q-…
shared store reads on a and b: delivered, delivered
shared store retry on b: requested
shared store replay on a: Error executing tool issue_refund: Refund R-0113 was already confirmed
```

With their own keys, both reads worked (delivered, delivered), but the retry failed: error -32602 Invalid or expired requestState. Replica b couldn't open a state that replica a sealed, so the SDK refused the retry before the tool ran.

With one shared key, replica b opened the state, and the call failed one step later, inside the tool: "Error executing tool issue_refund: There is no quote Q-…" The quote lived in replica a's memory. The shared key fixed the first kind of state and exposed the second.

With the shared store as well, the retry on replica b released the refund, and its status became requested. Replica b found replica a's quote in the shared store, and with it the refund the shop's API already held, so it released that refund without asking for a second one. The same answer sent again to replica a was refused: "Error executing tool issue_refund: Refund R-0113 was already confirmed" Replica a had never seen the first answer. Without the shared record, its own `OnceOnly` check would have passed, and it would have asked the shop's API to release the refund again. Only the API's 409 for a refund it no longer holds would have stopped it. The refund completed once, across two replicas, with no sticky sessions. The specification asks for opaque, expiring handles ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)). Where their state lives is the server's choice, but with replicas it must be somewhere every replica reaches.

A deployment that hasn't moved some state yet can use a stopgap from the routing headers in [Read one HTTP exchange](#http-on-the-wire). It isn't stickiness: a gateway sends every request whose `Mcp-Name` names a tool that depends on that state to one replica, and spreads the rest. A `subscriptions/listen` stream is held by one replica, and the SDK ships only an in-memory bus, so events published on another replica never reach it ([deploy and scale](https://py.sdk.modelcontextprotocol.io/v2/run/deploy/); `mcp/server/subscriptions.py`, `InMemorySubscriptionBus`).

**Working rule:** Run replicas with no sticky sessions, and give every replica the same server name and the same `requestState` keys, injected from your secret store. Before you add a second replica, list every piece of state your tools keep in memory, such as handles, once-only records and subscriptions, and move each into storage that every replica reaches. Until one is moved, route the tools that depend on it to a single replica by `Mcp-Name`.

## Reject requests from other origins {#validate-origin}

The replicas in [Run replicas without sticky sessions](#scale-without-sessions) listen on 127.0.0.1, which feels private. It isn't. Any web page open in a browser on the same machine can send requests to a loopback port. With **DNS rebinding**, an attacker's domain can be made to resolve to 127.0.0.1 after the page loads, so the browser treats the local server as part of the attacker's site. The specification's tutorial on local servers says that binding to 127.0.0.1 "is not an authentication boundary" ([local server security](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security)).

The browser hands the server its defence. It sends the page's `Origin` with each request it makes on the page's behalf. The [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) in the specification says servers MUST validate `Origin` on every incoming connection, MUST answer 403 when it is present and invalid, and SHOULD bind to 127.0.0.1 when they run locally. Checking `Host` as well stops the rebinding case, where the browser names the attacker's domain.

The SDK arms both checks by default. When the app's `host` is a loopback name and you pass no `transport_security`, it allows only `Host` values `127.0.0.1:*`, `localhost:*` and `[::1]:*`, and only `Origin` values with the same names under `http://` (`mcp/server/mcpserver/server.py`). Four requests probe that default: `tools/list` with no `Origin`, with the server's own origin, with `http://attacker.example`, and with a `Host` of `fernhill.example`. It then builds the same app with `host="0.0.0.0"`, the usual container setting, and sends the two foreign requests again. That app binds to 127.0.0.1, since only the setting is under test.

Example `reject-a-foreign-origin` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Sends tools/list to the shop's server with foreign Origin and Host headers, first with the SDK's loopback default and then
with host="0.0.0.0". The point rests on the foreign Origin and foreign Host lines: the default answers 403 and 421, and the
0.0.0.0 app answers 200 to both."""
from urllib.parse import urlsplit

from lib import http_mcp, loopback

server = http_mcp.load_server("serve-on-loopback.py")             # chapter 3's five tools
FOREIGN = "http://attacker.example"                                # a page in the user's browser, on another site


def probe(label: str, url: str, headers: dict[str, str]) -> None:
    response = http_mcp.post(url, "tools/list", headers=headers)
    print(f"{label}:", response.status_code, response.text if response.status_code != 200 else "tools listed")


def main() -> None:
    with loopback.serve(server.streamable_http_app()) as base_url:             # host defaults to 127.0.0.1
        # the server's own origin: loopback and the port it listens on, as a page served from it would send
        url, own = base_url + "/mcp", f"http://127.0.0.1:{urlsplit(base_url).port}"
        probe("no Origin", url, {})
        probe("own Origin", url, {"Origin": own})
        probe("foreign Origin", url, {"Origin": FOREIGN})
        probe("foreign Host", url, {"Host": "fernhill.example"})         # a Host the loopback allowlist does not name
    with loopback.serve(server.streamable_http_app(host="0.0.0.0")) as base_url:   # still bound to 127.0.0.1
        probe("0.0.0.0 app, foreign Origin", base_url + "/mcp", {"Origin": FOREIGN})
        probe("0.0.0.0 app, foreign Host", base_url + "/mcp", {"Host": "fernhill.example"})


main()
```

Output:

```text
no Origin: 200 tools listed
own Origin: 200 tools listed
foreign Origin: 403 Invalid Origin header
foreign Host: 421 Invalid Host header
0.0.0.0 app, foreign Origin: 200 tools listed
0.0.0.0 app, foreign Host: 200 tools listed
```

The loopback default turned away both foreign requests. A request with no `Origin` got 200 tools listed, and so did the server's own origin: 200 tools listed. The foreign origin got 403 Invalid Origin header, and the foreign host got 421 Invalid Host header, both as plain text rather than JSON-RPC (`mcp/server/transport_security.py`). The specification allows a body of either kind with the 403.

Built with `host="0.0.0.0"`, the app let both through: 200 tools listed and 200 tools listed. A host the SDK doesn't recognise as loopback only stops it arming the default, and with no settings passed, the check is off (`mcp/server/transport_security.py`). That falls short of the specification's MUST, and nothing in the logs says so.

The request with no `Origin` shows what this defence covers. Browsers send `Origin`, while scripts, command-line tools and other servers don't, and the SDK lets a request without one through. Origin validation protects a server from web pages. It does nothing against a program that can reach the port, which is what authorization is for ([Authorize clients with OAuth](#authorization)).

**Working rule:** Keep the SDK's loopback default on a developer's machine. When you deploy on any other address, pass `transport_security=TransportSecuritySettings(allowed_hosts=[...], allowed_origins=[...])` with the names your server answers to, such as `mcp.fernhill.example`, and never rely on the default. Treat Origin validation as protection against browsers only, and put authorization in front of every server that anything but its own host can reach.

## Choose stdio or Streamable HTTP {#stdio-or-http}

The sections before this one moved the shop's server onto Streamable HTTP. The work that move took, from cancellation to replicas to origin checks, is the price of moving. stdio has none of it. The [stdio transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio) in the specification has the client launch the server as a subprocess and exchange messages on its standard input and output. The host owns the process, so nothing else can reach it, the server inherits only what the host passes, and it lives as long as the host needs it.

The transports differ in who runs the server, and in what follows from that:

| | stdio | Streamable HTTP |
| --- | --- | --- |
| Started by | the host, one per host | you, once for many hosts |
| Reachable by | its own host | anything that reaches the address |
| Cancel | `notifications/cancelled` | close the response stream |
| Logs | standard error | your server's logs |
| Credentials | the host's environment | OAuth access tokens |
| Scales by | one process per host | replicas behind a load balancer |

We recommend stdio for a server that works for one user on that user's machine, such as one reading local files or using the user's own credentials, and for development. We recommend Streamable HTTP when several hosts share one server, when the server must run next to systems that the hosts can't reach, such as the shop's API inside its network, or when you need to deploy, scale and watch the server as a service. Then plan for authorization from the start, because a server on an address needs to know who is calling ([Find the authorization server from the resource](#protected-resource-metadata)).

With many hosts, the shop's API shouldn't be reachable from the support team's laptops, so the server moves to Streamable HTTP. The book keeps stdio for examples that need only one host and one server, because a subprocess is the shortest way to run one.

**Working rule:** Ship a server over stdio when it acts for one user on that user's machine. Ship it over Streamable HTTP when it serves several hosts, guards systems the hosts can't reach, or must scale, and give it origin checks and authorization before its first external user. The same server code can serve both, so choose per deployment, not per server.

## What goes wrong in production {#streamable-http-in-production}

The shop's server works on loopback with one client at a time. Behind real proxies, load balancers and clients it breaks in ways loopback never shows; here is each, with what it looks like.

**Every request gets 421.** The deployment kept the SDK's loopback allowlist, and requests arrive with the server's public name in `Host`. The sign is `Invalid Host header` in plain text on every call and nothing in the tool logs. Pass `allowed_hosts` with the names the server answers to ([Reject requests from other origins](#validate-origin)).

**The checks are off without anyone deciding.** A server started with `host="0.0.0.0"`, the usual container setting, accepts every `Host` and `Origin` (`mcp/server/transport_security.py`). Nothing fails, so the only sign is a probe like `reject-a-foreign-origin` getting 200. Run that probe against each deployment, and set `transport_security` explicitly.

**Progress arrives all at once.** A proxy that buffers the response holds back every notification until the result. The SDK sends `X-Accel-Buffering: no`, the header the specification names for this, but proxies and CDNs that ignore it have settings of their own. A progress bar that jumps from nothing to done gives it away. Test progress through the real path, not on loopback.

**Long calls die at a round number of seconds.** Proxies and load balancers close idle connections after a fixed time. Once a stream is open, the SDK sends a `: ping` comment after every 15 seconds without another event, to keep it busy (`mcp/server/_streamable_http_modern.py`). A proxy with a shorter idle limit, or a total limit per request, still cuts the stream, and the cut cancels the tool. Look for cancellations clustered at one duration. Raise the proxy's limits for the MCP path, or move the work into a task ([Start a task instead of waiting](#start-a-task)).

**A retry runs the work twice.** A broken stream can't be resumed, and the client sends the request again with a new ID ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)). A tool that isn't safe to repeat does its side effect twice. The shop's `issue_refund` is safe because a quote refunds once, and with the shared store that holds on every replica. Give every tool with a side effect a handle or a key that makes the second call return the first call's result, and keep that record where every replica sees it.

**`json_response=True` silences progress and cancellation.** It is tempting behind a gateway that dislikes event streams, and the SDK gives no warning ([Stream progress on a long call](#stream-progress)). It shows up as long calls that never report and keep running after clients leave.

**A gateway rewrites the body.** A gateway that edits JSON bodies but not headers makes requests fail with -32020, `HeaderMismatch`. The SDK's client resends once after fetching the tool list, so you'll see doubled `tools/call` requests and a steady trickle of -32020 in the server's responses.

**Clients on a 2025 revision need sessions.** The same app serves 2025-era clients through the old handshake, and by default it holds their sessions in one process's memory, which requires sticky routing (`mcp/server/streamable_http_manager.py`). Watch for `404` with "Session not found" from those clients only, after a request lands on another replica (`mcp/server/streamable_http_manager.py`). Set `stateless_http=True` if you serve them behind a load balancer, and know what it costs: those clients lose cancellation, so their handlers run to the end whatever the client did ([cancellation](https://py.sdk.modelcontextprotocol.io/v2/handlers/cancellation/)), and they lose server-to-client requests such as sampling and elicitation ([deploy and scale](https://py.sdk.modelcontextprotocol.io/v2/run/deploy/)). [Serve old and new clients through the window](#serve-both-revisions) weighs the trade.

**Large requests fail with 413.** The SDK caps a request body at 4 MiB by default (`mcp/server/transport_security.py`). A tool that takes a document as an argument hits it first. Raise `max_request_body_size` for that server, or pass a reference to the document instead of its bytes.

**Working rule:** Before the shop's server takes traffic on an address, test four things through the real proxy path: a foreign `Origin` gets 403, progress arrives while the call runs, a call longer than the proxy's idle limit survives, and closing a call's stream stops the tool. Then watch 421, 403 and -32020 by client, and cancellations by duration.

## Decisions this chapter made {#streamable-http-decisions}

- **The shop's server moves to Streamable HTTP** for the support team's hosts, with chapter 3's tools unchanged. stdio stays for examples with one host and one server.
- **`MCPServer.run(transport="streamable-http")` with the SDK's defaults:** loopback, path `/mcp`, and the default response mode, which streams. `stateless_http` stays unset until 2025-era clients need serving behind a load balancer, and then costs them cancellation.
- **`json_response=True` is never used,** because it drops progress and cancellation.
- **`recount_stock` reports progress after each product,** with a total and a message, and is safe to run twice.
- **Cancellation is a closed stream.** Long tools are `async def`, re-raise cancellation, and shield any awaited cleanup.
- **Replicas share their server name and `requestState` keys** through `SHOP_REQUEST_STATE_KEY`, and their quotes and answered confirmations through one shared store, `SHOP_STATE_STORE`. Every request, refunds included, runs on any replica. The examples' store is a SQLite file of JSON rows with wall-clock expiry; a deployment uses a database its replicas share.
- **Origin and Host checks stay on.** On any address but loopback, `transport_security` lists the server's names explicitly. Authorization, not Origin, keeps out callers that aren't browsers.
- **Gateways may route on `Mcp-Method` and `Mcp-Name`,** because the server rejects a request whose headers disagree with its body. No gateway rewrites a body.
- **HTTP traces come from `lib.wire.record_http`,** and hand-written requests from `lib.http_mcp.post`, only to show errors the SDK's client would never cause.
- **Examples run replicas as separate processes,** so that each has its own memory and its own key, as in a deployment.
