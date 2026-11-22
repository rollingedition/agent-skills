"""Each recorded run's prompt tokens at every step, against the prompt budget. The point rests on the largest prompt line
and the budget line: the prompts climb at every step, and the largest one sits under the budget, close to it."""
import json

from lib.context import PROMPT_BUDGET, REPLY, WINDOW
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.models import RECORDED

folder = RECORDED / "task-set"
manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
steps = [json.loads(line) for line in (folder / "replies.jsonl").read_text(encoding="utf-8").splitlines()]
assert manifest["n_ctx"] == WINDOW and manifest["max_tokens"] == REPLY, "the budget comes from the recorded load settings"

runs = {}  # run id -> its prompt counts, in step order
for step in sorted(steps, key=lambda s: (s["run"], s["step"])):
    runs.setdefault(step["run"], []).append(step["prompt_tokens"])
# ties go to the later run and step, so the same step is named on every run
largest = max(steps, key=lambda s: (s["prompt_tokens"], s["run"], s["step"]))
# each step carries the whole history, so a run's prompt should grow at every step
rising = sum(all(b > a for a, b in zip(counts, counts[1:])) for counts in runs.values())
cap = max(len(counts) for counts in runs.values())  # the x axis runs to the longest run in the recording
print("prompt budget, in tokens:", PROMPT_BUDGET)
print("runs drawn:", len(runs))
print("runs whose prompt rises at every step:", rising)
print("largest prompt, in tokens:", largest["prompt_tokens"])
print("largest prompt, run:", largest["run"])
print("largest prompt, step:", largest["step"])

fig, ax = new_figure(height=3.2)
others = [run for run in runs if run != largest["run"]]
for run in others:  # one legend entry names the group: the lines are told apart by their place, not by colour
    ax.plot(range(1, len(runs[run]) + 1), runs[run], color=MUTED, linestyle="-", linewidth=1.0,
            label=f"the other {len(others)} runs" if run == others[0] else None)
ax.plot(range(1, len(runs[largest["run"]]) + 1), runs[largest["run"]], color=ACCENT, linestyle="-", marker="o",
        markersize=3.5, linewidth=1.8, label=f"{largest['run']}, the largest prompt")
ax.axhline(PROMPT_BUDGET, color=INK, linestyle="--", linewidth=1.2, label=f"prompt budget, {PROMPT_BUDGET} tokens")
ax.set_xlabel("step of the run, counting from 1")
ax.set_ylabel("prompt, in tokens")
ax.set_xlim(0.5, cap + 0.5)
ax.set_xticks(range(1, cap + 1, 3))
ax.set_ylim(0, WINDOW)
ax.legend(frameon=False, loc="lower right")
save(fig, "prompt-per-step")

