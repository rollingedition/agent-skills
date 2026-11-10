---
title: "Open Table Formats"
chapter: "Change partitioning without rewriting old files"
chapter_id: partition-evolution
book: open-table-formats
edition: 2026.11.5
verified: 2026-11-10
edition_code: 5XY7-09KG
canonical: https://rollingedition.com/open-table-formats/partition-evolution
license: CC BY 4.0
attribution: "“Change partitioning without rewriting old files,” chapter 4 of Open Table Formats, Edition 2026.11.5, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/open-table-formats/partition-evolution. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Change partitioning without rewriting old files

By the end of this chapter you can change the partitioning of a table in Iceberg, Delta Lake and DuckLake, and count the files a query plans before and after the change. Partitioning decides which files a query opens, so a change to it changes what every reader pays. What it does to the files already written depends on the format.

The case's table, `wiki.pageviews_hourly`, is partitioned by day. Each example in this chapter builds its table from the cut again, with the original columns and not the ones [chapter 3](#columns-tracked-by-id) added. This chapter changes how the rows are grouped. The [three hourly loads](#append-each-hour) from the start are already on disk. The dashboards read one hour at a time, so the team wants hour partitions for every load after hour 02. They do not want to copy the three loads that exist, and they need to know what the change does to them.

The change has two costs. The first is the work to make it, which depends on whether the format leaves the old files alone. The second is what every later query pays, because a query that spans the change plans files from both eras. This chapter measures both with counts from each library, so the decision rests on what the tables do, not on a description of the format.

## Partition specs are versioned too {#partition-specs-are-versioned}

A partition spec says how a table groups its rows: one group per day of `hour_utc`, for example. In Iceberg the spec is part of the table's metadata, and the manifest that lists each data file records the spec it was written under. Changing the spec makes a second spec with its own ID. Later writes use the second spec, and the files already on disk keep the spec they were written under. The [Iceberg specification](https://iceberg.apache.org/spec/) says that a changed spec is added to the table's list of partition specs under a unique spec ID, and that each manifest records the ID of the spec used to write it (`partition_spec_id`).

That gives the table two partitioning eras side by side. A query reads the spec of each file it opens, so one scan can cover files under several specs. The planner does this for you, which means the cost of the change is visible only in the plan and the file counts, not in the rows the query returns. A query written against `hour_utc` keeps its text when the spec changes, which is the point of the design. What differs is the set of files the planner opens. The rest of this chapter shows both.

The change is also a metadata change. Iceberg writes a spec with its own ID and does not touch the data files. The file counts in [the next section](#files-written-under-each-spec) show it.

A spec change also leaves the old spec in place as history. The table keeps a record of every spec it has had, so a reader can always find out which fields a file was written under. This matters for a team that changes partitioning more than once: each file answers the question "how was I split?" with its own spec, and nobody has to remember the order of the changes. The record is metadata, so keeping it costs little, but it does mean that the table's list of specs grows with each change.

The other two formats handle partitioning differently, and the differences decide what a change costs. Delta Lake takes its partition columns by name, so the writer creates them as columns. DuckLake keeps its partitioning keys in its catalog. Each of the two has its own part in [the section on the other formats](#partitioning-in-other-formats), after the Iceberg steps that the rest of the chapter depends on.

**Working rule:** Change an Iceberg partition spec when your readers' filters change and the current spec plans too many files for them. If the current spec already plans few files for those filters, leave it alone. When you do change it, leave the old files where they are. Record the change, with the date, the old and replacement fields, and the readers' filters that prompted it, in the table's runbook. Keep the plan counts from before and after the change with it, as [the section on what a query scans](#check-what-a-query-scans) shows.

## Move from daily to hourly partitions {#daily-to-hourly-partitions}

Iceberg partitions by a transform of a column. The day transform on `hour_utc` puts each row under its calendar day, and the hour transform puts it under its hour. The pyiceberg library computes these transforms with the `pyiceberg-core` package. The day transform imports that package when it writes, so an install with only `pyiceberg` fails at the first append under a day or hour partition (pyiceberg 0.12.0 source, [`pyiceberg/transforms.py`](https://raw.githubusercontent.com/apache/iceberg-python/pyiceberg-0.12.0/pyiceberg/transforms.py), `DayTransform.pyarrow_transform`). The pins in this book therefore include `pyiceberg-core` at 0.11.0, next to `pyiceberg` at 0.12.0.

The case's table starts with a day spec. The code appends hours 00 to 02, changes the spec, and appends hours 03 to 05. The change is one `update_spec()` block that removes the day field and adds the hour field:

```python
with table.update_spec() as update:
    update.remove_field("ts_day")
    update.add_field("hour_utc", HourTransform(), "ts_hour")
```

Both calls go in one block, so the table gets one spec change with the day field gone. The example lists the specs in order and the transform of each field. The field names are the ones this book uses: `ts_day` and `ts_hour`, so a spec label says which transform each field applies. The source column stays `hour_utc`. The day field is a transform of that column, and the hour field is another, so a reader's filter on the column keeps working across both eras.

Example `day-then-hour-spec` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Partition an Iceberg table by day, then change the spec to hour and load three more hours.

Each partition spec is labelled in the order it was made. Every data file keeps the spec it was written under.
"""

from collections import Counter

from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.transforms import DayTransform, HourTransform

from lib.lakehouse import create_iceberg_table, new_warehouse, read_cut_hour, safe_error, scan_arrow


def main():
    try:
        with new_warehouse() as wh:
            day_spec = PartitionSpec(PartitionField(source_id=1, field_id=1000, transform=DayTransform(), name="ts_day"))
            table = create_iceberg_table(wh, partition_spec=day_spec)
            for hour in range(3):
                table.append(read_cut_hour(hour))

            with table.update_spec() as update:
                update.remove_field("ts_day")
                update.add_field("hour_utc", HourTransform(), "ts_hour")
            for hour in range(3, 6):
                table.append(read_cut_hour(hour))

            specs = sorted(table.specs())
            labels = {spec_id: f"spec {number}" for number, spec_id in enumerate(specs, start=1)}
            for spec_id in specs:
                for field in table.specs()[spec_id].fields:
                    print(f"{labels[spec_id]} field {field.name}: transform {field.transform}")

            files = Counter(table.inspect.data_files().column("spec_id").to_pylist())
            for spec_id in specs:
                print(f"{labels[spec_id]} data files: {files[spec_id]}")
            print(f"rows in table: {scan_arrow(table).num_rows}")
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
spec 1 field ts_day: transform day
spec 2 field ts_hour: transform hour
spec 1 data files: 3
spec 2 data files: 3
rows in table: 2999
```

The output has two specs. Spec 1 has one field, `ts_day`, with the day transform. Spec 2 has one field, `ts_hour`, with the hour transform. The table's rows are all there after the change: `2999` rows, which is the three hours before the change and the three after it.

The spec change is the only step that touches the metadata alone. The loads on either side of it write data files as usual. [The next subsection](#files-written-under-each-spec) shows which spec each file belongs to.

A mistake here shows up later, not in the change itself. If the spec list is wrong, every load after the change writes files under the wrong partitioning, and the counts from the next section are the first place you see it. Checking the spec list right after the change costs one line of output and saves a rewrite.

**Working rule:** In Iceberg, make the spec change in one `update_spec()` block, so the old field is removed in the same change that adds the replacement. Split the two edits only if a step has to run between them; this chapter has no such step. Check the spec list after the change, and check that the field names and transforms are the ones you meant before you load any data under the second spec.

### Files written under each spec {#files-written-under-each-spec}

Each data file belongs to the spec it was written under, so counting files by spec tells you which era each file is from. The example reads the spec ID of every data file, then prints the count for each spec, under the labels "spec 1" and "spec 2". The spec IDs themselves do not appear in the output, so it reads the same on every run.

The output shows `3` data files under spec 1 and `3` under spec 2. The three day-partitioned loads kept their files through the change, and the three hour-partitioned loads wrote their own. The spec change itself wrote nothing. If the count under spec 1 had dropped after the change, something would have rewritten those files, and you would need to find out what before you trusted the old era's data.

**Working rule:** After any spec change, count the data files under each spec and compare the counts with the loads you made. A count that moves when no rewrite was planned means the change did more than you wanted, so stop and check before the next load.

## Check what a query scans {#check-what-a-query-scans}

A partition spec is a way to skip files. Before a query reads a file, the planner looks at the file's partition values and its column bounds, and drops files that cannot match the filter. Your query is only as cheap as the files it does not plan. So the way to check a change is to count the files a typical filter plans, before and after the change, rather than to compare the rows. Planning a scan returns the list of files without reading their rows, so the count is cheap enough to run before every change.

The example plans three scans. Two filters each ask for one hour: hour 01 of the case's day, which was loaded before the change, and hour 04, which was loaded after it. The third has no filter, which is a full scan. It counts the planned files for each, before the spec change from day to hour partitions (see [moving to hourly partitions](#daily-to-hourly-partitions)) and after the three hour-partitioned loads.

Example `plan-files-by-partition` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Count the files an Iceberg scan plans for two hours and for the whole table, before and after a spec change.

The filters are hour 01 of the case's day, loaded before the change, and hour 04, loaded after it.
The spec changes from day to hour between the two counts.
"""

from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.transforms import DayTransform, HourTransform

from lib.lakehouse import create_iceberg_table, hour_filter, new_warehouse, read_cut_hour, safe_error


def plan_counts(table):
    """Return the files planned for hour 01, for hour 04 and for no filter, in that order."""
    one_hour = len(table.scan(row_filter=hour_filter(1)).plan_files())
    hour_four = len(table.scan(row_filter=hour_filter(4)).plan_files())
    everything = len(table.scan().plan_files())
    return one_hour, hour_four, everything


def main():
    try:
        with new_warehouse() as wh:
            day_spec = PartitionSpec(PartitionField(source_id=1, field_id=1000, transform=DayTransform(), name="ts_day"))
            table = create_iceberg_table(wh, partition_spec=day_spec)
            for hour in range(3):
                table.append(read_cut_hour(hour))
            one_hour, hour_four, everything = plan_counts(table)
            print(f"before the change, one-hour filter plans: {one_hour}")
            print(f"before the change, hour 04 filter plans: {hour_four}")
            print(f"before the change, no filter plans: {everything}")

            with table.update_spec() as update:
                update.remove_field("ts_day")
                update.add_field("hour_utc", HourTransform(), "ts_hour")
            for hour in range(3, 6):
                table.append(read_cut_hour(hour))
            one_hour, hour_four, everything = plan_counts(table)
            print(f"after the change, one-hour filter plans: {one_hour}")
            print(f"after the change, hour 04 filter plans: {hour_four}")
            print(f"after the change, no filter plans: {everything}")
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
before the change, one-hour filter plans: 1
before the change, hour 04 filter plans: 0
before the change, no filter plans: 3
after the change, one-hour filter plans: 1
after the change, hour 04 filter plans: 1
after the change, no filter plans: 6
```

| Stage | One-hour filter | Hour 04 filter | No filter |
| --- | --- | --- | --- |
| Before the change, three day-partitioned loads | 1 | 0 | 3 |
| After the change, three hour-partitioned loads added | 1 | 1 | 6 |

The one-hour filter plans 1 file before the change and 1 file after it. Hour 01 was loaded before the change, so the one file in both plans is that hour's day-partitioned file. Before the change, all three files share one day, so the planner can skip the other two only by their `hour_utc` bounds. After the change, the three hour-partitioned files are skipped as well. The hour 04 filter runs the other way. It plans 0 files before the change, because no day-partitioned file holds hour 04, and 1 file after it, the hour-partitioned file that holds that hour. The example does not show which part of the plan skips a file, by partition values or by column bounds, so the counts show what the plan does, not how it does it. The useful result is that each filter reaches the file of its own hour, in whichever era that hour was loaded.

A plan count is a count of files, not of bytes. Two plans with the same count can read different amounts of data, because files differ in size. The count is still the right first check, because it is the number the planner decides on. When the counts agree and the query is still slow, look at file sizes and at the query itself.

The no-filter plan grows from 3 files to 6. Those are the day-partitioned files plus the hour-partitioned ones. A full scan reads both eras, and it pays for every file the table has written. That is the cost of keeping old files in place, and it is the reason to run the full scan's count as well as the filtered ones.

**Working rule:** Plan the filters your readers use, and the full scan, before and after every partition change, and keep the counts with the runbook entry. If a filter that planned one file starts to plan many, the change has broken the pruning for that filter, and you should change the spec or the filter before the next load under it.

## Partitioning in the other formats {#partitioning-in-other-formats}

The same change looks different in the other two formats, and the difference is about the cost, not the result. In each format the rows read back are the same. The files and the plan are what change. The table below sums up the three.

| Format | How the change is made | Files already written | What to check after |
| --- | --- | --- | --- |
| Iceberg | One `update_spec()` block | Kept, and still under their old spec | File count per spec; plan counts |
| Delta Lake | Full overwrite with `schema_mode="overwrite"` | Written again in a later version; old version kept | Row count; file count; partition columns of the old version |
| DuckLake | `ALTER TABLE ... SET PARTITIONED BY` | Kept; the setting applies to later loads | File count after one load; the partition key |

**Delta Lake** partitions by plain columns. Its partition option takes column names, not expressions. The protocol defines `partitionColumns` as [an array containing the names of columns](https://raw.githubusercontent.com/delta-io/delta/v4.4.1/PROTOCOL.md) by which the data is partitioned. A generated column can compute `day` or `hour` inside the table, but it raises the table's writer protocol, so this book computes both in the writer before it writes. The example does that in `with_partition_columns`, which adds the two string columns from `hour_utc`. The table is first partitioned by `day`. A change to `hour` is refused unless the write is a full overwrite that also replaces the schema:

```
DeltaError: Generic error: Specified table partitioning does not match table partitioning: expected: ["day"], got: ["hour"]. To change partition columns, use full table overwrite with schema overwrite and no replaceWhere predicate.
```

The example first makes that write with `mode="overwrite"` alone, and prints the error. It then makes the same write with `schema_mode="overwrite"`, which is the setting the library's API at the pins uses in place of the older `overwrite_schema` flag. The rows are read into memory before the overwrite starts, because an overwrite replaces every row the table holds. Writing the rows back is the only way to keep them.

Example `delta-partition-overwrite` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Change a Delta Lake table's partition columns from day to hour, which rewrites the table.

The table holds three hourly loads with day and hour as plain columns. Delta numbers versions from 0.
"""

import pyarrow.compute as pc
from deltalake import DeltaTable, write_deltalake

from lib.lakehouse import delta_file_count, new_warehouse, read_cut_hour, read_delta, safe_error


def with_partition_columns(rows):
    """Add the day and hour columns that Delta partitions by. Delta partitions only by plain columns."""
    rows = rows.append_column("day", pc.strftime(rows["hour_utc"], format="%Y-%m-%d"))
    return rows.append_column("hour", pc.strftime(rows["hour_utc"], format="%H"))


def main():
    try:
        with new_warehouse() as wh:
            path = f"{wh.root}/delta/pageviews_hourly"
            for hour in range(3):
                write_deltalake(path, with_partition_columns(read_cut_hour(hour)), partition_by=["day"], mode="append")
            table = DeltaTable(path)
            print(f"partition columns before: {table.metadata().partition_columns}")
            print(f"version before: {table.version()}")
            print(f"data files before: {delta_file_count(table)}")

            rows = read_delta(path)
            try:
                write_deltalake(path, rows, partition_by=["hour"], mode="overwrite")
            except Exception as exc:
                print(f"change without schema mode: {safe_error(exc, wh)}")

            write_deltalake(path, rows, partition_by=["hour"], mode="overwrite", schema_mode="overwrite")
            table = DeltaTable(path)
            print(f"partition columns after: {table.metadata().partition_columns}")
            print(f"version after: {table.version()}")
            print(f"data files after: {delta_file_count(table)}")
            print(f"rows after: {read_delta(path).num_rows}")

            old = DeltaTable(path, version=2)
            print(f"partition columns in version 2: {old.metadata().partition_columns}")
            print(f"rows in version 2: {read_delta(path, version=2).num_rows}")
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
partition columns before: ['day']
version before: 2
data files before: 3
change without schema mode: DeltaError: Generic error: Specified table partitioning does not match table partitioning: expected: ["day"], got: ["hour"]. To change partition columns, use full table overwrite with schema overwrite and no replaceWhere predicate.
partition columns after: ['hour']
version after: 3
data files after: 3
rows after: 1499
partition columns in version 2: ['day']
rows in version 2: 1499
```

Delta counts versions from 0. The three loads are versions 0 to 2, so the table is at version 2 before the change. The rewrite makes version 3. It holds the same 1499 rows, in 3 files. That count matches the three hours, one file for each hour partition. Version 2 still reads back, with its `day` partition, and it holds 1499 rows. The example reads it with `read_delta`, which is the book's reader for Delta tables.

The Delta change is a rewrite of the table's current files, not a metadata edit. The example's table is small. A large table needs the same rewrite, at its own cost, so plan it as a maintenance task with a read window. The example also reads every row into memory before it writes, so the rewrite needs room for the whole table at once. For a table that does not fit, a copy into a new location is the safer route, and [chapter 9](#check-copy-with-digest) shows how to check such a copy.

**DuckLake** stores partitioning as a table setting in its catalog, and a change applies to later loads only. The [DuckLake documentation](https://ducklake.select/docs/stable/duckdb/advanced_features/partitioning) says the partitioning keys of a table affect only the data written after the change. The example sets the table to partition by `hour(hour_utc)`, loads one more hour, and counts the data files before and after that load. The helper attaches the catalog with inlining off, so each load writes a data file, and the file count shows what each load did.

Example `ducklake-partition-alter` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.5:

```python
"""Set a DuckLake table's partitioning to hour, then load one more hour and count the files each load wrote.

DuckLake applies the new partitioning to new data only. Inlining is off, so every load is a data file.
"""

from lib.lakehouse import (DUCKLAKE_ALIAS, NAMESPACE, TABLE, connect_ducklake, create_ducklake_table, ducklake_file_count,
                           ducklake_file_paths, new_warehouse, read_cut_hour, safe_error)


def load(con, hour):
    con.register("batch", read_cut_hour(hour))
    con.execute(f"INSERT INTO {DUCKLAKE_ALIAS}.{NAMESPACE}.{TABLE} SELECT * FROM batch")
    con.unregister("batch")


def main():
    try:
        with new_warehouse() as wh:
            con = connect_ducklake(wh.con)
            create_ducklake_table(con, wh.root)
            for hour in range(3):
                load(con, hour)
            print(f"data files before the change: {ducklake_file_count(con, DUCKLAKE_ALIAS, TABLE)}")
            before = ducklake_file_paths(con, DUCKLAKE_ALIAS, TABLE)

            con.execute(f"ALTER TABLE {DUCKLAKE_ALIAS}.{NAMESPACE}.{TABLE} SET PARTITIONED BY (hour(hour_utc))")
            load(con, 3)
            print(f"data files after one load under hour: {ducklake_file_count(con, DUCKLAKE_ALIAS, TABLE)}")
            after = ducklake_file_paths(con, DUCKLAKE_ALIAS, TABLE)
            print(f"files kept from before the change: {len(before & after)}")

            for key, transform in con.execute(
                "SELECT partition_key_index, transform FROM __ducklake_metadata_lake.ducklake_partition_column ORDER BY 1"
            ).fetchall():
                print(f"partition key {key}: transform {transform}")
            rows = con.execute(f"SELECT count(*) FROM {DUCKLAKE_ALIAS}.{NAMESPACE}.{TABLE}").fetchall()
            print(f"rows in table: {rows[0][0]}")
    except Exception as exc:
        print(safe_error(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

Output:

```text
data files before the change: 3
data files after one load under hour: 4
files kept from before the change: 3
partition key 0: transform hour
rows in table: 1999
```

The table has 3 data files after the three loads, and 4 after the hour load. The catalog lists one partition key, with the transform `hour`. The table holds 1999 rows. The load after the change is one file. Of the files listed after that load, 3 were already listed before it, so the three earlier loads were not rewritten, which is what the documentation's rule means in practice.

**Working rule:** In Iceberg and DuckLake, a partition change is a change to metadata. Old files stay in place and later loads use the partitioning the change set, so check the file counts after the first load. In Delta Lake, a partition change is a full overwrite that rewrites the table's current files, so plan it as a rewrite and check the row count and the file count after it.

## What goes wrong in production {#partition-production-failures}

Five failures come up often enough to name.

The first is a missing package. At the pins set out in [the section on moving to hourly partitions](#daily-to-hourly-partitions), the day and hour transforms need `pyiceberg-core`, and the transforms import it when they write. An environment that installs only `pyiceberg` can create the table and then fails at the first append under a time transform. You notice it at the first scheduled load, not when the spec is changed, which is why the pin belongs in the requirements file and not in someone's memory of the install.

The second is over-partitioning. A partition grain finer than the filters need gives each query more files to open, and each file holds fewer rows. Hourly loads of a few hundred rows each give files that are small in absolute terms. This is a rule of thumb, not a measurement: the cost depends on your storage and your engine. The check is the plan count in [the section on what a query scans](#check-what-a-query-scans), which shows how many files a query opens under each spec. You notice the problem when the full-scan count keeps growing with every load while the rows per file stay small, and the fix is compaction, which [chapter 6](#compact-iceberg-by-rewriting) covers, or a coarser grain for the later loads.

The third is a high-cardinality key. An identity partition on `page_title` makes one partition per title, and each load writes a file for every title it contains. The table here has a few thousand rows, but a real page table has many more titles than that, and the file count would follow the titles, not the time. Partition by time, which the filters use, and leave the titles as a column that queries filter on.

The fourth is judging the change by its result. The rows are the same before and after a partition change, so a check that compares the rows passes whether or not the change did anything useful. The examples in this chapter print the rows only as a check that nothing was lost. The counts are what show the change.

The fifth is a rewrite that runs against a table readers use. The example runs alone and does not test readers during the write. For a table that readers depend on, we recommend writing the rewrite to a copy, checking the copy's counts and rows, and then pointing readers at it. [Chapter 9](#check-copy-with-digest) uses the same check between formats. This recommendation is a judgement, not a measured result.

**Working rule:** Choose the partition grain from the filters your readers use and the size of the files you expect, not from how often data arrives. Before you run a partition change on a table that serves readers, run it on a copy, and compare the plan counts and the row count on both sides.

## Decisions this chapter made {#partition-decisions}

- We partition the Iceberg table by the day and hour transforms of `hour_utc`, and pin `pyiceberg-core` beside `pyiceberg`. The transforms keep the time column as the partition source, so a filter on time reads the same field the writer used. We recommend this for any table that filters on time.
- We change the Delta Lake table by a full overwrite with `schema_mode="overwrite"`, and we write its partition columns as plain string columns, `day` and `hour`, computed by the writer. We accept the rewrite, because in this library a partition change needs a full overwrite.
- We count files and plans through each library's own listing: `plan_files()` for Iceberg, `file_uris()` for Delta Lake and `ducklake_list_files` for DuckLake. The examples never print a file name, because the names carry a random ID that differs on every run.
- We turn off DuckLake's inlining of small inserts for every example that counts files, so a count of files is a count of data files.
- We choose the hour grain from the dashboards' filters, which read one hour at a time, and not from how often loads arrive.
- We show the Delta failure first, then the fix, so the schema setting is explained by the error that asks for it.
- We print the DuckLake partition key from the catalog's partition table, not from file names, so the output does not change when the file names do.
- We keep the field and spec labels in the output and never print a spec ID, a snapshot ID or a file name, because each of those differs from one run to the next.
