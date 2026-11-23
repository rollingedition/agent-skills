"""What content capture adds to a message's bytes on baseline day 1, and what the SDK does to a long content value. A
message's bytes are those of its spans' rows in the JSON-lines export. The assistant's own spans carry no content, so the
bytes content adds are the difference between the package's spans for the same calls with capture on and off. The point
rests on the printed bytes per message and on the value limit's count of cut values, which the example also checks."""
import lib  # lib first: threads and seeds are fixed before anything else

import os

from lib.case import load_messages
from lib.dayrun import run_day_traced
from lib.report import fmt_int, fmt_share
from lib.sampling import row_bytes
from lib.scan import CONTENT_KEYS, captured_day, is_json

DAY = "2026-12-08"
LIMIT = 1000  # characters, for the value limit below
messages = len(load_messages(DAY))
assistant = run_day_traced(DAY, live=False).spans  # the message's spans, capture off: no content in them
off, on = captured_day(DAY, "NO_CONTENT"), captured_day(DAY, "SPAN_ONLY")
added = row_bytes(on) - row_bytes(off)  # the bytes content adds to the package's spans, over every call of the day
total = row_bytes(assistant) + added
print("bytes per message, capture off:", fmt_int(round(row_bytes(assistant) / messages)))
print("bytes content adds per message, capture on:", fmt_int(round(added / messages)))
print("bytes per message, capture on:", fmt_int(round(total / messages)))
print("content share of the bytes, capture on:", fmt_share(added, total))


values = [value for row in on for key, value in row["attributes"].items() if key.startswith(CONTENT_KEYS)]
os.environ["OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT"] = str(LIMIT)  # read when the provider is made: set before captured_day
cut = [value for row in captured_day(DAY) for key, value in row["attributes"].items() if key.startswith(CONTENT_KEYS)]
del os.environ["OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT"]
pairs = [(full, short) for full, short in zip(values, cut) if len(full) > LIMIT]  # each value, with and without limit
print("longest content value, no limit:", fmt_int(max(map(len, values))), "characters")
print(f"value length limit: {LIMIT:,} characters")
print("longest content value, cut at the limit:", fmt_int(max(map(len, cut))), "characters")
print("content values on the day:", fmt_int(len(values)))
print("content values cut by the limit:", fmt_int(len(pairs)))
print("cut values that no longer parse as JSON:", fmt_int(sum(not is_json(short) for _, short in pairs)))
# Nothing in the span marks a cut value, so a reader sees a shorter, broken message and no flag.
assert len(cut) == len(values) and max(map(len, cut)) == LIMIT
assert all(len(short) == LIMIT for _, short in pairs)
assert all(not is_json(short) for _, short in pairs)  # a value cut at a character is no longer JSON
