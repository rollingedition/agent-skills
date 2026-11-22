---
title: "Agent Harnesses"
chapter: "When an agent is the wrong design"
chapter_id: when-an-agent-is-the-wrong-design
book: agent-harnesses
edition: 2026.11.6
verified: 2026-11-22
edition_code: 3KM9-2NP7
canonical: https://rollingedition.com/agent-harnesses/when-an-agent-is-the-wrong-design
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“When an agent is the wrong design,” chapter 12 of Agent Harnesses, Edition 2026.11.6, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/when-an-agent-is-the-wrong-design. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# When an agent is the wrong design

By the end of this chapter you can take any task in the case, sort it into a fixed pipeline, a single model call or an agent with gates, and say what the recorded runs show for it. The case gives the first test. Task T-02 is a one-line fix in `unitcraft`, the library whose tasks this chapter sorts by design: negative amounts lose their thousands separator, so `-1234.5 m` should print as `-1,234.50 m`. The recorded run with tool set v1 from [chapter 3](#tool-schemas), the set the task recording was made with, never finished it. It used all 16 of its steps and never called `finish`. The change is one replacement in one function, so the question is whether an agent was ever the right design for it.

## Start with the fixed pipeline {#fixed-pipeline-first}

The first question for T-02 is which steps it needs when nothing in the run has to be decided. Read the formatting module, replace the line that builds the number's text so that negative values keep the separator, run the visible tests, and finish with a sentence describing the change. None of those steps waits on what a model thinks of the file, so none needs a model. A fixed pipeline is a task's list of steps, written as code before the run starts.

Anthropic's engineering post on building agents draws a similar line. It calls a system a workflow when LLMs and tools are orchestrated through predefined code paths, and an agent when an LLM dynamically directs its own processes and tool use ([Anthropic, "Building effective agents"](https://www.anthropic.com/engineering/building-effective-agents), published 19 December 2024). A workflow in that sense still runs a model at its steps. The pipeline in this chapter goes one step further, because none of its steps needs a model. The same post recommends finding the simplest solution possible and adding complexity only when it is needed. The rule this chapter takes from that advice is a rule of thumb, not a measurement: if the steps can be written down before the run, write them down first.

Each pipeline is a list of exact edits and a summary, kept in `lib/pipeline.py`. An [edit](#edit-errors) names the text it replaces and the text that replaces it, and it fails when the old text is not in the file exactly once. The pipeline runs its list through tool set v1, so each call behaves as it does for the agent, and it scores the result with [the same done rule](#score). Only three pipelines are written, for T-02, T-04 and T-05. The example runs them and prints each one beside the agent's stored run on the same task.

Example `fixed-pipeline-same-task` (Python 3.12.15 · pydantic 2.14.4), passing in Edition 2026.11.6:

```python
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
```

Output:

```text
T-02 pipeline ended: finish
T-02 pipeline done: yes
T-02 pipeline actions: 4
T-02 pipeline model calls: 0
T-02 pipeline prompt tokens: 0
T-02 agent ended: step_cap
T-02 agent done: no
T-02 agent steps: 16
T-02 agent tool calls: 16
T-02 agent prompt tokens: 43904
T-04 pipeline ended: finish
T-04 pipeline done: yes
T-04 pipeline actions: 4
T-04 pipeline model calls: 0
T-04 pipeline prompt tokens: 0
T-04 agent ended: finish
T-04 agent done: yes
T-04 agent steps: 5
T-04 agent tool calls: 5
T-04 agent prompt tokens: 8809
T-05 pipeline ended: finish
T-05 pipeline done: yes
T-05 pipeline actions: 4
T-05 pipeline model calls: 0
T-05 pipeline prompt tokens: 0
T-05 agent ended: finish
T-05 agent done: yes
T-05 agent steps: 5
T-05 agent tool calls: 5
T-05 agent prompt tokens: 8494
T-02 agent edits failed: 9 of 9
T-02 agent test runs: 0
T-02 agent first edit result: error: old text not found in unitcraft/format.py
T-04 missing anchor ended: pipeline_stop
T-04 missing anchor actions: 2
T-04 missing anchor done: no
T-04 missing anchor result: error: old text not found in unitcraft/units.py
```

The pipeline finishes all three tasks, and it makes no model call. In this chapter a [step](#the-loop) is a model call, as it is everywhere in the book, so the pipeline has no steps. A pipeline has actions, which are its tool calls, and the line that counts them is `4` for T-02. The recorded agent on T-02 made `16` model calls, one for each step, and its prompt tokens add up to `43904`. The pipeline sent no prompt at all. On T-04 and T-05, where the agent finished, the agent still made more model calls than the pipeline had actions, and the example prints both counts for each. Chapter 11 explains why the book counts calls and tokens rather than money ([cost as counts](#cost-not-money)).

Replaying the agent's T-02 run from the recording shows the result of each call. Its edits failed, 9 of 9, each with the same message: `error: old text not found in unitcraft/format.py`. The agent read the file again and tried again, with the same error, and it never ran the tests: its test-run count is 0. The step cap stopped a run that could not make its change match the file. Nothing in the run checked whether a change had worked, so the count says how long the agent was stuck and nothing about why.

The pipeline fails in its own way too. Its last run gives it an edit for T-04 whose old text does not occur in the file, which is what happens when a file changes under a fixed list. The run ends at that step, after `2` actions, with the tool's own message: `error: old text not found in unitcraft/units.py`. The pipeline does not try another anchor, read the file again or ask anyone. For an edit a person wrote, stopping is the right response, because the file has changed and a person should look.

The stop still has to go somewhere, and a pipeline cannot hand it to a child, because it has none. It can hand the stop to a person, who reads the failed step and decides what to do. Or it can hand the task to an agent, given the step that failed and the file as it now stands. The hybrid, a pipeline first and an agent only on a `pipeline_stop`, is the natural one. The pipeline does the steps that need no judgement, and the agent sees only the part that broke. It starts the agent from a partial state, so the agent's run needs the same gates as any other. We recommend a person when the broken step touches a decision the case gives to a person. We recommend the agent when the step is a known edit that stopped on a changed anchor. This chapter does not measure the hybrid.

Three things limit what the pipeline shows. A person wrote each edit, so the comparison measures what the design costs, not what a pipeline could find alone. The three tasks are the ones whose edits could be named before the run, and nothing here shows how the others would fare. The pipeline also compares failing test ids before and after its edit, because the visible suite already fails before any edit.

**Working rule:** Before you give a model the loop, write the steps out, with the check that follows each one. If every step is known and a check decides the result without a model, build the pipeline and measure it. Decide where its stop goes before the first run: to a person, or to an agent given the failed step.

## When splitting the work helps {#when-to-split}

Once one agent struggles, the next thing people reach for is a second agent. Splitting can look like more care, so the useful question is when it actually helps. Two studies give conditions rather than a verdict.

Tran and Kiela compared one agent with several on multi-hop reasoning, holding the reasoning tokens equal ([Tran and Kiela, arXiv:2604.02460](https://arxiv.org/abs/2604.02460)). The single agent matched or beat the multi-agent systems. Their abstract predicts that multi-agent systems become competitive under two conditions: when a single agent's effective context use is degraded, and when more compute is spent.

Kim et al. ran a controlled comparison across 260 configurations and six agentic benchmarks ([Kim et al., arXiv:2512.08296](https://arxiv.org/abs/2512.08296)). Their abstract says that architecture-task alignment determines collaborative success, and that mismatched coordination degrades performance. The useful reading is conditional: a coordination pattern that helps on one task can hurt on another. Both studies are single papers. Their scope is reasoning and benchmarks, not a maintenance library, so read them as reasons to test a design and not as settled results.

The case can be checked against the first condition, a context the single agent cannot hold. The recording's context window is `8192` tokens. Its largest single request held `6556` prompt tokens, which leaves room under the window, and under the prompt budget that [chapter 5](#window) sets for it. No request in the set reached the window, so no task in the case has a context that forces a split. [Chapter 8](#designs) compares two kinds of split, and it says that this book does not measure a split against one loop. The case therefore gives no number for a split either. The decision table below takes the first condition as its test for splitting, and no row meets it.

**Working rule:** Split a task only when you can name the condition that makes splitting help, such as a context the single agent cannot hold, and when each part has a check that does not depend on the other parts. Otherwise keep one agent, or none.

## What goes wrong when you do use an agent {#failures}

An agent adds places where a run can go wrong, and most of them show only in the record of the run.

Cemri et al. built their taxonomy from 150 traces that expert annotators read closely. They then used an LLM-as-a-judge pipeline, checked against those annotators, to label the more than 1,600 traces in their dataset from seven multi-agent frameworks ([Cemri et al., arXiv:2503.13657](https://arxiv.org/abs/2503.13657), v3). The result is 14 failure modes in three categories: system design issues, inter-agent misalignment, and task verification. The taxonomy is for multi-agent systems, so it maps onto one agent only loosely. This chapter does not map any of its modes onto the case. The malformed tool calls in the replayed run of [chapter 1](#what-goes-wrong) are failures of what the model sends to a tool, and they are visible in the record of that run.

The T-02 run failed by repetition. Its 16 steps were a listing and a run of edits, most of them after a read of the same file, and each edit came back with the same error, because the old text it quoted was not in the file. The step cap ended the run, which is what the budget in [chapter 2](#step-budget) is for, but the cap only stopped the run. The record shows why it never finished: the agent never made a change that matched, and it never checked a change it had not made.

The stop tasks fail in another way. On T-17 and T-19 the agent asked a person a question, and neither run was counted as done. The scorer counts an `ask_user` only when its question names the reason for stopping, and it looks for words such as `half` or `truncat` on T-17 and `dimension`, `length` or `mass` on T-19. T-17 asks for the right rounding for money, and its final question proposes a change to the float-based rounding and asks whether to go ahead. T-19 asks for metres to be turned into kilograms, and its final question offers a special case that assumes a density of 1 and asks which approach the person prefers. Neither question names the reason the scorer looks for. Both runs also tried to edit before they asked. Each edit came back as an error, because its old text was not in the file, and a write to the existing file was refused, so the copies never changed. The record shows that the questions did not name the reason and that the edits failed first. It does not show what a person would have answered, and this chapter does not guess.

T-18 is the other stop task, and its record is a warning about the scorer. The scorer counts its run as done through a word inside a file path, and [chapter 10](#t18-path) explains how. This book leaves the scorer as it is, and it reports T-18 as a limit of the scorer, not as a good handoff.

Reliability is the failure a single run hides. tau-bench defines [pass^k](#score) as the chance that all k independent trials of a task succeed, averaged across tasks ([Yao et al., arXiv:2406.12045](https://arxiv.org/abs/2406.12045)). In its 2024 setup, function-calling agents, gpt-4o among them, succeeded on fewer than half of its tasks, and pass^8 in its retail domain stayed under 25%. One passing run is one trial. This book runs each task once, so it cannot report pass^k, and [chapter 10](#testing-the-agent) describes what it reports in its place.

**Working rule:** Before you trust an agent's design, sort its stopped runs by how they ended and read the record of each kind. A count of failures without their kinds does not say which part to fix, and one passing run does not predict the next.

## The check stays outside the agent {#check-outside}

A run that the agent judges finished is not yet a finished task.

Kim et al. found that architectures without centralized verification tend to propagate errors more than those with centralized coordination. In the paper's own measurement, independent agents amplified trace-level errors 17.2 times, and a centralized orchestrator held that to 4.4 times ([Kim et al.](https://arxiv.org/abs/2512.08296), Section 1 and Table 5). The paper is about several agents. The logic carries over to one: whatever decides that the work is right should not be the part that did the work.

The case applies that logic to its own score. For a fix, the hidden check runs after the run ends, in a copy the agent never sees. The agent may not edit a test to make it pass, and [chapter 10](#testing-the-agent) describes the hidden check.

The stop check is weaker. A stop task is scored from the question the agent wrote, so the agent's own words decide whether the run counts. T-18 shows how little that is worth ([chapter 10](#t18-path)). A check that reads the agent's account of its work is a check the agent can argue with. A visible test the agent can edit tells you what the agent thinks of its change, not what the code does.

**Working rule:** Put the check that decides a task's result where the agent cannot edit it or see it before the run ends. If a finish or a stop depends on the agent's own account of its work, add a check the agent did not write.

## The decision table {#which-design}

The decision table sorts each task by three readings: whether its steps are known before the run, whether a check can decide the result without a person, and whether a person has to say yes. A fourth matter comes before all three, which is whether the harness refuses the change outright. The readings are the author's judgement of each task, not measurements, and the rules are rules of thumb. Each row sits beside the recorded end of that task's run, and no model is called.

The rules run in one order, and the order is the point. First, a change the harness forbids is not a design question. Chapter 6's gate refuses any change under `.github/`, and it refuses a rename that removes a public name, because no yes can lift a rule of that kind ([never-class changes](#never-class)). Second, a person's yes means an agent behind a gate, because the gate must ask before it applies a change. Third, known steps mean a pipeline when a check decides the result, and one model call when no check does. Open steps mean an agent. The order matters for T-16, which the second rule alone would send to a gate, and which the first rule refuses.

Example `decision-table` (Python 3.12.15 · pydantic 2.14.4), passing in Edition 2026.11.6:

```python
"""The decision table for chapter 12: every task in the set, with the author's readings (judgement, not measured), the
design the rules give, and how the task's recorded run ended. The counts at the end are the ones the chapter quotes.
No model is called."""
import json

from lib.models import RECORDED, load_recording
from lib.pipeline import ONE_CALL_SHAPE, REFUSED, TASK_SHAPES, design

yes_no = {True: "yes", False: "no"}
manifest, _ = load_recording("task-set")
stored = {row["task"]: row for row in manifest["tasks"]}
replies = [json.loads(line) for line in
           (RECORDED / "task-set" / "replies.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

print("task | steps known | exploration | wrong change | auto check | person | design | recorded ended | recorded done")
for task_id, s in TASK_SHAPES.items():
    rec = stored[task_id]
    print(f"{task_id} | {yes_no[s.steps_known]} | {yes_no[s.exploration]} | {s.wrong_change} | "
          f"{yes_no[s.auto_check]} | {yes_no[s.person]} | {design(s)} | {rec['ended']} | {yes_no[rec['done']]}")

pipelines = [t for t, s in TASK_SHAPES.items() if design(s) == "fixed pipeline"]
agents = [t for t, s in TASK_SHAPES.items() if design(s) == "agent with gates"]
refused = [t for t, s in TASK_SHAPES.items() if design(s) == REFUSED]
print(f"rows with design 'fixed pipeline': {len(pipelines)}")
print(f"rows with design 'agent with gates': {len(agents)}")
print(f"rows with design 'one model call': {sum(design(s) == 'one model call' for s in TASK_SHAPES.values())}")
print(f"rows the harness refuses: {len(refused)}")
print(f"pipeline rows the recorded agent finished and passed: "
      f"{sum(stored[t]['ended'] == 'finish' and stored[t]['done'] for t in pipelines)}")
print(f"agent rows the recorded agent finished and passed: "
      f"{sum(stored[t]['ended'] == 'finish' and stored[t]['done'] for t in agents)}")
print(f"rows done in the recording: {sum(stored[t]['done'] for t in TASK_SHAPES)}")
print(f"one-call shape, not in the set: {design(ONE_CALL_SHAPE)}")
print(f"largest request in the recording, prompt tokens: {max(r['prompt_tokens'] for r in replies)}")
print(f"context window in the recording, tokens: {manifest['n_ctx']}")

assert pipelines == ["T-01", "T-02", "T-03", "T-04", "T-05", "T-10", "T-12", "T-14", "T-20"]
assert design(ONE_CALL_SHAPE) == "one model call"
assert refused == ["T-16", "T-18"]
assert max(r["prompt_tokens"] for r in replies) < manifest["n_ctx"]
```

Output:

```text
task | steps known | exploration | wrong change | auto check | person | design | recorded ended | recorded done
T-01 | yes | no | low | yes | no | fixed pipeline | step_cap | no
T-02 | yes | no | low | yes | no | fixed pipeline | step_cap | no
T-03 | yes | no | low | yes | no | fixed pipeline | ask_user | no
T-04 | yes | no | low | yes | no | fixed pipeline | finish | yes
T-05 | yes | no | low | yes | no | fixed pipeline | finish | yes
T-06 | no | yes | low | yes | no | agent with gates | step_cap | no
T-07 | no | yes | low | yes | no | agent with gates | finish | no
T-08 | no | yes | low | yes | no | agent with gates | finish | no
T-09 | no | yes | low | yes | no | agent with gates | finish | yes
T-10 | yes | no | low | yes | no | fixed pipeline | step_cap | no
T-11 | no | yes | high | yes | no | agent with gates | step_cap | no
T-12 | yes | no | low | yes | no | fixed pipeline | ask_user | no
T-13 | no | yes | low | yes | no | agent with gates | step_cap | no
T-14 | yes | no | low | yes | no | fixed pipeline | finish | yes
T-15 | no | yes | low | yes | no | agent with gates | ask_user | no
T-16 | yes | no | high | yes | yes | not a design choice: the harness refuses | step_cap | no
T-17 | no | no | high | no | yes | agent with gates | ask_user | no
T-18 | yes | no | high | yes | no | not a design choice: the harness refuses | ask_user | yes
T-19 | no | no | high | no | yes | agent with gates | ask_user | no
T-20 | yes | no | low | yes | no | fixed pipeline | ask_user | no
rows with design 'fixed pipeline': 9
rows with design 'agent with gates': 9
rows with design 'one model call': 0
rows the harness refuses: 2
pipeline rows the recorded agent finished and passed: 3
agent rows the recorded agent finished and passed: 1
rows done in the recording: 5
one-call shape, not in the set: one model call
largest request in the recording, prompt tokens: 6556
context window in the recording, tokens: 8192
```

The rules give `9` fixed pipelines, `9` agents with gates, and `2` refusals. The pipelines are T-01 to T-05, T-10, T-12, T-14 and T-20: the edits a person could write before the run, where a test then decides the result. The agents are the open-ended fixes and new functions, T-06 to T-09, T-11, T-13 and T-15, and the two stop tasks T-17 and T-19, where the steps are not known and a person has to decide. The table predicts where to look, not how a run will end.

The recorded agent bears that out only partly. Of the nine pipeline rows, it finished and passed `3` of them: T-04, T-05 and T-14. The other six hit the step cap or stopped with a question. Of the nine agent rows, it finished and passed `1`, T-09. In all, `5` of the twenty runs were done. The rule says a pipeline for the nine rows, and the pipeline has been built and run on only three of them. The other six are predictions, and the record gives them no pipeline result to compare.

T-16 is the row that shows what goes wrong when the order is ignored. Its task renames `parse_quantity` to `parse` and removes the old name. Chapter 6's gate refuses that change, because a removed public name is never the agent's to change, and the gate would refuse it when the diff is read at `finish`. The recorded agent never asked. It tried edits and writes until the step cap, and every one of them failed. An agent behind a gate would spend its whole budget on a change the harness will not apply. So T-16 is a refusal like T-18, and its right ending is a question to the maintainer that asks them to take the rename up as a separate decision. That is the question the scorer's stop word `approv` looks for. Put T-16 among the agent rows and the table is right on paper and wrong in the run.

T-18 is the refusal the other way round. Its edit is under `.github/`, which the gate refuses without a question, so the harness decides it and the design does not. The row records the harness's decision, and the scorer's count for this run is a limit ([chapter 10](#t18-path)), not a good ending.

The one-model-call row needs a case, and the set has none. A single model call fits a step that needs a model's judgement, with no tool and no loop, and whose output a person reads afterwards. Here is one that is not in the set: a summary of T-02's change for the pull request, written from the diff. Its steps are known, since the diff goes in and one paragraph comes out. No check decides whether the paragraph is good, and no yes is needed, because the maintainer reads it after the change. A pipeline cannot write it, because the wording is a judgement a person makes. An agent would add steps that check nothing. Anthropic's post makes a related point: "For many applications, however, optimizing single LLM calls with retrieval and in-context examples is usually enough" ([Anthropic, "Building effective agents"](https://www.anthropic.com/engineering/building-effective-agents)). The rules give `one model call` for that summary, and the example asserts it. No task in the set reaches the row, and the reason is that each task has a check that decides it, a person's yes that sends it to a gate, or steps nobody can name in advance. Every row of the set falls into one of those three, so the count is `0`. This chapter has no recorded single reply for the row, and it runs no new model to make one.

**Working rule:** Sort each task in this order before you choose a design: a refusal is a question to a person, not a design; a person's yes is an agent behind a gate; known steps with a check are a pipeline; known steps without a check are a single call whose output a person reads. Open steps are an agent, and then you count its stops by kind, as [chapter 10](#testing-the-agent) does, before you believe the design works.

## Decisions this chapter made {#design-decisions}

- The default for known steps with a check is a pipeline, built and measured before any agent. This follows the advice to start with the simplest design. It is a rule of thumb.
- Pipeline actions and agent model calls are counted apart and never priced, for the reason in [chapter 11](#cost-not-money).
- A refusal comes before a person's yes, because a yes cannot lift a forbidden change. Chapter 6 gives the reason.
- The readings are the author's judgement. A reader who disagrees changes a reading in the example and reruns it, and the rules stay as they are.
- The recorded runs are reported as they ended, and T-02's record is a repeated failure, not a near miss.
- No split is recommended for this case. No task reaches the context condition, and the book does not measure a split against one loop.
- The one-call design has a case, but it is not in the set, and its output is not checked by a test. Only the rule is shown.

What was learned is narrower than the rules suggest. Most of the set's known-step tasks are pipelines on paper, and only three have been run as one. The stop tasks were judged by their questions, and the scorer that did the judging is the weakest part of the case.

**Working rule:** Treat a rule's pipeline as a prediction until a run has measured it, and write down where its stop goes before you build it.
