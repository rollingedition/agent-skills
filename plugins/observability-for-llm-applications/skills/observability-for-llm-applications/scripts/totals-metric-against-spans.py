"""Summing usage over every span counts each input token twice, because the agent span carries its message's usage as well as
its model calls do (the registry's aggregation note). The assistant's live meter counts each call once, as the call ends,
and matches the inference spans. The two asserts are the facts the prose relies on."""
from lib.dayrun import RELEASE, run_day_traced
from lib.metrics import PER_OPERATION, USAGE, make_meter_provider, totals
from lib.names_map import NAMES, REGISTRY_VERSION
from lib.report import fmt_int
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

DAY = "2026-12-08"
INPUT = "gen_ai.usage.input_tokens"
reader = InMemoryMetricReader()
provider = make_meter_provider(reader, service_instance_id=f"{DAY}-metrics", service_version=RELEASE.service_version)
traced = run_day_traced(DAY, live=False, meter_provider=provider)   # the assistant records each call's tokens as it ends
attributes = [s["attributes"] for s in traced.spans]
inference = [a for a in attributes if a.get("gen_ai.operation.name") == "chat"]
agents = [a for a in attributes if a.get("gen_ai.operation.name") == "invoke_agent"]   # one per message


def summed(rows, key):
    """The sum of one usage attribute over span attributes; a span without it adds zero."""
    return sum(row.get(key, 0) for row in rows)


got = totals(reader)
spans_input = summed(inference, INPUT)
every_span_input = summed(attributes, INPUT)
counter_input = int(got[USAGE["input"]]["sum"])
print("messages:", fmt_int(len(traced.runs)))
print("inference spans, one per model call:", fmt_int(len(inference)))
print("agent spans, invoke_agent, one per message:", fmt_int(len(agents)))
print("input tokens, summed over the inference spans:", fmt_int(spans_input))
print("input tokens, summed over every span:", fmt_int(every_span_input))
print("input tokens, token counter total:", fmt_int(counter_input))
print("input tokens, per-operation histogram sum:", fmt_int(int(got[PER_OPERATION["input"]]["sum"])))
print("per-operation histogram, count of operations:", fmt_int(got[PER_OPERATION["input"]]["count"]))
print("output tokens, token counter total:", fmt_int(int(got[USAGE["output"]]["sum"])))
print("GenAI conventions version:", REGISTRY_VERSION)
print("package token histogram, gen_ai.client.token.usage, v0.1.0 names:", ", ".join(NAMES["gen_ai.client.token.usage"]))
assert every_span_input == 2 * spans_input      # the agent spans repeat every inference token once more
assert counter_input == spans_input             # the counter reads each call's usage once, as the call ends
