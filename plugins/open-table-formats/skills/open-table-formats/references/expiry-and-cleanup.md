---
title: "Open Table Formats"
chapter: "Expire snapshots and remove unreferenced files"
chapter_id: expiry-and-cleanup
book: open-table-formats
edition: 2026.11.16
verified: 2026-11-24
edition_code: XR7P-ZXAG
canonical: https://rollingedition.com/open-table-formats/expiry-and-cleanup
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Expire snapshots and remove unreferenced files,” chapter 7 of Open Table Formats, Edition 2026.11.16, examples passed Nov 24, 2026. By Rolling Edition, https://rollingedition.com/open-table-formats/expiry-and-cleanup. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Expire snapshots and remove unreferenced files

After this chapter you can expire old snapshots in each of the three formats, remove the data files that only those snapshots still listed, or in Delta Lake those past [vacuum](#vacuum-in-delta-lake)'s retention, and show that a read of an expired snapshot fails.

[Compaction](#hourly-appends-leave-small-files) leaves the same kind of old file: the rewrites left the replaced files on disk, because older snapshots still list them. This chapter expires the old snapshots of `wiki.pageviews_hourly`, then deletes the files that no snapshot lists any more. Every example here uses the hour-02 correction from [the corrections chapter](#late-data-as-correction), written as an overwrite of that hour rather than as the upsert in its later section, because the overwrite leaves exactly one old file per format. Those old files stay until their snapshots are expired and their files are removed. Both steps run in each format, and each step is checked with a count rather than with a listing you have to trust.

## Snapshots keep files alive {#snapshots-keep-files-alive}

Every snapshot records which data files make up the table at that commit. [What a snapshot points to](#what-a-snapshot-points-to) covers how each format stores that list. The point for this chapter is that a commit that replaces rows does not delete the files it replaces. It writes files for the replacement rows, and the snapshots from before the commit still list the old ones, so time travel keeps working. A data file becomes an [orphan](#find-orphan-files) only when no snapshot you keep lists it.

Removing a file takes two steps in Iceberg and DuckLake: expiry, which drops the snapshots that list it, and cleanup, which deletes it. The Iceberg maintenance page gives the same order: expiry removes snapshots from the metadata, so time travel can't reach them, and "data files are not deleted until they are no longer referenced by a snapshot that may be used for time travel or rollback" ([Apache Iceberg, maintenance](https://iceberg.apache.org/docs/latest/maintenance/)). After expiry, cleanup deletes the files that no remaining snapshot lists, and in Delta Lake [vacuum](#vacuum-in-delta-lake) also deletes a file that an older version still lists once its tombstone is past the retention.

`wiki.pageviews_hourly` takes three hourly appends, and then hour 02 is corrected by an overwrite of that hour. Each append writes one file. The overwrite writes a file with the corrected hour-02 rows, and it removes the old file from the current snapshot. The snapshot that appended the old file still lists it. Until that snapshot is expired, the old file cannot be deleted without breaking time travel to it. [Upserting a corrected hour](#upsert-corrected-hour) shows the other way to write the same correction, and it leaves the same kind of old file behind.

Each format has its own expiry call and its own cleanup call. The table lists them, and the rest of the chapter follows the same order for each format, except that Delta Lake's vacuum does not wait for expiry.

| Format | Expiry call | Expiry deletes files? | Cleanup call |
| --- | --- | --- | --- |
| Iceberg (pyiceberg) | `expire_snapshots().by_ids(...)` | No | None in the library: count and remove files yourself |
| Delta Lake (deltalake) | `cleanup_metadata`, by log retention | No | `vacuum` |
| DuckLake | `ducklake_expire_snapshots` | No | `ducklake_cleanup_old_files`, then `ducklake_delete_orphaned_files` |

**Working rule:** Decide which snapshots or versions a reader may still need, and expire the rest before you remove any file. Never remove a file that a snapshot you keep still lists, and check that claim with a count before you delete. In Delta Lake, the versions you keep are those inside vacuum's retention, not those still in the log: set `delta.deletedFileRetentionDuration` to cover every version a reader may need.

## Expire snapshots with pyiceberg {#expire-snapshots-in-iceberg}

In pyiceberg 0.12.0, `table.maintenance.expire_snapshots()` takes snapshot IDs, with `by_ids` for a list or `by_id` for one, or an `older_than` timestamp. It has no argument that keeps the last N snapshots. This chapter chooses IDs from the commit order, as the case does: the three hourly appends are the first three snapshots. The IDs themselves are random 64-bit numbers, so the example prints the labels "snapshot 1", "snapshot 2" and so on, in the same order.

The overwrite adds two snapshots, not one. pyiceberg writes a delete snapshot that removes the old file, then an append snapshot that adds the corrected rows. Snapshot 4 is the delete and snapshot 5 is the append. Expiring the three appends therefore leaves the overwrite in place, and that is the state the example checks.

The expiry call deletes no data files, so the example counts them itself, before and after: the distinct files that the snapshots list, and the files on disk that none of them lists. Watch the last count, which is where the replaced file shows up:

Example `expire-iceberg-snapshots` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.16:

```python
"""Expire the three append snapshots by ID, then count what the snapshots still reference. The point rests on the
line that counts unreferenced data files on disk: expiry removes metadata, and the file the overwrite replaced stays."""

from lib.lakehouse import (
    ICEBERG_ID,
    create_iceberg_table,
    hour_corrections,
    hour_filter,
    new_warehouse,
    orphan_data_files,
    read_cut_hour,
    scan_arrow,
    snapshot_labels,
)


def referenced_files(table):
    """Distinct data files that some retained snapshot lists. Count them; do not print them."""
    # all_files() can list one file from several manifests, so the set counts each file once
    return len(set(table.inspect.all_files()["file_path"].to_pylist()))


with new_warehouse() as wh:
    table = create_iceberg_table(wh)
    for hour in (0, 1, 2):
        table.append(read_cut_hour(hour))
    # hour_filter(2) matches only hour 02's rows, so the overwrite replaces that hour and leaves hours 00 and 01 alone
    table.overwrite(hour_corrections(read_cut_hour(2)), overwrite_filter=hour_filter(2))

    ids = [snapshot.snapshot_id for snapshot in table.metadata.snapshots]  # metadata lists snapshots in commit order
    labels = snapshot_labels(ids)
    print("snapshots before expiry:", len(ids))
    print("data files referenced before expiry:", referenced_files(table))
    print("data files in the current snapshot:", len(table.inspect.files()))  # files() reads the current snapshot only

    expired = ids[:3]  # the three hourly appends, by commit order
    table.maintenance.expire_snapshots().by_ids(expired).commit()
    table = wh.catalog.load_table(ICEBERG_ID)

    print("remaining snapshots:", ", ".join(labels[s.snapshot_id] for s in table.metadata.snapshots))
    print("data files referenced after expiry:", referenced_files(table))
    # files under the table location that no remaining snapshot lists; a file a writer has not committed counts too
    print("unreferenced data files left on disk:", len(orphan_data_files(table)))
    print("rows in the current snapshot:", scan_arrow(table).num_rows)
    try:
        scan_arrow(table, snapshot_id=expired[-1])
    except ValueError as exc:
        print(f"read {labels[expired[-1]]}: {type(exc).__name__}")
```

Output:

```text
snapshots before expiry: 5
data files referenced before expiry: 4
data files in the current snapshot: 3
remaining snapshots: snapshot 4, snapshot 5
data files referenced after expiry: 3
unreferenced data files left on disk: 1
rows in the current snapshot: 1499
read snapshot 3: ValueError
```

Before the expiry, the table has 5 snapshots, and 4 data files are listed by at least one of them. The current snapshot lists only 3 of those files. The remaining one is the old hour-02 file, which snapshot 3 still lists. Reading the counts this way shows what the overwrite did: the current table is complete, and the history still holds the file the overwrite replaced.

Then the example expires snapshots 1 to 3, the three appends. The snapshots that remain are snapshot 4, snapshot 5, the delete from the overwrite and its append. Afterwards 3 data files are listed, and the old hour-02 file is no longer listed by any snapshot. It is still on disk: the example reports 1 unreferenced file. The current table still returns 1499 rows, so the expiry changed no data a reader of the current table sees.

The last read fails. A scan of snapshot 3 after the expiry raises `ValueError`, which the output shows as "read snapshot 3: ValueError". A reader that pinned snapshot 3 before the expiry gets an error, not the old rows. The error, `Snapshot not found`, names the snapshot's ID, but it does not say that an expiry removed the snapshot. Your own logs have to record which expiry ran and which snapshot the report used.

Which file the expiry left unreferenced, and why, shows in Figure 7.1, which draws the same 5 snapshots as a grid. Each row is a snapshot and each column a data file, in the order the files were written, and a square marks a file that snapshot lists. Each row's label says whether the expiry removes that snapshot or keeps it. Look at the column for file 3, the old hour-02 file. Snapshot 3 lists it, and snapshot 4, the overwrite's delete, does not, so snapshot 3 is the only snapshot that lists it. Once the three expired rows are gone, no kept row lists it, and the note in that column says so.

*Figure 7.1. Which data files each snapshot lists, and which snapshots the expiry removes.*

![Once the three appends expire, the one file only they listed is in no kept snapshot](https://rollingedition.ai/books/open-table-formats/2026.11.16/figures/snapshots-keep-files.svg)

Example `figure-snapshots-keep-files` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · matplotlib 3.11.2 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.16:

```python
"""Expire the three append snapshots, then draw which data files each snapshot lists. The figure rests on the printed
lines: file 3 is listed by snapshot 3 before the expiry and by no kept snapshot after it, and it stays on disk."""

from lib.figures import ACCENT, MUTED, new_figure, save
from lib.lakehouse import (ICEBERG_ID, create_iceberg_table, hour_corrections, hour_filter, new_warehouse,
                           orphan_data_files, read_cut_hour, snapshot_labels)


def listed(table, sid):
    """Data-file paths one snapshot lists. The output names them by write order instead."""
    return set(table.inspect.files(snapshot_id=sid)["file_path"].to_pylist())


with new_warehouse() as wh:
    table = create_iceberg_table(wh)
    for hour in (0, 1, 2):
        table.append(read_cut_hour(hour))
    # hour_filter(2) matches only hour 02, so the overwrite leaves hours 00 and 01 alone
    table.overwrite(hour_corrections(read_cut_hour(2)), overwrite_filter=hour_filter(2))

    ids = [s.snapshot_id for s in table.metadata.snapshots]  # commit order
    labels, names = snapshot_labels(ids), {}
    for sid in ids:  # name each file by the first snapshot that lists it, so file 1 is the first one written
        new = listed(table, sid) - set(names)
        names.update({path: f"file {len(names) + 1}" for path in new})
    before = {sid: {names[path] for path in listed(table, sid)} for sid in ids}
    print("snapshots before expiry:", len(ids))
    for sid in ids:
        print(f"{labels[sid]} lists:", ", ".join(sorted(before[sid])))
    print("data files referenced before expiry:", len(names))

    expired = ids[:3]  # the three hourly appends, by commit order
    table.maintenance.expire_snapshots().by_ids(expired).commit()
    table = wh.catalog.load_table(ICEBERG_ID)
    print("remaining snapshots:", ", ".join(labels[s.snapshot_id] for s in table.metadata.snapshots))
    referenced = set().union(*(listed(table, s.snapshot_id) for s in table.metadata.snapshots))  # what kept snapshots list
    unreferenced = sorted(set(names.values()) - {names[path] for path in referenced})
    print("data files referenced after expiry:", len(referenced))
    print("unreferenced after expiry:", ", ".join(unreferenced))
    print("unreferenced data files left on disk:", len(orphan_data_files(table)))  # counted from the folder

    # One row per snapshot, one column per file; a square marks a listed file, and the expired rows are muted.
    fig, ax = new_figure(height=3.2, sharex=False)
    for row, sid in enumerate(ids, start=1):
        xs = [col for col, name in enumerate(names.values(), start=1) if name in before[sid]]
        ax.scatter(xs, [row] * len(xs), s=90, marker="s", color=MUTED if sid in expired else ACCENT, zorder=3)
    ax.set_yticks(range(1, len(ids) + 1), [f"{labels[s]} ({'expired' if s in expired else 'kept'})" for s in ids])
    ax.set_xticks(range(1, len(names) + 1), list(names.values()))
    ax.set_ylim(len(ids) + 0.5, 0.5)  # snapshot 1 at the top, the current snapshot at the bottom
    col = list(names.values()).index(unreferenced[0]) + 1  # the one column no kept row lists
    ax.text(col, len(expired) + 1.5, "listed by no\nkept snapshot", ha="center", va="center", color=MUTED)
    save(fig, "snapshots-keep-files")
```

Output:

```text
snapshots before expiry: 5
snapshot 1 lists: file 1
snapshot 2 lists: file 1, file 2
snapshot 3 lists: file 1, file 2, file 3
snapshot 4 lists: file 1, file 2
snapshot 5 lists: file 1, file 2, file 4
data files referenced before expiry: 4
remaining snapshots: snapshot 4, snapshot 5
data files referenced after expiry: 3
unreferenced after expiry: file 3
unreferenced data files left on disk: 1
figure: figures/snapshots-keep-files.svg
```

Printed, the file no kept snapshot lists is file 3, and 1 unreferenced file is still in the table's folder: the expiry removed the snapshot that listed it, not the file.

**Working rule:** Expire Iceberg snapshots by ID, chosen from the commit order, and count the files each remaining snapshot lists before and after. Expect no disk space back from the expiry. pyiceberg removes metadata only, so the files it leaves behind stay on disk until you remove them yourself.

### Find orphan files after expiry {#find-orphan-files}

A file that no snapshot lists is an orphan. Spark and Java offer a `deleteOrphanFiles` action: it lists the table location, compares the files with the metadata and deletes the difference, and its default age interval is 3 days ([Apache Iceberg, maintenance](https://iceberg.apache.org/docs/latest/maintenance/)). The pyiceberg API page lists no orphan-file step, and the 0.12.0 package has none either. Its maintenance methods expire snapshots ([PyIceberg API](https://py.iceberg.apache.org/api/)).

A helper in the book's shared module, [`examples/lib/lakehouse.py`](https://github.com/rollingedition/book-open-table-formats/blob/72ea8e730acf6ce6c2c2fabd0a388682cbad4d5a/examples/lib/lakehouse.py), `orphan_data_files`, makes the comparison by hand. It lists the Parquet files under the table location, subtracts the files that any remaining snapshot lists, and returns the rest. The output shows only the count, because the file names carry UUIDs. That count is the line that shows the expired file is still on disk.

A listing cannot tell an orphan from a file that a writer has written and not yet committed. The commit links the file to the table, and until then the file looks unreferenced. This is why the age guards matter. [DuckLake's `ducklake_delete_orphaned_files`](#expire-and-clean-up-in-ducklake) keeps young files by default, and the Spark action takes an age interval for the same reason. pyiceberg has no interval, so the check is yours to make. Deleting an orphan is a separate decision, and it belongs after the writers that could commit it have stopped.

**Working rule:** Count orphans by listing, and remove them only after you have confirmed that no writer can still commit them and no reader still uses a snapshot that lists them. In pyiceberg, nothing in the library makes that check for you.

## Vacuum a table with deltalake {#vacuum-in-delta-lake}

Delta Lake does not delete a file when a commit replaces it. A Delta commit that removes or replaces a file adds a `remove` action to the log, a tombstone that says the file is no longer part of the table, and the file stays on disk. The protocol states that such files "can be lazily deleted by the vacuum command after a user-specified retention period (default 7 days)" ([Delta transaction log protocol, v4.4.1](https://raw.githubusercontent.com/delta-io/delta/v4.4.1/PROTOCOL.md)). The output in this section uses Delta's own version numbers, which start at 0.

Vacuum deletes the files whose tombstones are older than the retention, and the files older than it that the log never mentions. Until then, every version can be read, because every file it lists still exists. The Delta utility page states the cost: "The ability to time travel back to a version older than the retention period is lost after running vacuum" ([Delta Lake, VACUUM](https://docs.delta.io/delta-utility/)).

Log retention is Delta's expiry, and it deletes no data file. `cleanup_metadata` removes old log entries by `delta.logRetentionDuration`, 30 days by default ([deltalake source](https://github.com/delta-io/delta-rs/blob/python-v1.6.6/python/deltalake/table.py)), but only entries older than a checkpoint, a file in the log that records the whole table state at one version ([Delta protocol, metadata cleanup](https://raw.githubusercontent.com/delta-io/delta/v4.4.1/PROTOCOL.md)). The example uses zero seconds:

Example `delta-log-retention` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.16:

```python
"""Show that Delta Lake's log retention removes old versions from the log and deletes no data file, not even the old
hour-02 file that a delete removed. The point rests on the loadable-version lines and the two data-file counts."""

from lib.lakehouse import new_warehouse, read_cut_hour, hour_corrections

from pathlib import Path

from deltalake import DeltaTable, write_deltalake
from deltalake.exceptions import TableNotFoundError

RETENTION = "interval 0 seconds"  # teaching value only: every entry before the checkpoint is past it; production keeps 30 days
VERSIONS = range(6)  # versions 0 to 2 are the appends, 3 the delete, 4 the corrected append, 5 sets the retention


def loadable_versions(path):
    """Return the versions of the table that still load from the log."""
    found = []
    for version in VERSIONS:
        try:
            DeltaTable(path, version=version)
        except TableNotFoundError:  # the log no longer holds this version
            continue
        found.append(version)
    return found


with new_warehouse() as wh:
    path = str(wh.root / "delta" / "pageviews_hourly")
    for hour in (0, 1, 2):
        write_deltalake(path, read_cut_hour(hour), mode="append")
    DeltaTable(path).delete("hour_utc = '2024-06-03T02:00:00'")  # hour 02, matched by its exact timestamp
    write_deltalake(path, hour_corrections(read_cut_hour(2)), mode="append")
    DeltaTable(path).alter.set_table_properties({"delta.logRetentionDuration": RETENTION})

    print("versions loadable before cleanup:", len(loadable_versions(path)))
    files_before = len(list(Path(path).glob("*.parquet")))
    # cleanup_metadata deletes only log entries older than a checkpoint, so write one at the current version first
    DeltaTable(path).create_checkpoint()
    DeltaTable(path).cleanup_metadata()

    after = loadable_versions(path)
    print("versions loadable after cleanup:", len(after))
    print("current version after cleanup:", DeltaTable(path).version())
    assert after == [5]  # only the current version is still in the log
    files_after = len(list(Path(path).glob("*.parquet")))
    print("data files on disk before cleanup:", files_before)
    print("data files on disk after cleanup:", files_after)
    assert files_after == files_before  # expiry removed versions and no file, the old hour-02 file included
```

Output:

```text
versions loadable before cleanup: 6
versions loadable after cleanup: 1
current version after cleanup: 5
data files on disk before cleanup: 4
data files on disk after cleanup: 4
```

The log loads 6 versions before the cleanup, and after it only the current one, 5. The disk holds 4 data files before the cleanup and 4 after it.

The case has three appends, which make versions 0 to 2, and then the hour-02 correction. The correction is a delete of that hour, which is version 3, followed by an append of the corrected rows, which is version 4. Version 2 still lists the old hour-02 file, and version 3 does not. Nothing has been removed yet, and that is the state the next section starts from.

The default retention in deltalake is 168 hours, seven days. A table can set its own in the `delta.deletedFileRetentionDuration` property, and `vacuum` uses that property when you pass no `retention_hours`. The library refuses a retention shorter than the property's value unless you turn off `enforce_retention_duration`. A longer retention needs no flag. The retention you choose is a promise about how far back history reaches. Every reader that opens an older version depends on it, and the next section shows the refusal and why this chapter's teaching run turns the check off.

**Working rule:** Keep vacuum's default retention, or set a longer one in `delta.deletedFileRetentionDuration`, so that every version a reader may request is still readable for that long after it stops being current. Go shorter only after you have checked the longest read and the longest write in your system, and only by turning `enforce_retention_duration` off as a deliberate, recorded decision.

### Dry run first {#vacuum-dry-run-first}

A dry run lists what a real call, such as a vacuum, would delete and deletes none of it. Run one before every vacuum, and compare its count with the table's history. A short list can be checked by hand: here, each file in the list is one that a delete removed, and the one that matters is the delete in version 3. Two dry runs on that history ask vacuum, at two retentions, what it would delete:

Example `vacuum-delta-dry-run` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.16:

```python
"""Show that vacuum's default retention keeps a file that a delete has just removed, and that a read of an older version
fails once a teaching-only run removes that file. The point rests on the default-retention line and the read of version 2."""

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake
from deltalake.exceptions import DeltaError

from lib.lakehouse import new_warehouse, read_cut_hour, read_delta, hour_corrections

with new_warehouse() as wh:
    path = str(wh.root / "delta" / "pageviews_hourly")
    for hour in (0, 1, 2):
        write_deltalake(path, read_cut_hour(hour), mode="append")
    dt = DeltaTable(path)
    dt.delete("hour_utc = '2024-06-03T02:00:00'")  # hour 02, matched by its exact timestamp
    # hour_corrections halves the views of some page titles in hour 02, so this append holds the corrected rows
    write_deltalake(path, hour_corrections(read_cut_hour(2)), mode="append")

    dt = DeltaTable(path)
    print("current version:", dt.version())
    # the delete was seconds ago, so the default retention still keeps its file
    print("default retention, dry run lists:", len(dt.vacuum(dry_run=True)))
    try:
        dt.vacuum(retention_hours=0, dry_run=True)  # a retention below the table's minimum: refused without the flag
    except DeltaError as exc:
        print("zero retention without the flag:", type(exc).__name__)
    # Teaching run only: a zero-hour retention removes files at once. Production keeps the 168-hour default.
    print("zero retention, dry run lists:", len(dt.vacuum(retention_hours=0, dry_run=True, enforce_retention_duration=False)))
    print("zero retention, removed:", len(dt.vacuum(retention_hours=0, dry_run=False, enforce_retention_duration=False)))
    print("rows in version 0:", read_delta(path, version=0).num_rows)  # version 0 reads files the vacuum left alone
    try:
        read_delta(path, version=2)  # version 2 still lists the hour-02 file that the vacuum removed
    except pa.ArrowInvalid as exc:
        print("read version 2:", type(exc).__name__)
```

Output:

```text
current version: 4
default retention, dry run lists: 0
zero retention without the flag: DeltaError
zero retention, dry run lists: 1
zero retention, removed: 1
rows in version 0: 499
read version 2: ArrowInvalid
```

The table is at version 4. With the default retention, the dry run lists 0 files. The file that version 3 removed is too recent to be listed, and vacuum keeps it.

The next call sets the retention to zero, and deltalake refuses it with DeltaError. The library's own message says that the minimum retention is 168 hours, so the check protects the default.

The teaching run turns that check off with `enforce_retention_duration=False`. The code marks it as teaching-only. With the check off, the dry run lists 1 file, and the real vacuum removes 1 file, the old hour-02 file. Zero retention suits a demo, because it deletes the file at once. In production it is wrong: any reader that started before the vacuum, or that pinned an older version, loses the files it reads in the middle of a query. A short retention also deletes the files of a writer that has written but not yet committed. The Delta utility page warns that "tables can be corrupted when VACUUM deletes files that have not yet been committed" ([Delta Lake, VACUUM](https://docs.delta.io/delta-utility/)).
The read at the end shows what the vacuum cost. Version 0 still reads, with 499 rows, because every file it lists still exists. Version 2 still loads from the log, but its read fails with `ArrowInvalid`, shown as "read version 2: ArrowInvalid". That class is the one the query engine raises for a failed Parquet read, and the message names the missing object. The read prints only the class. Read the message in your own logs before you decide that the table is damaged: it says which object is missing, and so whether a vacuum removed it.

A dry run is not a promise about the real run. A writer that commits between the two calls changes the table, and the real run works from the table state it finds. Treat the dry-run count as a check on what you expect, and read the real count next to it.

**Working rule:** Run vacuum as a dry run first and read the count. Remove files with a real run only when the count matches what you expected from the table's history, and keep the default retention unless you have checked the longest read in your system.

## Expire and clean up in DuckLake {#expire-and-clean-up-in-ducklake}

DuckLake keeps the physical files of a snapshot until that snapshot is expired. The DuckLake documentation says it this way: "Data can only be physically removed from DuckLake by expiring snapshots that refer to the old data" ([DuckLake, expire snapshots](https://ducklake.select/docs/stable/duckdb/maintenance/expire_snapshots)). The same page notes that expiry does not immediately delete the files it leaves unreferenced, and the cleanup page gives the second call ([DuckLake, cleanup of files](https://ducklake.select/docs/stable/duckdb/maintenance/cleanup_of_files)).

So DuckLake maintenance has two steps, and the example below runs both. `ducklake_expire_snapshots` takes a list of snapshot numbers in `versions`, or an `older_than` timestamp, but not both. `ducklake_cleanup_old_files` removes the files that expiry scheduled. With `older_than`, it removes only files scheduled before a given time. With `cleanup_all => true`, it removes every scheduled file, with no age check. Both steps support `dry_run`.

A third call, `ducklake_delete_orphaned_files`, handles files that no snapshot lists and that cleanup never scheduled, such as a file a writer left behind after a failed commit. Its default keeps a file that is still young, because a writer may be about to commit it. Its `cleanup_all` option removes such files regardless of age. The [catalog chapter](#catalog-production-failures) shows what that option does when a second catalog shares the data folder.

Attaching the catalog and creating the schema and the table through the helpers makes three snapshots before any rows: the attach makes snapshot 1, and the two `CREATE` statements make snapshots 2 and 3, labelled from 1 with setup included, as [chapter 2](#snapshot-decisions) does. Then the loading helper inserts hours 00 to 02, deletes hour 02 and inserts the corrected hour 02. That makes 8 snapshots, which the example labels "snapshot 1" up to the last one. The last is the corrected insert. The one before it is the delete, which drops the old hour-02 file. The insert before that, snapshot 6, is the last snapshot that lists it.

Example `ducklake-expire-cleanup` (Python 3.12.15 · deltalake 1.6.6 · duckdb 2.0.0 · pyarrow 26.0.1 · pyiceberg 0.12.0), passing in Edition 2026.11.16:

```python
"""Expire every snapshot before the correction, clean up what expiry released, and run the orphan check as a dry run. The
point rests on the cleanup lines and on the orphan line, which shows that the default age check spares the stray copy."""

import shutil
from pathlib import Path

import duckdb

from lib.lakehouse import (
    DUCKLAKE_ALIAS, NAMESPACE, TABLE, connect_ducklake, create_ducklake_table,
    ducklake_file_count, ducklake_file_paths, load_ducklake_with_correction, new_warehouse,
    version_labels,
)

LAKE = f"{DUCKLAKE_ALIAS}.{NAMESPACE}.{TABLE}"


def listed(con, call):
    """Run a DuckLake procedure and return how many rows it lists."""
    return con.sql(f"CALL {call}").to_arrow_table().num_rows


with new_warehouse() as wh:
    con = connect_ducklake(wh.con)
    create_ducklake_table(con, wh.root)
    load_ducklake_with_correction(con)  # lib inserts hours 00 to 02, deletes hour 02, then inserts the corrected hour 02

    # ORDER BY 1 sorts by snapshot_id, which grows with each commit, so the labels number the snapshots in commit order
    ids = [r[0] for r in con.execute(f"SELECT snapshot_id FROM ducklake_snapshots('{DUCKLAKE_ALIAS}') ORDER BY 1").fetchall()]
    labels = version_labels(ids, word="snapshot")
    print("snapshots before expiry:", len(ids))
    print("data files in the current snapshot:", ducklake_file_count(con, DUCKLAKE_ALIAS, TABLE))
    stray = Path(sorted(ducklake_file_paths(con, DUCKLAKE_ALIAS, TABLE))[0])  # sorted, so every run copies the same file
    shutil.copy(stray, stray.with_name("stray.parquet"))  # written, but no snapshot lists it

    expired = ids[:-1]  # all but the last snapshot, which is the corrected insert and stays
    # versions takes DuckLake's snapshot numbers, not the labels
    expire = f"ducklake_expire_snapshots('{DUCKLAKE_ALIAS}', versions => {expired}"
    print("expiry dry run lists:", listed(con, f"{expire}, dry_run => true)"))
    con.execute(f"CALL {expire})")
    print("remaining snapshots:", labels[ids[-1]])
    # no age check, so this is safe only because one catalog owns the folder and no reader is running
    cleanup = f"ducklake_cleanup_old_files('{DUCKLAKE_ALIAS}', cleanup_all => true"
    print("cleanup dry run lists:", listed(con, f"{cleanup}, dry_run => true)"))
    print("cleanup removed:", listed(con, f"{cleanup})"))
    # no cleanup_all, so the default age check spares the stray copy, which was written seconds ago
    orphans = f"ducklake_delete_orphaned_files('{DUCKLAKE_ALIAS}', dry_run => true)"
    print("orphans listed without cleanup_all:", listed(con, orphans))
    print("rows in the current snapshot:", con.sql(f"SELECT count(*) FROM {LAKE}").fetchall()[0][0])
    try:
        # the newest expired snapshot, the delete; reading it now fails
        con.sql(f"SELECT count(*) FROM {LAKE} AT (VERSION => {expired[-1]})").fetchall()
    except duckdb.InvalidInputException as exc:
        print(f"read {labels[expired[-1]]}: {type(exc).__name__}")
```

Output:

```text
snapshots before expiry: 8
data files in the current snapshot: 3
expiry dry run lists: 7
remaining snapshots: snapshot 8
cleanup dry run lists: 1
cleanup removed: 1
orphans listed without cleanup_all: 0
rows in the current snapshot: 1499
read snapshot 7: InvalidInputException
```

The current snapshot lists 3 data files, and one of them is copied to another name in the same folder, to stand in for a file a writer has written but not committed, as [Find orphan files](#find-orphan-files) describes. Then the steps run in order.

The expiry dry run lists 7 snapshots, which are all of them except the corrected insert. Because that insert stays, the table's current state is untouched. The real expiry leaves snapshot 8. The old hour-02 file is released at this step, because snapshot 6, the last snapshot that listed it, is expired.

The cleanup dry run lists 1 file, the old hour-02 file. The DELETE matched every row in that file, and no delete file is scheduled with it, so the old file is the only one left to remove. The real cleanup removes 1 file.

The orphan check lists 0 orphans. The stray copy is still in the folder, because the default age check kept it: the file is only seconds old. The table still returns 1499 rows.

Last, the read of the delete, snapshot 7, fails: "read snapshot 7: InvalidInputException". The class is the one DuckLake raises for a version it no longer has.

`cleanup_all => true` appears here because there is one catalog and no reader. Production uses `older_than` instead, with an age longer than the longest read, so that the cleanup removes only files that have been scheduled for long enough.

**Working rule:** Expire DuckLake snapshots first, then run each cleanup call as a dry run and then for real, in that order. Keep the default orphan check. Use `cleanup_all` only when one catalog owns the data folder and no reader still uses the files it removes, and use `older_than` otherwise.

## What goes wrong in production {#maintenance-production-failures}

**Removing a file that a reader still uses.** A query that started before a vacuum or a cleanup reads a file that is then gone, and the read fails partway through. You will see it as a read error that names a missing object, in a job that ran during a maintenance window. Schedule maintenance outside the long reads, and keep retention longer than the longest of them. A short retention can also delete a file that a writer has written and not yet committed, which corrupts the table rather than failing one read, so keep retention longer than the longest running write as well.

**Retention shorter than the longest query.** The seven-day default in Delta Lake is a margin, not a measurement. A dashboard that reads a version from a month ago is outside it. If a reader must see an older version, the retention has to cover it, or the reader has to copy the data first.

**Time travel that fails after maintenance.** The expired snapshot and the vacuumed version fail with `ValueError`, `ArrowInvalid` or `InvalidInputException`, depending on the format. [Iceberg](#expire-snapshots-in-iceberg) raises `ValueError`, and [Delta](#vacuum-dry-run-first) raises `ArrowInvalid`. [DuckLake](#expire-and-clean-up-in-ducklake) raises `InvalidInputException`. A Delta version that log retention removed no longer loads, with `TableNotFoundError`. Any job that records a snapshot ID or a version number to read later fails the same way once that snapshot is expired. Keep your own record of which snapshot each report used, so that a rebuild starts from the data and does not depend on reading the old snapshot.

**A dry run that differs from the real run.** Two calls can disagree when a writer commits between them. The count from the dry run is what you expected, not what the real run will remove. Read the real count next to the dry-run count, and stop if they differ by more than you can explain.

**An audit that needs an older snapshot.** Some reports must reproduce a figure from months earlier. Expiry removes that ability for good, so decide the audit window before you expire, and keep the snapshots or the copied data the audit needs. Expiry is not a substitute for a copy.

**A cleanup that deletes a file another catalog needs.** `cleanup_all` and the orphan check with `cleanup_all` delete files by path. If a second catalog points at the same data folder, its live files look like orphans to the first catalog. The [catalog chapter](#catalog-production-failures) shows that failure in a temporary directory.

**Working rule:** Before you expire or clean up, list the readers, reports and audits that may open an older snapshot or version, and set the retention to cover the longest of them. Run each call as a dry run, compare its count with what you expected, and run the real call only when the two agree.

## Decisions this chapter made {#maintenance-decisions}

- Iceberg snapshots are expired by ID, chosen from the commit order. The Iceberg expiry in this chapter is not by age, so its result does not depend on the machine's clock, and pyiceberg 0.12.0 has no keep-last-N argument.
- pyiceberg removes no files, so `expire-iceberg-snapshots` counts reachable and unreachable files and leaves the removal to the reader.
- The zero-retention run in `vacuum-delta-dry-run` is teaching-only. It is marked in the code, and production keeps the default retention.
- The zero-second log retention in `delta-log-retention` is teaching-only, like the zero-hour vacuum: every log entry before the checkpoint is past it, however long the run takes. Production keeps the 30-day default.
- DuckLake expiry and cleanup are separate calls, and each runs as a dry run before the real call.
- `cleanup_all` appears only in single-catalog examples. The catalog chapter covers the case where it removes live files.
- Each example prints counts, stable labels and error class names, and no IDs, timestamps, file names or paths ([chapter 1](#first-table-decisions) gives the reason), and every number in the text comes from a bound output line or from the example's own construction.
- Every example keeps the table the earlier chapters built, so each count can be checked against the history the reader has seen.
- Each example builds its own temporary warehouse, so no output depends on an earlier example or on the machine that runs it.
- The stray copy in `ducklake-expire-cleanup` stands in for a file a writer has not committed, as [Find orphan files](#find-orphan-files) describes. That shows the orphan rule without waiting for a file to age, because the run takes seconds.
