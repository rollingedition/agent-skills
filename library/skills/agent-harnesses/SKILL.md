---
name: agent-harnesses
description: "Use when building, hardening or testing an agent that runs a model with real tools on someone's project. Covers the tool loop and its stop rules, tool schemas and refusals, model adapters and replayed recordings, context budgets and compaction, approval gates bound to the exact diff, sandboxing and secrets, subagents and handoffs, MCP tools, scenario tests and honest scores, traces and token counts, and whether an agent is the right design at all."
license: CC-BY-NC-4.0
compatibility: "The book's examples ran on Python 3.12.15 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Agent Harnesses"
  edition: "2026.11.4"
  verified: "2026-11-20"
  examples: "64 of 64 examples pass"
  edition-code: "QTC9-C576"
  source: "https://rollingedition.com/agent-harnesses"
---

# Agent Harnesses

This agent skill is *Agent Harnesses*, Edition 2026.11.4, from Rolling Edition. Examples passed Nov 20, 2026: 64 of 64 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `agent-harnesses` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Use the book's terms as it defines them.** The book's Glossary has each term it defines, in the book's own sentence, with its section: https://rollingedition.com/agent-harnesses/glossary. The Rolling Edition MCP server's `define` gives one with its section, its edition and the version it's true for: where the task uses one, it means that.
- **Is this copy current?** Call `check_code` with `QTC9-C576` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/agent-harnesses
- **Credit the book** when you quote it or reuse its code: Agent Harnesses, Edition 2026.11.4, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/agent-harnesses. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `agent-harnesses` plugin and the zip on the book's page at rollingedition.ai.

## Build a tool loop with a stop rule

**When:** A model must call tools in a loop, and no harness exists yet.

1. Keep each request and its result in the messages, with the request's ID on the result ([The loop](https://rollingedition.com/agent-harnesses/s/the-loop)).
2. Give each tool one job. Only the stop tool ends a run; return a refused read or write as an error the model can act on ([Two tools](https://rollingedition.com/agent-harnesses/s/two-tools)).
3. Set a hard step budget before the run, counted in model calls, never time, so every machine stops at the same step ([Stop rule](https://rollingedition.com/agent-harnesses/s/stop-rule)).
4. Run the loop on a scripted model first. If that run fails, the fault is in the harness ([Scripted model](https://rollingedition.com/agent-harnesses/s/scripted-run)).
5. Replay a stored run the same way every time, and never edit a recording to pass ([Recorded model](https://rollingedition.com/agent-harnesses/s/replayed-run)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/scripted-run); its `ended` line should read finish.

**Pitfalls:**
- Tools that run in the harness's own process, on a scratch copy, are not a defence ([Chapter decisions](https://rollingedition.com/agent-harnesses/s/chapter-decisions)).

## Add stop rules for stuck runs

**When:** Runs repeat a call, edit without moving test counts, or spend the whole budget on one mistake.

1. Record one `ended` value per run, and count a run as done by its score, never by `ended` alone ([Ways to end](https://rollingedition.com/agent-harnesses/s/ways-to-end)).
2. Set the step budget from your task runs: the most steps a passing run needed, plus headroom ([Step budget](https://rollingedition.com/agent-harnesses/s/step-budget)).
3. Compare calls by tool name and sorted arguments, and end the run at three identical calls in a row ([Repeated calls](https://rollingedition.com/agent-harnesses/s/repeated-calls)).
4. Read test counts after each edit, not the model's account, and stop after two edits that leave them unchanged ([No progress](https://rollingedition.com/agent-harnesses/s/no-progress)).
5. Run the task set with the rules on and off, and keep a rule only if the done count holds ([Counting endings](https://rollingedition.com/agent-harnesses/s/ask-instead)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/repeated-calls); its `with the rule, ended` line should read repeated_call at step 13.

**Pitfalls:**
- Raising the repeat threshold without traces showing progress across identical calls. Measure the higher number on your task set first ([Repeated calls](https://rollingedition.com/agent-harnesses/s/repeated-calls)).

## Give tools schemas and hand refusals back

**When:** A model sends bad arguments, a name the harness does not run, or edit text that is not in the file.

1. Write each bound, type and default in the argument model, with a field description the model can read ([Schemas](https://rollingedition.com/agent-harnesses/s/schema-says)). The models use pydantic 2.14.3.
2. Choose lax or strict for each argument model: lax where a conversion is what the model meant, strict where a quiet conversion would change the tool's effect. Test each with a wrong-type value first ([Lax or strict](https://rollingedition.com/agent-harnesses/s/lax-or-strict)).
3. Return each refusal as a tool result naming the field, error type and message. End the run on a bad call only through the stop rules ([Readable errors](https://rollingedition.com/agent-harnesses/s/errors-readable)).
4. Take allowed names from the tools the loop runs, and list them in every refusal for an unknown name. Accept an alias only through a map the harness keeps ([One name](https://rollingedition.com/agent-harnesses/s/one-name)).
5. When an edit's text is missing from the file, return the nearest lines with their numbers and what to do next ([Nearest lines](https://rollingedition.com/agent-harnesses/s/edit-errors)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/lax-or-strict); its `strict, max_lines str 50` line should read int_type.

**Pitfalls:**
- A rule that lives only in the tool's sentence is a hint the harness never enforces ([Schemas](https://rollingedition.com/agent-harnesses/s/schema-says)).

## Put models behind one interface and replay recordings

**When:** You want one loop on several models, or to re-run a recorded run.

1. Make each adapter return a `Reply` with the raw text, counts and tool calls, never an SDK object ([One loop](https://rollingedition.com/agent-harnesses/s/one-loop)).
2. Test each adapter by calling `reply()` with the loop's messages and schemas, and check the fields returned ([Model protocol](https://rollingedition.com/agent-harnesses/s/model-protocol)).
3. Parse `function.arguments` as JSON, check it against the argument model, and return any failure as a tool result ([Hosted-style endpoint](https://rollingedition.com/agent-harnesses/s/openai-compatible)).
4. Refuse to send an API key over plain http to a remote host, and follow no redirects ([Hosted-style endpoint](https://rollingedition.com/agent-harnesses/s/openai-compatible)).
5. Record with the manifest's sampling, and keep the model file's hash beside it. Replay a stored run only with the prompt and check it was recorded with ([Local model](https://rollingedition.com/agent-harnesses/s/local-model), [Replay a stored run](https://rollingedition.com/agent-harnesses/s/scripted-and-replayed)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/scripted-and-replayed); its `reply texts compared exactly` line should read 8.

**Pitfalls:**
- Editing a stored reply to pass a replay hides the change that caused the failure. Record the run again instead ([Replay a stored run](https://rollingedition.com/agent-harnesses/s/scripted-and-replayed)).

## Keep a context budget and compact

**When:** Runs grow toward the window, or prompt tokens per step climb with every call.

1. Take the window from the load setting the run used, subtract the reply's limit, and never from a model's advertised length ([Window](https://rollingedition.com/agent-harnesses/s/window)). On the recorded runs the prompt budget is 7168 tokens.
2. Estimate the prompt at three characters per token, and check the estimate on each new model's first runs. An estimate under the reported count is a fault ([Estimating the prompt](https://rollingedition.com/agent-harnesses/s/estimate)).
3. Put the issue and notes first and the last tool result last, and claim the gain only once runs show it ([Last result](https://rollingedition.com/agent-harnesses/s/last-result)).
4. Compact the older steps to one line each, keep the last call and its result word for word, and refuse any cut that falls on a tool result. Check first that the fixed part fits the budget ([Compaction](https://rollingedition.com/agent-harnesses/s/compaction)).
5. Have the model write each fact a later step needs into a note, sent after the issue so compaction cannot cut it ([Notes](https://rollingedition.com/agent-harnesses/s/notes)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/compaction); its `calls still over the budget` line should read 0.

**Pitfalls:**
- Judge a budget only by runs that reached it. A run that stopped early never tested it ([Recorded budget](https://rollingedition.com/agent-harnesses/s/recorded-runs)).
- A tool the model never calls is untested: the recorded model wrote no notes in its three runs ([Recorded budget](https://rollingedition.com/agent-harnesses/s/recorded-runs)).

## Gate changes behind approval bound to the exact diff

**When:** The agent can change files, or anything else a person must approve.

The gate and guard are teaching code and a second layer; the primary defence is a container or a virtual machine. The guard compares the case library's bytes around every tool call and fails closed, ending the run as `library_changed` with nothing applied.

1. Give each run its own copy, refuse paths outside it, and let one function write to the original, after a yes. Name what the run's code can still do to the original; the gate does not stop that ([The copy](https://rollingedition.com/agent-harnesses/s/copy-first)).
2. Name the mode before adding the gate. With a callback that can answer, the gate waits for it; with no approver, it refuses to start ([Mode](https://rollingedition.com/agent-harnesses/s/mode)).
3. Put the gate in `finish`, reading the copy's whole diff, not the agent's summary ([Gate in finish](https://rollingedition.com/agent-harnesses/s/gate-in-finish)).
4. Give each proposal an ID and the hash of its bytes. The answer must name both, and both are rechecked before the apply; control characters are shown written out ([Approval bound](https://rollingedition.com/agent-harnesses/s/bound-approval)).
5. Refuse a forbidden change from a harness-owned list of diff rules, before any question; a yes cannot allow it ([Refused changes](https://rollingedition.com/agent-harnesses/s/never-class)).
6. Return a no to the model as a tool result carrying the person's reason, and end the run as a handoff with the same question text ([Refusals](https://rollingedition.com/agent-harnesses/s/refusal)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/gate-in-finish); its `ended` line should read finish.

**Pitfalls:**
- A vendor default that lets a flag or answer stand in for the check is no check. Test that a wrong answer, a moved copy and a claimed approval each fail ([Vendor defaults](https://rollingedition.com/agent-harnesses/s/in-production)).
- The gate reads the diff at `finish`, so it cannot stop a test the agent wrote from writing the original during `run_tests`. The guard detects that write afterwards and ends the run as `library_changed`; only a container or a virtual machine prevents it ([The copy](https://rollingedition.com/agent-harnesses/s/copy-first)).

## Run the agent's code in a sandbox and keep secrets out

**When:** The agent starts programs, such as a test suite, in a copy of the project.

The book's sandbox is teaching code and a second layer, not the protection. The primary defence is a container or a virtual machine, which no example runs or records.

1. Run code the agent wrote in a container or a virtual machine, the primary defence ([Sandbox and secrets](https://rollingedition.com/agent-harnesses/sandbox-and-secrets)). Read the book's sandbox table for what it leaves open ([Teaching sandbox](https://rollingedition.com/agent-harnesses/s/teaching-sandbox)).
2. List the exact argv of each program the agent may start, compare each parsed command with that list, and never pass the model's string to a shell. Fix what each program loads: config and plugins from outside the copy, conftest off ([Listed programs](https://rollingedition.com/agent-harnesses/s/listed-programs)).
3. Cap memory, CPU time and file size on every command, kill its process group on every exit, and count what it can start, since each process has its own caps ([Limits](https://rollingedition.com/agent-harnesses/s/limits)).
4. Where a command must not reach the network, require the network namespace, and check it with a listener the command must fail to reach ([Network block](https://rollingedition.com/agent-harnesses/s/network)).
5. Build each command's environment from the names it needs, never from a copy of the harness's ([Secrets](https://rollingedition.com/agent-harnesses/s/secrets)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/secrets); its `secret value in the output the model would see` line should read 0.

**Pitfalls:**
- A `setsid` child survives the group kill without a PID namespace; a container or a virtual machine closes that and the other gaps, if set up for it ([Limits](https://rollingedition.com/agent-harnesses/s/limits), [Teaching sandbox](https://rollingedition.com/agent-harnesses/s/teaching-sandbox)).
- A refused string is not a refused effect: a test file can still act. Treat every test module as code with the harness's rights ([Listed programs](https://rollingedition.com/agent-harnesses/s/listed-programs)).
- The harness's own test path, `run_tests` and the scoring run, does not require the network block. Require it on every path that runs code the agent wrote ([Network block](https://rollingedition.com/agent-harnesses/s/network)).
- Keys stay out of the harness's arguments and the copy's files: any command that reads the copy reads a key there, and `/proc` shows the parent's environment without a PID namespace ([Secrets](https://rollingedition.com/agent-harnesses/s/secrets)).

## Hand a subtask to a child and turn a stop into a question

**When:** A side task has a result that stands alone, or a run stopped on a stuck rule and a person must decide.

1. Give each child its own budget, counted in its own model calls, set from runs that finished ([Child budget](https://rollingedition.com/agent-harnesses/s/child-loop)).
2. Write the four parts of the brief before the child starts, with boundaries as files and tools ([Four-part brief](https://rollingedition.com/agent-harnesses/s/brief)).
3. Return to the parent only the child's ID, how it ended, its counts, files, and stop or summary ([What comes back](https://rollingedition.com/agent-harnesses/s/what-comes-back)).
4. Hand every stuck stop (`step_cap`, `repeated_call`, `no_progress`) to a person as a question, with its reason, counts and files ([Stop handed back](https://rollingedition.com/agent-harnesses/s/a-stop-handed-back)).
5. Use a child when its result stands without its reasons. Keep one loop where the parent must act on the files the child edits ([Two designs](https://rollingedition.com/agent-harnesses/s/designs)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/a-stop-handed-back); its `handed back to a parent` line should read 13.

**Pitfalls:**
- Two children that edit the same file can each hand back a clean summary. Before you merge, check each split's edits against the files the others changed, and give a parent handed a stop only the means to ask ([Splits in production](https://rollingedition.com/agent-harnesses/s/splits-in-production)).

## Connect MCP tools through the gate with namespacing and fenced output

**When:** A harness offers tools from MCP servers, some of them owned by other parties.

Other teams write these servers, and the harness runs each as a subprocess with its own rights. For a server you did not write, the primary defence is a container or a virtual machine; the gate and guard are a second layer.

1. Check the protocol revision in the first example's output. The pinned `mcp` package is 2.3.0 ([Revision](https://rollingedition.com/agent-harnesses/s/revision)).
2. List every server's tools at run start, and keep the list in the record ([Listing tools](https://rollingedition.com/agent-harnesses/s/listing-tools)).
3. Prefix every server tool with its server's name, in one module the rest of the harness imports. Assert the names the model sees are distinct ([Namespacing](https://rollingedition.com/agent-harnesses/s/namespacing)).
4. Give each server tool a class in the harness's own table, and never let an annotation set it. A tool the table does not name is not offered, and a call to it is refused ([Other tools](https://rollingedition.com/agent-harnesses/s/other-tools)).
5. Label every result from another party, fence it, and pass it to the model as data. Keep the stop rules, the allowed commands and the approvals out of anything the model reads ([Untrusted output](https://rollingedition.com/agent-harnesses/s/output-is-untrusted)).
6. Review each server, code included, before connecting it, and read refusals after each update. Run a server you did not write in a container or a virtual machine. Treat a tool it adds as unknown until your table names it ([MCP in production](https://rollingedition.com/agent-harnesses/s/mcp-tools-in-production)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/namespacing); its `names` line should read 11 and its `distinct` line 11.

**Pitfalls:**
- A read-only hint is the server's claim, and it never lets a call skip the gate ([Other tools](https://rollingedition.com/agent-harnesses/s/other-tools)).
- The table classes a name, not a tool's behaviour: a server that turns `read_file` into a write still runs as a read ([MCP in production](https://rollingedition.com/agent-harnesses/s/mcp-tools-in-production)).
- The fence marks a result as data, but the model may still ask for a change. The gate decides whether that call runs ([Untrusted output](https://rollingedition.com/agent-harnesses/s/output-is-untrusted)).

## Test the agent with scenario tests and score a task set honestly

**When:** Before changing a harness, a prompt or a model, and before quoting a score.

1. Name the replies each scenario test fixes, and what it measures: the harness's handling, not the model ([Scenario tests](https://rollingedition.com/agent-harnesses/s/scenario-tests)).
2. Run each check in a fresh copy, count only that copy's result, and review any file the agent planted in it ([Hidden check](https://rollingedition.com/agent-harnesses/s/hidden-check)).
3. Write the done rule before the run. Count a run as done only when its end state holds, and never one that hit a limit ([Score](https://rollingedition.com/agent-harnesses/s/score)).
4. Give each count its range in one sentence, and check a stop task's count against its question ([How sure](https://rollingedition.com/agent-harnesses/s/how-sure), [T-18 path](https://rollingedition.com/agent-harnesses/s/t18-path)).
5. Compare two versions as counts, state the result either way, and credit no one change in a bundle ([Two versions](https://rollingedition.com/agent-harnesses/s/v1-v2)).
6. Report a score with its tasks, runs, model and setting, and say it is not a benchmark ([Score limits](https://rollingedition.com/agent-harnesses/s/score-limits)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/score); its `pass@1` line should read 0.25.

**Pitfalls:**
- A score quoted without its tasks, runs and model cannot be checked ([Score limits](https://rollingedition.com/agent-harnesses/s/score-limits)).

## Trace runs and count cost in tokens

**When:** You need to explain a run, compare runs, or report what a task cost.

1. Write one line per step, with its run ID, call IDs and counts ([One line per event](https://rollingedition.com/agent-harnesses/s/one-line-per-event)).
2. Number runs and calls from a counter passed in, never from a clock or random generator ([IDs](https://rollingedition.com/agent-harnesses/s/ids)).
3. Store each token count with its model file and any setting that changes it. Never compare counts from different tokenizers ([Token counts](https://rollingedition.com/agent-harnesses/s/token-counts)).
4. Give each child its own run ID, with `parent` set to the call that started it. If a parent's cost includes its children's counts, say so ([Child records](https://rollingedition.com/agent-harnesses/s/child-records)).
5. Report steps, tool calls and tokens grouped by how each run ended, and quote no money ([Cost as counts](https://rollingedition.com/agent-harnesses/s/cost-not-money)).
6. Before a trace informs a decision, check its `result` and `stop` fields and printed sums against stored totals ([Trace pitfalls](https://rollingedition.com/agent-harnesses/s/trace-pitfalls)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/cost-not-money); its `step-capped runs done` line should read 0 of 7.

**Pitfalls:**
- A step-capped group is tokens spent without a finish, not evidence until a second measure agrees ([Cost as counts](https://rollingedition.com/agent-harnesses/s/cost-not-money)).

## Decide when an agent is the wrong design

**When:** Before you build an agent, or when a stopped agent's failures need a fix.

1. Write the steps out, each with its check. If every step is known and a check decides without a model, build and measure a pipeline first ([Fixed pipeline](https://rollingedition.com/agent-harnesses/s/fixed-pipeline-first)).
2. Sort each task in this order: a refusal is a question to a person; a person's yes is an agent behind a gate; known steps with a check are a pipeline; known steps without one are a single call that a person reads; open steps are an agent ([Design table](https://rollingedition.com/agent-harnesses/s/which-design)).
3. Split a task only when you can name the condition that makes splitting help, such as a context one agent cannot hold, and each part has its own check ([When to split](https://rollingedition.com/agent-harnesses/s/when-to-split)).
4. Keep the deciding check where the agent cannot edit or see it ([Check outside](https://rollingedition.com/agent-harnesses/s/check-outside)).
5. Sort stopped runs by how they ended, and read the record of each kind before choosing a fix. Write down where a pipeline's stop goes before you build it ([Agent failures](https://rollingedition.com/agent-harnesses/s/failures), [Fixed pipeline](https://rollingedition.com/agent-harnesses/s/fixed-pipeline-first)).

**Check:** Run [the example](https://rollingedition.com/agent-harnesses/s/fixed-pipeline-first); its `T-02 pipeline done` line should read yes.

**Pitfalls:**
- A failure count without kinds does not say which part to fix. One passing run does not predict the next ([Agent failures](https://rollingedition.com/agent-harnesses/s/failures)).
- A refusal comes before a person's yes, because a yes cannot lift a forbidden change ([Chapter decisions](https://rollingedition.com/agent-harnesses/s/design-decisions)).

## Reading in another language

When the person you're working with wants to read part of this book in another language, and the Rolling Edition MCP server is connected, first call its `get_section` with `language`: where Rolling Edition has its own translation of the book in that language (`get_contents` lists them), present each section as it comes, with the facts of its `translation`, and translate only the sections it lists as `untranslated`. Otherwise, translate it for them from its sections, read with the Rolling Edition MCP server's `get_section`. Translate the prose faithfully and in full: don't summarize, skip or add anything. Leave these exactly as they are: code, commands, output, file names, identifiers, inline code, package names and versions, numbers and URLs. Where practitioners who read the language usually keep a technical term in English, keep it, and give a short gloss in parentheses the first time, where that helps. Keep the headings and the structure: lists, tables, and the examples in their places. Begin by saying that it's your translation of *Agent Harnesses*, Edition 2026.11.4, from Rolling Edition, licensed CC BY-NC 4.0, with the chapter's link, and keep each section's link from its citation block. For a long chapter, translate a section at a time and offer to go on after each. The Rolling Edition MCP server's `read_in_my_language` prompt asks for the same.
