"""Where each design's utility cost comes from, counted in the traces of the benign tasks the design lost, on dev and on held-out.

The taint count rests on its refusals at send_message.body: each refused benign task is one the design lost. The dual
LLM count rests on the planner's questions in the tasks it lost, and on the quarantined calls in the benign tasks (the attack cases are not counted). The
held-out lines carry the split in their labels; held-out's quarantined count is reported as it is.
"""
from collections import Counter

from lib import cases, harness, replay, runs, scorers  # lib first: threads and seeds are fixed here


def refusals(trace):
    """The reasons of the calls a defence refused in one trace, each reason as the check wrote it."""
    return [e.result["reason"] for e in trace.events
            if e.kind == "defence" and isinstance(e.result, dict) and e.result.get("blocked")]


def main():
    for split, p in [("dev", ""), ("held-out", "held-out ")]:  # dev keeps its labels; held-out names its split
        tasks = cases.load_tasks(split)  # 15 benign tasks
        base_run = runs.replay_tasks(f"baseline-{split}", tasks)
        base = {t.id: scorers.utility(t, base_run[t.id]) for t in tasks}  # the baseline's answer per task
        taint = runs.replay_tasks(f"design-taint-{split}", tasks, variant="design-taint")
        refused = {t.id: refusals(taint[t.id]) for t in tasks if refusals(taint[t.id])}
        taint_lost = [t.id for t in tasks if base[t.id] and not scorers.utility(t, taint[t.id])]
        print(f"{p}benign tasks refused, design-taint: {len(refused)} of {len(tasks)}")
        by_arg = Counter(reason.split(":")[0] for reasons in refused.values() for reason in reasons)
        for arg in sorted(by_arg):  # the argument is the text before the first colon of each reason
            print(f"{p}refusals at {arg}: {by_arg[arg]}")
        print(f"{p}benign tasks lost, design-taint: {len(taint_lost)} of {len(tasks)}")
        # The cost is the refusals: every task taint lost was refused at send_message.body, and no other task was.
        assert sorted(refused) == taint_lost, split
        assert all(r.startswith("send_message.body:") for rs in refused.values() for r in rs), split

        dual = runs.replay_tasks(f"design-dual-llm-{split}", tasks, variant="design-dual-llm")
        dual_lost = [t.id for t in tasks if base[t.id] and not scorers.utility(t, dual[t.id])]
        print(f"{p}benign tasks lost, design-dual-llm: {len(dual_lost)} of {len(tasks)}")
        for task_id in dual_lost:
            asked = sorted(str((e.args or {}).get("question")) for e in dual[task_id].tool_calls("ask_quarantined"))
            print(f"{p}questions asked, lost task {task_id}: {', '.join(asked) or 'none'}")
        total_asks = sum(len(dual[t.id].tool_calls("ask_quarantined")) for t in tasks)
        print(f"{p}quarantined questions, all benign {split} tasks: {total_asks}")
        if split == "dev":  # the quarantined model answered nothing on dev; held-out's count is printed, not checked
            assert total_asks == 0

        # Plan-then-execute: the first reply of each benign task, counted by its tool calls, against the tasks it finished.
        plan = runs.replay_tasks(f"design-plan-then-execute-{split}", tasks, variant="design-plan-then-execute")
        recording = replay.ReplayModel(f"design-plan-then-execute-{split}")
        multi = [t for t in tasks if len(harness.parse_calls(recording.lookup(t.id, 0)["reply"])) > 1]
        print(f"{p}first replies holding more than one call, design-plan-then-execute: {len(multi)} of {len(tasks)}")
        done = sum(scorers.utility(t, plan[t.id]) for t in tasks)
        print(f"{p}benign tasks done, design-plan-then-execute: {done} of {len(tasks)}")


if __name__ == "__main__":
    main()
