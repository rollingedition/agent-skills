---
title: "Agent Harnesses"
chapter: "Hand a subtask to a child, and hand back a stop"
chapter_id: subagents-and-handoffs
book: agent-harnesses
edition: 2026.11.4
verified: 2026-11-20
edition_code: QTC9-C576
canonical: https://rollingedition.com/agent-harnesses/subagents-and-handoffs
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Hand a subtask to a child, and hand back a stop,” chapter 8 of Agent Harnesses, Edition 2026.11.4, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/subagents-and-handoffs. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Hand a subtask to a child, and hand back a stop

By the end of this chapter you can give a subtask to a child loop with a step budget of its own, and get back a summary and a stop reason in place of the child's whole transcript. You'll also make a stop reach a person: a run that the stop rules end as stuck goes to a parent, which puts the stop's question to the maintainer who filed the issue.

Take task T-02 from the case: in `unitcraft`, a small units library, a negative amount loses its thousands separator, and the maintenance agent has to fix it. The run reads `unitcraft/format.py` and makes two edits to it. Both edits fail, because the old text they name isn't in the file as written, so the test result stays where it was. [Chapter 2](#stop-rules) ends a run like that once the rules see no progress. [Harness v1](#v1-v2) ran T-02 to its step cap in the `task-set` recording. Replayed with both of chapter 2's stop rules, the same replies end this run as `no_progress at step 5 of 16`. The stop does its job, but it leaves the maintainer with a log and no account of what the agent was trying. Someone has to read the log to find out.

Size is the second problem. Finding where a rounding rule lives means reading several files, and every file the agent reads stays in the context its next step carries. A side task like that is better done in a context of its own, which returns only what the parent needs. [Anthropic's subagent documentation](https://code.claude.com/docs/en/sub-agents) describes that split for its product: the subagent does the work in its own context and returns only the summary.

This chapter builds the child for that case. A child is the same loop, with a budget of its own. In this book, a *handoff* is a run's end with a question back to a person, instead of a finish: either the model's own `ask_user` call, or the harness's structured handoff after a stop, which carries the stop reason, what the run tried and a question. A child returns its handoff to its parent: how it ended, what it tried, which files it read and changed, and either its summary or the question it stopped on. It never returns its transcript. A stop that ends a child reaches the maintainer as a question.

## A child is a loop with its own budget {#child-loop}

A side task in the case, such as finding where a rounding rule lives, can take steps that the parent's budget should not pay for. A child is the loop from [chapter 1](#tools-and-a-loop), started by a parent in the middle of its own run. It has the same tools and the same stop rules, and it keeps a transcript of its own. What differs is the count. The child's budget counts the child's own model calls, from its first call, so the parent's steps don't pay for the child's work, and a child that loops runs out of its own budget. That is the count [chapter 5](#context-budgets) promised a child: its own steps, not the parent's. A child's `run_tests` goes through the same sandboxed test runner as its parent's, with the caps, clean environment and no conftest files that [chapter 7](#sandbox-and-secrets) describes, because the child is given the same tool set. The path is `run_tests` in `lib/tools.py`, then `run_pytest` and `run_command` there, then `run_sandboxed` in `lib/sandbox.py`. No example runs a child's command any other way.

Give the child 4 steps and run it on T-01. The `task-set` recording's first steps, from the model of [chapter 1](#tools-and-a-loop), replay for it, so the child does what the recorded run did at the start.

Example `child-with-budget` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
"""A child loop on T-01 with a budget of 4 steps. The budget counts the child's own model calls, and it ends the child
as step_cap with no finish. The child's requests match the recording's first four steps, so they replay."""
from lib.case import load_tasks
from lib.models import ReplayModel
from lib.subagents import run_child
from lib.tools import V1
from lib.trace import IdCounter

BUDGET = 4
task = load_tasks(only=["T-01"])[0]
child = run_child(ReplayModel("task-set", "T-01"), task, V1, budget=BUDGET, ids=IdCounter())
print("child budget, steps:", BUDGET)
print("child steps:", child.handoff.steps)
print("child result:", child.handoff.ended)
print("child tools:", ", ".join(child.tool_names))
print("child steps, in order:", *child.trace, sep="\n  ")
child.run.close()
assert child.handoff.ended == "step_cap" and child.handoff.steps == BUDGET
```

Output:

```text
child budget, steps: 4
child steps: 4
child result: step_cap
child tools: list_files, read_file, run_tests, write_file, edit_file, ask_user, finish
child steps, in order:
  step 1: list_files: 25 files
  step 2: read_file: 23 lines
  step 3: edit_file: error: old text not found in unitcraft/format.py
  step 4: read_file: 23 lines
```

The budget, not the tools, ended this child: it used all its steps and never called `finish`. Its budget counts model calls, `4` of them here against a budget of `4`, and the harness ends the child as `step_cap`. Its tools are the full tool set v1, `list_files, read_file, run_tests, write_file, edit_file, ask_user, finish`, so the budget is what holds the child back, not a smaller tool set.

Those `4` steps are the child's whole run. It lists the files, reads one, tries an edit that fails because the old text isn't in the file as written, and reads the file again. Nothing in the budget cares which of those steps was useful. It counts them.

A parent can start the same child itself, through a tool. In the next example the parent is a loop with two tools, `start_child` and `ask_user`. It starts the child on T-02 under both stop rules, reads the child's handoff as the tool's result, and asks the person the question the handoff carries.

Example `parent-starts-child` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
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
```

Output:

```text
child budget, steps: 16
child steps: 5
child result: no_progress
parent steps: 2
parent result: ask_user
parent tools: start_child, ask_user
question asked matches the handoff: yes
child transcript, characters: 5408
handoff in parent context, characters: 436
parent context at last step, characters: 1041
child file text in parent context: no
parent steps, in order:
  step 1: start_child: child no_progress at step 5
  step 2: ask_user: ask_user
```

The parent's question is the child's, word for word, and the child's file text is not in the parent's context. The child takes `5` steps of its own budget, and the parent takes `2`, one to start the child and one to ask. The parent receives a handoff of `436` characters, where the child's transcript holds `5408`.

The end is a stop like any other. A child that reaches its budget ends without a finish, and the handoff in [the section on stops](#a-stop-handed-back) carries that end to the parent, which is where the next decision goes.

**Working rule:** Give each child a budget of its own, counted in its own model calls and never shared with the parent. Set it from runs that finished on the task set, not from a guess. A budget below what finished runs need turns finished work into stops.

## A brief with four parts {#brief}

The brief is the job as the child receives it. Here the child gets only the issue text: the T-02 child in `summary-to-parent` starts from the task's own issue, and nothing a parent wrote. [Anthropic's account of its multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) names four parts that each subagent's brief needs: an objective, an output format, guidance on the tools and sources to use, and clear task boundaries. Written to those four parts, a brief for a T-02 child might read:

```text
Objective: find out why the two edits to unitcraft/format.py left the test result where it was.
Output format: a short summary, then the files read and the files edited.
Tools and sources: read_file and run_tests on the scratch copy; edit_file only on unitcraft/format.py.
Boundaries: do not change a test or any file other than unitcraft/format.py. If the fix needs a public name changed, call ask_user instead of editing.
```

Each part guards against a failure the T-02 case makes likely. The objective keeps the child on the two edits, and off the rest of the library. The output format lets the parent read the result in one pass, with the files at the end, where it looks for them. The tools and sources line says which file the child may edit. The child in these examples has the full tool set v1, `write_file` included, so that line is text the parent writes and nothing here enforces it. The handoff's `files changed` line shows afterwards which files the child changed, and its `edits failed` line how many edits did not apply. The boundaries are the part a maintainer checks first, because the visible tests are the check, and an edit to a test would pass without a fix.

The brief is text the parent writes, and this chapter doesn't measure it. The same account reports, as an observation and not a measurement, that subagents given vague tasks sometimes duplicated one another's searches, and that an explicit brief was the vendor's fix. No example here tests a vague brief. What the brief does make checkable is the boundary. The handoff in [the section on what comes back](#what-comes-back) lists the files the child read and changed, and those can be set against the boundaries line by line.

**Working rule:** Write all four parts into a brief before a child starts, and write the boundaries as files and tools, not as intentions. A brief that can't say when the child is done, or which files it may edit, isn't ready to send.

## What comes back {#what-comes-back}

The T-02 run leaves a transcript of every file it read, every failed edit and every test run, and that is far more than its parent needs back. The parent needs the child's result, and enough of the child's path to judge the result. It doesn't need the reads. A stopped child needs the same treatment, with a stop reason and a question added.

Run T-02 as a child under both stop rules, with the task set's step cap, and print what the parent receives beside the size of the child's transcript.

Example `summary-to-parent` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
"""T-02's recorded run as a child, with both stop rules and the task set's step cap. The parent gets the
handoff's fields and not the child's transcript; the example prints the size of each."""
from lib.case import load_tasks
from lib.loop import Stops
from lib.models import ReplayModel
from lib.subagents import characters, run_child, tokens
from lib.tools import V1
from lib.trace import IdCounter

RULES = Stops(repeat_limit=3, no_progress_limit=2)
task = load_tasks(only=["T-02"])[0]
ids = IdCounter()
ids.next("run")  # the recording numbers its runs in task order, so T-02 is run-0002: skip T-01's number
child = run_child(ReplayModel("task-set", "T-02"), task, V1, budget=V1.step_cap, ids=ids, stops=RULES)
h = child.handoff
print("child result:", h.ended, "at step", h.steps, "of", h.budget)
print("transcript messages:", len(child.transcript))
print("child transcript, characters:", characters(child.transcript))
print("child transcript, estimated tokens:", tokens(characters(child.transcript)))
print("parent receives, characters:", len(h.text))
print("parent receives, estimated tokens:", tokens(len(h.text)))
print("saved by the handoff, characters:", characters(child.transcript) - len(h.text))
print("what the parent receives:")
print(h.text)
child.run.close()
assert task.issue not in h.text and len(h.text) < characters(child.transcript)
```

Output:

```text
child result: no_progress at step 5 of 16
transcript messages: 12
child transcript, characters: 5408
child transcript, estimated tokens: 1803
parent receives, characters: 436
parent receives, estimated tokens: 146
saved by the handoff, characters: 4972
what the parent receives:
child: child-0001
ended: no_progress
steps: 5 of 16
tried: edit_file 2, list_files 1, read_file 2
files read: unitcraft/format.py
files changed: none
edits failed: 2
stop: no_progress (edit_file, 2 edits in a row left the test result unchanged: 8 failed, 22 passed)
question: The last 2 edits left the test result unchanged (last result: 8 failed, 22 passed). Should a person look at unitcraft/format.py, or should the agent keep going?
```

The parent gets the handoff, and nothing else. The child ended as `no_progress at step 5 of 16`, and the transcript it kept runs to `5408` characters. The handoff the parent reads is `436` characters.

The handoff's files changed line reads none, and its edits failed line reads 2. Both edits named `unitcraft/format.py`, but the file's bytes did not change, so the changed line leaves it out and the failed count says the edits didn't apply.

In tokens, the same gap reads `1803` against `146`. Those are estimates made with the rule from [chapter 5](#context-budgets), not counts from the model's tokenizer, and this chapter uses them only to compare sizes.

The handoff's lines come in a fixed order: the child's ID, how it ended, its steps against its budget, the tools it tried and how often, the files it read, the files it changed, the number of its edits that failed, then the stop reason and the question. A child that finishes gives its summary in place of the stop and the question. Finished children are counted, but their summaries are not printed, so that line appears in no output. The example checks that the issue's text doesn't appear verbatim in the handoff, so the parent works from what the child did, not from the task's wording.

What the parent does with the handoff is the parent's choice, and this chapter doesn't script it. This chapter's code builds one choice: the parent puts the question to the maintainer. The same wiring could start a second child with a narrower brief that names a file the handoff lists, or answer from the fields alone. No example builds either. Each of those leaves the child's transcript out of the parent's context, which is the reason for the handoff in the first place.

The child's own record is kept, and it is what [chapter 11](#traces-and-cost) traces. The parent doesn't open it.

**Working rule:** Return to the parent a child's ID, how it ended, its counts, its files and its stop or its summary, and nothing more. Keep the transcript in the child's own record, where a trace can read it.

## A stop handed back {#a-stop-handed-back}

The T-02 run ends stuck, and a stop alone doesn't tell the maintainer what to decide. [Chapter 2](#stop-rules) gave each stop a name and a reason, but someone still has to choose between taking the task from the agent, giving it more steps and trying another approach. That someone is the maintainer who filed the issue. So a stop that the harness can't resolve becomes a handoff to a parent, and the parent asks the maintainer.

The alternative is to log the stop and drop the run. That keeps the parent's context small, and it leaves the decision with nobody. The handoff keeps the decision with the maintainer, and costs the parent one short step in the runs below.

For the three stops that end a child stuck, `step_cap`, `repeated_call` and `no_progress`, the harness builds the handoff from the run's own record: its trace, its streak of repeated calls and its test counts. The stop reason, the counts and the question all come from that record. No model writes them, so a replayed run gives the same handoff every time. The parent is a loop of its own, with a small step budget and two tools, `ask_user` and `finish`. In a live design the parent would be a model that words the question to the maintainer. Here a scripted parent passes the question on exactly as the handoff gives it, so the run shows the wiring and not a model's judgement.

A child that ends some other way is not handed back. A run that ends as `no_tool_call`, for example, gives a handoff with no stop reason and no question, so the parent has nothing to put to the person. No run here ended that way (`0` of the runs), so no example shows it.

Run every task-set run as a child under both stop rules. Each child that ends stuck goes to a parent, which asks the person its question.

Example `handoff-on-stuck` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
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
```

Output:

```text
child runs: 20
  finish: 6
  ask_user: 1
  step_cap: 1
  repeated_call: 1
  no_progress: 11
  no_tool_call: 0
done with the rules: 5
ended with finish or ask_user: 7
done among the handed back: 0
handed back to a parent: 13
  step_cap: 1
  repeated_call: 1
  no_progress: 11
handed back, tasks: T-01, T-02, T-03, T-06, T-10, T-11, T-12, T-13, T-15, T-16, T-17, T-19, T-20
parent asked the person, with the handoff's question: 13
child steps, all handed back: 83
parent steps, all handed back: 13
child transcripts, characters: 95252
handoffs the parents read, characters: 5874
saved by the handoffs, characters: 89378
```

None of the runs a stop handed back was done. The rules hand back `13` of the `20` runs, and none of those is done. Each one reaches a parent, and the parents put the question to the person `13` times, once for each. The stop that comes up most is `no_progress`, the same stop T-02 ended on.

The stop rules cost no finished work. `7` runs ended with `finish` (`6`) or with `ask_user` (`1`), and all `5` done runs are among them, because none of the handed-back runs was done. The other runs in that group are not done, and none of them ended on a stop rule, so no handoff covers them. A run that ends with `finish` or `ask_user` never reaches a parent under these rules, whether or not it was right to end there.

The handed-back runs are `T-01, T-02, T-03, T-06, T-10, T-11, T-12, T-13, T-15, T-16, T-17, T-19, T-20`. Between them their children took `83` steps, and their parents took `13` steps, one each, the call that asks the person.

The children's transcripts held `95252` characters, and the parents read `5874` characters of handoff between them. Every handed-back child is checked to give a stop reason and a question. That checks the shape of the handoff, and it doesn't check that the question is the right one to ask.

The question for the T-02 run ends: "Should a person look at unitcraft/format.py, or should the agent keep going?" It names the file that both failed edits named, so the maintainer knows where to look without opening the transcript. The handoff's files changed line says no file changed, so the question points at a file the edits named but never changed.

One caveat, said once: a handoff says that a run stopped and why. It doesn't say the task could not be finished. This book counts a handed-back run as not done, as the example does.

**Working rule:** Hand every stuck stop (`step_cap`, `repeated_call`, `no_progress`) to a person as a question, with its stop reason, its counts and its files. A parent works from the handoff. The child's record stays with the child, where a trace can read it.

## Two designs, and whose numbers {#designs}

Which design a split should use depends on what the parent has to do with the child's result. Two designs are in wide use, and they differ in what happens to the conversation. In [this chapter's design](#what-comes-back), the child returns a result and stops. In an SDK handoff, the conversation moves to another agent. The SDK uses the word handoff for the second design, which is not this chapter's meaning of it. Nothing in this section was run here, and its figures belong to their sources.

The [OpenAI Agents SDK's documentation on handoffs](https://openai.github.io/openai-agents-python/handoffs/), for SDK 0.24.0 as fetched in November 2026, describes the second. A handoff is a tool the model calls, named after its target; its example is `transfer_to_refund_agent`. The receiving agent sees the whole earlier conversation unless an input filter changes what it sees. For a specialist that should return a result without taking over the conversation, the same page recommends wrapping the agent as a tool, with `Agent.as_tool`. Its nested history, which summarizes the earlier conversation, is an opt-in beta and off by default.

The [Claude Code subagent documentation](https://code.claude.com/docs/en/sub-agents), as fetched in November 2026, describes the first kind. A subagent has a limit on agentic turns, which this book would call steps, set as `maxTurns`. When a subagent reaches the limit, its output comes back marked partial, and the parent can resume it. The page says the partial marking "requires Claude Code v2.1.246 or later"; nothing here was run at that version. The built-in subagents inherit the parent's permission rules, and most run with a restricted tool set. A custom subagent has its own tools and independent permissions. The shape matches this chapter's budget, with the handoff playing the part of the partial result.

The measurement this section quotes comes from the company that built the system it measures. In June 2025, [Anthropic's account of its research system](https://www.anthropic.com/engineering/multi-agent-research-system) reported that "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval." That comparison sets a multi-agent system against one agent, with a different model in the subagents, on an eval whose metric the post doesn't name. The post says its evaluations favor breadth-first queries, where many independent directions can be pursued at once.

The same post gives a second measurement, on the BrowseComp evaluation: "token usage by itself explains 80% of the variance". It says that multi-agent systems work mainly because they spend enough tokens to solve the problem. Its own data put agents at about four times a chat's tokens and multi-agent systems at about fifteen times. It also says that some domains where agents must share one context, or depend on each other in many ways, are not a good fit, and that its lead agent ran subagents in batches, waiting for each set to finish. A split isn't parallel because it has several agents.

A widely read argument against splitting comes from [Walden Yan's essay "Don't Build Multi-Agents"](https://cognition.ai/blog/dont-build-multi-agents), published by Cognition in 2025. Its first principle is "Share context, and share full agent traces, not just individual messages." The handoff breaks it: it passes a child's fields and its summary or stop, and never its full trace. The essay's second principle is that actions carry implicit decisions, so agents working apart can act on conflicting ones. It's an essay, one practitioner's judgement.

The essay's simplest way to follow its principles is one linear agent with a continuous context. For very long tasks it proposes a model that compresses the history into key details, events and decisions, and it says that this is hard to get right. That is close to chapter 5's compaction and to this handoff. The essay also accepts a subagent that answers a well-defined question, usually without writing any code.

This chapter's example child does write code: T-02's child edits `unitcraft/format.py`, which is the case the essay argues against. Here one child edits and the parent doesn't edit that file, so the conflict the second principle describes doesn't arise in these examples. The child's reasons for its edits still don't reach the parent, and the essay's objection to that stands. The book builds the child anyway, because the T-02 case needs a child that can change the library. The split pays when a result can be used without the reasons behind it, which is the case the product documentation describes.

We recommend a child for a side task whose result stands alone, and one loop for work where the parent and the child would edit the same files.

**Working rule:** Use a child when its result can be used without its reasons: a fact, a list of files, or a stop with its question. Keep one loop when the parent must act on the files the child would edit. This book doesn't measure a split against one loop, so the rule rests on the argument above, not on a measurement.

## What goes wrong in production {#splits-in-production}

Splitting work brings failures that a single loop doesn't have. The first is a budget in the wrong unit. A budget counted in seconds stops a child for a slow test run as readily as for a loop, and a replay can't repeat it, because the same run takes a different time each time. That is why this chapter counts model calls and no time.

The second is a parent that decides for the person. The parent in [handoff-on-stuck](#a-stop-handed-back) has `finish` as well as `ask_user` among its tools, so a model that thinks it knows the answer can end a stuck run without asking anyone. In production, a parent handed a stop should have only the means to ask, and a stop that reaches it should always end with a question to the maintainer.

The third is a split the parent can't reconcile. Two children that edit the same file can each hand back a clean summary, and the parent then has to open both records to see that their edits disagree. The handoff doesn't show that disagreement by itself, which is the point of [the counter-view](#designs).

The fourth is cost that doesn't show. A child's tokens are its own, and the vendor's figure puts a multi-agent system at about fifteen times a chat's tokens. Trace each child's tokens on its own record, as [chapter 11](#traces-and-cost) does, or the cost of a split never reaches the parent's count.

**Working rule:** Count a child's budget in model calls, give its parent only the means to ask, and check each split's edits against the files the other children changed before you merge them. Trace each child's tokens on its own record, so a split's cost is counted where it is spent.

## Decisions this chapter made {#subagent-decisions}

For the maintainer, the change is that the T-02 stop now arrives as a question about one file. It used to end as a log that the maintainer had to read, with no decision attached. Under this design it reaches the maintainer with its files and a question that names the file to look at. Each choice below is open to change, and each one changes what the maintainer sees when a run goes wrong. The first three decide what a child may spend, what it returns and where a stop's reason comes from. The last three decide when a child is worth splitting off, and who answers when it can't finish.

- A child's budget counts its own model calls, and the parent's count doesn't include them.
- A child returns fields and its summary or stop, never its transcript. The transcript stays in its own record.
- A stop's reason, counts and question come from the run's record, built by code, so a replay gives the same handoff.
- A stuck child goes to a parent with a small step budget, which asks the maintainer who filed the issue through `ask_user`.
- A child is for a side task whose result stands alone. Work where the parent and the child edit the same files stays in one loop.
- A stop that reaches a person as a question is more useful than a stop that ends in a log. [Chapter 12](#when-an-agent-is-the-wrong-design) takes up the case where no split, and no agent, is worth its cost.
