---
title: "Data Governance as Code"
chapter: "Retention, consent and erasure"
chapter_id: retention-consent-erasure
book: data-governance-as-code
edition: 2026.11.24
verified: 2026-11-12
edition_code: 7X69-5ZK7
canonical: https://rollingedition.com/data-governance-as-code/retention-consent-erasure
license: CC BY 4.0
attribution: "“Retention, consent and erasure,” chapter 7 of Data Governance as Code, Edition 2026.11.24, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/retention-consent-erasure. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Retention, consent and erasure

By the end of this chapter you can keep retention rules as reviewed config, make a withdrawal of consent change the next query, and erase one person from every table their data reached. You'll apply the rules against a day you pass in, find those tables from lineage, and keep only what your legal team has recorded an exception for. You'll also remove what a row delete leaves behind in an Iceberg table, old snapshots, unreferenced files and column statistics, and finish with a scan that reads every file left and shows that none of them holds the person.

The platform, the online learning platform this book follows, sells professional courses to adult learners and keeps its warehouse as Iceberg tables in one catalog. It has kept everything since its first sign-up in January 2024: every support ticket, and every learning event with the IP address it came from. Nothing says how long either should stay. Two requests from one learner test the rest of its governance. Learner 3590 withdraws their consent to marketing email, and some weeks later asks the platform to erase their data. The first should change what marketing sees from the next query on. The second should leave no copy of the learner anywhere: not in the tables built from theirs, and not in the old versions of each table that Iceberg keeps on purpose.

Three terms name the chapter's subjects. **Retention** is how long the platform keeps each kind of data. **Consent** is a person's agreement to one use of their data, such as marketing email, which they can withdraw. **Erasure** is removing a person's data on request. The chapter adds two things to the book's shared code: the platform's retention rules, in `governance/retention.toml`, and the module `lib.retention`, which applies them, plans and carries out an erasure, cleans up and checks the files afterwards, and keeps the register of erasures. It uses `lib.lineage` from [chapter 4](#lineage-from-pipelines) to find where a learner's data went, and the classifications in `lib.metadata` from [chapter 2](#a-catalog-you-can-test). Every example runs PyIceberg 0.12.0 on a local catalog.

## Keep retention rules in a reviewed file {#retention-rules-in-a-file}

A retention rule says how long one kind of data is kept, from which date the time counts, and which rows it applies to. The EU's General Data Protection Regulation (GDPR) states the principle as storage limitation: personal data are to be "kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed" (Article 5(1)(e)), and its Recital 39 says that "time limits should be established by the controller for erasure or for a periodic review" ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). NIST's catalog of security and privacy controls describes the same job in neutral words, in control SI-12(3): "dispose of, destroy, or erase information following the retention period" ([NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)). How long is necessary is for the platform's owners and lawyers to decide; the code applies what they decide, the same way every time.

That argues for rules as config, in a file reviewed like the access policies, and for code that applies them against a day it is given rather than the clock. A job that reads the clock deletes different rows depending on when it runs: a test can't pin its result, and a rerun after a failure can delete more than the run it replaces.

The platform's rules are in `governance/retention.toml`. The periods are the platform's own choices for this book's case, not legal advice:

```toml
[tables."support.tickets"]
keep_days = 730
counted_from = "opened_at"        # tickets record when they were opened, not when they were closed
only_when = { column = "status", equals = "closed" }

[tables."learning.events"]
keep_days = 365
counted_from = "occurred_at"

[tables."billing.payments"]
keep_days = 3650                  # a placeholder for the period the platform's legal team sets for payment records
counted_from = "paid_at"
```

Closed tickets are kept two years, events one year, and payments 3,650 days, a placeholder that [the erasure plan](#plan-erasure-from-lineage) relies on. The tickets rule should count from when a ticket was closed, but the table records only `opened_at`, so a ticket opened 25 months ago and closed last week goes at once. The platform lives with that because adding a `closed_at` column is the support team's change to their own table, not the governance team's; until they make it, the rule errs toward deleting early. `lib.retention.due` turns a rule and a day into an Iceberg filter. Count the rows due on the book's "today", Oct 1, 2026, and 90 days later:

Example `retention-rules-due` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""Which rows the platform's retention rules no longer keep, counted against a day the job is given, never the clock."""
from datetime import timedelta

from lib import retention
from lib.catalog import open_catalog
from lib.platform import TODAY

rules = retention.rules()["tables"]
catalog = open_catalog(sorted(rules))
for name, rule in sorted(rules.items()):
    state = rule.get("only_when")
    print(f"{name}: kept {rule['keep_days']} days from {rule['counted_from']}"
          + (f", once {state['column']} is {state['equals']}" if state else ""))

for day in (TODAY, TODAY + timedelta(days=90)):
    for name, rule in sorted(rules.items()):
        table = catalog.load_table(name)
        print(f"{name} on {day}, kept from:", retention.cutoff(rule, day))
        print(f"{name} on {day}, rows due:", f"{retention.count(table, retention.due(rule, day)):,}")
        print(f"{name} on {day}, rows in the table:", f"{retention.count(table):,}")
```

Output:

```text
billing.payments: kept 3650 days from paid_at
learning.events: kept 365 days from occurred_at
support.tickets: kept 730 days from opened_at, once status is closed
billing.payments on 2026-10-01, kept from: 2016-10-03
billing.payments on 2026-10-01, rows due: 0
billing.payments on 2026-10-01, rows in the table: 17,562
learning.events on 2026-10-01, kept from: 2025-10-01
learning.events on 2026-10-01, rows due: 9,060
learning.events on 2026-10-01, rows in the table: 100,000
support.tickets on 2026-10-01, kept from: 2024-10-01
support.tickets on 2026-10-01, rows due: 58
support.tickets on 2026-10-01, rows in the table: 2,000
billing.payments on 2026-12-30, kept from: 2017-01-01
billing.payments on 2026-12-30, rows due: 0
billing.payments on 2026-12-30, rows in the table: 17,562
learning.events on 2026-12-30, kept from: 2025-12-30
learning.events on 2026-12-30, rows due: 15,545
learning.events on 2026-12-30, rows in the table: 100,000
support.tickets on 2026-12-30, kept from: 2024-12-30
support.tickets on 2026-12-30, rows due: 111
support.tickets on 2026-12-30, rows in the table: 2,000
```

On Oct 1, 2026, the events rule keeps events from 2025-10-01 on, so 9,060 of the 100,000 events are due, and 58 of the 2,000 tickets are closed and were opened more than two years ago. Ninety days later, the same rules make 15,545 events and 111 tickets due. The payments rule makes 0 of the 17,562 payments due on Oct 1 and 0 on Dec 30. The counts depend on the day passed in and on the data, and on nothing else.

**Working rule:** Keep each table's retention period, the column it counts from and the state a row must be in, in a reviewed file, and apply it against a day the scheduler passes in, never the clock. Count from the date the rule means. When the table doesn't record that date, as the platform's tickets don't record when they closed, ask the table's owner to add the column rather than let the rule count from another date for good, and say in the rule's file which way it errs until then.

## Delete expired rows with row deletes {#delete-expired-rows}

With [the rules in a file](#retention-rules-in-a-file), the retention job deletes what they say. Iceberg writers delete rows in one of two ways, set by the table property `write.delete.mode`, which defaults to `copy-on-write` ([Iceberg configuration](https://iceberg.apache.org/docs/latest/configuration/)). Copy-on-write rewrites each affected data file without the deleted rows. Merge-on-read leaves the data file alone and writes a delete file beside it, which the spec defines in two kinds ([Iceberg table spec](https://iceberg.apache.org/spec/)): "Position deletes -- Mark a row deleted by data file path and the row position in the data file", a deletion vector in tables of version 3 or above, and "Equality deletes -- Mark a row deleted by one or more column values, like id = 5". PyIceberg 0.12.0's `Table.delete` always copies on write: with `merge-on-read` set, it warns "Merge on read is not yet supported, falling back to copy-on-write" and rewrites the files anyway ([source](https://github.com/apache/iceberg-python/blob/pyiceberg-0.12.0/pyiceberg/table/__init__.py)). Either way, a delete is a commit, a new snapshot, and the snapshot before it is still there.

`lib.retention.apply` deletes, for each rule, the rows `due` returns for the day it's given, and records the rule's table and the day in the commit's snapshot summary, so the table's own history says why the rows went. Apply the platform's rules on Oct 1, 2026, apply them again, read each table as it is now and by time travel to the snapshot before the delete, and expire the old snapshots by age:

Example `apply-retention` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""Apply the retention rules on the book's "today": Iceberg row deletes, which leave the old rows in older snapshots."""
from datetime import datetime, timedelta, timezone

from lib import retention
from lib.catalog import open_catalog
from lib.platform import TODAY

rules = retention.rules()["tables"]
catalog = open_catalog(sorted(rules))
before = {name: catalog.load_table(name).current_snapshot().snapshot_id for name in rules}

deleted = retention.apply(catalog, TODAY)
for name, rows in deleted.items():
    print(f"{name}, rows deleted:", f"{rows:,}")
print("rows deleted by running again for the same day:", sum(retention.apply(catalog, TODAY).values()))

for name in (name for name, rows in deleted.items() if rows):
    rule, table = rules[name], catalog.load_table(name)
    summary = table.current_snapshot().summary
    print(f"{name}, snapshots:", " then ".join(s.summary.operation.value for s in table.snapshots()))
    print(f"{name}, rows written again to delete the others:", f"{int(summary['added-records']):,}")
    print(f"{name}, the commit records:", summary["retention-rule"], "on", summary["retention-day"])
    rows_due = retention.due(rule, TODAY)
    print(f"{name}, rows due, read now:", f"{retention.count(table, rows_due):,}")
    print(f"{name}, rows due, read by time travel:", f"{retention.count(table, rows_due, before[name]):,}")
    # Snapshots carry real commit times, so their age is measured on the clock, by the table's own setting.
    print(f"{name}, snapshots expired by age today:", retention.expire_by_age(table))
    later = datetime.now(timezone.utc) + timedelta(days=6)
    print(f"{name}, snapshots expired by age six days later:", retention.expire_by_age(table, later))
```

Output:

```text
billing.payments, rows deleted: 0
learning.events, rows deleted: 9,060
support.tickets, rows deleted: 58
rows deleted by running again for the same day: 0
learning.events, snapshots: append then overwrite
learning.events, rows written again to delete the others: 90,940
learning.events, the commit records: learning.events on 2026-10-01
learning.events, rows due, read now: 0
learning.events, rows due, read by time travel: 9,060
learning.events, snapshots expired by age today: 0
learning.events, snapshots expired by age six days later: 1
support.tickets, snapshots: append then overwrite
support.tickets, rows written again to delete the others: 1,942
support.tickets, the commit records: support.tickets on 2026-10-01
support.tickets, rows due, read now: 0
support.tickets, rows due, read by time travel: 58
support.tickets, snapshots expired by age today: 0
support.tickets, snapshots expired by age six days later: 1
```

The job deleted 9,060 events, 58 tickets and 0 payments. Running it again for the same day deleted 0 rows and made no commit, so a retried run is harmless. Each table it changed went from an `append` snapshot to an `overwrite`, and the summary shows what copy-on-write costs: to delete the old events, PyIceberg wrote the other 90,940 again, because the table is one unpartitioned file. Partitioned by month of `occurred_at`, the table would let the same delete drop whole files instead, which `Table.delete` does when every row of a file matches. In PyIceberg 0.12.0, writing a table partitioned by month needs the `pyiceberg-core` extra, which this book's examples don't install.

The time-travel lines matter most here. Read as it is now, `learning.events` holds 0 rows past their retention. Read by time travel, the snapshot before the delete still returns all 9,060, IP addresses included, and the Parquet file that holds them is still on disk. `lib.retention.expire_by_age` expires snapshots older than the table's own `history.expire.max-snapshot-age-ms`, five days here, measured on the clock: it expires 0 snapshots of `learning.events` straight after the delete, and 1 six days later. The retention job isn't finished until the old snapshots are [expired](#expire-snapshots) and [the files no snapshot references are removed](#remove-unreferenced-files): the same clean-up an erasure needs.

**Working rule:** Apply retention as Iceberg row deletes, one rule at a time, and record the rule and the day in each commit's snapshot summary. Make the job idempotent for a given day. Partition large tables by the column a rule counts from, so its deletes drop whole files instead of rewriting them; in PyIceberg, install its `pyiceberg-core` extra to write them. Count the job done only once the old snapshots are expired and their files removed.

## Read consent where the query runs {#consent-at-query-time}

[Retention](#retention-rules-in-a-file) removes rows by age. Consent changes who may use them, and withdrawing it isn't the same event as asking for erasure, so the platform's code treats them as two paths. The GDPR's Article 7(3) says: "The data subject shall have the right to withdraw his or her consent at any time. The withdrawal of consent shall not affect the lawfulness of processing based on consent before its withdrawal." ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). Article 17(1)(b) lists a withdrawal as one ground for erasure, "where there is no other legal ground for the processing". Whether that applies to a given request is for the platform's lawyers. In the code, a withdrawal changes one attribute; an erasure deletes rows.

On the platform, consent is an attribute of the data that the access policy reads, as [chapter 5](#narrow-by-attribute) set it up: marketing's row filter keeps only learners whose `marketing_consent` is true, and the course assistant's keeps only the reviews whose authors' `ai_training_consent` is true. So a withdrawal needs no change to the policy. The CRM, the application where learners manage their accounts, syncs the new value into `crm.learners`, and the next query marketing runs through the enforcement layer, which [chapter 6](#enforcing-policies-on-queries) builds to rewrite every query, returns one learner fewer. Withdraw learner 3590's marketing consent, and compare what marketing sees and the tables hold before the withdrawal, after it, and after the marketing pipeline runs again:

Example `consent-withdrawal` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""A learner withdraws marketing consent: one attribute changes, and marketing's next query returns one learner fewer.
No row is deleted. A table built with the consent filter keeps the learner until its pipeline runs again."""
import json

import pyarrow as pa
from pyiceberg.expressions import EqualTo

from lib import pipelines, policy, retention
from lib.catalog import open_catalog
from lib.enforce import Enforcer

LEARNER = 3590
catalog = open_catalog(["crm.learners", "learning.enrollments", "learning.courses"])
pipelines.run(catalog, "marketing_audience")
decision = policy.decide(policy.request("marketing-1", "crm.learners", ["learner_id"]))
print("marketing's row filters on crm.learners:", json.dumps(decision["row_filters"]))


def report(when: str) -> None:
    seen = [row[0] for row in Enforcer(catalog).sql("select learner_id from crm.learners", "marketing-1").fetchall()]
    print(f"{when}, learners marketing sees:", f"{len(seen):,}")
    print(f"{when}, marketing sees learner {LEARNER}:", LEARNER in seen)
    print(f"{when}, rows stored in crm.learners:", f"{retention.count(catalog.load_table('crm.learners')):,}")
    audience = retention.count(catalog.load_table("marketing.audience"), EqualTo("learner_id", LEARNER))
    print(f"{when}, learner {LEARNER}'s rows in marketing.audience:", audience)


report("before")
learners = catalog.load_table("crm.learners")
row = learners.scan(row_filter=EqualTo("learner_id", LEARNER)).to_arrow()
row = row.set_column(row.schema.get_field_index("marketing_consent"), "marketing_consent", pa.array([False]))
learners.overwrite(row, overwrite_filter=EqualTo("learner_id", LEARNER))     # what the CRM's sync writes
report("after the withdrawal")
pipelines.run(catalog, "marketing_audience")
report("after the audience is built again")
```

Output:

```text
marketing's row filters on crm.learners: [{"column": "marketing_consent", "equals": true}, {"column": "status", "equals": "active"}]
before, learners marketing sees: 1,861
before, marketing sees learner 3590: True
before, rows stored in crm.learners: 5,000
before, learner 3590's rows in marketing.audience: 1
after the withdrawal, learners marketing sees: 1,860
after the withdrawal, marketing sees learner 3590: False
after the withdrawal, rows stored in crm.learners: 5,000
after the withdrawal, learner 3590's rows in marketing.audience: 1
after the audience is built again, learners marketing sees: 1,860
after the audience is built again, marketing sees learner 3590: False
after the audience is built again, rows stored in crm.learners: 5,000
after the audience is built again, learner 3590's rows in marketing.audience: 0
```

Marketing's row filters stay `[{"column": "marketing_consent", "equals": true}, {"column": "status", "equals": "active"}]`. Before the withdrawal, marketing sees 1,861 learners, learner 3590 among them; after it, 1,860, without learner 3590. `crm.learners` still stores 5,000 rows. Nothing was deleted, and the learner's account, enrollments and history are as they were.

The copy is the problem. `marketing.audience`, the list a marketing pipeline builds each night, applies the consent filter when it's built, and the policy gives marketing that table with no consent filter of its own. After the withdrawal it still holds 1 row for learner 3590. Until someone classifies the table's columns, the policy redacts them for every reader; once someone does, as [chapter 4](#classifications-from-lineage) proposes, a campaign sent from the table before its next build reaches someone who said no. Only once the pipeline runs again does it hold 0. A training corpus is built with a consent filter too, and [chapter 9](#withdrawn-after-the-build) checks each build against today's consent before training on it.

A true-or-false column also says too little: `ai_training_consent` is null for everyone who signed up before the platform asked, and false can mean refused or withdrawn. The Data Privacy Vocabulary, a W3C Community Group report rather than a standard, names the states a consent can be in, given, refused, withdrawn, expired and unknown among them ([DPV 2.3](https://w3c-cg.github.io/dpv/2.3/dpv/)).

**Working rule:** Keep consent where the query runs: in one table that the system the learner uses keeps current, read by the policy as a row filter, so a withdrawal changes the next query and deletes nothing. When the platform's lawyers decide that a withdrawal is also a ground for erasure, send it through [the erasure path](#plan-erasure-from-lineage) as well. Rebuild every table built with a consent filter whenever consent changes, or give its readers the same filter. Record each consent as a state and the time it changed, and derive the true-or-false attribute the policy reads from it, counting unknown as not given.

## Plan an erasure from lineage {#plan-erasure-from-lineage}

[A withdrawal](#consent-at-query-time) changes one attribute; an erasure has to find the person everywhere. The GDPR's Article 17(1) opens: "The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay", on the grounds it lists ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). Which grounds apply is a legal question. The platform treats a request as reaching every copy, so the first job is a list of where the person's data is, an engineering question with two halves. The source tables that hold a learner's ID come from the catalog: [chapter 2](#classify-pseudonymous-ids) decided that every table with a `learner_id` is part of every erasure, whatever its classification. The tables built from them come from lineage: [chapter 4](#impact-of-a-column-change)'s walk of the column graph, run from each source table, reaches every table their rows shaped.

Some data stays. Article 17(3) opens: "Paragraphs 1 and 2 shall not apply to the extent that processing is necessary:", and its five points include "(b) for compliance with a legal obligation which requires processing by Union or Member State law to which the controller is subject" ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). Whether an exception applies, to which table, and for how long is the platform's legal team's decision, never the code's. The code gives the decision one place, in `governance/retention.toml`, where the legal team writes each exception with its reason. The book's reason is a placeholder, because we decide no legal question:

```toml
[erasure.exceptions."billing.payments"]
reason = "PLACEHOLDER: a legal obligation to keep payment records, such as tax records. The legal team replaces this with the obligation and the law it comes from."
decided_by = "legal team"         # a role, never a person's name
erase_columns = ["card_number"]   # what the obligation doesn't need; an empty list keeps the whole row
```

An erasure keeps an excepted table's rows until the table's [retention rule](#retention-rules-in-a-file) deletes them, and erases the columns `erase_columns` lists from them at once: here the full card number, which the platform's metadata says "Should not be stored at all". `lib.retention.exceptions` refuses an exception with no reason, or one for a table no rule ends.

Finding a derived table isn't the same as finding the learner's rows in it. `lib.retention.plan` looks at the lineage edges into each table the walk reaches, for a column copied unchanged, an IDENTITY edge in OpenLineage's terms, from the learner's ID or from the ID of one of their rows, such as a review. If there is one, the plan deletes by that column. If there's none, the learner's rows only shaped the table, and the plan runs the table's job again once the sources are erased. The catalog the plan reads is the platform as the request finds it, weeks after the withdrawal: `crm.learners` holds learner 3590's withdrawn consent, and the four pipelines of [chapter 4](#lineage-from-pipelines), which build the analytics, marketing and AI tables, have run since, with their lineage recorded. Plan learner 3590's erasure:

Example `erasure-plan` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0 · tldextract 5.4.0), passing in Edition 2026.11.24:

```python
"""Plan one learner's erasure: the tables that hold their learner_id, then every table lineage says their rows reach,
with the exceptions the platform's legal team recorded in governance/retention.toml."""
from lib import pii, retention

LEARNER = 3590
catalog, graph = retention.open_platform()           # weeks after the learner withdrew marketing consent
steps = retention.plan(catalog, graph, LEARNER)
for step in steps:
    if step.column is None:
        print(f"{step.table}: run {retention.job_for(step.table)} again")
    elif step.kept:
        print(f"{step.table}: keep, under an exception, and erase {', '.join(step.cleared)}")
    else:
        print(f"{step.table}: delete where {step.column} in {list(step.values)}"
              + (f", a copy of {step.via}" if step.via else ""))

print("tables in the plan:", len(steps))
print("tables found by their learner_id column:", sum(1 for step in steps if step.column and not step.via))
print("tables found by lineage:", sum(1 for step in steps if step.via or step.column is None))
for step in (step for step in steps if step.kept):
    print(f"the reason recorded for {step.table}:", step.kept)
theirs = retention.rows_of([LEARNER])
for name in ("billing.payments", "marketing.audience"):
    print(f"the learner's rows in {name}:", retention.count(catalog.load_table(name), theirs))
found = retention.traces(catalog, steps, LEARNER)
# The phone number is printed through lib.pii.masked, which keeps its shape and its last four digits.
print("the learner's identifying values, as the scan searches for them:", pii.masked(", ".join(found.texts)))
named = retention.mentions(catalog, steps, found)
print("rows the plan doesn't delete whose text names the learner:", sum(named.values()))
```

Output:

```text
billing.payments: keep, under an exception, and erase card_number
crm.learners: delete where learner_id in [3590]
learning.enrollments: delete where learner_id in [3590]
learning.events: delete where learner_id in [3590]
learning.reviews: delete where learner_id in [3590]
support.tickets: delete where learner_id in [3590]
analytics.course_performance: run course_performance again
analytics.learner_activity: delete where learner_id in [3590], a copy of crm.learners.learner_id
marketing.audience: delete where learner_id in [3590], a copy of crm.learners.learner_id
ai.review_corpus: delete where review_id in [1199], a copy of learning.reviews.review_id
tables in the plan: 10
tables found by their learner_id column: 6
tables found by lineage: 4
the reason recorded for billing.payments: PLACEHOLDER: a legal obligation to keep payment records, such as tax records. The legal team replaces this with the obligation and the law it comes from.
the learner's rows in billing.payments: 2
the learner's rows in marketing.audience: 0
the learner's identifying values, as the scan searches for them: •••-•••-5880 x•, 87199 jacob rad, alexa reed, alexa590@post.e
rows the plan doesn't delete whose text names the learner: 0
```

The plan visits 10 tables: 6 source tables with a `learner_id` column, and 4 that lineage adds. It keeps the learner's 2 payments under the exception. The plan is decided by columns and lineage, not rows, so it lists two tables that hold nothing of the learner's: `support.tickets`, since learner 3590 never opened a ticket, and `marketing.audience`, which holds 0 rows because the pipeline rebuilt it after the withdrawal. `ai.review_corpus` has no `learner_id` at all, but lineage says its `review_id` is an IDENTITY copy of `learning.reviews.review_id`, so the plan deletes the learner's one review by that ID. `analytics.course_performance` holds only counts and averages per course, so the plan rebuilds it from the erased sources. Whether an average that once counted the learner is still their data is a legal question; rebuilding costs one pipeline run, so the code doesn't need the answer.

Text can name a person in rows the plan doesn't delete, such as another learner's ticket. The example searches every string column for the identifying values `governance/retention.toml` lists, and finds 0 such rows. The search matches the first 15 characters of each value, lowercased, anywhere in the text: here `•••-•••-5880 x•, 87199 jacob rad, alexa reed, alexa590@post.e`, printed with the phone number masked, cut to 15 for the reason [the final scan](#verify-the-erasure) explains. A name typed differently or a phone number without separators needs the detectors of [chapter 3](#finding-personal-data).

**Working rule:** Plan every erasure from the catalog and the lineage graph, not from a list someone maintains: every table with the person's ID column, then every table lineage says their rows reach. Delete from a derived table by a column that lineage shows is an unchanged copy of an ID, and rebuild the derived tables the person's rows only shaped. Keep exceptions in config, written by your legal team with their reasons, and let the plan read and show them; never let the code decide one. Run [chapter 4's check for tables no job's lineage accounts for](#job-nobody-instrumented) first, because the plan can't reach a copy the lineage doesn't show.

## Erase the rows the plan lists {#erase-the-rows}

[The plan](#plan-erasure-from-lineage) says where learner 3590's data is, and `lib.retention.erase` carries it out, in its order. It deletes each step's rows with `Table.delete`, sources first, writes the rows an exception keeps again with the exception's columns empty, and runs the job of each table the plan rebuilds once the sources are done. Every commit records the request's ID, `erasure-0001`, in its snapshot summary. A summary is written into the table's metadata files, which Iceberg keeps after the snapshot expires: all of them by default, and the last `write.metadata.previous-versions-max`, 100 by default, with `write.metadata.delete-after-commit.enabled` set ([Iceberg maintenance](https://iceberg.apache.org/docs/latest/maintenance/), [Iceberg configuration](https://iceberg.apache.org/docs/latest/configuration/)). So the summary holds only the request's ID, which [the erasure register](#erased-learner-comes-back) pairs with a keyed hash of the learner's ID, and never the learner's email. Erase the learner, then read two tables as they are now and by time travel:

Example `erase-learner` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""Carry out the erasure plan with Iceberg row deletes. The current snapshots no longer hold the learner; the snapshots
before them still do, and time travel reads them."""
from lib import retention

LEARNER = 3590
catalog, graph = retention.open_platform()
steps = retention.plan(catalog, graph, LEARNER)
before = {step.table: catalog.load_table(step.table).current_snapshot().snapshot_id for step in steps}

done = retention.erase(catalog, steps, "erasure-0001")
for table, rows in done.items():
    print(f"{table}, rows deleted:" if rows != "rebuilt" else f"{table}:", rows)
print("tables one row was deleted from:", ", ".join(table for table, rows in done.items() if rows == 1))
theirs = retention.rows_of([LEARNER])
payments = catalog.load_table("billing.payments").scan(row_filter=theirs).to_arrow()
print("billing.payments, the learner's rows kept:", payments.num_rows)
print("billing.payments, card numbers left in them:", payments.num_rows - payments["card_number"].null_count)
for name in ("crm.learners", "learning.events"):
    table = catalog.load_table(name)
    print(f"the learner's rows in {name}, read now:", retention.count(table, theirs))
    print(f"the learner's rows in {name}, read by time travel:", retention.count(table, theirs, before[name]))

summary = catalog.load_table("crm.learners").current_snapshot().summary
print("crm.learners, rows written again to delete one:", f"{int(summary['added-records']):,}")
print("crm.learners, the commit records:", summary["erasure-request"])
holding = [(table, snapshot) for step in steps if step.column is not None
           for table in [catalog.load_table(step.table)] for snapshot in table.snapshots()
           if not step.kept and retention.count(table, retention.rows(step), snapshot.snapshot_id)]
print("snapshots that still hold the rows the erasure deleted:", len(holding))
print("of them current:", sum(snapshot == table.current_snapshot() for table, snapshot in holding))
```

Output:

```text
billing.payments, rows deleted: 0
crm.learners, rows deleted: 1
learning.enrollments, rows deleted: 2
learning.events, rows deleted: 19
learning.reviews, rows deleted: 1
support.tickets, rows deleted: 0
analytics.course_performance: rebuilt
analytics.learner_activity, rows deleted: 1
marketing.audience, rows deleted: 0
ai.review_corpus, rows deleted: 1
tables one row was deleted from: crm.learners, learning.reviews, analytics.learner_activity, ai.review_corpus
billing.payments, the learner's rows kept: 2
billing.payments, card numbers left in them: 0
the learner's rows in crm.learners, read now: 0
the learner's rows in crm.learners, read by time travel: 1
the learner's rows in learning.events, read now: 0
the learner's rows in learning.events, read by time travel: 19
crm.learners, rows written again to delete one: 4,999
crm.learners, the commit records: erasure-0001
snapshots that still hold the rows the erasure deleted: 6
of them current: 0
```

The erasure deleted the learner's rows from every table in the plan that held any: 19 events, 2 enrollments, and one row from each of `crm.learners, learning.reviews, analytics.learner_activity, ai.review_corpus`. It deleted none from `support.tickets` and `marketing.audience`, which held none, and it rebuilt `analytics.course_performance`. `billing.payments` keeps the learner's 2 payments, with 0 card numbers left in them. Read now, `crm.learners` holds 0 rows for the learner. Read by time travel to the snapshot before the erasure, it returns 1, with name, email, phone and address, and `learning.events` returns all 19 events. To delete one row of `crm.learners`, PyIceberg wrote the other 4,999 into a new file, as copy-on-write does, and the old file, with the learner in it, belongs to the snapshot before.

Across the plan's tables, 6 snapshots still hold the rows the erasure deleted, and 0 of them are current. That is what snapshots are for: a reader can go back to any of them, and a bad commit can be rolled back. For an erasure, it means the delete took the learner out of the table but not out of storage.

**Working rule:** Carry out an erasure as row deletes in the plan's order, and record only a request ID in each commit, never a value of the person's. Treat the delete as the first of three steps: the snapshots before it still hold the person, and anyone allowed to time travel can read them until they're [expired](#expire-snapshots).

## Expire snapshots by the table's own settings {#expire-snapshots}

[After the erasure's deletes](#erase-the-rows), learner 3590's rows live on in the snapshots before them. The Iceberg spec says what comes next: "Table snapshots expire and are removed from metadata to allow removed or replaced data files to be physically deleted" ([Iceberg table spec](https://iceberg.apache.org/spec/)). Each table says how, in its properties ([Iceberg configuration](https://iceberg.apache.org/docs/latest/configuration/)): `gc.enabled` "Allows garbage collection operations such as expiring snapshots and removing orphan files", `history.expire.min-snapshots-to-keep` is how many snapshots to keep however old they are, and `history.expire.max-snapshot-age-ms` is the age at which the rest may go. In Iceberg's Java library, "Regularly expiring snapshots deletes unused data files" ([Iceberg maintenance](https://iceberg.apache.org/docs/latest/maintenance/)).

PyIceberg 0.12.0 does less. Its `table.maintenance.expire_snapshots()` commits one change, which removes the snapshots from the table's metadata, and deletes no file ([source](https://github.com/apache/iceberg-python/blob/pyiceberg-0.12.0/pyiceberg/table/update/snapshot.py)), though its documentation offers it to "clean up table metadata and reduce storage costs" ([PyIceberg API](https://py.iceberg.apache.org/api/)). Nothing in it reads `gc.enabled`, and only its command-line tool reads the `history.expire` settings. An issue asks for expiry to delete files too ([issue 2604](https://github.com/apache/iceberg-python/issues/2604)). Take `crm.learners` with 3 snapshots, the load and two deletes, once with `gc.enabled=false` and once with `history.expire.min-snapshots-to-keep=3`. Expire both by age with PyIceberg, `older_than` the current time, and with `lib.retention.expire`, which reads the two settings first:

Example `expiry-ignores-table-settings` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""PyIceberg's snapshot expiry ignores two of the table's own settings, gc.enabled and min-snapshots-to-keep. The
book's expiry reads them first."""
from datetime import datetime, timezone

from pyiceberg.expressions import EqualTo

from lib import retention
from lib.catalog import open_catalog


def learners_with(settings: dict):
    """crm.learners with three snapshots: the load, then two deletes."""
    table = open_catalog(["crm.learners"]).load_table("crm.learners")
    with table.transaction() as transaction:
        transaction.set_properties(settings)
    for learner in (3590, 3591):
        table.delete(EqualTo("learner_id", learner))
    return table


for settings in ({"gc.enabled": "false"}, {"history.expire.min-snapshots-to-keep": "3"}):
    setting = ", ".join(f"{key}={value}" for key, value in settings.items())
    table = learners_with(settings)
    print(f"{setting}, snapshots:", len(table.snapshots()))
    try:
        print(f"{setting}, the book's expiry expires:", retention.expire(table))
    except retention.RetentionError as error:
        print(f"{setting}, the book's expiry refuses:", error)
    table.maintenance.expire_snapshots().older_than(datetime.now(timezone.utc)).commit()     # by age, as of now
    print(f"{setting}, snapshots left by PyIceberg's expiry:", len(table.snapshots()))
```

Output:

```text
gc.enabled=false, snapshots: 3
gc.enabled=false, the book's expiry refuses: crm.learners has gc.enabled=false, which turns off garbage collection for the table
gc.enabled=false, snapshots left by PyIceberg's expiry: 1
history.expire.min-snapshots-to-keep=3, snapshots: 3
history.expire.min-snapshots-to-keep=3, the book's expiry expires: 0
history.expire.min-snapshots-to-keep=3, snapshots left by PyIceberg's expiry: 1
```

With garbage collection off, PyIceberg's expiry by age left 1 of the 3 snapshots, and with three to keep, it also left 1: `older_than` expires every snapshot older than the time it's given except those a branch or tag points at, here only the current one. The book's expiry refused the first table, `crm.learners has gc.enabled=false, which turns off garbage collection for the table`, and expired 0 snapshots of the second. An owner sets these properties for reasons the expiring code can't see, and in PyIceberg they are only advice.

For an erasure, both settings mean the job can't finish: a table that keeps a snapshot from before the delete still holds the person. A job that stopped at that table would already have deleted rows from the tables before it, and would leave every table after it unexpired, so the check belongs before the first delete. `lib.retention.erase_everywhere` runs `lib.retention.blocked` on every table in the plan first: garbage collection off, more than one snapshot to keep, or a branch or tag besides `main`. If any table fails, the job refuses to start and names every such table. Turn off garbage collection on `crm.learners`, keep three snapshots of `learning.events`, then run the job and the scan:

Example `erasure-refuses-to-start` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""The erasure job checks every table in its plan before it changes any. When a table's own settings would keep the
learner, it refuses to start and names the tables; the scan of every file still runs, and finds the learner."""
from datetime import timedelta

from lib import retention

LEARNER = 3590
catalog, graph = retention.open_platform()
for name, settings in (("crm.learners", {"gc.enabled": "false"}),
                       ("learning.events", {"history.expire.min-snapshots-to-keep": "3"})):
    with catalog.load_table(name).transaction() as transaction:
        transaction.set_properties(settings)
before = {name: catalog.load_table(name).current_snapshot().snapshot_id for name in retention.tables(catalog)}

try:
    steps, found, done = retention.erase_everywhere(catalog, graph, LEARNER, "erasure-0001", min_age=timedelta(0))
except retention.ErasureRefused as refusal:
    for name, why in refusal.tables.items():
        print(f"the job refuses, because of {name}:", why)
    found = refusal.found
print("tables the job changed:", sum(catalog.load_table(name).current_snapshot().snapshot_id != snapshot
                                     for name, snapshot in before.items()))
report = retention.scan(catalog, found)
print("tables whose files hold the learner:", sum(1 for _, holding in report.values() if holding))
print("files holding the learner:", sum(holding for _, holding in report.values()))
```

Output:

```text
the job refuses, because of crm.learners: gc.enabled=false turns off garbage collection for the table
the job refuses, because of learning.events: history.expire.min-snapshots-to-keep=3 keeps the snapshot from before the delete
tables the job changed: 0
tables whose files hold the learner: 7
files holding the learner: 8
```

The job names both tables, `crm.learners` because `gc.enabled=false turns off garbage collection for the table`, and `learning.events` because `history.expire.min-snapshots-to-keep=3 keeps the snapshot from before the delete`, and changed 0 tables. The scan runs either way, from the traces the refusal carries, and finds the learner in 8 files across 7 tables, since nothing was erased. A person then decides with the tables' owners, rather than code overriding an owner's setting.

**Working rule:** Expire snapshots through one function of your own that reads `gc.enabled` and the `history.expire` settings before it expires anything, and refuses when garbage collection is off, because PyIceberg's expiry reads neither; check again at every PyIceberg release. Before an erasure deletes anything, check every table in its plan the same way, and refuse the whole erasure when one would keep the person. For an erasure, expire every snapshot older than the delete. For retention, expire by age, as `history.expire.max-snapshot-age-ms` says, measured on the clock, since snapshots carry real commit times.

## Remove the files no snapshot references {#remove-unreferenced-files}

Once [the old snapshots are expired](#expire-snapshots), the files only they referenced are unreferenced: under the table's location, but in no snapshot's metadata. Iceberg calls them orphans, and its Java library removes them in a separate action, with a warning: "It is dangerous to remove orphan files with a retention interval shorter than the time expected for any write to complete", and "The default interval is 3 days." ([Iceberg maintenance](https://iceberg.apache.org/docs/latest/maintenance/)). PyIceberg 0.12.0 has no such action. Its release notes list none ([release notes](https://github.com/apache/iceberg-python/releases/tag/pyiceberg-0.12.0)), the issue that asked for one was closed by the project's stale bot, marked not planned ([issue 1200](https://github.com/apache/iceberg-python/issues/1200)), and two pull requests that added one were closed without being merged ([1958](https://github.com/apache/iceberg-python/pull/1958), [3358](https://github.com/apache/iceberg-python/pull/3358)). Its only call that deletes data files is `purge_table`, which deletes the whole table ([source](https://github.com/apache/iceberg-python/blob/pyiceberg-0.12.0/pyiceberg/catalog/__init__.py)).

So `lib.retention` removes them itself, from what the metadata tables PyIceberg exposes as `table.inspect` say a table references. `lib.retention.referenced` collects the metadata files, current and logged, every snapshot's manifest list, every manifest (a manifest lists data files, with each file's column statistics), every data and delete file live in any snapshot, and any statistics files. Every other file under the table's location is unreferenced, and `lib.retention.sweep` deletes the ones older than the minimum age its caller passes. `governance/retention.toml` sets that age to 72 hours, Java's default, and `lib.retention.min_file_age` reads it. After the erasure, expire the plan's tables, sweep with that age and then with none, and check every file for the learner:

Example `sweep-unreferenced-files` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""After the erasure, expire the old snapshots, then remove the files no snapshot references. PyIceberg's expiry
deletes no file, and it has no orphan-file removal, so lib.retention.sweep does it with PyIceberg's inspect tables."""
from datetime import timedelta

from lib import retention

LEARNER = 3590
catalog, graph = retention.open_platform()
steps = retention.plan(catalog, graph, LEARNER)
found = retention.traces(catalog, steps, LEARNER)
retention.erase(catalog, steps, "erasure-0001")
tables = [catalog.load_table(step.table) for step in steps]
print("snapshots expired:", sum(retention.expire(table) for table in tables))
print("files under the plan's tables:", sum(len(retention.files_under(table.location())) for table in tables))
print("files no metadata references:", sum(len(retention.unreferenced(table)) for table in tables))
print("files holding the learner, after expiry:", sum(held for _, held in retention.scan(catalog, found).values()))
print("files swept with the configured minimum age:", sum(retention.sweep(t, retention.min_file_age()) for t in tables))
# One writer, nothing in flight: no file is too young to remove, so the examples sweep with no minimum age.
print("files swept with no minimum age:", sum(retention.sweep(table, timedelta(0)) for table in tables))
print("files holding the learner, after the sweep:", sum(held for _, held in retention.scan(catalog, found).values()))

for table in tables:
    entries = table.inspect.entries()
    for status, metrics in zip(entries["status"].to_pylist(), entries["readable_metrics"].to_pylist()):
        bounds = metrics.get("email") or {}
        kept = (bounds.get("lower_bound"), bounds.get("upper_bound"))
        if any(text in bound.lower() for bound in kept if bound for text in found.texts):
            print(f"{'.'.join(table.name()[-2:])}, manifest entry with status {status}, email bounds:",
                  bounds["lower_bound"], "to", bounds["upper_bound"])
```

Output:

```text
snapshots expired: 8
files under the plan's tables: 100
files no metadata references: 28
files holding the learner, after expiry: 9
files swept with the configured minimum age: 0
files swept with no minimum age: 28
files holding the learner, after the sweep: 1
crm.learners, manifest entry with status 2, email bounds: ALEXA590@POST.EX to zofia.haase@exan
```

Expiry removed 8 snapshots and no file. Of the 100 files under the plan's tables, 28 are referenced by nothing, and 9 files hold the learner. A sweep with the configured 72 hours deleted 0 files, since every file was written seconds before. The examples then pass an age of zero, because one process writes their catalog. That sweep deleted 28 files, and 1 file still holds the learner: a manifest that the current snapshot of `crm.learners` references.

The spec says why: "When a file is replaced or deleted from the dataset, its manifest entry fields store the snapshot ID in which the file was deleted and status 2 (deleted)" ([Iceberg table spec](https://iceberg.apache.org/spec/)). That entry keeps the deleted file's column statistics. By default, under the metrics mode `truncate(16)` ([Iceberg configuration](https://iceberg.apache.org/docs/latest/configuration/)), those include each string column's smallest value, cut to 16 characters, and its largest, cut to 16 with the last character raised by one, so that it still bounds every value in the file ([source](https://github.com/apache/iceberg-python/blob/pyiceberg-0.12.0/pyiceberg/utils/truncate.py)). The deleted entry in `crm.learners` keeps the email bounds `ALEXA590@POST.EX to zofia.haase@exan`. The first is learner 3590's email, typed in capitals, which sorts before every other email on the platform. The second is learner 4998's, the platform's largest, whose 16th character, an `m`, became an `n`. No learner is safe from this: each data file's entry keeps the smallest and largest value of every column, so a table of many small files names many learners.

**Working rule:** Remove unreferenced files after every expiry, with a sweep of your own built on the inspect tables, since PyIceberg has none, and keep a minimum age of days in production so that a write in progress keeps its files. Use an age of zero only where a single process writes. Don't count a person erased because no data file holds them: the manifests may still hold their values.

## Keep personal values out of manifests {#keep-values-out-of-manifests}

[The sweep](#remove-unreferenced-files) left the learner's email in a manifest, as a column bound. Iceberg lets a table choose, per column, what its manifests keep, with the property `write.metadata.metrics.column.<name>`: `none` keeps nothing, `counts` keeps value and null counts, `truncate(n)` adds bounds cut to n characters, and `full` adds whole bounds ([Iceberg configuration](https://iceberg.apache.org/docs/latest/configuration/)). PyIceberg 0.12.0 looks the property up by the column's name when it writes a file ([source](https://github.com/apache/iceberg-python/blob/pyiceberg-0.12.0/pyiceberg/io/pyarrow.py)).

Typed by hand, those properties would drift from the classifications. `lib.retention.properties` generates them instead, from `governance/metadata.toml` and the `[statistics]` section of `governance/retention.toml`: `none` for every column classified `personal` or `sensitive`, and for every column nobody has classified, the same fail-closed default the access policy uses. It adds the `history.expire` settings from the rules' `[snapshots]` section. `lib.retention.apply_properties` sets them on every table and rewrites each table's data once, because a metrics mode applies only to the files written after it's set; expiry and a sweep then remove the files from before. Erase learner 4998, whose email is the largest bound in the manifest of `crm.learners`, on two platforms, one with default statistics and one with the generated properties:

Example `statistics-off-for-personal-columns` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""Generate each table's properties from the classifications, so manifests keep no values of personal columns, then
erase the learner whose email is the platform's largest on a platform with them and on one without."""
from datetime import timedelta

from lib import retention

LEARNER = 4998
for statistics_off in (False, True):
    catalog, graph = retention.open_platform(statistics_off)
    label = "statistics off for protected columns" if statistics_off else "default statistics"
    if statistics_off:
        generated = retention.properties(catalog)
        turned_off = [key for wanted in generated.values() for key in wanted if key.startswith(retention.METRICS)]
        print("columns with statistics turned off:", len(turned_off))
        unclassified = [name for name in generated if name not in retention.metadata.load()]
        print("of them in tables nobody has classified:",
              sum(key.startswith(retention.METRICS) for name in unclassified for key in generated[name]))
        print("crm.learners, properties set:", len(generated["crm.learners"]))
        for key, value in sorted(generated["crm.learners"].items()):
            print(f"  {key} = {value}")
    entry = catalog.load_table("crm.learners").inspect.entries()["readable_metrics"].to_pylist()[0]
    print(f"{label}, crm.learners email bounds:", entry["email"]["lower_bound"], "to", entry["email"]["upper_bound"])
    columns = retention.metadata.load()["crm.learners"].columns.values()
    personal = [column.name for column in columns if column.classification == "personal"]
    print(f"{label}, crm.learners personal columns:", len(personal))
    with_bounds = sum(entry[name]["lower_bound"] is not None for name in personal)
    print(f"{label}, of them with bounds in the manifest:", with_bounds)
    steps, found, _ = retention.erase_everywhere(catalog, graph, LEARNER, "erasure-0002", min_age=timedelta(0))
    print(f"{label}, files holding learner {LEARNER} after erasure, expiry and sweep:",
          sum(held for _, held in retention.scan(catalog, found).values()))
```

Output:

```text
default statistics, crm.learners email bounds: ALEXA590@POST.EX to zofia.haase@exan
default statistics, crm.learners personal columns: 7
default statistics, of them with bounds in the manifest: 7
default statistics, files holding learner 4998 after erasure, expiry and sweep: 1
columns with statistics turned off: 24
of them in tables nobody has classified: 10
crm.learners, properties set: 9
  history.expire.max-snapshot-age-ms = 432000000
  history.expire.min-snapshots-to-keep = 1
  write.metadata.metrics.column.city = none
  write.metadata.metrics.column.date_of_birth = none
  write.metadata.metrics.column.email = none
  write.metadata.metrics.column.full_name = none
  write.metadata.metrics.column.notes = none
  write.metadata.metrics.column.phone = none
  write.metadata.metrics.column.street_address = none
statistics off for protected columns, crm.learners email bounds: None to None
statistics off for protected columns, crm.learners personal columns: 7
statistics off for protected columns, of them with bounds in the manifest: 0
statistics off for protected columns, files holding learner 4998 after erasure, expiry and sweep: 0
```

The generated properties turn statistics off for 24 columns, 10 of them in `marketing.audience` and `ai.review_corpus`, the two tables that [chapter 2](#test-the-catalog-against-the-metadata) found with no metadata. `crm.learners` gets 9 properties, the two expiry settings and `none` for each personal column. With default statistics, the manifest's email bounds are `ALEXA590@POST.EX to zofia.haase@exan`, and it keeps bounds for 7 of the table's 7 personal columns. After the erasure, expiry and sweep, 1 file still holds learner 4998, through that raised upper bound. With statistics off, the email bounds are `None to None`, the manifest keeps bounds for 0 personal columns, and 0 files hold the learner.

The cost is pruning. Iceberg uses the bounds in manifests to skip files a query's filter can't match ([Iceberg table spec](https://iceberg.apache.org/spec/)), so without them, a query that filters on `email` reads every file. The platform filters and erases by `learner_id`, which is `internal` and keeps its statistics. `counts` is the other choice: it keeps the counts that help a planner, and no values. And because PyIceberg 0.12.0 keeps the property under the column's old name on a rename, leaving the new name without it, the properties are generated again on every schema change, as [chapter 2](#key-column-metadata-by-field-id) asks of every view of the metadata keyed by name.

**Working rule:** Generate per-column metrics properties from your classifications, `none` or `counts` for every personal, sensitive or unclassified column, and apply them when a table is created or, for an existing table, with one rewrite followed by expiry and a sweep. Keep statistics on the ID columns you filter and erase by. Generate the properties again after every schema change.

## Prove the erasure by reading every file {#verify-the-erasure}

[The delete](#erase-the-rows), [the expiry](#expire-snapshots), [the sweep](#remove-unreferenced-files) and [the statistics settings](#keep-values-out-of-manifests) each removed something the step before left behind, and left something of its own, which is the case for checking the result rather than trusting the steps. The European Data Protection Board's report on how controllers handle erasure, adopted in February 2026, found backups, and anonymisation used in place of deletion, among the weak points, and recommends that controllers "Verify that erasure has been carried out and be able to demonstrate such erasure" ([EDPB, 2026](https://www.edpb.europa.eu/system/files/2026-02/edpb_cef-report_2025_right-to-erasure_en.pdf)).

`lib.retention.scan` reads every file under the catalog's warehouse, each with its own format's reader, and looks for the learner's traces, which `lib.retention.traces` noted before the erasure: the IDs of every row the plan deletes, by column, and the first 15 characters, lowercased, of each identifying value. Fifteen, because a manifest keeps a largest value's first 15 characters unchanged and raises the 16th by one, so a search for 16 misses a person whose value is a file's largest, as learner 4998's email is. A Parquet file is read as rows. A manifest or manifest list, both Avro, is read record by record with PyIceberg's Avro reader: every string in it, bounds included, and the bounds of each ID column, decoded by the schema the manifest carries. A metadata file is read as text. In a table an exception keeps, the learner's IDs are expected, so there the scan looks only for values, including those of the columns the exception erased. `lib.retention.erase_everywhere` runs the whole job: plan, note the traces, check every table, erase, expire, sweep. Run it on the platform with the generated properties, then scan:

Example `verify-erasure` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""The whole erasure job on the platform with statistics off for protected columns, ending with a scan of every file
under the warehouse. What it prints is the evidence: IDs and counts, never the learner's values."""
from datetime import timedelta

from lib import retention

LEARNER, REQUEST = 3590, "erasure-0001"
catalog, graph = retention.open_platform(statistics_off=True)
steps, found, done = retention.erase_everywhere(catalog, graph, LEARNER, REQUEST, min_age=timedelta(0))

report = retention.scan(catalog, found)
for table, (files, holding) in report.items():
    print(f"{table}: {files} files read, {holding} holding the learner")

print("request:", REQUEST)
print("tables visited:", len(steps))
print("rows deleted:", sum(rows for rows in done.values() if rows != "rebuilt"))
print("tables rebuilt:", ", ".join(table for table, rows in done.items() if rows == "rebuilt"))
print("tables kept under an exception, columns erased:",
      "; ".join(f"{step.table}, {', '.join(step.cleared)}" for step in steps if step.kept))
print("snapshots a reader can still time travel to:",
      sum(len(catalog.load_table(step.table).snapshots()) - 1 for step in steps))
print("files no metadata references:",
      sum(len(retention.unreferenced(catalog.load_table(name))) for name in retention.tables(catalog)))
print("tables missing their generated properties:", ", ".join(retention.missing_properties(catalog)))
print("files read:", sum(files for files, _ in report.values()))
print("files holding the learner:", sum(holding for _, holding in report.values()))
```

Output:

```text
ai.review_corpus: 11 files read, 0 holding the learner
analytics.course_performance: 5 files read, 0 holding the learner
analytics.learner_activity: 11 files read, 0 holding the learner
billing.payments: 12 files read, 0 holding the learner
crm.instructors: 8 files read, 0 holding the learner
crm.learners: 11 files read, 0 holding the learner
learning.courses: 8 files read, 0 holding the learner
learning.enrollments: 11 files read, 0 holding the learner
learning.events: 11 files read, 0 holding the learner
learning.reviews: 11 files read, 0 holding the learner
marketing.audience: 8 files read, 0 holding the learner
support.tickets: 8 files read, 0 holding the learner
request: erasure-0001
tables visited: 10
rows deleted: 25
tables rebuilt: analytics.course_performance
tables kept under an exception, columns erased: billing.payments, card_number
snapshots a reader can still time travel to: 0
files no metadata references: 0
tables missing their generated properties: analytics.course_performance
files read: 115
files holding the learner: 0
```

The scan read 115 files under every table's location, and 0 of them hold the learner. No reader can time travel to the learner, since 0 snapshots older than the current ones remain, and 0 files are unreferenced. The lines after the per-table counts are the evidence: the request's ID, 10 tables visited, 25 rows deleted, the table rebuilt, the table an exception keeps and the column erased from it, `billing.payments, card_number`, with the reason in `governance/retention.toml`, and the scan's counts. They name no value of the learner's, so keeping them puts none back into the platform, which [chapter 8](#produce-evidence-as-data) relies on when it writes them to the audit log.

One line is a warning: `analytics.course_performance` lacks its generated properties, because `lib.pipelines.run` dropped the table and created it again without them. That table has no personal columns. The next table a pipeline rebuilds might have them, and the scan would then report its manifests' bounds as a failed erasure, so the check belongs after every pipeline run.

IDs can stay in a manifest too, since the ID columns keep their statistics. An erased ID that was a file's smallest or largest, such as learner 5000's, stays in the deleted entry's bounds, and the scan reports it. One more commit to the table, followed by an expiry and a sweep, removes it, because PyIceberg's next append leaves out a manifest that holds only deleted files ([source](https://github.com/apache/iceberg-python/blob/pyiceberg-0.12.0/pyiceberg/table/update/snapshot.py)).

The scan covers the warehouse only. Exports, backups, the source systems and logs outside it can hold the learner too, and the same traces can be searched for in each of them the platform can read.

**Working rule:** End every erasure with a scan of every file the platform stores, for the person's IDs and identifying values, read with each format's own reader, and keep its result, counts and IDs only, as the evidence. Search for as much of each value as every bound keeps unchanged, which is one character less than the truncation length. Treat any file that still holds the person as a failed erasure, not a warning. Search the stores outside the warehouse that you control, and list in the record the ones you can't search.

## What goes wrong in production {#retention-in-production}

Retention and erasure fail quietly: a delete that succeeds looks the same whether the data is gone or still in storage. The first failure here undoes a finished erasure.

### An erased learner comes back {#erased-learner-comes-back}

Besides the CRM's sync, the warehouse reloads all of `crm.learners` each night from the application's export, and the erasure ran in the warehouse only. Erase learner 3590 everywhere [the plan](#plan-erasure-from-lineage) says, then run the nightly reload and the pipelines that read it:

Example `erased-learner-returns` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · sqlglot 30.30.0), passing in Edition 2026.11.24:

```python
"""An erased learner comes back: the warehouse's copy of the CRM is reloaded each night from the application's
export, which nobody erased, and the pipelines rebuild from it. A check against the erasure register catches it."""
from datetime import timedelta

from lib import pipelines, retention

LEARNER, REQUEST = 3590, "erasure-0001"
catalog, graph = retention.open_platform()
retention.erase_everywhere(catalog, graph, LEARNER, REQUEST, min_age=timedelta(0))
register = [retention.register_entry(REQUEST, LEARNER)]      # the request's ID and a keyed hash of the learner's ID
print("the erasure register's entry:", register[0]["request"], register[0]["learner"])
learners = catalog.load_table("crm.learners")
print("the learner's rows in crm.learners after the erasure:", retention.count(learners, retention.rows_of([LEARNER])))

learners.overwrite(retention.crm_export())          # the nightly reload, from the application's export
for name in ("learner_activity", "marketing_audience"):
    pipelines.run(catalog, name)
for table in ("crm.learners", "analytics.learner_activity", "marketing.audience"):
    print(f"the learner's rows in {table} after the nightly run:",
          retention.count(catalog.load_table(table), retention.rows_of([LEARNER])))

for table, rows in retention.erased_rows(catalog, register).items():
    print(f"the check against the register, rows of erased learners in {table}:", rows)
```

Output:

```text
the erasure register's entry: erasure-0001 c25d8a8b12426596f0c0b1ebfb890246b42ea535791f07256efd16fc6c2cb84b
the learner's rows in crm.learners after the erasure: 0
the learner's rows in crm.learners after the nightly run: 1
the learner's rows in analytics.learner_activity after the nightly run: 1
the learner's rows in marketing.audience after the nightly run: 0
the check against the register, rows of erased learners in analytics.learner_activity: 1
the check against the register, rows of erased learners in crm.learners: 1
```

After the erasure, `crm.learners` holds 0 rows for the learner. After the nightly run it holds 1 again, and `analytics.learner_activity`, rebuilt from it, holds 1. `marketing.audience` stays clear only because the learner's consent comes back withdrawn and their enrollments, which it joins, were erased.

The check that catches this keeps an erasure register: for each request, its ID and a keyed hash (HMAC-SHA256) of the erased learner's ID, and nothing else. The key is the erasure job's secret, kept like the enforcement layer's pseudonymization key in [chapter 6](#write-masks-as-sql) but a different one, because whoever holds it can hash every learner ID and find whom the register names. After every load, restore and rebuild, `lib.retention.erased_rows` hashes each `learner_id` in every table with that column and looks it up, so a restore or a backfill is checked without the register holding anyone's ID. It finds the learner in `analytics.learner_activity` and `crm.learners`, and leaves out `billing.payments`, whose rows the exception keeps. The audit log's record of the erasure, in [chapter 8](#produce-evidence-as-data), holds the same request ID and counts, never the learner, so the register is the only place a request meets a learner, as a hash. We treat a keyed hash of an ID as pseudonymized data, never anonymized, so whether the platform may keep the register, and for how long, is a question for its lawyers.

**Working rule:** Erase in the source system first, or in the same request, and keep a register of keyed hashes of erased IDs that every load filters against and every run checks, with the key held as a secret apart from the data. Treat a row with an erased ID as an incident, as you would a leak.

### Other failures {#other-retention-failures}

- **Old snapshots and files keep "deleted" data.** A retention or erasure job that stops after its delete leaves everything readable by time travel, and in PyIceberg the files stay after expiry too. Run [the expiry](#expire-snapshots) and [the sweep](#remove-unreferenced-files) in the same job, then the scan.
- **Another engine deletes by merge-on-read.** PyIceberg reads the deletion vectors other engines write ([release notes](https://github.com/apache/iceberg-python/releases/tag/pyiceberg-0.12.0)). Rows deleted that way stay in their data files until compaction rewrites them, and a delete file may keep their values: "Both position and equality delete files allow encoding deleted row values with a delete" ([Iceberg table spec](https://iceberg.apache.org/spec/)). Compact the affected files before [the expiry](#expire-snapshots) and [the sweep](#remove-unreferenced-files), and scan the delete files too.
- **Backups keep everything the sweep deletes.** They are one of the weak points [the EDPB's report](#verify-the-erasure) names. Decide with the people who answer for the backups how they're erased or aged out, and record it with each request.
- **A derived table nobody erased.** A job that sends no lineage writes a copy the plan can't see, as [chapter 4's uninstrumented export](#job-nobody-instrumented) does. Run `lib.lineage.unaccounted` before every erasure.
- **A rebuilt table loses its properties.** A pipeline that drops and creates its table loses the generated statistics settings, and the next erasure leaves values in its manifests. Apply the properties after every run, or create tables with them.
- **A renamed column loses its setting.** In PyIceberg, the metrics property stays under the column's old name, so after a rename the new name has none. Generate the properties again on every schema change.
- **Retention counted from the wrong date.** A rule that means "after closing" but counts from opening deletes early, and one that counts from a load date deletes late. Store the date the rule means.

## What this chapter decided {#retention-decisions}

- **Retention rules are config,** applied against a day the job is given, never the clock. Events are kept 365 days, payments 3,650, and closed tickets 730 days from opening, because the table has no `closed_at`: the platform's choices, not legal advice.
- **Consent is an attribute the policy reads** at query time; a withdrawal deletes nothing, and tables built with a consent filter are rebuilt.
- **An erasure is planned from the catalog and the lineage:** every table with a `learner_id` column, then every table lineage reaches.
- **Exceptions to erasure are the legal team's,** recorded in `governance/retention.toml` with their reasons; the code keeps what they say until the table's retention rule ends it.
- **Commits record request IDs and rule names,** never a person's values.
- **The book's expiry reads each table's settings,** which PyIceberg's doesn't, and an erasure checks every table in its plan before it deletes anything.
- **The book's sweep removes unreferenced files,** with a minimum age of 72 hours in production.
- **Manifests keep no values of protected columns:** metrics mode `none`, generated from the classifications.
- **Every erasure ends with a scan** of every file, for IDs and 15 characters of each identifying value; its counts are the evidence.
- **The erasure register keeps a keyed hash of each erased ID,** checked after every load, restore and rebuild; whether to keep it, and how long, is for the lawyers.
