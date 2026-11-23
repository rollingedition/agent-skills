"""Print the resource and the instrumentation scope of the renamed spans, with the schema URL each one carries, beside
chapter 1's stamp.

The point rests on the schema lines: chapter 1's resource said 1.44.0, the renamed spans say 1.45.0, and the SDK's
constants have no 1.45.0 schema, which the assert checks. The book takes that URL from the registry's manifest
(genai.SCHEMA_URL), and make_provider puts it on the tracer as well as the resource."""
from lib.dayrun import RELEASE
from lib.genai import SCHEMA_URL
from lib.ids import SequentialIds
from lib.tracing import make_provider, span
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.schemas import Schemas

CHAPTER_1_SCHEMA = "https://opentelemetry.io/schemas/1.44.0"


def version_key(url):
    """Sort key for a schema URL: its version as numbers, so 1.9 sorts before 1.44."""
    return tuple(int(part) for part in url.rsplit("/", 1)[1].split("."))


exporter = InMemorySpanExporter()
provider = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", None, SequentialIds(),
                         exporter)
tracer = provider.get_tracer("ambrewick.assistant")  # no schema given: the tracer carries the provider's
span(tracer, "resource probe", 1, 2)  # one ended span, so the scope's schema can be read from it
scope = exporter.get_finished_spans()[0].instrumentation_scope
chapter_1 = make_provider("ambrewick-assistant", RELEASE.service_version, "dev-day-replay", None, SequentialIds(),
                          InMemorySpanExporter(), CHAPTER_1_SCHEMA)  # the resource chapter 1 built, read back from it
known = {schema.value for schema in Schemas}  # what opentelemetry-semantic-conventions 0.66b2 can stamp
print("chapter 1's resource schema URL:", chapter_1.resource.schema_url)
print("renamed spans' resource schema URL:", provider.resource.schema_url)
print("renamed spans' scope schema URL:", scope.schema_url)
print("instrumentation scope name:", scope.name)
print("highest schema in the SDK's constants:", max(known, key=version_key))
print("service.name:", provider.resource.attributes["service.name"])
print("service.version:", provider.resource.attributes["service.version"])
print("service.instance.id:", provider.resource.attributes["service.instance.id"])
assert SCHEMA_URL not in known  # the constants stop at 1.44.0, so the book takes its 1.45.0 from the registry
assert provider.resource.schema_url == scope.schema_url == SCHEMA_URL
assert provider.resource.attributes["service.instance.id"] == "dev-day-replay"  # set, not drawn at random
