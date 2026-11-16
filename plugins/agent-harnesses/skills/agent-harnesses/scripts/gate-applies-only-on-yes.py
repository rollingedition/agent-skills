"""The recorded T-04 run (add the inch) with the gate and a scripted yes: its one changed file reaches the library, and
the hidden check fails before the apply and passes after it. The second part shows two yeses that cannot apply: a copy
that changed after the person looked, and an answer that names another proposal."""
from lib.case import load_tasks
from lib.permissions import Answer, Gate, gated, library_copy, replay_task, scripted
from lib.tasks import hidden_check_passes
from lib.tools import V1, Workspace

task = load_tasks(only=["T-04"])[0]
with library_copy() as library:
    assert not hidden_check_passes(task, library)
    gate = Gate(library, scripted((True, "")))
    run = replay_task("T-04", gate, library)
    print("ended:", run.ended)
    print("proposals:", gate.counts["proposals"], "asked:", gate.counts["asked"])
    print("applied:", gate.counts["applied"], "files applied:", gate.counts["files applied"])
    print("visible tests after the apply:", Workspace(library).run_tests().splitlines()[0])
    print("hidden check after the apply:", hidden_check_passes(task, library))
    assert run.ended == "finish" and gate.counts["applied"] == 1 and hidden_check_passes(task, library)
    run.close()

with library_copy() as library, library_copy() as scratch:
    ws = Workspace(scratch)
    (scratch / "unitcraft" / "extra.py").write_text('"""Extra."""\nTOTAL = 1\n', encoding="utf-8")

    def drift(proposal):  # the copy changes in the window between the person's yes and the apply
        (scratch / "unitcraft" / "extra.py").write_text('"""Extra."""\nTOTAL = 2\n', encoding="utf-8")
        return Answer(True, proposal.id, proposal.sha256)

    late = gated(V1, Gate(library, drift)).call(ws, "finish", {"summary": "Add a constant."})
    print("drifted copy, handoff:", late.question)
    wrong = gated(V1, Gate(library, lambda p: Answer(True, "p-7", p.sha256)))
    print("answer for another proposal, handoff:", wrong.call(ws, "finish", {"summary": "Add a constant."}).question)
    assert late.end == "ask_user" and "changed after" in late.question
    assert not (library / "unitcraft" / "extra.py").exists()
