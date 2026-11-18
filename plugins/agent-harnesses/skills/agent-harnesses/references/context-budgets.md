---
title: "Agent Harnesses"
chapter: "Keep the context useful as the task grows"
chapter_id: context-budgets
book: agent-harnesses
edition: 2026.11.1
verified: 2026-11-16
edition_code: CBDA-H5E9
canonical: https://rollingedition.com/agent-harnesses/context-budgets
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/reuse
attribution: "“Keep the context useful as the task grows,” chapter 5 of Agent Harnesses, Edition 2026.11.1, examples passed Nov 16, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/context-budgets. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Keep the context useful as the task grows

By the end of this chapter you can work out how much room a run's prompt has, estimate a prompt's size when the harness cannot count it exactly, and compact a run's older steps without cutting a tool call away from its result.

The model reads its whole prompt on every step: the system prompt, the tool schemas, the issue, and everything the run has done so far. That prompt has to fit in the window the model was loaded with, and the reply has to fit in the same window. A run that keeps reading files eventually runs out of room.

The problem shows up in the case's longest runs. The maintenance agent for `unitcraft`, the library from [chapter 1](#tools-and-a-loop), reads files, runs the tests and tries an edit, and each read adds a whole file to the prompt. In the recorded task set, T-16 reached the step cap of 16 from [chapter 2](#stop-rules), and its last prompt was the largest of any step in the set. On the recorded counts, that last prompt left 612 tokens to spare, so the recorded runs came closest to the window there. The rest of the chapter covers what the harness must do when a prompt does not fit.

## The window the model has {#window}

The recorded model is Qwen3-4B-Instruct-2507, run from the GGUF file that [chapter 1](#tools-and-a-loop) introduced. The harness loads it with a context of 8192 tokens, and the recording's manifest stores that same value as `n_ctx`. That is a load setting the harness chose. The model itself supports far more: its model card gives a native context length of 262,144 tokens ([model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)), read on the card's main branch. This book runs the model in the smaller window, so the number the budget needs is the one the run loads.

The manifest also stores `max_tokens`, the most the reply may take: 1024 tokens. The reply comes out of the same window as the prompt, so the prompt gets whatever the reply leaves.

The arithmetic is short. 8192 tokens, less 1024 for the reply, leaves 7168 tokens for everything the model reads on one step. The prompt holds the system prompt, the tool schemas, the issue, the notes, the earlier steps and the last tool result, and all of it counts against that budget. A refusal is a tool result like any other: the harness returns its text to the model as a tool message, so it counts against the budget too. This chapter calls it the prompt budget.

Example `budget-counts-tokens` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.1:

```python
"""The context the harness loads the model with, the room the reply keeps, and each run's largest prompt against them.
The point rests on the line of steps over the prompt budget: no recorded step reached it."""
import json

from lib.context import PROMPT_BUDGET, REPLY, WINDOW
from lib.models import RECORDED

folder = RECORDED / "task-set"
manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
steps = [json.loads(line) for line in (folder / "replies.jsonl").read_text(encoding="utf-8").splitlines()]
assert manifest["n_ctx"] == WINDOW and manifest["max_tokens"] == REPLY, "the budget comes from the recorded load settings"

print("load setting, n_ctx, in tokens:", WINDOW)  # the harness's own load setting, not the model's native length
print("reply reservation, max_tokens, in tokens:", REPLY)
print("prompt budget, in tokens:", PROMPT_BUDGET)
print("steps recorded:", len(steps))
# ties go to the later run and step, so the same step is named on every run
largest = max(steps, key=lambda s: (s["prompt_tokens"], s["run"], s["step"]))
print("largest prompt, in tokens:", largest["prompt_tokens"])
print("largest prompt, run:", largest["run"])
print("largest prompt, step:", largest["step"])
print("room left for the reply at the largest step:", WINDOW - largest["prompt_tokens"] - REPLY)
print("steps over the prompt budget:", sum(s["prompt_tokens"] > PROMPT_BUDGET for s in steps))
for task in sorted(manifest["tasks"], key=lambda t: t["task"]):
    mine = [s["prompt_tokens"] for s in steps if s["run"] == task["task"]]
    print(f"{task['task']}: steps {len(mine)}, largest prompt {max(mine)}")
    assert len(mine) == task["steps"], "the stored step count must match the replies"
```

Output:

```text
load setting, n_ctx, in tokens: 8192
reply reservation, max_tokens, in tokens: 1024
prompt budget, in tokens: 7168
steps recorded: 220
largest prompt, in tokens: 6556
largest prompt, run: T-16
largest prompt, step: 16
room left for the reply at the largest step: 612
steps over the prompt budget: 0
T-01: steps 16, largest prompt 4519
T-02: steps 16, largest prompt 4419
T-03: steps 12, largest prompt 3429
T-04: steps 5, largest prompt 2545
T-05: steps 5, largest prompt 2389
T-06: steps 16, largest prompt 6143
T-07: steps 9, largest prompt 4919
T-08: steps 7, largest prompt 3123
T-09: steps 6, largest prompt 2400
T-10: steps 16, largest prompt 5493
T-11: steps 16, largest prompt 3139
T-12: steps 12, largest prompt 3997
T-13: steps 16, largest prompt 4880
T-14: steps 7, largest prompt 2763
T-15: steps 10, largest prompt 3052
T-16: steps 16, largest prompt 6556
T-17: steps 9, largest prompt 2878
T-18: steps 4, largest prompt 1559
T-19: steps 9, largest prompt 4204
T-20: steps 13, largest prompt 4183
```

Before it prints anything, the code checks that the recording's manifest names the same window and reply limit as the harness, and it fails the run when they differ. Then it prints the budget and each run's largest prompt against it.

A hosted API has a much larger window. The context editing page of the Anthropic API docs gives 100,000 input tokens as the default trigger for clearing old tool results ([context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing.md)). A trigger at 100,000 tokens would never fire on a window of 8192 tokens, so this book takes its budget from the load setting of the model it records, and never from a vendor's default.

**Working rule:** Take the window from the load setting the run used, as the manifest records it, and subtract the reply's limit before you set any budget. Never take it from a model's advertised length or a vendor's default, since a budget copied from a larger model lets a run fill the window before the budget acts.

## Where the recorded runs came closest to the budget {#where-tokens-go}

The recording stores the prompt count the model reported for every step, in `replies.jsonl`. The adapter returns that count as `prompt_tokens`, as [chapter 4](#model-adapters) defines the reply, so these are the model's own counts. The harness did not estimate them.

On those counts, no recorded step reached the [prompt budget](#window). Of the 220 recorded steps, 0 went over it. The largest was T-16's last step, and it left 612 tokens of the window spare once the reply's room was set aside. The check reads the recording and loads no model, so anyone can run it without the hardware that made the recording. The same check, run on any new recording, shows at once whether its prompts still fit the budget, which makes it the first thing to rerun after a model change.

That result says less than it seems. The recorded task set ran tool set v1 with nothing between the loop and the model that could shorten or refuse a prompt. Nothing compacted, and no step was ever cut to fit. The counts show that these prompts fit. They do not show what the harness does when a prompt does not fit, and the rest of this chapter is about that case.

**Working rule:** Compare every step's count with the prompt budget before you read anything into a run.

## Estimate the prompt when the harness can't count it {#estimate}

The exact count comes from the model's own tokenizer, which is part of the model file. This book's examples run offline and never open that file, which is about 2.5 GB and not in the book. So the harness estimates. It counts the characters of every message and of the tool schemas, and divides by three, rounding up: one token for every 3 characters.

We chose three by looking at the task-set recording. The first rule we tried was four characters per token. On the 220 task-set steps, four came out under the true count on 216 of them. An estimate under the count is the dangerous direction, because the harness would believe it had room the model did not have. So we moved to three.

Each step's estimate can be set against the count the model reported for that same step.

Example `estimate-vs-recorded` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.1:

```python
"""The estimate of each recorded request against the prompt count the model reported for it. The rule was chosen on
task-set; chapter-5-notes was recorded after the rule was fixed, so its lines are the held-out check. The point rests
on the steps below the recorded count: none, in either recording."""
import json

from lib.case import load_tasks
from lib.context import CHARS_PER_TOKEN, PROMPT_BUDGET, Measured, Notes, characters, estimate, notes_toolset
from lib.loop import Stops, run_task
from lib.models import RECORDED, ReplayModel
from lib.tools import V1
from lib.trace import IdCounter


def replay(recording, tasks, tools, **limits):
    """Every request the recorded runs sent: its messages, its tool schemas and the count the model reported."""
    ids, requests = IdCounter(), []  # the replay rebuilds each request, so each estimate sees the messages the model saw
    for task in tasks:
        model = Measured(ReplayModel(recording, task.id))
        run_task(model, task, tools, ids=ids, **limits).close()
        requests += model.requests
    return requests


def report(name, requests):
    """Prints the comparison of the estimate with the count, labelled with the recording's name, and returns the pairs."""
    pairs = [(estimate(m, t), n) for m, t, n in requests]
    print(f"{name} steps compared:", len(pairs))
    print(f"{name} characters per token, recorded (all steps):",
          f"{sum(characters(m, t) for m, t, _ in requests) / sum(n for _, n in pairs):.2f}")
    print(f"{name} steps where the estimate is above the recorded count:", sum(e > n for e, n in pairs))
    print(f"{name} steps where the estimate is below the recorded count:", sum(e < n for e, n in pairs))
    print(f"{name} lowest estimate divided by the recorded count: {min(e / n for e, n in pairs):.2f}")
    print(f"{name} highest estimate divided by the recorded count: {max(e / n for e, n in pairs):.2f}")
    assert all(e >= n for e, n in pairs), f"{name}: the rule should never count fewer tokens than the model did"
    return pairs


manifest = json.loads((RECORDED / "chapter-5-notes" / "manifest.json").read_text(encoding="utf-8"))
assert manifest["context"]["chars_per_token"] == CHARS_PER_TOKEN, "the held-out recording used the same rule"
print(f"estimate rule, characters per token: {CHARS_PER_TOKEN}")
task_set = replay("task-set", load_tasks(), V1, max_steps=V1.step_cap)
pairs = report("task-set", task_set)
# four is the rule a reader would try first: it is the one the comparison is against
print("task-set with 4 characters per token, steps below the recorded count:",
      sum(estimate(m, t, 4) < n for m, t, n in task_set))
print("task-set steps whose estimate is over the prompt budget:", sum(e > PROMPT_BUDGET for e, _ in pairs))
print("of those, steps whose recorded count is within the budget:",
      sum(e > PROMPT_BUDGET and n <= PROMPT_BUDGET for e, n in pairs))
report("held-out", replay("chapter-5-notes", load_tasks(only=["T-01", "T-02", "T-06"]), notes_toolset(Notes()),
                          max_steps=16, stops=Stops(repeat_limit=3, no_progress_limit=2)))
```

Output:

```text
estimate rule, characters per token: 3
task-set steps compared: 220
task-set characters per token, recorded (all steps): 3.67
task-set steps where the estimate is above the recorded count: 220
task-set steps where the estimate is below the recorded count: 0
task-set lowest estimate divided by the recorded count: 1.14
task-set highest estimate divided by the recorded count: 1.35
task-set with 4 characters per token, steps below the recorded count: 216
task-set steps whose estimate is over the prompt budget: 3
of those, steps whose recorded count is within the budget: 3
held-out steps compared: 18
held-out characters per token, recorded (all steps): 3.74
held-out steps where the estimate is above the recorded count: 18
held-out steps where the estimate is below the recorded count: 0
held-out lowest estimate divided by the recorded count: 1.22
held-out highest estimate divided by the recorded count: 1.29
```

The estimate was above the recorded count on every one of the 220 steps, and never under it. The ratio of estimate to count ran from 1.14 to 1.35. The recorded counts include the chat template's tokens, which the estimate does not count, so the average of 3.67 characters per token is a ratio for this prompt format, not for the text alone.

The price of the safe side is visible too. Three steps had an estimate over the [prompt budget](#window), and on all three the model's own count was within it. A harness that trusted the estimate would have compacted those steps for no reason.

The rule was chosen on the task-set steps, so those steps cannot test it. The held-out check is the chapter-5-notes recording. It was made after the rule was fixed, and its counts were not used to choose it. Its 18 steps show the same pattern: none under the count, with ratios from 1.22 to 1.29, and 3.74 characters per token. It is the same model and similar text, so it does not show the rule holds for another tokenizer, another language, or code full of symbols.

**Working rule:** Estimate with three characters per token, and check the estimate against the counts the model reports on the first runs of any new model. If the estimate ever falls under the reported count, use a smaller number of characters per token before you trust the budget.

## Put the last result at the end {#last-result}

Where a fact sits in a prompt matters as well as whether it is there. In a 2023 paper, Liu and colleagues found that performance was often highest when the relevant information came at the beginning or the end of a long input, and dropped when it sat in the middle ([Lost in the Middle](https://arxiv.org/abs/2307.03172)). Those models are older than the one this book records, so the paper describes a pattern in older models, not what Qwen3-4B-Instruct-2507 does with a long prompt.

The book's layout puts the issue and the notes near the start, and the last tool result at the end, where the model reads it last before it replies. That is the book's design rule. No source here says the last result must come last, and the book has not measured this layout on this model. The paper is the reason for the choice. The [compaction example below](#compaction) prints each message the model is sent on the last call, in order: the system prompt, the issue, the summary, the last call and its result.

The layout has a cost. Compaction puts the summary of the older steps between the issue and the last call with its result, which is the middle of the prompt. By the pattern the paper describes, that is where a model would use information least well. The book accepts that cost.

**Working rule:** Put the issue and the notes first and the last tool result last. Treat that as a design choice, and claim a gain only once a run on your own tasks shows one.

## Compact the older steps, and keep the last pair {#compaction}

When the [estimate](#estimate) goes over the [prompt budget](#window), the harness compacts. Compaction here is local: the harness writes the summary itself, and the model never sees it being written. The older steps become one message with one line per step: the call, its arguments cut to 60 characters, and the first line of its result, also cut to 60 characters. The system prompt and the issue stay as they are. The last step, its call and its result, goes in word for word, so the model sees the most recent evidence in full.

Vendors also offer compaction on their servers. Anthropic's compaction guide describes one: compaction "replaces the older turns of a conversation with a summary that Claude writes on the server" ([compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)). Its on-demand form is a beta, behind the header `compact-2026-09-04`. The book does not use the server form, and nothing in this chapter depends on how it behaves. We read that page and did not run it.

The cut rule is the one that matters for a local harness. The vendor's guide to keeping recent turns states it plainly: "Put the cut where no tool call is left open, with each tool call and its result on the same side" ([keeping recent turns](https://platform.claude.com/docs/en/build-with-claude/compaction-keep-recent-turns.md)). A cut that falls on a tool result leaves that result without the call that asked for it, so the harness refuses such a cut.

Four reads and a finish, under a budget of 2000 estimated tokens, are enough to cross it. That budget is far below the real 7168, on purpose, so that compaction happens on a small task. The real budget is not reached by this task.

Example `compact-keeps-last-result` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
budget, in estimated tokens: 2000
steps: 5
ended: finish
calls compacted: 3
calls still over the budget: 0
fixed part (system prompt, tool schemas, issue), estimated tokens: 1289
messages sent on the last call: 5
message 1, system: You are a maintenance
message 2, user: `format_quantity` drops the trailing
message 3, user: Earlier steps, summarised by
message 4, assistant: <tool_call> {"name": "read_file", "arguments":
message 5, tool: # unitcraft unitcraft parses,
summary of the older steps:
  step 1: read_file({"path": "unitcraft/convert.py"}) -> """convert: change a quantity to another unit of the same di
  step 2: read_file({"path": "unitcraft/units.py"}) -> """The unit table: each symbol with its dimension and its fa
  step 3: read_file({"path": "unitcraft/parse.py"}) -> """parse_quantity: read a quantity written as text, such as
kept call: {"name": "read_file", "arguments": {"path": "README.md"}}
kept result, in lines: 42
cut before the last result alone, clean: False
cut before the last call, clean: True
```

The run compacted 3 older calls, and the last call and its result came through whole: a read of `README.md`, whose result was 42 lines long. The fixed part, the system prompt, the tool schemas and the issue, came to 1289 estimated tokens. Compaction cannot cut that part, so a budget under it cannot be met by any compaction.

Two cuts are printed last. A cut before the last result on its own is refused, and a cut before its call is clean. The code asserts both, so a change to either fails the run.

**Working rule:** Keep the last call and its result together, refuse any cut that falls on a tool result, and check that the fixed part fits the budget before you rely on compaction to make the rest fit.

## Keep notes outside the context {#notes}

Compaction loses detail by design. Anthropic's engineering post on context engineering puts it as a choice: "The art of compaction lies in the selection of what to keep versus what to discard, as overly aggressive compaction can result in the loss of subtle but critical context whose importance only becomes apparent later" ([Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). The same post describes the way round it, with notes kept outside the window, and it reports no measurement of them.

The harness adds a `note` tool. The model writes one line per fact, and the harness sends the notes after the issue at every step. Compaction does not cut them, because they are not part of the older steps. A fact the model writes as a note survives every compaction. A fact that stays only in an older result is kept at most as the first line of that result.

Example `notes-survive` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
steps: 8
ended: finish
compactions: 5
notes written: 3
notes whole in the notes block: 3
lines in the notes block that name the fact (rstrip): 1
summary line for the read of format.py: step 1: read_file({"path": "unitcraft/format.py"}) -> """format_quantity: write a quantity as text, such as ``3.50
```

This example is a script, not the model. A `ScriptedModel` reads four files and writes three notes, each one right after the read it came from. The fact sits on line 18 of the file, and the summary keeps only the file's first line, so the summary's line for that read has the docstring and not the fact. The run compacted 5 times. All 3 notes are whole in the notes block of the last request, and 1 of those lines names the fact. Each note states something the run had read in the case, so a reader can check each one against the case files.

That shows the mechanism. It does not show that a model will write the notes. The next section checks that on a recording of the model.

**Working rule:** Write a fact that a later step needs into a note, not only into the summary. A summary keeps a selection, and the notes are the one place the book keeps a fact whole.

## What the recorded model did with the budget {#recorded-runs}

The recording `chapter-5-notes` was made with tool set v2 from [chapter 3](#tool-schemas), the note tool, and the stop rules from [chapter 2](#stop-rules). Its three runs are T-01, T-02 and T-06. Seven task-set runs reached the step cap of 16 (T-01, T-02, T-06, T-10, T-11, T-13, T-16), and the recording's script names these three as the long runs that each hit that cap. It does not run the other four. We replayed the three runs with compaction on, to see what the model did with the tools and the budget.

Example `recorded-context-use` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.1:

```python
"""The three recorded runs of chapter 5, replayed with the compaction on: how each ended, whether its check passed,
its note calls and compactions, and its largest prompt by the estimate and by the count the model reported. The point
rests on the check lines and the zero counts: no run passed its check, and no run wrote a note or was compacted."""
import json

from lib.case import load_tasks
from lib.context import Compacting, Context, Measured, Notes, estimate, notes_toolset
from lib.loop import Stops, run_task
from lib.models import RECORDED, ReplayModel
from lib.trace import IdCounter

manifest = json.loads((RECORDED / "chapter-5-notes" / "manifest.json").read_text(encoding="utf-8"))
recorded = {t["task"]: t for t in manifest["tasks"]}  # the recording's own check result, stored with each run
ids, passed, notes_total, compact_total, est_max, rec_max = IdCounter(), 0, 0, 0, 0, 0
for task in load_tasks(only=["T-01", "T-02", "T-06"]):
    notes = Notes()
    context = Context(notes=notes)  # the default budget, 7168 tokens, which no run reaches
    model = Compacting(Measured(ReplayModel("chapter-5-notes", task.id)), context)
    # the step cap of 16 and the stop rules are those the recording was made with
    run = run_task(model, task, notes_toolset(notes), max_steps=16, ids=ids,
                   stops=Stops(repeat_limit=3, no_progress_limit=2))
    run.close()
    print(f"{task.id} kind: {recorded[task.id]['kind']}")
    print(f"{task.id} ended: {run.ended}")
    print(f"{task.id} check passed: {'yes' if recorded[task.id]['done'] else 'no'}")
    print(f"{task.id} note calls: {sum(r['tool'] == 'note' for r in run.trace.records)}")
    print(f"{task.id} compactions: {context.compactions}")
    passed += recorded[task.id]["done"]
    notes_total += sum(r["tool"] == "note" for r in run.trace.records)
    compact_total += context.compactions
    est_max = max([est_max] + [estimate(m, t) for m, t, _ in model.inner.requests])
    rec_max = max([rec_max] + [n for _, _, n in model.inner.requests])
print("total note calls:", notes_total)
print("total compactions:", compact_total)
print("runs whose check passed:", passed)
print("largest estimated prompt over the three runs, in tokens:", est_max)
print("largest recorded prompt over the three runs, in tokens:", rec_max)
assert notes_total == 0, "the recorded runs made no note calls"
assert compact_total == 0, "the recorded runs were never compacted"
assert passed == 0, "none of the three recorded runs passed its check"
```

Output:

```text
T-01 kind: fix
T-01 ended: ask_user
T-01 check passed: no
T-01 note calls: 0
T-01 compactions: 0
T-02 kind: fix
T-02 ended: finish
T-02 check passed: no
T-02 note calls: 0
T-02 compactions: 0
T-06 kind: implement
T-06 ended: no_progress
T-06 check passed: no
T-06 note calls: 0
T-06 compactions: 0
total note calls: 0
total compactions: 0
runs whose check passed: 0
largest estimated prompt over the three runs, in tokens: 4012
largest recorded prompt over the three runs, in tokens: 3189
```

The model wrote no notes on any of the three runs, and no run was compacted. The largest prompt the estimate saw was 4012 tokens, and the largest the model reported was 3189. Both are under the [prompt budget](#window).

Each run ended before its context came near the budget, and none of them passed its check. T-01 ended as `ask_user`, when the model asked the person a question. T-01 is a fix task, so that question was a wrong handoff. T-02 ended as `finish`, when the model called finish, and its check did not pass. T-06 ended as `no_progress`, which is the stop rule from [chapter 2](#stop-rules): two edits in a row left the test counts unchanged. So the model stopped two runs itself, both wrongly, and a stop rule stopped the third. Printed run by run, the check results give 0 passes out of the three.

Three runs on three tasks show what happened on those tasks, and nothing about the other seventeen. These runs test neither the budget nor the notes.

**Working rule:** Before you judge a budget or a tool by a recording, check how each run ended. A run that stops early never tests the budget, and a model that never calls a tool never tests the tool.

## Measure the effect instead of quoting it {#measure}

A July 2025 technical report from Chroma, "Context Rot" by Hong, Troynikov and Huber, found that "model performance varies significantly as input length changes, even on simple tasks" ([Context Rot](https://www.trychroma.com/research/context-rot)). The report evaluates 18 LLMs from several vendors, including Qwen3, on its own tasks. This chapter does not re-run those tasks, so it quotes no effect size from them.

The book measures its own runs instead. [Chapter 10](#testing-the-agent) runs the task set on two harness versions and compares them as counts of finished tasks. Harness v2 adds the budget among several other changes, so that comparison cannot credit the budget alone. A child run in [chapter 8](#subagents-and-handoffs) keeps a budget of its own, counted on its own steps.

Each example here measures something else. The budget example measures where the recorded prompts sat, and the compaction and notes examples measure what the harness keeps. None measures how length affects a model's answers, so this chapter does not say that a long prompt costs accuracy.

**Working rule:** Measure how a budget changes your own task set, with the counts the runs report, before you claim that it helps. Quote a published effect only with its setup and its source, and only as that report's result.

## How a budget goes wrong, and how to notice {#production}

Four things go wrong with budgets in practice, and each one can be noticed.

The first is a changed model. A new model may have a different window, tokenizer or reply limit. The budget is then wrong without any error, because the check still runs and still passes against the old number. You notice it when the window in the recording's manifest no longer matches the constant the harness uses, so keep the two linked and fail a run when they differ. The [window section](#window) explains the check.

The second is an estimate that drifts. The estimate is only as good as the characters-per-token rule for the model and the text in front of it. The reply already carries the model's own count, so compare the two on every step of the first real runs, and log the pairs. An estimate under the count is the sign to act on, because the harness then believes it has room it does not have.

The third is a summary that drops what a later step needs. A compacted run can call the same tool again, because the first result is now one line in a summary. The stop rules from [chapter 2](#stop-rules) catch exact repeats, but a near-repeat, such as a read of the same file with a slightly different path, passes them. Count the reads a run makes of the same file, and treat a repeat as a sign that the summary lost something.

The fourth is a notes block that grows. The notes are sent at every step and compaction never cuts them, and nothing caps a note's length or how many there are. A run that writes many notes grows its fixed part until compaction cannot meet the budget. The context counts the calls still over the budget after compaction in `over_budget`, and a count above zero is the sign.

**Working rule:** Log the estimate and the reported count on every step of a real run, and treat an estimate under the count as a fault. When a run asks for a file that its own summary already covers, check what the summary kept before the run reads the file again.

## Decisions this chapter made {#what-this-chapter-decided}

- The prompt budget is the load setting less the reply's room, and it follows the load setting, not the model's advertised length.
- The harness estimates the prompt at three characters per token. The task-set steps chose that rule, and the later chapter-5-notes recording, which did not choose it, shows the same pattern.
- Compaction is local and deterministic, so a replayed run compacts exactly as the original did. The older steps become one line each, and the last call and its result are kept word for word. A cut that falls on a tool result is refused.
- The notes are a tool the model may use. They are sent after the issue at every step, so compaction never cuts them, and the model decides whether to write them.
- The book does not use the vendor's server-side compaction.

The recordings show that the prompts fit, and that the estimate stayed above the count on both sets of steps. [Chapter 10](#testing-the-agent) compares two harness versions as counts, and it cannot credit the budget alone.

**Working rule:** Name the runs a budget or a tool was tested on. A claim about a budget that no run reached is a claim about the design, not about the model.
