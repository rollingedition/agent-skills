---
title: "Tutor"
book: "Agent Harnesses"
edition: "2026.11.8"
---

# Teaching *Agent Harnesses*

How to teach *Agent Harnesses*, Edition 2026.11.8, when someone asks to be taught, tutored or quizzed on it, as "Teach this book, when asked" in `SKILL.md` says, then every chapter's sections. The method is adapted from Jane Street's socratic-tutor skill, under MIT: `LICENSE.md` keeps its notice.

## How to teach it

**The topics** are the book's chapters, in order:

1. [Give a model tools and a loop](tools-and-a-loop.md)
2. [Stop the loop when it's done or stuck](stop-rules.md)
3. [Give the model tools it can't misuse](tool-schemas.md)
4. [One interface for scripted, replayed, local and hosted models](model-adapters.md)
5. [Keep the context useful as the task grows](context-budgets.md)
6. [Gate the tools that change things](permission-gates.md)
7. [Run the agent's code in a sandbox, and keep secrets out of its view](sandbox-and-secrets.md)
8. [Hand a subtask to a child, and hand back a stop](subagents-and-handoffs.md)
9. [Connect the harness to MCP servers](mcp-tools.md)
10. [Test the agent, then measure it on a task set](testing-the-agent.md)
11. [Trace each run and count what it cost](traces-and-cost.md)
12. [When an agent is the wrong design](when-an-agent-is-the-wrong-design.md)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. "The book's sections", below, lists each chapter's sections, with the examples each one runs and the terms it defines.

**Start**

1. Read each section before you ask about it. Judge every answer against the book: the section's text, the term's definition in `glossary.md`, beside this file, and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" in `SKILL.md`.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
Give a model tools and a loop    overall: █████░░░░░ 53%
--------------------------------------------------------
What the agent does on one task  ████████░░  4/5  alone
A loop in about seventy lines    ██████░░░░  3/5  <- now
Two tools and one stop tool      ██░░░░░░░░  1/5
--------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what its script in `scripts/` will print, or what will change if they change one line. Then have them run it, as `SKILL.md` shows, and compare with its `.out` file. Check the output they got, not their account of it.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/agent-harnesses/s/ followed by its ID.

**Levels are earned**

- Raise a level only after two or more separate checks, at least one of them recalled unprompted, not just after you told them the answer.
- A vague or partly right answer isn't right. Probe until you know. Never credit them with an insight they didn't state.
- Now and then, without warning, ask again about an earlier topic. If they miss, lower its level and go back to it.
- Level 5 needs an edge case or a hard question handled, and an explanation you'd trust them to teach from.
- No flattery: "Not quite: why would X happen if Y were true?" beats "Great try!"

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures in `SKILL.md` covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

After the exam, tell them once that each chapter's page on rollingedition.com ends with exercises from its examples (a chapter's page is the `canonical` link in its front matter, beside this file), and that with Rolling Edition Labs, Submit checks an answer by running it at this edition's pinned versions. Say it plainly, and never make the tutoring wait for it: everything here is free.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.8 and its code `7VH3-TBZX`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/agent-harnesses/changes lists them.

## The book's sections

Each chapter of Edition 2026.11.8 and its sections, in order, with the examples each section runs and the terms it defines. Each section links to its place in the chapter beside this file, and each script is in `scripts/`. Read a section before you ask about it.

### 1. Give a model tools and a loop

[The chapter](tools-and-a-loop.md). Defines: agent harness.

- [What the agent does on one task](tools-and-a-loop.md#one-task). Runs `scripts/read-the-issue.py`.
- [A loop in about seventy lines](tools-and-a-loop.md#the-loop). Defines: malformed call, ReAct, step, tool call.
- [Two tools and one stop tool](tools-and-a-loop.md#two-tools). Runs `scripts/tool-refusal.py`.
- [Stop when it's finished, or when the budget runs out](tools-and-a-loop.md#stop-rule).
- [Run it on a scripted model](tools-and-a-loop.md#scripted-run). Runs `scripts/scripted-loop.py`. Defines: scripted model.
- [Run it on the recorded model](tools-and-a-loop.md#replayed-run). Runs `scripts/recorded-run.py`. Defines: replay, request.
- [What goes wrong, and what is counted](tools-and-a-loop.md#what-goes-wrong).
- [Decisions in this chapter](tools-and-a-loop.md#chapter-decisions).

### 2. Stop the loop when it's done or stuck

[The chapter](stop-rules.md). Defines: task set.

- [Ways a run ends](stop-rules.md#ways-to-end). Defines: ended, no_tool_call, turn.
- [The budget counts steps](stop-rules.md#step-budget). Runs `scripts/budget-stops-a-loop.py`. Defines: step budget.
- [The same call, again](stop-rules.md#repeated-calls). Runs `scripts/repeated-call-stops.py`. Defines: identical call, repeated call.
- [No progress across edits](stop-rules.md#no-progress). Runs `scripts/no-progress-stops.py`. Defines: visible tests.
- [Asking, stopping and counting the endings](stop-rules.md#ask-instead). Runs `scripts/stop-rules-over-task-set.py`, `scripts/figure-steps-with-and-without-rules.py`.
- [Decisions in this chapter](stop-rules.md#stop-rules-decisions). Defines: no progress.

### 3. Give the model tools it can't misuse

[The chapter](tool-schemas.md). Defines: tool set v1, tool set v2.

- [A schema says what is allowed](tool-schemas.md#schema-says). Runs `scripts/schema-from-model.py`, `scripts/tool-descriptions.py`. Defines: argument model, tool schema, tool sentence.
- [Lax by default, strict on purpose](tool-schemas.md#lax-or-strict). Runs `scripts/lax-and-strict.py`. Defines: lax mode, strict mode.
- [Errors the model can read](tool-schemas.md#errors-readable). Runs `scripts/bad-arguments-handed-back.py`. Defines: refusal.
- [One name per tool](tool-schemas.md#one-name).
- [Edit errors that name the nearest lines](tool-schemas.md#edit-errors). Runs `scripts/edit-error-nearest-lines.py`. Defines: edit, nearest lines.
- [Decisions in this chapter](tool-schemas.md#decisions).

### 4. One interface for scripted, replayed, local and hosted models

[The chapter](model-adapters.md). Defines: model adapter.

- [Ask every model the same question](model-adapters.md#model-protocol). Defines: finish reason.
- [Script the replies, or replay a stored run](model-adapters.md#scripted-and-replayed). Runs `scripts/same-loop-two-models.py`, `scripts/replay-byte-for-byte.py`. Defines: request hash.
- [A local model, and why its settings are fixed](model-adapters.md#local-model). Defines: GGUF.
- [A hosted-style endpoint, tested on loopback](model-adapters.md#openai-compatible). Runs `scripts/openai-compatible-loopback.py`, `scripts/adapter-refuses-unsafe-endpoints.py`.
- [One loop, several models](model-adapters.md#one-loop).

### 5. Keep the context useful as the task grows

[The chapter](context-budgets.md).

- [The window the model has](context-budgets.md#window). Runs `scripts/budget-counts-tokens.py`. Defines: max_tokens, prompt budget.
- [Where the recorded runs came closest to the budget](context-budgets.md#where-tokens-go). Runs `scripts/figure-prompt-per-step.py`.
- [Estimate the prompt when the harness can't count it](context-budgets.md#estimate). Runs `scripts/estimate-vs-recorded.py`. Defines: estimate.
- [Put the last result at the end](context-budgets.md#last-result).
- [Compact the older steps, and keep the last pair](context-budgets.md#compaction). Runs `scripts/compact-keeps-last-result.py`. Defines: fixed part, local compaction.
- [Keep notes outside the context](context-budgets.md#notes). Runs `scripts/notes-survive.py`. Defines: notes.
- [What the recorded model did with the budget](context-budgets.md#recorded-runs). Runs `scripts/recorded-context-use.py`.
- [Measure the effect instead of quoting it](context-budgets.md#measure).
- [How a budget goes wrong, and how to notice](context-budgets.md#production).
- [Decisions this chapter made](context-budgets.md#what-this-chapter-decided).

### 6. Gate the tools that change things

[The chapter](permission-gates.md). Defines: library guard, library_changed, permission gate.

- [The copy comes first](permission-gates.md#copy-first). Runs `scripts/apply-all-or-nothing.py`. Defines: copy.
- [Which mode this harness is in](permission-gates.md#mode). Defines: headless run.
- [The gate sits in finish](permission-gates.md#gate-in-finish). Runs `scripts/gate-applies-only-on-yes.py`, `scripts/finish-body-waits-for-yes.py`. Defines: proposal, proposal hash.
- [An approval answers one request](permission-gates.md#bound-approval). Runs `scripts/hidden-diff-lines-shown.py`, `scripts/answer-binds-bytes.py`, `scripts/approval-in-transcript.py`. Defines: proposal ID.
- [Some changes are refused without a question](permission-gates.md#never-class). Runs `scripts/never-class-refused.py`, `scripts/gutted-test-refused.py`. Defines: held as never.
- [Refusals go back to the model](permission-gates.md#refusal). Runs `scripts/refusal-handed-back.py`.
- [The wrapper checks every call](permission-gates.md#wrapper). Runs `scripts/library-guard-fails-closed.py`, `scripts/unknown-tool-refused.py`. Defines: never class.
- [Allow lists do not skip the check](permission-gates.md#allow-lists). Defines: allow list.
- [Across the task set](permission-gates.md#task-set). Runs `scripts/gate-over-task-set.py`.
- [Vendor defaults that would let a change through](permission-gates.md#in-production).
- [What this gate does not cover](permission-gates.md#open-limits).
- [Decisions this chapter made](permission-gates.md#gate-decisions).

### 7. Run the agent's code in a sandbox, and keep secrets out of its view

[The chapter](sandbox-and-secrets.md). Defines: teaching sandbox.

- [A teaching sandbox, not a container](sandbox-and-secrets.md#teaching-sandbox). Defines: command.
- [Only listed programs](sandbox-and-secrets.md#listed-programs). Runs `scripts/argv-allowlist.py`, `scripts/injected-text-refused.py`, `scripts/same-effect-through-a-test-file.py`. Defines: argv allowlist.
- [Limits, and the grandchild they miss](sandbox-and-secrets.md#limits). Runs `scripts/limits-stop-a-hog.py`, `scripts/escaped-child.py`.
- [A network namespace, where the kernel allows one](sandbox-and-secrets.md#network). Runs `scripts/network-label.py`.
- [Secrets stay out of the environment](sandbox-and-secrets.md#secrets). Runs `scripts/secret-not-in-env.py`.

### 8. Hand a subtask to a child, and hand back a stop

[The chapter](subagents-and-handoffs.md). Defines: handoff, structured handoff.

- [A child is a loop with its own budget](subagents-and-handoffs.md#child-loop). Runs `scripts/child-with-budget.py`, `scripts/parent-starts-child.py`. Defines: child, child budget.
- [A brief with four parts](subagents-and-handoffs.md#brief). Defines: brief.
- [What comes back](subagents-and-handoffs.md#what-comes-back). Runs `scripts/summary-to-parent.py`.
- [A stop handed back](subagents-and-handoffs.md#a-stop-handed-back). Runs `scripts/handoff-on-stuck.py`. Defines: stuck stop.
- [Two designs, and whose numbers](subagents-and-handoffs.md#designs).
- [What goes wrong in production](subagents-and-handoffs.md#splits-in-production).
- [Decisions this chapter made](subagents-and-handoffs.md#subagent-decisions).

### 9. Connect the harness to MCP servers

[The chapter](mcp-tools.md).

- [The revision this book runs](mcp-tools.md#revision).
- [Listing a server's tools](mcp-tools.md#listing-tools). Runs `scripts/list-server-tools.py`. Defines: class table.
- [Names that cannot clash](mcp-tools.md#namespacing). Runs `scripts/namespace-clash.py`. Defines: server tool prefix.
- [Another party's tools need approval](mcp-tools.md#other-tools). Runs `scripts/annotation-is-a-hint.py`. Defines: tool annotation, tool class.
- [Output is untrusted](mcp-tools.md#output-is-untrusted). Runs `scripts/fence-cannot-be-closed.py`, `scripts/untrusted-output.py`. Defines: fence, indirect prompt injection, untrusted-output label.
- [What goes wrong in production](mcp-tools.md#mcp-tools-in-production).
- [Decisions this chapter made](mcp-tools.md#mcp-tools-decisions).

### 10. Test the agent, then measure it on a task set

[The chapter](testing-the-agent.md). Defines: hidden check, scenario test.

- [Scenario tests over a scripted model](testing-the-agent.md#scenario-tests). Runs `scripts/scenario-refusal.py`, `scripts/scenario-gate.py`, `scripts/scenario-stop-rule.py`, `scripts/scenario-injected-output.py`.
- [The hidden check runs in a copy](testing-the-agent.md#hidden-check). Runs `scripts/hidden-check-in-copy.py`, `scripts/scoring-ignores-planted-config.py`.
- [Score: tasks done out of 20](testing-the-agent.md#score). Runs `scripts/score-task-set.py`. Defines: done (fix or implement task), done (stop task), pass@1, pass^k.
- [T-18 counts through a path](testing-the-agent.md#t18-path).
- [How sure the count is](testing-the-agent.md#how-sure). Runs `scripts/figure-naive-range-coverage.py`. Defines: naive range, standard error of the proportion.
- [Two harness versions, compared as counts](testing-the-agent.md#v1-v2). Runs `scripts/compare-v1-v2.py`. Defines: harness v1, harness v2.
- [What the score does not say](testing-the-agent.md#score-limits).

### 11. Trace each run and count what it cost

[The chapter](traces-and-cost.md). Defines: stored count, trace.

- [One line per event](traces-and-cost.md#one-line-per-event). Runs `scripts/trace-one-run.py`.
- [IDs without clocks](traces-and-cost.md#ids).
- [Tokens as counts](traces-and-cost.md#token-counts). Runs `scripts/token-counts-from-recording.py`. Defines: completion count, prompt count, token.
- [A child's records sit under its parent's call](traces-and-cost.md#child-records). Runs `scripts/child-trace-under-parent.py`.
- [Cost as counts, not money](traces-and-cost.md#cost-not-money). Runs `scripts/cost-as-counts.py`, `scripts/figure-tokens-against-steps.py`. Defines: cost.
- [Keep your own field names, and map them at the edge](traces-and-cost.md#own-fields).
- [What goes wrong, and how you would notice](traces-and-cost.md#trace-pitfalls).
- [What this chapter decided](traces-and-cost.md#trace-decisions).

### 12. When an agent is the wrong design

[The chapter](when-an-agent-is-the-wrong-design.md).

- [Start with the fixed pipeline](when-an-agent-is-the-wrong-design.md#fixed-pipeline-first). Runs `scripts/fixed-pipeline-same-task.py`. Defines: action, agent, fixed pipeline, hybrid, workflow.
- [When splitting the work helps](when-an-agent-is-the-wrong-design.md#when-to-split).
- [What goes wrong when you do use an agent](when-an-agent-is-the-wrong-design.md#failures).
- [The check stays outside the agent](when-an-agent-is-the-wrong-design.md#check-outside).
- [The decision table](when-an-agent-is-the-wrong-design.md#which-design). Runs `scripts/decision-table.py`. Defines: decision table, single model call.
- [Decisions this chapter made](when-an-agent-is-the-wrong-design.md#design-decisions).
