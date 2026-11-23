"""Send one message's three spans to MLflow 3.18.0 on SQLite over OTLP/HTTP, and read them back with search_traces. MLflow
returns span IDs base64-encoded, so the example decodes them before comparing. The code reads the trace's total token
usage from its metadata, and MLflow stores no cost, because it has no price for the model the chat span names."""
import tempfile

from lib.assistant import AGENT, RELEASES
from lib.clock import VirtualClock
from lib.export import spans_to_rows
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.mlflow_server import otlp_exporter, running, stored_spans, trace_usage
from lib.otlp import message_spans
from lib.tracing import make_provider

import mlflow
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-07", RELEASES["r0"]
memory = InMemorySpanExporter()
clock = VirtualClock(DAY)
with tempfile.TemporaryDirectory() as folder, running(folder, "ambrewick-sample") as (uri, experiment):
    provider = make_provider(AGENT, RELEASE.service_version, "mlflow-search-traces", clock, SequentialIds(), memory,
                             SCHEMA_URL)
    provider.add_span_processor(SimpleSpanProcessor(otlp_exporter(uri, experiment)))
    message_spans(provider.get_tracer("ambrewick.assistant"), clock)
    found = mlflow.search_traces(locations=[experiment])

spans, usage = stored_spans(found), trace_usage(found)
root = next(span for span in spans if span["parent"] is None)
chat = next(span for span in spans if span["name"].startswith("chat "))
# the trace ID is "tr-" followed by the 32 hex digits of the OpenTelemetry trace ID, 35 characters in all
assert len(found) == 1 and len(found.iloc[0]["trace_id"]) == 35 and found.iloc[0]["trace_id"].startswith("tr-")
assert {span["span"] for span in spans} == {row["span_id"] for row in spans_to_rows(memory)}  # decoded IDs match
assert all(span["parent"] in (None, root["span"]) for span in spans)  # the chat and tool spans sit under the root
assert chat["attributes"]["mlflow.spanType"] == "CHAT_MODEL"  # MLflow's own label, added on the chat span
assert usage["total"] == usage["input"] + usage["output"]  # cache reads are not added again
# MLflow prices a span only when it knows the span's model, and this book's model is not in its table
assert "mlflow.llm.cost" not in chat["attributes"] and "mlflow.trace.cost" not in found.iloc[0]["trace_metadata"]

print("traces found for the experiment:", len(found))
print("spans in the trace:", len(spans))
print("span IDs, decoded from base64, equal the exporter's IDs: yes (asserted)")
print("chat span, MLflow span type:", chat["attributes"]["mlflow.spanType"])
print("chat span, model MLflow recorded:", chat["attributes"]["mlflow.llm.model"])
print("trace token usage, input:", usage["input"])
print("trace token usage, output:", usage["output"])
print("trace token usage, cache read:", usage["cache_read"])
print("trace token usage, total = input + output: yes (asserted)")
print("cost MLflow stored for this model, on the chat span and in the trace: none (asserted)")
