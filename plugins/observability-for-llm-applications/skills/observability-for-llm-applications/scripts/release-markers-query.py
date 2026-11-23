"""Replay the same 60 messages under each of the five releases, export every span to one store, and query the release
markers: the resource's service.version and the inference span's gen_ai.prompt.version. Each release's markers are the
only thing that tells its traces apart, so the query must give five distinct pairs. The span IDs come from one sequence,
so no two releases share an ID in the store."""
from lib.assistant import RELEASES
from lib.case import load_messages
from lib.export import write_jsonl
from lib.gate import release_spans
from lib.query import connect
from lib.report import fmt_int

import tempfile
from pathlib import Path

DAY = "2026-12-08"
FOLDERS = {"r0": "baseline-day-1", "r1": "release-prompt-v2", "r2": "release-model-swap",
           "r3": "release-top-8", "r4": "release-cache-off"}
PAIRED = {m.message_id for m in load_messages("2026-12-08-paired")}   # the 60 messages, in every release's recording
rows = release_spans(DAY, FOLDERS, PAIRED)
with tempfile.TemporaryDirectory() as folder:
    rows_file = Path(folder) / "spans.jsonl"     # the stored rows, as a file a query can read
    write_jsonl(rows_file, rows)
    db = connect(rows_file)
    markers = db.execute(
        "WITH inference AS (SELECT json_extract_string(resource, '$.\"service.version\"') AS version, "
        "json_extract_string(attributes, '$.\"gen_ai.prompt.version\"') AS prompt, "
        "json_extract_string(attributes, '$.\"gen_ai.prompt.name\"') AS name, trace_id FROM spans "
        "WHERE json_extract_string(attributes, '$.\"gen_ai.operation.name\"') = 'chat') "
        "SELECT version, prompt, name, count(*), count(DISTINCT trace_id) FROM inference "
        "GROUP BY version, prompt, name ORDER BY version, prompt, name").fetchall()
    per_version = db.execute(
        "SELECT json_extract_string(resource, '$.\"service.version\"') AS version, count(DISTINCT trace_id) "
        "FROM spans GROUP BY version ORDER BY version").fetchall()

for version, prompt, name, calls, traces in markers:
    print(f"service.version {version}, gen_ai.prompt.version {prompt}, {name}: {fmt_int(calls)} inference spans")
for version, traces in per_version:
    print(f"service.version {version}, messages (traces): {fmt_int(traces)}")
pairs = {(version, prompt) for version, prompt, _, _, _ in markers}
assert pairs == {(r.service_version, r.prompt_version) for r in RELEASES.values() if r.name in FOLDERS}
assert all(traces == len(PAIRED) for _, traces in per_version)   # every release answered every paired message
