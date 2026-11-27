---
title: "Observability for LLM Applications"
chapter: "Keep private data out of telemetry"
chapter_id: keep-private-data-out
book: observability-for-llm-applications
edition: 2026.11.3
verified: 2026-11-23
edition_code: 9P10-Q8SD
canonical: https://rollingedition.com/observability-for-llm-applications/keep-private-data-out
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Keep private data out of telemetry,” chapter 12 of Observability for LLM Applications, Edition 2026.11.3, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/keep-private-data-out. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Keep private data out of telemetry

By the end of this chapter you can keep personal data out of the assistant's telemetry by default, turn content capture on for a stated purpose and count what that leaks, and say which leaks redaction can remove and which it cannot reach. You'll also run the scan that counts what is left, and you'll see which counts are zero by assertion and which are only measured.

Ambrewick's traces are read by people who did not write the assistant. The on-call engineer opens a trace after an alert, and the contacts team opens the traces that its own lookups joined. Some of what those traces hold is personal. Every message's root span carries the user's ID whether or not anyone asked for content, and the engineer who chases one wrong route will want the prompt and the reply. Capturing those puts the user's name in the same spans, next to the people, places and relations that the requests mention. The contacts server adds a leak that no capture switch controls. The problem, in the case, is that the trace that explains a wrong route is also a copy of the conversation.

The users, the tools and the contacts are synthetic, and the requests are MASSIVE's. The users' names come from fixed lists, their addresses sit on the `.example` domain, and the case has no payment or phone numbers of its own. The requests keep the person, place and relation values that MASSIVE annotates. Those values are request text that the dataset's crowd workers wrote, and this book leaves them as written, labelled by their slots. The scanner reads each span's values and its captured text, counts each kind it looks for, one item for each match, and this chapter reports the count that redaction cannot remove. Most of the examples replay baseline day 1. Where the contacts server matters, they read the incident day from [chapter 9](#an-alert-that-stays-quiet).

## Capture off comes first {#capture-off-by-default}

The [content capture](#the-capture-switch) switch from chapter 3 is the primary defence in this chapter, and it comes first. With the switch unset the package records no prompt and no reply, so there is nothing for a later step to remove. Everything after this section is for the cases where someone has turned the switch on. A service that has not named a purpose for content keeps the switch at its default, and it reads the default of every package it loads, because one package's default is not another's.

One model call under each of the four modes shows what each mode writes, to the span and to the logs.

Example `capture-modes` (Python 3.13.16 · bm25s 0.3.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.58.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
content attributes on the span, NO_CONTENT: 0
log records, NO_CONTENT: 0
content attributes on the span, SPAN_ONLY: 2
log records, SPAN_ONLY: 0
content attributes on the span, EVENT_ONLY: 0
log records, EVENT_ONLY: 1
event name on the log record, EVENT_ONLY: gen_ai.client.inference.operation.details
content attributes on the span, SPAN_AND_EVENT: 2
log records, SPAN_AND_EVENT: 1
event name on the log record, SPAN_AND_EVENT: gen_ai.client.inference.operation.details
```

With the switch unset, the content is in neither place: the span holds 0 content attributes, and the package writes 0 log records. The span modes put the prompt and the reply on the span, and the event modes write a log record, as the next section describes. That pair is the whole case for the primary defence: the content is not in the telemetry, so nothing downstream can leak it.

Capture off does not mean that nothing leaves. The user's ID sits on every message's root span whichever mode is set, and the [leak example](#what-leaks-when-capture-is-on) asserts one such span for each message, whatever the capture setting. The ID is the user's own identifier, and a trace needs some identifier to answer which user a message came from, so it cannot be left out. It has to be replaced before it is stored, and [keyed user pseudonyms](#keyed-user-pseudonyms) show how.

No email address appears in any span of baseline day 1, with capture on or off. The assistant's policy tells the model never to repeat a contact's address in a reply, and no tool span carries its arguments, so an address has no route into a span. The scanner finds no address before [redaction](#redaction-as-defence-in-depth) or after it. The email kind reads zero because the design gives an address no route, and the scanner, which looks for every case address as written, confirms it.

Names behave differently. With capture off, the [leak example](#what-leaks-when-capture-is-on) asserts that no user name and no message text reaches a span. Names appear only when capture is on, which the next section measures.

**Working rule:** Keep content capture off in every service, and read the default of each loaded package before you deploy it. Turn capture on only for a purpose you can name, and only where a redactor runs on every span before the backend keeps it.

## What leaks when capture is on {#what-leaks-when-capture-is-on}

Suppose an engineer turns capture on to debug one wrong route. The reason is a good one, and what it costs is the same for every message that day. Each mode writes content to a different place. In `SPAN_ONLY` the prompt and the reply go into two span attributes, `gen_ai.input.messages` and `gen_ai.output.messages`, the names the registry gives them. The system text is folded into the input messages, so the instructions the model was given travel with the user's text. In `EVENT_ONLY` the same content goes onto a log record named `gen_ai.client.inference.operation.details`, and the span holds none of it. `SPAN_AND_EVENT` writes both. The logs SDK is still published under the private `opentelemetry.sdk._logs` at 1.45.2. A reader configures a `LoggerProvider` from it, and `InMemoryLogRecordExporter` is the class that reads records back. The package writes through the logs API, not that path. A second switch writes content as well. The upload hook writes messages to a store whenever it is on, with capture set or not, and [keeping content by reference](#keep-content-by-reference) shows what that does.

A personal-looking value is a person, place or relation name in a request's text, written by the dataset's crowd workers and labelled by its slots; it looks like personal data in a span and is treated as such; it was written for the dataset and is not drawn from anyone's messages, though the dataset keeps some public names as written. [Data Governance as Code](https://rollingedition.com/concepts/data-governance/personal-data) treats personal data as data that relates to an identifiable person. The handling here, to find, redact and count, is the same. The same reading covers the other slot labels the scanner counts. The scanner finds these values by their words in the captured text. A word that is a value under one label can match under another, so the counts are measures.

Running the day twice, with capture off and then on, shows what each run's spans hold.

Example `leak-with-capture-on` (Python 3.13.16 · bm25s 0.3.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.58.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
messages on the day: 200
spans, capture off: 675
spans from the package, capture on: 321
user_id items, capture off and on: 200
user_id spans holding it: 200
user_name items, capture off and on: 2
user_name spans holding it: 2
email items, capture off and on: 0
email spans holding it: 0
person slot items, capture off and on: 55
person slot spans holding it: 38
place_name slot items, capture off and on: 44
place_name slot spans holding it: 33
relation slot items, capture off and on: 26
relation slot spans holding it: 25
email_address slot items, capture off and on: 0
email_address slot spans holding it: 0
personal_info slot items, capture off and on: 0
personal_info slot spans holding it: 0
contacts server spans the receiver stored: 22
contacts.lookup spans in error: 3
stack traces on the contacts server's spans: 3
stack traces on the assistant's spans: 4
incident traces holding a stack trace: 5
file paths named in the server's stack traces: 9
innermost frame, first server trace: File "<folder>/contacts_server.py", line 164, in find_contact
```

With capture off, each of the 200 messages leaves a user ID on its root span, and no name or message text reaches a span. With capture on, names reach 2 spans and the spans holding a person value number 38. The text sits in the package's model-call spans, of which there are 321, while the assistant's own spans carry no text. The next section's redaction is the answer to what the text leaves behind.

Capture also adds bytes to every message's trace, and [chapter 11](#retention) asked for that number before any period was set. Measuring the bytes on the same export path puts a number on the cost.

Example `content-bytes-per-message` (Python 3.13.16 · bm25s 0.3.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.58.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
bytes per message, capture off: 2,831
bytes content adds per message, capture on: 2,716
bytes per message, capture on: 5,547
content share of the bytes, capture on: 49.0%
longest content value, no limit: 2,907 characters
value length limit: 1,000 characters
longest content value, cut at the limit: 1,000 characters
content values on the day: 642
content values cut by the limit: 87
cut values that no longer parse as JSON: 87
```

Content nearly doubles a message's bytes. With capture off, a message's span rows take 2,831 bytes, the figure chapter 11 printed. With capture on they take 5,547, so content adds 2,716 bytes, which is 49.0% of the total. The bytes are those of each span's row in the JSON-lines export.

The SDK can also cut a long value. The longest content value on the day is 2,907 characters long. Under a value length limit of 1,000 characters, that value is cut to the limit. The limit touches 87 of the 642 values, and every cut value fails to parse as JSON. A value cut at a character is shorter, and it no longer reads as the structure it was. The limit counts characters, not bytes, so a value cut at the limit can still take more bytes than the limit suggests.

**Working rule:** Measure a message's bytes with content on, as well as with it off, before you choose a retention period. Count the bytes against the export the period will keep, and do not assume that a limit leaves a readable value.

## Stack traces leak without capture {#stack-traces-leak-without-capture}

The contacts server is a separate process, and its spans reach the receiver by a route the assistant's code does not control. [Chapter 4](#the-contacts-server) introduced the server, and [chapter 5](#the-book-receiver) showed that it exports its own spans over OTLP when it is given an endpoint. The server opens its `contacts.lookup` span with `start_as_current_span` and sets nothing about exceptions, so the API's default, `record_exception=True` at 1.45.2, writes an `exception` event on that span when a tool raises. The event can carry `exception.stacktrace`, the traceback. A traceback names each file by its path, and those paths name the folders of the process that ran the code.

Capture was off when the [leak example](#what-leaks-when-capture-is-on) read the incident day, and the stack traces were there anyway. On that day the receiver stored 22 contacts server spans. 3 of its `contacts.lookup` spans were in error, and each of those error spans carried a stack trace, 3 in all. Between them the traces name 9 file paths. The innermost frame of the first one is `find_contact`, in the server's own file, `contacts_server.py`, under a placeholder for the folder. The output prints the shape of that path and never the path itself, since a full path is what this section is about. The fix below drops only `exception.stacktrace`: the exception event, with its class and message, stays, as [chapter 8 decided](#find-the-failure-decisions).

The assistant's own spans carry stack traces as well, 4 of them on the incident day. The MCP SDK's client dispatcher writes those on the client spans, and the tool-attempt spans carry only the exception's class and message. So the traceback leaves from both processes, and the leak does not depend on what the assistant chooses to record. Tail sampling in [chapter 11](#tail-sampling) keeps a trace whose message has an error, and the scan reads every one of the 5 traces that hold a stack trace, kept or dropped.

A stack trace names no user, but its paths can name the account that ran the process, which is personal data, and they reveal the machine. The scanner counts stack traces as a kind of their own, apart from the personal items. A reader might ask whether the traceback is worth keeping. The engineer who opens a trace needs the exception's class and message, which the span keeps, and the failing tool's name, which it also keeps. The folder names add nothing a fix needs.

This is the leak that capture cannot stop, and the assistant's redactor cannot reach the server's half of it. The [redaction section](#redaction-as-defence-in-depth) counts what is left after the assistant's redactor runs, and shows where a redactor does reach these traces.

**Working rule:** Treat a stack trace as sensitive in every service, and keep it out of any backend. Remove it where every service's spans pass. At the source, ask the team that owns the server to set `record_exception=False` on the span and to set the exception's class and message by hand, since the client's traces can only be removed downstream.

## Redaction is defence in depth {#redaction-as-defence-in-depth}

Redaction replaces a personal value in a span's attributes or events with a placeholder before the span is stored: in the process that made it, or where every service's spans pass. The assistant's process does that with a span processor, as [chapter 1](#spans-by-hand) defined it. This processor exports a redacted copy of each span as the span ends. It has to copy, because the SDK freezes a span's attributes when the span ends, and after that an in-place edit is not possible. [Data Governance as Code's `redact`](https://rollingedition.com/concepts/data-governance/redact) is a NULL cast on a query's column, which is a different operation from this one, since this redaction applies to telemetry.

What the processor removes is specific. The synthetic users' names and addresses become the placeholders `[name]` and `[email]`. A user ID becomes its pseudonym, which the next section defines. A stack trace is dropped rather than replaced, because its paths name the folders of the process that ran the code. A `file://` reference keeps its scheme and its file name, and its folder becomes a placeholder. A span's status description is redacted too, since it can hold an exception's message. Personal-looking values pass through unchanged, since the processor cannot tell a name in free text from any other word, and the case gives it no labels that would tell them apart.

The next example runs the processor over the day's spans and counts what it leaves, then runs the receiver's redaction over the incident day's stored rows.

Example `scan-after-redaction` (Python 3.13.16 · bm25s 0.3.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.58.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
user_id items before redaction: 200
user_id items after redaction: 0
user_name items before redaction: 2
user_name items after redaction: 0
email items before redaction: 0
email items after redaction: 0
person slot, items before redaction: 55
person slot, residue after redaction: 55
place_name slot, items before redaction: 44
place_name slot, residue after redaction: 44
relation slot, items before redaction: 26
relation slot, residue after redaction: 26
email_address slot, items before redaction: 0
email_address slot, residue after redaction: 0
personal_info slot, items before redaction: 0
personal_info slot, residue after redaction: 0
stack traces on the assistant's spans, before redaction: 4
stack traces on the contacts server's spans, before redaction: 3
stack traces on the assistant's spans, after redaction at the receiver: 0
stack traces on the contacts server's spans, after redaction at the receiver: 0
```

Redaction removes every synthetic item the day holds and leaves the personal-looking values as they were, and the example asserts both. The 200 user IDs and the 2 user names fall to zero. The email kind has no items before or after, for the reason the [first section](#capture-off-by-default) gives. The 55 person values are all still there after redaction: the residue is 55, and the other slot labels are printed beside it.

On the incident day the stack traces reach the receiver from both processes, and redaction there removes them. The assistant's spans hold 4 stack traces and the contacts server's spans hold 3. The server's spans go from its exporter to the receiver without passing the assistant's processor, so that processor cannot see them. After redaction at the receiver, the counts are 0 and 0.

The receiver is where both processes' spans pass. [Chapter 5](#the-book-receiver) stored them there, and the example runs the same redaction over the stored rows. That is the second place the definition names, where every service's spans pass, and [changing the backend](#changing-backends) in chapter 5 named the Collector as the place where a rule sees every service's spans. The Collector's redaction processor does this work in production. It deletes keys that are not on an allow-list and masks values that match a blocked list, and its README calls it "one line of defence rather than the only compliance measure in place". The receiver stands in for that place in this book.

A process can redact only the spans it writes, so a redactor in one service protects that service and nothing else. Redaction works where the spans of every service pass, and a redactor in each process is a second line behind that.

**Working rule:** Run redaction in every process, so that it covers what that process writes, and run it again where every service's spans pass, so that it covers what the other processes write. Count the items after both. A non-zero count of a synthetic kind is a failure, and a non-zero count of a personal-looking value is the redactor's reach.

## Keyed user pseudonyms {#keyed-user-pseudonyms}

A user ID is the one identifier that every trace keeps, so redaction has to replace it and not drop it. A keyed pseudonym replaces a user ID with an HMAC-SHA256 of it under a key, kept to twelve hexadecimal digits, the same for one user wherever it appears. [Data Governance as Code](https://rollingedition.com/concepts/data-governance/keyed-pseudonym) has a keyed pseudonym of its own, which is related to this one and is not the same. That book keeps eight digits and hashes the entity type and the case-folded value under a key only its corpus job holds. This chapter's code keeps twelve digits and hashes the raw user ID under a demonstration key in the code, because the case has one identifier type and the key is there to show the construction.

The key matters because the user IDs are sequential, so anyone can write out every candidate. A plain SHA-256 of each candidate matches a stored hash directly, and the hash of a real ID protects nothing. The key changes the question. A reader who does not hold the key can hash every candidate and still match nothing.

Trying every candidate ID against one stored hash shows what the key is for.

Example `redact-and-hash` (Python 3.13.16 · bm25s 0.3.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.58.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
user_id before the processor: 0
user_id after the processor: 0
user_name before the processor: 2
user_name after the processor: 0
email before the processor: 0
email after the processor: 0
user ID on the root span, after the processor: user-fd52e7ae5e26
candidate IDs tried: 10,000
unkeyed SHA-256 matches for the stored hash: 1
keyed HMAC matches, with a key the attacker does not hold: 0
keyed HMAC matches, with the demonstration key in the code: 1
```

A keyed hash resists the enumeration that an unkeyed one does not. Of the 10,000 candidate IDs tried against one stored hash, an unkeyed SHA-256 finds 1 match, which is the target, while a keyed HMAC with a key the attacker does not hold finds 0. The same keyed HMAC with the demonstration key, which is written in this book's code, finds 1 match.

The last count is why the key has to be secret in practice. The demonstration key in the code is not a secret, since anyone who reads the file holds it. The run shows the construction and does not protect an identifier. We recommend a secret store for a real key, kept away from the code and from the telemetry.

That is why a pseudonym is safer than the raw ID to put in a span, which [chapter 4](#what-goes-in-baggage) promised to explain. It is not anonymous, though. A stable pseudonym still links all of one user's spans, so an engineer can find every message from the same user, and the content beside it can still identify the user. [OpenTelemetry's guidance on handling sensitive data](https://opentelemetry.io/docs/security/handling-sensitive-data/) notes that hashing may not give the anonymity a team needs. A user ID does not go into baggage, and the pseudonym does not go there either. In a span the pseudonym names no one to a reader who lacks the key, and the redactor applies the same pseudonym to a user ID that appears in a message's text, so two spans about one user still match after redaction.

**Working rule:** Key every pseudonym with a secret that the telemetry's readers never hold, and keep the key outside the code. Change the key only with a plan, since a new key starts every user's pseudonym again, and the traces made before the change no longer join the ones made after it.

## Keep content by reference {#keep-content-by-reference}

Redaction removes what it knows how to find. Another route keeps the content out of the span altogether. An external content reference puts a pointer in the span, a `*_ref` attribute, and the content itself in a store with its own access rules.

The package has an upload hook, which the variable `OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK` names, with the value `upload`. The specification names the variable `OTEL_INSTRUMENTATION_GENAI_CONTENT_HOOK`, but the package reads only the completion-hook name, so that is the one to set. The hook writes each call's messages to files and puts references on the span, `gen_ai.input.messages_ref` and `gen_ai.output.messages_ref`, which are the registry's names. The hook also needs `OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH` set, and it imports `fsspec`, which this book pins at 2026.9.0. [Chapter 3](#the-capture-switch) set neither, so this is the first point in the book where the hook runs.

Sending the same twenty calls through the hook three ways sorts out where the content goes.

Example `content-by-reference` (Python 3.13.16 · bm25s 0.3.16 · httpx 0.28.1 · mcp 2.3.0 · numpy 2.5.5 · openai 3.58.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""The upload hook, which writes each call's messages to a store and puts a reference on the span. The same twenty calls
run three ways: capture unset with the span sampled in, capture on, and the span sampled out. The point rests on the
printed counts: with capture unset the span holds only references while the store holds the user's text, and with the
span sampled out nothing is exported and the store still fills. References are printed after the redactor has replaced
their folder. The store is a folder this example makes and removes."""
import lib  # lib first: threads and seeds are fixed before anything else

import re
import tempfile
from pathlib import Path

from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON

from lib.dayrun import RECORDINGS
from lib.redact import has_absolute_path, redact_text
from lib.report import fmt_int
from lib.scan import CONTENT_KEYS, hooked_calls, model_calls, print_hook_run

CALLS = model_calls(RECORDINGS["2026-12-08"])[:20]  # twenty of baseline day 1's model calls
USER_TEXTS = [next(m["content"] for m in reversed(c["request"]["messages"]) if m["role"] == "user") for c in CALLS]
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")  # the uploaded files' random names

with tempfile.TemporaryDirectory() as root:
    unset_spans, unset = hooked_calls(CALLS, ALWAYS_ON, None, Path(root) / "unset")
    print_hook_run("capture unset and sampled in", unset_spans, unset)
    on_spans, on = hooked_calls(CALLS, ALWAYS_ON, "SPAN_ONLY", Path(root) / "on")
    print_hook_run("capture on and sampled in", on_spans, on)
    out_spans, out = hooked_calls(CALLS, ALWAYS_OFF, None, Path(root) / "out")
    print_hook_run("capture unset and sampled out", out_spans, out)
    refs = [s.attributes[k] for s in unset_spans for k in s.attributes if k.endswith("_ref")]
    redacted = [redact_text(ref) for ref in refs]  # the redactor replaces each reference's folder
    print("reference form on the span, after redaction:", UUID.sub("<id>", redacted[0]))
    print("absolute paths left in the redacted references:", fmt_int(sum(has_absolute_path(r) for r in redacted)))
    held = sum(any(text in body for body in unset["inputs"]) for text in USER_TEXTS)
    print("calls sent through the hook:", fmt_int(len(CALLS)))
    print("calls whose user text is in an uploaded input file, capture unset:", fmt_int(held))

assert len(unset_spans) == len(CALLS) and len(on_spans) == len(CALLS)  # every call's span is exported when sampled in
assert all(any(k.endswith("_ref") for k in s.attributes) for s in unset_spans)  # the span holds a reference
assert not any(k in CONTENT_KEYS for s in unset_spans for k in s.attributes)  # and no inline content, capture unset
assert all(any(k in CONTENT_KEYS for k in s.attributes) for s in on_spans)  # capture on: the content is inline
assert len(out_spans) == 0 and len(out["inputs"]) == len(CALLS) and len(out["outputs"]) == len(CALLS)  # sampled out
assert held == len(CALLS)  # the store holds each call's user text, with capture unset
assert all(has_absolute_path(ref) for ref in refs) and not any(has_absolute_path(r) for r in redacted)
```

Output:

```text
spans exported, capture unset and sampled in: 20
spans with a content reference, capture unset and sampled in: 20
spans with inline content, capture unset and sampled in: 0
uploaded inputs, capture unset and sampled in: 20
uploaded outputs, capture unset and sampled in: 20
spans exported, capture on and sampled in: 20
spans with a content reference, capture on and sampled in: 20
spans with inline content, capture on and sampled in: 20
uploaded inputs, capture on and sampled in: 20
uploaded outputs, capture on and sampled in: 20
spans exported, capture unset and sampled out: 0
spans with a content reference, capture unset and sampled out: 0
spans with inline content, capture unset and sampled out: 0
uploaded inputs, capture unset and sampled out: 20
uploaded outputs, capture unset and sampled out: 20
reference form on the span, after redaction: file://<folder>/<id>_inputs.json
absolute paths left in the redacted references: 0
calls sent through the hook: 20
calls whose user text is in an uploaded input file, capture unset: 20
```

With capture unset, the span holds a reference and no content, and the store holds the user's text: 20 input files, one for each call. Capture on adds the content inline to each of the 20 spans as well. Sampling the span out keeps it from the exporter altogether, and the hook still uploads each call's inputs and outputs: 20 inputs and 20 outputs, with no span exported.

The hook therefore writes for a span that the exporter never sends. [Chapter 11](#retention) said that sampling decides which spans reach the backend, and not what the process does with the spans it drops. The third run shows that point in practice. Content goes to the store even when the trace it belongs to is sampled out.

The reference is a `file://` address with the upload folder in it, which is an absolute path on the machine that wrote the file, so a reader who finds an unredacted reference learns where the file sits on that machine. The redactor replaces the folder with a placeholder and keeps the scheme and the file name. The example prints the reference after redaction, and the number of redacted references that still name a folder is 0.

The hook is not a privacy control. With capture unset, 20 of the 20 calls had their user text in an uploaded input file. Moving the content moved it. The redactor does not reach the files, so the store needs its own access rules and its own retention, and the same care as the spans the content came from.

**Working rule:** Do not turn on the upload hook as a way to keep content out of spans. Turn it on only with a store that has its own access and retention rules, and check the store as carefully as the spans, including the spans that sampling drops. Where spans pass, rewrite a reference's machine path, or use a store address that holds no machine path.

## Count what redaction leaves {#scanning-and-counting}

The scanner counts three groups of kinds, and this chapter keeps them apart in every table and figure. The first group is the synthetic users' items: user IDs, user names and email addresses, which redaction must remove. The second is the stack trace, which [an earlier section](#stack-traces-leak-without-capture) covered. The third is MASSIVE's slot labels, the person, place, relation and other values the scanner finds in the captured text. The first group is asserted zero after redaction. The third is measured.

The split follows what each group allows. The redactor knows the synthetic items, since they come from the case's own lists and the `.example` domain, so it can remove them, and the example asserts that it does. The zero means something because the scanner looks for the case's own values, not for the patterns the redactor matches. The redactor cannot know which words in a request are a person's name, because the app does not have the dataset's labels. Asserting zero for the slot labels would need those labels. So the example counts them before and after redaction, and the residue is 55 person values after redaction.

Two slot labels need a further word. The English annotations in the slice the book ships give `email_address` no values at all, so its pattern matches nothing and its zero follows from that slice. `personal_info` has one annotated phrase, and the scanner finds none of it in the day's captured text. That zero is a measurement, which is why it appears in the residue and not as an assertion.

The next example draws the spans that hold each kind, before and after redaction, in two panels.

Example `figure-personal-items-before-after` (Python 3.13.16 · bm25s 0.3.16 · httpx 0.28.1 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · openai 3.58.0 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""How many spans of baseline day 1 hold each kind of personal item, before and after redaction, in two panels: the
synthetic users' items, which redaction removes, and MASSIVE's personal-looking values, which it cannot tell apart from
other words and so leaves. The figure's point rests on the printed counts: the top panel's bars drop to zero, and the
bottom panel's stay where they were."""
import lib  # lib first: threads and seeds are fixed before anything else

from lib.figures import ACCENT, MUTED, RULE, new_figure, save
from lib.report import fmt_int
from lib.scan import SLOT_LABELS, SYNTHETIC, assistant_rows, captured_day, spans_holding

DAY = "2026-12-08"
rows = assistant_rows(DAY) + captured_day(DAY)  # the day's spans, capture on for the package's
cleaned = assistant_rows(DAY, redact=True) + captured_day(DAY, redact=True)  # the same, through the processor
before, after = spans_holding(rows), spans_holding(cleaned)
for kind in SYNTHETIC + tuple(f"slot:{label}" for label in SLOT_LABELS):
    label = kind.replace("slot:", "") + (" slot" if kind.startswith("slot:") else "")
    print(f"{label} spans before redaction: {fmt_int(before[kind])}")
    print(f"{label} spans after redaction: {fmt_int(after[kind])}")
assert all(after[kind] == 0 for kind in SYNTHETIC)  # the synthetic users' spans are all clean after redaction
assert all(after[f"slot:{label}"] == before[f"slot:{label}"] for label in SLOT_LABELS)  # measured, not moved

top_kinds = list(SYNTHETIC)
bottom_kinds = [f"slot:{label}" for label in SLOT_LABELS]
fig, (top, bottom) = new_figure(rows=2, height=5.6, sharex=False)  # one x scale per panel: 200 and 55 do not share one


def panel(ax, kinds, title):
    """Before and after, as horizontal bars, with each count printed at the bar's end."""
    ys = list(range(len(kinds)))
    xmax = max(before[kind] for kind in kinds) * 1.3 or 1  # room for the count and the legend
    ax.barh([y - 0.18 for y in ys], [before[kind] for kind in kinds], height=0.34, color=MUTED,
            label="before redaction")
    ax.barh([y + 0.18 for y in ys], [after[kind] for kind in kinds], height=0.34, color=RULE, edgecolor=ACCENT,
            hatch="////", label="after redaction")  # hatched, so the two bars differ by pattern as well as colour
    for y, kind in zip(ys, kinds):
        ax.text(before[kind] + xmax * 0.01, y - 0.18, str(before[kind]), va="center", fontsize=7.5)
        ax.text(after[kind] + xmax * 0.01, y + 0.18, str(after[kind]), va="center", fontsize=7.5)
    ax.set_yticks(ys, [kind.replace("slot:", "") for kind in kinds])
    ax.invert_yaxis()
    ax.set_xlim(0, xmax)
    ax.set_title(title, loc="left", fontsize=9)


panel(top, top_kinds, "Synthetic users' items: redaction removes them")
panel(bottom, bottom_kinds, "MASSIVE's personal-looking values: counted, not removed")
bottom.set_xlabel("spans holding each kind, baseline day 1")
top.legend(loc="lower right", fontsize=7.5)
save(fig, "personal-items-before-after")
```

Output:

```text
user_id spans before redaction: 200
user_id spans after redaction: 0
user_name spans before redaction: 2
user_name spans after redaction: 0
email spans before redaction: 0
email spans after redaction: 0
person slot spans before redaction: 38
person slot spans after redaction: 38
place_name slot spans before redaction: 33
place_name slot spans after redaction: 33
relation slot spans before redaction: 25
relation slot spans after redaction: 25
email_address slot spans before redaction: 0
email_address slot spans after redaction: 0
personal_info slot spans before redaction: 0
personal_info slot spans after redaction: 0
figure: figures/personal-items-before-after.svg
```

Figure 12.1 draws the spans on baseline day 1 that hold each kind of item, before and after redaction, in two panels. The top panel's synthetic kinds fall to nothing after redaction. The bottom panel's personal-looking values keep the bars they had before, 38 spans for person values before redaction and 38 after it. Each panel has its own scale, so compare bars within a panel and not across the two. The figure counts spans and the scan counts items, so the bottom panel's bars are smaller than the scan's counts for the same kinds, and both stay the same before and after redaction. In each pair, the second bar is the count after redaction.

*Figure 12.1. Spans holding each kind of personal item, before and after redaction, in two panels.*

![The synthetic users' items fall to nothing after redaction, and the dataset's personal-looking values keep their bars before and after.](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.3/figures/personal-items-before-after.svg)

The 55 person values that redaction leaves measure how much of the request text the redactor cannot reach. That is a count of the redactor's reach, not of anyone's records, and a reader should not take it as one.

**Working rule:** Assert zero only for the kinds the redactor is built to remove, and print every other kind as a measure. A count the redactor cannot reach is a fact to report, and it does not count against the check that passed.

## Who may read what is left {#who-may-read-traces}

A trace that has been redacted still holds data, and who may read it matters as much as what the redactor removed. The rows that remain carry pseudonyms in place of user IDs, the slot values the redactor could not find, and any stack trace that a service wrote and no later step removed. [The content store](#keep-content-by-reference) holds the user's text whole. Reading a span is therefore a kind of reading personal data, even when the span holds no name.

We recommend giving each reader the rows their purpose needs. The people who answer an alert read the redacted rows, which carry the pseudonym, the route and the timing, and they do not need the content. The people who debug a named route may read the content, for the purpose named when capture was turned on, and for as long as that purpose lasts. The contacts team reads the spans of its own server, which it owns. Who reads which rows is enforced by the backend's access controls, and the book's receiver has none, so these rules hold only where the backend can restrict content attributes or the content store by role. We recommend a backend that can do that.

Keeping personal data out of a model's own context is a different job. In *Securing LLM Applications and Agents*, [hidden context](https://rollingedition.com/concepts/llm-security/hidden-context) is what a system prompt holds out of the user's view, such as secrets. This chapter is about what the telemetry holds after the model has run.

**Working rule:** Before you turn capture on, write down who may read the raw content, for what purpose and until when. Give every other reader the redacted rows, and apply the same rule to the content store.

## Keeping private data out in production {#keep-private-data-out-in-production}

The redaction in this chapter works on the case the book runs, and production differs in several ways. The redactor knows the case's names and matches them case-sensitively. Its address rule matches the `.example` domain. A real name or a real address passes straight through. The redactor also leaves the span's name, its resource, its links and its array values alone. A production team needs a detector for the data it holds, such as a [PII model](https://rollingedition.com/concepts/data-governance/pii-model) trained for personal data, and it should measure that detector's misses against labelled data, which this book does not have.

The stack-trace rule keys on one attribute name, `exception.stacktrace`. A traceback written under another name passes, and so does a path that appears in a message's text. The scanner counts stack traces as their own kind, so a team can count them after each release and see whether a new service has begun to write them.

The raw span also crosses the network before the receiver redacts it. The transport and the receiver's own logs hold the raw content for that moment, and they need the same care as the rest of the path. A receiver that redacts is safe only if nothing else on the path keeps what it received.

The pseudonym is only as private as its key. A key in the code, as this book uses, lets anyone who reads the code match candidate IDs, and a leaked key gives the same result. In production, draw the key as 32 random bytes from a secret store: [RFC 2104](https://www.rfc-editor.org/rfc/rfc2104#section-3) advises against an HMAC key shorter than the hash's output. Twelve hexadecimal digits suit the case's 200 users, but a large user base needs more digits, since at ten million users a shared pseudonym is no longer unlikely. Rotating the key starts every user's pseudonym again, so the change needs a plan.

The content store keeps the user's text whole, and its retention is its own. [Chapter 11](#retention) left the period to the team that runs the backend, and the store's period belongs to that team as well. A store with no period keeps the text for as long as it exists.

**Working rule:** After each release, run the scan on a day of traffic, and treat any kind that counts above zero after redaction as a finding until someone can say why it may remain. Count the stack traces and the items in the same scan, so that a new source of either shows up in one report.

## The decisions this chapter made {#keep-private-data-out-decisions}

A process can remove only what it writes, so each decision below puts its check where the output of every process lands.

- We keep content capture off in every service. Capture off still leaves a user ID on every message's root span, so the keyed pseudonym is part of the default and not an extra.
- We drop stack traces where every service's spans pass, which in this book is the receiver, and we recommend the same step in a production Collector. The contacts team should set `record_exception=False` on its lookup span, but we do not depend on that change to protect the data.
- We run redaction in each process for what that process writes, and again where every service's spans pass, and the stack traces show what that limit costs.
- We key the user pseudonyms with a secret that the telemetry's readers never hold. The demonstration key in the code shows the construction only.
- We keep content in a store only with access and retention rules of its own, since the upload hook writes whenever it is on, including for spans that sampling drops.
- We assert zero for the synthetic kinds that redaction removes, and we print the residue of the dataset's values as a measure of what the redactor cannot reach.
- We run the scan on every release's output, so that a new source of stack traces or items shows in one report.
