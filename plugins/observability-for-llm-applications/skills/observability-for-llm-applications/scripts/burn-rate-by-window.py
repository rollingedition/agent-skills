"""The burn in each window on the incident day (chapter 9, `burn-rate`).

A burn rate is how fast a window spends the error budget. The windows are on virtual time: one hour (the long window)
and five minutes (the short one), each read as the difference between two cumulative reads of the metric at 5-minute
ticks. The live contacts server injects the three incident windows (lib.inject). The counts in each window are checked
against the spans' own counts, so the metric and the spans agree on what happened."""
from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.inject import load_incidents
from lib.metrics import DayMeter, alert_verdicts, tallies_by_tick
from lib.report import fmt_burn, fmt_int

DAY, STEP_NS, HOUR_NS = "2026-12-09", 300 * 1_000_000_000, 3600 * 1_000_000_000
MIN_REQUESTS = 10                                     # a burn counts only over an hour with this many messages (alert)
meter = DayMeter(DAY)                                 # the assistant's live meter, read after each message
traced = run_day_traced(DAY, meter_provider=meter.provider, after_message=meter.after)  # live: faults on virtual time
midnight = VirtualClock(DAY).now_ns
tallies = tallies_by_tick(meter.marks, DAY)
errors = alert_verdicts(tallies, slo=0.99, measure="failed")   # objective 99%: budget 1%
slow = alert_verdicts(tallies, slo=0.95, measure="slow")       # objective 95% within 20 s: budget 5%
messages = [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == "invoke_agent"]


def clock(ns: int) -> str:
    """A virtual time as hours, minutes and seconds UTC, from the day's midnight."""
    offset = (ns - midnight) // 1_000_000_000
    return f"{offset // 3600:02d}:{offset % 3600 // 60:02d}:{offset % 60:02d}"


for incident in load_incidents():
    first = -(-(incident.end_ns - midnight) // STEP_NS)     # the first tick at or after the window's end, 1-based
    error, latency = errors[first - 1], slow[first - 1]
    near = [v for v in errors if incident.start_ns < v.tick_ns <= incident.end_ns + STEP_NS]
    counted = {v.tick_ns for v in near if v.long.requests >= MIN_REQUESTS}   # the hours a page could read
    print(f"{incident.incident_id}, window:", f"{clock(incident.start_ns)} to {clock(incident.end_ns)} UTC")
    print(f"{incident.incident_id}, first tick after the window:", clock(error.tick_ns))
    print(f"{incident.incident_id}, messages in the hour to that tick:", fmt_int(error.long.requests))
    print(f"{incident.incident_id}, messages with no reply in that hour:", fmt_int(error.long.bad))
    print(f"{incident.incident_id}, error burn, 1 hour:", fmt_burn(error.long.burn))
    print(f"{incident.incident_id}, error burn, 1 hour, highest from the window to 5 minutes after it:",
          fmt_burn(max(v.long.burn for v in errors if v.tick_ns in counted)))
    print(f"{incident.incident_id}, error burn, 5 minutes, highest from the window to 5 minutes after it:",
          fmt_burn(max(v.short.burn for v in errors if v.tick_ns in counted)))
    print(f"{incident.incident_id}, messages over 20 s in that hour:", fmt_int(latency.long.bad))
    print(f"{incident.incident_id}, latency burn, 1 hour, highest from the window to 5 minutes after it:",
          fmt_burn(max(v.long.burn for v in slow if v.tick_ns in counted)))
    in_hour = [row for row in messages if error.tick_ns - HOUR_NS < row["end_ns"] <= error.tick_ns]
    assert len(in_hour) == error.long.requests                                              # the metric's count
    assert sum("error.type" in row["attributes"] for row in in_hour) == error.long.bad      # the spans' failures
