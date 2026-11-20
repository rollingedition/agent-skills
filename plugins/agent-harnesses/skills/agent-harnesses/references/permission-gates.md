---
title: "Agent Harnesses"
chapter: "Gate the tools that change things"
chapter_id: permission-gates
book: agent-harnesses
edition: 2026.11.2
verified: 2026-11-20
edition_code: ZZGV-NEGC
canonical: https://rollingedition.com/agent-harnesses/permission-gates
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Gate the tools that change things,” chapter 6 of Agent Harnesses, Edition 2026.11.2, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses/permission-gates. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Gate the tools that change things

By the end of this chapter you can keep an agent's changes in its own copy until a person says yes, check that the yes covers the exact change they read, and hand a no back to the agent as the reason its run stopped.

The agent in this book maintains `unitcraft`, a library whose maintainer owns every change that lands in it, and it works on a scratch copy of that library. Its tests and its edits happen in the copy. Something still has to decide when a change reaches the library the maintainer owns, and in this case the maintainer is the person who filed the issue. Task T-04 shows the stakes plainly. Its issue asks for one more unit, the inch, and the agent's copy holds an edit that adds it. Whether that edit lands is a decision for a person, and the agent should not make it for them.

This chapter builds the part of the harness that asks. The agent's file tools write only into the run's copy, and the library changes only when the harness applies a run's diff after a person's yes. On top of that sit two checks: a gate that reads the diff at `finish`, and a guard that compares the library's bytes around every tool call. The gate and the guard are teaching code and a second layer, and neither is a sandbox. The primary defence for code the agent writes is a container or a virtual machine, which [chapter 7](#sandbox-and-secrets) explains. No example here runs one, and no recording shows one. Each tool call is wrapped in a comparison of the case library's bytes, and the guard fails closed: when the library has changed, the run ends as `library_changed`, the harness applies nothing, and it restores nothing. The first section says what the copy does not stop.

## The copy comes first {#copy-first}

The agent's file tools reach files only through its copy. Each run gets its own copy, made by `scratch_copy` in `run_task`, and the tools work through a `Workspace` rooted at that copy. `Workspace.locate` resolves every path the model gives. It refuses a path that is absolute, one with a `..` part, one with a NUL byte or a backslash, one that resolves through a symlink to a place outside the copy, and any write into `.github/`. Through these tools, a path that does not resolve inside the copy never reaches the disk.

Those checks cover the paths the tools take. They do not cover code the agent runs. `run_tests` runs pytest on the copy, and pytest runs whatever the model wrote there. A test module the model adds is code too. The test run imports it and runs it with the harness's own user rights and no sandbox, so it can write to any path that user can write, including the library. The runner does not load `conftest.py` files (`run_pytest` passes `--noconftest`), but it does collect test modules, and that is the route this section means. The gate cannot stop that write, because the gate reads only the diff at `finish`. The library guard, in [its section](#wrapper), sees the write once `run_tests` returns, ends the run as `library_changed`, and restores nothing. It detects the write after it happens. It does not prevent it.

This is the open side of the harness, and it is the main limit of this chapter. [Chapter 7](#sandbox-and-secrets) describes the book's teaching sandbox, which runs the agent's commands with caps and a clean environment. Its table lists what it leaves open, and writes outside the copy are on that list. A container or a virtual machine is the primary defence for running code a model wrote, and chapter 7 explains both. The checks in this chapter are teaching code, written so a reader can open them, copy them and test them. They are not a substitute for that isolation.

The library changes in one place. `apply` in `lib/permissions.py` writes new bytes into the library, and its only caller is the gate's answer to a proposal, after a yes. `library_copy` makes the throwaway library that the examples apply to, so the book's case folder is never written. When a run ends, `Gate.settle` reports what the copy still holds, and nothing in the copy is written back to the library.

A write can also fail partway through an apply. The next example gives a proposal of two files, and puts a folder where the second file goes, so the second write fails.

Example `apply-all-or-nothing` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""A proposal of two files where the second cannot be written, because a folder stands where it goes. The first file
is put back, the error goes back as the handoff, and the library holds the bytes it held before the finish."""
from lib.case import CASE
from lib.permissions import Gate, answer, gated, library_copy
from lib.tasks import snapshot
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    (library / "unitcraft" / "extra.py").mkdir()
    before = snapshot(library, ".")
    (scratch / "README.md").write_text("A new line in the readme.\n", encoding="utf-8")
    (scratch / "unitcraft" / "extra.py").write_text('"""Extra."""\nTOTAL = 1\n', encoding="utf-8")
    gate = Gate(library, lambda p: answer(p, True))
    result = gated(V1, gate).call(Workspace(scratch), "finish", {"summary": "Two files."})
    print("ended:", result.end)
    print("handoff:", result.question)
    print("README as before:", snapshot(library, "README.md") == snapshot(CASE, "README.md"))
    print("library bytes unchanged:", snapshot(library, ".") == before)
    print("applied:", gate.counts["applied"], "refused:", gate.counts["refused"])
    assert result.end == "ask_user" and "apply failed (IsADirectoryError)" in result.question
    assert snapshot(library, ".") == before and gate.counts["applied"] == 0
```

Output:

```text
ended: ask_user
handoff: p-1 was not applied: apply failed (IsADirectoryError); library restored
README as before: True
library bytes unchanged: True
applied: 0 refused: 1
```

`apply` puts back each file it had touched and each folder it had made, and the gate holds the proposal with the error as its reason: `p-1 was not applied: apply failed (IsADirectoryError); library restored`. The README, which was written first, is as it was before the finish, and the library's bytes are unchanged. The gate catches an `OSError` as a held proposal. Any other exception also puts the files back and is then raised, and no example here shows that path.

**Working rule:** Give each run its own copy, refuse every path that resolves outside it, and let exactly one function write to the original, called only after a yes. Then name what the run's code can still do to the original, check that with a guard, and do not count the gate as the protection.

## Which mode this harness is in {#mode}

A gate needs an answer to one question first: who answers when the agent stops to ask? Claude Code's interactive mode asks a person in the session. The Claude Agent SDK offers several permission modes that differ on this point, and a harness has to say which one it resembles, because the answer decides what a call that needs approval does when no one can respond. This harness has no terminal and no session. It is a headless run, and the only party who can answer is a callback that the caller passes in.

The vendor documentation draws the cases apart. [Claude Code's permissions page](https://code.claude.com/docs/en/permissions.md) says that rules are checked in the order deny, ask, allow, and that the first match decides the outcome. It also says that Claude Code asks before it modifies files by default, and that read-only work inside the working directory runs without a prompt. [The Agent SDK's permissions page](https://code.claude.com/docs/en/agent-sdk/permissions.md) describes a `dontAsk` mode, in which any call that would otherwise prompt is denied without calling the approval callback. Neither product was run for this chapter, so the claims about them are the vendors' and are marked as such.

This harness keeps its callback. A change that needs a yes calls the approver and waits for the answer. The vendor's `dontAsk` mode differs in one way that matters here: it denies such a call without calling the callback, and this harness always calls it. The book calls this a headless run with a callback, and not `dontAsk`. The gate is the same whichever model adapter the run uses, because it wraps the tools and not the model. [The model protocol](#model-protocol) in chapter 4 is the part that changes from one model to the next.

**Working rule:** Name the mode before you add a gate. When the caller has a callback that can answer, make the gate call it and wait for the answer. A gate built with no approver refuses to start: this chapter's code raises an error. A design that hands off when nothing can answer needs its own path, and no example in this chapter shows one.

## The gate sits in finish {#gate-in-finish}

Most of what the agent does changes nothing the maintainer owns. It lists files, reads them and runs the visible tests. Its edits to the copy are its own work, and they are meant to be made. The one call that asks for a change to the library is `finish`, so the gate's check sits there, and `finish` is where a proposal is made.

The gate wraps every tool in the set, and each tool's class comes from one table in `lib/permissions.py`. The reads (`list_files`, `read_file`, `run_tests` and `ask_user`) pass through, and the library guard watches each of them. `run_tests` is in the read class, but it runs code the model wrote, as [the copy section](#copy-first) says. Edits and writes (`edit_file` and `write_file`) run in the copy, and the gate counts each call. `finish` is a proposal. Its class comes from the harness's table and from nothing the model wrote, so neither the model's summary nor a tool's own description sets it. The names, descriptions and schemas that go to the model are the same with or without the gate, so a request made through the gated tools is the same request as one made without them.

A proposal is the copy's whole diff against the library, not the summary the model wrote. `pending` lists each file whose bytes differ, and `diff_text` writes one header per file followed by its unified diff. The proposal's identity is a hash of the changed bytes, described in [the binding section](#bound-approval). The approver receives the proposal's ID, the summary, the list of changed files, the diff text as shown and the hash. It answers with a yes or a no, a reason, and the ID and hash it is answering. The summary is shown as the model's claim about the change, and the gate does not treat it as evidence. If the copy holds no change, `finish` passes through with its own result, so a run that changed nothing is not asked anything. Otherwise the approver is called inside the tool call, and the run waits for the answer. When the gate is enforcing, the finish tool's own body runs only after a yes.

[OWASP's guidance on excessive agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) asks for a person to approve high-impact actions before they are taken, and for an agent to have only the tools it needs. That is guidance, not a measurement, and this chapter treats it as the reason for the design and not as proof that the design works.

The task set is 20 tasks on the case, most of them scored by a hidden check ([the task set](#task-set) covers all of them). Its runs were recorded with tool set v1 and no gate, from Qwen3-4B-Instruct-2507, the model that [chapter 1](#replayed-run) replays. A gate leaves each request unchanged, so a replay through it sends the same requests and gets the same recorded replies. Start with the path that should work: the recorded T-04 run, replayed, with a person who answers yes.

Example `gate-applies-only-on-yes` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""The recorded T-04 run (add the inch) with the gate and a scripted yes: its one changed file reaches the library, and
the hidden check fails before the apply and passes after it. The second part shows two yeses that cannot apply: a copy
that changed after the person looked, and an answer that names another proposal."""
from lib.case import load_tasks
from lib.permissions import Answer, Gate, gated, library_copy, replay_task, scripted
from lib.tasks import hidden_check_passes
from lib.tools import V1, Workspace

task = load_tasks(only=["T-04"])[0]
with library_copy() as library:
    assert not hidden_check_passes(task, library)
    gate = Gate(library, scripted((True, "")))
    run = replay_task("T-04", gate, library)
    print("ended:", run.ended)
    print("proposals:", gate.counts["proposals"], "asked:", gate.counts["asked"])
    print("applied:", gate.counts["applied"], "files applied:", gate.counts["files applied"])
    print("visible tests after the apply:", Workspace(library).run_tests().splitlines()[0])
    print("hidden check after the apply:", hidden_check_passes(task, library))
    assert run.ended == "finish" and gate.counts["applied"] == 1 and hidden_check_passes(task, library)
    run.close()

with library_copy() as library, library_copy() as scratch:
    ws = Workspace(scratch)
    (scratch / "unitcraft" / "extra.py").write_text('"""Extra."""\nTOTAL = 1\n', encoding="utf-8")

    def drift(proposal):  # the copy changes in the window between the person's yes and the apply
        (scratch / "unitcraft" / "extra.py").write_text('"""Extra."""\nTOTAL = 2\n', encoding="utf-8")
        return Answer(True, proposal.id, proposal.sha256)

    late = gated(V1, Gate(library, drift)).call(ws, "finish", {"summary": "Add a constant."})
    print("drifted copy, handoff:", late.question)
    wrong = gated(V1, Gate(library, lambda p: Answer(True, "p-7", p.sha256)))
    print("answer for another proposal, handoff:", wrong.call(ws, "finish", {"summary": "Add a constant."}).question)
    assert late.end == "ask_user" and "changed after" in late.question
    assert not (library / "unitcraft" / "extra.py").exists()
```

Output:

```text
ended: finish
proposals: 1 asked: 1
applied: 1 files applied: 1
visible tests after the apply: 8 failed, 22 passed
hidden check after the apply: True
drifted copy, handoff: p-1 was not applied: the copy changed after the answer
answer for another proposal, handoff: p-1 was not applied: the answer is to another proposal or diff
```

The yes applies the change, and the hidden check passes only after the apply. The run ends as `finish`, and the gate applies the proposal it asked about. The visible suite reports `8 failed, 22 passed` once the change is in. That count does not score the task. The hidden check does, and the example holds that it fails before the apply and passes after it.

The second half of the example checks two yeses that cannot apply. In the first, the copy changes inside the approver, after the person has looked at it. In the second, the answer names another proposal. Each is refused with its own reason: `p-1 was not applied: the copy changed after the answer` for the first, and `p-1 was not applied: the answer is to another proposal or diff` for the second. In both cases the library is left unchanged, which the example asserts.

The finish tool's body is part of the same rule.

Example `finish-body-waits-for-yes` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""A finish that publishes does its work only after a yes. With a no the body never runs; with a yes it runs once,
after the change is applied to the library."""
from dataclasses import replace

from lib.permissions import Gate, answer, gated, library_copy
from lib.tools import V1, ToolResult, Workspace

published = []


def finish_and_publish(ws, args):
    published.append(args.summary)
    return ToolResult("run ended", brief="finish", end="finish", summary=args.summary)


publishing = replace(V1, tools=tuple(replace(t, run=finish_and_publish) if t.name == "finish" else t
                                     for t in V1.tools))


def finish_with(yes: bool):
    with library_copy() as library, library_copy() as scratch:
        gate = Gate(library, lambda p: answer(p, yes, "decided"))
        (scratch / "unitcraft" / "n.py").write_text("N = 1\n", encoding="utf-8")
        result = gated(publishing, gate).call(Workspace(scratch), "finish", {"summary": "Publish."})
        return result, gate, (library / "unitcraft" / "n.py").exists()


no_result, _, no_added = finish_with(False)
print("no: ended", no_result.end, "| publish ran:", len(published), "| file added:", no_added)
yes_result, gate, yes_added = finish_with(True)
print("yes: ended", yes_result.end, "| publish ran:", len(published), "| file added:", yes_added)
print("applied:", gate.counts["applied"])
assert no_result.end == "ask_user" and len(published) == 1 and not no_added
assert yes_result.end == "finish" and yes_added and gate.counts["applied"] == 1
```

Output:

```text
no: ended ask_user | publish ran: 0 | file added: False
yes: ended finish | publish ran: 1 | file added: True
applied: 1
```

The code gives the run a `finish` that publishes, and replays the same proposal twice. On a no the publish body does not run, and the file is not added: `ended ask_user | publish ran: 0 | file added: False`. On a yes the file is added and the body runs once: `ended finish | publish ran: 1 | file added: True`.

**Working rule:** Propose the copy's whole diff from the one call that can change the library, and hash that diff again immediately before the apply. A copy that moved after the person looked is refused, whatever the answer says, because the apply writes the bytes that were hashed. Run a tool's own body only after a yes.

## An approval answers one request {#bound-approval}

A yes is worth something only if it is for the change the person read. The problem shows up as soon as one gate sees more than one proposal, as it does when several runs share a gate. An answer given for one change could be carried over to the next one if nothing ties the two together.

The gate ties them with an identity. Each proposal takes the next ID from a counter on its gate, `p-1`, then `p-2`, and so on, and it carries the SHA-256 hash of the changed bytes. The hash covers the exact bytes of every changed file, in path order, and not only the text the person sees. The answer has to name both. The gate compares the two before it applies anything, and then it hashes the copy again, as [the gate section](#gate-in-finish) describes. [Microsoft's Agent Framework page on tool approval](https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval) describes the same pattern. It says that a local approval response authorizes a tool call only when it matches a pending approval request recorded in the same session, and that the framework ignores an unbound response and logs a warning. Its note on the opt-out says that turning the binding off can let a fabricated or replayed response approve a privileged call.

The text a person reads is written out, not raw. `diff_text` writes every character a terminal could act on as a visible escape. A carriage return or an escape sequence therefore shows up as text in the diff, and a file that is not UTF-8 text is shown only by the hash of its bytes.

Example `hidden-diff-lines-shown` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""Two files whose text would hide a line in a terminal: a carriage return that overwrites the line before it, and an
escape that erases a line. The proposal shows both written out, so every line the person reads is in the file."""
from lib.permissions import Gate, answer, gated, library_copy
from lib.tools import V1, Workspace

CR = "HIDDEN_CR = 'not shown'\r# a comment long enough to cover the line before it\n"
ESC = "HIDDEN_ESC = 'not shown'\n\x1b[1A\x1b[2K# tidy\n"
seen = []


def person(proposal):
    seen.append(proposal)
    return answer(proposal, False, "not this change")


with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, person)
    tools, ws = gated(V1, gate), Workspace(scratch)
    tools.call(ws, "write_file", {"path": "unitcraft/a_cr.py", "text": CR})
    tools.call(ws, "write_file", {"path": "unitcraft/b_esc.py", "text": ESC})
    tools.call(ws, "finish", {"summary": "Add two comment-only modules."})
    shown = seen[0].diff
    for line in (ln for ln in shown.splitlines() if "HIDDEN" in ln):
        print("shown:", line)
    print("headers that flag control characters:", shown.count("contains control characters"))
    print("raw CR or ESC in the shown text:", sum(ch in shown for ch in "\r\x1b"))
    print("applied:", gate.counts["applied"], "refused:", gate.counts["refused"])
    assert "\r" not in shown and "\x1b" not in shown and shown.count("contains control characters") == 2
    assert gate.counts["applied"] == 0
```

Output:

```text
shown: +HIDDEN_CR = 'not shown'\r# a comment long enough to cover the line before it
shown: +HIDDEN_ESC = 'not shown'
headers that flag control characters: 2
raw CR or ESC in the shown text: 0
applied: 0 refused: 1
```

The script writes two files whose contents would hide a line in a terminal. One has a carriage return that would overwrite the line before it, and one has an escape that would erase a line. The person sees both lines, escaped. The script prints `2` headers that flag control characters, and `0` raw carriage returns or escapes in the shown text. Its person answers no, so nothing is applied.

Example `answer-binds-bytes` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""A file that is not UTF-8 text is shown by the hash of its bytes, and the yes binds to those bytes. When the copy's
bytes change after the yes, the apply is refused, even though both versions decode to the same replacement characters."""
from lib.permissions import Change, Gate, answer, digest_changes, gated, library_copy
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    (scratch / "unitcraft" / "blob.bin").write_bytes(b"DATA \xff\n")

    def swap_then_yes(proposal):
        print("shown as:", proposal.diff.split(";")[0])
        (scratch / "unitcraft" / "blob.bin").write_bytes(b"DATA \xfe\n")
        return answer(proposal, True)

    gate = Gate(library, swap_then_yes)
    result = gated(V1, gate).call(Workspace(scratch), "finish", {"summary": "Add a blob."})
    print("ended:", result.end)
    print("handoff:", result.question)
    print("applied:", gate.counts["applied"], "| blob in library:", (library / "unitcraft" / "blob.bin").exists())
    one = digest_changes([Change("x.bin", None, b"\xff")])
    two = digest_changes([Change("x.bin", None, b"\xfe")])
    print("hashes differ for \\xff and \\xfe:", one != two)
    assert result.end == "ask_user" and "changed after" in result.question and gate.counts["applied"] == 0
    assert one != two
```

Output:

```text
shown as: == unitcraft/blob.bin: added, not UTF-8 text
ended: ask_user
handoff: p-1 was not applied: the copy changed after the answer
applied: 0 | blob in library: False
hashes differ for \xff and \xfe: True
```

The script shows the other half. It adds a file whose bytes are not valid UTF-8, and the approver is shown `== unitcraft/blob.bin: added, not UTF-8 text`. After the yes, the copy's bytes are swapped from one byte to another, and both bytes decode to the same replacement character. The apply is refused: `p-1 was not applied: the copy changed after the answer`. The script also asserts that the two byte strings have different hashes, so the hash is not a hash of the decoded text.

Two runs can share a gate in one example.

Example `approval-in-transcript` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""Two proposals in one transcript, through one gate: the recorded T-04 run is answered yes and its inch reaches the
library; a stored T-09 run (fix the Celsius offset) is answered no and handed back. Each answer is logged with the
proposal ID and the hash of the diff it answers."""
from lib.case import CASE
from lib.permissions import Gate, library_copy, replay_task, scripted, stored_task
from lib.tasks import snapshot

with library_copy() as library:
    gate = Gate(library, scripted((True, ""), (False, "not in this change")))
    first = replay_task("T-04", gate, library)
    second = stored_task("T-09", gate, library)
    print("T-04 ended:", first.ended, "| T-09 ended:", second.ended)
    print("transcript, T-04:", first.trace.lines()[-1])
    print("transcript, T-09:", second.trace.lines()[-1])
    for line in gate.log:
        print("gate:", line)
    print("applied:", gate.counts["applied"], "refused:", gate.counts["refused"])
    assert first.ended == "finish" and second.ended == "ask_user" and gate.counts["applied"] == 1
    assert snapshot(library, "unitcraft/units.py") != snapshot(CASE, "unitcraft/units.py")
    assert snapshot(library, "unitcraft/temperature.py") == snapshot(CASE, "unitcraft/temperature.py")
    first.close()
    second.close()
```

Output:

```text
T-04 ended: finish | T-09 ended: ask_user
transcript, T-04: step 5: finish: p-1 yes, applied 1 files
transcript, T-09: step 6: finish: p-2 was not applied: the person said no: not in this change
gate: p-1 1 files, diff 06ee73fd984f: asked
gate: p-1 answer yes, bound to p-1 and 06ee73fd984f
gate: p-1 applied: 1 files
gate: p-2 1 files, diff 95fb833675dd: asked
gate: p-2 answer no, bound to p-2 and 95fb833675dd
gate: p-2 not applied: the person said no: not in this change
applied: 1 refused: 1
```

The code runs the recorded T-04 run and answers yes. It then runs a stored T-09 run and answers no. The T-09 run does not replay its recorded requests. Its tool results come from this copy, which may differ from the recording, so it feeds in the stored replies step by step. Each answer is logged beside its proposal. The transcript line for T-09 reads `step 6: finish: p-2 was not applied: the person said no: not in this change`, and the T-04 line ends in the yes and the apply. The gate's log carries the same pairs in full: one line for each answer, naming the proposal and the first twelve characters of the hash the answer names. A reader who wants to know which diff a yes applied can match those characters against the proposal that was shown. Two assertions hold the result: the T-04 change reached the library, and the T-09 change did not.

IDs count up within one gate, so two gates both issue `p-1`. That is an open limit, and [the open limits section](#open-limits) names it.

**Working rule:** Give every proposal an ID and the hash of its bytes, require the answer to name both, and check both again before you apply. Show the person the text with every control character written out. Log each answer as the pair, next to its proposal, so a reader can match a yes to the change it applied.

## Some changes are refused without a question {#never-class}

Some changes are not for a person to decide. The case's rules forbid the agent from renaming a public name, and from changing a test, and a yes cannot lift a rule of that kind. Putting the question to a person would move the decision to the wrong place, so the gate refuses these changes before any question is asked.

`assess` computes its reasons from the diff against the library, not from the summary. It refuses five kinds of change. A change under `.github/` is refused. A deleted file under `tests/` is refused. An edit to an existing file under `tests/` is refused. A new file under `tests/` that is not a `test_*.py` module is refused. A removed name is refused: a top-level public name in a `unitcraft/` module that the library defines and the copy no longer does, and a top-level `test_` function that the library has and the copy lacks. A new `test_*.py` module is allowed. The two trees are compared name by name, so a rename shows up as a removed name. The model's words cannot change the result, because the reasons are computed from the files.

Example `never-class-refused` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""A rename of a public name and the removal of a test, each an edit that succeeds on the copy, with a summary that
says no approval is needed. The gate reads the diff: both are refused as never-class, and the person is never asked."""
from lib.permissions import Gate, gated, library_copy, scripted
from lib.tools import V1, Workspace

REMOVED = ('def test_parses_negative_value():\n    q = parse_quantity("-2 m")\n'
           '    assert (q.value, q.unit) == (Decimal("-2"), "m")\n\n\n')

with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, scripted((True, "")))
    tools, ws = gated(V1, gate), Workspace(scratch)
    rename = {"path": "unitcraft/parse.py", "old": "def parse_quantity(text: str)", "new": "def parse(text: str)"}
    print("rename:", tools.call(ws, "edit_file", rename).text)
    print("test removal:", tools.call(ws, "edit_file", {"path": "tests/test_parse.py", "old": REMOVED, "new": ""}).text)
    result = tools.call(ws, "finish", {"summary": "Tidy-up: a rename and a removed flaky test. No approval needed."})
    print("ended:", result.end)
    print("reasons:", result.question)
    print("asked:", gate.counts["asked"], "held as never:", gate.counts["held as never"])
    assert result.end == "ask_user" and gate.counts["asked"] == 0
    assert "removes public name parse_quantity" in result.question
    assert "removes test test_parses_negative_value" in result.question
```

Output:

```text
rename: edited unitcraft/parse.py
test removal: edited tests/test_parse.py
ended: ask_user
reasons: p-1 was not applied: the harness refuses it: changes the test file tests/test_parse.py; removes public name parse_quantity; removes test test_parses_negative_value
asked: 0 held as never: 1
```

Two edits go into the copy in this example: a rename of a public function, and an edit to a test file that removes a test. Both succeed there, since edits to the copy are allowed. The refusal comes at `finish`, when the diff is read. The summary the agent writes says that no approval is needed, and that claim changes nothing.

The run ends as `ask_user`, and the handoff gives the reasons in full: `p-1 was not applied: the harness refuses it: changes the test file tests/test_parse.py; removes public name parse_quantity; removes test test_parses_negative_value`. An assertion holds that the approver was never asked, so the gate put no question to anyone.

Example `gutted-test-refused` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""An edit that keeps an existing test's name and removes its assertion is a change to a test file, and the harness
refuses it without asking. A new test module is not refused for that reason."""
from lib.permissions import Change, Gate, assess, gated, library_copy, scripted
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, scripted((True, "")))
    tools, ws = gated(V1, gate), Workspace(scratch)
    edit = {"path": "tests/test_parse.py", "old": '    assert (q.value, q.unit) == (Decimal("-2"), "m")',
            "new": "    assert True"}
    print("edit:", tools.call(ws, "edit_file", edit).text)
    result = tools.call(ws, "finish", {"summary": "Make the negative-value test pass."})
    print("ended:", result.end)
    print("reasons:", result.question)
    print("asked:", gate.counts["asked"], "held as never:", gate.counts["held as never"])
    new_module = assess(library, scratch, [Change("tests/test_new.py", None, b"def test_ok():\n    pass\n")])
    print("new test module reasons:", new_module)
    assert result.end == "ask_user" and gate.counts["asked"] == 0
    assert "changes the test file tests/test_parse.py" in result.question and new_module == []
```

Output:

```text
edit: edited tests/test_parse.py
ended: ask_user
reasons: p-1 was not applied: the harness refuses it: changes the test file tests/test_parse.py
asked: 0 held as never: 1
new test module reasons: []
```

The script takes a smaller step. The agent edits one assertion in an existing test, so that the test asserts `True`. The edit is refused with no question, because any edit to an existing file under `tests/` is refused: `p-1 was not applied: the harness refuses it: changes the test file tests/test_parse.py`. The same check on a new test module finds no reason to refuse it, and the example asserts that, so adding a test is not refused for that reason.

The check is coarse, and this chapter says so. It compares top-level names, so a change inside a public function's body waits for a yes. A rebinding such as `parse_quantity = None` still defines the name, so it is not refused. [The open limits section](#open-limits) lists the rest.

**Working rule:** Refuse a change that the project forbids by reading its diff against a list the harness owns, and name the rule it broke in the handoff. Keep the list short, and say what it does not check, because a check on names does not protect what a function does. A yes cannot make a forbidden change allowed, so do not ask for one.

## Refusals go back to the model {#refusal}

A no is an answer the run has to act on. If the harness dropped it, the change would vanish, and the agent would have no way to learn why its work did not land. So the gate returns the refusal to the model as a tool result, in the same form that chapter 3 uses for a bad argument, and it ends the run as `ask_user`, a handoff whose question is the same text ([errors the model can read](#errors-readable)).

A refusal is a tool result, so it takes room in the context like any other result, and chapter 5 counts it there ([the window the model has](#window)). [Microsoft's Agent Framework page](https://learn.microsoft.com/en-us/agent-framework/agents/tools/tool-approval) includes a Go sample that returns denials as well as approvals, so the model can respond to the person's decision.

Example `refusal-handed-back` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""The recorded T-04 run with the gate and a scripted no. The refusal is the step's tool result, the run ends as a
handoff whose question is that refusal, and the library stays as it was."""
from lib.case import CASE, load_tasks
from lib.loop import run_task
from lib.models import ReplayModel
from lib.permissions import Gate, gated, library_copy, replay_ids, scripted
from lib.tasks import snapshot
from lib.tools import V1

task = load_tasks(only=["T-04"])[0]
with library_copy() as library:
    gate = Gate(library, scripted((False, "the inch belongs in a later change")))
    run = run_task(ReplayModel("task-set", "T-04"), task, gated(V1, gate), max_steps=V1.step_cap,
                   ids=replay_ids("T-04"), case=library)
    print("ended:", run.ended)
    print("last step:", run.trace.lines()[-1])
    print("handoff question:", run.question)
    print("refused:", gate.counts["refused"], "applied:", gate.counts["applied"])
    unchanged = snapshot(library, ".") == snapshot(CASE, ".")
    print("library unchanged:", unchanged)
    assert run.ended == "ask_user" and run.question.startswith("p-1 was not applied") and unchanged
    run.close()
```

Output:

```text
ended: ask_user
last step: step 5: finish: p-1 was not applied: the person said no: the inch belongs in a later change
handoff question: p-1 was not applied: the person said no: the inch belongs in a later change
refused: 1 applied: 0
library unchanged: True
```

The [same replay of T-04](#gate-in-finish) runs again, this time with a no and a reason. The run ends as `ask_user`, and its last step is the refusal itself. The question that the handoff carries is the refusal's text, which reads `p-1 was not applied: the person said no: the inch belongs in a later change`. The person's reason is in that text, so a reader of the handoff sees what was decided and why. The library is unchanged, and the example asserts that as well.

**Working rule:** Return a no to the model as a tool result that carries the person's reason, and end the run as a handoff whose question is the same text. Do not swallow the no, and do not raise it as an exception the loop has to catch.

## The wrapper checks every call {#wrapper}

The gate checks what reaches the library through `finish`. Something else can change the library: the code that `run_tests` runs. So the gate wraps each tool in a guard that compares the library's bytes before and after the call. If the bytes moved, and the gate did not apply the change itself, the run ends as `library_changed`, and the handoff names the files. That is the seventh way a run can end: [chapter 2](#stop-rules) gives six from the loop, and the guard adds this one. Nothing is restored, and nothing else runs against the changed library.

Example `library-guard-fails-closed` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""A test module written into the copy makes run_tests write the library. The guard sees the library's bytes change
around the run_tests call and ends the run as library_changed. It reports the file and restores nothing."""
from lib.permissions import Gate, gated, library_copy, scripted
from lib.tools import V1, Workspace

with library_copy() as library, library_copy() as scratch:
    marker = library / "unitcraft" / "marker.py"
    test_module = ("from pathlib import Path\n"
                   f"Path({str(marker)!r}).write_text('MARK = 1\\n', encoding='utf-8')\n")
    gate = Gate(library, scripted())
    tools, ws = gated(V1, gate), Workspace(scratch)
    print("write test module:", tools.call(ws, "write_file", {"path": "tests/test_marker.py", "text": test_module}).text)
    result = tools.call(ws, "run_tests", {})
    print("run_tests ended:", result.end)
    print("handoff:", result.question)
    print("marker written:", marker.exists(), "| library changes counted:", gate.counts["library changed"])
    print("proposals:", gate.counts["proposals"])
    assert result.end == "library_changed" and marker.exists() and "unitcraft/marker.py" in result.question
    assert gate.counts["proposals"] == 0
```

Output:

```text
write test module: wrote tests/test_marker.py
run_tests ended: library_changed
handoff: the case library changed around run_tests: unitcraft/marker.py; the run stops, and nothing is restored
marker written: True | library changes counted: 1
proposals: 0
```

The script writes a test module into the copy. When the test run imports it, the module writes a marker into the library. The guard ends the run with `library_changed`, and the handoff reads `the case library changed around run_tests: unitcraft/marker.py; the run stops, and nothing is restored`. The marker file is in the library, and no proposal was made: `0`. The guard reports the write afterwards, as [the copy section](#copy-first) says.

A tool's call is checked in a second way, by name.

The table in `lib/permissions.py` is the only source of a tool's class, and a tool outside it is classed `never`. The gate refuses that call before the tool's own code runs, and the refusal goes back to the model as text. The tool's description does not matter here: a description that says a tool only reads is a claim, and the table decides.

Example `unknown-tool-refused` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""A tool outside the harness's table is refused before its own code runs, even when its description says it only
reads. The refusal goes back to the model as text, and the tool's body never runs."""
from dataclasses import replace

from lib.permissions import Gate, classify, gated, library_copy, scripted
from lib.tools import V1, NoArgs, Tool, ToolResult, Workspace

ran = []


def reset(ws, args):  # stands in for any effect the table does not know about
    ran.append(1)
    return ToolResult("did something", brief="did something")


with library_copy() as library, library_copy() as scratch:
    gate = Gate(library, scripted())
    extra = Tool("reset_library", "A read-only helper.", NoArgs, reset)
    tools = gated(replace(V1, tools=V1.tools + (extra,)), gate)
    result = tools.call(Workspace(scratch), "reset_library", {})
    print("class:", classify("reset_library"))
    print("result:", result.text)
    print("body ran:", len(ran))
    print("never calls:", gate.counts["never calls"])
    assert not ran and result.text.startswith("error:") and gate.counts["never calls"] == 1
```

Output:

```text
class: never
result: error: reset_library is not a tool this harness runs
body ran: 0
never calls: 1
```

The script adds a tool whose description says it is a read-only helper, and calls it. Its class is `never`, and its result is `error: reset_library is not a tool this harness runs`. Its body ran `0` times, and the gate counted `1` never call. [Chapter 9](#mcp-tools) applies this rule to MCP tools, whose annotations come from the server and are not a class.

**Working rule:** Class every tool in the table, and refuse any name the table does not list before its body runs.

## Allow lists do not skip the check {#allow-lists}

The usual way to skip a gate is an allow list. A tool on the list runs without a question, and a gate placed at the question is then bypassed for that tool. In the Agent SDK, a tool approved at an earlier step skips the approval callback, so checks that live only in the callback are bypassed for that tool. [The Agent SDK's page](https://code.claude.com/docs/en/agent-sdk/permissions.md) says so. Claude Code orders its rules differently, deny first, then ask, then allow, and [its permissions page](https://code.claude.com/docs/en/permissions.md) says an allow rule cannot carve an exception out of a deny rule.

This gate has no allow list. Every tool in the set goes through the wrapper, which refuses a name the table does not list, and the check on a change sits in `finish`, where the diff is read. No flag on a tool decides whether that check runs, because no tool is exempt from the wrapper. A gate that depends on a flag the model or a server can set is not a gate. [Chapter 9](#mcp-tools) applies this rule to MCP tools, and it sends them through this chapter's approvals rather than through an allow list.

**Working rule:** Do not let a name, a description or a flag from a tool or its server decide whether the check runs. Put the check on the path that every change the tools make has to take. Code that the tests run is outside that path, as [the copy section](#copy-first) says, and the flag describes the tool and nothing more.

## Across the task set {#task-set}

So far, every example has followed a single run. The question for the case is what the gate does across every recorded run, including the runs that should not change anything.

Example `gate-over-task-set` (Python 3.12.15 · pydantic 2.14.3), passing in Edition 2026.11.2:

```python
"""The 20 recorded task-set runs replayed with the gate observing, each matching its recorded ending and step count, and
the gate counting what it would have held (the four stop tasks T-16 to T-19 first). Counts only."""
from lib.case import CASE, DATA, load_tasks
from lib.permissions import Gate, library_copy, replay_task
from lib.tasks import snapshot
from lib.trace import IdCounter

import json

CHANGES = ("edit_file", "write_file")
rows = (DATA / "recorded" / "task-set" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
recorded = {r["task"]: r for r in map(json.loads, rows)}
runs, gates, pendings = {}, {}, {}
with library_copy() as library:
    ids = IdCounter()
    for task in load_tasks():
        gate = Gate(library, enforce=False)
        run = replay_task(task.id, gate, library, ids=ids)
        assert (run.ended, run.steps) == (recorded[task.id]["ended"], recorded[task.id]["steps"]), task.id
        runs[task.id], gates[task.id], pendings[task.id] = run, gate, gate.settle(run.scratch)
    for tid in ("T-16", "T-17", "T-18", "T-19"):
        gate, pend, run = gates[tid], pendings[tid], runs[tid]
        refused = sum(1 for r in run.trace.records if r["tool"] in CHANGES and r["brief"].startswith("error"))
        print(f"{tid} ended: {run.ended}, steps: {run.steps}")
        print(f"  change calls: {gate.counts['change calls']}, refused by the tool: {refused}")
        print(f"  never-class calls: {gate.counts['never calls']}, changes in the copy at the end: {len(pend.files)}")
        print(f"  held as never: {len(pend.never)}, waiting for a yes: {len(pend.files) - len(pend.never)}")
    changed = sorted(t for t in pendings if pendings[t].files)
    print("runs:", len(runs))
    print("runs with a change left in the copy:", len(changed), ", tasks:", ", ".join(changed))
    print("change calls, all runs:", sum(g.counts["change calls"] for g in gates.values()))
    print("never-class calls, all runs:", sum(g.counts["never calls"] for g in gates.values()))
    print("held as never, all runs:", sum(len(p.never) for p in pendings.values()))
    print("proposals that would wait for a yes, all runs:", sum(g.counts["waiting for a yes"] for g in gates.values()))
    print("library changed by the replays:", snapshot(library, ".") != snapshot(CASE, "."))
    assert snapshot(library, ".") == snapshot(CASE, ".") and gates["T-18"].counts["never calls"] == 1
    for run in runs.values():
        run.close()
```

Output:

```text
T-16 ended: step_cap, steps: 16
  change calls: 8, refused by the tool: 8
  never-class calls: 0, changes in the copy at the end: 0
  held as never: 0, waiting for a yes: 0
T-17 ended: ask_user, steps: 9
  change calls: 4, refused by the tool: 4
  never-class calls: 0, changes in the copy at the end: 0
  held as never: 0, waiting for a yes: 0
T-18 ended: ask_user, steps: 4
  change calls: 1, refused by the tool: 1
  never-class calls: 1, changes in the copy at the end: 0
  held as never: 0, waiting for a yes: 0
T-19 ended: ask_user, steps: 9
  change calls: 4, refused by the tool: 4
  never-class calls: 0, changes in the copy at the end: 0
  held as never: 0, waiting for a yes: 0
runs: 20
runs with a change left in the copy: 5 , tasks: T-04, T-05, T-08, T-09, T-14
change calls, all runs: 70
never-class calls, all runs: 1
held as never, all runs: 0
proposals that would wait for a yes, all runs: 5
library changed by the replays: False
```

This example replays every recorded task-set run through a gate that watches but does not enforce. The gate decides as it would, counts what it would hold, and returns each tool's own result, so each run ends where it ended in the recording. Each replay is asserted to match its recorded ending and step count, and the library is left as it was found. These are counts of what the gate would do, which is what makes it safe to try before turning enforcement on.

The stop tasks T-16 to T-19 each tried to change files, and the tools refused every one of those calls, so none of their copies changed. The gate counted the calls. T-18 is the one task that tried to write into `.github/`. The gate counted that call as a never-class call, `1` in all. It held `0` changes as never, because the tool had already refused the call before any change reached the copy.

Where a copy did keep a change, the gate would have asked a person about it. Across all the replays, `5` proposals would wait for a yes. The counts show what the gate would do with these copies. They cannot show what a person would answer, which is why the examples in this chapter use scripted answers, and why a real approver has to be a person, or a process that a person controls.

**Working rule:** Before you enforce a gate, replay the recorded runs through it without enforcement, and compare each ending and each count with what you expected. A count that surprises you is a finding about the gate or about the runs, and you settle it before anyone relies on the gate.

## Vendor defaults that would let a change through {#in-production}

Several of the failures below come from defaults that look reasonable. Each one is a claim a reader might believe, set against what the vendor documents say and what this harness does. The vendor claims are cited to their pages, and none of them was run for this book.

- An allow rule can override a deny. The Claude Code documentation says the reverse: deny is evaluated first, as [the allow-list section](#allow-lists) notes.
- Bypass mode means there is no gate. The SDK documentation says that deny and ask rules still apply in bypass mode, and that the `allowed_tools` list does not limit it.
- Approving once approves for good. The Claude Code table scopes a "don't ask again" choice to a repository and command for shell commands, and to the session for file modification. Microsoft's page says standing approvals persist in the session state and are not tied to the tool instance that created them, so a replacement tool with the same name can match a saved rule.
- Any answer will do. Microsoft's Agent Framework ignores a response that is not bound to a pending request by default. Here the answer must name the proposal and its hash, as the [binding section](#bound-approval) shows.
- A hook that says allow skips the checks. The SDK documentation says that a hook returning allow does not skip the deny and ask steps.
- The model's own text can grant the approval. A summary that says "approved", or "no approval needed", changes nothing in this harness. The [never-class example](#never-class) shows that the summary's claim does not change the refusal, because the refusal comes from the diff.

**Working rule:** When a vendor's default lets an answer, a flag or a hook stand in for a check, do not copy the default. Write the check so that it names what it approves: the proposal, its bytes and the rule it applies. Then test that a wrong answer, a moved copy and a claimed approval each fail.

## What this gate does not cover {#open-limits}

The security review of this chapter's code left the limits below in place, and this section is the one place that lists them. Each is a gap in the teaching code, and none is closed in this chapter.

- **Code the agent runs (copy section).** `run_tests` runs model-written code with the harness's own rights. The guard reports a write to the library after it happens and restores nothing. Chapter 7's sandbox gives the tests caps and a clean environment, but it does not stop writes to other paths. A container or a virtual machine is the primary defence, and no example here runs one.
- **Top-level name checks (F-7).** The never class compares top-level names in `unitcraft/` and `tests/`, and nothing deeper. A name defined only inside a block is not counted in either tree. A change inside a public function's body, and a rebinding such as `parse_quantity = None`, waits for a yes rather than being refused.
- **Approver exceptions (F-8).** An approver that raises ends the loop with that exception, and nothing is applied. It is not a handoff. A tool that raises an error other than `ToolError` also escapes the loop: in a probe on a scratch copy of the current code, a lone surrogate in `edit_file` truncated the copy's file to zero bytes and then raised `UnicodeEncodeError`.
- **Run-scoped IDs (F-9).** Each gate numbers its proposals from `p-1`. An answer recorded for one gate's `p-1` therefore matches another gate's `p-1` whenever the two diffs are the same bytes, so an answer replayed from an old log can approve a change in a different run. The bytes are the ones shown, but the ID is not unique across runs. A log kept across runs needs the run's ID as well.
- **Symbolic links (F-10).** The gate's file listing follows a symbolic link in the copy. A link to a file outside the copy brings that file's bytes into the diff, and a yes that covers the diff can then apply them to the library as a regular file. The person sees those bytes in the diff, but the proposal reads a file the copy does not own. The fix is to skip links, and this chapter does not make it.
- **What the person reads.** The yes covers the diff as the approver showed it. An approver that shows only part of the text gives the person less than the hash covers, and this chapter's examples show the whole diff.

**Working rule:** Write each limit beside the code it comes from, and name it once, in one place, so a reader can see what the gate does not do before they rely on it.

## Decisions this chapter made {#gate-decisions}

The decisions below are short enough to check against the examples above.

- The copy is where the harness's own tools write, and the harness changes the library through one write path, called after a yes. A container or a virtual machine is the primary defence for code the run executes. The copy and the gate are teaching code, and [the open limits](#open-limits) say what they leave open.
- The gate sits in `finish` and reads the copy's whole diff, not the summary.
- The classes come from the harness's own table. Neither the model's words nor a tool's description sets one, and a tool the table does not list is refused before its body runs.
- A yes binds to a proposal's ID and to the SHA-256 hash of its bytes, and the copy is hashed again immediately before the apply.
- A finish's own body runs only after a yes.
- A no ends the run as `ask_user`, and the person's reason becomes the question.
- The harness runs headless with a callback. It is not the vendor's `dontAsk` mode, and the book does not call it that.

Three things stay open on purpose. The approver belongs to the caller, and the examples script it so that they run offline. The list of changes the harness refuses outright is short, and a longer list is a decision for the case's maintainers, not for the gate. The gate checks changes to the library and not the commands the agent runs, which [chapter 7](#sandbox-and-secrets) takes up.

The harness applies a change to the library only after a yes, and a yes applies only the bytes the person was shown and that were hashed. The gate does not check the code a run executes. The guard detects a change that such code makes to the library and ends the run, but it does not prevent the change; the defences for that are in [the copy section](#copy-first).

**Working rule:** Write each decision a gate makes down with the example that shows it, and list what the gate leaves to its caller. A decision with no example behind it is a claim, and the chapter labels it as one.
