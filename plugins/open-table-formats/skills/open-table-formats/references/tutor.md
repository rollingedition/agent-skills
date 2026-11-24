---
title: "Tutor"
book: "Open Table Formats"
edition: "2026.11.16"
---

# Teaching *Open Table Formats*

How to teach *Open Table Formats*, Edition 2026.11.16, when someone asks to be taught, tutored or quizzed on it, as "Teach this book, when asked" in `SKILL.md` says, then every chapter's sections. The method is adapted from Jane Street's socratic-tutor skill, under MIT: `LICENSE.md` keeps its notice.

## How to teach it

**The topics** are the book's chapters, in order:

1. [Build a first table, end to end](first-table.md)
2. [Read a table as it was at an earlier snapshot](snapshots-and-time-travel.md)
3. [Add and rename columns without rewriting files](evolving-schema.md)
4. [Change partitioning without rewriting old files](partition-evolution.md)
5. [Correct rows with deletes, updates and merges](corrections-and-merges.md)
6. [Compact the small files that hourly appends leave](compaction.md)
7. [Expire snapshots and remove unreferenced files](expiry-and-cleanup.md)
8. [Register tables in a catalog and query them from DuckDB](catalogs.md)
9. [Move a table between formats and check the copy](migrating-formats.md)
10. [Choose a format from what your tools support](choosing-a-format.md)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. "The book's sections", below, lists each chapter's sections, with the examples each one runs and the terms it defines.

**Start**

1. Read each section before you ask about it. Judge every answer against the book: the section's text, the term's definition in `glossary.md`, beside this file, and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" in `SKILL.md`.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
Build a first table, end to end    overall: █████░░░░░ 53%
---------------------------------------------------------------------------
What a table format adds to files                   ████████░░  4/5  alone
Why each format is taught through a Python library  ██████░░░░  3/5  <- now
Land three hours in a table                         ██░░░░░░░░  1/5
---------------------------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what its script in `scripts/` will print, or what will change if they change one line. Then have them run it, as `SKILL.md` shows, and compare with its `.out` file. Check the output they got, not their account of it.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/open-table-formats/s/ followed by its ID.

**Levels are earned**

- Raise a level only after two or more separate checks, at least one of them recalled unprompted, not just after you told them the answer.
- A vague or partly right answer isn't right. Probe until you know. Never credit them with an insight they didn't state.
- Now and then, without warning, ask again about an earlier topic. If they miss, lower its level and go back to it.
- Level 5 needs an edge case or a hard question handled, and an explanation you'd trust them to teach from.
- No flattery: "Not quite: why would X happen if Y were true?" beats "Great try!"

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures in `SKILL.md` covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

After the exam, tell them once that each chapter's page on rollingedition.com ends with exercises from its examples (a chapter's page is the `canonical` link in its front matter, beside this file), and that with Rolling Edition Labs, Submit checks an answer by running it at this edition's pinned versions. Say it plainly, and never make the tutoring wait for it: everything here is free.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.16 and its code `XR7P-ZXAG`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/open-table-formats/changes lists them.

## The book's sections

Each chapter of Edition 2026.11.16 and its sections, in order, with the examples each section runs and the terms it defines. Each section links to its place in the chapter beside this file, and each script is in `scripts/`. Read a section before you ask about it.

### 1. Build a first table, end to end

[The chapter](first-table.md).

- [What a table format adds to files](first-table.md#what-a-table-format-adds). Runs `scripts/rough-lakehouse.py`. Defines: commit, manifest, manifest list, metadata, metadata file.
  - [One load loop, three commit styles](first-table.md#one-load-loop).
  - [A commit names the table's files](first-table.md#files-metadata-and-commit). Defines: append, snapshot.
- [Why each format is taught through a Python library](first-table.md#why-python-libraries).
- [Land three hours in a table](first-table.md#land-three-hours).
  - [Create the table in a catalog](first-table.md#create-catalog-and-table). Defines: catalog.
  - [Append each hour as a commit](first-table.md#append-each-hour). Runs `scripts/append-hours.py`. Defines: snapshot ID, snapshot summary.
- [Query the table with DuckDB](first-table.md#query-with-duckdb). Runs `scripts/scan-into-duckdb.py`. Defines: scan.
- [What goes wrong in production](first-table.md#first-table-production-failures).
- [Decisions this chapter made](first-table.md#first-table-decisions).

### 2. Read a table as it was at an earlier snapshot

[The chapter](snapshots-and-time-travel.md).

- [Every data commit leaves a snapshot](snapshots-and-time-travel.md#every-commit-is-a-snapshot). Runs `scripts/snapshot-history.py`. Defines: operation, version.
  - [What a snapshot points to](snapshots-and-time-travel.md#what-a-snapshot-points-to).
- [Read an earlier snapshot](snapshots-and-time-travel.md#read-an-earlier-snapshot).
  - [Snapshots in pyiceberg](snapshots-and-time-travel.md#snapshots-in-pyiceberg). Runs `scripts/read-as-of-snapshot.py`.
  - [Read a commit by its number in each format](snapshots-and-time-travel.md#versions-in-ducklake-and-delta). Runs `scripts/three-version-numbers.py`. Defines: DuckLake snapshot.
- [What goes wrong in production](snapshots-and-time-travel.md#snapshot-production-failures).
- [Decisions this chapter made](snapshots-and-time-travel.md#snapshot-decisions).

### 3. Add and rename columns without rewriting files

[The chapter](evolving-schema.md).

- [Columns are tracked by ID](evolving-schema.md#columns-tracked-by-id). Defines: column mapping, display name, field ID, physical name.
- [Add load_batch after three hours](evolving-schema.md#add-response-bytes). Runs `scripts/add-column-to-existing-files.py`.
  - [Old files read as null](evolving-schema.md#old-files-read-as-null).
- [Rename a column by its ID without rewriting files](evolving-schema.md#rename-column-without-rewrite). Runs `scripts/rename-by-id.py`.
  - [Delta Lake has no rename at this pin](evolving-schema.md#rename-in-delta-lake). Runs `scripts/delta-rename-trap.py`, `scripts/delta-rename-by-rewrite.py`.
- [What goes wrong in production](evolving-schema.md#schema-production-failures).
- [Decisions this chapter made](evolving-schema.md#schema-decisions).
  - [Sources](evolving-schema.md#schema-sources).

### 4. Change partitioning without rewriting old files

[The chapter](partition-evolution.md).

- [Partition specs are versioned too](partition-evolution.md#partition-specs-are-versioned). Defines: partition spec.
- [Move from daily to hourly partitions](partition-evolution.md#daily-to-hourly-partitions). Runs `scripts/day-then-hour-spec.py`. Defines: day transform, hour transform.
  - [Files written under each spec](partition-evolution.md#files-written-under-each-spec).
- [Check what a query scans](partition-evolution.md#check-what-a-query-scans). Runs `scripts/plan-files-by-partition.py`, `scripts/figure-files-by-spec.py`. Defines: plan count.
- [Partitioning in the other formats](partition-evolution.md#partitioning-in-other-formats). Runs `scripts/delta-partition-overwrite.py`, `scripts/ducklake-partition-alter.py`. Defines: partitionColumns.
- [What goes wrong in production](partition-evolution.md#partition-production-failures).
- [Decisions this chapter made](partition-evolution.md#partition-decisions).

### 5. Correct rows with deletes, updates and merges

[The chapter](corrections-and-merges.md).

- [Late data arrives as a correction](corrections-and-merges.md#late-data-as-correction). Defines: correction, key.
- [Delete rows, and what each format writes](corrections-and-merges.md#delete-rows-iceberg-and-delta). Runs `scripts/delete-low-views.py`. Defines: copy-on-write, delete, delete file, merge-on-read.
  - [Copy-on-write and merge-on-read](corrections-and-merges.md#copy-on-write-and-merge-on-read). Runs `scripts/figure-rows-written-to-delete.py`. Defines: deletion vector.
- [Upsert a corrected hour](corrections-and-merges.md#upsert-corrected-hour). Defines: upsert.
  - [Upserts in pyiceberg](corrections-and-merges.md#upserts-in-pyiceberg). Runs `scripts/redeliver-hour-upsert.py`.
  - [MERGE in DuckLake](corrections-and-merges.md#merge-in-ducklake). Runs `scripts/merge-correction-ducklake.py`. Defines: MERGE.
- [Merge a changed label into the domains table](corrections-and-merges.md#merge-domains-table). Runs `scripts/merge-domains-label.py`. Defines: dimension table.
- [What goes wrong in production](corrections-and-merges.md#corrections-production-failures). Runs `scripts/duplicate-source-keys.py`.
- [Decisions this chapter made](corrections-and-merges.md#corrections-decisions).

### 6. Compact the small files that hourly appends leave

[The chapter](compaction.md). Defines: data file.

- [Hourly appends leave small files](compaction.md#hourly-appends-leave-small-files). Defines: compaction.
- [Compact with optimize.compact()](compaction.md#compact-in-delta-lake). Runs `scripts/file-counts-before-after.py`, `scripts/figure-files-live-and-on-disk.py`.
- [Compact in DuckLake](compaction.md#compact-in-ducklake).
  - [Merge adjacent files](compaction.md#merge-adjacent-files). Runs `scripts/compact-ducklake.py`.
- [Rewrite the table to compact it](compaction.md#compact-iceberg-by-rewriting). Runs `scripts/iceberg-rewrite-by-overwrite.py`.
  - [Why pyiceberg has no rewrite call](compaction.md#why-no-rewrite-call).
- [Check each compaction before you trust it](compaction.md#check-each-compaction).
- [What goes wrong in production](compaction.md#compaction-production-failures).
- [Decisions this chapter made](compaction.md#compaction-decisions).

### 7. Expire snapshots and remove unreferenced files

[The chapter](expiry-and-cleanup.md).

- [Snapshots keep files alive](expiry-and-cleanup.md#snapshots-keep-files-alive). Defines: cleanup, expiry.
- [Expire snapshots with pyiceberg](expiry-and-cleanup.md#expire-snapshots-in-iceberg). Runs `scripts/expire-iceberg-snapshots.py`, `scripts/figure-snapshots-keep-files.py`.
  - [Find orphan files after expiry](expiry-and-cleanup.md#find-orphan-files). Defines: orphan.
- [Vacuum a table with deltalake](expiry-and-cleanup.md#vacuum-in-delta-lake). Runs `scripts/delta-log-retention.py`. Defines: tombstone, vacuum.
  - [Dry run first](expiry-and-cleanup.md#vacuum-dry-run-first). Runs `scripts/vacuum-delta-dry-run.py`. Defines: dry run.
- [Expire and clean up in DuckLake](expiry-and-cleanup.md#expire-and-clean-up-in-ducklake). Runs `scripts/ducklake-expire-cleanup.py`.
- [What goes wrong in production](expiry-and-cleanup.md#maintenance-production-failures).
- [Decisions this chapter made](expiry-and-cleanup.md#maintenance-decisions).

### 8. Register tables in a catalog and query them from DuckDB

[The chapter](catalogs.md).

- [What a catalog holds](catalogs.md#what-a-catalog-holds). Defines: Iceberg REST catalog.
- [Register a table in a SQL catalog](catalogs.md#register-iceberg-in-sql-catalog). Runs `scripts/register-iceberg-table.py`. Defines: SQL catalog.
  - [Register a table from its metadata file](catalogs.md#register-from-metadata-file). Runs `scripts/registered-names-split.py`. Defines: registered name.
- [Attach a DuckLake catalog](catalogs.md#attach-ducklake-catalog). Runs `scripts/attach-ducklake.py`. Defines: data path.
- [Find a table by path, with no catalog](catalogs.md#find-delta-by-path). Runs `scripts/open-delta-by-path.py`.
- [Join tables from two catalogs](catalogs.md#join-tables-from-two-catalogs). Runs `scripts/join-pageviews-and-domains.py`.
- [What goes wrong in production](catalogs.md#catalog-production-failures). Runs `scripts/ducklake-orphan-cleanup-hazard.py`.
- [Decisions this chapter made](catalogs.md#catalog-decisions).

### 9. Move a table between formats and check the copy

[The chapter](migrating-formats.md).

- [What a copy keeps and loses](migrating-formats.md#what-a-copy-keeps-and-loses). Defines: copy.
- [Copy the pageviews table into DuckLake](migrating-formats.md#iceberg-to-ducklake). Runs `scripts/iceberg-to-ducklake-copy.py`. Defines: cutover problem.
- [Copy the Delta table into a pyiceberg table](migrating-formats.md#delta-to-iceberg). Runs `scripts/delta-to-iceberg-copy.py`.
- [Check timestamp precision before the copy](migrating-formats.md#timestamp-precision). Runs `scripts/timestamp-precision-check.py`.
- [Check each copy with a sorted digest](migrating-formats.md#check-copy-with-digest). Runs `scripts/verify-copies-by-digest.py`. Defines: digest.
- [What goes wrong in production](migrating-formats.md#migration-production-failures).
- [Decisions this chapter made](migrating-formats.md#migration-decisions).

### 10. Choose a format from what your tools support

[The chapter](choosing-a-format.md).

- [Measure support before you choose](choosing-a-format.md#measure-support-before-choosing).
- [Read what the pinned tools did](choosing-a-format.md#support-matrix-as-of-pins). Runs `scripts/ducklake-catalog-version.py`.
  - [Writing and reading versions](choosing-a-format.md#matrix-writing-and-reading).
  - [Changing and cleaning up](choosing-a-format.md#matrix-changing-and-cleaning-up). Runs `scripts/ducklake-delete-files.py`, `scripts/ducklake-inlined-delete.py`.
  - [Catalogs and DuckDB](choosing-a-format.md#matrix-catalogs-and-duckdb).
- [pyiceberg writes no version 3 table](choosing-a-format.md#iceberg-v3-and-deletion-vectors). Runs `scripts/iceberg-format-versions.py`.
- [Deletion vectors need a protocol upgrade](choosing-a-format.md#delta-deletion-vectors). Runs `scripts/feature-check.py`. Defines: reader check, reader feature.
- [A checklist for a new table](choosing-a-format.md#checklist-for-new-table).
- [Pick a format from your readers](choosing-a-format.md#choice-decision-guide).
- [What goes wrong in production](choosing-a-format.md#choice-production-failures).
- [Decisions this chapter made](choosing-a-format.md#choice-decisions).
