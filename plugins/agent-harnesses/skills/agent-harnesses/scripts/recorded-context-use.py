"""The three recorded runs of chapter 5, replayed with the compaction on: how each ended, whether its check passed,
its note calls and compactions, and its largest prompt by the estimate and by the count the model reported. The point
rests on the check lines and the zero counts: no run passed its check, and no run wrote a note or was compacted."""
import json

from lib.case import load_tasks
from lib.context import Compacting, Context, Measured, Notes, estimate, notes_toolset
from lib.loop import Stops, run_task
from lib.models import RECORDED, ReplayModel
from lib.trace import IdCounter

manifest = json.loads((RECORDED / "chapter-5-notes" / "manifest.json").read_text(encoding="utf-8"))
recorded = {t["task"]: t for t in manifest["tasks"]}  # the recording's own check result, stored with each run
ids, passed, notes_total, compact_total, est_max, rec_max = IdCounter(), 0, 0, 0, 0, 0
for task in load_tasks(only=["T-01", "T-02", "T-06"]):
    notes = Notes()
    context = Context(notes=notes)  # the default budget, 7168 tokens, which no run reaches
    model = Compacting(Measured(ReplayModel("chapter-5-notes", task.id)), context)
    # the step cap of 16 and the stop rules are those the recording was made with
    run = run_task(model, task, notes_toolset(notes), max_steps=16, ids=ids,
                   stops=Stops(repeat_limit=3, no_progress_limit=2))
    run.close()
    print(f"{task.id} kind: {recorded[task.id]['kind']}")
    print(f"{task.id} ended: {run.ended}")
    print(f"{task.id} check passed: {'yes' if recorded[task.id]['done'] else 'no'}")
    print(f"{task.id} note calls: {sum(r['tool'] == 'note' for r in run.trace.records)}")
    print(f"{task.id} compactions: {context.compactions}")
    passed += recorded[task.id]["done"]
    notes_total += sum(r["tool"] == "note" for r in run.trace.records)
    compact_total += context.compactions
    est_max = max([est_max] + [estimate(m, t) for m, t, _ in model.inner.requests])
    rec_max = max([rec_max] + [n for _, _, n in model.inner.requests])
print("total note calls:", notes_total)
print("total compactions:", compact_total)
print("runs whose check passed:", passed)
print("largest estimated prompt over the three runs, in tokens:", est_max)
print("largest recorded prompt over the three runs, in tokens:", rec_max)
assert notes_total == 0, "the recorded runs made no note calls"
assert compact_total == 0, "the recorded runs were never compacted"
assert passed == 0, "none of the three recorded runs passed its check"
