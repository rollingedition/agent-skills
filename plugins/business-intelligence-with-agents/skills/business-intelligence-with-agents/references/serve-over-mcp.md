---
title: "Business Intelligence with Agents"
chapter: "Serve the semantic layer over MCP"
chapter_id: serve-over-mcp
book: business-intelligence-with-agents
edition: 2026.11.9
verified: 2026-11-13
edition_code: A1YT-QABQ
canonical: https://rollingedition.com/business-intelligence-with-agents/serve-over-mcp
license: CC BY 4.0
attribution: "“Serve the semantic layer over MCP,” chapter 11 of Business Intelligence with Agents, Edition 2026.11.9, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/business-intelligence-with-agents/serve-over-mcp. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Serve the semantic layer over MCP

By the end of this chapter, you can serve the shop's governed metrics as MCP tools that answer for the role the server was built for, return each answer with its provenance as structured data, test the server in memory, and run the book's agent through it as a host.

The shop is the online outdoor-gear shop in three regions that this book follows throughout. Its agent so far lives inside the book's Python: [chapter 6](#metrics-not-tables) gave it five metric tools over the semantic layer, and [chapter 9](#row-filters-in-compiler) put each role's row filters, column masks and minimum group size underneath them, in `lib/policies.py`. People in the shop don't work inside that Python. They ask questions in the assistant they already use, a chat app on their desktop or an editor with an agent built in. Each of those could get its own copy of the tools, and then each copy would need its own copy of the access rules, kept in step by hand. The first copy that drifts gives a regional lead another region's revenue.

The Model Context Protocol (MCP) removes the copies. It is an open protocol in which an application, the **host**, runs a **client** for each **server** it connects to, and a server offers tools that the host's model can call. *Model Context Protocol in Practice* covers the protocol, from [host, client and server](https://rollingedition.com/model-context-protocol-in-practice/s/host-client-server) to authorization, and this chapter links to it rather than teaching it again. Here, the shop's semantic layer becomes one MCP server, which this chapter calls the semantic server, in `lib/semantic_server.py`. It offers the same five tools as the in-process agent, through chapter 9's `PolicyToolbox`, the metric tools with the role's access rules underneath, so every host that connects gets the same metrics and the same rules. The examples use the Python SDK, `mcp` 2.3.0, which speaks the specification's revision 2026-07-28, and every one of them runs in memory, with no port and no process.

## Turn metrics into tools {#metrics-as-tools}

An MCP tool is a name, a description the model reads, a JSON Schema for its arguments and, optionally, a schema for its result. A client discovers a server's tools with `tools/list` and calls one with `tools/call`. The specification says the list "MUST NOT vary per-connection" but "MAY vary by the authorization presented on the request", and that servers "SHOULD return tools in a deterministic order" ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)). So the questions for a semantic layer are which tools to offer, and whether a role should see fewer of them.

We recommend offering the tools the agent already has. [Chapter 6](#metrics-not-tables) chose five for the shop's agent: `list_metrics`, `describe_metric`, `query_metric`, `ask_back` and `cannot_answer`. They were measured on the golden questions, whose answers were checked by running them, and they ask the model to choose a metric request, never to write SQL. `build_server()` in `lib/semantic_server.py` registers one MCP tool for each, with a description the model reads and typed arguments, and each tool body calls the same method of chapter 9's `PolicyToolbox` that the in-process agent calls. The tools are registered in name order, so `tools/list` returns the same order every time. Each is marked read-only, idempotent and closed-world with MCP's tool annotations. *Model Context Protocol in Practice* explains how to [write descriptions the model reads](https://rollingedition.com/model-context-protocol-in-practice/s/write-tool-descriptions) and why annotations are [hints, not guarantees](https://rollingedition.com/model-context-protocol-in-practice/s/annotations-are-hints).

The example builds a server for the analyst, who sees everything, and one for the support team, who may see no revenue. It lists each server's tools, calls `list_metrics` on each, and compares the catalog with the one the in-process agent puts in its prompt.

Example `list-metric-tools` (Python 3.12.15 · anyio 4.16.0 · duckdb 2.0.0 · mcp 2.3.0 · pydantic 2.14.3 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.9:

```python
"""The semantic layer as an MCP server: the tools it lists, what query_metric takes, and each role's catalog."""
import anyio
from mcp import Client

from lib.metric_tools import catalog
from lib.policies import PolicyLayer, policy_for
from lib.semantic import load
from lib.semantic_server import build_server
from lib.warehouse import connect

con, layer = connect(), load()


async def main():
    listed = {}
    for role in ("analyst", "support"):
        async with Client(build_server(role, shop=con, layer=layer)) as client:   # in memory: no port, no process
            tools = (await client.list_tools()).tools
            text = (await client.call_tool("list_metrics", {})).structured_content["text"]
        listed[role] = [t.name for t in tools]
        metrics = [line[2:].split(":")[0] for line in text.splitlines()]
        print(f"{role}, tools: {', '.join(listed[role])}")
        print(f"{role}, metrics in list_metrics: {len(metrics)}")
        print(f"{role}, metrics: {', '.join(metrics)}")
        in_process = catalog(PolicyLayer(layer, policy_for(role), con))
        print(f"{role}, same catalog as the in-process agent: {text == in_process}")
    query = next(t for t in tools if t.name == "query_metric")
    print(f"query_metric inputs: {', '.join(query.input_schema['properties'])}")
    print(f"query_metric requires: {', '.join(query.input_schema['required'])}")
    print(f"tools marked read-only: {sum(t.annotations.read_only_hint for t in tools)} of {len(tools)}")
    print(f"tools with a role input: {sum('role' in t.input_schema['properties'] for t in tools)}")
    print(f"same tool list for both roles: {listed['analyst'] == listed['support']}")


anyio.run(main)
```

Output:

```text
analyst, tools: ask_back, cannot_answer, describe_metric, list_metrics, query_metric
analyst, metrics in list_metrics: 10
analyst, metrics: net_revenue, gross_revenue, orders, line_net_revenue, units_sold, refunds, order_refunds, new_customers, refund_rate, average_order_value
analyst, same catalog as the in-process agent: True
support, tools: ask_back, cannot_answer, describe_metric, list_metrics, query_metric
support, metrics in list_metrics: 5
support, metrics: orders, units_sold, refunds, order_refunds, new_customers
support, same catalog as the in-process agent: True
query_metric inputs: metrics, group_by, filters, order_by, limit
query_metric requires: metrics
tools marked read-only: 5 of 5
tools with a role input: 0
same tool list for both roles: True
```

Both servers list the same tools: `ask_back, cannot_answer, describe_metric, list_metrics, query_metric`. What differs is the catalog. The analyst's `list_metrics` returns 10 metrics and support's 5: `orders, units_sold, refunds, order_refunds, new_customers`. Every revenue metric is gone from support's catalog, because chapter 9's `PolicyLayer` hides any metric that reads a column the role is denied. For both roles, the catalog over MCP is the same text the in-process agent puts in its prompt (`True` for support). That matters for [the host](#answer-through-a-host): an unchanged catalog means an unchanged prompt.

`query_metric` takes `metrics, group_by, filters, order_by, limit` and requires only `metrics`. Of the server's tools, 5 of 5 are marked read-only, and 0 take an argument called `role`, which is the subject of [the next section](#carry-the-role).

Keeping one tool list for every role was a choice. The specification would allow support's server to list fewer tools, but each of the five tools is useful to every role, and the role changes what a tool returns, not whether it exists. A role that can't use a tool at all is the case for shortening the list, and *Model Context Protocol in Practice* shows a list that varies by what the token allows in [scope tools by what the token allows](https://rollingedition.com/model-context-protocol-in-practice/s/scopes-per-tool). The cost of a long list is a separate matter, which the same book takes up in [keep the tool list small](https://rollingedition.com/model-context-protocol-in-practice/s/keep-the-tool-list-small).

**Working rule:** Serve the tools your agent was measured with, each one a thin call into the same code the in-process agent uses, so that the server can't drift from what you tested. List them in a fixed order and mark them read-only. Let the role change what a tool returns, and shorten the tool list only when a role can't use a tool at all.

## Carry the caller's role into every query {#carry-the-role}

A server that enforces [chapter 9's access rules](#row-filters-in-compiler) has to know whose rules to enforce, and that's the part an MCP server most often gets wrong. Revision 2026-07-28 has no protocol-level sessions: it removed the `initialize` handshake and the `Mcp-Session-Id` header, so every request stands alone ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)). There's no session to hold a role. The specification gives two places for identity instead. A server that a host launches over stdio, for one person, "SHOULD NOT" use MCP's authorization and should "retrieve credentials from the environment" ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). A server on HTTP derives the user from a verified access token: the specification's security guidance, on binding a server's state to a user, derives "the user ID … from the verified token rather than supplied by the client" ([security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)).

The tempting third place is a tool argument: give `query_metric` a `role` parameter and let the host fill it in. Then the role is whatever the caller sends, and the caller is a model that reads questions and, as [chapter 9](#text-in-data-is-data) showed, text inside the data. The example builds three servers and sends each the same request: `gq-017`, net revenue in each of "our countries" in 2025, asked by EMEA's regional lead, with `"role": "analyst"` added to the arguments. The first server takes the role as an argument. The second is the semantic server, built for EMEA's lead with `build_server("regional_lead", "EMEA")`. The third is built by `server_from_environment()`, which reads `SHOP_ROLE` and `SHOP_REGION` as a host would set them when it launches the server for one person. Last, the example takes the policy out of the way on that third server, as the next paragraph explains.

Example `role-bound-at-build` (Python 3.12.15 · anyio 4.16.0 · duckdb 2.0.0 · mcp 2.3.0 · pydantic 2.14.3 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.9:

```python
"""gq-017 from EMEA's regional lead, sent with role "analyst": a server that takes the role as an argument obeys it,
and one that binds the role when it is built ignores it, and queries a database that holds only the lead's rows."""
import anyio
from mcp import Client
from mcp.server.mcpserver import MCPServer

from lib.policies import PolicyLayer, PolicyToolbox, policy_for
from lib.semantic import MetricRequest, load
from lib.semantic_server import build_server, server_from_environment
from lib.warehouse import connect

con, layer = connect(), load()
naive = MCPServer("role-as-argument")


@naive.tool()
def query_metric(metrics: list[str], group_by: list[str] = [], filters: dict = {}, role: str = "analyst",
                 region: str | None = None) -> list[list]:
    """The anti-pattern: whoever calls the tool says who they are, and it queries the whole warehouse."""
    toolbox = PolicyToolbox(con, PolicyLayer(layer, policy_for(role, region), con))
    return [list(row) for row in toolbox.query_metric({"metrics": metrics, "group_by": group_by,
                                                       "filters": filters}).answer.rows]


request = {"metrics": ["net_revenue"], "group_by": ["order__country"], "filters": {"metric_time__year": 2025},
           "role": "analyst"}                     # the lead's request, with a role the lead doesn't have
environment = {"SHOP_ROLE": "regional_lead", "SHOP_REGION": "EMEA"}   # what a host sets for a stdio server


async def main():
    servers = {"role as argument": naive, "role bound at build": build_server("regional_lead", "EMEA", con, layer),
               "role from the environment": (stdio := server_from_environment(environment, con))}
    for name, server in servers.items():
        async with Client(server) as client:
            result = (await client.call_tool("query_metric", request)).structured_content
        rows = result["result"] if "result" in result else result["answer"]["rows"]
        print(f"{name}, countries: {', '.join(row[0] for row in rows)}")
        if "answer" in result:
            provenance = result["answer"]["provenance"]
            print(f"{name}, provenance: role {provenance['role']}, row filter {provenance['filters']['row filter']}")
    # The policy bypassed: the plain semantic layer, which applies no role, on the stdio server's own database.
    bypass = layer.query(stdio.database, MetricRequest.from_arguments({k: v for k, v in request.items() if k != "role"}))
    print(f"role from the environment, no policy, countries: {', '.join(row[0] for row in bypass.rows)}")


anyio.run(main)
```

Output:

```text
role as argument, countries: AU, CA, DE, ES, FR, GB, JP, NL, SG, US
role bound at build, countries: DE, ES, FR, GB, NL
role bound at build, provenance: role regional_lead, row filter EMEA only
role from the environment, countries: DE, ES, FR, GB, NL
role from the environment, provenance: role regional_lead, row filter EMEA only
role from the environment, no policy, countries: DE, ES, FR, GB, NL
```

The server that takes the role as an argument returned `AU, CA, DE, ES, FR, GB, JP, NL, SG, US`: every country in the shop, because the request said "analyst" and the server believed it. The semantic server returned `DE, ES, FR, GB, NL`, EMEA's countries only, and its provenance says why: role regional_lead, row filter EMEA only. Its tools have no `role` parameter, so the extra argument went nowhere: the SDK validated the arguments against each tool's parameters, dropped the one it didn't know, and ran the call. The server built from the environment returned `DE, ES, FR, GB, NL`. Binding the role at build means one server per person, which is what stdio gives you: the host starts a process for its user, and the process lives as long as the host needs it ([Choose stdio or Streamable HTTP](https://rollingedition.com/model-context-protocol-in-practice/s/stdio-or-http)).

The binding decides two things, and the database is the first. The book's primary access control is what the database allows each role: a read-only connection to that role's own views, which hold only its rows and columns, as [chapter 7](#views-per-role) built it, with chapter 9's policy rewrite as a second layer behind it. So `build_server()` doesn't take a connection to query. It takes the shop's warehouse, derives the role's policy, and opens the role's own database with `agent_warehouse(shop, policy=policy, semantic=SEMANTIC_TABLES)`: chapter 7's database, plus the semantic layer's views and calendar as the role sees them, so that metrics can run on it. Every tool queries that database, and no caller can pair a role with another role's. The example's last step runs the lead's request through the plain semantic layer, which applies no role at all, straight on the database of the server built from the environment. It returned `DE, ES, FR, GB, NL`: with the policy bypassed, there are still only EMEA's rows to read. The server decides "forbidden" from the policy alone: a filter on `region` with any value but the lead's own is forbidden. Any other value the lead's rows don't hold, such as another region's country, gets a correctable error listing the lead's own values, whether it exists elsewhere or not, so it reveals nothing ([chapter 9](#access-in-production)).

A server on HTTP serves many people, so it can't bind a role when it starts. It needs the role on each request, from the token. In the Python SDK, the server is given a `TokenVerifier` whose `verify_token()` returns an `AccessToken` with the client's ID, its scopes and the token's claims, and a tool reads the verified token with `get_access_token()` (`mcp/server/auth/provider.py`, `mcp/server/auth/middleware/auth_context.py`). The server would map a claim to a role and region there, and choose that role's database and policy for the call. The token must have been issued for this server: servers "MUST validate that access tokens were issued specifically for them" ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)), which *Model Context Protocol in Practice* builds in [bind each token to one server](https://rollingedition.com/model-context-protocol-in-practice/s/token-audience). Scopes don't replace the access rules. A scope can say that a token may call `query_metric`; only the database and the policy can say which rows it reads, and the specification's guidance lists "treating claimed scopes in token as sufficient without server-side authorization logic" as a common mistake ([security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)). The examples don't run this path: an in-memory client has no HTTP layer, so no bearer token reaches the server, and `get_access_token()` returns `None` there.

**Working rule:** Bind the role where the person was authenticated, never in a tool's arguments. For a stdio server, the host passes the role in the environment, and the server opens that role's read-only database and builds its policy once. For an HTTP server, take the role from a verified token issued for this server, on every request, and enforce the role's rows in the database and the policy whatever the token's scopes say. Leave `role` out of every input schema, so there's nothing for a model or a question to fill in, and log any argument a tool ignores, `role` first, because one is a sign that text the model read is steering it ([treat ticket text as untrusted data](https://rollingedition.com/model-context-protocol-in-practice/s/untrusted-tool-output)).

## Return answers with their provenance {#return-provenance}

With the role bound, the server's answers are right for the person asking. The host still has to know what each answer is: which metric produced it, with which filters, for which role and from data how fresh. [Chapter 1](#bi-agent-end-to-end) called that an answer's provenance, and the in-process agent keeps it in `Answer.provenance`. Over MCP, a tool can declare an `outputSchema` and return `structuredContent` that conforms to it, and a tool that does "SHOULD also return the serialized JSON in a TextContent block" ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)). Structured content is what lets a host's code, rather than its model, read an answer's role and filters. *Model Context Protocol in Practice* shows how the SDK builds the schema from a return type in [return structured content with an output schema](https://rollingedition.com/model-context-protocol-in-practice/s/structured-output).

Every tool of the semantic server returns a `ToolReply`, a pydantic model with two fields: `text`, the text the in-process tool shows the model, and `answer`, the answer with its rows and provenance, or nothing when the result doesn't end the run. Failures take two routes. The specification reports a tool execution error as a result with `isError` set, with "actionable feedback that language models can use to self-correct" ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)). A request with a misspelt dimension is that kind of failure, so the server raises the SDK's `ToolError` with [chapter 6's validation](#validate-the-request) message. A request the role may not make isn't, and the server returns it as an answer that declines, with a reason that starts "forbidden", as `PolicyToolbox` does in process. The example sends three requests: the finance team's refund rate by region for fiscal 2026, the same with `order_region` for `order__region`, and the support team's net revenue for 2025.

Example `tool-result-with-provenance` (Python 3.12.15 · anyio 4.16.0 · duckdb 2.0.0 · mcp 2.3.0 · pydantic 2.14.3 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.9:

```python
"""What a host receives from query_metric: an answer with its provenance as structured content, a request the model
can correct as a tool error, and a request the role may not make as an answer that declines."""
import json

import anyio
from mcp import Client

from lib.semantic import load
from lib.semantic_server import build_server
from lib.warehouse import connect

con, layer = connect(), load()
asks = {"finance, refund rate": ("finance", {"metrics": ["refund_rate"], "group_by": ["order__region"],
                                             "filters": {"metric_time__fiscal_year": 2026}}),
        "finance, misspelt dimension": ("finance", {"metrics": ["refund_rate"], "group_by": ["order_region"]}),
        "support, net revenue": ("support", {"metrics": ["net_revenue"], "filters": {"metric_time__year": 2025}})}


async def main():
    for name, (role, request) in asks.items():
        async with Client(build_server(role, shop=con, layer=layer)) as client:
            tool = next(t for t in (await client.list_tools()).tools if t.name == "query_metric")
            result = await client.call_tool("query_metric", request)
        print(f"{name}, is_error: {result.is_error}")
        if result.is_error:
            print(f"{name}, text: {result.content[0].text}")
            continue
        answer = result.structured_content["answer"]
        print(f"{name}, answered: {answer['answered']}")
        print(f"{name}, text block is the same JSON: {json.loads(result.content[0].text) == result.structured_content}")
        if answer["answered"]:
            print(f"{name}, rows: {', '.join(f'{region} {rate:.2%}' for region, rate in answer['rows'])}")
            print(f"{name}, provenance fields: {', '.join(answer['provenance'])}")
            print(f"{name}, provenance: {json.dumps({k: v for k, v in answer['provenance'].items() if k != 'sql'})}")
        else:
            print(f"{name}, reason: {answer['reason']}")
    print(f"output schema requires: {', '.join(tool.output_schema['required'])}")


anyio.run(main)
```

Output:

```text
finance, refund rate, is_error: False
finance, refund rate, answered: True
finance, refund rate, text block is the same JSON: True
finance, refund rate, rows: AMER 7.11%, APAC 6.02%, EMEA 8.45%
finance, refund rate, provenance fields: source, metric, sql, filters, role, data_as_of
finance, refund rate, provenance: {"source": "metric", "metric": "refund_rate", "filters": {"metric_time__fiscal_year": 2026}, "role": "finance", "data_as_of": "2026-06-27 02:00:00"}
finance, misspelt dimension, is_error: True
finance, misspelt dimension, text: Error executing tool query_metric: error: request rejected: refund_rate can't use dimension 'order_region'; did you mean order__region?
support, net revenue, is_error: False
support, net revenue, answered: False
support, net revenue, text block is the same JSON: True
support, net revenue, reason: forbidden: the support role may not see net_revenue
output schema requires: text, answer
```

Finance's refund rates came back as structured rows, AMER 7.11%, APAC 6.02%, EMEA 8.45%, computed on finance's own database, whose copy of the calendar gives each day its fiscal year. The provenance has these fields: `source, metric, sql, filters, role, data_as_of`. Without the SQL, the provenance reads `{"source": "metric", "metric": "refund_rate", "filters": {"metric_time__fiscal_year": 2026}, "role": "finance", "data_as_of": "2026-06-27 02:00:00"}`. The text block holds the same JSON (`True`), and the output schema requires `text, answer`.

The misspelt dimension came back with `is_error` set and the text "Error executing tool query_metric: error: request rejected: refund_rate can't use dimension 'order_region'; did you mean order__region?" The suggestion is chapter 6's, and the model can act on it. The words before it aren't the server's: the SDK's tool wrapper puts "Error executing tool" and the tool's name in front of the message of any `ToolError` a tool raises (`mcp/server/mcpserver/tools/base.py`). The in-process agent never showed the model that prefix, and [Answer questions through a host](#answer-through-a-host) measures what it changes.

Support's net revenue came back without `is_error`: answered `False`, with the reason "forbidden: the support role may not see net_revenue". We return a refusal as an answer, not an error, on purpose. An error invites the model to correct its request and try again, and there's no request support can correct into net revenue. A decline ends the run, as it did in [chapter 9](#measure-access), and the host's code can see from the structured `reason` that the access rules, not the model, made the decision.

**Working rule:** Return a pydantic model from every tool, so that each answer travels as structured content with its rows, its role, its filters and its data's freshness, and a host's code can check them. Raise a tool error for a request the model can fix, with a message that says how. Return a refusal for access as an answer that declines, with its reason, so the host ends the run instead of letting the model try another way in.

## Test the server in memory {#test-the-server}

The semantic server's [structured answers](#return-provenance) make it testable by its fields, and the tests that matter are about access: a server built for one role must never answer as another. Tests like that should run on every change, so they can't need a port or a process. The Python SDK's `Client` connects to a server object in the same process when you pass it one instead of a URL, and `raise_exceptions=True` makes a failure outside a tool's body come back with its real message, as *Model Context Protocol in Practice* explains in [test tools in memory](https://rollingedition.com/model-context-protocol-in-practice/s/in-memory-tests). The same section lists what such tests can't reach: headers, origin checks and server-sent events, everything an HTTP server adds.

The example is the semantic server's test file. Each test builds a server for one role, calls one tool through an in-memory client, and asserts on the structured content. The tests cover the rules that [chapter 9](#measure-access) measured, and the database under them: EMEA's lead gets the golden result for `gq-017`; EMEA's lead asking for APAC is declined as forbidden; the lead's server's own database, queried directly with no policy in the way, holds no other region's orders; support's catalog hides every metric that reads revenue, and only those; marketing's small groups are suppressed; and a misspelt dimension is a tool error that suggests the right one. The book pins no test runner, so the file runs its tests with a small helper in `lib/semantic_server.py`; under pytest, each would be an ordinary async test.

Example `semantic-server-tests` (Python 3.12.15 · anyio 4.16.0 · duckdb 2.0.0 · mcp 2.3.0 · pydantic 2.14.3 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.9:

```python
"""In-memory tests of the semantic server, one role per server, and one check that a test can fail."""
import anyio

from lib.golden import golden_result, load_golden, results_match
from lib.semantic import load
from lib.semantic_server import build_server, call, run_tests
from lib.warehouse import connect

con, layer = connect(), load()
server = lambda role, region=None: build_server(role, region, con, layer)      # each on the role's own database
gold = golden_result(con, next(q for q in load_golden() if q.question_id == "gq-017"))
lead_request = {"metrics": ["net_revenue"], "group_by": ["order__country"], "filters": {"metric_time__year": 2025}}
HIDDEN_FROM_SUPPORT = {"average_order_value", "gross_revenue", "line_net_revenue", "net_revenue", "refund_rate"}


async def test_lead_answer_matches_the_golden_result():
    result = await call(server("regional_lead", "EMEA"), "query_metric", lead_request)
    assert results_match(result.structured_content["answer"]["rows"], gold)


async def test_lead_cannot_ask_for_another_region():
    result = await call(server("regional_lead", "EMEA"), "query_metric", {"metrics": ["orders"],
                        "filters": {"order__region": "APAC"}})
    assert not result.is_error and result.structured_content["answer"]["reason"].startswith("forbidden")


async def test_lead_database_holds_no_other_region():        # the policy layer bypassed: SQL straight to the database
    regions = server("regional_lead", "EMEA").database.execute("SELECT DISTINCT region FROM analytics.fct_orders")
    assert regions.fetchall() == [("EMEA",)]


async def test_support_catalog_hides_every_revenue_metric():
    listed = (await call(server("support"), "list_metrics", {})).structured_content["text"]
    assert HIDDEN_FROM_SUPPORT == set(layer.metrics) - {line[2:].split(":")[0] for line in listed.splitlines()}


async def test_marketing_small_groups_are_suppressed():
    result = await call(server("marketing"), "query_metric", {"metrics": ["orders"], "group_by":
                        ["order__channel", "order__country"], "filters": {"metric_time__month": "2026-06"}})
    assert any("(under 10)" in row for row in result.structured_content["answer"]["rows"])


async def test_unknown_dimension_is_a_tool_error_with_a_hint():
    result = await call(server("finance"), "query_metric", {"metrics": ["orders"], "group_by": ["order_region"]})
    assert result.is_error and "did you mean order__region?" in result.content[0].text


async def main():
    passed = await run_tests(globals())
    print(f"tests passed: {passed} of {passed}")
    unbound = (await call(server("analyst"), "query_metric", lead_request)).structured_content["answer"]["rows"]
    print(f"the lead's request on an analyst's server differs from the lead's gold: {not results_match(unbound, gold)}")


anyio.run(main)
```

Output:

```text
test_lead_answer_matches_the_golden_result: passed
test_lead_cannot_ask_for_another_region: passed
test_lead_database_holds_no_other_region: passed
test_support_catalog_hides_every_revenue_metric: passed
test_marketing_small_groups_are_suppressed: passed
test_unknown_dimension_is_a_tool_error_with_a_hint: passed
tests passed: 6 of 6
the lead's request on an analyst's server differs from the lead's gold: True
```

The run reports 6 of 6. A passing test is worth something only if it can fail, so the example also sends the first test's request to a server built for the analyst and compares the result with the lead's golden result. It differs (`True`), and it should: the analyst's server returns every country. So the first test would catch a server that lost its binding.

These tests check the server, not the transport. They go through the SDK's argument validation, its structured output and its error handling, which is where [the error prefix](#return-provenance) comes from, but no request carries a token. For an HTTP deployment, add at least one test over HTTP that sends tokens for two roles and checks that each gets its own rows, and one with a token issued for another server, which must be refused.

**Working rule:** Test each role's rules through an in-memory client, with one server per role and assertions on the structured answer, and include a check that fails when the binding is wrong. Use the golden questions' results as the expected values, so the tests and the scores agree on what correct means. Add tests over HTTP for whatever an in-memory client can't send, tokens first.

## Answer questions through a host {#answer-through-a-host}

[The tests](#test-the-server) show that the semantic server answers each tool call as the in-process agent would. The last question is whether an agent answers as well through it. A host is the application that runs the model and calls the server's tools for it, and the host here is the book's own: [chapter 1](#bi-agent-end-to-end)'s agent loop, `run_agent()` in `lib/agent.py`, with chapter 6's prompt and the recorded model, Qwen3-4B-Instruct-2507, that every chapter replays.

The only new piece is `ServerToolbox` in `lib/semantic_server.py`. It has the `call()` method the loop expects, and makes each call through an MCP client. `ask_through_server()` opens a client on a server, calls `list_metrics` to fill the prompt's catalog, and runs the loop in a worker thread, so that each tool call can reach the server on the event loop. A model's call that isn't a JSON object, or names a tool the server doesn't list, gets the in-process agent's message from the host without reaching the server, with the tools named in the in-process order. *Model Context Protocol in Practice* builds a general host in [run the host loop](https://rollingedition.com/model-context-protocol-in-practice/s/run-the-host-loop); this one stays as thin as the book's loop.

Replay needs the model to see exactly what it saw when it was recorded, and over MCP it mostly does: the catalog and the prompt are the same, and so is every successful tool result's text. A tool error is the exception. Its text carries [the SDK's prefix](#return-provenance), so the model's next call has a prompt that no earlier recording holds. The recording `mcp-host-runs`, made with `recordings/record_mcp_host.py`, holds the replies to those calls only, from the same pinned model and settings. The example runs every golden question twice, in process as chapter 9 measured it and through a server built for the question's role, and compares the outcomes.

Example `host-asks-the-server` (Python 3.12.15 · anyio 4.16.0 · duckdb 2.0.0 · mcp 2.3.0 · pydantic 2.14.3 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.9:

```python
"""The book's agent as an MCP host on every golden question, each tool on the asker's server, against chapter 9."""
from collections import Counter

import anyio

from lib.agent import run_agent
from lib.golden import golden_result, grade, load_golden
from lib.metric_tools import catalog
from lib.model import RecordedModels
from lib.policies import PolicyLayer, PolicyToolbox, policy_for
from lib.prompts import metrics_first_prompt
from lib.semantic import load
from lib.semantic_server import ask_through_server, build_server
from lib.warehouse import connect

con, layer = connect(), load()
model = RecordedModels("metric-agent-runs", "policy-agent-runs", "mcp-host-runs")   # ch 11 recorded the rest


async def main():
    counts, changed, details, errors = Counter(), [], [], 0
    for q in load_golden():
        seen_as = PolicyLayer(layer, policy_for(q.role, q.region or None), con)
        local = run_agent(q.question, metrics_first_prompt(catalog(seen_as)), model, PolicyToolbox(con, seen_as), 4)
        trace, calls = await ask_through_server(build_server(q.role, q.region or None, con, layer), q.question, model)
        outcomes = [grade(q, t.answer, golden_result(con, q)) for t in (local, trace)]
        counts[q.split, q.kind, "questions"] += 1
        counts[q.split, q.kind, "correct"] += outcomes[1] == "correct"
        errors += any("is_error" in c for c in calls)
        if outcomes[0] != outcomes[1]:
            changed.append(f"{q.question_id} ({q.split}, {q.kind}): {outcomes[0]} in process, "
                           f"{outcomes[1]} over MCP, by {trace.steps[-2].tool}")
            details += [f"{q.question_id} first request's filters: {trace.steps[0].arguments['filters']}",
                        f"{q.question_id} asked: {trace.answer.reason.splitlines()[0]}"]
        if q.question_id == "gq-017":
            print(f"gq-017 calls: {', '.join(calls)}")
    for split in ("dev", "test"):
        for kind in ("answer", "decline", "forbidden"):
            print(f"{split} {kind} correct over MCP: {counts[split, kind, 'correct']} of "
                  f"{counts[split, kind, 'questions']}")
    print(f"runs with a tool error: {errors}")
    total = len(load_golden())
    print(f"same outcome as in process: {total - len(changed)} of {total}")
    print("\n".join(changed + details) or "no outcome changed")   # one line per changed question, then details


anyio.run(main)
```

Output:

```text
gq-017 calls: list_metrics, query_metric
dev answer correct over MCP: 11 of 17
dev decline correct over MCP: 3 of 4
dev forbidden correct over MCP: 3 of 3
test answer correct over MCP: 6 of 17
test decline correct over MCP: 4 of 4
test forbidden correct over MCP: 3 of 3
runs with a tool error: 11
same outcome as in process: 46 of 48
gq-013 (dev, answer): correct in process, declined over MCP, by ask_back
gq-014 (dev, answer): correct in process, declined over MCP, by ask_back
gq-013 first request's filters: {'order__order_date': '2026-05'}
gq-013 asked: Are you looking for orders in the entire month of May 2026, or specifically on a single day in May 2026?
gq-014 first request's filters: {'order__order_date': '2026-05'}
gq-014 asked: Do you mean orders placed in the entire month of May 2026 or on a specific day in May 2026?
```

For `gq-017`, the host made the calls `list_metrics, query_metric`: one to fill the prompt and one with the model's request. Over all the golden questions, the host scored 11 of 17 on the answer questions of the dev split, the golden questions used while building, against 13 of 17 in process. On the test split's, it scored 6 of 17, against 6 of 17 in process. Every forbidden question was declined, 3 of 3 on dev and 3 of 3 on test, because the server's policy hides what the role may not see and refuses what it may not ask, as in chapter 9. The outcome was the same as in process for 46 of 48 questions.

The two that changed both went through a tool error. 11 runs met one, and in two of them the outcome changed. For `gq-013` and `gq-014`, orders in May 2026, the model's first request had the filters `{'order__order_date': '2026-05'}`, which validation rejects with a hint to filter `metric_time__month` instead. In process, the model followed the hint and got the right count. Over MCP, it read the same hint after "Error executing tool query_metric:", and asked the person back instead: "Are you looking for orders in the entire month of May 2026, or specifically on a single day in May 2026?" Both runs ended `correct in process, declined over MCP, by ask_back`. That's one sample per run at temperature 0.7, so it doesn't show that the prefix caused the change, only that a different text gave a different draw. It does show that an outcome can move with nothing changed but the transport's wording, and that only a score on the golden questions finds it.

Treat what the server returns as data in the host as well. OWASP's Top 10 for LLM applications lists an MCP server's output among the carriers of indirect prompt injection ([OWASP, LLM01:2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)), and a metric answer carries values from the warehouse, such as product names, that [chapter 9](#text-in-data-is-data) showed can hold instructions. The host shows the person the structured answer with its provenance, and never a model's retelling of it unchecked. *Model Context Protocol in Practice* covers the host's side in [treat ticket text as untrusted data](https://rollingedition.com/model-context-protocol-in-practice/s/untrusted-tool-output).

**Working rule:** Put the server under the host you already measured, and score it on the golden questions before anyone uses it, because the transport can change what the model reads. Compare outcomes question by question with the in-process runs, and read every run that changed. Record what the new text produces rather than editing the server's messages to match old recordings, and show people the structured answer with its provenance.

## What goes wrong in production {#serving-in-production}

These are the ways a semantic layer served over MCP fails once hosts connect to it, and how you'd notice each one.

**One process serves several people.** A stdio server bound to one role is safe only while one person's host owns it. Wrap it in a shared process, or put it behind HTTP without tokens, and everyone gets the role of whoever started it. The semantic server as built here writes no audit log, so a deployment should record [chapter 9](#log-who-asked)'s entry for each answer, with the principal the server was built for. You'd notice there: one principal whose requests come from several users or hosts, or at a rate no one person asks at. Serve more than one person only over HTTP, with the role from each request's token.

**The token's role and the policy file disagree.** A claim that names a role `roles.toml` doesn't have, or a regional lead with no region, must fail closed. `policy_for()` raises `PolicyError` for both, and a server that catches it and falls back to a default role has undone the binding. Test the mapping from claims to roles with tokens for every role and for none.

**The server's connection outranks its role.** The policy narrows queries, but the database decides what a query can reach. A server that binds the lead's role and then queries with the analyst's connection is one bug away from a leak. Open the role's own read-only database when you bind the role, as `build_server()` does, and check in a test that the connection can't read another region's rows, as [the tests](#test-the-server) do.

**A host caches an old catalog.** At revision 2026-07-28, list results can carry a lifetime and a cache scope, so hosts may reuse them ([Cache list results](https://rollingedition.com/model-context-protocol-in-practice/s/cache-list-results)). `list_metrics` is a tool call, so the protocol doesn't cache its catalog, but a host that caches it anyway shows a metric after the policy removed it. The access rules still refuse the request, so the cost is a forbidden decline where the model would have declined on its own.

**An SDK upgrade changes what the model reads.** The prefix on tool errors comes from the SDK, not from the server's code, and so does the text of argument validation errors. A new release can reword either, and the agent's behaviour after an error changes with it. Pin the SDK, rerun the golden questions through the host on every upgrade, and read the runs whose outcome changed.

**Two servers describe the same metrics.** Vendors serve semantic layers over MCP too. dbt's MCP server offers Semantic Layer tools named `list_metrics`, `get_dimensions` and `query_metrics`, among others, for projects on the dbt platform ([dbt Labs](https://docs.getdbt.com/docs/dbt-ai/mcp-available-tools)), and Snowflake's managed MCP server answers questions over semantic views through Cortex Analyst, using the connecting user's default role and a separate grant for each tool ([Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)). Those are vendors' descriptions of their own products. If a host connects both a vendor's server and yours, its model sees two `list_metrics` tools with two sets of definitions. Give each host one server per semantic layer, and name tools apart when it must have two, as *Model Context Protocol in Practice* does in [name tools across servers](https://rollingedition.com/model-context-protocol-in-practice/s/namespace-tools).

**A client on an older revision connects.** `mcp` 2.3.0 also serves clients on the 2025 revisions through the old handshake, and dbt's server pins the SDK's 1.x line ([`dbt-mcp`](https://github.com/dbt-labs/dbt-mcp)). The semantic server's tools don't depend on the revision, but an HTTP deployment's sessions and cancellation do; *Model Context Protocol in Practice* covers that in [serve old and new clients through the window](https://rollingedition.com/model-context-protocol-in-practice/s/serve-both-revisions).

**Working rule:** Run one stdio server per person, or HTTP with the role from each request's token, and fail closed on any claim the policy file doesn't know. Query with the role's own read-only database, not a shared one. Pin the SDK and rerun the golden questions through the host whenever it changes. Keep one server per semantic layer in each host, record an audit entry for every answer, and read it for a principal that more than one person seems to share.

## Decisions this chapter made {#serving-decisions}

This is where the book ends. You started from an agent that wrote SQL over a schema and got most golden questions wrong. You can now build the version the shop can use: one that asks governed metrics first, writes SQL only on its role's read-only database, inside guards, declines when it can't answer, keeps each role inside what it may see, and serves all of that to any host over MCP. Above all, you can measure each change on golden questions written from your own work, so the next change you make is one you can prove.

- **The semantic server offers chapter 6's five tools,** each a thin call into chapter 9's `PolicyToolbox`, so the server and the in-process agent run the same code.
- **One tool list for every role,** in name order and marked read-only; the role changes what `list_metrics` and the other tools return.
- **The role is bound when the server is built:** from the environment for stdio, and from a verified token on each request for HTTP. No tool takes a `role` argument.
- **Every server queries its role's own read-only database,** chapter 7's database with the semantic layer's views and calendar added; the policy is the second layer.
- **Every tool returns structured content:** the text the model is shown, and the answer with its rows and provenance.
- **A request the model can fix is a tool error; a request the role may not make is an answer that declines,** with a reason that starts "forbidden".
- **The server is tested in memory, one role per server,** against the golden results, with a check that fails when the binding is wrong.
- **The HTTP path is described, not run:** the examples open no socket, and an in-memory client carries no token, so the mapping from a verified token to a role needs its own tests over HTTP.
- **The host is the book's own loop and prompt.** Calls the earlier recordings hold are replayed; `mcp-host-runs` holds only the calls that follow an error text the SDK changed.
