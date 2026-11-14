---
title: "Data Governance as Code"
chapter: "Governance end to end"
chapter_id: governance-end-to-end
book: data-governance-as-code
edition: 2026.11.27
verified: 2026-11-14
edition_code: 2QX0-VKZT
canonical: https://rollingedition.com/data-governance-as-code/governance-end-to-end
license: CC BY 4.0
attribution: "“Governance end to end,” chapter 1 of Data Governance as Code, Edition 2026.11.27, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/governance-end-to-end. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Governance end to end

By the end of this chapter you can govern one table of a data platform with code, end to end. You'll catalog it with an owning team and a classification for every column, capture the lineage of a pipeline that copies it, decide who may read which of its rows and enforce that decision on a query, and see a pull request fail because it added a column nobody classified. Each piece is small and runs in seconds, and five later chapters each make one of them solid.

This book is for data, analytics and platform engineers who already build pipelines and warehouses and have been asked to make them governed. You know SQL, Python and Parquet or a lakehouse table, and you don't need governance theory: you need governance that runs, is tested, and is reviewed in pull requests like the rest of your code. By the end of the book, you can govern a data platform with code that runs in CI:

- a catalog where every table has an owner and every column a classification;
- personal data found automatically, with what the detector misses measured;
- lineage captured from pipelines;
- access policies as tested code, enforced as row filters and column masks;
- retention and erasure that remove data;
- an audit trail;
- checks that fail a pull request;
- the same rules applied to data that trains or grounds AI.

This book follows one case throughout: an online learning platform that sells professional courses to adult learners, which we call the platform. Its warehouse is a catalog of Iceberg tables, each under the namespace of the team that runs it: learners and instructors under `crm`, courses, enrollments, learning events and course reviews under `learning`, payments under `billing`, and support tickets under `support`. SQL pipelines build reporting tables from them. Support agents, instructors, marketing, finance, data scientists and the platform's course assistant, its AI, each need something different from those tables, and that's what makes the platform worth governing.

The platform's data, which every example in this book reads, is generated. A script makes it once from fixed seeds with Faker, a library for fake data, and the files are committed with a data card that says how they were made. No real person is in the data. Its email addresses are on domains reserved for examples, so they can't reach anyone, and its IP addresses are in ranges reserved for documentation, so they point at no one. Its phone numbers, card numbers and IBANs are random in a valid format, so one may match a number or an account in service: never call, message, charge or pay them. The data card also lists what is planted for the examples to find, such as full card numbers in a legacy column and personal data in free text.

Every example runs offline, in one Python 3.12.15 process, on pinned libraries: PyIceberg 0.12.0 for the Iceberg catalog and its tables, DuckDB 2.0.0 for queries, sqlglot 30.31.0 to parse SQL, openlineage-python 1.55.0 for lineage, and regopy 1.5.2 for policies written in Rego, the policy language of Open Policy Agent (OPA). Six services that a production platform runs don't run here, and each has a stand-in:

- **Trino**, the SQL engine tools query through: DuckDB behind the book's enforcement layer, which rewrites each query before running it.
- **OPA's server**, which Trino asks for access decisions ([Trino 484, OPA access control](https://trino.io/docs/484/security/opa-access-control.html)): regopy, evaluating the same Rego inside the Python process.
- **Spark**, or whatever engine runs the pipelines at scale: DuckDB, running each pipeline's SQL file.
- **A catalog server or a cloud catalog**, serving table metadata through an API such as the Iceberg REST catalog's ([REST catalog spec, 1.12.0](https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/open-api/rest-catalog-open-api.yaml)): PyIceberg's SQL catalog, backed by a SQLite file that records where each table's metadata is, with the metadata beside the data on local disk.
- **A lineage server**: a file of OpenLineage events, which the book's code reads back into a graph.
- **The CI service and git**: two folders, one for the main branch and one for a pull request's branch.

What you learn here is the open standards those services work with: Iceberg's table metadata, OpenLineage and Rego. What you build maps onto them.

The platform's governance starts with a spreadsheet. Someone listed the columns of `crm.learners`, which holds every learner's name, email, phone number and address, with a classification beside each, and that's all there is. No team is named as the table's owner. A nightly pipeline copies learners' names and emails into a table for marketing, and nothing records that it does. Support agents each serve one region, but a query on the warehouse returns every region's learners. And the CRM team is about to add a column. This chapter answers each of those with the code that the later chapters build, at the smallest scale that works: one table, one pipeline, one rule and one check. Only one of the four is a policy engine; the others are metadata, lineage events and a test, kept in the same repository and reviewed the same way.

[Chapter 2](#a-catalog-you-can-test) keeps the catalog in step with schema changes and measures a local model's drafted metadata. [Chapter 4](#lineage-from-pipelines) uses lineage for impact analysis and to propose classifications. [Chapter 5](#access-policies-as-code) writes the whole policy, with its tests, and [chapter 6](#enforcing-policies-on-queries) enforces it on every query. [Chapter 10](#governance-in-ci) runs the checks of chapters 2 to 7 in CI, with owners' approvals and waivers.

Four chapters add what this one leaves out. [Chapter 3](#finding-personal-data) finds the personal data the metadata misses. [Chapter 7](#retention-consent-erasure) covers retention, consent and erasure. [Chapter 8](#audit-and-evidence) keeps an audit trail, and [chapter 9](#governing-data-for-ai) applies the same rules to data that trains or grounds AI.

The shared modules, files in `examples/lib/` that hold the code many examples need, are yours to open and read, and each section names the ones it uses.

## Catalog a table with its owner and classifications {#catalog-a-table}

The platform's first problem is its spreadsheet, a list of columns that nothing checks. A catalog lists a platform's tables and their schemas, and governance needs two facts the data doesn't carry: who answers for each table, and how each column must be protected. Kept in a spreadsheet or a catalog server's web page, those facts change without review, and no test can say whether they're complete. Kept in a file in the repository, beside the pipelines, every change is a diff someone approves, and a test can compare the file with the catalog.

The platform's file is `governance/metadata.toml`. It gives each table an **owner**, a **domain**, the part of the business the table belongs to, and a description, and each column a description and a **classification**. Catalog tools mean different things by an owner, as [chapter 2](#keep-metadata-in-a-reviewed-file) compares, and we use one meaning throughout: the team accountable for the table, never a person, so the answer survives someone leaving. A classification is one of four values, from least to most protected:

- `public`: may be shown to anyone outside the platform;
- `internal`: for the platform's staff, and doesn't identify a person by itself;
- `personal`: identifies a person, or tells something about one;
- `sensitive`: data whose leak would directly harm someone, such as a card number.

Columns are keyed by their Iceberg field ID, which survives a rename, with the name beside it for people:

```toml
[tables."crm.learners"]
owner = "team-crm"
domain = "crm"
description = "Every learner who has signed up, with their contact details and consents. One row per learner."

[tables."crm.learners".columns]
3 = { name = "email", classification = "personal", description = "The email the learner signs in with." }
```

Three of the book's shared modules do the work. `lib.catalog.open_catalog` builds a fresh Iceberg catalog of the platform's tables in a temporary folder, which it removes when the example exits. `lib.metadata` loads the file, writes it into the catalog with `apply`, and checks the catalog against it with `problems`, which reports any table with no metadata or no owner, and any column with no classification.

Loading the file and cataloging `crm.learners` with it takes a few lines, and the check runs on what it builds:

Example `catalog-the-learners` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.27:

```python
"""Apply governance/metadata.toml to crm.learners: write its owner, domain and descriptions into the catalog, then run the
check on the catalog. The point rests on the last line, the problems the check finds once the file is applied."""
from collections import Counter

from lib import metadata
from lib.catalog import open_catalog

platform = open_catalog(["crm.learners"])            # a fresh Iceberg catalog holding the learners table
described = metadata.load()
learners = described["crm.learners"]
print("owner:", learners.owner)
print("domain:", learners.domain)
counts = Counter(column.classification for column in learners.columns.values())
print("columns classified personal:", counts["personal"])
print("personal columns:", ", ".join(c.name for c in learners.columns.values() if c.classification == "personal"))
print("columns classified internal:", counts["internal"])

# Write the descriptions into the table's schema, where readers see them, and the owner and domain into its properties.
metadata.apply(platform, described)
table = platform.load_table("crm.learners")
print("table properties:", ", ".join(f"{key}={value}" for key, value in sorted(table.properties.items())))
print("email's description, in the Iceberg schema:", table.schema().find_field("email").doc)

# The check: every table in the catalog has an owner, and every column one of the four classifications.
print("problems the check finds:", len(metadata.problems(platform, described)))
```

Output:

```text
owner: team-crm
domain: crm
columns classified personal: 7
personal columns: full_name, email, phone, city, street_address, date_of_birth, notes
columns classified internal: 8
table properties: domain=crm, owner=team-crm
email's description, in the Iceberg schema: The email the learner signs in with.
problems the check finds: 0
```

The file gives `crm.learners` to `team-crm`, in the domain `crm`, and classifies 7 of its columns as personal: `full_name, email, phone, city, street_address, date_of_birth, notes`. `notes` is among them although its name says nothing, because support agents type whatever they like into it. The remaining columns are `internal`: the learner's ID, two dates, their country, their two consent flags, their account's status and their support region.

Applying the file also puts the owner and the descriptions where every reader sees them. The table's properties read `domain=crm, owner=team-crm`, and `email`'s description sits in the Iceberg schema, where any reader of the table finds it: "The email the learner signs in with." The classifications stay in the file, because that is where the access policy and the checks read them. After `apply`, the check finds 0 problems.

A spreadsheet can't give you that zero. The check walks the catalog, so a column the file doesn't describe would show up as a problem, as `work_email` does in [the section on spreadsheets](#a-spreadsheet-nobody-updates).

**Working rule:** Keep owners, domains, descriptions and classifications in one reviewed file in the repository, with a team as every table's owner and one of a closed list of classifications on every column. Write the descriptions into the catalog, so every reader of a table sees them, and test the catalog against the file by walking the catalog, never the file. If edits happen in a catalog's web page, pick one side as the source, and generate the other from it ([chapter 2](#a-catalog-you-can-test)).

## Capture one pipeline's column lineage {#capture-one-pipelines-lineage}

[The catalog](#catalog-a-table) says what a table holds. Lineage says where its data came from and where it went, and governance needs both: a table built from `crm.learners` may or may not copy its emails. OpenLineage, an open specification for lineage, describes a **job**, such as a pipeline, its **runs**, and the **datasets** each run reads and writes. A run reports itself in events: a START when it begins, then one that ends it, such as COMPLETE or FAIL. Events carry **facets**, OpenLineage's name for blocks of metadata attached to a run, a job or a dataset.

The column lineage facet, on the output of a COMPLETE event, lists for each output column the input columns it came from, each marked DIRECT or INDIRECT. DIRECT means the output is derived from the input. INDIRECT means the input shapes the output without being copied: the output column value is "impacted by the value of inputField column, but it's not derived from it" ([column lineage facet](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet)). The columns of a join or a filter condition are INDIRECT inputs, since they decide which rows exist, and so are those of a grouping, sort, window or condition.

The client library computes no lineage of its own, as [chapter 4](#send-run-events) finds in its source: it sends what you give it. So the book's module `lib.lineage` does the work. It parses each pipeline's SQL with sqlglot and adds the INDIRECT inputs that sqlglot's own lineage leaves out. It also wraps `lib.pipelines.run`, which runs one of the platform's SQL pipelines on DuckDB and writes its output to the catalog: START before the run, COMPLETE with the lineage after it. The events go through OpenLineage's file transport to one file, with a fixed time and a run ID derived from that time and the job's name, so the example writes the same bytes every time.

The platform's `marketing_audience` pipeline is one `create table ... as select ...` statement that writes `marketing.audience`, the list of learners marketing may email. It selects each learner's ID, name, email and country from `crm.learners`, joins each learner to their favourite course category, ranked from their enrollments, and keeps the learners for whom `l.marketing_consent and l.status = 'active'` holds.

Run the pipeline with events on, read its lineage back from the events alone, and count the rows through `lib.warehouse.connect`, which gives DuckDB a view of each catalog table:

Example `audience-pipeline-lineage` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""Run the marketing_audience pipeline with OpenLineage events, then read its column lineage back from the events alone.
The point rests on the two INDIRECT lines: the filter and the joins decide which rows the audience table holds."""

from lib import lineage, metadata, warehouse
from lib.catalog import open_catalog
from lib.platform import scratch

platform = open_catalog(["crm.learners", "learning.courses", "learning.enrollments"])
events_file = scratch() / "events.jsonl"                 # the file that stands in for a lineage server: one event per line
lineage.run(platform, "marketing_audience", lineage.client(events_file))
events = lineage.read_events(events_file)

print("events:", ", ".join(f"{e['eventType']} of {e['job']['name']}" for e in events))
print("the run read:", ", ".join(dataset["name"] for dataset in events[0]["inputs"]))  # the START event lists the inputs
print("the run wrote:", events[-1]["outputs"][0]["name"])                             # the last event, COMPLETE, names the output

graph = lineage.graph(events)                            # built from the COMPLETE events' column lineage, not from the SQL
for column in ("full_name", "email"):
    inputs = [e for e in graph.edges if e.target == f"marketing.audience.{column}"]
    print(f"marketing.audience.{column} comes from:", ", ".join(f"{e.source} ({e.type} {e.subtype})" for e in inputs))
# The INDIRECT inputs of each kind: the inputs that decide which rows exist, not the ones copied into them.
for subtype in ("FILTER", "JOIN"):
    shaping = [e.source for e in graph.edges if e.target == "marketing.audience" and e.subtype == subtype]
    print(f"its rows are shaped by, INDIRECT {subtype}:", ", ".join(shaping))
duckdb = warehouse.connect(platform)                     # DuckDB on the catalog's tables, to count what the join dropped
# The learners the filter keeps, counted on crm.learners before any join drops one.
consenting = "select count(*) from crm.learners where marketing_consent and status = 'active'"
print("consenting, active learners in crm.learners:", f"{duckdb.sql(consenting).fetchall()[0][0]:,}")  # one row, one column
print("rows in marketing.audience:", f"{duckdb.sql('select count(*) from marketing.audience').fetchall()[0][0]:,}")  # one row, one column
# Every column a change to email can reach, at any depth of the graph.
reached = lineage.columns_reached(graph, lineage.downstream(graph, "crm.learners.email"))
print("a change to crm.learners.email reaches:", ", ".join(reached))

# The catalog check, run on the catalog the pipeline wrote to.
for problem in metadata.problems(platform, metadata.load()):
    print("the catalog check finds:", problem)
```

Output:

```text
events: START of marketing_audience, COMPLETE of marketing_audience
the run read: crm.learners, learning.courses, learning.enrollments
the run wrote: marketing.audience
marketing.audience.full_name comes from: crm.learners.full_name (DIRECT IDENTITY)
marketing.audience.email comes from: crm.learners.email (DIRECT IDENTITY)
its rows are shaped by, INDIRECT FILTER: crm.learners.marketing_consent, crm.learners.status
its rows are shaped by, INDIRECT JOIN: crm.learners.learner_id, learning.courses.category, learning.courses.course_id, learning.enrollments.course_id, learning.enrollments.learner_id
consenting, active learners in crm.learners: 1,861
rows in marketing.audience: 1,829
a change to crm.learners.email reaches: marketing.audience.email
the catalog check finds: marketing.audience: no metadata
```

Read from the events alone, the lineage shows what the table's name leaves out. `marketing.audience.email` comes from `crm.learners.email (DIRECT IDENTITY)`, and `full_name` from `crm.learners.full_name (DIRECT IDENTITY)`, both unchanged copies of personal columns.

The filter and the joins decide which rows the table holds. The filter's inputs are `crm.learners.marketing_consent, crm.learners.status`, so every row says its learner consented. The joins' inputs are `crm.learners.learner_id, learning.courses.category, learning.courses.course_id, learning.enrollments.course_id, learning.enrollments.learner_id`. A learner with no enrollment has no favourite category, so the join to it drops them. `crm.learners` holds 1,861 consenting, active learners, and `marketing.audience` holds 1,829.

A change to `crm.learners.email` reaches only `marketing.audience.email` in this pipeline's table, so renaming the column, or changing its format, touches that column alone. With all four of the platform's pipelines sending lineage, [chapter 4](#impact-of-a-column-change) finds that it reaches no other.

The catalog check, from [the section before](#catalog-a-table) and run on the same catalog, finds `marketing.audience: no metadata`. The pipeline created a table nobody has described, and lineage changes what that gap means: from a table the platform knows nothing about to a copy of two personal columns, chosen by consent. Until someone describes it, the platform's access policy treats every column it can't find a classification for as `sensitive`. So anyone who reads the copy through the platform's enforcement layer, which [a later section](#enforce-one-access-decision) introduces, gets no value from it, as [chapter 6's who-sees-what test](#test-who-sees-what) shows.

**Working rule:** Emit lineage from the code that runs each job, never after it ([chapter 4](#send-run-events)): a START event, then a COMPLETE or FAIL event, with the output's column lineage in the COMPLETE event, parsed from the job's SQL, and the inputs that join and filter rows as well as those that supply values. Read lineage back from the events, never from the SQL, so the graph shows what ran. Where a job isn't SQL that a parser can read, such as a Python script, write its lineage in the same code, and review the two together.

## Enforce one access decision on a query {#enforce-one-access-decision}

With the platform's tables [cataloged](#catalog-a-table), the next question is who may read what. Policy as code starts from OPA's premise that policy can be decoupled from the software it governs, so the people responsible for it can write, analyze, version and distribute it separately ([OPA philosophy](https://www.openpolicyagent.org/docs/philosophy)). A **policy** answers a request with a **decision**. The platform's policy answers with a document rather than a yes or no: whether to allow the read, the **row filters** that keep only the rows the user may see, and the **column masks** that change how a column is shown. The filters and masks are data, never SQL. A decision does nothing on its own. Something between the user and the engine has to apply it to every table a query reads.

Support agents on the platform each serve one region, `americas`, `emea` or `apac`, and need learners' contact details to answer tickets. The policy, `governance/policies/access.rego`, denies every request by default. It allows each group, the role a user holds in `governance/users.toml`, the tables its work needs, and reads the agent's region from the same file. This rule keeps an agent to their region:

```rego
row_filters contains {"column": "support_region", "equals": user.region} if {
	"support" in groups
	table in {"crm.learners", "support.tickets"}
}
```

`lib.policy.decide` evaluates the policy with regopy. `lib.enforce` holds the **enforcement layer**: its `Enforcer` asks the policy about every table a query reads, replaces each with a subquery that applies the decision, and runs the rewrite on DuckDB. `lib.enforce.answer` is the one function a service calls, and it returns rows, never the engine's connection.

`agent-a05`, a support agent in EMEA, asks for three columns of `crm.learners` and counts learners by region through the layer. Next, the emails are checked against the generated files that `lib.platform.load` reads:

Example `support-region-enforced` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""One access decision from the platform's Rego policy, and the same agent's query enforced in the layer. The point rests on
the emea line: the query names no region, yet only EMEA learners come back."""
import json

from lib import policy
from lib.catalog import open_catalog
from lib.enforce import Enforcer, answer
from lib.platform import load

# agent-a05, a support agent in EMEA, asks to read three columns of crm.learners.
request = policy.request("agent-a05", "crm.learners", ["learner_id", "email", "support_region"])  # the shape Trino's OPA plugin sends
decision = policy.decide(request)
assert decision["allow"] is True           # support may read crm.learners; a policy that denies it fails this run
print("allow:", decision["allow"])
print("row filters:", json.dumps(decision["row_filters"]))
print("column masks:", json.dumps(decision["column_masks"]))
print("reasons:", "; ".join(decision["reasons"]))

# The enforcement layer asks the policy about every table a query reads, then rewrites the query to apply the answer.
layer = Enforcer(open_catalog(["crm.learners"]))
query = "select support_region, count(*) as learners from crm.learners group by support_region order by support_region"
for region, learners in answer(layer, query, "agent-a05"):   # the layer adds the agent's region to the query before the engine runs it
    print(f"learners agent-a05 sees in {region}:", f"{learners:,}")

# Compare the emails the agent gets with the platform's data, without printing any.
stored = load("crm.learners")                                  # the generated data, not the catalog's copy
emails = dict(zip(stored.column("learner_id").to_pylist(), stored.column("email").to_pylist()))
seen = answer(layer, "select learner_id, email from crm.learners", "agent-a05")   # the agent's own query, with no region in it
print("emails agent-a05 sees, as stored:", f"{sum(email == emails[learner] for learner, email in seen):,} of {len(seen):,}")
print("learners in the platform's data:", f"{stored.num_rows:,}")
```

Output:

```text
allow: True
row filters: [{"column": "support_region", "equals": "emea"}]
column masks: {}
reasons: support may read crm.learners
learners agent-a05 sees in emea: 1,581
emails agent-a05 sees, as stored: 1,581 of 1,581
learners in the platform's data: 5,000
```

The layer applied the region inside the query, so the agent's SQL didn't have to, and couldn't avoid it. The decision allows the read, with the row filter `[{"column": "support_region", "equals": "emea"}]` on the agent's own region and the column masks `{}`, since support is the group that needs contact details. Its reason is `support may read crm.learners`. The agent's query has no filter on region, yet it returns 1,581 learners, all in EMEA, of the 5,000 the platform holds. Their emails come back as stored, 1,581 of 1,581, because the decision masks nothing.

regopy is the Python binding of rego-cpp, Microsoft's C++ implementation of Rego, which supports Rego v1.18.1 as OPA defines it ([rego-cpp README at v1.5.2](https://github.com/microsoft/rego-cpp/blob/v1.5.2/README.md)). regopy differs from OPA in ways [chapter 5](#where-regopy-differs-from-opa) lists, so OPA stays the reference for anything in production. [Chapter 6](#column-masks-leak) shows why the layer replaces whole tables rather than masking columns where a query names them.

**Working rule:** Write access rules as one policy in the repository that denies by default and returns its decision as data: allow, row filters and column masks. Apply that decision in one layer that rewrites every query before the engine runs it, and give users that layer's answers, never the engine's connection. When an engine can ask the policy itself, as Trino can ask OPA, let the engine be that layer.

## Fail the pull request that adds an unclassified column {#fail-the-pull-request}

[The catalog check](#catalog-a-table) proves the catalog complete on the day it runs, and the platform changes every week. A check that waits for someone to remember it gets run rarely and read less. Run on every pull request, where its exit code can fail it, the same check becomes a gate, and its findings appear where engineers already work. The authors of Tricorder, Google's platform for code analysis, found time and again that when developers have to open a dashboard or run a separate command line tool, their use of analysis drops off ([Sadowski et al., 2015](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43322.pdf)). That is one company's experience with code analysis, not data, but governance checks meet the same people. A gate also fails a pull request only for what it changes, so a finding already on main is reported with its owner and fails no pull request that leaves it as it is.

The book's module for this is `lib.ci`, the platform's governance job. A schema change on the platform is a migration, an `alter table` statement in a file in the branch's `migrations/` folder. Each side of a pull request is a checkout in its own folder, one of main and one of the branch. For each side, `lib.ci.run` builds a scratch platform, a fresh catalog made the way the platform runs. It holds the source tables, the side's migrations, its metadata written into the catalog, and its pipelines. It runs the checks it's given on the branch's platform, runs them on main's alone to learn what is already there, and compares the findings by ID.

This section runs one check, `coverage`. It is [the catalog check](#catalog-a-table), `lib.metadata.problems`, run on the branch's platform, and for each column nobody classified it adds what a rule on column names suggests, from the rules [chapter 3](#classify-columns-from-the-schema) writes.

The CRM team's pull request adds a column for learners' work email in one migration and forgets the column's metadata, so the coverage check has something to find:

Example `unclassified-column-fails` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""The CRM team's pull request adds a column to crm.learners and no metadata for it; the coverage check runs on its branch and
on main. The point rests on the exit code line: the pull request's own finding fails the job, and the findings on main don't."""
from lib import ci

main = ci.checkout()                      # the main branch: the governance files and pipelines, and no migrations yet
branch = ci.checkout(main)                # the pull request's branch, starting from main
# The pull request's only change: a migration that adds the column, with no metadata for it.
(branch / "migrations" / "0001-add-work-email.sql").write_text("alter table crm.learners add column work_email varchar;\n")
print("files the pull request changes:", ", ".join(ci.changed(main, branch)))

# Build a scratch platform from each side, run the coverage check on both, and compare their findings by ID.
report = ci.run(main, branch, checks=["coverage"])
for line in ci.lines(report):
    if not line.startswith("change "):    # schema changes are chapter 10's report
        print(line)
for line in ci.totals(report):
    if line.startswith(("findings the pull request introduces", "findings already on main", "exit code")):
        print(line)
```

Output:

```text
files the pull request changes: migrations/0001-add-work-email.sql
coverage: failed, findings 3, new 1, on main 2, waived 0, 12 tables checked
coverage/ai.review_corpus: no metadata; on main, owner team-platform
coverage/crm.learners.work_email: not classified; its name suggests personal
coverage/marketing.audience: no metadata; on main, owner team-platform
job: failed
findings the pull request introduces: 1
findings already on main: 2
exit code: 1
```

The pull request fails on 1 finding of its own, the column nobody classified. The file it changes is `migrations/0001-add-work-email.sql`, and the coverage check reports `failed, findings 3, new 1, on main 2, waived 0, 12 tables checked`, which counts the platform's eight source tables and the four its pipelines write. The new finding is `crm.learners.work_email`, reported as `not classified; its name suggests personal`. The name rule matches `email`, which suggests the classification, and its ID, `coverage/crm.learners.work_email`, stays the same from run to run, so it can be discussed and counted.

The findings already on main were there before the pull request: `coverage/ai.review_corpus`, and `coverage/marketing.audience`, the table [the lineage section](#capture-one-pipelines-lineage) found undescribed. Nobody owns either table, so the job names the platform team, the team answerable for tables without an owner. The job exits with code `1`, so the pull request fails until the column has a classification, and the findings on main fail no pull request that leaves them as they are. [Chapter 10's job](#run-every-rule-as-one-job) runs the checks of chapters 2 to 7 on the same pull request, 11 of them.

**Working rule:** Run every governance check as one job on every pull request, required by branch protection, and fail it by exit code on any finding the pull request introduces. Report the findings already on the main branch with their owners, without failing the pull request for them. Put every finding in the pull request itself, under an ID that stays the same from run to run, with what to do about it. Run the same checks on a schedule against the production catalog too, for what changes outside pull requests.

## What goes wrong in production {#end-to-end-in-production}

Governance fails without an error in two ways that the pieces above answer: [a spreadsheet nobody updates](#a-spreadsheet-nobody-updates), and [a policy that another tool bypasses](#a-policy-another-tool-bypasses). The first is why the metadata is code, and the second why enforcement sits in one place.

### A governance spreadsheet nobody updates {#a-spreadsheet-nobody-updates}

The spreadsheet this chapter [started from](#governance-end-to-end) lists tables and columns, with a classification beside each, and a spreadsheet describes the schema on the day it was written. Schemas don't hold still. A study of ten open-source database applications, with more than 160,000 revisions between them, lists first among its major findings that database schemas evolve frequently over an application's life ([Qiu, Li and Su, 2013](https://www.cs.ucdavis.edu/~su/publications/fse13-db-study.pdf)). The study covers application databases, not warehouses, but every change that adds a column adds one its spreadsheet doesn't list.

Take the platform's spreadsheet, an inventory of `crm.learners` exported as CSV, one row per column. Then the CRM team's migration from [the pull request above](#fail-the-pull-request) adds `work_email`. Compare it with the catalog after the migration to find what it misses:

Example `spreadsheet-misses-new-column` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""A governance inventory kept as a spreadsheet, exported before a schema change, then compared with the catalog after it.
The point rests on the two work_email lines: the spreadsheet doesn't list the column, and the check finds it unclassified."""
import csv
import io

from lib import ci, metadata
from lib.catalog import open_catalog

platform = open_catalog(["crm.learners"])
described = metadata.load()

# The inventory: one row per column of crm.learners, exported on the day someone was asked for one.
inventory = io.StringIO()
writer = csv.writer(inventory)
writer.writerow(["table", "column", "classification"])
for field in platform.load_table("crm.learners").schema().fields:
    # Metadata is keyed by Iceberg field ID, not by name, so the lookup survives a rename.
    writer.writerow(["crm.learners", field.name, described["crm.learners"].columns[field.field_id].classification])

# Later, the CRM team's migration adds a column for learners' work email, applied as an Iceberg schema change.
ci.migrate(platform, "alter table crm.learners add column work_email varchar;")

rows = list(csv.DictReader(io.StringIO(inventory.getvalue())))
print("columns the spreadsheet lists:", len(rows))
print("of them without a classification, by the spreadsheet:", sum(not row["classification"] for row in rows))  # a blank classification cell: a column the spreadsheet never classified
live = [field.name for field in platform.load_table("crm.learners").schema().fields]
print("columns crm.learners has:", len(live))
print("columns the spreadsheet doesn't list:", ", ".join(sorted(set(live) - {row["column"] for row in rows})))
for problem in metadata.problems(platform, described):
    print("the check against the catalog finds:", problem)
```

Output:

```text
columns the spreadsheet lists: 15
of them without a classification, by the spreadsheet: 0
columns crm.learners has: 16
columns the spreadsheet doesn't list: work_email
the check against the catalog finds: crm.learners.work_email: not classified
```

The spreadsheet looks complete and misses a column. By its own account it lists 15 columns, and 0 of them lack a classification. The table has 16 columns, and the column it doesn't list is `work_email`. Nothing in the spreadsheet can show that, because nothing compares it with the catalog. `lib.metadata.problems`, [the catalog check](#catalog-a-table), walks the catalog and finds `crm.learners.work_email: not classified`, the same finding that fails [the CRM team's pull request](#fail-the-pull-request). In our experience, a copy of the metadata kept by hand, whether a spreadsheet, a wiki page or a data dictionary, goes stale on its first schema change, and nothing says so.

**Working rule:** Never keep governance metadata in a document that nothing checks. Keep it in a reviewed file that a test compares with the live catalog, on every pull request and on a schedule. If people need a spreadsheet, generate it from the file, and say on it when it was generated.

### A policy one tool enforces and another bypasses {#a-policy-another-tool-bypasses}

A policy protects only the reads that pass through whatever enforces it. Trino applies row filters only when it's told where to fetch them, so without its `opa.policy.row-filters-uri` setting it applies no row filtering at all ([Trino 484, OPA access control](https://trino.io/docs/484/security/opa-access-control.html)). Iceberg's REST catalog specification, at 1.12.0, lets a catalog return read restrictions with a table, and states that "A reader that supports read restrictions must fail any read against the loaded table that cannot apply a returned restriction in full" ([REST catalog spec, 1.12.0](https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/open-api/rest-catalog-open-api.yaml)). The spec gives a reader a signal for delegated access, the `X-Iceberg-Access-Delegation` header, but none for read restrictions. So a catalog can't tell which readers will apply its restrictions. PyIceberg 0.12.0's REST client reads none ([source](https://github.com/apache/iceberg-python/blob/pyiceberg-0.12.0/pyiceberg/catalog/rest/__init__.py)). We recommend that a catalog that returns read restrictions give storage access only to engines that apply them.

The [enforcement layer](#enforce-one-access-decision) keeps `agent-a05` to EMEA. The layer has routes around it, though, because anything with the catalog's access can read the table's files. Read the table around the layer twice: with DuckDB through `lib.warehouse.connect`, which the layer itself uses, as a notebook would, and with PyIceberg's own scan, as any reader holding the catalog's access would:

Example `read-around-the-layer` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.31.0), passing in Edition 2026.11.27:

```python
"""The same table, read three ways: through the enforcement layer, and around it with DuckDB and with PyIceberg. The point
rests on the two lines around the layer, which return every region where the layer returns only EMEA's."""
from collections import Counter

from lib import warehouse
from lib.catalog import open_catalog
from lib.enforce import Denied, Enforcer, answer

platform = open_catalog(["crm.learners"])
query = "select support_region, count(*) from crm.learners group by support_region order by support_region"


def show(rows):
    return ", ".join(f"{region} {learners:,}" for region, learners in rows)


layer = Enforcer(platform)
print("through the enforcement layer, as agent-a05:", show(answer(layer, query, "agent-a05")))

# A notebook with DuckDB on the same catalog: the same SQL, and no policy in the way.
print("DuckDB on the same catalog:", show(warehouse.connect(platform).sql(query).fetchall()))

# Any reader that holds the catalog's access, here PyIceberg's own scan: no SQL to rewrite at all.
scan = platform.load_table("crm.learners").scan(selected_fields=("support_region", "email")).to_arrow()
print("PyIceberg's scan of the table:", show(sorted(Counter(scan.column("support_region").to_pylist()).items())))
print("emails PyIceberg's scan returns:", f"{scan.num_rows - scan.column('email').null_count:,}")  # rows whose email isn't null

# lib.warehouse builds each table's view on a scan it registers under a name of its own. Through the layer, it's denied.
try:
    answer(layer, "select count(*) from scan_crm_learners", "agent-a05")
except Denied as reason:
    print("the layer, asked for the raw scan:", reason)
```

Output:

```text
through the enforcement layer, as agent-a05: emea 1,581
DuckDB on the same catalog: americas 2,276, apac 1,143, emea 1,581
PyIceberg's scan of the table: americas 2,276, apac 1,143, emea 1,581
emails PyIceberg's scan returns: 5,000
the layer, asked for the raw scan: not a table in the catalog: scan_crm_learners
```

A reader outside the layer gets every region, because the policy was never asked. Through the layer, the agent's query returns `emea 1,581`. The same SQL on DuckDB with no layer in front returns `americas 2,276, apac 1,143, emea 1,581`. PyIceberg's scan, which has no SQL to rewrite, returns `americas 2,276, apac 1,143, emea 1,581`, with 5,000 emails. The same bypass happens in production whenever a second engine, a Spark job or a script with storage credentials reads the files the governed engine reads.

`lib.warehouse` builds each table's view on a scan that it registers under a name of its own, `scan_crm_learners` for this table, so the layer's connection holds the raw scan too. The last line of output shows the layer's answer when a query names that scan: `not a table in the catalog: scan_crm_learners`. That's the design [chapter 6](#enforcing-policies-on-queries) follows, which enforces in one place and denies everything else that reads data, [whatever isn't a catalog table](#allow-only-catalog-sources). In production, that place is the engine that tools query through, as [chapter 6](#engine-enforcement) argues. And since [storage permissions are part of enforcement](#enforcement-in-production), only that engine and the jobs that write the tables should be able to read the files.

**Working rule:** Choose one place that enforces the policy, the engine every tool queries through, and give storage credentials only to it and to the jobs that write the tables, never to people or notebooks. Deny every query in that place that reads data other than through a catalog table. Before you count a table as protected, list everything that can read its files, and treat any reader that doesn't ask the policy as a bypass, unless it's a job whose outputs are cataloged and classified like the tables it reads.

## What this chapter decided {#end-to-end-decisions}

- **Governance is four kinds of code in one repository:** a metadata file, the code that sends each job's lineage events, an access policy in Rego, and checks that run on every pull request. Only one of them is a policy engine.
- **Every table has an owning team,** never a person, and every column one of four classifications: `public`, `internal`, `personal` or `sensitive`. They live in `governance/metadata.toml`, keyed by Iceberg field ID, and the catalog is tested against the file by walking the catalog.
- **Every pipeline run sends OpenLineage events,** with column lineage parsed from its SQL, including the columns that join and filter rows.
- **Access decisions are data:** allow, row filters and column masks, from one policy that denies by default. An enforcement layer applies them to every query, and denies every read that isn't of a catalog table.
- **Missing metadata fails closed:** the access policy treats a column nobody has classified as `sensitive`, and a table nobody has described stays a finding in every report until someone describes it.
- **The governance job runs on every pull request,** fails on the findings the pull request introduces, and reports the findings already on main with their owners.
- **Everything runs in one process, offline,** on the stand-ins [listed at the start of this chapter](#governance-end-to-end). Governance done this way is a set of small rules, each checked where the data changes, so a gap in the metadata shows up as a failed check rather than as a surprise in a report. The chapters that follow test each rule in turn, on the platform's own tables.
