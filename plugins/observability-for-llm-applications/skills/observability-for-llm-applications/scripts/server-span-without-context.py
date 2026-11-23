"""Read baseline day 1's recorded contacts-server spans for message 16297. The recorder's client sent no context, so the
server's lookup span has no parent and starts a trace of its own: a detached root. The prose's two counts rest on the
printed lines, and the assert backs the parent count."""
from lib.dayrun import DATA
import json

rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "contacts-spans.jsonl").read_text(encoding="utf-8").splitlines()]
lookups = [r for r in rows if r["name"] == "tools/call find_contact"]
with_parent = [r for r in lookups if r["parent_span_id"] is not None]
lookup = next(r for r in rows if r["name"] == "contacts.lookup")
call = lookups[0]
assert with_parent == [] and lookup["parent_span_id"] == call["span_id"] and lookup["trace_id"] == call["trace_id"]
print("tools/call find_contact spans in the contacts server:", len(lookups))
print("of them with a parent:", len(with_parent))
print("contacts.lookup under it, in its trace: yes")
