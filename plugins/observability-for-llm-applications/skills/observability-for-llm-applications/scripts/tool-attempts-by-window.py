"""The tool attempts in each incident window, read from the assistant's meter (chapter 9, `burn-rate-by-window`).

The meter records gen_ai.execute_tool.duration once for each tool attempt. The example reads that histogram after each
message, so a message's attempts count at its reply, as the alert's ticks do. For each incident window it prints the
attempts in the hour up to the first tick after the window, and how many carry error.type. The day's totals are checked
against the spans, so the meter and the spans agree on every attempt."""
from functools import reduce

from lib.clock import VirtualClock
from lib.dayrun import run_day_traced
from lib.inject import load_incidents
from lib.metrics import DURATION, DayMeter, Tally, tally
from lib.report import fmt_int

DAY, STEP_NS, HOUR_NS = "2026-12-09", 300 * 1_000_000_000, 3600 * 1_000_000_000
meter, tools, last = DayMeter(DAY), [], [Tally(0, 0, 0)]   # the live meter; attempts by reply time; the last read


def after_message(run) -> None:
    """Read the tool histogram after one message: the attempts it added, keyed by its reply time."""
    now = tally(meter.reader, DURATION["execute_tool"], 20)
    tools.append((run.replied_ns, now - last[0]))
    last[0] = now


traced = run_day_traced(DAY, meter_provider=meter.provider, after_message=after_message)  # live: faults on virtual time
midnight = VirtualClock(DAY).now_ns
calls = [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == "execute_tool"]


def tools_in_hour(tick_ns: int) -> Tally:
    """The tool attempts of the messages that replied in the hour up to a tick."""
    return reduce(Tally.__add__, [added for replied, added in tools if tick_ns - HOUR_NS < replied <= tick_ns],
                  Tally(0, 0, 0))


for incident in load_incidents():
    tick = midnight + -(-(incident.end_ns - midnight) // STEP_NS) * STEP_NS    # the first tick after the window
    attempts = tools_in_hour(tick)
    print(f"{incident.incident_id}, tool attempts in the hour to that tick:", fmt_int(attempts.requests))
    print(f"{incident.incident_id}, tool attempts with error.type in that hour:", fmt_int(attempts.failed))

assert sum(added.requests for _, added in tools) == len(calls)                              # every attempt, as spans
assert sum(added.failed for _, added in tools) == sum("error.type" in row["attributes"] for row in calls)
