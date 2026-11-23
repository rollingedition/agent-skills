"""Put the release and the prompt version in baggage, and carry them as an MCP call would: the global propagator writes the
`baggage` entry that the SDK sends in `_meta`. A user identifier is refused under an unknown key and under an allowed one.
The prose rests on the last two printed lines, which the asserts back."""
from lib.context import ALLOWED_BAGGAGE_KEYS, baggage_context
from opentelemetry import baggage, propagate


def refused(values):
    """True when baggage_context refuses these values."""
    try:
        baggage_context(values)
    except ValueError:
        return True
    return False


ctx = baggage_context({"ambrewick.release": "1.0.0", "ambrewick.prompt.version": "p1"})
carrier = {}
propagate.inject(carrier, context=ctx)  # the same global propagator the SDK uses for `_meta`
carried = sorted(baggage.get_all(ctx))
assert carried == sorted(ALLOWED_BAGGAGE_KEYS)  # nothing else is carried
assert carrier["baggage"] == "ambrewick.prompt.version=p1,ambrewick.release=1.0.0"
assert refused({"ambrewick.user.id": "U0161"})  # a key that is not allowed
assert refused({"ambrewick.release": "U0161"})  # a user identifier under an allowed key, which is not in its form

print("allowed baggage keys:", ", ".join(sorted(ALLOWED_BAGGAGE_KEYS)))
print("baggage keys carried on a call:", ", ".join(carried))
print("baggage entry sent in _meta:", carrier["baggage"])
print("user identifier refused: yes")
print("user identifier under an allowed key refused: yes")
