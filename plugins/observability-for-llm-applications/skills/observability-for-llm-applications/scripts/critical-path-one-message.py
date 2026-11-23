"""Replay the slowest message of baseline day 1 and list the chain of spans that sets its end time. The replay runs the
calls one after another, so every call is on the chain, and shortening any one of them shortens this message: the point
rests on the path lines and the assert that the path covers the whole message. The recorder's gaps between calls are
not in the replay; the day's total of them is printed beside it. The tool's time is modelled, a few microseconds, so it
prints as 0.0 ms."""
from lib.critical_path import critical_path
from lib.dayrun import DATA, run_day, run_day_traced
from lib.report import fmt_ms, fmt_share

import json

DAY = "2026-12-08"
runs = run_day(DAY)                                                      # all 200 messages, in arrival order
slowest = max(runs, key=lambda run: run.replied_ns - run.arrived_ns)     # the longest of the day; no other message ties with it
traced = run_day_traced(DAY, [slowest.message.message_id], live=False)   # its spans, replayed the same way
by_id = {row["span_id"]: row for row in traced.spans}
path = critical_path(traced.spans)                                       # root first, then the chain in time order
message = by_id[path[0]]
message_time = message["end_ns"] - message["start_ns"]
chain = [by_id[span_id] for span_id in path[1:]]
covered = sum(row["end_ns"] - row["start_ns"] for row in chain)

print("message:", slowest.message.message_id)
print("route:", slowest.outcome.route)
print("message time:", fmt_ms(message_time))
for number, row in enumerate(chain, start=1):
    # The inference spans carry their prompt's name, so the route call and the answer calls read apart.
    name = row["attributes"].get("gen_ai.prompt.name", row["name"])
    print(f"on the path, {number}: {name}, time: {fmt_ms(row['end_ns'] - row['start_ns'])}")
print("share of the message time on the path:", fmt_share(covered, message_time))

# The recorder's own offsets give the gaps the replay does not keep: each message's span minus its calls' times.
rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
gap_ns = 0
for message_id in sorted({row["message_id"] for row in rows}):
    calls = [row for row in rows if row["message_id"] == message_id]
    span = max(c["offset_ns"] + c["total_ns"] for c in calls) - min(c["offset_ns"] for c in calls)
    gap_ns += span - sum(c["total_ns"] for c in calls)
print("gaps between calls, recorded, all messages of the day:", fmt_ms(gap_ns))

# A constructed tree, not the recording: two calls that overlap. The one that ends last sets the end, and the other
# is off the path, since the walk back from the end reaches the later call's start before it reaches the earlier one.
toy = [
    {"span_id": "a", "parent_span_id": None, "start_ns": 0, "end_ns": 10, "span_seq": 1},
    {"span_id": "b", "parent_span_id": "a", "start_ns": 0, "end_ns": 6, "span_seq": 2},
    {"span_id": "c", "parent_span_id": "a", "start_ns": 2, "end_ns": 9, "span_seq": 3},
]
toy_covered = sum(row["end_ns"] - row["start_ns"] for row in toy if row["span_id"] in critical_path(toy)[1:])
print("constructed overlap, span IDs on the path:", ", ".join(critical_path(toy)))
print("constructed overlap, share of the root's time on the path:", fmt_share(toy_covered, toy[0]["end_ns"] - toy[0]["start_ns"]))
assert critical_path(toy) == ["a", "c"]
assert covered == message_time                 # the chain's calls cover the whole message, with no gap
assert len(chain) == len(traced.spans) - 1     # every call of the message is on the path
