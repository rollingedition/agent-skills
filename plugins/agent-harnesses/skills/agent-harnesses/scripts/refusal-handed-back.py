"""The recorded T-04 run with the gate and a scripted no. The refusal is the step's tool result, the run ends as a
handoff whose question is that refusal, and the library stays as it was."""
from lib.case import CASE, load_tasks
from lib.loop import run_task
from lib.models import ReplayModel
from lib.permissions import Gate, gated, library_copy, replay_ids, scripted
from lib.tasks import snapshot
from lib.tools import V1

task = load_tasks(only=["T-04"])[0]
with library_copy() as library:
    gate = Gate(library, scripted((False, "the inch belongs in a later change")))
    run = run_task(ReplayModel("task-set", "T-04"), task, gated(V1, gate), max_steps=V1.step_cap,
                   ids=replay_ids("T-04"), case=library)
    print("ended:", run.ended)
    print("last step:", run.trace.lines()[-1])
    print("handoff question:", run.question)
    print("refused:", gate.counts["refused"], "applied:", gate.counts["applied"])
    unchanged = snapshot(library, ".") == snapshot(CASE, ".")
    print("library unchanged:", unchanged)
    assert run.ended == "ask_user" and run.question.startswith("p-1 was not applied") and unchanged
    run.close()
