"""Build one dev-day message's trace by hand: a span per step, each with its explicit start and end times, from sequential
IDs, a synchronous processor and an in-memory exporter. The steps and their times come from the replay; the printed
lines rest on the span count and on every child span's parent."""
from lib.dayrun import RELEASE, run_dev_day
from lib.export import spans_to_rows
from lib.ids import SequentialIds
from lib.report import fmt_int
from lib.tracing import make_provider, span
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

(run,) = run_dev_day(["809"])
outcome = run.outcome

# The resource names the service; service.instance.id is set, not drawn at random. Spans export as they end.
exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", run.clock, SequentialIds(),
                         exporter, "https://opentelemetry.io/schemas/1.44.0")
tracer = provider.get_tracer("ambrewick.assistant")
# The root is the message. Its span is made first, and each step's span names it as parent.
root = span(tracer, "message", run.arrived_ns, run.replied_ns,
            attributes={"ambrewick.route": outcome.route, "ambrewick.reply.source": outcome.source})
for step in outcome.steps:
    name = f"tool {step.name}" if step.step == "tool" else step.step      # named by step, not by the standard
    attributes = {"ambrewick.step": step.step}
    if step.step in ("route", "answer"):                                  # model calls carry their token counts
        attributes |= {"ambrewick.tokens.input": step.prompt_tokens, "ambrewick.tokens.cached": step.cached_tokens,
                       "ambrewick.tokens.output": step.completion_tokens}
    span(tracer, name, step.start_ns, step.end_ns, parent=root, attributes=attributes)

rows = spans_to_rows(exporter)                 # sorted by (trace, start, span), so the order is fixed
root_row = next(row for row in rows if row["parent_span_id"] is None)
children = [row for row in rows if row["parent_span_id"] is not None]
assert len({row["trace_seq"] for row in rows}) == 1                       # one message, one trace
assert all(row["parent_span_id"] == root_row["span_id"] for row in children)
print("spans in the trace:", fmt_int(len(rows)))
print("spans under the root:", fmt_int(len(children)))
route = next(row for row in children if row["name"] == "route")
print("route span, input tokens on the span:", fmt_int(route["attributes"]["ambrewick.tokens.input"]))
