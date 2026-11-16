"""A child loop on T-01 with a budget of 4 steps. The budget counts the child's own model calls, and it ends the child
as step_cap with no finish. The child's requests match the recording's first four steps, so they replay."""
from lib.case import load_tasks
from lib.models import ReplayModel
from lib.subagents import run_child
from lib.tools import V1
from lib.trace import IdCounter

BUDGET = 4
task = load_tasks(only=["T-01"])[0]
child = run_child(ReplayModel("task-set", "T-01"), task, V1, budget=BUDGET, ids=IdCounter())
print("child budget, steps:", BUDGET)
print("child steps:", child.handoff.steps)
print("child result:", child.handoff.ended)
print("child tools:", ", ".join(child.tool_names))
print("child steps, in order:", *child.trace, sep="\n  ")
child.run.close()
assert child.handoff.ended == "step_cap" and child.handoff.steps == BUDGET
