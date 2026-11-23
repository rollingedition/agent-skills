"""Write a traceparent into one call to the contacts server, then ask for a tool the server does not have. The prose's claim
that the SDK replaces the header rests on the second printed line, and its claim about the unknown tool on the third."""
from lib.clock import VirtualClock
from lib.contacts_server import SPANS_ENV
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.tracing import make_provider
import asyncio, json, sys, tempfile
from pathlib import Path
from mcp import Client, StdioServerParameters
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

HAND_WRITTEN = "00-" + "ab" * 16 + "-" + "cd" * 8 + "-01"  # a traceparent this app never made
CALLS = [("find_contact", {"user_id": "U0161", "name": "jake"}, {"traceparent": HAND_WRITTEN}), ("no_such_tool", {}, None)]
clock, exporter = VirtualClock("2026-12-08"), InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", "1.0.0", "propagate-example", clock, SequentialIds(), exporter, SCHEMA_URL)
trace.set_tracer_provider(provider)  # the SDK injects its header only when a provider is configured


async def make_calls(params):
    """Make each call inside its own tool span, which is current while the call waits for its reply."""
    replies = []
    async with Client(params) as client:
        for number, (name, arguments, meta) in enumerate(CALLS):
            app = provider.get_tracer("ambrewick.assistant").start_span(f"execute_tool {name}", start_time=clock.at(number))
            with trace.use_span(app, end_on_exit=False):  # ended below, with a virtual end time
                replies.append((app, await client.call_tool(name, arguments, meta=meta)))
            app.end(end_time=clock.at(number + 1))
    return replies


with tempfile.TemporaryDirectory() as folder:
    spans_file = Path(folder) / "spans.jsonl"  # the server's spans; read once the server has exited
    params = StdioServerParameters(command=sys.executable, args=["-m", "lib.contacts_server"],
                                   cwd=str(Path(__file__).resolve().parent), env={SPANS_ENV: str(spans_file)})
    replies = asyncio.run(make_calls(params))
    server = [json.loads(line) for line in spans_file.read_text(encoding="utf-8").splitlines()]

(app, _), (_, unknown) = replies
client = next(s for s in exporter.get_finished_spans()  # the SDK's client span, child of the tool span
              if s.name.startswith("MCP send tools/call") and s.parent and s.parent.span_id == app.context.span_id)
span = next(r for r in server if r["parent_span_id"] == format(client.context.span_id, "016x"))
assert span["trace_id"] == format(app.context.trace_id, "032x") != "ab" * 16  # joined the app's trace, not the header's
assert unknown.is_error and unknown.content[0].text == "Unknown tool: no_such_tool"
print("find_contact, hand-written traceparent: server span joins the app's trace: yes")
print("find_contact, hand-written traceparent kept: no")
print("no_such_tool, reply is an error result: yes")
