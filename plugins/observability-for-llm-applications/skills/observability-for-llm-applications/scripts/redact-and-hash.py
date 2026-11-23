"""The redacting processor, and the keyed pseudonym that replaces a user ID. Redaction is defence in depth: it removes
what the process can recognise from each span before the span is exported. The point rests on two printed results: the
processor's spans hold no synthetic name or address, and a keyed hash resists the enumeration that an unkeyed hash of
the same candidate IDs does not. The demonstration key is in the code, so the last enumeration succeeds, as it must."""
import lib  # lib first: threads and seeds are fixed before anything else

import hashlib
import hmac

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lib.case import load_users
from lib.ids import SequentialIds
from lib.redact import USER_ID_ATTRIBUTE, RedactingProcessor, hash_user, pseudonym
from lib.report import fmt_int
from lib.scan import SYNTHETIC, captured_day, scan_rows

DAY = "2026-12-08"
raw, redacted = captured_day(DAY), captured_day(DAY, redact=True)  # the same calls, without and with the processor
before, after = scan_rows(raw), scan_rows(redacted)
for kind in SYNTHETIC:
    print(f"{kind} before the processor: {fmt_int(before[kind])}")
    print(f"{kind} after the processor: {fmt_int(after[kind])}")
assert all(after[kind] == 0 for kind in SYNTHETIC)  # the processor removes every synthetic item the day's calls hold

# A root span with a user ID goes through the same processor. The attribute the span exports is the pseudonym.
TARGET = load_users()[0].user_id  # one of the case's synthetic users; not printed
exporter = InMemorySpanExporter()
provider = TracerProvider(id_generator=SequentialIds())
provider.add_span_processor(RedactingProcessor(exporter))  # the only path to the exporter
provider.get_tracer("ambrewick.assistant").start_span("invoke_agent ambrewick-assistant",
                                                      attributes={USER_ID_ATTRIBUTE: TARGET}).end()
root = exporter.get_finished_spans()[0]
print("user ID on the root span, after the processor:", root.attributes[USER_ID_ATTRIBUTE])
assert root.attributes[USER_ID_ATTRIBUTE] == pseudonym(TARGET) and TARGET not in str(dict(root.attributes))

# An attacker holds one stored hash of a user ID and tries every ID the format allows: U0000 to U9999.
CANDIDATES = [f"U{number:04d}" for number in range(10_000)]
stored_plain = hashlib.sha256(TARGET.encode("utf-8")).hexdigest()  # an unkeyed SHA-256 of the ID
stored_keyed = hash_user(TARGET)                                    # the keyed pseudonym, as the redactor makes it
print("candidate IDs tried:", fmt_int(len(CANDIDATES)))
found_plain = sum(hashlib.sha256(c.encode("utf-8")).hexdigest() == stored_plain for c in CANDIDATES)
print("unkeyed SHA-256 matches for the stored hash:", fmt_int(found_plain))
guess = b"a key the attacker does not hold"
found_guess = sum(hmac.new(guess, c.encode("utf-8"), hashlib.sha256).hexdigest() == stored_keyed for c in CANDIDATES)
print("keyed HMAC matches, with a key the attacker does not hold:", fmt_int(found_guess))
found_demo = sum(hash_user(c) == stored_keyed for c in CANDIDATES)  # with DEMO_KEY, which is in lib/redact.py
print("keyed HMAC matches, with the demonstration key in the code:", fmt_int(found_demo))
assert (found_plain, found_guess, found_demo) == (1, 0, 1)  # the key is the protection, and the code shows the one here
