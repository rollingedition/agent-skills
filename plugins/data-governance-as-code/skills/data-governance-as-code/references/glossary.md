---
title: "Glossary"
book: "Data Governance as Code"
edition: "2026.11.31"
canonical: "https://rollingedition.com/data-governance-as-code/glossary"
---

# Glossary of *Data Governance as Code*

The 151 terms this book defines, as Edition 2026.11.31 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/data-governance-as-code/glossary

## access log

a separate access log, with learner IDs, a retention period and no chain

- Defined in: [Keep values out of the record](audit-and-evidence.md#keep-values-out-of-the-record)
- Address: https://rollingedition.com/concepts/data-governance/access-log

## access review

An access review compares what each person may read with what they use.

- Also: access reviews
- Defined in: [Audit and evidence](audit-and-evidence.md)
- Address: https://rollingedition.com/concepts/data-governance/access-review

## approximate threshold

The curve's approximate threshold is (1/b)^(1/r).

- Formula: `(1/b)^(1/r)`
- Defined in: [Tune LSH for recall, then confirm every pair](governing-data-for-ai.md#tune-lsh-then-confirm)
- Address: https://rollingedition.com/concepts/data-engineering/approximate-threshold

## AssertCurrentSchemaId

A REST catalog commit can carry AssertCurrentSchemaId, which requires the table's current schema ID to match the one the requirement names

- Defined in: [Report what a schema change reaches](governance-in-ci.md#report-what-a-schema-change-reaches)
- Address: https://rollingedition.com/concepts/data-warehousing/assert-current-schema-id

## attribute

an attribute is any other fact a rule reads, about the principal, the data or the request

- Also: attributes
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/attribute

## attribute-based access control

NIST's guide to attribute-based access control defines the general approach, in which access is decided by attributes of the subject, the object, the requested operations and, sometimes, the environment.

- Also: ABAC
- Defined in: [Narrow by attribute: region, consent and purpose](access-policies-as-code.md#narrow-by-attribute)
- Address: https://rollingedition.com/concepts/data-governance/attribute-based-access-control

## audit log

an audit log is a record of who did what, when, and with what outcome, kept so that someone can check it later.

- Also: audit logs
- Defined in: [Audit and evidence](audit-and-evidence.md)
- Address: https://rollingedition.com/concepts/data-governance/audit-log

## branch protection

GitHub's branch protection can require that every required status check pass before collaborators can merge changes into the protected branch

- Defined in: [Gate the pull request, not the commit](governance-in-ci.md#gate-the-pull-request)
- Address: https://rollingedition.com/concepts/data-engineering/branch-protection

## breaking-change checker

breaking-change checkers, the tools that compare two versions of a schema for changes that break its readers

- Also: breaking-change checkers
- Defined in: [Governance in CI](governance-in-ci.md)
- Address: https://rollingedition.com/concepts/data-governance/breaking-change-checker

## candidate pair

two texts become a candidate pair when all the rows of any one band match

- Also: candidate pairs
- Part of: locality-sensitive hashing
- Defined in: [Tune LSH for recall, then confirm every pair](governing-data-for-ai.md#tune-lsh-then-confirm)
- Address: https://rollingedition.com/concepts/data-engineering/candidate-pair

## catalog

A catalog lists a platform's tables and their schemas

- Defined in: [Catalog a table with its owner and classifications](governance-end-to-end.md#catalog-a-table)
- Address: https://rollingedition.com/concepts/data-governance/catalog

## catalog label

labels, ownership or classification that a catalog returns with a table, per table and per field ID, kept out of properties on purpose

- Also: labels
- Contrasts with: table property
- Defined in: [Write descriptions into the table's schema](a-catalog-you-can-test.md#write-descriptions-into-the-schema)
- Address: https://rollingedition.com/concepts/data-warehousing/catalog-label

## Cedar schema

A schema declares every type of entity, the kinds of principal and resource a request can name, with its attributes

- Comes before: policy validation
- Defined in: [Write the same rules in Cedar](access-policies-as-code.md#the-same-rules-in-cedar)
- Address: https://rollingedition.com/concepts/data-governance/cedar-schema

## chance of a candidate

Leskovec, Rajaraman and Ullman derive the chance that a pair with Jaccard similarity s becomes a candidate pair

- Formula: `P(candidate) = 1 − (1 − sʳ)ᵇ`
- Measured from: candidate pair
- Defined in: [Tune LSH for recall, then confirm every pair](governing-data-for-ai.md#tune-lsh-then-confirm)
- Address: https://rollingedition.com/concepts/data-engineering/candidate-probability

## checkout

two folders called checkouts, one of the main branch and one of the pull request's branch

- Also: checkouts
- Defined in: [Governance in CI](governance-in-ci.md)
- Address: https://rollingedition.com/concepts/data-engineering/checkout

## classification

A classification is one of four values, ordered from least to most protected

- Also: classifications
- Part of: metadata
- Defined in: [Keep the metadata in a reviewed file](a-catalog-you-can-test.md#keep-metadata-in-a-reviewed-file)
- Address: https://rollingedition.com/concepts/data-governance/classification

## code owner

GitHub requests code owners' review automatically when a pull request modifies code they own

- Also: code owners, CODEOWNERS
- Defined in: [Route each domain's reviews by path](governance-in-ci.md#a-folder-and-a-code-owner-per-domain)
- Address: https://rollingedition.com/concepts/data-engineering/code-owner

## column lineage

Column lineage says which input columns each output column came from, and that is what governance needs

- Defined in: [Trace each output column to its sources](lineage-from-pipelines.md#trace-output-columns)
- Address: https://rollingedition.com/concepts/data-pipelines/column-lineage

## column mask

a column mask changes how a column's values are shown

- Also: column masks
- Part of: decision document
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/column-mask

## columnLineage facet

OpenLineage puts column lineage in a dataset facet, columnLineage, on the output: fields maps each output column to its inputFields, and an optional dataset list holds inputs that affect the whole dataset

- A kind of: facet
- Computed from: column lineage
- Defined in: [Trace each output column to its sources](lineage-from-pipelines.md#trace-output-columns)
- Address: https://rollingedition.com/concepts/data-pipelines/column-lineage-facet

## complete mediation

Saltzer and Schroeder's principle of complete mediation holds that "every access to every object must be checked for authority"

- Defined in: [Hand the same policies to an engine that enforces them](enforcing-policies-on-queries.md#engine-enforcement)
- Address: https://rollingedition.com/concepts/data-governance/complete-mediation

## consent

Consent is a person's agreement to one use of their data, such as marketing email, which they can withdraw.

- Defined in: [Retention, consent and erasure](retention-consent-erasure.md)
- Address: https://rollingedition.com/concepts/data-governance/consent

## copy-on-write

Copy-on-write rewrites each affected data file without the deleted rows.

- Contrasts with: merge-on-read
- Defined in: [Delete expired rows with row deletes](retention-consent-erasure.md#delete-expired-rows)
- Address: https://rollingedition.com/concepts/data-warehousing/copy-on-write

## coverage

lib.pii adds a third measure, coverage: whether every character of a labelled span is inside some detection, whatever its label.

- Measured from: truth
- Defined in: [Measure a detector against labelled spans](finding-personal-data.md#measure-against-labelled-spans)
- Address: https://rollingedition.com/concepts/data-governance/coverage

## coverage check

The coverage check is the catalog check, lib.metadata.problems, run on the branch's platform, and for each column nobody classified it adds what a rule on column names suggests

- Defined in: [Fail the pull request that adds an unclassified column](governance-end-to-end.md#fail-the-pull-request)
- Address: https://rollingedition.com/concepts/data-governance/coverage-check

## CRM

The CRM, the application where learners manage their accounts

- Defined in: [Read consent where the query runs](retention-consent-erasure.md#consent-at-query-time)
- Address: https://rollingedition.com/concepts/data-engineering/crm

## Croissant

Croissant is MLCommons' metadata format for machine-learning datasets

- True for: mlcroissant 1.1.1
- Implemented by: mlcroissant 1.1.1
- Defined in: [Generate the dataset card from the run](governing-data-for-ai.md#generate-the-dataset-card)
- Address: https://rollingedition.com/concepts/data-governance/croissant

## cross-check

Audited.check_engine_log matches each query in DuckDB's log, by keyed digest, against the rewritten_digest of the records written since the last check, then empties DuckDB's log, which holds the queries' values.

- Also: cross-check against the query log
- True for: duckdb 2.0.0
- Computed from: rewritten digest
- Defined in: [Cross-check the log against DuckDB's query log](audit-and-evidence.md#cross-check-the-query-log)
- Address: https://rollingedition.com/concepts/data-governance/cross-check

## data document

Everything else a rule needs besides the request, such as each user's groups and each column's classification, comes from a second document, which OPA calls data.

- Defined in: [Generate the data the policy reads](access-policies-as-code.md#generate-the-data-the-policy-reads)
- Address: https://rollingedition.com/concepts/data-governance/data-document

## dataset

A dataset is a table or file, named by a namespace and a name that together identify it.

- Also: datasets
- Defined in: [Send a run event from every pipeline](lineage-from-pipelines.md#send-run-events)
- Address: https://rollingedition.com/concepts/data-pipelines/dataset

## dataset card

A dataset card tells whoever trains or audits a model what's in its data, where it came from and what was done to it.

- Also: dataset cards
- Defined in: [Generate the dataset card from the run](governing-data-for-ai.md#generate-the-dataset-card)
- Address: https://rollingedition.com/concepts/data-governance/dataset-card

## decision

A decision is a policy's answer.

- Also: decisions
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/decision

## decision document

The platform's policy uses structured data to return its whole answer as one document, data.platform.access.decision, with four keys: allow, the row_filters, the column_masks, and the reasons.

- A kind of: decision
- Defined in: [Return the decision as one document](access-policies-as-code.md#return-the-decision-as-one-document)
- Address: https://rollingedition.com/concepts/data-governance/decision-document

## decision record

The platform's audit log holds one decision record per query.

- Also: decision records
- Part of: audit log
- Defined in: [Audit and evidence](audit-and-evidence.md)
- Address: https://rollingedition.com/concepts/data-governance/decision-record

## decision table

A decision table is one row per request, saying who reads which table and what they must get back, in the terms of their job.

- Also: who-sees-what table
- Defined in: [Check who sees what from a decision table](access-policies-as-code.md#check-who-sees-what)
- Address: https://rollingedition.com/concepts/data-governance/decision-table

## deny by default

With default allow := false, a request that no allow rule matches is denied, whoever sends it and whatever it asks for.

- Also: default deny
- A kind of: fail-safe defaults
- Defined in: [Deny by default, then allow by role](access-policies-as-code.md#deny-by-default-then-allow-by-role)
- Address: https://rollingedition.com/concepts/data-governance/deny-by-default

## deny list

a Presidio deny list of the names the platform knows: every word of every instructor's name

- Also: deny lists
- True for: presidio-analyzer 2.2.366
- Defined in: [Replace personal data in the text, then measure what's left](governing-data-for-ai.md#replace-personal-data)
- Address: https://rollingedition.com/concepts/data-governance/deny-list

## deploy

the deploy, which writes the metadata into the catalog and sets every table's generated properties

- Defined in: [Governance in CI](governance-in-ci.md)
- Address: https://rollingedition.com/concepts/data-governance/deploy

## deprecated

Any element of a contract, a schema object or a property, nested ones included, may set the optional deprecated boolean to signal that it is no longer recommended for use

- Defined in: [Deprecate a column before removing it](governance-in-ci.md#deprecate-before-removing)
- Address: https://rollingedition.com/concepts/data-governance/odcs-deprecated

## deprecation rule

Our second rule makes the deprecation warning a required step: a column may leave a table only once the main branch has marked it deprecated.

- Defined in: [Deprecate a column before removing it](governance-in-ci.md#deprecate-before-removing)
- Address: https://rollingedition.com/concepts/data-governance/deprecation-rule

## differencing

Differencing, comparing consecutive reports, is the attack Denning, Denning and Schwartz called a tracker.

- Also: tracker
- Contrasts with: minimum group size
- Defined in: [Hold back small groups in reports](enforcing-policies-on-queries.md#hold-back-small-groups)
- Address: https://rollingedition.com/concepts/data-governance/differencing

## DIRECT

DIRECT means the output value is derived from the input value, through IDENTITY, TRANSFORMATION or AGGREGATION.

- Also: DIRECT input
- Contrasts with: INDIRECT
- Defined in: [Add the inputs that decide which rows exist](lineage-from-pipelines.md#add-indirect-inputs)
- Address: https://rollingedition.com/concepts/data-pipelines/direct-input

## doc

each column can carry a doc, an optional comment that travels with the schema

- True for: pyiceberg 0.12.0
- Defined in: [Write descriptions into the table's schema](a-catalog-you-can-test.md#write-descriptions-into-the-schema)
- Address: https://rollingedition.com/concepts/data-warehousing/doc

## domain

a domain, the part of the business the table belongs to

- Part of: metadata
- Defined in: [Keep the metadata in a reviewed file](a-catalog-you-can-test.md#keep-metadata-in-a-reviewed-file)
- Address: https://rollingedition.com/concepts/data-governance/domain

## domain rule

Each domain has a package of its own, owned by its team

- Also: domain rules
- Defined in: [Layer domain rules on the global rules](governance-in-ci.md#run-global-and-domain-rules)
- Address: https://rollingedition.com/concepts/data-governance/domain-rule

## effective false positive

Google's Tricorder authors define an effective false positive as any report that a user chooses not to act on

- Defined in: [Count waived findings per check](governance-in-ci.md#count-waived-findings)
- Address: https://rollingedition.com/concepts/data-governance/effective-false-positive

## enforcement layer

The book's shared module lib.enforce enforces decisions; we call it the enforcement layer.

- Defined in: [Enforcing policies on queries](enforcing-policies-on-queries.md)
- Address: https://rollingedition.com/concepts/data-governance/enforcement-layer

## engine query log

its logging framework has a QueryLog type, which records the queries DuckDB executes, turned on with CALL enable_logging('QueryLog') and read from the duckdb_logs view

- Also: query log, DuckDB's query log
- True for: duckdb 2.0.0
- Contrasts with: audit log
- Defined in: [Cross-check the log against DuckDB's query log](audit-and-evidence.md#cross-check-the-query-log)
- Address: https://rollingedition.com/concepts/data-governance/engine-query-log

## equality delete

equality deletes, which mark it by the values of one or more columns

- Also: equality deletes
- Defined in: [Delete expired rows with row deletes](retention-consent-erasure.md#delete-expired-rows)
- Address: https://rollingedition.com/concepts/data-warehousing/equality-delete

## erasure

Erasure is removing a person's data on request.

- Defined in: [Retention, consent and erasure](retention-consent-erasure.md)
- Address: https://rollingedition.com/concepts/data-governance/erasure

## erasure register

an erasure register: for each request, its ID and a keyed hash (HMAC-SHA256) of the erased learner's ID, and nothing else

- Defined in: [An erased learner comes back](retention-consent-erasure.md#erased-learner-comes-back)
- Address: https://rollingedition.com/concepts/data-governance/erasure-register

## erasure scan

lib.retention.scan reads every file under the catalog's warehouse, each with its own format's reader, and looks for the learner's traces.

- Defined in: [Prove the erasure by reading every file](retention-consent-erasure.md#verify-the-erasure)
- Address: https://rollingedition.com/concepts/data-governance/erasure-scan

## evidence

Evidence is a report that shows a control works, generated from records rather than captured from a screen.

- Defined in: [Audit and evidence](audit-and-evidence.md)
- Address: https://rollingedition.com/concepts/data-governance/evidence

## exact matching

Exact matching, from the CoNLL-2003 shared task, counts an entity "correct only if it is an exact match of the corresponding entity in the data file"

- Contrasts with: overlap matching
- Measured from: truth
- Defined in: [Measure a detector against labelled spans](finding-personal-data.md#measure-against-labelled-spans)
- Address: https://rollingedition.com/concepts/data-governance/exact-matching

## facet

A facet is OpenLineage's name for a block of metadata attached to a run, a job or a dataset

- Also: facets
- Defined in: [Send a run event from every pipeline](lineage-from-pipelines.md#send-run-events)
- Address: https://rollingedition.com/concepts/data-pipelines/facet

## fail-safe defaults

Saltzer and Schroeder's principle of fail-safe defaults is to "Base access decisions on permission rather than exclusion"

- Defined in: [Deny by default, then allow by role](access-policies-as-code.md#deny-by-default-then-allow-by-role)
- Address: https://rollingedition.com/concepts/data-governance/fail-safe-defaults

## federated computational governance

federated computational governance, "a set of global rules - rules applied to all data products and their interfaces - to ensure a healthy and interoperable ecosystem"

- Defined in: [Layer domain rules on the global rules](governance-in-ci.md#run-global-and-domain-rules)
- Address: https://rollingedition.com/concepts/data-governance/federated-computational-governance

## field ID

Iceberg gives every column a field ID, an integer unique within the table's schema

- Also: field IDs
- True for: pyiceberg 0.12.0
- Defined in: [Key column metadata by field ID](a-catalog-you-can-test.md#key-column-metadata-by-field-id)
- Address: https://rollingedition.com/concepts/data-warehousing/field-id

## finding already on main

A finding already on main is reported on every run, counted and named with the team that owns it, but it fails no pull request that leaves it as it is.

- Also: findings already on main
- Defined in: [Run every check as one job](governance-in-ci.md#run-every-rule-as-one-job)
- Address: https://rollingedition.com/concepts/data-governance/finding-on-main

## finding ID

A violation's subject and the rule's name make the finding's ID.

- Also: finding IDs
- Defined in: [Layer domain rules on the global rules](governance-in-ci.md#run-global-and-domain-rules)
- Address: https://rollingedition.com/concepts/data-governance/finding-id

## function with side effects

has_side_effects is "true if this function changes the database state"

- Also: has_side_effects
- Defined in: [Allow only catalog tables, CTEs and subqueries](enforcing-policies-on-queries.md#allow-only-catalog-sources)
- Address: https://rollingedition.com/concepts/data-governance/function-with-side-effects

## gate

On a pull request, a check is a gate: it runs on every change, before the change merges, and it fails the pull request through its exit code.

- Also: gates
- Defined in: [Run every check as one job](governance-in-ci.md#run-every-rule-as-one-job)
- Address: https://rollingedition.com/concepts/data-governance/gate

## global rule

The platform team keeps one package of global rules, which the domains agree on

- Also: global rules
- Defined in: [Layer domain rules on the global rules](governance-in-ci.md#run-global-and-domain-rules)
- Address: https://rollingedition.com/concepts/data-governance/global-rule

## greedy decoding

The script decodes greedily, taking the most likely next token

- Defined in: [Draft metadata with a local model](a-catalog-you-can-test.md#draft-descriptions-with-a-local-model)
- Address: https://rollingedition.com/concepts/data-engineering/greedy-decoding

## hash chain

A hash chain detects a change to a log that's still growing: every record carries a sequence number, seq, and the SHA-256 of the line before it, prev_hash, so changing a record breaks the link to the next one, and removing one leaves a gap.

- Also: chain
- Defined in: [Chain the records so an edit shows](audit-and-evidence.md#chain-the-records)
- Address: https://rollingedition.com/concepts/data-governance/hash-chain

## head

a chain's head, the number of records and the hash of the last one, written down where the log's writer can't change it

- Also: chain head
- Part of: hash chain
- Defined in: [Chain the records so an edit shows](audit-and-evidence.md#chain-the-records)
- Address: https://rollingedition.com/concepts/data-governance/chain-head

## HMAC

HMAC is the construction RFC 2104 describes for keying a hash

- Defined in: [Keep pseudonyms consistent with a keyed hash](governing-data-for-ai.md#consistent-pseudonyms)
- Address: https://rollingedition.com/concepts/data-engineering/hmac

## IDENTITY edge

a column copied unchanged, an IDENTITY edge in OpenLineage's terms

- Also: IDENTITY edges
- Defined in: [Plan an erasure from lineage](retention-consent-erasure.md#plan-erasure-from-lineage)
- Address: https://rollingedition.com/concepts/data-pipelines/identity-edge

## impact analysis

Impact analysis asks what a change to one column can break.

- Computed from: lineage graph
- Defined in: [Find what a column change breaks](lineage-from-pipelines.md#impact-of-a-column-change)
- Address: https://rollingedition.com/concepts/data-pipelines/impact-analysis

## implicit flow

Denning calls the information that flows through conditions "implicit flow": a statement that assigns only when a condition holds still tells you the condition's value

- Defined in: [Add the inputs that decide which rows exist](lineage-from-pipelines.md#add-indirect-inputs)
- Address: https://rollingedition.com/concepts/data-governance/implicit-flow

## INDIRECT

INDIRECT means the output value is impacted by an input without being derived from it, through JOIN, GROUP_BY, FILTER, SORT, WINDOW or CONDITIONAL.

- Also: INDIRECT input
- Contrasts with: DIRECT
- Defined in: [Add the inputs that decide which rows exist](lineage-from-pipelines.md#add-indirect-inputs)
- Address: https://rollingedition.com/concepts/data-pipelines/indirect-input

## input

The service sends a JSON document describing the request, and the policy reads it as input.

- Defined in: [Shape the request like Trino's](access-policies-as-code.md#shape-the-request-like-trinos)
- Address: https://rollingedition.com/concepts/data-governance/policy-input

## job

A job is "a process that consumes or produces Datasets", such as a pipeline.

- Also: jobs
- Defined in: [Send a run event from every pipeline](lineage-from-pipelines.md#send-run-events)
- Address: https://rollingedition.com/concepts/data-pipelines/job

## keyed pseudonym

lib.ai_data.pseudonym computes an HMAC with SHA-256 of the entity type and the case-folded value, under a key only the corpus job holds, and keeps eight hexadecimal digits

- Also: keyed pseudonyms
- Computed from: HMAC
- Defined in: [Keep pseudonyms consistent with a keyed hash](governing-data-for-ai.md#consistent-pseudonyms)
- Address: https://rollingedition.com/concepts/data-governance/keyed-pseudonym

## last4

last4 keeps the last four digits of a card number, after removing anything that isn't a digit.

- A kind of: column mask
- Defined in: [Write each mask as SQL in one place](enforcing-policies-on-queries.md#write-masks-as-sql)
- Address: https://rollingedition.com/concepts/data-governance/last4

## lineage

Lineage is where each column's data came from, and where it goes.

- Defined in: [Lineage from pipelines](lineage-from-pipelines.md)
- Address: https://rollingedition.com/concepts/data-pipelines/lineage

## lineage graph

With column lineage in every COMPLETE event, the platform has a graph: columns are nodes, and each input field is an edge to the column or table it feeds.

- Computed from: column lineage
- Defined in: [Find what a column change breaks](lineage-from-pipelines.md#impact-of-a-column-change)
- Address: https://rollingedition.com/concepts/data-pipelines/lineage-graph

## locality-sensitive hashing

LSH cuts each signature into b bands of r rows

- Also: LSH
- True for: datasketch 2.0.0
- Computed from: MinHash signature
- Implemented by: datasketch 2.0.0
- Defined in: [Tune LSH for recall, then confirm every pair](governing-data-for-ai.md#tune-lsh-then-confirm)
- Address: https://rollingedition.com/concepts/data-engineering/lsh

## manifest

a manifest lists data files, with each file's column statistics

- Also: manifests
- Defined in: [Remove the files no snapshot references](retention-consent-erasure.md#remove-unreferenced-files)
- Address: https://rollingedition.com/concepts/data-warehousing/manifest

## masking flag

OpenLineage's masking flag says only that a value was obfuscated, such as by a hash

- Defined in: [Propose classifications from lineage](lineage-from-pipelines.md#classifications-from-lineage)
- Address: https://rollingedition.com/concepts/data-pipelines/masking-flag

## merge-on-read

Merge-on-read leaves the data file alone and writes a delete file beside it.

- Contrasts with: copy-on-write
- Defined in: [Delete expired rows with row deletes](retention-consent-erasure.md#delete-expired-rows)
- Address: https://rollingedition.com/concepts/data-warehousing/merge-on-read

## metadata

A catalog's metadata is what you know about each table that the data doesn't say: who owns it, which part of the business it belongs to, what it holds, and how each column must be protected.

- Defined in: [Keep the metadata in a reviewed file](a-catalog-you-can-test.md#keep-metadata-in-a-reviewed-file)
- Address: https://rollingedition.com/concepts/data-governance/metadata

## metrics mode

Iceberg lets a table choose, per column, what its manifests keep, with the property write.metadata.metrics.column.<name>: none keeps nothing, counts keeps value and null counts, truncate(n) adds bounds cut to n characters, and full adds whole bounds

- Also: metrics modes
- True for: pyiceberg 0.12.0
- Defined in: [Keep personal values out of manifests](retention-consent-erasure.md#keep-values-out-of-manifests)
- Address: https://rollingedition.com/concepts/data-warehousing/metrics-mode

## migration

A schema change on the platform is a migration, an alter table statement in a file in the branch's migrations/ folder.

- Defined in: [Fail the pull request that adds an unclassified column](governance-end-to-end.md#fail-the-pull-request)
- Address: https://rollingedition.com/concepts/data-warehousing/migration

## MinHash signature

Taking the smallest shingle under each of many permutations gives a MinHash signature, which estimates the similarity of two texts without comparing their sets

- Also: MinHash signatures, MinHash
- True for: datasketch 2.0.0
- Computed from: shingle
- Implemented by: datasketch 2.0.0
- Defined in: [Find near-duplicates with MinHash](governing-data-for-ai.md#near-duplicates-with-minhash)
- Address: https://rollingedition.com/concepts/data-engineering/minhash-signature

## minimum group size

The usual defence is a minimum group size, below which a reported group is held back.

- Defined in: [Hold back small groups in reports](enforcing-policies-on-queries.md#hold-back-small-groups)
- Address: https://rollingedition.com/concepts/data-governance/minimum-group-size

## model draft

a model's draft is a proposal that a person accepts, corrects or rejects in the pull request

- Also: model drafts
- Defined in: [Draft metadata with a local model](a-catalog-you-can-test.md#draft-descriptions-with-a-local-model)
- Address: https://rollingedition.com/concepts/data-governance/model-draft

## near-duplicate

A confirmed pair at 0.8 or more is a near-duplicate, unless it differs only in a name

- Also: near-duplicates
- Defined in: [Find near-duplicates with MinHash](governing-data-for-ai.md#near-duplicates-with-minhash)
- Address: https://rollingedition.com/concepts/data-engineering/near-duplicate

## NLP engine

The NLP engine does two jobs, named-entity recognition and feature extraction for rules, such as the context words that raise a score.

- True for: presidio-analyzer 2.2.366
- Defined in: [Run Presidio offline](finding-personal-data.md#run-presidio-offline)
- Address: https://rollingedition.com/concepts/data-governance/nlp-engine

## noise

measure each check's noise by the findings nobody acts on

- Defined in: [Governance in CI](governance-in-ci.md)
- Address: https://rollingedition.com/concepts/data-governance/noise

## normalized query

lib.audit.normalized keeps the query's shape and drops its values: sqlglot parses the query, and every literal, in any of DuckDB's syntaxes, becomes ?.

- Also: normalized text
- True for: sqlglot 30.33.0
- Defined in: [Keep values out of the record](audit-and-evidence.md#keep-values-out-of-the-record)
- Address: https://rollingedition.com/concepts/data-governance/normalized-query

## not-useful rate

the not-useful rate: an analyzer's Not useful clicks as a share of its Not useful, Please fix and Apply fix clicks

- Defined in: [Count waived findings per check](governance-in-ci.md#count-waived-findings)
- Address: https://rollingedition.com/concepts/data-governance/not-useful-rate

## overlap matching

Overlap matching asks only for one shared character, with a label of its type

- Measured from: truth
- Defined in: [Measure a detector against labelled spans](finding-personal-data.md#measure-against-labelled-spans)
- Address: https://rollingedition.com/concepts/data-governance/overlap-matching

## owner

an owner, the team answerable for the table, never a person

- Part of: metadata
- Defined in: [Keep the metadata in a reviewed file](a-catalog-you-can-test.md#keep-metadata-in-a-reviewed-file)
- Address: https://rollingedition.com/concepts/data-governance/owner

## owner rule

We add a first rule of our own: lowering a column's classification, changing a table's owner, or moving a table to another domain needs the approval of the team that owns the table on the main branch.

- Defined in: [Ask the owner before lowering a classification](governance-in-ci.md#ask-the-owner-before-lowering)
- Address: https://rollingedition.com/concepts/data-governance/owner-rule

## partial evaluation

Cedar's experimental partial evaluation, which returns residual policies for the parts it can't yet decide, and whose result is not a final authorization decision

- Defined in: [Write the same rules in Cedar](access-policies-as-code.md#the-same-rules-in-cedar)
- Address: https://rollingedition.com/concepts/data-governance/partial-evaluation

## personal data

The GDPR defines personal data as "any information relating to an identified or identifiable natural person"

- Defined in: [Keep values out of the record](audit-and-evidence.md#keep-values-out-of-the-record)
- Address: https://rollingedition.com/concepts/data-governance/personal-data

## PII

The authors of the SPY dataset define PII as the entities that can identify, contact or locate a specific individual

- Also: personally identifiable information
- Defined in: [Compare a PII model](finding-personal-data.md#compare-a-named-entity-model)
- Address: https://rollingedition.com/concepts/data-governance/pii

## PII model

We use a PII model, one trained for personally identifiable information

- A kind of: PII
- Defined in: [Compare a PII model](finding-personal-data.md#compare-a-named-entity-model)
- Address: https://rollingedition.com/concepts/data-governance/pii-model

## platform team

the platform team, the team answerable for tables without an owner

- Defined in: [Fail the pull request that adds an unclassified column](governance-end-to-end.md#fail-the-pull-request)
- Address: https://rollingedition.com/concepts/data-governance/platform-team

## policy

A policy is code that answers whether a request may go ahead.

- Also: policies
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/policy

## policy revision

A policy revision is a fingerprint of everything a decision depended on besides the request.

- Also: revision
- Defined in: [Audit and evidence](audit-and-evidence.md)
- Address: https://rollingedition.com/concepts/data-governance/policy-revision

## policy test

a test is a rule whose name is prefixed with test_

- Also: policy tests
- Defined in: [Unit-test the policy in Rego](access-policies-as-code.md#unit-test-the-policy-in-rego)
- Address: https://rollingedition.com/concepts/data-governance/policy-test

## policy validation

Validation checks policies against a schema before any request

- Also: validation
- Defined in: [Write the same rules in Cedar](access-policies-as-code.md#the-same-rules-in-cedar)
- Address: https://rollingedition.com/concepts/data-governance/policy-validation

## position delete

position deletes, which mark a row by its data file and its position

- Also: position deletes
- Defined in: [Delete expired rows with row deletes](retention-consent-erasure.md#delete-expired-rows)
- Address: https://rollingedition.com/concepts/data-warehousing/position-delete

## pre-commit hook

A pre-commit hook is the other place a check can run, on the author's machine, before a commit exists.

- Also: pre-commit hooks
- Contrasts with: gate
- Defined in: [Gate the pull request, not the commit](governance-in-ci.md#gate-the-pull-request)
- Address: https://rollingedition.com/concepts/data-engineering/pre-commit-hook

## precision

precision, the share of each label's detections that match a labelled span

- Measured from: truth
- Defined in: [Measure a detector against labelled spans](finding-personal-data.md#measure-against-labelled-spans)
- Address: https://rollingedition.com/concepts/data-governance/precision

## principal

The principal is who asks

- Also: principals
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/principal

## property id

ODCS defines a property's id as "A unique identifier for the element used to create stable, refactor-safe references"

- Defined in: [Route each domain's reviews by path](governance-in-ci.md#a-folder-and-a-code-owner-per-domain)
- Address: https://rollingedition.com/concepts/data-governance/odcs-property-id

## prov:wasDerivedFrom

the tables the pipeline's own SQL reads, which the values come from, as prov:wasDerivedFrom

- Defined in: [Generate the dataset card from the run](governing-data-for-ai.md#generate-the-dataset-card)
- Address: https://rollingedition.com/concepts/data-governance/prov-was-derived-from

## prov:wasInfluencedBy

the table the enforcement layer's rewrite adds, which only decides which rows exist, as prov:wasInfluencedBy

- Defined in: [Generate the dataset card from the run](governing-data-for-ai.md#generate-the-dataset-card)
- Address: https://rollingedition.com/concepts/data-governance/prov-was-influenced-by

## provenance

Provenance at the level of the record answers three questions: which table it came from, which row, and which run of which job put it in the corpus.

- Defined in: [Carry provenance on every record](governing-data-for-ai.md#carry-provenance)
- Address: https://rollingedition.com/concepts/data-governance/provenance

## pseudonym

a pseudonym: a token for one name, the same wherever that name appears

- Also: pseudonyms
- Defined in: [Keep pseudonyms consistent with a keyed hash](governing-data-for-ai.md#consistent-pseudonyms)
- Address: https://rollingedition.com/concepts/data-governance/pseudonym

## pseudonymization

pseudonymization, which replaces an identifier with a consistent stand-in

- A kind of: column mask
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/pseudonymization

## pseudonymize

pseudonymize is a keyed hash, SHA-256 over the key followed by the value

- Also: keyed hash
- A kind of: column mask
- Defined in: [Write each mask as SQL in one place](enforcing-policies-on-queries.md#write-masks-as-sql)
- Address: https://rollingedition.com/concepts/data-governance/pseudonymize

## pseudonymous identifier

An ID with no meaning of its own, such as learner_id, is a pseudonymous identifier: it doesn't name anyone, but it leads to someone through another table.

- Also: pseudonymous ID, pseudonymous IDs
- Defined in: [Classify pseudonymous IDs for joining](a-catalog-you-can-test.md#classify-pseudonymous-ids)
- Address: https://rollingedition.com/concepts/data-governance/pseudonymous-identifier

## purpose

The purpose is an attribute of the request.

- Defined in: [Narrow by attribute: region, consent and purpose](access-policies-as-code.md#narrow-by-attribute)
- Address: https://rollingedition.com/concepts/data-governance/purpose

## qualify

sqlglot parses a query into a tree, and its qualify step resolves every column against a schema, qualifies it with its table, and expands * into the columns it stands for when it has a schema to expand against

- True for: sqlglot 30.33.0
- Implemented by: sqlglot 30.33.0
- Defined in: [Find every table and column a query reads](enforcing-policies-on-queries.md#find-what-a-query-reads)
- Address: https://rollingedition.com/concepts/data-engineering/qualify

## recall

recall, the share of labelled spans of each type that a detector finds with a label of that type

- Measured from: truth
- Defined in: [Measure a detector against labelled spans](finding-personal-data.md#measure-against-labelled-spans)
- Address: https://rollingedition.com/concepts/data-governance/recall

## recognizer

Presidio's analyzer runs recognizers: regular expressions with checksums, phone-number parsing, and a named-entity model reached through an NLP engine.

- Also: recognizers
- True for: presidio-analyzer 2.2.366
- Implemented by: presidio-analyzer 2.2.366
- Defined in: [Run Presidio offline](finding-personal-data.md#run-presidio-offline)
- Address: https://rollingedition.com/concepts/data-governance/recognizer

## recording manifest

The recording's manifest names the model, its revision, a hash of the prompts and settings, and the date, so anyone can record again and compare.

- Defined in: [Draft metadata with a local model](a-catalog-you-can-test.md#draft-descriptions-with-a-local-model)
- Address: https://rollingedition.com/concepts/data-governance/recording-manifest

## redact

redact is a NULL cast to the column's type, so the column keeps its type for anything the query does with it, such as a union or a date function.

- A kind of: column mask
- Defined in: [Write each mask as SQL in one place](enforcing-policies-on-queries.md#write-masks-as-sql)
- Address: https://rollingedition.com/concepts/data-governance/redact

## redact_contacts

redact_contacts replaces emails and phone numbers in free text with [email] and [phone].

- A kind of: column mask
- Defined in: [Write each mask as SQL in one place](enforcing-policies-on-queries.md#write-masks-as-sql)
- Address: https://rollingedition.com/concepts/data-governance/redact-contacts

## resemblance

Broder defined the resemblance of two documents as the Jaccard similarity of their sets of shingles

- Computed from: shingle
- Defined in: [Find near-duplicates with MinHash](governing-data-for-ai.md#near-duplicates-with-minhash)
- Address: https://rollingedition.com/concepts/data-engineering/resemblance

## retention

Retention is how long the platform keeps each kind of data.

- Defined in: [Retention, consent and erasure](retention-consent-erasure.md)
- Address: https://rollingedition.com/concepts/data-governance/retention

## retention rule

A retention rule says how long one kind of data is kept, from which date the time counts, and which rows it applies to.

- Also: retention rules
- Part of: retention
- Defined in: [Keep retention rules in a reviewed file](retention-consent-erasure.md#retention-rules-in-a-file)
- Address: https://rollingedition.com/concepts/data-governance/retention-rule

## rewritten digest

The SQL the layer hands DuckDB is kept only as rewritten_digest, an HMAC-SHA256 under a key only the layer holds, which the cross-check matches against DuckDB's own log.

- Defined in: [Keep values out of the record](audit-and-evidence.md#keep-values-out-of-the-record)
- Address: https://rollingedition.com/concepts/data-governance/rewritten-digest

## role

a role is a group of principals with the same job

- Also: roles
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/role

## role explosion

The alternative, a role for every combination, is what NIST's guide calls "role explosion".

- Contrasts with: attribute-based access control
- Defined in: [Narrow by attribute: region, consent and purpose](access-policies-as-code.md#narrow-by-attribute)
- Address: https://rollingedition.com/concepts/data-governance/role-explosion

## role-based access control

Role-based access control, first formalized by Ferraiolo and Kuhn in 1992, grants access by the job a principal holds rather than by who they are.

- Also: RBAC
- Defined in: [Deny by default, then allow by role](access-policies-as-code.md#deny-by-default-then-allow-by-role)
- Address: https://rollingedition.com/concepts/data-governance/role-based-access-control

## row filter

A row filter limits which rows a query returns

- Also: row filters
- Part of: decision document
- Defined in: [Access policies as code](access-policies-as-code.md)
- Address: https://rollingedition.com/concepts/data-governance/row-filter

## run

A run is one occurrence of a job, identified by a UUID the client generates, and the spec recommends UUIDv7.

- Also: runs
- Part of: job
- Defined in: [Send a run event from every pipeline](lineage-from-pipelines.md#send-run-events)
- Address: https://rollingedition.com/concepts/data-pipelines/run

## run event

A run reports itself through run events: a START when it begins, then one terminal event, COMPLETE, FAIL or ABORT

- Also: run events
- Defined in: [Send a run event from every pipeline](lineage-from-pipelines.md#send-run-events)
- Address: https://rollingedition.com/concepts/data-pipelines/run-event

## scratch platform

lib.ci.build builds a scratch platform the way the platform runs: the source tables, the side's migrations, the deploy, which writes the metadata into the catalog and sets every table's generated properties, then the nightly run of the side's own pipelines, with lineage

- Also: scratch platforms
- Defined in: [Governance in CI](governance-in-ci.md)
- Address: https://rollingedition.com/concepts/data-governance/scratch-platform

## security barrier

In PostgreSQL, a view marked security_barrier keeps "maliciously-chosen functions and operators from being passed values from rows until after the view has done its work"

- Also: security_barrier
- Defined in: [Gate every column on the row filters](enforcing-policies-on-queries.md#gate-columns-on-row-filters)
- Address: https://rollingedition.com/concepts/data-governance/security-barrier

## semi-join

a semi-join, a test that the review's learner_id is among the learners who consented

- Defined in: [Build row filters from the decision's data](enforcing-policies-on-queries.md#build-row-filters-from-data)
- Address: https://rollingedition.com/concepts/data-engineering/semi-join

## shared module

The shared modules, files in examples/lib/ that hold the code many examples need, are yours to open and read

- Also: shared modules
- Defined in: [Governance end to end](governance-end-to-end.md)
- Address: https://rollingedition.com/concepts/data-engineering/shared-module

## shingle

shingles, the overlapping runs of characters or words in a text

- Also: shingles
- Defined in: [Find near-duplicates with MinHash](governing-data-for-ai.md#near-duplicates-with-minhash)
- Address: https://rollingedition.com/concepts/data-engineering/shingle

## skip on error

skip on error, which the documentation defines as "if a policy's evaluation returns error, the policy does not factor into the authorization response; it is skipped"

- Defined in: [Write the same rules in Cedar](access-policies-as-code.md#the-same-rules-in-cedar)
- Address: https://rollingedition.com/concepts/data-governance/skip-on-error

## snapshot expiry

Expiry removes snapshots, not files.

- Also: expiry
- True for: pyiceberg 0.12.0
- Defined in: [Remove the files no snapshot references](retention-consent-erasure.md#remove-unreferenced-files)
- Address: https://rollingedition.com/concepts/data-warehousing/snapshot-expiry

## source allowlist

Enforcer.check_sources walks the whole query and requires every FROM and JOIN source, at every level, to be a catalog table, a CTE in scope or a subquery, and a LATERAL to be over a subquery.

- Part of: enforcement layer
- Defined in: [Allow only catalog tables, CTEs and subqueries](enforcing-policies-on-queries.md#allow-only-catalog-sources)
- Address: https://rollingedition.com/concepts/data-governance/source-allowlist

## storage limitation

personal data are to be "kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed"

- Defined in: [Keep retention rules in a reviewed file](retention-consent-erasure.md#retention-rules-in-a-file)
- Address: https://rollingedition.com/concepts/data-governance/storage-limitation

## table property

A table also has properties, a map of strings

- Also: table properties
- True for: pyiceberg 0.12.0
- Defined in: [Write descriptions into the table's schema](a-catalog-you-can-test.md#write-descriptions-into-the-schema)
- Address: https://rollingedition.com/concepts/data-warehousing/table-property

## table rewrite

Enforcer.rewrite replaces each catalog table in the query, under the query's own alias for it, with a subquery built from the user's decision

- Part of: enforcement layer
- Defined in: [Replace each table with a filtered, masked subquery](enforcing-policies-on-queries.md#replace-each-table)
- Address: https://rollingedition.com/concepts/data-governance/table-rewrite

## tamper-evident

A log is tamper-evident when a change to it can be detected, though not prevented.

- Defined in: [Audit and evidence](audit-and-evidence.md)
- Address: https://rollingedition.com/concepts/data-governance/tamper-evident

## trace

lib.retention.traces notes the traces before the erasure: the IDs of every row the plan deletes, by column, and the first 15 characters, lowercased, of each identifying value.

- Also: traces
- Comes before: erasure scan
- Defined in: [Prove the erasure by reading every file](retention-consent-erasure.md#verify-the-erasure)
- Address: https://rollingedition.com/concepts/data-governance/trace

## truth

Every detector in this chapter is measured against one file, which we call the truth: data/platform/pii_spans.parquet.

- Defined in: [Finding personal data](finding-personal-data.md)
- Address: https://rollingedition.com/concepts/data-governance/truth

## type promotion

The spec's valid primitive type promotions are int to long, float to double, and a decimal's precision, which may only widen, plus, in format v3, date to timestamp or timestamp_ns, and a column of type unknown to any type.

- Also: type promotions
- Defined in: [Report what a schema change reaches](governance-in-ci.md#report-what-a-schema-change-reaches)
- Address: https://rollingedition.com/concepts/data-warehousing/type-promotion

## undefined

A rule whose body never evaluates to true has no value, which Rego calls undefined

- Defined in: [Deny by default, then allow by role](access-policies-as-code.md#deny-by-default-then-allow-by-role)
- Address: https://rollingedition.com/concepts/data-governance/undefined

## unreferenced file

An unreferenced file, which Iceberg calls an orphan, is under the table's location but in no snapshot's metadata.

- Also: unreferenced files, orphan file, orphan files
- Defined in: [Remove the files no snapshot references](retention-consent-erasure.md#remove-unreferenced-files)
- Address: https://rollingedition.com/concepts/data-warehousing/unreferenced-file

## waiver

On the platform, the decision not to act on a new finding is a waiver.

- Also: waivers
- Defined in: [Count waived findings per check](governance-in-ci.md#count-waived-findings)
- Address: https://rollingedition.com/concepts/data-governance/waiver
