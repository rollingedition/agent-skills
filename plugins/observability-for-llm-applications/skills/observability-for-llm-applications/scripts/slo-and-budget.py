"""The assistant's two objectives, and the error budget each one leaves (chapter 9, `service-level-objectives`).

The error objective: 99% of messages get a reply. A message that ended with no reply has `error.type` on its duration
point, and it spends the budget. The latency objective: 95% of messages finish within 20 seconds, the book's edge
(chapter 7). The edge sits above baseline day 1's p95, so a normal day meets it. Both are read from the metrics that the
alert reads, on the same day. The 30-day period is the arithmetic's period, not a traffic forecast."""
from decimal import Decimal

from lib.dayrun import run_day_traced
from lib.metrics import DayMeter, burn_rate, tallies_by_tick
from lib.report import fmt_burn, fmt_int, fmt_ms, fmt_share
from lib.stats import nearest_rank

DAY = "2026-12-08"
ERROR_SLO, LATENCY_SLO, PERIOD_HOURS = 0.99, 0.95, 30 * 24
meter = DayMeter(DAY)                                  # the assistant's live meter, read after each message
traced = run_day_traced(DAY, live=False, meter_provider=meter.provider, after_message=meter.after)
day = tallies_by_tick(meter.marks, DAY)[-1][1]         # the last tick's cumulative tally is the whole day
durations = sorted(row["end_ns"] - row["start_ns"] for row in traced.spans
                   if row["attributes"].get("gen_ai.operation.name") == "invoke_agent")
p95 = nearest_rank(durations, 95)

print("error objective, share of messages with a reply:", fmt_share(round(ERROR_SLO * 100), 100))
print("error budget, share of messages that may fail:", fmt_share(round((1 - ERROR_SLO) * 100), 100))
print("latency objective, share of messages within 20 s:", fmt_share(round(LATENCY_SLO * 100), 100))
print("latency budget, share of messages that may run over 20 s:", fmt_share(round((1 - LATENCY_SLO) * 100), 100))
print("messages, baseline day 1:", fmt_int(day.requests))
print("messages with no reply:", fmt_int(day.failed), "of", fmt_int(day.requests))
print("messages within 20 s:", fmt_int(day.within), "of", fmt_int(day.requests), "share", fmt_share(day.within, day.requests))
print("messages over 20 s:", fmt_int(day.slow), "of", fmt_int(day.requests))
print("error budget spent over the day, burn:", fmt_burn(burn_rate(day.failed, day.requests, ERROR_SLO)))
print("latency budget spent over the day, burn:", fmt_burn(burn_rate(day.slow, day.requests, LATENCY_SLO)))
print("p95 of message times, nearest rank, n:", fmt_int(len(durations)), "messages")
print("p95 of message times:", fmt_ms(p95))
print("share of the 30-day budget a 1-hour page at burn 14.4 spends:", fmt_share(Decimal("14.4") * 1, PERIOD_HOURS))

assert day.failed == 0                               # a normal day has no message without a reply
assert day.within / day.requests >= LATENCY_SLO      # and meets the latency objective
assert p95 <= 20 * 1_000_000_000                     # the edge sits above the day's p95 (chapter 7, P-24)
