"""Head sampling on baseline day 1: the share of messages each ratio keeps, and the rule that a larger ratio keeps every
message a smaller one kept. The decision is the SDK's TraceIdRatioBased on each message's trace ID, as its root would
make it, so the same messages stay kept as the ratio grows. A live provider samples the same trace IDs at the source, and
the replayed and the live decisions must agree."""
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.dayrun import run_day_traced
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share
from lib.sampling import head_ratio, head_sample, live_provider, message_traces, only_messages

MODEL = "Qwen3-4B-Instruct-2507"
DAY = "2026-12-08"                                  # baseline day 1: no injected faults
RATIOS = (0.01, 0.1, 0.5, 1.0)                      # 1.0 keeps everything, the check that the ratio is read as a share
traces = only_messages(message_traces(run_day_traced(DAY, live=False).spans, DAY, MODEL, PriceTable()))
print("messages on baseline day 1, of all messages:", fmt_int(len(traces)))
kept = {}                                           # ratio -> the sequential trace IDs it keeps
for ratio in RATIOS:
    kept[ratio] = {t.seq for t in head_sample(traces, ratio)}
    print(f"messages kept at ratio {ratio}, of {len(traces)}:", fmt_int(len(kept[ratio])))
    print(f"share of messages kept at ratio {ratio}:", fmt_share(len(kept[ratio]), len(traces)))
    # The source's own decision: a provider with the same sampler makes one root per trace ID, counting from 1.
    provider = live_provider(head_ratio(ratio), InMemorySpanExporter())
    tracer = provider.get_tracer("ambrewick.assistant")
    live = set()
    for seq in range(1, len(traces) + 1):
        root = tracer.start_span("invoke_agent probe")
        if root.is_recording():
            live.add(seq)
        root.end()
    differ = len(live ^ kept[ratio])
    print(f"trace IDs where the replayed and the live decision differ at ratio {ratio}, of {len(traces)}:", fmt_int(differ))
    assert differ == 0
# A trace kept at a small ratio is kept at every larger one: the decision compares one fixed value with the ratio.
assert kept[0.01] <= kept[0.1] <= kept[0.5] <= kept[1.0]
assert len(kept[1.0]) == len(traces)
