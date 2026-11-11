---
title: "Data Governance as Code"
chapter: "Audit and evidence"
chapter_id: audit-and-evidence
book: data-governance-as-code
edition: 2026.11.22
verified: 2026-11-11
edition_code: 52FE-HY24
canonical: https://rollingedition.com/data-governance-as-code/audit-and-evidence
license: CC BY 4.0
attribution: "“Audit and evidence,” chapter 8 of Data Governance as Code, Edition 2026.11.22, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/audit-and-evidence. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Audit and evidence

By the end of this chapter you can keep an audit log of every access decision and query, with no values in it, chained so that an edit shows. You'll write it where the decisions are made, and write down its head, the number and hash of its last record, where the log's writer can't change it, so that an edit to, or a removal of, any record up to that head shows. You'll also explain an old decision after the policy has changed, cross-check the log against the query engine's own record of what it ran, and generate access reviews and evidence reports from the log and the policies, as code that anyone can run again.

The platform, the online learning platform this book follows, sells professional courses to adult learners. [Chapter 5](#access-policies-as-code) wrote its access policy in Rego, and [chapter 6](#enforcing-policies-on-queries) built the **enforcement layer**, `lib.enforce.Enforcer`, which asks the policy for a **decision** about every table a query reads and rewrites the query so that DuckDB returns only what the decision allows. The layer forgets each decision as soon as it has applied it. When the support lead asks why an analyst could read review text last week, or an auditor asks the platform to show that its access rules work, nobody can answer from records. And the obvious fix, logging the text of every query, makes a second copy of what the policy protects: a support agent's query can carry a learner's email in its `WHERE` clause, and [chapter 7](#retention-consent-erasure) has to erase a learner from everywhere their data went.

The chapter's terms, as the rest of the book uses them: an **audit log** is a record of who did what, when, and with what outcome, kept so that someone can check it later. The platform's audit log holds one **decision record** per query. A **policy revision** is a fingerprint of everything a decision depended on besides the request. A log is **tamper-evident** when a change to it can be detected, though not prevented. An **access review** compares what each person may read with what they use. **Evidence** is a report that shows a control works, generated from records rather than captured from a screen.

The code is the book's shared module `lib.audit`. Its `Audited` class wraps [chapter 6](#enforcing-policies-on-queries)'s `Enforcer` without changing it: it writes a record for every query, and then lets the layer run the query. Most examples replay one day of the platform's queries, `lib.audit.DAY`: 13 queries on Oct 1, 2026, from a support agent, finance, an instructor through the course assistant, marketing, a data scientist, the assistant on its own account, and one user the platform doesn't know. The examples run DuckDB 2.0.0, sqlglot 30.30.0 and regopy 1.5.2.

## Record every decision where it's made {#record-every-decision}

An audit record is only as complete as what its writer knows. The query engine knows the SQL it ran, but not who asked or why. The policy knows its decision, but not the query. Only the enforcement layer holds all of it at once: the principal, meaning the user or program that asks, the tables and columns the query reads, each table's decision, and the SQL it hands the engine. That is where Open Policy Agent (OPA) writes its own record: "The decision logs contain events that describe policy queries. Each event includes the policy that was queried, the input to the query, bundle metadata, and other information that enables auditing and offline debugging of policy decisions" ([OPA, decision logs](https://www.openpolicyagent.org/docs/management-decision-logs)). Each event carries a `decision_id`, the `path` of the rule queried, the `input`, the `result`, a `timestamp`, and `bundles[_].revision`, the "Revision of the bundle at the time of evaluation". regopy, which runs the platform's policy inside Python, returns the value of the query and nothing more, so the platform's layer has to build every other field itself.

NIST's catalog of security controls gives a checklist for those fields. Control AU-3 asks that audit records "contain information that establishes the following: a. What type of event occurred; b. When the event occurred; c. Where the event occurred; d. Source of the event; e. Outcome of the event; and f. Identity of any individuals, subjects, or objects/entities associated with the event" ([NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)).

`lib.audit.Audited` takes a catalog and a `Log`, the audit log's file. Its `sql` method takes the same arguments as `Enforcer.sql`, plus `via`, the assistant that sent the query when one did. It plans the query, asks the policy about every table the query reads, writes one record, and only then hands the rewritten query to DuckDB. So no query reaches DuckDB through the layer without a record, and when the record can't be written, the query doesn't run. [Chapter 6](#query-on-someones-behalf) left this chapter one case: when the course assistant answers `instructor-17`, the query runs as the instructor, and both identities belong in the log. The example sends that query, then has the assistant try to put names to the ratings:

Example `decision-record` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
from lib import audit
from lib.catalog import open_catalog
from lib.enforce import Denied
from lib.platform import scratch

# Chapter 6's enforcement layer, wrapped so that every query it's given is recorded before DuckDB runs anything.
log = audit.Log(scratch() / "audit.jsonl")
platform = audit.Audited(open_catalog(["crm.learners", "learning.reviews"]), log)

# instructor-17 asks the course assistant how their reviews look. The assistant writes the SQL; the query runs as the
# instructor, with the assistant recorded as the one that sent it.
question = "select course_id, count(*) as reviews, round(avg(rating), 2) as rating from learning.reviews group by all"
platform.sql(question, user="instructor-17", via="assistant-1").fetchall()

# Then the assistant tries to put names to the ratings, which the instructor may not see.
try:
    platform.sql("select l.full_name, r.rating from learning.reviews as r join crm.learners as l using (learner_id)",
                 user="instructor-17", via="assistant-1").fetchall()
except Denied:
    pass

for record in log.records():
    print(f"record {record['seq']}:")
    print(audit.show(record))
```

Output:

```text
record 1:
  seq: 1
  event: query
  time: 2026-10-01T09:00:00Z
  catalog: platform
  user: instructor-17
  via: assistant-1
  purpose: null
  query: SELECT course_id, COUNT(*) AS reviews, ROUND(AVG(rating), ?) AS rating FROM learning.reviews GROUP BY ALL
  outcome: allowed
  denial: null
  decision: {"table": "learning.reviews", "columns": ["course_id", "rating"], "allow": true, "row_filters": [{"column": "course_id", "in": [2, 75, 80, 87, 103, 134]}], "column_masks": {}, "reasons": ["instructor may read learning.reviews"]}
  policy_revision: f761e4ad08d4...
  rewritten_digest: 385c5cdabeae...
  prev_hash: 000000000000...
record 2:
  seq: 2
  event: query
  time: 2026-10-01T09:01:00Z
  catalog: platform
  user: instructor-17
  via: assistant-1
  purpose: null
  query: SELECT alias_1.full_name, alias_2.rating FROM learning.reviews AS alias_2 JOIN crm.learners AS alias_1 USING (learner_id)
  outcome: denied
  denial: instructor-17 may not read crm.learners: no group of this user may read this table
  decision: {"table": "crm.learners", "columns": ["full_name", "learner_id"], "allow": false, "row_filters": [], "column_masks": {}, "reasons": ["no group of this user may read this table"]}
  decision: {"table": "learning.reviews", "columns": ["learner_id", "rating"], "allow": true, "row_filters": [{"column": "course_id", "in": [2, 75, 80, 87, 103, 134]}], "column_masks": {}, "reasons": ["instructor may read learning.reviews"]}
  policy_revision: f761e4ad08d4...
  rewritten_digest: null
  prev_hash: 0d3e61eaadeb...
```

Record 1 covers AU-3's six items. `event` is the type, and `time` says when, in UTC with a `Z`, since control AU-8 asks for time stamps that "use Coordinated Universal Time" or state their offset; the examples take it from a fixed clock. `catalog` says where. `user` and `via` are the source: the query ran as `instructor-17`, and `assistant-1` sent it. With the decision's `table`, they are the identities item f asks for. `query` and the decision's `columns` say what was read, and `outcome` and the decision's `allow`, `row_filters`, `column_masks` and `reasons` say how it ended, down to the course IDs the row filter kept. The next sections explain `policy_revision`, `rewritten_digest` and `prev_hash`.

Record 2 is a denial, and it holds both tables' decisions: the join may read `learning.reviews` but not `crm.learners`, and one denied table denies the query. Without `via`, the log would say that the instructor tried to read learners' names. With it, a reviewer knows the assistant wrote that query, and looks at the assistant's behaviour as well as the instructor's.

**Working rule:** Write the audit record in the enforcement layer, where the principal, the query and the decision meet, and write it before the query runs, so that a failed write stops the query. Record every identity involved, the person and any assistant acting for them, and every table's decision with its filters, masks and reasons. When an engine enforces the policy itself, as the SQL engine Trino does through OPA, turn on OPA's decision log instead, and make sure its input names every identity involved: Trino's `opa.identity.extra-credentials-keys`, for example, forwards the credentials it lists "to OPA as extraCredentials in the identity context" ([Trino 484, OPA access control](https://trino.io/docs/484/security/opa-access-control.html)).

## Keep values out of the record {#keep-values-out-of-the-record}

The [decision record](#record-every-decision) holds IDs, names of tables and columns, decisions and digests, and no value from the data its query read, because everything an audit log holds becomes data to protect. SP 800-53's discussion of AU-3 warns that "there is the potential to reveal personally identifiable information in the audit trail, especially if the trail records inputs", and its enhancement AU-3(3) asks systems to "Limit personally identifiable information contained in audit records to the following elements identified in the privacy risk assessment: [Assignment: elements]" ([NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)). Limit, not remove: AU-3 f asks for the principal, so every record names one, such as `instructor-17`, one instructor's account. The GDPR calls personal data "any information relating to an identified or identifiable natural person", identifiable "directly or indirectly, in particular by reference to an identifier such as a name, an identification number, location data, an online identifier" ([GDPR, Article 4(1)](https://eur-lex.europa.eu/eli/reg/2016/679/oj)), and an account ID like this one can be such an identifier. The platform has a sharper reason to keep learners out: [chapter 7](#retention-consent-erasure) erases a learner from every table their data reached, and erasing one record from the [chain](#chain-the-records) this chapter adds can't be told from tampering.

The risk is the query text. A support agent who looks a learner up by the email in a ticket writes that email into the query. `lib.audit.normalized` keeps the query's shape and drops its values: sqlglot parses the query, and every literal, in any of DuckDB's syntaxes, becomes `?`. So does every name the catalog doesn't hold, such as a value typed in double quotes, except that an alias or a CTE's name the query defines becomes `alias_1`, `alias_2` and so on. Comments, which can hold anything, are left out, and a denial's reason is recorded with the same values taken out. The SQL the layer hands DuckDB is kept only as `rewritten_digest`, an HMAC-SHA256 under a key only the layer holds, which the [cross-check](#cross-check-the-query-log) matches against DuckDB's own log. OPA starts from the whole input instead, and "queries the data.system.log.mask path prior to encoding and uploading decision logs" to remove what that policy names ([OPA, decision logs](https://www.openpolicyagent.org/docs/management-decision-logs)). The platform's layer never writes the values at all.

On the platform, `agent-a05` looks up an EMEA learner by email, then by ID, and `analyst-1` reads learners' emails, which the policy pseudonymizes. The example never prints the email or the ID:

Example `query-without-literals` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
from lib import audit
from lib.catalog import open_catalog
from lib.platform import load, scratch

log = audit.Log(scratch() / "audit.jsonl")
platform = audit.Audited(open_catalog(["crm.learners"]), log)

# agent-a05 looks up an EMEA learner by the email in a ticket, then by their ID. Neither value is ever printed.
learners = load("crm.learners").to_pylist()
learner = next(row for row in learners if row["support_region"] == "emea")
email, learner_id = learner["email"], learner["learner_id"]
platform.sql(f"select learner_id, full_name from crm.learners where email = '{email}'", "agent-a05").fetchall()
platform.sql(f"select email, phone from crm.learners where learner_id = {learner_id}", "agent-a05").fetchall()
platform.sql("select learner_id, email from crm.learners", "analyst-1").fetchall()      # pseudonymized with the key

for record in log.records():
    print("query in the record:", record["query"])
engine = audit.engine_queries(platform.enforcer.connection)
print("the email, in the audit log:", email in log.path.read_text())
print("the email, in DuckDB's query log:", any(email in query for query in engine))
print("the pseudonymization key, in DuckDB's query log:", any(platform.enforcer.key in query for query in engine))
print("its placeholder, in DuckDB's query log:", any("$pseudonym_key" in query for query in engine))

# Guessing which learner the agent looked up, from a list of the platform's emails: rebuild the text DuckDB ran with
# each email, digest it, and compare. First with a plain SHA-256 of the query, as a log might keep, then with the
# record's keyed digest, by someone without the layer's key and by someone who holds it.
ran = next(query for query in engine if email in query)
guesses = [ran.replace(email, row["email"]) for row in learners]
logged = log.records()[0]["rewritten_digest"]
print("emails tried:", f"{len(guesses):,}")
print("emails a plain SHA-256 of the query confirms:", sum(audit.sha256(g) == audit.sha256(ran) for g in guesses))
print("emails the keyed digest confirms, without the layer's key:",
      sum(audit.digest(g, "a-guessed-key") == logged for g in guesses))
print("emails the keyed digest confirms, with the layer's key:", sum(audit.digest(g, platform.key) == logged for g in guesses))
```

Output:

```text
query in the record: SELECT learner_id, full_name FROM crm.learners WHERE email = ?
query in the record: SELECT email, phone FROM crm.learners WHERE learner_id = ?
query in the record: SELECT learner_id, email FROM crm.learners
the email, in the audit log: False
the email, in DuckDB's query log: True
the pseudonymization key, in DuckDB's query log: False
its placeholder, in DuckDB's query log: True
emails tried: 5,000
emails a plain SHA-256 of the query confirms: 1
emails the keyed digest confirms, without the layer's key: 0
emails the keyed digest confirms, with the layer's key: 1
```

The records keep `WHERE email = ?` and `WHERE learner_id = ?`, and a search of the audit log for the email finds nothing (`False`). DuckDB's query log does hold it (`True`), because that log records the SQL text DuckDB runs, literals included. The pseudonymization key isn't there (`False`): [chapter 6](#write-masks-as-sql) passes the key as a parameter, so DuckDB's log shows the placeholder `$pseudonym_key` where the key would be.

The last lines show what the key does. The rewrite is code in the repository, so anyone with a list of emails, from an old export or a breach, can rebuild the text DuckDB ran for each one. Of 5,000 emails tried, a plain SHA-256 of that text confirms 1: the learner the agent looked up. The record's keyed digest confirms 0 without the layer's key, and 1 with it. So a keyed digest of a query that held an email is a pseudonym of that email, and the key is what keeps it one, as [chapter 6](#write-masks-as-sql) showed for the platform's pseudonyms. The key stays with the layer, away from anyone who reads the log, and so does the cross-check, which needs it.

DuckDB takes a value in more ways than a quoted string, and a name can hold one too. The second example, a regression test for `normalized`, types the same learner's email, name and ID into `agent-a05`'s queries in each of those ways:

Example `query-shape-hard-cases` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
import json
import re

from lib import audit
from lib.catalog import open_catalog
from lib.enforce import Denied
from lib.platform import load, scratch

log = audit.Log(scratch() / "audit.jsonl")
platform = audit.Audited(open_catalog(["crm.learners"]), log)

# An EMEA learner's email, name and ID, typed into agent-a05's queries as values and as names. None is ever printed.
learner = next(row for row in load("crm.learners").to_pylist() if row["support_region"] == "emea")
email, name, learner_id = learner["email"], learner["full_name"], learner["learner_id"]
cases = {
    "a string": f"select learner_id from crm.learners where email = '{email}'",
    "a dollar-quoted string": f"select learner_id from crm.learners where email = $${email}$$",
    "an escape string": f"select learner_id from crm.learners where email = e'{email}'",
    "a list": f"select learner_id from crm.learners where email in ['{email}']",
    "a number": f"select email from crm.learners where learner_id = {learner_id}",
    "a comment": f"select email from crm.learners where learner_id = {learner_id} -- {name}",
    "a name in double quotes": f'select learner_id from crm.learners where full_name = "{name}"',
    "a column alias": f'select learner_id as "{email}" from crm.learners',
    "a table alias": f'select "{name}".email from crm.learners as "{name}"',
    "a CTE's name": f'with "{email}" as (select learner_id from crm.learners) select learner_id from "{email}"',
    "a table the catalog doesn't hold": f'select learner_id from "{email}"',
}

for query in cases.values():
    try:
        platform.sql(query, "agent-a05").fetchall()
    except Denied:
        pass

# What each record keeps of its query. The email or the name anywhere in its line, or the ID in what it keeps, is a
# value that got through, and is never printed.
held = []
for case, line in zip(cases, log.lines()):
    record = json.loads(line)
    kept = record["query"] + (f" (denied: {record['denial']})" if record["denial"] else "")
    held.append(email in line or name in line or bool(re.search(rf"\b{learner_id}\b", kept)))
    print(f"{case}:", "(holds a value)" if held[-1] else kept)
print("records holding the email, the name or the ID:", sum(held), "of", len(cases))
```

Output:

```text
a string: SELECT learner_id FROM crm.learners WHERE email = ?
a dollar-quoted string: SELECT learner_id FROM crm.learners WHERE email = ?
an escape string: SELECT learner_id FROM crm.learners WHERE email = ?
a list: SELECT learner_id FROM crm.learners WHERE email IN (?)
a number: SELECT email FROM crm.learners WHERE learner_id = ?
a comment: SELECT email FROM crm.learners WHERE learner_id = ?
a name in double quotes: SELECT learner_id FROM crm.learners WHERE full_name = ? (denied: Column '?' could not be resolved)
a column alias: SELECT learner_id AS alias_1 FROM crm.learners
a table alias: SELECT alias_1.email FROM crm.learners AS alias_1
a CTE's name: WITH alias_1 AS (SELECT learner_id FROM crm.learners) SELECT learner_id FROM alias_1
a table the catalog doesn't hold: SELECT learner_id FROM ? (denied: not a table in the catalog: "?")
records holding the email, the name or the ID: 0 of 11
```

In allowed and denied queries alike, each record keeps the query's shape and none of its values. The last line counts the records that hold the email, the name or the ID: 0 of 11.

Two things are lost. The normalized text drops harmless values and names too: in the [first record](#record-every-decision), `ROUND(AVG(rating), 2)` became `ROUND(AVG(rating), ?)`, and in the second, the aliases `r` and `l` became `alias_2` and `alias_1`. And the log can't answer "who looked up this learner?". When the platform needs that answer, for a learner who asks who has read their data, keep it in a separate access log, with learner IDs, a retention period and no chain, which [chapter 7](#retention-consent-erasure)'s erasure reaches like any other table.

**Working rule:** Record a query's shape, never its values: replace every literal, in every syntax the engine accepts, and every name the catalog doesn't hold, drop comments, take the same values out of denial reasons, and keep the executed SQL only as a keyed digest whose key the log's readers never get. Never use a plain hash of text that may hold personal data. When you need to know who read one person's data, keep that in a separate log that retention and erasure reach, not in the tamper-evident one.

## Replay an old decision under its own policy {#replay-old-decisions}

A [decision record](#record-every-decision) holds the request, but a decision depends on three things: the request, the policy's rules, and the data the policy reads. The last two change all the time. The platform's policy reads `governance/users.toml`, `governance/metadata.toml` and `learning.courses`, as [chapter 5](#generate-the-data-the-policy-reads) set up, so a support agent moved to another region, or a course added to `learning.courses`, changes decisions without anyone touching Rego. If a record says nothing about what the policy was, its decision can't be explained once either changes: replayed later, it gives a different answer, and the log looks wrong. OPA records the policy's version as `bundles[_].revision`. For policies that call non-deterministic built-ins, such as the time or an HTTP request, OPA can also log their results in `nd_builtin_cache`, "Intended for use in debugging and decision replay" ([OPA, decision logs](https://www.openpolicyagent.org/docs/management-decision-logs)). The platform's policy calls none.

`lib.audit.bundle` puts together the policy's modules and its data document, the facts the policy reads, generated from those three sources, as OPA ships them in a bundle. `lib.audit.revision` is the SHA-256 of that bundle: a fingerprint that changes when any rule changes, or any fact the policy reads. Every record carries the revision that decided it. `lib.audit.Archive` keeps every bundle the layer has used, under its revision, so a decision can be made again under the policy that made it. A bundle holds rules and the attributes of the platform's users, not data about learners, so the archive can be kept as long as the log.

On the platform, `analyst-1` reads learners' emails and gets pseudonyms. Later, a pull request adds `analyst-1` to support for EMEA, the change [chapter 6](#test-who-sees-what) caught with its who-sees-what test. Make that change, then replay the old record under each revision:

Example `explain-old-decision` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
from lib import audit, policy
from lib.catalog import open_catalog
from lib.platform import scratch

folder = scratch()
archive = audit.Archive(folder / "bundles")         # every policy revision that has decided anything, by revision
log = audit.Log(folder / "audit.jsonl")

# analyst-1 reads learners' emails, which the policy pseudonymizes.
platform = audit.Audited(open_catalog(["crm.learners"]), log, archive=archive)
platform.sql("select learner_id, email from crm.learners", "analyst-1").fetchall()
record = log.records()[0]

# Later, a pull request adds analyst-1 to support for EMEA, as in chapter 6. Only users.toml changes.
data = policy.data_document()
data["platform"]["users"]["analyst-1"] = {"groups": ["data-science", "support"], "region": "emea"}
current, logged = audit.bundle(data=data), archive.get(record["policy_revision"])
print("logged under revision:", record["policy_revision"][:12])
print("current revision:", audit.revision(current)[:12])
print("policy modules changed:", current["modules"] != logged["modules"])
print("data document changed:", current["data"] != logged["data"])

# Explain the logged decision by making it again, from the request the record holds, under each revision.
print("email, as logged:", record["decisions"][0]["column_masks"].get("email", "shown as stored"))
for name, revision in [("the current revision", current), ("the logged revision", logged)]:
    again = audit.replay(record, revision)
    print(f"under {name}, email:", again[0]["column_masks"].get("email", "shown as stored"))
    print(f"under {name}, the decision matches the log:", again == record["decisions"])
```

Output:

```text
logged under revision: f761e4ad08d4
current revision: 0350e789b34d
policy modules changed: False
data document changed: True
email, as logged: pseudonymize
under the current revision, email: shown as stored
under the current revision, the decision matches the log: False
under the logged revision, email: pseudonymize
under the logged revision, the decision matches the log: True
```

The revision changed, from `f761e4ad08d4` to `0350e789b34d`, though no Rego did: asked whether the policy modules changed, the example answers `False`, and whether the data document changed, `True`. A fingerprint of the policy files alone would have missed the change. Replayed under the current revision, the decision no longer matches the log: `email` is `shown as stored`, because support sees contact details. An investigator holding only the current policy would conclude that the log, or the layer, was wrong. Replayed under the logged revision from the archive, `email` is `pseudonymize` again, and the decision matches the log: `True`.

Replay explains the decision, not the rows. A row filter is replayed as a rule, such as support's region or the consent filter `learner_consented`, and which rows passed it depended on the data that day, which may have changed since, or been erased. That split is by design: the log says what the rule was, and the tables, with their own snapshots and retention, say what it matched.

**Working rule:** Fingerprint every decision with a hash of everything it depended on besides the request: the policy's modules and its data document, together. Archive each revision for as long as you keep the log, and explain an old decision by replaying it under its own revision, never under the current one. If a policy reads the clock or calls another service, log those results too, as OPA's `nd_builtin_cache` does.

## Chain the records so an edit shows {#chain-the-records}

The platform's [decision records](#record-every-decision) are evidence only if a change to them can be detected. SP 800-53 asks systems to "Protect audit information and audit logging tools from unauthorized access, modification, and deletion" (AU-9), and, in AU-9(3), to "Implement cryptographic mechanisms to protect the integrity of audit information and audit tools". Its discussion of AU-9(3) gives as an example "signed hash functions using asymmetric cryptography" ([NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)), which only the holder of a private key can make. The platform's chain, below, is not that, and protects nothing on its own. NIST's guide to log management, SP 800-92, describes the plainest mechanism: "Log file integrity checking involves calculating a message digest for each file and storing the message digest securely to ensure that changes to archived logs are detected" ([NIST SP 800-92](https://doi.org/10.6028/NIST.SP.800-92)). The guide dates from 2006. It names MD5 and SHA-1 as the common digests of its day, and its own footnote 25 advises SHA-256, which the platform uses.

A digest per file detects a change to a closed file. A **hash chain** detects a change to a log that's still growing: every record carries a sequence number, `seq`, and the SHA-256 of the line before it, `prev_hash`, so changing a record breaks the link to the next one, and removing one leaves a gap. `lib.audit.check` walks the chain and reports each break. A chain is tamper-evident, not tamper-proof. Schneier and Kelsey designed a log in which an attacker who takes over the logging machine can neither read nor falsify the entries written before. Even there, the attacker "can delete a block of entries (or the entire log file)", and the trusted party the log reports to notices only the next time the machine contacts it ([Schneier and Kelsey, 1999](https://www.schneier.com/wp-content/uploads/2016/02/paper-auditlogs.pdf)). A plain chain like the platform's is weaker: anyone who can write the file can rebuild it, renumbering as they go. So what it proves depends on its **head**, the number of records and the hash of the last one, written down where the log's writer can't change it. An edit to, or a removal of, any record up to that head shows, however it's hidden. After the head, a chain rebuilt or cut passes every check, and without a head, so does a chain rebuilt from the start. `check` takes the head as an anchor.

The example replays `lib.audit.DAY`, the 13 queries the platform received on Oct 1, and writes the head down at noon, at record 9. Then it tampers with copies of the log. Before noon, record 3, `agent-a05`'s lookup of a learner's contact details, is handed to another agent, once as a plain edit and once with the chain rebuilt. After noon, record 12, the denied read by `someone-else`, the user the platform doesn't know, is removed, once plainly and once with the chain rebuilt; and the day's last two records are cut off. Before you run it, predict which of the five the chain finds on its own, and which against the noon head.

Example `chain-catches-edit` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
import json

from lib import audit
from lib.catalog import open_catalog
from lib.platform import scratch

log = audit.Log(scratch() / "audit.jsonl")
platform = audit.Audited(open_catalog(["crm.learners", "learning.reviews", "billing.payments", "support.tickets"]), log)
audit.run_day(platform, [query for query in audit.DAY if query[0] < "12:00"])     # the morning
anchor = log.head()                               # the head, written down at noon somewhere the log's writer can't reach
audit.run_day(platform, [query for query in audit.DAY if query[0] >= "12:00"])    # the afternoon
lines = log.lines()
print("records:", len(lines))
print("head written down at noon, at record:", anchor["records"])
print("record 3:", json.loads(lines[2])["user"], "reads", json.loads(lines[2])["query"])


def rechained(lines: list[str]) -> list[str]:
    """The chain built again, every record renumbered and every prev_hash recomputed: what anyone who can rewrite the
    log's file can do."""
    rebuilt, previous = [], audit.GENESIS
    for seq, line in enumerate(lines, start=1):
        rebuilt.append(audit.canonical(json.loads(line) | {"seq": seq, "prev_hash": previous}))
        previous = audit.sha256(rebuilt[-1])
    return rebuilt


# Before noon, record 3 handed to another agent. After noon, record 12 (someone-else's denied read) removed, and the
# day's last two records cut off.
edited = lines[:2] + [audit.canonical(json.loads(lines[2]) | {"user": "agent-a01"})] + lines[3:]
removed = lines[:11] + lines[12:]
for name, version in [("untouched", lines), ("record 3 edited", edited), ("record 3 edited, chain rebuilt", rechained(edited)),
                      ("record 12 removed", removed), ("record 12 removed, chain rebuilt", rechained(removed)),
                      ("last 2 records removed", lines[:-2])]:
    print(f"{name}, checked alone:", "; ".join(audit.check(version)) or "no problem found")
    print(f"{name}, checked against the noon head:", "; ".join(audit.check(version, anchor)) or "no problem found")
```

Output:

```text
records: 13
head written down at noon, at record: 9
record 3: agent-a05 reads SELECT full_name, email, phone FROM crm.learners WHERE learner_id = ?
untouched, checked alone: no problem found
untouched, checked against the noon head: no problem found
record 3 edited, checked alone: record 3 was changed: record 4 doesn't follow it
record 3 edited, checked against the noon head: record 3 was changed: record 4 doesn't follow it
record 3 edited, chain rebuilt, checked alone: no problem found
record 3 edited, chain rebuilt, checked against the noon head: the chain no longer passes through the head written down at record 9
record 12 removed, checked alone: record 12 is missing: record 13 follows record 11
record 12 removed, checked against the noon head: record 12 is missing: record 13 follows record 11
record 12 removed, chain rebuilt, checked alone: no problem found
record 12 removed, chain rebuilt, checked against the noon head: no problem found
last 2 records removed, checked alone: no problem found
last 2 records removed, checked against the noon head: no problem found
```

On its own, the chain finds the plain edit, `record 3 was changed: record 4 doesn't follow it`, and the plain removal, `record 12 is missing: record 13 follows record 11`. It misses both rebuilt chains, which are consistent from start to end, and the cut, since no record follows the last one to notice. Against the noon head, it also finds the chain rebuilt before noon: `the chain no longer passes through the head written down at record 9`. Everything hidden after noon passes: against the noon head, the removal with the chain rebuilt gives `no problem found`, and the cut gives `no problem found`. A head protects only the records written before it.

This is why the [rule about values](#keep-values-out-of-the-record) isn't optional. Erasing a learner from a chained log means changing or removing a record, and wherever a check can see that, it can't tell it from tampering. A log that holds no data about learners never meets [chapter 7](#retention-consent-erasure)'s erasure. The IDs of the people who query are another matter: give the log a retention period, and start a new chain each period, with its last head written down, so that a whole period can be deleted when it expires.

Checking a chain means re-reading every record. Crosby and Wallach describe tree-shaped logs that can prove "that individual logged events are still present, and that the log, as seen now, is consistent with how it was seen in the past", with proofs "with logarithmic size and space, improving over previous linear constructions" ([Crosby and Wallach, 2009](https://www.usenix.org/legacy/event/sec09/tech/full_papers/crosby.pdf)). As a rule of thumb, we recommend a chain checked daily for one platform's own log, and a tree when outside parties audit a log too large to re-read.

**Working rule:** Chain every record to the one before with SHA-256 and a sequence number, and count on the chain to protect only the records up to the last head written down outside the layer's control. Write the head down often, to an append-only store or to another system under other credentials, as often as the number of unprotected records you can accept; if that number is zero, send each record off the machine as it's written. Check the chain against the last head on a schedule. If you need what AU-9(3) describes, have each head signed by a system whose key the layer never holds. Never chain a record that might one day have to be erased for one person; let whole periods expire instead.

## Cross-check the log against DuckDB's query log {#cross-check-the-query-log}

The platform's [audit log](#record-every-decision) records every query that goes through the enforcement layer, and only those. A query run on the layer's DuckDB connection directly, by a notebook helper or a test that was handed the connection, gets no decision and no record. Noticing it takes a second record, kept by the engine. DuckDB 2.0.0 has one, off by default: its logging framework includes a `QueryLog` type, which "Logs which queries are executed in DuckDB", turned on with `CALL enable_logging('QueryLog')` and read from the `duckdb_logs` view ([DuckDB, logging](https://duckdb.org/docs/2.0/operations_manual/logging/overview.html)). A separate setting, `log_query_path`, "Specifies the path to which queries should be logged" in a file ([DuckDB, configuration](https://duckdb.org/docs/2.0/configuration/overview.html)), which the layer's connection refuses, as the [section on production](#audit-in-production) shows.

DuckDB's log isn't an audit log. Each entry holds the SQL text, with connection, transaction and query IDs and a timestamp: no user, and no decision. It sees only the rewritten query, and it belongs to the process it records. What it can do is check the audit log: every query DuckDB ran should be the SQL that some decision record handed it. `Audited` turns DuckDB's log on and locks the connection's configuration when it starts. `Audited.check_engine_log` matches each query in DuckDB's log, by keyed digest, against the `rewritten_digest` of the records written since the last check, then empties DuckDB's log, which holds the queries' values. A relation's query runs "when a method of the Output section reads the relation, and it runs again on every read" ([DuckDB, relational API](https://duckdb.org/docs/2.0/clients/python/relational_api)), and a narrowed relation runs SQL of its own, which no record handed DuckDB. So `Audited.sql` fetches each result itself, once, and hands the rows back as a relation on a connection of its own: whatever the caller does with it, DuckDB's log holds each allowed query once.

On the platform, replay `lib.audit.DAY`, the day's 13 queries, and check. Then send two more queries through the layer, one its caller never fetches and one it narrows to five rows, read a learner's email through the layer's connection, around the layer, and check again:

Example `query-log-cross-check` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
from lib import audit
from lib.catalog import open_catalog
from lib.platform import scratch

log = audit.Log(scratch() / "audit.jsonl")
platform = audit.Audited(open_catalog(["crm.learners", "learning.reviews", "billing.payments", "support.tickets"]), log)
day = audit.run_day(platform)
print("queries allowed:", day["allowed"])
print("queries denied:", day["denied"])

# DuckDB's own query log, kept on the layer's connection, against the records written since the last check. The check
# then empties DuckDB's log, which holds the queries' values.
found = platform.check_engine_log()
print("queries DuckDB ran:", found["engine queries"])
print("queries DuckDB ran with no decision record:", len(found["unrecorded"]))

# Two more queries through the layer: one whose caller never fetches it, and one the caller narrows to five rows.
platform.sql("select learner_id, country from crm.learners", "analyst-1")
platform.sql("select learner_id, country from crm.learners", "analyst-1").limit(5).fetchall()
# Then a notebook helper that was handed the layer's connection reads a learner's email with it, around the layer.
platform.enforcer.connection.sql("select email from crm.learners where learner_id = 541").fetchall()
found = platform.check_engine_log()
print("next check, records checked:", " to ".join(map(str, found["records checked"])))
print("next check, queries with no decision record:", len(found["unrecorded"]))
for query in found["unrecorded"]:
    print("unrecorded:", query)
print("next check, decision records DuckDB has no query for:", len(found["not in the engine log"]))
```

Output:

```text
queries allowed: 9
queries denied: 4
queries DuckDB ran: 9
queries DuckDB ran with no decision record: 0
next check, records checked: 14 to 15
next check, queries with no decision record: 1
unrecorded: SELECT email FROM crm.learners WHERE learner_id = ?
next check, decision records DuckDB has no query for: 0
```

Of the day's queries, 9 were allowed and 4 denied, and DuckDB ran 9: one for each allowed query, none for the denied ones, and 0 without a record. The next check covers records 14 to 15, the two queries through the layer, and neither raises an alarm. The read around the layer shows up as 1 query with no decision record, printed without its values. The last line checks the other direction, records whose query DuckDB has no trace of: 0 here.

What the check catches depends on who holds the connection. It catches a read around the layer by code that leaves DuckDB's log alone, such as this notebook helper, a test, or a job handed the connection by mistake. It doesn't catch code that holds the connection and means to hide. A read made after a check, with DuckDB's log emptied again before the layer's next query, leaves nothing for either direction to find. And DuckDB's `write_log` function takes the log type as an argument, so it can write `QueryLog` entries ([DuckDB source, v2.0.0](https://github.com/duckdb/duckdb/blob/v2.0.0/src/function/scalar/system/write_log.cpp)); the configuration lock doesn't stop a function. A guarantee against such code needs the engine's log written outside the process that holds the connection.

The check also finds the layer's own shortcuts, such as [chapter 6](#test-who-sees-what)'s `observe`, which reads the stored table on the layer's connection with no user behind it. Give such queries records of their own, with the layer as the user, rather than exceptions in the check.

**Working rule:** Turn on the engine's own query log wherever you enforce policies, fetch every result inside the layer, and check the log on a schedule against the records written since the last check, in both directions: every query the engine ran must match a record, and every allowed record must match a query. Then empty it, since it keeps the queries' values. Treat a mismatch as an incident to explain, not noise to filter. Count on the check to catch mistakes, not code that holds the connection and means to hide: against that, only a log written outside the process helps. Never use the engine's log as the audit log: it has no user and no decision.

## Generate the access review from the log {#generate-the-access-review}

The platform's [audit log](#record-every-decision) says what each person read, and the policy says what each person may read; an access review puts the two side by side. SP 800-53 asks organizations to "Review accounts for compliance with account management requirements" (AC-2 j), and to "Review [Assignment: frequency] the privileges assigned to [Assignment: roles and classes] to validate the need for such privileges" and "Reassign or remove privileges, if necessary" (AC-6(7)) ([NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)). A list of who holds which role answers neither, because it says nothing about need. Code can compute the facts a review needs: what the policy allows each person, what the log shows they used, what they were denied, and memberships that point at nothing. Whether to remove access stays a decision for the data's owners.

`lib.audit.review` evaluates the platform's policy for every user in `users.toml` against every table, reads the log, and lists for each user the tables they may read, the tables they read, the grants they didn't use, their denied queries with the assistant that sent them, and anything someone should look at. To give it something stale to find, the example adds `analyst-2` to the users, still listed in `bi`, a group the policy no longer has, as happens when a group is retired and nobody edits the users file:

Example `access-review` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
from lib import audit, policy
from lib.catalog import open_catalog
from lib.platform import TABLES, scratch

log = audit.Log(scratch() / "audit.jsonl")
platform = audit.Audited(open_catalog(["crm.learners", "learning.reviews", "billing.payments", "support.tickets"]), log)
audit.run_day(platform)

# users.toml as the review finds it: analyst-2 is still listed in bi, a group the policy no longer has.
data = policy.data_document()
data["platform"]["users"]["analyst-2"] = {"groups": ["bi"]}
rows = audit.review(audit.bundle(data=data), log.records(), TABLES)      # all eight of the platform's tables

for row in rows:
    print(f"{row['user']}: may read {len(row['may read'])}, read {len(row['read'])}, denied {row['denied']}"
          + (f" (sent by {', '.join(row['denied via'])})" if row["denied via"] else ""))
    if row["unused"]:
        print("  not used:", ", ".join(row["unused"]))
    for finding in row["findings"]:
        print("  look at:", finding)
print("users reviewed:", len(rows))
print("grants not used:", sum(len(row["unused"]) for row in rows))
print("users to look at:", sum(bool(row["findings"]) for row in rows))
print("denied queries flagged at:", audit.settings()["review"]["denied_queries_flagged"])
```

Output:

```text
agent-a01: may read 2, read 0, denied 0
  not used: crm.learners, support.tickets
agent-a05: may read 2, read 2, denied 0
agent-a09: may read 2, read 0, denied 0
  not used: crm.learners, support.tickets
analyst-1: may read 6, read 2, denied 0
  not used: billing.payments, learning.courses, learning.enrollments, learning.events
analyst-2: may read 0, read 0, denied 0
  look at: in group bi, which the policy doesn't know
assistant-1: may read 2, read 1, denied 0
  not used: learning.courses
finance-1: may read 3, read 1, denied 0
  not used: learning.courses, learning.enrollments
instructor-17: may read 3, read 1, denied 3 (sent by assistant-1)
  not used: learning.courses, learning.enrollments
  look at: 3 denied queries
marketing-1: may read 2, read 1, denied 0
  not used: learning.courses
someone-else: may read 0, read 0, denied 1
  look at: not in users.toml
users reviewed: 10
grants not used: 14
users to look at: 3
denied queries flagged at: 3
```

Over Oct 1, the day `lib.audit.DAY` replays, 14 grants went unused, and `agent-a01` and `agent-a09` read nothing at all. One day is too short to remove anyone's access: support works in shifts, and finance reads some tables only when it closes the month. Over a review period, such as a quarter, a grant unused for the whole period is what to bring to the table's owner. 3 users need a person to look at them:

- `analyst-2` is in a group no rule knows. The membership grants nothing today, and would grant whatever a future rule for `bi` allows, so remove it.
- `someone-else` isn't in `users.toml`, so a principal the platform doesn't know tried to read learners' emails.
- `instructor-17`'s line reads `may read 3, read 1, denied 3 (sent by assistant-1)`. In the two minutes after answering the instructor's first question, the assistant tried learners, then learners joined to reviews, then tickets. That is an assistant trying tables one by one, and without `via` the review would have blamed the instructor.

The threshold for flagging, 3 denied queries, is a rule of thumb, kept in `governance/audit.toml` with its reasoning, so that changing it is a reviewed change like any change to the policy.

**Working rule:** Generate access reviews from the policy and the audit log, never from a list of role memberships: what each person may read against what they read, their denials, and memberships the policy no longer knows. Run them over a period long enough for every job's rhythm, such as a quarter, and send each finding to the owner of the table or group it concerns. Remove a grant nobody used in the period unless its owner says why it's needed.

## Produce evidence as data {#produce-evidence-as-data}

The [chain check](#chain-the-records), the [cross-check](#cross-check-the-query-log) and the [access review](#generate-the-access-review) are worth most when someone outside the team can check them. The EU's General Data Protection Regulation (GDPR) puts that duty on the organization, as its accountability principle: "The controller shall be responsible for, and be able to demonstrate compliance with, paragraph 1 (‘accountability’)" ([GDPR, Article 5(2)](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). What counts as demonstrating is a question for lawyers; this section shows what code can produce. NIST's assessment procedures for account management list records to examine, among them "access authorization records", "account management compliance reviews" and "system audit records" ([NIST SP 800-53A Rev. 5, in NIST's OSCAL catalog](https://github.com/usnistgov/oscal-content/blob/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json)). A screenshot of a console is none of these: nobody can run it again, compare it with last quarter's, or tell which policy it showed.

`lib.audit.evidence` builds the platform's report from records and code, in these sections:

- the policy, with the digest of each module and of the data document;
- the policy's unit tests, from [chapter 5](#unit-test-the-policy-in-rego);
- the who-sees-what table, checked against the policy;
- classification coverage, from [chapter 2](#test-the-catalog-against-the-metadata)'s metadata checks;
- the audit log's chain check;
- the cross-check against DuckDB's log;
- the erasures the log records;
- the access review.

Every section names the policy revision it was computed under, the digests of its inputs, and what anyone needs to compute it again: the archived bundle, the test files, `metadata.toml` and the tables' schemas, the audit log. The engine cross-check can be computed again only in part, and says so. It keeps the keyed digest of every query DuckDB ran, so anyone holding the audit log can redo its two counts, but only the layer could read DuckDB's log, once, before emptying it. Generate the report for the platform on Oct 1, with every table and pipeline output in the catalog, [chapter 7](#retention-consent-erasure)'s erasure of a learner logged at 07:00, and the day's queries:

Example `evidence-report` (Python 3.12.15 · duckdb 2.0.0 · openlineage-python 1.55.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
import json
from datetime import timedelta

from lib import audit, retention
from lib.platform import scratch

# The platform on Oct 1: every table and pipeline output, chapter 7's erasure of learner 3590 at 07:00, then the day's
# queries through the audited layer.
catalog, graph = retention.open_platform(statistics_off=True)
log = audit.Log(scratch() / "audit.jsonl")
_, found, done = retention.erase_everywhere(catalog, graph, 3590, "erasure-0001", min_age=timedelta(0))
audit.record_erasure(log, "erasure-0001", done, retention.scan(catalog, found), at=audit.MIDNIGHT.replace(hour=7))
platform = audit.Audited(catalog, log)
audit.run_day(platform)

# The first report, so there's no head from an earlier one to check the chain against.
report = audit.evidence(platform, catalog, anchor=None)
reports = scratch()          # in production, another system, which the log's writer can't change
(reports / "evidence-2026-10-01.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
result = {name: section["result"] for name, section in report.items()}
print("sections:", ", ".join(report))
print("policy tests passed:", f"{result['policy tests']['passed']} of {result['policy tests']['of']}")
print("who-sees-what cases the policy agrees with:", f"{result['who sees what']['agree']} of {result['who sees what']['of']}")
for problem in result["classification coverage"]["problems"]:
    print("classification problem:", problem)
print("audit log records:", result["audit log"]["records"])
print("chain problems, checked alone:", len(result["audit log"]["chain problems"]))
print("queries DuckDB ran with no decision record:", len(result["engine cross-check"]["unrecorded"]))
print("decision records DuckDB has no query for:", len(result["engine cross-check"]["not in the engine log"]))
for erasure in result["erasures"]:
    print(f"erasure {erasure['request']}: {erasure['rows_deleted']} rows deleted, "
          f"{erasure['files_holding_the_person']} of {erasure['files_read']} files hold the person")
    for kept in erasure["kept"]:
        print(f"erasure {erasure['request']}, kept under an exception: {kept['table']}, decided by {kept['decided_by']},",
              f"{', '.join(kept['columns_erased'])} erased")
print("chain head written down, at record:", report["audit log"]["inputs"]["head"]["records"])
print("engine cross-check, computed again from:", "; ".join(report["engine cross-check"]["computed again from"]))
print("engine cross-check, not computed again:", report["engine cross-check"]["not computed again"])
```

Output:

```text
sections: policy, policy tests, who sees what, classification coverage, audit log, engine cross-check, erasures, access review
policy tests passed: 12 of 12
who-sees-what cases the policy agrees with: 12 of 12
classification problem: ai.review_corpus: no metadata
classification problem: marketing.audience: no metadata
audit log records: 14
chain problems, checked alone: 0
queries DuckDB ran with no decision record: 0
decision records DuckDB has no query for: 0
erasure erasure-0001: 25 rows deleted, 0 of 115 files hold the person
erasure erasure-0001, kept under an exception: billing.payments, decided by legal team, card_number erased
chain head written down, at record: 14
engine cross-check, computed again from: the audit log; the engine digests, for the two counts
engine cross-check, not computed again: the reading of DuckDB's log, and the unrecorded queries' shapes: the layer read that log once, then emptied it
```

The policy passes 12 of 12 unit tests and agrees with 12 of 12 who-sees-what cases. Classification coverage isn't clean, and the report says so: `ai.review_corpus` and `marketing.audience` have no metadata, the gaps that [chapters 2](#a-catalog-you-can-test) and [4](#lineage-from-pipelines) found and that the policy meanwhile treats as sensitive. A report that can only show passing checks is evidence of nothing. The chain has 0 problems, checked alone, since no earlier report wrote a head down. DuckDB ran 0 queries without a decision record, and 0 records have no query.

The erasure's lines, `25 rows deleted, 0 of 115 files hold the person` and `billing.payments, decided by legal team, card_number erased`, come from chapter 7's erasure, as the audit log records it: the request's ID, the tables, the counts, each table an exception kept with the reason `governance/retention.toml` gives, and the scan's result, never the learner's ID or values, so the record is safe to chain. The European Data Protection Board recommends that controllers "Verify that erasure has been carried out and be able to demonstrate such erasure" ([EDPB, 2026](https://www.edpb.europa.eu/system/files/2026-02/edpb_cef-report_2025_right-to-erasure_en.pdf)); this line records what the platform's own scan found. The report also writes down the chain's head, at record 14. Kept in another system, it is the anchor the next report checks the chain against: an edit to, or a removal of, any record up to it will show then, and a later record is protected only once a later head covers it.

The report claims nothing about any law or framework. It states what was checked, under which policy, from which inputs, and with what result.

**Working rule:** Generate evidence from records with code, on a schedule and on every policy change, and stamp each section with the policy revision, the digests of its inputs and what it takes to compute it again, saying which parts nobody can. Keep the reports where the log's writer can't change them, include failing findings rather than filtering them out, and let each report check the chain against the head the last one wrote down. Never send a screenshot where a report can be generated; [chapter 10](#governance-in-ci) runs checks like these on every pull request.

## What goes wrong in production {#audit-in-production}

An audit trail fails quietly: nothing breaks when it stops being complete, true or read. The failure that matters most is logging that the audited code can switch off, and DuckDB's query log is that kind: it belongs to the process it records. The example sets up two enforcement layers. The first doesn't lock its configuration, like any layer built without `lib.audit`; code holding its connection tries to log to a file, switches the log off, then reads a learner's email around the layer. The second is `lib.audit`'s, locked; the same kind of code tries to switch the log off, reads around the layer, then empties the log:

Example `query-log-switched-off` (Python 3.12.15 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2 · sqlglot 30.30.0), passing in Edition 2026.11.22:

```python
import duckdb

from lib import audit
from lib.catalog import open_catalog
from lib.platform import scratch

AROUND = "select email from crm.learners where learner_id = 541"       # a read around the enforcement layer
folder = scratch()

# A layer that doesn't lock its configuration: code holding its connection tries a file log, then switches logging off.
unlocked = audit.Audited(open_catalog(["crm.learners"]), audit.Log(folder / "unlocked.jsonl"), lock=False)
connection = unlocked.enforcer.connection
try:
    connection.execute("set log_query_path = 'queries.log'")
except duckdb.Error as error:
    print("a query log in a file, on the layer's connection:", type(error).__name__)
connection.execute("CALL disable_logging()")
connection.sql(AROUND).fetchall()
for query in unlocked.check_engine_log()["unrecorded"]:
    print("unlocked, unrecorded:", query)

# lib.audit's layer locks its configuration: switching the log off is refused, but emptying it isn't.
log = audit.Log(folder / "locked.jsonl")
locked = audit.Audited(open_catalog(["crm.learners"]), log)
locked.sql("select learner_id, email from crm.learners", "analyst-1").fetchall()
connection = locked.enforcer.connection
try:
    connection.execute("CALL disable_logging()")
except duckdb.Error as error:
    print("locked, disable_logging():", type(error).__name__)
connection.sql(AROUND).fetchall()
connection.execute("CALL truncate_duckdb_logs()")
found = locked.check_engine_log()
print("locked, after truncate_duckdb_logs(), queries with no decision record:", len(found["unrecorded"]))
print("locked, decision records DuckDB has no query for:", len(found["not in the engine log"]))
```

Output:

```text
a query log in a file, on the layer's connection: PermissionException
unlocked, unrecorded: CALL disable_logging()
unlocked, unrecorded: SET log_query_path = ?
locked, disable_logging(): InvalidInputException
locked, after truncate_duckdb_logs(), queries with no decision record: 0
locked, decision records DuckDB has no query for: 1
```

A log in a file is refused with a `PermissionException`, because [chapter 6](#find-what-a-query-reads) forbids the layer's connection to touch files. On the unlocked layer, `disable_logging()` works, and the read that follows leaves no trace. All the [cross-check](#cross-check-the-query-log) finds is the statements before the silence: the refused `SET log_query_path`, and `CALL disable_logging()` itself. On the locked layer, switching off fails with an `InvalidInputException`, but `truncate_duckdb_logs()` works, and afterwards the check finds 0 unrecorded queries. The check in the other direction notices the gap: 1 decision record has no query in DuckDB's log, so something emptied the log. It notices only because a record fell in the emptied stretch; code that writes entries back with `write_log` would leave the log looking whole.

None of this stops code that holds the connection. In production, enforce in an engine that runs as a service of its own, such as Trino with OPA, so that its log is written outside the process of anyone who queries it. Store the audit records on another system, as control AU-9(2) asks: "Store audit records [Assignment: frequency] in a repository that is part of a physically different system or system component than the system or component being audited" ([NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)). We recommend sending each record as it's written, and holding the chain's head somewhere else again.

Other failures to watch for:

- **Logs nobody reads.** NIST's guide to log management makes the case for reading them: "Routine log reviews and analysis are beneficial for identifying security incidents, policy violations, fraudulent activity, and operational problems shortly after they have occurred" (§2.2, [NIST SP 800-92](https://doi.org/10.6028/NIST.SP.800-92)). A log that is only written costs storage and protects nothing. Schedule the access review and the evidence report, give every finding an owner, and alert on what can't wait for a quarter, such as a user flagged for denied queries.
- **Decisions that can't be explained after a policy changed.** A record without a policy revision, or a revision without an archived bundle, replays under the current policy and contradicts itself. Fingerprint the data document with the rules, since a change to the data document changes decisions as surely as a change to the rules.
- **Logs that hold personal data.** Personal data reaches logs by many routes: query literals, the engine's own query log, error messages that print values, as [chapter 6](#column-masks-leak) showed for DuckDB's cast errors, and the layer's debugging output. A parser's warnings are one more: sqlglot's warning when it keeps a statement as text quotes the statement ([sqlglot source, v30.24.0](https://github.com/tobymao/sqlglot/blob/v30.24.0/sqlglot/parser.py)), so `lib.audit` silences sqlglot while it parses a user's query. Keep the audit log to IDs and digests, and give every other log a retention period that erasure reaches.
- **A decision log that isn't complete.** OPA can drop decision events by rule, through `system.log.drop`, and "OPA will drop events if the rate limit is exceeded" ([OPA, decision logs](https://www.openpolicyagent.org/docs/management-decision-logs)). Count the engine's queries against the decision records, as the cross-check does, rather than assume every decision was logged.
- **A head kept next to the log.** An anchor stored where the log's writer can change it detects nothing the chain doesn't. Keep it in another system, under other credentials.

## What this chapter decided {#audit-decisions}

- **One record per query, written by the enforcement layer before the query runs.** `lib.audit.Audited` wraps chapter 6's `Enforcer` without changing it, and fetches each result itself. The record covers AU-3's six items, the principal and the assistant that sent the query among them.
- **Records hold IDs, never values.** Every literal, in any of DuckDB's syntaxes, and every name the catalog doesn't hold is replaced, in the query and in the denial's reason, and comments are removed. The SQL DuckDB ran is kept as an HMAC-SHA256 digest under a key only the layer holds, since with the key the digest confirms a guess. Erasures are recorded by request ID.
- **Every record names its policy revision,** the SHA-256 of the policy's modules and data document, and every revision is archived for replay.
- **Records are chained with SHA-256 and numbered,** and the chain protects only the records up to the last head written down outside the layer's control. Each evidence report writes the head down; we recommend doing it more often.
- **DuckDB's query log is a cross-check for mistakes, not the audit log.** The layer turns it on, locks its configuration, checks it both ways against the records since the last check, then empties it. Code holding the connection can defeat it.
- **Access reviews and evidence reports are generated** from the policy, the log and the catalog, each section stamped with its policy revision and inputs. The threshold for flagging denied queries, 3, is a rule of thumb in `governance/audit.toml`.
