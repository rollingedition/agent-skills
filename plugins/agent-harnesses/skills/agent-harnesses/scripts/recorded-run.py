"""The recorded run of T-01, replayed step by step: each request must match the one recorded, and the replies are
the recorded text, mistakes included. The run stops at the step cap without a finish, so the task is not done."""
from lib.case import load_tasks
from lib.chapter1 import Recorder, report
from lib.models import ReplayModel
from lib.tools import CH1

from collections import Counter

task = load_tasks(only=["T-01"])[0]
model = Recorder(ReplayModel("chapter-1-t01", "T-01"))
run, done = report(model, task, CH1)
assert not done, "the recorded run should not solve T-01"
reasons = [reason for reply in model.replies for reason in reply.malformed]
print("malformed calls:", len(reasons))
for reason, count in sorted(Counter(reasons).items()):
    print(f"  {count} x {reason}")
assert all('"text": """' in reply.text for reply in model.replies[2:]), "from step 3 the call's text opens with triple quotes"
print("prompt tokens:", run.prompt_tokens)
print("completion tokens:", run.completion_tokens)
