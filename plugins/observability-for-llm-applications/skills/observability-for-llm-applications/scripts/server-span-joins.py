"""Replay baseline day 1's message 16297 with the real contacts server over stdio, and check that the server's span joins
the assistant's trace under the SDK's client span. The prose's counts rest on the two count lines; the server's clock is
its own, so only counts are printed."""
from lib.assistant import RELEASES, Assistant
from lib.bm25 import Retriever
from lib.case import load_articles, load_messages, load_tool_durations
from lib.clock import VirtualClock
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.replay import Replay
from lib.tools import LiveContacts, Tools
from lib.tracing import make_provider
import json, tempfile
from pathlib import Path
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

DAY, RELEASE = "2026-12-08", RELEASES["r0"]  # baseline day 1, and the release its recording was made with
exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "baseline-day-1-replay", VirtualClock(DAY),
                         SequentialIds(), exporter, SCHEMA_URL)
trace.set_tracer_provider(provider)  # the SDK makes its client span with the global provider, so it must be this one

message = next(m for m in load_messages(DAY) if m.message_id == "16297")
clock = VirtualClock(DAY, start_ns=message.arrival_ns)  # the message's clock starts at its arrival
with tempfile.TemporaryDirectory() as folder:
    spans_file = Path(folder) / "contacts-spans.jsonl"  # the server writes here; it is read once the server has exited
    contacts = LiveContacts(clock, spans_file)
    outcome = Assistant(Replay(Path(__file__).resolve().parent / "data" / "recorded" / "baseline-day-1"), Retriever(load_articles(), RELEASE.top_k),
                        Tools(load_tool_durations(), contacts), clock, provider.get_tracer("ambrewick.assistant"), RELEASE).handle(message)
    contacts.close()
    server = [json.loads(line) for line in spans_file.read_text(encoding="utf-8").splitlines()]

mine = exporter.get_finished_spans()
app = next(s for s in mine if s.name == "execute_tool find_contact")
client = next(s for s in mine if s.name == "MCP send tools/call find_contact")
call = next(r for r in server if r["name"] == "tools/call find_contact")
lookup = next(r for r in server if r["name"] == "contacts.lookup")
trace_id = format(app.context.trace_id, "032x")
assert client.parent.span_id == app.context.span_id and call["trace_id"] == trace_id  # tool span, client span, same trace
assert call["parent_span_id"] == format(client.context.span_id, "016x")  # the server's span is under the client span
assert lookup["parent_span_id"] == call["span_id"] and lookup["trace_id"] == trace_id  # and its lookup under that

print("route chosen:", outcome.route)
print("spans in the message's trace, assistant:", sum(s.context.trace_id == app.context.trace_id for s in mine))
print("spans in the message's trace, contacts server:", sum(r["trace_id"] == trace_id for r in server))
print("contacts server span under the SDK's client span, in the same trace: yes")
