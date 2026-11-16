"""The token counts of the task-set recording, summed per task and for the set, read from the stored counts. Replay
never tokenizes, so these are the counts the recording wrote; the live check against a tokenizer is not run."""
from lib.models import load_recording
from lib.trace import OTEL_TOKEN_FIELDS

manifest, rows = load_recording("task-set")  # rows: one per step, from replies.jsonl; the manifest has task totals
sums: dict[str, list[int]] = {}
for row in rows:
    total = sums.setdefault(row["run"], [0, 0, 0])
    total[0] += row["prompt_tokens"]
    total[1] += row["completion_tokens"]
    total[2] += 1  # each row is one step, so the third sum counts steps
for task in sorted(manifest["tasks"], key=lambda t: t["task"]):
    prompt, completion, steps = sums[task["task"]]
    print(f"{task['task']} prompt tokens: {prompt} completion tokens: {completion} steps: {steps}")
    assert (prompt, completion, steps) == (task["prompt_tokens"], task["completion_tokens"], task["steps"])
set_prompt = sum(total[0] for total in sums.values())
set_completion = sum(total[1] for total in sums.values())
print("set tasks:", len(sums))
print("set prompt tokens:", set_prompt)
print("set completion tokens:", set_completion)
print("live count check: not run")
for field, name in sorted(OTEL_TOKEN_FIELDS.items()):  # the mapping table; the book's own names stay in the trace
    print(f"field {field} would map to {name} (data only; OpenTelemetry is not used)")
assert set_prompt == sum(t["prompt_tokens"] for t in manifest["tasks"])
