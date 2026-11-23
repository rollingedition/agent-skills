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
