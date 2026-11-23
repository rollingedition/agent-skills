"""How often the router chose a route other than the scenario table's, on baseline day 1 (the 4B), the same messages under
the 0.6B (the model swap, from its recorded route replies) and the dev day. Each message's check event on its route span
holds the table's answer; the 0.6B's replies are read with the same parser. The interval is a bootstrap over messages."""
import json
from fractions import Fraction

from lib.assistant import parse_route
from lib.case import load_messages, scenario_to_route
from lib.dayrun import DATA, run_day, run_day_traced
from lib.report import fmt_int, fmt_share
from lib.stats import bootstrap_interval


def recorded_routes(recording, day):
    """(expected, chosen) for each route reply in one recording, in order. A reply that names no route is the fallback."""
    messages = {message.message_id: message for message in load_messages(day)}
    paths = sorted((DATA / recording / "calls").glob("*.json"))
    calls = sorted((json.loads(path.read_text(encoding="utf-8")) for path in paths), key=lambda call: call["seq"])
    return [(scenario_to_route(messages[c["message_id"]].scenario), parse_route(c["text"]) or "fallback")
            for c in calls if c["kind"] == "model" and c["step"] == "route"]


traced = run_day_traced("2026-12-08", live=False)
runs = traced.runs
# The check event is on each route span: the trace itself says whether the route was correct.
checks = [event["attributes"] for row in traced.spans for event in row["events"] if event["name"] == "ambrewick.check"]
wrong = [run.outcome.route != run.outcome.expected_route for run in runs]
assert len(checks) == len(runs) and sum(not check["ambrewick.route.correct"] for check in checks) == sum(wrong)
print(f"baseline day 1 (4B), messages: {fmt_int(len(runs))}")
RESAMPLES = 2000
low, high = bootstrap_interval(wrong, lambda units: Fraction(sum(units), len(units)), n=RESAMPLES)
print(f"bootstrap resamples of messages, baseline day 1: {fmt_int(RESAMPLES)}")
print(f"wrong routes, baseline day 1, 95% interval: {fmt_share(low.numerator, low.denominator)} to {fmt_share(high.numerator, high.denominator)}")
for route in sorted({run.outcome.expected_route for run in runs}):
    print(f"{route}, wrong routes of {fmt_int(sum(run.outcome.expected_route == route for run in runs))} messages: "
          f"{fmt_int(sum(run.outcome.route != route for run in runs if run.outcome.expected_route == route))}")
print("fallback replies to a scenario that is not fallback, baseline day 1: "
      f"{fmt_int(sum(run.outcome.route == 'fallback' and run.outcome.expected_route != 'fallback' for run in runs))}")

# The same messages under the 0.6B, from its recorded replies; the 4B's recorded replies must give the replay's count.
base = recorded_routes("baseline-day-1", "2026-12-08")
assert sum(expected != chosen for expected, chosen in base) == sum(wrong)
swap = recorded_routes("release-model-swap", "2026-12-08")
print(f"wrong routes, model swap (0.6B, release r2): {fmt_int(sum(e != c for e, c in swap))} of {fmt_int(len(swap))} messages")
print("fallback replies to a scenario that is not fallback, model swap: "
      f"{fmt_int(sum(c == 'fallback' and e != 'fallback' for e, c in swap))}")

# The dev day's 20 messages, for chapter 1's fallback replies, checked against the same table.
dev = run_day("2026-12-07")
print(f"dev day, messages: {fmt_int(len(dev))}")
print(f"wrong routes, dev day (20 messages): {fmt_int(sum(run.outcome.route != run.outcome.expected_route for run in dev))}")
print(f"fallback replies to a scenario that is not fallback, dev day: {fmt_int(sum(run.outcome.route == 'fallback' and run.outcome.expected_route != 'fallback' for run in dev))}")
