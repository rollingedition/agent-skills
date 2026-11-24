---
title: "Tutor"
book: "Business Intelligence with Agents"
edition: "2026.11.19"
---

# Teaching *Business Intelligence with Agents*

How to teach *Business Intelligence with Agents*, Edition 2026.11.19, when someone asks to be taught, tutored or quizzed on it, as "Teach this book, when asked" in `SKILL.md` says, then every chapter's sections. The method is adapted from Jane Street's socratic-tutor skill, under MIT: `LICENSE.md` keeps its notice.

## How to teach it

**The topics** are the book's chapters, in order:

1. [A data agent end to end](bi-agent-end-to-end.md)
2. [Where raw text-to-SQL gets the number wrong](wrong-numbers.md)
3. [Build golden questions from your own work](golden-questions.md)
4. [Give the agent layered context](layered-context.md)
5. [Define metrics once in a semantic layer](semantic-layer.md)
6. [Route questions to governed metrics first](metrics-first.md)
7. [Let the agent write SQL inside guards](guarded-sql.md)
8. [Say when the answer can't be given](say-when-it-cannot.md)
9. [Keep the agent inside who may see what](who-may-see-what.md)
10. [Judge answers and catch regressions](catch-regressions.md)
11. [Serve the semantic layer over MCP](serve-over-mcp.md)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. "The book's sections", below, lists each chapter's sections, with the examples each one runs and the terms it defines.

**Start**

1. Read each section before you ask about it. Judge every answer against the book: the section's text, the term's definition in `glossary.md`, beside this file, and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" in `SKILL.md`.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
A data agent end to end    overall: █████░░░░░ 53%
-------------------------------------------------------------
Meet the shop and its warehouse       ████████░░  4/5  alone
Ask a question, get SQL from a model  ██████░░░░  3/5  <- now
Run the SQL and check the number      ██░░░░░░░░  1/5
-------------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what its script in `scripts/` will print, or what will change if they change one line. Then have them run it, as `SKILL.md` shows, and compare with its `.out` file. Check the output they got, not their account of it.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/business-intelligence-with-agents/s/ followed by its ID.

**Levels are earned**

- Raise a level only after two or more separate checks, at least one of them recalled unprompted, not just after you told them the answer.
- A vague or partly right answer isn't right. Probe until you know. Never credit them with an insight they didn't state.
- Now and then, without warning, ask again about an earlier topic. If they miss, lower its level and go back to it.
- Level 5 needs an edge case or a hard question handled, and an explanation you'd trust them to teach from.
- No flattery: "Not quite: why would X happen if Y were true?" beats "Great try!"

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures in `SKILL.md` covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.19 and its code `6B1C-RVE3`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/business-intelligence-with-agents/changes lists them.

## The book's sections

Each chapter of Edition 2026.11.19 and its sections, in order, with the examples each section runs and the terms it defines. Each section links to its place in the chapter beside this file, and each script is in `scripts/`. Read a section before you ask about it.

### 1. A data agent end to end

[The chapter](bi-agent-end-to-end.md).

- [Meet the shop and its warehouse](bi-agent-end-to-end.md#meet-the-shop). Runs `scripts/load-the-warehouse.py`. Defines: analytics schema, fiscal year, raw schema.
- [Ask a question, get SQL from a model](bi-agent-end-to-end.md#ask-for-sql). Runs `scripts/first-question-to-sql.py`. Defines: recording, schema-only text-to-SQL.
- [Run the SQL and check the number](bi-agent-end-to-end.md#check-the-first-number). Runs `scripts/run-the-model-sql.py`. Defines: golden question, net revenue.
- [Answer from one defined metric](bi-agent-end-to-end.md#answer-from-a-metric). Runs `scripts/one-metric-answer.py`. Defines: metric, metric request, tool.
- [Score both on five golden questions](bi-agent-end-to-end.md#score-five-questions). Runs `scripts/score-five-golden.py`. Defines: comparison rule, correct, declined, error, wrong answer.
  - [Read the trace of one run](bi-agent-end-to-end.md#read-one-trace). Runs `scripts/print-one-trace.py`. Defines: trace.
- [What goes wrong in production](bi-agent-end-to-end.md#end-to-end-in-production).
- [Decisions this chapter made](bi-agent-end-to-end.md#end-to-end-decisions).

### 2. Where raw text-to-SQL gets the number wrong

[The chapter](wrong-numbers.md). Defines: golden result.

- [Joins that fan out and inflate a sum](wrong-numbers.md#joins-that-fan-out). Runs `scripts/tent-orders-fan-out.py`, `scripts/figure-lines-per-order.py`. Defines: fan-out.
- [Definitions the schema doesn't hold](wrong-numbers.md#definitions-not-in-schema). Runs `scripts/gross-or-net-revenue.py`. Defines: business definition, NL2SQL-BUGs.
- [Time zones and the fiscal calendar](wrong-numbers.md#time-and-calendars). Runs `scripts/fiscal-year-and-local-day.py`. Defines: local business day.
- [The table with the tempting name](wrong-numbers.md#the-tempting-table). Runs `scripts/legacy-table-answer.py`. Defines: legacy table, Spider 2.0.
- [Filters nobody wrote down](wrong-numbers.md#unwritten-filters). Runs `scripts/cancelled-lines-counted.py`. Defines: unwritten filter.
- [Count the failures by kind](wrong-numbers.md#count-failures-by-kind). Runs `scripts/classify-schema-only-errors.py`.
- [What goes wrong in production](wrong-numbers.md#wrong-numbers-in-production).
- [Decisions this chapter made](wrong-numbers.md#wrong-numbers-decisions). Defines: failure kind.

### 3. Build golden questions from your own work

[The chapter](golden-questions.md).

- [Why a public benchmark isn't your test](golden-questions.md#benchmarks-are-not-your-test). Runs `scripts/public-vs-own-score.py`. Defines: DABstep, public benchmark.
- [Write questions from the work people do](golden-questions.md#write-golden-questions). Runs `scripts/load-golden-questions.py`. Defines: question kind.
- [Compare results, not SQL text](golden-questions.md#compare-results-not-sql). Runs `scripts/results-match-rules.py`. Defines: execution accuracy, execution match.
  - [Order, rounding and column names](golden-questions.md#order-rounding-names). Runs `scripts/tolerant-comparison.py`. Defines: tolerance.
- [Check the gold before you trust it](golden-questions.md#check-the-gold). Runs `scripts/gold-runs-and-agrees.py`, `scripts/gold-fan-out-audit.py`, `scripts/reworded-golden-question.py`. Defines: check query.
- [Cover declines and roles, not only answers](golden-questions.md#cover-declines-and-roles). Runs `scripts/golden-coverage.py`. Defines: ambiguous question, forbidden question, unanswerable question.
- [Hold out a test split](golden-questions.md#hold-out-a-test-split). Runs `scripts/baseline-on-both-splits.py`. Defines: held-out split.
- [What goes wrong in production](golden-questions.md#golden-questions-in-production).
- [Decisions this chapter made](golden-questions.md#golden-questions-decisions).

### 4. Give the agent layered context

[The chapter](layered-context.md). Defines: layered context.

- [What the schema says, and what it doesn't](layered-context.md#what-the-schema-says). Runs `scripts/schema-digest.py`. Defines: schema, schema layer.
- [Describe columns where names mislead](layered-context.md#describe-columns). Runs `scripts/column-descriptions.py`. Defines: column note.
- [Add the business glossary](layered-context.md#add-the-glossary). Runs `scripts/glossary-context.py`. Defines: BIRD, business glossary, external knowledge evidence.
- [Retrieve verified queries as examples](layered-context.md#retrieve-verified-queries). Runs `scripts/retrieve-similar-queries.py`. Defines: verified query, verified query repository.
- [Fit the context to a budget](layered-context.md#fit-a-context-budget). Runs `scripts/context-token-budget.py`. Defines: token budget, token estimate.
- [Measure what each layer adds](layered-context.md#measure-each-layer). Runs `scripts/layer-ablation-dev.py`, `scripts/figure-layers-correct-and-tokens.py`, `scripts/missing-columns-schema-only.py`, `scripts/what-stays-wrong.py`. Defines: ablation.
- [Check the chosen layers on test](layered-context.md#check-layers-on-test). Runs `scripts/best-layers-on-test.py`.
- [What goes wrong in production](layered-context.md#layered-context-in-production). Defines: lexical retrieval.
- [Decisions this chapter made](layered-context.md#layered-context-decisions).

### 5. Define metrics once in a semantic layer

[The chapter](semantic-layer.md). Defines: dimension, semantic layer.

- [Describe each table as a semantic model](semantic-layer.md#entities-measures-dimensions). Runs `scripts/load-semantic-models.py`. Defines: entity, foreign entity, measure, primary entity, semantic model, time spine.
- [Compile a metric request to SQL](semantic-layer.md#compile-a-metric-request). Runs `scripts/compile-net-revenue.py`.
- [Join through entities so sums can't fan out](semantic-layer.md#join-through-entities). Runs `scripts/entity-join-no-fanout.py`, `scripts/figure-entity-graph.py`. Defines: line_net_revenue.
- [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics). Runs `scripts/refund-rate-metric.py`. Defines: average order value, derived metric, kept_orders, order_refunds, ratio metric, refund rate, simple metric.
- [Put the fiscal calendar in the time spine](semantic-layer.md#time-grains-and-fiscal). Runs `scripts/fiscal-quarter-grain.py`. Defines: custom granularity.
- [Check the definitions against MetricFlow](semantic-layer.md#check-against-metricflow). Runs `scripts/metricflow-agrees.py`, `scripts/metricflow-needs-a-date.py`.
  - [One definition, any warehouse's dialect](semantic-layer.md#any-dialect). Runs `scripts/transpile-metric-sql.py`.
- [What goes wrong in production](semantic-layer.md#semantic-layer-in-production). Defines: metric filter.
- [Decisions this chapter made](semantic-layer.md#semantic-layer-decisions).

### 6. Route questions to governed metrics first

[The chapter](metrics-first.md). Defines: metrics-first.

- [Give the agent metrics, not tables](metrics-first.md#metrics-not-tables). Runs `scripts/metric-tools.py`. Defines: metric tool.
- [Ask for a request, not SQL](metrics-first.md#request-not-sql). Runs `scripts/model-returns-a-request.py`. Defines: structured reply.
- [Validate the request against the layer](metrics-first.md#validate-the-request). Runs `scripts/reject-unknown-dimension.py`. Defines: request validation.
- [Ask back when a question is ambiguous](metrics-first.md#ask-back-when-ambiguous). Runs `scripts/clarify-best-customers.py`. Defines: ask_back.
- [Measure metrics-first on the golden questions](metrics-first.md#measure-metrics-first). Runs `scripts/metrics-first-score.py`, `scripts/figure-outcomes-by-approach.py`. Defines: step limit.
- [Read the runs that weren't correct](metrics-first.md#read-the-misses). Runs `scripts/metrics-first-misses.py`.
- [What goes wrong in production](metrics-first.md#metrics-first-in-production).
- [Decisions this chapter made](metrics-first.md#metrics-first-decisions).

### 7. Let the agent write SQL inside guards

[The chapter](guarded-sql.md). Defines: long tail.

- [Give the agent a database with only what it may read](guarded-sql.md#least-privilege-database). Runs `scripts/agent-warehouse.py`. Defines: database catalog, least privilege.
- [Give each role a database of views](guarded-sql.md#views-per-role). Runs `scripts/role-database.py`. Defines: role's view, secure view.
- [Parse the SQL before it runs](guarded-sql.md#parse-before-running). Runs `scripts/parse-agent-sql.py`. Defines: parsing, qualify.
- [Allow only read-only queries on known tables](guarded-sql.md#read-only-allowlist). Runs `scripts/block-a-delete.py`, `scripts/block-raw-tables.py`. Defines: allowlist.
- [Bound the rows and the cost](guarded-sql.md#bound-rows-and-cost). Runs `scripts/explain-before-running.py`, `scripts/figure-plan-row-estimates.py`. Defines: EXPLAIN.
- [Enforce the deadline by killing a process](guarded-sql.md#time-the-plan). Runs `scripts/stop-a-slow-plan.py`. Defines: worker.
- [Replay the attacks on the guard](guarded-sql.md#replay-the-bypasses). Runs `scripts/replay-guard-bypasses.py`.
- [Repair once from the error](guarded-sql.md#repair-once). Runs `scripts/repair-from-error.py`. Defines: repair.
- [Transpile to the warehouse's dialect](guarded-sql.md#transpile-to-the-warehouse). Runs `scripts/transpile-to-snowflake.py`.
- [When to prefer a new metric over SQL](guarded-sql.md#metric-or-sql). Runs `scripts/long-tail-score.py`.
- [What goes wrong in production](guarded-sql.md#guarded-sql-in-production).
- [Decisions this chapter made](guarded-sql.md#guarded-sql-decisions). Defines: guarded SQL.

### 8. Say when the answer can't be given

[The chapter](say-when-it-cannot.md).

- [Kinds of questions the warehouse can't answer](say-when-it-cannot.md#kinds-of-unanswerable). Runs `scripts/unanswerable-cases.py`. Defines: ambiguous SELECT column, nonexistent filter value, nonexistent SELECT column.
- [Decline with a reason](say-when-it-cannot.md#decline-with-a-reason). Runs `scripts/cannot-answer-tool.py`. Defines: decline, decline kind.
- [Check freshness before answering](say-when-it-cannot.md#check-freshness). Runs `scripts/stale-refunds.py`, `scripts/figure-refund-settling.py`. Defines: freshness, freshness check, settling window.
- [Show the provenance with every answer](say-when-it-cannot.md#show-provenance). Runs `scripts/answer-with-provenance.py`. Defines: provenance.
- [Measure declines, not only accuracy](say-when-it-cannot.md#measure-declines). Runs `scripts/decline-precision-recall.py`. Defines: coverage, decline precision, decline recall, penalty score, selective risk.
- [What goes wrong in production](say-when-it-cannot.md#declining-in-production).
- [Decisions this chapter made](say-when-it-cannot.md#declining-decisions).

### 9. Keep the agent inside who may see what

[The chapter](who-may-see-what.md). Defines: role.

- [A rule in the prompt is not a control](who-may-see-what.md#prompt-rules-fail). Runs `scripts/prompt-rule-bypassed.py`. Defines: control.
- [Apply row filters in the compiler](who-may-see-what.md#row-filters-in-compiler). Runs `scripts/regional-lead-revenue.py`. Defines: deny by default, PolicyLayer, row access policy, row filter.
- [Mask columns in every path](who-may-see-what.md#mask-every-path). Runs `scripts/masked-emails.py`. Defines: column mask, denied column.
- [Suppress groups small enough to identify someone](who-may-see-what.md#suppress-small-groups). Runs `scripts/small-group-suppressed.py`. Defines: minimum group size, small-group suppression.
  - [Subtracting two answers recovers a group](who-may-see-what.md#differencing-limit). Runs `scripts/difference-two-answers.py`. Defines: differencing, secondary suppression.
- [Treat text in the data as data](who-may-see-what.md#text-in-data-is-data). Runs `scripts/injected-product-name.py`.
- [Measure access on the golden questions](who-may-see-what.md#measure-access). Runs `scripts/role-scope-score.py`. Defines: PolicyToolbox.
- [Log who asked what, and what ran](who-may-see-what.md#log-who-asked). Runs `scripts/audit-entries.py`. Defines: audit entry, principal.
- [What goes wrong in production](who-may-see-what.md#access-in-production).
- [Decisions this chapter made](who-may-see-what.md#access-decisions).

### 10. Judge answers and catch regressions

[The chapter](catch-regressions.md).

- [Score a run on more than accuracy](catch-regressions.md#score-a-run). Runs `scripts/scorecard.py`, `scripts/figure-accuracy-intervals.py`. Defines: scorecard, Wilson interval.
- [Judge only what can't be compared](catch-regressions.md#judge-what-cannot-be-compared). Runs `scripts/judge-an-explanation.py`. Defines: decline reason, judge.
- [Calibrate the judge against reference labels](catch-regressions.md#calibrate-the-judge). Runs `scripts/judge-agreement.py`. Defines: Cohen's kappa, familiarity, judge calibration, reference label, Scott's pi, self-preference.
- [Repeat runs to see the variance](catch-regressions.md#repeat-to-see-variance). Runs `scripts/seed-variance.py`.
- [Gate a change in CI](catch-regressions.md#gate-a-change). Runs `scripts/regression-gate.py`. Defines: paired difference, regression gate, stable break, t interval.
  - [Catch a schema change before users do](catch-regressions.md#catch-a-schema-change). Runs `scripts/renamed-column-caught.py`.
- [What goes wrong in production](catch-regressions.md#regressions-in-production).
- [Decisions this chapter made](catch-regressions.md#regressions-decisions).

### 11. Serve the semantic layer over MCP

[The chapter](serve-over-mcp.md). Defines: client, Model Context Protocol, semantic server, server.

- [Turn metrics into tools](serve-over-mcp.md#metrics-as-tools). Runs `scripts/list-metric-tools.py`. Defines: MCP tool.
- [Carry the caller's role into every query](serve-over-mcp.md#carry-the-role). Runs `scripts/role-bound-at-build.py`. Defines: binding the role at build, token audience, TokenVerifier.
- [Return answers with their provenance](serve-over-mcp.md#return-provenance). Runs `scripts/tool-result-with-provenance.py`. Defines: error prefix, output schema, structured content, tool execution error, ToolReply.
- [Test the server in memory](serve-over-mcp.md#test-the-server). Runs `scripts/semantic-server-tests.py`. Defines: in-memory client.
- [Answer questions through a host](serve-over-mcp.md#answer-through-a-host). Runs `scripts/host-asks-the-server.py`. Defines: host, ServerToolbox.
- [What goes wrong in production](serve-over-mcp.md#serving-in-production).
- [Decisions this chapter made](serve-over-mcp.md#serving-decisions).
