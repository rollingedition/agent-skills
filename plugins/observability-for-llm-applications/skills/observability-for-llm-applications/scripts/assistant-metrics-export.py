"""The metrics the assistant exports, from its live meter (chapter 9, `metrics-the-assistant-exports`).

The assistant records each operation as it ends: a message is one `invoke_agent` operation, a model call one `chat`, a
tool attempt one `execute_tool`, and each model call's tokens go to the token counters and histograms. The names and
units come from the pinned registry (lib.genai.METRICS). The export must not lose what the spans count, so the sums
are checked against the spans' own sums."""
from lib.dayrun import run_day_traced
from lib.genai import METRICS
from lib.metrics import DURATION, USAGE, make_alert_meter_provider, totals
from lib.report import fmt_int
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

DAY = "2026-12-08"
reader = InMemoryMetricReader()
provider = make_alert_meter_provider(reader, service_instance_id=f"{DAY}-export")
traced = run_day_traced(DAY, live=False, meter_provider=provider)   # no faults on this day, so no live contacts server

reader.collect()
series = {}                                        # metric name: its number of series (one per attribute set)
for resource in reader.get_metrics_data().resource_metrics:
    for scope in resource.scope_metrics:
        for metric in scope.metrics:
            series[metric.name] = len(metric.data.data_points)
for name in sorted(series):
    print(f"series, {name}:", fmt_int(series[name]))
    print(f"unit, {name}:", METRICS[name]["unit"])

spans = lambda op: [row for row in traced.spans if row["attributes"].get("gen_ai.operation.name") == op]
messages, calls, attempts = spans("invoke_agent"), spans("chat"), spans("execute_tool")
print("messages, invoke_agent operations:", fmt_int(len(messages)))
print("model calls, chat operations:", fmt_int(len(calls)))
print("tool attempts, execute_tool operations:", fmt_int(len(attempts)))
sums = totals(reader)
print("input tokens, counter total:", fmt_int(int(sums[USAGE["input"]]["sum"])))
print("input tokens, summed over chat spans:", fmt_int(sum(c["attributes"]["gen_ai.usage.input_tokens"] for c in calls)))
print("message durations, histogram count:", fmt_int(sums[DURATION["invoke_agent"]]["count"]))

assert sums[DURATION["invoke_agent"]]["count"] == len(messages)     # one point per message, none lost
assert sums[DURATION["chat"]]["count"] == len(calls)                # one point per model call attempt
assert sums[DURATION["execute_tool"]]["count"] == len(attempts)     # one point per tool attempt
assert sums[USAGE["input"]]["sum"] == sum(c["attributes"]["gen_ai.usage.input_tokens"] for c in calls)
