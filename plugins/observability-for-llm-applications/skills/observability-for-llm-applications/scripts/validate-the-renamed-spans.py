"""Run the validator over every span of the dev day's twenty messages: no finding on any span the registry defines, and
one on each of the book's own fallback spans, which the registry does not define.

The point rests on the line "findings on registry spans: 0", which is asserted, and on the fallback count, which
equals the fallback replies."""
from lib.assistant import Assistant
from lib.bm25 import Retriever
from lib.case import load_articles, load_messages, load_tool_durations
from lib.clock import VirtualClock
from lib.dayrun import DAY, RECORDING, RELEASE
from lib.export import spans_to_rows
from lib.genai import REGISTRY_VERSION, SCHEMA_URL, validate
from lib.ids import SequentialIds
from lib.replay import Replay, ReplayContacts
from lib.report import fmt_int
from lib.tools import Tools
from lib.tracing import make_provider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from collections import Counter

replay = Replay(RECORDING)
retriever, tools = Retriever(load_articles(), RELEASE.top_k), Tools(load_tool_durations(), ReplayContacts(replay))
messages, fallback_replies, rows = load_messages(DAY), 0, []
for message in messages:  # arrival order, as the replay needs; each message gets its own clock, exporter and trace
    clock = VirtualClock(DAY, start_ns=message.arrival_ns)
    exporter = InMemorySpanExporter()  # one per message, so each message's IDs start from 1
    tracer = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", clock, SequentialIds(),
                           exporter, SCHEMA_URL).get_tracer("ambrewick.assistant", schema_url=SCHEMA_URL)
    fallback_replies += Assistant(replay, retriever, tools, clock, tracer, RELEASE).handle(message).source == "fallback"
    rows += spans_to_rows(exporter)

book = [row for row in rows if row["name"] == "ambrewick.fallback"]
# The book's own fallback span is not a registry span, so it is checked apart from the others.
registry_findings = [finding for row in rows if row["name"] != "ambrewick.fallback" for finding in validate(row)]
book_findings = [finding for row in book for finding in validate(row)]
# A span with no gen_ai.operation.name is counted under its own name, which is how the fallback span appears.
operations = Counter(row["attributes"].get("gen_ai.operation.name", row["name"]) for row in rows)
print("GenAI conventions version:", REGISTRY_VERSION)
print("messages:", fmt_int(len(messages)))
print("spans checked:", fmt_int(len(rows)))
for operation in sorted(operations):
    print(f"spans, {operation}:", fmt_int(operations[operation]))
print("findings on registry spans:", fmt_int(len(registry_findings)))
print("fallback replies:", fmt_int(fallback_replies))
print("findings on the book's fallback span:", fmt_int(len(book_findings)))
assert not registry_findings  # zero findings on every span the registry defines
assert len(book_findings) == len(book) == fallback_replies  # one per fallback span, and each span is a fallback reply
assert all("no known span type" in finding for finding in book_findings)
