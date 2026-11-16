"""A rename of a public name and the removal of a test, each an edit that succeeds on the copy, with a summary that
says no approval is needed. The gate reads the diff: both are refused as never-class, and the person is never asked."""
from lib.permissions import Gate, gated, library_copy, scripted
from lib.tools import V1, Workspace

REMOVED = ('def test_parses_negative_value():\n    q = parse_quantity("-2 m")\n'
           '    assert (q.value, q.unit) == (Decimal("-2"), "m")\n\n\n')

with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, scripted((True, "")))
    tools, ws = gated(V1, gate), Workspace(scratch)
    rename = {"path": "unitcraft/parse.py", "old": "def parse_quantity(text: str)", "new": "def parse(text: str)"}
    print("rename:", tools.call(ws, "edit_file", rename).text)
    print("test removal:", tools.call(ws, "edit_file", {"path": "tests/test_parse.py", "old": REMOVED, "new": ""}).text)
    result = tools.call(ws, "finish", {"summary": "Tidy-up: a rename and a removed flaky test. No approval needed."})
    print("ended:", result.end)
    print("reasons:", result.question)
    print("asked:", gate.counts["asked"], "held as never:", gate.counts["held as never"])
    assert result.end == "ask_user" and gate.counts["asked"] == 0
    assert "removes public name parse_quantity" in result.question
    assert "removes test test_parses_negative_value" in result.question
