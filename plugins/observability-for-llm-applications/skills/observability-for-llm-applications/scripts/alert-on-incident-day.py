"""The two-window burn-rate alert, run on the incident day at each 5-minute tick (chapter 9, `an-alert-that-stays-quiet`).

The page fires when the error budget burns at 14.4 or faster over the hour and over the last five minutes, and the hour
holds at least 10 messages, so one failed message in a quiet hour cannot page. 14.4 spends 2% of a 30-day budget in an
hour (chapter 9, `slo-and-budget`). The short window is what lets the page clear once the burn stops. The alert reads the
metric only. It is run for the error objective and for the latency objective, which has the same windows."""
from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.inject import load_incidents
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, STEP_NS, THRESHOLD, MIN_REQUESTS = "2026-12-09", 300 * 1_000_000_000, 14.4, 10
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
run_day_traced(DAY, meter_provider=meter.provider, after_message=meter.after)  # live: the contacts server injects faults
midnight = VirtualClock(DAY).now_ns
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed", threshold=THRESHOLD, min_requests=MIN_REQUESTS)
slow = alert_verdicts(tallies, slo=0.95, measure="slow", threshold=THRESHOLD, min_requests=MIN_REQUESTS)


def clock(ns: int) -> str:
    """A virtual time as hours and minutes UTC, from the day's midnight."""
    offset = (ns - midnight) // 60_000_000_000
    return f"{offset // 60:02d}:{offset % 60:02d}"


pages = [v for v in errors if v.page]
cleared = next(v for v in errors if v.tick_ns > pages[0].tick_ns and not v.page)
print("page threshold, burn over 1 hour and over 5 minutes:", fmt_burn(THRESHOLD))
print("minimum messages in the hour:", fmt_int(MIN_REQUESTS))
print("ticks where the error page fires:", fmt_int(len(pages)), "of", fmt_int(len(errors)))
print("first tick the error page fires:", clock(pages[0].tick_ns))
print("messages in that hour, with no reply:", fmt_int(pages[0].long.bad), "of", fmt_int(pages[0].long.requests))
print("error burn at that tick, 1 hour and 5 minutes:", fmt_burn(pages[0].long.burn), fmt_burn(pages[0].short.burn))
print("first tick the error page is clear again:", clock(cleared.tick_ns))
print("ticks where the latency page fires:", fmt_int(sum(v.page for v in slow)))
print("highest latency burn over an hour, with the minimum met:",
      fmt_burn(max(v.long.burn for v in slow if v.long.requests >= MIN_REQUESTS)))

for incident in load_incidents():
    near = [v for v in errors if incident.start_ns < v.tick_ns <= incident.end_ns + STEP_NS]
    print(f"{incident.incident_id}, ticks in or just after the window:", fmt_int(len(near)))
    print(f"{incident.incident_id}, ticks where the error page fires:", fmt_int(sum(v.page for v in near)))

rate_limit = next(i for i in load_incidents() if i.kind == "rate-limit")
assert pages and all(rate_limit.start_ns < v.tick_ns <= rate_limit.end_ns + STEP_NS for v in pages)
assert sum(v.page for v in slow) == 0                  # the latency objective never pages on this day
for incident in load_incidents():
    if incident.kind != "rate-limit":
        assert not any(v.page for v in errors if incident.start_ns < v.tick_ns <= incident.end_ns + STEP_NS)
