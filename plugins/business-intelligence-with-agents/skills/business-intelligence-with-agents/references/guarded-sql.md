---
title: "Business Intelligence with Agents"
chapter: "Let the agent write SQL inside guards"
chapter_id: guarded-sql
book: business-intelligence-with-agents
edition: 2026.11.7
verified: 2026-11-10
edition_code: ZNJE-JAVW
canonical: https://rollingedition.com/business-intelligence-with-agents/guarded-sql
license: CC BY 4.0
attribution: "“Let the agent write SQL inside guards,” chapter 7 of Business Intelligence with Agents, Edition 2026.11.7, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/business-intelligence-with-agents/guarded-sql. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Let the agent write SQL inside guards

By the end of this chapter, you can handle the questions no metric covers by letting the agent write SQL that runs read-only on a database holding only the rows and columns its role may read, and that is parsed, checked against an allowlist of tables, bounded in rows, size, cost and time, repaired once from an error, and transpiled to your warehouse's dialect. You can also tell from the golden questions when such a question should become a metric instead.

[Chapter 6](#metrics-first) routed the shop's questions to governed metrics first. The shop is the online outdoor-gear shop in three regions that this book follows throughout, and its semantic layer holds ten metrics. That covers the questions the finance team asks every month, but not the rest: how much revenue came from orders that included a tent, or what share of sessions converted. Chapter 6's agent declines those, which is honest and frustrating. We call these questions the long tail, and ten of the shop's golden questions are in it, listed in [the section on promoting them](#metric-or-sql).

For the long tail, the agent has to write SQL. [Chapter 4](#layered-context) already had it do so, and ran the SQL as written on a connection that can't write. This chapter puts guards around it: guarded SQL runs on a database holding only what the agent may read, checked first and inside limits. DuckDB's own documentation says to "Treat SQL in DuckDB like code in Bash or Python. Do not execute SQL from untrusted sources without proper sandboxing" ([DuckDB](https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview.html)). A model's SQL is SQL from an untrusted source in that sense, whoever typed the question.

So the security boundary is the database: the agent connects read-only, to a database that holds only views limiting the rows and columns its role may see. The rest of the chapter, the parser's checks in `lib/sql_guard.py`, the timer and the cost check, is a teaching layer and defence in depth. It catches mistakes, gives the model refusals to repair from, and bounds cost and time, but it doesn't keep data from a role. Drafts of the parser were bypassed, as [the replay section](#replay-the-bypasses) shows, and any parser can be.

## Give the agent a database with only what it may read {#least-privilege-database}

Least privilege means that the agent's SQL runs on a connection that can reach what the agent may query and nothing else. It comes before any check on the SQL, because a check is a judgement about text, and when the judgement is wrong, the database decides what the query reaches.

[Chapter 1](#meet-the-shop)'s `warehouse.connect()` is read-only, but it sees everything: the `raw` schema, the legacy mart and the semantic views. So `agent_warehouse()` in `lib/warehouse.py` copies the seven marts the agent may read, named one by one in `AGENT_TABLES`, into a second database file, and opens it read-only. File access and extensions are off, memory is limited to 1 GB and each query to two threads, and the settings are locked so that a query can't switch any of it back on. The example sends the agent's database six attempts to reach past it, with no guard in front, and reads what DuckDB's catalog still shows.

Example `agent-warehouse` (Python 3.12.15 · duckdb 2.0.0), passing in Edition 2026.11.7:

```python
"""The agent's own database: copies of the allowed marts, read-only, with files, extensions and settings locked."""
import duckdb

from lib.warehouse import agent_warehouse, connect

shop = connect()
agent = agent_warehouse(shop)                 # a second file: the seven allowed marts, copied, and nothing else
(shop_tables,), = shop.execute("SELECT count(*) FROM duckdb_tables()").fetchall()
print("tables in the shop's warehouse:", shop_tables)
tables = agent.execute("SELECT schema_name || '.' || table_name FROM duckdb_tables() ORDER BY 1").fetchall()
print("tables in the agent's database:", len(tables))
print("the agent's tables:", ", ".join(name for (name,) in tables))

(source,), = shop.execute("SELECT path FROM duckdb_databases() WHERE database_name = 'shop'").fetchall()
ATTEMPTS = {                                  # sent straight to the agent's database, with no guard in front
    "raw table": "SELECT count(*) FROM raw.customers",
    "legacy mart": "SELECT sum(revenue) FROM analytics.orders_legacy",
    "attach the shop's file": f"ATTACH '{source}' AS shop (READ_ONLY)",
    "read a file": "SELECT * FROM read_csv('data/golden/questions.toml')",
    "load an extension": "LOAD httpfs",
    "turn file access back on": "SET enable_external_access = true",
}
for label, sql in ATTEMPTS.items():
    try:
        agent.execute(sql).fetchall()
        print(f"{label}: allowed")
    except duckdb.Error as e:
        kind, message = str(e).splitlines()[0].split(": ", 1)
        print(f"{label}: {kind}, {message.split(' - ')[-1]}")   # the file's path is left out of the output

# What no setting hides: DuckDB's own catalog, which every database has.
(listed,), = agent.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'analytics'").fetchall()
print("catalog, tables it lists:", listed)
(settings,), = agent.execute("SELECT count(*) FROM duckdb_settings()").fetchall()
print("catalog, settings it lists:", settings)
(paths,), = agent.execute("SELECT count(*) FROM duckdb_databases() WHERE path IS NOT NULL").fetchall()
print("catalog, database files it names:", paths)
```

Output:

```text
tables in the shop's warehouse: 16
tables in the agent's database: 7
the agent's tables: analytics.dim_customers, analytics.dim_date, analytics.dim_products, analytics.fct_order_lines, analytics.fct_orders, analytics.fct_refunds, analytics.fct_sessions
raw table: Catalog Error, Table with name "raw.customers" does not exist because schema "raw" does not exist.
legacy mart: Catalog Error, Table with name orders_legacy does not exist!
attach the shop's file: Permission Error, file system operations are disabled by configuration
read a file: Permission Error, file system operations are disabled by configuration
load an extension: Permission Error, Loading external extensions is disabled through configuration
turn file access back on: Invalid Input Error, the configuration has been locked
catalog, tables it lists: 7
catalog, settings it lists: 170
catalog, database files it names: 1
```

The shop's warehouse has 16 tables, and the agent's database has 7. A query on `raw.customers` gets `Catalog Error, Table with name "raw.customers" does not exist because schema "raw" does not exist.` Nothing refused it; the schema isn't there. The legacy mart isn't there either. Attaching the shop's file or reading any other file fails with `Permission Error, file system operations are disabled by configuration`, loading an extension fails too, and a `SET` that would turn file access back on fails with `Invalid Input Error, the configuration has been locked`. The DuckDB documentation calls such settings "defense-in-depth" and adds that "they are not a substitute for proper sandboxing" ([DuckDB](https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview.html)). Here the sandbox is the database that holds only the allowed marts, and the settings keep it closed.

The last three lines show what no setting hides: DuckDB's catalog, such as `information_schema` and `duckdb_settings()`, which describes the database itself. In the agent's database it lists 7 tables, all of them ones the agent may read. It also lists 170 settings and names 1 database file with its path on disk. The database can't refuse those reads, so [the allowlist section](#read-only-allowlist) refuses them in the parser.

**Working rule:** Run the agent's SQL on a connection that can reach only what the agent may query: a role with only those grants, or, in DuckDB, a read-only database file that holds only the allowed tables, with file access and extension loading off and its settings locked. Name the allowed tables one by one. Then list what the database can't hide, such as its catalog, and refuse those reads in the guard.

## Give each role a database of views {#views-per-role}

[The agent's database](#least-privilege-database) leaves out whole tables, but the shop's people don't all see the same rows and columns of the rest. Five roles ask the agent questions, written down in `examples/data/shop/roles.toml`, which [chapter 9](#who-may-see-what) explains. EMEA's regional lead sees EMEA's rows only, finance sees customers with names and emails masked, and support sees orders without revenue. A role's view of a table returns those rows, with a masked column holding a constant and a denied column left out. The view, not the parser, should decide what the role reads.

Real warehouses do this with grants. PostgreSQL's documentation shows a view that hides a column, granted to a role that can't read the table under it: "because of the GRANT, the assistant can run a SELECT on the phone_number view" ([PostgreSQL](https://www.postgresql.org/docs/current/rules-privileges.html)). It warns that such views "cannot be used to reliably conceal the data in unseen rows unless the security_barrier flag has been set". Snowflake's secure views are meant "to limit access to sensitive data that should not be exposed to all users of the underlying table(s)" ([Snowflake](https://docs.snowflake.com/en/user-guide/views-secure)). Row access policies ([Snowflake](https://docs.snowflake.com/en/user-guide/security-row-intro)) and masking policies attach the same rules to the table itself, and a masking policy "is applied to the column at every location where the column appears" ([Snowflake](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro)). So in production, the agent's warehouse user has a read-only role with `SELECT` on the role's secure views and nothing else.

DuckDB has no roles or `GRANT`, and a view can be read only by a connection that can read the tables under it. So `agent_warehouse(con, policy=...)` builds the role its own database: each table in it is the role's view of a mart, written out as a table of the same name, and opened read-only with [the same locked settings](#least-privilege-database). The views come from chapter 9's `Policy.subquery()`, so each rule is written once. The example sends three queries that this chapter's guard accepts, since it knows tables and columns but not roles, straight to each role's database, then replays a catalog bypass a draft of the guard let through.

Example `role-database` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Each role's own database: SQL that chapter 7's guard accepts, sent with no guard, reaches only the role's views."""
import duckdb

from lib.guard_attacks import ATTEMPTS
from lib.policies import policy_for
from lib.sql_guard import SqlGuard
from lib.warehouse import agent_warehouse, connect

shop = connect()
marts = agent_warehouse(shop)                 # every allowed mart, whole: no role's limits
guard = SqlGuard(marts)                       # chapter 7's guard knows tables and columns, not roles
roles = {"EMEA's regional lead": policy_for("regional_lead", "EMEA"), "finance": policy_for("finance"),
         "support": policy_for("support")}
QUERIES = {"EMEA's regional lead": "SELECT count(DISTINCT region) AS regions FROM analytics.fct_orders",
           "finance": "SELECT count(*) AS n FROM analytics.dim_customers WHERE email LIKE 'customer-0004%'",
           "support": "SELECT sum(net_revenue_eur) AS revenue FROM analytics.fct_orders"}


def first_value(con, sql):
    try:
        return con.execute(sql).fetchall()[0][0]
    except duckdb.Error as e:
        return str(e).splitlines()[0]


for role, sql in QUERIES.items():
    database = agent_warehouse(shop, policy=roles[role])     # the role's database: its views of the marts only
    guard.check(sql)                                         # raises if the guard refuses; it doesn't
    print(f"{role}, guard accepts: yes")
    print(f"{role}, every mart: {first_value(marts, sql)}")
    print(f"{role}, role's database: {first_value(database, sql)}")

# A parser bypass a draft of the guard let through: a CTE named like DuckDB's catalog, which lists every table's SQL.
support = agent_warehouse(shop, policy=roles["support"])
listed = " ".join(str(row) for row in support.execute(ATTEMPTS["CTE named duckdb_tables"]).fetchall())
print(f"support, catalog bypass, tables listed: {listed.count('CREATE TABLE')}")
print(f"support, catalog bypass, names a revenue column: {'net_revenue_eur' in listed}")
print(f"support, a write: {first_value(support, 'DELETE FROM analytics.fct_orders')}")
```

Output:

```text
EMEA's regional lead, guard accepts: yes
EMEA's regional lead, every mart: 3
EMEA's regional lead, role's database: 1
finance, guard accepts: yes
finance, every mart: 10
finance, role's database: 0
support, guard accepts: yes
support, every mart: 4019333.37
support, role's database: Binder Error: Referenced column "net_revenue_eur" not found in FROM clause!
support, catalog bypass, tables listed: 6
support, catalog bypass, names a revenue column: False
support, a write: Invalid Input Error: Cannot execute statement of type "DELETE" on database "agent" which is attached in read-only mode!
```

Each query passed the guard, and each got only what the role's views hold. Counting regions in the orders table gives 3 on every mart and 1 on the lead's database. Finance's search for emails that start `customer-0004` matches 10 customers on every mart and 0 on finance's, because every email there is `(masked)`. Support's sum of net revenue fails with `Binder Error: Referenced column "net_revenue_eur" not found in FROM clause!`, because the column isn't there. The bypass, a CTE named like DuckDB's catalog, lists 6 tables in support's database, and whether any names a revenue column is False. A write fails as read-only.

**Working rule:** Make the database the boundary: connect the agent read-only, as a role that can read only views limiting the rows and columns that role may see, through secure views, row access policies and masking policies where the warehouse has them. In DuckDB, give each role its own read-only database of those views. Generate the views from the same policy the rest of your stack uses, and test them with queries the parser accepts.

## Parse the SQL before it runs {#parse-before-running}

A guard can only check what it can see, and SQL as text shows almost nothing: a check for the word `DELETE` misses a comment, a quoted name and a dozen ways to write the same statement. Parsing turns the text into a tree, with one node for each statement, table, column and function, so every check that follows asks a question about nodes instead of characters. sqlglot, at 30.30.0, parses SQL in DuckDB's dialect and many others, and the same tree later becomes SQL again. Its README warns about what parsing doesn't do: "SQLGlot is a transpiler, not a validator. A query that parses successfully may still fail at execution time" ([sqlglot](https://raw.githubusercontent.com/tobymao/sqlglot/v30.27.0/README.md)). So the guard parses first, then checks the tree against the warehouse it will run on.

The SQL to check is SQL the model already wrote. For `gq-017`, net revenue in each of the shop's countries in 2025, [chapter 4](#measure-each-layer)'s recorded reply with all four layers of context grouped by a country column of the calendar table. The example parses that reply, lists what the tree holds, and runs the guard's `check()` on it. Then it shows that one string can hold two statements, and where a broken query stops parsing.

Example `parse-agent-sql` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Parse the SQL a model wrote before it runs: one statement, the tables it reads, and a column that doesn't exist."""
import duckdb
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from lib.context import LAYERS, build_context
from lib.golden import load_golden
from lib.model import RecordedModel
from lib.prompts import layered_sql_messages
from lib.sql_guard import GuardError, allowed_schema, check
from lib.tools import extract_sql
from lib.warehouse import agent_warehouse, connect

con = connect()
question = next(q for q in load_golden() if q.question_id == "gq-017")
context = build_context(con, question.question, LAYERS)          # chapter 4's context, every layer
sql = extract_sql(RecordedModel("context-layers").complete(layered_sql_messages(context.text, question.question)))
print(f"question: {question.question}\n{sql}")

tree = sqlglot.parse_one(sql, read="duckdb")
print("root:", type(tree).__name__)
print("tables read:", ", ".join(f"{t.db}.{t.name} AS {t.alias}" for t in tree.find_all(exp.Table)))
print("columns named:", ", ".join(sorted({f"{c.table}.{c.name}" for c in tree.find_all(exp.Column) if c.table})))

try:
    check(sql, allowed_schema(agent_warehouse(con)))       # the allowlist: the agent's database's tables
except GuardError as e:
    print("guard refuses:", e.kind)
    message, columns = str(e).split(". The tables it reads have only these columns: ")
    print("guard message:", message)
    print("message then lists the columns of:", ", ".join(part.split(" has ")[0] for part in columns.split("; ")))
try:
    con.execute(sql)
except duckdb.Error as e:
    print("DuckDB, had it run:", str(e).splitlines()[0])

statements = sqlglot.parse("SELECT 1; DROP TABLE analytics.fct_orders", read="duckdb")
print("statements in one string:", ", ".join(type(s).__name__ for s in statements))
try:
    sqlglot.parse_one("SELECT region, sum(net_revenue_eur FROM analytics.fct_orders GROUP BY region", read="duckdb")
except ParseError as e:
    error = e.errors[0]
    print("parse error fields:", ", ".join(sorted(error)))
    print(f"parse error: {error['description']}\nparse error line: {error['line']}\nparse error column: {error['col']}")
```

Output:

```text
question: What was net revenue in each of our countries in 2025?
SELECT d.country, round(sum(o.net_revenue_eur), 2) AS net_revenue
FROM analytics.fct_orders AS o
JOIN analytics.dim_date AS d ON d.date_day = o.order_date_local
WHERE o.status <> 'cancelled'
  AND d.calendar_year = 2025
GROUP BY d.country
ORDER BY net_revenue DESC
root: Select
tables read: analytics.fct_orders AS o, analytics.dim_date AS d
columns named: d.calendar_year, d.country, d.date_day, o.net_revenue_eur, o.order_date_local, o.status
guard refuses: column
guard message: Unknown column: country
message then lists the columns of: analytics.fct_orders, analytics.dim_date
DuckDB, had it run: Binder Error: Table "d" does not have a column named "country"
statements in one string: Select, Drop
parse error fields: col, description, end_context, highlight, into_expression, line, start_context
parse error: Expecting )
parse error line: 1
parse error column: 39
```

The tree's root is a `Select`, and it reads analytics.fct_orders AS o, analytics.dim_date AS d. A parser alone would let `d.country` through. `check()` qualifies every column against the columns of the tables the query is allowed to read, with sqlglot's `qualify`, which resolves each column to its table and raises an error for a column it can't place. Here it refuses with `column`: `Unknown column: country`. The message then lists the columns of analytics.fct_orders, analytics.dim_date, which is what the model needs to fix the query. Run as written, the query would have failed in DuckDB with `Binder Error: Table "d" does not have a column named "country"`.

The last lines of the output are the parser's other reports. `SELECT 1; DROP TABLE analytics.fct_orders` is two statements, Select, Drop, so the guard accepts exactly one. A query missing a closing parenthesis raises sqlglot's `ParseError`, whose `errors` list gives each problem's col, description, end_context, highlight, into_expression, line, start_context. For the example's broken query, the description is `Expecting )`, at line 1, column 39. The guard passes the description, line and column to the model, as [the repair section](#repair-once) uses.

**Working rule:** Parse the agent's SQL into a tree before anything runs, in the dialect of the warehouse that will run it, and accept exactly one statement. Check nodes, never text. Treat a query that parses as a query whose shape you can now inspect, not as one that is valid, and resolve its columns against the tables it may read before you send it to the warehouse.

## Allow only read-only queries on known tables {#read-only-allowlist}

With the agent's SQL [parsed into a tree](#parse-before-running), the guard can ask two questions of it: does it only read, and does it read only what it may? Checking the statement at the root isn't enough: in DuckDB a common table expression, a CTE, can hold a `DELETE` with `RETURNING` inside a `SELECT`. So the guard accepts only a query at the root, and then walks every node of the tree and refuses any statement that writes, changes settings or reaches outside the warehouse.

The example sends one hostile query, whose CTE deletes every refund over 50 euros and whose outer `SELECT` counts them, through the guard, straight to the agent's read-only database, and to a writable copy of the shop in a temporary folder.

Example `block-a-delete` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""A DELETE hidden in a CTE: the root says SELECT, the tree walk finds the DELETE, and the read-only warehouse refuses it.

The attack runs for real only on a throwaway copy of the shop, built from the same seed in a temporary folder.
"""
import tempfile
from pathlib import Path

import duckdb
import sqlglot
from sqlglot import exp

from lib.sql_guard import GuardError, SqlGuard
from lib.warehouse import agent_warehouse, build, connect

ATTACK = """WITH gone AS (DELETE FROM analytics.fct_refunds WHERE amount_eur > 50 RETURNING refund_id)
SELECT count(*) AS refunds_over_50 FROM gone"""

tree = sqlglot.parse_one(ATTACK, read="duckdb")
print("root:", type(tree).__name__)
print("statements in the tree:", ", ".join(type(n).__name__ for n in tree.walk() if isinstance(n, (exp.Query, exp.DML))))

agent = agent_warehouse(connect())                      # the agent's read-only database
try:
    SqlGuard(agent).run(ATTACK)
except GuardError as e:
    print(f"guard refuses ({e.kind}): {e}")
try:
    agent.execute(ATTACK)                                 # past the guard, straight to the read-only database
except duckdb.Error as e:
    print("read-only database:", str(e).splitlines()[0])

with tempfile.TemporaryDirectory() as folder:             # a writable copy, deleted when the block ends
    path = Path(folder) / "shop.duckdb"
    build(path)
    with duckdb.connect(str(path)) as writable:
        (before,), = writable.execute("SELECT count(*) FROM analytics.fct_refunds").fetchall()
        (answer,), = writable.execute(ATTACK).fetchall()
        (after,), = writable.execute("SELECT count(*) FROM analytics.fct_refunds").fetchall()
print("writable copy, refunds before:", before)
print("writable copy, the query's answer:", answer)
print("writable copy, refunds after:", after)
```

Output:

```text
root: Select
statements in the tree: Select, Delete
guard refuses (write): the query contains a Delete statement; only reads may run
read-only database: Invalid Input Error: Cannot execute statement of type "SELECT" on database "agent" which is attached in read-only mode!
writable copy, refunds before: 1068
writable copy, the query's answer: 931
writable copy, refunds after: 137
```

The root is a `Select`, so a root check would pass the query. The walk finds Select, Delete, and the guard refuses it. The read-only database refuses it too, and its message names the statement it saw as a `SELECT`. On the writable copy, the query returned `931`, a plausible count of refunds, and `analytics.fct_refunds` went from 1068 rows to 137. Nothing in the answer says rows were deleted. The read-only database is what makes that impossible; the parse check turns it into a refusal the model can read.

The second question is which tables. The agent's database already leaves out `raw` and `analytics.orders_legacy`, the old definition of revenue that [chapter 2](#the-tempting-table) warned about. The guard checks the same list in the parser all the same, because its refusal names the tables a repair needs, and because it must refuse DuckDB's catalog. The allowlist is every table in the agent's database, read by `allowed_schema()` with each table's columns, and the same mapping is the schema `qualify` resolves columns against. The allowlist is its own check, because `qualify` doesn't check that a table exists.

A name without a schema can name a CTE, which is visible only in the query whose `WITH` defines it, in that query's subqueries, and to the CTEs after it in the same `WITH`. The guard's `refers_to_cte()` follows those rules, and refuses any other name without a schema. This example tries six ways around the allowlist, the last of them a CTE named like DuckDB's catalog, and then runs the guard over every golden question's golden SQL.

Example `block-raw-tables` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""The table allowlist: the marts the agent may read, the ways around it the guard refuses, and what it costs."""
from lib.golden import load_golden
from lib.sql_guard import GuardError, SqlGuard
from lib.warehouse import agent_warehouse, connect

con = agent_warehouse(connect())          # the agent's database: copies of the allowed marts, nothing else
guard = SqlGuard(con)                     # allowlist: the tables in it, read with their columns
print("allowed tables:", ", ".join(f"{db}.{t}" for db, tables in guard.schema.items() for t in tables))

ATTEMPTS = {
    "raw table": "SELECT count(*) AS customers FROM raw.customers",
    "legacy mart": "SELECT sum(revenue) AS revenue FROM analytics.orders_legacy",
    "no schema": "SELECT count(*) AS orders FROM fct_orders",
    "file as a table": "SELECT * FROM 'data/golden/questions.toml'",
    "table function": "SELECT * FROM read_csv('data/golden/questions.toml')",
    "CTE named like the catalog": """SELECT * FROM (WITH duckdb_tables AS (SELECT 1 AS x) SELECT x FROM duckdb_tables) AS a,
duckdb_tables""",
}
for label, sql in ATTEMPTS.items():
    try:
        guard.check(sql)
        print(f"{label}: allowed")
    except GuardError as e:
        print(f"{label}: refused ({e.kind}), {str(e).split(';')[0]}")

golden = [q for q in load_golden() if q.golden_sql]
outside = []
for q in golden:
    try:
        guard.check(q.golden_sql)
    except GuardError as e:
        outside.append(f"{q.question_id} ({str(e).split(' ')[0]})")
print(f"golden queries the allowlist refuses: {len(outside)} of {len(golden)}")
print("refused golden queries:", ", ".join(outside))
```

Output:

```text
allowed tables: analytics.dim_customers, analytics.dim_date, analytics.dim_products, analytics.fct_order_lines, analytics.fct_orders, analytics.fct_refunds, analytics.fct_sessions
raw table: refused (table), raw.customers isn't a table you may read
legacy mart: refused (table), analytics.orders_legacy isn't a table you may read
no schema: refused (table), fct_orders isn't a table you may read
file as a table: refused (table), data/golden/questions.toml isn't a table you may read
table function: refused (table), READ_CSV('data/golden/questions.toml') reads data through a function
CTE named like the catalog: refused (table), duckdb_tables is DuckDB's catalog, not a table you may read
golden queries the allowlist refuses: 2 of 34
refused golden queries: gq-034 (raw.marketing_spend), gq-037 (raw.customers)
```

All six are refused, and three of them aren't table names at all. A file path in the `FROM` clause parses as a table named after the path, so the allowlist refuses it. `read_csv()` parses as a function in the table's place, and the guard refuses anything in `FROM` other than a table, a subquery or a `VALUES` list, which covers `range()`, `unnest()` and `query_table()` too. The CTE named `duckdb_tables` is defined inside a subquery, so the `duckdb_tables` after it names DuckDB's catalog view, and the guard says so: `refused (table), duckdb_tables is DuckDB's catalog, not a table you may read`. It refuses every catalog name, such as those starting `duckdb_` or `pg_`, and every function that reads the instance, such as `current_setting()`. Any other function must be on `ALLOWED_FUNCTIONS`, the functions the shop's analytics need.

The last two lines show what the allowlist costs. It refuses 2 of 34 golden queries: gq-034 (raw.marketing_spend), gq-037 (raw.customers). Marketing spend has no mart, and duplicate sign-ups exist only in `raw.customers`, because the mart removed them. [The last section](#metric-or-sql) returns to those two questions.

**Working rule:** Accept only a query at the root, walk every node for a statement that writes, and allowlist tables by schema and name, with nothing but tables and subqueries in `FROM`. Resolve a name without a schema as a CTE only where a CTE of that name is visible, refuse the database's catalog by name, and allow only the functions your analytics need. Check the same list the agent's database holds. When a golden question needs a table off the list, give it a mart or a metric, not a wider list.

## Bound the rows and the cost {#bound-rows-and-cost}

A query that only reads [the allowed tables](#read-only-allowlist) can still hurt: it can return every row of a fact table into the agent's context, or join three fact tables with no join condition and run for hours. The guard bounds both, and the time. For rows, it adds a `LIMIT`, and after the run it refuses a result longer than 50,000 characters, since one row can hold a whole column. For cost, it asks DuckDB's `EXPLAIN` for the plan, which plans the query without running it and gives each step an estimated number of rows ([DuckDB](https://duckdb.org/docs/2.0/guides/meta/explain.html)). For time, it needs its own timer, because DuckDB has no statement timeout, and its documentation says to "Implement strict query timeouts at the application level" ([DuckDB](https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview.html)).

The costly mistake is [chapter 2](#joins-that-fan-out)'s fan-out taken to its end: orders, lines and refunds in one `FROM` clause with no keys. The example compares that plan with the same sum joined on `order_id`, checks the limit against the golden queries, and then shows a `LIMIT` the agent wrote, too many rows, and the join without keys stopped by the timer.

Example `explain-before-running` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Bound the rows and the cost: EXPLAIN a join that forgot its keys, keep the agent's LIMIT, and stop a slow query."""
import sqlglot

from lib.golden import load_golden
from lib.sql_guard import GuardError, SqlGuard, check, explain, run_with_timeout
from lib.warehouse import agent_warehouse, connect

guard = SqlGuard(con := agent_warehouse(connect()))   # the agent's database, where the guard runs its checks
NO_KEYS = """SELECT sum(o.net_revenue_eur) AS net_revenue FROM analytics.fct_orders AS o,
analytics.fct_order_lines AS l, analytics.fct_refunds AS r"""
KEYED = """SELECT sum(o.net_revenue_eur) AS net_revenue FROM analytics.fct_orders AS o
JOIN analytics.fct_order_lines AS l USING (order_id)"""
for label, sql in (("no join keys", NO_KEYS), ("joined on order_id", KEYED)):
    cost = explain(con, check(sql, guard.schema).sql)
    print(f"{label}, largest step: {cost.largest_step}\n{label}, estimated rows: {cost.largest_estimate:,}")
try:
    guard.check(NO_KEYS)
except GuardError as e:
    print(f"guard refuses ({e.kind}): {e}")
costs = {q.question_id: explain(con, check(q.golden_sql, guard.schema).sql)
         for q in load_golden() if q.golden_sql and q.question_id not in ("gq-034", "gq-037")}
print("golden queries estimated:", len(costs))
print(f"largest estimate among golden queries: {max(c.largest_estimate for c in costs.values()):,} rows")
print("golden plans with a cross product:", ", ".join(i for i, c in costs.items() if c.cross_products))
print("golden plans with a step that has no estimate:", sum(1 for c in costs.values() if c.unestimated))
print(f"limit on estimated rows: {guard.max_estimated_rows:,}")

TOP_FIVE = """SELECT product_id, sum(net_amount_eur) AS net_revenue FROM analytics.fct_order_lines
GROUP BY product_id ORDER BY net_revenue DESC LIMIT 5"""
print("sqlglot's .limit(1001):", sqlglot.parse_one(TOP_FIVE, read="duckdb").limit(1001).sql("duckdb").split("ORDER BY")[1].strip())
print("guard's limit on the top five:", check(TOP_FIVE, guard.schema).limit)
try:
    guard.run("SELECT order_id, net_revenue_eur FROM analytics.fct_orders")
except GuardError as e:
    print(f"every order ({e.kind}): {e}")

# The join without keys, through the time limit alone, as if the estimate had let it through. It reads its rows in
# batches, and DuckDB looks for the timer's interrupt between them.
try:
    run_with_timeout(con, check(NO_KEYS, guard.schema).sql, seconds=1.0)
except GuardError as e:
    print(f"no join keys, timer alone ({e.kind}): {e}")
print("connection still answers:", con.execute("SELECT count(*) FROM analytics.fct_orders").fetchall()[0][0])
```

Output:

```text
no join keys, largest step: CROSS_PRODUCT
no join keys, estimated rows: 604,042,404,768
joined on order_id, largest step: SEQ_SCAN
joined on order_id, estimated rows: 38,071
guard refuses (cost): one step of the plan (CROSS_PRODUCT) is estimated to produce 604,042,404,768 rows, over the limit of 10,000,000; join each table on its key
golden queries estimated: 32
largest estimate among golden queries: 38,071 rows
golden plans with a cross product: gq-031
golden plans with a step that has no estimate: 0
limit on estimated rows: 10,000,000
sqlglot's .limit(1001): net_revenue DESC LIMIT 1001
guard's limit on the top five: 5
every order (rows): the query returns more than 1000 rows; aggregate or filter it
no join keys, timer alone (timeout): the query ran past the 1-second time limit and was stopped
connection still answers: 14856
```

The keyed join's largest step is a `SEQ_SCAN` of 38,071 rows. Without keys, the largest step is a `CROSS_PRODUCT` of 604,042,404,768 rows, and the guard refuses it with a message that tells the model to join on keys. Any other step without an estimate, such as an `UNNEST` that makes rows from a list, makes the plan's cost unknown, and the guard refuses the plan rather than guess; 0 golden plans have such a step. A cross product isn't always a mistake, either: DuckDB's plan for the golden query of gq-031, units per order, has one, and that query is correct. The 32 golden queries the allowlist accepts peak at 38,071 rows, far under the limit of 10,000,000, a rule of thumb for the shop's size.

The `LIMIT` needs care. sqlglot's `.limit()` replaces the `LIMIT` a query already has, so a top-five query given `.limit(1001)` ends in `net_revenue DESC LIMIT 1001` and stops being a top five. The guard keeps the smaller limit, 5. Its own limit is one row more than the 1,000 it allows, so it can tell a result that was cut from one that fits. A query for every order is refused: `the query returns more than 1000 rows; aggregate or filter it`. The first 1,000 rows would look like an answer; a refusal makes the model aggregate.

The time limit is the backstop for estimates that are wrong. The example runs the join without keys under the timer alone. `run_with_timeout()` calls DuckDB's `interrupt()`, which DuckDB acts on between the batches of rows a query reads, so this query stops: `the query ran past the 1-second time limit and was stopped`. The connection then answers the next query, 14856 orders.

**Working rule:** Bound every query four ways: a row limit that keeps a smaller one the agent wrote, a limit on the result's size, a plan-size limit from `EXPLAIN` checked before the query runs, and one deadline over every step of the guard, planning included. Refuse a result over either limit rather than cut it, and refuse a plan with a step that has no estimate. Set the plan limit from your own known-good queries, never use `EXPLAIN ANALYZE`, which runs the query, and rely on the deadline and the result limits, not the estimate.

## Enforce the deadline by killing a process {#time-the-plan}

[The bounds section](#bound-rows-and-cost) stopped a slow query with an interrupt, but DuckDB acts on `interrupt()` only where it checks for one, and it can compute a constant while planning, before any such check. So the timer can't be relied on; a killed process stops wherever it is.

So the guard plans and runs the agent's query in a worker, a separate process started by `Worker` in `lib/sql_guard.py` that opens the agent's database file read-only with the guard's settings, and kills it when the 5-second deadline passes. At most 1,001 rows come back through a pipe, and an oversized result is refused inside the worker.

The example's query compares each order ID with a constant sum over 30 million generated numbers, its list functions let past the guard's list. The example plans it with a small constant, 18, on the shop's connection, which folds constants, and on the agent's database, which doesn't; then a worker plans the full query under a half-second deadline.

Example `stop-a-slow-plan` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Stop a slow plan: DuckDB computes a constant while it plans, before any row is read, so a timer's interrupt has
nothing to stop it at; a killed worker stops wherever it is."""
import json

from lib.sql_guard import GuardError, SqlGuard, Worker, check
from lib.warehouse import agent_warehouse, connect

shop = connect()                                      # chapter 1's connection: constant folding on
agent = agent_warehouse(shop)                         # the agent's database: constant folding off
guard = SqlGuard(agent, timeout=0.5)
SLOW_PLAN = """SELECT count(*) AS n FROM analytics.fct_orders
WHERE order_id < list_sum(list_transform(range(30000000), x -> list_sum(range(40))))"""
# Checked as if the function list allowed the list functions, as sqlglot names them (range() is GENERATE_SERIES and
# list_transform() is TRANSFORM), so the plan reaches DuckDB.
LIST_FUNCTIONS = {"list_sum", "transform", "generate_series"}
planned = check(SLOW_PLAN, guard.schema, functions=guard.functions | LIST_FUNCTIONS).sql
# The same query with a small constant, 3 lists summing to 6 each: 18, under every order ID. A plan with no rows to
# read means DuckDB computed the constant while planning.
small = planned.replace("30000000", "3").replace("RANGE(0, 40)", "RANGE(0, 4)")
for label, connection in (("shop's connection, folding on", shop), ("agent's database, folding off", agent)):
    (_, plan), = connection.execute(f"EXPLAIN (FORMAT json) {small}").fetchall()
    steps, nodes = [], json.loads(plan)
    while nodes:
        steps.append(nodes[0]["name"])
        nodes = nodes[0]["children"]
    print(f"EXPLAIN with a small constant, {label}: {' > '.join(steps)}")
worker = Worker(shop)                                 # a process with its own connection to the shop's file
try:
    worker.explain(planned, 0.5)
    outcome = "planned"
except GuardError as e:
    outcome = e.kind                                  # timeout, memory or worker_failed: the machine decides which
print("EXPLAIN in a worker with a half-second deadline, shop's connection, plan returned:", outcome == "planned")
print("EXPLAIN in a worker, still running afterwards:", worker.running)
try:
    guard.run(SLOW_PLAN)
except GuardError as e:
    print(f"slow plan through the guard ({e.kind}): {e}")
```

Output:

```text
EXPLAIN with a small constant, shop's connection, folding on: UNGROUPED_AGGREGATE > EMPTY_RESULT
EXPLAIN with a small constant, agent's database, folding off: UNGROUPED_AGGREGATE > EMPTY_RESULT
EXPLAIN in a worker with a half-second deadline, shop's connection, plan returned: False
EXPLAIN in a worker, still running afterwards: False
slow plan through the guard (function): list_sum() isn't a function the guard allows; use aggregates, window functions, casts, and date, number and text functions
```

The small plans read `UNGROUPED_AGGREGATE > EMPTY_RESULT` with folding on and `UNGROUPED_AGGREGATE > EMPTY_RESULT` with it off ([DuckDB](https://duckdb.org/docs/2.0/configuration/overview.html)): DuckDB computed the constant while planning and found no order ID under it. For the full constant that is the slow step, so folding off is only a second line; the guard relies on the kill. Plan returned: False. Worker still running: False.

**Working rule:** Start the deadline when the agent's SQL arrives, and run `EXPLAIN` under it as well as the query. Enforce it by killing a separate process with its own read-only connection, not with an interrupt. Check on your own database that a stopped plan and a stopped query really stop.

## Replay the attacks on the guard {#replay-the-bypasses}

A first draft of the guard trusted its parse checks and bounds, on chapter 1's connection, which could see every schema, and a critic got past the parser three ways. A CTE named like a catalog view returned the `CREATE` statement of every table, `raw` included. A constant folded while planning outran the timer. A cross product with `unnest(range(200000))` passed the plan-size limit, because a step with no estimate counted as small. Each was a place where the guard's model of SQL and the database disagreed, and the database's reading is the one that runs. Two security reviews found more ways past the hardened guard. That is why the parser is not the boundary.

The example replays the reviews' attempts and three smaller ones, some straight to the agent's database, and each through the guard with its 5-second limit.

Example `replay-guard-bypasses` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""The critics' attempts to get past the guard (lib/guard_attacks.py), replayed on the agent's database, a temporary
copy of the marts: what the database alone allows, and what the guard does."""
import duckdb

from lib.guard_attacks import ALONE, ATTEMPTS, alone, attempt, macro_then_sum
from lib.sql_guard import SqlGuard, explain
from lib.warehouse import agent_warehouse, connect

agent = agent_warehouse(connect())
guard = SqlGuard(agent)                       # the 5-second limit: the queries that run here finish far inside it
for label, sql in ATTEMPTS.items():
    if label in ALONE:                        # straight to the agent's database, with no guard in front
        print(f"{label}, database alone: {alone(agent, label)}")
    print(f"{label}, guard: {attempt(guard.run, sql)[0]}")
print("upper-case names, guard:", attempt(guard.run, "SELECT count(*) AS n FROM ANALYTICS.FCT_ORDERS")[0])

# A temporary macro named sum, on a cursor of the database alone, then sent straight to the guard's worker.
alone_sum, real = macro_then_sum(agent, guard.worker)
print("temp macro named sum, database alone, the next sum:", alone_sum)
print("temp macro named sum, guard's worker, the next sum is the real one:", real)

# The regex attempt. In-process, a timer's interrupt waits for the end of a batch of rows, and one batch is this much
# text. With repeat() and regexp_matches() (sqlglot's REGEXP_LIKE) allowed, the guard's worker runs it under the
# review's 2-second limit, and stops it by the deadline or the memory cap, whichever the machine reaches first.
REGEX, BATCH = ATTEMPTS["regex on a repeated email"], duckdb.__standard_vector_size__
(text,), = agent.execute(f"SELECT sum(length(email)) * 200000 FROM (SELECT email FROM analytics.dim_customers "
                         f"ORDER BY customer_id LIMIT {BATCH})").fetchall()
print(f"regex, characters to match in one batch of {BATCH:,} rows: {text:,}")
wider = SqlGuard(agent, timeout=2.0, functions=guard.functions | {"repeat", "regexp_like"})
print("regex, guard without the function list:", attempt(wider.run, REGEX)[1])
print("regex, worker still running afterwards:", wider.worker_running)
print("regex, the guard's next query:", attempt(wider.run, "SELECT count(*) AS n FROM analytics.fct_orders")[0])

# The inequality join ran. Its estimate varies a little between runs, so only its size is printed.
JOIN = ATTEMPTS["join on inequality"]
estimate, joined = explain(agent, JOIN).largest_estimate, guard.run(JOIN).rows[0][0]
print("join on inequality, estimate under the limit:", estimate < guard.max_estimated_rows)
print(f"join on inequality, rows it joined: {joined:,}")
print("join on inequality, rows joined more than 100 times the estimate:", joined > 100 * estimate)
```

Output:

```text
CTE named duckdb_tables, database alone: 7 rows, one per table, all in analytics: True
CTE named duckdb_tables, guard: refused (table), duckdb_tables is DuckDB's catalog, not a table you may read
CTE named pg_settings, database alone: 170 rows of settings
CTE named pg_settings, guard: refused (table), pg_settings is DuckDB's catalog, not a table you may read
slow plan, guard: refused (function), list_sum() isn't a function the guard allows
unnest in FROM, guard: refused (table), UNNEST(RANGE(0, 200000)) AS t(x) makes rows from a function, not a table
unnest in a subquery, guard: refused (function), unnest() isn't a function the guard allows
every email in one row, database alone: 1 row of 106,670 characters
every email in one row, guard: refused (size), the result is 106,670 characters long, over the limit of 50,000
a setting read by a function, database alone: 1 row, a folder's path
a setting read by a function, guard: refused (table), current_setting() reads the database's settings or catalog
a table named with its database, database alone: 14,856 orders
a table named with its database, guard: refused (table), agent.analytics.fct_orders names a database
regex on a repeated email, guard: refused (function), regexp_matches() isn't a function the guard allows
database name and version, database alone: agent, v2.0.0
database name and version, guard: refused (table), current_database() reads the database's settings or catalog
600 nested subqueries, guard: refused (parse), the SQL is nested too deeply to check (the limit is 200 levels)
SIMILAR TO on an email, guard: refused (function), SIMILAR TO isn't an operator the guard allows
temp macro named sum, guard: refused (statement), only queries may run, and this is a Create statement
join on inequality, guard: ran
upper-case names, guard: ran
temp macro named sum, database alone, the next sum: 42
temp macro named sum, guard's worker, the next sum is the real one: True
regex, characters to match in one batch of 2,048 rows: 10,649,600,000
regex, guard without the function list: stopped, no answer
regex, worker still running afterwards: False
regex, the guard's next query: ran
join on inequality, estimate under the limit: True
join on inequality, rows it joined: 45,147,384
join on inequality, rows joined more than 100 times the estimate: True
```

Each attempt but the last is refused. The CTE named `duckdb_tables`, sent to the agent's database alone, returns 7 rows, one per table, all in analytics: True: the catalog can't show the agent a table it may not read, because none is there. The slow plan and `unnest()` are now refused as functions off the list, as in `refused (function), list_sum() isn't a function the guard allows`. One row holding every customer's name and email, 1 row of 106,670 characters, is refused as too large.

The second review's first attempt matches a pattern against each customer's email repeated 200,000 times. It passed the parser and the plan's limit, and outran an interrupt, which DuckDB checks for only between batches of rows; one batch here holds 10,649,600,000 characters. The function list now refuses it: `refused (function), regexp_matches() isn't a function the guard allows`. Run with `repeat()` and `regexp_matches()` allowed, under the review's 2-second limit, it is `stopped, no answer`, whether the deadline or the worker's memory cap came first, and the worker is still running: False. The guard's next query ran.

`current_database()` and `version()`, which alone return agent, v2.0.0, had passed; the guard now checks every function. Six hundred nested subqueries, which crashed sqlglot's parser, are now refused: `refused (parse), the SQL is nested too deeply to check (the limit is 200 levels)`.

A final review added two. The guard now refuses `SIMILAR TO`, a regular expression as an operator: `refused (function), SIMILAR TO isn't an operator the guard allows`. A temporary macro named `sum`, accepted by the database alone, makes the next sum 42. The parser refuses it, and the worker, starting each query on a fresh cursor, would drop it, so the next sum is real: True.

The last attempt, a join of orders to every customer who didn't place them, ran, as the rules allow. Its estimate was under the limit, True, and it joined 45,147,384 rows, more than 100 times the estimate: True. So the plan's limit catches only the mistakes it was set for, and the kill, the result limits and the memory limit bound the rest, and [the production section](#guarded-sql-in-production) lists what remains.

**Working rule:** Rely on the database's limits, and treat the parser as defence in depth. Keep every attack anyone finds as a test: replay it against the agent's database alone and through the guard, and check that each is refused by the layer you expect. When an attack gets past the parser, ask first why the database let it reach anything, and then fix the parser.

## Repair once from the error {#repair-once}

Repair means giving the model the guard's refusal or the warehouse's error, once, and running what it writes next. The research on repair loops says when it helps. MAC-SQL's Refiner, which corrects SQL from "the error message feedback", added 4.6 points on BIRD's dev set with GPT-4 ([Wang et al.](https://arxiv.org/abs/2312.11242), Table 3). Repair without an outside signal is weaker: models "struggle to self-correct their responses without external feedback" ([Huang et al.](https://arxiv.org/abs/2310.01798)), and in DIN-SQL a prompt that told GPT-4 its SQL was buggy lowered its Spider score from 73.3 to 70.0 ([Pourreza and Rafiei](https://arxiv.org/abs/2304.11015), Table 5). So the guard repairs only on an outside signal, its own refusal or DuckDB's error, and the prompt asks for a correction only "if the message shows how".

The repair prompt is `GUARD_REPAIR` in `lib/prompts.py`: the model's own reply, the message, and the instruction to reply with corrected SQL or a line that starts `cannot answer:`. `answer_with_repair()` in `lib/sql_guard.py` runs it at most once per question. The recording `guarded-sql-runs` holds only the repair calls, made with the book's pinned model, Qwen3-4B-Instruct-2507 in a 4-bit file, chosen as [chapter 1](#ask-for-sql) explains. Each first reply is replayed from chapter 1's schema-only recording or [chapter 4](#measure-each-layer)'s layered one, and the model was called only where the guard refused that reply or DuckDB failed: 6 times for schema-only SQL and 1 for layered SQL on the dev split. The same run repaired the test split's replies, which [the long-tail section](#metric-or-sql) uses. The example scores both on the dev split's 17 answer questions, and shows two repairs: the layered run for `gq-017` from [the parse section](#parse-before-running), and the schema-only run for `gq-001`, net revenue in fiscal year 2026.

Example `repair-from-error` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Repair once from the guard's message: one repaired run, then how often repair acts at all, on the dev split."""
from collections import Counter

from lib.context import LAYERS, build_context
from lib.golden import golden_result, grade, load_golden
from lib.model import RecordedModels
from lib.prompts import layered_sql_messages, schema_only_messages
from lib.sql_guard import SqlGuard, answer_with_repair
from lib.warehouse import agent_warehouse, connect, describe_schema

con = connect()
guard, schema = SqlGuard(agent_warehouse(con)), describe_schema(con)
# First replies from chapters 1 and 4's recordings; each repair reply from this chapter's.
model = RecordedModels("schema-only-sql", "context-layers", "guarded-sql-runs")
MESSAGES = {"schema-only": lambda q: schema_only_messages(schema, q.question),
            "layered": lambda q: layered_sql_messages(build_context(con, q.question, LAYERS).text, q.question)}
dev = [q for q in load_golden() if q.split == "dev" and q.kind == "answer"]
shown = {}

for context, messages in MESSAGES.items():
    counts = Counter()
    for q in dev:
        run = answer_with_repair(guard, model, messages(q), q.question, role=q.role, repairs=1)
        outcome = grade(q, run.answer, golden_result(con, q))
        when = "after repair" if run.repaired else "first time"
        counts[f"ran {when}"] += run.attempts[-1].outcome == "ran"
        counts[f"correct {when}"] += outcome == "correct"
        counts[f"wrong {when}"] += outcome == "wrong"
        counts["refused or failed first"] += run.repaired
        counts["declined after repair"] += run.attempts[-1].outcome == "declined"
        shown[context, q.question_id] = run
    print(f"{context}, questions: {len(dev)}")
    for key in ("ran first time", "correct first time", "wrong first time", "refused or failed first",
                "ran after repair", "correct after repair", "wrong after repair", "declined after repair"):
        print(f"{context}, {key}: {counts[key]}")

for context, question_id in (("layered", "gq-017"), ("schema-only", "gq-001")):
    run = shown[context, question_id]
    print(f"{question_id} {context}, refused: {run.attempts[0].message.split('. The tables')[0]}")
    print(run.attempts[1].sql)
    rows = len(run.answer.rows)
    print(f"{question_id} {context}, after repair: {run.attempts[1].outcome} and returned {rows} row{'s' * (rows != 1)}")
```

Output:

```text
schema-only, questions: 17
schema-only, ran first time: 11
schema-only, correct first time: 2
schema-only, wrong first time: 9
schema-only, refused or failed first: 6
schema-only, ran after repair: 5
schema-only, correct after repair: 0
schema-only, wrong after repair: 5
schema-only, declined after repair: 0
layered, questions: 17
layered, ran first time: 16
layered, correct first time: 14
layered, wrong first time: 2
layered, refused or failed first: 1
layered, ran after repair: 1
layered, correct after repair: 0
layered, wrong after repair: 1
layered, declined after repair: 0
gq-017 layered, refused: Unknown column: country
SELECT o.country, round(sum(o.net_revenue_eur), 2) AS net_revenue
FROM analytics.fct_orders AS o
JOIN analytics.dim_date AS d ON d.date_day = o.order_date_local
WHERE o.status <> 'cancelled'
  AND d.calendar_year = 2025
GROUP BY o.country
ORDER BY net_revenue DESC
gq-017 layered, after repair: ran and returned 10 rows
gq-001 schema-only, refused: Column 'fiscal_year' could not be resolved. Line: 3, Col: 17
SELECT SUM(net_revenue_eur) AS net_revenue
FROM analytics.fct_orders
WHERE EXTRACT(YEAR FROM placed_at) = 2026
gq-001 schema-only, after repair: ran and returned 1 row
```

Repair worked as a mechanism. For `gq-017`, the guard's message named the unknown column and listed the orders table's columns, and the model moved `country` from the calendar to the orders table. The repaired query ran and returned 10 rows. For schema-only SQL, 5 of the 6 refused or failed queries ran after one repair.

It didn't make answers right. Schema-only SQL got 0 repaired answers correct, and layered SQL 0. The repaired `gq-017` returns every country, and the golden question is asked by EMEA's regional lead, who should see EMEA's countries only: a rule that [the lead's own database](#views-per-role) enforces, and that no SQL error reveals. For `gq-001`, the guard refused `fiscal_year`, which the model had looked for on the orders table, and the model's fix was to filter on the calendar year of the UTC timestamp instead. The query ran and returned 1 row, for a different question. Meanwhile layered SQL ran first time on 16 questions, with 2 of them wrong, and repair never sees those, because nothing failed. On the shop's dev split, repair turned visible errors into answers that run and are wrong, which is harder to catch than an error.

**Working rule:** Repair at most once, and only from an outside signal: the guard's refusal or the warehouse's error, passed to the model with its own SQL and a prompt that doesn't assume the SQL is wrong. Let the model decline in the repair. Score repaired answers on their own, apart from first-time answers, and if your golden questions show they are rarely right, decline on a refusal instead of repairing.

## Transpile to the warehouse's dialect {#transpile-to-the-warehouse}

The shop's warehouse is DuckDB, and most readers' isn't. The same tree can be written in another dialect, as [chapter 5](#any-dialect) did for the semantic layer's SQL. What is transpiled is the guard's SQL, with every identifier quoted. sqlglot's transpiler translates what it knows and, by default, warns and makes a "best-effort translation" of what it can't; with `unsupported_level=ErrorLevel.RAISE`, which `transpile()` in `lib/sql_guard.py` uses, it raises instead ([sqlglot](https://raw.githubusercontent.com/tobymao/sqlglot/v30.27.0/README.md)). Neither tells you that the result means the same thing on the target.

The example checks a long-tail query, net revenue by weekday and month in 2025, and transpiles it to Snowflake, first keeping the guard's quotes and then without them. Then it transpiles a query that uses DuckDB's `histogram()` aggregate, which is on the guard's function list.

Example `transpile-to-snowflake` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Transpile checked SQL to Snowflake: the quotes the guard added, a function it can't translate, a name that differs."""
from lib.sql_guard import SqlGuard, transpile
from lib.warehouse import agent_warehouse, connect

con = connect()
guard = SqlGuard(agent_warehouse(con))
WEEKDAYS = """SELECT dayname(order_date_local) AS weekday, strftime(order_date_local, '%Y-%m') AS month,
       round(sum(net_revenue_eur), 2) AS net_revenue
FROM analytics.fct_orders
WHERE status <> 'cancelled' AND year(order_date_local) = 2025
GROUP BY ALL ORDER BY month, weekday"""
checked = guard.check(WEEKDAYS)
print("kept quoted, Snowflake reads:", transpile(checked.sql, "snowflake", quoted=True).sql.split(" FROM ")[1].split(" WHERE")[0])

snowflake = transpile(checked.sql, "snowflake", pretty=True)
print(snowflake.sql)
print("functions passed through unchanged:", ", ".join(snowflake.passed_through) or "none")
print("DuckDB's first weekday:", guard.run(WEEKDAYS).rows[0][0])

MIX = """SELECT region, histogram(channel) AS orders_by_channel FROM analytics.fct_orders
WHERE year(order_date_local) = 2025 GROUP BY region"""
mix = transpile(guard.check(MIX).sql, "snowflake")
print("channel mix in Snowflake:", mix.sql.split(" FROM")[0])
print("functions passed through in the channel mix:", ", ".join(mix.passed_through) or "none")
```

Output:

```text
kept quoted, Snowflake reads: "analytics"."fct_orders" AS "fct_orders"
SELECT
  DAYNAME(fct_orders.order_date_local) AS weekday,
  TO_CHAR(fct_orders.order_date_local, 'yyyy-mm') AS month,
  ROUND(SUM(fct_orders.net_revenue_eur), 2) AS net_revenue
FROM analytics.fct_orders AS fct_orders
WHERE
  fct_orders.status <> 'cancelled' AND YEAR(fct_orders.order_date_local) = 2025
GROUP BY ALL
ORDER BY
  month,
  weekday
LIMIT 1001
functions passed through unchanged: none
DuckDB's first weekday: Friday
channel mix in Snowflake: SELECT fct_orders.region AS region, HISTOGRAM(fct_orders.channel) AS orders_by_channel
functions passed through in the channel mix: histogram
```

Kept quoted, the table becomes `"analytics"."fct_orders" AS "fct_orders"`. In Snowflake that names a different table: "Unquoted identifiers are stored and resolved in uppercase", while "Delimited identifiers (i.e. identifiers enclosed in double quotes) are case-sensitive" ([Snowflake](https://docs.snowflake.com/en/sql-reference/identifiers-syntax)). So `transpile()` drops the quotes unless asked to keep them, and the second version reads `analytics.fct_orders`. sqlglot rewrote `strftime()` as `TO_CHAR()` with Snowflake's format, and knew every function: none passed through.

That clean result still changes the answer. `dayname()` came out as `DAYNAME()`, and the two names don't mean the same: DuckDB's gives "The (English) name of the weekday" ([DuckDB](https://duckdb.org/docs/2.0/sql/functions/date.html)), here `Friday`, while Snowflake's "Extracts the three-letter day-of-week name" ([Snowflake](https://docs.snowflake.com/en/sql-reference/functions/dayname)). The same rows get different labels, so a golden result that says `Friday` fails on Snowflake. The channel mix is the other failure: `histogram` is a function sqlglot doesn't know, so it was written out unchanged, `SELECT fct_orders.region AS region, HISTOGRAM(fct_orders.channel) AS orders_by_channel`, with no error. `transpile()` lists such functions, here histogram, so you can refuse them or check them by hand.

**Working rule:** Let the agent write the dialect your golden questions are checked in, guard that SQL, and transpile the guard's output, not the agent's text, with errors raised for what the transpiler knows it can't translate. Drop the guard's quotes for warehouses that fold unquoted names to upper case, refuse functions the transpiler passed through, and run the golden questions on the target warehouse before you trust a transpiled answer, because a function with the same name can return different values.

## When to prefer a new metric over SQL {#metric-or-sql}

The database and the guards make the agent's SQL safe to run: [limited to its role's views](#views-per-role), [bounded](#bound-rows-and-cost) and [repaired once](#repair-once). None of them makes it right. A metric is right by construction, because a person defined it once. So guarded SQL is for questions asked once, and a question that keeps coming back, or whose number goes into a report, should become a metric. To tell them apart, score the guarded path on the long tail of golden questions and read every wrong answer.

The shop's long tail is the ten answer questions that no metric or dimension in `examples/data/semantic/` covers, such as orders that include a tent, session conversion and discount. 2 of the ten are on the dev split and 8 on the held-out test split. Two questions are too few to score, so the long-tail number comes from test. The guard and the repair prompt were fixed on dev, and nothing changed after we read test once; [chapter 4](#measure-each-layer) already scored the first replies there. Then the example promotes one question to the semantic layer, in a copy of its YAML.

Example `long-tail-score` (Python 3.12.15 · duckdb 2.0.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.7:

```python
"""Guarded SQL on the long tail, the answer questions no metric in the semantic layer covers; then one promoted."""
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from lib.answers import format_value
from lib.context import LAYERS, build_context
from lib.golden import golden_result, grade, load_golden, results_match
from lib.model import RecordedModels
from lib.prompts import layered_sql_messages
from lib.semantic import SEMANTIC_DIR, MetricRequest, load
from lib.sql_guard import SqlGuard, answer_with_repair
from lib.warehouse import agent_warehouse, connect

LONG_TAIL = {"gq-007": "a filter on what an order contains", "gq-016": "customers with an order",
             "gq-031": "units per order", "gq-032": "gross margin", "gq-033": "session conversion",
             "gq-034": "marketing spend", "gq-036": "one order's refunds", "gq-037": "duplicate sign-ups",
             "gq-038": "a weekday dimension", "gq-041": "discount"}
con, golden = connect(), {q.question_id: q for q in load_golden()}
guard, model = SqlGuard(agent_warehouse(con)), RecordedModels("context-layers", "context-layers-test", "guarded-sql-runs")
counts = Counter()
for question_id, needs in LONG_TAIL.items():
    q = golden[question_id]
    run = answer_with_repair(guard, model, layered_sql_messages(build_context(con, q.question, LAYERS).text,
                                                                 q.question), q.question, role=q.role)
    outcome = grade(q, run.answer, gold := golden_result(con, q))
    counts[q.split, outcome] += 1
    print(f"{question_id} ({q.split}, {needs}): {outcome}, after {' then '.join(a.outcome for a in run.attempts)}")
    if outcome == "wrong":
        row = ", ".join(map(format_value, min(run.answer.rows))) if run.answer.rows else "no rows"
        print(f"{question_id} first row: {row} (golden: {', '.join(map(format_value, min(gold)))})")
print(*(f"long tail questions on {s}: {sum(golden[i].split == s for i in LONG_TAIL)}" for s in ("dev", "test")), sep="\n")
for split, outcome in [(s, o) for s in ("dev", "test") for o in ("correct", "wrong", "declined")]:
    print(f"long tail {split} {outcome}: {counts[split, outcome]} of {sum(n for (s, _), n in counts.items() if s == split)}")

with tempfile.TemporaryDirectory() as folder:        # promote gq-038: one dimension added to a copy of the YAML
    shutil.copytree(SEMANTIC_DIR, copy := Path(folder) / "semantic")
    with open(copy / "orders.yml", "a") as orders:
        orders.write("    - name: weekday\n      type: categorical\n      expr: dayname(order_date_local)\n")
    layer = load(copy)
answer = layer.query(con, MetricRequest(("net_revenue", "orders"), ("order__weekday",), {"metric_time__year": 2025}))
print("gq-038 as a metric request matches golden:", results_match(answer.rows, golden_result(con, golden["gq-038"])))
```

Output:

```text
gq-007 (dev, a filter on what an order contains): wrong, after ran
gq-007 first row: NULL (golden: 377,497.40)
gq-016 (dev, customers with an order): correct, after ran
gq-031 (test, units per order): correct, after ran
gq-032 (test, gross margin): wrong, after ran
gq-032 first row: 773,723.34 (golden: 847,864.71)
gq-033 (test, session conversion): wrong, after ran
gq-033 first row: (none), 13.46 (golden: (none), 0.13)
gq-034 (test, marketing spend): declined, after table then declined
gq-036 (test, one order's refunds): correct, after ran
gq-037 (test, duplicate sign-ups): wrong, after ran
gq-037 first row: no rows (golden: 54)
gq-038 (test, a weekday dimension): wrong, after ran
gq-038 first row: Friday, 221,172.11, 822 (golden: Friday, 221,172.11, 869)
gq-041 (test, discount): correct, after ran
long tail questions on dev: 2
long tail questions on test: 8
long tail dev correct: 1 of 2
long tail dev wrong: 1 of 2
long tail dev declined: 0 of 2
long tail test correct: 3 of 8
long tail test wrong: 4 of 8
long tail test declined: 1 of 8
gq-038 as a metric request matches golden: True
```

On dev, guarded SQL gets 1 of 2 right; on test, 3 of 8, with 1 of 8 declined. The decline is `gq-034`, return on marketing spend: the guard refused `raw.marketing_spend`, and in its repair the model answered that no allowed table holds spend, which is right; the fix is a mart.

Every wrong answer ran cleanly through every guard. For `gq-007`, the model made both mistakes [chapter 4](#measure-each-layer) found: it wrote the category `tents` where the shop stores `Tents`, so the sum came back NULL (golden: 377,497.40), and it sums only the tent lines, where the question asks for the whole revenue of orders that included one. For `gq-032`, gross margin, the model subtracted net revenue from gross revenue, which gives the tax, and joined the order lines on `order_id`, so each order counts once per line, [chapter 2](#joins-that-fan-out)'s fan-out: 773,723.34 (golden: 847,864.71). The plan-size limit doesn't catch a fan-out on a key. For `gq-033`, it gave conversion as a percentage where the shop reports a fraction: (none), 13.46 (golden: (none), 0.13). For `gq-038`, net revenue and orders by weekday, revenue is right and the order count isn't: Friday, 221,172.11, 822 (golden: Friday, 221,172.11, 869). The model left cancelled orders out of the count, where the shop's `orders` metric keeps them.

`gq-038` is the one to promote. The shop defines both its metrics and lacks only a weekday dimension: three lines of YAML on the orders semantic model, with the expression `dayname(order_date_local)`. With it, the question becomes a metric request grouped by `order__weekday` in 2025, and it matches the golden result: True. That isn't a held-out result: we chose it from `gq-038`'s failure on test. The book's layer is unchanged, so `gq-038` stays in test; in your own layer, move it to dev. `gq-034` and `gq-037` need a mart first, because the agent rightly can't read `raw`. Lookups such as `gq-036`, one order's refunds and their reasons, are what guarded SQL answers well.

**Working rule:** Send a question to guarded SQL only when no metric covers it, and score that path on its own long tail of golden questions. Promote a question to the semantic layer when it recurs, when its answer goes into a report, or when guarded SQL gets it wrong on a definition, as with what counts as an order. Leave one-off lookups on the guarded path. When a question needs a table off the allowlist, build the mart and its metric rather than widening the list.

## What goes wrong in production {#guarded-sql-in-production}

These are the ways guarded SQL fails once real people use it, and how you'd notice each one.

**A wrong answer passes every guard.** The database and the guards limit what a query reads and costs, not what its number means. Execution-based correction can't fix SQL that runs and is wrong, which is why Hong et al. add error detection before repair ([Hong et al.](https://arxiv.org/abs/2603.03742)), and Chaturvedi et al. guide the correction with a taxonomy of errors ([Chaturvedi et al.](https://arxiv.org/abs/2509.00581)). You notice only by scoring the guarded path on golden questions, and by reading answers whose result is empty, `NULL` or a percentage where you expected a fraction.

**The agent's connection sits above the views.** The boundary holds only if the agent's warehouse user can't read the tables under its views. Check its grants whenever the warehouse's roles change.

**A role's view is wrong or out of date.** A view returns what its definition says, so a missing row filter or mask leaks on every path at once. In DuckDB, each role's database is also a copy made when it is built, so it must be rebuilt when the marts are. Generate the views from one policy, test each role with queries the parser accepts, as [the views section](#views-per-role) does, and name every table one by one, so a new mart stays out until someone adds it.

**The function and catalog lists are judgements.** A function the analysts need can be missing, one on the list can still be slow, and a new DuckDB catalog function can outgrow the list. Log every `function` refusal, and review both lists with each DuckDB release.

**The guard refuses good SQL.** The guard refuses DuckDB syntax that sqlglot can't model. Log every refusal with its kind, and run every golden query through the guard in CI, as [the allowlist section](#read-only-allowlist) does.

**An estimate is not a cost.** [The replay](#replay-the-bypasses) shows a join that produced more than 100 times its estimate. Log each query's estimate beside its run time.

**A read-only database still keeps state.** A read-only DuckDB connection accepts temporary tables, views, macros and variables, so a statement past the parser could change later answers, as [the replay](#replay-the-bypasses)'s macro shows. The worker gives each query a fresh cursor; do the same in any shared connection pool.

**DuckDB's memory limit doesn't cover every value.** It "only applies to the buffer manager" ([DuckDB](https://duckdb.org/docs/2.0/operations_manual/limits.html)), so the strings an expression builds escape its 1 GB. The worker caps its own process at 1.5 GB over its size once the database is open. A worker that runs out of memory, dies or never starts raises `GuardError` (`memory` or `worker_failed`) and returns no rows: the guard fails closed. The parse checks run in the guard's own process, bounded only by the 20,000-character limit and the depth cap. Give each agent run its own guard, because a worker answers one query at a time.

**The warehouse's own limit is far away.** Snowflake's `STATEMENT_TIMEOUT_IN_SECONDS` defaults to "172800 (2 days)" ([Snowflake](https://docs.snowflake.com/en/sql-reference/parameters)). Set the agent's time limit in the guard, and a lower limit on the agent's warehouse role as well.

**Repair hides errors.** On the shop's dev split, every repaired query that ran was wrong. Record the attempts with each answer, as `answer_with_repair()` does in its `GuardedRun`, and count repaired answers in every score.

**The guard's messages describe the database.** A refusal lists the allowed tables and their columns. Build the guard on the role's own database, so it lists only what the role may see.

**Working rule:** Treat the role's read-only database of views as the control, and the guard as a layer that turns mistakes into refusals and bounds the cost. Check the agent's grants and test each role's views, run every golden query through the guard in CI, set the time limit in the guard and on the warehouse, log every refusal, estimate and repair with its answer, and score the path on its own long tail of golden questions after every change.

## Decisions this chapter made {#guarded-sql-decisions}

- **Guarded SQL is the fallback, not the default,** for questions no metric covers, written with [chapter 4](#layered-context)'s four layers of context.
- **The database is the security boundary.** The agent's SQL runs read-only on `agent_warehouse()`: a file holding the seven allowed marts, or, given a role's policy, that role's views of them, with file access, extensions and constant folding off, memory and threads limited, and its settings locked. In a warehouse with roles, that is a read-only role with `SELECT` on secure views, or row access and masking policies.
- **The parser, the timer and the cost check are a teaching layer and defence in depth, not the boundary.**
- **What runs is the guard's SQL,** parsed and regenerated by sqlglot, with every column qualified and a row limit added: one statement, a query at the root, and no writing statement anywhere in the tree.
- **The allowlist is the database's tables, named one by one,** with CTE names resolved by scope, DuckDB's catalog refused, only listed functions allowed, `SIMILAR TO` and `GLOB` refused, nesting capped, and nothing but tables and subqueries in `FROM`. Two golden questions can't be answered inside it.
- **Four bounds on every query:** at most 1,000 rows and 50,000 characters, refused rather than cut; a plan whose largest step `EXPLAIN` estimates at no more than 10 million rows, a rule of thumb, with no step left unestimated; and one 5-second deadline over the checks, the plan and the run, enforced by killing the worker process, which runs each query on a fresh cursor.
- **One repair, from the guard's refusal or DuckDB's error,** with a prompt that lets the model decline. Repaired answers are scored apart.
- **Transpile the guard's output, without its quotes,** raising on what sqlglot can't translate and listing the functions it passed through.
- **Promote a question to a metric** when it recurs, when its number is reported, or when guarded SQL gets its definition wrong.
