---
title: "Data Governance as Code"
chapter: "Enforcing policies on queries"
chapter_id: enforcing-policies-on-queries
book: data-governance-as-code
edition: 2026.11.21
verified: 2026-11-10
edition_code: 249N-3RTC
canonical: https://rollingedition.com/data-governance-as-code/enforcing-policies-on-queries
license: CC BY 4.0
attribution: "“Enforcing policies on queries,” chapter 6 of Data Governance as Code, Edition 2026.11.21, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/enforcing-policies-on-queries. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Enforcing policies on queries

By the end of this chapter you can enforce access decisions on every query the platform runs. You'll rewrite each query so that every table it reads is replaced by a subquery that keeps only the rows the user may see and masks the columns they may not, deny every query that reads anything else, test who gets what by running real queries, and say where a rewrite in front of DuckDB stops protecting anything.

The platform, the online learning platform this book follows, sells professional courses to adult learners, and its warehouse holds their contact details, their payments and the text they write. [Chapter 5](#access-policies-as-code) wrote the platform's access policy in Rego. Given a user, a table, the columns they want and, optionally, why they want them, the policy returns a **decision**: a document that says whether to `allow` the read, which **row filters** keep the rows the user may see, which **column masks** change how a column is shown (`redact`, `last4`, `pseudonymize` or `redact_contacts`), and the `reasons`. A decision does nothing on its own. A support agent's SQL reaches DuckDB as text, and something between the two has to apply the decision to every table that text reads, however the query is written.

That layer is this chapter's subject: the book's shared module `lib.enforce`, which we call the **enforcement layer**. Its `Enforcer` holds four things: a DuckDB connection with a view for each catalog table (`lib.warehouse.connect`), the tables' schema, the policy and a key for pseudonyms. Users never get the connection. `Enforcer.sql(query, user)` rewrites a user's query and runs the rewrite. A service exposes only `lib.enforce.answer`, which calls it and returns the rows: never the relation, a handle on the connection, or `Enforcer.run`, which executes SQL the layer wrote with the key attached. The examples run sqlglot 30.30.0 and DuckDB 2.0.0.

## Find every table and column a query reads {#find-what-a-query-reads}

A policy can only decide about what it's asked, so before the enforcement layer asks, it has to know every table a query reads and which columns it reads from each. Reading that off SQL text is a parsing problem with traps: `*`, aliases, joins with `USING`, common table expressions (CTEs) and identifiers in any case. sqlglot parses a query into a tree, and its `qualify` step resolves every column against a schema, qualifies it with its table, and expands `*` into the columns it stands for when it has a schema to expand against ([`qualify` at v30.24.0](https://github.com/tobymao/sqlglot/blob/v30.24.0/sqlglot/optimizer/qualify.py)). The enforcement layer builds that schema when it starts: it lists the catalog's tables, and reads each one's columns and types from the view `lib.warehouse.connect` created for it, so a view DuckDB holds for anything else never enters the schema.

For the platform, `Enforcer.reads` returns the columns each query reads from each table:

Example `tables-a-query-reads` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers

from lib.catalog import open_catalog
from lib.enforce import Enforcer

platform = Enforcer(open_catalog(["crm.learners", "support.tickets"]))

# What each query reads, found by sqlglot's qualify against the catalog's schema, with `*` expanded.
queries = {
    "every column": "select * from crm.learners",
    "a join": """select l.country, count(*) as tickets
                 from crm.learners as l join support.tickets as t using (learner_id) group by all""",
    "a CTE": """with emea as (select * exclude (notes) from crm.learners where support_region = 'emea')
                select email from emea""",
    "names in capitals": 'select EMAIL from "CRM"."LEARNERS"',
}
for name, sql in queries.items():
    for table, columns in platform.reads(sql).items():
        print(f"{name}, {table}: {', '.join(columns)}")

# DuckDB resolves quoted capitals to the lowercase table. Whether sqlglot lowercases them depends on the dialect.
capitals = 'select count(*) from "CRM"."LEARNERS"'
print('DuckDB, "CRM"."LEARNERS":', f"{platform.connection.sql(capitals).fetchall()[0][0]:,} rows")
for dialect in ["duckdb", "trino", "postgres"]:
    table = normalize_identifiers(sqlglot.parse_one('select * from "LEARNERS"', read=dialect), dialect=dialect).find(exp.Table)
    print(f'{dialect} normalizes "LEARNERS" to:', table.name)
```

Output:

```text
every column, crm.learners: ai_training_consent, city, closed_at, country, date_of_birth, email, full_name, learner_id, marketing_consent, notes, phone, signup_at, status, street_address, support_region
a join, crm.learners: country, learner_id
a join, support.tickets: learner_id
a CTE, crm.learners: ai_training_consent, city, closed_at, country, date_of_birth, email, full_name, learner_id, marketing_consent, phone, signup_at, status, street_address, support_region
names in capitals, crm.learners: email
DuckDB, "CRM"."LEARNERS": 5,000 rows
duckdb normalizes "LEARNERS" to: learners
trino normalizes "LEARNERS" to: learners
postgres normalizes "LEARNERS" to: LEARNERS
```

`SELECT *` becomes every column of `crm.learners`, and the join reads `learner_id` from both tables, because the `USING` clause compares them, though neither appears in the output. In the query with a CTE, the outer query returns only `email`, but the CTE names every column of `crm.learners` except `notes`, so the layer asks about all of those: it asks about every column a query names anywhere, which can be more than the query returns, and never fewer. `"CRM"."LEARNERS"` resolves to `crm.learners`, because the layer normalizes identifiers the way DuckDB resolves them before it matches anything: DuckDB returns 5,000 rows of `crm.learners` for that name. The dialect matters: sqlglot lowercases `"LEARNERS"` for DuckDB and Trino, and keeps it as `LEARNERS` for PostgreSQL, so the layer normalizes with the dialect of the engine that runs the query.

`qualify` has one gap that decides the layer's design: it fails on an unknown column of a known table, but it passes over a table that isn't in the schema at all, and leaves that table's `*` unexpanded. Run it on a join with `marketing.audience`, which stands for a table a pipeline wrote after the schema was read, then send the same query and five other reads through the layer:

Example `unknown-tables-denied` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import sqlglot
from sqlglot.optimizer.qualify import qualify

from lib.catalog import open_catalog
from lib.enforce import Denied, Enforcer

platform = Enforcer(open_catalog(["crm.learners"]))

# marketing.audience stands for a table a pipeline wrote after the schema was read. qualify alone lets it through.
query = "select * from crm.learners as l join marketing.audience as a on a.learner_id = l.learner_id"
print("qualify on its own:", qualify(sqlglot.parse_one(query, read="duckdb"), schema=platform.schema, dialect="duckdb").sql("duckdb"))

# The enforcement layer denies anything that isn't a catalog table, before it asks the policy.
attempts = {
    "a table missing from the catalog": query,
    "a column the table doesn't have": "select shoe_size from crm.learners",
    "the scan behind a view": "select count(*) from scan_crm_learners",
    "a Parquet file": "select count(*) from read_parquet('data/platform/learners.parquet')",
    "a table function": "select count(*) from query_table('crm.learners')",
    "a statement that isn't a query": "summarize crm.learners",
}
for name, sql in attempts.items():
    try:
        platform.rewrite(sql, "analyst-1")
        print(f"{name}: allowed")
    except Denied as reason:
        print(f"{name}: denied, {reason}")

# What those reads would do on the layer's own connection, without the rewrite in front of it.
rows = lambda sql: f"{platform.connection.sql(sql).fetchall()[0][0]:,} rows"
print("the scan, run directly:", rows("select count(*) from scan_crm_learners"))
print("the table function, run directly:", rows("select count(*) from query_table('crm.learners')"))
try:
    rows("select count(*) from read_parquet('data/platform/learners.parquet')")
except Exception as error:
    print("the file, run directly:", str(error).split(":")[0])
try:
    platform.connection.execute("set enable_external_access = true")
except Exception as error:
    print("turning external access back on:", str(error).split(": ", 1)[1])
```

Output:

```text
qualify on its own: SELECT * FROM "crm"."learners" AS "l" JOIN "marketing"."audience" AS "a" ON "a"."learner_id" = "l"."learner_id"
a table missing from the catalog: denied, not a table in the catalog: marketing.audience AS a
a column the table doesn't have: denied, Column 'shoe_size' could not be resolved. Line: 1, Col: 16
the scan behind a view: denied, not a table in the catalog: scan_crm_learners
a Parquet file: denied, not a table in the catalog: READ_PARQUET('data/platform/learners.parquet')
a table function: denied, not a table in the catalog: QUERY_TABLE('crm.learners')
a statement that isn't a query: denied, only a single query is allowed
the scan, run directly: 5,000 rows
the table function, run directly: 5,000 rows
the file, run directly: Permission Error
turning external access back on: Cannot enable external access while database is running
```

`qualify` on its own returns the query with `SELECT *` intact and no error, so a layer that trusted it would ask the policy about `crm.learners` and pass `marketing.audience` through unchecked. The enforcement layer denies every table that isn't in the catalog before it asks the policy anything. A column the table doesn't have is denied by `qualify` itself. The other four reads show why that rule is broad. `lib.warehouse` registers each table's scan with DuckDB under a name of its own, such as `scan_crm_learners`. Run directly on the layer's connection, that scan returns 5,000 rows of raw learners. `read_parquet` reads a file, and `query_table` reads whatever table its string names, 5,000 rows when run directly. `SUMMARIZE` isn't a query the rewrite can analyse. The first three aren't catalog tables and the last isn't a query, so all four are denied. The layer's connection also has DuckDB's `enable_external_access` turned off, so a file read that got past the rewrite would still fail, with a `Permission Error` ([Securing DuckDB](https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview)).

**Working rule:** Ask the policy about every table and column a query names, with `*` expanded against the catalog's own schema, and deny anything that schema doesn't hold: unknown tables, files, table functions and statements other than a single query. A denial costs a user one question to the platform team; a pass-through costs whatever the unchecked table holds.

## Allow only catalog tables, CTEs and subqueries {#allow-only-catalog-sources}

[Denying names the catalog doesn't hold](#find-what-a-query-reads) isn't enough on its own, because a query can read data through sources that aren't table names. A table function can sit under `LATERAL`, or in a subquery in the select list. Outside a CTE's scope, or before the CTE is defined, DuckDB resolves its name to whatever else the connection holds under that name. A check that inspects only table names, and accepts any name a CTE uses, passes both.

So the enforcement layer checks sources against an allowlist. `Enforcer.check_sources` walks the whole query and requires every `FROM` and `JOIN` source, at every level, to be a catalog table, a CTE in scope or a subquery, and a `LATERAL` to be over a subquery. Everything else is denied, including table functions wherever they appear, `VALUES`, `UNNEST` and joins in parentheses. A CTE is in scope in its own query, below it and in later CTEs, and a recursive one also in its `UNION`'s recursive branch. An allowlist fails closed on a kind of source nobody thought of.

A query through the layer must also change nothing. DuckDB's scalar `write_log` writes into the engine's query log. `duckdb_functions()` marks such functions: `has_side_effects` is "`true` if this function changes the database state" ([DuckDB, `duckdb_functions`](https://duckdb.org/docs/2.0/sql/meta/duckdb_table_functions)). At 2.0.0 it also marks functions that only vary, such as `random` and `uuid`. The layer denies every flagged function, and every macro that calls one, such as `pg_sleep`, reading the list from `duckdb_functions()` when it starts: a list sorted by hand into harmful and harmless is one an upgrade can outdate unnoticed, and a governed read seldom needs a random number.

`lib.enforce` keeps the cases as a regression test, `source_cases`, which [chapter 10's CI](#run-every-rule-as-one-job) runs, as it does [the order test](#gate-columns-on-row-filters) below:

Example `catalog-sources-only` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib.catalog import open_catalog
from lib.enforce import MUST_ALLOW, MUST_DENY, Enforcer, source_cases

platform = Enforcer(open_catalog(["crm.learners", "support.tickets"]))

# The allowlist's regression test, lib.enforce.source_cases, which chapter 10's CI runs too: queries that read data
# other than through a catalog table, a call to each function DuckDB marks as having side effects, and a query the
# layer must still allow. A case passes when the layer denies it exactly when it must, and its parse logs nothing.
cases = source_cases(platform)
for case in cases:
    if case["case"] in MUST_DENY:
        print(f"{case['case']}:", f"denied, {case['reason']}" if case["denied"] else "ALLOWED")
functions = [case for case in cases if case["must"] == "deny" and case["case"] not in MUST_DENY]
print("functions with side effects:", ", ".join(case["case"].removeprefix("the function ") for case in functions))
print("functions with side effects, denied:", f"{sum(case['denied'] for case in functions)} of {len(functions)}")
print("cases whose parse sqlglot logged, quoting the query:", f"{sum(case['logged'] for case in cases)} of {len(cases)}")
passing = [case for case in cases if case["denied"] == (case["must"] == "deny") and not case["logged"]]
print("cases that pass:", f"{len(passing)} of {len(cases)}")

# What two of the cases do on the layer's own connection, without the layer in front of it.
before_the_cte = platform.connection.sql(MUST_DENY["a CTE's name before the CTE"]).fetchall()[0][0]
print("a CTE's name before the CTE, run directly:", f"{before_the_cte:,} rows")
platform.connection.execute("CALL enable_logging('QueryLog')")
platform.connection.sql(MUST_DENY["a function that writes DuckDB's log"]).fetchall()
logged = [message for (message,) in platform.connection.sql("select message from duckdb_logs where type = 'QueryLog'").fetchall()]
print("the log function, run directly, query-log entries it leaves:", logged)

# The query the allowlist must let through, run through the layer.
for name, query in MUST_ALLOW.items():
    print(f"{name}, allowed:", f"{platform.sql(query, 'agent-a05').fetchall()[0][0]:,} rows")
```

Output:

```text
a table function in FROM: denied, not a table in the catalog: QUERY_TABLE('crm.learners')
a table function in a scalar subquery: denied, not a table in the catalog: QUERY_TABLE('crm.learners')
a table function under LATERAL: denied, a LATERAL that isn't a subquery: LATERAL QUERY_TABLE('crm.learners')
a catalog-qualified name: denied, not a table in the catalog: memory.crm.learners
an information_schema view: denied, not a table in the catalog: information_schema.tables
a CTE's name outside its scope: denied, not a table in the catalog: other
a CTE's name before the CTE: denied, not a table in the catalog: scan_crm_learners
a function that writes DuckDB's log: denied, a function DuckDB marks as having side effects: write_log
a statement sqlglot keeps as text: denied, only a single query is allowed
functions with side effects: current_connection_id, current_query, current_query_id, current_transaction_id, currval, error, gen_random_uuid, nextval, pg_sleep, random, setseed, setval, sleep_ms, stats, uuid, uuidv4, uuidv7, vector_type, write_log
functions with side effects, denied: 19 of 19
cases whose parse sqlglot logged, quoting the query: 0 of 29
cases that pass: 29 of 29
a CTE's name before the CTE, run directly: 5,000 rows
the log function, run directly, query-log entries it leaves: ["select write_log('an entry', log_type := 'QueryLog')", 'an entry']
a CTE, a join and a scalar subquery, allowed: 61 rows
```

Each case is denied before any policy is asked, with a reason that names the source. The layer parses with sqlglot's warnings silenced, since sqlglot logs any statement it keeps as text, such as a `CALL`, values included ([sqlglot source, v30.24.0](https://github.com/tobymao/sqlglot/blob/v30.24.0/sqlglot/parser.py)), and every case checks that nothing was logged: 29 of 29 cases pass. Two of them, run on the layer's own connection, show what the denials prevent: the name used before its CTE reads the scan of the same name, 5,000 rows of raw learners, and `write_log` leaves `["select write_log('an entry', log_type := 'QueryLog')", 'an entry']`: its own statement, and an entry no query made. Every function with side effects is denied, 19 of 19. The last line checks that the allowlist doesn't deny too much: run as `agent-a05`, the EMEA support agent, a CTE, a join and a scalar subquery over catalog tables return 61 rows.

**Working rule:** Check every source a query reads against an allowlist of catalog tables, CTEs in scope and subqueries, and deny the rest, along with every function the engine marks as having side effects, read from its own list. Keep the cases as a regression test for every change to the layer and every engine upgrade, and add one whenever a new kind of source or function turns up.

## Masking column references leaks {#column-masks-leak}

With the columns known, the obvious enforcement rewrites them: wherever the query selects `email` and the decision masks it, select the mask instead. It needs nothing but the column list from [the first section](#find-what-a-query-reads), and it looks right on the queries people test with. It fails because a query can read a column without selecting it, and DuckDB can return a column without naming it.

On the platform, `analyst-1`, a data scientist, may read `crm.learners` with `email` and the other personal columns pseudonymized, and free text such as `notes` redacted. `Enforcer.mask_select_list` does the column rewrite, kept only to show this failure. The example prints its rewrite of a plain read, then runs five reads aimed at learner 2's email, with any stored email replaced by a placeholder, since the book's examples never print one. Before you run it, predict how many of the five the column rewrite stops:

Example `select-list-masks-leak` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import re

import duckdb

from lib.catalog import open_catalog
from lib.enforce import EMAIL, Enforcer

platform = Enforcer(open_catalog(["crm.learners"]))
# analyst-1, a data scientist, may read crm.learners with `email` pseudonymized. The attacks aim at learner 2.
email = platform.connection.sql("select email from crm.learners where learner_id = 2").fetchall()[0][0]
print("the column rewrite:", platform.mask_select_list("select learner_id, email from crm.learners", "analyst-1"))

attacks = {
    "a WHERE on the raw column": f"select learner_id from crm.learners where email = '{email}'",
    "the whole row as a struct": "select struct_extract(l, 'email') from crm.learners as l where learner_id = 2",
    "COLUMNS(...)": "select columns('^email$') from crm.learners where learner_id = 2",
    "to_json": "select to_json(l) ->> 'email' from crm.learners as l where learner_id = 2",
    "a cast error": "select learner_id from crm.learners where cast(email as integer) = 0",
}
for name, sql in attacks.items():
    try:
        answer = str(platform.run(platform.mask_select_list(sql, "analyst-1")).fetchall())
    except duckdb.Error as error:
        answer = str(error).splitlines()[0]
    print(f"{name}:", re.sub(EMAIL, "<a stored email>", answer))      # the book never prints a stored email
```

Output:

```text
the column rewrite: SELECT "learners"."learner_id" AS "learner_id", SHA256($pseudonym_key || CAST("learners"."email" AS TEXT)) AS "email" FROM "crm"."learners" AS "learners"
a WHERE on the raw column: [(2,)]
the whole row as a struct: [('<a stored email>',)]
COLUMNS(...): [('<a stored email>',)]
to_json: [('<a stored email>',)]
a cast error: Conversion Error: Could not convert string '<a stored email>' to INT32 when casting from source column email
```

None. The rewrite of the plain read is correct: `email` comes back as a hash. The five reads get past it in three ways:

- **A `WHERE` on the raw column** never passes through the select list, so it compares the stored email. The analyst guesses an email and gets back learner 2's ID, `[(2,)]`, which links that person to every row they can join on `learner_id`.
- **The whole row as a struct, `COLUMNS(...)` and `to_json`** return the stored email, `[('<a stored email>',)]`, without any column reference named `email` for the rewrite to find: DuckDB expands the row, or matches column names against a pattern, itself.
- **A cast error** prints a stored email in its message. DuckDB's cast errors include the value, and PostgreSQL's documentation warns that "most casting functions include their input values in the error messages they produce" ([PostgreSQL 18, Rules and Privileges](https://www.postgresql.org/docs/18/rules-privileges.html)).

Masking the column wherever the query names it, in the `WHERE` clause too, would stop the first and the last read. It can't stop the middle three, because they never name the column.

**Working rule:** Don't enforce masks by rewriting the column references in a query. However many reference shapes you cover, the engine has more ways to read a column than the rewrite has to recognize one. Mask where the data comes from instead, so every read sees the masked value, which is what the [next section](#replace-each-table) does.

## Replace each table with a filtered, masked subquery {#replace-each-table}

[Rewriting column references](#column-masks-leak) leaks because the raw table stays in the query. The fix replaces the table. `Enforcer.rewrite` replaces each catalog table in the query, under the query's own alias for it, with a subquery built from the user's decision:

- every column of the table, in the table's order, so `*`, a struct or `COLUMNS(...)` sees the shape it expects;
- each column the query reads, as stored or masked as the decision says, inside a `CASE` on the row filters that [a later section](#gate-columns-on-row-filters) explains;
- each column it doesn't read, as a typed `NULL`, since the policy wasn't asked about it;
- a `WHERE` clause with every row filter in the decision.

Everything the user's query does, from its `WHERE` to its struct reads, then happens on that subquery. It's the model Trino's OPA plugin follows, where a row filter "essentially behaves like an additional `WHERE` clause", as the [section on engines](#engine-enforcement) shows.

For the platform, take `instructor-17`, who reads the low ratings among their courses' reviews. The policy filters reviews to the instructor's own courses and shows `body` with contact details removed:

Example `table-rewrite` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import sqlglot

from lib.catalog import open_catalog
from lib.enforce import Enforcer

platform = Enforcer(open_catalog(["learning.reviews"]))

# instructor-17 reads the low ratings of their courses' reviews. The policy filters reviews to their six courses and
# shows `body` with contact details removed.
query = "select course_id, rating, body from learning.reviews where rating <= 2"
rewritten = platform.rewrite(query, "instructor-17")
print(sqlglot.transpile(rewritten, read="duckdb", write="duckdb", pretty=True)[0])
print("reviews returned:", len(platform.run(rewritten).fetchall()))
print("of them holding an email:", platform.run(f"select count(*) from ({rewritten}) where body like '%@%'").fetchall()[0][0])
```

Output:

```text
SELECT
  "reviews"."course_id" AS "course_id",
  "reviews"."rating" AS "rating",
  "reviews"."body" AS "body"
FROM (
  SELECT
    CAST(NULL AS BIGINT) AS review_id,
    CAST(NULL AS BIGINT) AS learner_id,
    CASE WHEN source.course_id IN (2, 75, 80, 87, 103, 134) THEN source.course_id END AS course_id,
    CASE WHEN source.course_id IN (2, 75, 80, 87, 103, 134) THEN source.rating END AS rating,
    CASE
      WHEN source.course_id IN (2, 75, 80, 87, 103, 134)
      THEN REGEXP_REPLACE(
        REGEXP_REPLACE(source.body, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+', '[email]', 'g'),
        '\+?\(?[0-9][0-9 ().-]{6,}[0-9]',
        '[phone]',
        'g'
      )
    END AS body,
    CAST(NULL AS TIMESTAMPTZ) AS posted_at
  FROM learning.reviews AS source
  WHERE
    source.course_id IN (2, 75, 80, 87, 103, 134)
) AS "reviews"
WHERE
  "reviews"."rating" <= 2
reviews returned: 9
of them holding an email: 0
```

The instructor's query stays on the outside, qualified but otherwise unchanged. Inside, `course_id` and `rating` come through as stored and `body` as the `redact_contacts` mask, each in a `CASE` on the row filter, a literal list of the instructor's courses, and the columns the query doesn't read are typed `NULL`s. The query returns 9 reviews, and 0 of them hold an email.

The five reads that defeated the column rewrite, run by `analyst-1` through the table rewrite, and through `lib.enforce.answer`, the function a service calls at its boundary:

Example `table-rewrite-holds` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import logging
import re

from lib.catalog import open_catalog
from lib.enforce import EMAIL, Enforcer, QueryFailed, answer

platform = Enforcer(open_catalog(["crm.learners"]))
operator_log = []                     # the platform team's log, kept in a list here so the example can print it
logging.getLogger("lib.enforce").addHandler(handler := logging.Handler())
handler.emit = lambda record: operator_log.append(record.getMessage().splitlines()[0])

# The five attacks on the column rewrite, run by analyst-1 again: through the table rewrite this time, and through
# `answer`, the function a service calls at its boundary.
email = platform.connection.sql("select email from crm.learners where learner_id = 2").fetchall()[0][0]
attacks = {
    "a WHERE on the raw column": f"select learner_id from crm.learners where email = '{email}'",
    "the whole row as a struct": "select struct_extract(l, 'email') from crm.learners as l where learner_id = 2",
    "COLUMNS(...)": "select columns('^email$') from crm.learners where learner_id = 2",
    "to_json": "select to_json(l) ->> 'email' from crm.learners as l where learner_id = 2",
    "a cast error": "select learner_id from crm.learners where cast(email as integer) = 0",
}
shorten = lambda text: re.sub(r"\b([0-9a-f]{8})[0-9a-f]{56}\b", r"\1…", re.sub(EMAIL, "<a stored email>", text))
for name, sql in attacks.items():
    try:
        got = str(answer(platform, sql, "analyst-1"))
    except QueryFailed as error:
        got = f"{type(error).__name__}, {error}"
    print(f"{name}:", shorten(got))
for line in operator_log:
    print("in the operator's log:", shorten(line))      # a pseudonym, 64 hex digits, shortened

# Why `answer` returns rows: the relation Enforcer.sql returns is a handle on the layer's connection, and runs any SQL.
relation = platform.sql("select learner_id from crm.learners", "analyst-1")
print("the relation, running SQL of its own:", shorten(str(relation.query("r", "select email from crm.learners where learner_id = 2").fetchall())))
print("what answer returns:", type(answer(platform, "select learner_id from crm.learners", "analyst-1")).__name__)
```

Output:

```text
a WHERE on the raw column: []
the whole row as a struct: [(None,)]
COLUMNS(...): [(None,)]
to_json: [(None,)]
a cast error: QueryFailed, the query failed: the platform team can see why
in the operator's log: a query by analyst-1 failed in the engine: Conversion Error: Could not convert string 'e4f62f1a…' to INT32 when casting from source column email
the relation, running SQL of its own: [('<a stored email>',)]
what answer returns: list
```

The `WHERE` finds no one, `[]`, because inside the subquery `email` is already the pseudonym. The struct, `COLUMNS(...)` and `to_json` reads return `NULL`, not the pseudonym, and that is the typed-`NULL` rule working: those queries name no column of `crm.learners` but `learner_id`, so the policy was asked about no other column, and the subquery gives the rest no value. A read the rewrite can't see fails closed. DuckDB's cast error now holds a pseudonym instead of an email, and the analyst doesn't see even that: `answer` fetches the rows inside a `try`, turns any engine error into `QueryFailed`, and writes DuckDB's message to the platform team's log, the example's last line. The analyst gets `QueryFailed, the query failed: the platform team can see why`. And `answer` returns rows because a DuckDB relation runs any SQL on its connection: the analyst's relation, asked for an email, returns `[('<a stored email>',)]`.

Generating the subquery per query, rather than writing a view per role, is what keeps it in step with the policy. The platform's decisions depend on region, courses, consent and purpose, and a hand-made view for every combination is the "role explosion" NIST describes, where conditions become "numerous roles that are ad hoc and limited in membership" ([NIST SP 800-162](https://doi.org/10.6028/NIST.SP.800-162)). The views would also drift from the policy the first time someone edited one and not the other.

**Working rule:** Replace every protected table with a subquery generated from the decision, under the query's own alias, and leave the user's query otherwise untouched. Give columns the query doesn't read a typed `NULL`. If your users need whole-row reads to show values, ask the policy about every column of each table instead: the masks then cover all of them, at the cost of requests, and audit records, that name columns the query never used.

## Write each mask as SQL in one place {#write-masks-as-sql}

The policy names a mask; the enforcement layer decides what SQL it becomes. Keeping that mapping in one place, the `MASKS` table in `lib.enforce` and the typed `NULL` beside it, means a fix to a mask reaches every table that uses it, and the policy never carries SQL, which would be code arriving as data. The [table rewrite](#replace-each-table) calls `lib.enforce.masked` for every masked column:

Example `masks-as-sql` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import duckdb
from sqlglot import exp

from lib.enforce import masked

# The four masks the policy names, as the SQL the enforcement layer writes for them.
for kind, column, type_ in [("redact", "date_of_birth", "DATE"), ("last4", "card_number", "VARCHAR"),
                            ("pseudonymize", "email", "VARCHAR"), ("redact_contacts", "body", "VARCHAR")]:
    print(f"{kind}:", masked(kind, exp.column(column), type_).sql("duckdb"))

# The pseudonymize mask hashes the key followed by the value, because DuckDB has no HMAC function to call.
hmac = duckdb.sql("select count(*) from duckdb_functions() where function_name ilike '%hmac%'").fetchall()[0][0]
print("DuckDB functions named like HMAC:", hmac)
```

Output:

```text
redact: CAST(NULL AS DATE)
last4: RIGHT(REGEXP_REPLACE(card_number, '[^0-9]', '', 'g'), 4)
pseudonymize: SHA256($pseudonym_key || CAST(email AS TEXT))
redact_contacts: REGEXP_REPLACE(REGEXP_REPLACE(body, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+', '[email]', 'g'), '\+?\(?[0-9][0-9 ().-]{6,}[0-9]', '[phone]', 'g')
DuckDB functions named like HMAC: 0
```

Each mask does one job:

- **`redact`** is a `NULL` cast to the column's type, so the column keeps its type for anything the query does with it, such as a union or a date function.
- **`last4`** keeps the last four digits of a card number, after removing anything that isn't a digit.
- **`pseudonymize`** is a keyed hash, SHA-256 over the key followed by the value, because DuckDB 2.0.0 has no HMAC function: `duckdb_functions()` lists 0 named like it. Where your engine has one, prefer HMAC ([RFC 2104](https://www.rfc-editor.org/rfc/rfc2104)).
- **`redact_contacts`** replaces emails and phone numbers in free text with `[email]` and `[phone]`.

The key is what makes a pseudonym a pseudonym. The next example plays someone who holds a list of the platform's emails and hashes each one to look for it among the pseudonyms that `analyst-1`, the platform's data scientist, sees in `crm.learners`:

Example `pseudonym-key` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib.catalog import open_catalog
from lib.enforce import Enforcer

# The pseudonyms analyst-1, the platform's data scientist, sees in crm.learners. Someone holding a list of the
# platform's emails hashes each one and looks for it among them: without the key the hashes match nothing, and with
# the key they match every learner.
platform = Enforcer(open_catalog(["crm.learners"]), key="example-key-not-a-secret")
seen = platform.sql("select learner_id, email from crm.learners", "analyst-1").to_arrow_table()
platform.connection.register("seen", seen)
for name, guess in [("without the key", "sha256(email)"), ("with the key", "sha256($pseudonym_key || email)")]:
    matched = platform.run(f"select count(*) from crm.learners where {guess} in (select email from seen)").fetchall()[0][0]
    print(f"pseudonyms matched from a list of emails, {name}: {matched:,} of {seen.num_rows:,}")

# A new key gives every learner a new pseudonym, so data pseudonymized under the old key no longer joins.
platform.key = "example-key-rotated"
rotated = platform.sql("select learner_id, email from crm.learners", "analyst-1").to_arrow_table()
changed = sum(a != b for a, b in zip(seen["email"].to_pylist(), rotated["email"].to_pylist()))
print("pseudonyms that change when the key is rotated:", f"{changed:,} of {seen.num_rows:,}")
```

Output:

```text
pseudonyms matched from a list of emails, without the key: 0 of 5,000
pseudonyms matched from a list of emails, with the key: 5,000 of 5,000
pseudonyms that change when the key is rotated: 5,000 of 5,000
```

Without the key, the hashes match 0 of 5,000. With the key, they match 5,000 of 5,000, so whoever holds the key and a list of emails can name every pseudonym on it. That's why the key belongs to the enforcement layer alone. It isn't in the policy, which is code read in pull requests, or in the query, where a user who chose the key could compute pseudonyms of guessed emails. The layer passes it to DuckDB as a query parameter, so it never appears in the query's text, which DuckDB's query log records, as [chapter 8](#keep-values-out-of-the-record) shows. That's also why the layer denies any user query that carries a parameter: one named `$pseudonym_key` would receive the key. In production, keep the key in a secret manager that only the enforcement layer can read. Rotate it when it may have leaked, and plan for what rotation does: 5,000 of 5,000 pseudonyms change, so data pseudonymized under the old key no longer joins with data under the new one.

`redact_contacts` is two regular expressions, and it's worth measuring what they remove. The platform's tickets and reviews come with every piece of personal data the generator placed in them, labelled by construction, which [chapter 3](#finding-personal-data) uses as its ground truth:

Example `redact-contacts-recall` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import duckdb
from sqlglot import exp

from lib.enforce import masked
from lib.platform import load

# The redact_contacts mask, run over every ticket and review, against the personal data the generator placed in them
# (pii_spans, labelled by construction).
con = duckdb.connect()
for name in ["support.tickets", "learning.reviews", "pii_spans"]:
    con.register(name.split(".")[-1], load(name))
mask = masked("redact_contacts", exp.column("body"), "VARCHAR").sql("duckdb")
counts = con.sql(f"""
    with masked as (select 'tickets' as source, ticket_id as row_id, {mask} as body from tickets
                    union all select 'reviews', review_id, {mask} from reviews)
    select source, entity, count(*), count(*) filter (where contains(masked.body, pii_spans.text))
    from pii_spans join masked using (source, row_id) group by all order by all""").fetchall()
for source, entity, placed, left in counts:
    print(f"{source}, {entity}, left in the text: {left:,} of {placed:,}")
# The phone pattern also takes card numbers, IBANs and dates, which are digits too.
replaced = con.sql(f"select sum(len(regexp_extract_all({mask}, '\\[phone\\]'))) from tickets").fetchall()[0][0]
print("[phone] replacements in tickets:", f"{replaced:,}")
```

Output:

```text
reviews, EMAIL_ADDRESS, left in the text: 0 of 120
reviews, PERSON, left in the text: 798 of 798
tickets, CREDIT_CARD, left in the text: 0 of 213
tickets, DATE_TIME, left in the text: 0 of 196
tickets, EMAIL_ADDRESS, left in the text: 0 of 423
tickets, IBAN_CODE, left in the text: 0 of 236
tickets, LOCATION, left in the text: 210 of 210
tickets, PERSON, left in the text: 1,657 of 1,657
tickets, PHONE_NUMBER, left in the text: 0 of 439
[phone] replacements in tickets: 1,520
```

In the reviews, which instructors and the assistant read through this mask, no email is left, 0 of 120, and every name is, 798 of 798. In the tickets, no phone number is left, 0 of 439, but the phone pattern made 1,520 replacements, because card numbers, IBANs and dates are digits too: 0 of 213 card numbers are left, 0 of 236 IBANs and 0 of 196 dates. Names and street addresses stay: the mask removes contact details, and it doesn't make text anonymous.

**Working rule:** Keep every mask's SQL in one table in the enforcement layer, and let the policy name masks, never write them. Key every pseudonym with a secret only the layer holds, passed as a parameter. Measure each text mask against labelled data before a policy relies on it, and name masks for what they remove, so nobody reads `redact_contacts` as "anonymized".

## Build row filters from the decision's data {#build-row-filters-from-data}

Masks change how a value is shown; row filters decide which rows a user gets. They arrive in a decision as data, in three shapes: a column equal to a value, a column in a list of values, and a consent check on the learner a row belongs to. `lib.enforce.row_filter` turns each into a SQL condition, with the values written as SQL literals by sqlglot, never pasted into SQL text. It denies the query for a shape it doesn't know or a column the table doesn't have, and the layer checks a consent filter's column against `crm.learners` before it builds the check. [Chapter 5](#return-the-decision-as-one-document) made the policy return filters as data for exactly this reason: nothing a request carries can reach a query as code.

The consent shape is the one that needs care. The course assistant, `assistant-1`, may read reviews only by learners who agreed to their text training the platform's AI, and that consent lives in `crm.learners`, which the assistant may not read. The layer turns it into a semi-join, a test that the review's `learner_id` is among the learners who consented, and runs it with the layer's own access to `crm.learners`:

Example `row-filters-from-data` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib.catalog import open_catalog
from lib.enforce import Enforcer, row_filter

platform = Enforcer(open_catalog(["crm.learners", "learning.reviews", "support.tickets"]))

# Each row filter in a decision, as the condition the enforcement layer writes for it.
for user, table in [("agent-a05", "support.tickets"), ("instructor-17", "learning.reviews"), ("assistant-1", "learning.reviews")]:
    decision = platform.decide(user, {table: set()})[table]
    for rule in decision["row_filters"]:
        print(f"{user}, {table}: {row_filter(rule, platform.columns(table)).sql('duckdb')}")

# A filter's values come from data, so a value that looks like SQL stays a value.
odd = {"column": "support_region", "equals": "emea' or '1' = '1"}
print("a region that looks like SQL:", row_filter(odd, platform.columns("support.tickets")).sql("duckdb"))

# The assistant's consent filter reads crm.learners, which the assistant itself may not read.
total = platform.connection.sql("select count(*) from learning.reviews").fetchall()[0][0]
read = platform.sql("select count(*) from learning.reviews", "assistant-1").fetchall()[0][0]
print("reviews the assistant reads:", f"{read:,} of {total:,}")
by_consent = platform.connection.sql("""select coalesce(l.ai_training_consent::varchar, 'never asked'), count(*)
    from learning.reviews r join crm.learners l using (learner_id) group by all order by all""").fetchall()
for consent, reviews in by_consent:
    print(f"reviews whose author's AI-training consent is {consent}: {reviews:,}")
try:
    platform.sql("select count(*) from crm.learners", "assistant-1")
except Exception as reason:
    print("the assistant reading crm.learners:", reason)
```

Output:

```text
agent-a05, support.tickets: source.support_region = 'emea'
instructor-17, learning.reviews: source.course_id IN (2, 75, 80, 87, 103, 134)
assistant-1, learning.reviews: source.learner_id IN (SELECT consent.learner_id FROM crm.learners AS consent WHERE consent.ai_training_consent IS TRUE)
a region that looks like SQL: source.support_region = 'emea'' or ''1'' = ''1'
reviews the assistant reads: 436 of 3,000
reviews whose author's AI-training consent is false: 955
reviews whose author's AI-training consent is never asked: 1,609
reviews whose author's AI-training consent is true: 436
the assistant reading crm.learners: assistant-1 may not read crm.learners: no group of this user may read this table
```

The agent's region and the instructor's courses become an equality and an `IN` list. A region value written to look like SQL stays a string, its quotes doubled. The assistant reads 436 of 3,000 reviews. The consent filter tests `IS TRUE`, so the authors of 1,609 reviews, who signed up before the platform asked the question and have no answer recorded, count as not consenting, along with those who said no. And the assistant asking for `crm.learners` itself is denied, with the policy's reason: the semi-join's read of that table belongs to the enforcement layer, not to the user.

**Working rule:** Build every row filter from the decision's values with a SQL builder, and deny any filter shape or column the layer doesn't recognize. Treat an unknown consent as no consent. When a filter needs a table the user may not read, read it with the layer's own access inside the subquery, and never by widening the user's access.

## Gate every column on the row filters {#gate-columns-on-row-filters}

[The row filters](#build-row-filters-from-data) sit in the subquery's `WHERE`, and the user's query wraps the subquery, so it's tempting to assume DuckDB applies the filters first. SQL promises no order, and an optimizer moves conditions wherever they're cheapest. A user's condition that can fail, such as a cast, can then run on rows the filters drop, and a generic error doesn't help: that the query fails says something about a row the user may not see. PostgreSQL's documentation names the leak: a function "that might throw an error depending on the values received as arguments ... could provide significant information about the unseen rows if applied before the security view's row filters". In PostgreSQL, a view marked `security_barrier` keeps "maliciously-chosen functions and operators from being passed values from rows until after the view has done its work", and only functions marked `LEAKPROOF` may still run first ([PostgreSQL 18, Rules and Privileges](https://www.postgresql.org/docs/18/rules-privileges.html)). DuckDB has neither.

So the enforcement layer makes the order irrelevant. Every column the query reads leaves the subquery as `CASE WHEN <row filters> THEN <value> END`, as in [the instructor's rewrite](#replace-each-table). The user's conditions then depend on the filters' result: whatever DuckDB evaluates first, on a row the filters drop they see `NULL` in every column.

The book's test, `lib.enforce.order_cases`, checks that for each filter shape the layer writes: the support agent's equality, the instructor's `IN` list and the course assistant's consent semi-join. For each, it copies the filtered table with a `body` that holds digits in the rows the filter keeps and text in the rows it drops. A query that casts `body` to a number then fails only if the cast sees a dropped row's value:

Example `row-filter-order` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib.enforce import order_cases

# The evaluation-order regression test, lib.enforce.order_cases, which chapter 10's CI runs on every DuckDB upgrade.
# For each shape of row filter the layer writes, it takes a real user's filter and a copy of the filtered table whose
# `body` holds digits in the rows the filter keeps and text in the rows it drops. A query that casts `body` to a number
# fails only if the cast sees a dropped row's value. It runs over the filter in a WHERE alone, and over the layer's
# subquery.
cases = order_cases()
for case in cases:
    for form, safe in [("with the filter in WHERE only", case["safe_with_where_only"]),
                       ("as the layer writes it", case["safe_as_written"])]:
        print(f"{case['shape']}, {form}: the cast {'never saw' if safe else 'saw'} a dropped row's value")
print("filter shapes the layer's subquery keeps safe:", f"{sum(case['safe_as_written'] for case in cases)} of {len(cases)}")
```

Output:

```text
equality, with the filter in WHERE only: the cast never saw a dropped row's value
equality, as the layer writes it: the cast never saw a dropped row's value
IN list, with the filter in WHERE only: the cast never saw a dropped row's value
IN list, as the layer writes it: the cast never saw a dropped row's value
consent semi-join, with the filter in WHERE only: the cast saw a dropped row's value
consent semi-join, as the layer writes it: the cast never saw a dropped row's value
filter shapes the layer's subquery keeps safe: 3 of 3
```

With the filter in the `WHERE` alone, the equality and the `IN` list were safe, and the consent semi-join wasn't: DuckDB ran the cast on reviews whose authors didn't consent. With every column gated, all three are safe, 3 of 3. The first two were safe by the optimizer's choice at 2.0.0, not by any promise, so the test runs on every upgrade. The gate costs evaluating the filters again in each column the query reads.

**Working rule:** Never rely on the engine's evaluation order to keep a user's conditions off rows a filter drops. Make every value a user's query can read depend on the row filters, and test each filter shape on every engine upgrade. Where an engine has a barrier of its own, such as PostgreSQL's `security_barrier` views, use it as well.

## Test who sees what by running queries {#test-who-sees-what}

[Chapter 5](#check-who-sees-what) checks the policy with a who-sees-what table, `lib.policy.WHO_SEES_WHAT`: a list of requests, each with the decision a reviewer expects for it. That tests the decisions, not what users get, which also depends on the layer's rewrite, its masks' SQL and the data. `lib.enforce.observe` runs each case's columns through the layer as the case's user, and compares what comes back with what's stored: how many rows, and which columns differ. A case agrees with its decision when the user is denied exactly when the case says so, gets fewer rows than stored exactly when the case expects a row filter, and gets changed values in exactly the columns the case expects masked:

Example `who-sees-what-in-queries` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib import pipelines, policy
from lib.catalog import open_catalog
from lib.enforce import Enforcer, agrees, observe

catalog = open_catalog(["crm.learners", "learning.reviews", "billing.payments", "learning.enrollments", "learning.courses"])
pipelines.run(catalog, "marketing_audience")          # a copy of learners' names and emails, with no metadata yet
platform = Enforcer(catalog)

# Chapter 5's who-sees-what table, run as queries: what each user gets, against what's stored. A column is "changed"
# when at least one value the user gets differs from the stored one.
agreeing = 0
for case in policy.WHO_SEES_WHAT:
    got = observe(platform, case.user, case.table, case.columns, case.purpose)
    who = case.user + (f" for {case.purpose}" if case.purpose else "")
    if got is None:
        print(f"{who}, {case.table}: denied")
    else:
        print(f"{who}, {case.table}: {got['rows']:,} of {got['stored']:,} rows, changed: {', '.join(got['changed']) or 'none'}")
    agreeing += agrees(case, got)
print("cases where what the user gets agrees with the decision:", f"{agreeing} of {len(policy.WHO_SEES_WHAT)}")

# marketing.audience is a table marketing may read, but nobody has classified its columns, so the policy treats each
# one as sensitive: marketing gets every row, and no value in any column.
rows = platform.sql("select * from marketing.audience", "marketing-1").fetchall()
shown = sum(any(value is not None for value in column) for column in zip(*rows))
print("marketing-1, marketing.audience, which has no metadata, rows:", f"{len(rows):,}")
print("marketing-1, marketing.audience, which has no metadata, columns with a value:", f"{shown} of {len(rows[0])}")
```

Output:

```text
agent-a05, crm.learners: 1,581 of 5,000 rows, changed: none
agent-a05, billing.payments: denied
instructor-17, learning.reviews: 69 of 3,000 rows, changed: body
instructor-17, crm.learners: denied
marketing-1, crm.learners: 1,861 of 5,000 rows, changed: phone
finance-1, billing.payments: 17,562 of 17,562 rows, changed: card_number
analyst-1, billing.payments: 17,562 of 17,562 rows, changed: card_number
analyst-1, crm.learners: 5,000 of 5,000 rows, changed: email, notes
analyst-1, learning.reviews: 3,000 of 3,000 rows, changed: body
analyst-1 for ai-training, learning.reviews: 436 of 3,000 rows, changed: body
assistant-1, learning.reviews: 436 of 3,000 rows, changed: body
someone-else, crm.learners: denied
cases where what the user gets agrees with the decision: 12 of 12
marketing-1, marketing.audience, which has no metadata, rows: 1,829
marketing-1, marketing.audience, which has no metadata, columns with a value: 0 of 5
```

What users get agrees with the decision in 12 of 12 cases. In the output, the EMEA support agent gets their region's learners as stored, marketing the consenting, active learners with `phone` changed, and the analyst every learner with `email` and `notes` changed. The last two lines cover `marketing.audience`, which a pipeline writes and nobody has classified yet. Marketing may read it, and gets 1,829 rows with 0 of 5 columns holding a value, because the policy treats an unclassified column as sensitive.

The test earns its place on a change. Suppose a pull request adds `analyst-1` to the support group for EMEA, so they can help with tickets. It's a two-line change to `governance/users.toml`, a group and the region support's row filter needs, and the example below makes it in memory, then runs the same cases:

Example `group-change-caught` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib import policy
from lib.catalog import open_catalog
from lib.enforce import Enforcer, agrees, observe

# A pull request changes one user in governance/users.toml, in two lines: analyst-1 joins support, with the region
# support's row filter needs, EMEA, to help with tickets.
data = policy.data_document()
data["platform"]["users"]["analyst-1"] = {"groups": ["data-science", "support"], "region": "emea"}
platform = Enforcer(open_catalog(["crm.learners", "learning.reviews", "billing.payments"]),
                    rego=policy.interpreter(data=data))

# The who-sees-what cases, run as queries with the change in place. The cases are unchanged: they say what each
# user should get, and the change was meant to touch support tickets only.
failing = 0
for case in policy.WHO_SEES_WHAT:
    got = observe(platform, case.user, case.table, case.columns, case.purpose)
    if not agrees(case, got):
        failing += 1
        who = case.user + (f" for {case.purpose}" if case.purpose else "")
        print(f"fails, {who}, {case.table}, rows: {got['rows']:,} of {got['stored']:,}")
        print(f"fails, {who}, {case.table}, columns changed: {', '.join(got['changed']) or 'none'}, "
              f"expected: {', '.join(case.masked)}")
print("cases that fail:", f"{failing} of {len(policy.WHO_SEES_WHAT)}")

# Chapter 5's table, which checks the decisions themselves, on the same change.
decisions = [policy.decide(policy.request(c.user, c.table, c.columns, c.purpose), platform.rego) for c in policy.WHO_SEES_WHAT]
print("cases that fail as decisions:", f"{sum(not policy.matches(c, d) for c, d in zip(policy.WHO_SEES_WHAT, decisions))} of {len(decisions)}")
```

Output:

```text
fails, analyst-1, crm.learners, rows: 1,581 of 5,000
fails, analyst-1, crm.learners, columns changed: none, expected: email, notes
fails, analyst-1, learning.reviews, rows: 3,000 of 3,000
fails, analyst-1, learning.reviews, columns changed: none, expected: body
fails, analyst-1 for ai-training, learning.reviews, rows: 436 of 3,000
fails, analyst-1 for ai-training, learning.reviews, columns changed: none, expected: body
cases that fail: 3 of 12
cases that fail as decisions: 3 of 12
```

The change fails 3 of 12 cases, and none of them is about tickets. On `crm.learners`, the analyst now gets 1,581 of 5,000 rows with no column changed: support's region filter applies to them, and the policy's personal-column masks apply only to users outside support, so every email and note comes through as stored. Review text, which a data scientist otherwise can't read at all, or reads with contacts removed when the purpose is AI training, comes through whole. [Chapter 5's decision-level table](#check-who-sees-what) fails on the same cases, 3 of 12; this one shows what the analyst would actually get.

**Working rule:** Run the who-sees-what cases as queries through the enforcement layer on every change to the policies, the users file, the metadata or the layer itself, and fail the build when any case disagrees. Fix a failing case by changing the policy or the users file, and change a case only when the people who own the data agree that what the user should get has changed.

## Hold back small groups in reports {#hold-back-small-groups}

Row filters and masks decide which rows and values a user sees. Aggregates are a second channel: a count or an average over a few people describes those people. The usual defence is a **minimum group size**, below which a reported group is held back. The number is a rule of thumb, not a measurement. One public data-use agreement from the US Centers for Medicare & Medicaid Services sets 11, and adds that "no use of percentages or other mathematical formulas may be used if they result in the display of a cell less than 11" ([CMS-R-0235L](https://www.cms.gov/medicare/cms-forms/cms-forms/downloads/cms-r-0235l.pdf)). The platform uses the same minimum, 11, and keeps it in `governance/enforcement.toml`, where a change is reviewed like a policy change, and `lib.enforce.minimum_group_size` reads it.

The platform sends each instructor a daily course report: learners and average progress per course and learner country. The report job reads learners' countries, which instructors may not read, and instructors may read their own courses' enrollments with each one's progress. Put those together:

Example `small-groups-difference` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib.catalog import open_catalog
from lib.enforce import Enforcer, minimum_group_size

platform = Enforcer(open_catalog(["crm.learners", "learning.courses", "learning.enrollments"]))
minimum = minimum_group_size()
print("minimum group size:", minimum)
count = lambda sql: platform.connection.sql(f"select count(*) from ({sql})").fetchall()[0][0]

# The platform's daily course report for instructor-17: learners and average progress, per course and learner country.
# The report job reads learners' countries, which instructors may not read.
platform.connection.execute("""create view mine as
    select e.course_id, e.progress_pct, e.enrolled_at::date as day, l.country
    from learning.enrollments e join crm.learners l using (learner_id)
    where e.course_id in (select course_id from learning.courses where instructor_id = 17)""")
platform.connection.execute("""create view report as
    select course_id, country, count(*) as learners, avg(progress_pct) as progress from mine group by all""")
print("cells in the report:", count("from report"))
print("cells under the minimum:", count(f"from report where learners < {minimum}"))

# instructor-17 may read their courses' enrollments, with each one's progress. A cell of one learner, matched on its
# progress, names that learner's country.
seen = platform.sql("select course_id, progress_pct from learning.enrollments", "instructor-17").to_arrow_table()
platform.connection.register("seen", seen)
print("cells of one learner:", count("from report where learners = 1"))
print("learners a cell of one names:", count("""from report as cell where learners = 1 and (select count(*) from seen
    where seen.course_id = cell.course_id and seen.progress_pct = cell.progress) = 1"""))
print("cells shown with the minimum:", count(f"from report where learners >= {minimum}"))

# The minimum doesn't stop differencing. An enrollment that arrives alone in its course on its day, in a cell already
# shown, raises that cell by one in the next day's report, and the instructor sees which enrollment arrived.
revealed = count(f"""from mine as m
    where (select count(*) from mine as o where o.course_id = m.course_id and o.day = m.day) = 1
      and (select count(*) from mine as o where o.course_id = m.course_id and o.country = m.country and o.day < m.day) >= {minimum}""")
print("learners whose country the daily report reveals anyway:", f"{revealed} of {count('from mine')}")
```

Output:

```text
minimum group size: 11
cells in the report: 63
cells under the minimum: 51
cells of one learner: 6
learners a cell of one names: 3
cells shown with the minimum: 12
learners whose country the daily report reveals anyway: 92 of 482
```

Of the 63 cells of `instructor-17`'s report, 51 are under the minimum, and 6 hold one learner each. A cell of one names its learner's country to anyone who can find that learner, and the instructor can: matching the cell's average progress against their own enrollments names 3 learners exactly. With the minimum, 12 cells are shown and none of those lookups works.

The minimum doesn't stop differencing. An enrollment that arrives alone in its course on its day, into a cell that's already shown, raises that cell by one in the next day's report, and the instructor sees which enrollment arrived. That reveals the country of 92 of 482 learners. This is the attack Denning, Denning and Schwartz called a tracker: they showed that "the compromise of small query sets can in fact almost always be accomplished with the help of characteristic formulas called trackers" ([Denning et al., 1979](https://doi.org/10.1145/320064.320069)). Snowflake, which enforces a minimum group size in its engine, says its policies "do not guarantee a malicious actor could not use deliberate queries to obtain potentially sensitive data" ([Snowflake aggregation policies](https://docs.snowflake.com/en/user-guide/aggregation-policies)). Against differencing, we recommend noise, as in differential privacy ([Dwork and Roth, 2014](https://doi.org/10.1561/0400000042)), rather than higher thresholds, and *Privacy Engineering for Data Teams* covers it.

**Working rule:** Hold back every reported group below the minimum in `governance/enforcement.toml`, and treat the minimum as protection against looking one person up, never against differencing. Don't break a report down by an attribute its reader may not read, sent to a reader who can see the rows behind it: the instructor's report by country is a lookup table for countries. Drop the breakdown, or report it only after it has been made noisy.

## Hand the same policies to an engine that enforces them {#engine-enforcement}

In production, enforcement belongs in the engine every tool queries through, because Saltzer and Schroeder's principle of complete mediation holds that "every access to every object must be checked for authority" ([Saltzer and Schroeder, 1975](https://web.mit.edu/Saltzer/www/publications/protection/Basic.html)), and a policy enforced in one tool and not another fails it. Trino, an open-source distributed SQL engine, can take its access control from Open Policy Agent (OPA) through a plugin, and [chapter 5](#shape-the-request-like-trinos) shaped the platform's requests like the plugin's so the same policy could serve both. Trino 484 offers file-based, OPA and Ranger access control, and none for Cedar ([Trino 484, Security](https://trino.io/docs/484/security.html)).

The plugin asks OPA separate questions at separate URIs ([Trino 484, OPA access control](https://trino.io/docs/484/security/opa-access-control.html)):

- **Whether to allow** an operation, such as `SelectFromColumns`, answered with a boolean `allow`.
- **Row filters**, `GetRowFilters`, for a table. OPA answers with a list of `{"expression": ...}`, and "each expression essentially behaves like an additional WHERE clause". The URI is optional: "if not set no row filtering is applied".
- **Column masks**, `GetColumnMask`, for one column, or a batch of columns at `opa.policy.batch-column-masking-uri`. "Only a single column mask may be returned for a given column."

The operation names and where each request puts its table or column are in the plugin's source at tag 484 ([`OpaAccessControl.java`](https://github.com/trinodb/trino/blob/484/plugin/trino-opa/src/main/java/io/trino/plugin/opa/OpaAccessControl.java), [`OpaHighLevelClient.java`](https://github.com/trinodb/trino/blob/484/plugin/trino-opa/src/main/java/io/trino/plugin/opa/OpaHighLevelClient.java)). The documentation's batch-mask policy reads `filterResources[i].catalogName` where its own request example nests those fields under `.column`, so as printed it wouldn't match. Build the platform's requests in those shapes and give them to its policy:

Example `trino-requests` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
import json

from lib import metadata, policy
from lib.enforce import row_filter

# The platform's policy, with a support agent added before anyone set their region (chapter 5's missing-region case).
data = policy.data_document()
data["platform"]["users"]["agent-new"] = {"groups": ["support"]}
rego = policy.interpreter(data=data)
described = metadata.load()


def trino_request(user: str, operation: str, resource: dict | None = None) -> dict:
    """A request in the shape Trino 484's OPA plugin sends (OpaAccessControl, OpaHighLevelClient)."""
    action = {"operation": operation} | ({"resource": resource} if resource else {})
    return {"context": {"identity": {"user": user, "groups": []}, "softwareStack": {"trinoVersion": "484"}}, "action": action}


# Trino asks `allow` about every operation: ExecuteQuery before any query runs, AccessCatalog for each catalog it names.
for operation, resource in [("ExecuteQuery", None), ("AccessCatalog", {"catalog": {"name": "platform"}})]:
    print(f"allow, {operation}, agent-a05:", policy.decide(trino_request("agent-a05", operation, resource), rego)["allow"])

# GetRowFilters names a table. The policy's row_filters rule on its own skips `allow` and its missing-attribute guard,
# so for agent-new it returns no filter, which Trino reads as no filtering. The answer comes from the decision instead,
# for the same read asked as SelectFromColumns: its filters in Trino's SQL, or a filter that keeps no rows.
for user, schema, table in [("agent-a05", "support", "tickets"), ("instructor-17", "learning", "reviews"),
                            ("agent-new", "support", "tickets")]:
    request = trino_request(user, "GetRowFilters", {"table": {"catalogName": "platform", "schemaName": schema, "tableName": table}})
    print(f"GetRowFilters, {user}, {schema}.{table}, the rule alone:",
          json.dumps(policy.evaluate(rego, "data.platform.access.row_filters", request)))
    decision = policy.decide(policy.request(user, f"{schema}.{table}", []), rego)
    columns = {c.name: "" for c in described[f"{schema}.{table}"].columns.values()}
    filters = [{"expression": row_filter(rule, columns, table=None).sql("trino")} for rule in decision["row_filters"]]
    print(f"GetRowFilters, {user}, {schema}.{table}, answered:", json.dumps(filters if decision["allow"] else [{"expression": "false"}]))

# GetColumnMask names one column, under action.resource.column. The policy reads the columns of a SelectFromColumns
# request instead, so it masks nothing here until the request is translated.
column = {"catalogName": "platform", "schemaName": "crm", "tableName": "learners", "columnName": "email", "columnType": "varchar"}
decision = policy.decide(trino_request("analyst-1", "GetColumnMask", {"column": column}), rego)
print("GetColumnMask as sent, analyst-1, crm.learners.email:", json.dumps(decision["column_masks"]), decision["reasons"][0])
translated = policy.request("analyst-1", "crm.learners", [column["columnName"]])
print("GetColumnMask translated, analyst-1, crm.learners.email:", json.dumps(policy.decide(translated, rego)["column_masks"]))
```

Output:

```text
allow, ExecuteQuery, agent-a05: False
allow, AccessCatalog, agent-a05: False
GetRowFilters, agent-a05, support.tickets, the rule alone: [{"column": "support_region", "equals": "emea"}]
GetRowFilters, agent-a05, support.tickets, answered: [{"expression": "support_region = 'emea'"}]
GetRowFilters, instructor-17, learning.reviews, the rule alone: [{"column": "course_id", "in": [2, 75, 80, 87, 103, 134]}]
GetRowFilters, instructor-17, learning.reviews, answered: [{"expression": "course_id IN (2, 75, 80, 87, 103, 134)"}]
GetRowFilters, agent-new, support.tickets, the rule alone: []
GetRowFilters, agent-new, support.tickets, answered: [{"expression": "false"}]
GetColumnMask as sent, analyst-1, crm.learners.email: {} GetColumnMask is not an operation this policy allows
GetColumnMask translated, analyst-1, crm.learners.email: {"email": "pseudonymize"}
```

The policy's `allow` admits only `SelectFromColumns`, so pointed at Trino unchanged it would deny the checks Trino makes first: `allow` is `False` for `ExecuteQuery`, asked before any query runs, and for `AccessCatalog`. The `row_filters` rule doesn't test the operation, so it answers `GetRowFilters`, but on its own it skips `allow` and [chapter 5](#deny-by-default-then-allow-by-role)'s missing-attribute guard: for `agent-new`, a support agent with no region yet, it returns `[]`, which Trino reads as no filtering. So the answer has to come from the decision for the same read, asked as `SelectFromColumns`: its filters, written in Trino's SQL by the same [`row_filter`](#build-row-filters-from-data) the rewrite uses, or, when it denies the read, `[{"expression": "false"}]`, which keeps no rows.

`GetColumnMask` names the column under `action.resource.column`, while the policy reads a `SelectFromColumns` request's columns, so as sent it masks nothing and the policy rejects the operation; translated, it gets `pseudonymize`. In production, the translations, the check of `allow` and the Trino SQL belong in a Rego module beside the policy, so OPA can answer Trino itself; the book's examples run no OPA server, so the example shows what that module must return. One more piece maps onto Trino directly: the consent filter reads `crm.learners`, which the assistant may not, and Trino lets a filter carry an `identity` to run as, "such that a filter can target a column the requesting user cannot see".

Since 1.9.0, OPA's Compile API can also write SQL `WHERE` clauses from a policy by partial evaluation ([OPA v1.9.0](https://github.com/open-policy-agent/opa/releases/tag/v1.9.0), [Data filtering with OPA](https://www.openpolicyagent.org/docs/filtering)), but it needs an OPA server, which the examples don't run.

**Working rule:** Put enforcement in the engine every tool queries through, and keep one policy for it and for any rewrite like this chapter's. With Trino, answer every operation the plugin asks about, set both the row-filter and the column-mask URIs, since without them it applies no filters or masks, and return row filters only from a decision that allows the read. Build your tests from the request shapes in the plugin's source rather than from its documentation's example policies.

## Query on someone's behalf {#query-on-someones-behalf}

An assistant that answers questions from the warehouse is one more user of the enforcement layer, with a choice to make: whose identity does its query carry? The platform's course assistant, `assistant-1`, has its own access, for reviews by consenting learners. When it answers a person, it must query as that person, so the answer contains exactly what they could have read themselves. OWASP's guidance for language-model applications says the same: "Implement authorization in downstream systems rather than relying on an LLM to decide if an action is allowed or not" ([OWASP LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)). The assistant itself belongs to *Data Assistants in Practice*; this section is about its queries.

`instructor-17` asks the assistant how their courses' reviews look, and the assistant writes a query. The tool it calls takes the user from the signed-in session, never from the model or the conversation, so no prompt can change who the query runs as:

Example `assistant-on-behalf` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.21:

```python
from lib import policy
from lib.catalog import open_catalog
from lib.enforce import Enforcer

platform = Enforcer(open_catalog(["crm.learners", "learning.reviews"]))
courses = set(policy.data_document()["platform"]["instructor_courses"]["17"])     # instructor-17's own courses


def query_tool(session_user: str):
    """The tool the course assistant calls to query the warehouse. The model writes the SQL; the user it runs as comes
    from the signed-in session, never from the model or the conversation."""
    return lambda sql: platform.sql(sql, user=session_user).fetchall()


# instructor-17 asks the assistant how their courses' reviews look. The assistant writes this query.
question = "select course_id, count(*) as reviews, round(avg(rating), 2) as rating from learning.reviews group by all"
for runs_as in ["instructor-17", "assistant-1"]:
    answer = query_tool(runs_as)(question)
    print(f"run as {runs_as}, courses in the answer:", len(answer))
    print(f"run as {runs_as}, reviews behind it:", sum(reviews for _, reviews, _ in answer))
    mine = [row for row in answer if row[0] in courses]
    print(f"run as {runs_as}, instructor-17's reviews behind it:", sum(reviews for _, reviews, _ in mine))
```

Output:

```text
run as instructor-17, courses in the answer: 6
run as instructor-17, reviews behind it: 69
run as instructor-17, instructor-17's reviews behind it: 69
run as assistant-1, courses in the answer: 130
run as assistant-1, reviews behind it: 436
run as assistant-1, instructor-17's reviews behind it: 7
```

Run as `instructor-17`, the answer covers their 6 courses and 69 reviews. Run as the assistant, it covers 130 courses, most of them other instructors', and only 7 of the instructor's own reviews, the ones whose authors consented to AI training. The assistant's identity is wrong both ways: it shows the instructor what they may not see, and hides what they may. The same holds for retrieval: an assistant grounded on governed text needs "permission-aware vector and embedding stores" ([OWASP LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)).

**Working rule:** Run an assistant's queries with the identity of the person it answers, taken from their authenticated session, and let the enforcement layer apply that person's decision. Use the assistant's own identity only for work it does for no one in particular, such as a nightly summary of consented reviews for the course pages, and record both identities in the audit log. Whoever builds the assistant's training set queries as themselves, with the purpose `ai-training`, as [chapter 9](#admit-consented-reviews) does.

## What goes wrong in production {#enforcement-in-production}

An enforcement layer fails by letting a read through that nobody tested, and most of these failures look like correct answers:

- **`SELECT *` slips past on a table missing from the schema.** `qualify` leaves the star unexpanded and raises nothing. Deny every table the catalog doesn't hold, and rebuild the schema whenever the catalog changes.
- **Aggregates leak small groups.** A cell of one names its member, and differences between reports name members of cells that pass any minimum, as [the report example](#hold-back-small-groups) showed. Set the minimum, and remove breakdowns by attributes the reader may not read.
- **Joins and copies bring masked columns back.** A pipeline that runs with full access, such as the one that writes `marketing.audience`, copies `email` into a table of its own, protected only by its own classification: unclassified, it's hidden from everyone, as [the who-sees-what test](#test-who-sees-what) showed, and classified `internal` by mistake, it's shown to anyone who may read the table. [Chapter 4](#classifications-from-lineage) propagates classifications along lineage to catch that. Unmasked columns re-identify through joins too: Sweeney found 87% of the US population likely unique on ZIP code, gender and date of birth in 1990 census data ([Sweeney, 2002](https://dataprivacylab.org/dataprivacy/projects/kanonymity/kanonymity.pdf)), and Golle, counting again, found 61% on the same 1990 data and 63% on 2000's ([Golle, 2006](https://doi.org/10.1145/1179601.1179615)). Rocher and colleagues estimate, from a model fitted to census data, that 15 demographic attributes would make 99.98% of people in Massachusetts unique ([Rocher et al., 2019](https://doi.org/10.1038/s41467-019-10933-3)).
- **Direct file reads bypass the rewrite.** `read_parquet`, a path in `FROM` and table functions read data without naming a table. Deny them in the rewrite, and turn off `enable_external_access`, which DuckDB then won't turn back on: "Cannot enable external access while database is running". `lock_configuration` keeps every other setting as the layer left it; set it once the layer's connection is fully configured ([Securing DuckDB](https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview)), not when it's created, since [chapter 8](#cross-check-the-query-log) starts DuckDB's query log after that. Anyone who can read the warehouse's files in storage needs no SQL at all, so storage permissions are part of enforcement.
- **Identifier case decides what a name matches.** A layer that matched names without normalizing them would let `"LEARNERS"`, which DuckDB resolves to `learners`, reach the raw table, as [the first section](#find-what-a-query-reads) showed. Normalize with the dialect of the engine that runs the query before matching any name.
- **Error messages print values.** DuckDB's cast errors include the value. The table rewrite makes it a masked one, and [the gate on each column](#gate-columns-on-row-filters) keeps dropped rows out of reach, but the message still reaches the user unless something stops it. Return a generic error at the service boundary, as `lib.enforce.answer` does, and log the engine's message where only the platform team reads it, apart from the audit log, which [chapter 8](#keep-values-out-of-the-record) keeps free of values. PostgreSQL warns that plans and timings remain covert channels even behind a security barrier ([PostgreSQL 18, Rules and Privileges](https://www.postgresql.org/docs/18/rules-privileges.html)).
- **DuckDB is not a security boundary.** "DuckDB executes SQL with the full privileges of the user running it, much like a shell or scripting interpreter" ([Securing DuckDB](https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview)). A rewrite inside the same process protects data only while users can't reach DuckDB by any other route. Treat this chapter's layer as a tested model of what an engine such as Trino enforces, and enforce there in production.

## What this chapter decided {#enforcement-decisions}

- **Enforcement replaces tables, not columns.** Each catalog table in a query becomes a subquery generated from the user's decision. Rewriting column references is kept only to show that it leaks.
- **The layer fails closed.** Its sources are an allowlist of catalog tables, CTEs in scope and subqueries. It denies functions with side effects, parameters and anything but a single query. Columns a query doesn't read are typed `NULL`s, and the ones it reads are gated on the row filters.
- **Users get one generic error** from `answer`, and DuckDB's message goes to the platform team.
- **Masks are SQL in one place.** The policy names masks; `lib.enforce` writes their SQL. Pseudonyms are keyed with a secret only the layer holds, passed as a parameter.
- **Row filters are built from data,** with values as literals. Consent is a semi-join the layer runs with its own access, and an unknown consent counts as no.
- **Who sees what is tested as queries:** chapter 5's cases run through the layer on every change.
- **Reports hold back groups under the minimum group size,** 11 in `governance/enforcement.toml`, and don't break down by attributes their readers may not read.
- **Assistants query as the person they answer,** with the identity taken from the session.
- **In production, the engine enforces:** Trino with OPA, from the same policy, with both URIs set and row filters answered only from an allowed decision.
