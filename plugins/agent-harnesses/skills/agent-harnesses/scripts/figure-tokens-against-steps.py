"""Each recorded run as one point: its steps against its prompt tokens, summed over the run, marked by how it ended.
The point rests on the step-capped runs sitting in one column at the cap, above every other run, and on the dashed
line for steps alone: every run's prompt total sits above it, because each step's prompt carries the steps before it."""
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.models import load_recording

manifest, rows = load_recording("task-set")
tasks = sorted(manifest["tasks"], key=lambda t: (t["steps"], t["task"]))  # ties in steps are broken by task ID
cap = manifest["step_cap"]
capped = [t for t in tasks if t["ended"] == "step_cap"]
others = [t for t in tasks if t["ended"] != "step_cap"]
assert all(t["steps"] == cap for t in capped), "a step-capped run stops at the cap"
assert min(t["prompt_tokens"] for t in capped) > max(t["prompt_tokens"] for t in others)
assert sum(r["step"] == 1 for r in rows) == len(tasks), "one first step per run"
first = sum(r["prompt_tokens"] for r in rows if r["step"] == 1) / len(tasks)  # the mean first-step prompt, in tokens
assert all(t["prompt_tokens"] > t["steps"] * first for t in tasks), "every run sits above steps times the first prompt"


def share(key):  # the step-capped runs' part of the whole set, in per cent
    return 100 * sum(t[key] for t in capped) / sum(t[key] for t in tasks)


def per_step(group):  # prompt tokens a step, over a group of runs
    return sum(t["prompt_tokens"] for t in group) // sum(t["steps"] for t in group)


fig, ax = new_figure(height=3.2)
for ending, color, marker, words in (("finish", INK, "o", "ended with a finish"), ("ask_user", MUTED, "s", "asked the person"), ("step_cap", ACCENT, "D", "hit the step cap")):
    group = [t for t in tasks if t["ended"] == ending]  # hollow, so two runs at one spot show as two rings
    ax.scatter([t["steps"] for t in group], [t["prompt_tokens"] for t in group], facecolors="none", edgecolors=color,
               marker=marker, s=30, linewidths=1.2, label=f"{words}, {len(group)} runs")
ax.plot([tasks[0]["steps"], cap], [tasks[0]["steps"] * first, cap * first], color=INK, linestyle="--", linewidth=1.0,  # tasks[0] took the fewest
        label="every step at the first step's prompt")
ax.set_xlabel("steps the run took")
ax.set_ylabel("prompt tokens, summed over its steps")
ax.set_xlim(tasks[0]["steps"] - 1, cap + 1)
ax.set_ylim(bottom=0)
ax.legend(frameon=False, loc="upper left")

print(f"runs drawn: {len(tasks)}")
print(f"runs above the dashed line: {sum(t['prompt_tokens'] > t['steps'] * first for t in tasks)} of {len(tasks)}")
print(f"lowest prompt total, step-capped runs: {min(t['prompt_tokens'] for t in capped)}")
print(f"highest prompt total, other runs: {max(t['prompt_tokens'] for t in others)}")
print(f"step-capped runs: {len(capped)}")
print(f"step cap, in steps: {cap}")
print(f"mean first-step prompt, in tokens: {first:.0f}")
print(f"step-capped share of steps: {share('steps'):.1f}%")
print(f"step-capped share of prompt tokens: {share('prompt_tokens'):.1f}%")
print(f"prompt tokens per step, step-capped runs: {per_step(capped)}")
print(f"prompt tokens per step, other runs: {per_step(others)}")
save(fig, "tokens-against-steps")
