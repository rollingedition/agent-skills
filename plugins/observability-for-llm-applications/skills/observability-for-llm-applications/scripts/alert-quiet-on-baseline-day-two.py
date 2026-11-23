"""The same alert on baseline day 2, a normal day with no injected incident (chapter 9, `an-alert-that-stays-quiet`).

It is the alert's quiet day: the page must not fire at any tick, for either objective. The page is quiet here because no
message fails, not because of the hour's minimum. The day has 80 messages, so most hours hold fewer than the minimum,
and the printed count of the ticks that hold the minimum shows how little of the day the error page could read."""
from lib.dayrun import run_day_traced
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, THRESHOLD, MIN_REQUESTS = "2026-12-10", 14.4, 10
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
run_day_traced(DAY, live=False, meter_provider=meter.provider, after_message=meter.after)  # no fault on this day
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
slow = alert_verdicts(tallies, slo=0.95, measure="slow", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
total = tallies[-1][1]

print("messages, baseline day 2:", fmt_int(total.requests))
print("messages with no reply:", fmt_int(total.failed))
print("messages over 20 s:", fmt_int(total.slow))
print("ticks where the hour holds the minimum:", fmt_int(sum(v.long.requests >= MIN_REQUESTS for v in errors)),
      "of", fmt_int(len(errors)))                     # the only ticks a full hour can page on this day
print("highest error burn over an hour:", fmt_burn(max(v.long.burn for v in errors)))
print("highest error burn over 5 minutes:", fmt_burn(max(v.short.burn for v in errors)))
print("highest latency burn over an hour, with the minimum met:",
      fmt_burn(max(v.long.burn for v in slow if v.long.requests >= MIN_REQUESTS)))
print("ticks where the error page fires:", fmt_int(sum(v.page for v in errors)))
print("ticks where the latency page fires:", fmt_int(sum(v.page for v in slow)))

assert total.failed == 0                               # no message on this day ended without a reply
assert not any(v.page for v in errors)                 # the error page stays quiet at every tick
assert not any(v.page for v in slow)                   # and so does the latency page
