---
title: "Open Table Formats"
chapter: "Correct rows with deletes, updates and merges"
chapter_id: corrections-and-merges
book: open-table-formats
edition: 2026.11.6
verified: 2026-11-14
edition_code: 7P1Z-JFJ2
canonical: https://rollingedition.com/open-table-formats/corrections-and-merges
license: CC BY 4.0
attribution: "“Correct rows with deletes, updates and merges,” chapter 5 of Open Table Formats, Edition 2026.11.6, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/open-table-formats/corrections-and-merges. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Correct rows with deletes, updates and merges

By the end of this chapter you can delete, upsert and merge rows in Iceberg, Delta Lake and DuckLake, say what each write does to the files, and count the snapshots a pyiceberg upsert adds. The table so far only grows. Every write in [chapter 1](#append-each-hour) added rows, and this chapter changes rows that are already committed. Each example starts from a fresh warehouse, so each one runs on its own, and each one prints counts and labels that a reader can compare with the text.

## Late data arrives as a correction {#late-data-as-correction}

The first delivery of hour 02 reached the table in [chapter 1](#append-each-hour) with the counts the source sent at the time. A later delivery of the same hour carries corrected counts for some pages, and one page that the first delivery left out. The pages in the correction are the same pages as before, so the table needs to change rows in place. Appending the corrected hour would store every page twice, once with each count.

A row in this table is identified by its key: `hour_utc`, `domain_code` and `page_title` together. A correction is a set of rows with keys. For each key, the table either already holds a row, which should change, or it does not, which should be added. Writing a correction is therefore a question about keys, and the write answers it with one rule: a key must identify one row in the batch you write. pyiceberg and DuckLake both enforce that rule. This chapter does not test a repeated key in a deltalake merge.

A correction usually arrives as the whole hour, re-delivered, and not as a few rows. Sending the whole hour keeps the batch self-contained, because the write decides row by row what changed. The cost is that every row of the hour is compared, not only the corrected ones. Because every row is compared, pyiceberg can count only the rows whose values differ, and a rerun of the same batch changes nothing.

The examples build the correction in code. The helper `hour_corrections` halves the counts of 20 page titles in hour 02, rounding down. The late row is a copy of the hour's first row, with a page title that the first delivery never had. The pageviews rows are the real cut from [chapter 1](#land-three-hours). Only the correction batch is generated.

**Working rule:** Before you write a correction, check that its batch holds each key once. pyiceberg and DuckLake refuse a batch with a repeated key, each in its own way, and a retry does not fix the data. The [production section](#corrections-production-failures) shows the failures.

## Delete rows, and what each format writes {#delete-rows-iceberg-and-delta}

A delete removes the rows that match a predicate. The rows go away in every format, but the files that held them can be handled in two ways. In copy-on-write, the writer rewrites each data file that held a matching row and leaves out the deleted rows. In merge-on-read, the writer leaves the data file alone and writes a delete file that records which rows are gone. Readers apply the delete file when they scan.

The two libraries in this chapter take the predicate in different forms. pyiceberg takes an expression object, built here from `EqualTo` and `LessThan`. deltalake takes a SQL string, which reads like the `WHERE` clause a reader already knows. The example uses both forms, so you can compare them on the same rows.

The example deletes hour 02 rows with fewer than 180 views. The number is a choice of this chapter. The cut in [chapter 1](#land-three-hours) keeps only the most-viewed rows in each hour, so a predicate for fewer than two views matches nothing. pyiceberg warns with `UserWarning: Delete operation did not match any records` and writes no snapshot, as its [source](https://raw.githubusercontent.com/apache/iceberg-python/pyiceberg-0.12.0/pyiceberg/table/__init__.py) shows. A threshold of 180 catches a few of the least-viewed rows in hour 02, which is enough to show what a delete writes.

Example `delete-low-views` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Delete the rows below 180 views from hour 02 in Iceberg, in a Delta Lake copy and in DuckLake."""

from datetime import datetime

from deltalake import DeltaTable
from pyiceberg.expressions import And, EqualTo, LessThan

from lib.lakehouse import DUCKLAKE_ALIAS, NAMESPACE, TABLE, ducklake_file_count, load_three_formats, new_warehouse, read_delta, safe_error, scan_arrow

HOUR_02 = datetime(2024, 6, 3, 2)
LOW_VIEWS = 180


def main():
    with new_warehouse() as wh:
        iceberg, delta_path, lake = load_three_formats(wh, range(6))
        iceberg_before = scan_arrow(iceberg).num_rows
        delta_before = read_delta(delta_path).num_rows
        table = f"{DUCKLAKE_ALIAS}.{NAMESPACE}.{TABLE}"
        lake_before = lake.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0]
        files_before = ducklake_file_count(lake, DUCKLAKE_ALIAS, TABLE)

        iceberg.delete(And(EqualTo("hour_utc", HOUR_02), LessThan("views", LOW_VIEWS)))
        summary = iceberg.current_snapshot().summary
        print("Iceberg deleted rows:", iceberg_before - scan_arrow(iceberg).num_rows)
        print("Iceberg remaining rows:", scan_arrow(iceberg).num_rows)
        print("Iceberg data files rewritten:", summary["deleted-data-files"])

        delta = DeltaTable(delta_path)
        metrics = delta.delete(f"hour_utc = '2024-06-03T02:00:00' AND views < {LOW_VIEWS}")
        print("Delta Lake deleted rows:", delta_before - read_delta(delta_path).num_rows)
        print("Delta Lake remaining rows:", read_delta(delta_path).num_rows)
        print("Delta Lake data files rewritten:", metrics["num_removed_files"])

        lake.execute(f"DELETE FROM {table} WHERE hour_utc = TIMESTAMP '2024-06-03 02:00:00' AND views < {LOW_VIEWS}")
        lake_after = lake.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0]
        print("DuckLake deleted rows:", lake_before - lake_after)
        print("DuckLake remaining rows:", lake_after)
        print("DuckLake data files before:", files_before)
        print("DuckLake data files after:", ducklake_file_count(lake, DUCKLAKE_ALIAS, TABLE))
        print("DuckLake delete files written:", lake.execute(
            f"SELECT count(*) FROM ducklake_list_files('{DUCKLAKE_ALIAS}', '{TABLE}', schema => '{NAMESPACE}') "
            "WHERE delete_file IS NOT NULL").fetchall()[0][0])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # the redacted error is what a reader sees
        print(safe_error(exc))
        raise SystemExit(1)
```

Output:

```text
Iceberg deleted rows: 4
Iceberg remaining rows: 2995
Iceberg data files rewritten: 1
Delta Lake deleted rows: 4
Delta Lake remaining rows: 2995
Delta Lake data files rewritten: 1
DuckLake deleted rows: 4
DuckLake remaining rows: 2995
DuckLake data files before: 6
DuckLake data files after: 6
DuckLake delete files written: 1
```

The example loads six hours into an Iceberg table, a Delta Lake table and a DuckLake table, then deletes the rows under the threshold from each. Iceberg's delete removes 4 rows and leaves 2995. Iceberg rewrote 1 data file, the one that held hour 02. The Delta Lake delete removes 4 rows, the same rows, and leaves 2995. It rewrote 1 file. Both formats rewrote the file for hour 02 and left the other five hours alone, because a file is the unit a copy-on-write delete replaces. A delete that touches many hours rewrites many files, so the cost of a delete depends on where its matching rows sit.

The DuckLake `DELETE` removes 4 rows and leaves 2995. It rewrites no data file. The data files stay at 6 before the delete and 6 after it, and the delete writes 1 delete file.

The cost of the Iceberg and Delta Lake deletes follows the size of the files they touch, not the number of rows they remove. 4 rows went, and 1 whole file was rewritten to remove them. A table whose matches are spread across many files pays for each of those files.

Each library reports its own counts, and this example computes the deleted rows as the rows before minus the rows after, so the deleted and remaining counts agree by construction. The rewritten-file counts come from the library: the Iceberg snapshot summary's `deleted-data-files` and the `num_removed_files` metric that deltalake returns from `delete`.

### Copy-on-write and merge-on-read {#copy-on-write-and-merge-on-read}

The two write styles trade cost between the writer and the reader. Copy-on-write makes the write expensive and the read cheap: a reader gets the rows as the files hold them, with nothing to apply. Merge-on-read makes the write cheap, because it writes only the positions of the deleted rows, and it moves the cost to reads until something rewrites the data files.

The three formats in this chapter differ as follows.

| Format | Library at the pins | How the library writes a delete at the pins | Shown in this chapter |
| --- | --- | --- | --- |
| Iceberg | pyiceberg 0.12.0 | Copy-on-write. `delete` rewrites the data files that contain matching rows and writes no delete files. With `write.delete.mode` set to merge-on-read, pyiceberg warns "Merge on read is not yet supported, falling back to copy-on-write" ([source](https://raw.githubusercontent.com/apache/iceberg-python/pyiceberg-0.12.0/pyiceberg/table/__init__.py)). | Yes, in the delete example |
| Delta Lake | deltalake 1.6.6 | Copy-on-write. The file with matching rows is rewritten, and the log records the old file as removed. | Yes, in the delete example |
| DuckLake | DuckDB 2.0.0 | Merge-on-read. `DELETE` writes a delete file and leaves the data file in place. | Yes, in the delete example |

The DuckLake row is shown by the delete example, which counts the delete file and the data files that stay in place. The [DuckLake documentation on deletion vectors](https://ducklake.select/docs/stable/duckdb/advanced_features/deletion_vectors) describes an experimental option that records deleted row positions in `.puffin` files. That option is off by default, and this chapter does not turn it on. The cost of reading through delete files is not measured here. A reader of a merge-on-read table pays that cost on every scan until the data files are rewritten, so measure it on the reader's own table.

Delta Lake also has deletion vectors, which record deleted row positions in a file. That makes them Delta's merge-on-read option, not a third write style, and this book does not use them. At the pins, deltalake 1.6.6 does not write a deletion vector: `delete` on a table with the feature enabled still rewrites the file. The [Delta protocol](https://raw.githubusercontent.com/delta-io/delta/v4.4.1/PROTOCOL.md) requires the deletion-vectors feature in a table's reader and writer features when the table uses deletion vectors, and enabling the feature adds it to both. `QueryBuilder`, which this book uses for every Delta read, reads such a table. `to_pyarrow_table` and `to_pyarrow_dataset` refuse it, because the table declares the feature. So this book keeps the feature off, and its Delta deletes are copy-on-write.

**Working rule:** Expect copy-on-write deletes to cost a file rewrite for each file that holds a match. Prefer predicates whose matches sit in few files, such as one hour, and batch the deletes that you know about into one write. Merge-on-read suits a table where writes are frequent and reads can pay for the delete files until something rewrites them.

## Upsert a corrected hour {#upsert-corrected-hour}

An upsert updates the row whose key matches and inserts the row whose key does not. It is the right write for a correction, because the corrected hour holds the keys that the table already has, and the late row holds a key the table does not have yet. A plain append would store the corrected rows next to the originals, so every page in the hour would appear twice.

The next two subsections show pyiceberg's method and DuckLake's SQL `MERGE` with the same batch.

The key finds the row that a change applies to, and it decides when two incoming rows are the same row. Too narrow a key collapses two real rows into one, and too wide a key inserts a second copy. The key here is `hour_utc`, `domain_code` and `page_title`, the identity the cut gives each row in [chapter 1](#land-three-hours). The batches in the examples hold each key once.

### Upserts in pyiceberg {#upserts-in-pyiceberg}

pyiceberg's `upsert` takes an Arrow table of rows and the columns that form the key, passed as `join_cols`. It returns the count of rows it updated and the count it inserted. A row counts as updated only when a non-key column changed, so a row that is identical to the table is not counted as updated. Copy-on-write still rewrites such a row when its file also holds a changed row.

Example `redeliver-hour-upsert` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Upsert the corrected hour 02 into the Iceberg table on its key, then upsert it again."""

import pyarrow as pa

from lib.lakehouse import KEY, hour_corrections, load_three_formats, new_warehouse, read_cut_hour, safe_error, snapshot_labels


def main():
    with new_warehouse() as wh:
        iceberg, _, _ = load_three_formats(wh, range(6))
        before = {snapshot.snapshot_id for snapshot in iceberg.snapshots()}
        corrected = hour_corrections(read_cut_hour(2))
        # A late row: a page the first delivery of hour 02 did not have.
        late = corrected.slice(0, 1).set_column(
            corrected.schema.get_field_index("page_title"),
            "page_title",
            pa.array(["Late_arrival_example"], type=pa.string()),
        )
        batch = pa.concat_tables([corrected, late])

        result = iceberg.upsert(batch, join_cols=list(KEY))
        print("rows updated:", result.rows_updated)
        print("rows inserted:", result.rows_inserted)

        iceberg.refresh()
        labels = snapshot_labels([snapshot.snapshot_id for snapshot in iceberg.snapshots()])
        added = [snapshot for snapshot in iceberg.snapshots() if snapshot.snapshot_id not in before]
        for snapshot in added:
            label = labels[snapshot.snapshot_id]
            print(label, snapshot.summary.operation.value)
            print(f"{label} records added:", snapshot.summary.get("added-records") or 0)
            print(f"{label} records deleted:", snapshot.summary.get("deleted-records") or 0)
        print("snapshots added:", len(added))

        again = iceberg.upsert(batch, join_cols=list(KEY))
        print("rows updated on second upsert:", again.rows_updated)
        print("rows inserted on second upsert:", again.rows_inserted)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # the redacted error is what a reader sees
        print(safe_error(exc))
        raise SystemExit(1)
```

Output:

```text
rows updated: 20
rows inserted: 1
snapshot 7 overwrite
snapshot 7 records added: 480
snapshot 7 records deleted: 500
snapshot 8 append
snapshot 8 records added: 20
snapshot 8 records deleted: 0
snapshot 9 append
snapshot 9 records added: 1
snapshot 9 records deleted: 0
snapshots added: 3
rows updated on second upsert: 0
rows inserted on second upsert: 0
```

The example loads six hours, builds the corrected hour with the late row, and upserts it on the key. The result reports 20 updated rows and 1 inserted row. The snapshot list then shows what the call wrote: 3 snapshots, labelled by the operation each one records, with the records each one added and deleted. The first is an overwrite that removes the hour-02 file and writes back its unchanged rows. It deletes 500 rows and adds 480. The next two are appends. The second adds 20 changed rows, and the third adds 1 row, the late row. The labels come from `snapshot_labels`, so the numbers are the commit order, not the snapshot IDs, which change on every run.

The count of snapshots is the part to remember. One `upsert` call is not one commit. In the [pyiceberg 0.12.0 source](https://raw.githubusercontent.com/apache/iceberg-python/pyiceberg-0.12.0/pyiceberg/table/__init__.py), `upsert` calls `overwrite` only when some rows changed, and `append` for the new rows only when there are some. `overwrite` writes two snapshots, a delete and an append. The library records the first as `overwrite`, because it also writes rows back. So a batch with changed and new rows adds three snapshots, one with only changed rows adds two, and one with only new rows adds one. Count them in the snapshot list, not from the library's call.

The example runs the same upsert a second time and prints 0 updated rows and 0 inserted rows. The second run finds every key already at its corrected value, so both counts are zero. A correction that is sent twice does not change the table twice, and that is what makes a retry safe.

**Working rule:** Use `upsert` with `join_cols` set to the key, and read its counts from the result. Count the snapshots from the snapshot list, and do not assume one commit per call. Run the same batch again when you are unsure whether the first write landed, and check that the second run reports no updates.

### MERGE in DuckLake {#merge-in-ducklake}

DuckLake takes the same correction as a `MERGE` statement in SQL. The statement names the target table, the source batch and the key in its `ON` clause. Each `WHEN` clause says what to do with a matched or unmatched row. The statement below is the one the example runs.

```sql
MERGE INTO lake.wiki.pageviews_hourly AS t
USING batch AS s
ON t.hour_utc = s.hour_utc AND t.domain_code = s.domain_code AND t.page_title = s.page_title
WHEN MATCHED AND t.views <> s.views THEN UPDATE SET views = s.views
WHEN NOT MATCHED THEN INSERT (hour_utc, domain_code, page_title, views, response_bytes)
    VALUES (s.hour_utc, s.domain_code, s.page_title, s.views, s.response_bytes)
```

The `WHEN NOT MATCHED` branch also inserts `response_bytes`, which is 0 in every row of the cut, so the late row's value is 0 too.

The `AND t.views <> s.views` condition matters. Without it, the `MERGE` would update and count every matched row, so a rerun would count them all again. With it, a matched row whose counts already agree is left alone and not counted. The examples do not run the statement without the condition, so the first half of that sentence is a reading of the statement, not a measured count.

Example `merge-correction-ducklake` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""MERGE the corrected hour 02, and its late row, into the DuckLake copy, then run the same MERGE again."""

import pyarrow as pa

from lib.lakehouse import hour_corrections, load_three_formats, new_warehouse, read_cut_hour, safe_error

MERGE = """
MERGE INTO lake.wiki.pageviews_hourly AS t
USING batch AS s
ON t.hour_utc = s.hour_utc AND t.domain_code = s.domain_code AND t.page_title = s.page_title
WHEN MATCHED AND t.views <> s.views THEN UPDATE SET views = s.views
WHEN NOT MATCHED THEN INSERT (hour_utc, domain_code, page_title, views, response_bytes)
    VALUES (s.hour_utc, s.domain_code, s.page_title, s.views, s.response_bytes)
"""


def main():
    with new_warehouse() as wh:
        _, _, lake = load_three_formats(wh, range(6))
        corrected = hour_corrections(read_cut_hour(2))
        late = corrected.slice(0, 1).set_column(
            corrected.schema.get_field_index("page_title"),
            "page_title",
            pa.array(["Late_arrival_example"], type=pa.string()),
        )
        lake.register("batch", pa.concat_tables([corrected, late]))
        print("source rows:", lake.execute("SELECT count(*) FROM batch").fetchall()[0][0])
        matched = lake.execute(
            "SELECT count(*) FROM lake.wiki.pageviews_hourly AS t JOIN batch AS s "
            "ON t.hour_utc = s.hour_utc AND t.domain_code = s.domain_code AND t.page_title = s.page_title"
        ).fetchall()[0][0]
        print("source rows matched:", matched)
        print("rows changed by the merge:", lake.execute(MERGE).fetchall()[0][0])
        print("rows changed by the same merge again:", lake.execute(MERGE).fetchall()[0][0])
        print("rows in table:", lake.execute("SELECT count(*) FROM lake.wiki.pageviews_hourly").fetchall()[0][0])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # the redacted error is what a reader sees
        print(safe_error(exc))
        raise SystemExit(1)
```

Output:

```text
source rows: 501
source rows matched: 500
rows changed by the merge: 21
rows changed by the same merge again: 0
rows in table: 3000
```

The example registers the corrected hour and the late row as a batch of 501 rows, then runs the merge on the DuckLake copy of the table. Of those, 500 match a key already in the table, so the one that does not match is the late row. The merge reports 21 rows changed. The example then runs the same statement again, and it reports 0 changed rows. The table ends with 3000 rows: the six hours and the late row.

The changed count adds the two kinds of change together, so the split needs the source size. The rows inserted are the source rows minus the matched rows, here 501 minus 500. The rows updated are the changed rows minus the rows inserted. A count of matched rows alone gives neither number.

The merge runs on the DuckLake copy. The examples attach DuckLake with inlining off, as [chapter 1](#files-metadata-and-commit) explains, so each load writes data files rather than rows in the catalog.

**Working rule:** Write a `MERGE` with a `WHEN MATCHED AND` condition that compares the columns you update, so that a rerun changes nothing. Make sure the source holds each key once before you run it. DuckLake refuses a merge that matches one target row to two source rows, and the [production section](#corrections-production-failures) shows the error.

## Merge a changed label into the domains table {#merge-domains-table}

The second table in this book, `wiki.domains`, maps each domain code to a language. A dimension table holds labels, not counts, and a merge suits a few labels that change at once. The point is that the same statement shape works on a dimension table, and the [rule about conditions](#merge-in-ducklake) applies there too.

An `UPDATE` would change the label. The `MERGE` shape also has a `WHEN NOT MATCHED` clause, which inserts a domain code the table does not hold yet, so a feed that adds a domain can use the same statement. A rerun that finds the label already set changes nothing. This table lives only in DuckLake, so the merge runs there. The pageviews table is merged in DuckLake in [MERGE in DuckLake](#merge-in-ducklake). In a pipeline, the label you merge here is the label that [chapter 8's join](#join-tables-from-two-catalogs) returns.

Example `merge-domains-label` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""MERGE a changed language label into the domains table in DuckLake, then run the same MERGE again."""

import pyarrow as pa

from lib.lakehouse import attach_ducklake, connect_ducklake, print_rows, read_domains, new_warehouse, safe_error

MERGE = """
MERGE INTO lake.wiki.domains AS t
USING labels AS s
ON t.domain_code = s.domain_code
WHEN MATCHED AND t.language <> s.language THEN UPDATE SET language = s.language
WHEN NOT MATCHED THEN INSERT (domain_code, language) VALUES (s.domain_code, s.language)
"""


def main():
    with new_warehouse() as wh:
        lake = connect_ducklake(wh.con)
        attach_ducklake(lake, "lake", wh.root, inlining_row_limit=0)
        lake.execute("CREATE SCHEMA lake.wiki")
        lake.execute("CREATE TABLE lake.wiki.domains (domain_code VARCHAR, language VARCHAR)")
        lake.register("dims", read_domains())
        lake.execute("INSERT INTO lake.wiki.domains SELECT * FROM dims")

        lake.register("labels", pa.table({"domain_code": ["fr"], "language": ["French (France)"]}))
        print("rows changed by the merge:", lake.execute(MERGE).fetchall()[0][0])
        print("rows changed by the same merge again:", lake.execute(MERGE).fetchall()[0][0])
        print_rows(lake.execute("SELECT domain_code, language FROM lake.wiki.domains").fetchall())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # the redacted error is what a reader sees
        print(safe_error(exc))
        raise SystemExit(1)
```

Output:

```text
rows changed by the merge: 1
rows changed by the same merge again: 0
de	German
en	English
fr	French (France)
ja	Japanese
```

The example creates the domains table in DuckLake, loads the four rows from the book's own data, and merges one changed label. The label for `fr` changes from `French` to `French (France)`. The merge reports 1 changed row. A second run of the same merge reports 0. The sorted table follows the output, with one row per domain code.

**Working rule:** Merge a dimension table with the same `WHEN MATCHED AND` condition as a fact table, and run the merge a second time to check that it changes nothing. A label change reaches every query that joins to the dimension, so review the label you are about to merge.

## What goes wrong in production {#corrections-production-failures}

Three things go wrong with corrections in practice: a repeated key, a loop of single-row deletes, and a snapshot count that surprises whoever reads the table's history. Each one is cheap to check before the write and expensive to find afterwards, so the checks belong in the job that writes the batch.

**A repeated key in the batch.** A correction sent twice, or two rows with the same key from a bad join, makes the batch invalid. The example sends one corrected row twice. pyiceberg refuses the upsert before it writes anything:

Example `duplicate-source-keys` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.6:

```python
"""Show what an upsert or a MERGE does when the batch has two rows for one key."""

import pyarrow as pa

from lib.lakehouse import KEY, hour_corrections, load_three_formats, new_warehouse, read_cut_hour, safe_error, scan_arrow

MERGE = """
MERGE INTO lake.wiki.pageviews_hourly AS t
USING batch AS s
ON t.hour_utc = s.hour_utc AND t.domain_code = s.domain_code AND t.page_title = s.page_title
WHEN MATCHED AND t.views <> s.views THEN UPDATE SET views = s.views
WHEN NOT MATCHED THEN INSERT (hour_utc, domain_code, page_title, views, response_bytes)
    VALUES (s.hour_utc, s.domain_code, s.page_title, s.views, s.response_bytes)
"""


def main():
    with new_warehouse() as wh:
        iceberg, _, lake = load_three_formats(wh, range(6))
        corrected = hour_corrections(read_cut_hour(2))
        # A corrected row, sent twice: the batch holds two rows with one key.
        before = read_cut_hour(2)["views"].to_pylist()
        changed = [i for i, after in enumerate(corrected["views"].to_pylist()) if after != before[i]]
        doubled = pa.concat_tables([corrected, corrected.slice(changed[0], 1)])

        try:
            iceberg.upsert(doubled, join_cols=list(KEY))
            print("Iceberg upsert: no error")
        except Exception as exc:
            print("Iceberg upsert:", safe_error(exc, wh))
        print("Iceberg rows after the failed upsert:", scan_arrow(iceberg).num_rows)

        lake.register("batch", doubled)
        try:
            lake.execute(MERGE)
            print("DuckLake merge: no error")
        except Exception as exc:
            print("DuckLake merge:", safe_error(exc, wh))
        print("DuckLake rows after the failed merge:", lake.execute("SELECT count(*) FROM lake.wiki.pageviews_hourly").fetchall()[0][0])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # the redacted error is what a reader sees
        print(safe_error(exc))
        raise SystemExit(1)
```

Output:

```text
Iceberg upsert: ValueError: Duplicate rows found in source dataset based on the key columns. No upsert executed
Iceberg rows after the failed upsert: 2999
DuckLake merge: InvalidInputException: Invalid Input Error: MERGE INTO command cannot affect the same target row more than once. A target row matched more than one source row; ensure the source rows are deduplicated or the ON condition is unique.
DuckLake rows after the failed merge: 2999
```

The output shows the refusal and the table's row count after it. The Iceberg upsert raises a `ValueError` and the table still holds 2999 rows. The DuckLake merge raises an `InvalidInputException` that names the cause, a target row that matched more than one source row, and the table still holds 2999 rows. In both runs the table kept every row it held before the write. A pipeline that catches the error and retries the same batch fails again, because the batch is the problem. Deduplicate the source by key before the write. This chapter does not test a Delta Lake merge with repeated keys, so it makes no claim about how deltalake handles one.

**A loop of single-row deletes.** Copy-on-write makes each delete a commit that rewrites the files that hold its matches. Ten deletes in a loop rewrite the file that holds their matches ten times and leave ten snapshots or versions behind. This is a rule of thumb from the cost model, not a measurement in this chapter. Collect the rows to delete, then write one delete with a predicate that covers them.

**A snapshot count that surprises the reader.** A single upsert with changed rows and new rows adds 3 snapshots in the [run above](#upserts-in-pyiceberg). A reader who expects one commit per change will find the history longer than the change log. The snapshots stay in the table's metadata until they are expired, which [chapter 7](#snapshots-keep-files-alive) covers, and each one keeps the files it refers to.

**How you'd notice.** Each of these shows up in a number you already log. The rows-updated and rows-inserted counts from pyiceberg's result, and the changed-rows count from a merge, should match the batch you sent. A rerun that reports changes means the batch differs from what you think it is. A snapshot count that grows faster than the snapshots you expect per load (up to three for an upsert) points at a non-idempotent retry, such as an append sent twice. The refusals show up as exceptions, so a job that catches them and continues will look healthy while its table stays behind.

**Working rule:** Check the batch for repeated keys before any write, and treat a refusal as a bug in the batch, not a transient fault. Gather deletes into one write. Count snapshots from the snapshot list when you audit a correction.

## Decisions this chapter made {#corrections-decisions}

- Corrections are matched on the key `hour_utc`, `domain_code` and `page_title`, and a batch must hold each key once before it is written.
- The delete example uses a threshold of 180 views, because the cut keeps only the most-viewed rows in each hour, so a threshold of two matches nothing.
- Iceberg and Delta Lake deletes are copy-on-write, and their examples show the files they rewrite. DuckLake `DELETE` writes a delete file and leaves the data files in place, and the same example shows that.
- Deletion vectors are not used. At the pins, deltalake 1.6.6 does not write them, and enabling the feature makes `to_pyarrow_table` and `to_pyarrow_dataset` refuse the table.
- Upserts and merges are checked by running them twice: the second run changes no rows.
- Snapshot counts are read from the snapshot list. The chapter does not treat one call as one commit.
- The DuckLake examples turn inlining off, so that the counts describe data files.
- The corrections are built in code, and the late row is generated. The examples show the write path, not the history of a real correction.
- The duplicate-key example shows the refusal itself, not a description of it, so the failure is in the output a reader sees.
- The chapter has no Delta Lake upsert or merge example, so it makes no claim about deltalake's merge beyond the delete.
- The examples keep the late row and the correction in the same batch, so one call shows both an update and an insert.
