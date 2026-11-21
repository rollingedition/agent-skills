---
title: "Agent Harnesses"
chapter: "Give a model tools and a loop"
chapter_id: tools-and-a-loop
book: agent-harnesses
edition: 2026.11.3
verified: 2026-11-20
edition_code: 1CW4-SHG5
canonical: https://rollingedition.com/agent-harnesses/tools-and-a-loop
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Give a model tools and a loop,” chapter 1 of Agent Harnesses, Edition 2026.11.3, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/tools-and-a-loop. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Give a model tools and a loop

By the end of this chapter you can run a model in a loop that gives it three tools: one reads a file, one runs the tests, and one finishes with a changed file. The loop stops when the model finishes, when it runs out of steps, or when it stops making calls. You'll run it on a scripted model that solves the task, then on a recorded open model that doesn't, and you'll see where that model goes wrong.

This chapter's agent maintains `unitcraft`, a small Python library that reads, converts and formats physical quantities written as text, such as `3.5 kg`. The agent takes an issue that a maintainer filed and proposes a change to the library's code. It can run the visible tests on its own copy, but it never sees the [hidden check](#testing-the-agent) that decides whether a change counts as done. That split is deliberate. An agent that can read its own grader will learn the grader, and the book's measurements in chapter 10 would mean nothing.

Andrew Ng's letter in [*The Batch*, issue 379](https://www.deeplearning.ai/the-batch/how-to-build-an-agent-harness-in-one-prompt), dated 13 Nov 2026, describes an agent harness as the code that wraps around an LLM and gives it context, tools and guardrails. This book uses the word for the same thing. The model makes the decisions. The harness supplies the loop, the tools and the limits on what those tools may do, and most of this book is about that second part.

The first task, T-01, is a one-file fix: the change goes in `unitcraft/format.py`. The visible suite fails in `tests/test_format.py`, and the issue reads: "`format_quantity` drops the trailing zeros: 3.5 kg prints as `3.5 kg`, and the default is two places." So the expected output for 3.5 kg is `3.50 kg`. A person would open `unitcraft/format.py`, read it, make the change and run the tests again. The agent has to do the same things in order, without a person between the steps, and the harness has to make sure that the order holds even when the model slips.

This chapter covers one task from start to finish. It explains what the agent starts with, the loop that runs it, the tools it calls, and the first rule that stops it. It then runs the loop twice, once on a scripted model and once on a recorded one, and counts what happened.

## What the agent does on one task {#one-task}

The agent starts with two messages: a system prompt that names its tools and their arguments, and the issue text. Nothing else about the task reaches the model. The agent never touches the case itself. The harness makes a scratch copy of the library for each run, and every write the agent makes lands only in that copy. When the run ends, the copy is scored and then discarded, so one run can't leave changes behind for the next.

A fix counts as [done](#score) when two things are true. The hidden check passes on the copy, and the run ended with a `finish` call. For T-01 the hidden check is H-01, a pytest file written from the issue text. It asserts one thing: that `format_quantity` pads 3.5, 0 and 12 kg to two places, as `3.50 kg`, `0.00 kg` and `12.00 kg`. The harness copies it into a fresh copy of the library after the run, so the agent never reads it. Chapter 10 applies the same rule to the whole [task set](#stop-rules). Applying a change to the case library is a separate decision, and chapter 6 is where an approval gate makes it.

The rule also closes one shortcut a model can take. It can edit the visible tests until they pass. For T-01 the task file says the `tests` folder must stay unchanged, so the scorer compares that folder with the case byte for byte, and an edited test makes the run not done, even when the hidden check passes. A model that is guessing at a fix can reach for that shortcut without any intent to cheat, and the rule is what stops it from counting.

Loading T-01 from the task file and listing the case's files takes one short example.

Example `read-the-issue` (Python 3.12.15), passing in Edition 2026.11.3:

```python
"""The issue the agent starts from, task T-01, and the case's files in sorted order. The model reads only the
issue and the system prompt, so these are what its first request holds about the task."""
from lib.case import CASE, case_files, load_tasks

task = load_tasks(only=["T-01"])[0]
print("task:", task.id)
print("issue:", task.issue)
files = case_files(CASE)
print("case files:", len(files))
for name in files:
    print(" ", name)
```

Output:

```text
task: T-01
issue: `format_quantity` drops the trailing zeros: 3.5 kg prints as `3.5 kg`, and the default is two places. CI is red on `tests/test_format.py`.
case files: 25
  .github/workflows/test.yml
  README.md
  pyproject.toml
  tests/test_arith.py
  tests/test_cli.py
  tests/test_convert.py
  tests/test_format.py
  tests/test_parse.py
  tests/test_rounding.py
  tests/test_table.py
  tests/test_temperature.py
  unitcraft/__init__.py
  unitcraft/__main__.py
  unitcraft/arith.py
  unitcraft/cli.py
  unitcraft/convert.py
  unitcraft/errors.py
  unitcraft/format.py
  unitcraft/parse.py
  unitcraft/prefixes.py
  unitcraft/quantity.py
  unitcraft/rounding.py
  unitcraft/table.py
  unitcraft/temperature.py
  unitcraft/units.py
```

The output prints the issue, then the case's files in sorted order. The issue is the only task-specific text in the model's first request, so every later step depends on what that first request held. The case has 25 files, and the agent can read any of them from its copy.

**Working rule:** Score a run only against its own copy and its task's check. Never score it against the case itself, because a change that reached the case would count for a run that never earned it.

## A loop in about seventy lines {#the-loop}

A model produces text, and the harness turns some of that text into actions. Each step sends the messages so far, along with the tool schemas, to the model. The reply comes back as text. The harness reads the tool call inside it, runs the tool on the scratch copy, appends the result to the messages, and goes around again. The model never runs anything itself. Anthropic's documentation for tool use states the contract in those terms: the model emits a structured request, the application runs the operation, and the result goes back into the conversation ([*How tool use works*](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works)).

The loop is `_loop` in [`examples/lib/loop.py`](https://github.com/rollingedition/book-agent-harnesses/blob/661879fe5a78f938f7b5c33652e27ad82d9f7c13/examples/lib/loop.py), about seventy lines. The file also holds rules for later chapters: the optional stops in `Stops` are off by default, and a reply cut off at the token limit is refused whatever the settings. None of this chapter's runs reach either. A step is one model call. A tool call is one request inside a step, and a reply can hold more than one. The loop acts on the first request and answers each other one with an error that says it was not run. Each request gets an ID from a counter, and the ID goes on the tool-result message that answers it. The assistant message that holds the reply carries no ID, and the trace keeps none. The [trace](#traces-and-cost), in `lib/trace.py`, holds one line per step: the step's number, the tool it called and what came back. Every reply stays in the messages too, which is why the model sees its own earlier steps on the next call, and why the request grows with each step.

The model's reply is plain text, and its tool call has a fixed shape: JSON inside `<tool_call>` tags. The chat template in the model file asks for that shape, a JSON object with a function name and arguments inside the tags ([the model file at its pinned revision](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf)). The recorded replies use this shape, and the harness reads only what is inside the tags:

```
<tool_call>
{"name": "read_file", "arguments": {"path": "<case-relative path>"}}
</tool_call>
```

Text outside the tags is ignored, so a reply may carry prose before the call. The harness never runs a block that doesn't parse: it records it as a malformed call and hands the reason back to the model as an error result, so the model can try again.

Across the run the messages grow in a fixed order: the system prompt, the issue, then each reply followed by the result of its call. Nothing is summarised and nothing is dropped. That makes the transcript readable, and it makes the cost of each step grow with the one before it. [Chapter 5](#context-budgets) takes up what to do when that growth reaches the model's window. The runs in this chapter are short, and they don't need that yet.

ReAct interleaves written reasoning with actions, and Yao and colleagues reported that the reasoning helps a model keep and revise a plan, and handle exceptions ([Yao et al., *ReAct*](https://arxiv.org/abs/2210.03629)). This loop keeps the actions and asks the model for no reasoning between them. Its system prompt says "Reply with a tool call only," and the parser passes over any prose the model writes anyway.

**Working rule:** Keep every request and its result in the messages, and give each result the ID of the request it answers. A loop that drops a result leaves the model without an answer to its request, and the messages are where that gap shows.

## Two tools and one stop tool {#two-tools}

The agent has to read, test and change, so the chapter gives it one tool for each job. The change tool is also the stop tool, because in this design a change ends the run.

| Tool | Arguments | What comes back | Ends the run? |
| --- | --- | --- | --- |
| `read_file` | `path`, a path inside the run's scratch copy of the case | the file's text, or an error | no |
| `run_tests` | none | the counts and the names of the failing tests, from the visible suite on the copy | no |
| `finish` | `path` and `text`, the whole new file | the counts and the failing tests after the change is written | yes |

`read_file` returns the whole file, and a path outside the copy is refused. `run_tests` runs the visible suite in the copy and returns its counts and the names of the failing tests, not the full output. A suite that runs past the time limit is stopped, along with its process group. `finish` takes the new text of one file, writes it into the copy, runs the visible suite and ends the run. If the write is refused, the error comes back as a tool result and the run goes on, so the model gets another try.

In this chapter the tools run inside the harness's own process, on the copy. [Chapter 7](#sandbox-and-secrets) runs the tests, the one command these tools start, in a sandbox.

A tool that reads files has to decide which paths it will read. Calling `read_file` with two paths outside the case shows what the model gets back when it asks for one.

Example `tool-refusal` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.3:

```python
"""The read tool refuses a path outside the case, and the refusal comes back as text the model can read. Only reads
are tried, and a refused path never reaches the disk."""
from lib.case import CASE
from lib.tools import CH1, Workspace

ABSOLUTE = "/etc/secret.txt"
ws = Workspace(CASE)
for path in ("../secret.txt", ABSOLUTE):
    result = CH1.call(ws, "read_file", {"path": path})
    # An absolute path differs on every machine, so the output shows a placeholder for it.
    print("refused:", result.text.replace(ABSOLUTE, "<absolute path>"))
```

Output:

```text
refused: error: path outside the case: ../secret.txt
refused: error: path outside the case: <absolute path>
```

Both paths are refused, and each refusal is a tool result. The model reads it in the next step like any other result, so it can correct its path and try again. Neither refused read touches the disk.

**Working rule:** Give each tool one job, and let only the stop tool end a run. A refused read or write should come back to the model as an error it can act on, and it should never stop the loop.

## Stop when it's finished, or when the budget runs out {#stop-rule}

A loop with no exit runs until somebody stops it, and every step costs tokens. So each run ends in one of three ways, and the run records which as `ended`. The model calls `finish`, and the run ends with its change. Or the run reaches the [step budget](#step-budget), which is eight steps for [this chapter's tool set](#two-tools), and it ends as `step_cap`. Or the model replies twice in a row with no tool call at all. The first such reply gets a retry, with a message that asks for one tool call. The second ends the run as `no_tool_call`.

A call to a tool that doesn't exist comes back as an error result, and the run goes on. The loop doesn't stop on a bad call. It counts the call, hands back the error and waits for the next step. The budget is what stops a model that keeps making bad calls from running forever. The budget counts model calls, not seconds, so the same run ends at the same step on any machine. The budget is also a separate limit from the size of the context: a run can hit the step budget with room left in the window, or run out of window first. The window is not a limit this chapter enforces.

[Chapter 2](#stop-rules) adds the rest of the stop rules. They cover a run that repeats the same call, a run that makes edits without moving the test counts, and a run that should ask the person a question instead of continuing. This chapter's loop has none of those, so a model that loops will loop until the eighth step.

**Working rule:** Set the step budget before the run starts, and treat it as a hard limit. A run that reaches the budget did not finish, whatever its last step looked like, and it should be reported as unfinished.

## Run it on a scripted model {#scripted-run}

With [the loop](#the-loop), its tools and its budget in place, the first run uses a model whose replies you write yourself. A scripted model gives back the replies you give it, in order, and nothing else. That makes it a clean test of the loop: any fault in the run is the loop's and not the model's, and the run shows what the loop does with correct replies, not what a model would choose. Four scripted replies for [T-01](#one-task) read the implementation, read its test, run the visible suite, and finish with a corrected file.

Example `scripted-loop` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
step 1: read_file: 23 lines
step 2: read_file: 27 lines
step 3: run_tests: 8 failed, 22 passed
step 4: finish: 7 failed, 23 passed
steps: 4
tool calls: 4
ended: finish
```

The run solves T-01 in four steps, which is all a scripted run can prove: the loop carries correct replies through to a passing check. The corrected file is the book's own solution, kept with the case data, and the example asserts that the run counts as done.

Read the output in order. Each line names one call and what came back from it, so the lines together show what the model had in front of it at every step. The counts move between step 3 and step 4: the fix takes the visible suite from 8 failed to 7 failed, and the test the issue describes now passes. The seven that remain fail other tests in the same visible suite. The check that counts for T-01 is H-01, and it passes. The run takes 4 steps and makes 4 tool calls, one per step, and it ends as `finish`.

**Working rule:** Run the loop on a scripted model before you run it on any model. If the scripted run fails, the fault is in the harness, and a model run would only hide it. If the scripted run passes and the model run fails, the fault is in the model or the prompt.

## Run it on the recorded model {#replayed-run}

The recorded run comes from Qwen3-4B-Instruct-2507, an open model quantised to Q4_K_M and run on a CPU at temperature 0 with a fixed seed. Its replies were saved as the raw text it produced, in a recording whose manifest names the model, its revision, the prompt's hash and the token counts. Replay checks that each request matches the one the recording holds, where a request is the messages and tool schemas sent at one step, and then returns the recorded reply.

Example `recorded-run` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
step 1: read_file: 23 lines
step 2: run_tests: 8 failed, 22 passed
step 3: malformed: error: malformed call
step 4: malformed: error: malformed call
step 5: malformed: error: malformed call
step 6: malformed: error: malformed call
step 7: malformed: error: malformed call
step 8: malformed: error: malformed call
steps: 8
tool calls: 8
ended: step_cap
malformed calls: 6
  6 x not JSON (Expecting ',' delimiter)
prompt tokens: 13009
completion tokens: 2128
```

The recorded model never finishes. Its first two steps are valid calls: a `read_file`, then a `run_tests`. From the third step on, each reply is a `finish` call that carries a whole new file, and each of those calls fails to parse. That happens 6 times, all with one reason, and the run ends as `step_cap` after 8 steps and 8 tool calls. The harness returns each failure as an error result, and the model answers it with a `finish` call of the same shape.

The shape of each failing call looks like this. The file is left out, and the call's text is shown with `...`:

```
<tool_call>
{"name": "finish", "arguments": {"path": "unitcraft/format.py", "text": """ ...the whole file...\""}}
</tool_call>
```

The value opens with three quotes. JSON reads the first two as an empty string, so the parser stops at the third, where it expects a comma. The value also closes with a single quote, after an escaped one.

The model's reading of the issue is wrong from step 2, and the format failure hides it. At step 2 the model writes that `format_quantity` "drops trailing zeros in the fractional part, which is correct" (the model's words, from step 2 of the recording's `replies.jsonl`). The file at step 3 keeps the bug: it still strips zeros from the fraction with `frac.rstrip("0")`. No `finish` call parses in this run, so that file never reaches the hidden check. A probe outside the book's examples ran the step 3 file, copied from its code block, in a copy of the case against H-01, using the pinned pytest 9.2.0:

```
FAILED test_t01.py::test_pads_to_two_places - AssertionError: assert '3.5 kg'...
```

The book's own solution passes the same check. So the change the model proposed was wrong, and only the format failure kept it from being checked.

The example asserts that the run did not count as done, and that from the third step on every reply carries its file in triple quotes inside the call. The stop tool is the one tool that carries a whole file, so the format failure sits there. [Chapter 3](#tool-schemas) returns to that tool and changes how a change is sent, which removes the triple-quoted file, though small edits bring quoting trouble of their own. It does not answer the misreading at step 2: a change sent in the right form can still be wrong.

**Working rule:** Replay a recording the same way on every run, and never edit it to make a run pass. A failing recording shows what the model really did. The fix belongs in the harness, the prompt or the model choice, and the result of that fix is a new recording.

## What goes wrong, and what is counted {#what-goes-wrong}

The recorded run from [the replayed run](#replayed-run) fails in two ways. The loop catches the first and doesn't repair it: each malformed call came back as an error result the model could read, and the step budget ended the run. The second is the wrong change. The loop never sees it, because no `finish` call parses and so no change runs. In this recording the model never called a wrong tool, and it never stopped early with a reply that had no call. The format failure repeated until the budget ran out, and it hid the misreading.

Four counts describe every run in this book. Steps count model calls, and tool calls count requests, including malformed ones. The two token counts are the [prompt tokens](#token-counts), summed over every request in the run, and the completion tokens the model produced. Tokens are counted by the pinned model's own tokenizer when the recording is made, and the count is stored in the recording's manifest. Replay reads the stored count and does not tokenize again. For the recorded run, the prompt tokens are 13009 and the completion tokens are 2128. The prompt total is high because each step sends the whole transcript again.

**Working rule:** Count steps and tool calls the same way on every run, so that two runs can be compared. When a run ends at its budget, read its error lines before you change the prompt or the model. The error lines show whether the model is repeating one mistake, and that tells you which part of the harness to look at.

## Decisions in this chapter {#chapter-decisions}

- **The tools run in the harness's own process, on a scratch copy.** That is enough to show the loop, and it is not a defence. Until a sandbox holds the tools, the copy is only a place for writes to land.
- **The stop tool takes the whole new text of one file.** That is the simplest change a stop tool can carry, and it is the change that the recorded model fails to send in a form the parser reads. A different stop tool would need a new recording.
- **The step budget is eight.** The number is small because this chapter's task needs about four steps, and a budget that fits the task makes a run that wanders stand out.
- **The recorded run is shown as it happened.** The format failure and the misreading both stay in the book, because a recording edited to pass would show a model that doesn't exist. The recording's raw replies are kept beside the counts, so anyone can check what the parser made of each one.

**Working rule:** Before you change any of these decisions, work out what the change does to the numbers this chapter prints. A new step budget changes the step counts, a new stop tool means a new recording, and a sandbox changes what the tools can reach. Make the change in its own chapter's terms, and rerun the scripted and recorded examples before you trust the result.
