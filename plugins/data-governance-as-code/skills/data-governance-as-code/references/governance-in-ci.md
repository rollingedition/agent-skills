---
title: "Data Governance as Code"
chapter: "Governance in CI"
chapter_id: governance-in-ci
book: data-governance-as-code
edition: 2026.11.28
verified: 2026-11-14
edition_code: GR11-MS4B
canonical: https://rollingedition.com/data-governance-as-code/governance-in-ci
license: CC BY 4.0
attribution: "“Governance in CI,” chapter 10 of Data Governance as Code, Edition 2026.11.28, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/governance-in-ci. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Governance in CI

By the end of this chapter you can run the governance checks of chapters 2 to 7 as one job on each pull request, judging only what the pull request changes. It fails when a column has no classification, runs the tests of the access policy and the enforcement layer, reports what each schema change reaches downstream, and enforces two rules that breaking-change checkers, the tools that compare two versions of a schema for changes that break its readers, don't. You'll keep ownership in contracts of the Open Data Contract Standard (ODCS), generated from the metadata, with a folder and a code owner per domain, layer each domain's rules on global ones, and measure each check's noise by the findings nobody acts on.

Earlier chapters built the governance checks of an online learning platform whose teams change its schemas every week, and no pull request runs any of them. [Chapter 2](#a-catalog-you-can-test) tests the catalog against the reviewed metadata, and [chapter 4](#lineage-from-pipelines) reads lineage from every pipeline run. [Chapter 5](#access-policies-as-code) tests the access policy, and [chapter 6](#enforcing-policies-on-queries) tests the layer that enforces it on queries. [Chapter 7](#retention-consent-erasure) generates table properties from the classifications. Each runs only when someone runs its example, never when a team changes the platform. Three changes are on their way. The CRM team wants a column for learners' work email, the learning team wants to rename a column the reporting pipelines read, and the data-science team wants to see learners' cities without a mask. Each is a small diff a reviewer would approve, and each changes what breaks or who sees what.

This chapter adds the book's shared module for catching them, `lib.ci`, which is the platform's governance job. In this chapter the job is this CI job, not an OpenLineage one. Each simulated pull request runs offline, as two folders called checkouts, one of the main branch and one of the pull request's branch. Each holds `governance/`, the platform's governance files; `pipelines/`, its pipelines' SQL; `migrations/`, the `alter table` statements a branch changes schemas with, which `lib.ci.migrate` applies as Iceberg schema changes; and the files [generated from the metadata](#a-folder-and-a-code-owner-per-domain). For each side, `lib.ci.build` builds a scratch platform the way the platform runs: the source tables, the side's migrations, the deploy, which writes the metadata into the catalog and sets every table's generated properties, then the nightly run of the side's own pipelines, with lineage. Among those pipelines, `review_corpus` stays [chapter 4](#lineage-from-pipelines)'s ungoverned copy, so the job keeps checking its lineage; the platform trains on [chapter 9's governed build](#admit-consented-reviews). `lib.ci.run` runs the checks and compares the two sides. No git or network is involved, and every date is compared with the book's "today", Oct 1, 2026, never the clock.

## Run every check as one job {#run-every-rule-as-one-job}

A check that runs when someone remembers it is a report, and reports go unread. On a pull request, a check is a gate: it runs on every change, before the change merges, and it fails the pull request through its exit code. That is how Open Policy Agent (OPA) advises running policies in CI, with flags, `--fail` and `--fail-defined`, that set the exit code to 1 based on query results ([OPA CI/CD docs](https://www.openpolicyagent.org/docs/cicd)). A job made of several checks needs four things more:

- **Every check runs and reports all its findings,** so one failure doesn't hide the next. A check that crashes becomes one finding, "the check could not run", which fails the job while the other checks run.
- **Every finding has a stable ID,** so the same problem has the same name on every run and can be discussed, counted and waived. `lib.ci` writes it as the check and the subject, such as `coverage/crm.learners.work_email`.
- **The job judges what the pull request changes.** It runs the main branch's checks too, and compares the two. A finding the pull request introduces fails it. A finding already on main is reported on every run, counted and named with the team that owns it, but it fails no pull request that leaves it as it is. We judge that a check that fails every pull request for findings nobody in it caused gets switched off. Google's code-analysis platform, Tricorder, shows most of its analyses' results only on the lines a change touches, by default ([Sadowski et al., 2015](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43322.pdf)).
- **The list of checks lives in a reviewed file,** `governance/ci.toml`, so switching one off is a diff that someone approves.

The platform's job runs these checks, in this order:

| Check | From | Fails when |
| --- | --- | --- |
| `coverage` | Chapters [2](#test-the-catalog-against-the-metadata) and [3](#classify-columns-from-the-schema) | A table has no metadata or owner, or a column no classification or one below its name's suggestion |
| `contract-rules` | [This chapter](#run-global-and-domain-rules) | A contract breaks a global or a domain rule |
| `contracts` | [This chapter](#a-folder-and-a-code-owner-per-domain) | A generated file is out of date |
| `policy-tests` | [Chapter 5](#unit-test-the-policy-in-rego) | A Rego test or a who-sees-what row fails |
| `enforcement-tests` | [Chapter 6](#allow-only-catalog-sources) | A regression case or a who-sees-what query fails |
| `migrations` | [This chapter](#a-broken-file-becomes-a-finding) | Iceberg refuses a migration |
| `pipelines` | [Chapter 4](#fail-on-unreadable-lineage) | A pipeline can't run, or its lineage can't be read |
| `lineage-classifications` | [Chapter 4](#personal-data-tagged-internal) | A column is declared less protected than lineage proposes |
| `owner-review` | [This chapter](#ask-the-owner-before-lowering) | A classification drops, or an owner or domain changes, unapproved |
| `removals` | [This chapter](#deprecate-before-removing) | A column is removed before it was deprecated |
| `properties` | [Chapter 7](#keep-values-out-of-manifests) | A table lacks the properties generated for it |

The first pull request the job sees is the CRM team's. Employers buy team licences for their staff, so the team adds `work_email` to `crm.learners` in one migration, and forgets the column's metadata:

Example `governance-ci-report` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""The platform's governance job on one pull request, run as a CI step runs it: the CRM team adds a work email to
crm.learners. The prose's point rests on the coverage finding for the new column and on the exit code the step returns."""

from lib import ci
from lib.platform import scratch

main = ci.checkout()                      # the main branch: governance files, pipelines and the files generated from them
branch = ci.checkout(main)                # the pull request's branch, starting from main
(branch / "migrations" / "0001-add-work-email.sql").write_text("alter table crm.learners add column work_email varchar;\n")
print("files the pull request changes:", ", ".join(ci.changed(main, branch)))

# What a CI step runs, `python -m lib.ci MAIN BRANCH --summary FILE`: it prints the report and its totals, writes the
# report as Markdown for the pull request, and exits with the code it returns.
summary = scratch() / "summary.md"
code = ci.main([str(main), str(branch), "--summary", str(summary)])     # 1 when a finding this pull request adds fails it
print("the step exits with:", code)
print("the summary it writes for the pull request:")
print(summary.read_text(encoding="utf-8"), end="")
```

Output:

```text
files the pull request changes: migrations/0001-add-work-email.sql
coverage: failed, findings 3, new 1, on main 2, waived 0, 12 tables checked
contract-rules: passed, findings 0, new 0, on main 0, waived 0, 10 contracts checked
contracts: passed, findings 0, new 0, on main 0, waived 0, 11 files checked
policy-tests: passed, findings 0, new 0, on main 0, waived 0, 24 tests and rows checked
enforcement-tests: passed, findings 0, new 0, on main 0, waived 0, 44 cases checked
migrations: passed, findings 0, new 0, on main 0, waived 0, 1 migrations checked
pipelines: passed, findings 0, new 0, on main 0, waived 0, 4 pipelines checked
lineage-classifications: passed, findings 0, new 0, on main 0, waived 0, 23 columns checked
owner-review: passed, findings 0, new 0, on main 0, waived 0, 77 columns checked
removals: passed, findings 0, new 0, on main 0, waived 0, 87 columns checked
properties: passed, findings 4, new 0, on main 4, waived 0, 12 tables checked
coverage/ai.review_corpus: no metadata; on main, owner team-platform
coverage/crm.learners.work_email: not classified; its name suggests personal
coverage/marketing.audience: no metadata; on main, owner team-platform
properties/ai.review_corpus: 7 of 7 generated properties missing; on main, owner team-platform
properties/analytics.course_performance: 4 of 4 generated properties missing; on main, owner team-analytics
properties/analytics.learner_activity: 4 of 4 generated properties missing; on main, owner team-analytics
properties/marketing.audience: 7 of 7 generated properties missing; on main, owner team-platform
change crm.learners, field 16: added as work_email string; named by 0 pipelines, reaches 0 columns
job: failed
checks run: 11
checks failed: 1
findings: 7
findings the pull request introduces: 1
findings already on main: 6
findings waived: 0
findings approved: 0
exit code: 1
the step exits with: 1
the summary it writes for the pull request:
## Governance job: failed

| Check | Result | New | On main | Waived | Checked |
| --- | --- | ---: | ---: | ---: | --- |
| `coverage` | failed | 1 | 2 | 0 | 12 tables |
| `contract-rules` | passed | 0 | 0 | 0 | 10 contracts |
| `contracts` | passed | 0 | 0 | 0 | 11 files |
| `policy-tests` | passed | 0 | 0 | 0 | 24 tests and rows |
| `enforcement-tests` | passed | 0 | 0 | 0 | 44 cases |
| `migrations` | passed | 0 | 0 | 0 | 1 migrations |
| `pipelines` | passed | 0 | 0 | 0 | 4 pipelines |
| `lineage-classifications` | passed | 0 | 0 | 0 | 23 columns |
| `owner-review` | passed | 0 | 0 | 0 | 77 columns |
| `removals` | passed | 0 | 0 | 0 | 87 columns |
| `properties` | passed | 0 | 4 | 0 | 12 tables |

### To fix in this pull request

- `coverage/crm.learners.work_email`: not classified; its name suggests personal

### Already on main, and whose it is

- `coverage/ai.review_corpus`: no metadata (team-platform)
- `coverage/marketing.audience`: no metadata (team-platform)
- `properties/ai.review_corpus`: 7 of 7 generated properties missing (team-platform)
- `properties/analytics.course_performance`: 4 of 4 generated properties missing (team-analytics)
- `properties/analytics.learner_activity`: 4 of 4 generated properties missing (team-analytics)
- `properties/marketing.audience`: 7 of 7 generated properties missing (team-platform)

### Schema changes

- `crm.learners`, field 16: added as work_email string; named by 0 pipelines, reaches 0 columns
```

The pull request introduces 1 finding, and it is the one that fails the job: `crm.learners.work_email` is not classified; its name suggests personal. The suggestion comes from [chapter 3](#classify-columns-from-the-schema)'s name rules, which match `e_?mail`, so the finding says what to add. Of the job's checks, 1 fails, and the step exits with code 1. The coverage findings on main are `marketing.audience` and `ai.review_corpus`, the tables nobody has described since [chapter 2](#a-catalog-you-can-test) found them. Neither table has an owner, so the job names the platform team, which `ci.toml` makes answerable for tables nobody owns. [Chapter 4](#classifications-from-lineage)'s lineage shows that both hold personal data, and every report repeats them until someone describes them.

The other checks pass, among them chapter 5's policy tests, run on the data the branch's files generate, and chapter 6's enforcement tests, run on the branch's tables. The properties check reports findings on main, such as `4 of 4 generated properties missing; on main, owner team-analytics`: the tables pipelines write lose their generated properties on every nightly run, as [chapter 7](#verify-the-erasure) found, on main as on the branch. The schema change, `added as work_email string; named by 0 pipelines, reaches 0 columns`, reaches nothing yet.

**Working rule:** Run every check as one job on every pull request, each reporting all its findings under stable IDs, and a crashed check as a failing finding. Fail the job by exit code on any finding the pull request introduces that is neither waived nor approved. Report every finding already on main, counted and named with its owner, without failing a pull request that leaves it as it is. Keep the list of checks in a reviewed file.

## Gate the pull request, not the commit {#gate-the-pull-request}

[The platform's job](#run-every-rule-as-one-job) runs in CI. A pre-commit hook is the other place a check can run, on the author's machine, before a commit exists. pre-commit, a framework for git hooks, which usually runs them only on the files a commit changes, and its documentation presents hooks as a way to catch simple problems before code review ([pre-commit](https://pre-commit.com/)). That suits checks that need one file: that `metadata.toml` parses, and that every classification is one of the four values.

It doesn't suit the coverage check. The CRM team's pull request changed `migrations/0001-add-work-email.sql` and no metadata file, so a hook filtered to metadata files would have had nothing to check. The gap sits between the catalog, which the migration changed, and a file the pull request never touched, and only a job that builds the whole catalog sees it. A hook can be set to run anyway, with pre-commit's `always_run`, so that it runs even when no file matches. But it runs only where someone installed it, and anyone can skip it, with pre-commit's `SKIP` variable or git's `--no-verify`, and no reviewer can see either.

So the gate is the job on the pull request, made required. GitHub's branch protection can require that every required status check pass before collaborators can merge changes into the protected branch ([GitHub, protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)), and a status that isn't required is only advice. Where the findings appear matters as much. Google's Tricorder authors found that analysis use drops off when developers have to open a dashboard or run a separate command-line tool ([Sadowski et al., 2015](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43322.pdf)). That is one company and code analysis, not data, but it's why `lib.ci.main` does more than return the exit code. A CI step runs it as `python -m lib.ci MAIN BRANCH`, and it prints one line per finding, with its ID and what to add. It also writes the report as Markdown for the pull request, where the reviewer reads the diff. Posting the summary, and reading approvals from the pull request's reviews, are the CI service's part and outside this book's scope.

**Working rule:** Use hooks for fast checks of single files on the author's machine, and make the CI job on the pull request the gate, required by branch protection on the main branch. Put every finding in the pull request itself, with its ID and what to do about it, never only on a dashboard. Run its checks on a schedule against the production catalog too, for the tables that change outside any pull request.

## Report what a schema change reaches {#report-what-a-schema-change-reaches}

The CRM team's added column reached nothing downstream, but a rename does, and its three kinds of readers, Iceberg, SQL and the governance metadata, judge it differently. Iceberg readers find columns by field ID, and the spec says that "projection must be done using field ids" ([Iceberg table spec, 1.12.0](https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/format/spec.md)), so a renamed column still reads every file written before the rename. SQL finds columns by name, so the same rename breaks every query and pipeline that names the column. The platform's governance metadata is keyed by field ID, as [chapter 2](#key-column-metadata-by-field-id) decided, so a rename needs only the name beside the ID updated. The spec's valid primitive type promotions are `int` to `long`, `float` to `double`, and a decimal's precision, which may only widen, plus, in format v3, `date` to `timestamp` or `timestamp_ns`, and a column of type `unknown` to any type. Any other change means a new column.

Which SQL a change breaks is a lineage question, and [chapter 4](#impact-of-a-column-change) answered it by walking the column graph. A review has to follow INDIRECT edges too, [chapter 4](#add-indirect-inputs)'s name for inputs that decide which rows an output holds rather than what its values are. OpenLineage's column lineage facet keeps a `dataset` list for column lineage that affects the whole dataset, through filtering, sorting, grouping, joining, window functions and the like ([ColumnLineageDatasetFacet, 1.54.0](https://github.com/OpenLineage/OpenLineage/blob/1.54.0/spec/facets/ColumnLineageDatasetFacet.json)). A column used only to join or group shapes every row it feeds, which a report of copied values misses. `lib.ci.changes` compares the two sides' schemas field ID by field ID. For every column the branch renames, retypes or removes, it walks the main branch's lineage graph: the pipelines whose SQL names the column, the columns whose values come from it, every column it can change, and the teams that own them.

Next comes the learning team's rename of `learning.courses.category` to `subject`, in a migration and in the metadata file. The same pull request also fixes the two pipelines that name the column:

Example `schema-change-impact` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""What the learning team's rename of learning.courses.category reaches, through Iceberg readers, SQL and lineage. The
prose's point rests on the courses an Iceberg reader still finds, the columns reached, and the job's verdict once the fix merges with the rename."""
import pyarrow.compute as pc

from lib import ci, retention

main = ci.checkout()
branch = ci.checkout(main)
(branch / "migrations" / "0001-rename-category.sql").write_text(
    "alter table learning.courses rename column category to subject;\n")
ci.edit(branch, "governance/metadata.toml", '3 = { name = "category", classification = "public"',
        '3 = { name = "subject", classification = "public"')       # the same field ID, renamed

before, after = ci.build(main), ci.build(branch)
# matched by field ID, so the rename is one change, not a column dropped and another added
change = next(c for c in ci.changes(before, after) if c.table == "learning.courses")
print("change:", change.kind, "from", change.before, "to", change.after)
print("field ID, before and after:", change.field_id)
# read by the new name: Iceberg maps it to the same field ID as before
subjects = after.catalog.load_table("learning.courses").scan(selected_fields=("subject",)).to_arrow()
print("courses whose subject an Iceberg reader finds:", pc.count(subjects["subject"]).as_py())
print("pipelines whose SQL names it:", ", ".join(change.jobs))
for job, why in sorted(after.failed.items()):
    print(f"pipeline {job}, on the branch:", why)
print("columns whose values come from it:", len(change.values))
for column in change.values:
    print("  value of:", column)
print("columns it can change, DIRECT and INDIRECT:", len(change.reached))
# a column's table is the first two parts of its name, schema.table.column
print("tables those columns are in:", ", ".join(sorted({".".join(c.split(".")[:2]) for c in change.reached})))
print("owners the report goes to:", ", ".join(change.owners))
print("tables on main:", len(retention.tables(before.catalog)))
print("tables on the branch:", len(retention.tables(after.catalog)))
coverage = ci.run(before, after, checks=["coverage"]).checks[0]
print("coverage findings on the branch:", ", ".join(finding.id for finding in coverage.findings))

# The same pull request, with both pipelines changed to read the new name. Each side runs its own pipelines/.
ci.edit(branch, "pipelines/course_performance.sql", "    c.category,", "    c.subject as category,")
ci.edit(branch, "pipelines/course_performance.sql", "c.title, c.category", "c.title, c.subject")
sql = (branch / "pipelines" / "marketing_audience.sql").read_text(encoding="utf-8")
(branch / "pipelines" / "marketing_audience.sql").write_text(sql.replace("c.category", "c.subject").replace(
    "f.category", "f.subject"), encoding="utf-8")
fixed = ci.build(branch)
ci.generate(fixed)                        # and the contracts generated again, as the author's hook would
print("files the fixed pull request changes:", ", ".join(ci.changed(main, branch)))
for line in ci.lines(ci.run(before, fixed, checks=["pipelines", "coverage", "contracts", "lineage-classifications"])):
    print("with the fix,", line)
```

Output:

```text
change: renamed from category string to subject string
field ID, before and after: 3
courses whose subject an Iceberg reader finds: 200
pipelines whose SQL names it: course_performance, marketing_audience
pipeline course_performance, on the branch: Unknown column: category
pipeline marketing_audience, on the branch: Unknown column: category
columns whose values come from it: 2
  value of: analytics.course_performance.category
  value of: marketing.audience.favourite_category
columns it can change, DIRECT and INDIRECT: 12
tables those columns are in: analytics.course_performance, marketing.audience
owners the report goes to: no owner, team-analytics
tables on main: 12
tables on the branch: 10
coverage findings on the branch: coverage/ai.review_corpus
files the fixed pull request changes: governance/contracts/learning/courses.odcs.yaml, governance/metadata.toml, migrations/0001-rename-category.sql, pipelines/course_performance.sql, pipelines/marketing_audience.sql
with the fix, pipelines: passed, findings 0, new 0, on main 0, waived 0, 4 pipelines checked
with the fix, coverage: passed, findings 2, new 0, on main 2, waived 0, 12 tables checked
with the fix, contracts: passed, findings 0, new 0, on main 0, waived 0, 11 files checked
with the fix, lineage-classifications: passed, findings 0, new 0, on main 0, waived 0, 23 columns checked
with the fix, coverage/ai.review_corpus: no metadata; on main, owner team-platform
with the fix, coverage/marketing.audience: no metadata; on main, owner team-platform
with the fix, change learning.courses, field 3: renamed from category string to subject string; named by 2 pipelines, reaches 12 columns
with the fix, job: passed
```

For Iceberg, nothing broke. The rename kept the column's field ID, so an Iceberg reader on the branch still finds a subject for 200 courses. For SQL, the pipelines that name the column, course_performance, marketing_audience, each stop before writing anything on the branch, because [chapter 4](#fail-on-unreadable-lineage) made unreadable lineage an error. Through values, the rename reaches 2 columns, the two copies of the category. Through every edge it reaches 12 columns, every column of `analytics.course_performance, marketing.audience`, because categories group the course report and rank each learner's favourite. The report goes to no owner, team-analytics: the analytics team, and nobody for `marketing.audience`, which has no owner yet.

A broken build hides what it breaks. The branch's catalog holds 10 tables, against 12 on main, because the broken pipelines wrote nothing. Coverage reports only `coverage/ai.review_corpus`: a table that doesn't exist can't be found undescribed, so `marketing.audience`'s finding is gone. Each side runs its own `pipelines/`, so the fix travels with the rename: with both pipelines reading `subject`, the job reports `passed`. In production, the merge can also guard what the review saw. A REST catalog commit can carry `AssertCurrentSchemaId`, which requires the table's current schema ID to match the one the requirement names ([REST catalog spec, 1.12.0](https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/open-api/rest-catalog-open-api.yaml)), so a migration reviewed against one schema fails instead of applying to another.

**Working rule:** Diff schemas by field ID, never by name or schema ID, and report every rename, type change and removal three ways: whether Iceberg readers are affected, which pipelines' SQL names the column, and what it reaches through lineage, INDIRECT edges included. Send the report to the owners of every table it reaches. Merge a rename that breaks a pipeline in the same pull request as the pipeline's fix, never before it.

## Ask the owner before lowering a classification {#ask-the-owner-before-lowering}

Breaking-change checkers protect the readers of a schema. dbt's model contracts flag removing a column, or changing its data type, as breaking changes that could affect downstream consumers ([dbt model contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts)). datacontract-cli's `breaking` command compares two ODCS contracts and fails a change that breaks a guarantee consumers rely on ([datacontract-cli 1.2.7](https://github.com/datacontract/datacontract-cli/blob/v1.2.7/README.md)). Neither treats protection as a guarantee. In datacontract-cli 1.2.7, no rule covers a property's classification or a team member's role, so a change to either falls to a rule that marks it untested ([rules.py](https://github.com/datacontract/datacontract-cli/blob/v1.2.7/datacontract/breaking/rules.py)). The detector reports such a change at INFO ([detector.py](https://github.com/datacontract/datacontract-cli/blob/v1.2.7/datacontract/breaking/detector.py)), a level that doesn't fail. The command exits 1 only for ERROR entries ([command_breaking.py](https://github.com/datacontract/datacontract-cli/blob/v1.2.7/datacontract/command_breaking.py), [model/breaking.py](https://github.com/datacontract/datacontract-cli/blob/v1.2.7/datacontract/model/breaking.py)). `examples/requirements.txt` doesn't pin it, so no example runs it. On Oct 22, 2026, datacontract-cli 1.2.7, run on the contracts this chapter generates for `crm.learners`, failed a renamed `email` with exit code 1. It read the rename as a removal, although the property kept its `id`, because it matches properties by name ([normalize.py](https://github.com/datacontract/datacontract-cli/blob/v1.2.7/datacontract/changelog/normalize.py)). It passed `email` reclassified from `personal` to `public`, and a change of owner, with exit code 0. ODCS itself says a classification "Can be anything" ([ODCS v3.2.0 schema](https://github.com/bitol-io/open-data-contract-standard/blob/v3.2.0/docs/schema.md)).

Yet every policy reads the classification, so lowering one is among the most consequential changes a metadata file can carry. We add a first rule of our own: lowering a column's classification, changing a table's owner, or moving a table to another domain needs the approval of the team that owns the table on the main branch. A move counts as an ownership change, because a domain's own rules apply to its tables ([a later section](#run-global-and-domain-rules)). The owner comes from the main branch, because otherwise a pull request could hand a table to a new owner, and the new owner could approve the downgrade. [Chapter 2](#measure-where-the-drafts-are-wrong) set the same rule for a model's drafts: only a reviewer lowers a classification, with the reason in the column's description.

The data-science team's pull request comes last. It lowers `crm.learners.city` from `personal` to `internal`, so data scientists can group learners by city. The access policy pseudonymizes personal columns for data scientists, and the downgrade takes `city` out of that rule. The run asks the policy before and after, then runs the checks that look at schemas and policies, and the owner rule:

Example `classification-downgrade` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""A pull request from the data-science team lowers crm.learners.city from personal to internal. The prose's point rests
on analyst-1's mask on each side, and on the owner rule failing alone."""
from lib import ci, policy

main = ci.checkout()
branch = ci.checkout(main)
ci.edit(branch, "governance/metadata.toml", '6 = { name = "city", classification = "personal"',
        '6 = { name = "city", classification = "internal"')
before, after = ci.build(main), ci.build(branch)

reading_city = policy.request("analyst-1", "crm.learners", ["learner_id", "city"])
for side, name in ((before, "main"), (after, "the branch")):
    rego = policy.interpreter(side.governance / "policies", data=ci.policy_data(side))
    # a column with no mask in the decision is shown as it is stored
    print(f"analyst-1 reading city, on {name}:", policy.decide(reading_city, rego)["column_masks"].get("city", "unmasked"))

checks = ["policy-tests", "enforcement-tests", "removals", "owner-review"]
report = ci.run(before, after, checks=checks)
print("schema changes:", len(report.changes))
for line in ci.lines(report):
    print(line)

# The approvals come from the pull request's reviews: one entry per approving review, named by the reviewer's team.
# The owner rule passes when it raises no unapproved finding.
owner_review = lambda approvals: "passed" if ci.run(before, after, approvals, checks=["owner-review"]).passed else "failed"
print("owner-review, once team-crm approves:", owner_review(["team-crm"]))
print("owner-review, once team-analytics approves:", owner_review(["team-analytics"]))
ci.edit(after.root, "governance/ci.toml", "teams = {}", "teams = { team-crm = 2 }")     # team-crm asks for two
# one approval from team-crm and one from another team: team-crm still needs a second of its own
print("owner-review, two required, one from team-crm:", owner_review(["team-crm", "team-platform"]))
print("owner-review, two required, two from team-crm:", owner_review(["team-crm", "team-crm"]))
```

Output:

```text
analyst-1 reading city, on main: pseudonymize
analyst-1 reading city, on the branch: unmasked
schema changes: 0
policy-tests: passed, findings 0, new 0, on main 0, waived 0, 24 tests and rows checked
enforcement-tests: passed, findings 0, new 0, on main 0, waived 0, 44 cases checked
removals: passed, findings 0, new 0, on main 0, waived 0, 87 columns checked
owner-review: failed, findings 1, new 1, on main 0, waived 0, 77 columns checked
owner-review/crm.learners.city: lowered from personal to internal; needs team-crm's approval
job: failed
owner-review, once team-crm approves: passed
owner-review, once team-analytics approves: failed
owner-review, two required, one from team-crm: failed
owner-review, two required, two from team-crm: passed
```

One word in the metadata file unmasks a column for a whole role, and no check but the owner rule notices. `analyst-1` reads `city` as `pseudonymize` on main, and as `unmasked` on the branch. The job reports 0 schema changes, so a breaking-change checker has nothing to compare. The policy tests pass, `passed, findings 0, new 0, on main 0, waived 0, 24 tests and rows checked`, and so do the enforcement tests, because none of them reads `city`, and the removals check passes because no column was removed. Only the owner rule fails, on `lowered from personal to internal; needs team-crm's approval`.

What settles the owner rule is the owner's approval. Approvals reach `lib.ci.run` as one entry per approving review, named by the reviewer's team. With `team-crm`'s approval, the owner rule reports `passed`, and with `team-analytics`', which doesn't own the table, `failed`.

**Working rule:** Treat a lowered classification, a changed owner and a move to another domain as changes that need the approval of the table's owner on the main branch, and fail the job until it's given; never rely on a breaking-change checker for them. Ask for the reason in the column's description in the same pull request. A raised classification needs no such approval, because it can only hide more.

## Deprecate a column before removing it {#deprecate-before-removing}

[The owner rule](#ask-the-owner-before-lowering) guards a change that breaking-change checkers ignore. Removing a column is the change they all catch, but by then the removal is already under review, too late to help the readers it breaks. ODCS 3.2.0 adds a way to warn readers first. Any element of a contract, a schema object or a property, nested ones included, may set the optional `deprecated` boolean to signal that it is no longer recommended for use. The standard also asks that the `description` point to a replacement and give migration guidance ([ODCS v3.2.0 schema](https://github.com/bitol-io/open-data-contract-standard/blob/v3.2.0/docs/schema.md)). Our second rule makes that warning a required step: a column may leave a table only once the main branch has marked it deprecated. That takes two pull requests, one that deprecates the column and one that removes it, and the column's readers have the time between them to move off it.

The platform's metadata file had no such field, so this chapter adds one: `deprecated = true` in a column's entry. `lib.metadata.load` reads it as `Column.deprecated`, false when it's absent, and `lib.ci.contract` writes it into the column's contract as ODCS's `deprecated`.

The platform's best candidate is `billing.payments.card_number`. Its own description says it "Should not be stored at all", and [chapter 3](#classify-columns-from-their-values) found that it holds full card numbers. `team-billing` removes it twice, each time by dropping the column in a migration and deleting its metadata entry: once straight away, and once after a pull request that deprecates it has merged:

Example `deprecate-then-remove` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""team-billing removes the legacy card_number column from billing.payments: once straight away, and once after a pull
request that deprecates it has merged. The prose's point rests on the two removal lines."""
import yaml

from lib import ci

entry = ('8 = { name = "card_number", classification = "sensitive", '
         'description = "The full card number, from a legacy export. Should not be stored at all." }\n')
# the note goes after the description's sentence ending "at all.", and deprecated = true goes inside the entry's braces
deprecated_entry = entry.replace("all.", "all. Deprecated: reconcile payments by payment_id.").replace(" }", ", deprecated = true }")


def remove_card_number(base, line):
    """A pull request on top of `base` that drops the column and deletes its metadata entry."""
    branch = ci.checkout(base)
    (branch / "migrations" / "0001-drop-card-number.sql").write_text("alter table billing.payments drop column card_number;\n")
    ci.edit(branch, "governance/metadata.toml", line, "")
    return branch


main = ci.checkout()
deprecated = ci.checkout(main)            # the first pull request: mark the column deprecated, and say what replaces it
ci.edit(deprecated, "governance/metadata.toml", entry, deprecated_entry)

for base, line, name in ((main, entry, "straight away"), (deprecated, deprecated_entry, "after the deprecation merged")):
    report = ci.run(ci.build(base), ci.build(remove_card_number(base, line)), checks=["removals"])
    print(f"removal, {name}:", "passed" if report.checks[0].passed else "failed")
    for finding in report.checks[0].findings:
        print(f"  {finding.id}:", finding.message)

# property 7 is the eighth column, field 8: card_number, the column the deprecation marks
card_number = ci.contract(ci.build(deprecated), "billing.payments")["schema"][0]["properties"][7]
print("the deprecated column in its ODCS contract:")
print(yaml.safe_dump(card_number, sort_keys=False, width=200), end="")
```

Output:

```text
removal, straight away: failed
  removals/billing.payments.card_number: removed without being deprecated on the main branch first
removal, after the deprecation merged: passed
the deprecated column in its ODCS contract:
id: field-8
name: card_number
logicalType: string
physicalType: string
required: false
description: 'The full card number, from a legacy export. Should not be stored at all. Deprecated: reconcile payments by payment_id.'
classification: sensitive
deprecated: true
```

Straight away, the removal fails, `removed without being deprecated on the main branch first`. After the deprecation has merged, the same removal reports `passed`. In between, the contract carried the warning to everyone who reads contracts, not only to the repository: `deprecated: true`, with a description that says how to reconcile payments without the column. The rule checks the order of the two changes, not the time between them. How long readers get is a decision for the owning team and the column's readers, and [the impact report](#report-what-a-schema-change-reaches) says who those readers are.

**Working rule:** Remove a column in two pull requests: first mark it deprecated, with its replacement in the description, and merge that; then drop it from the table and its entry from the metadata. Fail any removal of a column the main branch hadn't deprecated. Agree with the column's readers how long the deprecation lasts, since the job checks only that it came first.

## Route each domain's reviews by path {#a-folder-and-a-code-owner-per-domain}

The [owner rule](#ask-the-owner-before-lowering) asks a table's team to approve its downgrades, and the repository can route that request. GitHub requests code owners' review automatically when a pull request modifies code they own, and a branch protection rule can require that review ([GitHub's documentation, About code owners](https://github.com/github/docs/blob/d59b2631959db46d71ca5f7748ec04311c6d0870/content/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners.md)). The platform keeps all its metadata in one file, `governance/metadata.toml`, which suits 5 teams in one repository. A file has one set of owners, though, so the request can reach the right team only if each team's metadata lives under a path of its own.

ODCS draws the same lines. A contract names one `domain`, the logical data domain it belongs to ([ODCS v3.2.0 fundamentals](https://github.com/bitol-io/open-data-contract-standard/blob/v3.2.0/docs/fundamentals.md)). ODCS has no owner field: ownership is a free-form `role` on a member of the contract's `team` ([ODCS v3.2.0 team](https://github.com/bitol-io/open-data-contract-standard/blob/v3.2.0/docs/team.md)). `lib.ci.contract` writes each described table as an ODCS contract. It records the domain, the owning team as a member with the role `owner`, and each column as a property whose `id` holds its Iceberg field ID. ODCS defines that `id` as "A unique identifier for the element used to create stable, refactor-safe references". `lib.ci.generate` writes each contract into a folder for its domain, and a CODEOWNERS file in `.github/`, the first place GitHub looks for one. Both are generated from the metadata, never typed. Ask whom GitHub would request for [the data-science team's downgrade of `city`](#ask-the-owner-before-lowering):

Example `domain-contracts` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""Ownership as ODCS contracts, a folder per domain, and who GitHub asks to review the downgrade of crm.learners.city
when the metadata is one shared file, and when each domain has a folder of contracts generated from it. The prose's
point rests on the first review line and on the contracts check failing before the files are generated again."""
import yaml

from lib import ci

main = ci.checkout()                      # the main branch holds the contracts and CODEOWNERS generated from its metadata
branch = ci.checkout(main)
ci.edit(branch, "governance/metadata.toml", '6 = { name = "city", classification = "personal"',
        '6 = { name = "city", classification = "internal"')

shared = ["/governance/ @example-org/team-platform"]          # one file for every domain, owned by the platform team
for path, owners in ci.reviewers(shared, ["governance/metadata.toml"]).items():
    print(f"one shared file, review of {path}:", " ".join(owners))

crm = yaml.safe_load((main / "governance/contracts/crm/learners.odcs.yaml").read_text(encoding="utf-8"))
print(yaml.safe_dump({"domain": crm["domain"], "team": crm["team"]}, sort_keys=False), end="")
lines = (main / ".github/CODEOWNERS").read_text(encoding="utf-8").splitlines()
for line in lines[1:]:                                       # the first line says the file is generated
    print("CODEOWNERS", line)
before, after = ci.build(main), ci.build(branch)          # the pull request changes the metadata only
print("teams that own tables:", len({table.owner for table in before.described.values()}))
# drops the job's verdict, the last line, which this example doesn't print
for line in ci.lines(ci.run(before, after, checks=["contracts"]))[:-1]:
    print("before generating again,", line)
print("files generated again:", len(ci.generate(after)))
print("after generating again, contracts:", "passed" if ci.run(before, after, checks=["contracts"]).passed else "failed")
# the last matching CODEOWNERS line wins, as GitHub applies it
for path, owners in ci.reviewers(lines, ci.changed(main, branch)).items():
    print(f"a folder per domain, review of {path}:", " ".join(owners))
```

Output:

```text
one shared file, review of governance/metadata.toml: @example-org/team-platform
domain: crm
team:
  name: team-crm
  members:
  - username: team-crm
    role: owner
CODEOWNERS /.github/CODEOWNERS @example-org/team-platform
CODEOWNERS /governance/ @example-org/team-platform
CODEOWNERS /migrations/ @example-org/team-platform
CODEOWNERS /pipelines/ @example-org/team-platform
CODEOWNERS /pipelines/course_performance.sql @example-org/team-analytics
CODEOWNERS /pipelines/learner_activity.sql @example-org/team-analytics
CODEOWNERS /governance/contracts/analytics/ @example-org/team-analytics
CODEOWNERS /governance/contracts/billing/ @example-org/team-billing
CODEOWNERS /governance/contracts/crm/ @example-org/team-crm
CODEOWNERS /governance/ci/domains/crm.rego @example-org/team-crm
CODEOWNERS /governance/contracts/learning/ @example-org/team-learning
CODEOWNERS /governance/contracts/support/ @example-org/team-support
teams that own tables: 5
before generating again, contracts: failed, findings 1, new 1, on main 0, waived 0, 11 files checked
before generating again, contracts/governance/contracts/crm/learners.odcs.yaml: differs from what the metadata generates: generate it again
files generated again: 11
after generating again, contracts: passed
a folder per domain, review of governance/contracts/crm/learners.odcs.yaml: @example-org/team-crm
a folder per domain, review of governance/metadata.toml: @example-org/team-platform
```

With one shared file, the downgrade changes `governance/metadata.toml`, and GitHub asks `@example-org/team-platform` to review it. That is the team that owns the file, not `team-crm`, whose column it is. The generated CODEOWNERS gives the platform team the file itself, because About code owners says a repository is fully protected against unauthorized changes only when the CODEOWNERS file itself has an owner ([GitHub's documentation](https://github.com/github/docs/blob/d59b2631959db46d71ca5f7748ec04311c6d0870/content/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners.md)). The platform team also gets the governance files, the migrations and the pipelines. Each pipeline then goes to the team that owns its table, and each folder of contracts goes to its domain's team. The pull request changed only the metadata, so the `contracts` check, which generates every file again and compares, fails: `differs from what the metadata generates: generate it again`. Generated again, the pull request also changes the crm contract, and its review goes to `@example-org/team-crm`, because GitHub gives the last matching pattern precedence. A hook that generates the files saves the author a failed run. The check makes the routing certain.

When code-owner review is required, an approval from any one of a file's owners meets it ([About code owners](https://github.com/github/docs/blob/d59b2631959db46d71ca5f7748ec04311c6d0870/content/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners.md)). Branch protection asks for one number of approvals for the whole branch, met by reviewers with write permissions ([GitHub, protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)), so any such reviewer counts toward it, and it can't ask for two of `team-crm`'s members. The job can, from the approvals it's given. The owner rule counts them per team, against a number per team in `ci.toml`. With `team-crm` asking for two, [the downgrade of `city`](#ask-the-owner-before-lowering) with one `team-crm` approval reports `failed`, and with two it reports `passed`. Iceberg 1.12.0's REST catalog spec offers another place for classifications, `labels` per table and field ID ([REST catalog spec](https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/open-api/rest-catalog-open-api.yaml)). Coverage and the contract rules could read a catalog server's labels, but changes to them would need the server's own review, since the spec doesn't require that labels be persisted or versioned.

**Working rule:** Keep each domain's metadata under a path of its own, as one ODCS contract per table with one domain and one owning team, generated from the metadata and checked by the job, with a CODEOWNERS line for that team. Give the platform team the CODEOWNERS file, the job's settings, its global rules, the waivers and the migrations. Require code-owner review, and count approvals per team in the job when one isn't enough.

## Layer domain rules on the global rules {#run-global-and-domain-rules}

Teams that own [their domains' contracts](#a-folder-and-a-code-owner-per-domain) still share one platform, and some rules have to hold in every domain. Dehghani's description of data mesh calls this federated computational governance, "a set of global rules - rules applied to all data products and their interfaces - to ensure a healthy and interoperable ecosystem". Those global rules sit beside the decisions each domain makes for itself, and the platform executes both ([Dehghani, 2020](https://martinfowler.com/articles/data-mesh-principles.html)). That's a framing, not a measurement, and it maps onto code. The platform team keeps one package of global rules, which the domains agree on, and in Dehghani's version the domain and platform product owners together decide them. Each domain has a package of its own, owned by its team, and one job runs them all.

The OPA project's tool for rules over files is Conftest, which tests structured configuration data with Rego ([Conftest](https://www.conftest.dev/)). `lib.ci` runs the same kind of rules in-process with regopy, as [chapter 5](#access-policies-as-code) runs the access policy. `governance/ci/global.rego` holds the global rules: one owner, whatever the case of its role; one domain, which a missing, empty or blank value fails, since an empty string is a defined value in Rego and `not` alone would pass it; a classification from the four, since ODCS accepts any string; and a description for every column. `governance/ci/domains/crm.rego` holds `team-crm`'s rule: nothing in crm is public, because everything in it describes a learner or an instructor. The `contract-rules` check runs the global package on every contract, and each domain's package on the contracts of that domain on the branch. A rule returns each violation as data, with the rule's name, a subject and a message. The subject and the rule make the finding's ID. These files sit outside `governance/policies/`, the access policy's folder, so changing them never changes the policy revision that [chapter 8](#replay-old-decisions) records with every decision.

[The CRM team's change](#run-every-rule-as-one-job) comes back, this time with metadata. `work_email` is classified `public`, on the argument that a work address is business information, and its description is empty. The second try adds a description and moves `crm.learners` to the analytics domain, which has no rules of its own:

Example `global-and-domain-rules` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""The platform's global rules and the crm domain's own rule, run on the CRM team's two tries at work_email: classified
public with no description, then described with crm.learners moved to the analytics domain, which has no rules of its own.
The prose's point rests on the two contract-rules findings of the first try and on the owner-review finding after the move."""
from lib import ci

main = ci.checkout()
branch = ci.checkout(main)
(branch / "migrations" / "0001-add-work-email.sql").write_text("alter table crm.learners add column work_email varchar;\n")
ci.edit(branch, "governance/metadata.toml", '15 = { name = "notes"',
        '16 = { name = "work_email", classification = "public", description = "" }\n15 = { name = "notes"')

for path in sorted((branch / "governance" / "ci").rglob("*.rego")):
    print("rules:", path.relative_to(branch).as_posix())
before = ci.build(main)
report = ci.run(before, branch, checks=["coverage", "contract-rules"])
for line in ci.lines(report):
    print(line)

# The second try: a description, and the table moved to a domain whose rules allow public columns.
ci.edit(branch, "governance/metadata.toml", 'description = "" }', 'description = "The learner\'s work address." }')
# the table's domain changes from crm to analytics, which has no rules of its own
ci.edit(branch, "governance/metadata.toml", 'owner = "team-crm"\ndomain = "crm"\ndescription = "Every learner',
        'owner = "team-crm"\ndomain = "analytics"\ndescription = "Every learner')
report = ci.run(before, branch, checks=["coverage", "contract-rules", "owner-review"])
for line in ci.lines(report):
    print("moved to analytics,", line)
```

Output:

```text
rules: governance/ci/domains/crm.rego
rules: governance/ci/global.rego
coverage: failed, findings 3, new 1, on main 2, waived 0, 12 tables checked
contract-rules: failed, findings 2, new 2, on main 0, waived 0, 10 contracts checked
coverage/ai.review_corpus: no metadata; on main, owner team-platform
coverage/crm.learners.work_email: classified public; its name suggests personal; needs team-crm's approval
coverage/marketing.audience: no metadata; on main, owner team-platform
contract-rules/crm.learners.work_email/described: no description (global rule described)
contract-rules/crm.learners.work_email/no-public: crm classifies no column public (domains.crm rule no-public)
change crm.learners, field 16: added as work_email string; named by 0 pipelines, reaches 0 columns
job: failed
moved to analytics, coverage: failed, findings 3, new 1, on main 2, waived 0, 12 tables checked
moved to analytics, contract-rules: passed, findings 0, new 0, on main 0, waived 0, 10 contracts checked
moved to analytics, owner-review: failed, findings 1, new 1, on main 0, waived 0, 77 columns checked
moved to analytics, coverage/ai.review_corpus: no metadata; on main, owner team-platform
moved to analytics, coverage/crm.learners.work_email: classified public; its name suggests personal; needs team-crm's approval
moved to analytics, coverage/marketing.audience: no metadata; on main, owner team-platform
moved to analytics, owner-review/crm.learners/domain: domain changed from crm to analytics; needs team-crm's approval
moved to analytics, change crm.learners, field 16: added as work_email string; named by 0 pipelines, reaches 0 columns
moved to analytics, job: failed
```

Coverage flags the classification now: `classified public; its name suggests personal; needs team-crm's approval`. A name is evidence, and a pull request has no values to read, so a classification below the name's suggestion is a finding only the owner on main can answer.

The contract rules ask more. The global package flags `no description (global rule described)`, and the crm package flags `crm classifies no column public (domains.crm rule no-public)`. `team-crm` decided the second rule without asking any other team, and the platform runs it for them on every pull request, including pull requests from `team-crm`.

On the second try, the analytics domain's rules apply, and the contract rules pass: `passed, findings 0, new 0, on main 0, waived 0, 10 contracts checked`. The move itself fails, on `domain changed from crm to analytics; needs team-crm's approval`, and so does the classification.

**Working rule:** Write the rules every domain must follow as one global package, kept by the platform team, and let each domain add a package of its own, owned by its team, that runs on that domain's contracts only. Return violations as data with a stable subject, never as a bare pass or fail. Let domain rules add to the global rules, never replace them, and treat a table's move to another domain as an ownership change, so no team escapes its domain's rules by changing one word.

## Count waived findings per check {#count-waived-findings}

[The checks so far](#run-every-rule-as-one-job) each fail a pull request for a reason. A gate also fails when people stop believing it. Google's Tricorder authors define an effective false positive as any report that a user chooses not to act on, and they keep that rate under 10% at code review. What they act on is narrower, the not-useful rate: an analyzer's Not useful clicks as a share of its Not useful, Please fix and Apply fix clicks. At 10% or more, an analyzer goes on probation, and above 25%, it may be turned off at once ([Sadowski et al., 2015](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43322.pdf)). That is one company's code analysis, with thresholds of its own choosing, and we know of no published equivalent for data governance. The measure carries over as an analogy. Count, for each check, the findings nobody acts on, waived or left on main.

On the platform, the decision not to act on a new finding is a waiver. A waiver in `governance/waivers.toml` names one finding by its ID, the team answerable for it, a reason, and the last day it applies. `lib.ci` accepts a waiver that runs at most 90 days past the day the job runs. That limit is a rule of thumb kept in `governance/ci.toml`, so every waiver comes back for a decision. The same file lists the checks no waiver silences, whatever its date: coverage, since a table with no owner or a column with no classification is fixed in the pull request, and the enforcement tests. A finding already on main needs no waiver. An expired waiver silences nothing, and the report lists it. The platform team owns the waivers file, so each waiver is a reviewed change too.

The CRM change needs two waivers. The first covers the unclassified column. The second covers, once the column is classified `personal`, the description it hasn't written yet. The team first asks for the second to run until the summer, then until Oct 31:

Example `waived-findings` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""Waivers on the CRM team's pull request: one for the unclassified work_email column, which coverage never allows;
then, with the column classified but not yet described, one that asks for too long, and one that fits, on the book's
today and a month later. The prose's point rests on the two refusals and on the expired waiver the report lists."""
from datetime import date

from lib import ci
from lib.platform import TODAY


def waive(branch, finding, expires, reason):
    with open(branch / "governance" / "waivers.toml", "a", encoding="utf-8") as waivers:
        # the date is written unquoted, so TOML reads it as a date, which the job compares with the day it runs
        waivers.write(f'\n[[waivers]]\nfinding = "{finding}"\nowner = "team-crm"\nreason = "{reason}"\nexpires = {expires}\n')


main = ci.checkout()
before = ci.build(main)
unclassified = ci.checkout(main)
(unclassified / "migrations" / "0001-add-work-email.sql").write_text("alter table crm.learners add column work_email varchar;\n")
waive(unclassified, "coverage/crm.learners.work_email", "2026-10-31", "Classified once the sign-up form is live.")
for line in ci.lines(ci.run(before, unclassified, checks=["coverage"])):
    print("unclassified,", line)

undescribed = ci.checkout(main)          # the second try: classified, with its description still to come
(undescribed / "migrations" / "0001-add-work-email.sql").write_text("alter table crm.learners add column work_email varchar;\n")
ci.edit(undescribed, "governance/metadata.toml", '15 = { name = "notes"',
        '16 = { name = "work_email", classification = "personal", description = "" }\n15 = { name = "notes"')
waive(undescribed, "contract-rules/crm.learners.work_email/described", "2027-06-30", "Described once the form's copy is final.")
after = ci.build(undescribed)
for line in ci.lines(ci.run(before, after, checks=["coverage", "contract-rules"])):
    print("undescribed, asked until 2027-06-30,", line)

# the same waiver, shortened to the end of October, within the longest a waiver may run
ci.edit(undescribed, "governance/waivers.toml", "2027-06-30", "2026-10-31")
for day in (TODAY, date(2026, 11, 1)):    # the book's today, then a month later, after the waiver has expired
    report = ci.run(before, after, today=day, checks=["coverage", "contract-rules"])
    print(f"undescribed, asked until 2026-10-31, on {day}, contract-rules:", "passed" if report.checks[1].passed else "failed")
    print(f"undescribed, asked until 2026-10-31, on {day}, findings waived:", sum(len(c.waived) for c in report.checks))
    print(f"undescribed, asked until 2026-10-31, on {day}, waivers that silence nothing:",
          "; ".join(why for _, why in report.unused) or "none")
```

Output:

```text
unclassified, coverage: failed, findings 3, new 1, on main 2, waived 0, 12 tables checked
unclassified, coverage/ai.review_corpus: no metadata; on main, owner team-platform
unclassified, coverage/crm.learners.work_email: not classified; its name suggests personal
unclassified, coverage/marketing.audience: no metadata; on main, owner team-platform
unclassified, change crm.learners, field 16: added as work_email string; named by 0 pipelines, reaches 0 columns
unclassified, waiver coverage/crm.learners.work_email: silences nothing, coverage findings are never waived
unclassified, job: failed
undescribed, asked until 2027-06-30, coverage: passed, findings 2, new 0, on main 2, waived 0, 12 tables checked
undescribed, asked until 2027-06-30, contract-rules: failed, findings 1, new 1, on main 0, waived 0, 10 contracts checked
undescribed, asked until 2027-06-30, coverage/ai.review_corpus: no metadata; on main, owner team-platform
undescribed, asked until 2027-06-30, coverage/marketing.audience: no metadata; on main, owner team-platform
undescribed, asked until 2027-06-30, contract-rules/crm.learners.work_email/described: no description (global rule described)
undescribed, asked until 2027-06-30, change crm.learners, field 16: added as work_email string; named by 0 pipelines, reaches 0 columns
undescribed, asked until 2027-06-30, waiver contract-rules/crm.learners.work_email/described: silences nothing, runs to 2027-06-30, past the longest allowed, 2026-12-30
undescribed, asked until 2027-06-30, job: failed
undescribed, asked until 2026-10-31, on 2026-10-01, contract-rules: passed
undescribed, asked until 2026-10-31, on 2026-10-01, findings waived: 1
undescribed, asked until 2026-10-31, on 2026-10-01, waivers that silence nothing: none
undescribed, asked until 2026-10-31, on 2026-11-01, contract-rules: failed
undescribed, asked until 2026-10-31, on 2026-11-01, findings waived: 0
undescribed, asked until 2026-10-31, on 2026-11-01, waivers that silence nothing: expired on 2026-10-31
```

The waiver for the unclassified column is refused, although it asks for only one month: `silences nothing, coverage findings are never waived`. No waiver can make that pull request pass. The waiver for the description is refused while it runs to the summer, `silences nothing, runs to 2027-06-30, past the longest allowed, 2026-12-30`. Shortened to Oct 31, it silences the finding. On Oct 1 the contract rules report `passed`. On Nov 1 they report `failed`. On Oct 1 the list of waivers that silence nothing is `none`; on Nov 1 it is `expired on 2026-10-31`: the date passed, and the problem didn't.

**Working rule:** Let a waiver name exactly one finding a pull request introduces, with an owning team, a reason and an end date at most a few months away, and list the checks no waiver may silence, such as a missing classification or owner. Report, for each check, how many findings nobody acted on, waived or left on main, and review any check where that's most of them: either the check is wrong or the platform is, and the count hides which.

## What goes wrong in production {#ci-in-production}

On our judgment, a governance job is switched off more often than it breaks: teams remove the checks that are slow or noisy, one line of `governance/ci.toml` at a time, and the gate goes on passing while it guards less. Two staged checks show how, with counts in place of timings, and a third shows a job that breaks.

### A check that reads every row {#a-check-that-reads-every-row}

The support team adds two columns to `support.tickets`: `callback_number`, classified `internal`, and `reply_email`, classified `public`. A team that wants values judged, not only names, then adds [chapter 3](#classify-columns-from-their-values)'s classification of the table to the job, by sample and by every row:

Example `slow-check-every-row` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""The support team's pull request adds two columns to support.tickets, which coverage judges by their names and chapter
3's value checks judge by reading a sample, or every row. The prose's point rests on the callback number's empty column
and on the values each check reads; counts of values stand in for time, which depends on the machine."""
import pyarrow as pa

from lib import ci, pii

main = ci.checkout()
branch = ci.checkout(main)
(branch / "migrations" / "0001-callback-and-reply.sql").write_text(
    "alter table support.tickets add column callback_number varchar;\n"
    "alter table support.tickets add column reply_email varchar;\n")
ci.edit(branch, "governance/metadata.toml", '8 = { name = "status"',
        '9 = { name = "callback_number", classification = "internal", description = "A number to call the learner back on." }\n'
        '10 = { name = "reply_email", classification = "public", description = "Where the reply goes." }\n8 = { name = "status"')
before, after = ci.build(main), ci.build(branch)

report = ci.run(before, after, checks=["coverage", "classify-sampled", "classify-every-row"])
for name in ("body", "callback_number", "reply_email"):
    values = after.catalog.load_table("support.tickets").scan(selected_fields=(name,)).to_arrow()[name]
    print(f"support.tickets.{name}, values on the branch:", f"{len(values) - values.null_count:,}")
    for check in report.checks:
        found = [f.message for f in check.findings if f.id == f"{check.name}/support.tickets.{name}"]
        print(f"support.tickets.{name}, {check.name}:", found[0] if found else "no finding")
for check in report.checks[1:]:
    print(f"{check.name}, values read:", f"{check.checked:,}")

text_columns, sampled, every_row = 0, 0, 0
for name in sorted(before.described):
    data = before.catalog.load_table(name).scan().to_arrow()
    # the non-null values of each text column, the ones a value check classifies
    filled = [len(column) - column.null_count for column in data.columns if pa.types.is_string(column.type)]
    text_columns += len(filled)
    # the sampled check reads at most pii.ROWS values of each column
    sampled += sum(min(pii.ROWS, count) for count in filled)
    every_row += sum(filled)
print("text columns in the described tables:", text_columns)
print("values the sampled check would read in them:", f"{sampled:,}")
print("values the every-row check would read in them:", f"{every_row:,}")
```

Output:

```text
support.tickets.body, values on the branch: 2,000
support.tickets.body, coverage: no finding
support.tickets.body, classify-sampled: values support sensitive, reviewed as personal
support.tickets.body, classify-every-row: values support sensitive, reviewed as personal
support.tickets.callback_number, values on the branch: 0
support.tickets.callback_number, coverage: no finding
support.tickets.callback_number, classify-sampled: no finding
support.tickets.callback_number, classify-every-row: no finding
support.tickets.reply_email, values on the branch: 0
support.tickets.reply_email, coverage: classified public; its name suggests personal; needs team-support's approval
support.tickets.reply_email, classify-sampled: its name suggests personal, reviewed as public
support.tickets.reply_email, classify-every-row: its name suggests personal, reviewed as public
classify-sampled, values read: 1,000
classify-every-row, values read: 10,000
text columns in the described tables: 32
values the sampled check would read in them: 5,800
values the every-row check would read in them: 429,453
```

Coverage fails `reply_email` by its name, `classified public; its name suggests personal; needs team-support's approval`, and passes `callback_number`, `no finding`, because no name rule matches it. The branch holds 0 values in the new column, so reading values doesn't help yet either. The migration adds the column empty, and every row gives `no finding`. [Chapter 3](#reclassify-on-schema-change)'s scheduled sample catches the phone numbers once the column fills.

The sampled check reads 1,000 values and the every-row check reads 10,000. Both find `support.tickets.body` sensitive under a personal classification, which chapter 3 already sent to `team-support`. Across every text column in the described tables, a sample would read 5,800 values, and every row would read 429,453. The second number grows with the data, on every pull request, whatever the pull request changed. A job that keeps people waiting, we judge, gets skipped, and then removed.

**Working rule:** Size pull-request checks by the change, not by the data: metadata, schemas, policies and the names of the columns a pull request adds. Run checks that read values on a schedule, with a fixed sample, as chapter 3 does, and send their findings to the owning team. Document where the job's checks stop, such as at a column added empty.

### A check that flags every ID {#a-check-that-flags-every-id}

A cautious team adds a check that treats every column named like an ID as personal data. The platform decided otherwise for the IDs it joins on: [chapter 2](#classify-pseudonymous-ids) classifies `learner_id` as `internal` and protects the table that resolves it. The check's findings are new, so each owning team waives them:

Example `noisy-check-waivers` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""A noisy check added to the job: every column named like an ID is personal. The platform decided otherwise for IDs
used for joining, so each owning team waives its findings, and the waiver count climbs. The prose's point rests on the
not-acted-on line of each check."""
from collections import Counter

from lib import ci

main = ci.checkout()
branch = ci.checkout(main)                          # the platform team adds the check to the job's settings
ci.edit(branch, "governance/ci.toml", '"properties"]', '"properties", "id-columns"]')
before, after = ci.build(main), ci.build(branch)

report = ci.run(before, after)
print("waivers in the file, before:", len(ci.waivers(after.governance)))
noisy = next(check for check in report.checks if check.name == "id-columns")
print("job, before the waivers:", "passed" if report.passed else "failed")
print("id-columns, findings:", len(noisy.findings))
print("id-columns, findings on main:", len(noisy.on_main))
# the last word of each message is the classification
classified = Counter(finding.message.rpartition(" ")[2] for finding in noisy.findings)
for level, count in sorted(classified.items()):
    print(f"id-columns, findings classified {level}:", count)
# the part of the finding's ID after the check's name: the column's full name
print("id-columns, the public one:", ", ".join(f.id.split("/")[1] for f in noisy.findings if f.message.endswith("public")))

with open(after.governance / "waivers.toml", "a", encoding="utf-8") as waivers:
    for finding in noisy.findings:
        waivers.write(f'\n[[waivers]]\nfinding = "{finding.id}"\nowner = "{finding.owner}"\n'
                      'reason = "An ID for joining, internal by decision."\nexpires = 2026-10-31\n')

report = ci.run(before, after)
print("waivers in the file, after:", len(ci.waivers(after.governance)))
print("job, with the waivers:", "passed" if report.passed else "failed")
for check in (check for check in report.checks if check.findings):
    idle = [f for f in check.findings if f.waiver or f.on_main]          # findings nobody acted on
    print(f"{check.name}, not acted on:", f"{len(idle)} of {len(check.findings)} findings, {len(idle) / len(check.findings):.0%}: "
          f"{len(check.waived)} waived, {len(check.on_main)} on main")
```

Output:

```text
waivers in the file, before: 0
job, before the waivers: failed
id-columns, findings: 21
id-columns, findings on main: 0
id-columns, findings classified internal: 20
id-columns, findings classified public: 1
id-columns, the public one: learning.courses.course_id
waivers in the file, after: 21
job, with the waivers: passed
coverage, not acted on: 2 of 2 findings, 100%: 0 waived, 2 on main
properties, not acted on: 4 of 4 findings, 100%: 0 waived, 4 on main
id-columns, not acted on: 21 of 21 findings, 100%: 21 waived, 0 on main
```

The check finds 21 columns, each an ID the platform classified on purpose. 20 of them are `internal`, and `learning.courses.course_id` is `public`.

The waivers file grows from 0 waivers to 21, and the ID check shows `21 of 21 findings, 100%: 21 waived, 0 on main`. That is past any threshold [Tricorder's authors use](#count-waived-findings), as an analogy only, since theirs count clicks, not waivers. The properties check shows the same share, `4 of 4 findings, 100%: 0 waived, 4 on main`, and it's right to: its findings are a fix the pipeline runner needs. The count can't tell the two apart, and the reasons can.

**Working rule:** Before adding a check, run it on the main branch and read every finding; if most would be waived, change the rule rather than waiving its findings. Remove a check whose findings stay mostly waived, and treat a high share on a correct check as work to schedule, with an owner and a date.

### A broken file becomes a finding {#a-broken-file-becomes-a-finding}

A support agent's entry goes into `governance/users.toml` with a quote missing. The same pull request changes `crm.learners.country` from text to a number, and it carries the CRM team's unclassified `work_email`:

Example `broken-files-become-findings` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.28:

```python
"""A pull request that breaks two files the job reads: a support agent added to the users file with a quote missing,
and a migration Iceberg refuses. It also carries the CRM team's unclassified work_email column. The prose's point rests
on the two checks that could not run and on the exit code."""
from lib import ci

main = ci.checkout()
branch = ci.checkout(main)
# the closing quote after "support" is missing, so the users file no longer parses
ci.edit(branch, "governance/users.toml", '[users.agent-a09]', '[users.agent-a12]\ngroups = ["support]\nregion = "emea"\n\n'
        '[users.agent-a09]')
(branch / "migrations" / "0001-add-work-email.sql").write_text("alter table crm.learners add column work_email varchar;\n")
# a string column cannot become an int: that isn't one of Iceberg's type promotions, so the migration is refused
(branch / "migrations" / "0002-country-as-number.sql").write_text("alter table crm.learners alter column country type int;\n")
print("files the pull request changes:", ", ".join(ci.changed(main, branch)))

report = ci.run(main, branch)
for line in ci.lines(report):
    print(line)
print("checks that could not run:", ", ".join(check.name for check in report.checks if check.error))
print("checks that ran:", sum(check.error is None for check in report.checks))
print("exit code:", report.exit_code)
```

Output:

```text
files the pull request changes: governance/users.toml, migrations/0001-add-work-email.sql, migrations/0002-country-as-number.sql
coverage: failed, findings 3, new 1, on main 2, waived 0, 12 tables checked
contract-rules: passed, findings 0, new 0, on main 0, waived 0, 10 contracts checked
contracts: passed, findings 0, new 0, on main 0, waived 0, 11 files checked
policy-tests: failed, the check could not run
enforcement-tests: failed, the check could not run
migrations: failed, findings 1, new 1, on main 0, waived 0, 2 migrations checked
pipelines: passed, findings 0, new 0, on main 0, waived 0, 4 pipelines checked
lineage-classifications: passed, findings 0, new 0, on main 0, waived 0, 23 columns checked
owner-review: passed, findings 0, new 0, on main 0, waived 0, 77 columns checked
removals: passed, findings 0, new 0, on main 0, waived 0, 87 columns checked
properties: passed, findings 4, new 0, on main 4, waived 0, 12 tables checked
coverage/ai.review_corpus: no metadata; on main, owner team-platform
coverage/crm.learners.work_email: not classified; its name suggests personal
coverage/marketing.audience: no metadata; on main, owner team-platform
policy-tests/error: the check could not run: governance/users.toml doesn't parse: Illegal character '\n' (at line 13, column 20)
enforcement-tests/error: the check could not run: governance/users.toml doesn't parse: Illegal character '\n' (at line 13, column 20)
migrations/0002-country-as-number.sql: refused: Cannot change column type: country: string -> int
properties/ai.review_corpus: 7 of 7 generated properties missing; on main, owner team-platform
properties/analytics.course_performance: 4 of 4 generated properties missing; on main, owner team-analytics
properties/analytics.learner_activity: 4 of 4 generated properties missing; on main, owner team-analytics
properties/marketing.audience: 7 of 7 generated properties missing; on main, owner team-platform
change crm.learners, field 16: added as work_email string; named by 0 pipelines, reaches 0 columns
job: failed
checks that could not run: policy-tests, enforcement-tests
checks that ran: 9
exit code: 1
```

The users file breaks the two checks that read it: `the check could not run: governance/users.toml doesn't parse: Illegal character '\n' (at line 13, column 20)`. Iceberg refuses the type change, which isn't a promotion, as `refused: Cannot change column type: country: string -> int`. The two checks that could not run don't stop the other checks, migrations among them, so the author also sees `not classified; its name suggests personal`, and the job exits with code 1. Without the catch, the job would stop at the first error, and the author would fix one problem per run.

**Working rule:** Turn a check that crashes into one finding that fails the job, with the error's first line and the file it names, run the other checks anyway, and never let a waiver silence it.

### Other failures {#other-ci-failures}

- **A gate nobody required.** A job whose status check branch protection doesn't require reports its findings, and the pull request merges anyway. Require it, and count merged pull requests whose job failed.
- **A broken build hides findings.** A table that a broken pipeline didn't write can't be found undescribed. Read the `pipelines` check first.
- **Waivers outlive their reason.** A finding gets fixed and its waiver stays, ready to hide the next one with the same ID. The report lists waivers that match no finding; delete them.
- **A rename changes finding IDs.** IDs name columns, so a renamed column's findings come back under new IDs, and the report lists their waivers as matching no finding. Move the waivers in the rename's pull request.
- **An approval outlives what it approved.** `team-crm` approves the downgrade of `city`, then the author pushes a downgrade of `email`, and the approval covers both. Have branch protection "dismiss stale pull request approvals when commits are pushed that affect the diff in the pull request".
- **One approval speaks for a team.** Any one code owner's approval meets GitHub's requirement, and branch protection's count is per branch. Count approvals per team in the job where a domain wants more.
- **The blocked team edits the gate.** A team whose pull request fails removes the check from `ci.toml`, adds a waiver, or edits CODEOWNERS. Give all three the platform team as code owner.
- **Changes outside pull requests.** A notebook creates a table, or a migration runs by hand. Run the job on a schedule against production too, as [chapter 2](#test-the-catalog-against-the-metadata) runs `problems`.

## What this chapter decided {#ci-decisions}

- **One job runs the checks of chapters 2 to 7 on every pull request,** `lib.ci.run`, listed in `governance/ci.toml`; only chapter 3's sampling of values runs on a schedule instead. `lib.ci.main` returns the exit code and writes the report as Markdown.
- **The job judges what the pull request changes.** A finding it introduces fails it unless approved or waived; a finding already on main is reported with its owner and fails nothing. A check that crashes is one failing finding.
- **Every finding has a stable ID,** the check and its subject, such as `coverage/crm.learners.work_email`.
- **A pull request is compared with the main branch on scratch platforms** built the way the platform runs, each with its own migrations and pipelines.
- **Schema changes are diffed by field ID** and reported three ways: Iceberg readers, the pipelines whose SQL names the column, and every column lineage says it reaches, INDIRECT edges included.
- **Two rules of our own:** lowering a classification, changing an owner or moving a table to another domain needs the approval of the table's owner on the main branch, counted per team; and a column is removed only after the main branch has marked it `deprecated`.
- **Ownership is an ODCS contract per table,** with one domain and the owning team in the role `owner`, generated into a folder per domain with a CODEOWNERS line, and checked by the job. The platform team owns CODEOWNERS, the job's settings, its global rules, the waivers and the migrations.
- **Global rules and domain rules are Rego,** run in-process with regopy on every contract, outside the access policy's folder.
- **The planted gaps stay on main:** `marketing.audience` and `ai.review_corpus` appear in every report as coverage findings, with the platform team as their owner, until they're described.
- **Noise is measured as findings nobody acts on, per check: waived, or left on main.** A check whose findings are mostly ignored is either wrong or the platform is, and the count alone can't say which. A waiver names one finding, an owner, a reason and an end date at most 90 days away, and coverage and the enforcement tests are never waived.
- **Pull-request checks are sized by the change;** checks that read values run on a schedule. The checks are only useful while people keep them on, so each one is sized to the change.
