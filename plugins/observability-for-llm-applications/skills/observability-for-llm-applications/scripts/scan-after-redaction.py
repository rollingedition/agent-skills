"""The scanner's count after redaction, with the redacting processor on every set of spans. On baseline day 1 the synthetic
kinds are asserted zero, and MASSIVE's slot labels are counted before and after, their residue printed and never asserted
zero. On the incident day the contacts server's stack traces reach the receiver, and the receiver's redaction removes them
from both processes' spans. The point rests on the zeros and on the residue; the example prints counts only."""
import lib  # lib first: threads and seeds are fixed before anything else

from lib.redact import redact_row
from lib.report import fmt_int
from lib.scan import SLOT_LABELS, SYNTHETIC, absolute_paths, assistant_rows, captured_day, label, live_rows, of_service
from lib.scan import scan_rows, stack_traces

DAY, INCIDENT = "2026-12-08", "2026-12-09"
before = scan_rows(assistant_rows(DAY) + captured_day(DAY))  # the day's spans, as they are made
after = scan_rows(assistant_rows(DAY, redact=True) + captured_day(DAY, redact=True))  # the same, through the processor
for kind in SYNTHETIC:
    print(f"{kind} items before redaction: {fmt_int(before[kind])}")
    print(f"{kind} items after redaction: {fmt_int(after[kind])}")
SLOTS = [f"slot:{name}" for name in SLOT_LABELS]
for kind in SLOTS:  # counted in the captured text: measured, not asserted zero
    print(f"{label(kind)}, items before redaction: {fmt_int(before[kind])}")
    print(f"{label(kind)}, residue after redaction: {fmt_int(after[kind])}")
assert all(after[kind] == 0 for kind in SYNTHETIC)  # the synthetic users' items are all removed
assert all(after[kind] == before[kind] for kind in SLOTS)  # values untouched

# The incident day's rows as the receiver stores them: the assistant's spans and the contacts server's spans.
live = live_rows(INCIDENT)
cleaned = [redact_row(row) for row in live]  # the receiver's redaction, over both processes' spans
OWN, SERVER = "ambrewick-assistant", "contacts-server"
print("stack traces on the assistant's spans, before redaction:", fmt_int(len(stack_traces(of_service(live, OWN)))))
print("stack traces on the contacts server's spans, before redaction:",
      fmt_int(len(stack_traces(of_service(live, SERVER)))))
print("stack traces on the assistant's spans, after redaction at the receiver:",
      fmt_int(len(stack_traces(of_service(cleaned, OWN)))))
print("stack traces on the contacts server's spans, after redaction at the receiver:",
      fmt_int(len(stack_traces(of_service(cleaned, SERVER)))))
assert not stack_traces(cleaned)  # the receiver's redaction reaches both processes' spans
assert stack_traces(of_service(live, SERVER))  # the server's spans reach the receiver with their traces
assert absolute_paths(cleaned) == 0 and absolute_paths(live) > 0  # no path survives redaction; the raw rows hold paths
