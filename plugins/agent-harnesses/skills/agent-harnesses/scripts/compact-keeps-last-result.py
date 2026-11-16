"""Four reads of the case, then finish, under a small budget that the reads cross. The point rests on the calls
compacted line and the last two lines: the summary replaces the older steps, and a cut that would leave the last
call's result on its own is refused."""
from lib.case import load_tasks
from lib.chapter1 import call
from lib.context import Compacting, Context, Measured, clean_cut, estimate
from lib.loop import run_task
from lib.models import ScriptedModel
from lib.tools import V2
from lib.trace import IdCounter

# estimated tokens: above the fixed part and one result, below the full transcript; the chapter's budget is 7168,
# which the case's files never reach
BUDGET = 2000
replies = [call("read_file", path=p) for p in ("unitcraft/convert.py", "unitcraft/units.py", "unitcraft/parse.py",
                                                "README.md")] + [call("finish", summary="Read four files.")]
ctx = Context(prompt_budget=BUDGET)
model = Compacting(Measured(ScriptedModel(replies)), ctx)
run = run_task(model, load_tasks(only=["T-01"])[0], V2, max_steps=V2.step_cap, ids=IdCounter())
sent, tools, _ = model.inner.requests[-1]
# the last request: system prompt, issue, summary, the last call, its result
print("budget, in estimated tokens:", BUDGET)
print("steps:", run.steps)
print("ended:", run.ended)
print("calls compacted:", ctx.compactions)
print("calls still over the budget:", ctx.over_budget)
print("fixed part (system prompt, tool schemas, issue), estimated tokens:", estimate(sent[:2], tools))
print("messages sent on the last call:", len(sent))
for number, message in enumerate(sent, start=1):
    print(f"message {number}, {message['role']}:", " ".join(message["content"].split()[:4]))
# the summary's first line is its heading, so the steps start at the second line
print("summary of the older steps:", *sent[2]["content"].splitlines()[1:], sep="\n  ")
# the call is wrapped in <tool_call> tags, so its JSON is the second line
print("kept call:", sent[3]["content"].strip().splitlines()[1][:60])
print("kept result, in lines:", len(sent[4]["content"].splitlines()))
print("cut before the last result alone, clean:", clean_cut(sent, len(sent) - 1))
print("cut before the last call, clean:", clean_cut(sent, len(sent) - 2))
assert ctx.compactions > 0 and not clean_cut(sent, len(sent) - 1) and clean_cut(sent, len(sent) - 2)
