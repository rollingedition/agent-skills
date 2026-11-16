"""A note the agent writes keeps a fact that an older read result had, after a compaction. The summary keeps only the
first line of each read, and the fact sits on line 18 of format.py, so the read's summary line lacks it while the note
keeps it whole. The point rests on the last assertions: the fact is in the notes block and not in the read's line."""
from lib.case import load_tasks
from lib.chapter1 import call
from lib.context import Compacting, Context, Measured, Notes, notes_toolset
from lib.loop import run_task
from lib.models import ScriptedModel
from lib.trace import IdCounter

BUDGET = 2000  # estimated tokens: the notes and the reads cross it, the last request fits under it
# each note states a fact the run has just read in the case, so every note is true of unitcraft
notes = [
    "format_quantity strips trailing zeros on line 18 of format.py (frac.rstrip), so 3.50 kg prints as 3.5 kg",
    "test_pads_to_two_places in tests/test_format.py expects 3.5 kg to print as 3.50 kg, so the strip fails it",
    "round_places goes through float, so 2.675 rounds to 2.67, and test_tie_at_a_binary_float_edge expects 2.68",
]
replies = [call("read_file", path="unitcraft/format.py"), call("note", text=notes[0]),
           call("read_file", path="tests/test_format.py"), call("note", text=notes[1]),
           call("read_file", path="unitcraft/rounding.py"), call("note", text=notes[2]),
           call("read_file", path="README.md"), call("finish", summary="Read the case and noted the failing tests.")]
store = Notes()
ctx = Context(notes=store, prompt_budget=BUDGET)  # the notes are kept outside the older steps, so compaction keeps them
model = Compacting(Measured(ScriptedModel(replies)), ctx)
run = run_task(model, load_tasks(only=["T-01"])[0], notes_toolset(store), max_steps=16, ids=IdCounter())
sent = model.inner.requests[-1][0]
block = next(m["content"] for m in sent if m["content"].startswith("Your notes so far"))
summary = next(m["content"] for m in sent if m["content"].startswith("Earlier steps"))
read_line = summary.splitlines()[1]  # the first step: the read of format.py, with its first result line cut short
print("steps:", run.steps)
print("ended:", run.ended)
print("compactions:", ctx.compactions)
print("notes written:", len(store.lines))
print("notes whole in the notes block:", sum(line in block for line in store.lines))
print("lines in the notes block that name the fact (rstrip):", sum("rstrip" in line for line in block.splitlines()))
print("summary line for the read of format.py:", read_line)
assert ctx.compactions > 0, "the run should compact"
assert all(line in block for line in store.lines), "every note should be whole in the notes block"
assert "format.py" in read_line and "rstrip" not in read_line, "the read's summary line must lack the fact"
assert "rstrip" in block, "the note must keep the fact"
