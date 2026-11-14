---
title: "Model Context Protocol in Practice"
chapter: "Serve data as resources and prompts"
chapter_id: resources-and-prompts
book: model-context-protocol-in-practice
edition: 2026.11.11
verified: 2026-11-14
edition_code: 2VMD-DEEC
canonical: https://rollingedition.com/model-context-protocol-in-practice/resources-and-prompts
license: CC BY 4.0
attribution: "“Serve data as resources and prompts,” chapter 4 of Model Context Protocol in Practice, Edition 2026.11.11, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/model-context-protocol-in-practice/resources-and-prompts. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Serve data as resources and prompts

By the end of this chapter you can publish the shop's policies and records as Model Context Protocol resources, address many records with one resource template, complete an argument while a user types it, tell a client when a resource changes, and package a refund review as a prompt the user can pick. The chapter's claims, and the code behind them, hold for `mcp` 2.3.0, the Python SDK, at revision 2026-07-28 of the specification.

[The shop](#the-shop) sells kitchen and garden goods, and most of what its support team's host needs to answer a ticket is something to read, not something to do. [Separate the host, the client and the server](#host-client-server) gave the shop's server, `shop-support`, one capability of each kind: the tool `get_order_status`, the refund policy as a resource, and a short `review_refund` prompt. One document and one prompt don't cover it. Every refund answer must follow the refund policy, a ticket is about one order, and a stock question is about one product's count. If each of those is a tool, the model has to decide to fetch it, and it may not.

For this, a Model Context Protocol (MCP) server has two other primitives, which differ from tools in who decides when they're used ([Put each capability in the right primitive](#choose-a-primitive)). A **resource** is data the server publishes under a URI, and the host decides whether to put it in front of a model. A **prompt** is a message template the server offers, and the user picks it. This chapter builds both out for the shop.

The server keeps the name `shop-support` throughout. Each example defines only the part its section teaches, and runs itself as chapter 2's server examples do: with no arguments, the file starts a client that launches the same file with `--serve` over stdio.

## Expose the policies as resources {#policies-as-resources}

`shop-support` already publishes one of the rules an answer must follow, the refund policy, which [Resources are data the application chooses](#resources-application-chooses) showed how to serve, and the shop has five more. Each one suits a resource: data that a server publishes under a URI, with a `name`, an optional `title` and `description`, a `mimeType`, and contents that are either text or a base64 `blob` ([resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)). A client lists a server's resources with `resources/list` and reads one with `resources/read`.

Resources are application-driven: the host decides how they're used. The specification's resources page says a host might show a picker, search the resources, or include some automatically, based on heuristics or the model's own selection. The protocol gives the model no way to read a resource; the host decides, though it may let the model choose. A resource's URI follows RFC 3986, and a server may use a scheme of its own. The specification keeps `https://` for resources a client can fetch without the server, directly from the web.

The six are **the shop's policies**, short rules written for this book on refunds, returns, shipping, stock, data handling and escalation. They are Markdown files in `examples/data/shop/policies/`, licensed CC BY 4.0 with the book's text and listed in the data card, `examples/data/shop/README.md`. `lib.policies` reads each one's title, `Updated:` date and one-sentence summary, so the server can describe every policy without opening the files on each request.

The server publishes each policy as a static resource at `shop://policies/{slug}`. The refund policy keeps the URI `shop://policies/refund` and the name `refund-policy` that chapter 2 gave it. The SDK's `FileResource` reads the file again on every `resources/read`, so an edited policy reaches the next read without a restart (`mcp/server/mcpserver/resources/types.py`). Each resource also carries three **annotations**, which are hints the host may use or ignore ([resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)):

- `audience` says who the content is for. The policies are for `assistant`, the model.
- `priority`, from 0.0 to 1.0, says how important the content is, and 1 means "effectively required". We give the refund policy 1.0 and the others 0.5. That is a judgement: every refund answer must follow the refund policy, while the other five matter only for some tickets.
- `lastModified` is an ISO 8601 time, here each policy's `Updated:` date.

At the pinned revision, `resources/list` and `resources/read` results carry two cache hints. `ttlMs` says how long a result stays fresh, and `cacheScope` says whether a cache may share it across callers ([caching](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching)). The SDK's default is a `ttlMs` of 0 with the `private` scope (`mcp/server/caching.py`). The policies are the same for every caller and change rarely, so this server marks both methods `public` for an hour. Listing and reading the policies shows both hints.

Example `list-policy-resources` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Serves the shop's six policies as static resources, then lists them and reads the refund policy from a client.
The point rests on the priority lines, where only the refund policy is 1.0, and on the two cache scope lines, which say public."""
import asyncio
import sys

from mcp import Client, StdioServerParameters
from mcp.server.caching import CacheHint
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.resources import FileResource
from mcp.types import Annotations

from lib.policies import load_policies

HOUR_MS = 3_600_000
server = MCPServer("shop-support", version="0.4.0", cache_hints={   # policies are the same for every caller
    "resources/list": CacheHint(ttl_ms=HOUR_MS, scope="public"),
    "resources/read": CacheHint(ttl_ms=HOUR_MS, scope="public")})

for policy in load_policies():
    server.add_resource(FileResource(
        uri=f"shop://policies/{policy.slug}", name=f"{policy.slug}-policy", title=policy.title,
        description=policy.summary, mime_type="text/markdown", path=policy.path,
        # the refund policy is effectively required (1.0); the others matter only for some tickets (0.5)
        annotations=Annotations(audience=["assistant"], priority=1.0 if policy.slug == "refund" else 0.5,
                                # the file gives a day, not a time, so its update is taken as midnight UTC
                                last_modified=f"{policy.updated}T00:00:00Z")))


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[__file__, "--serve"], env={})
    async with Client(params) as client:
        print("protocol revision:", client.protocol_version)
        listed = await client.list_resources()
        print("resources:", len(listed.resources))
        for resource in listed.resources:
            print(f"  {resource.uri}  {resource.title!r}  priority {resource.annotations.priority}")
        print("list cache scope:", listed.cache_scope)
        print("list ttl ms:", listed.ttl_ms)
        read = await client.read_resource("shop://policies/refund")
        contents = read.contents[0]                       # a read returns a list of contents; this file is its only item
        print("mime type:", contents.mime_type)
        print("first line:", contents.text.splitlines()[0])  # the file's first line is its title
        print("read cache scope:", read.cache_scope)
        print("read ttl ms:", read.ttl_ms)


if __name__ == "__main__":
    server.run() if "--serve" in sys.argv else asyncio.run(main())
```

Output:

```text
protocol revision: 2026-07-28
resources: 6
  shop://policies/data-handling  'Data-handling policy'  priority 0.5
  shop://policies/escalation  'Escalation policy'  priority 0.5
  shop://policies/refund  'Refund policy'  priority 1.0
  shop://policies/returns  'Returns policy'  priority 0.5
  shop://policies/shipping  'Shipping policy'  priority 0.5
  shop://policies/stock  'Stock policy'  priority 0.5
list cache scope: public
list ttl ms: 3600000
mime type: text/markdown
first line: # Refund policy
read cache scope: public
read ttl ms: 3600000
```

The client sees 6 resources, sorted by slug, and only the refund policy has priority 1.0. The list carries the scope `public` and a lifetime of 3600000 milliseconds, so a client may reuse it for an hour and share it between users. [Cache list results](#cache-list-results) shows what a client does with the hints.

Reading `shop://policies/refund` returned the file itself, as `text/markdown` text that begins with the line `# Refund policy`. The read carries the same scope, `public`, because the server marks both methods `public`.

That exchange never put the refund policy in front of a model. The server published it, and the host alone decides when to include it. [Put resources in the model's context](#resources-in-context) builds the host loop that does so for every refund ticket.

**Working rule:** Publish the documents a host should be able to put in front of a model as static resources, under a scheme that names your system, with a MIME type and a description the host can show. Use `https://` only for resources the client can fetch without your server. Mark a result `public` only when every caller gets the same one, and give high priority only to the one or two documents every answer depends on, not to all of them.

## Address records with resource templates {#resource-templates}

The six policies in [the previous section](#policies-as-resources) suit a list, but the shop's orders don't. The data holds 501 orders whose IDs start with `O-2` alone, and a resource for each would be useless to a host and expensive to serve. A **resource template** names many resources with one URI template, written in the syntax of RFC 6570 ([RFC 6570](https://datatracker.ietf.org/doc/html/rfc6570)). A client lists templates with `resources/templates/list`, fills in the variables, and reads the result with `resources/read` ([resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)).

In the Python SDK, the URI passed to `@server.resource()` picks the kind. Braces around a variable register a template, and the function's parameters must match the variables. A URI without braces registers a static resource (`mcp/server/mcpserver/server.py`, `resource`). The return value sets the contents: a `str` gives text, `bytes` give a blob, and anything else is converted to JSON.

A template also changes what a miss means. A read of a resource that doesn't exist fails, at the pinned revision, with the JSON-RPC error -32602, Invalid Params, and the URI goes in the error's `data`. The server "MUST NOT return an empty `contents` array" instead ([resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)). Revision 2025-11-25 used -32002 for the same case, and clients should still accept that code from older servers ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)). In `MCPServer`, a function gets -32602 by raising `ResourceNotFoundError`. Any other `ResourceError` becomes -32603, and a resource, unlike a tool, has no `isError` result to fail with ([handling errors](https://py.sdk.modelcontextprotocol.io/v2/servers/handling-errors/)).

The shop's order template is `shop://orders/{order_id}`, and its function wraps `GET /orders/{order_id}` on the shop's API, the endpoint that `get_order_status` wraps too. It raises `ResourceNotFoundError` when the API answers 404. An order belongs to one customer, so the read keeps the SDK's default cache hint, `private` with a lifetime of 0. The caching page names `private` as the scope for `resources/read` results "that depend on the authenticated user" ([caching](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching)). Before the API sees anything, the function checks that the variable looks like an order ID, `O-` and four digits, and raises `ResourceNotFoundError` if it doesn't, so a malformed ID never reaches the API.

Four reads, one success and three kinds of miss: a real order, one that doesn't exist, one ID in the wrong format, and one URI whose variable tries to climb out of the order's path.

Example `order-resource-template` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Reads orders through the template shop://orders/{order_id} and prints what each kind of miss returns.
The point rests on the codes, which are all the same, and on the traversal's message, which the SDK wrote rather than the handler."""
import asyncio
import json
import re
import sys

from mcp import Client, MCPError, StdioServerParameters
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError

from lib import loopback, shop_api, shop_reads

server = MCPServer("shop-support", version="0.4.0")   # default cache hint: ttl 0, scope private


@server.resource("shop://orders/{order_id}", title="One of the shop's orders", mime_type="application/json")
async def order(order_id: str) -> dict:
    """One order: its status, dates, lines and total, as the shop's API returns it."""
    if not re.fullmatch(r"O-\d{4}", order_id):                      # check the format before the API sees it
        raise ResourceNotFoundError(f"Order IDs look like O-1873, not {order_id!r}.")
    if (found := await shop_reads.get_json(f"/orders/{order_id}")) is None:    # the API answered 404
        raise ResourceNotFoundError(f"The shop has no order {order_id}.")
    return found


async def main() -> None:
    with loopback.serve(shop_api.create_app()) as base_url:
        params = StdioServerParameters(command=sys.executable, args=[__file__, "--serve"],
                                       env=shop_api.server_env(base_url))
        async with Client(params) as client:
            template = (await client.list_resource_templates()).resource_templates[0]  # the server defines one template
            print("template:", template.uri_template)
            read = await client.read_resource("shop://orders/O-2476")
            print("O-2476 status:", json.loads(read.contents[0].text)["status"])  # a read returns a list; the order is its only item
            print("read cache scope:", read.cache_scope)
            for case, uri in (("unknown order", "shop://orders/O-7144"),
                              ("malformed", "shop://orders/2476"),
                              # %2F is an encoded slash, so the URI has no path separator until the SDK decodes the variable
                              ("traversal", "shop://orders/..%2F..%2Frefunds")):
                try:
                    await client.read_resource(uri)
                except MCPError as err:
                    print(f"{case} code:", err.error.code)
                    print(f"{case} says:", err.error.message)
                    print(f"{case} data uri:", err.error.data["uri"])  # the URI the server could not read, which the error carries
                    assert err.error.code == -32602, case  # every miss gets the same code, the one the prose names


if __name__ == "__main__":
    server.run() if "--serve" in sys.argv else asyncio.run(main())
```

Output:

```text
template: shop://orders/{order_id}
O-2476 status: shipped
read cache scope: private
unknown order code: -32602
unknown order says: The shop has no order O-7144.
unknown order data uri: shop://orders/O-7144
malformed code: -32602
malformed says: Order IDs look like O-1873, not '2476'.
malformed data uri: shop://orders/2476
traversal code: -32602
traversal says: Unknown resource: shop://orders/..%2F..%2Frefunds
traversal data uri: shop://orders/..%2F..%2Frefunds
```

The template is listed as `shop://orders/{order_id}`, and order O-2476 reads as shipped, with the cache scope `private`.

The three misses fail with the same code, -32602, but their messages come from different places. The unknown order, O-7144, gets the handler's own message, and its URI comes back in the error's data, `shop://orders/O-7144`. The ID `2476` gets the format check's message, `Order IDs look like O-1873, not '2476'.`.

The traversal read fails too, but its message is the SDK's, `Unknown resource: shop://orders/..%2F..%2Frefunds`, not the handler's. The SDK decoded the variable to `../../refunds`, found `..` path segments in it, and refused the URI before the function ran. Without that refusal, the handler would have sent `../../refunds` in its request path to the shop's API.

That refusal is `ResourceSecurity`, which by default rejects `..` segments, absolute paths and NUL bytes in template variables, whatever encoding the URI used (`mcp/server/mcpserver/resources/templates.py`). The specification requires servers to validate every resource URI ([resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)), and the SDK's check backs that up without replacing it. It doesn't stop `2476`, which passes `ResourceSecurity`, so only the handler's format check catches that one.

This template reads any order for whoever holds the server's API key, which suits the support team's host. [The next section](#argument-completion) scopes reads to one customer.

**Working rule:** Use a resource template for records that share one shape and an ID. Return the API's own JSON, and raise `ResourceNotFoundError` for a miss, which gives the client -32602 with the URI. Keep the scope `private` for anything that belongs to a user. Leave the SDK's `ResourceSecurity` on, and validate the variable's format yourself too. Exempt a variable from the check only when it must carry a path, and then check the path yourself.

## Complete arguments for the user {#argument-completion}

A host that shows the order template from [the previous section](#resource-templates) to a person needs them to fill in `order_id`, and few people remember order IDs. **Argument completion** lets the host ask the server for suggestions while the user types. The host sends `completion/complete` with a reference, either `ref/resource` with a template's URI or `ref/prompt` with a prompt's name, plus the argument's name and its partial value. It may add `context.arguments`, the values the user has already chosen for other arguments. The result holds `values`, at most 100 of them, with an optional `total` and `hasMore`. A server that offers completion declares the `completions` capability ([completion](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/completion)).

One `@server.completion()` handler, in the Python SDK, serves every template and prompt on the server. It receives the reference, the argument and the context, and returns a `Completion` or `None`. Registering it declares the capability. The SDK doesn't filter what it returns, so whatever goes in `values` is what the UI shows ([completions](https://py.sdk.modelcontextprotocol.io/v2/servers/completions/)). It doesn't enforce the 100-item cap either. The `Completion` type says it must not exceed 100 items, but nothing checks that (`mcp_types/_types.py`), so the handler has to cap the list itself.

Completion is also a lookup, and a lookup can leak. The specification requires servers to control access to sensitive suggestions, which keeps completion from disclosing information it shouldn't ([completion](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/completion)). A handler that completed order IDs from the whole shop would tell anyone who types `O-2` which of the shop's orders exist.

So the handler completes only the orders of the customer the server acts for. Over stdio, the host names that customer in the server's environment, as it passes the shop's API key. Here `SHOP_CUSTOMER_ID` is C-0127, the customer who placed order O-2476. Over HTTP, [Authorize clients with OAuth](#authorization) replaces the variable with what an access token says. A support host's token names a member of staff, so the customer comes from the ticket the server looks up (the token's subject is the customer only where customers sign in themselves; see [Keep the server from acting as a confused deputy](#confused-deputy)).

The handler asks the shop's API for that customer's orders and keeps those that start with what the user typed. The API returns at most 100 of a customer's orders, newest first (`examples/lib/shop_api.py`), so the answer can never pass the protocol's cap. The handler keeps that order too: for a support ticket the newest orders are the likeliest, and the specification asks for suggestions "sorted by relevance" ([completion](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/completion)).

The API's response also carries the customer's total order count. When that total is more than the API returned, older orders might match too, so the handler leaves `total` out and sets `has_more`. Otherwise it reports the number of matches as `total`. The order template applies the same scope to reads: another customer's order gets the same not-found answer as an order that doesn't exist. A shared module, `lib.shop_reads`, holds the async helper both handlers use to call the shop's API. The run types two prefixes and reads two orders the caller can't see.

Example `complete-order-ids` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Completes order IDs for shop://orders/{order_id} from the orders of the one customer the server acts for, and answers another customer's order as if it didn't exist.
The point rests on the offers, which hold only the caller's orders, and on the two answers at the end, which differ only in the ID."""
import asyncio
import os
import sys

from mcp import Client, MCPError
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError
from mcp.types import Completion, ResourceTemplateReference

from lib import loopback, shop_api, shop_reads
server = MCPServer("shop-support", version="0.4.0")


@server.resource("shop://orders/{order_id}", title="One of your orders", mime_type="application/json")
async def order(order_id: str) -> dict:
    found = await shop_reads.get_order(order_id)                     # checks the ID's format before the API sees it
    # the customer the server acts for, from the server's environment
    if found is None or found["customer_id"] != os.environ["SHOP_CUSTOMER_ID"]:
        raise ResourceNotFoundError(f"You have no order {order_id}.")   # the same answer either way
    return found


@server.completion()
async def complete(ref, argument, context) -> Completion | None:
    # this handler completes only the order template's order_id argument
    if not isinstance(ref, ResourceTemplateReference) or argument.name != "order_id":
        return None
    # the API's newest-first page, at most 100 orders, which is also the protocol's cap of 100 values
    page = await shop_reads.get_json("/orders", customer_id=os.environ["SHOP_CUSTOMER_ID"], limit=100)
    # upper-cases what the user typed, so o-24 matches O-2476
    matches = [o["order_id"] for o in page["orders"] if o["order_id"].startswith(argument.value.upper())]
    cut_short = page["total"] > len(page["orders"])          # older orders the API didn't return may match too
    # total is reported only when every match was counted
    return Completion(values=matches, total=None if cut_short else len(matches), has_more=cut_short)


async def main() -> None:
    print("shop orders starting O-2:", shop_reads.orders_starting("O-2"))
    print("most orders for one customer:", shop_reads.most_orders_per_customer())
    with loopback.serve(shop_api.create_app()) as base_url:
        # C-0127 is the customer the server acts for, passed in the server's environment
        async with Client(shop_reads.server_params(__file__, base_url, SHOP_CUSTOMER_ID="C-0127")) as client:
            for typed in ("O-2", "o-24"):
                ref = ResourceTemplateReference(uri="shop://orders/{order_id}")
                result = (await client.complete(ref, {"name": "order_id", "value": typed})).completion
                print(f"{typed} offers:", ", ".join(result.values), f"({result.total} in all)")
            for order_id in ("O-1767", "O-7144"):                 # another customer's order, and nobody's
                try:
                    await client.read_resource(f"shop://orders/{order_id}")
                except MCPError as err:
                    print(f"{order_id} answer:", err.error.code, err.error.message)


if __name__ == "__main__":
    server.run() if "--serve" in sys.argv else asyncio.run(main())
```

Output:

```text
shop orders starting O-2: 501
most orders for one customer: 100
O-2 offers: O-2476, O-2230 (2 in all)
o-24 offers: O-2476 (1 in all)
O-1767 answer: -32602 You have no order O-1767.
O-7144 answer: -32602 You have no order O-7144.
```

Completion offers each caller only their own orders. Over the whole shop, `O-2` would match 501 orders, more than the cap allows in one answer, but customer C-0127 typing `O-2` is offered O-2476, O-2230 (2 in all) and nothing else. Typing `o-24` in lower case gets O-2476 (1 in all), because the handler upper-cases what the user typed first.

Reading another customer's order, O-1767, returns `-32602 You have no order O-1767.`, and reading O-7144, which doesn't exist, returns `-32602 You have no order O-7144.`. The two answers differ only in the ID, so the caller can't tell whether an order exists.

The cap matters only to a customer with more than 100 orders. The most any one customer has in the shop's data is 100, so for every customer the API returns all their orders, and the handler reports a `total`. A customer with a 101st order would be offered matches from the newest 100 only, with no `total` and `has_more` true. The run can't show that case, since no customer has that many.

`context.arguments` earns its place with a prompt that takes more than one argument, such as one that narrows order IDs to a customer the user picked first. Treat it as the user's input, never as authorization, because whoever calls the server chooses what it says. The specification also asks servers to rate-limit completion requests and clients to debounce them, since a host may send one per keystroke ([completion](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/completion)).

**Working rule:** Complete arguments only from what the caller may read, decided by who the server acts for, not by anything in the request. Filter by the typed prefix yourself, and keep the list within 100 values, because the SDK won't. Set `has_more` whenever the source you filtered was itself cut short, and report a `total` only when you counted every match. Give an inaccessible record the same not-found answer as a missing one, on reads and in completions alike.

## Tell clients when a resource changes {#resource-change-notifications}

A host that has put a resource in front of a model, such as an order from [the order template](#resource-templates), must hear about changes, or it keeps showing a stale copy. At the pinned revision, a client asks for change notifications with one request, `subscriptions/listen`. Its filter can name resource URIs to watch (`resourceSubscriptions`) and ask for list changes (`resourcesListChanged`, `toolsListChanged`, `promptsListChanged`), and the response is a long-lived stream of notifications ([subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)).

`subscriptions/listen` replaces three things from the 2025 revisions: `resources/subscribe`, `resources/unsubscribe` and the HTTP GET stream ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)). The SDK's `Client.subscribe_resource` is deprecated, and it talks only to 2025-era servers (`mcp/client/client.py`). [Inventory what the old server depends on](#inventory-2025-features) covers the move away from it.

The stream has a fixed shape ([subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)):

- The server first sends `notifications/subscriptions/acknowledged`, naming the subset of the filter it will honour.
- It then tags every notification with `io.modelcontextprotocol/subscriptionId`, the listen request's JSON-RPC ID, and "MUST NOT send notification types the client has not explicitly requested."
- A `notifications/resources/updated` message carries the URI and nothing else. It says that the resource changed, not what it holds, so the client reads it again.
- On stdio, the server keeps no subscription state across reconnections. After a dropped stream, the client sends `subscriptions/listen` again and refetches what it depends on.

In the Python SDK, server code publishes a change with `await ctx.notify_resource_updated(uri)`. That hands the update to a subscription bus, which every open stream reads from (`mcp/server/mcpserver/context.py`). On the client, `async with client.listen(resource_subscriptions=[...]) as changes` sends the request and waits for the acknowledgment. `changes.honored` then holds what the server agreed to, and iterating over `changes` yields events. A graceful close by the server ends the loop, and an abrupt drop raises `SubscriptionLost` (`mcp/client/client.py`, `listen`). Nothing is replayed, and the SDK says a dropped stream is not resumable (`mcp/server/subscriptions.py`). The stock example shows what that costs.

The shop's stock policy says a negative count means a recount is due, and KG-1018 has a negative count in the `south` warehouse. To show a change within one process, the example keeps the counts in the server's memory, standing in for the shop's stock system. It publishes each product's counts as `shop://stock/{sku}`, and it adds a tool, `set_on_hand`, that a warehouse's host would call after a recount. The tool replaces one count and publishes an update for that product's URI. The client watches KG-1018 and KG-9999, which doesn't exist. It records a recount of another product, then one of KG-1018, and later closes the stream and opens it again.

Example `stock-resource-changes` (Python 3.12.15 · anyio 4.16.0 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Watches two products with subscriptions/listen, records recounts while a stream is open and while it is closed, and re-reads after each.
The point rests on the first event, which arrives, and on the re-listening line, which shows that nothing is replayed."""
import asyncio
import sys

import anyio
from mcp import Client, StdioServerParameters
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError

from lib.shop_data import WAREHOUSES, load_shop
from lib.shop_reads import stock_summary

server = MCPServer("shop-support", version="0.4.0")
counts = {(s.sku, s.warehouse): s.on_hand for s in load_shop().stock}   # stands in for the shop's stock system


@server.resource("shop://stock/{sku}", title="On-hand stock for one product", mime_type="application/json")
def stock(sku: str) -> dict:
    if (sku, WAREHOUSES[0]) not in counts:              # a product exists if the first warehouse has a count for it
        raise ResourceNotFoundError(f"The shop sells no product {sku}.")
    return {warehouse: counts[sku, warehouse] for warehouse in WAREHOUSES}


@server.tool()
async def set_on_hand(sku: str, warehouse: str, counted: int, ctx: Context) -> str:
    """Record a warehouse's recount of one product, replacing its on-hand count."""
    counts[sku, warehouse] = counted
    await ctx.notify_resource_updated(f"shop://stock/{sku}")  # the exact URI clients watch; another spelling never matches
    return f"{sku} in {warehouse}: {counted}"


async def main() -> None:
    watched = ["shop://stock/KG-1018", "shop://stock/KG-9999"]           # KG-9999 doesn't exist
    async with Client(StdioServerParameters(command=sys.executable, args=[__file__, "--serve"], env={})) as client:
        async with client.listen(resource_subscriptions=watched) as changes:
            print("honoured:", " and ".join(changes.honored.resource_subscriptions))
            print("before:", await stock_summary(client, watched[0]))  # watched[0] is KG-1018
            # KG-1026 isn't watched, so this recount sends nothing on the stream
            await client.call_tool("set_on_hand", {"sku": "KG-1026", "warehouse": "north", "counted": 0})
            # KG-1018 is watched, so its update reaches the open stream
            await client.call_tool("set_on_hand", {"sku": "KG-1018", "warehouse": "south", "counted": 4})
            print("first event:", (await anext(changes)).uri)
            print("after:", await stock_summary(client, watched[0]))  # watched[0] is KG-1018
        # recorded while no stream is open, so no stream can hear it
        await client.call_tool("set_on_hand", {"sku": "KG-1018", "warehouse": "south", "counted": 3})
        async with client.listen(resource_subscriptions=watched) as changes:
            with anyio.move_on_after(1.0) as waited:                      # wait a second for anything replayed
                await anext(changes)
            print("events after re-listening:", 0 if waited.cancelled_caught else "at least 1")
            print("re-read:", await stock_summary(client, watched[0]))  # watched[0] is KG-1018


if __name__ == "__main__":
    server.run() if "--serve" in sys.argv else asyncio.run(main())
```

Output:

```text
honoured: shop://stock/KG-1018 and shop://stock/KG-9999
before: north 2, south -6
first event: shop://stock/KG-1018
after: north 2, south 4
events after re-listening: 0
re-read: north 2, south 3
```

The SDK honours every URI a client asks for, even one that doesn't exist. Here the acknowledgment honours both, `shop://stock/KG-1018 and shop://stock/KG-9999`, including the product the shop doesn't sell, and the SDK doesn't check whether the caller may read either (`mcp/server/subscriptions.py`). [What goes wrong in production](#resources-and-prompts-in-production) returns to that.

A change made while a stream is open reaches the client as an event, and the client re-reads. The recount of KG-1026 sent nothing on this stream, because nobody asked to watch it, and the first event names `shop://stock/KG-1018`. KG-1018 reads `north 2, south -6` before the recount and `north 2, south 4` after it.

The notification for a change made while nobody listens is gone for good. The client closed the stream, and a second recount set the `south` count to 3. On the reopened stream, a wait of a second turned up 0 events, and only a fresh read, `north 2, south 3`, shows the change.

The in-memory bus reaches only the streams in its own process. With two replicas of the server, a change on one never reaches a stream on the other, so replicas need a shared bus ([subscriptions](https://py.sdk.modelcontextprotocol.io/v2/handlers/subscriptions/)). [Run replicas without sticky sessions](#scale-without-sessions) runs the shop's server that way.

**Working rule:** Watch only the resources the host has put in front of a model or a user, and treat each event as a cue to read again, never as the new value. Re-read everything you depend on whenever you open a stream, the first time and after every drop, because nothing is replayed. Publish an update for the exact URI clients read, from the code path that makes the change.

## Package a workflow as a prompt {#workflows-as-prompts}

The resources in [the previous sections](#policies-as-resources) give a host the shop's data. Some of the support team's work, though, is a fixed procedure that a person starts, such as reviewing a refund before anyone issues it. A **prompt** packages such a procedure as a named message template that the server offers and the user picks, for example as a slash command. The user decides when it's used, and the server writes it, as [Prompts are templates the user chooses](#prompts-user-chooses) quoted.

A prompt has a `name`, an optional `title` and `description`, and `arguments`, each with a name, a description and whether it's required. A client lists prompts with `prompts/list` and fills one in with `prompts/get`, which returns `messages`. Each message has the role `user` or `assistant` and one content block: text, an image, audio, a resource link, or an embedded resource that carries a resource's contents inside the message. There is no `system` role, so a prompt is not a system prompt, and the host keeps its own. The same page says implementations "MUST carefully validate all prompt inputs and outputs to prevent injection attacks or unauthorized access to resources."

With the Python SDK, `@server.prompt()` takes the prompt's name from the function, its arguments from the parameters and its description from the docstring. The function returns the messages, and a bare string or content block becomes one `user` message (`mcp/server/mcpserver/prompts/base.py`). An `MCPError` the function raises reaches the client unchanged. But for an unknown prompt or a missing required argument, the SDK raises a plain `ValueError` (`mcp/server/mcpserver/server.py`, `get_prompt`), though the specification assigns -32602 to both ([schema](https://modelcontextprotocol.io/specification/2026-07-28/schema)).

The support team reviews each refund request against the refund policy, which says that a refund above €150.00 needs a support lead to confirm it. Chapter 2's `review_refund` took only an `order_id`, and its one message told the model which tool and resource to fetch. Here the prompt gains a second argument, `amount`, and carries what the review needs itself. Before it calls anything, it checks that both arguments look like the shop's formats. Then it looks the order up through the shop's API and returns two `user` messages. The first embeds the refund policy under its URI, `shop://policies/refund`, so the host needn't read it separately. The second quotes the order and asks the review's three questions.

Filling the prompt in for order O-1145, whose customer asks for €343.49, shows the messages a model would receive. Three bad calls follow: a path where an order ID belongs, a missing argument and a misspelled prompt name.

Example `refund-review-prompt` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.11:

```python
"""Packages a refund review as a prompt, with the refund policy embedded, the order quoted and the arguments checked first.
The point rests on the two messages, and on the three failures: a bad path gets Invalid Params, while a missing amount and a misspelled name both get an internal error."""
import asyncio
import json
import re
import sys

from mcp import Client, MCPError, StdioServerParameters
from mcp.server.mcpserver import MCPServer
from mcp.types import INVALID_PARAMS, EmbeddedResource, TextResourceContents

from lib import loopback, shop_api, shop_reads
from lib.policies import policy

server = MCPServer("shop-support", version="0.4.0")


@server.prompt(title="Review a refund request")
async def review_refund(order_id: str, amount: str) -> list[EmbeddedResource | str]:
    """Check a customer's refund request against the refund policy before a person issues it."""
    # up to five whole digits and exactly two decimals, so 24.99 and 343.49 pass
    if not re.fullmatch(r"\d{1,5}\.\d{2}", amount):
        raise MCPError(INVALID_PARAMS, f"Amounts look like 24.99, not {amount!r}.")
    # the API is asked only for an ID in the right format, and None from it means no such order
    if not re.fullmatch(r"O-\d{4}", order_id) or (order := await shop_reads.get_json(f"/orders/{order_id}")) is None:
        raise MCPError(INVALID_PARAMS, f"No order {order_id!r}. Order IDs look like O-1873.")
    return [EmbeddedResource(type="resource", resource=TextResourceContents(       # each item: one user message
                uri="shop://policies/refund", mime_type="text/markdown", text=policy("refund").text)),
            (f"Order {order_id}: {json.dumps(order)}\n\nThe customer asks for a refund of {amount}. "
             "From the policy and the order only: does it qualify, how much may the shop refund, "
             "and must a support lead confirm it?")]


async def main() -> None:
    good = {"order_id": "O-1145", "amount": "343.49"}  # the order, and the amount its customer asks for
    tries = {"path as order_id": ("review_refund", {**good, "order_id": "../refunds"}),  # a path where an ID belongs
             "missing amount": ("review_refund", {"order_id": "O-1145"}),
             "unknown prompt": ("refund_review", good)}  # misspelled: the prompt is review_refund
    with loopback.serve(shop_api.create_app()) as base_url:
        env = shop_api.server_env(base_url)
        async with Client(StdioServerParameters(command=sys.executable, args=[__file__, "--serve"], env=env)) as client:
            for n, message in enumerate((await client.get_prompt("review_refund", good)).messages, 1):
                print(f"message {n}:", message.role, message.content.type)
            for case, (name, arguments) in tries.items():
                try:
                    await client.get_prompt(name, arguments)
                except MCPError as err:
                    print(f"{case}:", err.error.code, err.error.message)


if __name__ == "__main__":
    server.run() if "--serve" in sys.argv else asyncio.run(main())
```

Output:

```text
message 1: user resource
message 2: user text
path as order_id: -32602 No order '../refunds'. Order IDs look like O-1873.
missing amount: -32603 Internal server error
unknown prompt: -32603 Internal server error
```

The filled-in prompt is two messages. The first, `user resource`, embeds the refund policy itself, and the second, `user text`, carries the order and the questions. Nothing here calls a model. These messages are what a host sends a model when a person picks the prompt, and [Run the host loop](#run-the-host-loop) makes that turn.

The failures show where the SDK and the specification part. The path, `../refunds`, never reached the shop's API, because the format check raised `MCPError` with `INVALID_PARAMS`, and the client got `-32602 No order '../refunds'. Order IDs look like O-1873.`. The two failures the SDK handles itself came back differently. A missing amount gave `-32603 Internal server error`, and the misspelled name gave `-32603 Internal server error`. Both carry the internal-error code rather than the -32602 the specification assigns, and the SDK's own message is hidden behind a generic one. So a host can't tell either mistake from a crash in the server.

Prompt arguments also become text that a model reads. A customer's words pasted into a free-text argument would reach the model inside a `user` message, which is one reason this prompt takes only an order ID and a decimal amount. [Treat ticket text as untrusted data](#untrusted-tool-output) covers that path in general.

**Working rule:** Offer a prompt for a procedure a person starts by name, and keep its arguments to values with a format you can check. Embed the resources the procedure depends on, so the host needn't fetch them. Validate every argument before you use it, and raise `MCPError` with `INVALID_PARAMS` for a bad one, because the SDK's own checks answer with an internal error.

## Choose between a resource and a tool {#resource-or-tool}

[Put each capability in the right primitive](#choose-a-primitive) settled most of the choice by asking who decides when the data is used. It left one case open, data that is both. [The previous sections](#policies-as-resources) published the same kinds of shop data that the tools in [Shape tools around tasks, not endpoints](#tasks-not-endpoints) return: an order, from `get_order_status`, and a product's stock, from `check_stock`. What follows is judgement, not measurement.

The order template lets a host attach the order a ticket is about before the model reads the ticket. `get_order_status` lets the model look up an order it finds in the ticket's text instead. Keep both reading through the same API call, so they can't disagree.

When a tool finds records the host may want to keep, it can return resource links to them instead of their full contents, and the host reads the ones it needs. The specification doesn't guarantee that such links appear in a `resources/list` result ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)), so a server can link to records that only a template addresses.

**Working rule:** Offer a record as both a resource and a tool when hosts attach it and models look it up, and serve both from one code path so they can't disagree. When a tool finds records the host may keep, return resource links to them rather than their contents.

## What goes wrong in production {#resources-and-prompts-in-production}

The shop's resources and prompts work on one machine with one caller. In production, with many callers, caches, replicas and hosts the shop didn't write, they fail in a handful of ways, and each has a symptom you can catch early.

**A per-user read gets a public cache scope.** A cache "MUST NOT" be shared across authorization contexts, and `public` tells it the result may be ([caching](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching)). `MCPServer` can't set the hint on each function, so `cache_hints` sets one hint per method, and a server that serves public policies and private orders gives the same hint on every `resources/read` (`mcp/server/mcpserver/server.py`, `_handle_read_resource`). Keep `resources/read` private on a server that serves anything per user, or give the policies a server of their own. The sign is a user who sees an order that isn't theirs, which no test with one user finds. And `ttlMs` is not a polling interval: clients "SHOULD NOT" poll on it.

**Lists differ between connections.** `resources/list` and `prompts/list` must not vary per connection, as [Cache list results](#cache-list-results) said of the tool list. A list may vary by the authorization on the request, and it may change over time if the server sends a list-changed notification ([resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources), [prompts](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)). A server that adds a resource after a tool call breaks every client's cache. It shows up as a list that changes after a tool call, or changes with no list-changed notification.

**A client watches what it can't read.** The SDK honours every URI a client asks to watch, as [the stock example](#resource-change-notifications) showed with a product the shop doesn't sell. A client watching another customer's order would learn that the order exists, and when it changed. Put middleware on `subscriptions/listen` that rejects URIs the caller may not read ([subscriptions](https://py.sdk.modelcontextprotocol.io/v2/handlers/subscriptions/)). Watch for an acknowledgment that echoes URIs the caller could never read.

**An update never matches.** `MCPServer` compares URIs as exact strings ([subscriptions](https://py.sdk.modelcontextprotocol.io/v2/handlers/subscriptions/)), so a client watching `shop://stock/kg-1018` never hears about `shop://stock/KG-1018`. The specification also allows an update to name a sub-resource of the watched URI ([schema](https://modelcontextprotocol.io/specification/2026-07-28/schema)), and `MCPServer` never matches one. The giveaway is a client that refreshes only when it reconnects. Publish the exact URI your templates produce, and normalize IDs before you build a URI.

**A dropped stream goes unnoticed.** Nothing is replayed, so a host that loses its stream and never re-listens shows stale data indefinitely. One that re-listens without re-reading misses every change made while it was away, as [the stock example](#resource-change-notifications) showed (`mcp/server/subscriptions.py`). Catch `SubscriptionLost`, re-listen, then re-read.

**Completion becomes an enumeration endpoint.** A handler that completes from every record, or trusts `context.arguments` for access, lets anyone list what exists, one keystroke at a time. A host that sends a request per keystroke also multiplies the load ([completion](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/completion)). Scope suggestions to the caller, cap them, rate-limit per caller, and watch completion request rates as you would login attempts.

**Prompt errors look like crashes.** The SDK answers an unknown prompt or a missing argument with -32603, as [the prompt example](#workflows-as-prompts) showed, so a host's logs mix users' mistakes with server faults. Raise `MCPError` with `INVALID_PARAMS` for every argument you reject, and alert on the internal errors that remain.

**Working rule:** Test resources and prompts with two callers before they reach production. Neither may see, complete or watch the other's records, and neither should see a list change without a list-changed notification. Check that every `resources/read` of a user's data carries the `private` scope, and that a host recovers from a dropped stream by re-listening and re-reading.

## Decisions this chapter made {#resources-and-prompts-decisions}

- **The shop's policies are six static resources** at `shop://policies/{slug}`, served from Markdown files written for the book, with the refund policy at priority 1.0 as a judgement.
- **The policies' list and reads are `public` for an hour,** because they are the same for every caller. Orders keep the `private` default.
- **Orders are a resource template,** `shop://orders/{order_id}`, over the same API endpoint as `get_order_status`, and a miss raises `ResourceNotFoundError` for -32602.
- **The SDK's `ResourceSecurity` stays on,** and handlers still check the format of what they're given.
- **Completion offers only the caller's own orders,** newest first and bounded by the API's limit of 100, with `has_more` when the API held more back. Another customer's order reads as not found.
- **Who the server acts for comes from the environment** over stdio. Over HTTP, the token's subject says who is calling: for the support host, a member of staff, with the customer taken from the ticket record ([Authorize clients with OAuth](#authorization), [Keep the server from acting as a confused deputy](#confused-deputy)).
- **The stock example keeps counts in the server's memory,** standing in for the shop's stock system, and the `set_on_hand` tool publishes the update from the code path that changes the count.
- **Change notifications use `subscriptions/listen`,** never `resources/subscribe`, and the client re-reads on every event and every new stream.
- **No model call in this chapter.** The prompt's messages are the input to a model turn that the book's host loop makes later.
- **The `review_refund` prompt embeds the refund policy,** checks its arguments' formats first, and raises `MCPError` with `INVALID_PARAMS` itself.
- **Data the host attaches is a resource, and data the model looks up is a tool.** A record can be both, served from one code path.
