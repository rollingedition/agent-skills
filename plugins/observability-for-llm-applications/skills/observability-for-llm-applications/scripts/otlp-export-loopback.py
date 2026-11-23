"""Export one dev-day message's three spans over OTLP/HTTP to the book's receiver on loopback, and check that a span's
request is in the receiver when its span.end() returns. The stored rows equal the in-memory exporter's rows, so the
protobuf round trip loses nothing the book's rows keep; the request count is printed and the yes lines are asserted."""
from lib.assistant import AGENT, RELEASES
from lib.clock import VirtualClock
from lib.export import spans_to_rows
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.otlp import message_spans, start
from lib.tracing import make_provider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-07", RELEASES["r0"]
receiver = start()                       # the book's receiver on loopback; the port is never printed
memory = InMemorySpanExporter()          # the same spans, kept in memory, to compare with what arrives
clock = VirtualClock(DAY)
provider = make_provider(AGENT, RELEASE.service_version, "otlp-export-loopback", clock, SequentialIds(), memory, SCHEMA_URL)
# SimpleSpanProcessor calls the exporter when each span ends, so the request is sent on the ending thread (O-7)
provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=receiver.endpoint)))
root, chat, tool = message_spans(provider.get_tracer("ambrewick.assistant"), clock)

assert receiver.address == "127.0.0.1"   # bound to loopback only, never to a network address
assert len(receiver.requests()) == 3     # one request per span the processor exported
assert sum(count == 1 for _, count in receiver.requests()) == 3  # each request holds one span
assert receiver.rows() == spans_to_rows(memory)  # the stored rows equal the exporter's own rows

# A span from a provider with only the OTLP exporter: its request must be in the receiver when end() returns.
probe = TracerProvider(resource=Resource.create({"service.name": AGENT, "service.instance.id": "probe"}))
probe.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=receiver.endpoint)))
before = len(receiver.requests())
# 36001 s is an offset on the virtual clock, past the message's spans, so the probe's times do not overlap them
probe.get_tracer("probe").start_span("probe", start_time=clock.at(36001)).end(end_time=clock.at("36001.1"))
assert len(receiver.requests()) == before + 1

print("bound to loopback: yes (asserted)")
print("requests for the message's three spans:", before)
print("spans per request: one in each, for every request (asserted)")
print("content types of the requests:", ", ".join(sorted({kind for kind, _ in receiver.requests()})))
print("stored rows equal the exporter's rows: yes (asserted)")
print("a request is in the receiver when span.end() returns: yes (asserted)")
receiver.stop()
