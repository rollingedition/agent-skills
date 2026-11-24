---
title: "Glossary"
book: "Business Intelligence with Agents"
edition: "2026.11.19"
canonical: "https://rollingedition.com/business-intelligence-with-agents/glossary"
---

# Glossary of *Business Intelligence with Agents*

The 144 terms this book defines, as Edition 2026.11.19 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/business-intelligence-with-agents/glossary

## ablation

An ablation measures every layer the same way: it scores a series of configurations that differ by one layer each, on the same questions, under the same comparison rule.

- Also: ablations
- Measured from: golden question
- Close to: https://rollingedition.com/concepts/artificial-intelligence/ablation
- Defined in: [Measure what each layer adds](layered-context.md#measure-each-layer)
- Address: https://rollingedition.com/concepts/llm-evaluation/ablation

## allowlist

The allowlist is every table in the agent's database, read by allowed_schema() with each table's columns, and the same mapping is the schema qualify resolves columns against.

- Also: allowlists
- Contrasts with: qualify
- Defined in: [Allow only read-only queries on known tables](guarded-sql.md#read-only-allowlist)
- Address: https://rollingedition.com/concepts/artificial-intelligence/allowlist

## ambiguous question

An ambiguous question, such as "Who are our best customers?", has several reasonable answers, and the agent should say which choices it needs.

- Also: ambiguous questions
- Contrasts with: unanswerable question
- Kinds: ambiguous SELECT column
- Defined in: [Cover declines and roles, not only answers](golden-questions.md#cover-declines-and-roles)
- Address: https://rollingedition.com/concepts/llm-evaluation/ambiguous-question

## ambiguous SELECT column

an ambiguous SELECT column, where several valid SQLs differ in the columns they select

- A kind of: ambiguous question
- Defined in: [Kinds of questions the warehouse can't answer](say-when-it-cannot.md#kinds-of-unanswerable)
- Address: https://rollingedition.com/concepts/artificial-intelligence/ambiguous-select-column

## analytics schema

The analytics schema holds the marts built from the raw tables in SQL, such as fct_orders, one row per real order with its amounts in euros.

- Computed from: raw schema
- Defined in: [Meet the shop and its warehouse](bi-agent-end-to-end.md#meet-the-shop)
- Address: https://rollingedition.com/concepts/data-warehousing/analytics-schema

## ask_back

The ask_back tool ends the run with a question to the person and the options the model offers.

- Also: ask back, asking back, question back
- Part of: metrics-first
- Defined in: [Ask back when a question is ambiguous](metrics-first.md#ask-back-when-ambiguous)
- Address: https://rollingedition.com/concepts/ai-agents/ask-back

## audit entry

every question the agent handles gets an audit entry, written by code beside the answer, never by the model

- Also: audit entries, audit log
- Defined in: [Log who asked what, and what ran](who-may-see-what.md#log-who-asked)
- Address: https://rollingedition.com/concepts/data-governance/audit-log

## average order value

Average order value is a derived metric, net_revenue / kept_orders

- Also: AOV
- Formula: `net_revenue / kept_orders`
- A kind of: derived metric
- Computed from: kept_orders
- Computed from: net revenue
- Defined in: [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics)
- Address: https://rollingedition.com/concepts/data-warehousing/average-order-value

## binding the role at build

Binding the role at build means one server per person, which is what stdio gives you: the host starts a process for its user, and the process lives as long as the host needs it

- Also: role binding, bind the role
- Defined in: [Carry the caller's role into every query](serve-over-mcp.md#carry-the-role)
- Address: https://rollingedition.com/concepts/ai-agents/binding-the-role-at-build

## BIRD

BIRD, a text-to-SQL benchmark whose questions come with "external knowledge evidence"

- A kind of: public benchmark
- Defined in: [Add the business glossary](layered-context.md#add-the-glossary)
- Address: https://rollingedition.com/concepts/llm-evaluation/bird

## business definition

Words such as revenue, order value or active customer have one meaning in a business, chosen by the people who own the number, and that meaning lives in a finance policy, a dashboard's SQL or someone's memory.

- Kinds: net revenue
- Defined in: [Definitions the schema doesn't hold](wrong-numbers.md#definitions-not-in-schema)
- Address: https://rollingedition.com/concepts/data-governance/business-definition

## business glossary

A business glossary lists the business words whose meaning a company's teams chose, and writes each meaning in terms of the warehouse's tables and columns.

- Also: glossary
- Part of: layered context
- Defined in: [Add the business glossary](layered-context.md#add-the-glossary)
- Address: https://rollingedition.com/concepts/artificial-intelligence/business-glossary

## check query

Where you can, a second query written another way, the gold's check_sql, must return the same result as the golden SQL.

- Also: check_sql, check queries
- Part of: golden question
- Defined in: [Check the gold before you trust it](golden-questions.md#check-the-gold)
- Address: https://rollingedition.com/concepts/llm-evaluation/check-query

## client

an application, the host, runs a client for each server it connects to

- Also: MCP client, clients
- Part of: Model Context Protocol
- Defined in: [Serve the semantic layer over MCP](serve-over-mcp.md)
- Address: https://rollingedition.com/concepts/ai-agents/mcp-client

## Cohen's kappa

Cohen's kappa estimates chance agreement from each rater's own label shares

- Also: kappa, κ
- Formula: `kappa, pi = (p_o − chance) / (1 − chance)`
- Contrasts with: Scott's pi
- The same as: https://rollingedition.com/concepts/search-and-recommendation/cohens-kappa
- Close to: https://rollingedition.com/concepts/artificial-intelligence/kappa
- Defined in: [Calibrate the judge against reference labels](catch-regressions.md#calibrate-the-judge)
- Address: https://rollingedition.com/concepts/llm-evaluation/cohens-kappa

## column mask

A column mask decides what a role sees in a column: the value replaced by something that reveals nothing, here the text (masked).

- Also: column masks, mask, masking
- Contrasts with: denied column
- Defined in: [Mask columns in every path](who-may-see-what.md#mask-every-path)
- Address: https://rollingedition.com/concepts/data-governance/column-mask

## column note

A column note is a sentence about one table or column that says what its name doesn't: which rows the table holds, the unit and sign of an amount, the time zone of a timestamp, the values a column takes, or that a table is deprecated.

- Also: column notes
- Part of: layered context
- Defined in: [Describe columns where names mislead](layered-context.md#describe-columns)
- Address: https://rollingedition.com/concepts/artificial-intelligence/column-note

## comparison rule

The comparison rule, results_match() in lib/golden.py, accepts an answer when it has as many rows as the golden result and its columns include every golden column's values.

- Also: results_match()
- Comes before: execution match
- Defined in: [Score both on five golden questions](bi-agent-end-to-end.md#score-five-questions)
- Address: https://rollingedition.com/concepts/llm-evaluation/comparison-rule

## control

A control is something the model can't change.

- Also: controls, access control
- Defined in: [A rule in the prompt is not a control](who-may-see-what.md#prompt-rules-fail)
- Address: https://rollingedition.com/concepts/data-governance/access-control

## correct

An answer is correct when the result matches the golden result, or when it declines a question that should be declined.

- Measured from: golden question
- Defined in: [Score both on five golden questions](bi-agent-end-to-end.md#score-five-questions)
- Address: https://rollingedition.com/concepts/llm-evaluation/correct-outcome

## coverage

Coverage is the share of questions the system answers

- Formula: `coverage = questions answered with a number / questions asked`
- Defined in: [Measure declines, not only accuracy](say-when-it-cannot.md#measure-declines)
- Address: https://rollingedition.com/concepts/llm-evaluation/selective-coverage

## custom granularity

A custom granularity, such as fiscal_year, is a column of the time spine that names the period each day belongs to

- Also: custom grain, custom grains, custom granularities
- True for: metricflow 0.214.0
- Part of: time spine
- Defined in: [Put the fiscal calendar in the time spine](semantic-layer.md#time-grains-and-fiscal)
- Address: https://rollingedition.com/concepts/data-warehousing/custom-granularity

## DABstep

DABstep asks questions about a payments processor's transactions, scores only the final answer, and keeps the answers to most of its tasks hidden for its leaderboard

- Also: Data Agent Benchmark for Multi-step Reasoning
- A kind of: public benchmark
- Defined in: [Why a public benchmark isn't your test](golden-questions.md#benchmarks-are-not-your-test)
- Address: https://rollingedition.com/concepts/llm-evaluation/dabstep

## database catalog

What no setting hides is DuckDB's catalog, such as information_schema and duckdb_settings(), which describes the database itself.

- Also: DuckDB's catalog
- True for: duckdb 2.0.0
- Defined in: [Give the agent a database with only what it may read](guarded-sql.md#least-privilege-database)
- Address: https://rollingedition.com/concepts/data-warehousing/database-catalog

## decline

A decline is an answer: it ends the run, it says why, and the person can act on it.

- Also: declines, declining
- Contrasts with: ask_back
- Defined in: [Decline with a reason](say-when-it-cannot.md#decline-with-a-reason)
- Address: https://rollingedition.com/concepts/ai-agents/decline

## decline kind

A decline's kind, the reason's other part, comes from a fixed list, for the code, so declines can be counted, routed and scored by kind instead of read one at a time.

- Part of: decline
- Defined in: [Decline with a reason](say-when-it-cannot.md#decline-with-a-reason)
- Address: https://rollingedition.com/concepts/ai-agents/decline-kind

## decline precision

Decline precision asks how many of the agent's declines were due

- Formula: `decline precision = correct declines / all declines`
- Measured from: decline
- Contrasts with: decline recall
- Defined in: [Measure declines, not only accuracy](say-when-it-cannot.md#measure-declines)
- Address: https://rollingedition.com/concepts/llm-evaluation/decline-precision

## decline reason

A decline's reason, the sentence that tells the person why no number came

- Also: decline's reason, reason for declining
- Part of: decline
- Defined in: [Judge only what can't be compared](catch-regressions.md#judge-what-cannot-be-compared)
- Address: https://rollingedition.com/concepts/llm-evaluation/decline-reason

## decline recall

decline recall asks how many of the due declines the agent made

- Formula: `decline recall = correct declines / questions whose right answer is a decline`
- Measured from: decline
- Defined in: [Measure declines, not only accuracy](say-when-it-cannot.md#measure-declines)
- Address: https://rollingedition.com/concepts/llm-evaluation/decline-recall

## declined

A declined answer says it can't answer a question that has an answer.

- Contrasts with: wrong answer
- Defined in: [Score both on five golden questions](bi-agent-end-to-end.md#score-five-questions)
- Address: https://rollingedition.com/concepts/llm-evaluation/false-refusal

## denied column

A denied column is left out of the role's database and its allowlist, so the guard refuses it, and the refusal, which lists the columns the model may use, doesn't name it.

- Also: denied columns
- Defined in: [Mask columns in every path](who-may-see-what.md#mask-every-path)
- Address: https://rollingedition.com/concepts/data-governance/denied-column

## deny by default

Deny by default means that any table a filtered role's filter doesn't name or list as unfiltered is refused, so a mart added later stays closed to the lead until someone writes its filter.

- Defined in: [Apply row filters in the compiler](who-may-see-what.md#row-filters-in-compiler)
- Address: https://rollingedition.com/concepts/data-governance/deny-by-default

## derived metric

a derived metric combines several metrics with an expression

- Also: derived metrics
- A kind of: metric
- Computed from: simple metric
- Defined in: [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics)
- Address: https://rollingedition.com/concepts/data-warehousing/derived-metric

## differencing

Differencing involves an intruder using multiple overlapping tables and subtraction

- Also: differencing attack
- Defined in: [Subtracting two answers recovers a group](who-may-see-what.md#differencing-limit)
- Address: https://rollingedition.com/concepts/data-governance/differencing

## dimension

dimensions (what you can group and filter by)

- Also: dimensions
- Part of: semantic model
- Part of: metric request
- Defined in: [Define metrics once in a semantic layer](semantic-layer.md)
- Address: https://rollingedition.com/concepts/data-warehousing/dimension

## entity

An entity is a key with a type.

- Also: entities
- True for: metricflow 0.214.0
- Part of: semantic model
- Defined in: [Describe each table as a semantic model](semantic-layer.md#entities-measures-dimensions)
- Address: https://rollingedition.com/concepts/data-warehousing/entity

## error

An error is an answer whose SQL doesn't run.

- Contrasts with: wrong answer
- Defined in: [Score both on five golden questions](bi-agent-end-to-end.md#score-five-questions)
- Address: https://rollingedition.com/concepts/llm-evaluation/error-outcome

## error prefix

the SDK's tool wrapper puts "Error executing tool" and the tool's name in front of the message of any ToolError a tool raises

- True for: mcp 2.3.0
- Part of: tool execution error
- Defined in: [Return answers with their provenance](serve-over-mcp.md#return-provenance)
- Address: https://rollingedition.com/concepts/ai-agents/error-prefix

## execution accuracy

execution accuracy, which compares the rows each query returns

- Defined in: [Compare results, not SQL text](golden-questions.md#compare-results-not-sql)
- Address: https://rollingedition.com/concepts/llm-evaluation/execution-accuracy

## execution match

An execution match means the agent's result equals the golden result under the question's comparison rule.

- Measured from: golden question
- Defined in: [Compare results, not SQL text](golden-questions.md#compare-results-not-sql)
- Address: https://rollingedition.com/concepts/llm-evaluation/execution-match

## EXPLAIN

For cost, the guard asks DuckDB's EXPLAIN for the plan, which plans the query without running it and gives each step an estimated number of rows

- Also: query plan
- True for: duckdb 2.0.0
- Implemented by: duckdb 2.0.0
- Defined in: [Bound the rows and the cost](guarded-sql.md#bound-rows-and-cost)
- Address: https://rollingedition.com/concepts/data-warehousing/explain

## external knowledge evidence

hints that link a question's words to the database, such as what a term means as a formula over columns

- Part of: BIRD
- Defined in: [Add the business glossary](layered-context.md#add-the-glossary)
- Address: https://rollingedition.com/concepts/llm-evaluation/external-knowledge-evidence

## failure kind

Five kinds of plausible wrong number: fan-out, a definition the schema doesn't hold, time zones and the fiscal calendar, a tempting table, and an unwritten filter.

- Also: failure kinds, kinds of plausible wrong number
- Defined in: [Decisions this chapter made](wrong-numbers.md#wrong-numbers-decisions)
- Address: https://rollingedition.com/concepts/llm-evaluation/failure-kind

## familiarity

familiarity, text that has low perplexity for the judge

- Defined in: [Calibrate the judge against reference labels](catch-regressions.md#calibrate-the-judge)
- Address: https://rollingedition.com/concepts/llm-evaluation/familiarity

## fan-out

Fan-out is what happens when a query joins a table to another that has several rows for each of its rows, and then sums or counts a column of the first.

- A kind of: failure kind
- A kind of: failure kind
- Defined in: [Joins that fan out and inflate a sum](wrong-numbers.md#joins-that-fan-out)
- Address: https://rollingedition.com/concepts/data-warehousing/fan-out

## fiscal year

The shop's fiscal year starts on February 1, and is named for the year it ends in.

- Also: fiscal years
- Defined in: [Meet the shop and its warehouse](bi-agent-end-to-end.md#meet-the-shop)
- Address: https://rollingedition.com/concepts/data-warehousing/fiscal-year

## forbidden question

A forbidden question is answerable, but not for the role asking: the shop's finance team may not see customers' emails, and a regional lead may see only their own region.

- Also: forbidden questions
- A kind of: golden question
- Defined in: [Cover declines and roles, not only answers](golden-questions.md#cover-declines-and-roles)
- Address: https://rollingedition.com/concepts/llm-evaluation/forbidden-question

## foreign entity

A foreign entity is a key that points at another table's primary entity, and it may repeat.

- Also: foreign entities
- True for: metricflow 0.214.0
- A kind of: entity
- Defined in: [Describe each table as a semantic model](semantic-layer.md#entities-measures-dimensions)
- Address: https://rollingedition.com/concepts/data-warehousing/foreign-entity

## freshness

Freshness is how far a source's events have arrived, read from when its rows were loaded.

- Also: data freshness
- Comes before: freshness check
- Part of: provenance
- Defined in: [Check freshness before answering](say-when-it-cannot.md#check-freshness)
- Address: https://rollingedition.com/concepts/data-warehousing/freshness

## freshness check

The freshness check in lib/declining.py compares each feed's newest load with the end of the period a request filters on, plus the settling window of the metrics that read the feed.

- Computed from: settling window
- Defined in: [Check freshness before answering](say-when-it-cannot.md#check-freshness)
- Address: https://rollingedition.com/concepts/data-warehousing/freshness-check

## golden question

A golden question is a question with its checked answer: the kind of answer expected and, when the answer is a result, the golden SQL, written against the owner's definition, and the golden result that SQL returns.

- Also: golden questions
- Defined in: [Run the SQL and check the number](bi-agent-end-to-end.md#check-the-first-number)
- Address: https://rollingedition.com/concepts/llm-evaluation/golden-question

## golden result

the golden result: the question's answer from SQL written against the finance team's definitions and checked by running it

- Also: golden results
- Part of: golden question
- Defined in: [Where raw text-to-SQL gets the number wrong](wrong-numbers.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/golden-result

## guarded SQL

Guarded SQL is the fallback, not the default, for questions no metric covers, written with chapter 4's four layers of context.

- Also: guarded SQL path
- Contrasts with: metric
- Defined in: [Decisions this chapter made](guarded-sql.md#guarded-sql-decisions)
- Address: https://rollingedition.com/concepts/ai-agents/guarded-sql

## held-out split

A held-out split is the usual defence: tune on one part, and score the other only when you report a result.

- Also: held-out set, test split
- The same as: https://rollingedition.com/concepts/artificial-intelligence/test-split
- Defined in: [Hold out a test split](golden-questions.md#hold-out-a-test-split)
- Address: https://rollingedition.com/concepts/llm-evaluation/held-out

## host

A host is the application that runs the model and calls the server's tools for it

- Also: MCP host, hosts
- Part of: Model Context Protocol
- Defined in: [Answer questions through a host](serve-over-mcp.md#answer-through-a-host)
- Address: https://rollingedition.com/concepts/ai-agents/mcp-host

## in-memory client

The Python SDK's Client connects to a server object in the same process when you pass it one instead of a URL

- Also: in-memory clients
- True for: mcp 2.3.0
- A kind of: client
- Implemented by: mcp 2.3.0
- Defined in: [Test the server in memory](serve-over-mcp.md#test-the-server)
- Address: https://rollingedition.com/concepts/ai-agents/in-memory-client

## judge

a judge, a model call that grades an answer against a rubric and returns a verdict

- Also: judges, model as a judge, LLM judge
- Close to: https://rollingedition.com/concepts/search-and-recommendation/judge
- Contrasts with: comparison rule
- Defined in: [Judge only what can't be compared](catch-regressions.md#judge-what-cannot-be-compared)
- Address: https://rollingedition.com/concepts/llm-evaluation/judge

## judge calibration

Calibrating a judge against reference labels measures how often the judge agrees with a check you trust, and in which direction it errs.

- Also: calibrating a judge, calibrate the judge
- Measured from: reference label
- Defined in: [Calibrate the judge against reference labels](catch-regressions.md#calibrate-the-judge)
- Address: https://rollingedition.com/concepts/llm-evaluation/judge-calibration

## kept_orders

kept_orders is the orders metric with the rule on cancelled orders applied as an input filter

- A kind of: simple metric
- Defined in: [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics)
- Address: https://rollingedition.com/concepts/data-warehousing/kept-orders

## layered context

Layered context is the most direct fix for what a schema can't say: write the rules down where the model reads them.

- Contrasts with: semantic layer
- Defined in: [Give the agent layered context](layered-context.md)
- Address: https://rollingedition.com/concepts/artificial-intelligence/layered-context

## least privilege

Least privilege means that the agent's SQL runs on a connection that can reach what the agent may query and nothing else.

- Defined in: [Give the agent a database with only what it may read](guarded-sql.md#least-privilege-database)
- Address: https://rollingedition.com/concepts/data-governance/least-privilege

## legacy table

Most warehouses keep tables that nobody should query any more and nobody can drop: an older mart that old dashboards read, a copy from a migration, a table built for one analysis.

- Also: legacy tables, tempting table
- A kind of: failure kind
- Defined in: [The table with the tempting name](wrong-numbers.md#the-tempting-table)
- Address: https://rollingedition.com/concepts/data-warehousing/legacy-table

## lexical retrieval

Lexical retrieval matches words

- The same as: https://rollingedition.com/concepts/search-and-recommendation/lexical-retrieval
- Defined in: [What goes wrong in production](layered-context.md#layered-context-in-production)
- Address: https://rollingedition.com/concepts/artificial-intelligence/lexical-retrieval

## line_net_revenue

line_net_revenue is net revenue counted on the lines themselves, in the order_lines semantic model, with net revenue's rule on cancelled orders.

- Also: line-level net revenue, line-level revenue
- A kind of: simple metric
- A kind of: net revenue
- Defined in: [Join through entities so sums can't fan out](semantic-layer.md#join-through-entities)
- Address: https://rollingedition.com/concepts/data-warehousing/line-net-revenue

## local business day

The shop counts each order on its region's local business day, stored as order_date_local in the orders mart, beside the UTC timestamp placed_at.

- Also: local business days
- Defined in: [Time zones and the fiscal calendar](wrong-numbers.md#time-and-calendars)
- Address: https://rollingedition.com/concepts/data-warehousing/local-business-day

## long tail

The questions no metric covers are the long tail: how much revenue came from orders that included a tent, or what share of sessions converted.

- Comes before: guarded SQL
- Defined in: [Let the agent write SQL inside guards](guarded-sql.md)
- Address: https://rollingedition.com/concepts/data-warehousing/long-tail

## MCP tool

An MCP tool is a name, a description the model reads, a JSON Schema for its arguments and, optionally, a schema for its result.

- Also: MCP tools
- Part of: server
- Defined in: [Turn metrics into tools](serve-over-mcp.md#metrics-as-tools)
- Address: https://rollingedition.com/concepts/ai-agents/mcp-tool

## measure

the measure: an aggregation declared on the semantic model, which a metric then names

- Also: measures
- True for: metricflow 0.214.0
- Contrasts with: simple metric
- Defined in: [Describe each table as a semantic model](semantic-layer.md#entities-measures-dimensions)
- Address: https://rollingedition.com/concepts/data-warehousing/measure

## metric

A metric is a business measure written down once, by the people who own it: a name, a description a person can check, how it is computed from the marts, the rule for which rows count, and the dimensions it may be grouped and filtered by.

- Also: metrics, defined metric
- Comes before: metric request
- Defined in: [Answer from one defined metric](bi-agent-end-to-end.md#answer-from-a-metric)
- Address: https://rollingedition.com/concepts/data-warehousing/metric

## metric filter

A metric's filter is a Jinja template

- True for: metricflow 0.214.0
- Part of: metric
- Defined in: [What goes wrong in production](semantic-layer.md#semantic-layer-in-production)
- Address: https://rollingedition.com/concepts/data-warehousing/metric-filter

## metric request

A metric request names the metric, the dimensions to group by and one value per filtered dimension, and compile_request() turns it into SQL.

- Also: metric requests
- Defined in: [Answer from one defined metric](bi-agent-end-to-end.md#answer-from-a-metric)
- Address: https://rollingedition.com/concepts/data-warehousing/metric-request

## metric tool

A metric tool exposes what a semantic layer holds in the shape a person asks for it: metric names with their descriptions, the dimensions each can be grouped and filtered by, and the time grains.

- Also: metric tools
- Part of: metrics-first
- Defined in: [Give the agent metrics, not tables](metrics-first.md#metrics-not-tables)
- Address: https://rollingedition.com/concepts/ai-agents/metric-tool

## metrics-first

Routing a question to governed metrics first takes writing the query away from the model: its job shrinks to choosing which metric, grouped by what, filtered how, and the layer, which people own and test, writes the SQL.

- Also: governed metrics first
- Contrasts with: layered context
- Defined in: [Route questions to governed metrics first](metrics-first.md)
- Address: https://rollingedition.com/concepts/ai-agents/metrics-first

## minimum group size

a minimum group size, a number of people below which a group's values are held back

- Also: minimum group sizes
- Comes before: small-group suppression
- Defined in: [Suppress groups small enough to identify someone](who-may-see-what.md#suppress-small-groups)
- Address: https://rollingedition.com/concepts/data-governance/minimum-group-size

## Model Context Protocol

MCP is an open protocol in which an application, the host, runs a client for each server it connects to, and a server offers tools that the host's model can call.

- Also: MCP
- Implemented by: mcp 2.3.0
- The same as: https://rollingedition.com/concepts/artificial-intelligence/mcp-protocol
- Defined in: [Serve the semantic layer over MCP](serve-over-mcp.md)
- Address: https://rollingedition.com/concepts/ai-agents/model-context-protocol

## net revenue

The golden SQL for gq-002 follows the shop's definition of net revenue, which the finance team owns: revenue in euros after discounts and before tax, from real orders that weren't cancelled, on the order's local business day.

- A kind of: metric
- Defined in: [Run the SQL and check the number](bi-agent-end-to-end.md#check-the-first-number)
- Address: https://rollingedition.com/concepts/data-warehousing/net-revenue

## NL2SQL-BUGs

One detailed taxonomy, NL2SQL-BUGs, sorts semantic errors in text-to-SQL into 9 categories and 31 subcategories, from 2,018 expert-annotated cases, 999 of them wrong

- Defined in: [Definitions the schema doesn't hold](wrong-numbers.md#definitions-not-in-schema)
- Address: https://rollingedition.com/concepts/llm-evaluation/nl2sql-bugs

## nonexistent filter value

a nonexistent filter value, in PRACTIQ's terms, is a filter value no row holds, such as a region called Europe.

- Also: nonexistent filter values
- Defined in: [Kinds of questions the warehouse can't answer](say-when-it-cannot.md#kinds-of-unanswerable)
- Address: https://rollingedition.com/concepts/artificial-intelligence/nonexistent-filter-value

## nonexistent SELECT column

a nonexistent SELECT column, where "The column that contains the results asked in the question do not exist in the database"

- Defined in: [Kinds of questions the warehouse can't answer](say-when-it-cannot.md#kinds-of-unanswerable)
- Address: https://rollingedition.com/concepts/artificial-intelligence/nonexistent-select-column

## order_refunds

order_refunds, a metric counted on the order's local day

- A kind of: simple metric
- Defined in: [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics)
- Address: https://rollingedition.com/concepts/data-warehousing/order-refunds

## output schema

a tool can declare an outputSchema and return structuredContent that conforms to it

- Also: outputSchema
- Part of: MCP tool
- Defined in: [Return answers with their provenance](serve-over-mcp.md#return-provenance)
- Address: https://rollingedition.com/concepts/ai-agents/output-schema

## paired difference

Comparison in lib/regressions.py takes, for each question, the share of runs correct under the base and under the candidate, and their difference.

- Also: paired differences, mean paired difference
- Close to: https://rollingedition.com/concepts/artificial-intelligence/paired-difference
- Close to: https://rollingedition.com/concepts/search-and-recommendation/per-query-differences
- Defined in: [Gate a change in CI](catch-regressions.md#gate-a-change)
- Address: https://rollingedition.com/concepts/llm-evaluation/paired-difference

## parsing

Parsing turns the text into a tree, with one node for each statement, table, column and function, so each later check asks about nodes, not characters.

- Comes before: allowlist
- Comes before: qualify
- Defined in: [Parse the SQL before it runs](guarded-sql.md#parse-before-running)
- Address: https://rollingedition.com/concepts/artificial-intelligence/parsing

## penalty score

In the penalty score, each question scores one point for a right answer or a right decline, nothing for declining an answerable question, and minus c for a wrong number, including an answer to a question it should have declined; the score is the mean over the questions

- Formula: `penalty score = (right answers + correct declines − c × wrong numbers) / questions asked`
- Computed from: wrong answer
- Defined in: [Measure declines, not only accuracy](say-when-it-cannot.md#measure-declines)
- Address: https://rollingedition.com/concepts/llm-evaluation/penalty-score

## PolicyLayer

PolicyLayer is the semantic layer as one role sees it, and passes every query it compiles through apply().

- A kind of: semantic layer
- Defined in: [Apply row filters in the compiler](who-may-see-what.md#row-filters-in-compiler)
- Address: https://rollingedition.com/concepts/data-governance/policy-layer

## PolicyToolbox

PolicyToolbox, chapter 6's metric tools over PolicyLayer, which end the run with a decline whose reason starts with "forbidden" when the policy refuses a request

- Defined in: [Measure access on the golden questions](who-may-see-what.md#measure-access)
- Address: https://rollingedition.com/concepts/data-governance/policy-toolbox

## primary entity

A primary entity is unique in its table, so other tables can join to it many rows to one.

- Also: primary entities
- True for: metricflow 0.214.0
- A kind of: entity
- Contrasts with: foreign entity
- Defined in: [Describe each table as a semantic model](semantic-layer.md#entities-measures-dimensions)
- Address: https://rollingedition.com/concepts/data-warehousing/primary-entity

## principal

the principal, meaning whoever your sign-in system says is asking

- Also: principals
- Part of: audit entry
- Defined in: [Log who asked what, and what ran](who-may-see-what.md#log-who-asked)
- Address: https://rollingedition.com/concepts/data-governance/principal

## provenance

An answer's provenance is the metric or SQL behind it, the filters, the role it was computed for and how fresh the data was.

- Part of: ToolReply
- Defined in: [Show the provenance with every answer](say-when-it-cannot.md#show-provenance)
- Address: https://rollingedition.com/concepts/data-governance/provenance

## public benchmark

A public benchmark for text-to-SQL or data agents gives you questions, a database and a gold answer for each question, and a score that others have reported on the same set.

- Also: public benchmarks
- Contrasts with: golden question
- Defined in: [Why a public benchmark isn't your test](golden-questions.md#benchmarks-are-not-your-test)
- Address: https://rollingedition.com/concepts/llm-evaluation/public-benchmark

## qualify

check() qualifies every column against the columns of the tables the query may read, with sqlglot's qualify, which raises an error for a column it can't place.

- Also: qualification, qualifies
- True for: sqlglot 30.31.0
- Implemented by: sqlglot 30.31.0
- The same as: https://rollingedition.com/concepts/data-engineering/qualify
- Defined in: [Parse the SQL before it runs](guarded-sql.md#parse-before-running)
- Address: https://rollingedition.com/concepts/artificial-intelligence/column-qualification

## question kind

A golden question's kind says what a right answer looks like: answer when the warehouse can answer it, decline when it can't, and forbidden when the role may not see the answer.

- Part of: golden question
- Defined in: [Write questions from the work people do](golden-questions.md#write-golden-questions)
- Address: https://rollingedition.com/concepts/llm-evaluation/kind

## ratio metric

A ratio metric divides one metric by another

- Also: ratio metrics
- A kind of: metric
- Computed from: simple metric
- Defined in: [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics)
- Address: https://rollingedition.com/concepts/data-warehousing/ratio-metric

## raw schema

The raw schema holds what the source systems loaded: orders, order lines, refunds, customers, products, sessions, marketing spend and exchange rates.

- Defined in: [Meet the shop and its warehouse](bi-agent-end-to-end.md#meet-the-shop)
- Address: https://rollingedition.com/concepts/data-warehousing/raw-schema

## recording

A recording is a saved set of model replies with a manifest, made once by a script in the repository's recordings/ folder and replayed by the examples.

- Also: recordings
- The same as: https://rollingedition.com/concepts/llm-evaluation/recording
- Defined in: [Ask a question, get SQL from a model](bi-agent-end-to-end.md#ask-for-sql)
- Address: https://rollingedition.com/concepts/artificial-intelligence/recording

## reference label

Reference labels computed by results_match() are nobody's opinion: anyone can recompute them from questions.toml and the recordings, and when one looks wrong, the fix is to the golden question, where it's open to correction like the rest of the book.

- Also: reference labels
- Computed from: comparison rule
- Defined in: [Calibrate the judge against reference labels](catch-regressions.md#calibrate-the-judge)
- Address: https://rollingedition.com/concepts/llm-evaluation/reference-label

## refund rate

The shop's finance team defines the refund rate in golden question gq-028: refunded euros over gross revenue of the same orders, those placed in the period that weren't cancelled.

- A kind of: ratio metric
- Computed from: order_refunds
- Defined in: [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics)
- Address: https://rollingedition.com/concepts/data-warehousing/refund-rate

## regression gate

gate() applies two rules of our choosing: it fails on a stable break, a question the base got right in at least four runs of five and the candidate in at most one, or when the whole interval of the mean difference lies below zero.

- Also: CI gate
- Computed from: paired difference
- Defined in: [Gate a change in CI](catch-regressions.md#gate-a-change)
- Address: https://rollingedition.com/concepts/llm-evaluation/regression-gate

## repair

Repair means giving the model the guard's refusal or the warehouse's error, once, and running what it writes next.

- Part of: guarded SQL
- Defined in: [Repair once from the error](guarded-sql.md#repair-once)
- Address: https://rollingedition.com/concepts/ai-agents/repair

## request validation

Validating a request means checking it against the layer's definitions and the warehouse's values before it compiles, and sending every problem back to the model with what would be allowed instead.

- Also: validating a request, validation
- Part of: metrics-first
- Defined in: [Validate the request against the layer](metrics-first.md#validate-the-request)
- Address: https://rollingedition.com/concepts/ai-agents/request-validation

## role

A role is who is asking, role in the code

- Also: roles
- Part of: provenance
- Part of: golden question
- Defined in: [Keep the agent inside who may see what](who-may-see-what.md)
- Address: https://rollingedition.com/concepts/data-governance/requester-role

## role's view

A role's view of a table returns the rows that role may see, with a masked column holding a constant and a denied column left out.

- Also: role view, role's views
- Kinds: secure view
- Defined in: [Give each role a database of views](guarded-sql.md#views-per-role)
- Address: https://rollingedition.com/concepts/data-governance/role-view

## row access policy

Snowflake's row access policies "determine which rows to return in the query result"

- Also: row access policies
- Defined in: [Apply row filters in the compiler](who-may-see-what.md#row-filters-in-compiler)
- Address: https://rollingedition.com/concepts/data-governance/row-access-policy

## row filter

A row filter takes the decision away from the model: a condition on a table, such as region = 'EMEA', that every query reading the table gets, whatever else the query says.

- Also: row filters
- Contrasts with: column mask
- Defined in: [Apply row filters in the compiler](who-may-see-what.md#row-filters-in-compiler)
- Address: https://rollingedition.com/concepts/data-governance/row-filter

## schema

A schema tells a model which tables exist, what their columns are called and what type each column holds.

- Also: schemas
- Part of: layered context
- Defined in: [What the schema says, and what it doesn't](layered-context.md#what-the-schema-says)
- Address: https://rollingedition.com/concepts/data-warehousing/schema

## schema layer

The schema layer is the whole warehouse: all 16 tables, about 912 tokens.

- Part of: layered context
- Defined in: [What the schema says, and what it doesn't](layered-context.md#what-the-schema-says)
- Address: https://rollingedition.com/concepts/artificial-intelligence/schema-layer

## schema-only text-to-SQL

Schema-only text-to-SQL means the model is given the name and type of every column and the person's question, and nothing else, and writes the SQL.

- Also: schema-only SQL
- Contrasts with: metric
- Defined in: [Ask a question, get SQL from a model](bi-agent-end-to-end.md#ask-for-sql)
- Address: https://rollingedition.com/concepts/artificial-intelligence/schema-only-text-to-sql

## scorecard

a scorecard reports wrong numbers, declines and failures apart, the decline measures from chapter 8, and the cost in model calls and prompt tokens, beside accuracy

- Also: scorecards
- Defined in: [Score a run on more than accuracy](catch-regressions.md#score-a-run)
- Address: https://rollingedition.com/concepts/llm-evaluation/scorecard

## Scott's pi

Scott's pi estimates chance agreement from the two raters' shares pooled

- Also: pi, π
- Formula: `kappa, pi = (p_o − chance) / (1 − chance)`
- Defined in: [Calibrate the judge against reference labels](catch-regressions.md#calibrate-the-judge)
- Address: https://rollingedition.com/concepts/llm-evaluation/scotts-pi

## secondary suppression

Secondary suppression, which the handbook also calls complementary suppression (section 4.2.2), suppresses further cells so that no suppressed cell can be worked out from the totals and the cells shown, across breakdowns planned in advance.

- Also: complementary suppression
- Defined in: [Subtracting two answers recovers a group](who-may-see-what.md#differencing-limit)
- Address: https://rollingedition.com/concepts/data-governance/secondary-suppression

## secure view

Snowflake's secure views hide their definition and skip optimizations that could expose filtered rows

- Also: secure views
- Defined in: [Give each role a database of views](guarded-sql.md#views-per-role)
- Address: https://rollingedition.com/concepts/data-governance/secure-view

## selective risk

selective risk is the error rate on the questions the system answers

- Formula: `selective risk = wrong numbers / questions answered with a number`
- Computed from: wrong answer
- Defined in: [Measure declines, not only accuracy](say-when-it-cannot.md#measure-declines)
- Address: https://rollingedition.com/concepts/llm-evaluation/selective-risk

## self-preference

Self-preference, a judge that "scores its own outputs higher than others' while human annotators consider them of equal quality" (Panickssery et al.), is a known bias

- Also: self-enhancement bias
- Defined in: [Calibrate the judge against reference labels](catch-regressions.md#calibrate-the-judge)
- Address: https://rollingedition.com/concepts/llm-evaluation/self-preference

## semantic layer

A semantic layer is where the choices behind joins, grains and ratios are written down once.

- Also: semantic layers
- True for: metricflow 0.214.0
- Implemented by: metricflow 0.214.0
- Comes before: metrics-first
- Defined in: [Define metrics once in a semantic layer](semantic-layer.md)
- Address: https://rollingedition.com/concepts/data-warehousing/semantic-layer

## semantic model

A semantic model is one table described for the layer: which table it reads, the entities it holds, the dimensions it offers and the time dimension its numbers are counted on.

- Also: semantic models
- True for: metricflow 0.214.0
- Part of: semantic layer
- Defined in: [Describe each table as a semantic model](semantic-layer.md#entities-measures-dimensions)
- Address: https://rollingedition.com/concepts/data-warehousing/semantic-model

## semantic server

the shop's semantic layer becomes one MCP server, which this chapter calls the semantic server

- A kind of: server
- Defined in: [Serve the semantic layer over MCP](serve-over-mcp.md)
- Address: https://rollingedition.com/concepts/ai-agents/semantic-server

## server

a server offers tools that the host's model can call

- Also: MCP server, servers
- Part of: Model Context Protocol
- Defined in: [Serve the semantic layer over MCP](serve-over-mcp.md)
- Address: https://rollingedition.com/concepts/ai-agents/mcp-server

## ServerToolbox

ServerToolbox has the call() method the loop expects, and makes each call through an MCP client.

- Defined in: [Answer questions through a host](serve-over-mcp.md#answer-through-a-host)
- Address: https://rollingedition.com/concepts/ai-agents/server-toolbox

## settling window

A metric's settling window, as we call it, is the time until every event it counts for a period has come.

- Also: settling windows
- Comes before: freshness check
- Defined in: [Check freshness before answering](say-when-it-cannot.md#check-freshness)
- Address: https://rollingedition.com/concepts/data-warehousing/settling-window

## simple metric

Simple metrics, like the line-level revenue, aggregate one column of one table.

- Also: simple metrics
- True for: metricflow 0.214.0
- A kind of: metric
- Defined in: [Build ratio and derived metrics from simple ones](semantic-layer.md#ratio-and-derived-metrics)
- Address: https://rollingedition.com/concepts/data-warehousing/simple-metric

## small-group suppression

PolicyLayer then replaces each value of a group behind fewer than 10 customers with (under N), where N is the role's minimum group size.

- Also: suppression, suppressed group
- Defined in: [Suppress groups small enough to identify someone](who-may-see-what.md#suppress-small-groups)
- Address: https://rollingedition.com/concepts/data-governance/small-group-suppression

## Spider 2.0

Spider 2.0, a benchmark of enterprise text-to-SQL tasks

- A kind of: public benchmark
- Defined in: [The table with the tempting name](wrong-numbers.md#the-tempting-table)
- Address: https://rollingedition.com/concepts/llm-evaluation/spider-2

## stable break

a stable break, a question the base got right in at least four runs of five and the candidate in at most one

- Also: stable breaks
- Part of: regression gate
- Defined in: [Gate a change in CI](catch-regressions.md#gate-a-change)
- Address: https://rollingedition.com/concepts/llm-evaluation/stable-break

## step limit

A run that uses all four model calls without an answer is a failure, and grade() scores it as step limit, apart from the declines the model chose.

- Contrasts with: decline
- Defined in: [Measure metrics-first on the golden questions](metrics-first.md#measure-metrics-first)
- Address: https://rollingedition.com/concepts/ai-agents/step-limit

## structured content

Structured content, the JSON a tool returns in structuredContent, is what lets a host's code, rather than its model, read an answer's role and filters.

- Also: structuredContent
- Defined in: [Return answers with their provenance](serve-over-mcp.md#return-provenance)
- Address: https://rollingedition.com/concepts/ai-agents/structured-content

## structured reply

A structured reply is one the code can parse into a typed object and check field by field.

- Also: structured replies
- Kinds: metric request
- Defined in: [Ask for a request, not SQL](metrics-first.md#request-not-sql)
- Address: https://rollingedition.com/concepts/ai-agents/structured-reply

## t interval

a t interval, the mean plus and minus the standard error times Student's t for one fewer degrees of freedom than questions

- Computed from: paired difference
- Defined in: [Gate a change in CI](catch-regressions.md#gate-a-change)
- Address: https://rollingedition.com/concepts/llm-evaluation/t-interval

## time spine

the time spine, a table with one row per day

- True for: metricflow 0.214.0
- Part of: semantic layer
- Defined in: [Describe each table as a semantic model](semantic-layer.md#entities-measures-dimensions)
- Address: https://rollingedition.com/concepts/data-warehousing/time-spine

## token audience

servers must check that each access token was issued for them, as its intended audience

- Also: intended audience
- Defined in: [Carry the caller's role into every query](serve-over-mcp.md#carry-the-role)
- Address: https://rollingedition.com/concepts/ai-agents/token-audience

## token budget

A token budget is the most context the agent may send with one question.

- Defined in: [Fit the context to a budget](layered-context.md#fit-a-context-budget)
- Address: https://rollingedition.com/concepts/large-language-models/token-budget

## token estimate

Token counts in lib/context.py are estimates: estimate_tokens() divides the number of characters by 3.5, because the examples don't load the model's tokenizer.

- Defined in: [Fit the context to a budget](layered-context.md#fit-a-context-budget)
- Address: https://rollingedition.com/concepts/large-language-models/token-estimate

## TokenVerifier

the server is given a TokenVerifier whose verify_token() returns an AccessToken with the client's ID, its scopes and the token's claims

- Also: AccessToken
- True for: mcp 2.3.0
- Implemented by: mcp 2.3.0
- Defined in: [Carry the caller's role into every query](serve-over-mcp.md#carry-the-role)
- Address: https://rollingedition.com/concepts/ai-agents/token-verifier

## tolerance

Numbers must agree with the gold within 0.05% relative by default, plus an absolute slack of half a unit in the last place the gold rounds to.

- Also: absolute slack
- Part of: comparison rule
- Defined in: [Order, rounding and column names](golden-questions.md#order-rounding-names)
- Address: https://rollingedition.com/concepts/llm-evaluation/comparison-tolerance

## tool

A tool is a function the model may ask the code to run, by replying with a JSON object that names it and gives its arguments.

- Also: tools
- The same as: https://rollingedition.com/concepts/search-and-recommendation/tool
- Defined in: [Answer from one defined metric](bi-agent-end-to-end.md#answer-from-a-metric)
- Address: https://rollingedition.com/concepts/ai-agents/tool

## tool execution error

The MCP specification reports a tool execution error as a result with isError set, with "actionable feedback that language models can use to self-correct"

- Also: tool error, tool errors, ToolError
- Contrasts with: decline
- Defined in: [Return answers with their provenance](serve-over-mcp.md#return-provenance)
- Address: https://rollingedition.com/concepts/ai-agents/tool-execution-error

## ToolReply

Every tool of the semantic server returns a ToolReply, a pydantic model with two fields: text, the text the in-process tool shows the model, and answer, the answer with its rows and provenance, or nothing when the result doesn't end the run.

- Defined in: [Return answers with their provenance](serve-over-mcp.md#return-provenance)
- Address: https://rollingedition.com/concepts/ai-agents/tool-reply

## trace

The trace is every step of one run, kept by run_agent(): each model reply, and each tool result sent back.

- Also: traces
- The same as: https://rollingedition.com/concepts/search-and-recommendation/trace
- Defined in: [Read the trace of one run](bi-agent-end-to-end.md#read-one-trace)
- Address: https://rollingedition.com/concepts/ai-agents/trace

## unanswerable question

An unanswerable question, such as the cost of shipping, asks for data the warehouse doesn't hold, and the agent should say so.

- Also: unanswerable questions
- Kinds: nonexistent SELECT column
- Defined in: [Cover declines and roles, not only answers](golden-questions.md#cover-declines-and-roles)
- Address: https://rollingedition.com/concepts/llm-evaluation/unanswerable-item

## unwritten filter

Some rules about which rows count are so familiar to the people who own a number that nobody writes them down: cancelled orders don't count as revenue, test accounts aren't customers, a refund belongs to the month of its order.

- Also: unwritten filters
- A kind of: failure kind
- A kind of: failure kind
- Defined in: [Filters nobody wrote down](wrong-numbers.md#unwritten-filters)
- Address: https://rollingedition.com/concepts/data-warehousing/unwritten-filter

## verified query

A verified query shows the shop's rules applied: a question someone asked, with SQL a person checked against the shop's definitions.

- Also: verified queries
- Part of: layered context
- Part of: verified query repository
- Defined in: [Retrieve verified queries as examples](layered-context.md#retrieve-verified-queries)
- Address: https://rollingedition.com/concepts/artificial-intelligence/verified-query

## verified query repository

Snowflake's Cortex Analyst keeps a verified query repository of "questions and corresponding SQL queries to answer them"

- Defined in: [Retrieve verified queries as examples](layered-context.md#retrieve-verified-queries)
- Address: https://rollingedition.com/concepts/artificial-intelligence/verified-query-repository

## Wilson interval

Wilson's interval inverts the test of a proportion: it holds every true accuracy that the observed one wouldn't reject at the chosen level, so it never runs below 0 or above 1.

- Also: Wilson's interval, Wilson score interval
- Formula: `centre = (p + z² / 2n) / (1 + z² / n) half = z × √( p(1 − p) / n + z² / 4n² ) / (1 + z² / n) interval = centre − half to centre + half`
- Part of: scorecard
- Defined in: [Score a run on more than accuracy](catch-regressions.md#score-a-run)
- Address: https://rollingedition.com/concepts/llm-evaluation/wilson-interval

## worker

The guard plans and runs the agent's query in a worker, a separate process started by Worker in lib/sql_guard.py that opens the agent's database file read-only with the guard's settings, and kills it when the 5-second deadline passes.

- Also: worker process
- Defined in: [Enforce the deadline by killing a process](guarded-sql.md#time-the-plan)
- Address: https://rollingedition.com/concepts/artificial-intelligence/worker

## wrong answer

A wrong answer returns a different result, or returns any result for a question that should be declined.

- Also: wrong answers
- Measured from: golden question
- Contrasts with: error
- Defined in: [Score both on five golden questions](bi-agent-end-to-end.md#score-five-questions)
- Address: https://rollingedition.com/concepts/llm-evaluation/wrong-outcome
