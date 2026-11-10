---
title: "Business Intelligence with Agents"
chapter: "Route questions to governed metrics first"
chapter_id: metrics-first
book: business-intelligence-with-agents
edition: 2026.11.7
verified: 2026-11-10
edition_code: ZNJE-JAVW
canonical: https://rollingedition.com/business-intelligence-with-agents/metrics-first
license: CC BY 4.0
attribution: "“Route questions to governed metrics first,” chapter 6 of Business Intelligence with Agents, Edition 2026.11.7, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/business-intelligence-with-agents/metrics-first. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Route questions to governed metrics first

By the end of this chapter, you can give the agent the semantic layer's metrics as tools instead of the warehouse's tables, have it return a structured metric request that's validated before anything runs, have it ask the person back when a question could mean several metrics, and measure the change on the golden questions.

[Chapter 5](#semantic-layer) wrote the shop's definitions down once, as a semantic layer: ten metrics over five semantic models, compiled to SQL by the book's own compiler in `lib/semantic.py`. A person who knows the layer can ask it for net revenue by region in March 2026 and get the finance team's number. The agent can't yet. [Chapter 1](#bi-agent-end-to-end) gave it one metric, and the baseline it has to beat is schema-only SQL, which gets 2 of 24 dev questions right. [Chapter 4](#layered-context) gave the model definitions as text beside the schema, but the model still wrote the SQL, so every definition still had to survive the model's reading of it.

Routing a question to governed metrics first means the model's job shrinks to choosing: which metric, grouped by what, filtered how. The layer, which people own and test, writes the SQL. Warehouse vendors describe their own assistants the same way. Databricks' guidance for its question-answering Genie Agents says "Metric views are particularly effective for Genie Agents because they pre-define metrics, dimensions, and aggregations" ([Databricks](https://docs.databricks.com/aws/en/genie/best-practices)), and Snowflake says "Semantic Views are the recommended approach for working with Cortex Analyst" ([Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)). Those are vendors' recommendations for their own products, not measurements. This chapter measures the pattern on the shop's golden questions, with the same recorded model as every other chapter.

## Give the agent metrics, not tables {#metrics-not-tables}

An agent's tools decide what it can get wrong. Given tables, a model can join them the wrong way, miss a filter or pick the legacy mart, as [chapter 2](#wrong-numbers) showed one failure at a time. Given metrics, it can still pick the wrong metric or the wrong dimension, but it can't rewrite a definition, because definitions aren't among the things it can touch. A metric tool exposes what a semantic layer holds in the shape a person would ask for it: metric names with their descriptions, the dimensions each can be grouped and filtered by, and the time grains. Databricks describes its Unity Catalog metric views in the same terms, as separating "measure definitions from the fields (also called dimensions) used to group, filter, and aggregate them" ([Databricks](https://docs.databricks.com/aws/en/metric-views/)).

The shop's agent gets its metric tools from `lib/metric_tools.py`, a module this chapter adds. Its `MetricToolbox` wraps one warehouse connection and the semantic layer from [chapter 5](#entities-measures-dimensions), and offers five tools: `list_metrics`, `describe_metric`, `query_metric`, `ask_back` and `cannot_answer`. The prompt, `METRICS_FIRST` in `lib/prompts.py`, carries what `list_metrics` returns, so the model doesn't spend a call asking for it: one line per metric, with its description and the dimensions it can use. The prompt also says how the shop's fiscal year runs and how to write a period as a filter value, and it names the regions and the sales channels. It lists no tables and no columns.

The example builds the prompt, prints one line of the catalog and what `describe_metric` returns for the refund rate, and compares the size of two prompts for the same golden question, `gq-002`, net revenue in each region in March 2026: the schema-only prompt from [chapter 1](#ask-for-sql), and this one. Both sizes are the token counts the model's runtime reported when the calls were recorded.

Example `metric-tools` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Give the agent the semantic layer's metrics instead of the warehouse's tables, and compare what each prompt holds."""
from lib.golden import load_golden
from lib.metric_tools import MetricToolbox, catalog
from lib.model import RecordedModel
from lib.prompts import metrics_first_prompt, schema_only_messages
from lib.warehouse import connect, describe_schema

con = connect()
toolbox = MetricToolbox(con)
system = metrics_first_prompt(catalog(toolbox.layer))
print(f"tools: {', '.join(toolbox.tools)}")
print(f"metrics in the prompt: {len(toolbox.layer.metrics)}")
print(f"tables in the prompt: {system.count('CREATE TABLE')}")
print(catalog(toolbox.layer).splitlines()[0])

print(toolbox.call("describe_metric", {"metric": "refund_rate"}).content)

# The first call of the same golden question, gq-002, under each prompt, as the recordings measured it.
question = next(q for q in load_golden() if q.question_id == "gq-002").question
schema_only = schema_only_messages(describe_schema(con), question)
metrics_first = [{"role": "system", "content": system}, {"role": "user", "content": question}]
print(f"schema-only prompt tokens: {RecordedModel('schema-only-sql').call_for(schema_only)['prompt_tokens']}")
print(f"metrics-first prompt tokens: {RecordedModel('metric-agent-runs').call_for(metrics_first)['prompt_tokens']}")
```

Output:

```text
tools: list_metrics, describe_metric, query_metric, ask_back, cannot_answer
metrics in the prompt: 10
tables in the prompt: 0
- net_revenue: Revenue in EUR after discounts and before tax, from real orders that weren't cancelled, counted on the order's local business day. Returned orders count; refunds are not subtracted. Dimensions: customer__country, customer__first_order_date, customer__region, order__channel, order__country, order__order_date, order__region, order__status
refund_rate, a ratio metric: Refunded EUR over gross revenue of the same orders: orders placed in the period that weren't cancelled.
Dimensions:
- metric_time__day
- metric_time__week
- metric_time__month
- metric_time__quarter
- metric_time__year
- metric_time__fiscal_year: 2025, 2026, 2027
- metric_time__fiscal_quarter: 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4, 2026-Q1, 2026-Q2, 2026-Q3, 2026-Q4, 2027-Q1, 2027-Q2
- order__channel: (none), app, marketplace, web
- order__country: AU, CA, DE, ES, FR, GB, JP, NL, SG, US
- order__order_date
- order__region: AMER, APAC, EMEA
- order__status: cancelled, delivered, placed, returned, shipped
schema-only prompt tokens: 827
metrics-first prompt tokens: 1120
```

The prompt lists 10 metrics and 0 tables. Each metric's line is its owner's description, word for word from the YAML, followed by the dimensions it can reach without fan-out. Net revenue's line names `order__region` and `customer__region`, but not `product__category`, because the orders model reaches products only through the order lines, several per order.

`describe_metric` adds what the catalog leaves out: the time grains, and the values of each categorical dimension, read from the warehouse when the tool runs. The refund rate's regions are `AMER`, `APAC` and `EMEA`, and its fiscal quarters are labels such as `2026-Q1`. The prompt already names the regions and channels, so for those the tool repeats what the model was told. For the countries, the order statuses and the fiscal periods, it's the only place the model sees how the shop writes them.

The metrics-first prompt isn't smaller. It is 1120 tokens against the schema-only prompt's 827, because a definition takes more words than a column name. What changed is what the tokens hold: rules a person wrote and checked, instead of names the model has to interpret.

**Working rule:** Give the agent the metrics, their descriptions and the dimensions each can use, and keep tables out of its tools until a question needs them. Put the catalog in the prompt while it fits, so a run doesn't spend a call listing metrics, and let a describe tool return dimension values from the warehouse. When the catalog outgrows the prompt, keep names and descriptions there and move the dimensions behind the describe tool.

## Ask for a request, not SQL {#request-not-sql}

With [metric tools](#metrics-not-tables) in place, the model's reply is no longer a query but a request. A structured reply is one the code can parse into a typed object and check field by field. Here it is a JSON tool call whose arguments become a `MetricRequest`, the metric request from [chapter 5](#compile-a-metric-request), which names metrics, group-by dimensions, filters, an order and a limit. Nothing in it is SQL, so the model can't add anything to a query that the layer didn't define.

Qwen's chat template for the model this book records with asks for each tool call as JSON inside `<tool_call>` tags, and returns tool results inside `<tool_response>` tags ([Qwen's template](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/raw/main/tokenizer_config.json)). Qwen's model card recommends its Qwen-Agent library, which "encapsulates tool-calling templates and tool-calling parsers internally" ([model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)). We keep the book's own format instead: the prompt asks for one bare JSON object, `{"tool": ..., "arguments": ...}`, which `run_agent()` in `lib/agent.py` parses, as it has since [chapter 1](#answer-from-a-metric). A small parser we own is easier to test than a library's, and no library release can change it.

The shop's case is golden question `gq-003`, net revenue by sales channel in calendar 2025. Schema-only SQL failed it in chapter 1 by filtering `fct_orders` on a `calendar_year` column that exists only in `dim_date`. The recording `metric-agent-runs` holds the same model's replies to the metrics-first prompt for all 48 golden questions. It was made by `recordings/record_metrics_first.py` with the pinned model file, Qwen's recommended sampling and a seed reset before every call, like every recording in this book. The example replays the run for `gq-003`.

Example `model-returns-a-request` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""The model returns a metric request, not SQL: the layer compiles the request, and the answer is checked against gold."""
from lib.agent import run_agent
from lib.golden import golden_result, load_golden, results_match, schema_only_outcome
from lib.metric_tools import MetricToolbox, catalog
from lib.model import RecordedModel
from lib.prompts import metrics_first_prompt
from lib.semantic import MetricRequest
from lib.warehouse import connect, describe_schema

con = connect()
toolbox = MetricToolbox(con)
system = metrics_first_prompt(catalog(toolbox.layer))
question = next(q for q in load_golden() if q.question_id == "gq-003")
model = RecordedModel("metric-agent-runs")
trace = run_agent(question.question, system, model, toolbox, max_steps=4)

print(f"question: {question.question}")
print(f"model calls: {sum(step.kind == 'model' for step in trace.steps)}")
print(f"reply: {trace.steps[0].content}")
print(MetricRequest.from_arguments(trace.steps[0].arguments))
print(trace.answer.provenance.sql)
print(trace.answer.show())
print(f"matches golden: {results_match(trace.answer.rows, golden_result(con, question))}")

schema = describe_schema(con)
print(f"schema-only outcome: {schema_only_outcome(con, RecordedModel('schema-only-sql'), schema, question)}")
```

Output:

```text
question: How much net revenue did each sales channel bring in during calendar year 2025?
model calls: 1
reply: {"tool": "query_metric", "arguments": {"metrics": ["net_revenue"], "group_by": ["order__channel"], "filters": {"metric_time__year": 2025}}}
MetricRequest(metrics=('net_revenue',), group_by=('order__channel',), filters={'metric_time__year': 2025}, order_by=(), limit=None)
SELECT
  orders.channel AS order__channel,
  SUM(orders.net_revenue_eur) AS net_revenue
FROM analytics.fct_orders AS orders
WHERE
  orders.status <> 'cancelled'
  AND CAST(DATE_TRUNC('YEAR', CAST(orders.order_date_local AS DATE)) AS DATE) = CAST('2025-01-01' AS DATE)
GROUP BY
  orders.channel
ORDER BY
  order__channel ASC
order__channel  net_revenue
(none)          82,922.75
app             431,258.70
marketplace     227,826.99
web             909,519.42
matches golden: True
schema-only outcome: error
```

The run took 1 model call. The reply names `net_revenue`, groups by `order__channel` and filters `metric_time__year` to 2025: the question's three parts, each mapped to a name the layer defines. The layer wrote the SQL. It reads `analytics.fct_orders`, leaves out cancelled orders by the metric's own filter, truncates the local business day to its year and groups by channel, and its result matches the golden result: `matches golden: True`. The same question under schema-only SQL ends in `error`.

The request also makes the answer's provenance exact. `answer.provenance` names the metric, the filters and the SQL that ran, so a person who doubts the number checks a short request and the metric's definition, not a query the model wrote. Reviewing a request takes a glance; reviewing a model's SQL takes the same care as reviewing anyone's.

**Working rule:** Have the model return a metric request as structured arguments to a tool, and parse it into a typed request before anything else happens. Keep the reply format simple enough for your own code to parse, and keep that parser in one place. Accept SQL from a model only on a separate, guarded path, for questions no metric covers.

## Validate the request against the layer {#validate-the-request}

A [parsed request](#request-not-sql) is well-formed, which isn't the same as right. Some mistakes fail loudly: the compiler from [chapter 5](#semantic-layer) refuses a metric it doesn't define, and a dimension that would [fan out](#join-through-entities). Others compile and run. A filter value that no row holds, such as a region called `Europe`, returns an empty total. A month written against a dimension that holds days matches one day. Both results look like answers. Validating a request means checking it against the layer's definitions and the warehouse's values before it compiles, and sending every problem back to the model with what would be allowed instead.

`validate_request()` in `lib/metric_tools.py` does that for the shop. It checks each metric's name, and suggests the nearest defined names for a misspelt one. It checks each dimension against what the requested metrics can reach, and when one can't, it names the metrics that can. It checks each categorical filter value against the values in the warehouse, each filter on `metric_time` against its grain, so that a month must be the first day of a month, and each filter on a date dimension, which must be a single day. `query_metric` runs it on every request. A request with problems comes back to the model as an error that lists every problem it finds once the metrics are known, so one correction can fix them all. An unknown metric comes back on its own, before anything else is checked.

The example sends three requests a person might write: orders by customer email, which no semantic model defines; net revenue by product category, which would fan out; and net revenue for a region called `Europe`. Then it replays the model's own first request for `gq-002`, runs it without validation to show what would have happened, and follows the run to its answer.

Example `reject-unknown-dimension` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Validate a metric request against the layer and the warehouse before it runs, and show what would run without it."""
from lib.agent import run_agent
from lib.golden import golden_result, load_golden, results_match
from lib.metric_tools import MetricToolbox, catalog, validate_request
from lib.model import RecordedModel
from lib.prompts import metrics_first_prompt
from lib.semantic import MetricRequest
from lib.warehouse import connect

con = connect()
toolbox = MetricToolbox(con)
layer = toolbox.layer
for label, request in [("no such dimension", MetricRequest(("orders",), group_by=("customer__email",))),
                       ("fan-out", MetricRequest(("net_revenue",), group_by=("product__category",))),
                       ("no such value", MetricRequest(("net_revenue",), filters={"order__region": "Europe"}))]:
    print(f"{label}: {validate_request(layer, con, request)[0]}")
print(f"unchecked, region Europe: {layer.query(con, request).rows}")

# The model's own requests for gq-002, net revenue in each region in March 2026, replayed from the recording.
question = next(q for q in load_golden() if q.question_id == "gq-002")
system = metrics_first_prompt(catalog(layer))
trace = run_agent(question.question, system, RecordedModel("metric-agent-runs"), toolbox, max_steps=4)
first, second = (MetricRequest.from_arguments(s.arguments) for s in trace.steps if s.tool == "query_metric")
golden = golden_result(con, question)
unchecked = layer.query(con, first)                # what would have run without validation
print(f"first request filters: {first.filters}")
print(f"unchecked total: {sum(row[1] for row in unchecked.rows):,.2f}")
print(f"golden total: {sum(row[1] for row in golden):,.2f}")
print(f"unchecked matches golden: {results_match(unchecked.rows, golden)}")
print(f"validation said: {trace.steps[1].content}")
print(f"second request filters: {second.filters}")
print(f"matches golden: {results_match(trace.answer.rows, golden)}")
```

Output:

```text
no such dimension: orders can't use dimension 'customer__email'; no metric defines it
fan-out: net_revenue can't use dimension 'product__category'; metrics that can use it: line_net_revenue, units_sold
no such value: no row has order__region = 'Europe'; its values: AMER, APAC, EMEA
unchecked, region Europe: ((None,),)
first request filters: {'order__order_date': '2026-03'}
unchecked total: 4,150.82
golden total: 150,082.83
unchecked matches golden: False
validation said: error: request rejected: order__order_date = '2026-03': a date dimension matches single days only; for a period, filter metric_time at its grain, as metric_time__month = "2026-03" or metric_time__year = 2025
second request filters: {'metric_time__month': '2026-03'}
matches golden: True
```

Each of the three requests is refused with a message that says what to do instead: no metric defines a customer's email, two other metrics can reach product category, and the regions are `AMER`, `APAC` and `EMEA`. Without the check, the request for `Europe` runs and returns one row with an empty total, which an agent would report as no revenue.

The model's own request is the case that matters, because no person wrote it. For March 2026 it filtered `order__order_date`, the orders' daily date dimension, to `"2026-03"`. The compiler reads a month written against a daily dimension as the month's first day, so the unchecked request returns March 1 alone: 4,150.82 euros across the three regions, against a golden total of 150,082.83, and `unchecked matches golden: False`. Nothing in that answer says it covers one day. Validation refused the filter and named the dimension to use, `metric_time__month`. The model's second request used it, and its answer matches: `matches golden: True`.

The model made the same mistake often. Across the dev split, validation refused 10 requests, and 6 runs went on to a correct answer after a refusal. Most of those refusals were the date filter. The prompt says a month is written as `"2026-03"` and lists `metric_time__month` among the grains, though it never shows the two together. The model reached for `order__order_date` anyway, probably because the catalog lists it beside the region. A check in code catches that mistake every time; a sentence in a prompt catches it only when the model follows the sentence.

**Working rule:** Validate every request before it compiles: names against the layer, categorical values against the warehouse, dates against their grain. Refuse with a message that names the allowed alternatives, and send it back to the model, which can usually correct itself in one call. Treat any request that would compile into an empty or partial result as invalid, not as an answer of zero.

## Ask back when a question is ambiguous {#ask-back-when-ambiguous}

[Validation](#validate-the-request) catches requests the layer can't serve. It can't catch a valid request for the wrong thing. "Which region is doing best?" maps to a valid request for net revenue by region, and equally to one for orders or refund rate by region, and each can name a different region. When a question fits several metrics and the choice changes the answer, the right reply is a question back to the person, with the choices spelt out. The shop's golden set marks such questions as declines of type `ambiguous`, and [chapter 3](#cover-declines-and-roles) scores any reply to them that doesn't return a result as correct.

The `ask_back` tool ends the run with a question to the person and the options the model offers. An option that names a metric is shown with the layer's description of it, so the person chooses between definitions, not between words: revenue becomes revenue in euros after discounts and before tax, from orders that weren't cancelled. The answer carries `ask_back` as its source in the provenance, so a score can count clarifications apart from declines.

The dev split has four questions of kind `decline`, whose right answer is a question back or a reason: two ambiguous, `gq-019` ("Who are our best customers?") and `gq-020` ("Which region is doing best?"), and two unanswerable, a forecast and the cost of shipping. The example replays all four and prints the tool each run ended with, then the questions the agent asked for `gq-019` and `gq-005` and the answer it gave for `gq-020`. Last, it tries a check the recorded runs didn't have, which the end of this section describes.

Example `clarify-best-customers` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Ask back when a question could mean several metrics: the layer supplies each option's definition to the person."""
from lib.agent import run_agent
from lib.golden import load_golden
from lib.metric_tools import MetricToolbox, catalog, unbounded_ranking
from lib.model import RecordedModel
from lib.prompts import metrics_first_prompt
from lib.semantic import MetricRequest
from lib.warehouse import connect

con = connect()
toolbox = MetricToolbox(con)
system = metrics_first_prompt(catalog(toolbox.layer))
model = RecordedModel("metric-agent-runs")
traces = {q.question_id: run_agent(q.question, system, model, MetricToolbox(con, toolbox.layer, role=q.role),
                                   max_steps=4) for q in load_golden()}
for q in load_golden():
    if q.split == "dev" and q.kind == "decline":
        last = next(s for s in reversed(traces[q.question_id].steps) if s.kind == "model")
        print(f"{q.question_id} ({q.decline_type}): {last.tool}")
        print(f"  {q.question}")

print("gq-019 asks back:")
print(traces["gq-019"].answer.reason)
print("gq-005 asks back:")
print(traces["gq-005"].answer.reason)
answered = next(s for s in reversed(traces["gq-020"].steps) if s.tool == "query_metric")
print(f"gq-020 request: {answered.arguments}")
print(traces["gq-020"].answer.show())

# A check the recorded runs didn't have: refuse a request that ranks its result over no period.
# Applied here to the last request of every run, dev and test, that returned a result.
final = {question_id: MetricRequest.from_arguments(next(s for s in reversed(t.steps) if s.tool == "query_metric")
                                                   .arguments)
         for question_id, t in traces.items() if t.answer.answered}
flagged = [question_id for question_id, request in final.items() if unbounded_ranking(request)]
print(f"runs with a result: {len(final)}")
print(f"requests that order their result: {sum(bool(r.order_by) for r in final.values())}")
print(f"ranking check flags: {', '.join(flagged) or 'none'}")
print(f"ranking check on gq-020: {unbounded_ranking(final['gq-020'])}")
```

Output:

```text
gq-005 (unanswerable): ask_back
  What will our net revenue be next quarter?
gq-019 (ambiguous): ask_back
  Who are our best customers?
gq-020 (ambiguous): query_metric
  Which region is doing best?
gq-021 (unanswerable): cannot_answer
  How much did shipping cost us in fiscal year 2026?
gq-019 asks back:
Do you mean customers by highest net revenue, or by highest number of orders?
- net_revenue: Revenue in EUR after discounts and before tax, from real orders that weren't cancelled, counted on the order's local business day. Returned orders count; refunds are not subtracted.
- orders: The number of real orders, cancelled ones included.
gq-005 asks back:
Do you mean net revenue for the next calendar quarter or the next fiscal quarter?
- calendar quarter
- fiscal quarter
gq-020 request: {'metrics': ['net_revenue'], 'group_by': ['customer__region'], 'order_by': ['net_revenue']}
customer__region  net_revenue
APAC              925,657.84
AMER              1,174,510.02
EMEA              1,690,339.73
runs with a result: 31
requests that order their result: 1
ranking check flags: gq-020
ranking check on gq-020: the request ranks its result but names no period; filter or group by a metric_time grain
```

For `gq-019`, the agent asked whether best means the highest net revenue or the most orders, and the layer added each metric's definition. That is the behaviour the tool exists for, and it scores as correct. Read the options against the layer, though. No semantic model has a dimension that identifies a customer, so neither choice leads to a request the layer can serve. The honest reply was a decline: the shop's metrics don't rank customers.

For `gq-020`, the agent didn't ask. It requested net revenue by `customer__region` with no period, and returned all-time revenue for each region, smallest first. Every name in the request is valid, so validation passed it, and the score counts it as wrong. For the forecast, `gq-005`, the agent asked whether "next quarter" meant the calendar or the fiscal quarter, a question whose answer wouldn't help, since no metric forecasts. It scores as correct because it returned no number, and only the trace shows that the reason was wrong. The shipping question, `gq-021`, was declined with the right reason.

So the tool works when the model calls it, and the model's choice of when to call it is unreliable. A check in code catches `gq-020`'s case: refuse a request that ranks its result but names no period. `unbounded_ranking()` in `lib/metric_tools.py` is that check, and the example applies it to the last request of every recorded run, dev and test, that returned a result. Of those 31, it flags gq-020. That shows it catches this case, not that it never misfires, because only 1 of those requests orders its result at all. `query_metric` doesn't run the check yet: the recordings were made without it, so adding it means recording again.

`gq-019`'s case needs a check we haven't built: refuse an `ask_back` whose metric options can't group by what the question asks about. It would need to know what the question asks about, a customer here, and nothing in the toolbox knows that. It wouldn't cover `gq-005` either, whose options are periods, not metrics. Both checks are rules about the shop's questions, and they belong in code, where a test can hold them, rather than in more prompt text.

**Working rule:** Give the agent a tool to ask back, with options that name the layer's metrics, and show the person each option's definition. Ask back only when every option leads to a request the layer can answer; when none does, decline instead. Read clarifications in traces as you read declines, because a score counts a useless question as correct.

## Measure metrics-first on the golden questions {#measure-metrics-first}

The examples so far followed [single runs](#validate-the-request). The measurement that counts is the one [chapter 3](#hold-out-a-test-split) set up: every golden question, scored by `grade()` with `results_match()`, tuned on the dev split and checked once on the held-out test split, beside the schema-only baseline. The metrics-first prompt and tools were adjusted on dev only. We recorded the dev split three times while tuning, and two changes came from those runs. The catalog in the prompt stopped printing each metric's type beside its name, because the model copied the type into its requests; `describe_metric` still prints it. And a year written as text, such as `"2025"`, became the number it can only mean. Only the final dev recording is kept, and the recording's manifest says the two earlier ones were discarded. The dev numbers below were measured on the split the changes were chosen on, so they're optimistic. The test split was recorded once, after those changes, and nothing changed afterwards.

Each run gets at most four model calls. A run that uses all four without an answer is a failure, and `grade()` scores it as `step limit`, apart from the declines the model chose. The example replays every run and counts outcomes per split, for metrics-first and for schema-only SQL. Then it counts what the tools did: model calls, refused requests, runs that reached a correct answer after a refusal, and clarifications by kind of question.

Example `metrics-first-score` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Score metrics-first against the schema-only baseline on both splits: dev for tuning, test once for the final number."""
from collections import Counter, defaultdict

from lib.agent import run_agent
from lib.golden import golden_result, grade, load_golden, schema_only_outcome
from lib.metric_tools import MetricToolbox, catalog
from lib.model import RecordedModel
from lib.prompts import metrics_first_prompt
from lib.semantic import load
from lib.warehouse import connect, describe_schema

con, layer = connect(), load()
schema, system = describe_schema(con), metrics_first_prompt(catalog(layer))
agent_model, sql_model = RecordedModel("metric-agent-runs"), RecordedModel("schema-only-sql")
counts, facts, missed = defaultdict(Counter), defaultdict(Counter), defaultdict(list)
for q in load_golden():
    toolbox = MetricToolbox(con, layer, role=q.role)
    trace = run_agent(q.question, system, agent_model, toolbox, max_steps=4)
    outcome = grade(q, trace.answer, golden_result(con, q))
    counts[q.split, "metrics-first"][outcome] += 1
    counts[q.split, "schema-only"][schema_only_outcome(con, sql_model, schema, q)] += 1
    facts[q.split][f"{q.kind} questions"] += 1
    facts[q.split][f"{q.kind} correct"] += outcome == "correct"
    facts[q.split]["forbidden answered"] += q.kind == "forbidden" and trace.answer.answered
    facts[q.split]["model calls"] += sum(step.kind == "model" for step in trace.steps)
    facts[q.split]["requests rejected"] += len(toolbox.rejected)
    facts[q.split]["correct after a rejection"] += bool(toolbox.rejected) and outcome == "correct"
    facts[q.split][f"asked back, {q.kind}"] += trace.answer.provenance.source == "ask_back"
    if outcome != "correct":
        missed[q.split].append(f"{q.question_id} {q.kind} {outcome}")

for split in ("dev", "test"):
    for approach in ("schema-only", "metrics-first"):     # only an agent run can hit the step limit
        for outcome in ("correct", "wrong", "error", "declined") + (("step limit",) if approach != "schema-only" else ()):
            print(f"{split} {approach} {outcome}: {counts[split, approach][outcome]} of 24")
    for kind in ("answer", "decline", "forbidden"):
        print(f"{split} metrics-first {kind} correct: {facts[split][kind + ' correct']} of {facts[split][kind + ' questions']}")
    for fact in ("forbidden answered", "model calls", "requests rejected", "correct after a rejection",
                 "asked back, answer", "asked back, decline", "asked back, forbidden"):
        print(f"{split} {fact}: {facts[split][fact]}")
    print(f"{split} not correct: {', '.join(missed[split])}")
```

Output:

```text
dev schema-only correct: 2 of 24
dev schema-only wrong: 14 of 24
dev schema-only error: 8 of 24
dev schema-only declined: 0 of 24
dev metrics-first correct: 16 of 24
dev metrics-first wrong: 7 of 24
dev metrics-first error: 0 of 24
dev metrics-first declined: 0 of 24
dev metrics-first step limit: 1 of 24
dev metrics-first answer correct: 12 of 17
dev metrics-first decline correct: 3 of 4
dev metrics-first forbidden correct: 1 of 3
dev forbidden answered: 2
dev model calls: 43
dev requests rejected: 10
dev correct after a rejection: 6
dev asked back, answer: 0
dev asked back, decline: 2
dev asked back, forbidden: 0
dev not correct: gq-007 answer step limit, gq-012 answer wrong, gq-016 answer wrong, gq-017 answer wrong, gq-018 answer wrong, gq-020 decline wrong, gq-023 forbidden wrong, gq-024 forbidden wrong
test schema-only correct: 3 of 24
test schema-only wrong: 13 of 24
test schema-only error: 8 of 24
test schema-only declined: 0 of 24
test metrics-first correct: 10 of 24
test metrics-first wrong: 7 of 24
test metrics-first error: 0 of 24
test metrics-first declined: 6 of 24
test metrics-first step limit: 1 of 24
test metrics-first answer correct: 5 of 17
test metrics-first decline correct: 4 of 4
test metrics-first forbidden correct: 1 of 3
test forbidden answered: 2
test model calls: 36
test requests rejected: 6
test correct after a rejection: 0
test asked back, answer: 1
test asked back, decline: 2
test asked back, forbidden: 0
test not correct: gq-028 answer wrong, gq-031 answer wrong, gq-032 answer declined, gq-033 answer declined, gq-034 answer declined, gq-035 answer wrong, gq-036 answer declined, gq-037 answer declined, gq-038 answer wrong, gq-039 answer step limit, gq-040 answer wrong, gq-041 answer declined, gq-046 forbidden wrong, gq-048 forbidden wrong
```

On the dev split, metrics-first gets 16 of 24 questions right, against schema-only SQL's 2 of 24. On the held-out test split, the numbers are 10 of 24 and 3 of 24. No metrics-first run ended in an error, because the model never wrote SQL that could fail to run. That isn't the same as never failing: the step limit ended 1 of 24 dev runs and 1 of 24 test runs, `gq-007` and `gq-039`, which used all their calls without an answer. The runs took 43 model calls for the 24 dev questions. The calls beyond the first in a run went to describing a metric before querying it, and to corrections after a refusal.

The test split is the number to report, and it is much lower than dev. Metrics-first gets 5 of 17 answerable test questions right, against 12 of 17 on dev, and the difference is mostly questions it gave no answer to. Metrics-first declined 6 of 24 test questions, all of which the warehouse can answer, and every one is a gap in the layer. Gross margin, the share of sessions that led to an order, return on marketing spend, discounts given, customers who signed up twice, and one order's refund and its reason all need definitions the layer doesn't hold. The model declined the first five with a reason that names what's missing, which is a metric to write. It didn't decline the last one, `gq-036`: after a refused request it asked whether the person meant an order ID or a date range, the one clarification on an answerable test question (`test asked back, answer: 1`). That question back offers nothing the layer can serve, so a decline was due. [Chapter 3](#cover-declines-and-roles) found that marketing and support ask answerable questions only in the test split, and the shop's layer was written around the questions finance and the analyst ask, so nothing tuned on dev could reveal those gaps. The test questions whose right answer is a decline were all declined or asked back: 4 of 4.

This is one model, one sampled reply per call and one synthetic warehouse, so the numbers describe the shop and this setup, not text-to-SQL in general. On a split of 24, one question is about four points of accuracy, and a difference of one or two questions is noise. The gap between the two approaches here is far larger than that.

**Working rule:** Score metrics-first beside your baseline on the same golden questions, and tune on dev only. Say how many times you recorded the dev split while tuning, and record the test split once, after. Report correct, wrong, error, declined and runs ended by the step limit separately, and count clarifications and refused requests too, because they show where the calls go.

## Read the runs that weren't correct {#read-the-misses}

[The score](#measure-metrics-first) says how many runs failed, but not why. The why is in the traces, and it decides what to fix: a metric, a description, a check or an access rule. The example replays every run that wasn't correct and prints each call, the tool and arguments the model sent and the first line of what came back. It also prints the request for `gq-008`, a correct run that the dev wrong answers are set beside, and it asks the layer for the request `gq-039`'s run was reaching for.

Example `metrics-first-misses` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Read every metrics-first run that wasn't correct, call by call, and ask the layer what gq-039's run was reaching for."""
import json

from lib.agent import run_agent
from lib.golden import golden_result, grade, load_golden, results_match
from lib.metric_tools import MetricToolbox, catalog
from lib.model import RecordedModel
from lib.prompts import metrics_first_prompt
from lib.semantic import MetricRequest, load
from lib.warehouse import connect

con, layer = connect(), load()
system, model, golden = metrics_first_prompt(catalog(layer)), RecordedModel("metric-agent-runs"), load_golden()
for q in golden:
    trace = run_agent(q.question, system, model, MetricToolbox(con, layer, role=q.role), max_steps=4)
    outcome, answer = grade(q, trace.answer, golden_result(con, q)), trace.answer
    calls = list(zip(trace.steps[::2], trace.steps[1::2]))      # each model reply, then what its tool returned
    if q.question_id == "gq-008":                               # correct, and gq-012's words without the regions
        print(f"gq-008 ({outcome}) request: {json.dumps(calls[-1][0].arguments)}")
    if outcome == "correct":
        continue
    print(f"{q.question_id} ({q.split}, {q.kind}, {outcome}): {q.question}")
    print(f"{q.question_id} model calls: {len(calls)}")
    for number, (reply, result) in enumerate(calls, start=1):
        sent = f"{reply.tool} {json.dumps(reply.arguments)}" if reply.tool else reply.content
        got = result.content.splitlines()[0][:150]
        ended = {"metric": f"{len(answer.rows)} row" + "s" * (len(answer.rows) != 1), "none": "declined",
                 "ask_back": "asked back"}
        if number == len(calls) and answer.provenance.source in ended:
            got = ended[answer.provenance.source]
        print(f"  {number}. {sent} -> {got}")
    if answer.answered:
        print(f"{q.question_id} rows: {len(answer.rows)}")

# gq-039 is answerable from the layer: the request its run was reaching for, with the order written as "-name".
gq039 = next(q for q in golden if q.question_id == "gq-039")
request = MetricRequest(("line_net_revenue",), group_by=("product__product_name",),
                        filters={"metric_time__year": 2025}, order_by=("-line_net_revenue",), limit=5)
print(f"gq-039 from the layer: {request}")
print(f"gq-039 from the layer, matches golden: "
      f"{results_match(layer.query(con, request).rows, golden_result(con, gq039), gq039.order_matters)}")
```

Output:

```text
gq-007 (dev, answer, step limit): How much net revenue came from orders that included a tent in 2025?
gq-007 model calls: 4
  1. query_metric {"metrics": ["net_revenue"], "group_by": ["product__product_name"], "filters": {"product__product_name": "tent", "metric_time__year": 2025}} -> error: request rejected: net_revenue can't use dimension 'product__product_name'; metrics that can use it: line_net_revenue, units_sold
  2. query_metric {"metrics": ["line_net_revenue"], "group_by": [], "filters": {"product__product_name": "tent", "metric_time__year": 2025}} -> error: request rejected: no row has product__product_name = 'tent'; its values: 120 values
  3. describe_metric "product__product_name" -> error: arguments must be a JSON object
  4. describe_metric "product__product_name" -> error: arguments must be a JSON object
gq-008 (correct) request: {"metrics": ["net_revenue"], "group_by": [], "filters": {"metric_time__year": "2025"}, "order_by": []}
gq-012 (dev, answer, wrong): What was total revenue for each sales region in 2025?
gq-012 model calls: 2
  1. query_metric {"metrics": ["gross_revenue"], "group_by": ["order__region"], "filters": {"order__order_date": "2025"}} -> error: request rejected: order__order_date = '2025': a date dimension matches single days only; for a period, filter metric_time at its grain, as metr
  2. query_metric {"metrics": ["gross_revenue"], "group_by": ["order__region"], "filters": {"metric_time__year": 2025}} -> 3 rows
gq-012 rows: 3
gq-016 (dev, answer, wrong): How many customers placed at least one order in 2025?
gq-016 model calls: 2
  1. describe_metric {"metric": "new_customers"} -> new_customers, a simple metric: Customers whose first order fell in the period.
  2. query_metric {"metrics": ["new_customers"], "group_by": [], "filters": {"metric_time__year": "2025"}, "order_by": [], "limit": null} -> 1 row
gq-016 rows: 1
gq-017 (dev, answer, wrong): What was net revenue in each of our countries in 2025?
gq-017 model calls: 1
  1. query_metric {"metrics": ["net_revenue"], "group_by": ["order__country"], "filters": {"metric_time__year": 2025}} -> 10 rows
gq-017 rows: 10
gq-018 (dev, answer, wrong): How much was refunded, in euros, on orders placed in March 2026?
gq-018 model calls: 2
  1. describe_metric {"metric": "refunds"} -> refunds, a simple metric: Refunded EUR, counted on the local day the refund was made.
  2. query_metric {"metrics": ["refunds"], "group_by": ["metric_time__month"], "filters": {"metric_time__month": "2026-03"}} -> 1 row
gq-018 rows: 1
gq-020 (dev, decline, wrong): Which region is doing best?
gq-020 model calls: 2
  1. describe_metric {"metric": "net_revenue"} -> net_revenue, a simple metric: Revenue in EUR after discounts and before tax, from real orders that weren't cancelled, counted on the order's local bus
  2. query_metric {"metrics": ["net_revenue"], "group_by": ["customer__region"], "order_by": ["net_revenue"]} -> 3 rows
gq-020 rows: 3
gq-023 (dev, forbidden, wrong): What were the most common reasons for refunds in 2025?
gq-023 model calls: 2
  1. describe_metric {"metric": "refunds"} -> refunds, a simple metric: Refunded EUR, counted on the local day the refund was made.
  2. query_metric {"metrics": ["refunds"], "group_by": ["refund__reason"], "filters": {"metric_time__year": 2025}} -> 5 rows
gq-023 rows: 5
gq-024 (dev, forbidden, wrong): What was net revenue in EMEA in March 2026?
gq-024 model calls: 2
  1. query_metric {"metrics": ["net_revenue"], "group_by": ["order__region"], "filters": {"order__region": "EMEA", "order__order_date": "2026-03"}} -> error: request rejected: order__order_date = '2026-03': a date dimension matches single days only; for a period, filter metric_time at its grain, as m
  2. query_metric {"metrics": ["net_revenue"], "group_by": ["order__region"], "filters": {"order__region": "EMEA", "metric_time__month": "2026-03"}} -> 1 row
gq-024 rows: 1
gq-028 (test, answer, wrong): Which country had the highest refund rate in fiscal year 2026?
gq-028 model calls: 2
  1. describe_metric {"metric": "refund_rate"} -> refund_rate, a ratio metric: Refunded EUR over gross revenue of the same orders: orders placed in the period that weren't cancelled.
  2. query_metric {"metrics": ["refund_rate"], "group_by": ["order__country"], "filters": {"metric_time__fiscal_year": 2026}} -> 10 rows
gq-028 rows: 10
gq-031 (test, answer, wrong): How many units did an order contain on average in 2025, counting quantities, not order lines?
gq-031 model calls: 2
  1. describe_metric {"metric": "units_sold"} -> units_sold, a simple metric: Units sold on orders that weren't cancelled.
  2. query_metric {"metrics": ["units_sold"], "group_by": [], "filters": {"metric_time__year": "2025"}, "order_by": []} -> 1 row
gq-031 rows: 1
gq-032 (test, answer, declined): What was our gross margin in euros on products sold in 2025?
gq-032 model calls: 2
  1. describe_metric {"metric": "refund_rate"} -> refund_rate, a ratio metric: Refunded EUR over gross revenue of the same orders: orders placed in the period that weren't cancelled.
  2. cannot_answer {"reason": "The requested gross margin cannot be computed as gross margin is not a directly available metric. Gross margin is derived from gross revenue and net revenue, which are not provided as a single metric. Refund_rate is available but does not represent gross margin."} -> declined
gq-033 (test, answer, declined): What share of sessions in each channel led to an order in 2025?
gq-033 model calls: 1
  1. cannot_answer {"reason": "The metrics available do not include session data or a measure of sessions per channel. Therefore, it is not possible to determine the share of sessions in each channel that led to an order."} -> declined
gq-034 (test, answer, declined): What was the return on marketing spend for paid search in 2025?
gq-034 model calls: 1
  1. cannot_answer {"reason": "The data does not include metrics related to marketing spend or return on marketing spend (ROMS), so it is not possible to calculate the return on marketing spend for paid search in 2025."} -> declined
gq-035 (test, answer, wrong): How many orders did we get in each country in March 2026?
gq-035 model calls: 2
  1. query_metric {"metrics": ["orders"], "group_by": ["order__country"], "filters": {"order__order_date": "2026-03"}} -> error: request rejected: order__order_date = '2026-03': a date dimension matches single days only; for a period, filter metric_time at its grain, as m
  2. query_metric {"metrics": ["orders"], "group_by": ["order__country"], "filters": {"metric_time__month": "2026-03"}} -> 10 rows
gq-035 rows: 10
gq-036 (test, answer, declined): How much was refunded on order 113432, in euros, and why?
gq-036 model calls: 2
  1. query_metric {"metrics": ["refunds"], "filters": {"order__order_date": "113432"}, "group_by": ["refund__reason"]} -> error: request rejected: order__order_date = '113432': a date dimension matches single days only; for a period, filter metric_time at its grain, as me
  2. ask_back {"question": "Do you mean the refund amount for a specific order (by order ID) or for a specific date range?", "options": ["order ID 113432", "a date range"]} -> asked back
gq-037 (test, answer, declined): How many customers signed up twice with the same email address?
gq-037 model calls: 1
  1. cannot_answer {"reason": "The available metrics do not track customer sign-ups or email address uniqueness, so it's not possible to determine how many customers signed up twice with the same email address."} -> declined
gq-038 (test, answer, wrong): What were net revenue and the number of orders on each day of the week in 2025?
gq-038 model calls: 1
  1. query_metric {"metrics": ["net_revenue", "orders"], "group_by": ["order__order_date"], "filters": {"order__order_date": "2025-01-01"}, "order_by": []} -> 1 row
gq-038 rows: 1
gq-039 (test, answer, step limit): Which five products brought in the most net revenue in 2025, from the highest down?
gq-039 model calls: 4
  1. query_metric {"metrics": ["net_revenue"], "group_by": ["product__product_name"], "filters": {"order__order_date": "2025"}, "order_by": ["net_revenue", "-"], "limit": 5} -> error: request rejected: net_revenue can't use dimension 'product__product_name'; metrics that can use it: line_net_revenue, units_sold; order__order_
  2. query_metric {"metrics": ["line_net_revenue"], "group_by": ["product__product_name"], "filters": {"metric_time__year": 2025}, "order_by": ["line_net_revenue", "-"], "limit": 5} -> error: request rejected: can't order by '': it isn't a requested metric or group-by
  3. query_metric {"metrics": ["line_net_revenue"], "group_by": ["product__product_name"], "filters": {"metric_time__year": 2025}, "order_by": ["line_net_revenue", "-"], "limit": 5} -> error: request rejected: can't order by '': it isn't a requested metric or group-by
  4. describe_metric "line_net_revenue" -> error: arguments must be a JSON object
gq-040 (test, answer, wrong): What was revenue in each region in 2024 and in 2025?
gq-040 model calls: 2
  1. describe_metric {"metric": "net_revenue"} -> net_revenue, a simple metric: Revenue in EUR after discounts and before tax, from real orders that weren't cancelled, counted on the order's local bus
  2. query_metric {"metrics": ["net_revenue"], "group_by": ["customer__region"], "filters": {"metric_time__year": ["2024", "2025"]}} -> 3 rows
gq-040 rows: 3
gq-041 (test, answer, declined): How much discount did we give, in euros, in fiscal year 2026?
gq-041 model calls: 1
  1. cannot_answer {"reason": "The provided metrics do not include a metric for discount amounts. While net_revenue and gross_revenue are available, they represent revenue after discounts and before tax, but there is no specific metric to measure the total discount given in euros."} -> declined
gq-046 (test, forbidden, wrong): What was net revenue in APAC in June 2026?
gq-046 model calls: 2
  1. query_metric {"metrics": ["net_revenue"], "group_by": ["order__region"], "filters": {"order__region": "APAC", "order__order_date": "2026-06"}} -> error: request rejected: order__order_date = '2026-06': a date dimension matches single days only; for a period, filter metric_time at its grain, as m
  2. query_metric {"metrics": ["net_revenue"], "group_by": ["order__region"], "filters": {"order__region": "APAC", "metric_time__month": "2026-06"}} -> 1 row
gq-046 rows: 1
gq-048 (test, forbidden, wrong): How many orders did customers in AMER place in 2025?
gq-048 model calls: 1
  1. query_metric {"metrics": ["orders"], "group_by": ["customer__region"], "filters": {"customer__region": "AMER", "metric_time__year": 2025}} -> 1 row
gq-048 rows: 1
gq-039 from the layer: MetricRequest(metrics=('line_net_revenue',), group_by=('product__product_name',), filters={'metric_time__year': 2025}, order_by=('-line_net_revenue',), limit=5)
gq-039 from the layer, matches golden: True
```

The test run that hit the step limit wasn't a gap in the layer. `gq-039` asks for the five products with the most net revenue in 2025, from the highest down, and the layer can answer it: `line_net_revenue` grouped by product name, ordered by `["-line_net_revenue"]` and limited to five, matches the golden result (`matches golden: True`). The model kept writing the order as `["line_net_revenue", "-"]`, validation refused it each time, and the run ran out of calls.

The test split's wrong answers are the same kinds as dev's. Asked for the country with the highest refund rate, the agent returned every country's rate; asked for revenue in 2024 and in 2025, one total for both years; asked for the average number of units per order, the total number of units; and asked for each day of the week in 2025, it grouped by order date and filtered to January 1, 2025, one day. Each of those requests was valid, and each answered a different question. The last wrong answer, `gq-035`, came from AMER's regional lead, who asked for orders in each country and got all 10 countries, the same problem with roles as dev's `gq-017`.

The questions it gets wrong on dev fall into four groups, and each points at other work. It picks a near-miss metric: `gq-012` asks for "total revenue" by region and gets `gross_revenue`, where the finance team means net, while `gq-008`, the same words without regions, got net revenue; and `gq-018` asks for refunds on March's orders and gets `refunds`, counted on the day of the refund, instead of `order_refunds`. It answers a question the layer has no metric for with the closest one: `gq-016` asks how many customers placed an order in 2025 and gets the count of new customers. It can't see who is asking: `gq-017`, from EMEA's regional lead, asks about "our countries" and gets all 10, and 2 forbidden questions are answered because nothing below the model stops them, which is [chapter 9](#who-may-see-what)'s work. And it can't answer what only SQL can: `gq-007`, revenue from orders that included a tent, needs a filter on the order lines that no metric offers. It spent its 4 calls on a tent filter, refused first because net revenue can't filter by product and then because no product is named `tent`, and on describe calls whose arguments weren't a JSON object, and then hit the step limit. [Chapter 7](#guarded-sql) gives such questions a guarded SQL path.

**Working rule:** Read every run that wasn't correct, call by call, and sort it by what it needs: a near-miss metric means the descriptions need sharpening or the question needs asking back, a missing metric means the layer needs one or the question needs guarded SQL, and an answer that depends on the role means access rules, not prompts.

## What goes wrong in production {#metrics-first-in-production}

The shop's agent answers about half of its golden questions from metrics, and fewer on the held-out test split. An agent over a real semantic layer fails in these ways, and each has a way to notice.

**Two metrics fit the words, and the agent picks the other one.** In [the runs that weren't correct](#read-the-misses), "total revenue" went to net revenue for `gq-008` and to gross revenue for `gq-012`, and refunds on March's orders went to the refund day instead of the order day. A layer with near-duplicates invites this. Databricks' release notes record its dashboard-authoring agent, Genie Code, becoming "more likely to reference existing Unity Catalog metric views instead of creating new ones" when importing Tableau and Power BI reports, on Jul 2, 2026, and, on Sep 10, 2026, preferring governed metric views over ad-hoc SQL datasets when it builds a dashboard ([Databricks](https://docs.databricks.com/aws/en/ai-bi/release-notes/2026)). Those are a vendor's statements about building dashboards, not about answering questions, but they address the same problem: definitions that multiply. Keep one metric per business term where you can, write descriptions that say when not to use a metric, and keep golden questions for each pair of near-duplicates.

**A metric with a nearby name answers a question it doesn't cover.** New customers aren't customers who ordered. The agent's request is valid, the answer runs, and only a golden question shows it's wrong. Write golden questions for terms the layer doesn't define, and expect the right answer to be a decline.

**Validation messages are part of the prompt.** The model reads every refusal, and its next request follows the wording. Changing a message changes the conversation, and every recording that saw the old message stops replaying. Treat the messages as prompt text: keep them in one module, test them, and record again on purpose when they change.

**Dimension values drift.** Validation reads categorical values from the warehouse when the tool runs. A new country appears the day its first order loads, and a value list cached when the agent was deployed would refuse it. This chapter's prompt has that weakness on a small scale: it names the regions and channels, which spares the model a describe call, and it would go stale the day a region is added. Read values at request time, or refresh a cache with the load that changes them, and build any list the prompt carries from the same source.

**The agent can't see who is asking.** A regional lead's "our countries" needs a filter from the role, and a forbidden question needs a refusal from below the model. Neither belongs in the prompt, where a question can talk the model out of it. Apply row filters and column masks in the compiler, as [chapter 9](#who-may-see-what) does, so no request can reach past them.

**Asking back becomes the answer to everything.** A score counts a clarifying question on a question that should be declined as correct, so the score alone can't tell a useful question back from a useless one. The forecast's question back followed the prompt: `ask_back`'s description in `METRICS_FIRST` invites one when a question "fits several metrics or periods", and "next quarter" fits two periods. `gq-036`'s question back, on a question no metric covers, should have been a decline. Count clarifications on answerable questions as a cost, read them in traces, and write the tool's description to say when not to ask. A check that refuses an `ask_back` whose options the layer can't serve is untested: we haven't built it.

**Corrections cost calls.** Every refusal is another model call, and the loop's limit of four model calls per run ends a run that keeps being refused. In [the runs that weren't correct](#read-the-misses), `gq-007` spent its calls on a tent filter and on malformed describe calls, and `gq-039` spent its calls on an order written the wrong way. Watch the calls per question, and when one kind of refusal dominates, fix its cause in the catalog or the tools rather than raising the limit.

**Working rule:** Before you widen the agent's audience, keep one metric per business term with descriptions that say when not to use it, review validation messages as you review prompts, read dimension values when requests run, enforce roles below the agent, and count clarifications and refusals beside the score. Start with the near-duplicate metrics, because they produce valid requests that return wrong numbers.

## Decisions this chapter made {#metrics-first-decisions}

- **The agent sees metrics, never tables.** Its tools are `list_metrics`, `describe_metric`, `query_metric`, `ask_back` and `cannot_answer`, over the semantic layer from chapter 5, and its prompt carries the catalog of metrics and their dimensions.
- **The model returns a metric request, not SQL,** as a JSON tool call that `run_agent()` parses into a `MetricRequest`. The book keeps its own reply format instead of Qwen's `<tool_call>` tags.
- **Every request is validated before it compiles,** against the layer's names, the warehouse's categorical values and each time grain, and a refused request goes back to the model with the allowed alternatives.
- **A request that would return an empty or partial result is invalid,** such as a period written against a daily date dimension.
- **Asking back is a tool,** whose options carry the layer's definitions, and its answers are counted apart from declines.
- **Metrics-first is measured on both splits** beside the schema-only baseline, tuned on dev, with the test split recorded once after tuning.
- **The catalog goes in the prompt,** and `describe_metric` adds the time grains and each dimension's values, read from the warehouse when the tool runs.
- **A run gets at most four model calls,** which leaves room for a description and a correction or two, and ends a run that keeps being refused. A run that hits the limit is scored as `step limit`, a failure, never as a decline.
- **Questions no metric covers are declined here.** Chapter 7 gives them a guarded SQL path, and chapter 9 applies the roles the agent can't see.
