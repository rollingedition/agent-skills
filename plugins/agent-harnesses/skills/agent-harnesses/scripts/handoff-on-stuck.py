"""The 20 task-set runs as children, with both stop rules. Each child that ended stuck is handed to a parent, which
puts the stop's question to the person with ask_user. Counts only: how the children ended, and what the parents got."""
from collections import Counter

from lib.loop import Stops
from lib.models import ScriptedModel
from lib.subagents import STUCK, asks, characters, hand_to_parent, task_set_children
from lib.trace import IdCounter

RULES = Stops(repeat_limit=3, no_progress_limit=2)
ENDS = ("finish", "ask_user", "step_cap", "repeated_call", "no_progress", "no_tool_call")
children = task_set_children(RULES)
stuck = [(task, h, transcript) for task, h, _, transcript in children if h.stuck]
ends = Counter(h.ended for _, h, _, _ in children)
print("child runs:", len(children))
for ended in ENDS:
    print(f"  {ended}: {ends[ended]}")
print("done with the rules:", sum(1 for _, _, ok, _ in children if ok))
print("ended with finish or ask_user:", sum(1 for _, h, _, _ in children if h.ended in ("finish", "ask_user")))
print("done among the handed back:", sum(1 for _, h, ok, _ in children if h.stuck and ok))
print("handed back to a parent:", len(stuck))
handed = Counter(h.ended for _, h, _ in stuck)
for ended in STUCK:
    print(f"  {ended}: {handed[ended]}")
print("handed back, tasks:", ", ".join(task.id for task, _, _ in stuck))

parent_ids = IdCounter()  # the parents number their runs apart, so the children's run IDs stay the recording's
parents = [(h, hand_to_parent(ScriptedModel([asks(h.question)]), h, parent_ids)) for _, h, _ in stuck]
print("parent asked the person, with the handoff's question:",
      sum(1 for h, r in parents if r.ended == "ask_user" and r.question == h.question))
print("child steps, all handed back:", sum(h.steps for _, h, _ in stuck))
print("parent steps, all handed back:", sum(r.steps for _, r in parents))
print("child transcripts, characters:", sum(characters(t) for _, _, t in stuck))
print("handoffs the parents read, characters:", sum(len(h.text) for _, h, _ in stuck))
print("saved by the handoffs, characters:",
      sum(characters(t) for _, _, t in stuck) - sum(len(h.text) for _, h, _ in stuck))
assert all(h.stop and h.question for _, h, _ in stuck), "every stuck child gives a stop reason and a question"
assert not any(ok for _, h, ok, _ in children if h.stuck), "a done task must not be handed back"
