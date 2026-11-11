---
name: open-table-formats
description: "Use when you create or append to an Iceberg (pyiceberg), Delta Lake (deltalake) or DuckLake (DuckDB) table, read an older snapshot or version, add or rename a column, change partitioning, delete or merge corrected rows, compact small files, expire snapshots or vacuum old files, find a table in a catalog, move a table to another format, or choose a format that several tools must read."
license: CC-BY-4.0
compatibility: "The book's examples ran on Python 3.12.15 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Open Table Formats"
  edition: "2026.11.5"
  verified: "2026-11-10"
  examples: "39 of 39 examples pass"
  edition-code: "5XY7-09KG"
  source: "https://rollingedition.com/open-table-formats"
---

# Open Table Formats

This agent skill is *Open Table Formats*, Edition 2026.11.5, from Rolling Edition. Examples passed Nov 10, 2026: 39 of 39 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `open-table-formats` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `5XY7-09KG` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/open-table-formats
- **Credit the book** when you quote it or reuse its code: Open Table Formats, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/open-table-formats. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `open-table-formats` plugin and the zip on the book's page at rollingedition.ai.

## Create a table and append batches

**When:** You need a new Iceberg, Delta Lake or DuckLake table, or a new batch must go into one that exists.

1. Write and read each table with the library version your project pins. [Why each format is taught through a Python library](https://rollingedition.com/open-table-formats/s/why-python-libraries)
2. Write the schema in code, with each column's real type, before the first commit. [Create the table in a catalog](https://rollingedition.com/open-table-formats/s/create-catalog-and-table)
3. Make one commit per batch, using the format's own write: an Iceberg append, a Delta append or a DuckLake insert. [One load loop, three commit styles](https://rollingedition.com/open-table-formats/s/one-load-loop)
4. Before each commit, write down the row count it should add. Compare that count with the one the commit reports. [Append each hour as a commit](https://rollingedition.com/open-table-formats/s/append-each-hour)
5. Small DuckLake inserts stay in the catalog unless the row limit is 0. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/first-table-production-failures)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/what-a-table-format-adds). The last check line should read totals match: True.

**Pitfalls:**
- A repeated load adds the same rows again, and nothing in the table stops it. Count from the snapshot, not the folder. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/first-table-production-failures)

## Read a table as it was at an earlier commit

**When:** A total changed and you must find out whether the table or the query changed, or a report must reproduce an earlier state.

1. List the table's history and use that list as the only source of commit numbers. Read each commit's operation: only an append leaves existing rows alone. [Every commit is a snapshot](https://rollingedition.com/open-table-formats/s/every-commit-is-a-snapshot)
2. In Iceberg, pass a snapshot ID from the snapshot list to the scan, never a position. [Snapshots in pyiceberg](https://rollingedition.com/open-table-formats/s/snapshots-in-pyiceberg)
3. In Delta Lake, read a version by its number in the history, through deltalake's query builder. In DuckLake, read a snapshot number taken from the catalog's snapshot table, not one you count yourself. Compare formats by the hour each commit loaded. [Read a commit by its number in each format](https://rollingedition.com/open-table-formats/s/versions-in-ducklake-and-delta), [Decisions this chapter made](https://rollingedition.com/open-table-formats/s/snapshot-decisions)
4. Before you trust either count, compare the row counts for the same hour across formats. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/snapshot-production-failures)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/snapshots-in-pyiceberg). The second snapshot should hold 999 rows.

**Pitfalls:**
- A label passed where an ID belongs fails with an error that names the value. Look the ID up instead. [Snapshots in pyiceberg](https://rollingedition.com/open-table-formats/s/snapshots-in-pyiceberg)
- A timestamp picks a state by the clock, so use IDs or numbers when the answer must not change between runs. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/snapshot-production-failures)

## Add a column to a table that already holds data

**When:** A new column is added, and the table already holds rows written before it existed.

1. Add the column with the format's schema call: `update_schema()` with `add_column` in Iceberg, or `alter.add_columns` in Delta Lake. Do not rewrite the files. Expect old rows to read as null, because a field with no initial default reads null where the file has no value. [Add load_batch after three hours](https://rollingedition.com/open-table-formats/s/add-response-bytes), [Columns are tracked by ID](https://rollingedition.com/open-table-formats/s/columns-tracked-by-id)
2. Count nulls by hour, where each hour is one write. Rows written before the add should be null, and rows written after it should not be. If the pattern breaks, find the writer that sent different columns or nulls before you trust the column. [Old files read as null](https://rollingedition.com/open-table-formats/s/old-files-read-as-null)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/add-response-bytes). The rows written before the add with a null value, 1499, should equal the rows written before the add, 1499.

**Pitfalls:**
- A null in an added column looks like missing data, so check the pattern by hour, not the null count alone. [Old files read as null](https://rollingedition.com/open-table-formats/s/old-files-read-as-null)
- A schema change can leave the snapshot count and the file count where they were. Compare the schema by field ID and name, not the snapshot count. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/schema-production-failures)

## Rename a column without rewriting its files

**When:** A column's name is wrong, and the table already holds data under the old name.

1. In Iceberg, call `update_schema()` and `rename_column`. The field ID stays the same. Check that the field ID and the data file count are unchanged, and tell readers that older snapshots still show the old name. [Rename a column by its ID without rewriting files](https://rollingedition.com/open-table-formats/s/rename-column-without-rewrite)
2. In Delta Lake at the pinned release, do not use `set_column_metadata` to rename. It commits a version and changes no name. Choose Delta column names when the table is created. A later rename is a rewrite: read the table, rename the column in memory, and write it back with mode and schema mode both set to overwrite. [Delta Lake has no rename at this pin](https://rollingedition.com/open-table-formats/s/rename-in-delta-lake)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/rename-column-without-rewrite). The field ID before the rename, 3, should equal the field ID after it, 3.

**Pitfalls:**
- A Delta rename that does nothing returns without an error, and the first query on the new name then fails. Read the column names back after every change. Older versions keep their old names, so a job pinned to one must use the names that were current then. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/schema-production-failures)

## Change partitioning without rewriting old files

**When:** Readers' filters change, and the current partitioning plans too many files.

1. Before the change, count the files that your readers' filters plan, and the files a full scan plans. [Check what a query scans](https://rollingedition.com/open-table-formats/s/check-what-a-query-scans)
2. In Iceberg, change the spec in one `update_spec()` block: remove the old field and add the new one. Old files keep the spec they were written under. [Move from daily to hourly partitions](https://rollingedition.com/open-table-formats/s/daily-to-hourly-partitions), [Partition specs are versioned too](https://rollingedition.com/open-table-formats/s/partition-specs-are-versioned)
3. Count data files under each spec. A count that moves without a planned rewrite means the change did more than you meant. [Files written under each spec](https://rollingedition.com/open-table-formats/s/files-written-under-each-spec)
4. In Delta Lake, a partition change is a full overwrite with schema mode set to overwrite, and partition columns must be plain columns. In DuckLake, `ALTER TABLE ... SET PARTITIONED BY` applies to later loads only, so check the file count after the first load. [Partitioning in the other formats](https://rollingedition.com/open-table-formats/s/partitioning-in-other-formats)
5. After the first load under the new partitioning, rerun the counts from step 1, and keep them with the change record. [Check what a query scans](https://rollingedition.com/open-table-formats/s/check-what-a-query-scans)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/check-what-a-query-scans). The full scan should plan 6 files after the change, up from 3 before it.

**Pitfalls:**
- The day and hour transforms need the pyiceberg-core package, or the first append under them fails. A grain finer than the filters need gives many small files. Judge a change by plan counts, not rows. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/partition-production-failures)

## Delete rows

**When:** Rows that match a condition must be removed, and you need to know what each format writes to disk.

1. Count the rows the condition matches first. A condition that matches no row makes pyiceberg warn and write no snapshot. [Delete rows, and what each format writes](https://rollingedition.com/open-table-formats/s/delete-rows-iceberg-and-delta)
2. Expect Iceberg and Delta Lake deletes to rewrite each data file that holds a match. In DuckLake, `DELETE` writes a delete file and leaves the data files in place. Count the delete files too, since a small delete can be inlined and write none. [Copy-on-write and merge-on-read](https://rollingedition.com/open-table-formats/s/copy-on-write-and-merge-on-read), [What goes wrong in production](https://rollingedition.com/open-table-formats/s/choice-production-failures)
3. Do not turn on Delta deletion vectors unless every reader in your set implements the feature. [Deletion vectors need a protocol upgrade](https://rollingedition.com/open-table-formats/s/delta-deletion-vectors)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/delete-rows-iceberg-and-delta). The deleted rows should match across formats: 4 in Iceberg, 4 in Delta Lake and 4 in DuckLake.

**Pitfalls:**
- A loop of single-row deletes costs one rewrite per delete, so gather the deletes into one write. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/corrections-production-failures)
- The book does not measure the cost of reading through delete files. Measure it on your own table before you rely on merge-on-read. [Copy-on-write and merge-on-read](https://rollingedition.com/open-table-formats/s/copy-on-write-and-merge-on-read)

## Upsert or merge a corrected batch

**When:** A correction re-sends rows, some of which the table already holds and some of which are new.

1. Check that the batch holds each key once. The key is the set of columns that identify one row. Do not append a correction, because an append stores every row a second time. [Late data arrives as a correction](https://rollingedition.com/open-table-formats/s/late-data-as-correction)
2. In pyiceberg, call `upsert` with the key columns as `join_cols`, and read the updated and inserted counts from its result. [Upserts in pyiceberg](https://rollingedition.com/open-table-formats/s/upserts-in-pyiceberg)
3. In DuckLake, write a `MERGE INTO` with a `WHEN MATCHED AND` condition that compares the columns you update. [MERGE in DuckLake](https://rollingedition.com/open-table-formats/s/merge-in-ducklake)
4. Run the same batch a second time, and check that it changes nothing. This applies to the upsert and to the merge. [Upserts in pyiceberg](https://rollingedition.com/open-table-formats/s/upserts-in-pyiceberg), [MERGE in DuckLake](https://rollingedition.com/open-table-formats/s/merge-in-ducklake)
5. The book has no Delta Lake upsert or merge example and makes no claim about one. [Decisions this chapter made](https://rollingedition.com/open-table-formats/s/corrections-decisions)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/upserts-in-pyiceberg). The second upsert should report 0 updated and 0 inserted rows.

**Pitfalls:**
- A repeated key fails the write, and a retry of the same batch fails again, so deduplicate first. One upsert can add up to three snapshots, so count snapshots from the snapshot list. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/corrections-production-failures)

## Compact small files

**When:** Frequent loads have left many small data files, and reads or planning have slowed.

1. Count the data files from the table's own listing after each load. Choose a schedule from how fast files arrive and the file size your readers need. [Hourly appends leave small files](https://rollingedition.com/open-table-formats/s/hourly-appends-leave-small-files)
2. In Delta Lake, call `optimize.compact()`. [Compact with optimize.compact()](https://rollingedition.com/open-table-formats/s/compact-in-delta-lake)
3. In DuckLake, call `ducklake_merge_adjacent_files`. It skips files that have delete files, which need `ducklake_rewrite_data_files`. [Merge adjacent files](https://rollingedition.com/open-table-formats/s/merge-adjacent-files)
4. In Iceberg, pyiceberg has no compaction call. Overwrite an unpartitioned table with its own scan, read as a stream, while no other writer commits. [Rewrite the table to compact it](https://rollingedition.com/open-table-formats/s/compact-iceberg-by-rewriting)
5. After each run, check the file count, the current row count against the count before, that an older version still reads, and that the Parquet files on disk exceed the listed count only by the old files awaiting cleanup. If a check fails, stop. [Check each compaction before you trust it](https://rollingedition.com/open-table-formats/s/check-each-compaction)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/compact-in-delta-lake). The file count should fall from 6 to 1.

**Pitfalls:**
- Storage grows before it shrinks, because replaced files stay on disk until cleanup. The book does not test a compaction that overlaps a commit, so schedule it where no writer commits. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/compaction-production-failures)

## Expire snapshots and remove unreferenced files

**When:** Old snapshots or versions keep storage in use, or a cleanup is planned.

1. Decide which snapshots or versions any reader, report or audit may still need. Expire the rest before you remove any file. [Snapshots keep files alive](https://rollingedition.com/open-table-formats/s/snapshots-keep-files-alive)
2. In Iceberg, expire by snapshot ID. The call deletes no data files. Find the files that no snapshot lists, and remove them only after no writer can commit them. [Expire snapshots with pyiceberg](https://rollingedition.com/open-table-formats/s/expire-snapshots-in-iceberg), [Find orphan files after expiry](https://rollingedition.com/open-table-formats/s/find-orphan-files)
3. In Delta Lake, run `vacuum` as a dry run and compare its count with the table's history, then run it for real. Keep the default retention unless you have checked the longest read and write. [Dry run first](https://rollingedition.com/open-table-formats/s/vacuum-dry-run-first), [Vacuum a table with deltalake](https://rollingedition.com/open-table-formats/s/vacuum-in-delta-lake)
4. In DuckLake, expire the snapshots, clean up the scheduled files, then clean up the orphans, each as a dry run before the real call. Use `cleanup_all` only when one catalog owns the data folder and no reader uses those files. [Expire and clean up in DuckLake](https://rollingedition.com/open-table-formats/s/expire-and-clean-up-in-ducklake)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/expire-snapshots-in-iceberg). The table should still return 1499 rows, and 1 unreferenced file should remain on disk.

**Pitfalls:**
- A query that started before a cleanup can fail partway, when a file it reads is gone. A dry run can also differ from the real run, so stop if the counts differ. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/maintenance-production-failures)

## Register tables in a catalog and open them from DuckDB

**When:** Several tools must find a table by name, a Delta table must be opened by path, or DuckDB must join tables from two catalogs.

1. Record which catalog or path names each table, and who owns it. [What a catalog holds](https://rollingedition.com/open-table-formats/s/what-a-catalog-holds)
2. Open a pyiceberg SQL catalog under one name everywhere. Reload an Iceberg table before you read it if another writer may have committed. [Register a table in a SQL catalog](https://rollingedition.com/open-table-formats/s/register-iceberg-in-sql-catalog)
3. Attach a DuckLake catalog by its file path. Copy the catalog file with its data folder, while no session has it attached. [Attach a DuckLake catalog](https://rollingedition.com/open-table-formats/s/attach-ducklake-catalog)
4. Open a Delta table by its folder path. A missing path is an error, not an empty table. [Find a table by path, with no catalog](https://rollingedition.com/open-table-formats/s/find-delta-by-path)
5. To join across catalogs, read the Iceberg table as Arrow, register it in the DuckDB session, and count the rows that find no match. The Arrow side must fit in memory. [Join tables from two catalogs](https://rollingedition.com/open-table-formats/s/join-tables-from-two-catalogs)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/join-tables-from-two-catalogs). The rows with no language should be 0.

**Pitfalls:**
- A loaded table keeps the state it had at load time, and nothing fails. A fresh, empty catalog file pointed at a live data folder makes every data file an orphan, so a `cleanup_all` would delete live files. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/catalog-production-failures)

## Copy a table into another format and check the copy

**When:** A table must move to another format, and the new table must own its files and its history.

1. List what the copy will not keep: the commit history, the partition spec, and any value finer than the target stores. Decide for each one. [What a copy keeps and loses](https://rollingedition.com/open-table-formats/s/what-a-copy-keeps-and-loses)
2. Before the first copy, test timestamps with a value below a microsecond, and choose the rule in advance. [Check timestamp precision before the copy](https://rollingedition.com/open-table-formats/s/timestamp-precision)
3. Read the source through its own library into Arrow, and write it with the target's own writer. For DuckLake, create the empty table, set its partition spec with `ALTER`, and only then insert the rows. [Copy the pageviews table into DuckLake](https://rollingedition.com/open-table-formats/s/iceberg-to-ducklake)
4. For an Iceberg target, write the target schema yourself, and print both schemas after the copy. [Copy the Delta table into a pyiceberg table](https://rollingedition.com/open-table-formats/s/delta-to-iceberg)
5. After the last write to the source, compare the row counts and a digest of typed values over the same columns, on both sides. Keep the source until both match. [Check each copy with a sorted digest](https://rollingedition.com/open-table-formats/s/check-copy-with-digest)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/check-copy-with-digest). The Iceberg-to-DuckLake digest should match: True.

**Pitfalls:**
- A digest is true only for the rows that existed when it ran, so a later write makes the copy stale. Delta Lake cut nanosecond timestamps to microseconds with no error and no change in the row count, so check values, not only counts. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/migration-production-failures)

## Choose a format from the readers that will open it

**When:** Several tools will write and read a table, and you must choose a format, a format version or a feature.

1. List every reader and writer with its pinned version. A tool left off the list is a reader you have not tested. [A checklist for a new table](https://rollingedition.com/open-table-formats/s/checklist-for-new-table)
2. Measure each feature on each reader, not only on the writer. A successful write shows only that the writer can produce the files. [Measure support before you choose](https://rollingedition.com/open-table-formats/s/measure-support-before-choosing)
3. Pick the format that every reader in your measured set opens: Iceberg format version 2 for several readers, DuckLake when DuckDB is the only engine, and Delta Lake, with no rename promise, where it already exists. Then use only the features that set supports. [Pick a format from your readers](https://rollingedition.com/open-table-formats/s/choice-decision-guide)
4. Pyiceberg at its pin refuses to create a newer format version, so measure what your writer creates. [pyiceberg writes no version 3 table](https://rollingedition.com/open-table-formats/s/iceberg-v3-and-deletion-vectors)
5. Turn on Delta deletion vectors only when every reader implements the feature, and read the protocol back after the change. [Deletion vectors need a protocol upgrade](https://rollingedition.com/open-table-formats/s/delta-deletion-vectors)
6. Promise a rename only where support is measured: Iceberg renames by field ID, and deltalake has no rename at these pins. Upgrade the readers first, then the writers, then the protocol, and read the table after each step. [A checklist for a new table](https://rollingedition.com/open-table-formats/s/checklist-for-new-table)

**Check:** Run [the example](https://rollingedition.com/open-table-formats/s/iceberg-v3-and-deletion-vectors). Creating a newer format version should raise NotImplementedError.

**Pitfalls:**
- A vendor's support page describes one engine at one version, so use it to find what to test. The DuckLake catalog version is tied to the DuckDB release, and an older DuckDB may not open the catalog after an upgrade. [What goes wrong in production](https://rollingedition.com/open-table-formats/s/choice-production-failures)
