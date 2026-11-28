---
title: "Glossary"
book: "Observability for LLM Applications"
edition: "2026.11.4"
canonical: "https://rollingedition.com/observability-for-llm-applications/glossary"
---

# Glossary of *Observability for LLM Applications*

The 78 terms this book defines, as Edition 2026.11.4 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/observability-for-llm-applications/glossary

## agent-invocation span

An agent-invocation span is the span of one invocation of an agent.

- A kind of: span
- Defined in: [Span types for each step](name-spans.md#span-types-for-each-step)
- Address: https://rollingedition.com/concepts/llm-observability/agent-invocation-span

## attribute

An attribute is a key and a value recorded on a span or a resource, such as gen_ai.request.model.

- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/attribute

## automatic instrumentation

automatic instrumentation collects telemetry with no change to the application's source code

- Defined in: [A call through the client](client-library-instrumentation.md#a-call-through-the-client)
- Address: https://rollingedition.com/concepts/llm-observability/automatic-instrumentation

## backend

A backend stores spans and answers queries over them.

- Defined in: [The exporter sends each span over OTLP](send-to-a-backend.md#otlp-over-http)
- Address: https://rollingedition.com/concepts/llm-observability/backend

## baggage

Baggage is a set of key-value pairs that travels with the context into every later process when every process along the way propagates it.

- True for: opentelemetry-api 1.45.2
- Defined in: [What goes in baggage](across-processes.md#what-goes-in-baggage)
- Address: https://rollingedition.com/concepts/llm-observability/baggage

## burn rate

the burn rate is how fast failures spend it, where 1 spends it exactly by the period's end

- Computed from: error budget
- Defined in: [Service-level objectives](alerts-on-metrics.md#service-level-objectives)
- Address: https://rollingedition.com/concepts/llm-observability/burn-rate

## cached input tokens

cached input tokens are the part its cache held

- Defined in: [Three counts for each call](tokens-and-cost.md#three-token-counts)
- Address: https://rollingedition.com/concepts/llm-observability/cached-input-tokens

## cardinality

A metric's cardinality is the number of distinct attribute combinations it is recorded with, each a series to store.

- Measured from: metric
- Defined in: [Cardinality](alerts-on-metrics.md#cardinality)
- Address: https://rollingedition.com/concepts/llm-observability/cardinality

## collector

A collector is a separate process that receives, processes and exports telemetry

- Also: OpenTelemetry Collector
- Contrasts with: backend
- Defined in: [The exporter sends each span over OTLP](send-to-a-backend.md#otlp-over-http)
- Address: https://rollingedition.com/concepts/llm-observability/collector

## content capture

Content capture is the instrumentation's switch for recording prompts and replies themselves, and it is off, NO_CONTENT, unless set.

- True for: opentelemetry-instrumentation-genai-openai 1.3b0
- Defined in: [The capture switch](client-library-instrumentation.md#the-capture-switch)
- Address: https://rollingedition.com/concepts/llm-observability/content-capture

## context propagation

Context propagation carries the context, the span's identity and any baggage, to the next process

- Comes before: baggage
- Defined in: [The MCP SDK writes traceparent into _meta](across-processes.md#traceparent-in-meta)
- Address: https://rollingedition.com/concepts/llm-observability/context-propagation

## cost

A call's cost is its tokens priced by a named, dated price table

- Contrasts with: https://rollingedition.com/concepts/ai-agents/cost
- Defined in: [Cost by route and step](tokens-and-cost.md#cost-per-route)
- Address: https://rollingedition.com/concepts/llm-observability/cost

## cost attribution

cost attribution assigns each call's cost to the step, route and user that caused it

- Defined in: [Cost by route and step](tokens-and-cost.md#cost-per-route)
- Address: https://rollingedition.com/concepts/llm-observability/cost-attribution

## counter

a counter only adds

- A kind of: metric
- Defined in: [Summing spans double counts](tokens-and-cost.md#totals-from-metrics-not-spans)
- Address: https://rollingedition.com/concepts/llm-observability/counter

## critical path

The critical path is the chain of spans that sets a message's end time; shortening any other span doesn't end the message sooner.

- Computed from: span
- Defined in: [The critical path sets the end time](latency-sources.md#the-critical-path)
- Address: https://rollingedition.com/concepts/llm-observability/critical-path

## detached root

A span that starts a trace of its own this way is a detached root: a span whose context was lost, so it starts a new trace and sits outside the message's trace.

- Defined in: [Context is lost at a thread boundary](across-processes.md#lost-context)
- Address: https://rollingedition.com/concepts/llm-observability/detached-root

## Development status

Every page of the GenAI conventions, version 0.1.0, is Development: its names may change in any release.

- Also: Development
- Defined in: [The standard at a Development version](name-spans.md#the-standard-at-v0-1-0)
- Address: https://rollingedition.com/concepts/llm-observability/stability-status

## error

An error is a span whose status is ERROR.

- Also: errors
- Computed from: span status
- Defined in: [How a span records failure](find-the-failure.md#how-a-span-records-failure)
- Address: https://rollingedition.com/concepts/llm-observability/error

## error budget

the error budget is the share it lets fail

- Computed from: objective
- Defined in: [Service-level objectives](alerts-on-metrics.md#service-level-objectives)
- Address: https://rollingedition.com/concepts/llm-observability/error-budget

## error.type

error.type names the error: the class name the package writes, or a registry value where one exists, so failures can be counted by kind.

- Also: error type
- Defined in: [How a span records failure](find-the-failure.md#how-a-span-records-failure)
- Address: https://rollingedition.com/concepts/llm-observability/error-type

## estimate from a sample

Scaling a head sample's total by the inverse of its ratio estimates the whole, because every trace has the same chance of being kept: the kept total, times the inverse of the ratio, estimates the day.

- Computed from: sampling ratio
- Defined in: [Estimate the day's totals from a sample](choose-what-to-keep.md#estimating-totals-from-a-sample)
- Address: https://rollingedition.com/concepts/llm-observability/estimate-from-a-sample

## exporter

A span processor is called when each span starts and when it ends, and on end it hands the span to an exporter, which sends it somewhere: to memory, a file or an OTLP endpoint.

- True for: opentelemetry-sdk 1.45.2
- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/exporter

## external content reference

An external content reference puts a pointer in the span, a *_ref attribute, and the content itself in a store with its own access rules.

- Also: content reference
- Defined in: [Keep content by reference](keep-private-data-out.md#keep-content-by-reference)
- Address: https://rollingedition.com/concepts/llm-observability/external-content-reference

## failed message

A message fails, for the objective, when its user got no reply; a retry that recovered is not a failure.

- Contrasts with: error
- Defined in: [Service-level objectives](alerts-on-metrics.md#service-level-objectives)
- Address: https://rollingedition.com/concepts/llm-observability/failed-message

## fallback reply

A fallback reply is the fixed text Ambrewick sends when the router chooses fallback; no model writes it, and its span says so.

- Also: fallback replies
- Defined in: [Where the time went in twenty messages](trace-a-request.md#where-the-time-went-in-twenty-messages)
- Address: https://rollingedition.com/concepts/llm-observability/fallback-reply

## finish reason

The finish reason says why the model stopped: on its own (stop) or at the token cap (length).

- Also: finish reasons
- Measured from: inference span
- Close to: https://rollingedition.com/concepts/large-language-models/finish-reason
- Defined in: [Replies cut at the cap](find-the-failure.md#replies-cut-at-the-cap)
- Address: https://rollingedition.com/concepts/llm-observability/finish-reason

## generation

generation is it writing the reply, one token at a time

- Contrasts with: prefill
- Defined in: [Prefill against generation](latency-sources.md#prefill-against-generation)
- Address: https://rollingedition.com/concepts/llm-observability/generation

## head sampling

Head sampling decides whether to keep a trace when it starts, before any span has run.

- True for: opentelemetry-sdk 1.45.2
- Contrasts with: tail sampling
- Defined in: [Head sampling decides before the trace runs](choose-what-to-keep.md#head-sampling)
- Address: https://rollingedition.com/concepts/llm-observability/head-sampling

## histogram

a histogram counts values into buckets with their sum and count

- A kind of: metric
- Defined in: [Summing spans double counts](tokens-and-cost.md#totals-from-metrics-not-spans)
- Address: https://rollingedition.com/concepts/llm-observability/histogram

## histogram bucket

A bucket counts the values between two edges, so a percentile read from buckets is known only to within its bucket.

- Also: bucket
- Part of: histogram
- Defined in: [Histogram buckets and what they hide](latency-sources.md#histogram-buckets-and-what-they-hide)
- Address: https://rollingedition.com/concepts/llm-observability/histogram-bucket

## inference span

An inference span is the span of one client call to a generative model that answers the prompt or asks for a tool call.

- A kind of: span
- Defined in: [Span types for each step](name-spans.md#span-types-for-each-step)
- Address: https://rollingedition.com/concepts/llm-observability/inference-span

## input tokens

Input tokens are the whole prompt the model read, cached part included

- Defined in: [Three counts for each call](tokens-and-cost.md#three-token-counts)
- Address: https://rollingedition.com/concepts/llm-observability/input-tokens

## instrumentation library

An instrumentation library is a package that makes the telemetry for another library's calls

- Defined in: [A call through the client](client-library-instrumentation.md#a-call-through-the-client)
- Address: https://rollingedition.com/concepts/llm-observability/instrumentation-library

## instrumentation scope

The instrumentation scope names the unit of code that made a span, usually an instrumentation library, and here the assistant's own module.

- Defined in: [Who made the span](name-spans.md#who-made-the-span)
- Address: https://rollingedition.com/concepts/llm-observability/instrumentation-scope

## interval

An interval says how far a number would move had the day brought other messages drawn the same way; here, the middle 95% of 2,000 bootstrap resamples of messages.

- Also: intervals
- Close to: https://rollingedition.com/concepts/artificial-intelligence/interval
- Defined in: [Tail percentiles with intervals](latency-sources.md#tail-percentiles-with-intervals)
- Address: https://rollingedition.com/concepts/llm-observability/interval

## keyed pseudonym

A keyed pseudonym replaces a user ID with an HMAC-SHA256 of it under a key, kept to twelve hexadecimal digits, the same for one user wherever it appears.

- Also: keyed pseudonyms
- Close to: https://rollingedition.com/concepts/data-governance/keyed-pseudonym
- Defined in: [Keyed user pseudonyms](keep-private-data-out.md#keyed-user-pseudonyms)
- Address: https://rollingedition.com/concepts/llm-observability/keyed-pseudonym

## manual instrumentation

Manual instrumentation is spans your code makes

- Contrasts with: automatic instrumentation
- Defined in: [A call through the client](client-library-instrumentation.md#a-call-through-the-client)
- Address: https://rollingedition.com/concepts/llm-observability/manual-instrumentation

## message

once an utterance is in the traffic it is a message

- Also: messages
- Defined in: [One message, one trace](trace-a-request.md#one-message-one-trace)
- Address: https://rollingedition.com/concepts/llm-observability/message

## metric

A metric is a measurement the SDK aggregates over many operations and exports without each one's detail

- Also: metrics
- True for: opentelemetry-sdk 1.45.2
- Defined in: [Summing spans double counts](tokens-and-cost.md#totals-from-metrics-not-spans)
- Address: https://rollingedition.com/concepts/llm-observability/metric

## objective

An objective is the share of messages that must succeed, or finish within a time, over a period

- Also: service-level objective, SLO
- Defined in: [Service-level objectives](alerts-on-metrics.md#service-level-objectives)
- Address: https://rollingedition.com/concepts/llm-observability/objective

## orphan

An orphan is a span whose parent ID names a span the store does not hold.

- Contrasts with: detached root
- Defined in: [Context is lost at a thread boundary](across-processes.md#lost-context)
- Address: https://rollingedition.com/concepts/llm-observability/orphan

## OTLP

OTLP is OpenTelemetry's protocol for sending telemetry to a receiver.

- Defined in: [The exporter sends each span over OTLP](send-to-a-backend.md#otlp-over-http)
- Address: https://rollingedition.com/concepts/llm-observability/otlp

## output tokens

output tokens are what it wrote

- Defined in: [Three counts for each call](tokens-and-cost.md#three-token-counts)
- Address: https://rollingedition.com/concepts/llm-observability/output-tokens

## paired comparison

A paired comparison runs two releases on the same messages and summarises, for each message, the release's value minus the baseline's.

- Close to: https://rollingedition.com/concepts/artificial-intelligence/paired-comparison
- Defined in: [Paired comparison on messages](catch-a-regression.md#paired-comparison-on-messages)
- Address: https://rollingedition.com/concepts/llm-observability/paired-comparison

## parent span

A span's parent is the span whose work it is part of

- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/parent-span

## parent-based sampling

Parent-based sampling makes each span follow its parent's decision.

- True for: opentelemetry-sdk 1.45.2
- Defined in: [Children follow the root's decision](choose-what-to-keep.md#parent-based-sampling)
- Address: https://rollingedition.com/concepts/llm-observability/parent-based-sampling

## percentile

The p-th percentile is the value at sorted position ceil(p/100 × n)

- Also: p95, p99
- Defined in: [Tail percentiles with intervals](latency-sources.md#tail-percentiles-with-intervals)
- Address: https://rollingedition.com/concepts/llm-observability/percentile

## personal-looking value

A personal-looking value is a person, place or relation name in a request's text, written by the dataset's crowd workers and labelled by its slots; it looks like personal data in a span and is treated as such; it was written for the dataset and is not drawn from anyone's messages, though the dataset keeps some public names as written.

- Also: personal-looking values
- Close to: https://rollingedition.com/concepts/data-governance/personal-data
- Defined in: [What leaks when capture is on](keep-private-data-out.md#what-leaks-when-capture-is-on)
- Address: https://rollingedition.com/concepts/llm-observability/personal-looking-value

## prefill

Prefill is the model reading the prompt

- Part of: time to first chunk
- Defined in: [Prefill against generation](latency-sources.md#prefill-against-generation)
- Address: https://rollingedition.com/concepts/llm-observability/prefill

## price table

The price table is a dated, versioned file of rates per million tokens, read at each call's virtual timestamp.

- Defined in: [The price table](tokens-and-cost.md#the-price-table)
- Address: https://rollingedition.com/concepts/llm-observability/price-table

## prompt version

A release is marked by service.version on the resource and gen_ai.prompt.version on the inference span, so a query can split traces by release.

- Comes before: paired comparison
- Defined in: [Release markers in the spans](catch-a-regression.md#release-markers-in-the-spans)
- Address: https://rollingedition.com/concepts/llm-observability/prompt-version

## redaction

Redaction replaces a personal value in a span's attributes or events with a placeholder before the span is stored: in the process that made it, or where every service's spans pass.

- Also: redact, redacting
- Defined in: [Redaction is defence in depth](keep-private-data-out.md#redaction-as-defence-in-depth)
- Address: https://rollingedition.com/concepts/llm-observability/redaction

## regression

A regression is a release's change that makes a trace-derived number worse than its limit allows, judged by the end of its interval nearest the limit.

- Defined in: [The CI gate](catch-a-regression.md#the-ci-gate)
- Address: https://rollingedition.com/concepts/llm-observability/regression

## regression gate

A regression gate is a check in CI that stops a release from merging when a number read from its traces has moved past its threshold, judged against its paired interval.

- Close to: https://rollingedition.com/concepts/llm-evaluation/gate
- Defined in: [The CI gate](catch-a-regression.md#the-ci-gate)
- Address: https://rollingedition.com/concepts/llm-observability/regression-gate

## release marker

A release is marked by service.version on the resource and gen_ai.prompt.version on the inference span

- Defined in: [Release markers in the spans](catch-a-regression.md#release-markers-in-the-spans)
- Address: https://rollingedition.com/concepts/llm-observability/release-marker

## requirement level

A requirement level says when an attribute must appear: required, conditionally required, recommended or opt-in

- Also: requirement levels
- Defined in: [Which attributes a span must carry](name-spans.md#requirement-levels)
- Address: https://rollingedition.com/concepts/llm-observability/requirement-level

## resource

The resource describes what made the telemetry and is the same on every span one tracer provider makes: service.name, service.version, service.instance.id.

- True for: opentelemetry-sdk 1.45.2
- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/resource

## retention

Retention is how long the backend keeps each kind of telemetry.

- Close to: https://rollingedition.com/concepts/data-governance/retention
- Defined in: [What a kept trace costs to hold](choose-what-to-keep.md#retention)
- Address: https://rollingedition.com/concepts/llm-observability/retention

## retrieval span

A retrieval span is the span of one run of the application's retrieval step, which returns the documents relevant to a query.

- A kind of: span
- Defined in: [Span types for each step](name-spans.md#span-types-for-each-step)
- Address: https://rollingedition.com/concepts/llm-observability/retrieval-span

## retry

A retry is another attempt at a failed call, recorded as its own span.

- Also: retries
- Defined in: [Retries under a timeout](find-the-failure.md#retries-under-a-timeout)
- Address: https://rollingedition.com/concepts/llm-observability/retry

## sampling ratio

The ratio is the share of traces kept

- Part of: head sampling
- Defined in: [Head sampling decides before the trace runs](choose-what-to-keep.md#head-sampling)
- Address: https://rollingedition.com/concepts/llm-observability/sampling-ratio

## schema URL

A schema URL names a published telemetry schema, a release of the semantic conventions, that the telemetry follows.

- Defined in: [Who made the span](name-spans.md#who-made-the-span)
- Address: https://rollingedition.com/concepts/llm-observability/schema-url

## semantic convention

A semantic convention is a published name, type and meaning for a span, attribute or metric, so that any backend reads the same name the same way.

- Also: semantic conventions
- Defined in: [The standard at a Development version](name-spans.md#the-standard-at-v0-1-0)
- Address: https://rollingedition.com/concepts/llm-observability/semantic-convention

## span

A span is a named, timed operation with attributes and a parent, except the root, which has none.

- True for: opentelemetry-sdk 1.45.2
- Part of: trace
- Close to: https://rollingedition.com/concepts/artificial-intelligence/span
- Defined in: [One message, one trace](trace-a-request.md#one-message-one-trace)
- Address: https://rollingedition.com/concepts/llm-observability/span

## span context

its span context, chiefly the trace ID, span ID and trace flags, is what lets other code and other processes name it

- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/span-context

## span ID

a span ID is the number of one span

- Part of: span context
- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/span-id

## span kind

A span's kind says where its work ran: CLIENT for a call out of the process, SERVER for one received, INTERNAL for work inside

- Also: span kinds
- Defined in: [The span kind follows the process](name-spans.md#span-kind-follows-the-process)
- Address: https://rollingedition.com/concepts/llm-observability/span-kind

## span processor

A span processor is called when each span starts and when it ends, and on end it hands the span to an exporter

- True for: opentelemetry-sdk 1.45.2
- Implemented by: opentelemetry-sdk 1.45.2
- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/span-processor

## span status

A span's status is unset, ok or error.

- Defined in: [How a span records failure](find-the-failure.md#how-a-span-records-failure)
- Address: https://rollingedition.com/concepts/llm-observability/span-status

## tail latency

the tail is the slowest few percent of messages

- Also: the tail
- Defined in: [Tail percentiles with intervals](latency-sources.md#tail-percentiles-with-intervals)
- Address: https://rollingedition.com/concepts/llm-observability/tail-latency

## tail sampling

Tail sampling decides once the whole trace is in, by what it holds.

- Defined in: [Tail sampling reads the whole trace](choose-what-to-keep.md#tail-sampling)
- Address: https://rollingedition.com/concepts/llm-observability/tail-sampling

## time to first chunk

Time to first chunk is the time from sending a model call to receiving the first streamed piece of its reply.

- Measured from: inference span
- Defined in: [Time to first chunk](latency-sources.md#time-to-first-chunk)
- Address: https://rollingedition.com/concepts/llm-observability/time-to-first-chunk

## token count

A token count is the number of tokens a model reads or writes for one call, in that model's own vocabulary.

- Also: token counts
- Defined in: [Three counts for each call](tokens-and-cost.md#three-token-counts)
- Address: https://rollingedition.com/concepts/llm-observability/token-count

## tool-execution span

A tool-execution span is the span of one run of a tool, named for the tool.

- Also: tool-execution spans
- A kind of: span
- Defined in: [Span types for each step](name-spans.md#span-types-for-each-step)
- Address: https://rollingedition.com/concepts/llm-observability/tool-execution-span

## trace

A trace is the record of one user message's work: every span made for it, sharing one trace ID. Their parent links join them into a tree, and a span whose parent is missing still belongs to the trace.

- True for: opentelemetry-sdk 1.45.2
- Close to: https://rollingedition.com/concepts/ai-agents/trace
- Defined in: [One message, one trace](trace-a-request.md#one-message-one-trace)
- Address: https://rollingedition.com/concepts/llm-observability/trace

## trace ID

A trace ID is the number every span of one trace carries

- Part of: span context
- Defined in: [Spans by hand](trace-a-request.md#spans-by-hand)
- Address: https://rollingedition.com/concepts/llm-observability/trace-id

## traceparent

traceparent is the W3C field for the span's part: the trace ID, the parent's span ID and the trace flags, of which the sampled flag is the only one defined.

- Part of: context propagation
- Defined in: [The MCP SDK writes traceparent into _meta](across-processes.md#traceparent-in-meta)
- Address: https://rollingedition.com/concepts/llm-observability/traceparent

## utterance

A row of the dataset is an utterance

- Also: utterances
- Defined in: [One message, one trace](trace-a-request.md#one-message-one-trace)
- Address: https://rollingedition.com/concepts/llm-observability/utterance
