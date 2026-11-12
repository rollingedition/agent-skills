---
name: data-governance-as-code
description: "Data governance as code for warehouses built on Iceberg, Parquet and SQL: a metadata file tested against the catalog, personal data found and measured, column lineage from pipeline events, access policies in tested Rego enforced on every query, retention, consent and erasure, audit logs, consent-checked AI training data, and governance checks as a CI gate. Use when cataloging owners and classifications, finding personal data, tracing lineage, writing or enforcing access policies, deleting personal data, auditing access, building training corpora, or gating pull requests on governance."
license: CC-BY-4.0
compatibility: "The book's examples ran on Python 3.12.15 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Data Governance as Code"
  edition: "2026.11.23"
  verified: "2026-11-12"
  examples: "108 of 108 examples pass"
  edition-code: "4TXR-45EN"
  source: "https://rollingedition.com/data-governance-as-code"
---

# Data Governance as Code

This agent skill is *Data Governance as Code*, Edition 2026.11.23, from Rolling Edition. Examples passed Nov 12, 2026: 108 of 108 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `data-governance-as-code` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `4TXR-45EN` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/data-governance-as-code
- **Credit the book** when you quote it or reuse its code: Data Governance as Code, Edition 2026.11.23, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `data-governance-as-code` plugin and the zip on the book's page at rollingedition.ai.

## Keep a catalog's metadata in a reviewed file and test it

**When:** Owners and classifications must be reviewed like pipeline code.

1. Move owners, domains, descriptions and classifications into one file in the repository, changed only by pull request, with a closed list of classifications and one owning team per table. [Keep the metadata in a reviewed file](https://rollingedition.com/data-governance-as-code/s/keep-metadata-in-a-reviewed-file)
2. Key each column's metadata by its Iceberg field ID, with the name beside it, so a rename is reviewed rather than read as a new column. [Key column metadata by field ID](https://rollingedition.com/data-governance-as-code/s/key-column-metadata-by-field-id)
3. Write column descriptions into the table's schema as `doc`, and compare schema changes by field IDs, names and types, never by schema IDs. [Write descriptions into the table's schema](https://rollingedition.com/data-governance-as-code/s/write-descriptions-into-the-schema), [A description edit is a schema change](https://rollingedition.com/data-governance-as-code/s/a-description-edit-is-a-schema-change)
4. Walk the catalog, not the metadata file, and fail on any table without an owner or any column without a classification. [Test the catalog against the metadata](https://rollingedition.com/data-governance-as-code/s/test-the-catalog-against-the-metadata)
5. On every schema change, report columns with no reviewed classification and entries whose field ID the table no longer has. Remove a dropped column's entry in the pull request that drops it. [Catch schema changes before the metadata goes stale](https://rollingedition.com/data-governance-as-code/s/catch-schema-changes)
6. Classify a pseudonymous ID by what its own table reveals, protect the table that resolves it, and include the ID in every erasure. [Classify pseudonymous IDs for joining](https://rollingedition.com/data-governance-as-code/s/classify-pseudonymous-ids)
7. Let a model's drafts raise a classification, never lower it, and measure the model against your reviewed metadata before it drafts any. [Measure where the model's drafts are wrong](https://rollingedition.com/data-governance-as-code/s/measure-where-the-drafts-are-wrong)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/test-the-catalog-against-the-metadata). Its output includes `problems found: 2`. Fix each table it names in the file.

**Pitfalls:**
- A table created outside the pipelines escapes the test. Run it on a schedule against production.

## Find personal data in columns and text, and measure the detector

**When:** You must find personal data in columns or free text, and know what the detector misses.

1. Run name rules over every column first. They may raise a classification and never lower one. [Classify columns from the schema](https://rollingedition.com/data-governance-as-code/s/classify-columns-from-the-schema)
2. Sample non-null values of every free-text column with a fixed seed kept with the result, sized from the rarest personal data you must catch. [Sample a column's values the same way every run](https://rollingedition.com/data-governance-as-code/s/sample-column-values)
3. Propose the strictest classification the name or any sampled value supports, with `internal` as the floor. [Classify columns from their values](https://rollingedition.com/data-governance-as-code/s/classify-columns-from-their-values)
4. Before a detector masks anything, measure recall per entity type, by exact and by overlap matching, against labelled spans. [Measure a detector against labelled spans](https://rollingedition.com/data-governance-as-code/s/measure-against-labelled-spans)
5. Keep only the recognizers your text can hold, each with a threshold set from its own scores, never Presidio's default threshold. [Tune the recognizers against the truth](https://rollingedition.com/data-governance-as-code/s/tune-the-recognizers)
6. Use patterns only for what has a checkable shape. Mask free text with a PII model and the tuned patterns together: the model for names and addresses, checksums for card numbers and IBANs. [See where patterns fail](https://rollingedition.com/data-governance-as-code/s/where-patterns-fail), [Read the model's misses](https://rollingedition.com/data-governance-as-code/s/read-the-models-misses)
7. Report coverage beside recall with the right label. [Count what a wrong label costs](https://rollingedition.com/data-governance-as-code/s/what-a-wrong-label-costs)
8. Classify every field ID the metadata doesn't have in the pull request that adds it, and sample text columns again on a schedule. [Classify again when the schema changes](https://rollingedition.com/data-governance-as-code/s/reclassify-on-schema-change)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/measure-against-labelled-spans). Its output includes `CREDIT_CARD, recall, exact: 0.71`, the baseline under Presidio's defaults. Tuning must not lower it.

**Pitfalls:**
- Under Presidio's defaults, every run of 8 to 17 digits is read as a US bank number. Count detections per label to notice.
- `AnalyzerEngine()` downloads a model at run time. Configure the engine, pin what it fetches, and run the tests with the network off. [Run Presidio offline](https://rollingedition.com/data-governance-as-code/s/run-presidio-offline)

## Build column lineage from pipeline run events

**When:** You need what a column depends on, what a change to it reaches, and its classification.

1. Send a START event, then a COMPLETE or FAIL event, from the code that runs each job. Name datasets by catalog identifier, never by path. [Send a run event from every pipeline](https://rollingedition.com/data-governance-as-code/s/send-run-events)
2. Trace each output column with sqlglot's `lineage`, passing the catalog's schema generated from the table metadata. [Trace each output column to its sources](https://rollingedition.com/data-governance-as-code/s/trace-output-columns)
3. Record the INDIRECT inputs too: the join keys, filters and grouping columns of every `SELECT`. [Add the inputs that decide which rows exist](https://rollingedition.com/data-governance-as-code/s/add-indirect-inputs)
4. Treat a statement the parser can't read as an error, never as empty lineage. Refuse `MERGE`, or record its lineage from a `SELECT` of the columns it writes. [Fail on statements the parser can't read](https://rollingedition.com/data-governance-as-code/s/fail-on-unreadable-lineage)
5. Run impact analysis on the graph built from events, INDIRECT edges included, and send each report to the owners of the tables it reaches. [Find what a column change breaks](https://rollingedition.com/data-governance-as-code/s/impact-of-a-column-change)
6. Propose each derived column's classification as the stricter of its inputs', counting INDIRECT inputs, and send it to the table's owner. [Propose classifications from lineage](https://rollingedition.com/data-governance-as-code/s/classifications-from-lineage)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/add-indirect-inputs). Compare `source columns, values only: 5` with `source columns, with the rows' inputs: 10`. If your counts are equal, the INDIRECT inputs are missing.

**Pitfalls:**
- The client drops every event when `OPENLINEAGE_DISABLED` is `true`. After every scheduled run, compare the jobs that ran with the COMPLETE events that arrived.
- A table classified `internal` can hold personal copies. Fail when a declared classification is lower than lineage proposes.

## Write access policies as tested Rego

**When:** You must decide which roles may read which tables, rows and columns, as code that tests can check.

1. Generate the policy's data from the file or table that owns each fact, every time you load the policy. [Generate the data the policy reads](https://rollingedition.com/data-governance-as-code/s/generate-the-data-the-policy-reads)
2. Start the policy with `default allow := false`, and allow only through rules that name the role and the resource. [Deny by default, then allow by role](https://rollingedition.com/data-governance-as-code/s/deny-by-default-then-allow-by-role)
3. Model each condition as an attribute read by one rule per role. Let a requester-supplied attribute, such as a purpose, unlock access only under a narrower condition. [Narrow by attribute](https://rollingedition.com/data-governance-as-code/s/narrow-by-attribute)
4. Return one decision document per request, holding the allow, the row filters, the column masks and the reasons. [Return the decision as one document](https://rollingedition.com/data-governance-as-code/s/return-the-decision-as-one-document)
5. Write a test for every rule that grants or narrows access, and for every way a request can be denied. Compare whole filters and masks. [Unit-test the policy in Rego](https://rollingedition.com/data-governance-as-code/s/unit-test-the-policy-in-rego)
6. Keep a who-sees-what table with the policy and run it with the tests. [Check who sees what from a decision table](https://rollingedition.com/data-governance-as-code/s/check-who-sees-what)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/policies-in-production). Compare `with the guard, allowed: False` with `without the guard, allowed: True`. A support agent with no region must be denied.

**Pitfalls:**
- A missing attribute disables a rule silently. Guard `allow`, and deny explicitly when a required attribute is absent.
- regopy can accept a policy that OPA refuses. Check and test every policy with OPA before it guards production data. [Know where regopy differs from OPA](https://rollingedition.com/data-governance-as-code/s/where-regopy-differs-from-opa)

## Enforce policies on every query

**When:** Each query may see only the rows and columns its decision allows.

1. Ask the policy about every table and column a query names, with `*` expanded against the catalog's schema. Deny anything that schema doesn't hold. [Find every table and column a query reads](https://rollingedition.com/data-governance-as-code/s/find-what-a-query-reads)
2. Check every source against an allowlist of catalog tables, CTEs in scope and subqueries, and deny the rest. [Allow only catalog tables, CTEs and subqueries](https://rollingedition.com/data-governance-as-code/s/allow-only-catalog-sources)
3. Don't mask by rewriting column references. Replace each protected table with a subquery generated from the decision. [Masking column references leaks](https://rollingedition.com/data-governance-as-code/s/column-masks-leak), [Replace each table with a filtered, masked subquery](https://rollingedition.com/data-governance-as-code/s/replace-each-table)
4. Keep every mask's SQL in one table in the layer, and let the policy name masks, never write them. Key pseudonyms with a secret only the layer holds. [Write each mask as SQL in one place](https://rollingedition.com/data-governance-as-code/s/write-masks-as-sql)
5. Build every row filter from the decision's values with a SQL builder, and deny any filter shape the layer doesn't recognize. [Build row filters from the decision's data](https://rollingedition.com/data-governance-as-code/s/build-row-filters-from-data)
6. Make every value a query can read depend on the row filters, never on the engine's evaluation order. [Gate every column on the row filters](https://rollingedition.com/data-governance-as-code/s/gate-columns-on-row-filters)
7. Run the who-sees-what cases as queries through the layer on every change, and fail the build when a case disagrees. [Test who sees what by running queries](https://rollingedition.com/data-governance-as-code/s/test-who-sees-what)
8. Hold back every reported group below a minimum size. [Hold back small groups in reports](https://rollingedition.com/data-governance-as-code/s/hold-back-small-groups)
9. With Trino, set both the row-filter and the column-mask URIs, and return row filters only from a decision that allows the read. [Hand the same policies to an engine that enforces them](https://rollingedition.com/data-governance-as-code/s/engine-enforcement)
10. Run an assistant's queries with the identity of the person it answers. [Query on someone's behalf](https://rollingedition.com/data-governance-as-code/s/query-on-someones-behalf)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/test-who-sees-what). Its output includes `marketing-1, crm.learners: 1,861 of 5,000 rows, changed: phone`. Marketing must read fewer rows than the table holds, with the masked column named.

**Pitfalls:**
- Direct file reads, such as `read_parquet`, name no table and bypass the rewrite. Deny them, and turn off external access.
- DuckDB is not a security boundary. Enforce in an engine that runs as a service of its own, such as Trino.

## Apply retention, consent and erasure as code

**When:** You must delete personal data on a schedule or when a person asks, and prove it is gone from every table, snapshot and file.

1. Keep each table's retention period, the column it counts from and the state a row must be in, in a reviewed file. Apply it against a day the scheduler passes in, never the clock. [Keep retention rules in a reviewed file](https://rollingedition.com/data-governance-as-code/s/retention-rules-in-a-file)
2. Apply retention as Iceberg row deletes, recording the rule and the day in each commit's snapshot summary. [Delete expired rows with row deletes](https://rollingedition.com/data-governance-as-code/s/delete-expired-rows)
3. Keep consent in one table that the query reads as a row filter, so a withdrawal changes the next query. [Read consent where the query runs](https://rollingedition.com/data-governance-as-code/s/consent-at-query-time)
4. Plan each erasure from the catalog and the lineage graph, not a maintained list, after checking every table is accounted for by some job's lineage. Keep exceptions in config written by your legal team. [Plan an erasure from lineage](https://rollingedition.com/data-governance-as-code/s/plan-erasure-from-lineage)
5. Carry out the erasure as row deletes in the plan's order, recording only a request ID in each commit. [Erase the rows the plan lists](https://rollingedition.com/data-governance-as-code/s/erase-the-rows)
6. Expire snapshots through one function that reads `gc.enabled` and the `history.expire` settings, and refuse the whole erasure when one table would keep the person. [Expire snapshots by the table's own settings](https://rollingedition.com/data-governance-as-code/s/expire-snapshots)
7. Remove unreferenced files after every expiry, keeping a minimum age of days in production. [Remove the files no snapshot references](https://rollingedition.com/data-governance-as-code/s/remove-unreferenced-files)
8. Set metrics properties to `none` or `counts` for every personal, sensitive or unclassified column. [Keep personal values out of manifests](https://rollingedition.com/data-governance-as-code/s/keep-values-out-of-manifests)
9. Scan every file the platform stores, and treat a file that still holds the person as a failed erasure. [Prove the erasure by reading every file](https://rollingedition.com/data-governance-as-code/s/verify-the-erasure)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/erase-the-rows). Compare `the learner's rows in crm.learners, read now: 0` with `the learner's rows in crm.learners, read by time travel: 1`. Rows time travel still reads mean the snapshots must be expired next.

**Pitfalls:**
- An erased person comes back after a nightly reload. Erase in the source system first, and keep a register of keyed hashes that every load filters against.
- Backups keep what the sweep deletes. Decide with their owners how they age out.

## Audit every decision and check the log against the engine

**When:** You must show who read which data, that the record is unaltered, and that it matches what the engine ran.

1. Write the audit record in the enforcement layer, before the query runs, with every identity involved and each table's decision. [Record every decision where it's made](https://rollingedition.com/data-governance-as-code/s/record-every-decision)
2. Record a query's shape, never its values. Keep the executed SQL only as a keyed digest. [Keep values out of the record](https://rollingedition.com/data-governance-as-code/s/keep-values-out-of-the-record)
3. Fingerprint every decision with a hash of the policy's modules and its data document together, and explain an old decision under its own revision. [Replay an old decision under its own policy](https://rollingedition.com/data-governance-as-code/s/replay-old-decisions)
4. Chain every record to the one before with SHA-256 and a sequence number, and write the head down outside the layer's control. [Chain the records so an edit shows](https://rollingedition.com/data-governance-as-code/s/chain-the-records)
5. Check the engine's query log on a schedule: every query must match a record, and every allowed record a query. [Cross-check the log against DuckDB's query log](https://rollingedition.com/data-governance-as-code/s/cross-check-the-query-log)
6. Generate access reviews from the policy and the audit log, never from role lists. [Generate the access review from the log](https://rollingedition.com/data-governance-as-code/s/generate-the-access-review)
7. Generate evidence from records with code, include failing findings, and let each report check the chain against the head the last one wrote down. [Produce evidence as data](https://rollingedition.com/data-governance-as-code/s/produce-evidence-as-data)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/chain-the-records). Compare `record 3 edited, chain rebuilt, checked alone: no problem found` with `record 3 edited, chain rebuilt, checked against the noon head: the chain no longer passes through the head written down at record 9`. Only a head kept elsewhere catches a rebuilt chain.

**Pitfalls:**
- The audited code can switch off its own logging. Enforce in a service with its own log.
- OPA drops decision events when its rate limit is exceeded. Count the engine's queries against the decision records.

## Build AI training data you can defend

**When:** You build a corpus or retrieval index from personal text, and each record's consent, personal data, duplicates and provenance must be handled.

1. Admit only records whose consent answer is yes for the use. Never filter out the refusals and keep the rest. [Admit only reviews whose authors consented](https://rollingedition.com/data-governance-as-code/s/admit-consented-reviews)
2. Detect personal data in the text after the enforcement layer's masks, and measure what's left, by value. [Replace personal data in the text, then measure what's left](https://rollingedition.com/data-governance-as-code/s/replace-personal-data)
3. Make pseudonyms with HMAC under a key only the job holds. [Keep pseudonyms consistent with a keyed hash](https://rollingedition.com/data-governance-as-code/s/consistent-pseudonyms)
4. Deduplicate exact copies by a hash of the normalized text, then near-duplicates by MinHash, confirming each candidate by its exact similarity. [Find near-duplicates with MinHash](https://rollingedition.com/data-governance-as-code/s/near-duplicates-with-minhash)
5. Tune LSH below your similarity threshold, so it misses few pairs, and measure its misses on a sample. [Tune LSH for recall, then confirm every pair](https://rollingedition.com/data-governance-as-code/s/tune-lsh-then-confirm)
6. Give every record its source table, row ID, and the job and run that wrote it. Filter every retrieval by the reader's own decision on each record's source row before a model sees it. [Carry provenance on every record](https://rollingedition.com/data-governance-as-code/s/carry-provenance)
7. Generate the dataset card in the run that builds the data. [Generate the dataset card from the run](https://rollingedition.com/data-governance-as-code/s/generate-the-dataset-card)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/admit-consented-reviews). Compare `reviews the governed build reads, as analyst-1 for ai-training: 436` with `reviews a filter on refusals keeps: 2,045`. The gap is consent the refusal filter never checked.

**Pitfalls:**
- A filter on refusals keeps the unknowns, mostly from people never asked. Count records per consent answer.
- A person withdraws after a build, but that build and any model made from it still hold the record. Record each model's build run, and check every build against today's consent before training.
- Presidio's `hash` operator gives a different output on each call at the pinned version. Never use it without a salt for pseudonyms.

## Run governance checks as one gate on every pull request

**When:** Governance rules must block a merge the way tests do.

1. Run every check as one job on every pull request, each reporting all its findings under stable IDs. A finding the pull request introduces fails it; one already on main doesn't. [Run every check as one job](https://rollingedition.com/data-governance-as-code/s/run-every-rule-as-one-job)
2. Make that job required by branch protection on main, and put every finding in the pull request. [Gate the pull request, not the commit](https://rollingedition.com/data-governance-as-code/s/gate-the-pull-request)
3. Diff schemas by field ID, and report what each rename, type change and removal reaches: readers, pipelines and lineage. [Report what a schema change reaches](https://rollingedition.com/data-governance-as-code/s/report-what-a-schema-change-reaches)
4. Require the table owner's approval for a lowered classification, a changed owner or a move to another domain. [Ask the owner before lowering a classification](https://rollingedition.com/data-governance-as-code/s/ask-the-owner-before-lowering)
5. Remove a column in two pull requests: deprecate it, then drop it. [Deprecate a column before removing it](https://rollingedition.com/data-governance-as-code/s/deprecate-before-removing)
6. Keep each domain's metadata under its own path, with a CODEOWNERS line for its team, and require code-owner review. [Route each domain's reviews by path](https://rollingedition.com/data-governance-as-code/s/a-folder-and-a-code-owner-per-domain)
7. Let domain rules add to the global rules, never replace them. [Layer domain rules on the global rules](https://rollingedition.com/data-governance-as-code/s/run-global-and-domain-rules)
8. Let a waiver name exactly one finding, with an owning team, a reason and an end date, and list the checks no waiver may silence. Count waived findings per check. [Count waived findings per check](https://rollingedition.com/data-governance-as-code/s/count-waived-findings)

**Check:** Run [the example](https://rollingedition.com/data-governance-as-code/s/run-every-rule-as-one-job). Its report has `coverage: failed, findings 3, new 1, on main 2, waived 0, 12 tables checked`. The new finding fails the job; the findings already on main don't.

**Pitfalls:**
- A broken file can hide every other finding. Turn the crash into one finding that names the file, and run the other checks anyway.
- A team whose pull request fails may remove the check or add a waiver. Make the platform team the code owner of the check settings, the waivers and CODEOWNERS.
