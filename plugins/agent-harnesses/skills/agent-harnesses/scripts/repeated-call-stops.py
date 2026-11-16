"""The recorded run of T-02 with and without the repeated-call rule. Three identical calls in a row end the run as
repeated_call. The rule compares the name and the sorted arguments, so reordered keys still count as the same call."""
from lib.case import load_tasks
from lib.loop import Stops, run_task
from lib.models import ReplayModel
from lib.tools import V1
from lib.trace import IdCounter

task = load_tasks(only=["T-02"])[0]


def replay(stops: Stops):
    ids = IdCounter()
    ids.next("run")  # the recording numbers its runs in task order, so T-02 is run-0002: skip T-01's number
    return run_task(ReplayModel("task-set", "T-02"), task, V1, max_steps=V1.step_cap, ids=ids, stops=stops)


plain = replay(Stops())
print("without the rule, ended:", plain.ended, "at step", plain.steps)
run = replay(Stops(repeat_limit=3))
print("with the rule, ended:", run.ended, "at step", run.steps)
print("repeated call:", run.stuck_on)
print("first of the identical calls: step", run.streak_from)
print("identical calls in a row:", run.steps - run.streak_from + 1)
print("last two steps:", *run.trace.lines()[-2:], sep="\n  ")
assert run.ended == "repeated_call" and run.streak_from == 11 and run.steps == 13
