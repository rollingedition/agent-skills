"""The decision table for chapter 12: every task in the set, with the author's readings (judgement, not measured), the
design the rules give, and how the task's recorded run ended. The counts at the end are the ones the chapter quotes.
No model is called."""
import json

from lib.models import RECORDED, load_recording
from lib.pipeline import ONE_CALL_SHAPE, REFUSED, TASK_SHAPES, design

yes_no = {True: "yes", False: "no"}
manifest, _ = load_recording("task-set")
stored = {row["task"]: row for row in manifest["tasks"]}
replies = [json.loads(line) for line in
           (RECORDED / "task-set" / "replies.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

print("task | steps known | exploration | wrong change | auto check | person | design | recorded ended | recorded done")
for task_id, s in TASK_SHAPES.items():
    rec = stored[task_id]
    print(f"{task_id} | {yes_no[s.steps_known]} | {yes_no[s.exploration]} | {s.wrong_change} | "
          f"{yes_no[s.auto_check]} | {yes_no[s.person]} | {design(s)} | {rec['ended']} | {yes_no[rec['done']]}")

pipelines = [t for t, s in TASK_SHAPES.items() if design(s) == "fixed pipeline"]
agents = [t for t, s in TASK_SHAPES.items() if design(s) == "agent with gates"]
refused = [t for t, s in TASK_SHAPES.items() if design(s) == REFUSED]
print(f"rows with design 'fixed pipeline': {len(pipelines)}")
print(f"rows with design 'agent with gates': {len(agents)}")
print(f"rows with design 'one model call': {sum(design(s) == 'one model call' for s in TASK_SHAPES.values())}")
print(f"rows the harness refuses: {len(refused)}")
print(f"pipeline rows the recorded agent finished and passed: "
      f"{sum(stored[t]['ended'] == 'finish' and stored[t]['done'] for t in pipelines)}")
print(f"agent rows the recorded agent finished and passed: "
      f"{sum(stored[t]['ended'] == 'finish' and stored[t]['done'] for t in agents)}")
print(f"rows done in the recording: {sum(stored[t]['done'] for t in TASK_SHAPES)}")
print(f"one-call shape, not in the set: {design(ONE_CALL_SHAPE)}")
print(f"largest request in the recording, prompt tokens: {max(r['prompt_tokens'] for r in replies)}")
print(f"context window in the recording, tokens: {manifest['n_ctx']}")

assert pipelines == ["T-01", "T-02", "T-03", "T-04", "T-05", "T-10", "T-12", "T-14", "T-20"]
assert design(ONE_CALL_SHAPE) == "one model call"
assert refused == ["T-16", "T-18"]
assert max(r["prompt_tokens"] for r in replies) < manifest["n_ctx"]
