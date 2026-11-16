"""The task-set recording's 20 runs, replayed as recorded and again with both stop rules. Counts only: which runs hit
the step cap, which rule ended the runs that stopped early, and whether any done task is cut short."""
from collections import Counter

from lib.case import load_tasks
from lib.loop import Stops, run_task
from lib.models import ReplayModel
from lib.tasks import score
from lib.tools import V1
from lib.trace import IdCounter

RULES = Stops(repeat_limit=3, no_progress_limit=2)


def replay(stops: Stops) -> dict:
    """Every task in file order, so the run IDs match the recording's. Maps task ID to (ended, steps, done)."""
    ids, out = IdCounter(), {}
    for task in load_tasks():
        run = run_task(ReplayModel("task-set", task.id), task, V1, max_steps=V1.step_cap, ids=ids, stops=stops)
        out[task.id] = (run.ended, run.steps, score(task, run))
        run.close()
    return out


ENDS = ("finish", "ask_user", "step_cap", "repeated_call", "no_progress", "no_tool_call")
plain, ruled = replay(Stops()), replay(RULES)
capped = sorted(t for t, (ended, _, _) in plain.items() if ended == "step_cap")
ruled_ends = Counter(ended for ended, _, _ in ruled.values())
done = sorted(t for t, (_, _, ok) in plain.items() if ok)
print("task set step cap:", V1.step_cap)
print("runs:", len(plain))
print("step cap without the rules:", len(capped))
print("step cap without the rules, tasks:", ", ".join(capped))
print("step cap with the rules:", ruled_ends["step_cap"])
print("ended early with the rules:", len([t for t in capped if ruled[t][0] != "step_cap"]))
for ended in ENDS:
    print(f"  {ended}: {ruled_ends[ended]}")
print("done without the rules:", len(done))
print("done without the rules, tasks:", ", ".join(done))
print("done with the rules:", sum(1 for _, _, ok in ruled.values() if ok))
print("done with the rules, by finish:", sum(1 for ended, _, ok in ruled.values() if ended == "finish" and ok))
print("finish but not done, with the rules:", sum(1 for ended, _, ok in ruled.values() if ended == "finish" and not ok))
print("done with the rules, by ask_user:", sum(1 for ended, _, ok in ruled.values() if ended == "ask_user" and ok))
wrong = [t for t, (ended, _, ok) in plain.items() if ended == "ask_user" and not ok]
print("ask_user but not done, without the rules:", len(wrong))
print("of those, cut early with the rules:", len([t for t in wrong if ruled[t][0] != "ask_user"]))
assert len(capped) == 7 and all(ruled[t][2] for t in done), "a done task must survive the rules"
assert sum(ruled_ends.values()) == len(plain), "every run has one ending"
