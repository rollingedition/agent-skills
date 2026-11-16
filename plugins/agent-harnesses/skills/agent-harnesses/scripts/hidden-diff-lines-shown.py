"""Two files whose text would hide a line in a terminal: a carriage return that overwrites the line before it, and an
escape that erases a line. The proposal shows both written out, so every line the person reads is in the file."""
from lib.permissions import Gate, answer, gated, library_copy
from lib.tools import V1, Workspace

CR = "HIDDEN_CR = 'not shown'\r# a comment long enough to cover the line before it\n"
ESC = "HIDDEN_ESC = 'not shown'\n\x1b[1A\x1b[2K# tidy\n"
seen = []


def person(proposal):
    seen.append(proposal)
    return answer(proposal, False, "not this change")


with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, person)
    tools, ws = gated(V1, gate), Workspace(scratch)
    tools.call(ws, "write_file", {"path": "unitcraft/a_cr.py", "text": CR})
    tools.call(ws, "write_file", {"path": "unitcraft/b_esc.py", "text": ESC})
    tools.call(ws, "finish", {"summary": "Add two comment-only modules."})
    shown = seen[0].diff
    for line in (ln for ln in shown.splitlines() if "HIDDEN" in ln):
        print("shown:", line)
    print("headers that flag control characters:", shown.count("contains control characters"))
    print("raw CR or ESC in the shown text:", sum(ch in shown for ch in "\r\x1b"))
    print("applied:", gate.counts["applied"], "refused:", gate.counts["refused"])
    assert "\r" not in shown and "\x1b" not in shown and shown.count("contains control characters") == 2
    assert gate.counts["applied"] == 0
