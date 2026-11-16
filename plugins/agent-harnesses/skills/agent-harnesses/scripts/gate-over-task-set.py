"""The 20 recorded task-set runs replayed with the gate observing, each matching its recorded ending and step count, and
the gate counting what it would have held (the four stop tasks T-16 to T-19 first). Counts only."""
from lib.case import CASE, DATA, load_tasks
from lib.permissions import Gate, library_copy, replay_task
from lib.tasks import snapshot
from lib.trace import IdCounter

import json

CHANGES = ("edit_file", "write_file")
rows = (DATA / "recorded" / "task-set" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
recorded = {r["task"]: r for r in map(json.loads, rows)}
runs, gates, pendings = {}, {}, {}
with library_copy() as library:
    ids = IdCounter()
    for task in load_tasks():
        gate = Gate(library, enforce=False)
        run = replay_task(task.id, gate, library, ids=ids)
        assert (run.ended, run.steps) == (recorded[task.id]["ended"], recorded[task.id]["steps"]), task.id
        runs[task.id], gates[task.id], pendings[task.id] = run, gate, gate.settle(run.scratch)
    for tid in ("T-16", "T-17", "T-18", "T-19"):
        gate, pend, run = gates[tid], pendings[tid], runs[tid]
        refused = sum(1 for r in run.trace.records if r["tool"] in CHANGES and r["brief"].startswith("error"))
        print(f"{tid} ended: {run.ended}, steps: {run.steps}")
        print(f"  change calls: {gate.counts['change calls']}, refused by the tool: {refused}")
        print(f"  never-class calls: {gate.counts['never calls']}, changes in the copy at the end: {len(pend.files)}")
        print(f"  held as never: {len(pend.never)}, waiting for a yes: {len(pend.files) - len(pend.never)}")
    changed = sorted(t for t in pendings if pendings[t].files)
    print("runs:", len(runs))
    print("runs with a change left in the copy:", len(changed), ", tasks:", ", ".join(changed))
    print("change calls, all runs:", sum(g.counts["change calls"] for g in gates.values()))
    print("never-class calls, all runs:", sum(g.counts["never calls"] for g in gates.values()))
    print("held as never, all runs:", sum(len(p.never) for p in pendings.values()))
    print("proposals that would wait for a yes, all runs:", sum(g.counts["waiting for a yes"] for g in gates.values()))
    print("library changed by the replays:", snapshot(library, ".") != snapshot(CASE, "."))
    assert snapshot(library, ".") == snapshot(CASE, ".") and gates["T-18"].counts["never calls"] == 1
    for run in runs.values():
        run.close()
