"""The v1 and v2 recordings of the same 20 tasks, as counts: each task's done flag, ending, steps, tool calls and tokens,
then the totals, the step cap, the count with T-18's path match taken out, and the step differences. The counts are
printed as stored, with no winner and no cause given. It reads the task-set and task-set-v2 recordings (plan section 17).
The stricter count changes no score; see lib/tasks.py stop_reason_outside_paths."""
from collections import Counter

from lib.case import load_tasks
from lib.models import load_recording
from lib.tasks import stored_done_without_path, stored_question

NAMES = ("task-set", "task-set-v2")
TASKS = {t.id: t for t in load_tasks()}
loaded = {name: load_recording(name) for name in NAMES}
runs = {name: {row["task"]: row for row in manifest["tasks"]} for name, (manifest, _) in loaded.items()}
v1, v2 = runs["task-set"], runs["task-set-v2"]
assert len(v1) == len(v2) == 20 and list(v1) == list(v2), "both recordings cover the same 20 tasks"
assert all(v1[t]["check_sha256"] == v2[t]["check_sha256"] for t in v1), "the hidden checks are the same"


def text(row: dict) -> str:
    return (f"done {'yes' if row['done'] else 'no'}, ended {row['ended']}, steps {row['steps']}, "
            f"tool calls {row['tool_calls']}, prompt tokens {row['prompt_tokens']}, "
            f"completion tokens {row['completion_tokens']}")


for task in v1:
    print(f"{task} {v1[task]['kind']} v1: {text(v1[task])}")
    print(f"{task} {v1[task]['kind']} v2: {text(v2[task])}")
for name in NAMES:
    rows = list(runs[name].values())
    print(f"{name} step cap: {loaded[name][0]['step_cap']}")
    print(f"{name} done by the rule: {sum(r['done'] for r in rows)} of 20")
    print(f"{name} done without T-18's path match: "
          f"{sum(stored_done_without_path(TASKS[t], row, loaded[name][1]) for t, row in runs[name].items())} of 20")
    print(f"{name} steps: {sum(r['steps'] for r in rows)}")
    print(f"{name} tool calls: {sum(r['tool_calls'] for r in rows)}")
    print(f"{name} prompt tokens: {sum(r['prompt_tokens'] for r in rows)}")
    print(f"{name} completion tokens: {sum(r['completion_tokens'] for r in rows)}")
    for ended, count in sorted(Counter(r["ended"] for r in rows).items()):
        print(f"{name} ended {ended}: {count}")
diff = {task: v2[task]["steps"] - v1[task]["steps"] for task in v1}
print("tasks where version 2 takes more steps:", ", ".join(f"{t} +{d}" for t, d in diff.items() if d > 0) or "none")
print("tasks where version 2 takes fewer steps:", sum(d < 0 for d in diff.values()))
print("tasks where the step counts match:", sum(d == 0 for d in diff.values()))
assert stored_question(loaded["task-set"][1], "T-18") and stored_question(loaded["task-set-v2"][1], "T-18")
