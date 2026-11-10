---
title: "Open Table Formats"
chapter: "Move a table between formats and check the copy"
chapter_id: migrating-formats
book: open-table-formats
edition: 2026.11.5
verified: 2026-11-10
edition_code: 5XY7-09KG
canonical: https://rollingedition.com/open-table-formats/migrating-formats
license: CC BY 4.0
attribution: "“Move a table between formats and check the copy,” chapter 9 of Open Table Formats, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/open-table-formats/migrating-formats. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Move a table between formats and check the copy

By the end of this chapter you can copy a table from one format into another, check that the copy holds the same rows, and name what the copy leaves behind. You will also know which of those losses to accept and which ones should stop the move.

The case reaches this point when a team changes its format. The pageviews table has lived in Apache Iceberg since the earlier chapters. Suppose the analysts now want it in DuckLake, where they query a catalog file through DuckDB. Another team keeps its tables in Delta Lake and wants the same rows in Iceberg. In both moves the source stays where it is, and the move is a copy into a new table. A copy is a one-time write. Most of the work is in the checks around it.

The examples in this chapter pin 0.12.0 for pyiceberg, 1.6.6 for deltalake and 2.0.0 for DuckDB, which also runs DuckLake. Each copy example builds its own small source in a temporary warehouse, from the same three hours of the pageviews cut. That is 1499 rows. Each example runs alone, so none depends on the state that an earlier chapter left behind.

## What a copy keeps and loses {#what-a-copy-keeps-and-loses}

A copy reads the rows of one table at one moment and writes them into another table, in another format. Each target library writes its own data files, its own metadata and its own history. What survives the trip is what both sides can represent: the rows, and the columns whose types both sides support. Everything else stays with the source, or has to be set again on the target by hand.

The losses are easiest to see as a table. Each row names a part of the table, what the copy does with it, and where this chapter shows the result.

| Part of the table | After the copy | Where this chapter shows it |
| --- | --- | --- |
| Rows and their values | Kept | The digest check |
| Column names and types | Kept where both formats have the type | The Delta Lake section |
| Commit history | Lost. The copy starts a history of its own | Both copy sections |
| Partition spec | Lost unless it is set on the target | The DuckLake section |
| Timestamps below a microsecond | Depends on the format: rejected, cut short or kept | The timestamp section |

The history is a loss that readers often do not notice. Iceberg records changes as snapshots, and Delta Lake records each commit as a version. The chapter on [snapshots and time travel](#read-an-earlier-snapshot) showed how a reader uses them. A copy starts a new history in the target, so the target's history begins at the copy. The source keeps its own history for as long as you keep the source. Nothing in the copy refers back to it.

A copy is also different from registration. A [registered metadata file](#register-from-metadata-file) makes a table visible in a second catalog without touching its files, so both catalogs read the same data. A copy writes new files and leaves the source alone, which means two tables now take writes and can drift apart. Choose a copy when the target must own its files and its history. Choose registration when the two catalogs should share one set of files, and accept that the shared files must stay put.

The rows survive because the copy moves values, not files. A copy does not move data files. It reads values out of one table and writes new Parquet files for the other. That is why file names and file counts differ between a source and its copy, and why comparing file names or file counts can't check the copy. The check has to compare the rows.

**Working rule:** Before a copy, list what the source holds that the target will not keep: its history, its partition spec and any value finer than the target can store. Give each item one decision, either to accept the loss, to set the property by hand on the target, or to stop the move. The runbook should name every decision.

## Copy the pageviews table into DuckLake {#iceberg-to-ducklake}

The copy reads the Iceberg table as an Arrow table with `scan_arrow`, a shared helper that calls pyiceberg's `scan().to_arrow()`, then gives those rows to DuckLake. DuckLake creates an empty table with their columns, sets the partition spec on it, and then inserts the rows with `INSERT ... SELECT`. Arrow is the bridge because each side keeps its own library. pyiceberg reads the source, and DuckDB writes the DuckLake table through its own `ducklake` extension. Neither side reads the other's files. The [catalog chapter](#attach-ducklake-catalog) showed how the DuckLake catalog is attached, and the helper in this chapter attaches it the same way.

The source is partitioned by the hour of `hour_utc`, which is the layout that [moving from daily to hourly partitions](#daily-to-hourly-partitions) arrives at. The example builds the source with that spec, then appends three hours, one commit each:

Example `iceberg-to-ducklake-copy` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Copy an Iceberg table into DuckLake through Arrow, partitioned from the start, then check its layout and history."""

from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.transforms import HourTransform

from lib.lakehouse import (copy_to_ducklake, create_iceberg_table, ducklake_files_by_partition, ducklake_partition_transforms,
                           new_warehouse, read_cut_hour, safe_error, scan_arrow, TABLE)


def main():
    try:
        with new_warehouse() as wh:
            spec = PartitionSpec(PartitionField(source_id=1, field_id=1000, transform=HourTransform(), name="ts_hour"))
            table = create_iceberg_table(wh, partition_spec=spec)
            for hour in range(3):
                table.append(read_cut_hour(hour))
            arrow = scan_arrow(table)
            print(f"source rows: {arrow.num_rows}")
            print(f"source snapshots: {len(table.metadata.snapshots)}")
            for field in table.spec().fields:
                print(f"source partition field: {field.name}")

            target = copy_to_ducklake(wh, arrow, partition_by="hour(hour_utc)")
            print(f"copy rows: {wh.con.execute(f'SELECT count(*) FROM {target}').fetchall()[0][0]}")
            print(f"copy partition transforms: {ducklake_partition_transforms(wh.con, table=TABLE, current=True)}")
            files = ducklake_files_by_partition(wh.con, "lake", TABLE)
            print(f"copy partition values: {[value for value, _, _ in files]}")
            print(f"copy files per partition: {[count for _, count, _ in files]}")
            print(f"copy rows per partition: {[int(rows) for _, _, rows in files]}")
            changes = wh.con.execute("SELECT changes FROM ducklake_snapshots('lake') ORDER BY snapshot_id").fetchall()
            for number, (change,) in enumerate(changes, start=1):
                print(f"copy snapshot {number}: {', '.join(sorted(change))}")
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
source rows: 1499
source snapshots: 3
source partition field: ts_hour
copy rows: 1499
copy partition transforms: ['hour']
copy partition values: ['0', '1', '2']
copy files per partition: [1, 1, 1]
copy rows per partition: [499, 500, 500]
copy snapshot 1: schemas_created
copy snapshot 2: schemas_created
copy snapshot 3: tables_created
copy snapshot 4: tables_altered
copy snapshot 5: tables_inserted_into
```

The helper `scan_arrow` reads the source at its current snapshot and returns every row of that snapshot as one Arrow table. The copy therefore holds the rows of one moment, the last commit that the scan saw. Writers that commit after the scan are not in the copy, and nothing in the copy tells you so. That is the cutover problem, which the production section returns to.

The output has four parts, and each one answers a question about the copy.

The first part describes the source. It prints the row count, the number of snapshots and the partition fields. The source has 3 snapshots, one for each append, and one partition field, `ts_hour`, an hour transform of `hour_utc`.

The second part is the copy's row count, which is 1499. The row count is the same as the source's. It is a useful first check, but the digest section below explains why it is not enough on its own.

The third part is the copy's layout, and it is where a copy goes wrong without any error. The example creates the copy empty, runs `ALTER TABLE ... SET PARTITIONED BY (hour(hour_utc))` on it, and only then inserts the rows. The [DuckLake partitioning docs](https://ducklake.select/docs/stable/duckdb/advanced_features/partitioning) say the partition keys "only affect new data written to the table", so an `ALTER` after the rows are in place would leave them unpartitioned. The partition list reads the catalog table `ducklake_partition_column`, as the [DuckLake specification](https://ducklake.select/docs/stable/specification/tables/ducklake_partition_column) defines it, through the attached metadata database. No public function returns it at this pin. The helper keeps only the spec still in force, and it lists one transform, `hour`. The list says what the copy was given. The files say what it holds: the copy writes [1, 1, 1] files, and the rows are divided between them as [499, 500, 500]. A copy made in one statement carries no partition spec, so its list is empty and its rows sit in unpartitioned files. The rows are all there either way, so the check has to look at the layout.

The fourth part is the copy's snapshot list. Each line gives a snapshot's number and the changes it made. The numbers count from 1 over every snapshot DuckLake records, including the setup ones, so label N is DuckLake's own snapshot number N−1, because DuckLake counts from 0. The first two snapshots create the default schema and the `wiki` schema. The third creates the empty table, the fourth sets its partition spec, and the fifth writes the rows into the table that is already partitioned. The three hourly appends from the source do not appear. The copy's history starts at its own creation, so time travel on the copy reaches back only that far. To read the source as it was after the first hour, you still need the Iceberg table.

The example also sets `DATA_INLINING_ROW_LIMIT` to 0 through the attach helper, so the copied rows are written as Parquet files, and the file counts in the third part count those files.

**Working rule:** Copy through Arrow with the target's own writer. Create the target empty, set its partition spec with an `ALTER`, and only then insert the rows. Print the target's partition list and its files per partition. Read the copy's snapshots as the copy's own history, and keep the source until the checks in the last two sections have passed.

## Copy the Delta table into a pyiceberg table {#delta-to-iceberg}

The Delta source is built the way a team's pipeline would build it: three appends with deltalake, one per hour. Delta counts its versions from 0, so the three appends are versions 0, 1 and 2. The example reads the table's current rows with `read_delta`, a shared helper that reads through deltalake's `QueryBuilder`. It then appends those rows to an Iceberg table made with the target schema:

Example `delta-to-iceberg-copy` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Copy a Delta Lake table into Iceberg through Arrow, then compare the copy with its source."""

from deltalake import DeltaTable

from lib.lakehouse import (create_iceberg_table, new_warehouse, print_schema, read_delta, safe_error, scan_arrow,
                           write_delta_hours)


def main():
    try:
        with new_warehouse() as wh:
            path = write_delta_hours(wh.root, range(3))
            source = read_delta(path)
            print(f"delta versions: {DeltaTable(path).version() + 1}")
            print(f"delta rows: {source.num_rows}")
            print("delta columns (name, type, nullability):")
            print_schema(source.schema)

            table = create_iceberg_table(wh)
            table.append(source)
            print(f"iceberg snapshots: {len(table.metadata.snapshots)}")
            print(f"iceberg rows: {scan_arrow(table).num_rows}")
            print("iceberg columns (name, type, requirement):")
            for field in sorted(table.schema().fields, key=lambda field: field.name):
                requirement = "required" if field.required else "optional"
                print(f"{field.name}\t{field.field_type}\t{requirement}")
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
delta versions: 3
delta rows: 1499
delta columns (name, type, nullability):
domain_code	string	nullable
hour_utc	timestamp[us]	nullable
page_title	string	nullable
response_bytes	int64	nullable
views	int64	nullable
iceberg snapshots: 1
iceberg rows: 1499
iceberg columns (name, type, requirement):
domain_code	string	optional
hour_utc	timestamp	optional
page_title	string	optional
response_bytes	long	optional
views	long	optional
```

The output starts with the source. The Delta table has 3 versions and 1499 rows. The Iceberg table is built from one append of all of them, so it has 1 snapshot. Three commits in the source became one commit in the copy. The copy's row count, 1499, is the same as the source's. Like the DuckLake copy, this one starts its own history.

The rest of the output lists both schemas, one column per line. Read them side by side:

| Column | Delta Lake (Arrow type) | Iceberg type |
| --- | --- | --- |
| `domain_code` | `string` | `string` |
| `hour_utc` | `timestamp[us]` | `timestamp` |
| `page_title` | `string` | `string` |
| `response_bytes` | `int64` | `long` |
| `views` | `int64` | `long` |

Names come across unchanged, because the copy takes them from the Arrow schema. The types map one to one. The only spelling change is `int64` in Arrow, which Iceberg calls `long`. Both sides use microseconds for `hour_utc`, and the timestamp check below explains what happens when they do not.

Names matter more than they look. pyiceberg checks the Arrow schema against the table's schema before it writes. It stops with a mismatch error when a column name differs, or when a type cannot be promoted to the table's type. It accepts a type it can promote, such as `int` to `long`. That check is in the pinned library's `_check_pyarrow_schema_compatible` function in `pyiceberg/io/pyarrow.py`. The Delta table also cannot rename a column at this pin, as [the rename section of the schema chapter](#rename-in-delta-lake) showed. If the two sides disagree on a name, you change the target, not the source. pyiceberg matches the Arrow columns to the table by name, so the target's field IDs come from the schema you write. You write the target schema yourself, rather than letting the first batch decide it.

**Working rule:** Write the target schema yourself, with the types you want, and print both schemas after the copy, as the example does. Accept a near-equal type such as `int64` to `long` only after you have checked it in the output. Do not accept a name that differs.

## Check timestamp precision before the copy {#timestamp-precision}

Timestamps are a place where the formats disagree, sometimes silently. The Iceberg specification defines nanosecond timestamps as a version 3 type, so a version 2 table has no type for them ([the Iceberg specification](https://iceberg.apache.org/spec/), version 3 section). The example's table is version 2, the default. At this pin, pyiceberg refuses to write version 3, so the nanosecond values can only be kept by a format other than Iceberg. This example writes two values that differ only below a microsecond, 1000000500 and 1000000999 nanoseconds, to each format:

Example `timestamp-precision-check` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Write one timestamp with nanoseconds to each format, and read back what each format kept."""

import pyarrow as pa
from deltalake import write_deltalake
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, TimestampType

from lib.lakehouse import copy_to_ducklake, new_warehouse, NAMESPACE, read_delta, safe_error, sql_rows

NANOSECONDS = pa.table({"hour_utc": pa.array([1000000500, 1000000999], pa.timestamp("ns"))})


def main():
    try:
        with new_warehouse() as wh:
            print(f"written distinct values: {len(set(NANOSECONDS['hour_utc'].cast(pa.int64()).to_pylist()))}")
            table = wh.catalog.create_table(
                f"{NAMESPACE}.precision",
                schema=Schema(NestedField(1, "hour_utc", TimestampType(), required=False)),
            )
            try:
                table.append(NANOSECONDS)
            except Exception as exc:
                print(f"iceberg append: {safe_error(exc, wh)}")

            path = str(wh.root / "precision")
            write_deltalake(path, NANOSECONDS, mode="overwrite")
            kept = read_delta(path)["hour_utc"].cast(pa.int64()).to_pylist()
            print(f"delta read back as microseconds: {kept}")
            print(f"delta distinct values read back: {len(set(kept))}")

            target = copy_to_ducklake(wh, NANOSECONDS)
            rows = sql_rows(wh.con, f"SELECT epoch_ns(hour_utc) FROM {target}")
            print(f"ducklake epoch nanoseconds read back: {[row[0] for row in rows]}")
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
written distinct values: 2
iceberg append: UnsupportedPyArrowTypeException: Column 'hour_utc' has an unsupported type: timestamp[ns]
delta read back as microseconds: [1000000, 1000000]
delta distinct values read back: 1
ducklake epoch nanoseconds read back: [1000000500, 1000000999]
```

The first line is the input: the two values are distinct. Then each format answers in its own way.

The Iceberg append fails. The error is UnsupportedPyArrowTypeException: Column 'hour_utc' has an unsupported type: timestamp[ns]. The error names the column and the type, so the failure is the clearest of the three cases, and by default nothing is silently changed. pyiceberg's error names a setting, `PYICEBERG_DOWNCAST_NS_TIMESTAMP_TO_US_ON_WRITE`, that downcasts nanoseconds to microseconds on write. With it set, the same append succeeds and the values read back as whole microseconds, with only a logged warning. That is the same cut that Delta makes, so set it only for a job that has decided to cut the values, and not in an environment that every writer shares.

The Delta write succeeds, and the read back shows [1000000, 1000000]. Both values were cut to whole microseconds, and the two distinct values became one. The write raised no error, and the row count is the same. Only a check on the values shows the loss. The distinct count drops from 2 to 1.

DuckLake keeps the nanoseconds. Its table stores the two values as they were written, and the example reads them back as [1000000500, 1000000999].

The pageviews table records hours, so the case never reaches the problem. A table of raw request logs does. Its timestamps come from a clock that counts finer than a microsecond, and its copy has to choose a rule for those digits. Ask the question for every timestamp column before the first copy, because the answer is only visible in the values. The copies in this chapter use microsecond timestamps, which all three formats keep, so the copies match. A real table can hold values below a microsecond from its source, and the copy has to decide what to do with them before the first write.

**Working rule:** Check timestamp precision with a value below a microsecond before the first copy. Choose the rule in advance. Cast the column to microseconds and count the values the cast changes, reject the copy, or write to a format that keeps nanoseconds. Do not leave the choice to the writer library, because a silent cut gives no error to act on.

## Check each copy with a sorted digest {#check-copy-with-digest}

A matching row count does not prove that the values match. A copy can keep the count and change one value, and the count will not show it. A digest does. `digest_rows` sorts the rows, writes each one out as a line of text and hashes the result. The sort makes the digest independent of the order in which the rows come back, so two copies with the same rows get the same digest, however each format returns them. The example runs the check on both copies, and then on a copy that has one view count changed on purpose:

Example `verify-copies-by-digest` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Check each copy with a sorted digest, and show that one changed value fails the check."""

from lib.lakehouse import (copy_to_ducklake, create_iceberg_table, digest_rows, new_warehouse, read_cut_hour,
                           read_delta, safe_error, scan_arrow, sql_rows, write_delta_hours)


def same(source, copy):
    return digest_rows(source) == digest_rows(copy)


def check_iceberg_to_ducklake():
    with new_warehouse() as wh:
        table = create_iceberg_table(wh)
        for hour in range(3):
            table.append(read_cut_hour(hour))
        target = copy_to_ducklake(wh, scan_arrow(table))
        source_rows = sql_rows(wh.con, "SELECT * FROM source", source=scan_arrow(table))
        copy_rows = wh.con.execute(f"SELECT * FROM {target}").fetchall()
        first = copy_rows[0]
        changed = [(*first[:3], first[3] + 1, first[4]), *copy_rows[1:]]
        print(f"iceberg to ducklake rows: {len(source_rows)} and {len(copy_rows)}")
        print(f"iceberg to ducklake match: {same(source_rows, copy_rows)}")
        print(f"iceberg to ducklake with one changed view count match: {same(source_rows, changed)}")


def check_delta_to_iceberg():
    with new_warehouse() as wh:
        path = write_delta_hours(wh.root, range(3))
        table = create_iceberg_table(wh)
        table.append(read_delta(path))
        source_rows = sql_rows(wh.con, "SELECT * FROM source", source=read_delta(path))
        copy_rows = sql_rows(wh.con, "SELECT * FROM copy", copy=scan_arrow(table))
        print(f"delta to iceberg rows: {len(source_rows)} and {len(copy_rows)}")
        print(f"delta to iceberg match: {same(source_rows, copy_rows)}")


def main():
    try:
        check_iceberg_to_ducklake()
        check_delta_to_iceberg()
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
iceberg to ducklake rows: 1499 and 1499
iceberg to ducklake match: True
iceberg to ducklake with one changed view count match: False
delta to iceberg rows: 1499 and 1499
delta to iceberg match: True
```

For the [Iceberg-to-DuckLake copy](#iceberg-to-ducklake), the output prints both row counts, which are equal, and then the digest comparison. It reports `True`. The same check on the Delta-to-Iceberg copy also matches. The changed copy reports `False`. One changed number is enough to change the digest, so a digest that matches is evidence, and a digest that differs is a stop.

The digest compares the values as the database returns them, and it has a limit you should know. If both sides are cast to text before hashing, two values of different types can produce the same text. The integer `1` and the text `'1'` are the same text. Compare typed values, as the example does, and print the schemas as the [Delta-to-Iceberg copy](#delta-to-iceberg) did. The digest also says nothing about column names or types. Two tables with the same rows under different column names have the same digest. The schema listings in the earlier sections check the names, and the digest checks the values, so a copy needs both.

The digest is not a hash of the files. The rows are sorted by their typed values, each becomes one line of its Python representation, and the joined text is hashed with SHA-256. Two rows with equal values produce equal lines, which is what the comparison needs. A change in one value changes one line and so the whole digest.

Also choose the moment of the check. A digest is true for the rows that existed when it ran. Any write to the source after that point makes the copy stale, and the digest from before the write no longer applies. The check belongs after the last write to the source, and before anyone reads from the copy.

**Working rule:** Digest both sides after the last write to the source, over the same columns, with typed values. Compare the row counts and the digests together. Do not move readers or delete the source until both match. If writers ran during the copy, repeat the copy and the digest.

## What goes wrong in production {#migration-production-failures}

Most failed migrations pass the first check and fail later. These are the failures to look for, and how you would notice each one.

- **A cutover that races a writer.** A digest is true at the moment it is taken. The first append after it makes the copy stale, and the digest does not warn you. Stop the writers, copy, digest and then move the readers. If the writers cannot stop, copy in windows and check the rows that arrived after the last window.
- **Deleting the source before the checks pass.** The source holds the history that the copy does not. Once the source is gone, time travel into its snapshots and versions goes with it. Keep the source until the digests match and every reader has moved. Then decide how long to keep it, in writing.
- **A copy with the rows and without the layout.** A copy made without the `ALTER` would hold every row and match the digest, with no partition set. The partition list and the files per partition are the checks that show the layout is missing, so print both after the copy.
- **Timestamps that change without an error.** [Delta Lake](#timestamp-precision) cut the nanosecond values to microseconds and raised no error. The row count stayed the same. A check on the values is the only thing that catches it, so a copy with sub-microsecond data needs that check before it runs.
- **Names and types that differ.** pyiceberg refuses an append whose column names differ from the table's, or whose type it cannot promote, and that refusal is the clearest failure. The harder case is a column whose name matches and whose type it accepts, such as a `long` that was an `int`. Print both schemas and read them, rather than trusting that the append succeeded.
- **Size and memory.** The helpers in this chapter read a whole table into memory before they write it. That suits 1499 rows. A table of billions of rows needs a copy that reads and writes in batches, and the digest must then be computed over the same batches on both sides, so it stays a check of the whole table.
- **Readers that write to both tables.** During a copy, a job that writes to both tables by mistake makes the two tables differ, and the digest will show a mismatch that no single write explains. Name one writer per table in the runbook before the cutover starts.
- **A digest over text.** A digest over casts can match when the types differ. The check in this chapter compares typed values, and the runbook should say so, so that a later edit to the check does not quietly drop the types.

## Decisions this chapter made {#migration-decisions}

- **Copies go through Arrow, and each target is written by the library that owns its format.** pyiceberg writes Iceberg, DuckDB's `ducklake` extension writes DuckLake, and deltalake writes Delta Lake. This book does not use DuckDB's `iceberg` or `delta` extensions, so no copy in it depends on them.
- **Delta tables are read through `read_delta`,** which uses deltalake's `QueryBuilder`. Every read of a Delta table in this chapter takes that path.
- **A copy is one-time, starts a new history and is checked before anyone switches to it.** The source stays in place until the digests match and the readers have moved.
- **The partition spec is set on the target by hand, with an `ALTER` before the rows are inserted, and printed.** The copy does not bring it across.
- **Each copy example builds its own source from the same three hours of the cut.** Every example runs alone, and each check reads only the rows that its own example wrote.
- **Checks run on typed values, after the last write, over the same columns.** The row count and the digest are read together, and neither one is used alone to call a copy good.
- **The copies use microsecond timestamps, and a separate example checks sub-microsecond values.** Each copy in this chapter keeps its microsecond values, so the digests match. The precision example shows what each format does with a value it cannot keep.
- **Metadata-only migration is not used here.** pyiceberg's `Table.add_files` adds Parquet files that already exist to an Iceberg table as data files (`Table.add_files` in `pyiceberg/table/__init__.py`, pyiceberg 0.12.0). Its [API docs](https://py.iceberg.apache.org/api/), which are not pinned to that version, describe this as committing the files without rewriting them. That keeps the data files in place, which a copy does not. This chapter did not run it, and it copies rows instead.
