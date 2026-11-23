"""The incident day's failed messages, kept by a 10 percent head sample and by the tail rule. A message failed when a span
in its trace ends with ERROR (chapter 8). The head sample decides before anything runs, so the count it keeps is chance;
the tail rule reads each whole trace and keeps every failed one. A detached root is judged as a trace of its own."""
from lib.clock import NS_PER_SECOND
from lib.dayrun import run_day_traced
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_ms, fmt_share, fmt_usd
from lib.sampling import TailRule, head_sample, message_traces, only_messages
from lib.stats import nearest_rank

MODEL = "Qwen3-4B-Instruct-2507"
BASE, INCIDENT = "2026-12-08", "2026-12-09"
SLOW_NS = 20 * NS_PER_SECOND                        # chapter 9's latency objective: a message over 20 s is slow
price = PriceTable()
# The expensive threshold is baseline day 1's 99th percentile of message cost (nearest rank, PL-5): the incident is
# judged by the day before it, not by itself.
expensive = nearest_rank([t.cost for t in only_messages(message_traces(run_day_traced(BASE, live=False).spans, BASE, MODEL, price))], 99)
live = run_day_traced(INCIDENT)                     # live: the contacts server runs the injected faults over stdio
traces = message_traces(live.spans + live.server, INCIDENT, MODEL, price)  # each trace whole, the server's spans included
messages = only_messages(traces)
failed = [t for t in messages if t.error]
head = head_sample(messages, 0.1)
kept = TailRule(keep_error=True, slow_ns=SLOW_NS, expensive=expensive, budget=sum(len(t.rows) for t in traces)).keep(traces)
print("latency threshold, the 20 s objective:", fmt_ms(SLOW_NS))
print("cost threshold, baseline day 1's 99th percentile per message:", fmt_usd(expensive))
print("messages on the incident day:", fmt_int(len(messages)))
print("detached roots, traces of their own with no message, incident day:", fmt_int(len(traces) - len(messages)))
print("messages with an error, of all messages:", fmt_int(len(failed)))
print("share of messages with an error:", fmt_share(len(failed), len(messages)))
print(f"messages with an error kept by a 10% head sample, of {len(failed)}:", fmt_int(sum(t.error for t in head)))
print("share of messages with an error kept by a 10% head sample:", fmt_share(sum(t.error for t in head), len(failed)))
print(f"messages with an error kept by the tail rule, of {len(failed)}:", fmt_int(sum(t.seq in kept for t in failed)))
print("share of messages with an error kept by the tail rule:", fmt_share(sum(t.seq in kept for t in failed), len(failed)))
assert all(t.seq in kept for t in failed)           # the tail rule keeps every failed message
assert sum(t.error for t in head) < len(failed)     # the head sample loses most of them
assert all(max(r["end_ns"] for r in t.rows if r["parent_span_id"] is None) == max(r["end_ns"] for r in t.rows)
           for t in traces)                         # the root ends last, so a trace is whole when its root arrives (B-83)
