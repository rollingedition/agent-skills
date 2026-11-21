---
title: "Glossary"
book: "Model Context Protocol in Practice"
edition: "2026.11.16"
canonical: "https://rollingedition.com/model-context-protocol-in-practice/glossary"
---

# Glossary of *Model Context Protocol in Practice*

The 69 terms this book defines, as Edition 2026.11.16 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/model-context-protocol-in-practice/glossary

## access token

An access token is a bearer credential, so whoever holds it can present it.

- Defined in: [Bind each token to one server](authorization.md#token-audience)
- Address: https://rollingedition.com/concepts/artificial-intelligence/access-token

## application-driven

The specification calls resources application-driven: hosts decide how to use them, whether by letting the user pick, by their own heuristics, or by asking the model

- Defined in: [Put resources in the model's context](build-a-host.md#resources-in-context)
- Address: https://rollingedition.com/concepts/model-context-protocol/application-driven

## argument completion

Argument completion lets the host ask the server for suggestions while the user types.

- Defined in: [Complete arguments for the user](resources-and-prompts.md#argument-completion)
- Address: https://rollingedition.com/concepts/model-context-protocol/argument-completion

## authorization server

an authorization server issues the tokens, either beside the MCP server or apart from it

- Defined in: [Authorize clients with OAuth](authorization.md)
- Address: https://rollingedition.com/concepts/artificial-intelligence/authorization-server

## cache scope

cacheScope, either "public", which a cache may share across callers, or "private", which it MUST NOT share across authorization contexts

- Also: cacheScope
- Defined in: [Cache list results](what-mcp-adds.md#cache-list-results)
- Address: https://rollingedition.com/concepts/model-context-protocol/cache-scope

## capability

A capability is something a client or server declares it supports, such as a server that offers tools or a client that can answer a request for input.

- Defined in: [Separate the host, the client and the server](what-mcp-adds.md#host-client-server)
- Address: https://rollingedition.com/concepts/model-context-protocol/capability

## capability laundering

Capability laundering is hiding what a tool's code can do behind a description that leaves it out

- Defined in: [Draw the trust boundaries](mcp-security.md#trust-boundaries)
- Address: https://rollingedition.com/concepts/ai-agents/capability-laundering

## client

A client is the host's connection to one server

- The same as: https://rollingedition.com/concepts/ai-agents/mcp-client
- Defined in: [Separate the host, the client and the server](what-mcp-adds.md#host-client-server)
- Address: https://rollingedition.com/concepts/model-context-protocol/client

## Client ID Metadata Document

A Client ID Metadata Document makes the client ID a URL.

- Implemented by: mcp 2.3.0
- Defined in: [Identify the client with a metadata document](authorization.md#client-id-metadata-documents)
- Address: https://rollingedition.com/concepts/artificial-intelligence/client-id-metadata-document

## confused deputy

In the classic sense, a confused deputy is a program that holds authority of its own, takes a name from its caller, and uses its authority on that name where the caller had none.

- Defined in: [Keep the server from acting as a confused deputy](mcp-security.md#confused-deputy)
- Address: https://rollingedition.com/concepts/artificial-intelligence/confused-deputy

## consent

Consent is the host asking the user before a call that changes something

- Defined in: [Shape tools around tasks, not endpoints](design-tools.md#tasks-not-endpoints)
- Address: https://rollingedition.com/concepts/ai-agents/consent

## core protocol

The core protocol is what every client and server must implement.

- Contrasts with: extension
- Defined in: [Negotiate an extension](tasks-and-extensions.md#negotiate-an-extension)
- Address: https://rollingedition.com/concepts/model-context-protocol/core-protocol

## destructiveHint

a tool that changes something may destroy or overwrite data, rather than only add to it

- Also: destructive hint
- Part of: tool annotation
- Defined in: [Mark what a tool changes with annotations](design-tools.md#tool-annotations)
- Address: https://rollingedition.com/concepts/model-context-protocol/destructive-hint

## DNS rebinding

With DNS rebinding, an attacker's domain can be made to resolve to 127.0.0.1 after the page loads, so the browser treats the local server as part of the attacker's site.

- Defined in: [Reject requests from other origins](streamable-http.md#validate-origin)
- Address: https://rollingedition.com/concepts/artificial-intelligence/dns-rebinding

## dual-era

a dual-era server, which serves both eras on the same endpoint

- Defined in: [Serve old and new clients through the window](migrate-from-2025.md#serve-both-revisions)
- Address: https://rollingedition.com/concepts/model-context-protocol/dual-era

## earliest removal

An earliest removal is the date when a feature becomes eligible to go, not when it goes.

- Defined in: [Inventory what the old server depends on](migrate-from-2025.md#inventory-2025-features)
- Address: https://rollingedition.com/concepts/model-context-protocol/earliest-removal

## elicitation

elicitation: a structured question that a server sends and the client shows the user

- Kinds: form mode
- Kinds: URL mode
- Implemented by: mcp 2.3.0
- Defined in: [Ask the user in the middle of a call](multi-round-trip-requests.md)
- Address: https://rollingedition.com/concepts/model-context-protocol/elicitation

## era

A client still learns its server's era: the pinned revision or a 2025 one.

- Defined in: [Connect one client per server](build-a-host.md#one-client-per-server)
- Address: https://rollingedition.com/concepts/model-context-protocol/era

## extension

Tasks is an extension, an optional addition to the protocol that both sides must agree to use.

- Implemented by: mcp 2.3.0
- Defined in: [Run long work as tasks](tasks-and-extensions.md)
- Address: https://rollingedition.com/concepts/model-context-protocol/extension

## extension identifier

An extension's identifier is a vendor prefix, a slash and a name.

- Defined in: [Negotiate an extension](tasks-and-extensions.md#negotiate-an-extension)
- Address: https://rollingedition.com/concepts/model-context-protocol/extension-identifier

## form mode

In form mode, the server sends a message and a schema, the client renders a form, and the answer returns through the client.

- A kind of: elicitation
- Defined in: [Ask for structured input with elicitation](multi-round-trip-requests.md#elicitation-forms)
- Address: https://rollingedition.com/concepts/model-context-protocol/form-mode

## handle

a tool that needs state from an earlier call gets it as an explicit handle: one tool returns an ID, and the next takes it as an argument

- Also: handles, explicit handle
- Defined in: [Shape tools around tasks, not endpoints](design-tools.md#tasks-not-endpoints)
- Address: https://rollingedition.com/concepts/ai-agents/handle

## host

The host is the application the user works in.

- The same as: https://rollingedition.com/concepts/ai-agents/mcp-host
- Defined in: [Separate the host, the client and the server](what-mcp-adds.md#host-client-server)
- Address: https://rollingedition.com/concepts/model-context-protocol/host

## host loop

The book's host loop, lib.host, is a small host the book writes itself, so each step is visible.

- A kind of: host
- Defined in: [Let a model choose the tool](mcp-end-to-end.md#let-a-model-choose)
- Address: https://rollingedition.com/concepts/ai-agents/host-loop

## idempotentHint

calling the tool again with the same arguments has no further effect

- Also: idempotent hint
- Part of: tool annotation
- Defined in: [Mark what a tool changes with annotations](design-tools.md#tool-annotations)
- Address: https://rollingedition.com/concepts/model-context-protocol/idempotent-hint

## implicit poisoning

In implicit poisoning, one tool's metadata steers the agent to a different, more privileged tool, and the poisoned tool is never called.

- Defined in: [Catch poisoned tool descriptions](mcp-security.md#tool-poisoning)
- Address: https://rollingedition.com/concepts/ai-agents/implicit-poisoning

## indirect prompt injection

Indirect prompt injection is the general name for data that carries instructions: text the application retrieves, here a customer's ticket, contains instructions that the model follows, and those instructions can decide which tools it calls

- Defined in: [Treat ticket text as untrusted data](mcp-security.md#untrusted-tool-output)
- Address: https://rollingedition.com/concepts/large-language-models/indirect-prompt-injection

## input request

The server answers the call with an input request instead of a result, and the client calls again with the answer.

- Defined in: [Ask the user in the middle of a call](multi-round-trip-requests.md)
- Address: https://rollingedition.com/concepts/model-context-protocol/input-request

## MCP Apps

MCP Apps is an official extension that changes how a result is shown.

- A kind of: extension
- Defined in: [Know what MCP Apps add](tasks-and-extensions.md#mcp-apps)
- Address: https://rollingedition.com/concepts/model-context-protocol/mcp-apps

## mix-up attack

In a mix-up, an attacker's authorization server gets the host to start a flow with it, then sends the user's browser on to an honest authorization server.

- Also: mix-up
- Defined in: [Validate the issuer of each response](authorization.md#validate-the-issuer)
- Address: https://rollingedition.com/concepts/artificial-intelligence/mix-up-attack

## Model Context Protocol

The Model Context Protocol (MCP) is how an application that uses a model gets tools and data from programs it didn't write.

- Also: MCP
- Implemented by: mcp 2.3.0
- The same as: https://rollingedition.com/concepts/ai-agents/model-context-protocol
- Defined in: [MCP end to end](mcp-end-to-end.md)
- Address: https://rollingedition.com/concepts/artificial-intelligence/mcp-protocol

## Multi Round-Trip Request

a Multi Round-Trip Request, a pattern in which one call can end with a question instead of a result

- Implemented by: mcp 2.3.0
- Defined in: [Ask the user in the middle of a call](multi-round-trip-requests.md)
- Address: https://rollingedition.com/concepts/model-context-protocol/multi-round-trip-request

## openWorldHint

the tool reaches entities outside a closed domain, such as the web

- Also: open world hint
- Part of: tool annotation
- Defined in: [Mark what a tool changes with annotations](design-tools.md#tool-annotations)
- Address: https://rollingedition.com/concepts/model-context-protocol/open-world-hint

## PKCE

PKCE binds the code to the client that asked for it.

- Also: Proof Key for Code Exchange
- Implemented by: mcp 2.3.0
- Defined in: [Get a token with PKCE](authorization.md#authorization-code-with-pkce)
- Address: https://rollingedition.com/concepts/artificial-intelligence/pkce

## primitive

A server's three primitives are its tools, resources and prompts

- Also: primitives
- Kinds: tool
- Kinds: resource
- Kinds: prompt
- Defined in: [Put each capability in the right primitive](what-mcp-adds.md#choose-a-primitive)
- Address: https://rollingedition.com/concepts/model-context-protocol/primitive

## progress

Progress is MCP's answer to a long call: the server reports how far it has got while the call runs

- Also: notifications/progress
- Part of: core protocol
- Defined in: [Stream progress on a long call](streamable-http.md#stream-progress)
- Address: https://rollingedition.com/concepts/model-context-protocol/progress

## progressive discovery

progressive discovery, a small search tool that returns definitions on demand

- Defined in: [What goes wrong in production](build-a-host.md#build-a-host-in-production)
- Address: https://rollingedition.com/concepts/ai-agents/progressive-discovery

## prompt

A prompt is a template of messages, with arguments, that the server defines and the user picks

- Also: prompts, MCP prompt
- Defined in: [Prompts are templates the user chooses](what-mcp-adds.md#prompts-user-chooses)
- Address: https://rollingedition.com/concepts/model-context-protocol/prompt

## Protected Resource Metadata

Protected Resource Metadata (RFC 9728), a JSON document that names the resource and lists at least one authorization server

- Implemented by: mcp 2.3.0
- Defined in: [Find the authorization server from the resource](authorization.md#protected-resource-metadata)
- Address: https://rollingedition.com/concepts/artificial-intelligence/protected-resource-metadata

## protocol error

A protocol error is a JSON-RPC error, for an unknown tool, a request that doesn't fit the tools/call schema, or a server failure.

- Also: protocol errors
- Contrasts with: tool execution error
- Defined in: [Report failures as tool results](design-tools.md#tool-errors)
- Address: https://rollingedition.com/concepts/ai-agents/protocol-error

## readOnlyHint

the tool doesn't change its environment

- Also: read-only hint
- Part of: tool annotation
- Defined in: [Mark what a tool changes with annotations](design-tools.md#tool-annotations)
- Address: https://rollingedition.com/concepts/model-context-protocol/read-only-hint

## requestState

requestState is an opaque string the client must send back.

- Defined in: [Return an input request instead of a result](multi-round-trip-requests.md#return-an-input-request)
- Address: https://rollingedition.com/concepts/model-context-protocol/request-state

## resource

A resource is data a server exposes under a URI, and the application decides when to read it and what to do with it

- Also: resources
- Contrasts with: tool
- Defined in: [Resources are data the application chooses](what-mcp-adds.md#resources-application-chooses)
- Address: https://rollingedition.com/concepts/model-context-protocol/resource

## resource annotation

A resource's annotations are three hints the host may use or ignore

- Also: resource annotations
- Defined in: [Expose the policies as resources](resources-and-prompts.md#policies-as-resources)
- Address: https://rollingedition.com/concepts/model-context-protocol/resource-annotation

## resource template

A resource template names many resources with one URI template, written in the syntax of RFC 6570

- Defined in: [Address records with resource templates](resources-and-prompts.md#resource-templates)
- Address: https://rollingedition.com/concepts/model-context-protocol/resource-template

## rug pull

a rug pull, where a server changes a definition after the user approved it

- A kind of: tool poisoning
- Defined in: [Catch poisoned tool descriptions](mcp-security.md#tool-poisoning)
- Address: https://rollingedition.com/concepts/ai-agents/rug-pull

## server

A server exposes capabilities, such as tools, and knows nothing else about the host.

- The same as: https://rollingedition.com/concepts/ai-agents/mcp-server
- Defined in: [Separate the host, the client and the server](what-mcp-adds.md#host-client-server)
- Address: https://rollingedition.com/concepts/model-context-protocol/server

## shadowing

shadowing, where one server's description changes how the model uses another server's tools

- A kind of: tool poisoning
- Defined in: [Catch poisoned tool descriptions](mcp-security.md#tool-poisoning)
- Address: https://rollingedition.com/concepts/ai-agents/shadowing

## span

an application creates spans, each a named, timed operation with attributes and a parent

- Defined in: [Trace calls with OpenTelemetry](test-and-observe.md#trace-with-opentelemetry)
- Address: https://rollingedition.com/concepts/artificial-intelligence/span

## stdio

server.run() serves over stdio, where the client starts the server as a subprocess and the two exchange messages on standard input and output

- Also: stdio transport
- True for: mcp 2.3.0
- Implemented by: mcp 2.3.0
- Defined in: [Wrap one endpoint as a tool](mcp-end-to-end.md#wrap-an-endpoint-as-a-tool)
- Address: https://rollingedition.com/concepts/model-context-protocol/stdio

## step-up

Step-up is the 403 from Scope tools by what the token allows and the client's answer to it: on insufficient_scope, the client authorizes again with the union of the scopes it asked for before and the scopes in the challenge, retries, and limits how many times it tries

- Implemented by: mcp 2.3.0
- Defined in: [Ask for more scope when a call needs it](authorization.md#step-up-scopes)
- Address: https://rollingedition.com/concepts/artificial-intelligence/step-up

## sticky sessions

sticky sessions, which route every request carrying the same Mcp-Session-Id to the replica that held the session

- Also: sticky routing
- Defined in: [Run replicas without sticky sessions](streamable-http.md#scale-without-sessions)
- Address: https://rollingedition.com/concepts/artificial-intelligence/sticky-sessions

## Streamable HTTP

For a server that many hosts share, the Model Context Protocol (MCP) defines a second transport, Streamable HTTP.

- Also: Streamable HTTP transport
- Defined in: [Serve over Streamable HTTP](streamable-http.md)
- Address: https://rollingedition.com/concepts/model-context-protocol/streamable-http

## structured content

structuredContent: the result's data as JSON that a program can read without parsing text

- Also: structuredContent
- The same as: https://rollingedition.com/concepts/ai-agents/structured-content
- Defined in: [Return structured content with an output schema](design-tools.md#structured-output)
- Address: https://rollingedition.com/concepts/model-context-protocol/structured-content

## task

a task: the call's work, whose status the client asks for as often as the server suggests, and whose result waits on the server until the client fetches it

- Contrasts with: progress
- Defined in: [Run long work as tasks](tasks-and-extensions.md)
- Address: https://rollingedition.com/concepts/model-context-protocol/task

## task handle

A task's handle is a CreateTaskResult: a result whose resultType is "task" instead of "complete".

- Defined in: [Start a task instead of waiting](tasks-and-extensions.md#start-a-task)
- Address: https://rollingedition.com/concepts/model-context-protocol/task-handle

## task lifetime

A task's lifetime is its ttlMs, counted from createdAt, or null for no limit, and the server may change it.

- Defined in: [Expire and cancel tasks](tasks-and-extensions.md#task-lifetime)
- Address: https://rollingedition.com/concepts/model-context-protocol/task-lifetime

## Tasks extension

With the Tasks extension, the server answers the call at once with a handle to a task

- A kind of: extension
- Defined in: [Run long work as tasks](tasks-and-extensions.md)
- Address: https://rollingedition.com/concepts/model-context-protocol/tasks-extension

## terminal status

The completed, failed and cancelled statuses are terminal, and once a task reaches one, its state doesn't change

- Defined in: [Poll a task and fetch its result](tasks-and-extensions.md#poll-a-task)
- Address: https://rollingedition.com/concepts/model-context-protocol/terminal-status

## token passthrough

a server either accepts a token that was issued to someone else or forwards the token it received to the API behind it

- Defined in: [Never pass a client's token through](mcp-security.md#no-token-passthrough)
- Address: https://rollingedition.com/concepts/artificial-intelligence/token-passthrough

## tool

A tool is a named action with a description and an input schema, and the model decides whether to call it and with what

- Also: tools
- Contrasts with: resource
- The same as: https://rollingedition.com/concepts/search-and-recommendation/tool
- Defined in: [Tools are actions the model chooses](what-mcp-adds.md#tools-model-chooses)
- Address: https://rollingedition.com/concepts/ai-agents/tool

## tool annotation

A tool's annotations tell the host what a call will do before it's made

- Also: tool annotations, ToolAnnotations
- Part of: tool definition
- The same as: https://rollingedition.com/concepts/ai-agents/tool-annotation
- Defined in: [Mark what a tool changes with annotations](design-tools.md#tool-annotations)
- Address: https://rollingedition.com/concepts/model-context-protocol/tool-annotation

## tool definition

A tool's definition is text from its server that the host passes to the model: its description, input schema and annotations.

- Defined in: [Catch poisoned tool descriptions](mcp-security.md#tool-poisoning)
- Address: https://rollingedition.com/concepts/ai-agents/tool-definition

## tool execution error

A tool execution error is an ordinary result with isError set to true, for an API failure, an invalid input or a broken business rule.

- Also: tool execution errors, execution error
- Contrasts with: protocol error
- Defined in: [Report failures as tool results](design-tools.md#tool-errors)
- Address: https://rollingedition.com/concepts/ai-agents/tool-execution-error

## tool poisoning

Tool poisoning puts instructions for the model into a tool's definition.

- Defined in: [Catch poisoned tool descriptions](mcp-security.md#tool-poisoning)
- Address: https://rollingedition.com/concepts/ai-agents/tool-poisoning

## tool-selection accuracy

tool-selection accuracy: the share of cases in which the model's first call uses the tool a correct agent would use, often called top-1 accuracy

- Also: top-1 accuracy
- Defined in: [Measure how often the right tool is chosen](test-and-observe.md#tool-selection-accuracy)
- Address: https://rollingedition.com/concepts/ai-agents/tool-selection-accuracy

## trust boundary

A trust boundary is a place where data or authority passes from one party to another that shouldn't take it on faith.

- Defined in: [Draw the trust boundaries](mcp-security.md#trust-boundaries)
- Address: https://rollingedition.com/concepts/artificial-intelligence/trust-boundary

## TTL

ttlMs, how many milliseconds the result stays fresh, like HTTP's max-age

- Also: ttlMs
- Defined in: [Cache list results](what-mcp-adds.md#cache-list-results)
- Address: https://rollingedition.com/concepts/model-context-protocol/ttl

## URL mode

In URL mode, the server sends the user to a web page, not a form

- A kind of: elicitation
- Defined in: [Ask for structured input with elicitation](multi-round-trip-requests.md#elicitation-forms)
- Address: https://rollingedition.com/concepts/model-context-protocol/url-mode
