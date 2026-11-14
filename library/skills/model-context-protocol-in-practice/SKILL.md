---
name: model-context-protocol-in-practice
description: "Use when designing, building, securing, testing or running Model Context Protocol (MCP) servers and clients with the Python SDK, or when moving a 2025-era MCP server to the pinned revision. Covers wrapping an existing HTTP API as tools, resources and prompts; choosing which primitive each capability uses; asking the user mid-call; serving over Streamable HTTP; long-running tasks; OAuth authorization; security controls; building a host that works through a ticket queue; testing and tracing; and migration."
license: CC-BY-4.0
compatibility: "The book's examples ran on Python 3.12.15 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Model Context Protocol in Practice"
  edition: "2026.11.11"
  verified: "2026-11-14"
  examples: "70 of 70 examples pass"
  edition-code: "2VMD-DEEC"
  source: "https://rollingedition.com/model-context-protocol-in-practice"
---

# Model Context Protocol in Practice

This agent skill is *Model Context Protocol in Practice*, Edition 2026.11.11, from Rolling Edition. Examples passed Nov 14, 2026: 70 of 70 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `model-context-protocol-in-practice` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `2VMD-DEEC` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/model-context-protocol-in-practice
- **Credit the book** when you quote it or reuse its code: Model Context Protocol in Practice, Edition 2026.11.11, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/model-context-protocol-in-practice. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `model-context-protocol-in-practice` plugin and the zip on the book's page at rollingedition.ai.

## Wrap an existing API as an MCP server

**When:** A model or host needs part of an existing HTTP API.

1. Keep the API as the system of record, and make the server a thin adapter that calls it ([Meet the shop and its API](https://rollingedition.com/model-context-protocol-in-practice/s/the-shop)).
2. Start with one read-only tool for one endpoint, with a docstring for the model. Once you wrap more than a handful of endpoints, shape tools around tasks instead. Raise `ToolError` with a message that says what to do differently ([Wrap one endpoint as a tool](https://rollingedition.com/model-context-protocol-in-practice/s/wrap-an-endpoint-as-a-tool)).
3. Launch stdio servers with `sys.executable` and an explicit `env=`, and connect with `mcp.Client`. When a tool fails with only the generic message, read the server's standard error before changing the client ([Call the tool from a client](https://rollingedition.com/model-context-protocol-in-practice/s/call-a-tool-from-a-client)).
4. When a call misbehaves, trace the wire with a relay that logs each line ([Read the messages on the wire](https://rollingedition.com/model-context-protocol-in-practice/s/read-the-messages)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/call-a-tool-from-a-client); its `wrong ID says` line should read Error executing tool get_order_status: The shop has no order O-7144. Order IDs look like O-1873..

**Pitfalls:**
- Anything written to standard output breaks a stdio server. Log to standard error.
- A stdio client passes only a short allowlist of variables. Pass each one the server needs.

## Choose a primitive for each capability

**When:** Deciding whether each capability is a tool, a resource or a prompt.

1. Make a capability a tool when the model should decide from the conversation whether to use it, including every action that changes something. Make data a resource when the host's code can tell when it's needed, such as a policy for a known kind of ticket. Make a workflow a prompt only when a person starts it and every run follows the same steps. If no person starts it, make it a tool or put the steps in the host's instructions ([Put each capability in the right primitive](https://rollingedition.com/model-context-protocol-in-practice/s/choose-a-primitive)).
2. Keep a plain HTTP API for callers whose code knows which endpoint to call, such as other services and batch jobs ([Keep an HTTP API where MCP adds nothing](https://rollingedition.com/model-context-protocol-in-practice/s/when-mcp-is-wrong)).
3. Decide nothing on `clientInfo`, which the client chooses to send ([Carry the version and capabilities on every request](https://rollingedition.com/model-context-protocol-in-practice/s/request-meta)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/choose-a-primitive); its `tool says order status` line should read shipped.

**Pitfalls:**
- A policy served as a tool gets skipped when the model doesn't ask for it. A refund served as a resource gives the host no point to request consent.

## Design a tool the model can use

**When:** A model must choose and call a tool to finish a task.

1. Shape each tool around one task from the tickets, not one per endpoint, and move decisions such as amounts into the server ([Shape tools around tasks, not endpoints](https://rollingedition.com/model-context-protocol-in-practice/s/tasks-not-endpoints)).
2. Write each description in two to four sentences: what the tool does, when to use it instead of its most-confused neighbour, what its inputs look like and what it returns. Pass it as `description=` ([Write descriptions the model reads](https://rollingedition.com/model-context-protocol-in-practice/s/write-tool-descriptions)).
3. Type every argument as narrowly as the API allows: a pattern for IDs, an enum for fixed values, bounds and a date format ([Type inputs with JSON Schema](https://rollingedition.com/model-context-protocol-in-practice/s/type-tool-inputs)).
4. Give each tool a pydantic return model, so the SDK publishes an output schema ([Return structured content with an output schema](https://rollingedition.com/model-context-protocol-in-practice/s/structured-output)).
5. Raise `ToolError` for every failure the model could correct, and never return an error as a plain string ([Report failures as tool results](https://rollingedition.com/model-context-protocol-in-practice/s/tool-errors)).
6. Annotate every tool. Mark it idempotent only when the server enforces that ([Mark what a tool changes with annotations](https://rollingedition.com/model-context-protocol-in-practice/s/tool-annotations)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/structured-output); its `within limit` line should read False.

**Pitfalls:**
- Two tools the model can't tell apart get confused. Watch how often each is called per ticket.

## Serve documents as resources and workflows as prompts

**When:** A host needs policies or records in front of a model, or a person starts a fixed procedure by name.

1. Publish documents as static resources, under a scheme that names your system, with a MIME type and a description. Mark results `public` only when every caller gets the same result ([Expose the policies as resources](https://rollingedition.com/model-context-protocol-in-practice/s/policies-as-resources)).
2. For records that share one shape and an ID, use a resource template. Raise `ResourceNotFoundError` for a miss, and keep user data `private` ([Address records with resource templates](https://rollingedition.com/model-context-protocol-in-practice/s/resource-templates)).
3. Complete arguments only from what the caller may read. Filter by the typed prefix yourself, and give an inaccessible record the same answer as a missing one ([Complete arguments for the user](https://rollingedition.com/model-context-protocol-in-practice/s/argument-completion)).
4. Watch only resources the host has put in front of a model. Treat each event as "read this again", and re-read after every new stream and every drop ([Tell clients when a resource changes](https://rollingedition.com/model-context-protocol-in-practice/s/resource-change-notifications)).
5. Validate each prompt argument, and raise `MCPError` with `INVALID_PARAMS` for a bad one ([Package a workflow as a prompt](https://rollingedition.com/model-context-protocol-in-practice/s/workflows-as-prompts)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/policies-as-resources); its `list cache scope` line should read public.

**Pitfalls:**
- A read of a user's data with a `public` scope can reach another user's cache.
- A client can watch a resource it isn't allowed to read. Gate the watch filter.
- The SDK answers a bad prompt argument with an internal error unless you raise `INVALID_PARAMS`.

## Ask the user mid-call without holding the connection

**When:** A tool can't finish without an answer only the person at the host can give, such as a refund reason or a confirmation.

1. Never wait inside a tool call for something only the client can give you ([See why a stateless server can't wait for an answer](https://rollingedition.com/model-context-protocol-in-practice/s/why-calls-cannot-wait)). Return an `InputRequiredResult` with one input request per question. Check the client's declared capabilities first. Put only what the retry needs in `requestState`, and make every side effect before the question idempotent or harmless when no one answers ([Return an input request instead of a result](https://rollingedition.com/model-context-protocol-in-practice/s/return-an-input-request)).
2. In the host, let `Client.call_tool` run the rounds with an elicitation callback. On the server, read the answer and the state together ([Resume the call with the answer](https://rollingedition.com/model-context-protocol-in-practice/s/resume-with-the-answer)).
3. Use form mode only for answers the person alone can give. Send secrets and sign-ins through URL mode ([Ask for structured input with elicitation](https://rollingedition.com/model-context-protocol-in-practice/s/elicitation-forms)).
4. For any step that must happen once, record answered states on the server, and check that record before the side effect ([Keep round-trip state tamper-proof](https://rollingedition.com/model-context-protocol-in-practice/s/round-trip-state)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/resume-with-the-answer); its `by Client.call_tool` line should read R-0112 requested.

**Pitfalls:**
- The SDK seals state with a key made at process start. A restart or another replica can't open it, and the answer fails with -32602.
- A URL-mode flow the user abandons can loop. Count the rounds and stop after a few.

## Serve over Streamable HTTP

**When:** A server serves several hosts, guards systems hosts can't reach, or must scale. Keep stdio for one user on their own machine.

1. Serve with `MCPServer.run(transport="streamable-http")` on loopback while developing, and give clients the endpoint's URL ([Move the server from stdio to HTTP](https://rollingedition.com/model-context-protocol-in-practice/s/stdio-to-http)).
2. When a call fails, read the exchange first: the three routing headers, `_meta` in the body, the status and the content type ([Read one HTTP exchange](https://rollingedition.com/model-context-protocol-in-practice/s/http-on-the-wire)).
3. Report progress from any tool that runs longer than a few seconds. Keep the default response mode, since `json_response=True` drops progress and cancellation ([Stream progress on a long call](https://rollingedition.com/model-context-protocol-in-practice/s/stream-progress)).
4. Write long tools as `async def`, re-raise cancellation, and make them safe to retry ([Cancel a call the client no longer needs](https://rollingedition.com/model-context-protocol-in-practice/s/cancel-a-call)).
5. Pass `transport_security` with the names the server answers to; keep the loopback default for development only ([Reject requests from other origins](https://rollingedition.com/model-context-protocol-in-practice/s/validate-origin)).
6. Run replicas with no sticky sessions. Move each in-memory store into shared storage before adding a replica ([Run replicas without sticky sessions](https://rollingedition.com/model-context-protocol-in-practice/s/scale-without-sessions)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/validate-origin); its `0.0.0.0 app, foreign Origin` line should read 200 tools listed. The 200 shows what a 0.0.0.0 deployment without `transport_security` does; send the same probe to yours and expect 403.

**Pitfalls:**
- A server bound to `0.0.0.0` accepts every host and origin, and nothing fails.

## Run long work as a task

**When:** A tool's work can outlast the connection, so the caller comes back for the result.

1. Turn the extension on only through the SDK's extension classes, never by writing its identifier into capabilities by hand. Return a task only to a request that declared the extension. Otherwise return a result, or error -32021 when the work can't finish in a plain call ([Negotiate an extension](https://rollingedition.com/model-context-protocol-in-practice/s/negotiate-an-extension)).
2. Store the task before returning its handle, and generate the ID from a random source with at least 128 bits ([Start a task instead of waiting](https://rollingedition.com/model-context-protocol-in-practice/s/start-a-task)).
3. Poll at the server's `pollIntervalMs`, and stop at the first terminal status. Treat `completed` as the original call's result ([Poll a task and fetch its result](https://rollingedition.com/model-context-protocol-in-practice/s/poll-a-task)).
4. Give each task a TTL that covers the wait before the client fetches it, and purge after it. Check for cancellation at each natural step ([Expire and cancel tasks](https://rollingedition.com/model-context-protocol-in-practice/s/task-lifetime)).
5. Use a plain call when the result arrives within every timeout, progress when the caller waits on a stable connection, and a task otherwise ([Choose a task, progress or a plain call](https://rollingedition.com/model-context-protocol-in-practice/s/task-or-call)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/poll-a-task); its `statuses` line should read working then completed.

**Pitfalls:**
- Tasks kept in one replica's memory answer -32602 on another replica.
- Task IDs can be the only check on a result. Check the owner on every task request.

## Authorize clients with OAuth

**When:** A server must accept only tokens issued for it, and hosts sign users in through an authorization server.

1. Give each protected server `AuthSettings` with its endpoint URL as `resource_server_url`, and the smallest `required_scopes` every request needs. Test the chain with one request that has no token. Expect 401 and a `resource_metadata` URL ([Find the authorization server from the resource](https://rollingedition.com/model-context-protocol-in-practice/s/protected-resource-metadata)).
2. Give each host one Client ID Metadata Document at a stable `https://` URL, with no secret, passed as `client_metadata_url` ([Identify the client with a metadata document](https://rollingedition.com/model-context-protocol-in-practice/s/client-id-metadata-documents)).
3. Let `OAuthClientProvider` run the flow, and refuse an authorization server whose metadata doesn't list `S256` ([Get a token with PKCE](https://rollingedition.com/model-context-protocol-in-practice/s/authorization-code-with-pkce)).
4. Set `validate_token_resource=True`, fill `AccessToken.resource` from the token's `aud`, and treat an `MCPDeprecationWarning` from `AuthSettings` as a failed deployment ([Bind each token to one server](https://rollingedition.com/model-context-protocol-in-practice/s/token-audience)).
5. Send `iss` from every authorization server you run, and advertise it. Keep the SDK's issuer check in the host ([Validate the issuer of each response](https://rollingedition.com/model-context-protocol-in-practice/s/validate-the-issuer)).
6. Map each tool to its scopes, and answer a missing scope with a 403 `insufficient_scope` challenge ([Scope tools by what the token allows](https://rollingedition.com/model-context-protocol-in-practice/s/scopes-per-tool)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/token-audience); its `verifier checks aud, partner's token` line should read 401.

**Pitfalls:**
- Without `validate_token_resource`, a server accepts tokens issued for other servers.
- An authorization server that omits `iss` leaves the host without its mix-up defence.

## Secure tools against misuse

**When:** Before shipping a server that acts for users, or a host that connects to servers you don't operate.

1. Write the boundary table: one row for each pair of parties that exchange data or authority, with what crosses and who checks it. Close any row whose checker is the model ([Draw the trust boundaries](https://rollingedition.com/model-context-protocol-in-practice/s/trust-boundaries)).
2. Accept only tokens whose audience is your server. Call upstream services with the server's own credential, never the bearer token you received ([Never pass a client's token through](https://rollingedition.com/model-context-protocol-in-practice/s/no-token-passthrough)).
3. Take the acting user from the verified token's subject, never from a tool argument. Bind each handle to the user it was issued to ([Keep the server from acting as a confused deputy](https://rollingedition.com/model-context-protocol-in-practice/s/confused-deputy)).
4. Treat every definition from a server you don't operate as untrusted. Pin each approved definition by hash, and show the user any change before enabling it ([Catch poisoned tool descriptions](https://rollingedition.com/model-context-protocol-in-practice/s/tool-poisoning)).
5. Take amounts, owners and limits from server records, never from text a model fills in from a ticket. Log arguments a tool ignores ([Treat ticket text as untrusted data](https://rollingedition.com/model-context-protocol-in-practice/s/untrusted-tool-output)).
6. Ask the user before each call not on the host's list of side-effect-free calls. Build that list per server, never from annotations ([Ask for consent before side effects](https://rollingedition.com/model-context-protocol-in-practice/s/consent-before-side-effects)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/consent-before-side-effects); its `decisions logged` line should read get_order_status allowed by the host's list; issue_refund approved by the user; track_parcel declined by the user.

**Pitfalls:**
- Tests in memory or over stdio never reach the HTTP authorization layer.
- Consent turns into a reflex when nearly every question gets "yes" within a second.

## Build a host that works through tickets

**When:** A host lets a model work through a ticket queue across several MCP servers.

1. Give each server its own auto-mode `Client`, under a key from the host's configuration ([Connect one client per server](https://rollingedition.com/model-context-protocol-in-practice/s/one-client-per-server)).
2. Prefix every tool name with its server's configuration key, and route each call through your own map. Send an unknown name back to the model as an error ([Name tools across servers](https://rollingedition.com/model-context-protocol-in-practice/s/namespace-tools)).
3. Keep the loop bounded: route, consent, timeout, and send every outcome back, errors included. Cap model calls per ticket ([Run the host loop](https://rollingedition.com/model-context-protocol-in-practice/s/run-the-host-loop)).
4. Give each client its own elicitation callback that names its server. Return a decline to the model as an error ([Answer input requests for the user](https://rollingedition.com/model-context-protocol-in-practice/s/answer-input-requests)).
5. Decide which resources reach the model by stated rules, with a size cap ([Put resources in the model's context](https://rollingedition.com/model-context-protocol-in-practice/s/resources-in-context)).
6. Before a reply reaches a customer, compare its promises with the calls that returned results. Send any mismatch to a person, and strip handles such as `quote_id` ([Work through the ticket queue](https://rollingedition.com/model-context-protocol-in-practice/s/work-the-queue)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/run-the-host-loop); its `turn 1 outcome` line should read tool error.

**Pitfalls:**
- A long tool list outgrows the context, since every definition goes into every call.
- Annotations and outputs from servers you don't trust are claims, not facts.

## Test a server and watch it run

**When:** Before releasing a change to a server's tools, or when reading traces.

1. Test each tool in memory with `Client(server, raise_exceptions=True)`, asserting on `structured_content` and `is_error`, and keep one loopback test per shipped transport ([Test tools in memory](https://rollingedition.com/model-context-protocol-in-practice/s/in-memory-tests)).
2. Keep the last release's `tools/list` in the repository, and validate each structured result against it and the new schema in CI. Treat a removed or retyped output field as breaking ([Check schemas as a contract](https://rollingedition.com/model-context-protocol-in-practice/s/schema-contract-tests)).
3. Replay a recorded run of the whole queue in CI, and assert on each ticket's tool sequence ([Replay recorded host runs](https://rollingedition.com/model-context-protocol-in-practice/s/replay-host-runs)).
4. Install an OpenTelemetry SDK and exporter in every server and host. Build dashboards on `mcp.method.name`, `gen_ai.tool.name` and `error.type`, which follow a Development-status convention ([Trace calls with OpenTelemetry](https://rollingedition.com/model-context-protocol-in-practice/s/trace-with-opentelemetry)).
5. Score tool choice on the first tool per tag, and score arguments separately. State the model, prompt and ticket set beside every score ([Measure how often the right tool is chosen](https://rollingedition.com/model-context-protocol-in-practice/s/tool-selection-accuracy)).
6. Retire a tool in three releases: add the replacement, deprecate the old tool, keep both through an announced window, then answer the old name with an error naming the replacement ([Change tools without breaking clients](https://rollingedition.com/model-context-protocol-in-practice/s/change-tools-safely)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/in-memory-tests); its `tests passed` line should read 4 of 4.

**Pitfalls:**
- A span name that holds an order ID or customer ID makes one name per value, past what a backend can index.
- A recording keeps passing after the model changes. Record again at each model change.

## Migrate a 2025-era server

**When:** A server built on a 2025 revision must move to the pinned revision and keep old clients working through a window.

1. Inventory the removed and deprecated features, sorted by status. Fix every removed dependency before a client at the pinned revision connects ([Inventory what the old server depends on](https://rollingedition.com/model-context-protocol-in-practice/s/inventory-2025-features)).
2. Replace each session with an opaque handle that one tool returns and the next takes as an argument. Check the caller on every use, and store it where every replica can read it ([Remove initialize and session IDs](https://rollingedition.com/model-context-protocol-in-practice/s/remove-sessions)).
3. Delete the HTTP+SSE transport rather than porting it, unless your logs show hosts that still use it ([Move from HTTP+SSE to Streamable HTTP](https://rollingedition.com/model-context-protocol-in-practice/s/move-off-http-sse)).
4. Move each pushed elicitation into a resolver, delete sampling, turn roots into a checked parameter, and send logs to standard error ([Replace sampling, roots and logging](https://rollingedition.com/model-context-protocol-in-practice/s/replace-deprecated-features)).
5. Publish a Client ID Metadata Document for each host, and keep dynamic registration only until those hosts move ([Replace dynamic client registration](https://rollingedition.com/model-context-protocol-in-practice/s/replace-dynamic-registration)).
6. Keep the server on the SDK release it was built with until its port passes its tests, then port in one change and pin the new release exactly ([Port the code from SDK 1.x to 2.x](https://rollingedition.com/model-context-protocol-in-practice/s/sdk-1-to-2)).
7. Serve both eras from one `streamable_http_app()` through the window. Count requests by era, and drop the 2025 path only when that count stays at zero for as long as your slowest host takes to upgrade ([Serve old and new clients through the window](https://rollingedition.com/model-context-protocol-in-practice/s/serve-both-revisions)).

**Check:** Run [the example](https://rollingedition.com/model-context-protocol-in-practice/s/inventory-2025-features); its `removed dependencies` line should read 2.

**Pitfalls:**
- A 2025 session lands on another replica and gets 404 "Session not found".
- A proxy that strips unknown headers drops `MCP-Protocol-Version`, and the server picks the wrong era.
- The earliest removal date is not a deadline: the first revision released on or after it may remove the feature. Move before it, and plan by what your logs show.
