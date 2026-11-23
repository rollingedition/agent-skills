"""Make one span on each of four workers started inside one tool span, and show which ones find its context: a plain pool
thread, the same thread with carry(), an asyncio task, and the loop's executor. The prose's counts of detached roots rest
on the asserts, which compare each span's parent with the tool span."""
from lib.clock import VirtualClock
from lib.context import carry, new_task
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.tracing import make_provider, span
from opentelemetry import trace
import asyncio
from concurrent.futures import ThreadPoolExecutor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

clock, exporter = VirtualClock("2026-12-08"), InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", "1.0.0", "orphan-example", clock, SequentialIds(), exporter, SCHEMA_URL)
tracer = provider.get_tracer("ambrewick.assistant")


def retrieve(name):
    """The worker's work: one span, made on whichever thread runs this. Its times are fixed, as every span's are."""
    span(tracer, f"retrieve {name}", clock.at(1), clock.at(2))  # no parent given: the span takes the current one


async def from_task():
    retrieve("task")  # runs in its own task, which asyncio gave a copy of the tool span's context


async def main():
    """Runs as a task inside the tool span, starts a second task, and hands one worker to the loop's executor."""
    await new_task(from_task())
    await asyncio.get_running_loop().run_in_executor(None, retrieve, "executor")  # copies no context


app = tracer.start_span("execute_tool retrieve", start_time=clock.at(0))
with trace.use_span(app, end_on_exit=False):  # current while the workers run, so their spans can find it
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(retrieve, "plain").result()  # the pool's thread starts with an empty context
        pool.submit(carry(retrieve), "carried").result()  # carry() runs the work in a copy of this context
    asyncio.run(main())
app.end(end_time=clock.at(3))

spans = {s.name: s for s in exporter.get_finished_spans()}
joined = {name: spans[name].parent is not None and spans[name].parent.span_id == app.context.span_id for name in spans}
assert joined == {"retrieve plain": False, "retrieve carried": True, "retrieve task": True, "retrieve executor": False,
                  "execute_tool retrieve": False}
assert all(spans[n].context.trace_id != app.context.trace_id for n in ["retrieve plain", "retrieve executor"])  # own traces
print("retrieve on a plain thread, joins the tool span: no")
print("retrieve on a thread with carry(), joins the tool span: yes")
print("retrieve in an asyncio task, joins the tool span: yes")
print("retrieve through run_in_executor, joins the tool span: no")
print("detached roots without the helper:", sum(not joined[n] for n in ["retrieve plain", "retrieve executor"]))
print("detached roots with the helper:", sum(not joined[n] for n in ["retrieve carried"]))
print("detached root's trace differs from the tool span's: yes")
