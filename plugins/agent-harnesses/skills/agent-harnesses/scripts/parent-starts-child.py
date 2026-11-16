"""A parent loop starts the child on T-02 through a tool, reads the child's handoff and asks the person the child's
question. The output counts the parent's steps apart from the child's, and shows that the child's file text stays out of
the parent's context."""
from lib.case import load_tasks
from lib.loop import Stops, run_task
from lib.models import ReplayModel
from lib.subagents import ParentReadsHandoff, characters, start_child_tools
from lib.tools import V1
from lib.trace import IdCounter

RULES = Stops(repeat_limit=3, no_progress_limit=2)
task = load_tasks(only=["T-02"])[0]
child_ids = IdCounter()
child_ids.next("run")  # the recording numbers its runs in task order, so T-02 is run-0002: skip T-01's number
children = []
tools = start_child_tools(task, lambda: ReplayModel("task-set", task.id), ids=child_ids, stops=RULES, children=children)
parent_model = ParentReadsHandoff(task.id)
parent = run_task(parent_model, task, tools, max_steps=tools.step_cap, ids=IdCounter())
child = children[0]
h = child.handoff
# the child's longest tool result is its read of the library file, the text a parent must not receive
file_text = max((m["content"] for m in child.transcript if m["role"] == "tool"), key=len)
parent_text = "\n".join(m["content"] for m in parent_model.messages)
print("child budget, steps:", V1.step_cap)
print("child steps:", h.steps)
print("child result:", h.ended)
print("parent steps:", parent.steps)
print("parent result:", parent.ended)
print("parent tools:", ", ".join(t.name for t in tools.tools))
print("question asked matches the handoff:", "yes" if parent.question == h.question else "no")
print("child transcript, characters:", characters(child.transcript))
print("handoff in parent context, characters:", len(h.text))
print("parent context at last step, characters:", characters(parent_model.messages))
print("child file text in parent context:", "yes" if file_text in parent_text else "no")
print("parent steps, in order:", *parent.trace.lines(), sep="\n  ")
assert h.ended == "no_progress" and parent.ended == "ask_user" and parent.steps == 2
assert parent.question == h.question and file_text not in parent_text
parent.close()
