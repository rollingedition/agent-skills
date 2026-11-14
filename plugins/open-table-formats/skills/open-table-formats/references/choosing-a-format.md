---
title: "Open Table Formats"
chapter: "Choose a format from what your tools support"
chapter_id: choosing-a-format
book: open-table-formats
edition: 2026.11.6
verified: 2026-11-14
edition_code: 7P1Z-JFJ2
canonical: https://rollingedition.com/open-table-formats/choosing-a-format
license: CC BY 4.0
attribution: "“Choose a format from what your tools support,” chapter 10 of Open Table Formats, Edition 2026.11.6, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/open-table-formats/choosing-a-format. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Choose a format from what your tools support

By the end of this chapter, you can list every tool that reads or writes your tables, measure what each one supports at its pinned version, and choose a format and its features from those measurements.

Across chapters 1 to 9, one table, `wiki.pageviews_hourly`, went through its whole life in three formats: Apache Iceberg, Delta Lake and DuckLake. Each format did the same jobs in a different way, and each library supported a different subset of them. The choice you face is not which format is best in general. It is which format every tool in your team can open, change and clean up, at the versions you run. This chapter sets out how to measure that, shows the measurements for this book's pins, and gives a short guide for the choice.

In the running case, the readers of `wiki.pageviews_hourly` are a dashboard that queries through DuckDB, a pipeline that appends through pyiceberg, and an archive job that reads a Delta Lake copy through deltalake. Each reader has its own pin, and each one must open the data the others write. That is the situation the rest of this chapter prepares you for.

Three things make the choice harder than it looks. The features that differ most between formats, such as deletes, renames and partition changes, are the ones a team needs first. Each library changes on its own schedule, so a table one tool reads at one version may not open at another. And a check that passes on one machine says nothing about the versions your other tools run. The sections in this chapter deal with each of these in turn.

## Measure support before you choose {#measure-support-before-choosing}

A format name does not tell you what a tool supports. Support belongs to a tool at one version: a writer can create a feature that a reader cannot open, and a vendor page describes the vendor's engine, not the library on your laptop. So start from the readers, not the format. Write down every tool that will read the table, with its version, and then test each feature you plan to use on each of those versions.

The examples measure in that order: the reader first, then the feature. The `iceberg-format-versions` example creates an Iceberg table in format version 2, deletes rows from it, and asks pyiceberg for format version 3. The `feature-check` example turns on deletion vectors in a Delta Lake table and reads it back. The `ducklake-catalog-version` example prints a DuckLake catalog's version, and the `ducklake-delete-files` and `ducklake-inlined-delete` examples count delete files after a small and a large delete. Each prints one labelled line per result, so you can compare the output with the tables in [the support matrix](#support-matrix-as-of-pins) and with your own readers.

The person who owns the table should run the measurements on the machines that run the readers, not on a developer's laptop with different versions. Keep the record in a small table with one row per reader. The columns are the reader, its pinned version, the features your tables need and the date you measured them. A feature with no measurement counts as unsupported, and that rule is the one that prevents most of the failures later in this chapter.

| Reader | Pinned version | Features you need | Measured on |
| --- | --- | --- | --- |
| pyiceberg | 0.12.0 | Format version 2 writes, deletes | Date of your run |

Read each printed line as a claim that holds at one version of one tool. A line that says a write was refused is as useful as one that says it worked, because the refusal tells you which format version to drop. The examples print class names, not messages, so the output stays the same when a library rewords an error.

**Working rule:** Measure each reader on its own pinned version before you choose a format version or a feature. Write each result down with the version it was measured at. Run the measurement again whenever any reader's version changes, and do not reuse a support table from a vendor page.

## Read what the pinned tools did {#support-matrix-as-of-pins}

These tables state what the pinned tools did in this book's runs. Each column is one tool: pyiceberg for Iceberg, deltalake for Delta Lake, and the DuckLake extension in DuckDB for DuckLake. The pins are pyiceberg 0.12.0, deltalake 1.6.6 and DuckDB 2.0.0. DuckDB 2.0.0 is a long-term support release, dated Oct 21, 2026 ([DuckDB release calendar](https://duckdb.org/release_calendar)). DuckLake 1.0 was released on Apr 13, 2026 ([DuckLake release calendar](https://ducklake.select/release_calendar.html)). The catalog at these pins reports version 1.1, and that is the version readers must open. The extension is a separate version: DuckDB reports its build as 417a9117f5, and the extension ships with DuckDB 2.0.0, so its version follows DuckDB's. The last column names the example or source behind each cell. Not shown here means a gap in this book, not a missing feature.

Example `ducklake-catalog-version` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Attach a DuckLake catalog and print its catalog version and the version of the DuckLake extension that DuckDB loaded."""

from lib.lakehouse import attach_ducklake, connect_ducklake, new_warehouse


def main():
    with new_warehouse() as wh:
        con = connect_ducklake(wh.con)
        attach_ducklake(con, "probe", wh.root)
        version = con.execute("SELECT value FROM __ducklake_metadata_probe.ducklake_metadata WHERE key = 'version'").fetchall()[0][0]
        print("ducklake catalog version:", version)
        extension = con.execute("SELECT extension_version FROM duckdb_extensions() WHERE extension_name = 'ducklake'").fetchall()[0][0]
        print("ducklake extension version:", extension)


if __name__ == "__main__":
    main()
```

Output:

```text
ducklake catalog version: 1.1
ducklake extension version: 417a9117f5
```

### Writing and reading versions {#matrix-writing-and-reading}

| Versions and reads | pyiceberg | deltalake | DuckLake | Shown in |
| --- | --- | --- | --- | --- |
| Write rows as commits | Yes | Yes | Yes | [Land three hours](#land-three-hours) |
| Read an earlier commit by number | Yes, by snapshot | Yes, by version | Yes, by snapshot | [Iceberg](#snapshots-in-pyiceberg), [Delta and DuckLake](#versions-in-ducklake-and-delta) |
| Create format version 3 | No, raises an error | — | — | [Example](https://github.com/rollingedition/book-open-table-formats/blob/a917156a8ff947942a0ff79949efc3324c9c51af/examples/iceberg-format-versions.py) |
| Rename a column | Yes, by field ID | No, a silent no-op | Not shown here | [Iceberg](#rename-column-without-rewrite), [deltalake](#rename-in-delta-lake) |
| Column mapping at create | — | Yes | — | [deltalake](#rename-in-delta-lake) |

### Changing and cleaning up {#matrix-changing-and-cleaning-up}

| Changes and cleanup | pyiceberg | deltalake | DuckLake | Shown in |
| --- | --- | --- | --- | --- |
| Delete rows | Rewrites files | Rewrites files | Writes delete files | [Chapter 5](#delete-rows-iceberg-and-delta) |
| Delete files written | None | None | Yes, unless inlined | [Format versions](https://github.com/rollingedition/book-open-table-formats/blob/a917156a8ff947942a0ff79949efc3324c9c51af/examples/iceberg-format-versions.py), [feature check](https://github.com/rollingedition/book-open-table-formats/blob/a917156a8ff947942a0ff79949efc3324c9c51af/examples/feature-check.py), [DuckLake](https://github.com/rollingedition/book-open-table-formats/blob/a917156a8ff947942a0ff79949efc3324c9c51af/examples/ducklake-delete-files.py), [inlined](https://github.com/rollingedition/book-open-table-formats/blob/a917156a8ff947942a0ff79949efc3324c9c51af/examples/ducklake-inlined-delete.py) |
| Upsert or merge | Upsert, several snapshots | Not shown here | `MERGE INTO` | [Upserts](#upserts-in-pyiceberg), [MERGE](#merge-in-ducklake) |
| Change partitioning | Old files keep the old spec | Overwrite with schema mode | Change with `ALTER TABLE` | [Chapter 4](#daily-to-hourly-partitions), [other formats](#partitioning-in-other-formats) |
| Compact small files | No method; overwrite the table | `optimize.compact()` | Merge adjacent files | [Iceberg](#compact-iceberg-by-rewriting), [deltalake](#compact-in-delta-lake), [DuckLake](#compact-in-ducklake) |
| Expire snapshots | By ID or `older_than`; deletes no files | Vacuum by retention | Expire, then clean up | [Iceberg](#expire-snapshots-in-iceberg), [deltalake](#vacuum-dry-run-first), [DuckLake](#expire-and-clean-up-in-ducklake) |

Example `ducklake-delete-files` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Load six hours into a DuckLake table with data inlining off, then count the delete files that a small and a large delete write."""

from lib.lakehouse import DUCKLAKE_ALIAS, NAMESPACE, TABLE, connect_ducklake, create_ducklake_table, new_warehouse, read_cut_hour

LOW_VIEWS = 180
VERY_LOW_VIEWS = 1000


def delete_files(con):
    return con.execute(f"SELECT count(*) FROM ducklake_list_files('{DUCKLAKE_ALIAS}', '{TABLE}', schema => '{NAMESPACE}') "
                       "WHERE delete_file IS NOT NULL").fetchall()[0][0]


def main():
    with new_warehouse() as wh:
        con = connect_ducklake(wh.con)
        create_ducklake_table(con, wh.root, inlining_row_limit=0)
        table = f"{DUCKLAKE_ALIAS}.{NAMESPACE}.{TABLE}"
        for hour in range(6):
            con.register("hour", read_cut_hour(hour))
            con.execute(f"INSERT INTO {table} SELECT * FROM hour")
            con.unregister("hour")

        con.execute(f"DELETE FROM {table} WHERE hour_utc = TIMESTAMP '2024-06-03 02:00:00' AND views < {LOW_VIEWS}")
        print("rows left after the small delete:", con.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0])
        print("delete files after the small delete:", delete_files(con))

        con.execute(f"DELETE FROM {table} WHERE views < {VERY_LOW_VIEWS}")
        print("rows left after the large delete:", con.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0])
        print("delete files after the large delete:", delete_files(con))


if __name__ == "__main__":
    main()
```

Output:

```text
rows left after the small delete: 2995
delete files after the small delete: 1
rows left after the large delete: 195
delete files after the large delete: 6
```

Example `ducklake-inlined-delete` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Load six hours into a DuckLake table with DuckLake's default data inlining, then count the delete files that a small and a large delete write."""

from lib.lakehouse import DUCKLAKE_ALIAS, NAMESPACE, TABLE, connect_ducklake, create_ducklake_table, new_warehouse, read_cut_hour

LOW_VIEWS = 180
VERY_LOW_VIEWS = 1000


def delete_files(con):
    return con.execute(f"SELECT count(*) FROM ducklake_list_files('{DUCKLAKE_ALIAS}', '{TABLE}', schema => '{NAMESPACE}') "
                       "WHERE delete_file IS NOT NULL").fetchall()[0][0]


def main():
    with new_warehouse() as wh:
        con = connect_ducklake(wh.con)
        create_ducklake_table(con, wh.root, inlining_row_limit=None)
        table = f"{DUCKLAKE_ALIAS}.{NAMESPACE}.{TABLE}"
        for hour in range(6):
            con.register("hour", read_cut_hour(hour))
            con.execute(f"INSERT INTO {table} SELECT * FROM hour")
            con.unregister("hour")

        con.execute(f"DELETE FROM {table} WHERE hour_utc = TIMESTAMP '2024-06-03 02:00:00' AND views < {LOW_VIEWS}")
        print("rows left after the small delete:", con.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0])
        print("delete files after the small delete:", delete_files(con))

        con.execute(f"DELETE FROM {table} WHERE views < {VERY_LOW_VIEWS}")
        print("rows left after the large delete:", con.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0])
        print("delete files after the large delete:", delete_files(con))


if __name__ == "__main__":
    main()
```

Output:

```text
rows left after the small delete: 2995
delete files after the small delete: 0
rows left after the large delete: 195
delete files after the large delete: 6
```

### Catalogs and DuckDB {#matrix-catalogs-and-duckdb}

| Catalogs and DuckDB | pyiceberg | deltalake | DuckLake | Shown in |
| --- | --- | --- | --- | --- |
| Catalog needed | Yes, a SQL catalog | No, found by path | Yes, the catalog file | [Chapter 8](#what-a-catalog-holds), [by path](#find-delta-by-path), [catalog file](#attach-ducklake-catalog) |
| DuckDB reads it | Through Arrow | Through Arrow, from `QueryBuilder` | Natively | [Chapter 1](#query-with-duckdb), [Chapter 9](#check-copy-with-digest), [Chapter 8](#attach-ducklake-catalog) |
| DuckDB writes it | — | — | Natively, through SQL | [Chapter 8](#attach-ducklake-catalog) |

DuckDB's own `delta` extension is a separate path from deltalake. It can write Delta Lake tables, which is covered in the decision guide below.

**Working rule:** Read each cell against the example or source it names. A cell with no example behind it is a claim to test on your own readers, not one to rely on.

## pyiceberg writes no version 3 table {#iceberg-v3-and-deletion-vectors}

The version 3 section of the Iceberg specification makes binary deletion vectors the row-level delete format. It says that "writers are not allowed to add new position delete files to v3 tables" ([Iceberg spec](https://iceberg.apache.org/spec/)). The same section adds row lineage for new rows, default column values, the variant type and nanosecond timestamps.

Example `iceberg-format-versions` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Create a format version 2 Iceberg table, delete rows from it, then ask pyiceberg for format version 3."""

from pyiceberg.expressions import LessThan

from lib.lakehouse import create_iceberg_table, new_warehouse, read_cut_hour, scan_arrow

LOW_VIEWS = 180


def main():
    with new_warehouse() as wh:
        table = create_iceberg_table(wh, properties={"format-version": "2"})
        table.append(read_cut_hour(0))
        print("format version:", table.metadata.format_version)

        before = scan_arrow(table).num_rows
        table.delete(LessThan("views", LOW_VIEWS))
        print("rows deleted:", before - scan_arrow(table).num_rows)
        contents = table.inspect.files().column("content").to_pylist()
        print("delete files after the delete:", sum(1 for content in contents if content != 0))
        for number, snapshot in enumerate(table.metadata.snapshots, start=1):
            print(f"snapshot {number} operation:", snapshot.summary.operation.value)

        try:
            create_iceberg_table(wh, identifier="wiki.format_three", properties={"format-version": "3"})
        except NotImplementedError as exc:
            print("format version 3 create:", type(exc).__name__)
        else:
            print("format version 3 create: created")


if __name__ == "__main__":
    main()
```

Output:

```text
format version: 2
rows deleted: 82
delete files after the delete: 0
snapshot 1 operation: append
snapshot 2 operation: overwrite
format version 3 create: NotImplementedError
```

pyiceberg at this pin writes format version 2. The example prints the format version of its table, which is 2. The delete removed 82 rows and left 0 delete files. The table has two snapshots: the first is an `append`, and the second, the delete, is an `overwrite`. The same example asks for format version 3, and the create raises `NotImplementedError`, so none of the version 3 features is available from this writer.

pyiceberg deletes by rewriting the data files it touches at these pins, although format version 2 also allows delete files ([chapter 5](#copy-on-write-and-merge-on-read)). Measure that rewrite on a copy of your own table before you choose.

| Feature | Iceberg v3 specification | pyiceberg at these pins |
| --- | --- | --- |
| Binary deletion vectors | Row-level delete format | Not written |
| Position delete files | Legacy, in format version 2 tables only | Not written |
| Row lineage, defaults, variant, nanosecond timestamps | Part of version 3 | Not available: no version 3 table |

**Working rule:** Write format version 2 with pyiceberg at these pins, and do not promise a version 3 feature to any reader. Choose version 3 only when the writer you use creates it and every reader in your set opens it, and check both on their own pins.

## Deletion vectors need a protocol upgrade {#delta-deletion-vectors}

The Delta Lake protocol, at the release tag its link names, says a table with deletion vectors needs reader version 3 and writer version 7, with the `deletionVectors` feature in both feature lists. It also says a reader must implement every feature in the reader list before it reads the table ([Delta protocol](https://raw.githubusercontent.com/delta-io/delta/v4.4.1/PROTOCOL.md)). A feature is a promise that the reader handles it, so a reader without it cannot read the table correctly.

Example `feature-check` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Turn on deletion vectors in a Delta Lake table, delete the rows below 180 views, and print the protocol the table declares."""

from deltalake import DeltaTable, write_deltalake

from lib.lakehouse import new_warehouse, read_cut_hour, read_delta

LOW_VIEWS = 180


def deletion_vector_files(path):
    """Count files under the table folder that are not Parquet or the Delta log."""
    return sum(1 for item in path.rglob("*")
               if item.is_file() and item.suffix != ".parquet" and "_delta_log" not in item.parts)


def main():
    with new_warehouse() as wh:
        path = wh.root / "dv_table"
        write_deltalake(str(path), read_cut_hour(0), configuration={"delta.enableDeletionVectors": "true"})
        table = DeltaTable(str(path))
        protocol = table.protocol()
        print("minimum reader version:", protocol.min_reader_version)
        print("minimum writer version:", protocol.min_writer_version)
        print("reader features:", ", ".join(sorted(protocol.reader_features)))

        before = read_delta(str(path)).num_rows
        metrics = table.delete(f"views < {LOW_VIEWS}")
        print("rows deleted:", before - read_delta(str(path)).num_rows)
        print("data files rewritten:", metrics["num_removed_files"])
        print("rows through QueryBuilder:", read_delta(str(path)).num_rows)
        print("deletion vector files:", deletion_vector_files(path))


if __name__ == "__main__":
    main()
```

Output:

```text
minimum reader version: 3
minimum writer version: 7
reader features: deletionVectors, timestampNtz, variantType
rows deleted: 82
data files rewritten: 1
rows through QueryBuilder: 417
deletion vector files: 0
```

The example enables the deletion vector setting on a table of pageviews, deletes the rows below 180 views and prints what the table declares. The minimum reader version is 3, and the minimum writer version is 7. The reader features are `deletionVectors, timestampNtz, variantType`. The example set only the deletion vector setting, so the library added the other two features on its own. The delete removed 82 rows and rewrote 1 data file. The table holds 0 deletion vector files, and `QueryBuilder` reads 417 rows. So at this pin deltalake declares the feature but deletes by rewriting the file. The setting changes the protocol that readers must support, not the way deletes write. The book reads Delta tables only through `QueryBuilder`, as [chapter 8](#find-delta-by-path) shows.

Every feature in the list matters, not only the deletion vector. A reader that lacks `timestampNtz` or `variantType` has the same problem as one that lacks `deletionVectors`. Compare the printed feature lists with each reader's own list after every change.

So a deletion vector setting is a protocol change for every reader of the table, and the write succeeds before any reader is tested. Turn it on only when every reader in your set implements the `deletionVectors` feature. Otherwise keep copy-on-write.

A reader check, in the sense used here, opens the table through the reader's own interface, before the first production write. For the Delta Lake copy in the case, that check is a read through `QueryBuilder` and a read of the protocol, both in the feature-check example.

**Working rule:** Enable deletion vectors only after you have checked each reader's feature support on its own version. Read the table's protocol back after each change, and keep copy-on-write for any table that a reader outside your tested set will open.

## A checklist for a new table {#checklist-for-new-table}

Use this list before you create a table that more than one tool will open. Each item closes a risk that [the support matrix](#support-matrix-as-of-pins) and the [deletion vector section](#delta-deletion-vectors) showed.

1. List every reader and writer, with its version. A tool you leave off the list is a reader you have not tested, and it will be the one that fails.
2. For each feature the table needs, measure its support on each tool, as the examples in this chapter do. Measure the reader, not only the writer, because a successful write proves only that the writer can produce the files.
3. Set the format version and the protocol on purpose. Print them back, and read the table from each reader. Do not accept a default you did not choose.
4. Refuse any format version or feature that one reader in the set does not support. A table that one reader cannot open is an outage, however good the features are for the other readers.
5. Promise a rename only where the measured support allows it. Iceberg renames by field ID. deltalake has no rename at these pins, so plan a rewrite instead, and check the column names afterwards.
6. Keep a plain copy-on-write path for deletes unless every reader has been tested with deletion vectors. Copy-on-write costs rewritten files, and it opens everywhere.
7. Plan any upgrade in this order: readers first, then writers, then the protocol. Read the table after each step, and stop if a reader fails.
8. Run the measurements again on every pin change, and record the new versions in the table of readers.

**Working rule:** Keep the list with the table's design note, so the next person who adds a reader starts from the same record. A list kept up to date costs less than one rebuilt after a failed read.

## Pick a format from your readers {#choice-decision-guide}

Use this guide after you have measured your readers. The first column is the situation, not the format. It maps a measured reader set to a format, and it does not replace the measurements.

| If your situation is | Choose | Why |
| --- | --- | --- |
| pyiceberg and DuckDB read the table | Iceberg, format version 2 | pyiceberg reads it, and DuckDB queries its output |
| Several readers, and you need in-place renames | Iceberg | Renames keep the field ID, as [chapter 3](#rename-column-without-rewrite) shows |
| DuckDB is the only engine, and you want SQL changes | DuckLake | Deletes, merges and partition changes run as SQL |
| Delta tables already exist and deltalake reads them | Keep Delta Lake, with no rename promise | Change partitions by overwrite, and read back after each change |
| You want DuckDB to change a Delta table | Not at these pins | DuckDB can only append; use deltalake for updates and deletes |

DuckDB's `delta` extension can write Delta Lake tables. The DuckDB documentation for the pinned release, 2.0.0, says it can create tables and append to them, and it lists `UPDATE`, `DELETE`, `MERGE INTO`, `ALTER TABLE` and `DROP TABLE` as not supported ([DuckDB delta docs, Limitations](https://duckdb.org/docs/2.0/core_extensions/delta.html)). No example in this book runs the extension. The examples install nothing at run time and use each format's own library, so the reader sees the same library that writes the table, and nothing downloads while an example runs.

Read the table row by row. When two rows point in different directions, the readers decide. First choose the format that every reader in your measured set opens, then choose features that every reader supports.

Apply the guide to the running case. The dashboard and the pipeline both open the pageviews table with pyiceberg or DuckDB, which points to Iceberg format version 2. The archive job reads a Delta Lake copy, so the Delta row applies to that copy only, and the copy keeps its deletes as copy-on-write.

We recommend Iceberg format version 2 as the default for a table that several tools read, because pyiceberg writes it, DuckDB reads its output, and the examples measure both. Its costs at these pins: every delete rewrites the data files it touches, the table needs a catalog, and pyiceberg has no compaction or orphan-file cleanup call. We recommend DuckLake when DuckDB is the only engine, because the reader and the writer share one SQL surface. Its costs: readers are limited to DuckDB, the catalog version is tied to the DuckDB release, and small deletes are inlined unless you turn inlining off. Choose differently when the checks in this chapter show that a reader cannot do what you need.

**Working rule:** Pick the format that every reader in your measured set opens, then choose only the features that set supports. If no format meets every need, split the table or change the readers. Do not promise a feature to a reader that the measurements do not cover.

## What goes wrong in production {#choice-production-failures}

Most format failures in a shared lakehouse come from a tool the writer did not test, not from a bug in the format. Each failure in this section is one that an earlier section measured or cited, so you can check for it in your own tables.

**Choosing by vendor claims.** A support page describes one engine, often at a different version from yours. Use it to find what to test, not as the answer. Check the claim against your own pins.

**Testing one engine only.** A table can be written by one library and read by another that does not support the same feature. The write succeeds in one tool, and the failure appears when a second tool opens the table. Run the reader check for each tool in the set before the first write.

**A feature the reader does not implement.** The deletion vector setting adds a reader feature to the table, and the protocol requires readers to implement it. A reader outside your set may open the table and fail on it. Find out from the protocol record, which the feature-check example prints, and not from a later query error.

**A rename that does nothing.** At these pins, deltalake's `set_column_metadata` call returns without an error and bumps the version, but the column names stay the same. [Chapter 3](#rename-in-delta-lake) shows the trap. The check is to read the column names after the change.

**Upgrading in the wrong order.** A writer that moves ahead of its readers can produce a table that the readers cannot open, and the first sign is a failed read in another team's job. The order in the checklist keeps every reader able to open the table at each step.

**Judging a table by its write.** A write that succeeds shows that the writer can produce the files. It does not show that another tool can read them. The deletion vector check in this chapter writes, deletes and then counts the reader's features for exactly this reason.

**Counting rows for a DuckLake delete.** Under DuckLake's default inlining, a small delete of a few rows writes no delete file, and the same delete with inlining off writes one. A check that counts rows says the delete worked either way. Count delete files too, as the [DuckLake delete example](https://github.com/rollingedition/book-open-table-formats/blob/a917156a8ff947942a0ff79949efc3324c9c51af/examples/ducklake-delete-files.py) does.

**A catalog version that moves with DuckDB.** The DuckLake catalog at these pins reports version 1.1, and the extension that opens it reports the build 417a9117f5. The DuckLake documentation names the DuckDB release that version 1.1 requires ([DuckLake docs](https://ducklake.select/docs/stable/)). An older DuckDB may not open that catalog, so an upgrade can break a reader that did not change.

**Working rule:** Measure every reader on its own pinned version before you write, upgrade or rely on a vendor claim. When you upgrade a writer or a catalog, keep the old release in place until every reader has opened the result.

## Decisions this chapter made {#choice-decisions}

- We recommend Iceberg format version 2 with pyiceberg at these pins. We do not promise format version 3 to any reader, and we set no date for when that changes. The pin decides, and the measurement shows it.
- We state the matrix as measured at these pins, and each cell points to an example or a cited source.
- We keep deletion vectors out of tables that a reader outside the tested set will open.
- We do not promise a rename on a deltalake table at these pins.
- We count DuckLake delete files as well as rows.
- We treat an unmeasured feature as unsupported, because the failures in this chapter all came from a feature someone assumed.
- We state the DuckLake catalog version apart from the extension version. The catalog version decides which readers can open the catalog, and the extension version follows DuckDB.
- We chose a measured matrix over a vendor's support page, because the pinned versions decide what opens.
- The default of Iceberg format version 2 is a judgement, labelled as one. The measurements behind it are the examples, and they are the part to re-run.
- The book runs no DuckDB `delta` or `iceberg` extension. Its examples install nothing at run time and use each format's own library. The DuckDB `delta` extension can write Delta Lake tables, as its documentation describes.
