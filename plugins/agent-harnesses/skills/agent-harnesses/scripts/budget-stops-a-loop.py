"""The chapter 1 recorded run of T-01 under its step budget of 8. The budget ends the run as step_cap, with no finish;
the last line shows the model's final step, a call the harness refused, and the budget ended the run after it."""
from lib.case import load_tasks
from lib.loop import run_task
from lib.models import ReplayModel
from lib.tools import CH1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]
run = run_task(ReplayModel("chapter-1-t01", "T-01"), task, CH1, max_steps=CH1.step_cap, ids=IdCounter())
print("budget (steps):", CH1.step_cap)
print("steps:", run.steps)
print("tool calls:", run.tool_calls)
print("ended:", run.ended)
print("last step:", run.trace.lines()[-1])
assert run.ended == "step_cap" and run.steps == CH1.step_cap, "the budget should stop the run on step 8"
assert not run.summary, "a budget stop carries no summary"
