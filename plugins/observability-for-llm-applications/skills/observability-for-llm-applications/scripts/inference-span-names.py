"""Print the span name each step gets from the assistant, beside the registry's pattern for that span type. The names are
the spans', the patterns are the registry's, and each assert checks one span's name against its pattern.

The point rests on the four name lines: the inference, tool and agent names from message 11159 (a route, an answer, a
tool call and a second answer), and the retrieval name from message 809."""
from lib.assistant import Assistant
from lib.bm25 import Retriever
from lib.case import load_articles, load_messages, load_tool_durations
from lib.clock import VirtualClock
from lib.dayrun import DAY, RECORDING, RELEASE
from lib.export import spans_to_rows
from lib.genai import REGISTRY_VERSION, SCHEMA_URL, SPAN_OPERATIONS, SPAN_TYPES
from lib.ids import SequentialIds
from lib.replay import Replay, ReplayContacts
from lib.tools import Tools
from lib.tracing import make_provider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

replay = Replay(RECORDING)
retriever, tools = Retriever(load_articles(), RELEASE.top_k), Tools(load_tool_durations(), ReplayContacts(replay))
rows = {}
for message in (m for m in load_messages(DAY) if m.message_id in ("809", "11159")):
    clock, exporter = VirtualClock(DAY, start_ns=message.arrival_ns), InMemorySpanExporter()  # one exporter per message
    tracer = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", clock, SequentialIds(),
                           exporter, SCHEMA_URL).get_tracer("ambrewick.assistant", schema_url=SCHEMA_URL)
    Assistant(replay, retriever, tools, clock, tracer, RELEASE).handle(message)
    rows[message.message_id] = spans_to_rows(exporter)
agent = next(row for row in rows["11159"] if row["parent_span_id"] is None)  # the root is the agent's invocation
inference = next(row for row in rows["11159"] if row["attributes"].get("gen_ai.operation.name") == "chat")
tool = next(row for row in rows["11159"] if row["attributes"].get("gen_ai.operation.name") == "execute_tool")
retrieval = next(row for row in rows["809"] if row["attributes"].get("gen_ai.operation.name") == "retrieval")
print("GenAI conventions version:", REGISTRY_VERSION)
print("inference span name:", inference["name"])
print("retrieval span name:", retrieval["name"])
print("tool span name:", tool["name"])
print("agent span name:", agent["name"])
print("inference provider name:", inference["attributes"]["gen_ai.provider.name"])
print("inference prompt name:", inference["attributes"]["gen_ai.prompt.name"])
print("inference prompt version:", inference["attributes"]["gen_ai.prompt.version"])
# Model spans are `{operation} {model}`, retrieval is its operation alone, tools are `execute_tool {tool}`, the agent is
# `invoke_agent {agent}`. Each assert checks one span against its pattern.
assert inference["name"] == f"chat {RELEASE.model}" and retrieval["name"] == "retrieval"
assert tool["name"] == f"execute_tool {tool['attributes']['gen_ai.tool.name']}"
assert agent["name"] == f"invoke_agent {agent['attributes']['gen_ai.agent.name']}"
for span_type in sorted(SPAN_OPERATIONS):  # the operation names the registry defines, per span type
    print(f"operation names, {span_type}:", ", ".join(SPAN_OPERATIONS[span_type]))
for span_type in sorted(SPAN_TYPES):  # the attributes the validator requires, per span type
    print(f"required attributes, {span_type}:", len(SPAN_TYPES[span_type]["required"]))
