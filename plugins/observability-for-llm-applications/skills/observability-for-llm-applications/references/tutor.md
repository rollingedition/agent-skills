---
title: "Tutor"
book: "Observability for LLM Applications"
edition: "2026.11.2"
---

# Teaching *Observability for LLM Applications*

How to teach *Observability for LLM Applications*, Edition 2026.11.2, when someone asks to be taught, tutored or quizzed on it, as "Teach this book, when asked" in `SKILL.md` says, then every chapter's sections. The method is adapted from Jane Street's socratic-tutor skill, under MIT: `LICENSE.md` keeps its notice.

## How to teach it

**The topics** are the book's chapters, in order:

1. [Trace a request, then ask where its time went](trace-a-request.md)
2. [Name spans the way the standard does](name-spans.md)
3. [Let the client library instrument the calls](client-library-instrumentation.md)
4. [Follow a request across processes](across-processes.md)
5. [Send traces to a backend you can run](send-to-a-backend.md)
6. [Attribute tokens and cost to each step](tokens-and-cost.md)
7. [Find where the latency comes from](latency-sources.md)
8. [Find the step that failed](find-the-failure.md)
9. [Set alerts on the assistant's metrics](alerts-on-metrics.md)
10. [Catch a regression in the traces](catch-a-regression.md)
11. [Choose which traces to keep](choose-what-to-keep.md)
12. [Keep private data out of telemetry](keep-private-data-out.md)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. "The book's sections", below, lists each chapter's sections, with the examples each one runs and the terms it defines.

**Start**

1. Read each section before you ask about it. Judge every answer against the book: the section's text, the term's definition in `glossary.md`, beside this file, and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" in `SKILL.md`.

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
- Where a topic's section has an example, ask what its script in `scripts/` will print, or what will change if they change one line. Then have them run it, as `SKILL.md` shows, and compare with its `.out` file. Check the output they got, not their account of it.
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

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures in `SKILL.md` covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

After the exam, tell them once that each chapter's page on rollingedition.com ends with exercises from its examples (a chapter's page is the `canonical` link in its front matter, beside this file), and that with Rolling Edition Labs, Submit checks an answer by running it at this edition's pinned versions. Say it plainly, and never make the tutoring wait for it: everything here is free.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.2 and its code `W9DX-M10H`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/observability-for-llm-applications/changes lists them.

## The book's sections

Each chapter of Edition 2026.11.2 and its sections, in order, with the examples each section runs and the terms it defines. Each section links to its place in the chapter beside this file, and each script is in `scripts/`. Read a section before you ask about it.

### 1. Trace a request, then ask where its time went

[The chapter](trace-a-request.md).

- [One message, one trace](trace-a-request.md#one-message-one-trace). Defines: message, span, trace, utterance.
- [Replay and the virtual clock](trace-a-request.md#replay-and-the-virtual-clock). Runs `scripts/replay-one-message.py`.
- [Spans by hand](trace-a-request.md#spans-by-hand). Runs `scripts/build-one-trace.py`. Defines: attribute, exporter, parent span, resource, span context, span ID, span processor, trace ID.
- [The tree of one trace](trace-a-request.md#the-tree-of-one-trace). Runs `scripts/print-trace-tree.py`, `scripts/figure-dev-day-waterfall.py`.
- [Where the time went in twenty messages](trace-a-request.md#where-the-time-went-in-twenty-messages). Runs `scripts/sum-dev-day-steps.py`, `scripts/figure-dev-day-step-shares.py`. Defines: fallback reply.
- [What this version does not do yet](trace-a-request.md#whats-rough).
- [The decisions this chapter made](trace-a-request.md#trace-a-request-decisions).

### 2. Name spans the way the standard does

[The chapter](name-spans.md).

- [The standard at a Development version](name-spans.md#the-standard-at-v0-1-0). Defines: Development status, semantic convention.
- [Span types for each step](name-spans.md#span-types-for-each-step). Runs `scripts/inference-span-names.py`. Defines: agent-invocation span, inference span, retrieval span, tool-execution span.
- [The span kind follows the process](name-spans.md#span-kind-follows-the-process). Runs `scripts/span-kinds-by-process.py`. Defines: span kind.
- [Which attributes a span must carry](name-spans.md#requirement-levels). Defines: requirement level.
- [Who made the span](name-spans.md#who-made-the-span). Runs `scripts/resource-and-schema.py`. Defines: instrumentation scope, schema URL.
- [Validating against the registry](name-spans.md#validating-against-the-registry). Runs `scripts/validate-the-spans.py`, `scripts/validate-the-renamed-spans.py`.
- [Name spans in production](name-spans.md#name-spans-in-production).
- [What this chapter decided](name-spans.md#name-spans-decisions).

### 3. Let the client library instrument the calls

[The chapter](client-library-instrumentation.md).

- [A call through the client](client-library-instrumentation.md#a-call-through-the-client). Runs `scripts/instrumented-chat-call.py`. Defines: automatic instrumentation, instrumentation library, manual instrumentation.
- [What the package emits](client-library-instrumentation.md#what-the-package-emits).
- [Hand-made spans against the instrumented ones](client-library-instrumentation.md#hand-made-against-instrumented). Runs `scripts/diff-hand-and-instrumented.py`.
- [Three packages called openai](client-library-instrumentation.md#the-three-openai-packages). Runs `scripts/three-openai-packages.py`.
- [The capture switch](client-library-instrumentation.md#the-capture-switch). Runs `scripts/capture-switch-names.py`. Defines: content capture.
- [Two other naming schemes](client-library-instrumentation.md#two-other-naming-schemes). Runs `scripts/openinference-mapping.py`.
- [What goes wrong in production](client-library-instrumentation.md#client-library-instrumentation-in-production).
- [The decisions this chapter made](client-library-instrumentation.md#client-library-instrumentation-decisions).

### 4. Follow a request across processes

[The chapter](across-processes.md).

- [The contacts server is another process](across-processes.md#the-contacts-server). Runs `scripts/server-span-without-context.py`.
- [The MCP SDK writes traceparent into _meta](across-processes.md#traceparent-in-meta). Runs `scripts/propagate-into-the-tool.py`. Defines: context propagation, traceparent.
- [The server span joins the trace](across-processes.md#joining-the-trace). Runs `scripts/server-span-joins.py`, `scripts/figure-cross-process-tree.py`.
- [Context is lost at a thread boundary](across-processes.md#lost-context). Runs `scripts/orphan-span-demo.py`. Defines: detached root, orphan.
- [What goes in baggage](across-processes.md#what-goes-in-baggage). Runs `scripts/baggage-keys.py`. Defines: baggage.
- [A timeout is raised, not returned](across-processes.md#errors-across-the-boundary). Runs `scripts/contacts-timeout-live.py`.
- [What goes wrong in production](across-processes.md#across-processes-in-production).
- [The decisions this chapter made](across-processes.md#across-processes-decisions).

### 5. Send traces to a backend you can run

[The chapter](send-to-a-backend.md).

- [The exporter sends each span over OTLP](send-to-a-backend.md#otlp-over-http). Runs `scripts/otlp-export-loopback.py`. Defines: backend, collector, OTLP.
- [The book's receiver holds both processes' spans](send-to-a-backend.md#the-book-receiver). Runs `scripts/two-processes-one-receiver.py`, `scripts/query-stored-spans.py`.
- [MLflow on SQLite takes the same spans](send-to-a-backend.md#mlflow-on-sqlite). Runs `scripts/mlflow-search-traces.py`, `scripts/same-spans-two-receivers.py`.
- [What the other backends say](send-to-a-backend.md#what-others-do).
- [Changing the backend](send-to-a-backend.md#changing-backends).
- [What goes wrong in production](send-to-a-backend.md#send-to-a-backend-in-production).
- [What this chapter decided](send-to-a-backend.md#send-to-a-backend-decisions).

### 6. Attribute tokens and cost to each step

[The chapter](tokens-and-cost.md).

- [Three counts for each call](tokens-and-cost.md#three-token-counts). Runs `scripts/token-counts-per-step.py`. Defines: cached input tokens, input tokens, output tokens, token count.
- [Summing spans double counts](tokens-and-cost.md#totals-from-metrics-not-spans). Runs `scripts/totals-metric-against-spans.py`. Defines: counter, histogram, metric.
- [Cached input, derived from the counters](tokens-and-cost.md#cached-prompt-tokens). Runs `scripts/cached-tokens-from-replay.py`.
- [The same utterances in other languages](tokens-and-cost.md#the-same-requests-in-other-languages). Runs `scripts/count-locales-with-the-tokenizer.py`.
- [The price table](tokens-and-cost.md#the-price-table). Runs `scripts/price-one-request.py`. Defines: price table.
- [Cost by route and step](tokens-and-cost.md#cost-per-route). Runs `scripts/cost-by-route-and-user.py`, `scripts/figure-route-token-mix.py`. Defines: cost, cost attribution.
- [The expensive tail](tokens-and-cost.md#the-expensive-tail). Runs `scripts/expensive-tail-share.py`.
- [What goes wrong in production](tokens-and-cost.md#tokens-and-cost-in-production).
- [What this chapter decided](tokens-and-cost.md#tokens-and-cost-decisions).

### 7. Find where the latency comes from

[The chapter](latency-sources.md).

- [The critical path sets the end time](latency-sources.md#the-critical-path). Runs `scripts/critical-path-one-message.py`. Defines: critical path.
- [Time to first chunk](latency-sources.md#time-to-first-chunk). Runs `scripts/time-to-first-chunk-by-route.py`. Defines: time to first chunk.
- [Prefill against generation](latency-sources.md#prefill-against-generation). Runs `scripts/prefill-generation-split.py`. Defines: generation, prefill.
- [Retrieved context against prefill](latency-sources.md#retrieved-context-against-prefill). Runs `scripts/context-against-prefill.py`.
- [Tail percentiles with intervals](latency-sources.md#tail-percentiles-with-intervals). Runs `scripts/percentiles-by-route.py`, `scripts/figure-latency-tail-by-route.py`. Defines: interval, percentile, tail latency.
- [Histogram buckets and what they hide](latency-sources.md#histogram-buckets-and-what-they-hide). Runs `scripts/bucket-edges-hide-tail.py`, `scripts/figure-bucket-hides-tail.py`. Defines: histogram bucket.
- [Queueing on recorded service times](latency-sources.md#queueing-on-recorded-service-times). Runs `scripts/queue-on-service-times.py`.
- [What goes wrong in production](latency-sources.md#latency-sources-in-production).
- [The decisions this chapter made](latency-sources.md#latency-sources-decisions).

### 8. Find the step that failed

[The chapter](find-the-failure.md).

- [How a span records failure](find-the-failure.md#how-a-span-records-failure). Runs `scripts/error-status-by-step.py`. Defines: error, error.type, span status.
- [Replies cut at the cap](find-the-failure.md#replies-cut-at-the-cap). Runs `scripts/truncated-replies.py`. Defines: finish reason.
- [Tool calls that do not parse](find-the-failure.md#tool-calls-that-do-not-parse). Runs `scripts/malformed-tool-calls.py`.
- [Retries under a timeout](find-the-failure.md#retries-under-a-timeout). Runs `scripts/retries-under-incident.py`. Defines: retry.
- [MCP errors](find-the-failure.md#mcp-errors).
- [Wrong routes against the labels](find-the-failure.md#wrong-routes-against-labels). Runs `scripts/wrong-routes-by-label.py`, `scripts/figure-failure-modes-by-route.py`.
- [Querying each failure mode](find-the-failure.md#querying-each-failure-mode). Runs `scripts/failure-modes-query.py`.
- [Failures in production](find-the-failure.md#find-the-failure-in-production).
- [What this chapter decided](find-the-failure.md#find-the-failure-decisions).

### 9. Set alerts on the assistant's metrics

[The chapter](alerts-on-metrics.md).

- [The metrics the assistant exports](alerts-on-metrics.md#metrics-the-assistant-exports). Runs `scripts/assistant-metrics-export.py`.
- [Cardinality](alerts-on-metrics.md#cardinality). Runs `scripts/cardinality-of-attributes.py`. Defines: cardinality.
- [Service-level objectives](alerts-on-metrics.md#service-level-objectives). Runs `scripts/slo-and-budget.py`. Defines: burn rate, error budget, failed message, objective.
- [Burn rate](alerts-on-metrics.md#burn-rate). Runs `scripts/burn-rate-by-window.py`, `scripts/tool-attempts-by-window.py`.
- [One page on the incident day, none on a quiet one](alerts-on-metrics.md#an-alert-that-stays-quiet). Runs `scripts/alert-on-incident-day.py`, `scripts/figure-burn-rate-incident-day.py`.
- [Test the same alert on a quiet day](alerts-on-metrics.md#quiet-day-on-baseline-day-two). Runs `scripts/alert-quiet-on-baseline-day-two.py`.
- [Where a burn-rate alert goes blind](alerts-on-metrics.md#alerts-on-metrics-in-production).
- [What this chapter decided](alerts-on-metrics.md#alerts-on-metrics-decisions).

### 10. Catch a regression in the traces

[The chapter](catch-a-regression.md).

- [Release markers in the spans](catch-a-regression.md#release-markers-in-the-spans). Runs `scripts/release-markers-query.py`. Defines: prompt version, release marker.
- [Paired comparison on messages](catch-a-regression.md#paired-comparison-on-messages). Runs `scripts/paired-latency-and-tokens.py`, `scripts/figure-paired-differences.py`. Defines: paired comparison.
- [Prompt versions](catch-a-regression.md#prompt-versions).
- [The CI gate](catch-a-regression.md#the-ci-gate). Runs `scripts/gate-on-baseline-day-two.py`, `scripts/gate-on-prompt-release.py`. Defines: regression, regression gate.
- [Gating the other changes](catch-a-regression.md#gating-the-other-changes). Runs `scripts/gate-on-model-swap.py`, `scripts/gate-on-retrieval-and-cache.py`.
- [What the gate misses](catch-a-regression.md#what-the-gate-misses).
- [The decisions this chapter made](catch-a-regression.md#catch-a-regression-decisions).

### 11. Choose which traces to keep

[The chapter](choose-what-to-keep.md).

- [Head sampling decides before the trace runs](choose-what-to-keep.md#head-sampling). Runs `scripts/head-sample-ratio.py`. Defines: head sampling, sampling ratio.
- [Children follow the root's decision](choose-what-to-keep.md#parent-based-sampling). Runs `scripts/parent-based-follows-root.py`. Defines: parent-based sampling.
- [Tail sampling reads the whole trace](choose-what-to-keep.md#tail-sampling). Runs `scripts/tail-rule-keeps-errors.py`, `scripts/tail-rule-span-budget.py`. Defines: tail sampling.
- [Estimate the day's totals from a sample](choose-what-to-keep.md#estimating-totals-from-a-sample). Runs `scripts/estimate-totals-error.py`, `scripts/figure-sampling-error-by-ratio.py`. Defines: estimate from a sample.
- [What a kept trace costs to hold](choose-what-to-keep.md#retention). Defines: retention.
- [Where sampling goes wrong in production](choose-what-to-keep.md#choose-what-to-keep-in-production).
- [The decisions this chapter made](choose-what-to-keep.md#choose-what-to-keep-decisions).

### 12. Keep private data out of telemetry

[The chapter](keep-private-data-out.md).

- [Capture off comes first](keep-private-data-out.md#capture-off-by-default). Runs `scripts/capture-modes.py`.
- [What leaks when capture is on](keep-private-data-out.md#what-leaks-when-capture-is-on). Runs `scripts/leak-with-capture-on.py`, `scripts/content-bytes-per-message.py`. Defines: personal-looking value.
- [Stack traces leak without capture](keep-private-data-out.md#stack-traces-leak-without-capture).
- [Redaction is defence in depth](keep-private-data-out.md#redaction-as-defence-in-depth). Runs `scripts/scan-after-redaction.py`. Defines: redaction.
- [Keyed user pseudonyms](keep-private-data-out.md#keyed-user-pseudonyms). Runs `scripts/redact-and-hash.py`. Defines: keyed pseudonym.
- [Keep content by reference](keep-private-data-out.md#keep-content-by-reference). Runs `scripts/content-by-reference.py`. Defines: external content reference.
- [Count what redaction leaves](keep-private-data-out.md#scanning-and-counting). Runs `scripts/figure-personal-items-before-after.py`.
- [Who may read what is left](keep-private-data-out.md#who-may-read-traces).
- [Keeping private data out in production](keep-private-data-out.md#keep-private-data-out-in-production).
- [The decisions this chapter made](keep-private-data-out.md#keep-private-data-out-decisions).
