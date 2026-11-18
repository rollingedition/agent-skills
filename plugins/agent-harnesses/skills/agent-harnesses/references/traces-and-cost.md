---
title: "Agent Harnesses"
chapter: "Trace each run and count what it cost"
chapter_id: traces-and-cost
book: agent-harnesses
edition: 2026.11.1
verified: 2026-11-16
edition_code: CBDA-H5E9
canonical: https://rollingedition.com/agent-harnesses/traces-and-cost
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Trace each run and count what it cost,” chapter 11 of Agent Harnesses, Edition 2026.11.1, examples passed Nov 16, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/traces-and-cost. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Trace each run and count what it cost

By the end of this chapter, you can make every run write one record per step to a file that a later reader can parse, give each record IDs that tie it to its run and its call, and say what the run cost in tokens. Cost here means counts. It never means money.

The maintenance agent makes its runs on `unitcraft` in a scratch copy. A run can end well, badly or not at all, and its stop reason says only how it ended. Take the [chapter 1](#tools-and-a-loop) run on T-01, one of the tasks in the task set. It reads the right file and runs the tests, then makes a string of malformed calls until it reaches the step cap. The stop reason reads `step_cap`, and that is all the stop reason says. It does not say what the malformed calls had in common, what the harness did with each one, or how many tokens each step used. Those answers sit in the steps, so the harness has to keep the steps.

The record of each step is the trace. [Chapter 10](#testing-the-agent)'s score already reads the stored counts, and a reader who asks why a run stopped needs the steps before the stop. This chapter writes the trace as data, gives its IDs a fixed form, and counts what it holds. Every count here is read from a recording or printed by a script. None is taken from a live model, so the counts are stored counts, and the one check that would re-derive them from the model has not been run.

## One line per event {#one-line-per-event}

A trace is a file with one JSON object per line. The format has a name, JSON Lines, and a short definition: each line holds one JSON value, the file is UTF-8, and a line feed ends each line. The page recommends a line feed after the last line as well, but does not require one, and it also accepts a carriage return and a line feed. The [JSON Lines format](https://jsonlines.org/) says that a byte order mark must not be included. The harness writes each record with sorted keys, no spaces and ASCII only, so the same record always comes out as the same bytes. That matters for the same reason the printed output matters: a reader can compare two traces line by line.

Replaying the [chapter 1](#tools-and-a-loop) run on T-01 writes its steps in this form. The replay reads the recorded reply for each step, so the trace is the same on every run.

Example `trace-one-run` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.1:

```python
"""The chapter 1 recorded run of T-01 as JSON lines: one record per step, with run-scoped IDs and the recorded token
counts. The lines are written to a file and read back, and the reader counts the empty pieces it skips."""
import json
import tempfile
from pathlib import Path

from lib.case import load_tasks
from lib.loop import run_task
from lib.models import ReplayModel
from lib.tools import CH1
from lib.trace import IdCounter, StepRecorder, dumps, read_lines, step_records

task = load_tasks(only=["T-01"])[0]
model = StepRecorder(ReplayModel("chapter-1-t01", "T-01"))
run = run_task(model, task, CH1, max_steps=CH1.step_cap, ids=IdCounter())
records = step_records(run, model)
for record in records:
    print(dumps(record))
print("records:", len(records))
print("first call ID:", records[0]["calls"][0])
print("results:", ", ".join(f"step {r['step']} {r['result']}" for r in records))
print("prompt tokens, summed over the records:", sum(r["prompt_tokens"] for r in records))
print("completion tokens, summed over the records:", sum(r["completion_tokens"] for r in records))
try:
    json.loads("")  # a blank line is not a JSON value
except json.JSONDecodeError as error:
    print("blank line:", error)
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "trace.jsonl"
    path.write_text("".join(dumps(record) + "\n" for record in records), encoding="utf-8")
    read_back, skipped = read_lines(path.read_text(encoding="utf-8"))
print("lines read back:", len(read_back))
print("empty pieces skipped:", skipped)
assert read_back == records and skipped == 1  # the one piece after the last line feed
assert run.ended == "step_cap" and len(records) == CH1.step_cap and records[-1]["stop"] == "step_cap"
assert sum(r["prompt_tokens"] for r in records) == run.prompt_tokens
run.close()
```

Output:

```text
{"arguments":{"path":"unitcraft/format.py"},"brief":"23 lines","calls":["run-0001-c1"],"completion_tokens":22,"gate":[],"malformed":[],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":501,"result":"ok","run":"run-0001","step":1,"stop":"","tool":"read_file"}
{"arguments":{},"brief":"8 failed, 22 passed","calls":["run-0001-c2"],"completion_tokens":70,"gate":[],"malformed":[],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":713,"result":"ok","run":"run-0001","step":2,"stop":"","tool":"run_tests"}
{"arguments":null,"brief":"error: malformed call","calls":["run-0001-c3"],"completion_tokens":560,"gate":[],"malformed":["not JSON (Expecting ',' delimiter)"],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":941,"result":"refused","run":"run-0001","step":3,"stop":"","tool":"malformed"}
{"arguments":null,"brief":"error: malformed call","calls":["run-0001-c4"],"completion_tokens":292,"gate":[],"malformed":["not JSON (Expecting ',' delimiter)"],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":1528,"result":"refused","run":"run-0001","step":4,"stop":"","tool":"malformed"}
{"arguments":null,"brief":"error: malformed call","calls":["run-0001-c5"],"completion_tokens":296,"gate":[],"malformed":["not JSON (Expecting ',' delimiter)"],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":1847,"result":"refused","run":"run-0001","step":5,"stop":"","tool":"malformed"}
{"arguments":null,"brief":"error: malformed call","calls":["run-0001-c6"],"completion_tokens":296,"gate":[],"malformed":["not JSON (Expecting ',' delimiter)"],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":2170,"result":"refused","run":"run-0001","step":6,"stop":"","tool":"malformed"}
{"arguments":null,"brief":"error: malformed call","calls":["run-0001-c7"],"completion_tokens":296,"gate":[],"malformed":["not JSON (Expecting ',' delimiter)"],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":2493,"result":"refused","run":"run-0001","step":7,"stop":"","tool":"malformed"}
{"arguments":null,"brief":"error: malformed call","calls":["run-0001-c8"],"completion_tokens":296,"gate":[],"malformed":["not JSON (Expecting ',' delimiter)"],"offered":["finish","read_file","run_tests"],"parent":null,"prompt_tokens":2816,"result":"refused","run":"run-0001","step":8,"stop":"step_cap","tool":"malformed"}
records: 8
first call ID: run-0001-c1
results: step 1 ok, step 2 ok, step 3 refused, step 4 refused, step 5 refused, step 6 refused, step 7 refused, step 8 refused
prompt tokens, summed over the records: 13009
completion tokens, summed over the records: 2128
blank line: Expecting value: line 1 column 1 (char 0)
lines read back: 8
empty pieces skipped: 1
```

The run has 8 records, one for each of its steps, and its last record carries the stop, `step_cap`. Each record holds the step number, the tool, the arguments, a one-line brief of what came back, a result class, the call IDs, the tools that were offered, the gate's lines for that step and the token counts for that step. The first call's ID is run-0001-c1.

The later steps are malformed calls. The model's reply was not valid JSON, so the harness did not run the call. It recorded the step as `refused`, and it put the parse error in the `malformed` field. `refused` covers every call that the harness did not run, or that a tool turned away before it ran: a reply that cannot be parsed or was cut off, a tool name the harness does not offer, arguments that do not fit the tool, a change a gate holds, and a path that a tool's own check refuses. The third class, `error`, is different. It means a tool ran and reported a failure. Reading `refused` as a tool error sends a reader to look for a bug in a tool that was never called.

Summed over the records, the replayed run used 13009 prompt tokens and 2128 completion tokens. Those are the counts the recording stored for each step, not counts taken during the replay.

The file has one trap, and the example shows it at the end. JSON Lines does not allow a blank line, because a blank line is not a value. Parsing an empty line fails, and Python reports it as Expecting value: line 1 column 1 (char 0). Its records go to a file and come back through a reader. Splitting the text on line feeds leaves one empty piece after the last line feed, so the reader skips that piece on purpose and counts it. Here 8 records come back, and 1 piece is skipped. A reader that did not skip it would stop at the end of every file.

**Working rule:** A reader of a trace skips an empty line only on purpose, and it counts the lines it skipped. Otherwise it stops at the first empty line. The writer never adds a blank line between records.

## IDs without clocks {#ids}

A step in a trace has to be found again, by the run it belongs to, by the call it answers and by its place in order. The trace takes its IDs from counters passed in by the caller, and from nothing else. A run is `run-0001`, numbered from one. A tool call is its run's ID with `c` and a number, so the first call of that run is `run-0001-c1`, the same ID that the first record of the replayed run carries. Steps are numbered from 1 in the order they happened.

No record carries a time. A timestamp would be different on every run, and so would the printed output of any example that showed it. Each example is compared with the output it printed when it was recorded, so a timestamp would fail that comparison on every run. The trace holds counts, short results and IDs, and nothing that comes from a clock.

The IDs matter for a second reason. Run IDs and call IDs go into the requests the harness sends to the model, so a replay sends the same request as the recording only when it numbers its runs the way the recording did. The replay code for a task picks up its counter at that task's place in the recording, which is why [the child example](#child-records) numbers its run from the recording's order and not from its own start.

**Working rule:** Number runs and calls from a counter passed in, never from a clock or a random generator. An ID that changes between runs changes the request, and a replay of that run stops at the first request it cannot match against the recording.

## Tokens as counts {#token-counts}

Each record in the [trace](#one-line-per-event) carries two token counts, in the pinned model's tokens as [chapter 1](#what-goes-wrong) defines them. The prompt count is the tokens the model read, and the completion count is the tokens it wrote. The recording takes both counts when it runs. It stores each step's counts with its reply, in `replies.jsonl`, and each task's totals in its manifest. Replay reads the stored counts and never tokenizes again, so a replay cannot produce a count the recording did not write.

Summing the stored step counts per task, and for the set, is the job of the next example. It checks each task's sums against the totals the manifest stores for that task, and it checks the set's prompt sum against the sum of those task totals.

Example `token-counts-from-recording` (Python 3.12.15), passing in Edition 2026.11.1:

```python
"""The token counts of the task-set recording, summed per task and for the set, read from the stored counts. Replay
never tokenizes, so these are the counts the recording wrote; the live check against a tokenizer is not run."""
from lib.models import load_recording
from lib.trace import OTEL_TOKEN_FIELDS

manifest, rows = load_recording("task-set")  # rows: one per step, from replies.jsonl; the manifest has task totals
sums: dict[str, list[int]] = {}
for row in rows:
    total = sums.setdefault(row["run"], [0, 0, 0])
    total[0] += row["prompt_tokens"]
    total[1] += row["completion_tokens"]
    total[2] += 1  # each row is one step, so the third sum counts steps
for task in sorted(manifest["tasks"], key=lambda t: t["task"]):
    prompt, completion, steps = sums[task["task"]]
    print(f"{task['task']} prompt tokens: {prompt} completion tokens: {completion} steps: {steps}")
    assert (prompt, completion, steps) == (task["prompt_tokens"], task["completion_tokens"], task["steps"])
set_prompt = sum(total[0] for total in sums.values())
set_completion = sum(total[1] for total in sums.values())
print("set tasks:", len(sums))
print("set prompt tokens:", set_prompt)
print("set completion tokens:", set_completion)
print("live count check: not run")
for field, name in sorted(OTEL_TOKEN_FIELDS.items()):  # the mapping table; the book's own names stay in the trace
    print(f"field {field} would map to {name} (data only; OpenTelemetry is not used)")
assert set_prompt == sum(t["prompt_tokens"] for t in manifest["tasks"])
```

Output:

```text
T-01 prompt tokens: 44836 completion tokens: 2025 steps: 16
T-02 prompt tokens: 43904 completion tokens: 2059 steps: 16
T-03 prompt tokens: 27562 completion tokens: 1463 steps: 12
T-04 prompt tokens: 8809 completion tokens: 1054 steps: 5
T-05 prompt tokens: 8494 completion tokens: 906 steps: 5
T-06 prompt tokens: 55109 completion tokens: 4670 steps: 16
T-07 prompt tokens: 24989 completion tokens: 3468 steps: 9
T-08 prompt tokens: 13713 completion tokens: 1154 steps: 7
T-09 prompt tokens: 10324 completion tokens: 701 steps: 6
T-10 prompt tokens: 51056 completion tokens: 3549 steps: 16
T-11 prompt tokens: 33951 completion tokens: 817 steps: 16
T-12 prompt tokens: 30787 completion tokens: 1617 steps: 12
T-13 prompt tokens: 49249 completion tokens: 942 steps: 16
T-14 prompt tokens: 12651 completion tokens: 972 steps: 7
T-15 prompt tokens: 20409 completion tokens: 1254 steps: 10
T-16 prompt tokens: 57696 completion tokens: 4621 steps: 16
T-17 prompt tokens: 17601 completion tokens: 1511 steps: 9
T-18 prompt tokens: 5122 completion tokens: 304 steps: 4
T-19 prompt tokens: 22713 completion tokens: 2154 steps: 9
T-20 prompt tokens: 33630 completion tokens: 2065 steps: 13
set tasks: 20
set prompt tokens: 572605
set completion tokens: 37306
live count check: not run
field completion_tokens would map to gen_ai.usage.output_tokens (data only; OpenTelemetry is not used)
field prompt_tokens would map to gen_ai.usage.input_tokens (data only; OpenTelemetry is not used)
```

Every task's sums agree with its manifest, so the set's totals below are the recording's own counts. The task set has 20 tasks, which together used 572605 prompt tokens and 37306 completion tokens. The output's live count check, which would tokenize the recorded prompts with the pinned model, reports not run.

The library's source shows how a count of this kind is produced. llama-cpp-python's source was read at the release that the recordings pin, and it was not run here. Its non-streamed completions report the length of the prompt's token list and of the completion's token list, and their sum as the total ([llama.py at v0.3.36](https://raw.githubusercontent.com/abetlen/llama-cpp-python/v0.3.36/llama_cpp/llama.py)). Its `tokenize` method takes UTF-8 bytes and returns a list of integer token IDs. It adds a beginning-of-sequence token unless it is told not to, so a prompt's count depends on that setting as well as on the model's vocabulary.

Counts from different tokenizers are not comparable. This is a rule of thumb, not a measurement: a token is a unit of one vocabulary, and the same text can split into different numbers of units under another. A reader who compares two counts must first check that the model file and the settings match.

The recording's manifest stores the model file and its SHA-256, but not the settings that shape a prompt's count: the chat template that the library applied, and the beginning-of-sequence setting. The recording used the library's defaults for both, and the book does not yet write them down.

**Working rule:** Store each count with the model file it came from, and with any setting that changes it, such as the beginning-of-sequence token. Do not compare counts from different tokenizers. A count that no check has re-derived is reported as a stored count, never as a live one.

## A child's records sit under its parent's call {#child-records}

[Chapter 8](#subagents-and-handoffs) hands a subtask to a child loop and gets back a summary and a stop reason. It also keeps the child's own record with the child, so that the parent's summary is not the only trace of what happened. This section keeps that promise in the trace. A child's steps are written as their own run, with their own run ID and their own call IDs. Each of its records carries `parent`, the ID of the call that started it. The child's records print directly after the parent's call that started them.

Here a parent starts a child on T-04, a task that asks for an inch unit. The child's recorded run ends with a finish that changes files. A scripted person says no to that change, so the gate holds the finish, and the child hands back with a question.

Example `child-trace-under-parent` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.1:

```python
"""A parent starts a child on T-04, whose recorded run ends with a finish that changes files. The gate holds that finish
because the person says no, so the child hands back with ask_user. The child's records sit under the parent's start call;
the parent is scripted, so its records carry zero tokens."""
from lib.case import load_tasks
from lib.chapter1 import call
from lib.models import ReplayModel, load_recording
from lib.permissions import Gate, library_copy, replay_ids, scripted
from lib.subagents import START_CHILD
from lib.tasks import snapshot
from lib.tools import V1
from lib.trace import StepRecorder, child_under_parent, dumps

task = load_tasks(only=["T-04"])[0]
manifest, _ = load_recording("task-set")
stored = next(t for t in manifest["tasks"] if t["task"] == "T-04")
with library_copy() as library:
    before = snapshot(library, "unitcraft")
    gate = Gate(library, scripted((False, "not this change")))  # the scripted person says no, with this reason
    child_model = StepRecorder(ReplayModel("task-set", "T-04"), gate)
    replies = [call(START_CHILD, task_id="T-04"), call("ask_user", question="The child's change was held. Pass it on?")]
    parent, child, records = child_under_parent(task, replies, child_model, gate, library, replay_ids("T-04"))
    for record in records:
        print(dumps(record))
    print("child budget:", V1.step_cap)
    print("child ended:", child.handoff.ended)
    print("gate refusals:", gate.counts["refused"])
    print("parent ended:", parent.ended)
    print("copy unchanged by the held finish:", before == snapshot(library, "unitcraft"))
    child_records = [r for r in records if r["run"] == child.run.id]
    parent_records = [r for r in records if r["run"] != child.run.id]
    print("child run:", child.run.id)
    print("parent call of the child:", child_records[0]["parent"])
    print("held step:", next(r["step"] for r in child_records if r["result"] == "refused"))
    print("parent tokens, summed:", sum(r["prompt_tokens"] + r["completion_tokens"] for r in parent_records))
    child_prompt = sum(r["prompt_tokens"] for r in child_records)
    child_completion = sum(r["completion_tokens"] for r in child_records)
    print("child prompt tokens, summed:", child_prompt)
    print("child completion tokens, summed:", child_completion)
    assert child.handoff.ended == "ask_user" and sum(r["result"] == "refused" for r in records) == 1
    assert parent.ended == "ask_user" and before == snapshot(library, "unitcraft")
    assert (child_prompt, child_completion) == (stored["prompt_tokens"], stored["completion_tokens"])
    parent.close()
```

Output:

```text
{"arguments":{"task_id":"T-04"},"brief":"child ask_user at step 5","calls":["run-0001-c1"],"completion_tokens":0,"gate":[],"malformed":[],"offered":["ask_user","start_child"],"parent":null,"prompt_tokens":0,"result":"ok","run":"run-0001","step":1,"stop":"","tool":"start_child"}
{"arguments":{},"brief":"25 files","calls":["run-0004-c1"],"completion_tokens":51,"gate":[],"malformed":[],"offered":["ask_user","edit_file","finish","list_files","read_file","run_tests","write_file"],"parent":"run-0001-c1","prompt_tokens":1049,"result":"ok","run":"run-0004","step":1,"stop":"","tool":"list_files"}
{"arguments":{"path":"unitcraft/units.py"},"brief":"36 lines","calls":["run-0004-c2"],"completion_tokens":108,"gate":[],"malformed":[],"offered":["ask_user","edit_file","finish","list_files","read_file","run_tests","write_file"],"parent":"run-0001-c1","prompt_tokens":1253,"result":"ok","run":"run-0004","step":2,"stop":"","tool":"read_file"}
{"arguments":{"new":"Unit(\"m\", \"length\", Decimal(1)),\n        Unit(\"km\", \"length\", Decimal(1000)),\n        Unit(\"cm\", \"length\", Decimal(\"0.01\")),\n        Unit(\"mm\", \"length\", Decimal(\"0.001\")),\n        Unit(\"ft\", \"length\", Decimal(\"0.3048\")),\n        Unit(\"in\", \"length\", Decimal(\"0.0254\")),\n        Unit(\"kg\", \"mass\", Decimal(1)),\n        Unit(\"g\", \"mass\", Decimal(\"0.001\")),\n        Unit(\"lb\", \"mass\", Decimal(\"0.45359237\")),\n        Unit(\"s\", \"time\", Decimal(1)),\n        Unit(\"min\", \"time\", Decimal(60)),\n        Unit(\"h\", \"time\", Decimal(3600)),\n        Unit(\"C\", \"temperature\", None),\n        Unit(\"F\", \"temperature\", None),\n        Unit(\"K\", \"temperature\", None),","old":"Unit(\"m\", \"length\", Decimal(1)),\n        Unit(\"km\", \"length\", Decimal(1000)),\n        Unit(\"cm\", \"length\", Decimal(\"0.01\")),\n        Unit(\"mm\", \"length\", Decimal(\"0.001\")),\n        Unit(\"ft\", \"length\", Decimal(\"0.3048\")),\n        Unit(\"kg\", \"mass\", Decimal(1)),\n        Unit(\"g\", \"mass\", Decimal(\"0.001\")),\n        Unit(\"lb\", \"mass\", Decimal(\"0.45359237\")),\n        Unit(\"s\", \"time\", Decimal(1)),\n        Unit(\"min\", \"time\", Decimal(60)),\n        Unit(\"h\", \"time\", Decimal(3600)),\n        Unit(\"C\", \"temperature\", None),\n        Unit(\"F\", \"temperature\", None),\n        Unit(\"K\", \"temperature\", None),","path":"unitcraft/units.py"},"brief":"edited unitcraft/units.py","calls":["run-0004-c3"],"completion_tokens":570,"gate":[],"malformed":[],"offered":["ask_user","edit_file","finish","list_files","read_file","run_tests","write_file"],"parent":"run-0001-c1","prompt_tokens":1686,"result":"ok","run":"run-0004","step":3,"stop":"","tool":"edit_file"}
{"arguments":{},"brief":"8 failed, 22 passed","calls":["run-0004-c4"],"completion_tokens":111,"gate":[],"malformed":[],"offered":["ask_user","edit_file","finish","list_files","read_file","run_tests","write_file"],"parent":"run-0001-c1","prompt_tokens":2276,"result":"ok","run":"run-0004","step":4,"stop":"","tool":"run_tests"}
{"arguments":{"summary":"Added the inch unit ('in') with a factor of 0.0254 to the units dictionary in unitcraft/units.py. This allows parse_quantity('2 in') to work correctly and enables the convert function to handle inch-to-meter conversions. The test suite failures indicate other issues in the codebase that are outside the scope of this specific task."},"brief":"p-1 was not applied: the person said no: not this change","calls":["run-0004-c5"],"completion_tokens":214,"gate":["p-1 1 files, diff 06ee73fd984f: asked","p-1 answer no, bound to p-1 and 06ee73fd984f","p-1 not applied: the person said no: not this change"],"malformed":[],"offered":["ask_user","edit_file","finish","list_files","read_file","run_tests","write_file"],"parent":"run-0001-c1","prompt_tokens":2545,"result":"refused","run":"run-0004","step":5,"stop":"ask_user","tool":"finish"}
{"arguments":{"question":"The child's change was held. Pass it on?"},"brief":"ask_user","calls":["run-0001-c2"],"completion_tokens":0,"gate":[],"malformed":[],"offered":["ask_user","start_child"],"parent":null,"prompt_tokens":0,"result":"ok","run":"run-0001","step":2,"stop":"ask_user","tool":"ask_user"}
child budget: 16
child ended: ask_user
gate refusals: 1
parent ended: ask_user
copy unchanged by the held finish: True
child run: run-0004
parent call of the child: run-0001-c1
held step: 5
parent tokens, summed: 0
child prompt tokens, summed: 8809
child completion tokens, summed: 1054
```

The child's run takes the number that the recording gave T-04, the fourth run in it, so its requests match the recorded ones. The run is run-0004, and its first record names the parent's call in `parent`: run-0001-c1.

The child's records carry the counts the recording stored for T-04, 8809 prompt tokens and 1054 completion tokens, which the script asserts against the manifest. The parent is scripted, so its records carry no tokens: 0.

The person's no is where the child's run ends. The gate holds the finish at step 5, the child's last record, and the child hands back a question instead.

The child stops with ask_user, and the gate refused 1 call. That stop comes from the gate, not from the budget of 16 steps. The parent, which is also scripted, asks the person a question of its own and stops with ask_user. The library copy is unchanged after the run, which is the whole point of the gate: the held change never reached the library.

This example does not show a child that runs out of budget. [Chapter 8](#subagents-and-handoffs) covers that case, and its stop reason comes from the budget, not from a held change.

**Working rule:** Give each child its own run ID and its own records, each with `parent` set to the call that started it. When you report what a parent run cost, add its children's counts and say that you did so. This trace prints them apart and sums none of them into the parent.

## Cost as counts, not money {#cost-not-money}

With the stored counts [summed per task](#token-counts), a run's cost is three numbers: its steps, its tool calls and its tokens. This book reports those three and nothing else. A price table goes stale, and a figure in dollars stays wrong after the first price change, so the book does not multiply its counts by a price. A reader who needs dollars can multiply the counts by the price their provider charges today, and the book's numbers stay right when prices change.

Grouping the stored counts by how each run ended puts the step-capped runs beside the others, so the cost of each stop reason shows in the same output.

Example `cost-as-counts` (Python 3.12.15), passing in Edition 2026.11.1:

```python
"""The cost of the task-set runs as counts only: steps, tool calls and tokens, summed per way a run ended. The cost is
tokens, never money, and the tokens are the recording's stored counts; the groups are sorted, so the output is stable."""
from lib.models import load_recording

manifest, rows = load_recording("task-set")
tasks = sorted(manifest["tasks"], key=lambda t: (t["task"], t["kind"]))
for ending in sorted({t["ended"] for t in tasks}):
    group = [t for t in tasks if t["ended"] == ending]
    print(f"ended {ending}: runs {len(group)}, done {sum(t['done'] for t in group)}, "
          f"steps {sum(t['steps'] for t in group)}, tool calls {sum(t['tool_calls'] for t in group)}, "
          f"prompt tokens {sum(t['prompt_tokens'] for t in group)}, "
          f"completion tokens {sum(t['completion_tokens'] for t in group)}")
    print("  tasks:", ", ".join(t["task"] for t in group))
    print("  done:", ", ".join(t["task"] for t in group if t["done"]) or "none")
print(f"all: runs {len(tasks)}, done {sum(t['done'] for t in tasks)}, steps {sum(t['steps'] for t in tasks)}, "
      f"tool calls {sum(t['tool_calls'] for t in tasks)}, prompt tokens {sum(t['prompt_tokens'] for t in tasks)}, "
      f"completion tokens {sum(t['completion_tokens'] for t in tasks)}")
capped = [t for t in tasks if t["ended"] == "step_cap"]
print(f"step-capped runs done: {sum(t['done'] for t in capped)} of {len(capped)}")
print(f"step-capped runs, steps: {sum(t['steps'] for t in capped)} of {sum(t['steps'] for t in tasks)}")
print(f"step-capped runs, prompt tokens: {sum(t['prompt_tokens'] for t in capped)} of "
      f"{sum(t['prompt_tokens'] for t in tasks)}")
prompts: dict[str, list[int]] = {}
for row in sorted(rows, key=lambda r: (r["run"], r["step"])):  # the stored step rows, in step order
    prompts.setdefault(row["run"], []).append(row["prompt_tokens"])
rising = [t["task"] for t in capped if all(b > a for a, b in zip(prompts[t["task"]], prompts[t["task"]][1:]))]
print(f"step-capped runs whose prompt count rises at every step: {len(rising)} of {len(capped)}")
assert all(t["tool_calls"] == t["steps"] for t in tasks), "one tool call per step in this recording"
```

Output:

```text
ended ask_user: runs 7, done 1, steps 69, tool calls 69, prompt tokens 157824, completion tokens 10368
  tasks: T-03, T-12, T-15, T-17, T-18, T-19, T-20
  done: T-18
ended finish: runs 6, done 4, steps 39, tool calls 39, prompt tokens 78980, completion tokens 8255
  tasks: T-04, T-05, T-07, T-08, T-09, T-14
  done: T-04, T-05, T-09, T-14
ended step_cap: runs 7, done 0, steps 112, tool calls 112, prompt tokens 335801, completion tokens 18683
  tasks: T-01, T-02, T-06, T-10, T-11, T-13, T-16
  done: none
all: runs 20, done 5, steps 220, tool calls 220, prompt tokens 572605, completion tokens 37306
step-capped runs done: 0 of 7
step-capped runs, steps: 112 of 220
step-capped runs, prompt tokens: 335801 of 572605
step-capped runs whose prompt count rises at every step: 7 of 7
```

The step-capped runs took 112 of 220 steps and 335801 of 572605 prompt tokens. The line for the step-capped runs reads runs 7, done 0, steps 112, tool calls 112, prompt tokens 335801, completion tokens 18683. The line for all the runs reads runs 20, done 5, steps 220, tool calls 220, prompt tokens 572605, completion tokens 37306, and it covers every group above it. A further assertion checks the recording: every run made one tool call per step, so the tool-call counts and the step counts are the same number.

None of the step-capped runs is done: the count reads 0 of 7. A step-capped run ends with neither a `finish` nor a handoff, so the zero follows from [the done rule](#score) whatever its files hold. The ask_user group's one done is T-18, whose count comes through a path match ([chapter 10](#t18-path)). The zero says nothing about how close any step-capped run came, and this chapter does not read it as a finding about the tasks.

Judgement, not a measurement: the step-capped line is the cost of runs that spent their tokens and did not finish. A token budget on the run's total tokens, not the per-request prompt budget of [chapter 5](#context-budgets), would have stopped those runs sooner. Its price is the chance of stopping a run that would have finished on a later step, and this recording cannot show that chance, because each step-capped run stopped at the cap and wrote no later step. The prompt count is what makes the cost grow: the loop sends the whole transcript again at every step. Counting the step-capped runs whose prompt count rises at every step gives 7 of 7. A step budget counts steps, so for a long run it says less about the cost than the tokens do. If a token budget is set, the harness should end the run with its own stop reason and its own counts, so that a cut by the budget can be told apart from a cut by the step cap.

[Chapter 12](#when-an-agent-is-the-wrong-design) compares an agent with a fixed pipeline in these same units, and the units are only useful if every run reports them the same way.

**Working rule:** Report a cost as the steps, tool calls and tokens of each run, grouped by how it ended, with the groups printed beside each other. Quote no money. Read a step-capped group as tokens spent without a finish, and not as evidence about the task until a second measure says otherwise.

## Keep your own field names, and map them at the edge {#own-fields}

The record's token fields are `prompt_tokens` and `completion_tokens`, and they are the book's own. The OpenTelemetry project publishes conventions for telemetry from generative AI systems. Its GenAI spans page, in revision v1.37.0 of the semantic conventions, names the same two counts `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens` ([the semantic conventions, GenAI spans](https://raw.githubusercontent.com/open-telemetry/semantic-conventions/v1.37.0/docs/gen-ai/gen-ai-spans.md)). In that revision the page marks its status as "Development", so the names may change. The book does not use OpenTelemetry. The [token-count example](#token-counts) prints the two names beside the book's fields, as data only, and this chapter makes no claim about how an OpenTelemetry tool reads a trace.

The book keeps its own names for a practical reason. A reader who exports the trace to another tool needs one mapping table, and the table is the only place that depends on the standard. The book's field names do not change when the standard does. The mapping adds nothing to the counts. The prompt count and the completion count are the same numbers under both sets of names, and the trace's records stay as they were written.

**Working rule:** Name the trace's fields for what they count, in your own project. Map them to a standard's names at the edge, in one table, with the revision of the standard written beside the table. Check the table again when the standard's revision changes.

## What goes wrong, and how you would notice {#trace-pitfalls}

The first mistake is in the `result` field. A `refused` call never ran, and a reader who takes `refused` for a tool's error looks in the wrong place. You notice it in the record: `result` is `refused`, `malformed` gives the parse error, the tool field reads `malformed` rather than a tool's name, and the gate's lines are empty. The brief of such a step starts with `error:`, which reads like a tool's failure, so read `result` and `malformed` rather than the brief.

The second mistake is a timestamp, added for debugging. It changes the printed output on every run, so the example's comparison with its recorded output fails on the first run after the change. The fix is to remove the timestamp and use the step number. The step number is the same on every run, and it is enough to put a line in order.

The third mistake is the blank line in [the first section](#one-line-per-event). A reader that passes an empty line to a JSON parser fails on it, and the failure looks like a damaged file when the file is fine. You notice it when the parse fails on an empty string. The fix is a rule that skips the empty piece on purpose and counts the skip, as the example does.

The fourth mistake is to treat the trace as a control. A trace records what the gate and the sandbox decided. It decides nothing, and it cannot undo a call that ran. The held finish in [the child example](#child-records) was held by the gate, which [chapter 6](#permission-gates) describes. The limits on commands come from the sandbox in [chapter 7](#sandbox-and-secrets). Reading a trace after a bad run tells you what the harness allowed, and nothing more.

The fifth point is a limit of this chapter. It traces the built-in tools only. No MCP server is traced here, so this chapter makes no claim about how MCP calls appear in a trace. [Chapter 9](#mcp-tools) covers the tools themselves.

**Working rule:** Before you trust a trace for a decision, read its `result` and `stop` fields, then check its printed sums against the stored totals. A trace that does not match its totals has a bug in its writer, and the run it records is not yet a finding about the agent.

## What this chapter decided {#trace-decisions}

- Each run writes one JSON line per step, in step order, with sorted keys, no spaces and ASCII only. No blank line is written.
- IDs come from counters passed in by the caller: runs as `run-0001`, calls as `run-0001-c1`. No clock or random value enters a trace.
- Token counts are the ones the recording stored. The live count check is not run, and the chapter says so where it matters.
- A child's records carry their own run ID and a `parent` field. A parent's cost includes its children's counts only when the report says so.
- Cost is steps, tool calls and tokens, grouped by how each run ended. The book quotes no money.
- The book's field names are its own. The OpenTelemetry names are printed as data and not used.

A trace costs one line per step, and it buys the answer to the question a stop reason cannot answer: which step went wrong, what the harness refused, and how many tokens each step took. The stop reason, the score and the cost are only as checkable as the lines they are counted from. Keep the lines, keep their IDs, and keep the counts as the recording wrote them.

**Working rule:** Keep one line per step, with its IDs and its stored counts, for every run you report. A figure that cannot be traced back to those lines is not reported.
