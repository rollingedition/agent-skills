"""Run the validator over chapter 1's rough spans for message 809: every span fails, because none names a registry span
type.

The point rests on the count of findings, one per span, and on the text of each: "no known span type" means the span
carries neither `gen_ai.operation.name` nor an MCP method, which is how the validator finds a registry span's type."""
from lib.dayrun import RELEASE, run_dev_day
from lib.export import spans_to_rows
from lib.genai import REGISTRY_VERSION, validate
from lib.ids import SequentialIds
from lib.report import fmt_int
from lib.tracing import make_provider, span
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# Chapter 1 stamped this schema; kept so the spans are the ones chapter 1 printed.
CHAPTER_1_SCHEMA = "https://opentelemetry.io/schemas/1.44.0"

(run,) = run_dev_day(["809"])  # message 809: a route call, a retrieval, and an answer call
outcome = run.outcome
exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", run.clock, SequentialIds(),
                         exporter, CHAPTER_1_SCHEMA)
tracer = provider.get_tracer("ambrewick.assistant")
# Chapter 1's names: the root is the message, each step is named by its step, and no kind is set (INTERNAL).
root = span(tracer, "message", run.arrived_ns, run.replied_ns,
            attributes={"ambrewick.route": outcome.route, "ambrewick.reply.source": outcome.source})
for step in outcome.steps:
    attributes = {"ambrewick.step": step.step}
    if step.step in ("route", "answer"):  # model calls carry their token counts, under the book's own keys
        attributes |= {"ambrewick.tokens.input": step.prompt_tokens, "ambrewick.tokens.cached": step.cached_tokens,
                       "ambrewick.tokens.output": step.completion_tokens}
    span(tracer, step.step, step.start_ns, step.end_ns, parent=root, attributes=attributes)

rows = spans_to_rows(exporter)  # sorted by (trace, start, span), so the findings print in the same order every run
findings = [finding for row in rows for finding in validate(row)]
print("GenAI conventions version:", REGISTRY_VERSION)
print("spans checked:", fmt_int(len(rows)))
for finding in findings:
    print("finding:", finding)
print("findings, no known span type:", fmt_int(sum("no known span type" in finding for finding in findings)))
print("findings, all:", fmt_int(len(findings)))
assert all(len(validate(row)) == 1 for row in rows)  # each span fails once, and only once
