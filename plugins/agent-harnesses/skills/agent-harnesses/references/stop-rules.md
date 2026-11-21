---
title: "Agent Harnesses"
chapter: "Stop the loop when it's done or stuck"
chapter_id: stop-rules
book: agent-harnesses
edition: 2026.11.4
verified: 2026-11-20
edition_code: QTC9-C576
canonical: https://rollingedition.com/agent-harnesses/stop-rules
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Stop the loop when it's done or stuck,” chapter 2 of Agent Harnesses, Edition 2026.11.4, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/stop-rules. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Stop the loop when it's done or stuck

By the end of this chapter you can say why any run stopped, from the one word the harness records for it, and add the two rules that end a run which has stopped making progress.

[Chapter 1](#tools-and-a-loop) built a loop that ends a run in one of three ways: the model calls `finish`, the run reaches its step cap of 8, or the model gives no call twice. That covers a model that finishes. It doesn't cover a model that keeps sending the same edit, which is what an edit that can't find its text invites. Chapter 1's tools have no edit, so that case comes from the task set: the 20 tasks that [testing the agent](#testing-the-agent) scores, run with [tool set v1](#tool-schemas), whose tools include edits. In the running case, unitcraft, a small units library whose visible suite gives a count after each change, a stuck run of that kind goes to the cap, and the only record of its end is that the cap ended it. Each lost step is a model call and a line in the transcript that a reviewer has to read. This chapter names the ways the loop ends a run, adds two rules that end a stuck run early, and measures what they do on the task set.

## Ways a run ends {#ways-to-end}

Every run ends for one stated reason, and the harness writes that reason into the run's `ended` field. Two of the reasons are the model's choice: it calls `finish` to end the run, or it calls `ask_user` with a question for the person. Three are limits the harness sets: the step budget, the repeated-call rule and the no-progress rule. The sixth, `no_tool_call`, is set by a model that gives no call. The loop sets these six, and [permission gates](#permission-gates) adds a seventh in chapter 6. The table lists the six.

| `ended` | Set when | Shown by |
| --- | --- | --- |
| `finish` | the model calls `finish`, which ends the run | the task-set counts |
| `ask_user` | the model calls `ask_user` with a question, and no change is made | the task-set counts |
| `step_cap` | the run reaches its step budget | `budget-stops-a-loop` |
| `repeated_call` | the same call comes three times in a row | `repeated-call-stops` |
| `no_progress` | two edits in a row leave the test counts where they were | `no-progress-stops` |
| `no_tool_call` | the model gives no call twice in a row | the task-set counts, where it is 0 |

The task-set counts are the lines the last example in [asking, stopping and counting](#ask-instead) prints. In tool set v1, which the task set uses, `finish` takes only a summary: it ends the run with a summary of the edits the run already made to its scratch copy, and it writes no file. Chapter 1's `finish` also wrote one file before it ended the run. The tool sets this chapter measures do not.

When more than one end applies on the same step, the loop checks them in a fixed order. A `finish` or `ask_user` call is handled first, then the repeated-call rule, then the no-progress rule. The budget applies when the loop runs out of steps, so it is checked last. The order matters only on the step where two ends meet, and the rest of the chapter keeps to the single case.

A reply with no call gets one retry. A second reply with no call in a row ends the run as `no_tool_call`. No example in this chapter reaches it, so nothing here depends on it.

Each end is a value, not a sentence in the last reply, so a report can say which one happened without reading that reply. In production the difference between these ends is hard to see from outside. A run that ends at `step_cap` looks like a slow run that didn't finish, and a reviewer who reads only the final message can't tell it from a run that was about to finish. The `ended` value is what shows the difference in a report, and it is the first thing to check when a run costs more than its task should.

The names matter beyond this chapter. [Permission gates](#permission-gates) is where the change a `finish` call proposes waits until a person says yes. [Subagents and handoffs](#subagents-and-handoffs) turns a stop into a question for a person, and [testing the agent](#testing-the-agent) counts the endings. Each reads these values, so a name changed here would change there too.

We list the endings the harness can observe, not every reason a run can fail. A model that gives a wrong answer and calls `finish` ends as `finish`, and only the [check](#one-task), the hidden test that scores the final copy, shows that it failed. That is why the done count comes from the check and not from the `ended` value, a point the working rule below returns to. The Agent SDK's documentation, [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop), describes its ends the same way: a run that reaches its turn limit ends with a result whose subtype is `error_max_turns` and no final response. In that SDK a turn is one pass through its loop, a model reply with its tool calls, and `max_turns` counts those passes plus one for the final text-only reply. Here that pass is one step. This book keeps "turn" for an exchange with the person who gave the task. The same page warns that a loop with no limit can run for a long time on open-ended prompts. The book doesn't use the SDK, so we cite that page for the design, not for any code.

**Working rule:** Record one `ended` value with every run, and never report a run's result without it. Count a run as done by the rule in [the score](#score), never by its `ended` value alone.

## The budget counts steps {#step-budget}

A model that never calls `finish` gives the loop no reason to stop, so the loop needs a count that does. A [step](#the-loop) is one call to the model and the reply it returns. The step budget is the most steps a run may take, and the loop stops when it reaches that number. Steps are counted, not timed: the loop reads no clock.

The [task set](#testing-the-agent), the 20 tasks this chapter's last example counts, runs on tool set v1 with a budget of 16 steps. Chapter 1 uses a smaller budget, 8.

The chapter 1 recording of T-01 shows the budget at work. The model, Qwen3-4B-Instruct-2507, is an open model, and its replies were recorded and are replayed here, so every run in this chapter gets the same output on every machine. In that recording the model did not finish within eight steps. Its last step was a malformed tool call, which the harness refused. Replay the run under the budget, with no other rule, and the output shows where the cap ends it:

Example `budget-stops-a-loop` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
"""The chapter 1 recorded run of T-01 under its step budget of 8. The budget ends the run as step_cap, with no finish;
the last line shows the model's final step, a call the harness refused, and the budget ended the run after it."""
from lib.case import load_tasks
from lib.loop import run_task
from lib.models import ReplayModel
from lib.tools import CH1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]
run = run_task(ReplayModel("chapter-1-t01", "T-01"), task, CH1, max_steps=CH1.step_cap, ids=IdCounter())
print("budget (steps):", CH1.step_cap)
print("steps:", run.steps)
print("tool calls:", run.tool_calls)
print("ended:", run.ended)
print("last step:", run.trace.lines()[-1])
assert run.ended == "step_cap" and run.steps == CH1.step_cap, "the budget should stop the run on step 8"
assert not run.summary, "a budget stop carries no summary"
```

Output:

```text
budget (steps): 8
steps: 8
tool calls: 8
ended: step_cap
last step: step 8: malformed: error: malformed call
```

The run ends as step_cap after 8 steps, with 8 tool calls, against a budget of 8. The two counts match because each step made one request. The line to keep is the last one. The model's final reply was a call the harness could not parse, and the budget was the only thing that ended the run. Nothing in the record says the model had finished.

A step budget does not bound time, and it does not bound tokens. A tool that hangs holds its step open until it returns, so the timeout belongs to the sandbox, in [sandbox and secrets](#sandbox-and-secrets). A long reply uses more tokens inside a single step, and counting tokens is the work of [context budgets](#context-budgets). The budget bounds model calls and nothing else, so a run that reaches it has used its calls, and nothing more is known about why.

Malformed replies count too. A reply the harness cannot parse is still a model call, so it spends a step, and the budget counts it. A model that keeps producing calls the harness can't read reaches the budget as surely as one that keeps repeating a good call. Both end as `step_cap`, so only the last few steps show which of the two happened: a repeated good call, or calls the harness couldn't read.

**Working rule:** Set the step budget from runs on your own tasks, not from a guess. Take the most steps a passing run needed, leave room above it, and write in the code what that room is for.

## The same call, again {#repeated-calls}

A model that has seen a tool fail can send the same call again and again, and the loop will run each one until the budget ends the run. It is tempting to think the model will notice that it is looping. The ReAct paper, by Yao and colleagues (2022, published at ICLR 2023), reports repetition as a frequent error pattern: in its question-answering runs, the model repeatedly generated thoughts and actions it had already produced. The paper's tasks are question answering and decision making, not code, so it gives us a reason to watch for repetition and no rate for it. [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/html/2210.03629v3) is the source. The harness has to detect repetition itself.

The rule the book uses is simple. Three identical calls in a row end the run as `repeated_call`. A call is identical when it has the same tool name and the same arguments, compared with the keys sorted. The sort matters. Two replies can carry the same arguments with the keys in a different order, and then the raw text differs even though the call does not. At the pinned Python, 3.12.15, `json.dumps` gives two different strings for the same two keys in two orders, `plain dumps equal: False`, and one string when the keys are sorted, `sort_keys dumps equal: True`. That is a probe we ran, not an example in this book, so read it as a check you can repeat.

Three is this book's threshold, not a fixed one. It is a judgement, and the working rule below says when to change it. A parsed call that differs from the one before it starts the count again, and so does a reply with a malformed call block, which has no parsed call to compare. A reply cut off at the token limit, or a reply with no call, leaves the streak as it was. The loop skips the streak check on those replies, so identical calls on either side of one still count together.

T-01 never sends the same call three times in a row, so this example replays T-02, where the model does:

Example `repeated-call-stops` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
"""The recorded run of T-02 with and without the repeated-call rule. Three identical calls in a row end the run as
repeated_call. The rule compares the name and the sorted arguments, so reordered keys still count as the same call."""
from lib.case import load_tasks
from lib.loop import Stops, run_task
from lib.models import ReplayModel
from lib.tools import V1
from lib.trace import IdCounter

task = load_tasks(only=["T-02"])[0]


def replay(stops: Stops):
    ids = IdCounter()
    ids.next("run")  # the recording numbers its runs in task order, so T-02 is run-0002: skip T-01's number
    return run_task(ReplayModel("task-set", "T-02"), task, V1, max_steps=V1.step_cap, ids=ids, stops=stops)


plain = replay(Stops())
print("without the rule, ended:", plain.ended, "at step", plain.steps)
run = replay(Stops(repeat_limit=3))
print("with the rule, ended:", run.ended, "at step", run.steps)
print("repeated call:", run.stuck_on)
print("first of the identical calls: step", run.streak_from)
print("identical calls in a row:", run.steps - run.streak_from + 1)
print("last two steps:", *run.trace.lines()[-2:], sep="\n  ")
assert run.ended == "repeated_call" and run.streak_from == 11 and run.steps == 13
```

Output:

```text
without the rule, ended: step_cap at step 16
with the rule, ended: repeated_call at step 13
repeated call: edit_file
first of the identical calls: step 11
identical calls in a row: 3
last two steps:
  step 12: edit_file: error: old text not found in unitcraft/format.py
  step 13: edit_file: error: old text not found in unitcraft/format.py
```

Without the rule, the run ends as step_cap at step 16. With it, the run ends as repeated_call at step 13. The point is in the last steps: the same `edit_file` call, sent again, failing each time with `old text not found in unitcraft/format.py`. The first of the identical calls came at step 11, and the count reached 3 in a row before the rule ended the run. The example asserts the ending and the step it stops on, so a change that moves the stop fails the run instead of quietly changing the printed output.

A model that alternates a read with an edit never trips this rule, because each read breaks the streak. The next rule is for that case.

The rule is about the same well-formed call coming back unchanged. A broken reply is a different failure, and [tool schemas](#tool-schemas) is where a bad call comes back as a typed error the model can read.

**Working rule:** Compare calls by tool name and sorted arguments, and end the run at three identical calls in a row. Raise the threshold only after your own traces show three identical calls in a row that were making progress. Then measure the higher number on your task set before you keep it.

## No progress across edits {#no-progress}

A model that alternates reads with edits never sends the same call three times in a row, so the [repeated-call rule](#repeated-calls) has nothing to count, even when the run goes nowhere. The signal that fits that case is the test counts. After each edit, the harness runs the visible tests, the case's own test suite, on the [scratch copy](#one-task) and keeps the counts line of the summary it builds, such as `8 failed, 22 passed`. The model never sees that run. The harness keeps it for its own decision.

This is the kind of signal the guidance in [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) asks for. It says it is crucial for an agent to get ground truth from the environment at each step, and a test count is ground truth of that kind. The guidance is an opinion from a December 2024 article, not a measurement.

The rule keeps a count of edits in a row that leave the counts unchanged. The first edit is compared with the counts from before any edit was made. An edit that moves the counts resets the count to zero. A read doesn't touch it. Two in a row end the run as `no_progress`. A failed edit leaves the file as it was, so its counts stay the same, and the rule counts it as no progress.

Run T-01 from the task-set recording, which uses tool set v1 and whose edits fail, twice: once with no rules and once with the no-progress rule set to two edits. Read where each run ends:

Example `no-progress-stops` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
"""The recorded run of T-01 under the no-progress rule. Two edits in a row that leave the test counts where they
were end the run as no_progress. The counts come from the harness's own run of the visible tests after each edit."""
from lib.case import load_tasks
from lib.loop import EDITS, Stops, run_task
from lib.models import ReplayModel
from lib.tools import V1
from lib.trace import IdCounter

task = load_tasks(only=["T-01"])[0]


def replay(stops: Stops):
    return run_task(ReplayModel("task-set", "T-01"), task, V1, max_steps=V1.step_cap, ids=IdCounter(), stops=stops)


plain = replay(Stops())
print("without the rule, ended:", plain.ended, "at step", plain.steps)
run = replay(Stops(no_progress_limit=2))
print("with the rule, ended:", run.ended, "at step", run.steps)
edit_steps = [r["step"] for r in run.trace.records if r["tool"] in EDITS]
print("edits that left the counts unchanged, steps:", " and ".join(str(step) for step in edit_steps[-2:]))
print("counts after the last edit:", run.counts)
print("last two steps:", *run.trace.lines()[-2:], sep="\n  ")
assert run.ended == "no_progress" and run.steps == 5
```

Output:

```text
without the rule, ended: step_cap at step 16
with the rule, ended: no_progress at step 5
edits that left the counts unchanged, steps: 3 and 5
counts after the last edit: 8 failed, 22 passed
last two steps:
  step 4: read_file: 23 lines
  step 5: edit_file: error: old text not found in unitcraft/format.py
```

Without the rule, the run ends as step_cap at step 16. With it, the run ends as no_progress at step 5, on the second of two edits that left the counts unchanged. Those edits are at 3 and 5. Both failed with `old text not found`, so neither moved the counts, which stayed at 8 failed, 22 passed. The last two steps in the output are a read and that second failed edit. The read sits between the two edits and doesn't reset the count, which is why the rule can fire on edits that are not next to each other in the transcript.

The rule reads one line from the test summary: the counts line, such as `8 failed, 22 passed`. It doesn't read which test failed. An edit that fixes one test and breaks another, with the same count, therefore looks like no progress. Comparing the file doesn't help either. A failed edit leaves the file unchanged, but an edit that does change it can still leave the counts the same. We keep the counts because the harness can compare them without reading test names. Check that choice on your own runs, where a swap of one failure for another would show up as a stop.

Two failed edits are enough to stop this run, though a third edit might have worked. We chose two, and the book makes no claim about how often a run that stops this way would have gone on to succeed. In the task set, 11 runs ended this way, and none of them is done, by the rule in [the score](#score).

The failed edit is the failure that [tool schemas](#tool-schemas) addresses. Chapter 3 changes what an edit that can't find its text returns: the nearest lines of the file, so the model can correct its text instead of sending it again, as [edit errors that name the nearest lines](#edit-errors) shows.

**Working rule:** Watch the counts the harness gets from the tests after each edit, not what the model says it changed. Stop a run after two edits in a row that leave the counts unchanged. Record it as `no_progress`, and keep the counts it stopped on beside the run.

## Asking, stopping and counting the endings {#ask-instead}

Once a rule ends a run, nothing in the loop asks the person who gave the task what to do next.

Only `ask_user` asks. The model calls it with a question, the harness hands the question back, and no change is made. The stop rules work differently. A `repeated_call` or `no_progress` stop records the rule that fired and the call or the counts it stopped on, and the run is over. Turning such a stop into a question for a person is the handoff in [subagents and handoffs](#subagents-and-handoffs). What a change may do without a person's yes is the gate in [permission gates](#permission-gates).

The last check in this chapter runs all 20 tasks twice, once as recorded and once with both rules, [repeated calls](#repeated-calls) and [no progress](#no-progress). It prints counts only:

Example `stop-rules-over-task-set` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.4:

```python
"""The task-set recording's 20 runs, replayed as recorded and again with both stop rules. Counts only: which runs hit
the step cap, which rule ended the runs that stopped early, and whether any done task is cut short."""
from collections import Counter

from lib.case import load_tasks
from lib.loop import Stops, run_task
from lib.models import ReplayModel
from lib.tasks import score
from lib.tools import V1
from lib.trace import IdCounter

RULES = Stops(repeat_limit=3, no_progress_limit=2)


def replay(stops: Stops) -> dict:
    """Every task in file order, so the run IDs match the recording's. Maps task ID to (ended, steps, done)."""
    ids, out = IdCounter(), {}
    for task in load_tasks():
        run = run_task(ReplayModel("task-set", task.id), task, V1, max_steps=V1.step_cap, ids=ids, stops=stops)
        out[task.id] = (run.ended, run.steps, score(task, run))
        run.close()
    return out


ENDS = ("finish", "ask_user", "step_cap", "repeated_call", "no_progress", "no_tool_call")
plain, ruled = replay(Stops()), replay(RULES)
capped = sorted(t for t, (ended, _, _) in plain.items() if ended == "step_cap")
ruled_ends = Counter(ended for ended, _, _ in ruled.values())
done = sorted(t for t, (_, _, ok) in plain.items() if ok)
print("task set step cap:", V1.step_cap)
print("runs:", len(plain))
print("step cap without the rules:", len(capped))
print("step cap without the rules, tasks:", ", ".join(capped))
print("step cap with the rules:", ruled_ends["step_cap"])
print("ended early with the rules:", len([t for t in capped if ruled[t][0] != "step_cap"]))
for ended in ENDS:
    print(f"  {ended}: {ruled_ends[ended]}")
print("done without the rules:", len(done))
print("done without the rules, tasks:", ", ".join(done))
print("done with the rules:", sum(1 for _, _, ok in ruled.values() if ok))
print("done with the rules, by finish:", sum(1 for ended, _, ok in ruled.values() if ended == "finish" and ok))
print("finish but not done, with the rules:", sum(1 for ended, _, ok in ruled.values() if ended == "finish" and not ok))
print("done with the rules, by ask_user:", sum(1 for ended, _, ok in ruled.values() if ended == "ask_user" and ok))
wrong = [t for t, (ended, _, ok) in plain.items() if ended == "ask_user" and not ok]
print("ask_user but not done, without the rules:", len(wrong))
print("of those, cut early with the rules:", len([t for t in wrong if ruled[t][0] != "ask_user"]))
assert len(capped) == 7 and all(ruled[t][2] for t in done), "a done task must survive the rules"
assert sum(ruled_ends.values()) == len(plain), "every run has one ending"
```

Output:

```text
task set step cap: 16
runs: 20
step cap without the rules: 7
step cap without the rules, tasks: T-01, T-02, T-06, T-10, T-11, T-13, T-16
step cap with the rules: 1
ended early with the rules: 6
  finish: 6
  ask_user: 1
  step_cap: 1
  repeated_call: 1
  no_progress: 11
  no_tool_call: 0
done without the rules: 5
done without the rules, tasks: T-04, T-05, T-09, T-14, T-18
done with the rules: 5
done with the rules, by finish: 4
finish but not done, with the rules: 2
done with the rules, by ask_user: 1
ask_user but not done, without the rules: 6
of those, cut early with the rules: 6
```

The rules cut stuck runs short without losing a done task. Without them, the budget ends 7 of the 20 runs; with them, only 1 still reaches it.

With the rules on, the most common end was `no_progress`, at 11 runs, and `finish` came next, at 6 runs.

Each done task still passes with the rules on, and the example checks it. Of the 5 done runs, 4 end with `finish` and pass their check, and 1 ends with the `ask_user` on T-18, which is the fifth. The other 2 `finish` runs fail their check, so they are not done.

Without the rules, 6 runs asked a question and were not done. With the rules, 6 of those runs ended earlier, and none of them asked. The one `ask_user` left with the rules on is T-18's, which the scorer counts as done; [chapter 10](#t18-path) shows that it counts only through a word in a path. A stop that ends a run early doesn't make the run right. It ends the run before the wrong question is asked, and that run is still not done. The rules cut the waste; they can't tell a right question from a wrong one.

You can check the output yourself. The six endings with the rules on add up to the number of runs, as the lines of the output show, and the done count is the same with the rules and without them. If the done count ever moves, a rule has cut a run that was going to pass, and the rule is the thing to change. If a run in your own work ends stuck, read it in this order: the `ended` value, then the last few steps, then the first step where a call began to repeat. Those reads take less time than reading the whole transcript.

**Working rule:** Count each run by the `ended` value it recorded, and report the counts with the rules on and off, next to the done count. A stop can only turn a run into one that is not done, so when you change a rule, check that the done count holds before you keep the change.

## Decisions in this chapter {#stop-rules-decisions}

Each of these is a default the book chose, and none is a law. The working rules say when to change one, and a change belongs on your own task set first, where you can count what it did to the done tasks before anyone else relies on it.

- The stop rules are optional and off by default in the loop. A run without them makes the same requests as chapter 1's loop.
- A repeated call is three identical calls in a row, compared by tool name and sorted arguments.
- No progress is two edits in a row that leave the harness's test counts unchanged. The first edit is compared with the counts before any edit.
- A stop ends the run as a result. No stop rule asks a person, and the handoff waits for [subagents and handoffs](#subagents-and-handoffs).
- The step budget counts model calls, malformed replies included. This chapter doesn't count it as a limit on time or on tokens.
- The names of the six endings stay fixed. The gate adds one, in chapter 6.
- A stop that names its rule and its counts is one a reader can check, and a stop that names only the budget sends the reader back through every step.
