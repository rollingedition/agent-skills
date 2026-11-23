"""What the day's telemetry holds before any redaction, with content capture off and on, and the stack traces that leave the
contacts server with capture off. The point rests on the printed counts: every root span holds its user's ID either way,
the names and the dataset's values appear only with capture on, and the server's error spans carry stack traces that
reach the receiver. The example prints counts and the shape of one path, never a value or a full path."""
import lib  # lib first: threads and seeds are fixed before anything else

import re
from pathlib import Path

from lib.case import load_messages
from lib.dayrun import run_day_traced
from lib.report import fmt_int
from lib.scan import KINDS, captured_day, label, live_rows, of_service, scan_rows, spans_holding, stack_traces

DAY, INCIDENT = "2026-12-08", "2026-12-09"   # baseline day 1, and the incident day, whose contacts server fails
assistant = run_day_traced(DAY, live=False).spans  # the assistant's own spans; the replay keeps no content
content = captured_day(DAY)                        # the day's model calls through the package, content on
rows = assistant + content
items, spans = scan_rows(rows), spans_holding(rows)
print("messages on the day:", fmt_int(len(load_messages(DAY))))
print("spans, capture off:", fmt_int(len(assistant)))
print("spans from the package, capture on:", fmt_int(len(content)))
for kind in KINDS:
    if kind != "stacktrace":  # the stack traces are on the incident day, below
        print(f"{label(kind)} items, capture off and on: {fmt_int(items[kind])}")
        print(f"{label(kind)} spans holding it: {fmt_int(spans[kind])}")
off = scan_rows(assistant)
assert all(off[kind] == 0 for kind in KINDS if kind not in ("user_id", "stacktrace"))  # capture off: no name, no text
assert spans["user_id"] == len(load_messages(DAY))  # one root span per message, each with the user's ID, whatever the capture
assert items["user_name"] > 0 and items["slot:person"] > 0  # capture on: names and the dataset's values reach spans

# The incident day through the book's receiver, capture off. The contacts server's error spans carry the traceback.
live = live_rows(INCIDENT)
server, mine = of_service(live, "contacts-server"), of_service(live, "ambrewick-assistant")
server_traces = stack_traces(server)
errors = sum(row["status"] == "ERROR" for row in server if row["name"] == "contacts.lookup")
traced = {row["trace_id"] for row in live if stack_traces([row])}
print("contacts server spans the receiver stored:", fmt_int(len(server)))
print("contacts.lookup spans in error:", fmt_int(errors))
print("stack traces on the contacts server's spans:", fmt_int(len(server_traces)))
print("stack traces on the assistant's spans:", fmt_int(len(stack_traces(mine))))
print("incident traces holding a stack trace:", fmt_int(len(traced)))
print("file paths named in the server's stack traces:", fmt_int(sum(t.count('File "') for t in server_traces)))
# The innermost frame names the file and line that raised. Only the file's name is printed; its folder is a placeholder.
path, line, function = re.findall(r'File "([^"]+)", line (\d+), in (\S+)', server_traces[0])[-1]
print(f'innermost frame, first server trace: File "<folder>/{Path(path).name}", line {line}, in {function}')
assert len(server_traces) == errors and stack_traces(mine)  # every error span of the server carries its traceback
