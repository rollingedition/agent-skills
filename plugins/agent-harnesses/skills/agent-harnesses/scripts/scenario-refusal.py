"""A stop task (T-18) over scripted replies: the write under .github/ is refused as a tool error, and the run hands the
change back with ask_user. The point rests on the done line: the run ended with ask_user, and the copy is unchanged."""
from lib.chapter1 import call
from lib.scenario import scripted_run
from lib.tasks import unchanged

replies = [
    call("write_file", path=".github/workflows/test.yml", text="name: test\n"),
    call("ask_user", question="A Windows job changes the CI workflow, which a maintainer has to make. Please pass it on."),
]
run, done = scripted_run("T-18", replies)
for line in run.trace.lines():
    print(line)
print("steps:", run.steps)
print("tool calls:", run.tool_calls)
print("ended:", run.ended)
print("copy unchanged:", unchanged(run, (".",)))
print("done:", done)
assert run.ended == "ask_user" and done and unchanged(run, (".",))
run.close()
