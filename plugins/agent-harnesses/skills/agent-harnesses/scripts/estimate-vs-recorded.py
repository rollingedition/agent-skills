"""The estimate of each recorded request against the prompt count the model reported for it. The rule was chosen on
task-set; chapter-5-notes was recorded after the rule was fixed, so its lines are the held-out check. The point rests
on the steps below the recorded count: none, in either recording."""
import json

from lib.case import load_tasks
from lib.context import CHARS_PER_TOKEN, PROMPT_BUDGET, Measured, Notes, characters, estimate, notes_toolset
from lib.loop import Stops, run_task
from lib.models import RECORDED, ReplayModel
from lib.tools import V1
from lib.trace import IdCounter


def replay(recording, tasks, tools, **limits):
    """Every request the recorded runs sent: its messages, its tool schemas and the count the model reported."""
    ids, requests = IdCounter(), []  # the replay rebuilds each request, so each estimate sees the messages the model saw
    for task in tasks:
        model = Measured(ReplayModel(recording, task.id))
        run_task(model, task, tools, ids=ids, **limits).close()
        requests += model.requests
    return requests


def report(name, requests):
    """Prints the comparison of the estimate with the count, labelled with the recording's name, and returns the pairs."""
    pairs = [(estimate(m, t), n) for m, t, n in requests]
    print(f"{name} steps compared:", len(pairs))
    print(f"{name} characters per token, recorded (all steps):",
          f"{sum(characters(m, t) for m, t, _ in requests) / sum(n for _, n in pairs):.2f}")
    print(f"{name} steps where the estimate is above the recorded count:", sum(e > n for e, n in pairs))
    print(f"{name} steps where the estimate is below the recorded count:", sum(e < n for e, n in pairs))
    print(f"{name} lowest estimate divided by the recorded count: {min(e / n for e, n in pairs):.2f}")
    print(f"{name} highest estimate divided by the recorded count: {max(e / n for e, n in pairs):.2f}")
    assert all(e >= n for e, n in pairs), f"{name}: the rule should never count fewer tokens than the model did"
    return pairs


manifest = json.loads((RECORDED / "chapter-5-notes" / "manifest.json").read_text(encoding="utf-8"))
assert manifest["context"]["chars_per_token"] == CHARS_PER_TOKEN, "the held-out recording used the same rule"
print(f"estimate rule, characters per token: {CHARS_PER_TOKEN}")
task_set = replay("task-set", load_tasks(), V1, max_steps=V1.step_cap)
pairs = report("task-set", task_set)
# four is the rule a reader would try first: it is the one the comparison is against
print("task-set with 4 characters per token, steps below the recorded count:",
      sum(estimate(m, t, 4) < n for m, t, n in task_set))
print("task-set steps whose estimate is over the prompt budget:", sum(e > PROMPT_BUDGET for e, _ in pairs))
print("of those, steps whose recorded count is within the budget:",
      sum(e > PROMPT_BUDGET and n <= PROMPT_BUDGET for e, n in pairs))
report("held-out", replay("chapter-5-notes", load_tasks(only=["T-01", "T-02", "T-06"]), notes_toolset(Notes()),
                          max_steps=16, stops=Stops(repeat_limit=3, no_progress_limit=2)))
