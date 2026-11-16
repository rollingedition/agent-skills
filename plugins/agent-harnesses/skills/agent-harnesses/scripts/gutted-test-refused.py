"""An edit that keeps an existing test's name and removes its assertion is a change to a test file, and the harness
refuses it without asking. A new test module is not refused for that reason."""
from lib.permissions import Change, Gate, assess, gated, library_copy, scripted
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, scripted((True, "")))
    tools, ws = gated(V1, gate), Workspace(scratch)
    edit = {"path": "tests/test_parse.py", "old": '    assert (q.value, q.unit) == (Decimal("-2"), "m")',
            "new": "    assert True"}
    print("edit:", tools.call(ws, "edit_file", edit).text)
    result = tools.call(ws, "finish", {"summary": "Make the negative-value test pass."})
    print("ended:", result.end)
    print("reasons:", result.question)
    print("asked:", gate.counts["asked"], "held as never:", gate.counts["held as never"])
    new_module = assess(library, scratch, [Change("tests/test_new.py", None, b"def test_ok():\n    pass\n")])
    print("new test module reasons:", new_module)
    assert result.end == "ask_user" and gate.counts["asked"] == 0
    assert "changes the test file tests/test_parse.py" in result.question and new_module == []
