---
title: "Glossary"
book: "Agent Harnesses"
edition: "2026.11.4"
canonical: "https://rollingedition.com/agent-harnesses/glossary"
---

# Glossary of *Agent Harnesses*

The 86 terms this book defines, as Edition 2026.11.4 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/agent-harnesses/glossary

## action

A pipeline has actions, which are its tool calls

- Also: actions
- Contrasts with: step
- Defined in: [Start with the fixed pipeline](when-an-agent-is-the-wrong-design.md#fixed-pipeline-first)
- Address: https://rollingedition.com/concepts/ai-agents/action

## agent

an agent when an LLM dynamically directs its own processes and tool use

- Also: agents
- Defined in: [Start with the fixed pipeline](when-an-agent-is-the-wrong-design.md#fixed-pipeline-first)
- Address: https://rollingedition.com/concepts/ai-agents/agent

## agent harness

The harness supplies the loop, the tools and the limits on what those tools may do

- Also: harness
- Defined in: [Give a model tools and a loop](tools-and-a-loop.md)
- Address: https://rollingedition.com/concepts/ai-agents/agent-harness

## allow list

A tool on an allow list runs without a question, and a gate placed at the question is then bypassed for that tool.

- Also: allow lists
- Defined in: [Allow lists do not skip the check](permission-gates.md#allow-lists)
- Address: https://rollingedition.com/concepts/ai-agents/allow-list

## argument model

an argument model, a small pydantic class that lists the fields the tool takes

- Also: argument models
- True for: pydantic 2.14.3
- Comes before: tool schema
- Implemented by: pydantic 2.14.3
- Defined in: [A schema says what is allowed](tool-schemas.md#schema-says)
- Address: https://rollingedition.com/concepts/ai-agents/argument-model

## argv allowlist

The allowlist is the check a command tool would use: it parses a command string once with shlex.split, and compares the argv with a short list of exact argv tuples.

- Also: allowlist
- Defined in: [Only listed programs](sandbox-and-secrets.md#listed-programs)
- Address: https://rollingedition.com/concepts/ai-agents/argv-allowlist

## brief

The brief is the job as the child receives it.

- Defined in: [A brief with four parts](subagents-and-handoffs.md#brief)
- Address: https://rollingedition.com/concepts/ai-agents/brief

## child

A child is the loop from chapter 1, started by a parent in the middle of its own run.

- Also: subagent, child run
- Defined in: [A child is a loop with its own budget](subagents-and-handoffs.md#child-loop)
- Address: https://rollingedition.com/concepts/ai-agents/child

## child budget

The child's budget counts the child's own model calls, from its first call, so the parent's steps don't pay for the child's work, and a child that loops runs out of its own budget.

- Part of: child
- Defined in: [A child is a loop with its own budget](subagents-and-handoffs.md#child-loop)
- Address: https://rollingedition.com/concepts/ai-agents/child-budget

## class table

The harness's class table, POLICY in lib/mcp_tools.py, gives each server tool a class, read or change, and only names that table gives a class appear in that line.

- Also: POLICY
- Defined in: [Listing a server's tools](mcp-tools.md#listing-tools)
- Address: https://rollingedition.com/concepts/ai-agents/class-table

## command

A command is an argv list, never a shell string, and the runner starts it with shell=False, so no shell reads its quotes or its semicolons (subprocess).

- Also: argv list
- Defined in: [A teaching sandbox, not a container](sandbox-and-secrets.md#teaching-sandbox)
- Address: https://rollingedition.com/concepts/ai-agents/command

## completion count

the completion count is the tokens it wrote

- Also: completion tokens, completion_tokens
- Defined in: [Tokens as counts](traces-and-cost.md#token-counts)
- Address: https://rollingedition.com/concepts/large-language-models/completion-count

## copy

Each run gets its own copy, made by scratch_copy in run_task, and the tools work through a Workspace rooted at that copy.

- Also: scratch copy
- Defined in: [The copy comes first](permission-gates.md#copy-first)
- Address: https://rollingedition.com/concepts/ai-agents/copy

## cost

a run's cost is three numbers: its steps, its tool calls and its tokens

- Computed from: step
- Computed from: tool call
- Computed from: token
- Defined in: [Cost as counts, not money](traces-and-cost.md#cost-not-money)
- Address: https://rollingedition.com/concepts/ai-agents/cost

## decision table

The decision table sorts each task by three readings: whether its steps are known before the run, whether a check can decide the result without a person, and whether a person has to say yes.

- Defined in: [The decision table](when-an-agent-is-the-wrong-design.md#which-design)
- Address: https://rollingedition.com/concepts/ai-agents/decision-table

## done (fix or implement task)

A fix or an implement task is done when the run ended with finish, its hidden check passes on the final copy, and the task's protected paths match the case byte for byte.

- Also: done
- Measured from: hidden check
- Defined in: [Score: tasks done out of 20](testing-the-agent.md#score)
- Address: https://rollingedition.com/concepts/llm-evaluation/done-fix-task

## done (stop task)

A stop task is done when the run ended with ask_user, its question contains one of the task's reason words, and no file in the copy differs from the case.

- Defined in: [Score: tasks done out of 20](testing-the-agent.md#score)
- Address: https://rollingedition.com/concepts/llm-evaluation/done-stop-task

## edit

An edit names the text it replaces.

- Also: edits
- Defined in: [Edit errors that name the nearest lines](tool-schemas.md#edit-errors)
- Address: https://rollingedition.com/concepts/ai-agents/edit

## ended

Every run ends for one stated reason, and the harness writes that reason into the run's ended field.

- Also: stop reason, ended value
- Defined in: [Ways a run ends](stop-rules.md#ways-to-end)
- Address: https://rollingedition.com/concepts/ai-agents/ended

## estimate

The estimate counts the characters of every message and of the tool schemas, and divides by three, rounding up: one token for every 3 characters.

- Also: prompt estimate
- Contrasts with: prompt count
- Defined in: [Estimate the prompt when the harness can't count it](context-budgets.md#estimate)
- Address: https://rollingedition.com/concepts/large-language-models/estimate

## fence

The fence is an opening tag that names the tool, and a closing tag.

- Defined in: [Output is untrusted](mcp-tools.md#output-is-untrusted)
- Address: https://rollingedition.com/concepts/ai-agents/fence

## finish reason

the finish reason, which says whether the model stopped on its own or ran out of tokens

- Also: finish_reason
- Defined in: [Ask every model the same question](model-adapters.md#model-protocol)
- Address: https://rollingedition.com/concepts/large-language-models/finish-reason

## fixed part

The fixed part, the system prompt, the tool schemas and the issue

- Defined in: [Compact the older steps, and keep the last pair](context-budgets.md#compaction)
- Address: https://rollingedition.com/concepts/ai-agents/fixed-part

## fixed pipeline

A fixed pipeline is a task's list of steps, written as code before the run starts.

- Also: pipeline
- Contrasts with: agent
- Defined in: [Start with the fixed pipeline](when-an-agent-is-the-wrong-design.md#fixed-pipeline-first)
- Address: https://rollingedition.com/concepts/ai-agents/fixed-pipeline

## GGUF

a GGUF file, the single-file format llama.cpp reads

- Also: GGUF file
- Defined in: [A local model, and why its settings are fixed](model-adapters.md#local-model)
- Address: https://rollingedition.com/concepts/large-language-models/gguf

## handoff

a handoff is a run's end with a question back to a person, instead of a finish

- Also: handoffs
- Defined in: [Hand a subtask to a child, and hand back a stop](subagents-and-handoffs.md)
- Address: https://rollingedition.com/concepts/ai-agents/handoff

## harness v1

Harness v1 is the loop of chapter 1 with tool set v1 from chapter 3, a step cap of 16 steps, and no stop rule beyond it.

- Defined in: [Two harness versions, compared as counts](testing-the-agent.md#v1-v2)
- Address: https://rollingedition.com/concepts/ai-agents/harness-v1

## harness v2

Harness v2 is the configuration of chapter 5: it runs tool set v2, with strict argument models, typed error results and edit errors that name the nearest lines of the file.

- Contrasts with: harness v1
- Defined in: [Two harness versions, compared as counts](testing-the-agent.md#v1-v2)
- Address: https://rollingedition.com/concepts/ai-agents/harness-v2

## headless run

This harness has no terminal and no session: it is a headless run, and the only party who can answer is a callback that the caller passes in.

- Also: headless run with a callback
- Defined in: [Which mode this harness is in](permission-gates.md#mode)
- Address: https://rollingedition.com/concepts/ai-agents/headless-run

## hidden check

The hidden check asks whether a finished run fixed the task.

- Defined in: [Test the agent, then measure it on a task set](testing-the-agent.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/hidden-check

## hybrid

The hybrid, a pipeline first and an agent only on a pipeline_stop

- Defined in: [Start with the fixed pipeline](when-an-agent-is-the-wrong-design.md#fixed-pipeline-first)
- Address: https://rollingedition.com/concepts/ai-agents/hybrid

## identical call

A call is identical when it has the same tool name and the same arguments, compared with the keys sorted.

- Also: identical calls
- Comes before: repeated call
- Defined in: [The same call, again](stop-rules.md#repeated-calls)
- Address: https://rollingedition.com/concepts/ai-agents/identical-call

## indirect prompt injection

The threat is indirect prompt injection: text that an application retrieves from outside can carry instructions, and a model that reads that text may follow them.

- Also: prompt injection
- Defined in: [Output is untrusted](mcp-tools.md#output-is-untrusted)
- Address: https://rollingedition.com/concepts/large-language-models/indirect-prompt-injection

## lax mode

In pydantic's default, lax mode, a value is converted when the conversion is clear and refused when it is not.

- True for: pydantic 2.14.3
- Implemented by: pydantic 2.14.3
- Defined in: [Lax by default, strict on purpose](tool-schemas.md#lax-or-strict)
- Address: https://rollingedition.com/concepts/ai-agents/lax-mode

## library guard

a guard that compares the library's bytes around every tool call

- Also: guard
- Defined in: [Gate the tools that change things](permission-gates.md)
- Address: https://rollingedition.com/concepts/ai-agents/library-guard

## library_changed

when the library has changed, the run ends as library_changed, the harness applies nothing, and it restores nothing

- A kind of: ended
- Defined in: [Gate the tools that change things](permission-gates.md)
- Address: https://rollingedition.com/concepts/ai-agents/library-changed

## local compaction

Compaction here is local: the harness writes the summary itself, and the model never sees it being written.

- Also: compaction
- Defined in: [Compact the older steps, and keep the last pair](context-budgets.md#compaction)
- Address: https://rollingedition.com/concepts/ai-agents/local-compaction

## malformed call

The harness never runs a block that doesn't parse: it records it as a malformed call and hands the reason back to the model as an error result, so the model can try again.

- Also: malformed calls
- Defined in: [A loop in about seventy lines](tools-and-a-loop.md#the-loop)
- Address: https://rollingedition.com/concepts/ai-agents/malformed-call

## max_tokens

max_tokens, the most the reply may take

- Defined in: [The window the model has](context-budgets.md#window)
- Address: https://rollingedition.com/concepts/large-language-models/max-tokens

## model adapter

The adapter is the code that makes each source, from a scripted list of strings to an HTTP endpoint, look the same to the loop

- Also: adapter, adapters
- Defined in: [One interface for scripted, replayed, local and hosted models](model-adapters.md)
- Address: https://rollingedition.com/concepts/ai-agents/model-adapter

## naive range

The naive range treats each task as an independent trial, and it is built with the usual multiplier for a 95% interval, which is slightly under two.

- Computed from: standard error of the proportion
- Defined in: [How sure the count is](testing-the-agent.md#how-sure)
- Address: https://rollingedition.com/concepts/llm-evaluation/naive-range

## nearest lines

The harness slides a window of the same length as old down the file, keeps the window that matches best, and breaks a tie toward the earlier window, so the answer is the same on every run.

- Also: nearest-line errors
- Defined in: [Edit errors that name the nearest lines](tool-schemas.md#edit-errors)
- Address: https://rollingedition.com/concepts/ai-agents/nearest-lines

## never class

The table in lib/permissions.py is the only source of a tool's class, and a tool outside it is classed never.

- A kind of: tool class
- Defined in: [The wrapper checks every call](permission-gates.md#wrapper)
- Address: https://rollingedition.com/concepts/ai-agents/never-class

## no progress

No progress is two edits in a row that leave the harness's test counts unchanged.

- Also: no_progress, no-progress rule
- A kind of: ended
- Defined in: [Decisions in this chapter](stop-rules.md#stop-rules-decisions)
- Address: https://rollingedition.com/concepts/ai-agents/no-progress

## no_tool_call

A second reply with no call in a row ends the run as no_tool_call.

- A kind of: ended
- Defined in: [Ways a run ends](stop-rules.md#ways-to-end)
- Address: https://rollingedition.com/concepts/ai-agents/no-tool-call

## notes

The harness adds a note tool: the model writes one line per fact, and the harness sends the notes after the issue at every step.

- Also: note tool
- Contrasts with: local compaction
- Defined in: [Keep notes outside the context](context-budgets.md#notes)
- Address: https://rollingedition.com/concepts/ai-agents/notes

## pass@1

The score is pass@1: the number of done tasks, divided by the number of tasks.

- Also: score
- Computed from: done (fix or implement task)
- Computed from: done (stop task)
- Contrasts with: pass^k
- Defined in: [Score: tasks done out of 20](testing-the-agent.md#score)
- Address: https://rollingedition.com/concepts/llm-evaluation/pass-at-1

## pass^k

tau-bench defines pass^k as the chance that all k trials of a task succeed, "averaged across tasks", and it needs k trials per task.

- Defined in: [Score: tasks done out of 20](testing-the-agent.md#score)
- Address: https://rollingedition.com/concepts/llm-evaluation/pass-hat-k

## permission gate

a gate that reads the diff at finish

- Also: gate
- Defined in: [Gate the tools that change things](permission-gates.md)
- Address: https://rollingedition.com/concepts/ai-agents/permission-gate

## prompt budget

This chapter calls the tokens left for everything the model reads on one step the prompt budget.

- Computed from: max_tokens
- Defined in: [The window the model has](context-budgets.md#window)
- Address: https://rollingedition.com/concepts/large-language-models/prompt-budget

## prompt count

The prompt count is the tokens the model read

- Also: prompt tokens, prompt_tokens
- Defined in: [Tokens as counts](traces-and-cost.md#token-counts)
- Address: https://rollingedition.com/concepts/large-language-models/prompt-count

## proposal

A proposal is the copy's whole diff against the library, not the summary the model wrote.

- Also: proposals
- Defined in: [The gate sits in finish](permission-gates.md#gate-in-finish)
- Address: https://rollingedition.com/concepts/ai-agents/proposal

## proposal hash

The proposal's identity is a hash of the changed bytes

- Part of: proposal
- Defined in: [The gate sits in finish](permission-gates.md#gate-in-finish)
- Address: https://rollingedition.com/concepts/ai-agents/proposal-hash

## proposal ID

Each proposal takes the next ID from a counter on its gate, p-1, then p-2, and so on

- Part of: proposal
- Defined in: [An approval answers one request](permission-gates.md#bound-approval)
- Address: https://rollingedition.com/concepts/ai-agents/proposal-id

## ReAct

ReAct interleaves written reasoning with actions

- Defined in: [A loop in about seventy lines](tools-and-a-loop.md#the-loop)
- Address: https://rollingedition.com/concepts/ai-agents/react

## refusal

each refusal goes back as the text of a tool result, the same kind of text as any other result, which the model reads on its next step

- Also: refusals
- Defined in: [Errors the model can read](tool-schemas.md#errors-readable)
- Address: https://rollingedition.com/concepts/ai-agents/refusal

## repeated call

Three identical calls in a row end the run as repeated_call.

- Also: repeated_call, repeated-call rule
- A kind of: ended
- Defined in: [The same call, again](stop-rules.md#repeated-calls)
- Address: https://rollingedition.com/concepts/ai-agents/repeated-call

## replay

Replay checks that each request matches the one the recording holds, where a request is the messages and tool schemas sent at one step, and then returns the recorded reply.

- Also: replayed run, ReplayModel
- Defined in: [Run it on the recorded model](tools-and-a-loop.md#replayed-run)
- Address: https://rollingedition.com/concepts/ai-agents/replay

## request

a request is the messages and tool schemas sent at one step

- Comes before: replay
- Defined in: [Run it on the recorded model](tools-and-a-loop.md#replayed-run)
- Address: https://rollingedition.com/concepts/large-language-models/request

## request hash

ReplayModel hashes the request it was given, the sha256 of its messages and tool schemas in canonical JSON

- Computed from: request
- Defined in: [Script the replies, or replay a stored run](model-adapters.md#scripted-and-replayed)
- Address: https://rollingedition.com/concepts/ai-agents/request-hash

## scenario test

A scenario test asks whether the harness does the right thing with one fixed sequence of replies.

- Also: scenario tests
- Contrasts with: pass@1
- Defined in: [Test the agent, then measure it on a task set](testing-the-agent.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/scenario-test

## scripted model

A scripted model gives back the replies you give it, in order, and nothing else.

- Also: ScriptedModel
- Defined in: [Run it on a scripted model](tools-and-a-loop.md#scripted-run)
- Address: https://rollingedition.com/concepts/ai-agents/scripted-model

## server tool prefix

the harness gives each server's tools a prefix: server__tool, with a double underscore as the separator

- Also: server__tool
- Defined in: [Names that cannot clash](mcp-tools.md#namespacing)
- Address: https://rollingedition.com/concepts/ai-agents/server-tool-prefix

## single model call

A single model call fits a step that needs a model's judgement, with no tool and no loop, and whose output a person reads afterwards.

- Defined in: [The decision table](when-an-agent-is-the-wrong-design.md#which-design)
- Address: https://rollingedition.com/concepts/ai-agents/single-model-call

## standard error of the proportion

The standard error of the proportion is the square root of a fraction: the proportion times one minus the proportion, divided by the number of tasks.

- Computed from: pass@1
- Defined in: [How sure the count is](testing-the-agent.md#how-sure)
- Address: https://rollingedition.com/concepts/llm-evaluation/standard-error-of-the-proportion

## step

A step is one model call.

- Also: steps
- Comes before: step budget
- Defined in: [A loop in about seventy lines](tools-and-a-loop.md#the-loop)
- Address: https://rollingedition.com/concepts/ai-agents/step

## step budget

The step budget is the most steps a run may take, and the loop stops when it reaches that number.

- Also: step cap, step_cap
- Defined in: [The budget counts steps](stop-rules.md#step-budget)
- Address: https://rollingedition.com/concepts/ai-agents/step-budget

## stored count

Every count in this chapter is read from a recording or printed by a script, and none is taken from a live model, so the counts are stored counts, and the one check that would re-derive them from the model has not been run.

- Also: stored counts
- Defined in: [Trace each run and count what it cost](traces-and-cost.md)
- Address: https://rollingedition.com/concepts/large-language-models/stored-count

## strict mode

In strict mode, a value must already have the declared type.

- True for: pydantic 2.14.3
- Contrasts with: lax mode
- Implemented by: pydantic 2.14.3
- Defined in: [Lax by default, strict on purpose](tool-schemas.md#lax-or-strict)
- Address: https://rollingedition.com/concepts/ai-agents/strict-mode

## structured handoff

the harness's structured handoff after a stop, which carries the stop reason, what the run tried and a question

- A kind of: handoff
- Defined in: [Hand a subtask to a child, and hand back a stop](subagents-and-handoffs.md)
- Address: https://rollingedition.com/concepts/ai-agents/structured-handoff

## stuck stop

For the three stops that end a child stuck, step_cap, repeated_call and no_progress, the harness builds the handoff from the run's own record: its trace, its streak of repeated calls and its test counts.

- Also: stuck stops
- Comes before: structured handoff
- Defined in: [A stop handed back](subagents-and-handoffs.md#a-stop-handed-back)
- Address: https://rollingedition.com/concepts/ai-agents/stuck-stop

## task set

the task set: the 20 tasks that testing the agent scores, run with tool set v1, whose tools include edits

- Defined in: [Stop the loop when it's done or stuck](stop-rules.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/task-set

## teaching sandbox

What the book builds is the sandbox in sandbox.py, which is teaching code and a second layer, not the protection itself.

- Also: sandbox
- Defined in: [Run the agent's code in a sandbox, and keep secrets out of its view](sandbox-and-secrets.md)
- Address: https://rollingedition.com/concepts/ai-agents/teaching-sandbox

## token

a token is a unit of one vocabulary, and the same text can split into different numbers of units under another

- Also: tokens
- Comes before: prompt count
- Comes before: completion count
- Defined in: [Tokens as counts](traces-and-cost.md#token-counts)
- Address: https://rollingedition.com/concepts/large-language-models/token

## tool annotation

An annotation is the server's own description of its tool, and a server that is wrong, or compromised, sets the same field as one that is right.

- Also: annotation, annotations
- True for: mcp 2.3.0
- Contrasts with: class table
- Implemented by: mcp 2.3.0
- Defined in: [Another party's tools need approval](mcp-tools.md#other-tools)
- Address: https://rollingedition.com/concepts/ai-agents/tool-annotation

## tool call

A tool call is one request inside a step

- Also: tool calls
- Part of: step
- Defined in: [A loop in about seventy lines](tools-and-a-loop.md#the-loop)
- Address: https://rollingedition.com/concepts/ai-agents/tool-call

## tool class

Chapter 6 divided the harness's tools into classes: a read runs, and a change waits.

- Defined in: [Another party's tools need approval](mcp-tools.md#other-tools)
- Address: https://rollingedition.com/concepts/ai-agents/tool-class

## tool schema

Think of a tool's schema as the form the model fills in before it makes a call.

- Also: schema, tool schemas
- Defined in: [A schema says what is allowed](tool-schemas.md#schema-says)
- Address: https://rollingedition.com/concepts/ai-agents/tool-schema

## tool sentence

A tool's sentence says what the tool is for.

- Also: tool description
- Defined in: [A schema says what is allowed](tool-schemas.md#schema-says)
- Address: https://rollingedition.com/concepts/ai-agents/tool-sentence

## tool set v1

Tool set v1 is the seven tools the task-set recording was made with: list_files, read_file, run_tests, write_file, edit_file, ask_user and finish.

- Also: v1 tools
- Defined in: [Give the model tools it can't misuse](tool-schemas.md)
- Address: https://rollingedition.com/concepts/ai-agents/tool-set-v1

## tool set v2

Tool set v2 has the same seven tools as tool set v1, with the same sentences and the same system prompt, and three changes: strict argument models, the error type named in each refusal, and nearest-line errors for a failed edit.

- Also: v2 tools
- Contrasts with: tool set v1
- Defined in: [Give the model tools it can't misuse](tool-schemas.md)
- Address: https://rollingedition.com/concepts/ai-agents/tool-set-v2

## trace

The record of each step is the trace.

- Also: traces
- Defined in: [Trace each run and count what it cost](traces-and-cost.md)
- Address: https://rollingedition.com/concepts/ai-agents/trace

## turn

This book keeps "turn" for an exchange with the person who gave the task.

- Contrasts with: step
- Defined in: [Ways a run ends](stop-rules.md#ways-to-end)
- Address: https://rollingedition.com/concepts/ai-agents/turn

## untrusted-output label

The label says that the text comes from another party, that it is to be read as data, and that it cannot change the stop rules, the allowed commands or an approval, because the harness enforces those whatever the text says.

- Defined in: [Output is untrusted](mcp-tools.md#output-is-untrusted)
- Address: https://rollingedition.com/concepts/ai-agents/untrusted-output-label

## visible tests

the visible tests, the case's own test suite

- Also: visible suite
- Contrasts with: hidden check
- Defined in: [No progress across edits](stop-rules.md#no-progress)
- Address: https://rollingedition.com/concepts/llm-evaluation/visible-tests

## workflow

a workflow when LLMs and tools are orchestrated through predefined code paths

- Contrasts with: agent
- Defined in: [Start with the fixed pipeline](when-an-agent-is-the-wrong-design.md#fixed-pipeline-first)
- Address: https://rollingedition.com/concepts/ai-agents/workflow
