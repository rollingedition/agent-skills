---
title: "Data Governance as Code"
chapter: "Access policies as code"
chapter_id: access-policies-as-code
book: data-governance-as-code
edition: 2026.11.27
verified: 2026-11-14
edition_code: 2QX0-VKZT
canonical: https://rollingedition.com/data-governance-as-code/access-policies-as-code
license: CC BY 4.0
attribution: "“Access policies as code,” chapter 5 of Data Governance as Code, Edition 2026.11.27, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/access-policies-as-code. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Access policies as code

By the end of this chapter you can write a data platform's access rules as one policy that denies by default and returns row filters and column masks as data. The policy allows by role and narrows by attribute, and an engine can apply its whole decision. You'll write it in Rego, the policy language of Open Policy Agent (OPA), test it the way `opa test`, OPA's test runner, does, check it against a who-sees-what table that the data's owners can read, know where the in-process engine this book uses differs from OPA, and see the same rules in Cedar, a narrower policy language.

Each group that reads the platform's warehouse, from support agents to its course assistant, needs something different. Support agents each serve one region, `americas`, `emea` or `apac`, and need learners' contact details to answer tickets. Instructors see the learners and reviews of their own courses, without contact details. Marketing may reach only learners who agreed to marketing email. Finance reconciles payments, and the legacy `card_number` column of `billing.payments` must never show more than its last four digits. Data scientists see `learner_id` as stored, to join tables on it, with personal columns pseudonymized and free text redacted. The course assistant reads only the reviews whose authors agreed to AI training. [Chapter 1](#governance-end-to-end) showed one rule, support agents see only their own region, and enforced it on one query. Rules for every group need to live in one place, stated exactly, and tested before anyone relies on them.

This chapter's terms are the ones the rest of the book uses. A **policy** is code that answers whether a request may go ahead; its answer is a **decision**. The **principal** is who asks, a **role** is a group of principals with the same job, and an **attribute** is any other fact a rule reads, about the principal, the data or the request. A **row filter** limits which rows a query returns, and a **column mask** changes how a column's values are shown, such as **pseudonymization**, which replaces an identifier with a consistent stand-in.

The platform's policy is `governance/policies/access.rego`, and its tests are in `governance/policies/access_test.rego`. The book's shared module `lib.policy` loads both into regopy 1.5.2, the Python binding of rego-cpp, Microsoft's C++ implementation of Rego, which evaluates policies inside the Python process with no server to run.

## Shape the request like Trino's {#shape-the-request-like-trinos}

A policy engine answers questions about requests, so the shape of a request decides which systems can ask it. OPA's premise is that policy is taken out of the service that enforces it: OPA "lets you decouple policy from that software service", so that it can be read, versioned and tested on its own ([OPA philosophy](https://www.openpolicyagent.org/docs/philosophy)). The service sends a JSON document describing the request, and the policy reads it as `input`. Trino, an open-source SQL engine, does exactly this: for each access check a query needs, its OPA plugin sends a document with `context.identity`, the user and their groups, and `action`, the operation and the resource, down to the catalog, schema, table and columns ([Trino 484, OPA access control](https://trino.io/docs/484/security/opa-access-control.html)).

The platform's policy reads the same fields, so it decides Trino's request to read columns, `SelectFromColumns`, as Trino sends it. Trino needs more than that one decision. It wants each row filter and column mask as SQL, a row filter as `{"expression": "clause"}`, where the policy returns a column and a value ([Trino 484, OPA access control](https://trino.io/docs/484/security/opa-access-control.html)). It also asks about other checks, such as `ExecuteQuery` and `AccessCatalog`, which this policy's `allow` denies ([`OpaAccessControl.java` at Trino 484](https://github.com/trinodb/trino/blob/484/plugin/trino-opa/src/main/java/io/trino/plugin/opa/OpaAccessControl.java)). [Chapter 6](#engine-enforcement) shows what a module beside the policy has to return for them. `lib.policy.request` builds the platform's requests in Trino's shape, and the next example uses it for an `emea` support agent, `agent-a05`, reading three columns of `support.tickets`:

Example `trino-shaped-request` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""The request a support agent's read sends the policy, shaped as Trino's OPA plugin sends it. The point rests on the printed `action`: the operation SelectFromColumns, and the table with the columns the query reads."""
import json

from lib import policy

# A support agent's query reads three columns of the tickets table: the request Trino's OPA plugin would send for it.
# no groups here, because the policy reads them from users.toml; no purpose either, since request adds one only when given
request = policy.request("agent-a05", "support.tickets", ["ticket_id", "opened_at", "body"])
print(json.dumps(request, indent=2))
```

Output:

```text
{
  "context": {
    "identity": {
      "user": "agent-a05"
    }
  },
  "action": {
    "operation": "SelectFromColumns",
    "resource": {
      "table": {
        "catalogName": "platform",
        "schemaName": "support",
        "tableName": "tickets",
        "columns": [
          "ticket_id",
          "opened_at",
          "body"
        ]
      }
    }
  }
}
```

The operation is `SelectFromColumns`, Trino's name for a read, and the table sits under `action.resource.table` with its catalog, schema, name and the columns the query touches. The platform's request differs from Trino's in two places that matter. It leaves out `context.identity.groups`, because the policy looks a user's groups up in the same file as their attributes, `governance/users.toml`, so the tests and the policy read one source of truth. And it may carry a top-level `purpose`, such as `ai-training`, which Trino doesn't send. Behind Trino, we recommend deriving the purpose from the identity, for instance by giving the training pipeline a service user of its own, rather than trusting a value the client sets.

**Working rule:** Shape the policy's input like the requests of the engine that will enforce it, field for field, and add only what that engine can't send, at the top level where a reviewer sees it. If your engine isn't Trino, start from its request format instead, and keep the shape in one function, as `lib.policy.request` does, so tests and callers can't drift apart.

## Generate the data the policy reads {#generate-the-data-the-policy-reads}

The [request](#shape-the-request-like-trinos) says who asks for what. Everything else a rule needs, such as each user's groups and each column's classification, comes from a second document, which OPA calls `data`. A fact in that document is only as current as its source, and every fact the platform's policy reads already has an owner. Users and their attributes live in `governance/users.toml`. Each column's classification lives in `governance/metadata.toml`, the reviewed metadata file that [chapter 2](#key-column-metadata-by-field-id) keys by Iceberg field ID. And which instructor teaches which course is in the `learning.courses` table itself. Typing any of these into the policy, or copying them into a second file, makes a copy that someone has to remember to update.

`lib.policy.data_document` builds the document from those three sources each time a policy is loaded, and never from anything typed:

Example `generated-policy-data` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""The data the policy reads besides the request, built from the files that own each fact. The point rests on the last two lines: instructor 17's courses come from learning.courses, not from anything typed."""
from lib import policy

# What the policy reads besides the request, built from the files that own each fact.
# the document's one top-level key, which the policy reads as data.platform
data = policy.data_document()["platform"]

print("users, from governance/users.toml:", len(data["users"]))
print("agent-a05:", data["users"]["agent-a05"])
print("instructor-17:", data["users"]["instructor-17"])

classifications = data["classifications"]
print("tables, from governance/metadata.toml:", len(classifications))
print("columns classified:", sum(len(columns) for columns in classifications.values()))
print("crm.learners.email:", classifications["crm.learners"]["email"])
print("billing.payments.card_number:", classifications["billing.payments"]["card_number"])

courses = data["instructor_courses"]
print("instructors with courses, from learning.courses:", len(courses))
# instructor IDs are string keys in the document, so the lookup is "17"
print("instructor 17's courses:", courses["17"])
```

Output:

```text
users, from governance/users.toml: 8
agent-a05: {'groups': ['support'], 'region': 'emea'}
instructor-17: {'groups': ['instructor'], 'instructor_id': 17}
tables, from governance/metadata.toml: 10
columns classified: 77
crm.learners.email: personal
billing.payments.card_number: sensitive
instructors with courses, from learning.courses: 48
instructor 17's courses: [2, 75, 80, 87, 103, 134]
```

Each fact in the document comes from the file or table that owns it, and the output labels each count with its source: the users in `governance/users.toml`, the classified columns across the tables in `governance/metadata.toml`, and the instructors in `learning.courses`. `agent-a05` has a group and a region, and `instructor-17` a group and an instructor ID, but nothing in `users.toml` says which courses instructor 17 teaches. The document finds [2, 75, 80, 87, 103, 134] in `learning.courses`. When the platform publishes another of their courses, the instructor's row filter includes it the next time the policy's data is generated, with no edit anywhere. A classification works the same way: changing `card_number` from `sensitive` would take one reviewed change to `metadata.toml`, and the policy would follow.

**Working rule:** Generate the policy's data from the file or table that owns each fact, every time you load the policy, and never copy a fact into the policy or into a second file. When a fact has no owner yet, such as a support agent's region, give it one file, reviewed like code, as the platform does with `users.toml`.

## Deny by default, then allow by role {#deny-by-default-then-allow-by-role}

With the [request](#shape-the-request-like-trinos) and its [data](#generate-the-data-the-policy-reads) in place, the first thing a policy must settle is what happens to a request no rule anticipated. Saltzer and Schroeder's principle of fail-safe defaults gives the answer: "Base access decisions on permission rather than exclusion" ([Saltzer and Schroeder, 1975](https://web.mit.edu/Saltzer/www/publications/protection/Basic.html)). In Rego, that is a default value. A rule whose body never evaluates to true has no value, which Rego calls **undefined**, and OPA uses the default when every rule sharing a name is undefined ([OPA policy language](https://www.openpolicyagent.org/docs/policy-language)). So with `default allow := false`, a request that no `allow` rule matches is denied, whoever sends it and whatever it asks for.

Role-based access control, first formalized by [Ferraiolo and Kuhn in 1992](https://csrc.nist.gov/files/pubs/conference/1992/10/13/rolebased-access-controls/final/docs/ferraiolo-kuhn-92.pdf), grants access by the job a principal holds rather than by who they are. On the platform, a role is a group in `users.toml`, and the policy's `readable` object maps each group to the tables it may read. A request is allowed when it's a read, some group of the user may read the table, and nothing the group's row filters depend on is missing:

```rego
default allow := false

allow if {
	input.action.operation == "SelectFromColumns"
	readable_by_a_group
	not missing_attribute
}
```

The last line guards against a failure that [the section on production](#policies-in-production) shows by removing it. Print the map and decide four requests to see the default at work:

Example `allow-by-role` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""Which groups may read which tables, then four requests decided by the default-deny policy. The points rest on the four decisions and their reasons, printed last."""
from lib import policy

rego = policy.interpreter()

# The groups the policy knows, and the tables each may read: the role part of the policy.
readable = policy.evaluate(rego, "data.platform.access.readable", {})
for group, tables in readable.items():
    print(f"{group} may read:", ", ".join(tables))

# Who may read what. Anything no rule allows is denied, including a user or an operation the policy has never seen.
requests = [
    policy.request("finance-1", "billing.payments", ["amount"]),
    policy.request("marketing-1", "billing.payments", ["amount"]),
    policy.request("someone-else", "crm.learners", ["learner_id"]),
]
delete = policy.request("finance-1", "billing.payments", ["amount"])
# the same request as finance's read, asking to delete instead
delete["action"]["operation"] = "DeleteFromTable"
for request in requests + [delete]:
    decision = policy.decide(request, rego)
    who, table = request["context"]["identity"]["user"], request["action"]["resource"]["table"]
    print(f"{who}, {request['action']['operation']} on {table['schemaName']}.{table['tableName']}:",
          "allowed" if decision["allow"] else "denied", "|", "; ".join(decision["reasons"]))
```

Output:

```text
ai may read: learning.courses, learning.reviews
data-science may read: analytics.course_performance, analytics.learner_activity, billing.payments, crm.learners, learning.courses, learning.enrollments, learning.events, learning.reviews
finance may read: billing.payments, learning.courses, learning.enrollments
instructor may read: learning.courses, learning.enrollments, learning.reviews
marketing may read: crm.learners, learning.courses, marketing.audience
support may read: crm.learners, support.tickets
finance-1, SelectFromColumns on billing.payments: allowed | finance may read billing.payments
marketing-1, SelectFromColumns on billing.payments: denied | no group of this user may read this table
someone-else, SelectFromColumns on crm.learners: denied | no group of this user may read this table
finance-1, DeleteFromTable on billing.payments: denied | DeleteFromTable is not an operation this policy allows
```

Only what a rule grants is allowed. Finance may read `billing.payments`, and the reason names the group that allowed it. Marketing may not, and neither may `someone-else`, a user the policy has never heard of, because nothing grants either of them anything. The fourth request is finance again, asking to delete rather than read. No rule mentions `DeleteFromTable`, so it's denied too, and the reason says why. A policy that tried to list what is forbidden would have needed a rule for that operation; this one needs none. Every decision carries its reasons, so a denial can be explained to the person who got it, and logged.

**Working rule:** Start every policy with `default allow := false`, and allow only through rules that name the role and the resource. Keep the map from roles to tables in one place, where a reviewer can read all of it in one sitting, and give every decision a reason. When a request is denied that should have been allowed, add a rule that allows it; never weaken the default.

## Narrow by attribute: region, consent and purpose {#narrow-by-attribute}

[Roles](#deny-by-default-then-allow-by-role) say which tables a group may read; they can't say which rows. NIST's guide to attribute-based access control defines the general approach, in which access is decided by attributes of the subject, the object, the requested operations and, sometimes, the environment. It treats a role as one such attribute ([NIST SP 800-162](https://doi.org/10.6028/NIST.SP.800-162)). The alternative, a role for every combination, is what the same guide calls "role explosion".

The platform shows why. Support by region would need three support roles, and adding marketing's consent and a purpose for AI training would multiply the roles again. Instead, the policy keeps one role per job and reads three attributes. The **region** is an attribute of the principal, from `users.toml`. **Consent** is an attribute of the data: the learner's `marketing_consent` and `ai_training_consent` columns in `crm.learners`. The **purpose** is an attribute of the request. Each one becomes a row filter, a structured condition on a column that the engine adds to the query. The support agent's filter reads the agent's region:

```rego
row_filters contains {"column": "support_region", "equals": user.region} if {
	"support" in groups
	table in {"crm.learners", "support.tickets"}
}
```

Reads by support agents, an instructor, marketing and a data scientist show what each attribute does, with the data scientist reading reviews twice, once with no purpose and once for `ai-training`:

Example `attributes-as-row-filters` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""Row filters the policy builds for seven reads, from three attributes: the agent's region, the learner's consent and the request's purpose. The points rest on the analyst's two review reads, with and without a purpose."""
import json

from lib import policy

rego = policy.interpreter()

# Region is the agent's attribute, consent the learner's, and purpose the request's. Each becomes a row filter.
reads = [
    ("agent-a01", "support.tickets", ["ticket_id"], None),
    ("agent-a05", "support.tickets", ["ticket_id"], None),
    ("agent-a09", "support.tickets", ["ticket_id"], None),
    ("instructor-17", "learning.reviews", ["rating"], None),
    ("marketing-1", "crm.learners", ["email"], None),
    ("analyst-1", "learning.reviews", ["rating", "body"], None),
    # the same read with a purpose, the one attribute the requester supplies
    ("analyst-1", "learning.reviews", ["rating", "body"], "ai-training"),
]
for user, table, columns, purpose in reads:
    decision = policy.decide(policy.request(user, table, columns, purpose), rego)
    who = user + (f" for {purpose}" if purpose else "")
    # json shows the consent filter with its learner_consented key, not a column
    print(f"{who} reads {table}, row filters:", json.dumps(decision["row_filters"]))
    if "body" in columns:
        print(f"{who} reads {table}, body shown as:", decision["column_masks"]["body"])
```

Output:

```text
agent-a01 reads support.tickets, row filters: [{"column": "support_region", "equals": "americas"}]
agent-a05 reads support.tickets, row filters: [{"column": "support_region", "equals": "emea"}]
agent-a09 reads support.tickets, row filters: [{"column": "support_region", "equals": "apac"}]
instructor-17 reads learning.reviews, row filters: [{"column": "course_id", "in": [2, 75, 80, 87, 103, 134]}]
marketing-1 reads crm.learners, row filters: [{"column": "marketing_consent", "equals": true}, {"column": "status", "equals": "active"}]
analyst-1 reads learning.reviews, row filters: []
analyst-1 reads learning.reviews, body shown as: redact
analyst-1 for ai-training reads learning.reviews, row filters: [{"learner_consented": "ai_training_consent"}]
analyst-1 for ai-training reads learning.reviews, body shown as: redact_contacts
```

The purpose is what changes a data scientist's view of review text. Without one, every review is visible, but the text, `body`, is shown as `redact`. For `ai-training`, only the reviews of learners who agreed to AI training remain, and the text comes back as `redact_contacts`, with contact details taken out. The three agents get the same rule with one value per region, from one role, and instructor 17's filter lists their courses, generated from `learning.courses`. Marketing gets two filters, consent given and account active, and an engine applies both. The AI-training filter, `learner_consented`, tests the review's author, not the review, so enforcing it takes a join to `crm.learners`. A learner who signed up before the platform asked about AI training has no answer in `ai_training_consent`, according to the platform's data card, so enforcing the filter has to count an unknown answer as a no.

The purpose is the one attribute the requester supplies, so it reveals more only under a narrower condition: stating `ai-training` shows review text, but only for consenting learners and without contact details. Leaving it out, or giving any other purpose, gets what the role allows anyway, with the text hidden.

**Working rule:** Model each condition as an attribute of the principal, the data or the request, read by one rule per role, rather than as another role. When an attribute comes from the requester, as a purpose does, let it unlock access only under a narrower condition, so that leaving it out, or getting it wrong, falls back to what the role allows anyway.

## Return the decision as one document {#return-the-decision-as-one-document}

A yes or no can't carry the [row filters](#narrow-by-attribute) that attributes produce. A Rego decision needn't be yes or no, because OPA policies can represent decisions as structured data, from booleans to maps of lists of maps ([OPA philosophy](https://www.openpolicyagent.org/docs/philosophy)). The platform's policy uses that to return its whole answer as one document, `data.platform.access.decision`, with four keys: `allow`, the `row_filters`, the `column_masks`, and the `reasons`. `lib.policy.decide` asks for it with one query and returns it as a Python dictionary.

The filters and masks are data, never SQL. A filter names a column and a value or a list of values, or, for consent, the learner's consent column. A mask is a name, one of `redact`, `last4`, `pseudonymize` and `redact_contacts`. Whatever enforces the decision turns each into SQL with its own code, so nothing a request or a user record contains, such as a region typed into `users.toml`, can reach a query as SQL text. Masks follow each column's classification. Sensitive columns are hidden from everyone, except the last four digits of a card number, which finance sees. Personal columns are shown to support, which needs contact details, and masked for everyone else as their job requires. And a column the metadata doesn't classify counts as sensitive:

```rego
classification(column) := level if {
	level := data.platform.classifications[table][column]
} else := "sensitive"
```

Take marketing reading four columns of `crm.learners`, three of them classified in the metadata. The fourth, `linkedin_url`, stands for a column a pipeline has added and nobody has classified yet:

Example `one-decision-document` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""The whole decision for one read: marketing's four columns of crm.learners, one of them unclassified. The point rests on the masks and the reasons, which give one line per mask and per group that allowed the read."""
import json

from lib import policy

# Marketing reads four columns of crm.learners. `linkedin_url` stands for a column added to the table and not yet
# classified in governance/metadata.toml.
request = policy.request("marketing-1", "crm.learners", ["full_name", "email", "phone", "linkedin_url"])
# with no interpreter given, decide loads the platform's policy itself
decision = policy.decide(request)
print(json.dumps(decision, indent=2))
print("keys:", ", ".join(sorted(decision)))
```

Output:

```text
{
  "allow": true,
  "column_masks": {
    "linkedin_url": "redact",
    "phone": "redact"
  },
  "reasons": [
    "linkedin_url is sensitive, shown as redact",
    "marketing may read crm.learners",
    "phone is personal, shown as redact"
  ],
  "row_filters": [
    {
      "column": "marketing_consent",
      "equals": true
    },
    {
      "column": "status",
      "equals": "active"
    }
  ]
}
keys: allow, column_masks, reasons, row_filters
```

Marketing gets the read, with its two row filters, and two of the four columns are masked. `phone` is personal, and marketing doesn't need it for email. `linkedin_url` is unclassified, so it's treated as sensitive until someone reviews it. `full_name` and `email` have no mask, and a column without a mask is shown as stored, which marketing needs to send an email. The reasons give one line per group that allowed the read and one per mask, so the document explains itself. A denial carries empty filters and masks, because the policy builds the two outcomes with two separate rules, so nothing downstream can mistake a denial for a read with some columns masked.

**Working rule:** Return one decision document per request, holding the allow, the row filters, the column masks and the reasons, and read it as a whole. Keep filters and masks as names and values that your enforcement code translates, never as SQL that the policy writes. If an engine needs SQL from the policy, as Trino does for its row filters and column masks ([Trino 484, OPA access control](https://trino.io/docs/484/security/opa-access-control.html)), generate it in one tested function between the two.

## Unit-test the policy in Rego {#unit-test-the-policy-in-rego}

The [decision document](#return-the-decision-as-one-document) is what a test can compare, which matters because a policy decides who sees personal data, and a change to it can widen access without anyone seeing it in a diff. OPA's answer is tests written in Rego: a test is a rule whose name is prefixed with `test_`, and "If the test rule is undefined or generates a non-true value the test result is reported as FAIL" ([OPA policy testing](https://www.openpolicyagent.org/docs/policy-testing)). A test sets up its request with `with`, which replaces part of `input` or `data` for one expression.

The book's engine, regopy, has no `opa test`, so `lib.policy.run_tests` plays its part. It finds every `test_` rule in the folder's `_test.rego` files, evaluates each one, and reports PASS when the rule is true, FAIL when it's false or undefined, and ERROR when evaluation fails. Each of the platform's tests sets the user and the action as two separate paths, each to a literal value, for reasons [the section on regopy](#where-regopy-differs-from-opa) shows:

```rego
test_finance_sees_only_the_last_four_digits if {
	decision := access.decision with input.context.identity.user as "finance-1"
		with input.action as {"operation": "SelectFromColumns", "resource": {"table": {"schemaName": "billing", "tableName": "payments", "columns": ["amount", "card_number"]}}}
	decision.allow
	decision.row_filters == []
	decision.column_masks == {"card_number": "last4"}
}
```

The tests cover each group's allow, its filters and its masks, and the ways a request is denied: a table the group isn't given, an operation other than a read, a user the policy doesn't know, and a support agent with no region.

Example `policy-unit-tests` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""Runs every test in the platform's Rego test file and counts the passes. The point rests on the last line, the tests passed out of all of them."""
from collections import Counter

from lib import policy

# Every `test_` rule in governance/policies/access_test.rego, run by name: PASS, FAIL or ERROR, as `opa test` reports.
results = policy.run_tests()
for test, result in results.items():
    print(f"{result}: {test}")
# len(results) counts every test, so one that fails or errors still shows in the total
print("tests passed:", f"{Counter(results.values())['PASS']} of {len(results)}")
```

Output:

```text
PASS: test_support_reads_only_its_own_region
PASS: test_support_without_a_region_is_denied
PASS: test_marketing_sees_only_consenting_active_learners
PASS: test_a_group_only_reads_its_own_tables
PASS: test_finance_sees_only_the_last_four_digits
PASS: test_data_science_never_sees_card_numbers
PASS: test_data_science_sees_pseudonyms_not_people
PASS: test_an_unclassified_column_is_hidden
PASS: test_an_unknown_user_is_denied
PASS: test_an_instructor_sees_only_their_courses
PASS: test_the_assistant_reads_only_consented_reviews
PASS: test_training_reads_only_consented_reviews_without_contacts
tests passed: 12 of 12
```

A test that checks only `decision.allow` would miss most mistakes, so every test of an allowed read compares the row filters and the column masks whole. In finance's test, `decision.row_filters == []` fails if the policy adds any filter to finance's reads, and `decision.column_masks == {"card_number": "last4"}` fails if it masks one column more or one fewer, or shows the card number another way. The run passes 12 of 12 tests.

**Working rule:** Write a test for every rule that grants or narrows access, and one for every way a request can be denied, and compare whole filters and masks, not single keys. Run the tests on every change to the policy and to the data the policy reads.

## Check who sees what from a decision table {#check-who-sees-what}

[Unit tests](#unit-test-the-policy-in-rego) are written in Rego by whoever writes the policy. The people who own the data, such as the support lead or the finance team, should be able to check the policy too, without reading Rego. A decision table gives them that: one row per request, saying who reads which table and what they must get back, in the terms of their job.

The platform's table is `lib.policy.WHO_SEES_WHAT`, a list of rows in Python. Each gives a user, a table, the columns read and an optional purpose, then whether the read is allowed, which columns the row filters test and which columns are masked, and how. Every row goes through `lib.policy.decide`, which returns the [decision document](#return-the-decision-as-one-document), and the example prints one line per row, in the form to show the data's owners:

Example `who-sees-what` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""Each row of the who-sees-what table run through the policy and printed as one line, with the count of rows the policy matches. The point rests on the last line, the count of rows whose decision matches the outcome its row expects."""
from lib import policy

rego = policy.interpreter()

# Each row of lib.policy.WHO_SEES_WHAT is a request and the decision a reviewer expects for it.
matching = 0
for case in policy.WHO_SEES_WHAT:
    decision = policy.decide(policy.request(case.user, case.table, case.columns, case.purpose), rego)
    # matches returns True or False, which add as 1 or 0
    matching += policy.matches(case, decision)
    who = case.user + (f" ({case.purpose})" if case.purpose else "")
    shown = "allowed" if decision["allow"] else "denied"
    # a consent filter has no column key, so filtered_on reads its learner_consented key
    filters = ", ".join(policy.filtered_on(decision)) or "-"
    masks = ", ".join(f"{column}: {mask}" for column, mask in decision["column_masks"].items()) or "-"
    print(f"{who:26} {case.table:17} {shown:8} rows: {filters:29} masks: {masks}")
print("rows of the table the policy matches:", f"{matching} of {len(policy.WHO_SEES_WHAT)}")
```

Output:

```text
agent-a05                  crm.learners      allowed  rows: support_region                masks: -
agent-a05                  billing.payments  denied   rows: -                             masks: -
instructor-17              learning.reviews  allowed  rows: course_id                     masks: body: redact_contacts
instructor-17              crm.learners      denied   rows: -                             masks: -
marketing-1                crm.learners      allowed  rows: marketing_consent, status     masks: phone: redact
finance-1                  billing.payments  allowed  rows: -                             masks: card_number: last4
analyst-1                  billing.payments  allowed  rows: -                             masks: card_number: redact
analyst-1                  crm.learners      allowed  rows: -                             masks: email: pseudonymize, notes: redact
analyst-1                  learning.reviews  allowed  rows: -                             masks: body: redact
analyst-1 (ai-training)    learning.reviews  allowed  rows: ai_training_consent           masks: body: redact_contacts
assistant-1                learning.reviews  allowed  rows: ai_training_consent           masks: body: redact_contacts
someone-else               crm.learners      denied   rows: -                             masks: -
rows of the table the policy matches: 12 of 12
```

Read down the table and each role's rules show up as outcomes. The policy matches 12 of 12 rows: the support agent filtered by region and denied payments; the instructor filtered by course and denied the learners table; finance seeing `card_number` as `last4` where the data scientist sees `redact`; and the data scientist's two reads of reviews, with and without a purpose. A reviewer who thinks a row is wrong can say so in a pull request without knowing which rule produced it.

**Working rule:** Keep a who-sees-what table in the repository with the policy, run it with the unit tests, and show its printed form to the data's owners, in terms they can check. When an owner disagrees with a row, change the row first, and let the failing row drive the change to the policy.

## Know where regopy differs from OPA {#where-regopy-differs-from-opa}

The platform's [tests](#unit-test-the-policy-in-rego) run in regopy because the book's examples must run offline, in seconds, inside Python, and OPA is a separate program. regopy 1.5.2 is close to OPA. Its engine states that it supports Rego v1.18.1 as OPA defines it, and that it passes all the non-built-in test suites OPA publishes. Its README lists the built-ins it doesn't support, such as `net.*` and `http.send` ([rego-cpp README at v1.5.2](https://github.com/microsoft/rego-cpp/blob/v1.5.2/README.md)), but regopy also differs from OPA in ways that README doesn't list. The platform's policy and tests avoid each of the cases that follow, and OPA itself is the reference for anything in production.

The first group runs without any error:

Example `regopy-silent-differences` (Python 3.12.15 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""Small policies that regopy answers differently from OPA, each printed with the answer regopy gives. The prose's points rest on the printed values, and the bound and literal-mock lines are the controls where regopy agrees with OPA."""
import json

from regopy import Input, Interpreter


def ask(rules: str, query: str, request: dict) -> str:
    """One query's answer from regopy: the value bound to x, or "undefined"."""
    rego = Interpreter()
    rego.add_module("example", "package example\n" + rules)
    rego.set_input(Input(request))
    output = str(rego.query(query))
    # regopy writes undefined as a bare word; otherwise the binding for x is the answer
    return output if output == "undefined" else json.dumps(json.loads(output)["bindings"]["x"])


admins_only = 'default allow := false\nallow if input.user == "admin"\n'
# no variable in the query
print("a false decision, queried on its own:", ask(admins_only, "data.example.allow", {"user": "guest"}))
# bound to x, the same false decision comes back as a value
print("the same decision, bound to a variable:", ask(admins_only, "x := data.example.allow", {"user": "guest"}))

pre_1_0 = 'allow { input.user == "admin" }\n'                      # no `if`: OPA 1.x refuses to load this
print("a rule in pre-1.0 syntax:", ask(pre_1_0, "x := data.example.allow", {"user": "admin"}))

# regoin is never defined, so deny is undefined and not deny is true for any request
typo = 'region := "emea"\ndefault allow := false\nallow if not deny\ndeny if input.region != regoin\n'
print("a deny with a misspelt, unbound variable, for apac:", ask(typo, "x := data.example.allow", {"region": "apac"}))

mocks = """region := input.user.region
emea := {"region": "emea"}
with_a_literal := seen if { seen := region with input.user as {"region": "emea"} }
with_a_reference := seen if { seen := region with input.user as emea }
"""
print("region under a mock written as a literal:", ask(mocks, "x := data.example.with_a_literal", {"user": {"region": "apac"}}))
# the mock refers to the rule emea, which regopy ignores, so the real input's region comes back
print("region under a mock that refers to a rule:", ask(mocks, "x := data.example.with_a_reference", {"user": {"region": "apac"}}))
```

Output:

```text
a false decision, queried on its own: undefined
the same decision, bound to a variable: false
a rule in pre-1.0 syntax: true
a deny with a misspelt, unbound variable, for apac: true
region under a mock written as a literal: "emea"
region under a mock that refers to a rule: "apac"
```

- **A false decision comes back undefined.** Asked for `data.example.allow` on its own, regopy answers `undefined` where the value is `false`, so "denied" can't be told from "no decision". Bound to a variable, the same query gives `false`. `lib.policy` binds every decision it reads.
- **Pre-1.0 syntax runs.** Since OPA 1.0, `if` is required for every rule and `contains` for multi-value rules ([OPA v1.0.0 release notes](https://github.com/open-policy-agent/opa/releases/tag/v1.0.0)), and rego-cpp's changelog records that it has dropped support for v0 Rego ([rego-cpp changelog](https://github.com/microsoft/rego-cpp/blob/v1.5.2/CHANGELOG)). Yet regopy evaluates `allow { ... }` and answers `true`, so a policy can pass here and fail to load in OPA, and behind Trino as well.
- **An unbound variable switches a rule off.** OPA requires a variable in a comparison to be bound by another expression in the same rule, and rejects the policy otherwise ([OPA policy language](https://www.openpolicyagent.org/docs/policy-language)). regopy runs it anyway. A `deny` with `regoin` misspelt for `region` is silently undefined, so `allow if not deny` allows an `apac` request, as `true` shows.
- **A mock that refers to another rule is ignored.** In a policy whose `region` rule reads `input.user.region`, a mock written as a literal, `with input.user as {"region": "emea"}`, gives `"emea"`. Written as a reference to a rule holding the same object, it gives the real input's `"apac"`.

The second group fails, and one failure takes Python down with it. One case adds a test to a copy of the platform's tests; the other formats the same string from nine sources:

Example `regopy-failed-outputs` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""One test that replaces the whole input, and what that does to the interpreter: every query fails, and printing a failed output ends Python. The points rest on the printed error count, the assert that true does not succeed, and the signal the crash ends with."""
import signal
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from lib import policy

# The platform's tests, plus one that replaces the whole input at once rather than one path at a time.
whole_input = """
test_finance_reads_payments if {
	access.decision.allow with input as {"context": {"identity": {"user": "finance-1"}}, "action": {"operation": "SelectFromColumns", "resource": {"table": {"schemaName": "billing", "tableName": "payments", "columns": ["amount"]}}}}
}
"""
with tempfile.TemporaryDirectory() as name:
    folder = Path(name)
    for path in policy.POLICIES.glob("*.rego"):
        (folder / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    with open(folder / "access_test.rego", "a", encoding="utf-8") as tests:
        tests.write(whole_input)
    results = policy.run_tests(folder)
    print("tests that end in ERROR:", f"{Counter(results.values())['ERROR']} of {len(results)}")
    rego = policy.interpreter(folder, tests=True)
    succeeded = rego.query("true").ok()
    # no query succeeds here, not even true: the interpreter loads the file with the broken test
    assert not succeeded
    print("the query true succeeds:", succeeded)

    # lib.policy checks each output before reading it, so a decision asked of this interpreter raises an error.
    try:
        policy.decide(policy.request("finance-1", "billing.payments", ["amount"]), rego)
    except RuntimeError as error:
        print("lib.policy.decide raises:", error)

    # Printing one of those failed outputs, in a separate Python process.
    crash = "import sys; from pathlib import Path; from lib import policy; print(policy.interpreter(Path(sys.argv[1]), tests=True).query('true'))"
    ended = subprocess.run([sys.executable, "-c", crash, str(folder)], capture_output=True)
    # a negative return code names the signal that ended the process
    print("printing the failed output ends Python with:", signal.Signals(-ended.returncode).name)
```

Output:

```text
tests that end in ERROR: 13 of 13
the query true succeeds: False
lib.policy.decide raises: regopy couldn't evaluate data.platform.access.decision, so there is no decision to read
printing the failed output ends Python with: SIGSEGV
```

Example `regopy-sprintf-quotes` (Python 3.12.15 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""One label formatted from nine sources, the schema taken from each in turn. The point rests on the printed lines where regopy's JSON is invalid: a source that keeps its quotes breaks the output."""
import json

from regopy import Input, Interpreter

# The same label, sprintf("%s.%s", [schema, input.table]), with the schema "crm" taken from nine places.
# crm is a rule and schema_of a function, two of the nine sources
helpers = 'crm := "crm"\nschema_of(x) := "crm" if x == 1\n'
cases = [
    ("from input.schema", "input.schema", "true"),
    ("from a rule", "crm", "true"),
    ("from a function", "schema_of(1)", "true"),
    ("from iterating over a set", "s", 'some s in {"crm"}'),
    ("from object.get, the key found", 'object.get(input, "schema", "public")', "true"),
    # namespace is not in the input, so object.get returns its default, crm
    ("from object.get, its default", 'object.get(input, "namespace", "crm")', "true"),
    ("from lower(input.schema)", "lower(input.schema)", "true"),
    ("from concat", 'concat("", ["c", "rm"])', "true"),
    ("from a local variable set to a literal", "v", 'v := "crm"'),
]
for name, schema, body in cases:
    rego = Interpreter()
    rego.add_module("example", f'package example\n{helpers}label := sprintf("%s.%s", [{schema}, input.table]) if {{ {body} }}\n')
    rego.set_input(Input({"schema": "crm", "table": "learners"}))
    try:
        print(f"{name}:", json.loads(str(rego.query("x := data.example.label")))["bindings"]["x"])
    except json.JSONDecodeError as error:
        print(f"{name}, regopy's invalid JSON:", error.doc)
```

Output:

```text
from input.schema: crm.learners
from a rule: crm.learners
from a function: crm.learners
from iterating over a set: crm.learners
from object.get, the key found: crm.learners
from object.get, its default, regopy's invalid JSON: {"expressions":[true], "bindings":{"x":""crm".learners"}}
from lower(input.schema), regopy's invalid JSON: {"expressions":[true], "bindings":{"x":""crm".learners"}}
from concat, regopy's invalid JSON: {"expressions":[true], "bindings":{"x":""crm".learners"}}
from a local variable set to a literal, regopy's invalid JSON: {"expressions":[true], "bindings":{"x":""crm".learners"}}
```

- **Replacing the whole input breaks every query.** One extra test that writes its request as `with input as {...}`, and evaluates rules that call built-ins such as `sprintf`, makes every query in that interpreter fail. Every test then ends in ERROR, 13 of 13, and so does the first query asked of a fresh interpreter loaded with the same files, before any test runs: even the query `true` fails. Replacing one path at a time, as the platform's tests do, works.
- **Printing a failed output crashes Python.** Converting one of those failed outputs to a string ends the process with `SIGSEGV`. So `lib.policy` checks `output.ok()` before it reads anything, and a decision asked of that interpreter raises an error instead: `regopy couldn't evaluate data.platform.access.decision, so there is no decision to read`.
- **`sprintf` keeps stray quotes.** Formatting a string returned by some built-ins, such as `object.get`'s default, `lower` or `concat`, or a local variable set to a literal, keeps its quotes. regopy's own output is then invalid JSON, which its Python wrapper fails to parse, as `{"expressions":[true], "bindings":{"x":""crm".learners"}}` shows. Strings from `input`, a rule, a function, iteration and `object.get`'s found value format cleanly, and the platform's policy formats only strings like those.

**Working rule:** Treat regopy as a fast local evaluator and OPA as the reference. Write Rego v1 only, bind every decision to a variable, mock input one path at a time with literal values, and check that an output succeeded before reading it. Before a policy guards production data, check and test it with OPA itself, with `opa check --strict` and `opa test`.

## Write the same rules in Cedar {#the-same-rules-in-cedar}

Rego isn't the only language for policies like the platform's. Cedar's designers present it as a language for expressive, fast, safe and analyzable authorization ([Cutler et al., 2024](https://arxiv.org/abs/2403.04651)), and it takes a narrower view of a decision. A Cedar request names a principal, an action and a resource, and the answer follows three rules: default deny, forbid overrides permit, and skip on error, which the documentation defines as "if a policy's evaluation returns error, the policy does not factor into the authorization response; it is skipped" ([Cedar, authorization](https://docs.cedarpolicy.com/auth/authorization.html)). A schema declares every type of entity, the kinds of principal and resource a request can name, with its attributes, and attributes are required unless the schema marks them optional ([Cedar, schema](https://docs.cedarpolicy.com/schema/schema.html)). Validation checks policies against that schema before any request, and a set that validates avoids most of the errors that evaluation could raise, for requests that match the schema ([Cedar, validation](https://docs.cedarpolicy.com/policies/validation.html)). The book's examples run Cedar with cedarpy 4.12.2, which wraps the Rust Cedar Policy library for Python ([cedarpy](https://pypi.org/project/cedarpy/4.12.2/)).

The platform's rules in Cedar are in `governance/policies/access.cedar`, with the schema in `access.cedarschema`. A `permit` per group repeats the Rego policy's [`readable` map](#deny-by-default-then-allow-by-role). A `forbid` keeps support agents to learners in their own region, and another hides sensitive columns from everyone except finance's view of card numbers. `lib.policy.cedar_entities` generates the users, groups, tables and columns from the same [data document](#generate-the-data-the-policy-reads) the Rego policy reads, and the code adds the first learner of `crm.learners` in each region:

Example `cedar-same-rules` (Python 3.12.15 · cedarpy 4.12.2 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""The platform's Cedar policies checked against their schema, then asked the questions the Rego policy answers, over entities generated from its data. The points rest on the printed decisions, and on the misspelt-region error the schema gives before any request."""
import cedarpy

from lib import policy
from lib.platform import load

policies = policy.CEDAR_POLICIES.read_text(encoding="utf-8")
schema = policy.CEDAR_SCHEMA.read_text(encoding="utf-8")
print("policies valid against the schema:", cedarpy.validate_policies(policies, schema).validation_passed)
# misspells region in the policy's text, so the schema reports the attribute that User lacks
typo = cedarpy.validate_policies(policies.replace("principal.region", "principal.regoin"), schema)
# the validator's first error
print("with region misspelt:", typo.errors[0].error)

# Entities generated from the files the Rego policy reads, plus the first learner of crm.learners in each region.
first = {}
for learner in load("crm.learners").select(["learner_id", "support_region"]).to_pylist():
    # setdefault keeps the first learner seen in each region
    first.setdefault(learner["support_region"], learner)
entities = policy.cedar_entities(learners=first.values())


def ask(user: str, resource: str) -> cedarpy.AuthzResult:
    request = {"principal": f'User::"{user}"', "action": 'Action::"read"', "resource": resource, "context": {}}
    return cedarpy.is_authorized(request, policies, entities, schema)


for user, kind, name in [("finance-1", "Column", "billing.payments.card_number"),
                         ("analyst-1", "Column", "billing.payments.card_number"),
                         ("analyst-1", "Column", "billing.payments.amount"),
                         ("marketing-1", "Table", "billing.payments")]:
    print(f"{user} reads {name}:", ask(user, f'{kind}::"{name}"').decision.value)
for region, learner in sorted(first.items()):
    print(f"agent-a05 (emea) reads a learner in {region}:", ask("agent-a05", f'Learner::"{learner["learner_id"]}"').decision.value)
answer = ask("finance-1", 'Column::"billing.payments.card_number"')
# the policies that decided the answer, and those skipped on an error, come from its diagnostics
print("everything Cedar returns for finance-1's card numbers:", answer.decision.value, list(answer.diagnostics.reasons), list(answer.diagnostics.errors))
```

Output:

```text
policies valid against the schema: True
with region misspelt: for policy `policy6`, attribute `regoin` on entity type `User` not found
finance-1 reads billing.payments.card_number: Allow
analyst-1 reads billing.payments.card_number: Deny
analyst-1 reads billing.payments.amount: Allow
marketing-1 reads billing.payments: Deny
agent-a05 (emea) reads a learner in americas: Deny
agent-a05 (emea) reads a learner in apac: Deny
agent-a05 (emea) reads a learner in emea: Allow
everything Cedar returns for finance-1's card numbers: Allow ['policy3'] []
```

The decisions agree with the Rego policy wherever Cedar can express them. Finance may read the `card_number` column, and the data scientist may not, where Rego allows the read and redacts the column. The data scientist may read `amount`, and marketing may not read payments. The `emea` agent may read the `emea` learner and neither of the others. The policies validate against the schema too, and misspelling `region` gives a precise error before anything runs: for policy `policy6`, attribute `regoin` on entity type `User` not found.

Rego has no such check by default. The same typo in an attribute, `user.regoin` in the support agent's row filter, is undefined in OPA and regopy alike, and `opa check --strict` passes it, because OPA checks references against a schema only when you give it one ([OPA policy language, schemas](https://www.openpolicyagent.org/docs/policy-language#using-schemas-to-enhance-the-rego-type-checker)), and the platform gives none. The agent's row filter disappears, and only a test that compares the filters, such as `test_support_reads_only_its_own_region`, catches it.

Cedar returns a decision and little else. The last line of the output is everything it gives back for finance's card numbers: the decision, and the ID of the policy that made it. cedarpy names policies by position, `policy3` for the fourth, not by their `@id` annotations such as `finance-tables`. Cedar's documentation says `@id` means nothing to the language itself: its CLI uses it to set policy IDs, and other interfaces set them another way ([Cedar, syntax](https://docs.cedarpolicy.com/policies/syntax-policy.html)). Nothing in the answer says `last4`, the [mask](#return-the-decision-as-one-document) the Rego policy returns for finance's card numbers, because Cedar can permit a column but can't say how to show it. That rule would move into the enforcement code, outside the policy and its tests. Rows are the same. Cedar decides one learner at a time, so filtering the platform's learners means one request per learner, or Cedar's experimental partial evaluation, which returns residual policies for the parts it can't yet decide, and whose result is not a final authorization decision ([cedarpy](https://pypi.org/project/cedarpy/4.12.2/)). Cedar's paper makes the trade-off from the other side: "Rego's added expressiveness is a blessing but also a curse". It adds that Rego provides no built-in authorization concepts such as `allow` or `deny`. The same paper reports Cedar 42.8 to 80.8 times faster than Rego at the median, on three workloads with transitive relations, with Cedar 3.0.1 against OPA's Rego 0.61.0. Those are its designers' measurements, not this book's, and they say nothing about regopy.

**Working rule:** Choose Cedar when every question is "may this principal do this to this resource?", as in an application's permission checks, and you want a schema to check every policy before it runs. Choose Rego when the answer has to carry data, as a warehouse's row filters and column masks do, or when the engine already asks OPA, as Trino does. For the platform's warehouse, we recommend Rego.

## What goes wrong in production {#policies-in-production}

We consider the most damaging failure a rule that silently doesn't apply because an attribute is missing, and it happens in both languages. In Rego, "Expressions that refer to undefined values are also undefined" ([OPA policy language](https://www.openpolicyagent.org/docs/policy-language)). The support agent's [row filter](#narrow-by-attribute) takes its value from `user.region`, so for a user without a region the filter doesn't exist at all. A rule that allows by group still allows, and no filter means every row.

Take a copy of the platform's policy and tests, in a temporary folder, and remove the one line, `not missing_attribute`, from [`allow`](#deny-by-default-then-allow-by-role). Then add a support agent with their group and no region, as happens when someone is given a role before anyone sets their region, and ask both policies for the agent's tickets:

Example `missing-region-guard` (Python 3.12.15 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""The support policy with and without its guard, asked for a support agent's tickets. The prose's points rest on the printed reasons, row filters and regions seen with each version, and on the test the copy without the guard fails."""
import tempfile
from pathlib import Path

from lib import policy
from lib.platform import load

# A support agent added to users.toml with their group, before anyone has set their region.
data = policy.data_document()
data["platform"]["users"]["agent-new"] = {"groups": ["support"]}
request = policy.request("agent-new", "support.tickets", ["ticket_id", "body"])
# every region with a ticket, the candidates for what the agent may see
regions = sorted(set(load("support.tickets").column("support_region").to_pylist()))

# A copy of the platform's policy and tests, with one line taken out of `allow`: the missing-attribute guard.
with tempfile.TemporaryDirectory() as name:
    folder = Path(name)
    for path in policy.POLICIES.glob("*.rego"):
        # the guard's line in allow is indented with a tab, and this removes it
        (folder / path.name).write_text(path.read_text(encoding="utf-8").replace("\tnot missing_attribute\n", ""), encoding="utf-8")

    for label, policies in [("with the guard", policy.POLICIES), ("without the guard", folder)]:
        decision = policy.decide(request, policy.interpreter(policies, data=data))
        # a region counts when the decision allows the read and every row filter names it, so no filters means every region
        seen = [r for r in regions if decision["allow"] and all(f["equals"] == r for f in decision["row_filters"])]
        print(f"{label}, allowed:", decision["allow"])
        print(f"{label}, reasons:", "; ".join(decision["reasons"]))
        print(f"{label}, row filters:", decision["row_filters"])
        print(f"{label}, regions whose tickets the agent sees:", ", ".join(seen) or "none")

    failing = [test for test, result in policy.run_tests(folder).items() if result != "PASS"]
print("tests that fail without the guard:", ", ".join(failing))
```

Output:

```text
with the guard, allowed: False
with the guard, reasons: support's row filter needs the user's region, and there is none
with the guard, row filters: []
with the guard, regions whose tickets the agent sees: none
without the guard, allowed: True
without the guard, reasons: support may read support.tickets; support's row filter needs the user's region, and there is none
without the guard, row filters: []
without the guard, regions whose tickets the agent sees: americas, apac, emea
tests that fail without the guard: test_support_without_a_region_is_denied
```

Without the guard, the agent is allowed, with row filters `[]`, and sees the tickets of `americas, apac, emea`, including every learner's message and contact details. The reasons already say the region is missing; nothing in `allow` asked. With the guard, the agent is denied, and the reason names what is missing: support's row filter needs the user's region, and there is none. `default allow := false` didn't help either, because a rule did allow. One test catches it, `test_support_without_a_region_is_denied`, which is why the policy's tests include the case of the missing attribute.

Cedar fails the same way, through [skip on error](#the-same-rules-in-cedar). Strip the `has region` check from the support agents' `forbid` in the platform's Cedar policies, and it reads `principal.region` on an agent who has none:

Example `cedar-missing-region` (Python 3.12.15 · cedarpy 4.12.2 · pyarrow 26.0.1 · pyiceberg 0.12.0 · regopy 1.5.2), passing in Edition 2026.11.27:

```python
"""Cedar's support forbid with and without its `has region` check, asked about a support agent with no region. The points rest on the printed decisions with each version, and on the validation error the unguarded policy gets."""
import cedarpy

from lib import policy
from lib.platform import load

guarded = policy.CEDAR_POLICIES.read_text(encoding="utf-8")
unguarded = guarded.replace("principal has region && ", "")            # the same forbid, without its `has` check
schema = policy.CEDAR_SCHEMA.read_text(encoding="utf-8")

# A support agent with no region yet, as when a role is given before anyone sets one, and the first learner of crm.learners in each region.
data = policy.data_document()
data["platform"]["users"]["agent-new"] = {"groups": ["support"]}
first = {}
for learner in load("crm.learners").select(["learner_id", "support_region"]).to_pylist():
    first.setdefault(learner["support_region"], learner)
entities = policy.cedar_entities(learners=first.values(), data=data)

for name, policies in [("with `has region`", guarded), ("without it", unguarded)]:
    for region, learner in sorted(first.items()):
        request = {"principal": 'User::"agent-new"', "action": 'Action::"read"',
                   "resource": f'Learner::"{learner["learner_id"]}"', "context": {}}
        answer = cedarpy.is_authorized(request, policies, entities, schema)
        print(f"{name}, a learner in {region}:", answer.decision.value)
    # answer is the last learner's request, in emea, the last region in sorted order
    print(f"{name}, policies skipped on an error:", list(answer.diagnostics.errors))
# the first error the validator returns for the unguarded policies
print("validation without it:", cedarpy.validate_policies(unguarded, schema).errors[0].error)
```

Output:

```text
with `has region`, a learner in americas: Deny
with `has region`, a learner in apac: Deny
with `has region`, a learner in emea: Deny
with `has region`, policies skipped on an error: []
without it, a learner in americas: Allow
without it, a learner in apac: Allow
without it, a learner in emea: Allow
without it, policies skipped on an error: ['error while evaluating policy `policy6`: `User::"agent-new"` does not have the attribute `region`']
validation without it: for policy `policy6`, unable to guarantee safety of access to optional attribute `region` on entity type `User`
```

Without the check, Cedar lets a support agent with no region read the learners of all three regions. Evaluating the `forbid` raises an error, Cedar skips that policy, and the support `permit` still applies. With the check, the same agent is denied every learner. Passing the schema to `is_authorized` didn't stop it, because the schema declares `region` optional, since users outside support have none. Validation did, before any request: for policy `policy6`, unable to guarantee safety of access to optional attribute `region` on entity type `User`.

Other failures to watch for:

- **A misspelt attribute is undefined, not an error.** `user.regoin` for `user.region` passes `opa check --strict`, and the support filter disappears as it does for a missing region. Compare whole filters in the tests, and give OPA a schema if you want the check before any test runs.
- **A deny rule that reads a missing attribute fails open.** The guard fixes `allow`; a `deny` or `forbid` needs the same care. Deny explicitly when a required attribute is absent, and write the test for it before the rule.
- **Policies nobody can test.** Rules kept in an engine's settings or in hand-made views per role can't be unit-tested or diffed, so they drift. Keep the policy, its tests and its decision table in the repository, and run all three on every change.
- **regopy passes and OPA refuses.** Pre-1.0 syntax and unbound variables run in regopy. Check every policy with `opa check --strict` before deploying it to OPA.
- **Data that changed under the policy.** A support agent moved to another region is one edit to `users.toml`, and the decision follows only when the data document is rebuilt. Rebuild it whenever its sources change, and deploy it with the policy.

## What this chapter decided {#policies-decisions}

- **One policy, in Rego,** `governance/policies/access.rego`, denies by default, allows by group, and narrows by three attributes: the agent's region, the learner's consent and the request's purpose.
- **Requests are shaped like Trino's OPA requests,** built by `lib.policy.request`, plus an optional top-level `purpose`; groups come from `users.toml`, not from the request.
- **The policy's data is generated** by `lib.policy.data_document` from `users.toml`, `metadata.toml` and `learning.courses`, and never typed.
- **Each decision is one document** with `allow`, `row_filters`, `column_masks` and `reasons`. Filters and masks are data, never SQL, and the masks are `redact`, `last4`, `pseudonymize` and `redact_contacts`. A denial carries no filters or masks.
- **Missing facts fail closed:** a column the metadata doesn't classify is treated as sensitive, and a user whose row filter needs a missing attribute is denied.
- **The one purpose the policy knows is `ai-training`,** which limits reviews to learners who agreed to AI training and shows their text with contact details removed. A read without a purpose gets what the role allows, with review text hidden.
- **Two kinds of test run on every change:** the Rego unit tests through `lib.policy.run_tests`, and the who-sees-what table, `lib.policy.WHO_SEES_WHAT`.
- **regopy for the examples, OPA as the reference:** Rego v1 only, every decision bound to a variable, input mocked one path at a time with literals, and every output checked before it's read.
- **Cedar is for comparison** (`governance/policies/access.cedar`). It suits allow-or-deny checks on single resources; the platform's warehouse needs filters and masks as data, so it uses Rego. An access policy is only as clear as its tests are thorough. Writing the rules as code means a change to who sees what is a diff a reviewer can read, and a test can run before anyone relies on it.
