---
title: "Business Intelligence with Agents"
chapter: "Say when the answer can't be given"
chapter_id: say-when-it-cannot
book: business-intelligence-with-agents
edition: 2026.11.10
verified: 2026-11-13
edition_code: 0Q0N-P15N
canonical: https://rollingedition.com/business-intelligence-with-agents/say-when-it-cannot
license: CC BY 4.0
attribution: "“Say when the answer can't be given,” chapter 8 of Business Intelligence with Agents, Edition 2026.11.10, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/business-intelligence-with-agents/say-when-it-cannot. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Say when the answer can't be given

By the end of this chapter, you can make declining a first-class answer: tell the questions the warehouse can't answer from the ones it can, decline with a reason of a known kind, check that the data for the period asked about has arrived, show the provenance behind every answer, and measure declines with precision and recall, so the agent neither guesses nor refuses too often.

The shop, the online outdoor-gear shop in three regions that this book follows throughout, has an agent that answers from its semantic layer. [Chapter 6](#metrics-first) built it: the model chooses a metric, its dimensions and its filters, and the layer writes the SQL. On the dev split of the golden questions, that agent got most answerable questions right, and two of its failures are this chapter's subject. Asked "Which region is doing best?", it returned every region's all-time revenue, smallest first, a number for a question that has no single answer. Asked for next quarter's net revenue, it asked whether the person meant the calendar or the fiscal quarter, as if either reading could be answered from data that ends on the last day of June 2026.

Both failures look like answers, and a wrong number from a warehouse is worse than none, because it gets pasted into a deck. Research on text-to-SQL makes the same point: unanswerable questions "may generate not only incorrect text but also executable programs that yield misleading results" ([Ren et al.](https://arxiv.org/abs/2601.10398)). This chapter gives the agent ways to say no, and the measurements to tell a good decline from a refusal to work. It builds on chapter 6's metrics-first agent rather than on [chapter 7](#guarded-sql)'s guarded SQL path, so a question no metric covers is still declined here, and the measurements count each such decline as a cost.

## Kinds of questions the warehouse can't answer {#kinds-of-unanswerable}

A question that shouldn't get a single number is one of two kinds, and they need different replies. An ambiguous question has several valid answers: the words fit more than one metric, period or filter, and the right reply is a question back to the person or a stated assumption. An unanswerable question has no valid answer in the warehouse: the data doesn't hold what it needs, or it asks for something SQL can't do, such as a forecast.

The research gives both kinds names you can use. PRACTIQ, a conversational text-to-SQL dataset, sorts them into four ambiguous categories, such as an ambiguous SELECT column, a "Question with multiple valid SQLs that differ in the columns used in the SELECT clause", and four unanswerable ones, such as a nonexistent SELECT column, where "The column that contains the results asked in the question do not exist in the database" ([Dong et al.](https://arxiv.org/abs/2410.11076)). TrustSQL adds the questions that fail "due to schema incompatibility or functionalities beyond SQL" ([Lee et al.](https://arxiv.org/abs/2403.15879)). Knowing the schema doesn't remove the ambiguity: AMBROSIA's authors found that "the ambiguity persists even when the database context is provided" ([Saparina and Lapata](https://arxiv.org/abs/2406.19073)).

The shop's golden questions, from [chapter 3](#cover-declines-and-roles), include eight whose right answer is a decline, four in each split, and each carries a `decline_type`: two ambiguous and two unanswerable per split. The example prints each one with its category in PRACTIQ's terms, or TrustSQL's for the forecast, and searches both schemas for a column whose name matches the words the question needs. Then it answers two ambiguous questions in each of their readings, from the semantic layer. One of the ambiguous questions has no reading to answer: "Who are our best customers?", `gq-019`, is ambiguous in PRACTIQ's terms, but no metric or dimension ranks customers, so its right reply is a decline, not a question back.

Example `unanswerable-cases` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.10:

```python
"""The golden questions whose right answer is a decline: which are ambiguous, which are unanswerable, and why."""
from lib.golden import load_golden
from lib.semantic import MetricRequest, load
from lib.warehouse import connect

con, layer = connect(), load()
# Each decline question's category: PRACTIQ's names, and TrustSQL's for the forecast. Words to look for in the schema.
CATEGORIES = {"gq-005": ("beyond SQL: a forecast", "forecast|predict"), "gq-019": ("ambiguous SELECT column", None),
              "gq-020": ("ambiguous SELECT column", None), "gq-021": ("nonexistent SELECT column", "ship"),
              "gq-042": ("ambiguous filter criteria", None), "gq-043": ("ambiguous values within a column", None),
              "gq-044": ("unsupported join", "view|page"), "gq-045": ("nonexistent WHERE column", "deliver|promise")}
for q in load_golden():
    if q.kind == "decline":
        category, words = CATEGORIES[q.question_id]
        print(f"{q.question_id} ({q.split}, {q.decline_type}): {category}")
        if words:
            found = con.execute("""SELECT string_agg(table_name || '.' || column_name, ', ') FROM information_schema.columns
                                   WHERE table_schema IN ('raw', 'analytics') AND regexp_matches(column_name, ?)""",
                                [words]).fetchall()[0][0]
            print(f"  columns matching {words!r}: {found or 'none'}")

cost = con.execute("""SELECT string_agg(table_name || '.' || column_name, ', ') FROM information_schema.columns
                      WHERE table_schema IN ('raw', 'analytics') AND regexp_matches(column_name, 'cost')""").fetchall()
print(f"columns named for cost: {cost[0][0] or 'none'}")
reasons = [r for (r,) in con.execute("SELECT DISTINCT reason FROM analytics.fct_refunds ORDER BY 1").fetchall()]
print(f"refund reasons: {', '.join(reasons)}")
print(f"last order day: {con.execute('SELECT max(order_date_local) FROM analytics.fct_orders').fetchall()[0][0]}")

# "Which region is doing best?" in fiscal 2026, by three metrics the layer defines.
fiscal_2026 = {"metric_time__fiscal_year": 2026}
for metric, order in (("net_revenue", "-net_revenue"), ("orders", "-orders"), ("refund_rate", "refund_rate")):
    answer = layer.query(con, MetricRequest((metric,), ("order__region",), fiscal_2026, (order,), 1))
    print(f"best region by {order.lstrip('-')}{' (lowest)' if order == metric else ''}: {answer.rows[0][0]}")

# "What was revenue in Q2?" read as a calendar quarter and as a fiscal quarter of the same year.
for name, value in (("metric_time__quarter", "2025-04-01"), ("metric_time__fiscal_quarter", "2026-Q2")):
    (revenue,), = layer.query(con, MetricRequest(("net_revenue",), (), {name: value})).rows
    print(f"net revenue, {name.removeprefix('metric_time__')} {value}: {revenue:,.2f}")
```

Output:

```text
gq-005 (dev, unanswerable): beyond SQL: a forecast
  columns matching 'forecast|predict': none
gq-019 (dev, ambiguous): ambiguous SELECT column
gq-020 (dev, ambiguous): ambiguous SELECT column
gq-021 (dev, unanswerable): nonexistent SELECT column
  columns matching 'ship': none
gq-042 (test, ambiguous): ambiguous filter criteria
gq-043 (test, ambiguous): ambiguous values within a column
gq-044 (test, unanswerable): unsupported join
  columns matching 'view|page': none
gq-045 (test, unanswerable): nonexistent WHERE column
  columns matching 'deliver|promise': none
columns named for cost: dim_products.unit_cost, products.unit_cost
refund reasons: changed_mind, damaged, late_delivery, other, wrong_size
last order day: 2026-06-30
best region by net_revenue: EMEA
best region by orders: EMEA
best region by refund_rate (lowest): APAC
net revenue, quarter 2025-04-01: 415,495.84
net revenue, fiscal_quarter 2026-Q2: 467,081.90
```

No column in `raw` or `analytics` is named for shipping, product views, delivery promises or forecasts, and the last order day is 2026-06-30. So the four unanswerable questions have nothing to compute from, but each has something nearby that a model could reach for. The products table has `unit_cost` (`dim_products.unit_cost, products.unit_cost`), which is the product's cost, not shipping. The refunds table has a reason called `late_delivery`, which counts refunds, not late deliveries. A model that trusts the question's premise will write runnable SQL against those columns: PremiseSQL's authors found that models "are strongly premise-trusting by default and rarely critique flawed premises" ([Lin et al.](https://arxiv.org/abs/2610.22158)).

The ambiguous questions have answers, too many of them. "Which region is doing best?" in fiscal 2026 is EMEA by net revenue and by orders, and APAC by the lowest refund rate. "What was revenue in Q2?" in 2025 is 415,495.84 euros of net revenue for the calendar quarter and 467,081.90 for the fiscal one, which runs from May to July. Each of those numbers is right for one reading and wrong for the others, and nothing in the result says which reading produced it.

A third kind looks unanswerable and isn't: a filter value no row holds, such as a region called `Europe`. PRACTIQ lists it as a nonexistent filter value. In the shop, [chapter 6's validation](#validate-the-request) refuses it and names the regions that exist, so the model can correct its request instead of declining.

**Working rule:** Sort every question your golden set marks as a decline into ambiguous or unanswerable, and name its category, so you know which reply it needs. Ask back on an ambiguous question only when every reading is answerable, and decline an unanswerable one with what's missing. For each unanswerable question, find the column or value nearby that a model could mistake for the answer, because that's the wrong number you're guarding against.

## Decline with a reason {#decline-with-a-reason}

The [two kinds of question](#kinds-of-unanswerable) need a reply that isn't a number, and a reply the code can read. A decline is an answer: it ends the run, it says why, and the person can act on it. The reason has two parts. One is a sentence for the person, naming what's missing. The other is a kind from a fixed list, for the code, so declines can be counted, routed and scored by kind instead of read one at a time. In chapter 6, the forecast's question back about the calendar or the fiscal quarter scored as correct because it returned no number, and only its trace showed that the reason was wrong.

This chapter's agent, which we call the declining agent, lives in `lib/declining.py`, a module this chapter adds. Its `DecliningToolbox` keeps chapter 6's five metric tools and changes what two of them do. `cannot_answer` takes a `kind` as well as a reason, and refuses a kind outside the list. `query_metric` runs two checks in code before it answers: [chapter 6's ranking check](#ask-back-when-ambiguous), which refuses a request that ranks its result over no period, and the freshness check that [the section on freshness](#check-freshness) builds. The prompt, `DECLINING` in `lib/prompts.py`, differs from chapter 6's in three places. It lists the kinds the model may give; it allows `ask_back` only when every option is a request the metrics can answer, chapter 6's working rule; and it states what a wrong number costs, in the form Kalai and colleagues propose: "Answer only if you are >t confident, since mistakes are penalized t/(1-t) points" ([Kalai et al.](https://arxiv.org/abs/2509.04664)), with t at 0.75, so by the formula a wrong number costs 0.75/0.25 = 3 points and a decline 0.

The recording `decline-runs` holds the pinned model's replies to that prompt for the dev split's answer and decline questions, 21 of them. It was made by `recordings/record_decline_runs.py` with the same model file, sampling and seed as every recording in this book, and at most four model calls a run, as in chapter 6. The three forbidden questions on dev aren't recorded, because their decline belongs below the model, in [chapter 9](#who-may-see-what). We chose the prompt's changes by reading chapter 6's dev traces, so the dev split informed them. We recorded the dev split once, after writing the prompt, and changed nothing afterwards. The recording's manifest says so in its `tuning` field, and every replay checks it in part: a reply is found by a hash of the messages that produced it, prompt included, so a changed prompt finds no reply.

The example prints the kinds and who decides each, sends `cannot_answer` a call without a kind, and replays the four dev decline questions and one answerable question the agent declined.

Example `cannot-answer-tool` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.10:

```python
"""Decline with a kind from a fixed list and a reason, so declines can be checked and counted like answers."""
from lib.agent import run_agent
from lib.declining import DECLINE_KINDS, MODEL_KINDS, DecliningToolbox, decline_kind
from lib.golden import load_golden
from lib.metric_tools import catalog
from lib.model import RecordedModel
from lib.prompts import declining_prompt
from lib.warehouse import connect

con = connect()
toolbox = DecliningToolbox(con)
for kind, meaning in DECLINE_KINDS.items():
    print(f"{kind}{' (model)' if kind in MODEL_KINDS else ' (code)'}: {meaning}")
print(toolbox.call("cannot_answer", {"reason": "no shipping costs"}).content)
print(toolbox.call("cannot_answer", {"kind": "not_in_data", "reason": "no shipping costs"}).answer.show())

system, model = declining_prompt(catalog(toolbox.layer)), RecordedModel("decline-runs")
for q in load_golden():
    if q.split == "dev" and q.kind == "decline" or q.question_id == "gq-016":
        trace = run_agent(q.question, system, model, DecliningToolbox(con, toolbox.layer, role=q.role), max_steps=4)
        calls = [step for step in trace.steps if step.kind == "model"]
        print(f"{q.question_id} ({q.decline_type or q.kind}): {q.question}")
        print(f"{q.question_id} ended with: {calls[-1].tool}, kind {decline_kind(trace.answer)}")
        print(f"{q.question_id} model calls: {len(calls)}")
        label = "asks" if trace.answer.provenance.source == "ask_back" else "reason"
        print(f"  {label}: {trace.answer.reason.splitlines()[0]}")
        if q.question_id == "gq-021":
            print(f"  first reply: {calls[0].content}")
        if q.question_id == "gq-020":
            asked = next(i for i, step in enumerate(trace.steps) if step.tool == "query_metric")
            request = trace.steps[asked].arguments
            print(f"gq-020 request: {', '.join(request['metrics'])} by {', '.join(request['group_by'])}, ordered by "
                  f"{', '.join(request['order_by'])}, period: {request.get('filters') or 'none'}")
            print(f"gq-020 check: {trace.steps[asked + 1].content}")
            print(f"gq-020 options: {', '.join(trace.steps[-2].arguments['options'])}")
```

Output:

```text
not_in_data (model): no metric or dimension holds what the question needs
forecast (model): the question asks about a period that hasn't happened, or for a prediction
no_definition (model): the question uses a term the shop hasn't defined, and no metric settles it
stale (code): the data for the period hasn't all arrived: not loaded yet, or not happened yet
forbidden (code): the role asking may not see the answer (chapter 9)
error: kind must be one of not_in_data, forecast, no_definition; got ''
cannot answer: not_in_data: no shipping costs
gq-005 (unanswerable): What will our net revenue be next quarter?
gq-005 ended with: cannot_answer, kind forecast
gq-005 model calls: 1
  reason: forecast: The question asks about a future period that hasn't happened yet, and no data is available for forecasting.
gq-016 (answer): How many customers placed at least one order in 2025?
gq-016 ended with: cannot_answer, kind not_in_data
gq-016 model calls: 2
  reason: not_in_data: The metric 'new_customers' cannot use 'order__order_date' as a filter, and no alternative metric or dimension is available to answer the question about customers placing at least one order in 2025.
gq-019 (ambiguous): Who are our best customers?
gq-019 ended with: cannot_answer, kind no_definition
gq-019 model calls: 1
  reason: no_definition: The term 'best' is not defined in the available metrics or dimensions, and no metric or dimension can determine customer performance based on this vague criterion.
gq-020 (ambiguous): Which region is doing best?
gq-020 ended with: ask_back, kind None
gq-020 model calls: 3
  asks: Which time period are you interested in? For example, the most recent month, the last quarter, or a specific year?
gq-020 request: net_revenue by customer__region, ordered by net_revenue, period: none
gq-020 check: error: request rejected: the request ranks its result but names no period; filter or group by a metric_time grain; or ask the person which period they mean
gq-020 options: last month, last quarter, 2026
gq-021 (unanswerable): How much did shipping cost us in fiscal year 2026?
gq-021 ended with: cannot_answer, kind not_in_data
gq-021 model calls: 2
  reason: not_in_data: The shop's data does not include a metric for shipping costs.
  first reply: {"kind": "not_in_data", "reason": "The shop's data does not include a metric for shipping costs."}
```

The model may give three kinds: `not_in_data`, `forecast` and `no_definition`. Code gives the other two: `stale`, when the data for the period hasn't arrived, and `forbidden`, which chapter 9's access rules will give. A call without a kind comes back as an error that lists the allowed kinds, so the model can correct it in its next call.

In the declining agent's run, the forecast, `gq-005`, ends in a decline of kind `forecast`, in 1 model call. "Who are our best customers?", `gq-019`, is declined with kind `no_definition`, which is the honest reply chapter 6 said was due: the shop's metrics don't rank customers, so no option could have been answered. The shipping question, `gq-021`, took 2 calls. The model's first reply was the decline's arguments without the tool's name, the loop sent back an error, and the second reply declined with kind `not_in_data`.

"Which region is doing best?", `gq-020`, is the one to read closely. The model asked for net revenue by region, ordered, with no period (`net_revenue by customer__region, ordered by net_revenue, period: none`), the request chapter 6's agent ran. The ranking check refused it because it ranks its result but names no period, and the model then asked back which period the person meant, offering last month, last quarter, 2026. That counts as a correct reply, and it settles half the question. A period doesn't say what "best" means, and [the readings](#kinds-of-unanswerable) give different regions.

The last question, `gq-016`, asks how many customers placed at least one order in 2025. The warehouse can answer it, but no metric in the layer counts customers who ordered, and chapter 6's agent answered it with the count of new customers, a wrong number. The declining agent declined it as `not_in_data`, which is honest about the layer, and gave a reason about a filter the metric can't use, which is beside the point.

**Working rule:** Make declining a tool that ends the run with a kind from a fixed list and a sentence for the person. Let the model choose among the kinds it can judge, such as missing data, a forecast or an undefined term, and let code decide the kinds code can check, such as stale data or a forbidden role. Count declines by kind, and read the reasons in traces, because a decline of the right kind can still give the wrong reason.

## Check freshness before answering {#check-freshness}

A [decline the model chooses](#decline-with-a-reason) covers questions the data can't answer at all. A subtler case is data that can answer the question, but hasn't all arrived. A partial total looks complete: the SQL runs, the number has the right shape, and it's too small. Freshness is how far a source's events have arrived, read from when its rows were loaded. dbt's source freshness check works that way: it reads the newest load time from a `loaded_at_field`, or from `loaded_at_query`, "A SQL expression that returns the most recent loaded timestamp", and compares it to thresholds such as `warn_after`, "How old the most recent data can be before a freshness check reports a warning" ([dbt](https://docs.getdbt.com/reference/resource-properties/freshness)). dbt can also read the warehouse's own metadata when you give it neither; we don't, for the reason below.

Freshness has to come from the data, not from the warehouse's table metadata. Snowflake's `LAST_ALTERED` is the "Date and time the object was last altered by a DML, DDL, or background metadata operation" ([Snowflake](https://docs.snowflake.com/en/sql-reference/info-schema/tables)), so maintenance moves it too. DuckDB's table catalog, `duckdb_tables()`, has no time column at all (`duckdb_tables() time columns: none`).

The shop's generator gives every raw table a `_loaded_at` column, when the nightly load brought the row in, at 02:00 UTC the day after the event, and the marts carry it through. Its refunds feed stopped after June 26, 2026, while orders run to June 30. Some metrics keep changing after their period ends. The refund rate, `refund_rate`, divides refunded euros by the gross revenue of the same orders, and counts each refund on its order's day. A refund comes weeks after its order, so a month's rate keeps rising until every refund on its orders has come. We call that time the metric's settling window. The freshness check in `lib/declining.py` compares each feed's newest load with the end of the period a request filters on, plus the settling window of the metrics that read the feed. `FEEDS` names, for each table a metric reads, the feed whose loads decide its freshness, and `SETTLING_DAYS` gives the window of each metric counted on an earlier date than its events; every other metric's is zero. Loads are in UTC and the shop's days are local, so the period ends when its last local day ends in the region furthest behind UTC. The example measures the window, estimates why May and June fall short, and runs the check.

Example `stale-refunds` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.10:

```python
"""Check freshness: refunds stopped loading after June 26, 2026, and come weeks after the order."""
from datetime import date

from lib.declining import (FEEDS, SETTLING_DAYS, DecliningToolbox, check_freshness, refund_delays, refund_shortfall,
                           settled_refund_rate)
from lib.semantic import MetricRequest, load
from lib.warehouse import connect, data_as_of

con, layer = connect(), load()
catalog = [c for (c, t, *_) in con.execute("DESCRIBE SELECT * FROM duckdb_tables()").fetchall() if "TIME" in t]
print(f"duckdb_tables() time columns: {', '.join(catalog) or 'none'}")
for table in ("analytics.fct_orders", "analytics.fct_refunds", "analytics.dim_customers"):
    print(f"data as of, {table}: {data_as_of(con, table)}")
delays = refund_delays(con)                # the longest delay on settled orders is what SETTLING_DAYS uses
print(f"refunds per day: {delays['per day']:.1f}\nmedian days from order to refund: {delays['median']}\n"
      f"refunds within 30 days of the order: {delays['within 30']:.0%}\n"
      f"refunds within 45 days of the order: {delays['within 45']:.0%}\n"
      f"longest days from order to refund: {delays['longest']}\n"
      f"settling window, order_refunds: {SETTLING_DAYS['order_refunds']} days")
for month in ("2026-04", "2026-05", "2026-06"):           # without a check, the layer answers for any month
    (rate,), = layer.query(con, MetricRequest(("refund_rate",), (), {"metric_time__month": month})).rows
    print(f"refund rate, {month}, unchecked: {rate:.2%}")
# Why May and June are short, estimated from the twelve months whose refunds have all come.
print(f"refund rate, settled months: {settled_refund_rate(con):.2%}")
for month, end in (("2026-05", date(2026, 6, 1)), ("2026-06", date(2026, 7, 1))):
    short = refund_shortfall(con, end)
    print(f"{month}, settled months' rate with refunds as loaded: {short['as loaded']:.2%}\n"
          f"{month}, points short, refunds not loaded: {short['not loaded'] * 100:.2f}\n"
          f"{month}, points short, refunds not happened yet: {short['not happened'] * 100:.2f}\n"
          f"{month}, share of the shortfall not loaded: {short['share not loaded']:.0%}")

print(f"new customers, feed for dim_customers: {FEEDS['analytics.dim_customers']}")  # customers load at sign-up
for name, metric in (("refund rate", "refund_rate"), ("new customers", "new_customers")):
    for check in check_freshness(con, layer, MetricRequest((metric,), (), {"metric_time__month": "2026-06"})):
        print(f"{name}, 2026-06: {check.describe()}")
for month in ("2026-06", "2026-05", "2026-04"):
    query = {"metrics": ["refund_rate"], "filters": {"metric_time__month": month}}
    a = (r := DecliningToolbox(con, layer).call("query_metric", query)).answer
    print(f"refund rate, {month}, checked: "
          + (f"{a.rows[0][0]:.2%}, data as of {a.provenance.data_as_of}" if a.answered else r.content))
```

Output:

```text
duckdb_tables() time columns: none
data as of, analytics.fct_orders: 2026-07-02 02:00:00
data as of, analytics.fct_refunds: 2026-06-27 02:00:00
data as of, analytics.dim_customers: 2026-06-15 02:00:00
refunds per day: 1.2
median days from order to refund: 27.5
refunds within 30 days of the order: 56%
refunds within 45 days of the order: 93%
longest days from order to refund: 49
settling window, order_refunds: 49 days
refund rate, 2026-04, unchecked: 6.74%
refund rate, 2026-05, unchecked: 6.85%
refund rate, 2026-06, unchecked: 0.54%
refund rate, settled months: 7.21%
2026-05, settled months' rate with refunds as loaded: 5.78%
2026-05, points short, refunds not loaded: 0.48
2026-05, points short, refunds not happened yet: 0.95
2026-05, share of the shortfall not loaded: 33%
2026-06, settled months' rate with refunds as loaded: 1.17%
2026-06, points short, refunds not loaded: 0.46
2026-06, points short, refunds not happened yet: 5.57
2026-06, share of the shortfall not loaded: 8%
new customers, feed for dim_customers: analytics.fct_orders
refund rate, 2026-06: analytics.fct_orders last loaded 2026-07-02 02:00, period ends 2026-06-30: complete
refund rate, 2026-06: analytics.fct_refunds last loaded 2026-06-27 02:00, period ends 2026-06-30, its rows can arrive through 2026-08-18 (49 days later): STALE (not loaded, not happened yet)
new customers, 2026-06: analytics.fct_orders last loaded 2026-07-02 02:00, period ends 2026-06-30: complete
refund rate, 2026-06, checked: declined: stale: analytics.fct_refunds was last loaded at 2026-06-27 02:00, and rows for the period ending 2026-06-30 can arrive through 2026-08-18, 49 days later (not loaded, not happened yet), so the answer would be missing rows
refund rate, 2026-05, checked: declined: stale: analytics.fct_refunds was last loaded at 2026-06-27 02:00, and rows for the period ending 2026-05-31 can arrive through 2026-07-19, 49 days later (not loaded, not happened yet), so the answer would be missing rows
refund rate, 2026-04, checked: 6.74%, data as of 2026-06-27 02:00:00
```

The refunds were last loaded at 2026-06-27 02:00:00, and the orders at 2026-07-02 02:00:00. On orders placed before March 2026, old enough for all their refunds to have come, 56% of refunds came within 30 days of the order and 93% within 45, and the longest took 49 days. So the refund rate's window is 49 days, the longest delay the shop has seen.

Without a check, the layer reports a refund rate of 0.54% for June 2026, against 6.85% for May and 6.74% for April. June's fall has two causes: some of June's refunds were made but never loaded, and most haven't been made yet. The twelve settled months, May 2025 to April 2026, estimate each. Their refund rate is 7.21%, and 1.17% counting only the refunds made by the point the feed's last load reaches for June. Of June's shortfall, refunds not loaded account for about 0.46 points and refunds not yet made for about 5.57: the stale feed explains only 8% of the shortfall. May's rate looks normal and is short too, by about 0.48 points not loaded and 0.95 not yet made, 33% from the stale feed. These are estimates from other months, not measurements.

The check finds June's orders complete and its refunds short for both causes, and the tool declines May and June with kind `stale` and a reason that names the feed, its last load and the last day the period's refunds can come. The model never sees a number to report. April's window ended before the refunds' last load, so its rate is answered, with the refunds' load time in its provenance.

The naive version of the check misfires. The customers table was last loaded at 2026-06-15 02:00:00, because a customer's row loads when they sign up, and nobody signed up after mid-June. Checked against its own loads, June's new customers would be declined. But a customer's first order date comes from the orders, so `FEEDS` maps the customers table to the orders feed, and June's new customers pass. Which feed decides a table's freshness is a fact about your pipeline, and it belongs in a mapping a person writes, as dbt sources declare their own `loaded_at_field`.

We decline a period that hasn't settled rather than answer with a warning, as a rule of thumb. A warning travels with the answer only until someone copies the number. A decline that names the last load and the last day the period's events can come lets the person ask for a period that has settled.

**Working rule:** Check freshness in code before every answer that names a period: compare the newest load of each feed the answer reads with the end of the period plus the metric's settling window, and decline as stale when the feed stops short, whether its rows haven't loaded or haven't happened. Measure each window from your own data, as the delay that covers the events you've seen. Read load times from your own load columns or a load log, never from table metadata, and map each table to the feed that decides its freshness. Answer a question with no period, and show its data as of in the provenance.

## Show the provenance with every answer {#show-provenance}

[A decline](#decline-with-a-reason) tells the person why there's no number. An answer owes them the same: where the number came from. An answer's provenance is the metric or SQL behind it, the filters, the role it was computed for and how fresh the data was. The shop's `Answer` has carried `answer.provenance` since [chapter 1](#answer-from-a-metric). This section is about showing it. We found no study that measures whether showing provenance makes people catch more wrong numbers, so this is our design choice, not a measured effect. The reasoning is that a person checks a metric's definition in seconds, and a query in minutes.

`provenance_card()` in `lib/declining.py` prints an answer with its provenance: the result, each metric's name and the definition its owner wrote in the semantic layer, the filters, the role, the data as of, the freshness check for each feed and, optionally, the SQL. A decline's card is its kind, its reason and the role. The example replays three of the declining agent's runs: net revenue by region in March 2026, which it got right; total revenue by sales region in 2025, which it got wrong; and the cost of shipping, which it declined.

Example `answer-with-provenance` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.10:

```python
"""Show the provenance with every answer: the metric's definition, filters, role, freshness and the SQL that ran."""
from lib.agent import run_agent
from lib.declining import DecliningToolbox, provenance_card
from lib.golden import golden_result, grade, load_golden
from lib.metric_tools import catalog
from lib.model import RecordedModel
from lib.prompts import declining_prompt
from lib.semantic import load
from lib.warehouse import connect

con, layer = connect(), load()
system, model = declining_prompt(catalog(layer)), RecordedModel("decline-runs")
golden = {q.question_id: q for q in load_golden()}
for question_id in ("gq-002", "gq-012", "gq-021"):
    q = golden[question_id]
    toolbox = DecliningToolbox(con, layer, role=q.role)
    trace = run_agent(q.question, system, model, toolbox, max_steps=4)
    print(f"{question_id}: {q.question}")
    print(provenance_card(trace.answer, layer, toolbox.freshness, sql=question_id == "gq-002"))
    print(f"{question_id} outcome: {grade(q, trace.answer, golden_result(con, q))}")
    print()
```

Output:

```text
gq-002: What was net revenue in each region in March 2026?
order__region  net_revenue
AMER           51,762.14
APAC           35,296.93
EMEA           63,023.76
metric: net_revenue: Revenue in EUR after discounts and before tax, from real orders that weren't cancelled, counted on the order's local business day. Returned orders count; refunds are not subtracted.
filters: {'metric_time__month': '2026-03'}
role: analyst
data as of: 2026-07-02 02:00:00
freshness: analytics.fct_orders last loaded 2026-07-02 02:00, period ends 2026-03-31: complete
sql:
SELECT
  orders.region AS order__region,
  SUM(orders.net_revenue_eur) AS net_revenue
FROM analytics.fct_orders AS orders
WHERE
  orders.status <> 'cancelled'
  AND CAST(DATE_TRUNC('MONTH', CAST(orders.order_date_local AS DATE)) AS DATE) = CAST('2026-03-01' AS DATE)
GROUP BY
  orders.region
ORDER BY
  order__region ASC
gq-002 outcome: correct

gq-012: What was total revenue for each sales region in 2025?
order__region  gross_revenue
AMER           538,429.66
APAC           444,472.81
EMEA           897,698.19
metric: gross_revenue: Revenue in EUR including tax, before refunds, from real orders that weren't cancelled.
filters: {'metric_time__year': 2025}
role: analyst
data as of: 2026-07-02 02:00:00
freshness: analytics.fct_orders last loaded 2026-07-02 02:00, period ends 2025-12-31: complete
gq-012 outcome: wrong

gq-021: How much did shipping cost us in fiscal year 2026?
declined: not_in_data: The shop's data does not include a metric for shipping costs.
role: finance
gq-021 outcome: correct
```

The first card, `gq-002`, is the answer with everything behind it. Net revenue's definition says what the number includes, the filter says March 2026, the freshness line says the orders feed was complete for that period, and the SQL shows the cancelled orders left out. Its outcome is `correct`.

The second card, `gq-012`, is why the card exists. The question asks for total revenue, and the shop's finance team means net revenue by it. The agent chose `gross_revenue`, and the card's definition line says "Revenue in EUR including tax". A person who reads only the numbers sees three plausible regional totals. A person who reads the first line under them sees that tax is included and asks again. The outcome is `wrong`, and the card made the mistake visible without the SQL.

The third card is a decline with its kind and its reason, `not_in_data`, and the role it was computed for, `finance`. A decline needs no SQL, but it needs the role: when [chapter 9](#who-may-see-what) adds access rules, the same question can be answered for one role and declined for another.

**Working rule:** Show every answer with its provenance, and put the metric's name and definition first, since that's where a near-miss metric shows. Then show the filters, the period, the role and the data as of, and keep the SQL one step away for the people who check it. Show declines the same way, with their kind, reason and role.

## Measure declines, not only accuracy {#measure-declines}

The [declines](#decline-with-a-reason), [freshness check](#check-freshness) and [provenance](#show-provenance) change how the agent fails, and a score has to show which way. Accuracy doesn't. It counts a decline on an answerable question as a miss, the same as a wrong number, so an agent that guesses scores no worse than one that declines. Kalai and colleagues argue that grading this way rewards guessing ([Kalai et al.](https://arxiv.org/abs/2509.04664)). Two pairs of measures separate the cases, and one score weighs them.

Decline precision and recall treat a question whose right answer is a decline as a positive, and a run that ended without a number, by a decline or a question back, as a predicted positive. Precision asks how many of the agent's declines were due; recall asks how many of the due declines it made. Coverage and selective risk come from selective prediction: coverage is "the probability mass of the non-rejected region", the share of questions answered, and selective risk is the error rate on those answered ([Geifman and El-Yaniv](https://arxiv.org/abs/1705.08500)). Lowering the bar for answering raises coverage and usually risk. TrustSQL's penalty score weighs them. Each question scores one point for a right answer or a right decline, nothing for declining an answerable question, and minus c for a wrong number, where "A penalty of −c is assigned when the generated SQL is incorrect" or when the model answers a question it should have declined; the score is the mean over the questions ([Lee et al.](https://arxiv.org/abs/2403.15879)). TrustSQL's questions to decline are unanswerable ones only, and it leaves resolving ambiguity out of its scope. We score the ambiguous questions too, as questions to decline, and count a question back on one as a right decline, so our score is TrustSQL's adapted to the shop's golden set. With c at 0 it is the share of correct replies, as accuracy is; with c large, one wrong number cancels many right ones. As formulas, where a wrong number includes any number given for a question that should be declined:

```text
decline precision = correct declines / all declines
decline recall    = correct declines / questions whose right answer is a decline
coverage          = questions answered with a number / questions asked
selective risk    = wrong numbers / questions answered with a number
penalty score     = (right answers + correct declines − c × wrong numbers) / questions asked
```

A run that hit the step limit is neither a decline nor an answer: it adds nothing to the score and counts as unanswered for coverage. `Tally` in `lib/declining.py` computes all five. The example replays chapter 6's metrics-first agent and the declining agent on the same 21 dev questions, 17 answerable and 4 to decline, and prints each measure, with c at 3, the cost [the prompt](#decline-with-a-reason) states, and at 10, a value TrustSQL uses. Choosing c is a judgement about what a wrong number costs, not a measurement.

Example `decline-precision-recall` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.10:

```python
"""Measure declines, not only accuracy: precision, recall, coverage, selective risk and a penalty score, on dev."""
from lib.agent import run_agent
from lib.declining import DecliningToolbox, Tally
from lib.golden import golden_result, grade, load_golden
from lib.metric_tools import MetricToolbox, catalog
from lib.model import RecordedModel
from lib.prompts import declining_prompt, metrics_first_prompt
from lib.semantic import load
from lib.warehouse import connect

con, layer = connect(), load()
agents = {"metrics-first": (metrics_first_prompt(catalog(layer)), RecordedModel("metric-agent-runs"), MetricToolbox),
          "declining": (declining_prompt(catalog(layer)), RecordedModel("decline-runs"), DecliningToolbox)}
# The dev split's answer and decline questions; forbidden questions are decided below the model, in chapter 9.
questions = [q for q in load_golden() if q.split == "dev" and q.kind in ("answer", "decline")]
for name, (system, model, Toolbox) in agents.items():
    tally, by_type = Tally(), {"ambiguous": Tally(), "unanswerable": Tally()}
    for q in questions:
        answer = run_agent(q.question, system, model, Toolbox(con, layer, role=q.role), max_steps=4).answer
        outcome = grade(q, answer, golden_result(con, q))
        tally.add(q.question_id, q.kind, answer, outcome)
        if q.kind == "decline":
            by_type[q.decline_type].add(q.question_id, q.kind, answer, outcome)
    for ending in ("right", "wrong", "abstained", "step limit"):
        print(f"{name} {ending}: {tally.count(ending=ending)} of {len(questions)}")
    for label, kind, ending in (("wrong numbers", None, "wrong"), ("declined answerable", "answer", "abstained")):
        ids = [i for i, k, e in tally.rows if kind in (None, k) and e == ending]
        print(f"{name} {label}: {', '.join(ids) or 'none'}")
    print(f"{name} decline precision: {tally.precision:.2f}")
    print(f"{name} decline recall: {tally.recall:.2f}")
    for kind, part in by_type.items():
        print(f"{name} recall, {kind}: {part.count('decline', 'abstained')} of {part.count('decline')}")
    print(f"{name} coverage: {tally.coverage:.2f}")
    print(f"{name} selective risk: {tally.selective_risk:.2f}")
    for c in (3, 10):
        print(f"{name} penalty score, c={c}: {tally.penalty_score(c):.2f}")
```

Output:

```text
metrics-first right: 12 of 21
metrics-first wrong: 5 of 21
metrics-first abstained: 3 of 21
metrics-first step limit: 1 of 21
metrics-first wrong numbers: gq-012, gq-016, gq-017, gq-018, gq-020
metrics-first declined answerable: none
metrics-first decline precision: 1.00
metrics-first decline recall: 0.75
metrics-first recall, ambiguous: 1 of 2
metrics-first recall, unanswerable: 2 of 2
metrics-first coverage: 0.81
metrics-first selective risk: 0.29
metrics-first penalty score, c=3: 0.00
metrics-first penalty score, c=10: -1.67
declining right: 11 of 21
declining wrong: 4 of 21
declining abstained: 5 of 21
declining step limit: 1 of 21
declining wrong numbers: gq-008, gq-012, gq-017, gq-018
declining declined answerable: gq-016
declining decline precision: 0.80
declining decline recall: 1.00
declining recall, ambiguous: 2 of 2
declining recall, unanswerable: 2 of 2
declining coverage: 0.71
declining selective risk: 0.27
declining penalty score, c=3: 0.14
declining penalty score, c=10: -1.19
```

Recall rose from 0.75 to 1.00: the declining agent declined or asked back on all four questions, where chapter 6's agent answered "Which region is doing best?". Precision fell from 1.00 to 0.80, because it declined one answerable question, `gq-016`, the count of customers who ordered. Coverage fell from 0.81 to 0.71, and selective risk moved from 0.29 to 0.27. The penalty score at c = 3 went from 0.00 to 0.14, and at c = 10 from -1.67 to -1.19.

The wrong numbers tell the rest. Chapter 6's agent gave gq-012, gq-016, gq-017, gq-018, gq-020; the declining agent gave gq-008, gq-012, gq-017, gq-018. Two left the list by the routes this chapter built: `gq-020` through the ranking check and a question back, and `gq-016` through a decline. One joined it: `gq-008`, total revenue in 2025, which chapter 6's agent answered with net revenue and this one with gross revenue, the near-miss pair [chapter 6](#read-the-misses) described. The prompt's sentence that a metric with a similar name isn't the same metric didn't prevent it, though with one sample per call, a single flip such as `gq-008` may be chance. The rest are the near-miss metrics of `gq-012` and `gq-018`, and `gq-017`, which needs the asker's region, chapter 9's work. Both agents score below zero at c = 10: a handful of wrong numbers outweighs every right one, which matches TrustSQL's own finding, that "achieving high scores under severe penalties requires significant effort".

Read these as small numbers. The dev split has four questions to decline, so recall moves in steps of a quarter, and one question of 21 changes coverage by about five points. The prompt's changes were chosen from chapter 6's dev traces, so the dev numbers are optimistic, and this chapter records nothing on the test split. The direction agrees with larger studies: prompting helps abstention but doesn't fix it ([Kirichenko et al.](https://arxiv.org/abs/2506.09038)), and prompts that push models to critique questions also raise "false invalid judgments" on valid ones ([Lin et al.](https://arxiv.org/abs/2610.22158)).

**Working rule:** Score an agent on declines as well as answers: report decline precision and recall, coverage and selective risk, and a penalty score with a c your stakeholders agree to, stated as a judgement. Compare agents on the same questions, and list the wrong numbers each gave, because a change that removes one wrong number can add another. When the decline questions number in single digits, read the runs, not only the rates.

## What goes wrong in production {#declining-in-production}

The shop's declining agent declines the dev questions it should, and pays for it with one answerable question. An agent with declines over a real warehouse fails in these ways, and each has a way to notice.

**A quiet feed looks stale.** The freshness check reads the newest `_loaded_at` in the data, and a feed with no events on a day loads no rows that day. The shop's refunds arrive at about 1.2 a day, so a quiet weekend would make a complete period look stale. A load log that records every run, with its row count, fixes this; dbt's `loaded_at_query` exists for sources like that. You notice by counting stale declines per feed: a feed that is declined on most days is quiet, not late.

**A settling window goes out of date.** Half the shop's refunds come more than 27.5 days after their order, and the window is the longest delay seen so far. A longer returns period, or a slower payment provider, makes the window too short, and the check passes months that are still rising. Measure each window again on a schedule, from orders old enough to have all their events, and watch the share of events that arrive after it.

**A series' last period escapes the check.** The check reads the period a request filters on. A request grouped by month with no period filter returns every month, the last one partial, and passes. Check the last group of any time series against the feeds, or require a period in every request that groups by time.

**Declines grow where the layer stops.** The declining agent declined `gq-016` because no metric counts customers who ordered. Each `not_in_data` decline on a question the warehouse could answer is a gap in the layer: read them as a backlog for a metric to write or for [chapter 7's guarded SQL](#metric-or-sql).

**The kind can be right and the reason wrong.** `gq-016`'s reason talks about a filter, and chapter 6's forecast reply asked about the wrong thing. The kind is for counting; the sentence is for the person, and the model writes it. Read a sample of reasons each week, and keep the kinds few enough that a person can tell them apart.

**A confidence target in the prompt isn't calibration.** The prompt asks the model to answer only above 75% confidence, and the model has no reliable way to know its confidence: LLMs verbalizing their confidence "tend to be overconfident" ([Xiong et al.](https://arxiv.org/abs/2306.13063)), and one unreviewed study puts "query executability" among signals that rank correct SQL above incorrect only at about 0.61 to 0.68 AUROC ([Richardson](https://arxiv.org/abs/2607.06799)). Prefer checks in code, such as an unknown metric, a ranking over no period or a stale feed, and treat the prompt's target as a nudge.

**A question back can settle half the question.** `gq-020` asked about the period and left "best" undefined, and the score counts it as correct. Read questions back in traces, and give the ask-back tool options that name metrics, so the person chooses a definition.

**Working rule:** Before you widen the agent's audience, give the freshness check a load log, measure each metric's settling window again on a schedule, check every time series' last period, count declines by kind and feed, and read a sample of reasons and questions back. Start with the `not_in_data` declines on answerable questions, because each one names a metric to write.

## Decisions this chapter made {#declining-decisions}

- **Declining is a tool that ends the run,** with a kind from a fixed list and a sentence for the person. The model chooses among `not_in_data`, `forecast` and `no_definition`; code gives `stale` and, from chapter 9, `forbidden`.
- **Ambiguous and unanswerable questions are told apart,** each named in PRACTIQ's or TrustSQL's terms. Ask back only when every reading is answerable.
- **Checks in code come before the model's judgement:** the ranking check refuses a ranking over no period, and the freshness check declines a period whose feed stops short of its end plus the metric's settling window.
- **Freshness comes from load times in the data,** mapped from each table to the feed that decides it, never from table metadata.
- **A period that hasn't settled is declined, not answered with a warning,** as a rule of thumb, with a reason that names the feed's last load and the last day its events can come. The refund rate's window is the longest delay the shop's refunds show.
- **Every answer shows its provenance,** metric and definition first, then filters, role, data as of and freshness, with the SQL one step away.
- **Declines are measured with precision and recall, coverage and selective risk, and a penalty score** at c = 3 and c = 10, TrustSQL's mean with the ambiguous questions scored as declines, on the dev split's 21 answer and decline questions, beside chapter 6's agent. Forbidden questions are left to chapter 9.
- **The prompt was written from chapter 6's dev traces and recorded once,** with no test split recorded for this chapter.
