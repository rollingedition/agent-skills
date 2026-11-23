"""Take each message's last answer call on baseline day 1, the one that writes the reply the user reads, and compare its time
to first chunk with its total time, by route. Fallback replies make no answer call, so they have no first chunk, and each
interval resamples messages, not calls (PL-6)."""

from lib.dayrun import DATA, run_day
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.stats import bootstrap_interval, nearest_rank

import json
from collections import defaultdict

runs = run_day("2026-12-08")
routes = {run.message.message_id: run.outcome.route for run in runs}
rows = [json.loads(line) for line in (DATA / "baseline-day-1" / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
# A first chunk comes before the call ends, and the recorder keeps both times for every call.
assert all(row["ttfc_ns"] <= row["total_ns"] for row in rows)
last_answer = {}
for row in sorted(rows, key=lambda r: r["seq"]):          # the sequence numbers give the order the calls were made
    if row["step"] == "answer":
        last_answer[row["message_id"]] = row               # the later call overwrites the earlier one
by_route = defaultdict(list)
for message_id, row in last_answer.items():
    by_route[routes[message_id]].append(row)
assert not any(routes[message_id] == "fallback" for message_id in last_answer)

print("interval method: bootstrap over messages, 2,000 resamples, seed 20261207, 95%")
for route in sorted(by_route):
    calls = by_route[route]
    ttfc = [call["ttfc_ns"] for call in calls]
    total = [call["total_ns"] for call in calls]
    low, high = bootstrap_interval(calls, lambda units: nearest_rank([u["ttfc_ns"] for u in units], 50))
    print(f"{route}, messages with an answer call: {fmt_int(len(calls))}")
    print(f"{route}, time to first chunk, median: {fmt_ms(nearest_rank(ttfc, 50))}")
    print(f"{route}, time to first chunk, 95% interval: {fmt_ms(low)} to {fmt_ms(high)}")
    print(f"{route}, total time of the answer call, median: {fmt_ms(nearest_rank(total, 50))}")
    print(f"{route}, time to first chunk, share of the call's time: {fmt_share(sum(ttfc), sum(total))}")

route_calls = [row for row in rows if row["step"] == "route"]
print("route calls, time to first chunk, median, all messages:", fmt_ms(nearest_rank([c["ttfc_ns"] for c in route_calls], 50)))
print("route calls, n:", fmt_int(len(route_calls)))
print("messages with no answer call:", fmt_int(len(runs) - len(last_answer)))
