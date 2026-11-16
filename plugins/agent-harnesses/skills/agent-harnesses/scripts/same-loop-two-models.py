"""Chapter-1-t01 runs through the loop twice: once with a ScriptedModel holding the stored reply texts, once with a
ReplayModel. The assert compares the two runs' step lines, and the lines printed below are the replayed run's."""
import json

from lib.case import load_tasks
from lib.loop import run_task
from lib.models import RECORDED, ReplayModel, ScriptedModel
from lib.tools import CH1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]
rows = [json.loads(line) for line in (RECORDED / "chapter-1-t01" / "replies.jsonl").read_text(encoding="utf-8").splitlines()]


def run_once(model):
    run = run_task(model, task, CH1, max_steps=CH1.step_cap, ids=IdCounter())  # counter-based IDs, never random (P-3)
    try:
        return list(run.trace.lines()), run.steps, run.ended
    finally:
        run.close()


scripted = run_once(ScriptedModel([row["text"] for row in rows]))
replayed = run_once(ReplayModel("chapter-1-t01", "T-01"))
assert scripted == replayed, "the two adapters gave the loop different steps"
lines, steps, ended = replayed
for line in lines:
    print(line)
print(f"steps: {steps}")
print(f"ended: {ended}")
