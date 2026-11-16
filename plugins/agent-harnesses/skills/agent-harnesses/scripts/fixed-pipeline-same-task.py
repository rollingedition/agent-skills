"""The fixed pipeline on the tasks where one known edit works (T-02, T-04, T-05), with no model, beside the recorded
agent's run on the same task. The point rests on two lines per run: the pipeline's actions and its model calls (0), and
the agent's steps, which are its model calls. The edits are written by a person; the scoring is the same for both."""
from lib.case import load_tasks
from lib.models import load_recording
from lib.pipeline import PIPELINES, Edit, Pipeline, agent_edit_results, run_pipeline
from lib.tasks import score

manifest, _ = load_recording("task-set")
stored = {row["task"]: row for row in manifest["tasks"]}
for task in load_tasks(only=sorted(PIPELINES)):
    run = run_pipeline(task, PIPELINES[task.id])
    done = score(task, run)
    run.close()
    agent = stored[task.id]
    print(f"{task.id} pipeline ended: {run.ended}")
    print(f"{task.id} pipeline done: {'yes' if done else 'no'}")
    print(f"{task.id} pipeline actions: {run.tool_calls}")
    print(f"{task.id} pipeline model calls: {run.steps}")
    print(f"{task.id} pipeline prompt tokens: {run.prompt_tokens}")
    print(f"{task.id} agent ended: {agent['ended']}")
    print(f"{task.id} agent done: {'yes' if agent['done'] else 'no'}")
    print(f"{task.id} agent steps: {agent['steps']}")
    print(f"{task.id} agent tool calls: {agent['tool_calls']}")
    print(f"{task.id} agent prompt tokens: {agent['prompt_tokens']}")
    assert done and run.steps == 0 and run.tool_calls < agent["tool_calls"], task.id

# The agent's T-02 run, replayed from the recording: the result the tools gave each of its edits and test runs.
edits, tests = agent_edit_results("T-02")
print(f"T-02 agent edits failed: {sum(e.startswith('error') for e in edits)} of {len(edits)}")
print(f"T-02 agent test runs: {len(tests)}")
print(f"T-02 agent first edit result: {edits[0]}")
assert all(e.startswith("error") for e in edits) and not tests

# The pipeline's own failure: its one edit names text the file does not hold, so the run stops at that step.
task = load_tasks(only=["T-04"])[0]
run = run_pipeline(task, Pipeline((Edit("unitcraft/units.py", "no such line", "x"),), "not run"))
print(f"T-04 missing anchor ended: {run.ended}")
print(f"T-04 missing anchor actions: {run.tool_calls}")
print(f"T-04 missing anchor done: {'yes' if score(task, run) else 'no'}")
print(f"T-04 missing anchor result: {run.stop_detail}")
run.close()
assert run.ended == "pipeline_stop" and run.tool_calls == 2
