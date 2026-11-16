"""The recorded run of T-01 under the no-progress rule. Two edits in a row that leave the test counts where they
were end the run as no_progress. The counts come from the harness's own run of the visible tests after each edit."""
from lib.case import load_tasks
from lib.loop import EDITS, Stops, run_task
from lib.models import ReplayModel
from lib.tools import V1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]


def replay(stops: Stops):
    return run_task(ReplayModel("task-set", "T-01"), task, V1, max_steps=V1.step_cap, ids=IdCounter(), stops=stops)


plain = replay(Stops())
print("without the rule, ended:", plain.ended, "at step", plain.steps)
run = replay(Stops(no_progress_limit=2))
print("with the rule, ended:", run.ended, "at step", run.steps)
edit_steps = [r["step"] for r in run.trace.records if r["tool"] in EDITS]
print("edits that left the counts unchanged, steps:", " and ".join(str(step) for step in edit_steps[-2:]))
print("counts after the last edit:", run.counts)
print("last two steps:", *run.trace.lines()[-2:], sep="\n  ")
assert run.ended == "no_progress" and run.steps == 5
