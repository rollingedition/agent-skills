---
title: "Model Context Protocol in Practice"
chapter: "What MCP adds to an API"
chapter_id: what-mcp-adds
book: model-context-protocol-in-practice
edition: 2026.11.11
verified: 2026-11-14
edition_code: 2VMD-DEEC
canonical: https://rollingedition.com/model-context-protocol-in-practice/what-mcp-adds
license: CC BY 4.0
attribution: "“What MCP adds to an API,” chapter 2 of Model Context Protocol in Practice, Edition 2026.11.11, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/model-context-protocol-in-practice/what-mcp-adds. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# What MCP adds to an API

By the end of this chapter you can say what the host, the client and the server each do, put each of the shop's capabilities in the right Model Context Protocol primitive, read the version and capabilities that every request carries, and decide when the shop should keep a plain HTTP API instead. Its claims and examples are tied to revision 2026-07-28 of the specification and to `mcp`, the Python SDK, at version 2.3.0.

What this chapter needs from [the shop](#the-shop), Fernhill Supply's fictional online store for kitchen and garden goods, is an HTTP API whose order lookup the support team's host already uses. [MCP end to end](#mcp-end-to-end) put that lookup behind a Model Context Protocol (MCP) server, so that a model in the support team's host could call it. That server had one tool. The support team wants more: the refund policy, which the host should have at hand whenever a ticket mentions money, and a standard way to review a refund request. Meanwhile the warehouse team, which reads stock levels from the same API every night, asks whether it should move to MCP too.

Both questions turn on what MCP adds to an API that already works. An HTTP client is written against endpoints its developer read about. An MCP client learns at run time what a server offers, in a form a model can read, and the protocol says who decides when each capability is used. This chapter takes those additions one at a time, measures what they cost on the wire, and ends with where the shop shouldn't pay for them.

## Separate the host, the client and the server {#host-client-server}

The server from [Wrap one endpoint as a tool](#wrap-an-endpoint-as-a-tool) ran behind a client that the code in that chapter drove. Before the shop adds more to it, be exact about which part does what, because MCP's guarantees attach to the roles, not the processes.

The specification names three roles ([architecture](https://modelcontextprotocol.io/specification/2026-07-28/architecture)). The **host** is the application the user works in. It creates clients, holds the conversation with the model, and enforces security policies and consent. A **client** is the host's connection to one server: "Each client is created by the host and communicates with exactly one server". A **server** exposes capabilities, such as tools, and knows nothing else about the host. The same page sets a design principle that follows from that split: a server should not see the whole conversation, nor look into other servers. The host decides what each server sees, and anything that crosses servers happens in the host.

The support team's host plays the host role and runs the book's host loop. Each server it uses gets its own client: in this chapter one, `shop-support`, and in [Catch poisoned tool descriptions](#tool-poisoning) a second server from a partner, which must never learn what the shop's server returned. `shop-support` is this chapter's server. It keeps chapter 1's `get_order_status` tool and adds a resource, the refund policy, and a prompt, `review_refund`, so that each kind of capability appears once. Like every server example here, the file defines the server and, run with no arguments, starts a client that launches it with `--serve`.

The first thing a client does is ask the server what it offers. A **capability** is something a client or server declares it supports, such as a server that offers tools or a client that can answer a request for input. At the pinned revision that takes one request, `server/discover`, whose answer holds the versions the server supports, its capabilities and its name, so a client can show everything a server supports from that one answer ([discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)). The client then lists each kind of capability with `tools/list`, `resources/list` and `prompts/list`. In its default auto mode, `mcp.Client` sends `server/discover` when it opens, and keeps the answer as `client.session.discover_result` (`mcp/client/session.py`).

Example `list-what-the-server-offers` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""shop-support, the chapter 2 server, offers one tool, one resource and one prompt. Run bare, the file starts it as a
client, which prints what it discovers: the tools, resources and prompts lines are the ones the prose reads."""
import asyncio
import os
import sys

import httpx2
from mcp import Client, StdioServerParameters
from mcp.server.caching import CacheHint
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from lib.policies import policy

# ttl_ms is in milliseconds, so 300_000 is five minutes; "public" lets a shared cache reuse the tool list.
server = MCPServer("shop-support", version="0.2.0",
                   cache_hints={"tools/list": CacheHint(ttl_ms=300_000, scope="public")})


@server.tool()
def get_order_status(order_id: str) -> dict:
    """Look up one of the shop's orders by its ID, such as O-1873: its status, dates, lines and total."""
    response = httpx2.get(f"{os.environ['SHOP_API_URL']}/orders/{order_id}",
                          headers={"X-API-Key": os.environ["SHOP_API_KEY"]}, timeout=5.0)   # timeout in seconds
    if response.status_code == 404:
        raise ToolError(f"The shop has no order {order_id}. Order IDs look like O-1873.")
    response.raise_for_status()
    return response.json()


@server.resource("shop://policies/refund", name="refund-policy", mime_type="text/markdown")
def refund_policy() -> str:
    return policy("refund").path.read_text(encoding="utf-8")       # examples/data/shop/policies/refund.md


@server.prompt()
def review_refund(order_id: str) -> str:
    """Review a customer's refund request for one order against the shop's refund policy."""
    return (f"Review the refund request for order {order_id}. Look up the order with get_order_status, read the "
            "refund policy at shop://policies/refund, and say whether the refund needs a person to confirm it.")


async def main() -> None:
    # No variables are passed: listing never calls the tool, so the server needs none of the shop's API settings.
    async with Client(StdioServerParameters(command=sys.executable, args=[__file__, "--serve"], env={})) as client:
        print("server:", client.server_info.name, client.server_info.version)
        print("protocol revision:", client.protocol_version)
        # auto mode keeps the server/discover answer on the session, so the versions come from there
        print("supported versions:", ", ".join(client.session.discover_result.supported_versions))
        # exclude_none drops the capabilities the server didn't declare, leaving only the ones it offers
        print("capabilities:", ", ".join(sorted(client.server_capabilities.model_dump(exclude_none=True))))
        print("tools:", ", ".join(t.name for t in (await client.list_tools()).tools))
        print("resources:", ", ".join(str(r.uri) for r in (await client.list_resources()).resources))
        print("prompts:", ", ".join(p.name for p in (await client.list_prompts()).prompts))


if __name__ == "__main__":
    # With --serve this file is the server the client launches; run bare, it is the client.
    server.run() if "--serve" in sys.argv else asyncio.run(main())
```

Output:

```text
server: shop-support 0.2.0
protocol revision: 2026-07-28
supported versions: 2026-07-28
capabilities: prompts, resources, tools
tools: get_order_status
resources: shop://policies/refund
prompts: review_refund
```

The client's code never names any of the three. It learned them from the server, along with the server's own name, shop-support 0.2.0, the revision it supports, 2026-07-28, and the capabilities it declares, prompts, resources, tools, printed beside the example. That is the first thing MCP adds to the shop's API: a client that knows nothing about the shop can find out what the shop offers, with a description of each item and, for tools and prompts, the arguments they take, and a host can put those in front of a model. The server also sets a cache hint on its tool list, which [Cache list results](#cache-list-results) explains.

**Working rule:** Give each server its own client in the host, and keep the conversation and anything that crosses servers in the host's code, never in a server. Start every client by reading what the server offers rather than assuming it, so that a server that changes its tools doesn't break the host. When you write a server, assume it sees only the requests sent to it, because that is all the specification lets it see.

## Put each capability in the right primitive {#choose-a-primitive}

The `shop-support` server from [the previous section](#host-client-server) offers one tool, one resource and one prompt. These are a server's three primitives, and they differ less in what they return than in who decides when they're used. The specification's server overview puts it in a table: prompts are user-controlled, resources are application-controlled, and tools are model-controlled ([server features](https://modelcontextprotocol.io/specification/2026-07-28/server)). So the question to ask of each capability is not whether it reads or writes, but who should decide when it runs: the model, the host's own code, or the person at the desk.

The [tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) page mandates no particular interface for a tool. The [resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources) and [prompts](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts) pages do the same for their primitives. A host can show them however it likes, but one that respects the control model gives each to the party the table names. The next script uses each of `shop-support`'s three once, the way a host would.

Example `three-primitives-side-by-side` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Use each of shop-support's three primitives once, as a host would: the tool for the model, the resource for the
host's code, the prompt for the person at the desk. The prose quotes the order's status, the policy's first line and
the prompt's one required argument."""
import asyncio
import json
import sys

from mcp import Client, StdioServerParameters

from lib import loopback, shop_api


async def main() -> None:
    with loopback.serve(shop_api.create_app()) as base_url:
        # the server from list-what-the-server-offers, run as its own process with --serve; its env points at the shop's API
        params = StdioServerParameters(command=sys.executable, args=["list-what-the-server-offers.py", "--serve"],
                                       env=shop_api.server_env(base_url))
        async with Client(params) as client:
            # A tool: the host lists it for the model, and calls it when the model asks.
            result = await client.call_tool("get_order_status", {"order_id": "O-2476"})
            assert result.is_error is False      # the lookup must succeed for the prose's claim
            # a tool's result is a list of content blocks; the order arrives as JSON text in the first one
            print("tool says order status:", json.loads(result.content[0].text)["status"])

            # A resource: the host reads it when its own code decides the model needs it.
            policy = (await client.read_resource("shop://policies/refund")).contents[0]   # this server returns one item
            print("resource type:", policy.mime_type)
            print("resource first line:", policy.text.splitlines()[0])

            # A prompt: the host shows it to the user, who picks it and fills in its arguments.
            listed = (await client.list_prompts()).prompts[0]     # the first prompt, the only one shop-support offers
            print("prompt arguments:", "; ".join(f"{a.name}, {'required' if a.required else 'optional'}"
                                                 for a in listed.arguments))
            prompt = await client.get_prompt("review_refund", {"order_id": "O-2476"})
            print("prompt messages:", len(prompt.messages))
            print("prompt role:", prompt.messages[0].role)
            print("prompt starts:", prompt.messages[0].content.text[:44] + "…")   # 44 characters: enough to name the order


asyncio.run(main())
```

Output:

```text
tool says order status: shipped
resource type: text/markdown
resource first line: # Refund policy
prompt arguments: order_id, required
prompt messages: 1
prompt role: user
prompt starts: Review the refund request for order O-2476. …
```

### Tools are actions the model chooses {#tools-model-chooses}

A **tool** is a named action with a description and an input schema, and the model decides whether to call it and with what ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)). The host lists the tools for the model and runs the calls it asks for. The lookup of order O-2476 succeeded without an error, and the order's status came back as `shipped`.

A lookup belongs here because the ticket decides whether it's needed. One customer quotes an order ID and asks where the parcel is; another asks whether a frying pan comes in 28 cm. Only something that reads the ticket can choose, and in this host that is the model. [Let a model choose the tool](#let-a-model-choose) showed the model making that choice on a recording.

**Working rule:** Make a capability a tool when the model should decide, from the conversation, whether to use it. That covers lookups that depend on what the customer wrote, and every action that changes something, such as a refund, for which the host then asks for consent before the call.

### Resources are data the application chooses {#resources-application-chooses}

A **resource** is data a server exposes under a URI, and the application decides when to read it and what to do with it ([resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)). The host might attach a resource to the model's context, show it to the user or index it. `shop-support` serves the shop's refund policy, one of the short policy documents written for the book, under `shop://policies/refund`. Reading it returned `text/markdown` text, whose first line is `# Refund policy`.

The refund policy is a resource because the shop knows in advance when it matters: on every ticket about money. The host's code can attach it to the model's context for those tickets without asking the model. As a tool, it would depend on the model remembering to fetch it, and cost a turn each time. A resource is not the same as a read-only tool: both return data, but a resource's reader is the host's code, and its result can be cached under the rules in [Cache list results](#cache-list-results). [Expose the policies as resources](#policies-as-resources) serves the rest of the shop's policies the same way.

**Working rule:** Make data a resource when the host's own code can tell when it's needed, such as a policy that applies to a known kind of ticket, or a record the user has opened. Keep it a tool when only the model, reading the conversation, can tell whether it's needed.

### Prompts are templates the user chooses {#prompts-user-chooses}

A **prompt** is a template of messages, with arguments, that the server defines and the user picks ([prompts](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)). The specification is precise about the word: "user-controlled" refers to "who decides when the prompt is used, not who authors its content". The server writes the content, and a host typically offers prompts in a menu or as commands. `review_refund` takes one argument, `order_id, required`. Filled in for order O-2476, it returned 1 message from the `user` role, beginning "Review the refund request for order O-2476. …".

`review_refund` is a prompt because a person on the support team decides to start a refund review, usually after reading the ticket, and the shop wants every review to follow the same steps. The prompt's text names the tool and the resource the review needs, so the model starts from the policy and the order, not a guess. A prompt isn't a system prompt the user writes: the shop writes it once, on the server, and every host that connects gets the same text. [Package a workflow as a prompt](#workflows-as-prompts) grows `review_refund` into the full review, with the refund amount as a second argument.

**Working rule:** Make a workflow a prompt when a person should start it and every run should follow the same steps, and keep the prompt's text on the server so that a change reaches every host at once. If no person chooses when it runs, it isn't a prompt: make the steps a tool, or put them in the host's own instructions.

## Carry the version and capabilities on every request {#request-meta}

The client in [Put each capability in the right primitive](#choose-a-primitive) made three calls, and the server answered each one without remembering the others, by design. At the pinned revision there's no handshake: every request carries, in its `_meta` field, the protocol version and the client's capabilities, and those fields "MUST be included on every request" ([base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic)). Each request should also carry the client's name and version, and each result the server's.

Three rules on the same page shape how the shop's server uses these fields:

- A request without a required field is rejected with JSON-RPC error `-32602` (invalid params), and over HTTP with status 400.
- A server must not rely on a capability the client didn't declare on that request. If it needs one, it answers with error `-32021`, whose data lists the missing capabilities.
- `clientInfo` and `serverInfo` are self-reported. Implementations "SHOULD NOT rely on them for security decisions", so the shop's server never treats the client's name as an identity.

`_meta` also carries keys of your own, under a reverse-DNS prefix that ends in `/`. A prefix whose second label is `modelcontextprotocol` or `mcp` is reserved for the protocol, and so are `traceparent`, `tracestate` and `baggage`, which belong to OpenTelemetry ([base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic)). The shop's domain is `fernhill.example`, so its keys start with `example.fernhill/`.

To see the envelope, the client calls `get_order_status` through `lib.wire`, which logs every line between the client and the server. It passes one key of the shop's own, a request ID that support staff can quote. It then sends a `tools/list` request without the client's capabilities, through a second small module, `lib.raw_stdio`, which starts a stdio server and writes JSON-RPC lines by hand. The code needs that because `mcp.Client` never sends a malformed request.

Example `request-meta-on-the-wire` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Show the _meta that every request and result carries, add one key of the shop's own, and send a request without
the client's capabilities. The prose's claims about the envelope come from the printed keys and the bare request's error code."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.types import Implementation

from lib import byte_meter, loopback, raw_stdio, shop_api, wire

COMMAND = [sys.executable, "list-what-the-server-offers.py", "--serve"]


async def main() -> None:
    Path("meta.jsonl").unlink(missing_ok=True)       # the relay appends to its log
    with loopback.serve(shop_api.create_app()) as base_url:
        server = StdioServerParameters(command=COMMAND[0], args=COMMAND[1:], env=shop_api.server_env(base_url))
        # the relay logs every line the client and server exchange, so the byte counts are of lines as sent
        async with Client(wire.relay(server, log="meta.jsonl"),
                          # the name and version the SDK sends as clientInfo in _meta; the server must not rely on them
                          client_info=Implementation(name="shop-host", version="0.1.0")) as client:
            # a key under the shop's own prefix, which the protocol leaves to the shop to define
            await client.call_tool("get_order_status", {"order_id": "O-2476"},
                                   meta={"example.fernhill/requestId": "req-0001"})
    trace = [message for _, message in wire.read_trace("meta.jsonl")]
    call = next(m for m in trace if m.get("method") == "tools/call")          # the first tools/call request in the log
    result = next(m for m in trace if m.get("id") == call["id"] and "result" in m)   # its response, with the same id
    for key, value in call["params"]["_meta"].items():
        print(f"request {key}:", json.dumps(value))
    for key, value in result["result"]["_meta"].items():
        print(f"result {key}:", json.dumps(value))
    lines = [json.loads(entry)["line"] for entry in Path("meta.jsonl").read_text(encoding="utf-8").splitlines()]   # as sent
    print("request _meta bytes:", byte_meter.meta_bytes(lines, call["params"]["_meta"]))
    print("result _meta bytes:", byte_meter.meta_bytes(lines, result["result"]["_meta"]))

    with raw_stdio.launch(COMMAND, env={}) as raw:          # the same request, without clientCapabilities
        # capabilities=None leaves clientCapabilities out of _meta: the request the server must reject
        reply = raw.request("tools/list", meta=raw_stdio.envelope("2026-07-28", capabilities=None))
        print("without capabilities, error code:", reply["error"]["code"])
        print("without capabilities, message:", reply["error"]["message"])


asyncio.run(main())
```

Output:

```text
request example.fernhill/requestId: "req-0001"
request io.modelcontextprotocol/protocolVersion: "2026-07-28"
request io.modelcontextprotocol/clientInfo: {"name": "shop-host", "version": "0.1.0"}
request io.modelcontextprotocol/clientCapabilities: {}
result io.modelcontextprotocol/serverInfo: {"name": "shop-support", "version": "0.2.0"}
request _meta bytes: 228
result _meta bytes: 88
without capabilities, error code: -32602
without capabilities, message: params._meta is missing the required envelope key(s): io.modelcontextprotocol/clientCapabilities
```

The shop's key travels beside the protocol's own. The `tools/call` request's `_meta` held four keys. The shop's `example.fernhill/requestId`, set to "req-0001", came first, and the SDK added the protocol's three after it: the version, "2026-07-28", then the client's name, version and capabilities, which the output prints, the capabilities empty because this client declares none. The result's `_meta` carried the server's name and version, also printed.

The request without capabilities failed with code -32602, and the SDK's message names the missing key: "params._meta is missing the required envelope key(s): io.modelcontextprotocol/clientCapabilities". A hand-written client, or a gateway that rewrites bodies and drops `_meta`, fails this way on its first request.

What this costs the shop is bytes on every message. Measured on the lines as sent, the request's `_meta`, with the shop's key, took 228 bytes, and the result's 88. They are part of the per-call overhead that [Keep an HTTP API where MCP adds nothing](#when-mcp-is-wrong) measures. What it buys is a server that needs no memory of earlier requests: any copy of `shop-support` can answer any request, which is what lets [Run replicas without sticky sessions](#scale-without-sessions) put two replicas behind one address.

**Working rule:** Read the version and the client's capabilities from each request, never from an earlier one, and answer `-32021` when a call needs a capability the request didn't declare. Put the shop's own request metadata under its own reverse-DNS prefix, never under `io.modelcontextprotocol/` or `mcp`. Log `clientInfo` and `serverInfo` for debugging, and decide nothing on them.

## Handle a version the server doesn't support {#version-mismatch}

Every request in [Carry the version and capabilities on every request](#request-meta) named its protocol version, so a server can meet, on any request, a version it doesn't implement. No negotiation step settles it in advance. A server that doesn't implement the requested version "MUST respond with an UnsupportedProtocolVersionError listing the versions it does support", error code `-32022`, with the supported versions and the requested one in its data. The client SHOULD pick a version from that list that both sides support, and retry, or else show the user an error ([versioning](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)). Over Streamable HTTP the version also travels in the `MCP-Protocol-Version` header, which must match the body, and an unsupported version gets status 400 ([Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)).

The shop meets this when a host built for a later revision connects to `shop-support`. Showing the error means sending a version the server doesn't know, and the obvious way fails first: `mcp.Client` accepts as its `mode` only `"auto"`, `"legacy"` or one of the SDK's per-request revisions, such as `2026-07-28`, and raises before it sends anything (`mcp/client/client.py`). So the script tries that first, then uses `lib.raw_stdio` from [the previous section](#request-meta) to write the request by hand. It asks for `2099-01-01`, a made-up revision that stands for any the server lacks, then retries with a version from the server's list.

Example `unsupported-version-error` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Ask shop-support for a revision it doesn't implement, read its -32022 error, and retry with the newest revision both
sides list. The prose reads the error code, the versions in its data and the retry's tool list from the printed lines."""
import sys

from mcp import Client, StdioServerParameters
from mcp_types.version import MODERN_PROTOCOL_VERSIONS

from lib import raw_stdio

COMMAND = [sys.executable, "list-what-the-server-offers.py", "--serve"]
UNKNOWN = "2099-01-01"                       # stands for any revision this server doesn't implement

try:
    # the SDK's client checks the mode when it is built, so this raises before anything is sent
    Client(StdioServerParameters(command=COMMAND[0], args=COMMAND[1:]), mode=UNKNOWN)
except ValueError as refused:
    print("client refuses:", type(refused).__name__)

with raw_stdio.launch(COMMAND, env={}) as server:
    # capabilities={} declares no client capabilities: the request is well formed, and only its version is unknown
    error = server.request("tools/list", meta=raw_stdio.envelope(UNKNOWN, capabilities={}))["error"]
    print("error code:", error["code"])
    print("error message:", error["message"])
    print("server supports:", ", ".join(error["data"]["supported"]))     # the server lists its versions in the error's data
    print("client asked for:", error["data"]["requested"])

    # the versions both sides know, in the order the SDK lists them
    mutual = [version for version in MODERN_PROTOCOL_VERSIONS if version in error["data"]["supported"]]
    if not mutual:
        sys.exit("no version in common: show the user an error instead of retrying")
    print("retry with:", mutual[-1])        # the last of that list is the newest version both sides know
    # the same process: at this revision each request names its own version, so the retry needs no new connection
    retry = server.request("tools/list", meta=raw_stdio.envelope(mutual[-1], capabilities={}))
    print("retry tools:", ", ".join(tool["name"] for tool in retry["result"]["tools"]))
```

Output:

```text
client refuses: ValueError
error code: -32022
error message: Unsupported protocol version
server supports: 2026-07-28
client asked for: 2099-01-01
retry with: 2026-07-28
retry tools: get_order_status
```

The SDK's client never reached the server: it refused the unknown mode before sending anything, with the error the output beside the example shows. The server's answer is what makes the retry possible. Given the raw request, it refused with the code and message the output prints, and its data listed the versions it supports, 2026-07-28, beside the one the client asked for. From that list the script picked 2026-07-28, the newest version both sides know, and the retry listed `get_order_status`. The retry went to the same process, because a connection carries no agreed version at the pinned revision, so the next request may name another one.

Two details of the SDK at 2.3.0 matter when you read this error from someone else's server. First, an SDK stdio server decides from the client's first request which era of the protocol to speak. A request whose `_meta` has a protocol version opens a connection at the pinned revision, even when the version is unknown, which is why this request got `-32022` instead of a demand for the 2025 `initialize` handshake (`mcp/server/runner.py`). Second, the server's `supported` list holds only the versions that use per-request `_meta`, although the same server still accepts 2025 clients through `initialize` (`mcp/shared/inbound.py`). The specification's own example of the error lists a 2025 revision as well; the SDK's list doesn't. The SDK's client, in its default auto mode, reads a `-32022` whose list shares nothing with its own as a real incompatibility, and any other error on its first request as a 2025 server that needs the old handshake (`mcp/client/_probe.py`). [Serve old and new clients through the window](#serve-both-revisions) covers that second path.

**Working rule:** When a server answers `-32022`, pick the newest version in both your list and its `supported` list, retry once, and show the user an error naming both lists if they share none. Don't retry in a loop, and don't guess a version the server didn't list. On your own server, keep the supported list exact, because clients choose from it.

## Cache list results {#cache-list-results}

The `server/discover` answer and the tool list in [Separate the host, the client and the server](#host-client-server) change only when the shop deploys, but a stateless client could ask before every model turn. Each result of `server/discover`, `tools/list`, `prompts/list`, `resources/list`, `resources/templates/list` and `resources/read` must carry two caching hints at the pinned revision ([caching](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching)):

- `ttlMs`, how many milliseconds the result stays fresh, like HTTP's `max-age`. Zero means stale at once.
- `cacheScope`, either `"public"`, which a cache may share across callers, or `"private"`, which it MUST NOT share across authorization contexts.

The same page limits what the hints mean. A TTL is a freshness hint, not a polling interval: a client checks freshness when it needs the data, and any polling must use jitter and backoff. A `list_changed` notification invalidates a cached result that is still fresh. And `cacheScope` is no access control: a server "MUST NOT rely on cacheScope alone to prevent unauthorized access".

Caching a tool list works only if the list is stable. The specification says a server's `tools/list` MUST NOT vary from one connection to the next, though it may vary with the authorization on the request, and that servers should return tools in a deterministic order, which helps prompt caches hit more often ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)). The SDK's `MCPServer` lists tools in the order you register them, which meets that rule (`mcp/server/mcpserver/tools/tool_manager.py`).

In the SDK, a server's hints default to `ttl_ms=0` and `"private"`, so nothing is reused unless the server opts in. `shop-support` opts in for its tool list with `cache_hints={"tools/list": CacheHint(ttl_ms=300_000, scope="public")}`, five minutes and shareable (`mcp/server/caching.py`). On the other side, `mcp.Client` caches by default, in memory, by the server's hints, and each list call takes a `cache_mode` of `"use"`, `"refresh"` or `"bypass"`. A call that passes its own `meta` always reaches the server, and the client caps any TTL at 24 hours (`mcp/client/caching.py`). To count what caching saves, list the tools twice from chapter 1's server, which sets no hint, then twice from `shop-support`, and count on the wire, with `lib.wire`, how many `tools/list` requests reached each server.

Example `cache-the-tool-list` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Call list_tools() twice on each of two servers, one that sets no cache hint and one with a five-minute public hint,
and count the tools/list requests that reach each; the prose reads the three counts."""
import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from lib import wire


async def list_twice(script: str, second_call: str = "use") -> tuple[str, str, int]:
    log = Path(script).with_suffix(".jsonl")             # the relay's log, beside the server file
    log.unlink(missing_ok=True)                          # the relay appends to its log
    server = StdioServerParameters(command=sys.executable, args=[script, "--serve"], env={})
    async with Client(wire.relay(server, log=str(log))) as client:
        first = await client.list_tools()                # cache_mode="use" is the default
        await client.list_tools(cache_mode=second_call)
        name = client.server_info.name
    # responses carry no method, so this counts only the requests that reached the server
    sent = sum(1 for _, message in wire.read_trace(str(log)) if message.get("method") == "tools/list")
    return name, f"ttlMs {first.ttl_ms}, cacheScope {first.cache_scope}", sent


async def main() -> None:
    name, hint, sent = await list_twice("order-status-server.py")         # chapter 1's server, which sets no hint
    print(f"{name} hint:", hint)
    print(f"{name} tools/list sent for two calls:", sent)
    name, hint, sent = await list_twice("list-what-the-server-offers.py")  # this chapter's server, with its tool-list hint
    print(f"{name} hint:", hint)
    print(f"{name} tools/list sent for two calls:", sent)
    name, hint, sent = await list_twice("list-what-the-server-offers.py", second_call="bypass")   # bypass skips the cache
    print(f"{name} tools/list sent when the second call bypasses:", sent)


asyncio.run(main())
```

Output:

```text
shop-orders hint: ttlMs 0, cacheScope private
shop-orders tools/list sent for two calls: 2
shop-support hint: ttlMs 300000, cacheScope public
shop-support tools/list sent for two calls: 1
shop-support tools/list sent when the second call bypasses: 2
```

The hint decides how many requests arrive. Chapter 1's `shop-orders` returned `ttlMs 0, cacheScope private`, so both calls went to the server, 2 requests in all. `shop-support`'s list came back with `ttlMs 300000, cacheScope public`, so the client's cache answered the second call, and only 1 request reached the server. With `cache_mode="bypass"` on the second call, both calls reached the server again, and the output beside the example counts them. A host that renders the tool list into every model turn saves a request a turn. And because the list keeps its order, the model's prompt starts with the same bytes, which a provider's prompt cache needs.

The shop's tool list can be public because every caller sees the same tools. The shop's per-customer data can't. When [Address records with resource templates](#resource-templates) serves one resource per order, those reads stay `"private"`, so a shared cache never hands one customer's order to another customer's session. If the tool list ever depends on the caller's token, as it may once [Scope tools by what the token allows](#scopes-per-tool) applies, it turns private too.

**Working rule:** Set a TTL and `"public"` scope on lists that are the same for every caller, such as the shop's tool list, and choose a TTL no longer than you'd accept a stale list after a deploy: minutes, not hours. Keep `"private"`, the SDK's default, on anything that depends on who is asking, and never let `cacheScope` stand in for an authorization check. On the client, keep the default cache, which drops an entry when a change notification arrives on a `client.listen(tools_list_changed=True)` stream (`mcp/client/client.py`), the kind of stream that [Tell clients when a resource changes](#resource-change-notifications) opens. Without that stream no notification reaches the client, so open one, and use `cache_mode="refresh"` when you have another reason to doubt an entry, rather than polling on the TTL.

## Keep an HTTP API where MCP adds nothing {#when-mcp-is-wrong}

Each section so far showed something MCP adds to the shop's API. [Separate the host, the client and the server](#host-client-server) added run-time discovery, and [Put each capability in the right primitive](#choose-a-primitive) gave each capability a control model. [Carry the version and capabilities on every request](#request-meta) made every request versioned and self-describing. The host's consent step, in [Ask for consent before side effects](#consent-before-side-effects), is another. Each of those helps when a model or a user's host chooses among capabilities at run time. None of them helps a program whose developer already knows which endpoint it will call.

The specification doesn't say when not to use MCP, so this is the book's judgement, not a protocol rule. We recommend a plain HTTP API for three kinds of work:

- **Service-to-service calls with no model choosing,** such as the warehouse's nightly read of stock levels. Its code calls fixed endpoints, so nobody reads the discovery answers or the descriptions.
- **Fixed workflows,** where the same steps run in the same order every time. Write them as code over the API, and if a model needs to start one, expose the whole workflow as one tool.
- **High-volume batch work,** where every byte and round trip is multiplied.

We recommend MCP where a model or a user's host chooses among capabilities at run time, as the support team's host does. The two don't compete. [Meet the shop and its API](#the-shop) kept the shop's API as the system of record, and `shop-support` is a thin adapter over it, so the warehouse keeps its API calls while the support team's host uses MCP.

This run prices the adapter, so the trade-off rests on numbers. The script fetches order O-2476 twice: once from the shop's API, with `GET /orders/O-2476`, and once through `shop-support`'s `get_order_status` tool over Streamable HTTP, the transport [Move the server from stdio to HTTP](#stdio-to-http) teaches. `lib.byte_meter`, a small module for this measurement, puts a TCP relay in front of each server and counts every byte both ways, headers included, and counts the HTTP requests each server handles. Everything runs in one process on 127.0.0.1, over HTTP/1.1 without TLS. On the MCP side, the count covers a host's setup on opening a client, including the tool listing, but not the tool call. That setup is measured twice: in the default auto mode, which first probes the server with `server/discover`, and with the version pinned. The tool call itself is made with the version pinned. No times are measured, because times on one machine's loopback say little about a network.

Example `api-call-versus-tool-call` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Fetch order O-2476 from the shop's API, then through shop-support's tool over Streamable HTTP, and count the cost.
The prose's comparison comes from the byte totals and the request counts the script prints."""
import asyncio
import os
import runpy

import httpx2
from mcp import Client

from lib import byte_meter, loopback, shop_api


async def session(url, traffic, requests, mode: str, calls: int) -> tuple[list[str], int]:
    """Open a client, list the tools as a host does, make `calls` tool calls, close it: the requests and bytes."""
    traffic.reset()
    requests.reset()
    # auto mode first sends server/discover to probe the server; a pinned revision skips that probe
    async with Client(f"{url}/mcp", mode=mode) as client:
        await client.list_tools()
        for _ in range(calls):
            await client.call_tool("get_order_status", {"order_id": "O-2476"})
    return list(requests.names), traffic.sent + traffic.received     # bytes both ways, from the relay


async def main() -> None:
    print("setup: one process, 127.0.0.1, HTTP/1.1, no TLS, bytes counted at a TCP relay, headers included")
    api_app, api_requests = byte_meter.count_requests(shop_api.create_app())
    with loopback.serve(api_app) as api_url, byte_meter.relay(api_url) as (url, traffic):
        # the one API call, sent through the relay so that its bytes are counted the way the tool's are
        httpx2.get(f"{url}/orders/O-2476", headers={"X-API-Key": shop_api.DEMO_API_KEY}).raise_for_status()
        api_bytes = traffic.sent + traffic.received
        print("api call round trips:", api_requests.count)
        print("api call bytes:", api_bytes)

        os.environ.update(shop_api.server_env(api_url))      # the tool calls the API directly, not through a relay
        shop_support = runpy.run_path("list-what-the-server-offers.py")["server"]    # defined there, not run
        mcp_app, mcp_requests = byte_meter.count_requests(shop_support.streamable_http_app())
        with loopback.serve(mcp_app) as mcp_url, byte_meter.relay(mcp_url) as (url, traffic):
            for mode, label in (("auto", "auto"), ("2026-07-28", "pinned")):
                names, setup_bytes = await session(url, traffic, mcp_requests, mode, calls=0)   # setup only, no tool call
                print(f"mcp {label} setup request count:", len(names))
                print(f"mcp {label} setup requests:", ", ".join(names))
                print(f"mcp {label} setup bytes:", setup_bytes)
            names, with_call = await session(url, traffic, mcp_requests, "2026-07-28", calls=1)
            call_bytes = with_call - setup_bytes          # a pinned session with one call, less the pinned setup
            print("mcp tool call round trips:", names.count("tools/call"))
            print("mcp tool call bytes:", call_bytes)
            print("tool call bytes per api call byte:", round(call_bytes / api_bytes, 1))  # one decimal place, as the prose quotes


asyncio.run(main())
```

Output:

```text
setup: one process, 127.0.0.1, HTTP/1.1, no TLS, bytes counted at a TCP relay, headers included
api call round trips: 1
api call bytes: 591
mcp auto setup request count: 2
mcp auto setup requests: server/discover, tools/list
mcp auto setup bytes: 2157
mcp pinned setup request count: 1
mcp pinned setup requests: tools/list
mcp pinned setup bytes: 1147
mcp tool call round trips: 1
mcp tool call bytes: 1357
tool call bytes per api call byte: 2.3
```

On the wire the tool call costs more bytes, not more round trips. The API call takes 1 round trip and the tool call takes 1, but it sends 2.3 times the bytes, which the output beside the example counts. The difference is the JSON-RPC envelope, the `_meta` on the request and on the result, the routing headers that Streamable HTTP adds, and the order itself, which the SDK returns as indented JSON inside a text block, with its quotes escaped, as [Read the messages on the wire](#read-the-messages) showed.

Setup costs more on top of that. In auto mode, opening the client sent 2 requests before its first call; with the version pinned it skipped the `server/discover` probe and sent 1. The output beside the example lists the requests and their bytes. Behind the server, each tool call also made its own request to the shop's API, which the counts leave out because the caller never sees it.

Some of those bytes buy something without a model. The headers `Mcp-Method`, on every request, and `Mcp-Name`, on `tools/call`, `resources/read` and `prompts/get`, let a gateway route by method and by tool without parsing bodies ([Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)). For the support team's host, which makes a few calls per ticket, 1357 bytes a call is small beside the model's own tokens. For the warehouse's nightly read of 64 products, every call pays for an envelope its code never reads, and the adapter adds a process to a job that ran without one.

**Working rule:** Keep a plain HTTP API for callers whose code knows which endpoint to call, such as other services, fixed workflows and batch jobs, and put an MCP server in front of the same API for hosts where a model or a user chooses at run time. Measure the overhead on your own transport before you route high-volume traffic through MCP, and pin the protocol version in clients you control, so they skip the discovery probe. Keep auto mode for clients that may meet servers you don't control, which may speak only the 2025 protocol.

## What goes wrong in production {#what-mcp-adds-in-production}

The parts this chapter added fail in a few recognisable ways, and each leaves a trace you can look for.

**A capability lands in the wrong primitive.** A policy served as a tool gets skipped when the model doesn't think to fetch it, and a refund served as a resource leaves the host no point at which to ask for consent. The sign is behaviour that varies from ticket to ticket for no reason in the ticket: answers about money given without the policy, or side effects with no consent step in the logs. Ask of each capability who should decide when it runs, as [Put each capability in the right primitive](#choose-a-primitive) does.

**A gateway drops or rewrites `_meta`.** Proxies and API gateways built for plain JSON APIs sometimes rewrite request bodies. A request that loses its version or capabilities fails with `-32602`, as [Carry the version and capabilities on every request](#request-meta) showed. On Streamable HTTP, a body that no longer matches its headers fails with `-32020`, because the `MCP-Protocol-Version`, `Mcp-Method` and `Mcp-Name` headers must agree with the body ([Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)). Pass MCP traffic through unchanged, and route on the headers rather than editing bodies.

**`clientInfo` is used as an identity.** The client's name in `_meta` is whatever the client chose to send, and the specification says not to rely on it for security ([base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic)). A server that grants more to a client named `shop-host` grants it to anyone who sends that name. Authorization comes from tokens, which [Find the authorization server from the resource](#protected-resource-metadata) starts on.

**A public cache entry crosses customers.** A result marked `"public"` may be shared across authorization contexts, even when it came from an authenticated endpoint ([caching](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching)). A server that marks per-customer data public lets a shared cache serve one customer's order to another. Keep the SDK's `"private"` default for anything that depends on the caller, and treat every `"public"` hint in a code review as a claim to check.

**A long TTL hides a deploy.** With a tool list fresh for hours, a client keeps offering a tool the server has removed, and calls to it fail. The sign is unknown-tool errors that stop when clients restart. Keep tool-list TTLs to minutes, and let clients refresh on a change notification, which reaches a client only on a `subscriptions/listen` stream it opened, as [Tell clients when a resource changes](#resource-change-notifications) sets up.

**A client calls a tool it never listed.** At 2.3.0, `mcp.Client` checks a tool's result against the tool's output schema, and if it hasn't listed the tools yet, it sends `tools/list` first (`mcp/client/session.py`). A client that calls tools without listing them pays an extra request on its first call. List the tools when the client opens, as a host does anyway.

**Old error codes from old material.** The pinned revision reserves `-32020` to `-32099` for the specification, treats `-32000` to `-32019` as a legacy range that new code shouldn't use, and asks for application codes outside the range JSON-RPC reserves ([base protocol](https://modelcontextprotocol.io/specification/2026-07-28/basic)). The revision renumbered its error codes on the way to release ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)), so material written against a draft can show other numbers for the same errors. Match error codes against the specification, not against a blog post.

**The specification moves on.** MCP is governed by the Agentic AI Foundation, a directed fund under the Linux Foundation, which took MCP on as a founding project in December 2025 ([announcement](https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/)). Revisions are dated, and a deprecated feature stays for at least twelve months ([feature lifecycle](https://modelcontextprotocol.io/community/feature-lifecycle)). The window is shorter only for an active security risk, and then at least ninety days, or where the [deprecated features registry](https://modelcontextprotocol.io/specification/2026-07-28/deprecated) says so. Read the registry when you plan a server's next release, and watch logs for `-32022` from clients built for a later revision.

**Working rule:** Check four things on any server you are about to ship: each capability's primitive matches who decides when it runs, nothing between client and server edits MCP bodies, nothing is decided on `clientInfo`, and every `"public"` cache hint covers data that is the same for every caller. Log the protocol version and error code of every failed request, because version and envelope errors are the first sign that a client or a gateway has changed.

## Decisions this chapter made {#what-mcp-adds-decisions}

- **One client per server, in the host.** The conversation and anything that crosses servers stay in the host's code; a server sees only the requests sent to it.
- **The shop's server is `shop-support`,** with chapter 1's `get_order_status` tool, the refund policy as a resource at `shop://policies/refund`, and `review_refund` as a prompt.
- **Each capability goes to the primitive whose controller should decide when it runs:** the model for tools, the host's code for resources, the person at the desk for prompts.
- **Version and capabilities are read from each request,** never from an earlier one, and a missing capability gets `-32021`.
- **The shop's own `_meta` keys use the `example.fernhill/` prefix.** Nothing is decided on `clientInfo` or `serverInfo`.
- **On `-32022`, the client retries once** with the newest version both sides list, and shows an error otherwise.
- **The tool list is public with a five-minute TTL.** Per-customer data stays private, and the tool list turns private if it comes to depend on the token.
- **Hand-written JSON-RPC, through `lib.raw_stdio`, is only for showing errors** that the SDK's client would never cause.
- **We recommend a plain HTTP API** for service-to-service calls, fixed workflows and batch work, and MCP where a model or a user's host chooses at run time, backed by the byte and round-trip counts in `api-call-versus-tool-call`.
