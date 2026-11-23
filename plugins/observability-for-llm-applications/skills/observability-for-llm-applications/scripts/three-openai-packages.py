"""Three packages called openai instrument the client, and they disagree on names and on content. Two are OpenTelemetry's
and differ in naming scheme; the third is Traceloop's and captures content by default. Only the first is installed in the
pinned environment, so the point rests on that one: its version is printed, and the module that reads its content switch
names the switch the table gives. The other two are not importable here, so their names and defaults are the source
readings the chapter cites, printed as wheel readings and not as runs."""
import lib  # lib first: threads and seeds are fixed before anything else

import importlib.util
from importlib.metadata import version

# Name as PyPI spells it; the module it imports; its project; the naming its source gives; its content switch and that
# switch's default, both from the source reading in notes/research/client-library-instrumentation.md (S2, S6, S7).
PACKAGES = (
    ("opentelemetry-instrumentation-genai-openai", "opentelemetry.instrumentation.genai.openai", "OpenTelemetry",
     "GenAI conventions, latest experimental, unconditionally", "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
     "NO_CONTENT"),
    ("opentelemetry-instrumentation-openai-v2", "opentelemetry.instrumentation.openai_v2", "OpenTelemetry",
     "GenAI conventions v1.30.0 unless the experimental opt-in is set", "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
     "false"),
    ("opentelemetry-instrumentation-openai", "opentelemetry.instrumentation.openai", "Traceloop",
     "its own names, from opentelemetry-semantic-conventions-ai 0.5.1", "TRACELOOP_TRACE_CONTENT", "true"),
)
installed = [row for row in PACKAGES if importlib.util.find_spec(row[1]) is not None]
assert [row[0] for row in installed] == ["opentelemetry-instrumentation-genai-openai"]
source = importlib.util.find_spec("opentelemetry.util.genai.utils").origin
assert installed[0][4] in open(source, encoding="utf-8").read()     # the module that reads the switch names it

print("packages importable in this environment:", len(installed))
print("installed version:", version(installed[0][0]))
for name, module, project, naming, switch, default in PACKAGES:
    print(f"{name}, evidence:", "installed source" if name == installed[0][0] else "wheel reading")
    print(f"{name}, project:", project)
    print(f"{name}, naming:", naming)
    print(f"{name}, content switch:", switch)
    print(f"{name}, content switch default:", default)
