"""Send one message's spans, from one provider, to two receivers: the book's receiver and MLflow. Both hold the same span
IDs and the same attributes, and MLflow adds its own attributes under mlflow.*; the book's receiver adds none."""
import tempfile

from lib.assistant import AGENT, RELEASES
from lib.clock import VirtualClock
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.mlflow_server import otlp_exporter, running, stored_spans
from lib.otlp import message_spans, start
from lib.tracing import make_provider

import mlflow
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-07", RELEASES["r0"]
receiver = start()                   # the book's receiver on loopback
clock = VirtualClock(DAY)
with tempfile.TemporaryDirectory() as folder, running(folder, "ambrewick-two-backends") as (uri, experiment):
    provider = make_provider(AGENT, RELEASE.service_version, "same-spans-two-receivers", clock, SequentialIds(),
                             InMemorySpanExporter(), SCHEMA_URL)
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=receiver.endpoint)))
    provider.add_span_processor(SimpleSpanProcessor(otlp_exporter(uri, experiment)))
    message_spans(provider.get_tracer("ambrewick.assistant"), clock)
    found = mlflow.search_traces(locations=[experiment])

book = {row["span_id"]: row for row in receiver.rows()}
other = {span["span"]: span for span in stored_spans(found)}
receiver.stop()
assert len(book) == len(other) == 3 and set(book) == set(other)  # the same spans in both
added = set()
for span_id, row in book.items():
    kept = {key: value for key, value in other[span_id]["attributes"].items() if not key.startswith("mlflow.")}
    assert kept == row["attributes"]  # every attribute the book stored is still there, unchanged
    assert not any(key.startswith("mlflow.") for key in row["attributes"])  # the book's rows hold no mlflow.* keys
    added |= set(other[span_id]["attributes"]) - set(row["attributes"])

print("spans received by the book's receiver:", len(book))
print("spans received by MLflow:", len(other))
print("the same span IDs in both: yes (asserted)")
print("the book's attributes equal in both, on every span: yes (asserted)")
print("attributes MLflow adds, by name:", ", ".join(sorted(added)))
print("mlflow.* attributes in the book's rows: none (asserted)")
