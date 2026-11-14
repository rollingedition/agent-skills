---
title: "Data Governance as Code"
chapter: "Lineage from pipelines"
chapter_id: lineage-from-pipelines
book: data-governance-as-code
edition: 2026.11.27
verified: 2026-11-14
edition_code: 2QX0-VKZT
canonical: https://rollingedition.com/data-governance-as-code/lineage-from-pipelines
license: CC BY 4.0
attribution: "“Lineage from pipelines,” chapter 4 of Data Governance as Code, Edition 2026.11.27, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/lineage-from-pipelines. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Lineage from pipelines

By the end of this chapter you can capture lineage from your pipelines as OpenLineage run events, with column lineage parsed from their SQL, including the columns that only join, filter and group. You'll use the graph those events describe to say what a column change breaks downstream, and to propose classifications for tables nobody has classified. You'll also have checks for the three ways lineage fails in production: events that never arrive, a job that sends none, and a copy of personal data classified as less than personal.

The online learning platform from [chapter 1](#governance-end-to-end) builds its reporting tables with four SQL pipelines over eight source tables. Each pipeline is one `create table ... as select ...` in `examples/pipelines/`, and the book's shared module `lib.pipelines` runs it on DuckDB and writes the result back to the catalog:

- `course_performance` writes `analytics.course_performance`: enrollments, completions, ratings and revenue per course.
- `learner_activity` writes `analytics.learner_activity`: each learner's events and last activity.
- `marketing_audience` writes `marketing.audience`: the learners marketing may email, with their name and email.
- `review_corpus` writes `ai.review_corpus`: the review text the platform's course assistant is grounded on.

[Chapter 2](#a-catalog-you-can-test)'s metadata check found that two of those outputs, `marketing.audience` and `ai.review_corpus`, have no metadata at all: no owner, and no classification for any column. Yet one holds learners' names and emails, and the other holds the free text of reviews, where [chapter 3](#classify-columns-from-their-values) found names and emails too. Two questions follow, and the catalog can't answer either. Which columns of those tables are personal data? And if the CRM team renames or reformats `crm.learners.email`, what breaks? Both are lineage questions: where each column's data came from, and where it goes.

This chapter adds the book's shared module for lineage, `lib.lineage`. It runs each pipeline, tells OpenLineage what the run read and wrote, column by column, and reads the result back as a graph that answers both questions.

## Send a run event from every pipeline {#send-run-events}

OpenLineage, an open specification for lineage, describes it with three objects ([object model](https://openlineage.io/docs/spec/object-model)). A **job** is "a process that consumes or produces Datasets", such as a pipeline. A **run** is one occurrence of a job, identified by a UUID the client generates, and the spec recommends UUIDv7. A **dataset** is a table or file, named by a namespace and a name that together identify it. A run reports itself through **run events**: a START when it begins, then one terminal event, COMPLETE, FAIL or ABORT, and a server treats the events for one run as accumulating ([run cycle](https://openlineage.io/docs/spec/run-cycle)). Lineage comes mostly from the work itself: a backend learns about datasets mainly from information about jobs.

The Python client, openlineage-python 1.55.0, builds events from `RunEvent`, `Run`, `Job`, `InputDataset` and `OutputDataset` in `openlineage.client.event_v2`, and sends them through a transport ([client docs](https://openlineage.io/docs/client/python)). It ships HTTP and Kafka transports for servers, and a file transport "designed mainly for integration testing", which with `append` set writes one JSON event per line to a single file ([configuration](https://openlineage.io/docs/client/python/configuration)). The client computes no lineage. It serializes what the caller passes in and adds only metadata of its own: a run facet with its version, the job's source location when it runs in a Git checkout, and any environment variables you configure it to collect (`emit` in `client/client.py`, [openlineage-python](https://pypi.org/project/openlineage-python/1.54.0/)). This means the lineage that reaches a server is the lineage your code put in the event.

`lib.lineage.run` wraps `lib.pipelines.run`, which runs one of the platform's four SQL pipelines and writes its table to the catalog. It sends START with the tables the SQL reads as inputs, runs the pipeline, and then sends COMPLETE with the output dataset and two facets on it. A **facet** is OpenLineage's name for a block of metadata attached to a run, a job or a dataset, and these two hold the output's schema and its column lineage, which the [next section](#trace-output-columns) builds. If the pipeline raises, it sends FAIL instead, and `lib.lineage.run_all` runs all four pipelines this way, into one events file. The datasets need a namespace, and OpenLineage's [naming conventions](https://openlineage.io/docs/spec/naming) have no entry for an Iceberg table in a local SQL catalog. The nearest is the local file system, named by its path, which would put a folder on your machine into every event. Hence `lib.lineage` uses the placeholder `iceberg://platform`, with the catalog's identifiers, such as `crm.learners`, as names.

The examples need the same bytes every time, yet an event's time and random run ID change by default. Here `lib.lineage` stamps every event with the nominal start of the nightly run on the book's "today", and derives the run ID with the client's `generate_static_uuid`, which, its docstring says, "always produces the same result" for the same time and data: here, the job's name. Run the four pipelines with lineage twice, into two files, and print what the first file's events say, not the raw JSON:

Example `pipeline-run-events` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""Runs the four pipelines with lineage twice, into two files, and reads back what the first file's events say. The
prose rests on the counts of events and run IDs, on the run facet the client adds, and on the same-bytes check, which
the example asserts."""

from openlineage.client.uuid import generate_new_uuid, generate_static_uuid

from lib import lineage
from lib.catalog import open_catalog
from lib.platform import scratch

folder = scratch()
catalog = open_catalog()
lineage.run_all(catalog, folder / "first.jsonl")
lineage.run_all(catalog, folder / "second.jsonl")          # the same nightly run, sent again
# lib.lineage fixes the event time and derives the run IDs
assert (folder / "first.jsonl").read_bytes() == (folder / "second.jsonl").read_bytes()
events = lineage.read_events(folder / "first.jsonl")

print("events:", len(events))
for event in events:
    job, state = event["job"]["name"], event["eventType"]
    if state == "START":
        print(f"{job} START, reads:", ", ".join(dataset["name"] for dataset in event["inputs"]))
    else:
        output = event["outputs"][0]
        lineage_fields = output["facets"]["columnLineage"]["fields"]
        print(f"{job} {state}, writes:", output["name"], f"({len(lineage_fields)} columns with lineage)")

print("event times:", ", ".join(sorted({event["eventTime"] for event in events})))
print("distinct run IDs:", len({event["run"]["runId"] for event in events}))
print("run facets the client added:", ", ".join(events[0]["run"]["facets"]))
print("same bytes when sent again:", (folder / "first.jsonl").read_bytes() == (folder / "second.jsonl").read_bytes())
# generate_new_uuid draws a random UUID each time; generate_static_uuid derives one from its arguments.
print("two random run IDs equal:", generate_new_uuid() == generate_new_uuid())
print("two static run IDs equal:", generate_static_uuid(lineage.NIGHTLY, b"marketing_audience")
      == generate_static_uuid(lineage.NIGHTLY, b"marketing_audience"))
```

Output:

```text
events: 8
course_performance START, reads: billing.payments, learning.courses, learning.enrollments, learning.reviews
course_performance COMPLETE, writes: analytics.course_performance (7 columns with lineage)
learner_activity START, reads: crm.learners, learning.events
learner_activity COMPLETE, writes: analytics.learner_activity (6 columns with lineage)
marketing_audience START, reads: crm.learners, learning.courses, learning.enrollments
marketing_audience COMPLETE, writes: marketing.audience (5 columns with lineage)
review_corpus START, reads: learning.courses, learning.reviews
review_corpus COMPLETE, writes: ai.review_corpus (5 columns with lineage)
event times: 2026-10-01T02:00:00+00:00
distinct run IDs: 4
run facets the client added: tags
same bytes when sent again: True
two random run IDs equal: False
two static run IDs equal: True
```

Sending the same nominal run again wrote the same bytes, as random run IDs never would, and the example asserts it. The first file holds 8 events, a START and a COMPLETE for each of 4 runs, all stamped `2026-10-01T02:00:00+00:00`. The `marketing_audience` job's START names the tables its SQL reads, `crm.learners`, `learning.courses` and `learning.enrollments`, and its COMPLETE names `marketing.audience`, with lineage for each column. Yet the events hold something you didn't put there: a run facet named `tags`, carrying the client's own version ([changelog, 1.38.0](https://github.com/OpenLineage/OpenLineage/blob/main/CHANGELOG.md)), and every facet's `_producer` URL names that version too (`DEFAULT_PRODUCER` in `client/constants.py`). So the bytes change with each client release, though the lineage doesn't, and a test should compare what events say, as this example's summary does.

A production emitter stamps COMPLETE with the time the run finished. A derived run ID is still worth keeping there, made from the scheduled time, the job's name and the attempt number: an event sent twice then lands in the same run instead of creating a second one, and a retried job gets a run of its own. Production events should also carry the output's Iceberg snapshot ID, in the `version` dataset facet the [object model](https://openlineage.io/docs/spec/object-model) names for it. The code here leaves it out, because PyIceberg 0.12.0 draws each snapshot ID from a random UUID (`_generate_snapshot_id` in its `pyiceberg/table/metadata.py`).

**Working rule:** Send a START and then a COMPLETE or FAIL event from the code that runs each job, so no run can happen without them, and name datasets by catalog identifiers under a namespace you choose, never a path. In tests, use the file transport with a fixed event time and static run IDs, and compare what events say, never their bytes. In production, send through a transport to your lineage server, and derive each run ID from the scheduled time, the job and the attempt, so a resent event never creates a duplicate run.

## Trace each output column to its sources {#trace-output-columns}

A [run event](#send-run-events) says which tables a job read and wrote. Column lineage says which input columns each output column came from, and that is what governance needs: a table that reads `crm.learners` may or may not copy its emails. OpenLineage puts column lineage in a dataset facet, `columnLineage`, on the output: `fields` maps each output column to its `inputFields`, and an optional `dataset` list holds inputs that affect the whole dataset ([facet schema](https://openlineage.io/spec/facets/1-2-0/ColumnLineageDatasetFacet.json)). Since the client computes none of it, something has to parse each job's SQL.

sqlglot, a SQL parser, does it with `sqlglot.lineage.lineage`. Given a statement and the schema of the tables it reads, it returns, for each output column, a tree whose leaves are source columns, and with `column=None` it returns every output column at once ([sqlglot lineage](https://sqlglot.com/sqlglot/lineage.html)). It needs the schema. Without one, `SELECT *` comes back as a single output named `*`, and an unqualified column in a join as a placeholder with no table. `lib.lineage.schema` builds the schema from the catalog's Iceberg metadata, so the parser sees the columns the warehouse has, at sqlglot 30.31.0.

Start with `marketing_audience`, which feeds the list marketing may email. In words, it picks learners who agreed to marketing email and whose account is active, and adds each one's favourite course category, which a CTE computes by ranking categories by the learner's enrollments. Ask sqlglot for the lineage of the pipeline's outputs and of two `course_performance` columns, to see what it leaves out:

Example `sqlglot-misses-row-inputs` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""What sqlglot.lineage says the pipeline outputs come from, and what it leaves out. The prose rests on the CTE-traced
source of favourite_category, on the sources of the two course performance columns, and on the assertion that neither
column the WHERE reads reaches any output."""
import sqlglot
from sqlglot import exp

from lib import lineage, pipelines
from lib.catalog import open_catalog

# sqlglot resolves each name against the catalog's columns, so lineage.schema builds them from the table metadata.
schema = lineage.schema(open_catalog(["crm.learners", "learning.courses", "learning.enrollments", "learning.reviews",
                                      "billing.payments"]))
statement = pipelines.sql("marketing_audience")
found = lineage.sqlglot_sources(statement, schema)
for column, sources in found.items():
    print(f"marketing.audience.{column} comes from:", ", ".join(sources))

parsed = sqlglot.parse_one(statement, read="duckdb")
# the WHERE names columns by alias, as in l.status, so each alias maps to its table
tables = {table.alias_or_name: f"{table.db}.{table.name}" for table in parsed.find_all(exp.Table)}
where = parsed.find(exp.Where)
print("the pipeline's WHERE:", where.this.sql(dialect="duckdb"))
in_lineage = {source for sources in found.values() for source in sources}     # every source column of every output
for column in where.find_all(exp.Column):
    source = f"{tables[column.table]}.{column.name}"
    assert source not in in_lineage        # every column the WHERE reads, checked against the lineage above
    print(f"{source} in any column's lineage:", source in in_lineage)

course_performance = lineage.sqlglot_sources(pipelines.sql("course_performance"), schema)
for column in ("completions", "revenue_usd"):    # the two aggregates that carry a FILTER inside them
    print(f"analytics.course_performance.{column} comes from:", ", ".join(course_performance[column]))
```

Output:

```text
marketing.audience.learner_id comes from: crm.learners.learner_id
marketing.audience.full_name comes from: crm.learners.full_name
marketing.audience.email comes from: crm.learners.email
marketing.audience.country comes from: crm.learners.country
marketing.audience.favourite_category comes from: learning.courses.category
the pipeline's WHERE: l.marketing_consent AND l.status = 'active'
crm.learners.marketing_consent in any column's lineage: False
crm.learners.status in any column's lineage: False
analytics.course_performance.completions comes from: learning.enrollments.completed_at, learning.enrollments.enrollment_id
analytics.course_performance.revenue_usd comes from: billing.payments.amount, billing.payments.status
```

The values are right, but what decides which learners are in the table is missing. `email` comes from `crm.learners.email`, and `favourite_category` is traced through the CTE to `learning.courses.category`. The pipeline's `WHERE` is `l.marketing_consent AND l.status = 'active'`, and neither of its columns, `marketing_consent` or `status`, is in any output's lineage. The example asserts both. The consent filter is the reason marketing may hold this table at all, and the lineage doesn't mention it. Nor does it mention the join keys from enrollments and courses.

The second problem is the reverse: an input that only filters is listed as if it were a value. `course_performance` sums only succeeded payments, with `filter (where p.status = 'succeeded')`, and sqlglot says `revenue_usd` comes from `billing.payments.amount, billing.payments.status`: the column summed and the column that only decides which payments count, listed alike. `completions` counts enrollments with `filter (where e.completed_at is not null)`, and comes back the same way, from `learning.enrollments.completed_at, learning.enrollments.enrollment_id`. Both problems follow from how sqlglot builds the tree. It collects the columns in each output's expression, so it sees a filter inside an expression and nothing outside it, and its nodes carry no type to say how an input was used.

**Working rule:** Use sqlglot's `lineage` for the columns each output's value is computed from, and always pass the catalog's schema, generated from the table metadata, never typed. Don't read its answer as everything a column depends on: it misses the columns that join, filter and group, and it doesn't say which of its inputs are values.

## Add the inputs that decide which rows exist {#add-indirect-inputs}

[sqlglot's lineage](#trace-output-columns) lists the columns a value is computed from, and OpenLineage has a place for the rest. Each input field carries a list of transformations, each with a type, a subtype and a `masking` flag ([column lineage facet](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet)). DIRECT means the output value is derived from the input value, through IDENTITY, TRANSFORMATION or AGGREGATION. INDIRECT means the output value is impacted by an input without being derived from it, through JOIN, GROUP_BY, FILTER, SORT, WINDOW or CONDITIONAL. Inputs that shape every row, such as a `WHERE`, belong in the facet's `dataset` list.

For governance, the INDIRECT side matters, since information flows through conditions as well as values. Denning calls it "implicit flow": a statement that assigns only when a condition holds still tells you the condition's value ([Denning, 1976](https://doi.org/10.1145/360051.360056)). A row in `marketing.audience` tells you that learner consented.

`lib.lineage.column_lineage` adds two things sqlglot's answer lacks: a type for each value input, and the INDIRECT inputs. It types each value input by where the column sits in the output's expression: a bare column is IDENTITY, a column inside an aggregate is AGGREGATION, and anything else is TRANSFORMATION. A column inside an aggregate's `FILTER`, a window's `PARTITION BY` or `ORDER BY`, or a `CASE`'s condition or operand is INDIRECT, and a hash on the way sets `masking`. `COALESCE`'s arguments count as values: OpenLineage lists `COALESCE` under CONDITIONAL, but any of its arguments can become the output's value. Then it walks every `SELECT` in the statement, CTEs included, and collects the columns of its row clauses, following CTE columns back to the tables they come from:

```python
ROW_CLAUSES = {"joins": "JOIN", "where": "FILTER", "group": "GROUP_BY", "having": "FILTER", "qualify": "FILTER",
               "order": "SORT"}
```

Run it on the same pipeline and the same two columns:

Example `indirect-column-lineage` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""The book's column lineage for the marketing audience pipeline and two course performance columns: each input,
with its OpenLineage type and subtype, then the inputs that shape every row. The prose rests on the source counts."""
from lib import lineage, pipelines
from lib.catalog import open_catalog

schema = lineage.schema(open_catalog(["crm.learners", "learning.courses", "learning.enrollments", "learning.reviews",
                                      "billing.payments"]))
# rows holds the inputs that shape every row, which OpenLineage keeps in the dataset list
fields, rows = lineage.column_lineage(pipelines.sql("marketing_audience"), schema)
for column, inputs in fields.items():
    print(f"marketing.audience.{column}:", ", ".join(f"{dependency.source} {dependency.type} {dependency.subtype}"
                                                    for dependency in inputs))
print("inputs that shape every row of marketing.audience:")
for source in sorted({dependency.source for dependency in rows}):
    print(f"  {source}:", "INDIRECT",
          ", ".join(dependency.subtype for dependency in rows if dependency.source == source))

# the source columns that the output values are computed from
values = {dependency.source for inputs in fields.values() for dependency in inputs}
print("source columns, values only:", len(values))
# A column can both give a value and shape the rows, so the union counts it once.
print("source columns, with the rows' inputs:", len(values | {dependency.source for dependency in rows}))

fields, _ = lineage.column_lineage(pipelines.sql("course_performance"), schema)   # only these two columns are printed
for column in ("completions", "revenue_usd"):
    print(f"analytics.course_performance.{column}:",
          ", ".join(f"{dependency.source} {dependency.type} {dependency.subtype}" for dependency in fields[column]))
```

Output:

```text
marketing.audience.learner_id: crm.learners.learner_id DIRECT IDENTITY
marketing.audience.full_name: crm.learners.full_name DIRECT IDENTITY
marketing.audience.email: crm.learners.email DIRECT IDENTITY
marketing.audience.country: crm.learners.country DIRECT IDENTITY
marketing.audience.favourite_category: learning.courses.category DIRECT IDENTITY
inputs that shape every row of marketing.audience:
  crm.learners.learner_id: INDIRECT JOIN
  crm.learners.marketing_consent: INDIRECT FILTER
  crm.learners.status: INDIRECT FILTER
  learning.courses.category: INDIRECT GROUP_BY, JOIN
  learning.courses.course_id: INDIRECT JOIN
  learning.enrollments.course_id: INDIRECT JOIN
  learning.enrollments.learner_id: INDIRECT GROUP_BY, JOIN
source columns, values only: 5
source columns, with the rows' inputs: 10
analytics.course_performance.completions: learning.enrollments.completed_at INDIRECT FILTER, learning.enrollments.enrollment_id DIRECT AGGREGATION
analytics.course_performance.revenue_usd: billing.payments.amount DIRECT AGGREGATION, billing.payments.status INDIRECT FILTER
```

The values match [sqlglot's](#trace-output-columns), each an IDENTITY copy, and the rows' inputs are the new part. Adding them grows what `marketing.audience` depends on from 5 source columns to 10. Some row inputs are columns no value uses: `marketing_consent` and `status` as FILTER, the two course IDs as JOIN, and the enrollments' `learner_id` as GROUP_BY and JOIN. `crm.learners.learner_id` and `learning.courses.category`, which values copy too, also shape rows: the ID as JOIN, the category as GROUP_BY and JOIN. For `revenue_usd`, the two inputs are now told apart: `amount` is a DIRECT AGGREGATION, and `status` an INDIRECT FILTER. So are the two inputs of `completions`: `enrollment_id` is counted, and `completed_at` only filters.

One more detail: the per-field `transformationType` and `transformationDescription` are deprecated, replaced by the per-input `transformations` that `lib.lineage` writes ([changelog, 1.17.1](https://github.com/OpenLineage/OpenLineage/blob/main/CHANGELOG.md)). And OpenLineage 1.53.0 added a Lineage dataset facet for declared lineage, such as a view's, sent on a `DatasetEvent`, which consumers should prefer where both describe the same relationship ([lineage facet](https://openlineage.io/docs/spec/facets/dataset-facets/lineage)). Run events from jobs carry `columnLineage`, as the platform's do.

**Working rule:** Record INDIRECT inputs with every job's column lineage: the join keys, filters and grouping columns of every `SELECT`, CTEs included, in the facet's `dataset` list, and type each value input with OpenLineage's subtypes. Expect more edges, many of them join keys. Keep them anyway: a filter on a consent column decides who may be emailed, and it reaches the table only as an INDIRECT input.

## Fail on statements the parser can't read {#fail-on-unreadable-lineage}

The platform's [column lineage](#add-indirect-inputs) is only as good as the parse behind it, and a parse can be wrong without failing. sqlglot's `lineage` accepts more than a `SELECT`: it finds the query inside a `CREATE TABLE ... AS`, an `INSERT ... SELECT` or a `CREATE VIEW`, and it reads a `MERGE` too ([sqlglot](https://pypi.org/project/sqlglot/30.24.0/), `optimizer/scope.py`). Three cases come back looking fine. An `INSERT`'s outputs are named after its `SELECT`, never after the table's columns. A `MERGE` comes back as the last query sqlglot reaches in it, as if that query were what the `MERGE` writes. When `USING` names a table or a CTE and no subquery follows, sqlglot returns no lineage and no error. When `USING` is a subquery, or a subquery sits in a `WHEN` condition or a `SET`, it returns the columns of the last such subquery, whether the `MERGE` writes them or not. And a misspelt column gets through when it's unqualified in a query on one table: sqlglot assigns it to that table whether the table has the column or not.

All four of the platform's pipelines are `CREATE TABLE ... AS` statements. As tables grow, pipelines like these often become incremental: an `INSERT` that appends a day's revenue to `analytics.daily_revenue`, or a `MERGE` that updates `analytics.learner_activity` in place. Ask sqlglot and `lib.lineage.column_lineage` about each, the `INSERT` and the `MERGE` in two forms, and compare the answers:

Example `insert-and-merge-lineage` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""sqlglot.lineage's answers for an INSERT and for two MERGE statements, beside the book's lineage: sqlglot names the
INSERT's outputs after its SELECT, and returns nothing or a subquery's columns for a MERGE, which the book refuses. The
prose rests on the sqlglot outputs and on the refusals at the end."""
import pyarrow as pa
from sqlglot.lineage import lineage as sqlglot_lineage

from lib import lineage
from lib.catalog import open_catalog

catalog = open_catalog(["billing.payments", "crm.learners"])
catalog.create_namespace("analytics")             # the incremental table, as it exists before the day's INSERT
catalog.create_table("analytics.daily_revenue", schema=pa.schema([("day", pa.date32()), ("revenue_usd", pa.float64())]))
schema = lineage.schema(catalog)
insert = """insert into analytics.daily_revenue
select cast(p.paid_at as date), sum(p.amount) from billing.payments p where p.status = 'succeeded' group by 1"""
merges = {"USING a table": """merge into analytics.learner_activity a using crm.learners l
on a.learner_id = l.learner_id when matched then update set country = l.country""",
          "USING a subquery": """merge into analytics.learner_activity a
using (select l.learner_id, l.country, l.email from crm.learners l) s on a.learner_id = s.learner_id
when not matched then insert (learner_id, country) values (s.learner_id, s.country)"""}

print("analytics.daily_revenue columns:", ", ".join(schema["analytics"]["daily_revenue"]))
# The SELECT's expressions have no aliases, so sqlglot names each output after the SELECT, not the table. None asks for
# every output column at once.
print("sqlglot, INSERT outputs:", ", ".join(sqlglot_lineage(None, insert, schema, dialect="duckdb")))
fields, rows = lineage.column_lineage(insert, schema)
for column, inputs in fields.items():
    print(f"book, INSERT {column}:", ", ".join(f"{dependency.source} {dependency.type} {dependency.subtype}"
                                               for dependency in inputs))
print("book, INSERT rows shaped by:", ", ".join(f"{dependency.source} {dependency.subtype}" for dependency in rows))
for label, merge in merges.items():
    outputs = sqlglot_lineage(None, merge, schema, dialect="duckdb")
    print(f"sqlglot, MERGE {label}, outputs:", ", ".join(outputs) or "none")

# One value too many for daily_revenue's two columns, caught after sqlglot parses it; each MERGE is refused before sqlglot is asked.
refused = {"INSERT with one value too many": insert.replace("sum(p.amount)", "sum(p.amount), count(*)"),
           **{f"MERGE {label}": merge for label, merge in merges.items()}}
for label, statement in refused.items():
    try:
        lineage.column_lineage(statement, schema)
    except lineage.LineageError as error:
        print(f"book, {label}:", error)
```

Output:

```text
analytics.daily_revenue columns: day, revenue_usd
sqlglot, INSERT outputs: paid_at, _col_1
book, INSERT day: billing.payments.paid_at DIRECT TRANSFORMATION
book, INSERT revenue_usd: billing.payments.amount DIRECT AGGREGATION
book, INSERT rows shaped by: billing.payments.paid_at GROUP_BY, billing.payments.status FILTER
sqlglot, MERGE USING a table, outputs: none
sqlglot, MERGE USING a subquery, outputs: learner_id, country, email
book, INSERT with one value too many: analytics.daily_revenue: the INSERT writes 2 columns, and its SELECT has 3 values
book, MERGE USING a table: analytics.learner_activity: lineage is read only from CREATE ... AS and INSERT ... SELECT, not from MERGE
book, MERGE USING a subquery: analytics.learner_activity: lineage is read only from CREATE ... AS and INSERT ... SELECT, not from MERGE
```

The table `analytics.daily_revenue` has the columns `day, revenue_usd`, yet sqlglot names the `INSERT`'s outputs `paid_at, _col_1`: the first after the column inside the `cast`, the second a generated name for an expression with no alias.

An `INSERT` fills columns by position, so `lib.lineage` matches by position too, taking the names from the catalog: the columns the `INSERT` lists, or else all of the table's. So `day` comes from `billing.payments.paid_at DIRECT TRANSFORMATION`, and the `INSERT`'s grouping and its filter on `status` shape every row: `billing.payments.paid_at GROUP_BY, billing.payments.status FILTER`. When the `SELECT` has more or fewer values than the columns written, `lib.lineage` raises: `analytics.daily_revenue: the INSERT writes 2 columns, and its SELECT has 3 values`.

For the `MERGE` whose `USING` names a table, sqlglot returns none, and no error. For the one whose `USING` is a subquery, it returns `learner_id, country, email`, though that `MERGE` writes only `learner_id` and `country`. A check for empty lineage catches the first and passes the second, so `lib.lineage` doesn't judge what sqlglot returns for a `MERGE`. Before it calls sqlglot, it refuses every statement that isn't a `CREATE ... AS` or an `INSERT ... SELECT`: `analytics.learner_activity: lineage is read only from CREATE ... AS and INSERT ... SELECT, not from MERGE`.

A misspelt column, the third case, depends on how the column is written. The platform's pipelines qualify every column with its table's alias, as in `l.email`, and sqlglot checks a qualified column against the schema itself:

Example `misspelt-column-lineage` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""A misspelt column, emial for email, in a query on one table: sqlglot raises when the column is qualified by its
alias, and traces it to the table when it isn't. The prose rests on the sqlglot answer for each form, and on the book's
check against the schema."""
from sqlglot.errors import OptimizeError

from lib import lineage
from lib.catalog import open_catalog

schema = lineage.schema(open_catalog(["crm.learners"]))    # the schema lets sqlglot check each column name
# the alias l is right, and only the column name is misspelt
qualified = "create table marketing.audience as select l.learner_id, l.emial from crm.learners l"
# no alias, so nothing names the table the column comes from
unqualified = "create table marketing.audience as select learner_id, emial from crm.learners"

try:
    lineage.sqlglot_sources(qualified, schema)
except OptimizeError as error:
    print("sqlglot, qualified l.emial:", f"{type(error).__name__}: {error}")
print("sqlglot, unqualified emial comes from:", ", ".join(lineage.sqlglot_sources(unqualified, schema)["emial"]))
try:
    lineage.column_lineage(unqualified, schema)
except lineage.LineageError as error:
    print("book, unqualified emial:", error)
```

Output:

```text
sqlglot, qualified l.emial: OptimizeError: Unknown column: emial
sqlglot, unqualified emial comes from: crm.learners.emial
book, unqualified emial: crm.learners has no column emial
```

A qualified typo stops sqlglot with `OptimizeError: Unknown column: emial`. An unqualified one, in a query on one table, comes back as `crm.learners.emial`: a confident answer about a column that doesn't exist. In a join, a misspelt unqualified column belongs to none of the tables, and sqlglot returns a placeholder with no table ([sqlglot](https://pypi.org/project/sqlglot/30.24.0/), `lineage.py`), which `lib.lineage` rejects as a source it can't place. For the single-table case, `lib.lineage` checks every source against the schema and raises `crm.learners has no column emial`.

`lib.lineage.record`, which `run` uses, reads the lineage before the job runs, so a pipeline whose lineage can't be read fails before it writes anything. That is strict, and deliberate: a job with empty lineage would vanish from every impact report and classification check in this chapter, and one with wrong lineage would mislead them. Run the same check in CI on every pull request that changes a pipeline, so the failure shows up in review rather than at night.

**Working rule:** Treat a statement your parser can't read correctly as an error, never as empty or partial lineage. Refuse every kind of statement it gets wrong, such as `MERGE`, before you ask it, and fail on empty lineage, a source the parser can't place and a column the schema doesn't have. Match an `INSERT`'s columns by position against the table's columns in the catalog, never the `SELECT`'s names, and fail when the counts differ. For a `MERGE`, write a `SELECT` of the columns it writes, and record the job's lineage from that, as an `INSERT ... SELECT` into the `MERGE`'s table, until your parser handles `MERGE` itself.

## Find what a column change breaks {#impact-of-a-column-change}

With [column lineage](#add-indirect-inputs) in every COMPLETE event, the platform has a graph: columns are nodes, and each input field is an edge to the column or table it feeds. **Impact analysis** asks what a change to one column can break. It walks that graph from the column, following every edge out of it and continuing from wherever each lands, at any depth. No special method is needed; it's graph reachability. One rule is specific to lineage. An INDIRECT edge into a table means every row of it can change, so the walk continues from all of that table's columns.

`lib.lineage.graph` builds the graph from the events file alone, as a lineage server would, not from the SQL. Thus it includes every job that sends events, whatever it's written in, and nothing that doesn't. `lib.lineage.downstream` does the walk.

Take three changes the platform's teams might make. The CRM team lowercases every email, or renames `crm.learners.email`. A new sign-up flow changes what `crm.learners.marketing_consent` means for older accounts. The learning team renames a category in `learning.courses`. Make a guess first: how many columns can the consent change reach?

Example `column-impact` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""What a change to one source column can break, walked over the column graph that the nightly run's events describe.
The prose rests on the reach counts printed for each column: through values, and in all."""

from lib import lineage
from lib.catalog import open_catalog
from lib.platform import scratch

events_file = scratch() / "events.jsonl"
lineage.run_all(open_catalog(), events_file)
graph = lineage.graph(lineage.read_events(events_file))    # built from the events alone, as a lineage server would
print("edges in the column graph:", len(graph.edges))

for column in ("crm.learners.email", "crm.learners.marketing_consent", "learning.courses.category"):
    reached = lineage.downstream(graph, column)
    print(f"{column} reaches:")
    # dict.fromkeys drops repeated targets and keeps the order they were found in
    for target in dict.fromkeys(edge.target for edge in reached):
        how = ", ".join(f"{edge.type} {edge.subtype}" for edge in reached if edge.target == target)
        # a table's name has one dot and a column's two, so a table target means every row of it
        print(f"  {target}{', every row' if target.count('.') == 1 else ''}:", how)
    values = [edge for edge in reached if edge.type == "DIRECT"]    # only DIRECT edges copy values
    print(f"{column}, columns reached through values:", len(lineage.columns_reached(graph, values)))
    print(f"{column}, columns reached in all:", len(lineage.columns_reached(graph, reached)))
```

Output:

```text
edges in the column graph: 51
crm.learners.email reaches:
  marketing.audience.email: DIRECT IDENTITY
crm.learners.email, columns reached through values: 1
crm.learners.email, columns reached in all: 1
crm.learners.marketing_consent reaches:
  marketing.audience, every row: INDIRECT FILTER
crm.learners.marketing_consent, columns reached through values: 0
crm.learners.marketing_consent, columns reached in all: 5
learning.courses.category reaches:
  analytics.course_performance, every row: INDIRECT GROUP_BY
  analytics.course_performance.category: DIRECT IDENTITY
  marketing.audience, every row: INDIRECT GROUP_BY, INDIRECT JOIN
  marketing.audience.favourite_category: DIRECT IDENTITY
learning.courses.category, columns reached through values: 2
learning.courses.category, columns reached in all: 12
```

Consent is the surprise. A change to it reaches 0 columns through values, yet through its filter it reaches all 5 columns of `marketing.audience`, because it changes who gets emailed. A values-only lineage tool would report a change to consent as having no impact.

A change to `email` reaches 1 column, `marketing.audience.email`, so renaming it breaks the marketing pipeline and no other job that sends lineage. A category rename reaches 2 columns through values, and 12 in all, because categories also group `analytics.course_performance` and rank each learner's favourite.

The same walk serves two later chapters: [chapter 7](#plan-erasure-from-lineage) follows a learner's columns downstream to find every derived table an erasure must reach, and [chapter 10](#report-what-a-schema-change-reaches) writes an impact report for every pull request that changes a schema.

**Working rule:** Run impact analysis on the graph built from events, INDIRECT edges included, and report two lists: columns whose values can change, and tables whose rows can change. Treat a change to a column used only in filters and joins as a change to every column of the tables it filters, and send the report to the owners of each table it reaches.

## Propose classifications from lineage {#classifications-from-lineage}

A derived column holds data from its inputs, so its classification can be derived from theirs. The classic rule comes from Denning's lattice model of information flow: the class of a value computed from several inputs is the least upper bound, the "join", of their classes ([Denning, 1976](https://doi.org/10.1145/360051.360056)). The platform's classifications form a line, `public`, `internal`, `personal` and `sensitive`, so the join is the stricter of them, which `stricter` in `lib.metadata`, the book's metadata module, returns. Which inputs count is a judgement. We count INDIRECT inputs too, following Denning's implicit flows, because a table filtered on consent reveals each learner's consent. That choice lives in `governance/lineage.toml`, so a team can change it in one reviewed line.

Two more choices follow from the same caution. OpenLineage's `masking` flag says only that a value was obfuscated, such as by a hash ([column lineage facet](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet)). Whether a hashed identifier is still personal data is a legal question: [chapter 2](#classify-pseudonymous-ids) quotes the GDPR recital on pseudonymized data and leaves the answer to lawyers. So the book's rule never lowers a classification because of masking. Catalog servers leave the choice to configuration too. Apache Atlas propagates classifications along lineage, and can block that on an edge, for example where a view masks a PII column ([Atlas](https://atlas.apache.org/1.0.0/ClassificationPropagation.html)). DataHub propagates glossary terms along column lineage, a feature its 1.7.0 documentation calls a public beta in DataHub Cloud ([DataHub](https://docs.datahub.com/docs/automations/glossary-term-propagation)). A proposal is a floor, not a verdict: like the drafts a local model writes in [chapter 2](#draft-descriptions-with-a-local-model), it's reviewed before it goes into `governance/metadata.toml`, the platform's file of owners and classifications.

`lib.lineage.propose` proposes a classification for every column a job wrote, and `lib.metadata.problems` lists the tables that need one. Check the rule on the two tables people did classify, `analytics.course_performance` and `analytics.learner_activity`, before you trust it on `marketing.audience` and `ai.review_corpus`, the two with no metadata:

Example `propagate-classifications` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""Proposes classifications from lineage for the columns with no declared one, then checks the rule against the columns
people did classify. The prose rests on the personal count, on the reproduced counts, and on the check that no declared class is lower."""

from lib import lineage, metadata
from lib.catalog import open_catalog
from lib.platform import scratch

catalog = open_catalog()
events_file = scratch() / "events.jsonl"
lineage.run_all(catalog, events_file)
for problem in metadata.problems(catalog, metadata.load()):
    print("metadata problem:", problem)

graph, known = lineage.graph(lineage.read_events(events_file)), lineage.declared()   # known: governance/metadata.toml
print("propagated through:", " and ".join(lineage.rules()["propagate_through"]))      # from governance/lineage.toml
proposed = lineage.propose(graph, known)
for column, (classification, decided_by) in proposed.items():
    if column not in known:
        first = decided_by[0]      # lib sorts the deciding edges DIRECT first, so this is a value when one decides
        print(f"{column}: {classification}, from {first.source} ({first.type} {first.subtype})")
print("personal columns proposed:", sum(1 for column, (classification, _) in proposed.items()
                                        if column not in known and classification == "personal"))

classified = [column for column in proposed if column in known]
print("declared classifications checked:", len(classified))
print("classes declared for them:", ", ".join(sorted({known[column] for column in classified})))
for through in (["DIRECT", "INDIRECT"], ["DIRECT"]):
    proposals = lineage.propose(graph, known, through)
    agree = sum(1 for column in classified if proposals[column][0] == known[column])
    print(f"declared classifications reproduced, through {' and '.join(through)}:", f"{agree} of {len(classified)}")
# proposals is the DIRECT-only run from the loop above
missed = [column for column in classified if proposals[column][0] != known[column]]
print("missed with DIRECT inputs only:", len(missed))
for column in missed:
    print(f"  {column}: declared {known[column]}, DIRECT inputs propose {proposals[column][0]}")
print("declared less protected than lineage proposes:", len(lineage.understated(proposed, known)))
assert not lineage.understated(proposed, known)
```

Output:

```text
metadata problem: ai.review_corpus: no metadata
metadata problem: marketing.audience: no metadata
propagated through: DIRECT and INDIRECT
marketing.audience.learner_id: internal, from crm.learners.learner_id (DIRECT IDENTITY)
marketing.audience.full_name: personal, from crm.learners.full_name (DIRECT IDENTITY)
marketing.audience.email: personal, from crm.learners.email (DIRECT IDENTITY)
marketing.audience.country: internal, from crm.learners.country (DIRECT IDENTITY)
marketing.audience.favourite_category: internal, from crm.learners.learner_id (INDIRECT JOIN)
ai.review_corpus.review_id: internal, from learning.reviews.review_id (DIRECT IDENTITY)
ai.review_corpus.course_id: internal, from learning.reviews.course_id (DIRECT IDENTITY)
ai.review_corpus.course_title: internal, from learning.reviews.course_id (INDIRECT JOIN)
ai.review_corpus.rating: internal, from learning.reviews.rating (DIRECT IDENTITY)
ai.review_corpus.body: personal, from learning.reviews.body (DIRECT IDENTITY)
personal columns proposed: 3
declared classifications checked: 13
classes declared for them: internal
declared classifications reproduced, through DIRECT and INDIRECT: 13 of 13
declared classifications reproduced, through DIRECT: 10 of 13
missed with DIRECT inputs only: 3
  analytics.course_performance.course_id: declared internal, DIRECT inputs propose public
  analytics.course_performance.title: declared internal, DIRECT inputs propose public
  analytics.course_performance.category: declared internal, DIRECT inputs propose public
declared less protected than lineage proposes: 0
```

The metadata check from [chapter 2](#test-the-catalog-against-the-metadata) still reports the two tables with no metadata, and lineage proposes a classification for each of their columns. It proposes 3 personal columns: `full_name` and `email` in `marketing.audience`, each an IDENTITY copy of a personal column in `crm.learners`, and `body` in `ai.review_corpus`, a copy of the reviews' free text. The rest come out internal, including `favourite_category`, for which the example prints `internal, from crm.learners.learner_id (INDIRECT JOIN)`. Its values are public course-catalog category names, but the rows they sit in are chosen by a join on learner IDs and a consent filter, so those are internal.

Counting INDIRECT inputs reproduces the declared classifications on the columns people did classify, 13 of 13, and all of them are `internal`.

DIRECT inputs alone reproduce 10 of 13, and miss 3: `course_id`, `title` and `category` of `analytics.course_performance`. A DIRECT-only rule calls them public, as in the course catalog, while the analytics team chose internal. So the rule proposes no less than people chose here, and lineage finds no declared classification lower than its proposal. That is weak evidence: a rule that proposed internal for every column would score as well. And it can't show what the rule does with a personal filter, since none of the platform's filters or joins reads a personal column: even `marketing_consent` is classified internal.

So build a table whose filter does. For a birthday offer, marketing wants the learners who consented and were born this month, with their ID and country, and nothing else:

Example `personal-filter-propagates` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""A birthday-offer table whose only personal input is a filter on date of birth. The prose rests on the learner count,
and on the proposals counting DIRECT inputs alone and counting DIRECT and INDIRECT inputs."""

from lib import lineage
from lib.catalog import open_catalog
from lib.platform import scratch
from lib.warehouse import connect

catalog = open_catalog(["crm.learners"])
# The consenting learners born in the month of the nightly run, on the book's "today".
select = ("select l.learner_id, l.country from crm.learners l "
          f"where l.marketing_consent and month(l.date_of_birth) = {lineage.NIGHTLY.month}")


def offers() -> None:
    rows = connect(catalog).sql(select).to_arrow_table()
    catalog.create_namespace_if_not_exists("marketing")
    catalog.create_table("marketing.birthday_offers", schema=rows.schema).append(rows)


events_file = scratch() / "events.jsonl"
# record derives the lineage from this statement, and reads it before offers() runs
lineage.record(lineage.client(events_file), "birthday_offers", f"create table marketing.birthday_offers as {select}",
               catalog, offers)
offers_table = catalog.load_table("marketing.birthday_offers").scan().to_arrow()
print("learners in marketing.birthday_offers:", f"{len(offers_table):,}")

graph, known = lineage.graph(lineage.read_events(events_file)), lineage.declared()
print("crm.learners.date_of_birth declared:", known["crm.learners.date_of_birth"])
for through in (["DIRECT", "INDIRECT"], ["DIRECT"]):
    for column, (classification, decided_by) in lineage.propose(graph, known, through).items():
        label = f"{column}, through {' and '.join(through)}"
        print(f"{label}:", classification)
        print(f"{label}, decided by:", f"{decided_by[0].source} ({decided_by[0].type} {decided_by[0].subtype})")
```

Output:

```text
learners in marketing.birthday_offers: 165
crm.learners.date_of_birth declared: personal
marketing.birthday_offers.learner_id, through DIRECT and INDIRECT: personal
marketing.birthday_offers.learner_id, through DIRECT and INDIRECT, decided by: crm.learners.date_of_birth (INDIRECT FILTER)
marketing.birthday_offers.country, through DIRECT and INDIRECT: personal
marketing.birthday_offers.country, through DIRECT and INDIRECT, decided by: crm.learners.date_of_birth (INDIRECT FILTER)
marketing.birthday_offers.learner_id, through DIRECT: internal
marketing.birthday_offers.learner_id, through DIRECT, decided by: crm.learners.learner_id (DIRECT IDENTITY)
marketing.birthday_offers.country, through DIRECT: internal
marketing.birthday_offers.country, through DIRECT, decided by: crm.learners.country (DIRECT IDENTITY)
```

Neither column copies anything personal, but every row says its learner was born in the offer's month, part of a date of birth. The table holds 165 learners, and `governance/metadata.toml` classifies the date of birth `personal`. Counting DIRECT inputs alone proposes `internal` for `learner_id` and `internal` for `country`.

Add INDIRECT inputs, and it proposes `personal` for `learner_id` and `personal` for `country`, both decided by `crm.learners.date_of_birth (INDIRECT FILTER)`. That is the case INDIRECT inputs are for, and it shows the cost too: one personal filter makes every column of a table personal.

OpenLineage can carry classifications in the events themselves, with the Tags dataset facet, whose `field` key "identifies the field in a dataset if a tag applies to one" ([tags facet](https://openlineage.io/docs/spec/facets/dataset-facets/tag-facet), [schema](https://openlineage.io/spec/facets/1-0-0/TagsDatasetFacet.json)). We keep them in `governance/metadata.toml` instead, the one source that the platform's access policies also read, through `lib.policy`, the book's policy module ([chapter 5](#generate-the-data-the-policy-reads)).

**Working rule:** Propose each derived column's classification as the stricter of its inputs', counting INDIRECT inputs, and send the proposals to the table's owner for review before they become metadata. Never let lineage lower a classification someone declared, and never treat masking as declassification. Count DIRECT inputs only if your pipelines often join or filter on personal columns, such as matching on email, and every output would otherwise come out personal; then review INDIRECT personal inputs by hand.

## What goes wrong in production {#lineage-in-production}

Lineage fails quietly: a missing edge looks exactly like a column with no dependencies, and every check built on the graph, from [impact analysis](#impact-of-a-column-change) to [proposed classifications](#classifications-from-lineage), then passes. Three failures are common, and each has a check.

### Events that never arrive {#events-that-never-arrive}

The client reads `OPENLINEAGE_DISABLED` from the environment, and when it's `true`, events are dropped ([configuration](https://openlineage.io/docs/client/python/configuration)). In the client's source, that check comes first ([openlineage-python](https://pypi.org/project/openlineage-python/1.54.0/), `client/client.py`): before it looks at the transport you passed explicitly, the client picks a transport that does nothing. Its only notice is an INFO log line: "OpenLineage is disabled. No events will be emitted." Python's root logger is set to `WARNING` by default, so the line never shows ([logging HOWTO](https://docs.python.org/3.12/howto/logging.html)). A variable left in a shared environment file after debugging is enough. Set the variable, run `review_corpus` with an explicit file transport, and check what reaches the file:

Example `lineage-disabled-silently` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""With OPENLINEAGE_DISABLED=true in the environment, an explicit file transport writes nothing and raises nothing. The
prose rests on the transport the client chose and on the job the check finds without a COMPLETE event."""
import os

from lib import lineage
from lib.catalog import open_catalog
from lib.platform import scratch

os.environ["OPENLINEAGE_DISABLED"] = "true"        # say, left in a shared environment file after a debugging session

events_file = scratch() / "events.jsonl"
client = lineage.client(events_file)                # a file transport, passed in explicitly
catalog = open_catalog(["learning.courses", "learning.reviews"])
output = lineage.run(catalog, "review_corpus", client)

print("transport the client chose:", client.transport.kind)      # OPENLINEAGE_DISABLED wins over the transport passed in
print("pipeline wrote:", output)
print("rows written:", f"{len(catalog.load_table(output).scan().to_arrow()):,}")
assert not events_file.exists()         # the noop transport never creates the file
print("events file exists:", events_file.exists())
missing = lineage.missing_runs(["review_corpus"], lineage.read_events(events_file))   # ran, but sent no COMPLETE
print("jobs that ran with no COMPLETE event:", ", ".join(missing))
```

Output:

```text
transport the client chose: noop
pipeline wrote: ai.review_corpus
rows written: 3,000
events file exists: False
jobs that ran with no COMPLETE event: review_corpus
```

With the variable set, the pipeline still runs, but nothing reaches the file. The client chose the `noop` transport over the file transport the code passed in, and the pipeline wrote 3,000 rows to `ai.review_corpus` without an error and without an events file. The check that catches it compares the jobs the scheduler ran with the jobs that sent a COMPLETE event: `lib.lineage.missing_runs` lists `review_corpus` as having run without one.

**Working rule:** After every scheduled run, compare the jobs that ran with the jobs whose COMPLETE events arrived, and alert on any difference. Don't rely on the emitter to report its own silence.

### A job nobody instrumented {#job-nobody-instrumented}

Lineage covers only the jobs that send it. The platform's marketing team runs a weekly Python script that copies `marketing.audience` into `marketing.campaign_list`, a table its email tool reads. Nobody wired the script to OpenLineage:

Example `uninstrumented-job` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""A Python step copies marketing.audience for the email tool and sends no lineage. The prose rests on the walk from the
email column, which misses the copy, and on the catalog check against the lineage, which finds it."""

from lib import lineage
from lib.catalog import open_catalog
from lib.platform import scratch
from lib.warehouse import connect

catalog = open_catalog()
events_file = scratch() / "events.jsonl"
lineage.run_all(catalog, events_file)

# The marketing team's weekly export, written straight to the catalog: no lineage event.
export = connect(catalog).sql("select learner_id, full_name, email from marketing.audience").to_arrow_table()
catalog.create_table("marketing.campaign_list", schema=export.schema).append(export)
print("rows exported:", f"{len(export):,}")

events = lineage.read_events(events_file)
reached = lineage.downstream(lineage.graph(events), "crm.learners.email")
print("crm.learners.email reaches:", ", ".join(edge.target for edge in reached))
# the catalog's tables, less the platform's sources and the outputs the events name
print("tables no job's lineage accounts for:", ", ".join(lineage.unaccounted(catalog, events)))
```

Output:

```text
rows exported: 1,829
crm.learners.email reaches: marketing.audience.email
tables no job's lineage accounts for: marketing.campaign_list
```

An export that sends no events is invisible to impact analysis. The script copied 1,829 learners' names and emails, yet `crm.learners.email` still reaches only `marketing.audience.email`, so an erasure guided by this lineage would miss the copy. The catalog knows the table exists, though, so `lib.lineage.unaccounted` compares the catalog's tables with the lineage: every table must be one of the platform's sources or the output of a job that lineage knows. It finds `marketing.campaign_list`.

**Working rule:** Check the catalog against the lineage on a schedule, and treat a table no job's lineage accounts for as an incident: find the job, and make it send events.

### Personal data in a table classified internal {#personal-data-tagged-internal}

Instrumenting [the marketing team's export](#job-nobody-instrumented) fixes the graph, and exposes a second problem. When the export's owner created `marketing.campaign_list`, they classified every column internal, because only the marketing team reads it. That's a statement about who reads a table, not what it holds. Wrap the script's work in `lib.lineage.record`, with the `SELECT` it runs as its lineage, and compare the declared classifications with lineage's proposal:

Example `personal-copy-tagged-internal` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""The same export, now recorded with lineage, into a table its owner tagged internal. The prose rests on the walk to
the copy and on the check for understated classifications."""

from lib import lineage
from lib.catalog import open_catalog
from lib.platform import scratch
from lib.warehouse import connect

catalog = open_catalog()
events_file = scratch() / "events.jsonl"
lineage.run_all(catalog, events_file)

select = "select a.learner_id, a.full_name, a.email from marketing.audience a"


def export() -> None:
    rows = connect(catalog).sql(select).to_arrow_table()
    catalog.create_table("marketing.campaign_list", schema=rows.schema).append(rows)


# record reads this statement's lineage before export() runs
statement = f"create table marketing.campaign_list as {select}"
lineage.record(lineage.client(events_file), "campaign_export", statement, catalog, export)

# Its owner tagged every column internal: "only the marketing team reads it".
known = lineage.declared() | {f"marketing.campaign_list.{c}": "internal" for c in ("learner_id", "full_name", "email")}
graph = lineage.graph(lineage.read_events(events_file))
print("crm.learners.email reaches:", ", ".join(edge.target for edge in lineage.downstream(graph, "crm.learners.email")))
for problem in lineage.understated(lineage.propose(graph, known), known):
    print("understated:", problem)
```

Output:

```text
crm.learners.email reaches: marketing.audience.email, marketing.campaign_list.email
understated: marketing.campaign_list.full_name: declared internal, lineage proposes personal
understated: marketing.campaign_list.email: declared internal, lineage proposes personal
```

Once the export sends lineage, the walk reaches its copy: `crm.learners.email` reaches `marketing.audience.email, marketing.campaign_list.email`, two hops, the second through the export. And `lib.lineage.understated` reports `full_name` and `email` in `marketing.campaign_list` as declared internal while lineage proposes personal: copies of personal data that any policy reading the declared classification would treat as internal.

**Working rule:** Run `lib.lineage.understated`, or your own check like it, on every lineage update, and fail when a declared classification is lower than lineage proposes. Classify by what a table holds, never by who reads it, and fix such a finding by raising the classification, not by dropping the edge.

## What this chapter decided {#lineage-decisions}

- **Every pipeline run sends OpenLineage run events,** START and then COMPLETE or FAIL, from the code that runs it (`lib.lineage.run`), with the output's schema and column lineage. Datasets are named by catalog identifiers under the placeholder namespace `iceberg://platform`. Examples fix event times and derive run IDs from the nominal run, and compare what events say, not their bytes.
- **Column lineage is sqlglot's value lineage, typed as OpenLineage subtypes, plus INDIRECT inputs:** the join, filter, grouping and sort columns of every `SELECT`, CTEs included, in the facet's `dataset` list.
- **Lineage that can't be read correctly is an error,** never empty or partial. `lib.lineage` reads only `CREATE ... AS` and `INSERT ... SELECT`, refuses every other statement, `MERGE` included, whatever its `USING` names. Empty lineage, an unplaceable source or an unknown column stops the job before it runs. An `INSERT`'s columns come from the table's schema in the catalog, matched by position, and a count that differs is an error.
- **Impact analysis walks the graph built from events,** INDIRECT edges included, and reports columns whose values can change and tables whose rows can change.
- **Classifications propagate as the stricter of all inputs',** DIRECT and INDIRECT, as set in `governance/lineage.toml`, so a table chosen by a personal filter is proposed personal. Lineage never lowers a declared classification, and masking never declassifies. The proposals for the two unclassified tables, `full_name`, `email` and `body` personal and every other column internal, go to their owners for review before they enter `governance/metadata.toml`.
- **Three checks guard the lineage itself:** jobs that ran with no COMPLETE event, tables no job's lineage accounts for, and declared classifications lower than lineage proposes. A lineage graph is only as complete as its events, and a missing edge looks exactly like a column with no dependencies.
