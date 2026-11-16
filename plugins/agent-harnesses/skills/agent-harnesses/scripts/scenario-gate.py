"""A scripted run on T-04 whose finish proposes a rename of an existing test. The gate holds the proposal as never, before
any person is asked, so the scripted yes is never used: the run ends as a handoff, and the library stays as it was."""
from lib.case import CASE
from lib.chapter1 import call
from lib.permissions import Gate, gated, library_copy, scripted
from lib.scenario import scripted_run
from lib.tasks import snapshot
from lib.tools import V1

replies = [
    call("edit_file", path="tests/test_format.py", old="def test_pads_to_two_places():",
         new="def test_pads_two_places():"),
    call("finish", summary="Rename a test."),
]
with library_copy() as library:
    gate = Gate(library, scripted((True, "")))
    run, done = scripted_run("T-04", replies, gated(V1, gate), case=library)
    for line in run.trace.lines():
        print(line)
    print("ended:", run.ended)
    print("handoff question:", run.question)
    print("held as never:", gate.counts["held as never"])
    print("asked:", gate.counts["asked"], "applied:", gate.counts["applied"])
    same = snapshot(library, ".") == snapshot(CASE, ".")
    print("library unchanged:", same)
    print("done:", done)
    assert run.ended == "ask_user" and gate.counts["asked"] == 0 and gate.counts["applied"] == 0
    assert run.question.startswith("p-1 was not applied") and not done and same
    run.close()
