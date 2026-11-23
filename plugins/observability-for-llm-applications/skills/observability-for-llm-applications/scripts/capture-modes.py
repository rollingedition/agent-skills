"""The four content modes of the official package, each set before the package is instrumented and run on the same
recorded answer call. The point rests on the printed pairs: only the span modes put the messages on the span, and only
the event modes write a log record, so SPAN_AND_EVENT writes both. The example prints counts, never the messages."""
import lib  # lib first: threads and seeds are fixed before anything else

import os

from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.assistant import RELEASES
from lib.clock import VirtualClock
from lib.ids import SequentialIds
from lib.scan import CAPTURE, CONTENT_KEYS, captured_call, model_calls
from lib.tracing import make_provider

CALL = next(call for call in model_calls("baseline-day-1") if call["step"] == "answer")  # the day's first answer call
EXPECTED = {"NO_CONTENT": (0, 0), "SPAN_ONLY": (2, 0), "EVENT_ONLY": (0, 1), "SPAN_AND_EVENT": (2, 1)}


def run(mode: str) -> tuple[int, int, str]:
    """One call under `mode`: the content attributes on its span, the log records written, and the log's event name."""
    os.environ[CAPTURE] = mode  # the package reads the mode when it is instrumented, so it is set first
    spans, logs = InMemorySpanExporter(), InMemoryLogRecordExporter()
    logger_provider = LoggerProvider()
    logger_provider.add_log_record_processor(SimpleLogRecordProcessor(logs))  # where the event modes write their record
    provider = make_provider("ambrewick-assistant", RELEASES["r0"].service_version, "modes",
                             VirtualClock("2026-12-08"), SequentialIds(), spans,
                             "https://opentelemetry.io/schemas/1.45.0")
    instrumentor = OpenAIInstrumentor()
    instrumentor.instrument(tracer_provider=provider, logger_provider=logger_provider)
    captured_call(CALL)
    instrumentor.uninstrument()
    del os.environ[CAPTURE]
    content = sum(key.startswith(CONTENT_KEYS) for key in spans.get_finished_spans()[0].attributes)
    names = {record.log_record.event_name for record in logs.get_finished_logs()}
    return content, len(logs.get_finished_logs()), ", ".join(sorted(names))


for mode in EXPECTED:
    content, records, event = run(mode)
    print(f"content attributes on the span, {mode}: {content}")
    print(f"log records, {mode}: {records}")
    if event:
        print(f"event name on the log record, {mode}: {event}")
    assert (content, records) == EXPECTED[mode]  # the pairs the prose quotes
