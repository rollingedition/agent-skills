"""A proposal of two files where the second cannot be written, because a folder stands where it goes. The first file
is put back, the error goes back as the handoff, and the library holds the bytes it held before the finish."""
from lib.case import CASE
from lib.permissions import Gate, answer, gated, library_copy
from lib.tasks import snapshot
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    (library / "unitcraft" / "extra.py").mkdir()
    before = snapshot(library, ".")
    (scratch / "README.md").write_text("A new line in the readme.\n", encoding="utf-8")
    (scratch / "unitcraft" / "extra.py").write_text('"""Extra."""\nTOTAL = 1\n', encoding="utf-8")
    gate = Gate(library, lambda p: answer(p, True))
    result = gated(V1, gate).call(Workspace(scratch), "finish", {"summary": "Two files."})
    print("ended:", result.end)
    print("handoff:", result.question)
    print("README as before:", snapshot(library, "README.md") == snapshot(CASE, "README.md"))
    print("library bytes unchanged:", snapshot(library, ".") == before)
    print("applied:", gate.counts["applied"], "refused:", gate.counts["refused"])
    assert result.end == "ask_user" and "apply failed (IsADirectoryError)" in result.question
    assert snapshot(library, ".") == before and gate.counts["applied"] == 0
