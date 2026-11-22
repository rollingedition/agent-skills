"""The task-set recording's 20 runs, each replayed as recorded and again with both stop rules, drawn as steps per task.
The rules shorten the stuck runs and leave the done runs at the same steps, which the last assert checks."""
from lib.case import load_tasks
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.loop import Stops, run_task
from lib.models import ReplayModel
from lib.tasks import score
from lib.tools import V1
from lib.trace import IdCounter


def replay(stops: Stops) -> dict:
    """Each task's (steps, done) in file order, so the run IDs match the recording's."""
    ids, out = IdCounter(), {}
    for task in load_tasks():
        run = run_task(ReplayModel("task-set", task.id), task, V1, max_steps=V1.step_cap, ids=ids, stops=stops)
        out[task.id] = (run.steps, score(task, run))
        run.close()
    return out


# Three identical calls in a row, and two edits that leave the counts where they were.
plain, ruled = replay(Stops()), replay(Stops(repeat_limit=3, no_progress_limit=2))
x = list(range(1, len(plain) + 1))
steps_plain, steps_ruled = [[runs[t][0] for t in plain] for runs in (plain, ruled)]
done = [i for i, t in enumerate(plain) if plain[t][1]]
assert all(ruled[t] == plain[t] for t in plain if plain[t][1]), "a done run changed with the rules"
assert all(r <= p for r, p in zip(steps_ruled, steps_plain)), "a rule lengthened a run"

print("task set step cap:", V1.step_cap)
print("runs:", len(plain))
print("runs the rules shortened:", sum(r < p for r, p in zip(steps_ruled, steps_plain)))
print("steps saved in all:", sum(steps_plain) - sum(steps_ruled))
print("steps saved on the runs that hit the step cap:", sum(p - r for p, r in zip(steps_plain, steps_ruled) if p == V1.step_cap))
print("done runs:", len(done))
print("steps of the done runs as recorded:", sum(steps_plain[i] for i in done))
print("steps of the done runs with both rules:", sum(steps_ruled[i] for i in done))

fig, ax = new_figure(height=3.6)
# A thin line joins each task's two counts: a drop is a shortened run, and no line means the steps did not change.
ax.vlines(x, steps_ruled, steps_plain, color=MUTED, linewidth=0.8)
ax.plot(x, steps_plain, linestyle="none", marker="o", ms=9, mew=1.2, mfc="none", color=MUTED, label="as recorded")
ax.plot(x, steps_ruled, linestyle="none", marker="s", ms=4, color=ACCENT, label="with both rules")
ax.axhline(V1.step_cap, color=INK, linestyle="--", linewidth=1.0, label=f"step cap, {V1.step_cap} steps")
# The done runs sit on a row of their own below zero, so which runs passed reads without the colour or the line.
ax.plot([x[i] for i in done], [-2] * len(done), linestyle="none", marker="^", ms=6, color=INK, label="done")
ax.set(ylabel="steps in the run", ylim=(-3, V1.step_cap + 6), xlabel="task, in file order", xticks=x, xticklabels=list(plain))
ax.set_yticks([-2, *range(0, V1.step_cap + 1, 4)], ["done", *map(str, range(0, V1.step_cap + 1, 4))])
ax.legend(frameon=False, loc="upper center", ncol=2)   # headroom above the cap line holds the legend
ax.tick_params(axis="x", labelrotation=90, labelsize=7)
save(fig, "steps-with-and-without-rules")
