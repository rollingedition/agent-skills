---
title: "Glossary"
book: "Open Table Formats"
edition: "2026.11.12"
canonical: "https://rollingedition.com/open-table-formats/glossary"
---

# Glossary of *Open Table Formats*

The 50 terms this book defines, as Edition 2026.11.12 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/open-table-formats/glossary

## append

For an append, the operation is append, which the Iceberg spec describes as "Only data files were added and no files were removed."

- A kind of: operation
- Defined in: [A commit names the table's files](first-table.md#files-metadata-and-commit)
- Address: https://rollingedition.com/concepts/data-engineering/append

## catalog

An Iceberg table needs a catalog, which is the registry that maps a table name to the table's current metadata.

- Defined in: [Create the table in a catalog](first-table.md#create-catalog-and-table)
- Address: https://rollingedition.com/concepts/table-formats/catalog

## cleanup

After expiry, cleanup deletes the files that no remaining snapshot lists.

- Defined in: [Snapshots keep files alive](expiry-and-cleanup.md#snapshots-keep-files-alive)
- Address: https://rollingedition.com/concepts/table-formats/cleanup

## column mapping

The Delta Lake protocol defines an optional column mapping feature that separates the name in the files from the name readers see

- Defined in: [Columns are tracked by ID](evolving-schema.md#columns-tracked-by-id)
- Address: https://rollingedition.com/concepts/data-engineering/column-mapping

## commit

A change to the table is a commit, which writes new metadata in a single step.

- Also: commits
- Comes before: snapshot
- Defined in: [What a table format adds to files](first-table.md#what-a-table-format-adds)
- Address: https://rollingedition.com/concepts/data-engineering/commit

## compaction

Compaction rewrites many small data files into fewer, larger ones.

- A kind of: commit
- Defined in: [Hourly appends leave small files](compaction.md#hourly-appends-leave-small-files)
- Address: https://rollingedition.com/concepts/data-engineering/compaction

## copy

A copy reads the rows of one table at one moment and writes them into another table, in another format.

- Contrasts with: registered name
- Defined in: [What a copy keeps and loses](migrating-formats.md#what-a-copy-keeps-and-loses)
- Address: https://rollingedition.com/concepts/table-formats/copy

## copy-on-write

In copy-on-write, the writer rewrites each data file that held a matching row and leaves out the deleted rows.

- Contrasts with: merge-on-read
- The same as: https://rollingedition.com/concepts/data-warehousing/copy-on-write
- Implemented by: pyiceberg 0.12.0
- Implemented by: deltalake 1.6.6
- Defined in: [Delete rows, and what each format writes](corrections-and-merges.md#delete-rows-iceberg-and-delta)
- Address: https://rollingedition.com/concepts/data-engineering/copy-on-write

## correction

A correction is a set of rows with keys, and for each key the table either already holds a row, which should change, or does not, which should be added.

- Also: corrections
- Defined in: [Late data arrives as a correction](corrections-and-merges.md#late-data-as-correction)
- Address: https://rollingedition.com/concepts/data-pipelines/correction

## cutover problem

Commits that land after a copy's scan and never reach the copy are the cutover problem

- Defined in: [Copy the pageviews table into DuckLake](migrating-formats.md#iceberg-to-ducklake)
- Address: https://rollingedition.com/concepts/data-engineering/cutover-problem

## data file

A data file is a Parquet file that holds rows of a table.

- Also: data files
- Defined in: [Compact the small files that hourly appends leave](compaction.md)
- Address: https://rollingedition.com/concepts/data-engineering/data-file

## data path

The data path, the folder where DuckLake writes Parquet files, is stored in the catalog.

- True for: duckdb 2.0.0
- Part of: catalog
- Defined in: [Attach a DuckLake catalog](catalogs.md#attach-ducklake-catalog)
- Address: https://rollingedition.com/concepts/data-engineering/data-path

## day transform

the day transform puts each row under its calendar day

- Implemented by: pyiceberg 0.12.0
- Defined in: [Move from daily to hourly partitions](partition-evolution.md#daily-to-hourly-partitions)
- Address: https://rollingedition.com/concepts/data-engineering/day-transform

## delete

A delete removes the rows that match a predicate.

- Comes before: copy-on-write
- Comes before: merge-on-read
- Defined in: [Delete rows, and what each format writes](corrections-and-merges.md#delete-rows-iceberg-and-delta)
- Address: https://rollingedition.com/concepts/data-engineering/delete

## delete file

a delete file that records which rows are gone

- Also: delete files
- Part of: merge-on-read
- Defined in: [Delete rows, and what each format writes](corrections-and-merges.md#delete-rows-iceberg-and-delta)
- Address: https://rollingedition.com/concepts/data-engineering/delete-file

## deletion vector

Delta Lake also has deletion vectors, which record deleted row positions in a file.

- Also: deletion vectors
- A kind of: merge-on-read
- Defined in: [Copy-on-write and merge-on-read](corrections-and-merges.md#copy-on-write-and-merge-on-read)
- Address: https://rollingedition.com/concepts/data-engineering/deletion-vector

## digest

The digest of a table is a hash of its sorted rows

- Also: sorted digest
- Defined in: [Check each copy with a sorted digest](migrating-formats.md#check-copy-with-digest)
- Address: https://rollingedition.com/concepts/data-engineering/digest

## dimension table

A dimension table holds labels, not counts

- Defined in: [Merge a changed label into the domains table](corrections-and-merges.md#merge-domains-table)
- Address: https://rollingedition.com/concepts/data-warehousing/dimension-table

## display name

the name readers use is a display name that can change without touching the files

- Part of: column mapping
- Defined in: [Columns are tracked by ID](evolving-schema.md#columns-tracked-by-id)
- Address: https://rollingedition.com/concepts/data-engineering/display-name

## dry run

A dry run lists the files that a real vacuum would delete and deletes none of them.

- True for: deltalake 1.6.6
- Defined in: [Dry run first](expiry-and-cleanup.md#vacuum-dry-run-first)
- Address: https://rollingedition.com/concepts/data-engineering/dry-run

## DuckLake snapshot

DuckLake keeps a snapshot for each change to the catalog, and the change includes creating a schema and creating a table.

- True for: duckdb 2.0.0
- A kind of: snapshot
- Implemented by: duckdb 2.0.0
- Defined in: [Read a commit by its number in each format](snapshots-and-time-travel.md#versions-in-ducklake-and-delta)
- Address: https://rollingedition.com/concepts/data-engineering/ducklake-snapshot

## expiry

expiry removes snapshots from the metadata, so time travel can't reach them

- Also: snapshot expiry
- Comes before: cleanup
- The same as: https://rollingedition.com/concepts/data-warehousing/snapshot-expiry
- Implemented by: pyiceberg 0.12.0
- Implemented by: duckdb 2.0.0
- Defined in: [Snapshots keep files alive](expiry-and-cleanup.md#snapshots-keep-files-alive)
- Address: https://rollingedition.com/concepts/data-engineering/expiry

## field ID

Iceberg gives every column an integer field ID when the column is created, and it matches columns by that ID.

- Also: field IDs
- The same as: https://rollingedition.com/concepts/data-warehousing/field-id
- Defined in: [Columns are tracked by ID](evolving-schema.md#columns-tracked-by-id)
- Address: https://rollingedition.com/concepts/data-engineering/field-id

## hour transform

the hour transform puts each row under its hour

- Implemented by: pyiceberg 0.12.0
- Defined in: [Move from daily to hourly partitions](partition-evolution.md#daily-to-hourly-partitions)
- Address: https://rollingedition.com/concepts/data-engineering/hour-transform

## Iceberg REST catalog

The Iceberg REST catalog is a catalog of another kind, a service instead of a file.

- Also: REST catalog
- A kind of: catalog
- Contrasts with: SQL catalog
- Defined in: [What a catalog holds](catalogs.md#what-a-catalog-holds)
- Address: https://rollingedition.com/concepts/data-engineering/rest-catalog

## key

In this book, a row is identified by its key: hour_utc, domain_code and page_title together.

- Comes before: correction
- Comes before: upsert
- Defined in: [Late data arrives as a correction](corrections-and-merges.md#late-data-as-correction)
- Address: https://rollingedition.com/concepts/data-pipelines/key

## manifest

each manifest names data files along with their statistics

- Also: manifests
- Part of: metadata
- The same as: https://rollingedition.com/concepts/data-warehousing/manifest
- Defined in: [What a table format adds to files](first-table.md#what-a-table-format-adds)
- Address: https://rollingedition.com/concepts/data-engineering/manifest

## manifest list

the manifest list names manifests

- Part of: metadata
- Defined in: [What a table format adds to files](first-table.md#what-a-table-format-adds)
- Address: https://rollingedition.com/concepts/data-engineering/manifest-list

## MERGE

A MERGE statement names the target table, the source batch and the key in its ON clause, and each WHEN clause says what to do with a matched or an unmatched row.

- Implemented by: duckdb 2.0.0
- Defined in: [MERGE in DuckLake](corrections-and-merges.md#merge-in-ducklake)
- Address: https://rollingedition.com/concepts/data-pipelines/merge-statement

## merge-on-read

In merge-on-read, the writer leaves the data file alone and writes a delete file that records which rows are gone.

- Implemented by: duckdb 2.0.0
- The same as: https://rollingedition.com/concepts/data-warehousing/merge-on-read
- Defined in: [Delete rows, and what each format writes](corrections-and-merges.md#delete-rows-iceberg-and-delta)
- Address: https://rollingedition.com/concepts/data-engineering/merge-on-read

## metadata

A table's metadata is a record of the table's schema and of the data files that make up the table at each point in its history.

- Defined in: [What a table format adds to files](first-table.md#what-a-table-format-adds)
- Address: https://rollingedition.com/concepts/table-formats/metadata

## metadata file

An Iceberg table keeps a metadata file that names its current snapshot.

- Part of: metadata
- Defined in: [What a table format adds to files](first-table.md#what-a-table-format-adds)
- Address: https://rollingedition.com/concepts/data-engineering/metadata-file

## operation

A snapshot's summary has a required field, operation, which is one of append, replace, overwrite or delete.

- Part of: snapshot summary
- Defined in: [Every commit is a snapshot](snapshots-and-time-travel.md#every-commit-is-a-snapshot)
- Address: https://rollingedition.com/concepts/data-engineering/operation

## orphan

A file that no snapshot lists is an orphan.

- Also: orphan file, orphan files, orphans
- The same as: https://rollingedition.com/concepts/data-warehousing/unreferenced-file
- Defined in: [Find orphan files after expiry](expiry-and-cleanup.md#find-orphan-files)
- Address: https://rollingedition.com/concepts/data-engineering/orphan

## partition spec

A partition spec says how a table groups its rows, for example one group per day of hour_utc.

- Also: partition specs
- Part of: metadata
- Defined in: [Partition specs are versioned too](partition-evolution.md#partition-specs-are-versioned)
- Address: https://rollingedition.com/concepts/data-engineering/partition-spec

## partitionColumns

The Delta Lake protocol defines partitionColumns as an array containing the names of columns by which the data is partitioned.

- Defined in: [Partitioning in the other formats](partition-evolution.md#partitioning-in-other-formats)
- Address: https://rollingedition.com/concepts/data-engineering/partition-columns

## physical name

every column gets a physical name stored in the files

- Part of: column mapping
- Defined in: [Columns are tracked by ID](evolving-schema.md#columns-tracked-by-id)
- Address: https://rollingedition.com/concepts/data-engineering/physical-name

## plan count

A plan count is a count of files, not of bytes.

- Defined in: [Check what a query scans](partition-evolution.md#check-what-a-query-scans)
- Address: https://rollingedition.com/concepts/data-engineering/plan-count

## reader check

A reader check, in the sense used here, opens the table through the reader's own interface, before the first production write.

- Defined in: [Deletion vectors need a protocol upgrade](choosing-a-format.md#delta-deletion-vectors)
- Address: https://rollingedition.com/concepts/data-engineering/reader-check

## reader feature

A reader feature in a Delta table's protocol is a promise that every reader handles it, so a reader without it cannot read the table correctly.

- Also: reader features
- Defined in: [Deletion vectors need a protocol upgrade](choosing-a-format.md#delta-deletion-vectors)
- Address: https://rollingedition.com/concepts/data-engineering/reader-feature

## registered name

A registered name is a second route to the same table, not a second table.

- Defined in: [Register a table from its metadata file](catalogs.md#register-from-metadata-file)
- Address: https://rollingedition.com/concepts/data-engineering/registered-name

## scan

A scan is the table's own reading of a snapshot.

- Implemented by: pyiceberg 0.12.0
- Defined in: [Query the table with DuckDB](first-table.md#query-with-duckdb)
- Address: https://rollingedition.com/concepts/data-engineering/scan

## snapshot

The Apache Iceberg table spec defines a snapshot as the state of a table at some time, which a reader uses to find every data file in the table.

- Also: snapshots
- Defined in: [A commit names the table's files](first-table.md#files-metadata-and-commit)
- Address: https://rollingedition.com/concepts/data-engineering/snapshot

## snapshot ID

An Iceberg snapshot ID is a long integer that the spec requires to be unique

- Also: snapshot IDs
- Part of: snapshot
- Defined in: [Append each hour as a commit](first-table.md#append-each-hour)
- Address: https://rollingedition.com/concepts/data-engineering/snapshot-id

## snapshot summary

The snapshot summary is what the table records about its own commits

- Also: summary
- Part of: snapshot
- Defined in: [Append each hour as a commit](first-table.md#append-each-hour)
- Address: https://rollingedition.com/concepts/data-engineering/snapshot-summary

## SQL catalog

The pyiceberg SqlCatalog keeps its tables in a database.

- Also: SqlCatalog
- True for: pyiceberg 0.12.0
- A kind of: catalog
- Implemented by: pyiceberg 0.12.0
- Defined in: [Register a table in a SQL catalog](catalogs.md#register-iceberg-in-sql-catalog)
- Address: https://rollingedition.com/concepts/data-engineering/sql-catalog

## tombstone

A Delta commit that replaces a file adds a remove action to the log, a tombstone that says the file is no longer part of the table, and the file stays on disk.

- Also: remove action
- Comes before: vacuum
- Defined in: [Vacuum a table with deltalake](expiry-and-cleanup.md#vacuum-in-delta-lake)
- Address: https://rollingedition.com/concepts/data-engineering/tombstone

## upsert

An upsert updates the row whose key matches and inserts the row whose key does not.

- Also: upserts
- Implemented by: pyiceberg 0.12.0
- Defined in: [Upsert a corrected hour](corrections-and-merges.md#upsert-corrected-hour)
- Address: https://rollingedition.com/concepts/data-pipelines/upsert

## vacuum

Vacuum deletes the files whose tombstones are older than the retention.

- True for: deltalake 1.6.6
- A kind of: cleanup
- Implemented by: deltalake 1.6.6
- Defined in: [Vacuum a table with deltalake](expiry-and-cleanup.md#vacuum-in-delta-lake)
- Address: https://rollingedition.com/concepts/table-formats/vacuum

## version

Delta Lake calls each commit a version

- Also: versions, Delta version
- Contrasts with: snapshot ID
- Defined in: [Every commit is a snapshot](snapshots-and-time-travel.md#every-commit-is-a-snapshot)
- Address: https://rollingedition.com/concepts/table-formats/version
