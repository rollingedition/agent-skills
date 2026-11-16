"""T-02's recorded run as a child, with both stop rules and the task set's step cap. The parent gets the
handoff's fields and not the child's transcript; the example prints the size of each."""
from lib.case import load_tasks
from lib.loop import Stops
from lib.models import ReplayModel
from lib.subagents import characters, run_child, tokens
from lib.tools import V1
from lib.trace import IdCounter

RULES = Stops(repeat_limit=3, no_progress_limit=2)
task = load_tasks(only=["T-02"])[0]
ids = IdCounter()
ids.next("run")  # the recording numbers its runs in task order, so T-02 is run-0002: skip T-01's number
child = run_child(ReplayModel("task-set", "T-02"), task, V1, budget=V1.step_cap, ids=ids, stops=RULES)
h = child.handoff
print("child result:", h.ended, "at step", h.steps, "of", h.budget)
print("transcript messages:", len(child.transcript))
print("child transcript, characters:", characters(child.transcript))
print("child transcript, estimated tokens:", tokens(characters(child.transcript)))
print("parent receives, characters:", len(h.text))
print("parent receives, estimated tokens:", tokens(len(h.text)))
print("saved by the handoff, characters:", characters(child.transcript) - len(h.text))
print("what the parent receives:")
print(h.text)
child.run.close()
assert task.issue not in h.text and len(h.text) < characters(child.transcript)
