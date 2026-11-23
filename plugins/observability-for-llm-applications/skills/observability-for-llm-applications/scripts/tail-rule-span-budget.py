"""The tail rule under a span budget on the incident day: errors first, then the slowest messages, then the costliest, each
kept whole until the budget is spent. The budget of 120 spans is below the 127 the rule would keep with none, so it has
to drop something; the point rests on every error being kept and the slow message with no error being dropped."""
from lib.clock import NS_PER_SECOND
from lib.dayrun import run_day_traced
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_ms, fmt_share
from lib.sampling import TailRule, message_traces, only_messages, retained_bytes
from lib.stats import nearest_rank

MODEL = "Qwen3-4B-Instruct-2507"
BASE, INCIDENT = "2026-12-08", "2026-12-09"
BUDGET, SLOW_NS = 120, 20 * NS_PER_SECOND
price = PriceTable()
base = only_messages(message_traces(run_day_traced(BASE, live=False).spans, BASE, MODEL, price))
expensive = nearest_rank([t.cost for t in base], 99)  # the baseline day's 99th percentile of cost, as in the last example
live = run_day_traced(INCIDENT)                     # live: the contacts server runs the injected faults over stdio
traces = message_traces(live.spans + live.server, INCIDENT, MODEL, price)  # each trace whole, the server's rows included
messages = only_messages(traces)
spans = sum(len(t.rows) for t in messages)
kept = TailRule(True, SLOW_NS, expensive, BUDGET).keep(traces)
no_budget = TailRule(True, SLOW_NS, expensive, sum(len(t.rows) for t in traces)).keep(traces)
kept_spans = sum(len(t.rows) for t in traces if t.seq in kept)
dropped = [t for t in messages if t.duration_ns > SLOW_NS and not t.error and t.seq not in kept]
print("spans in the incident day's messages:", fmt_int(spans))
print("spans in messages with an error:", fmt_int(sum(len(t.rows) for t in messages if t.error)))
print("span budget:", fmt_int(BUDGET))
print("spans the tail rule keeps with no budget, incident day:", fmt_int(sum(len(t.rows) for t in traces if t.seq in no_budget)))
print("spans kept under the budget, of all spans:", fmt_int(kept_spans))
print("share of spans kept under the budget:", fmt_share(kept_spans, spans))
for reason in ("error", "slow", "expensive"):
    print(f"messages kept for {reason}, under the budget:", fmt_int(sum(v == reason for v in kept.values())))
print("slow messages with no error, dropped for the budget:", fmt_int(len(dropped)))
print("time of the slowest message dropped for the budget:", fmt_ms(max(t.duration_ns for t in dropped)))
print("messages over the expensive threshold with no error or slow time, incident day:",
      fmt_int(sum(t.cost > expensive and not t.error and t.duration_ns <= SLOW_NS for t in messages)))
print("messages over the expensive threshold with no error or slow time, baseline day 1:",
      fmt_int(sum(t.cost > expensive and not t.error and t.duration_ns <= SLOW_NS for t in base)))
# Retention: bytes per message without content, in the JSON-lines export (capture is off until chapter 12).
per_message, kept_bytes, day_bytes = retained_bytes(base, messages, kept)
print("bytes per message without content, baseline day 1:", fmt_int(per_message))
print("bytes kept under the budget, of the incident day's bytes:", fmt_share(kept_bytes, day_bytes))
assert all(t.seq in kept for t in messages if t.error)  # the budget leaves every error in
assert kept_spans <= BUDGET
assert sum(len(t.rows) for t in traces if t.seq in no_budget) > BUDGET
