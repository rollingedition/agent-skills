"""The context the harness loads the model with, the room the reply keeps, and each run's largest prompt against them.
The point rests on the line of steps over the prompt budget: no recorded step reached it."""
import json

from lib.context import PROMPT_BUDGET, REPLY, WINDOW
from lib.models import RECORDED

folder = RECORDED / "task-set"
manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
steps = [json.loads(line) for line in (folder / "replies.jsonl").read_text(encoding="utf-8").splitlines()]
assert manifest["n_ctx"] == WINDOW and manifest["max_tokens"] == REPLY, "the budget comes from the recorded load settings"

print("load setting, n_ctx, in tokens:", WINDOW)  # the harness's own load setting, not the model's native length
print("reply reservation, max_tokens, in tokens:", REPLY)
print("prompt budget, in tokens:", PROMPT_BUDGET)
print("steps recorded:", len(steps))
# ties go to the later run and step, so the same step is named on every run
largest = max(steps, key=lambda s: (s["prompt_tokens"], s["run"], s["step"]))
print("largest prompt, in tokens:", largest["prompt_tokens"])
print("largest prompt, run:", largest["run"])
print("largest prompt, step:", largest["step"])
print("room left for the reply at the largest step:", WINDOW - largest["prompt_tokens"] - REPLY)
print("steps over the prompt budget:", sum(s["prompt_tokens"] > PROMPT_BUDGET for s in steps))
for task in sorted(manifest["tasks"], key=lambda t: t["task"]):
    mine = [s["prompt_tokens"] for s in steps if s["run"] == task["task"]]
    print(f"{task['task']}: steps {len(mine)}, largest prompt {max(mine)}")
    assert len(mine) == task["steps"], "the stored step count must match the replies"
