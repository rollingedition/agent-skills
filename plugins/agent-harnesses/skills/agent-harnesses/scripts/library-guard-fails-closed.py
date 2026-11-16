"""A test module written into the copy makes run_tests write the library. The guard sees the library's bytes change
around the run_tests call and ends the run as library_changed. It reports the file and restores nothing."""
from lib.permissions import Gate, gated, library_copy, scripted
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    marker = library / "unitcraft" / "marker.py"
    test_module = ("from pathlib import Path\n"
                   f"Path({str(marker)!r}).write_text('MARK = 1\\n', encoding='utf-8')\n")
    gate = Gate(library, scripted())
    tools, ws = gated(V1, gate), Workspace(scratch)
    print("write test module:", tools.call(ws, "write_file", {"path": "tests/test_marker.py", "text": test_module}).text)
    result = tools.call(ws, "run_tests", {})
    print("run_tests ended:", result.end)
    print("handoff:", result.question)
    print("marker written:", marker.exists(), "| library changes counted:", gate.counts["library changed"])
    print("proposals:", gate.counts["proposals"])
    assert result.end == "library_changed" and marker.exists() and "unitcraft/marker.py" in result.question
    assert gate.counts["proposals"] == 0
