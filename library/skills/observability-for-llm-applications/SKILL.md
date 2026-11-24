---
name: observability-for-llm-applications
description: "Use when an LLM application's traces, token counts and cost, latency, failures, alerts, release comparisons, sampling or private data have to be worked out from OpenTelemetry GenAI spans. Covers naming spans to the GenAI conventions, tracing a request across an MCP server into one OTLP backend, deriving cached input tokens and pricing a call, finding the slow step and the failed step, setting a burn-rate alert, gating a release on paired traces, choosing a trace sampling policy, and keeping personal data out of telemetry. When someone explicitly asks to be taught, tutored or quizzed on what this book covers (\"teach me\", \"tutor me\", \"quiz me\"), it also tutors them, one question at a time. Not for a one-off \"explain X\" or \"what is X\"."
license: CC-BY-NC-4.0 AND MIT
compatibility: "The book's examples ran on Python 3.13.16 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Observability for LLM Applications"
  edition: "2026.11.2"
  verified: "2026-11-23"
  examples: "80 of 80 examples pass"
  edition-code: "W9DX-M10H"
  source: "https://rollingedition.com/observability-for-llm-applications"
---

# Observability for LLM Applications

This agent skill is *Observability for LLM Applications*, Edition 2026.11.2, from Rolling Edition. Examples passed Nov 23, 2026: 80 of 80 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `observability-for-llm-applications` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Use the book's terms as it defines them.** The book's Glossary has each term it defines, in the book's own sentence, with its section: https://rollingedition.com/observability-for-llm-applications/glossary. The Rolling Edition MCP server's `define` gives one with its section, its edition and the version it's true for: where the task uses one, it means that.
- **Is this copy current?** Call `check_code` with `W9DX-M10H` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/observability-for-llm-applications
- **Credit the book** when you quote it or reuse its code: Observability for LLM Applications, Edition 2026.11.2, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `observability-for-llm-applications` plugin and the zip on the book's page at rollingedition.ai.

## Name each span by the GenAI conventions

Use when a backend or another team has to read an LLM application's spans by the standard's names, types and kinds. The conventions are at version 0.1.0, a Development release whose names may change in any release.

1. Give each model call an inference span named `{operation} {model}`, with the operation `chat`, as [Span types for each step](https://rollingedition.com/observability-for-llm-applications/s/span-types-for-each-step) gives. Its kind is CLIENT when the model runs in another process and INTERNAL when it runs in the application's own process.
2. Give each retrieval step a retrieval span, each tool run an `execute_tool {tool}` span and each agent run an `invoke_agent` span, using the table in the same section. [The example](https://rollingedition.com/observability-for-llm-applications/s/span-types-for-each-step) prints the names.
3. Check each span's required attributes against its type, as [Which attributes a span must carry](https://rollingedition.com/observability-for-llm-applications/s/requirement-levels) says. A required attribute appears on every span of its type; a conditionally required one appears when its condition holds.
4. Run the validator over the whole run and fail the run on any finding for a span the registry defines, as [Validating against the registry](https://rollingedition.com/observability-for-llm-applications/s/validating-against-the-registry) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/validating-against-the-registry)).

Check: zero findings on registry spans. A span with no known type gets a finding that says so, which means a span still carries a name from before the rename. The validator checks the kind and the required attributes only, so a conditional case can pass it and still lack an attribute ([Which attributes a span must carry](https://rollingedition.com/observability-for-llm-applications/s/requirement-levels)).

## Let the instrumentation package make the model spans

Use when the application calls a model through a client library that ships its own instrumentation, and the spans should come from that package rather than from hand-made code.

1. Install the pinned package, 1.3b0, with `uv pip install -r examples/requirements.txt`, and install the instrumentation once in the start-up code, as [A call through the client](https://rollingedition.com/observability-for-llm-applications/s/a-call-through-the-client) does.
2. Make one call and list the span's attributes, as [What the package emits](https://rollingedition.com/observability-for-llm-applications/s/what-the-package-emits) does. Set them beside the hand-made spans with [Hand-made spans against the instrumented ones](https://rollingedition.com/observability-for-llm-applications/s/hand-made-against-instrumented) ([the example](https://rollingedition.com/observability-for-llm-applications/s/hand-made-against-instrumented)), and rename any that differ.
3. Before relying on content capture, check which variable the package reads. Set the spec's variable, count the content attributes on the span, and compare with the package's own variable, as [The capture switch](https://rollingedition.com/observability-for-llm-applications/s/the-capture-switch) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/the-capture-switch)). A variable the package does not read leaves the span with no content and no error.

Pitfall: each package has its own default for capture. [The capture switch](https://rollingedition.com/observability-for-llm-applications/s/the-capture-switch) gives the defaults of the packages the book compares, so read the one you load.

## Trace a request across an MCP server into one backend

Use when a tool server in another process must join the trace of the request that called it, and both processes' spans must land in one store.

1. Make the calling tool span the current span when the request is sent. The MCP SDK then writes `traceparent` into the request's `_meta`, as [The MCP SDK writes traceparent into _meta](https://rollingedition.com/observability-for-llm-applications/s/traceparent-in-meta) describes. Check the join: the server's span has the caller's client span as its parent, and all of them share one trace ID, as [The server span joins the trace](https://rollingedition.com/observability-for-llm-applications/s/joining-the-trace) shows ([the example](https://rollingedition.com/observability-for-llm-applications/s/joining-the-trace)).
2. Keep work that moves to another thread inside the caller's context. `threading.Thread`, `executor.submit` and `loop.run_in_executor` start with an empty context, while `asyncio.to_thread` and `asyncio.run_coroutine_threadsafe` copy it, as [Context is lost at a thread boundary](https://rollingedition.com/observability-for-llm-applications/s/lost-context) says. Wrap such functions to run in a copy of the caller's context (the book's `carry()`), or use `opentelemetry-instrumentation-threading` for pools you don't own.
3. Count detached roots apart: root spans other than the agent span, and any server span that arrived with no `traceparent`, as [Context is lost at a thread boundary](https://rollingedition.com/observability-for-llm-applications/s/lost-context) defines them. Count orphans apart again: spans whose parent ID names a span the store does not hold, as the same section defines them. The [example](https://rollingedition.com/observability-for-llm-applications/s/lost-context) prints the detached roots; no example counts orphans.
4. Put only the release and the prompt version in baggage, under the keys the section names, and refuse other values, as [What goes in baggage](https://rollingedition.com/observability-for-llm-applications/s/what-goes-in-baggage) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/what-goes-in-baggage)). Baggage can carry sensitive information, so nothing else goes in it.
5. Send each process's spans over OTLP/HTTP to one receiver. Each exporter posts to `/v1/traces` and gets HTTP 200 on success, as [The exporter sends each span over OTLP](https://rollingedition.com/observability-for-llm-applications/s/otlp-over-http) describes. Check that both processes' rows are in the store, as [The book's receiver holds both processes' spans](https://rollingedition.com/observability-for-llm-applications/s/the-book-receiver) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/the-book-receiver)).

Pitfall: the book's receiver keeps its rows in memory for one run. A team needs a store of its own, as [Changing the backend](https://rollingedition.com/observability-for-llm-applications/s/changing-backends) explains.

## Derive cached input tokens and price a call

Use when a bill, or a cost per message, has to be attributed to a route, a user or a release, and the runtime reports no cached-token count.

1. Read the input and output counts for each call. Input tokens include the cached part, so adding cached tokens to input counts them twice, as [Three counts for each call](https://rollingedition.com/observability-for-llm-applications/s/three-token-counts) says.
2. Derive the cached count where the runtime does not report it. Cached input is the prompt tokens minus the tokens the runtime evaluated; the evaluated count is a difference between two calls, because the counters accumulate, as [Cached input, derived from the counters](https://rollingedition.com/observability-for-llm-applications/s/cached-prompt-tokens) shows ([the example](https://rollingedition.com/observability-for-llm-applications/s/cached-prompt-tokens)). A reuse counter that counts graph reuse, not tokens, is not the cached count.
3. Price each call from a dated price table of rates per million tokens. Cached input is billed at its rate and the rest of the input and the output at theirs, from the row that applies on the call's date, as [The price table](https://rollingedition.com/observability-for-llm-applications/s/the-price-table) describes ([the example](https://rollingedition.com/observability-for-llm-applications/s/the-price-table)).
4. Before pricing, check how each provider reports input: Anthropic's `input_tokens` excludes cached tokens, and the conventions ask instrumentation to add them in, so add them before pricing ([The price table](https://rollingedition.com/observability-for-llm-applications/s/the-price-table)).
5. Compute cost at query time from the table, not from a stored cost, and attribute it to route and user as [Cost by route and step](https://rollingedition.com/observability-for-llm-applications/s/cost-per-route) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/cost-per-route)). Total tokens from the meter's counters rather than by summing each span's usage, which double counts, as [Summing spans double counts](https://rollingedition.com/observability-for-llm-applications/s/totals-from-metrics-not-spans) explains ([the example](https://rollingedition.com/observability-for-llm-applications/s/totals-from-metrics-not-spans)).

## Read latency tails with an interval

Use when the median message is fast enough and the slowest messages are not, and the question is which step makes them slow.

1. Walk the critical path back from the root's end: take the child that ends last, then the child that ends last before it starts, until the walk reaches the root's start, as [The critical path sets the end time](https://rollingedition.com/observability-for-llm-applications/s/the-critical-path) describes ([the example](https://rollingedition.com/observability-for-llm-applications/s/the-critical-path)).
2. Split a streamed model call at its first chunk. [Time to first chunk](https://rollingedition.com/observability-for-llm-applications/s/time-to-first-chunk) gives the wait from sending the call to the first streamed piece, and [Prefill against generation](https://rollingedition.com/observability-for-llm-applications/s/prefill-against-generation) separates the model reading the prompt from the model writing the reply ([the example](https://rollingedition.com/observability-for-llm-applications/s/prefill-against-generation)).
3. Take nearest-rank percentiles and state the count, n, beside each. Put an interval on each: the middle 95% of 2,000 bootstrap resamples of messages, not of spans, as [Tail percentiles with intervals](https://rollingedition.com/observability-for-llm-applications/s/tail-percentiles-with-intervals) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/tail-percentiles-with-intervals)).
4. Read a percentile from histogram buckets only to within its bucket, as [Histogram buckets and what they hide](https://rollingedition.com/observability-for-llm-applications/s/histogram-buckets-and-what-they-hide) says ([the example](https://rollingedition.com/observability-for-llm-applications/s/histogram-buckets-and-what-they-hide)).

Pitfall: twenty messages cannot support a tail percentile, as [Tail percentiles with intervals](https://rollingedition.com/observability-for-llm-applications/s/tail-percentiles-with-intervals) explains. Read the n with every percentile.

## Find which step failed

Use when users got no useful answer and the question is which step failed, how often, and why.

1. Count messages that had an error. A message has an error when any of its spans has status ERROR. Count messages or attempts, never ERROR spans, because one fault can leave several, as [MCP errors](https://rollingedition.com/observability-for-llm-applications/s/mcp-errors) and [How a span records failure](https://rollingedition.com/observability-for-llm-applications/s/how-a-span-records-failure) set out ([the example](https://rollingedition.com/observability-for-llm-applications/s/how-a-span-records-failure)).
2. Split failures by `error.type`: the class name of the exception the caller sees, or the registry value where one exists, `tool_error` for an MCP result with `isError` set, which raises nothing ([MCP errors](https://rollingedition.com/observability-for-llm-applications/s/mcp-errors)). A span with no `error.type` is still an error, so never filter on the attribute to find failures ([How a span records failure](https://rollingedition.com/observability-for-llm-applications/s/how-a-span-records-failure)) ([the example](https://rollingedition.com/observability-for-llm-applications/s/how-a-span-records-failure)).
3. Find replies cut at the token cap: a finish reason of `length` in `gen_ai.response.finish_reasons`. [Replies cut at the cap](https://rollingedition.com/observability-for-llm-applications/s/replies-cut-at-the-cap) explains that such a reply raises nothing, so the status rule misses it ([the example](https://rollingedition.com/observability-for-llm-applications/s/replies-cut-at-the-cap)).
4. Find wrong routes by comparing each route's choice with the labelled expected route. The route span holds that label in an event. A fallback reply is right only for a message that no tool or article resolves, as [Wrong routes against the labels](https://rollingedition.com/observability-for-llm-applications/s/wrong-routes-against-labels) says ([the example](https://rollingedition.com/observability-for-llm-applications/s/wrong-routes-against-labels)).
5. Write one query for each failure mode over the receiver's rows, and keep the baseline and the incident day apart, as [Querying each failure mode](https://rollingedition.com/observability-for-llm-applications/s/querying-each-failure-mode) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/querying-each-failure-mode)).

Pitfall: keep both counts and label each: errors by span status ([How a span records failure](https://rollingedition.com/observability-for-llm-applications/s/how-a-span-records-failure)) and failed messages, those whose user got no reply ([Service-level objectives](https://rollingedition.com/observability-for-llm-applications/s/service-level-objectives)). A refused request whose retry got a reply, or a lookup that timed out on both attempts and still got a reply, is an error but not a failed message.

## Set a burn-rate alert

Use when someone must be paged about a failure rate, not about each failure.

1. Set the objective: the share of messages that must get a reply over the period. The error budget is 1 minus that share, as [Service-level objectives](https://rollingedition.com/observability-for-llm-applications/s/service-level-objectives) defines them ([the example](https://rollingedition.com/observability-for-llm-applications/s/service-level-objectives)).
2. Compute each window's burn rate as its failed share of messages divided by the error budget. Read each window as the difference between two cumulative reads of the same histogram, as [Burn rate](https://rollingedition.com/observability-for-llm-applications/s/burn-rate) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/burn-rate)).
3. Page only when the one-hour window and the five-minute window both reach 14.4, and the hour holds at least 10 messages. The short window clears the page once the spend stops, as [An alert that stays quiet](https://rollingedition.com/observability-for-llm-applications/s/an-alert-that-stays-quiet) sets it ([the example](https://rollingedition.com/observability-for-llm-applications/s/an-alert-that-stays-quiet)).
4. Run the same alert over a quiet day and check that it pages nowhere, as [Test the same alert on a quiet day](https://rollingedition.com/observability-for-llm-applications/s/quiet-day-on-baseline-day-two) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/quiet-day-on-baseline-day-two)).
5. Keep each metric's labels to a few values each, such as error type, operation and model; never a user, since a label per user adds a series per user, as [Cardinality](https://rollingedition.com/observability-for-llm-applications/s/cardinality) explains ([the example](https://rollingedition.com/observability-for-llm-applications/s/cardinality)).

Pitfall: the 14.4 comes from the *Site Reliability Workbook*'s traffic ([Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)). Treat it as a starting point, as [An alert that stays quiet](https://rollingedition.com/observability-for-llm-applications/s/an-alert-that-stays-quiet) says. A fault the model answers around, like the timeout window, never reaches the error objective, so watch the tool's ERROR attempts for it ([One page on the incident day](https://rollingedition.com/observability-for-llm-applications/s/an-alert-that-stays-quiet)).

## Gate a release on paired traces

Use when a release claims to change nothing that matters, and the question is which numbers moved, on the same messages.

1. Mark each release: `service.version` on the resource and `gen_ai.prompt.version` on each inference span, so a query splits the traces by release, as [Release markers in the spans](https://rollingedition.com/observability-for-llm-applications/s/release-markers-in-the-spans) says ([the example](https://rollingedition.com/observability-for-llm-applications/s/release-markers-in-the-spans)).
2. Run the baseline and the candidate on the same messages. For each message, take the candidate's value minus the baseline's, for latency, tokens, cost, errors and route, as [Paired comparison on messages](https://rollingedition.com/observability-for-llm-applications/s/paired-comparison-on-messages) does ([the example](https://rollingedition.com/observability-for-llm-applications/s/paired-comparison-on-messages)).
3. Put an interval on each difference, and gate with the regression rule in [The CI gate](https://rollingedition.com/observability-for-llm-applications/s/the-ci-gate): a release is flagged when the end of its interval nearest the limit lies past the limit. A flag therefore means worse than the limit beyond the 95% interval ([the example](https://rollingedition.com/observability-for-llm-applications/s/the-ci-gate)).
4. Run the same gate on a second baseline day. It must not flag ([the example](https://rollingedition.com/observability-for-llm-applications/s/the-ci-gate)).

## Choose a trace sampling policy

Use when keeping every trace costs too much, and the kept set must still hold the failures and the slow tail.

1. Start with head sampling at a fixed ratio on the trace ID. Every span of a trace gets the same answer on every run, but the sampler cannot aim at failures, as [Head sampling decides before the trace runs](https://rollingedition.com/observability-for-llm-applications/s/head-sampling) explains ([the example](https://rollingedition.com/observability-for-llm-applications/s/head-sampling)).
2. Make each span follow its parent's sampled flag, so a server in another process keeps the spans of a sampled trace, as [Children follow the root's decision](https://rollingedition.com/observability-for-llm-applications/s/parent-based-sampling) says ([the example](https://rollingedition.com/observability-for-llm-applications/s/parent-based-sampling)).
3. Add tail rules, which decide once the whole trace is in. The chapter's rule keeps a trace whose message has an error, one past the latency objective, and one whose model calls cost more than a baseline percentile, as [Tail sampling reads the whole trace](https://rollingedition.com/observability-for-llm-applications/s/tail-sampling) sets out ([the example](https://rollingedition.com/observability-for-llm-applications/s/tail-sampling)).
4. Estimate totals only for a split that the counters cannot make. Scale a head sample's total by the inverse of its ratio. Print its 95% interval, the estimate plus or minus 1.96 standard errors from the sampled traces alone. This is the sample's own interval, not the bootstrap of [Tail percentiles with intervals](https://rollingedition.com/observability-for-llm-applications/s/tail-percentiles-with-intervals). Check the estimate against the counter total for the same day where one exists. At small kept counts the interval holds the full count less often than its label says. Do not scale tail-kept traces by the ratio, since they are not a fixed share of the day, as [Estimate the day's totals from a sample](https://rollingedition.com/observability-for-llm-applications/s/estimating-totals-from-a-sample) explains ([the example](https://rollingedition.com/observability-for-llm-applications/s/estimating-totals-from-a-sample)).
5. Set the retention period with the team that runs the backend. The chapter sets none, and [Retention](https://rollingedition.com/observability-for-llm-applications/s/retention) says why.

## Keep personal data out of telemetry

Use when spans could carry user names, email addresses, user IDs, or the people and places a request's text mentions.

1. Leave content capture off unless a stated purpose needs prompts or replies. Check the default of each package the service loads, as [Capture off comes first](https://rollingedition.com/observability-for-llm-applications/s/capture-off-by-default) says ([the example](https://rollingedition.com/observability-for-llm-applications/s/capture-off-by-default)).
2. If capture is on, the content lands in span attributes or in log records, depending on the mode, so check where each mode writes, as [What leaks when capture is on](https://rollingedition.com/observability-for-llm-applications/s/what-leaks-when-capture-is-on) shows ([the example](https://rollingedition.com/observability-for-llm-applications/s/what-leaks-when-capture-is-on)).
3. Redact before the span is stored. Redact in every process with a span processor that exports a redacted copy as each span ends, because the SDK freezes a span's attributes at that point. Redact again where every service's spans pass, such as the Collector, because a process's redactor never sees another process's spans, as [Redaction is defence in depth](https://rollingedition.com/observability-for-llm-applications/s/redaction-as-defence-in-depth) describes ([the example](https://rollingedition.com/observability-for-llm-applications/s/keyed-user-pseudonyms)).
4. Replace each user ID with a keyed pseudonym: an HMAC-SHA256 of the ID under a key, kept to twelve hexadecimal digits. Keep the key out of the code and out of the telemetry. The book's key is a demonstration, as [Keyed user pseudonyms](https://rollingedition.com/observability-for-llm-applications/s/keyed-user-pseudonyms) says.
5. Drop `exception.stacktrace` and keep the exception event's class and message, rather than replacing the stack trace, since its file paths name the folders of the process that ran the code, with capture off as well. Do it where every service's spans pass. Ask the team that owns each server to set `record_exception=False` and record the class and message by hand ([Stack traces leak without capture](https://rollingedition.com/observability-for-llm-applications/s/stack-traces-leak-without-capture)). The [example](https://rollingedition.com/observability-for-llm-applications/s/what-leaks-when-capture-is-on) shows the leak, and [the scan](https://rollingedition.com/observability-for-llm-applications/s/redaction-as-defence-in-depth) shows both processes' stack traces removed by redaction at the receiver.
6. Where content must be kept, store it by reference: a `*_ref` attribute on the span, and the content in a store with its own access rules, as [Keep content by reference](https://rollingedition.com/observability-for-llm-applications/s/keep-content-by-reference) describes ([the example](https://rollingedition.com/observability-for-llm-applications/s/keep-content-by-reference)).
7. Scan what is left for the values redaction should have removed, and count them. Seed the test traffic with known identifiers; after redaction their count must be zero. Count, and don't assert, the free-text names the redactor can't recognise, as [Count what redaction leaves](https://rollingedition.com/observability-for-llm-applications/s/scanning-and-counting) explains ([the example](https://rollingedition.com/observability-for-llm-applications/s/redaction-as-defence-in-depth)).

## Teach this book, when asked

**When:** only when the person you're working with explicitly asks to be taught, tutored or quizzed on this book, one of its chapters or a topic it covers ("teach me", "tutor me", "quiz me", "help me master"). A one-off question ("explain X", "what is X", "how do I use X") gets a normal answer from the procedures above, with no quiz. If you can't tell which they want, ask one short question: a quick answer, or should you teach it properly?

**The topics** are the book's chapters, in order:

1. [Trace a request, then ask where its time went](https://rollingedition.com/observability-for-llm-applications/trace-a-request)
2. [Name spans the way the standard does](https://rollingedition.com/observability-for-llm-applications/name-spans)
3. [Let the client library instrument the calls](https://rollingedition.com/observability-for-llm-applications/client-library-instrumentation)
4. [Follow a request across processes](https://rollingedition.com/observability-for-llm-applications/across-processes)
5. [Send traces to a backend you can run](https://rollingedition.com/observability-for-llm-applications/send-to-a-backend)
6. [Attribute tokens and cost to each step](https://rollingedition.com/observability-for-llm-applications/tokens-and-cost)
7. [Find where the latency comes from](https://rollingedition.com/observability-for-llm-applications/latency-sources)
8. [Find the step that failed](https://rollingedition.com/observability-for-llm-applications/find-the-failure)
9. [Set alerts on the assistant's metrics](https://rollingedition.com/observability-for-llm-applications/alerts-on-metrics)
10. [Catch a regression in the traces](https://rollingedition.com/observability-for-llm-applications/catch-a-regression)
11. [Choose which traces to keep](https://rollingedition.com/observability-for-llm-applications/choose-what-to-keep)
12. [Keep private data out of telemetry](https://rollingedition.com/observability-for-llm-applications/keep-private-data-out)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. The Rolling Edition MCP server's `get_contents` lists each chapter's sections, and `get_section` reads one, with its examples.

**Start**

1. Read each section, with `get_section`, before you ask about it. Judge every answer against the book: the section's text, the term's definition from `define` and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" below.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
Trace a request, then ask where its time went    overall: █████░░░░░ 53%
------------------------------------------------------------------------
One message, one trace        ████████░░  4/5  alone
Replay and the virtual clock  ██████░░░░  3/5  <- now
Spans by hand                 ██░░░░░░░░  1/5
------------------------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what it prints, or what would change if one line changed, then compare with the output its section shows.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/observability-for-llm-applications/s/ followed by its ID.

**Levels are earned**

- Raise a level only after two or more separate checks, at least one of them recalled unprompted, not just after you told them the answer.
- A vague or partly right answer isn't right. Probe until you know. Never credit them with an insight they didn't state.
- Now and then, without warning, ask again about an earlier topic. If they miss, lower its level and go back to it.
- Level 5 needs an edge case or a hard question handled, and an explanation you'd trust them to teach from.
- No flattery: "Not quite: why would X happen if Y were true?" beats "Great try!"

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures above covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.2 and its code `W9DX-M10H`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/observability-for-llm-applications/changes lists them.

## Reading in another language

When the person you're working with wants to read part of this book in another language, and the Rolling Edition MCP server is connected, first call its `get_section` with `language`: where Rolling Edition has its own translation of the book in that language (`get_contents` lists them), present each section as it comes, with the facts of its `translation`, and translate only the sections it lists as `untranslated`. Otherwise, translate it for them from its sections, read with the Rolling Edition MCP server's `get_section`. Translate the prose faithfully and in full: don't summarize, skip or add anything. Leave these exactly as they are: code, commands, output, file names, identifiers, inline code, package names and versions, numbers and URLs. Where practitioners who read the language usually keep a technical term in English, keep it, and give a short gloss in parentheses the first time, where that helps. Keep the headings and the structure: lists, tables, and the examples in their places. Begin by saying that it's your translation of *Observability for LLM Applications*, Edition 2026.11.2, from Rolling Edition, licensed CC BY-NC 4.0, with the chapter's link, and keep each section's link from its citation block. For a long chapter, translate a section at a time and offer to go on after each. The Rolling Edition MCP server's `read_in_my_language` prompt asks for the same.
