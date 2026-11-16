"""The chapter 1 recorded run of T-01 as JSON lines: one record per step, with run-scoped IDs and the recorded token
counts. The lines are written to a file and read back, and the reader counts the empty pieces it skips."""
import json
import tempfile
from pathlib import Path

from lib.case import load_tasks
from lib.loop import run_task
from lib.models import ReplayModel
from lib.tools import CH1
from lib.trace import IdCounter, StepRecorder, dumps, read_lines, step_records

task = load_tasks(only=["T-01"])[0]
model = StepRecorder(ReplayModel("chapter-1-t01", "T-01"))
run = run_task(model, task, CH1, max_steps=CH1.step_cap, ids=IdCounter())
records = step_records(run, model)
for record in records:
    print(dumps(record))
print("records:", len(records))
print("first call ID:", records[0]["calls"][0])
print("results:", ", ".join(f"step {r['step']} {r['result']}" for r in records))
print("prompt tokens, summed over the records:", sum(r["prompt_tokens"] for r in records))
print("completion tokens, summed over the records:", sum(r["completion_tokens"] for r in records))
try:
    json.loads("")  # a blank line is not a JSON value
except json.JSONDecodeError as error:
    print("blank line:", error)
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "trace.jsonl"
    path.write_text("".join(dumps(record) + "\n" for record in records), encoding="utf-8")
    read_back, skipped = read_lines(path.read_text(encoding="utf-8"))
print("lines read back:", len(read_back))
print("empty pieces skipped:", skipped)
assert read_back == records and skipped == 1  # the one piece after the last line feed
assert run.ended == "step_cap" and len(records) == CH1.step_cap and records[-1]["stop"] == "step_cap"
assert sum(r["prompt_tokens"] for r in records) == run.prompt_tokens
run.close()
