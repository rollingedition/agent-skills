"""The content switch: whether the official package's span holds the prompt and the reply. The package reads one variable,
and the spec's name for the same switch is read nowhere in the package. The point rests on three counts. With the spec's
name set to SPAN_ONLY, one call's span holds no content. With the package's own name set to SPAN_ONLY, a control call's
span holds two, so the count can rise and the package does read its name. And the package's parser gives NO_CONTENT when
its variable is unset and when it holds a value that is not a mode. The control records content for one call, and this
example prints only how many content attributes that span holds, never their values."""
import lib  # lib first: threads and seeds are fixed before anything else

import os

import opentelemetry.sdk.trace as sdk_trace
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.util.genai.utils import ContentCapturingMode, get_content_capturing_mode

from lib.assistant import RELEASES
from lib.case import load_messages
from lib.clock import VirtualClock
from lib.http_replay import client, route_body
from lib.ids import SequentialIds
from lib.tracing import make_provider

PACKAGE_VARIABLE = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"
SPEC_VARIABLE = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT"
print("the package reads:", PACKAGE_VARIABLE, "| the spec's name for the switch:", SPEC_VARIABLE)
print("values the package parses:", ", ".join(mode.name for mode in ContentCapturingMode))
os.environ.pop(PACKAGE_VARIABLE, None)
print("mode, package variable unset:", get_content_capturing_mode().name)
os.environ[PACKAGE_VARIABLE] = "not a mode"                   # the parser logs this and falls back, it does not raise
print("mode, value that is not a mode:", get_content_capturing_mode().name)
os.environ.pop(PACKAGE_VARIABLE)


# Instrument afresh with the variable set to SPAN_ONLY, make one call, and print how many content attributes its span
# holds. The package reads its mode when it is instrumented, so the variable is set before that and removed after.
def content_attributes(variable: str, label: str, expected: int) -> None:
    os.environ[variable] = "SPAN_ONLY"
    clock = VirtualClock("2026-12-07")
    sdk_trace.time_ns = lambda: clock.advance(1_000_000)      # virtual span times, as in instrumented-chat-call
    exporter = InMemorySpanExporter()
    provider = make_provider("ambrewick-assistant", RELEASES["r0"].service_version, "example", clock, SequentialIds(),
                             exporter, "https://opentelemetry.io/schemas/1.45.0")
    instrumentor = OpenAIInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    client().chat.completions.create(**route_body(load_messages("2026-12-07")[0]))
    instrumentor.uninstrument()
    os.environ.pop(variable)
    call = exporter.get_finished_spans()[0]
    count = len([key for key in call.attributes if key.startswith(("gen_ai.input.messages", "gen_ai.output.messages"))])
    print(f"content attributes on the span, {label}:", count)
    assert count == expected


content_attributes(SPEC_VARIABLE, "spec variable set", 0)     # set, and read by nothing in the package
content_attributes(PACKAGE_VARIABLE, "package variable set", 2)   # the control: the package's own name, one call
