"""One chat call through the openai client, instrumented by the official package and answered from the recording. The
point rests on three printed facts: the call makes one client span, named for its operation and model; that span is a
child of the message's span; and it holds the usage the reply reported. The metrics are named and counted here, never
valued, since their durations use real time."""
from lib.http_replay import client, route_body    # lib first: threads and seeds are fixed before anything else

import opentelemetry.sdk.trace as sdk_trace
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.assistant import RELEASES
from lib.case import load_messages
from lib.clock import VirtualClock
from lib.ids import SequentialIds
from lib.names_map import name_map
from lib.report import fmt_int
from lib.tracing import make_provider

clock = VirtualClock("2026-12-07")
# The SDK reads span times from its trace module's time_ns, so patching that name gives every span, the package's included,
# virtual times.
sdk_trace.time_ns = lambda: clock.advance(1_000_000)
exporter, reader = InMemorySpanExporter(), InMemoryMetricReader()
provider = make_provider("ambrewick-assistant", RELEASES["r0"].service_version, "example", clock, SequentialIds(),
                         exporter, "https://opentelemetry.io/schemas/1.45.0")
OpenAIInstrumentor().instrument(tracer_provider=provider, meter_provider=MeterProvider(metric_readers=[reader]))

with provider.get_tracer("ambrewick-assistant").start_as_current_span("invoke_agent ambrewick-assistant"):
    reply = client().chat.completions.create(**route_body(load_messages("2026-12-07")[0]))

call, root = exporter.get_finished_spans()                  # the call ends before the message's span does
metrics = reader.get_metrics_data().resource_metrics[0].scope_metrics[0].metrics
print("spans in the trace:", len(exporter.get_finished_spans()))
print("instrumented span, name:", call.name)
print("instrumented span, kind:", call.kind.name)
print("instrumented span, scope schema URL:", call.instrumentation_scope.schema_url)
print("attributes on the span:", ", ".join(sorted(call.attributes)))
print("gen_ai.provider.name on the span:", call.attributes["gen_ai.provider.name"])
print("server.address on the span:", call.attributes["server.address"])
print("server.port on the span:", call.attributes["server.port"])
print("input count on the span:", fmt_int(call.attributes["gen_ai.usage.input_tokens"]))
print("output count on the span:", fmt_int(call.attributes["gen_ai.usage.output_tokens"]))
for metric in metrics: print(f"metric {metric.name}, unit {metric.unit.strip('{}')}, data points: {len(metric.data.data_points)}")
types = {p.attributes["gen_ai.token.type"] for m in metrics if m.name == "gen_ai.client.token.usage" for p in m.data.data_points}
print("token types on the usage metric:", ", ".join(sorted(types)))
# The call is a child of the message's span, and its usage is the reply's. Every name it makes is in the table.
assert call.parent.span_id == root.context.span_id
assert (call.attributes["gen_ai.usage.input_tokens"], call.attributes["gen_ai.usage.output_tokens"]) == (
    reply.usage.prompt_tokens, reply.usage.completion_tokens)
assert {m.name for m in metrics} | set(call.attributes) | {"gen_ai.token.type"} <= set(name_map())
