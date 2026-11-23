"""OpenInference, a naming scheme the book does not emit, at its pinned version. Its module names the facts a model call
carries (the model, the provider, the token counts, the span kind, the messages) in its own words. The point rests on
the table: each name is one the pinned module defines, and each maps to a GenAI conventions name the book's registry or
its name table holds. The mapping is written here by hand, and checked against both."""
import lib  # lib first: threads and seeds are fixed before anything else

from importlib.metadata import version

from openinference.semconv.trace import OpenInferenceLLMSystemValues, OpenInferenceSpanKindValues, SpanAttributes

from lib import genai
from lib.names_map import NAMES

# OpenInference's constant and the GenAI name for the same fact. OpenInference's span kind has no GenAI attribute: the
# operation name carries the same meaning, chat for a model call.
MAPPING = (
    (SpanAttributes.LLM_MODEL_NAME, "gen_ai.request.model"),
    (SpanAttributes.LLM_SYSTEM, "gen_ai.provider.name"),
    (SpanAttributes.LLM_TOKEN_COUNT_PROMPT, "gen_ai.usage.input_tokens"),
    (SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, "gen_ai.usage.output_tokens"),
    (SpanAttributes.LLM_TOKEN_COUNT_PROMPT_DETAILS_CACHE_READ, "gen_ai.usage.cache_read.input_tokens"),
    (SpanAttributes.OPENINFERENCE_SPAN_KIND, "gen_ai.operation.name"),
    (SpanAttributes.LLM_INPUT_MESSAGES, "gen_ai.input.messages"),
    (SpanAttributes.LLM_OUTPUT_MESSAGES, "gen_ai.output.messages"),
)
known = set(genai.ATTR) | {name for names in NAMES.values() for name in names}
print("openinference-semantic-conventions version:", version("openinference-semantic-conventions"))
for openinference, conventions in MAPPING:
    print(f"{openinference} -> {conventions}")
    assert conventions in known
print("span kind for a model call:", OpenInferenceSpanKindValues.LLM.value)
print(f"{SpanAttributes.LLM_SYSTEM} for an OpenAI client:", OpenInferenceLLMSystemValues.OPENAI.value)
