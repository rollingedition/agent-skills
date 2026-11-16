"""The cost of the task-set runs as counts only: steps, tool calls and tokens, summed per way a run ended. The cost is
tokens, never money, and the tokens are the recording's stored counts; the groups are sorted, so the output is stable."""
from lib.models import load_recording

manifest, rows = load_recording("task-set")
tasks = sorted(manifest["tasks"], key=lambda t: (t["task"], t["kind"]))
for ending in sorted({t["ended"] for t in tasks}):
    group = [t for t in tasks if t["ended"] == ending]
    print(f"ended {ending}: runs {len(group)}, done {sum(t['done'] for t in group)}, "
          f"steps {sum(t['steps'] for t in group)}, tool calls {sum(t['tool_calls'] for t in group)}, "
          f"prompt tokens {sum(t['prompt_tokens'] for t in group)}, "
          f"completion tokens {sum(t['completion_tokens'] for t in group)}")
    print("  tasks:", ", ".join(t["task"] for t in group))
    print("  done:", ", ".join(t["task"] for t in group if t["done"]) or "none")
print(f"all: runs {len(tasks)}, done {sum(t['done'] for t in tasks)}, steps {sum(t['steps'] for t in tasks)}, "
      f"tool calls {sum(t['tool_calls'] for t in tasks)}, prompt tokens {sum(t['prompt_tokens'] for t in tasks)}, "
      f"completion tokens {sum(t['completion_tokens'] for t in tasks)}")
capped = [t for t in tasks if t["ended"] == "step_cap"]
print(f"step-capped runs done: {sum(t['done'] for t in capped)} of {len(capped)}")
print(f"step-capped runs, steps: {sum(t['steps'] for t in capped)} of {sum(t['steps'] for t in tasks)}")
print(f"step-capped runs, prompt tokens: {sum(t['prompt_tokens'] for t in capped)} of "
      f"{sum(t['prompt_tokens'] for t in tasks)}")
prompts: dict[str, list[int]] = {}
for row in sorted(rows, key=lambda r: (r["run"], r["step"])):  # the stored step rows, in step order
    prompts.setdefault(row["run"], []).append(row["prompt_tokens"])
rising = [t["task"] for t in capped if all(b > a for a, b in zip(prompts[t["task"]], prompts[t["task"]][1:]))]
print(f"step-capped runs whose prompt count rises at every step: {len(rising)} of {len(capped)}")
assert all(t["tool_calls"] == t["steps"] for t in tasks), "one tool call per step in this recording"
