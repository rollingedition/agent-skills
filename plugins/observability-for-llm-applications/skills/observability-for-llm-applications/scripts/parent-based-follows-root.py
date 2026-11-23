"""A parent-based sampler at the assistant decides each message's trace once, at its root, and the contacts server follows
that decision through the traceparent. The point rests on the server's count: no span reaches the receiver from a
trace the assistant did not sample."""
import json
import tempfile
from collections import Counter
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.clock import VirtualClock
from lib.report import fmt_int, fmt_share
from lib.sampling import head_ratio, live_provider
from lib.tools import LiveContacts

DAY, PROBES, RATIO = "2026-12-09", 40, 0.5
exporter = InMemorySpanExporter()
provider = live_provider(head_ratio(RATIO), exporter)  # the assistant's provider: its roots sampled at 0.5, children follow
trace.set_tracer_provider(provider)                    # the MCP client span is made by the process's global provider
tracer = provider.get_tracer("ambrewick.assistant")
recorded = {}                                          # trace ID -> whether the assistant's root was recorded
with tempfile.TemporaryDirectory() as folder:
    spans_file = Path(folder) / "contacts-spans.jsonl"  # the server writes here, and the file is read after it exits
    with LiveContacts(VirtualClock(DAY), spans_file) as contacts:
        for number in range(PROBES):
            with tracer.start_as_current_span(f"invoke_agent probe {number}") as root:
                recorded[format(root.get_span_context().trace_id, "032x")] = root.is_recording()
                contacts.find("U0028", "Ana")          # one tool call, inside this root, so its traceparent carries the root's flag
    server = [json.loads(line) for line in spans_file.read_text(encoding="utf-8").splitlines()]
per_trace = Counter(row["trace_id"] for row in server)
sampled = [t for t, yes in recorded.items() if yes]
unsampled = [t for t, yes in recorded.items() if not yes]
print("probes, one assistant root each:", fmt_int(PROBES))
print(f"roots sampled at ratio {RATIO}, of {PROBES}:", fmt_int(len(sampled)))
print(f"share of roots sampled at ratio {RATIO}:", fmt_share(len(sampled), PROBES))
print("contacts server spans under sampled roots:", fmt_int(sum(per_trace[t] for t in sampled)))
print("contacts server spans under unsampled roots:", fmt_int(sum(per_trace[t] for t in unsampled)))
print("unsampled roots with any server span, of the unsampled:", fmt_int(sum(per_trace[t] > 0 for t in unsampled)))
print("sampled roots with any server span, of the sampled:", fmt_int(sum(per_trace[t] > 0 for t in sampled)))
assert all(t in recorded for t in per_trace)  # every server span belongs to a probe's trace
assert not any(per_trace[t] for t in unsampled)     # the server records nothing for an unsampled trace
assert all(per_trace[t] for t in sampled)           # and everything for a sampled one
