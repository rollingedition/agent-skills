"""Replay baseline day 1's messages that route to the messages tools, with the contacts server live, and send both
processes' spans to one receiver: every server span joins a trace the assistant made. The server's clock is its own,
so the example prints counts only, never a span time from it."""
from lib.assistant import AGENT
from lib.case import load_messages, scenario_to_route
from lib.contacts_server import SERVICE_NAME
from lib.dayrun import run_day_traced
from lib.otlp import start

DAY = "2026-12-08"
receiver = start()                   # the book's receiver on loopback; its port is never printed
ids = {m.message_id for m in load_messages(DAY) if scenario_to_route(m.scenario) == "messages"}  # only these can call a contacts tool
traced = run_day_traced(DAY, message_ids=ids, otlp_endpoint=receiver.endpoint)  # both processes export here
stored = receiver.rows()
mine = [row for row in stored if row["resource"]["service.name"] == AGENT]
theirs = [row for row in stored if row["resource"]["service.name"] == SERVICE_NAME]
mine_ids = {row["span_id"] for row in mine}
find = {row["trace_id"] for row in mine if row["name"] == "execute_tool find_contact"}  # those messages' traces
both = {row["trace_id"] for row in mine} & {row["trace_id"] for row in theirs}

assert mine == traced.spans                    # the stored assistant rows equal export.py's rows
assert find <= {row["trace_id"] for row in theirs}  # each find_contact message has server spans in its trace
assert find <= {row["trace_id"] for row in mine if row["name"].startswith("invoke_agent")}  # and a message root
# every server span whose parent is set names a stored span, from either process: the join crosses no gap
assert all(row["parent_span_id"] in mine_ids | {r["span_id"] for r in theirs} for row in theirs if row["parent_span_id"])

rooted = {row["trace_id"] for row in mine if row["name"].startswith("invoke_agent")}
print("messages replayed:", len(traced.runs))
print("messages that called find_contact:", len(find))
print("assistant traces with a message root:", len(rooted))
print("assistant traces without one (the startup, with its discovery call):", len({row["trace_id"] for row in mine} - rooted))
print("traces with spans from both processes:", len(both))
print("spans from the assistant, in the find_contact messages:", sum(row["trace_id"] in find for row in mine))
print("spans from the contacts server, in the find_contact messages:", sum(row["trace_id"] in find for row in theirs))
print("spans from the assistant, all messages:", len(mine))
print("spans from the contacts server, all messages:", len(theirs))
print("contacts server spans under an assistant span:", sum(row["parent_span_id"] in mine_ids for row in theirs))
print("stored assistant rows equal the exporter's rows: yes (asserted)")
receiver.stop()
