---
title: "Business Intelligence with Agents"
chapter: "Give the agent layered context"
chapter_id: layered-context
book: business-intelligence-with-agents
edition: 2026.11.7
verified: 2026-11-10
edition_code: ZNJE-JAVW
canonical: https://rollingedition.com/business-intelligence-with-agents/layered-context
license: CC BY 4.0
attribution: "“Give the agent layered context,” chapter 4 of Business Intelligence with Agents, Edition 2026.11.7, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/business-intelligence-with-agents/layered-context. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Give the agent layered context

By the end of this chapter, you can give a model that writes SQL more than the schema, in layers: notes on columns whose names mislead, a glossary of the shop's business terms, and verified queries retrieved for each question. You can fit those layers to a token budget, measure what each one adds on the dev split of the golden questions, and check the best set once on the held-out test split.

The problem shows up in the first question chapter 1 asked of the shop, the online outdoor-gear shop in three regions that this book follows throughout. Given only the warehouse's schema, the model wrote a query for net revenue in each region in March 2026 that ran, looked right and counted cancelled orders. The rule it missed exists, in the finance team's definition of net revenue, but nothing the model was given contains it. Layered context is the most direct fix: write the rules down where the model reads them. It isn't the fix this book ends with, since chapters 5 and 6 move the definitions into a semantic layer the model can't misread. But any agent that writes SQL needs context, including the guarded one in chapter 7, and the habit this chapter teaches, adding one layer at a time and measuring each, applies to every change that follows.

## What the schema says, and what it doesn't {#what-the-schema-says}

A schema tells a model which tables exist, what their columns are called and what type each column holds. That is a lot, and it never goes out of date, because the database produces it. What it can't tell the model is what the columns mean: which rows a table holds, which rows count toward a business number, which time zone a timestamp is in, and which of two similar tables is the one people trust. Those meanings decide whether a query returns the right number, and they live in the SQL that built the marts and in the heads of the people who own them.

The book's measure of this is the shop's golden questions, which chapter 3 built: questions with a verified answer, split into a dev set for tuning context and prompts and a held-out test set for checking the result once. Every layer in this chapter is added to the schema, so the schema is the first layer, and the place to start is what it leaves open. `build_context()` in `lib/context.py`, the shared module that builds every layer in this chapter, returns the schema layer when it's asked for nothing else.

Example `schema-digest` (Python 3.12.15 · duckdb 2.0.0), passing in Edition 2026.11.7:

```python
"""What the schema tells the model about revenue, and three totals for March 2026 that all fit it."""
from lib.context import build_context
from lib.warehouse import connect

con = connect()
schema = build_context(con, "", layers=("schema",))
print(f"tables in the schema: {schema.text.count('CREATE TABLE')}")
print(f"schema tokens (estimated): {schema.tokens}")
for line in schema.text.splitlines():
    if "analytics.fct_orders " in line or "analytics.orders_legacy " in line:
        print(line)

march = "BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'"
candidates = {
    "orders_legacy.revenue": f"SELECT sum(revenue) FROM analytics.orders_legacy WHERE order_date {march}",
    "fct_orders.net_revenue_eur, every order":
        f"SELECT sum(net_revenue_eur) FROM analytics.fct_orders WHERE order_date_local {march}",
    "fct_orders.net_revenue_eur, not cancelled":
        f"SELECT sum(net_revenue_eur) FROM analytics.fct_orders WHERE order_date_local {march} "
        "AND status <> 'cancelled'",
}
for name, sql in candidates.items():
    (total,), = con.execute(sql).fetchall()
    print(f"{name}: {total:,.2f}")
```

Output:

```text
tables in the schema: 16
schema tokens (estimated): 912
CREATE TABLE analytics.fct_orders (order_id INTEGER, customer_id INTEGER, region VARCHAR, country VARCHAR, channel VARCHAR, status VARCHAR, placed_at TIMESTAMP, order_date_local DATE, currency VARCHAR, line_count BIGINT, gross_revenue_eur DECIMAL(12,2), net_revenue_eur DECIMAL(12,2), discount_eur DECIMAL(12,2), tax_eur DECIMAL(12,2), _loaded_at TIMESTAMP);
CREATE TABLE analytics.orders_legacy (id INTEGER, cust_id INTEGER, order_date DATE, order_status VARCHAR, sales_region VARCHAR, revenue DECIMAL(12,2));
orders_legacy.revenue: 186,635.93
fct_orders.net_revenue_eur, every order: 162,542.79
fct_orders.net_revenue_eur, not cancelled: 150,082.83
```

The schema layer holds all 16 tables of the warehouse, about 912 tokens. Read the two lines it prints as a model would. `analytics.fct_orders` has a `net_revenue_eur` column and a `status` column, and `analytics.orders_legacy` has a `revenue` column and an `order_date`. Each of the three totals the example computes for March 2026 is a reasonable reading of those two lines. The legacy table's `revenue` gives 186,635.93 euros. The mart's `net_revenue_eur` over every order gives 162,542.79, which is what chapter 1's model computed. Only the third, 150,082.83, follows the finance team's definition, and nothing in the schema points to it rather than the other two.

The schema is small here. The whole of the shop's warehouse fits in those 912 tokens, so there's no case for trimming it: a study of strong models on the BIRD benchmark found that passing the whole schema when it fits can beat selecting tables first, because the selection step can drop a column the query needs ([Maamari et al., 2024](https://arxiv.org/abs/2408.07702)). A warehouse with thousands of tables is a different problem, which this chapter doesn't solve. The shop's problem isn't which tables to show. It's that what the tables show doesn't say which number is right.

**Working rule:** Keep the whole schema in the context when it fits, and add meaning to it rather than taking tables away. Before you write any other layer, take one real question and list every reading of the schema that answers it. Each reading the schema doesn't rule out is a rule some other layer has to state.

## Describe columns where names mislead {#describe-columns}

The [schema](#what-the-schema-says) leaves open which of several readings is right, and the cheapest place to close some of them is the column itself. A column note is a sentence about one table or column that says what its name doesn't: which rows the table holds, the unit and sign of an amount, the time zone of a timestamp, the values a column takes, or that a table is deprecated. A note isn't documentation of every column. A column called `product_name` needs none, and a note that repeats the name costs tokens and says nothing. The notes worth writing are on the columns a careful analyst new to the warehouse would misread.

Published evidence points the same way. A study that generated column descriptions with a language model found that adding them to the prompt improved text-to-SQL accuracy and, in an ablation that replaced column names with uninformative ones, that the descriptions helped most there ([Wretblad et al., 2024](https://arxiv.org/abs/2408.04691)); it is a single preprint on the BIRD benchmark. Databricks' guidance for its Genie Agents says that "quality table and column descriptions in Unity Catalog are critical for Genie accuracy" ([Databricks](https://docs.databricks.com/aws/en/genie/best-practices)), which is the vendor's advice, not a measurement.

The shop's notes live in `examples/data/shop/columns.toml`, one entry per table with an optional note per column, and `load_column_notes()` in `lib/context.py` turns each into one line, such as `analytics.fct_orders.placed_at: When the order was placed, in UTC.` The notes cover the traps chapter 2 found: `orders_legacy` is deprecated, `net_revenue_eur` still holds a value for cancelled orders, `placed_at` is UTC while `order_date_local` is the business day, `discount` is negative in `raw.order_lines` and positive in the marts, and the fiscal year starts on February 1.

To see what the notes do, the example replays the recording `context-layers`. It holds the pinned model's SQL for every dev question of kind `answer`, written once with each layer set this chapter measures, using the prompt `LAYERED_SQL` in `lib/prompts.py`. The recording was made by `recordings/record_context_layers.py`, with the same model, sampling and seed as chapter 1's, and the examples replay it by the hash of the exact messages.

Example `column-descriptions` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Add notes on columns whose names mislead, and see which dev questions the recorded model now gets right."""
from lib.context import LAYER_SETS, build_context, grade_with_context, load_column_notes
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.warehouse import connect

con = connect()
notes = load_column_notes()
print(f"column notes: {len(notes)}")
print(f"column notes tokens (estimated): {build_context(con, '', layers=('columns',)).tokens}")
for note in notes:
    if note.startswith(("analytics.fct_orders.status", "analytics.fct_orders.placed_at")):
        print(note)

model = RecordedModel("context-layers")
before, after = LAYER_SETS[0], LAYER_SETS[1]          # schema; schema and column notes
dev = [q for q in load_golden() if q.split == "dev" and q.kind == "answer"]
fixed, broken = [], []
for q in dev:
    was, now = grade_with_context(con, model, q, before), grade_with_context(con, model, q, after)
    if was != "correct" and now == "correct":
        fixed.append(q.question_id)
    if was == "correct" and now != "correct":
        broken.append(q.question_id)
print(f"fixed by column notes: {len(fixed)} ({', '.join(fixed)})")
print(f"broken by column notes: {len(broken)} ({', '.join(broken)})")
```

Output:

```text
column notes: 33
column notes tokens (estimated): 1087
analytics.fct_orders.status: One of placed, shipped, delivered, cancelled, returned. Revenue leaves out cancelled orders; order and customer counts include them. Returned orders count everywhere.
analytics.fct_orders.placed_at: When the order was placed, in UTC. Don't filter or group dates on it; use order_date_local.
fixed by column notes: 7 (gq-001, gq-002, gq-003, gq-004, gq-008, gq-009, gq-011)
broken by column notes: 1 (gq-018)
```

The 33 notes add about 1087 tokens, more than the schema itself. On the dev questions they fix 7 (gq-001, gq-002, gq-003, gq-004, gq-008, gq-009, gq-011), among them `gq-002`, the March question from chapter 1, whose query now filters out cancelled orders. They also break 1 (gq-018). That question asks for the refunds on orders placed in March 2026, and with the notes the model filtered on both the order's date and `refund_month`, so it dropped refunds paid in a later month. The note on `refund_month` was accurate. The model used it on a question that didn't call for it, which is what a note can't prevent.

**Working rule:** Write notes only for tables and columns whose names mislead: deprecated tables, amounts with a sign or unit you wouldn't guess, timestamps in a time zone other than the business's, and columns whose values include a placeholder such as `(none)`. Write them as facts about the column, not as instructions for one question. Expect a note to fix many questions and occasionally mislead on one, and keep the questions it broke in the golden set so you see it happen.

## Add the business glossary {#add-the-glossary}

[Column notes](#describe-columns) describe the tables. Many questions turn on something else: what a business word means at this company. "Revenue" could be gross or net. "Orders" could include cancelled ones or not. Refunds "in March" could mean refunds paid in March or refunds on March's orders. These are choices, made by the teams that own the numbers, and no table states them. A business glossary is a list of those words, each with its meaning written in terms of the warehouse's tables and columns.

Evidence for this layer comes from BIRD, a text-to-SQL benchmark whose questions come with "external knowledge evidence": hints that link a question's words to the database, such as what a term means as a formula over columns. In the benchmark's paper, adding the evidence raised GPT-4's execution accuracy on the dev set from 30.90% to 46.35%, with 2023 models and zero-shot prompts ([Li et al., 2023](https://arxiv.org/abs/2305.03111)). The hints are written per question, though, which is closer to giving the model the answer's ingredients than to giving it a glossary written once.

The shop's glossary is `examples/data/shop/glossary.toml`. Its entries define revenue as net revenue unless the question says gross, orders as every order including cancelled ones, average order value, fiscal periods, new customers, refunds by the month they were paid, units sold, and the two meanings of "channel". `load_glossary()` turns each into one line.

The glossary wasn't written blind, and the book's history shows how it changed. In the same change that recorded the model's first dev replies, with the schema alone, the entry for orders was corrected: it had said that order counts leave out cancelled orders, which disagreed with the finance team's golden SQL. The entries for units sold and for customers who ordered were added in that change too, and the column note on `status` was reworded to match. Later, after the test questions had been recorded with the schema alone, the refund-rate entry was changed to the book-wide definition that chapter 5 uses and that test question `gq-028` also follows: refunded amount divided by gross revenue, because a refund pays back tax and only gross revenue includes it. Each change made the glossary agree with golden SQL that it was then scored against. That is how a dev score gets fitted to dev, and [the check on test](#check-layers-on-test) comes back to what it costs.

Example `glossary-context` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Add the business glossary on top of the column notes, and see what it changes on the dev questions."""
from lib.context import LAYER_SETS, build_context, grade_with_context, load_glossary
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.prompts import layered_sql_messages
from lib.warehouse import connect

con = connect()
terms = load_glossary()
print(f"glossary terms: {len(terms)}")
print(f"glossary tokens (estimated): {build_context(con, '', layers=('glossary',)).tokens}")
print(next(t for t in terms if t.startswith("revenue:")))

model = RecordedModel("context-layers")
before, after = LAYER_SETS[1], LAYER_SETS[2]          # schema and column notes; then the glossary too
dev = [q for q in load_golden() if q.split == "dev" and q.kind == "answer"]
changes = {(was, now): [] for was in ("correct", "other") for now in ("correct", "other")}
for q in dev:
    was, now = (grade_with_context(con, model, q, layers) for layers in (before, after))
    changes["correct" if was == "correct" else "other", "correct" if now == "correct" else "other"].append(q.question_id)
print(f"fixed by the glossary: {len(changes['other', 'correct'])} ({', '.join(changes['other', 'correct'])})")
print(f"broken by the glossary: {len(changes['correct', 'other'])} ({', '.join(changes['correct', 'other'])})")

q = next(q for q in dev if q.question_id == "gq-002")
reply = model.complete(layered_sql_messages(build_context(con, q.question, after).text, q.question))
print(f"gq-002 with the glossary filters status: {'status' in reply}")
```

Output:

```text
glossary terms: 13
glossary tokens (estimated): 609
revenue: Net revenue unless the question says gross: sum of analytics.fct_orders.net_revenue_eur over orders whose status isn't 'cancelled'. In EUR.
fixed by the glossary: 3 (gq-012, gq-015, gq-018)
broken by the glossary: 3 (gq-002, gq-009, gq-016)
gq-002 with the glossary filters status: False
```

The 13 terms add about 609 tokens on top of the schema and the column notes. They fix 3 (gq-012, gq-015, gq-018) dev questions and break 3 (gq-002, gq-009, gq-016). The broken ones are the instructive part. For `gq-002`, the same March question, the query written with the glossary no longer filters on `status` (`filters status: False`), although the revenue entry and the note on `status` both say to leave cancelled orders out. For `gq-016`, the model left cancelled orders out of a customer count, applying the revenue rule where the glossary says it doesn't apply. For `gq-009`, the average order value, it divided the average order's net revenue by the number of orders again, although the glossary defines the measure as net revenue divided by the number of orders.

Each configuration was recorded once, with one sampled reply per question, so a change of one or two questions out of 17 is within what a second sample could undo. Chapter 10 measures that spread with repeated runs. What this result supports is narrower: the glossary didn't make this model better on these questions, and a rule stated twice was still missed. A plausible reason, which we haven't measured here, is that a longer context makes a small model use each part of it less reliably. Studies of long contexts find that models use information in the middle of a prompt worse than at its edges ([Liu et al., 2024](https://arxiv.org/abs/2307.03172)), and that accuracy falls with length when the question and the passage don't share words ([Modarressi et al., 2025](https://arxiv.org/abs/2502.05167)).

**Working rule:** Write a glossary entry for each business word whose meaning is a choice someone made, and state it in terms of tables and columns. Prefer one place for each rule, a column note or a glossary entry; the shop's files state the cancelled-orders rule in both, and the miss on `gq-002` shows that saying it twice doesn't make it stick. Measure the glossary on your dev questions before you trust it, and keep it only if it helps there or the next layer depends on it.

## Retrieve verified queries as examples {#retrieve-verified-queries}

Column notes and a glossary state rules. A verified query shows them applied: a question someone asked, with SQL a person checked against the shop's definitions. Given a few such pairs that resemble the question, a model can copy their shape, such as the join to `dim_date` for a fiscal period or the filter on `status`, instead of inventing one. A systematic comparison of prompt designs for text-to-SQL found that the best setup chose examples by the similarity of their questions, after masking domain-specific words, and by the similarity of their SQL to a draft query written first, and showed each as a question and its SQL alone ([Gao et al., 2023](https://arxiv.org/abs/2308.15363)). Warehouse vendors build the same idea into their assistants. Snowflake's Cortex Analyst keeps a verified query repository of "questions and corresponding SQL queries to answer them" ([Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/verified-query-repository)), and Databricks says a Genie Agent "can either use the example query directly or learn from" an example SQL query, and treats parameterized ones as trusted assets ([Databricks](https://docs.databricks.com/aws/en/genie-agents/tune-quality)). Both are the vendors' own descriptions, not measurements.

The shop's verified queries live in `examples/data/shop/verified_queries.toml`. Their fields follow Snowflake's field names, `name`, `question`, `sql`, `verified_at` and `verified_by`, plus the `role` the query was checked for. Two differ in content. Snowflake's `verified_at` is optional and counted in seconds since 1970, and its `verified_by` names the person who checked the query; the shop's files give a date and name a team, never a person. None of the verified queries is a golden question. They are near neighbours of questions in both splits, such as net revenue by fiscal quarter for fiscal 2025 or average order value by region for 2024, which is how a real repository grows: from questions people asked before. A verified query that was itself a golden question would make the score measure copying.

Retrieval in `lib/context.py` is lexical, with no embeddings. `question_terms()` lowercases the question, drops common words and masks three kinds of word: numbers, month names and the shop's three region codes. Every other word stays as it is. `QueryIndex` scores each verified question against the masked question with TF-IDF and cosine similarity, and `search()` keeps at most three matches that score at least 0.4. This is a cheap stand-in for the selection in [Gao et al.](https://arxiv.org/abs/2308.15363), not a reproduction of it: it masks far fewer words, and it drops the second step, which compares draft SQL.

Example `retrieve-similar-queries` (Python 3.12.15 · duckdb 2.0.0), passing in Edition 2026.11.7:

```python
"""Retrieve the verified queries most like a question, by TF-IDF over masked question words."""
from lib.context import QueryIndex, load_verified_queries, question_terms

queries = load_verified_queries()
index = QueryIndex(queries)
print(f"verified queries: {len(queries)}")

for label, question in (("aov", "What was the average order value in each region in March 2026?"),
                        ("parcels", "Which warehouse ships the most parcels?")):
    print(f"question: {question}")
    print(f"masked terms: {' '.join(question_terms(question))}")
    for score, query in index.search(question, k=3, min_score=0.0):
        print(f"  {score:.3f}  {query.name}")
    print(f"{label} matches kept: {len(index.search(question))}")

# What masking does to the words that name a time or a region, and what it leaves.
for phrase in ("March 2026", "January 2025", "calendar year 2024", "EMEA in Q3"):
    print(f"masked \"{phrase}\": {' '.join(question_terms(phrase))}")
```

Output:

```text
verified queries: 16
question: What was the average order value in each region in March 2026?
masked terms: average order value region <month> <number>
  0.835  average_order_value_by_region
  0.422  gross_revenue_by_region_month
  0.191  orders_of_one_customer
aov matches kept: 2
question: Which warehouse ships the most parcels?
masked terms: warehouse ships most parcels
  0.375  units_sold_by_product
  0.357  net_revenue_by_category
  0.000  average_order_value_by_region
parcels matches kept: 0
masked "March 2026": <month> <number>
masked "January 2025": <month> <number>
masked "calendar year 2024": calendar year <number>
masked "EMEA in Q3": <region> q3
```

For the average order value in each region in March 2026, the closest of the 16 verified queries is the same measure by region for 2024, and 2 matches pass the threshold. The second question, about which warehouse ships the most parcels, is one the shop's data can't answer at all. Its best scores come from the single shared word "most", and none passes the threshold, so 0 queries are offered. Without the threshold, the model would get three confident-looking examples, two of them about products, for a question about shipping.

The last lines of the output show what masking does and doesn't do. "March 2026" and "January 2025" both become `<month> <number>`, so a question about one month matches a verified query about another. "Calendar year 2024" becomes `calendar year <number>`, because "calendar" and "year" are neither common words nor values, and a quarter written as "Q3" isn't masked at all. That is why the March question's best match, a question about calendar year 2024, scores less than a perfect 1.

**Working rule:** Retrieve a few verified queries per question, chosen by similarity of the masked question, and show each as its question and SQL. Set a minimum score and check it on questions the warehouse can't answer, because lexical retrieval always returns something. Never let a golden question into the verified set. Move to embeddings only when your own measurement shows lexical retrieval missing queries that a person would call similar.

## Fit the context to a budget {#fit-a-context-budget}

With the schema, column notes, the glossary and [retrieved verified queries](#retrieve-verified-queries), the shop's context already takes several times as many tokens as the schema alone, and every layer you add makes it longer. A token budget is the most context the agent may send with one question. It exists for three reasons. The model's window is finite: the book's recording runtime gives the model 8,192 tokens, and up to 384 of them are kept for the reply. Each prompt token costs time on a CPU and money with a hosted model. And a longer context isn't used evenly, since models make less use of information in the middle of a long prompt than at its start or end ([Liu et al., 2024](https://arxiv.org/abs/2307.03172)).

Fitting a context to a budget means deciding what to leave out, and that decision needs an order of priority. `build_context()` takes the layers in priority order, adds their items one at a time, and drops any item that would take the context over the budget, so a later, shorter item may still fit. The schema is never dropped, for the [reason the first section gave](#what-the-schema-says): a schema that fits should be sent whole. Whatever the priority, the context is rendered in one fixed order, with the stable layers first, the retrieved queries after them, and the question last. That keeps the question beside the examples most like it, and it lets the model runner reuse the part of the prompt that every question shares instead of reading it again for each call. The runner that made the book's recordings, llama-cpp-python 0.3.36, does this in `Llama.generate`: it compares the new prompt's tokens with the last one's and evaluates only the tokens after the longest prefix they share ([llama-cpp-python 0.3.36, `llama.py`](https://github.com/abetlen/llama-cpp-python/blob/v0.3.36/llama_cpp/llama.py)).

Token counts in `lib/context.py` are estimates: `estimate_tokens()` divides the number of characters by 3.5, because the examples don't load the model's tokenizer. The example checks that estimate against the count the model's tokenizer reported when the prompt was recorded, then fits the context for the average-order-value question, `gq-009`, to an illustrative budget of 2,400 tokens under two priorities.

Example `context-token-budget` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Fit one question's layered context to a token budget, and check the token estimate against the model's count."""
from lib.context import LAYERS, build_context, estimate_tokens
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.prompts import layered_sql_messages
from lib.warehouse import connect

con = connect()
question = next(q for q in load_golden() if q.question_id == "gq-009").question
full = build_context(con, question)
for layer, tokens in full.layer_tokens().items():
    print(f"{layer} tokens (estimated): {tokens}")

messages = layered_sql_messages(full.text, question)
call = RecordedModel("context-layers").call_for(messages)
print(f"prompt tokens (estimated): {estimate_tokens(''.join(m['content'] for m in messages))}")
print(f"prompt tokens (model's tokenizer): {call['prompt_tokens']}")

budget = 2400
for name, priority in (("default", LAYERS), ("examples first", ("schema", "columns", "verified", "glossary"))):
    fitted = build_context(con, question, layers=priority, budget=budget)
    kept = {layer: len(items) for layer, items in fitted.items.items()}
    print(f"{name} priority: {fitted.tokens} tokens, kept {kept}")
    print(f"{name} dropped: {len(fitted.dropped)}")
print(f"render order: {', '.join(layer for layer, items in fitted.items.items() if items)}, then the question")
```

Output:

```text
schema tokens (estimated): 912
columns tokens (estimated): 1087
glossary tokens (estimated): 609
verified tokens (estimated): 200
prompt tokens (estimated): 2917
prompt tokens (model's tokenizer): 2364
default priority: 2393 tokens, kept {'schema': 1, 'columns': 33, 'glossary': 9, 'verified': 0}
default dropped: 6
examples first priority: 2384 tokens, kept {'schema': 1, 'columns': 33, 'glossary': 5, 'verified': 2}
examples first dropped: 8
render order: schema, columns, glossary, verified, then the question
```

The estimate for the whole prompt is 2917 tokens, against 2364 counted by the model's tokenizer. An estimate that runs high is the safe direction for a budget: the context it admits always fits. With the default priority, which follows the order the layers were introduced, the budget keeps every column note and part of the glossary and drops both retrieved queries, 6 items in all. With verified queries ranked above the glossary, the same budget keeps the two queries and drops 8 glossary entries instead. Neither order is right in general. The [next section](#measure-each-layer) measures which layers earn their tokens on the shop's questions, and that is what should set the order.

**Working rule:** Set a token budget well inside the model's window, and fit each question's context to it by a priority you have measured, not by the order you wrote the layers in. Never drop the schema when it fits. Render the stable layers first and the question last, whatever was dropped. Check your token estimate against the model's real count once, and keep it on the high side.

## Measure what each layer adds {#measure-each-layer}

Each layer so far was judged by the questions it fixed and broke. To choose which layers to keep, and in what order a [budget](#fit-a-context-budget) should drop them, you need all of them measured the same way. An ablation does that: it scores a series of configurations that differ by one layer each, on the same questions, under the same comparison rule. The questions are the dev split of the golden questions, because choosing among configurations is tuning, and tuning on the test split would leave nothing held out to check the choice.

The shop's dev split has 24 golden questions. This chapter scores the 17 of kind `answer`. The other 7 should be declined, because the warehouse can't answer them or the role asking may not see the answer, and a prompt that only writes SQL can't decline, so they would score as wrong under every layer set; chapters 8 and 9 score them. Each layer set adds one layer to the one before: the schema alone, then column notes, then the glossary, then up to three retrieved verified queries. The outcomes come from `grade()` in `lib/golden.py`, as in every chapter: correct when the result matches the golden result, wrong when it runs and doesn't, error when it doesn't run. The first layer set, the schema alone, isn't [chapter 3's baseline](#golden-questions) either. That baseline used the schema-only prompt and scored every question in each split, while this run uses the layered prompt `LAYERED_SQL` with no other layer filled in and scores the answer questions only, so its numbers differ.

Example `layer-ablation-dev` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Score each layer set on the dev split's answer questions, replaying the recorded model's SQL for each."""
from collections import Counter

from lib.context import LAYER_SETS, build_context, grade_with_context, layer_set_name
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.warehouse import connect

con = connect()
model = RecordedModel("context-layers")
dev_split = [q for q in load_golden() if q.split == "dev"]
dev = [q for q in dev_split if q.kind == "answer"]
print(f"dev split questions: {len(dev_split)}")
print(f"dev questions: {len(dev)}")
print(f"dev questions to decline: {len(dev_split) - len(dev)}")

grid = {}
for layers in LAYER_SETS:
    name = layer_set_name(layers)
    grid[name] = [grade_with_context(con, model, q, layers) for q in dev]
    counts = Counter(grid[name])
    tokens = sum(build_context(con, q.question, layers).tokens for q in dev) // len(dev)
    print(f"{name}: correct {counts['correct']}, wrong {counts['wrong']}, error {counts['error']}")
    print(f"{name} correct: {counts['correct']}")
    print(f"{name} error: {counts['error']}")
    print(f"{name} tokens: {tokens}")

print("question  " + "  ".join(f"{i + 1}" for i in range(len(LAYER_SETS))))
for i, q in enumerate(dev):
    print(f"{q.question_id}    " + "  ".join(grid[name][i][0] for name in grid))

# What the verified queries changed, against the run with the glossary.
before, after = grid[layer_set_name(LAYER_SETS[2])], grid[layer_set_name(LAYER_SETS[3])]
fixed = [q.question_id for q, was, now in zip(dev, before, after) if was != "correct" and now == "correct"]
broken = [q.question_id for q, was, now in zip(dev, before, after) if was == "correct" and now != "correct"]
print(f"fixed by verified queries: {len(fixed)}")
print(f"fixed by verified queries, IDs: {', '.join(fixed)}")
print(f"broken by verified queries: {len(broken)}")
```

Output:

```text
dev split questions: 24
dev questions: 17
dev questions to decline: 7
schema: correct 3, wrong 9, error 5
schema correct: 3
schema error: 5
schema tokens: 912
schema+columns: correct 9, wrong 7, error 1
schema+columns correct: 9
schema+columns error: 1
schema+columns tokens: 1999
schema+columns+glossary: correct 9, wrong 8, error 0
schema+columns+glossary correct: 9
schema+columns+glossary error: 0
schema+columns+glossary tokens: 2608
schema+columns+glossary+verified: correct 14, wrong 2, error 1
schema+columns+glossary+verified correct: 14
schema+columns+glossary+verified error: 1
schema+columns+glossary+verified tokens: 2775
question  1  2  3  4
gq-001    e  c  c  c
gq-002    w  c  w  c
gq-003    e  c  c  c
gq-004    w  c  c  c
gq-006    e  e  w  w
gq-007    w  w  w  w
gq-008    w  c  c  c
gq-009    w  c  w  c
gq-010    e  w  w  c
gq-011    w  c  c  c
gq-012    w  w  c  c
gq-013    e  w  w  c
gq-014    c  c  c  c
gq-015    w  w  c  c
gq-016    c  c  w  c
gq-017    w  w  w  e
gq-018    c  w  c  c
fixed by verified queries: 5
fixed by verified queries, IDs: gq-002, gq-009, gq-010, gq-013, gq-016
broken by verified queries: 0
```

The schema alone gets 3 of the 17 right, and 5 of its queries don't run. Column notes take it to 9, for about 1999 tokens of context on average. The glossary gives 9, no better. Verified queries on top give 14, for about 2775 tokens. The grid shows where. Against the run with the glossary, retrieved examples fixed 5 questions and broke 0. Two of the fixes are new: the fiscal-quarter question `gq-010` and the order count by region `gq-013`, whose nearest verified queries show exactly the join and the count they needed. The other three, `gq-002`, `gq-009` and `gq-016`, are the questions the glossary run had lost, so there the examples won back what the glossary had cost.

The totals say how much each layer helped. The failures say what the next layer should be, so the next two examples read them. The first takes the schema-only queries that don't run and finds the column DuckDB couldn't find.

Example `missing-columns-schema-only` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Why the dev queries written with the schema alone don't run: the column each one names, and the tables that have it."""
import re
from collections import Counter

import duckdb
from lib.context import LAYER_SETS, build_context
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.prompts import layered_sql_messages
from lib.tools import extract_sql, run_sql
from lib.warehouse import connect

con, model = connect(), RecordedModel("context-layers")
dev = [q for q in load_golden() if q.split == "dev" and q.kind == "answer"]
where = Counter()
for q in dev:
    context = build_context(con, q.question, LAYER_SETS[0])          # the schema alone
    sql = extract_sql(model.complete(layered_sql_messages(context.text, q.question)))
    try:
        run_sql(con, sql)
        continue
    except duckdb.Error as e:
        column = re.search(r'column (?:named )?"(\w+)"', str(e)).group(1)
    (tables,), = con.execute(
        "SELECT string_agg(table_schema || '.' || table_name, ', ' ORDER BY 1) FROM information_schema.columns "
        "WHERE table_schema = 'analytics' AND column_name = ?", [column]).fetchall()
    where[tables] += 1
    print(f"{q.question_id}: no column {column}; it is in {tables}")
print(f"schema-only queries that don't run: {where.total()}")
for tables, n in where.items():
    print(f"missing column only {tables} has: {n}")
```

Output:

```text
gq-001: no column fiscal_year; it is in analytics.dim_date
gq-003: no column calendar_year; it is in analytics.dim_date
gq-006: no column quantity; it is in analytics.fct_order_lines
gq-010: no column fiscal_quarter; it is in analytics.dim_date
gq-013: no column order_date; it is in analytics.orders_legacy
schema-only queries that don't run: 5
missing column only analytics.dim_date has: 3
missing column only analytics.fct_order_lines has: 1
missing column only analytics.orders_legacy has: 1
```

Every failure is a column the model put on the wrong table. Of the 5, 3 ask the orders mart for a fiscal or calendar column that only `dim_date` has, 1 asks it for `quantity`, which only the order lines have, and 1 uses the legacy table's `order_date`. These are the mistakes column notes are for: with the notes, 1 query in the whole dev set fails to run.

The second example prints the query for each dev question that all four layers still don't get right.

Example `what-stays-wrong` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""The dev questions that stay wrong with all four layers: each one's query, and whether gq-007 fails only on spelling."""
import duckdb
from lib.context import LAYERS, build_context, grade_with_context
from lib.golden import golden_result, grade, load_golden
from lib.model import RecordedModel
from lib.prompts import layered_sql_messages
from lib.tools import extract_sql, run_sql
from lib.warehouse import connect

con, model = connect(), RecordedModel("context-layers")
dev = [q for q in load_golden() if q.split == "dev" and q.kind == "answer"]


def sql_with_all_layers(q):
    return extract_sql(model.complete(layered_sql_messages(build_context(con, q.question, LAYERS).text, q.question)))


unsolved = [(q, outcome) for q in dev if (outcome := grade_with_context(con, model, q, LAYERS)) != "correct"]
print(f"not correct with all four layers: {len(unsolved)}")
for q, outcome in unsolved:
    sql = sql_with_all_layers(q)
    print(f"{q.question_id} ({outcome}): {q.question}")
    print("\n".join("    " + line for line in sql.strip().splitlines()))
    if outcome == "error":
        try:
            run_sql(con, sql)
        except duckdb.Error as e:
            print(f"    -- {str(e).splitlines()[0]}")

gq007 = next(q for q in dev if q.question_id == "gq-007")
respelled = sql_with_all_layers(gq007).replace("'tents'", "'Tents'")
print(f"gq-007 with 'Tents' spelled as stored: {grade(gq007, run_sql(con, respelled), golden_result(con, gq007))}")
```

Output:

```text
not correct with all four layers: 3
gq-006 (wrong): What were net revenue and the number of units sold in each region in 2025?
    SELECT
        o.region,
        SUM(o.net_revenue_eur) AS net_revenue,
        SUM(l.quantity) AS units_sold
    FROM analytics.fct_orders AS o
    JOIN analytics.fct_order_lines AS l USING (order_id)
    WHERE o.order_date_local >= '2025-01-01' AND o.order_date_local < '2026-01-01'
        AND o.status <> 'cancelled'
    GROUP BY o.region
    ORDER BY net_revenue DESC
gq-007 (wrong): How much net revenue came from orders that included a tent in 2025?
    SELECT
        SUM(fol.net_amount_eur) AS net_revenue
    FROM
        analytics.fct_order_lines fol
    JOIN
        analytics.fct_orders fo ON fol.order_id = fo.order_id
    JOIN
        analytics.dim_products dp ON fol.product_id = dp.product_id
    JOIN
        analytics.dim_date dd ON fo.order_date_local = dd.date_day
    WHERE
        dp.category = 'tents'
        AND dd.calendar_year = 2025
        AND fo.status != 'cancelled'
gq-017 (error): What was net revenue in each of our countries in 2025?
    SELECT d.country, round(sum(o.net_revenue_eur), 2) AS net_revenue
    FROM analytics.fct_orders AS o
    JOIN analytics.dim_date AS d ON d.date_day = o.order_date_local
    WHERE o.status <> 'cancelled'
      AND d.calendar_year = 2025
    GROUP BY d.country
    ORDER BY net_revenue DESC
    -- Binder Error: Table "d" does not have a column named "country"
gq-007 with 'Tents' spelled as stored: wrong
```

With all four layers, 3 questions are still not right. `gq-006` asks for net revenue and units sold by region. The model joined the orders mart to its lines and summed `net_revenue_eur` over the joined rows, so an order's revenue counts once for every line it has. The glossary's entry for units sold says to sum the lines per order first for exactly this reason, so this is a rule the context stated and the model missed. `gq-007` filters on the category `'tents'` where the data says `'Tents'`, a value no layer lists. Spelled as stored, the answer is still wrong, because the query sums only the tent lines, where the question asks for the whole revenue of the orders that included one. `gq-017` asks for "our countries", which depends on the region of the regional lead asking. No layer says who is asking, and the model's query, which takes `country` from `dim_date`, doesn't run.

This is the book's measurement on one synthetic warehouse, one 4-billion-parameter model and one sampled reply per question, not a general result about layered context. We found no peer-reviewed study from 2025 or 2026 that measures retrieved verified queries separately from other context on business data, which is why the chapter measures it here.

**Working rule:** Measure context one layer at a time on the dev split, with the same questions, comparison rule and model, and keep the outcomes per question, not only the totals. Treat a difference of one or two questions on a set this size as noise until repeated runs say otherwise. Read the queries that fail, because each one names a layer you don't have yet or a rule the model still skips.

## Check the chosen layers on test {#check-layers-on-test}

The [ablation](#measure-each-layer) chose all four layers on the dev split, the questions the chapter tuned on. The set that scored best there still has to be checked once on the held-out test split, together with the schema alone, so the comparison isn't flattered by having been chosen on the same questions. The recording `context-layers-test` holds the model's SQL for the 17 test questions of kind `answer`, under those two layer sets only. The example also scores each question against its best-matching verified query, which the next paragraphs need.

Example `best-layers-on-test` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Choose the best layer set on the dev split, then score it once on the held-out test split beside the schema alone."""
from collections import Counter

from lib.context import LAYER_SETS, QueryIndex, grade_with_context, layer_set_name, load_verified_queries
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.warehouse import connect

con = connect()
questions = [q for q in load_golden() if q.kind == "answer"]
dev = [q for q in questions if q.split == "dev"]
test = [q for q in questions if q.split == "test"]

dev_model = RecordedModel("context-layers")
dev_correct = {layers: sum(grade_with_context(con, dev_model, q, layers) == "correct" for q in dev)
               for layers in LAYER_SETS}
best = max(LAYER_SETS, key=lambda layers: (dev_correct[layers], -len(layers)))   # ties go to fewer layers
print(f"best on dev: {layer_set_name(best)}")
print(f"best on dev correct: {dev_correct[best]} of {len(dev)}")

test_model = RecordedModel("context-layers-test")
print(f"test questions: {len(test)}")
print(f"test question IDs: {', '.join(q.question_id for q in test)}")
for name, layers in (("schema", LAYER_SETS[0]), ("best", best)):
    counts = Counter(grade_with_context(con, test_model, q, layers) for q in test)
    print(f"test {name}: correct {counts['correct']}, wrong {counts['wrong']}, error {counts['error']}")
    print(f"test {name} correct: {counts['correct']}")

# How close each split's questions sit to the verified queries, by the retriever's own score.
index = QueryIndex(load_verified_queries())
for split, qs in (("dev", dev), ("test", test)):
    best_match = [(index.search(q.question, k=1, min_score=0.0)[0], q) for q in qs]
    print(f"{split} mean top retrieval score: {sum(score for (score, _), _ in best_match) / len(qs):.2f}")
    print(f"{split} questions with no verified query kept: {sum(not index.search(q.question) for q in qs)}")
    (score, query), q = max(best_match, key=lambda pair: pair[0][0])
    print(f"{split} closest pair: {q.question_id} and {query.name}")
    print(f"{split} closest score: {score:.3f}")
```

Output:

```text
best on dev: schema+columns+glossary+verified
best on dev correct: 14 of 17
test questions: 17
test question IDs: gq-025, gq-026, gq-027, gq-028, gq-029, gq-030, gq-031, gq-032, gq-033, gq-034, gq-035, gq-036, gq-037, gq-038, gq-039, gq-040, gq-041
test schema: correct 4, wrong 9, error 4
test schema correct: 4
test best: correct 8, wrong 7, error 2
test best correct: 8
dev mean top retrieval score: 0.57
dev questions with no verified query kept: 2
dev closest pair: gq-001 and net_revenue_by_fiscal_quarter
dev closest score: 0.862
test mean top retrieval score: 0.63
test questions with no verified query kept: 1
test closest pair: gq-029 and new_customers_by_region
test closest score: 0.933
```

The set chosen on dev is all four layers, schema+columns+glossary+verified, with 14 of 17 right there. On the 17 test questions, the schema alone gets 4 right and the four layers get 8. The layers still help on questions nobody tuned them on, which is the result that counts.

The gap between the dev and test scores is the other result, and this chapter didn't measure its cause. One explanation is that the verified queries suit dev better, and the retriever's own scores contradict it. Taking each question's best match, the mean score is 0.57 on dev and 0.63 on test. The closest pair of a golden question and a verified query is on test, gq-029 and new_customers_by_region, at 0.933, the same question asked of calendar year 2024; the closest on dev scores 0.862.

Two things are known. First, dev was used for more than choosing the set. As [the glossary section](#add-the-glossary) said, the glossary was edited to agree with golden SQL as the first dev replies were recorded, and an edit like that fits the context to the questions it will be scored on, whether or not anyone means it to. That is how dev gets overfitted, and why a dev score isn't the result to report. Second, the splits ask different things: the test split asks about gross margin, sessions and marketing spend, which no dev question touches. Telling those causes apart would take more questions and repeated runs than this chapter has.

**Working rule:** Choose the set on dev, then score it once on the test split beside the baseline, and report the test number. Write down every change you made to the context after reading a dev result, because each one is a way the dev score can overstate. When dev and test disagree, check what you can measure, such as how close each split sits to your examples, before you explain the gap.

## What goes wrong in production {#layered-context-in-production}

The layers this chapter built raised the shop's dev score a long way above the schema alone. These are the ways the same layers fail once people depend on them, and how you'd notice each one.

**The notes drift away from the marts.** A column note is true about the mart as it was built when someone wrote it. When the analytics engineers change `fct_orders`, for example to drop cancelled orders from the mart, the note that says to filter on `status` becomes wrong, and nothing fails. You notice by keeping the notes in the same repository as the SQL that builds the marts, reviewing them in the same pull requests, and checking in CI that every table and column a note names still exists.

**A value the context never lists.** The model wrote `'tents'` for a category stored as `'Tents'`, and the query ran and returned nothing. Questions name values, such as categories, channels, regions and campaign names, and a model guesses their spelling. You notice by reading the wrong answers whose result is empty or zero. For columns with a few dozen distinct values, list them in the column note. For columns with many, retrieve the values that match the question's words, as you retrieve verified queries.

**A rule stated in context is still ignored.** With the glossary, the model dropped the cancelled-orders filter on `gq-002` and left cancelled orders out of the customer count for `gq-016`. With the column notes, and again with the glossary, it left them out of the order count for `gq-013`. Both go against what the note on `status` and the glossary say. With all four layers, it summed order revenue over order lines on `gq-006`, which the glossary's entry for units sold warns against. Context makes a rule available. It doesn't make the model follow it. You notice only by scoring every change on golden questions, per question. When a rule has to hold every time, move it out of the prompt and into code the model can't skip, which is what chapter 5's semantic layer does.

**Retrieval offers the wrong example.** Lexical retrieval matches words, so a question that shares only "most" with a verified query gets that query as its example unless a threshold stops it, and a question that means the same thing in other words gets nothing. You notice by logging which verified queries each answer was given, as Snowflake's Cortex Analyst reports in its API's `confidence` field which verified query it used ([Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/verified-query-repository)), and reading the logs for answers that went wrong.

**A verified query is mistaken for a verified answer.** A retrieved query guides the model, and the SQL it writes is new SQL that nobody checked. Databricks marks a Genie answer as verified only when the exact text of a parameterized example query is used ([Databricks](https://docs.databricks.com/aws/en/genie-agents/tune-quality)), which is the distinction to keep. Never show an answer as verified because a similar query was. You notice by checking what your interface says about answers that were built from examples.

**Verified queries go stale.** A query checked in October uses the definitions of October. When finance changes a definition, the old queries teach the old rule to every similar question. Keep a `verified_at` date on each query, re-run each against its golden counterpart when a definition changes, and remove queries nobody has checked since the change.

**The context grows until it costs more than it gives.** Each layer is cheap to add, and nobody removes one that stopped helping. On a CPU every prompt token costs time, and with a hosted model it costs money on every call. You notice by recording the tokens of each call with its outcome, as the recordings here do, and by re-running the ablation when a layer grows, so a layer that stops paying for its tokens can go.

**Working rule:** Treat context as code that ships with the warehouse: versioned beside the marts, checked in CI against the tables it names, scored on golden questions with every change, and logged per answer with the verified queries it used. Move any rule that must always hold out of the context and into a definition the model can't skip.

## Decisions this chapter made {#layered-context-decisions}

- **Context comes in four layers:** the whole schema, notes on columns whose names mislead, a business glossary, and verified queries retrieved per question. Each lives in a file under `examples/data/shop/`, and `build_context()` in `lib/context.py` assembles them.
- **The schema is never trimmed** while it fits; the budget applies to the other layers.
- **Verified queries are retrieved lexically,** by TF-IDF over the question's words with numbers, months and region codes masked, at most three, each with a score of at least 0.4. None of them is a golden question, and each names the team that verified it, never a person.
- **The context is rendered stable layers first and the question last,** so the question sits beside its examples and the runner can reuse the shared prefix.
- **Tokens are estimated from characters,** at 3.5 characters a token, which overestimated the model's count on the prompt checked, so a context that fits the estimate should fit the model; check it on your own prompts.
- **Layers are measured by ablation on the dev split's answer questions,** one layer at a time, and the best set is checked once on the test split beside the schema alone.
- **The book keeps all four layers** for the chapters that write SQL, because that set scored best on dev. The glossary stays although it didn't improve the score by itself: the verified-query layer was measured on top of it, and we didn't measure verified queries without it.
