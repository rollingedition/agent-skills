"""Query the receiver's stored rows with DuckDB: the spans each process stored, the join across the process boundary,
and the orphans (spans whose parent names no stored span). Every query orders by its group keys, so the printed order
is the same on every run; the server's own times are never printed."""
import tempfile
from pathlib import Path

from lib.case import load_messages, scenario_to_route
from lib.contacts_server import SERVICE_NAME
from lib.dayrun import run_day_traced
from lib.export import write_jsonl
from lib.otlp import start
from lib.query import connect

DAY = "2026-12-08"
receiver = start()                   # the book's receiver on loopback, as in the example before
ids = {m.message_id for m in load_messages(DAY) if scenario_to_route(m.scenario) == "messages"}
run_day_traced(DAY, message_ids=ids, otlp_endpoint=receiver.endpoint)  # both processes export to the receiver
with tempfile.TemporaryDirectory() as folder:
    rows_file = Path(folder) / "spans.jsonl"          # the stored rows, as a file a query can read
    write_jsonl(rows_file, receiver.rows())
    db = connect(rows_file)
    assert db.execute("SELECT count(*) FROM spans").fetchone()[0] == len(receiver.rows())
    per_service = db.execute("SELECT service, count(*), count(DISTINCT trace_id) FROM spans GROUP BY service "
                             "ORDER BY service").fetchall()
    server_names = db.execute("SELECT name, count(*) FROM spans WHERE service = ? GROUP BY name ORDER BY name",
                              [SERVICE_NAME]).fetchall()
    # a server span whose parent is an assistant span: the join across the process boundary
    joins = db.execute("SELECT c.name, count(*) FROM spans c JOIN spans p ON c.parent_span_id = p.span_id "
                       "WHERE c.service <> p.service GROUP BY c.name ORDER BY c.name").fetchall()
    both = db.execute("SELECT count(*) FROM (SELECT trace_id FROM spans GROUP BY trace_id "
                      "HAVING count(DISTINCT service) = 2 ORDER BY trace_id)").fetchone()[0]
    orphans = db.execute("SELECT count(*) FROM spans c WHERE c.parent_span_id IS NOT NULL AND NOT EXISTS "
                         "(SELECT 1 FROM spans p WHERE p.span_id = c.parent_span_id) ORDER BY 1").fetchone()[0]

for service, count, traces in per_service:
    print(f"stored spans from {service}: {count}, in {traces} traces")
for name, count in server_names:
    print(f"contacts server spans named {name}: {count}")
for name, count in joins:
    print(f"contacts server spans under an assistant span, named {name}: {count}")
print("traces holding both processes' spans:", both)
print("orphans in the stored rows:", orphans)
