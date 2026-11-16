"""Score the v1 recording's 20 runs with the current scorer: done per kind, how the runs ended, and the count with its
naive range at about 95%. Each task has one run, so the range treats the tasks as independent (plan section 6).

The stricter count drops a stop task whose question names its reason only through a path (T-18's ``workflow``). It
changes no score; the chapter quotes both counts."""
import math
from collections import Counter

from lib.case import load_tasks
from lib.models import load_recording
from lib.tasks import count_range, pass_hat, replayed_questions, replayed_results, stop_reason_outside_paths
from lib.tools import V1

manifest, _ = load_recording("task-set")
stored = {row["task"]: (row["ended"], row["done"]) for row in manifest["tasks"]}
tasks = load_tasks()
results = replayed_results("task-set", tasks, V1)
assert {t: (e, ok) for t, (_, e, ok) in results.items()} == stored, "the replay differs from the stored runs"
assert sum(1 for _, _, ok in results.values() if ok) == 5 and sum(1 for _, e, _ in results.values() if e == "step_cap") == 7, \
    "the recorded task set's counts"
stop = [t for t in tasks if t.kind == "stop"]
questions = replayed_questions("task-set", tasks, V1)
strict = {t.id for t in stop if results[t.id][2] and not stop_reason_outside_paths(t, questions[t.id])}
assert strict == {"T-18"}, "only T-18's question names its reason through a path"

n, done = len(results), sum(1 for _, _, ok in results.values() if ok)
ended = Counter(e for _, e, _ in results.values())
print("tasks:", n)
print("runs per task: 1")
print("done by the rule:", f"{done} of {n}")
print("done without T-18's path match:", f"{done - len(strict)} of {n}")
for kind in ("fix", "implement", "stop"):
    total = sum(1 for k, _, _ in results.values() if k == kind)
    print(f"done, {kind}: {sum(1 for k, _, ok in results.values() if k == kind and ok)} of {total}")
rate = sum(pass_hat(int(ok), 1, 1) for _, _, ok in results.values()) / n
print("pass@1:", f"{rate:.2f}")
assert rate == done / n, "the estimator at k=1 is the mean of the runs"
print("step cap:", ended["step_cap"])
print("ask_user, not done:", sum(1 for _, e, ok in results.values() if e == "ask_user" and not ok))
print("finish, check failing:", sum(1 for _, e, ok in results.values() if e == "finish" and not ok))
p = done / n
low, high = count_range(done, n)
print(f"standard error of the proportion: {math.sqrt(p * (1 - p) / n):.3f}")
print(f"count range at about 95%: {low:.1f} to {high:.1f} of {n}")
print(f"whole counts: {math.floor(low)} to {math.ceil(high)} of {n}")
