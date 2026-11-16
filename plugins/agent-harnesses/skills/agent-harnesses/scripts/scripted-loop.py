"""Four scripted replies solve T-01 through the step loop: read the file, read its test, run the visible suite,
then finish with the fixed file. The model is scripted, so the output shows the loop's steps and not a model's choices."""
from lib.case import load_tasks
from lib.chapter1 import SOLUTION, call, report
from lib.models import ScriptedModel
from lib.tools import CH1

task = load_tasks(only=["T-01"])[0]
model = ScriptedModel([
    call("read_file", path="unitcraft/format.py"),
    call("read_file", path="tests/test_format.py"),
    call("run_tests"),
    call("finish", path="unitcraft/format.py", text=SOLUTION.read_text(encoding="utf-8")),
])
run, done = report(model, task, CH1)  # CH1: three tools, their system prompt and a budget of eight steps; report prints the trace and scores the run
assert done, "the scripted run should solve T-01"
