"""A parent starts a child on T-04, whose recorded run ends with a finish that changes files. The gate holds that finish
because the person says no, so the child hands back with ask_user. The child's records sit under the parent's start call;
the parent is scripted, so its records carry zero tokens."""
from lib.case import load_tasks
from lib.chapter1 import call
from lib.models import ReplayModel, load_recording
from lib.permissions import Gate, library_copy, replay_ids, scripted
from lib.subagents import START_CHILD
from lib.tasks import snapshot
from lib.tools import V1
from lib.trace import StepRecorder, child_under_parent, dumps

task = load_tasks(only=["T-04"])[0]
manifest, _ = load_recording("task-set")
stored = next(t for t in manifest["tasks"] if t["task"] == "T-04")
with library_copy() as library:
    before = snapshot(library, "unitcraft")
    gate = Gate(library, scripted((False, "not this change")))  # the scripted person says no, with this reason
    child_model = StepRecorder(ReplayModel("task-set", "T-04"), gate)
    replies = [call(START_CHILD, task_id="T-04"), call("ask_user", question="The child's change was held. Pass it on?")]
    parent, child, records = child_under_parent(task, replies, child_model, gate, library, replay_ids("T-04"))
    for record in records:
        print(dumps(record))
    print("child budget:", V1.step_cap)
    print("child ended:", child.handoff.ended)
    print("gate refusals:", gate.counts["refused"])
    print("parent ended:", parent.ended)
    print("copy unchanged by the held finish:", before == snapshot(library, "unitcraft"))
    child_records = [r for r in records if r["run"] == child.run.id]
    parent_records = [r for r in records if r["run"] != child.run.id]
    print("child run:", child.run.id)
    print("parent call of the child:", child_records[0]["parent"])
    print("held step:", next(r["step"] for r in child_records if r["result"] == "refused"))
    print("parent tokens, summed:", sum(r["prompt_tokens"] + r["completion_tokens"] for r in parent_records))
    child_prompt = sum(r["prompt_tokens"] for r in child_records)
    child_completion = sum(r["completion_tokens"] for r in child_records)
    print("child prompt tokens, summed:", child_prompt)
    print("child completion tokens, summed:", child_completion)
    assert child.handoff.ended == "ask_user" and sum(r["result"] == "refused" for r in records) == 1
    assert parent.ended == "ask_user" and before == snapshot(library, "unitcraft")
    assert (child_prompt, child_completion) == (stored["prompt_tokens"], stored["completion_tokens"])
    parent.close()
