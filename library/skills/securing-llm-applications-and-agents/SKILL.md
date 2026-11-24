---
name: securing-llm-applications-and-agents
description: "Use when threat-modelling an LLM assistant or agent that has tools and reads text other people wrote, or when measuring whether a defence against prompt injection, data exfiltration or tool misuse works. Covers the threat model; an attack set scored in code, split into dev and held-out; paired comparisons with intervals; prompt defences, detectors and their false alarms; least privilege, egress rules and isolation in the harness; secrets and retrieval by role; checking third-party tools and model files; adaptive red-teaming; and regression gates. When someone explicitly asks to be taught, tutored or quizzed on what this book covers (\"teach me\", \"tutor me\", \"quiz me\"), it also tutors them, one question at a time. Not for a one-off \"explain X\" or \"what is X\"."
license: CC-BY-NC-4.0 AND MIT
compatibility: "The book's examples ran on Python 3.13.16 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Securing LLM Applications and Agents"
  edition: "2026.11.2"
  verified: "2026-11-22"
  examples: "60 of 60 examples pass"
  edition-code: "Y3X2-HXT9"
  source: "https://rollingedition.com/securing-llm-applications-and-agents"
---

# Securing LLM Applications and Agents

This agent skill is *Securing LLM Applications and Agents*, Edition 2026.11.2, from Rolling Edition. Examples passed Nov 22, 2026: 60 of 60 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `securing-llm-applications-and-agents` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Use the book's terms as it defines them.** The book's Glossary has each term it defines, in the book's own sentence, with its section: https://rollingedition.com/securing-llm-applications-and-agents/glossary. The Rolling Edition MCP server's `define` gives one with its section, its edition and the version it's true for: where the task uses one, it means that.
- **Is this copy current?** Call `check_code` with `Y3X2-HXT9` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/securing-llm-applications-and-agents
- **Credit the book** when you quote it or reuse its code: Securing LLM Applications and Agents, Edition 2026.11.2, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/securing-llm-applications-and-agents. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `securing-llm-applications-and-agents` plugin and the zip on the book's page at rollingedition.ai.

## Draw the assistant's threat model

**When:** Before you add a defence, when you need to know which tools and data an assistant can reach from text it did not write.

1. Draw the assets and trust boundaries from the code's list of tools, not from the design document. For each tool, record what it reads, what it writes, which results carry text from outside, and whether its definition came from outside ([Assets and trust](https://rollingedition.com/securing-llm-applications-and-agents/s/assets-and-trust)).
2. Map the data flows, including the outward ones. Name each location's carrier and the tool that delivers it, and count a location as a channel only when some delivery reaches the model ([Data flows](https://rollingedition.com/securing-llm-applications-and-agents/s/data-flows)).
3. Count the legs of the lethal trifecta for every tool: private data, untrusted content, and a way to communicate outward. Then remove each leg's tools in turn and count again. Apply the Rule of Two, and keep no tool that combines all three ([The trifecta and the rule of two](https://rollingedition.com/securing-llm-applications-and-agents/s/the-trifecta-and-the-rule-of-two)).
4. Map each risk to an OWASP, ASI or ATLAS entry only when the book has confirmed its ID, and say that the risk is not measured when no chapter measures it ([Risks mapped](https://rollingedition.com/securing-llm-applications-and-agents/s/risks-mapped)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/the-trifecta-and-the-rule-of-two). Its `tools checked` line should read 8, and every tool with all three legs should be named in your model. Check the tool count in [the tool table](https://rollingedition.com/securing-llm-applications-and-agents/s/assets-and-trust) against your prompt's tool list.

**Pitfalls:**
- An allowlist on one channel says nothing about the others. Read every outward flow the same way.
- A design document can list tools the code does not offer, and miss some it does.

## Build an attack set you can score in code

**When:** You need an attack rate you can explain: each case has a goal, a location for its text and a style, and a check decides whether it succeeded.

1. Choose the goals, the locations where the attacker's text can arrive, and the styles it is written in. Keep the three as separate, crossed labels ([Goals, locations and styles](https://rollingedition.com/securing-llm-applications-and-agents/s/goals-locations-styles)).
2. Write each goal's check first, on the trace, and make it read every channel the goal names. Test it on one trace that reaches the goal and one that does not, and make it pass both before any case uses it. Count a run that errors apart from a failed attack ([Scorers on the trace](https://rollingedition.com/securing-llm-applications-and-agents/s/scorers-on-the-trace)).
3. Split the cases into dev and held-out, with at least one case of each goal, location and style on each. Do not add cases to a split once its results are in ([Dev and held-out](https://rollingedition.com/securing-llm-applications-and-agents/s/dev-and-held-out)).
4. Measure the undefended assistant on dev before you change anything, and report each rate with its count and interval. Where a cell is small, report the count alone ([The undefended assistant on dev](https://rollingedition.com/securing-llm-applications-and-agents/s/undefended-baseline)).
5. Keep attack strings in data files. Use a public corpus only to measure a classifier on text in general ([Why not a public corpus](https://rollingedition.com/securing-llm-applications-and-agents/s/why-not-a-public-corpus)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/scorers-on-the-trace). Its passing count for the phone goal should read 2 of 2, which is the check working on both traces.

**Pitfalls:**
- A rate over a handful of cases is a count in disguise. Quote the count in the same sentence.

## Measure a defence on the same cases

**When:** You have added a defence and need to say whether it changed attack success or benign utility, and by how much.

1. Run the same cases twice, once undefended and once with the defence on, and pair the results case by case ([An outbound allowlist](https://rollingedition.com/securing-llm-applications-and-agents/s/an-outbound-allowlist)).
2. Report the paired difference with its interval and counts. Call the change real only when the interval excludes zero ([Evaluating LLM Applications, chapter 8](https://rollingedition.com/evaluating-llm-applications/s/paired-comparisons)).
3. Compare two configurations only on the same users and tasks ([The office and its assistant](https://rollingedition.com/securing-llm-applications-and-agents/s/the-office-and-its-assistant)).
4. Beside any result on a defence, list the channels the defence does not see, in the same paragraph ([What the allowlist cannot see](https://rollingedition.com/securing-llm-applications-and-agents/s/what-the-allowlist-cannot-see)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/an-outbound-allowlist). Its `paired difference, interval` line should read [-100.0, -100.0] points.

**Pitfalls:**
- A zero on tool calls is not a zero on replies or on records.

## Measure what a prompt-level defence buys

**When:** You are considering a warning, delimiters, datamarking, an encoding or a repeated request in the prompt.

1. Tune the wording on dev only. If a dev result sends you back to change the defence, it is a new defence with its own held-out run ([Dev and held-out](https://rollingedition.com/securing-llm-applications-and-agents/s/dev-and-held-out)).
2. Run the defence once on held-out, and count its benign cost beside any gain. Keep a warning as a layer only when its held-out attack-success interval excludes zero. A zero on dev is a reason to run held-out, not a result ([A warning in the prompt](https://rollingedition.com/securing-llm-applications-and-agents/s/a-warning-in-the-prompt)).
3. Treat delimiters as a way to show the model where untrusted text starts and stops, not as a control on what the model does ([Delimiters](https://rollingedition.com/securing-llm-applications-and-agents/s/delimiters-alone)). Measure datamarking's utility on held-out before you accept it ([Datamarking](https://rollingedition.com/securing-llm-applications-and-agents/s/datamarking)).
4. Read an encoding's utility on the held-out benign tasks before you call it a defence. It can stop every attack in a set and still leave the assistant unable to do its work ([Encoding](https://rollingedition.com/securing-llm-applications-and-agents/s/encoding)).
5. Before you repeat the request, count the tasks that need an action, and check that the run still makes those calls. A repeat that stops the action also stops the task ([Repeating the request](https://rollingedition.com/securing-llm-applications-and-agents/s/repeating-the-request)).
6. Count each defence's tokens with the deployed model's tokeniser, beside its benign and attack results ([What each costs](https://rollingedition.com/securing-llm-applications-and-agents/s/what-each-costs)).
7. Before you credit a smaller model with lower attack success, count how often it read the carrier text ([A smaller model](https://rollingedition.com/securing-llm-applications-and-agents/s/a-smaller-model)).
8. Report each defence's held-out paired difference with its interval, and do not tune again on held-out ([The held-out run](https://rollingedition.com/securing-llm-applications-and-agents/s/the-held-out-run)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/prompt-defences). Its baseline attack success on the 60 held-out cases should read 11.7% (7 of 60), the figure each defence is compared against.

**Pitfalls:**
- A prompt defence is one layer. Do not describe it as a fix for prompt injection.

## Detect injected text, and count the false alarms

**When:** You want a classifier or a model to flag injected text before the assistant reads it, and you need to know how often it is wrong.

1. Read the model card for what the model was built for, and count the detector's errors on your own texts before you trust a flag ([A classifier guard](https://rollingedition.com/securing-llm-applications-and-agents/s/a-classifier-guard)).
2. Pick the threshold on dev, with a rule written down before you saw the scores. Print the flagged counts at every grid value, and the number of scores near the pick ([Picking a threshold on dev](https://rollingedition.com/securing-llm-applications-and-agents/s/picking-a-threshold-on-dev)).
3. Count false alarms on held-out and on public text separately, naming the kind of text in each count ([False alarms on real text](https://rollingedition.com/securing-llm-applications-and-agents/s/false-alarms-on-real-text)).
4. Measure a filter's price on the benign tasks it touches, paired with the same tasks undefended. Read each interval before its point ([The detector as a filter](https://rollingedition.com/securing-llm-applications-and-agents/s/the-detector-as-a-filter)).
5. For a model used as a detector, count its errors on dev and state which way they run before its verdicts count ([The open model as a detector](https://rollingedition.com/securing-llm-applications-and-agents/s/the-open-model-as-a-detector)).
6. A content-safety guard that flags nothing on benign text answers a different question, so its quiet says nothing about injection ([A content-safety guard is not an injection detector](https://rollingedition.com/securing-llm-applications-and-agents/s/a-content-guard-is-not-a-detector)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/picking-a-threshold-on-dev). Its `dev scores within 0.02 of the pick` line should read 0 of 86.

## Enforce least privilege in the harness

**When:** A task should reach only the tools it needs, and a refusal must come from code rather than from the model's judgment.

1. Write each task's tool list in code, from the task's request, before the run starts. Put only those tools in the prompt, and refuse and log any call to a tool outside the list. A task that cannot name its tools before it reads data is outside this control, and its design should say so ([A tool filter per task](https://rollingedition.com/securing-llm-applications-and-agents/s/a-tool-filter-per-task)).
2. Write one argument policy per task, from its request and schemas. Run it on every call, and refuse any call it cannot read. Test it against the encodings an attacker would try, and write down each form it allows ([Argument policies](https://rollingedition.com/securing-llm-applications-and-agents/s/argument-policies)).
3. Put an approval on every tool with a side effect, counting a fetch that carries data out as one ([Approval for side effects](https://rollingedition.com/securing-llm-applications-and-agents/s/approval-for-side-effects)).
4. Tokenise untrusted text with special tokens off, insert your own markers by ID, and check the token IDs of the composed prompt ([Control tokens in untrusted text](https://rollingedition.com/securing-llm-applications-and-agents/s/control-tokens-in-untrusted-text)).
5. Replay each control on held-out as well as dev, and count refusals on the benign tasks. Fifteen tasks with no lost task show a cost under about one task in fifteen ([What least privilege costs](https://rollingedition.com/securing-llm-applications-and-agents/s/what-least-privilege-costs)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/held-out-run). Its `baseline, attack success, 60 held-out cases` line should read 11.7% (7 of 60), and its controls should be read beside it.

**Pitfalls:**
- A rule on the values in a call is not a rule on its content.

## Close the exfiltration channels

**When:** The assistant can fetch pages, send messages, or put links and images in its reply.

1. Allowlist the hosts first, then read what the allowed requests carry. A host check says where data goes, and a query check says what the data is. Name the one you measured and the one you did not ([Egress rules](https://rollingedition.com/securing-llm-applications-and-agents/s/egress-rules)).
2. Keep the network limit outside the code as the primary defence. The check in the harness is the second layer, and it should refuse when it cannot decide ([Egress rules](https://rollingedition.com/securing-llm-applications-and-agents/s/egress-rules)).
3. Apply the render policy to links and images in the reply, and list in the same paragraph the channels it covers and those it does not, such as a redirect an office host sends on ([Links and images in the reply](https://rollingedition.com/securing-llm-applications-and-agents/s/links-and-images-in-the-reply), [What the render policy does with each form](https://rollingedition.com/securing-llm-applications-and-agents/s/render-forms)).
4. Treat the output as untrusted, and check the reply at the point where it leaves the harness. Name each check's blind spot in the paragraph that reports its result ([Output is untrusted](https://rollingedition.com/securing-llm-applications-and-agents/s/output-is-untrusted)).
5. A secret scan on output answers one question: was the plain text there? It does not show that the secret left. Remove the secret from the context first, and keep the scan for what that removal missed ([Scanning the reply for secrets](https://rollingedition.com/securing-llm-applications-and-agents/s/scanning-the-reply-for-secrets)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/egress-rules). Its `utility, baseline, 15 dev benign tasks` line should read 93.3% (14 of 15), and the paired difference in attack success should read with its interval beside it.

**Pitfalls:**
- A zero from one set is a fact about that set and that model, not about the channel.

## Isolate untrusted text from the model that plans

**When:** The model that chooses calls must never read untrusted text directly, or a design must keep it apart.

1. For a dual LLM, hold untrusted text in variables the planner refers to, and let a quarantined model read them. Check that the quarantined model is ever called. A design whose second model never runs is measured only by what it hides ([The dual LLM](https://rollingedition.com/securing-llm-applications-and-agents/s/dual-llm)).
2. For plan-then-execute, count the first replies that hold the whole plan. If the model writes one call at a time, let the plan grow across replies, or expect the send to be refused after the reads ([Plan-then-execute](https://rollingedition.com/securing-llm-applications-and-agents/s/plan-then-execute)).
3. For taint labels, label a value where a tool result enters the planner's context, and refuse it only where it reaches a side-effecting argument. Measure the refusals on held-out before you fix the rule ([Taint labels](https://rollingedition.com/securing-llm-applications-and-agents/s/taint-labels)).
4. Report each design's benign utility on held-out beside its attack success. Keep a design only where its attack-success interval excludes zero ([The utility cost](https://rollingedition.com/securing-llm-applications-and-agents/s/the-utility-cost)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/dual-llm). Its `benign tasks lost, design-dual-llm` line should read 2 of 15.

## Keep secrets and other people's records out of the context

**When:** A prompt would hold a key, a note, or records the acting user may not read.

1. Keep the key and the note out of the prompt before you rely on any check of the reply, since a value that never entered the prompt cannot be printed. Then count the prompts that still hold a value ([Hidden context](https://rollingedition.com/securing-llm-applications-and-agents/s/hidden-context)).
2. Keep each credential with the code that uses it, and give the model results, not values. Measure the defence by the prompt count and by the attack goals that need the value ([Keys out of the prompt](https://rollingedition.com/securing-llm-applications-and-agents/s/keys-out-of-the-prompt)).
3. Filter by the acting user's rights before ranking, never after, since the scores of hidden documents still shape a top k that is filtered later ([Retrieval by role](https://rollingedition.com/securing-llm-applications-and-agents/s/retrieval-by-role)).
4. Treat a figure in a reply as unsupported until the reply cites an office document that states it, and read that document too, since the check reads only the reply ([Poisoned documents in the index](https://rollingedition.com/securing-llm-applications-and-agents/s/poisoned-documents-in-the-index)).
5. Rerun the prompt count and the held-out split after each change to the prompt, the source labels or the citation format ([What goes wrong in production](https://rollingedition.com/securing-llm-applications-and-agents/s/what-goes-wrong-in-production)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/hidden-context). Its `dev, baseline, attack success, 60 cases` line should read 11.7% (7 of 60), beside the prompt count.

## Check third-party parts before the assistant is offered them

**When:** You are adding a tool from another party, a model file, or a dependency.

1. Check each tool's declared effect and arguments against its behaviour, on the definition the server offers and again on each change ([Declared effects are claims](https://rollingedition.com/securing-llm-applications-and-agents/s/descriptions-are-claims)).
2. Pin every tool definition from the version a person approved, and compare the pin on each load. A changed definition drops out until a person approves it and regenerates its pin. A pin does not show that the approved claim was true, so run the claim check as well ([Pinning tool definitions](https://rollingedition.com/securing-llm-applications-and-agents/s/pinning-tool-definitions)).
3. Load only safetensors weights, from a pinned commit. Check the SHA-256 and size of every file the loader reads, and refuse pickle-format files without unpickling them ([Model files](https://rollingedition.com/securing-llm-applications-and-agents/s/model-files)).
4. Pin every requirement with `==`, and record a hash for each line, so that an install fails on any changed byte. Until the hashes are in place, say that the versions are fixed, not that the bytes are ([Dependency pins](https://rollingedition.com/securing-llm-applications-and-agents/s/dependency-pins)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/dependency-pins). Its `exact == pins` line should read 60, and its `refused requirement lines` line should be zero.

## Red-team with an adaptive attacker

**When:** You need to know what a defence does when the attacker can read the reply and try again.

1. Before you read an adaptive rate, check that round 0 matches the fixed set for the same cases and defences. If it does not, the two numbers do not share a baseline ([An attacker that iterates](https://rollingedition.com/securing-llm-applications-and-agents/s/an-attacker-that-iterates)).
2. Fix the number of attacker turns before the run, and use the same number for every defence and every case. A budget chosen after the results can make any defence look stronger or weaker ([The budget](https://rollingedition.com/securing-llm-applications-and-agents/s/the-budget)).
3. Read each gap beside its round 0 count and case count. A zero gap with a zero-width interval means no case changed ([The gap to the fixed set](https://rollingedition.com/securing-llm-applications-and-agents/s/the-gap-to-the-fixed-set)).
4. In the same paragraph as any adaptive result, name the defences the loop did not attack ([What the result does not show](https://rollingedition.com/securing-llm-applications-and-agents/s/what-the-result-does-not-show)).
5. Before a garak module counts as covering a location, confirm at the pinned version that its detector scores the reply the assistant would send ([Mapping onto a toolkit](https://rollingedition.com/securing-llm-applications-and-agents/s/mapping-onto-a-toolkit)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/an-attacker-that-iterates). Its `round 0 mismatches against the fixed set` line should say none.

## Keep the defences from regressing

**When:** You changed a defence's code, wording, policy or recording, and need a gate that runs on every change.

1. Run the gate on every change, on dev only. Treat a failed check as a regression until someone has found its cause on dev. Do not rerun held-out to see whether a failing change passes, because that spends the split ([The gate](https://rollingedition.com/securing-llm-applications-and-agents/s/the-gate)).
2. Choose each threshold once, on dev, from the defended run and the baseline, and store it with the rule that produced it. Read each check against the interval's bound, never against the rate. A changed threshold is a new choice on dev, reviewed like any other change to the gate ([Choose thresholds once, from dev](https://rollingedition.com/securing-llm-applications-and-agents/s/thresholds-and-intervals)).
4. Log every outbound call, allowed or refused, every refused call, and every withheld result, with its host where the call has one. Log nothing else until an incident needs it ([Log what the defences decide](https://rollingedition.com/securing-llm-applications-and-agents/s/security-events)).
5. When an incident names a case, read every refusal logged for it before any code, then that case's lines under each configuration. Do not name a product as the cause, or reproduce a real incident's payload ([Answer an incident from the log](https://rollingedition.com/securing-llm-applications-and-agents/s/answering-an-incident)).
6. Print each risk ID with its list's year or date, and take IDs only from lists the book has checked ([Report in the standards' terms](https://rollingedition.com/securing-llm-applications-and-agents/s/reporting-in-the-standards-terms)).

**Check:** Run [the example](https://rollingedition.com/securing-llm-applications-and-agents/s/the-gate). Its `ceiling, stored` line should read 0.17, and the regressed run should FAIL the attack check.

**Pitfalls:**
- A gate on dev catches drift on the cases it was measured on. It does not show the defence works on new cases.

## Teach this book, when asked

**When:** only when the person you're working with explicitly asks to be taught, tutored or quizzed on this book, one of its chapters or a topic it covers ("teach me", "tutor me", "quiz me", "help me master"). A one-off question ("explain X", "what is X", "how do I use X") gets a normal answer from the procedures above, with no quiz. If you can't tell which they want, ask one short question: a quick answer, or should you teach it properly?

**The topics** are the book's chapters, in order:

1. [Attack an assistant, then measure a fix](https://rollingedition.com/securing-llm-applications-and-agents/attack-and-measure)
2. [Draw the assistant's threat model](https://rollingedition.com/securing-llm-applications-and-agents/threat-model)
3. [Build an attack set you can score in code](https://rollingedition.com/securing-llm-applications-and-agents/attack-set)
4. [Measure what prompt-level defences buy](https://rollingedition.com/securing-llm-applications-and-agents/prompt-defences)
5. [Detect injected text, and count the false alarms](https://rollingedition.com/securing-llm-applications-and-agents/injection-detectors)
6. [Enforce least privilege outside the model](https://rollingedition.com/securing-llm-applications-and-agents/least-privilege)
7. [Close the exfiltration channels](https://rollingedition.com/securing-llm-applications-and-agents/exfiltration-channels)
8. [Keep untrusted data out of the plan](https://rollingedition.com/securing-llm-applications-and-agents/isolation-by-design)
9. [Keep secrets and other people's records out of the context](https://rollingedition.com/securing-llm-applications-and-agents/secrets-and-records)
10. [Check what third parties hand the assistant](https://rollingedition.com/securing-llm-applications-and-agents/third-party-parts)
11. [Red-team the assistant with an adaptive attacker](https://rollingedition.com/securing-llm-applications-and-agents/adaptive-attacker)
12. [Keep the defences from regressing](https://rollingedition.com/securing-llm-applications-and-agents/regression-gates)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. The Rolling Edition MCP server's `get_contents` lists each chapter's sections, and `get_section` reads one, with its examples.

**Start**

1. Read each section, with `get_section`, before you ask about it. Judge every answer against the book: the section's text, the term's definition from `define` and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" below.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
Attack an assistant, then measure a fix    overall: █████░░░░░ 53%
------------------------------------------------------------------
The office and its assistant  ████████░░  4/5  alone
The attack that works         ██████░░░░  3/5  <- now
Scoring in code               ██░░░░░░░░  1/5
------------------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what it prints, or what would change if one line changed, then compare with the output its section shows.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/securing-llm-applications-and-agents/s/ followed by its ID.

**Levels are earned**

- Raise a level only after two or more separate checks, at least one of them recalled unprompted, not just after you told them the answer.
- A vague or partly right answer isn't right. Probe until you know. Never credit them with an insight they didn't state.
- Now and then, without warning, ask again about an earlier topic. If they miss, lower its level and go back to it.
- Level 5 needs an edge case or a hard question handled, and an explanation you'd trust them to teach from.
- No flattery: "Not quite: why would X happen if Y were true?" beats "Great try!"

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures above covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.2 and its code `Y3X2-HXT9`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/securing-llm-applications-and-agents/changes lists them.

## Reading in another language

When the person you're working with wants to read part of this book in another language, and the Rolling Edition MCP server is connected, first call its `get_section` with `language`: where Rolling Edition has its own translation of the book in that language (`get_contents` lists them), present each section as it comes, with the facts of its `translation`, and translate only the sections it lists as `untranslated`. Otherwise, translate it for them from its sections, read with the Rolling Edition MCP server's `get_section`. Translate the prose faithfully and in full: don't summarize, skip or add anything. Leave these exactly as they are: code, commands, output, file names, identifiers, inline code, package names and versions, numbers and URLs. Where practitioners who read the language usually keep a technical term in English, keep it, and give a short gloss in parentheses the first time, where that helps. Keep the headings and the structure: lists, tables, and the examples in their places. Begin by saying that it's your translation of *Securing LLM Applications and Agents*, Edition 2026.11.2, from Rolling Edition, licensed CC BY-NC 4.0, with the chapter's link, and keep each section's link from its citation block. For a long chapter, translate a section at a time and offer to go on after each. The Rolling Edition MCP server's `read_in_my_language` prompt asks for the same.
