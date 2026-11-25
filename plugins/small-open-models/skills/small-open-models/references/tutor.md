---
title: "Tutor"
book: "Small Open Models"
edition: "2026.11.16"
---

# Teaching *Small Open Models*

How to teach *Small Open Models*, Edition 2026.11.16, when someone asks to be taught, tutored or quizzed on it, as "Teach this book, when asked" in `SKILL.md` says, then every chapter's sections. The method is adapted from Jane Street's socratic-tutor skill, under MIT: `LICENSE.md` keeps its notice.

## How to teach it

**The topics** are the book's chapters, in order:

1. [Build a router for the bank's inbox that hands off when unsure](route-a-message.md)
2. [Measure the routing task before you choose a model](measure-the-routing-task.md)
3. [Choose a base model by counting what one message costs](choose-a-base-model.md)
4. [Prompt a small model and constrain its answers to the teams](prompt-and-constrain.md)
5. [Fine-tune a classification head with LoRA](fine-tune-with-lora.md)
6. [Distill a larger model's answers into a small one](distill-a-larger-model.md)
7. [Quantize the router and measure what changes](quantize-and-measure.md)
8. [Serve the router on a CPU, with the hand-off inside the route](serve-the-router-on-a-cpu.md)
9. [Version the router, watch its hand-offs and fall back to people](version-watch-and-fall-back.md)
10. [When a small model is the wrong choice](when-a-small-model-is-the-wrong-choice.md)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. "The book's sections", below, lists each chapter's sections, with the examples each one runs and the terms it defines.

**Start**

1. Read each section before you ask about it. Judge every answer against the book: the section's text, the term's definition in `glossary.md`, beside this file, and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" in `SKILL.md`.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
Build a router for the bank's inbox that hands off when unsure    overall: █████░░░░░ 53%
-----------------------------------------------------------------------------------------
What the router returns       ████████░░  4/5  alone
Ask a model for one team      ██████░░░░  3/5  <- now
Hand off the unsure messages  ██░░░░░░░░  1/5
-----------------------------------------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what its script in `scripts/` will print, or what will change if they change one line. Then have them run it, as `SKILL.md` shows, and compare with its `.out` file. Check the output they got, not their account of it.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/small-open-models/s/ followed by its ID.

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
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.16 and its code `ND69-JQ1D`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/small-open-models/changes lists them.

## The book's sections

Each chapter of Edition 2026.11.16 and its sections, in order, with the examples each section runs and the terms it defines. Each section links to its place in the chapter beside this file, and each script is in `scripts/`. Read a section before you ask about it.

### 1. Build a router for the bank's inbox that hands off when unsure

[The chapter](route-a-message.md). Defines: BANKING77, inbox, rough router, router, support staff, team.

- [What the router returns](route-a-message.md#what-the-router-returns). Defines: confidence, dev split, hand-off, hand-off flag, selective classification, token.
- [Ask a model for one team](route-a-message.md#ask-a-model-for-one-team). Runs `scripts/record-your-own-answers.py`. Defines: answer log-probability, greedy decoding, test_1001.
- [Hand off the unsure messages](route-a-message.md#hand-off-the-unsure-messages). Runs `scripts/route-one-message.py`. Defines: hand-off rule, placeholder threshold.
- [Score the router on a fixed sample](route-a-message.md#score-the-router-on-a-fixed-sample). Runs `scripts/route-recorded-answers.py`. Defines: accuracy, accuracy on messages not handed off, hand-off rate, test_40.
- [Show what a small model does first](route-a-message.md#show-what-a-small-model-does-first). Runs `scripts/unconstrained-first-try.py`. Defines: SmolLM2-135M-Instruct.
- [Where a rough router breaks](route-a-message.md#where-a-rough-router-breaks).

### 2. Measure the routing task before you choose a model

[The chapter](measure-the-routing-task.md). Defines: stand-in.

- [The data and its licence](measure-the-routing-task.md#the-data-and-its-licence).
- [Dev, test and fixed samples](measure-the-routing-task.md#dev-test-and-fixed-samples). Runs `scripts/count-the-splits.py`, `scripts/figure-train-rows-per-team.py`. Defines: test split, test_200.
- [Three measures, each with its denominator](measure-the-routing-task.md#three-measures-each-with-its-denominator). Defines: threshold.
- [The baseline from recorded answers](measure-the-routing-task.md#the-baseline-from-recorded-answers). Runs `scripts/baseline-measures.py`, `scripts/figure-baseline-handoff-tradeoff.py`. Defines: baseline, recording, recording manifest.
- [Where the labels collide](measure-the-routing-task.md#where-the-labels-collide). Runs `scripts/confusions-in-the-baseline.py`. Defines: error.

### 3. Choose a base model by counting what one message costs

[The chapter](choose-a-base-model.md).

- [Which candidates we keep](choose-a-base-model.md#the-candidates-and-what-we-keep). Defines: base model, SmolLM2.
- [Load each model at its pinned revision](choose-a-base-model.md#load-each-model-at-its-pinned-revision). Runs `scripts/load-both-models-offline.py`. Defines: layer, parameter, pinned revision, pins file.
- [Measure what one message costs](choose-a-base-model.md#measure-what-one-message-costs). Runs `scripts/count-forward-passes.py`, `scripts/count-prompt-tokens.py`. Defines: classifier, forward pass, generative model, median, router prompt, tokenizer.
- [Why 135M is the core](choose-a-base-model.md#why-135m-is-the-core).
- [What a bigger model would need](choose-a-base-model.md#what-a-bigger-model-would-need).

### 4. Prompt a small model and constrain its answers to the teams

[The chapter](prompt-and-constrain.md).

- [The prompt, settled before any recording](prompt-and-constrain.md#the-prompt-settled-before-any-recording). Runs `scripts/constrained-decode-135m-chat.py`. Defines: chat form, raw form.
- [Why free text fails](prompt-and-constrain.md#why-free-text-fails). Defines: free decoding.
- [A token trie allows only team names](prompt-and-constrain.md#a-token-trie-allows-only-team-names). Runs `scripts/constrained-decode-135m.py`. Defines: end-of-answer token, prefix_allowed_tokens_fn, router_lib, trie.
- [Decode greedily so every count repeats](prompt-and-constrain.md#ties-and-determinism).
- [Measure the constrained answers](prompt-and-constrain.md#measure-the-constrained-answers). Runs `scripts/constrained-decode-360m.py`, `scripts/prompting-on-test-200.py`, `scripts/figure-answers-pile-on-one-team.py`.
- [Why a prior is not a router](prompt-and-constrain.md#why-the-prior-wins). Runs `scripts/label-scoring-prior.py`. Defines: label scoring, log-probability, prior, top team.
- [What this chapter decided](prompt-and-constrain.md#what-this-chapter-decided).

### 5. Fine-tune a classification head with LoRA

[The chapter](fine-tune-with-lora.md).

- [A head that scores the teams](fine-tune-with-lora.md#a-head-that-scores-the-teams). Defines: classification head, confidence, softmax.
- [Adapters train a small part of the model](fine-tune-with-lora.md#adapters-train-a-small-part-of-the-model). Defines: adapter, full fine-tuning, LoRA, LoRA rank, lora_alpha.
- [Thirty steps are not enough](fine-tune-with-lora.md#thirty-steps-are-not-enough). Runs `scripts/lora-thirty-steps.py`. Defines: uniform guess.
- [Train on the training rows, never on the test rows](fine-tune-with-lora.md#train-on-the-training-rows-never-on-the-test-rows).
- [Use the recorded adapter](fine-tune-with-lora.md#use-the-recorded-adapter). Runs `scripts/figure-lora-loss-curve.py`, `scripts/lora-recorded-adapter.py`, `scripts/compare-with-standin.py`. Defines: banking77-lora-v1.
- [Choose the threshold on dev](fine-tune-with-lora.md#choose-the-threshold-on-dev). Runs `scripts/choose-threshold-on-dev.py`, `scripts/calibration-bands-on-dev.py`. Defines: poorly calibrated.

### 6. Distill a larger model's answers into a small one

[The chapter](distill-a-larger-model.md).

- [What distillation copies](distill-a-larger-model.md#what-distillation-copies). Defines: distillation, greedy answer, soft targets.
- [A teacher whose terms allow it](distill-a-larger-model.md#a-teacher-whose-terms-allow-it). Defines: open-weights licence.
- [Label training rows with the teacher](distill-a-larger-model.md#label-training-rows-with-the-teacher). Runs `scripts/teacher-agreement.py`.
- [Train the student on the teacher's labels](distill-a-larger-model.md#train-the-student-on-the-teachers-labels). Defines: banking77-distilled-v1, teacher's recording.
- [Measure agreement, not only accuracy](distill-a-larger-model.md#measure-agreement-not-only-accuracy). Runs `scripts/student-recorded-adapter.py`, `scripts/student-vs-gold-control.py`. Defines: agreement with the teacher, banking77-gold-1000-v1.
- [When the teacher is wrong](distill-a-larger-model.md#when-the-teacher-is-wrong). Runs `scripts/figure-teacher-agreement-by-team.py`. Defines: teacher's agreement with gold.

### 7. Quantize the router and measure what changes

[The chapter](quantize-and-measure.md).

- [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers). Runs `scripts/int8-layers-and-bytes.py`. Defines: int8 copy, Int8WeightOnlyConfig, linear layer, merging, per-row scale, quantization, quantization scale.
- [Count the predictions that change](quantize-and-measure.md#count-the-predictions-that-change). Runs `scripts/int8-changed-predictions.py`. Defines: changed-prediction count.
- [Keep the score head in float32](quantize-and-measure.md#keep-the-score-head-in-float32).
- [Measure speed in a recording](quantize-and-measure.md#measure-speed-in-a-recording).
- [Decide with the hand-off in view](quantize-and-measure.md#decide-with-the-hand-off-in-view).

### 8. Serve the router on a CPU, with the hand-off inside the route

[The chapter](serve-the-router-on-a-cpu.md).

- [One route that returns the hand-off](serve-the-router-on-a-cpu.md#one-route-that-returns-the-hand-off). Runs `scripts/serve-route-testclient.py`. Defines: route.
- [Load the model once at startup](serve-the-router-on-a-cpu.md#load-the-model-once-at-startup). Defines: intra-op threads.
- [Know what the route cannot score](serve-the-router-on-a-cpu.md#reject-what-the-route-cannot-score). Runs `scripts/truncation-count.py`. Defines: truncation.
- [Test the route in the same process](serve-the-router-on-a-cpu.md#test-the-route-without-a-socket).
- [What goes wrong in production](serve-the-router-on-a-cpu.md#what-goes-wrong-in-production). Defines: adapter version, spawned worker.

### 9. Version the router, watch its hand-offs and fall back to people

[The chapter](version-watch-and-fall-back.md).

- [Name the router by its parts](version-watch-and-fall-back.md#name-the-router-by-its-parts). Runs `scripts/adapter-manifest-check.py`.
- [Check the adapter's files against its manifest](version-watch-and-fall-back.md#check-the-adapters-files-against-its-manifest).
- [Watch the hand-off rate](version-watch-and-fall-back.md#watch-the-hand-off-rate). Runs `scripts/handoff-windows.py`. Defines: dev baseline, drift, hand-off watch.
- [Sample handed-off messages for people](version-watch-and-fall-back.md#sample-handed-off-messages-for-people). Defines: kept message, kept-message sample, sample of handed-off messages.
- [Fall back to a person](version-watch-and-fall-back.md#fall-back-to-a-person). Runs `scripts/fallback-to-larger-model.py`. Defines: suggestion.
- [Retrain on a trigger](version-watch-and-fall-back.md#retrain-on-a-trigger). Runs `scripts/retrain-trigger.py`.
- [What goes wrong in production](version-watch-and-fall-back.md#failures-in-production).
- [The decisions this chapter made](version-watch-and-fall-back.md#the-decisions-this-chapter-made). Defines: version check.

### 10. When a small model is the wrong choice

[The chapter](when-a-small-model-is-the-wrong-choice.md).

- [Where the small model still loses](when-a-small-model-is-the-wrong-choice.md#where-the-small-model-still-loses). Runs `scripts/router-on-test-1001.py`, `scripts/where-the-router-still-loses.py`.
- [Count the bill and the machine](when-a-small-model-is-the-wrong-choice.md#count-the-bill-and-the-machine). Runs `scripts/cost-ratio-from-recording.py`, `scripts/monthly-bill-from-labelled-inputs.py`. Defines: hosted bill, machine bill, machine capacity, utilisation.
- [Keep the data inside the building](when-a-small-model-is-the-wrong-choice.md#keep-the-data-inside-the-building).
- [Choose with a table](when-a-small-model-is-the-wrong-choice.md#choose-with-a-table).
- [Know the break-even](when-a-small-model-is-the-wrong-choice.md#know-the-break-even). Runs `scripts/break-even-from-recorded-ratio.py`, `scripts/figure-break-even-bills.py`. Defines: break-even, machine cost per message.
- [The decisions this book made for the inbox](when-a-small-model-is-the-wrong-choice.md#the-decisions-this-book-made-for-the-inbox).
