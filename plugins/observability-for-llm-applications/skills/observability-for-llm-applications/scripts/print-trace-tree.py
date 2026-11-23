"""Print one dev-day message's trace as a tree, with each span's step, then check how its times add up. The spans are the
ones build-one-trace makes. The steps run one after another, so none overlap and the message's time is their sum. Where
spans do overlap, a parent's duration is not the sum of its children's; this trace shows no overlap."""
from lib.dayrun import RELEASE, run_dev_day
from lib.export import spans_to_rows
from lib.ids import SequentialIds
from lib.report import fmt_ms
from lib.tracing import make_provider, span
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

(run,) = run_dev_day(["809"])
outcome = run.outcome

exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", run.clock, SequentialIds(),
                         exporter, "https://opentelemetry.io/schemas/1.44.0")
tracer = provider.get_tracer("ambrewick.assistant")
root = span(tracer, "message", run.arrived_ns, run.replied_ns,
            attributes={"ambrewick.route": outcome.route, "ambrewick.reply.source": outcome.source})
for step in outcome.steps:
    name = f"tool {step.name}" if step.step == "tool" else step.step
    span(tracer, name, step.start_ns, step.end_ns, parent=root, attributes={"ambrewick.step": step.step})

rows = spans_to_rows(exporter)
root_row = next(row for row in rows if row["parent_span_id"] is None)
children = [row for row in rows if row["parent_span_id"] is not None]


def print_tree(row, depth):
    """Print a span, then its children one level further in. Shows the shape of the trace, not its times."""
    print("  " * depth + f"{row['name']}  step: {row['attributes'].get('ambrewick.step', '(root)')}")
    for child in (r for r in rows if r["parent_span_id"] == row["span_id"]):
        print_tree(child, depth + 1)


print_tree(root_row, 0)
# Sorted by start, two steps overlap exactly when a step starts before the one before it has ended.
ordered = sorted(children, key=lambda row: row["start_ns"])
overlap = any(later["start_ns"] < earlier["end_ns"] for earlier, later in zip(ordered, ordered[1:]))
root_time = root_row["end_ns"] - root_row["start_ns"]
steps_time = sum(row["end_ns"] - row["start_ns"] for row in children)
print("message span, time:", fmt_ms(root_time))
print("steps, time added up:", fmt_ms(steps_time))
print("steps overlap in time:", "yes" if overlap else "no")
print("message time equals the sum of its steps:", "yes" if root_time == steps_time else "no")
assert not overlap and root_time == steps_time
