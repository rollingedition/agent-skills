---
name: evaluating-llm-applications
description: "Use when evaluating an LLM application, in Python, with examples built on a documentation assistant: measuring a baseline with an interval, coding reply failures, test sets and public benchmarks, code checks, LLM judges with rubrics, calibrating a judge and correcting its pass rate, judge position and length bias, paired comparisons and sample size, grounding and version-correctness, over-refusal and missed refusals, and CI gates. Use it to decide whether a change made an assistant better, and how sure you can be. When someone explicitly asks to be taught, tutored or quizzed on what this book covers (\"teach me\", \"tutor me\", \"quiz me\"), it also tutors them, one question at a time. Not for a one-off \"explain X\" or \"what is X\"."
license: CC-BY-NC-4.0 AND MIT
compatibility: "Python 3.12.15 and the pinned packages in scripts/requirements.txt; the scripts run offline."
metadata:
  publisher: "Rolling Edition"
  book: "Evaluating LLM Applications"
  edition: "2026.11.7"
  verified: "2026-11-22"
  examples: "58 of 58 examples pass"
  edition-code: "WCKB-Y7EK"
  source: "https://rollingedition.com/evaluating-llm-applications"
---

# Evaluating LLM Applications

This agent skill is *Evaluating LLM Applications*, Edition 2026.11.7, from Rolling Edition. Examples passed Nov 22, 2026: 58 of 58 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, `references/` holds each chapter, and `references/glossary.md` the terms the book defines, and `scripts/` holds the examples as the edition ran them.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section in `references/` before you act on it, and adapt it to the project in front of you.
- **Check against the book.** Each example in `scripts/` has its expected output beside it (`.out`), at the versions in `scripts/requirements.txt`. If the project uses other versions, say so before relying on a step.
- **Use the book's terms as it defines them.** `references/glossary.md` has each term this book defines, in the book's own sentence, with the section that defines it and the version it's true for: where the task uses one, it means that, and cite its section.
- **Is this copy current?** Call `check_code` with `WCKB-Y7EK` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/evaluating-llm-applications
- **Credit the book** when you quote it or reuse its code: Evaluating LLM Applications, Edition 2026.11.7, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

To run an example as the book does, with [uv](https://docs.astral.sh/uv/):

```sh
uv venv --python 3.12.15
uv pip install -r scripts/requirements.txt --index-strategy unsafe-best-match
cd scripts && uv run --no-project python list-the-docs.py
```

## Measure a baseline with an interval

**When:** you need a pass rate for an assistant over a fixed set of questions.

1. Write each item, with its version, kind and expected answer, before running the assistant. Label items written to catch one mistake ([The twenty items](references/measure-before-you-change.md#the-twenty-items)).
2. Record the sections each reply was given, and check retrieval before the answer ([Retrieve, then answer](references/measure-before-you-change.md#retrieve-then-answer)).
3. Score the same recorded replies for every comparison. Record again only when the model, prompt or sections change ([Replay the answers](references/measure-before-you-change.md#replay-the-answers)).
4. Run the citation and decline checks on every reply. Keep a fixture that cites outside its prompt, and check that the check fires on it ([Citations in code](references/measure-before-you-change.md#citations-in-code), [Declines in code](references/measure-before-you-change.md#declines-in-code)).
5. Give the judge a written reference for every item, and read its FAIL verdicts as closely as its PASS verdicts. Agreement with your own labels is not calibration ([One judge](references/measure-before-you-change.md#one-judge)).
6. Report each pass rate with its denominator, interval and rate per kind. Treat a kind with few items as a note ([A pass rate and its interval](references/measure-before-you-change.md#a-pass-rate-and-its-interval)).
7. For two prompts, score the same items, report the paired difference with its interval, and call one better only when the whole interval lies above zero ([Two prompts](references/measure-before-you-change.md#two-prompts)).

**Check:** run [the example](scripts/check-citations.py). Every rate prints with its counts.

**Pitfalls:** about twenty items can find broken answers but cannot rank two prompts ([What twenty questions can't show](references/measure-before-you-change.md#what-twenty-questions-cant-show)).

## Read replies and code their failure modes

**When:** a variant fails and you need to know how.

1. Read replies from every variant, grouped by kind, before counting ([What the replies look like](references/read-the-outputs.md#what-the-replies-look-like)).
2. Give each reply one note and one failure mode, and print one labelled line per count ([Coding the failures](references/read-the-outputs.md#coding-the-failures)).
3. Count a decline by what the reply does, not by whether the exact phrase stands alone. Count over-declining apart from wrong answers ([Over-declining](references/read-the-outputs.md#over-declining)).
4. Check each reply's version twice: its citations and its claim must match the asked version's reference ([Wrong-version answers](references/read-the-outputs.md#wrong-version-answers)).
5. Require a decline on every unanswerable item, and read every answer to one against its cited section ([Missed refusals](references/read-the-outputs.md#missed-refusals)).
6. Only then write one check per mode. A check built from expected failures misses the rest ([From a failure to a check](references/read-the-outputs.md#from-a-failure-to-a-check)).

**Check:** run [the example](scripts/tally-failure-modes.py). Every count matches a labelled line.

**Pitfalls:** a count shows that a variant fails; only the replies show how ([What the replies look like](references/read-the-outputs.md#what-the-replies-look-like)). Counts coded by one coder carry no agreement figure ([Coding the failures](references/read-the-outputs.md#coding-the-failures)).

## Build a test set and read public benchmarks

**When:** you build the set an assistant is measured on, or quote a public score.

1. Write the set before changing anything you will measure with it, and keep it under version control ([What a test set is for](references/build-the-test-set.md#what-a-test-set-is-for)).
2. Treat any problem the schema check prints as a failure, and read a sample of items by hand ([The item schema](references/build-the-test-set.md#the-item-schema)).
3. Count coverage for each behaviour, and treat a behaviour with few items as untested ([Kinds and coverage](references/build-the-test-set.md#kinds-and-coverage)).
4. Plant an item only for a trap you can name, and check the cited sections confirm its wrong reply is wrong ([Planted items](references/build-the-test-set.md#planted-items)).
5. Read each synthetic item against real phrasing before it counts ([Synthetic items and what they hide](references/build-the-test-set.md#synthetic-items)).
6. Ask each question as a user would. For a version-dependent behaviour, name the version and write its twin ([Kinds and coverage](references/build-the-test-set.md#kinds-and-coverage)).
7. Split dev from held-out. Correct a question only when its reference or sections are wrong, never because the assistant fails it ([Dev and held-out](references/build-the-test-set.md#dev-and-held-out)).
8. Quote a public score only beside its sample, model build, prompt, parser, reply cap and interval, never beside a published number ([Public benchmarks](references/build-the-test-set.md#public-benchmarks)).
9. Count the replies with no final line before you quote a score ([GSM8K](references/build-the-test-set.md#gsm8k)).
10. Print where the correct option sits, and each position's reply share beside the chance share. If it is always first, shuffle the options with a fixed seed and compare the runs with a paired interval ([TruthfulQA](references/build-the-test-set.md#truthfulqa)).
11. Name contamination beside every public score, never as the assistant's ability ([Contamination](references/build-the-test-set.md#contamination)).

**Check:** run [the schema example](scripts/check-item-schema.py). The check prints zero problems.

**Pitfalls:** a public benchmark that tests none of your assistant's tasks checks your harness ([GSM8K](references/build-the-test-set.md#gsm8k)). A reply cut off at the token cap is scored by its last number, often an intermediate one, so the score partly measures the cap ([GSM8K](references/build-the-test-set.md#gsm8k)).

## Write code checks

**When:** a failure can be read from the reply, the item or the run: a format, a citation ID, a decline.

1. Write a code check only when the reply, item or run holds the fact it needs. Send claim-level failures to a judge ([What a code check can see](references/checks-in-code.md#what-a-code-check-can-see)).
2. Run format and order checks on every reply before a judge reads it, and report counts per split ([Format checks](references/checks-in-code.md#format-checks)).
3. Count a citation as supported only when its ID is on the item's list. Read each unlisted citation against its section before you call it a problem ([Support](references/checks-in-code.md#citation-support)).
4. Whether a listed section supports its sentence is a judgement the ID check cannot make. Read it, or use the answer-level faithfulness judge ([Faithfulness](references/grounded-answers.md#faithfulness)).
5. Use an exact match where the expected text is fixed. Use a fuzzy ratio only to order replies for reading ([Exact and fuzzy match](references/checks-in-code.md#exact-and-fuzzy)).
6. Do not use BLEU or ROUGE as the pass mark for an answer with one right form ([Where BLEU and ROUGE mislead](references/checks-in-code.md#where-bleu-rouge-mislead)).
7. Count both decline errors per split ([Declines in code](references/checks-in-code.md#decline-checks)).
8. Report wrong-version and missing outcomes as their own rates, and never let a zero stand for a right answer ([Existence and version](references/checks-in-code.md#citation-existence)).

**Check:** run [the example](scripts/format-problems-baseline.py). Each check fires on its fixture.

**Pitfalls:** when a count rises, read the replies behind it before you change the check ([Format checks](references/checks-in-code.md#format-checks)).

## Write a judge rubric and parse verdicts

**When:** a claim cannot be checked in code, and a judge's verdict must be countable.

1. Write the rubric as text a team can read. Hash it with the run it produces, and name it by its first line ([What a judge is asked](references/a-judge-with-a-rubric.md#what-a-judge-is-asked)).
2. Use a reference whenever the set has one, with a rule for an empty reference. Name what the judge must ignore, such as length or tone ([Reference-guided or reference-free](references/a-judge-with-a-rubric.md#reference-guided)).
3. Use pass and fail for correctness. Use a scale only when each step leads to an action and human ratings exist at each step ([Pass, fail, or a scale](references/a-judge-with-a-rubric.md#pass-fail-or-scale)).
4. Parse the verdict from the first non-empty line only. A reply that does not open with exactly PASS or FAIL has an unreadable verdict, which is not a FAIL. Print it; stop the run or leave it out of the rate, and say which, with the count beside the rate ([Verdict first](references/a-judge-with-a-rubric.md#verdict-first)).
5. Check the parser on the judge's real replies, not only your sample ([Verdict first](references/a-judge-with-a-rubric.md#verdict-first)).
6. Tune wording on dev only; a changed wording is a new rubric with its own hash ([Tuning the wording](references/a-judge-with-a-rubric.md#tuning-the-wording)).

**Check:** run [the example](scripts/parse-verdicts.py). The parser gives PASS, FAIL or an unreadable verdict for every reply.

**Pitfalls:** a rubric that parses on a sample can still lose verdicts to a format it did not ask for ([Verdict first](references/a-judge-with-a-rubric.md#verdict-first)).

## Calibrate a judge and correct a pass rate

**When:** a judge's verdicts need checking, or a corrected rate built on them.

1. Label a calibration set for the question the judge answers, and write the score-to-pass rule before you look at results. Keep tuning and reported splits apart ([Human ratings](references/calibrate-the-judge.md#human-ratings)).
2. Run the judge on each calibration row with the same rubric, and count its disagreements with the human label before any rate ([Agreement and kappa](references/calibrate-the-judge.md#agreement-and-kappa)).
3. Report agreement beside kappa, and read kappa against its chance figure ([Agreement and kappa](references/calibrate-the-judge.md#agreement-and-kappa)).
4. Compute TPR and TNR, each with its counts, and say which way the judge errs ([TPR and TNR](references/calibrate-the-judge.md#tpr-and-tnr)).
5. Correct a pass rate only with TPR and TNR from dev alone. Refuse when TPR + TNR − 1 is below a floor you set in code before the run; the book uses 0.1 ([Correcting a pass rate](references/calibrate-the-judge.md#correcting-a-pass-rate)).
6. Give the corrected rate with its bootstrap interval, the share of resamples at the cap, and the one-row moves ([How much one row moves the corrected rate](references/calibrate-the-judge.md#how-much-one-row-moves-it)).
7. Write the transfer assumption in the same paragraph: until human labels on the answers exist, the corrected rate holds only if it does ([The transfer assumption](references/calibrate-the-judge.md#transfer-assumption)).

**Check:** run [the TPR example](scripts/tpr-tnr.py) and [the correction example](scripts/corrected-pass-rate.py). TPR and TNR print with counts beside the corrected rate.

**Pitfalls:** kappa depends on the label mix ([Agreement and kappa](references/calibrate-the-judge.md#agreement-and-kappa)). Checking the arithmetic does not test transfer ([The transfer assumption](references/calibrate-the-judge.md#transfer-assumption)). An unreadable verdict is printed and left out of the corrected rate, never counted as FAIL ([Correcting a pass rate](references/calibrate-the-judge.md#correcting-a-pass-rate)).

## Test a judge for position and length bias

**When:** the judge compares two replies, or its verdicts may track length.

1. Judge every pair in both orders, and map each verdict back to its reply before you count ([Position](references/when-the-judge-stops-being-reliable.md#position)).
2. Count a pair whose verdict changes with the order as no verdict for either reply. Report the order-change rate beside the verdict counts ([Position](references/when-the-judge-stops-being-reliable.md#position)).
3. When changes lean one way, say which way, how many, and with what interval. Do not assume another judge leans alike ([Position](references/when-the-judge-stops-being-reliable.md#position)).
4. For length, compare the longest and shortest bands, with the gap's interval and each band's count. If it includes zero, say no difference was detected ([Length](references/when-the-judge-stops-being-reliable.md#length)).
5. To test whether length matters, build pairs where only the length changes ([Length](references/when-the-judge-stops-being-reliable.md#length)).
6. If the judge is the model whose answers it grades, report that beside every rate. Never claim self-preference was tested, and do not use that judge to compare its own model with another ([Self-preference](references/when-the-judge-stops-being-reliable.md#self-preference)).
7. Stop trusting a verdict, and say so, when it changes with the order or cannot be read ([Where to stop](references/when-the-judge-stops-being-reliable.md#where-to-stop)).

**Check:** run [the position example](scripts/position-flips.py) and [the length example](scripts/length-and-verdicts.py). The order-change rate prints beside the verdict counts.

**Pitfalls:** a few length bands cannot name a length effect, or its absence ([Length](references/when-the-judge-stops-being-reliable.md#length)). On the judge's own model, a gap between answers is not evidence about self-preference ([Self-preference](references/when-the-judge-stops-being-reliable.md#self-preference)). Unreadable verdicts are left out, never counted as FAILs ([Where to stop](references/when-the-judge-stops-being-reliable.md#where-to-stop)).

## Compare variants and size a set

**When:** you want to know whether one variant beats another, or how many items a comparison needs.

1. Run the variance set at the temperature you ship, and read the flip rate beside the mean pass rate ([Variance within one item](references/intervals-and-sample-size.md#variance-within-one-item)).
2. Resample items, never runs within an item. Fix the resample count and seed in the code ([The bootstrap over items](references/intervals-and-sample-size.md#bootstrap-over-items)).
3. Compare the variants on the same items, paired, with the difference, its interval and n. Call one better only when the whole interval sits above zero, and worse only when it sits below ([Paired comparisons](references/intervals-and-sample-size.md#paired-comparisons)).
4. Fix the variants, level and reading rule before opening held-out, and run each comparison once ([Held-out, once](references/intervals-and-sample-size.md#held-out-once)).
5. Count the comparisons on one metric before running them, and set each interval's level from that count ([Many comparisons](references/intervals-and-sample-size.md#many-comparisons)).
6. To size a set, estimate on dev how often the variants disagree, state that share as the assumption, and give the items needed with a range ([How many questions a difference needs](references/intervals-and-sample-size.md#how-many-questions)).
7. If the set is smaller, say it cannot detect a difference that size, and do not read no difference as a ruling against the change ([How many questions a difference needs](references/intervals-and-sample-size.md#how-many-questions)).

**Check:** run [the comparison example](scripts/compare-two-prompts.py) and [the sample-size example](scripts/sample-size.py). Each interval prints with its n and level.

**Pitfalls:** the main items-needed estimate comes from item-level disagreement between the variants, so it is an order of magnitude, not a count. The floor from sampling noise alone is only a lower bound, and it holds only for a comparison that samples its replies ([How many questions a difference needs](references/intervals-and-sample-size.md#how-many-questions)).

## Check grounding and version-correctness

**When:** answers must cite the docs, and must match the docs of the version asked.

1. Give each check its own count over its own denominator. A pass starts the reading; it does not end it ([What grounded means here](references/grounded-answers.md#what-grounded-means)).
2. Read the item rate and citation rate together, and read each unlisted citation ([Citation accuracy](references/grounded-answers.md#citation-accuracy)).
3. Label every faithfulness rate "uncalibrated", and read the first unfaithful items before you trust it ([Faithfulness](references/grounded-answers.md#faithfulness)).
4. Read each citation's ID against its answer's version, and keep version-dependent items in their own count ([Version-correctness](references/grounded-answers.md#version-correctness)).
5. Treat retrieval as a gate on passes and a lead on fails. A pass without the supporting section needs an explanation ([The retrieval step](references/grounded-answers.md#the-retrieval-step)).
6. Before calling a reply grounded, read its citation, claims, version and retrieval together ([Outcome and path](references/grounded-answers.md#outcome-and-path)).

**Check:** run [the faithfulness example](scripts/faithfulness-rate.py) and [the version example](scripts/version-correct-answers.py).

**Pitfalls:** a zero from the citation check means no flagged ID, not no wrong-version citation ([Version-correctness](references/grounded-answers.md#version-correctness)). When every item passes, or none does, the bootstrap interval is degenerate: give the exact bound ([Faithfulness](references/grounded-answers.md#faithfulness)).

## Measure both decline errors

**When:** the assistant sometimes refuses answerable questions, or answers ones the docs do not cover.

1. Report the false refusal rate and the false answer rate apart, each over its own denominator. Leave version-dependent and ambiguous items out of both ([Two errors, both counted](references/declining-when-the-docs-dont-say.md#two-errors)).
2. Count a decline by what the reply does. Exact-match code counts a differently worded refusal as an answer, a false answer on an unanswerable item. Fix the decline sentence in the prompt, and read replies that refuse in other words before you trust either rate ([Two errors, both counted](references/declining-when-the-docs-dont-say.md#two-errors)).
3. Read each dev false refusal by hand before you change the prompt; one may expose a gap in the docs ([What the baseline does](references/declining-when-the-docs-dont-say.md#what-the-baseline-does)).
4. Compare variants on dev, on the same items. Report a paired interval only where an example prints one, else report counts and draw no conclusion. Run held-out once to confirm the choice ([What the baseline does](references/declining-when-the-docs-dont-say.md#what-the-baseline-does)).
5. If a guard declines on a score, build its scores from the index that made the replies, and check the match before you read any rate ([A guard on recorded replies](references/declining-when-the-docs-dont-say.md#a-guard)).
6. Before tuning a threshold, write each error's cost in the team's terms, before anyone reads the sweep ([Too many refusals and too few](references/declining-when-the-docs-dont-say.md#too-many-and-too-few)).
7. Keep a guard only when its held-out run changes replies as its dev sweep promised ([What a reader should accept](references/declining-when-the-docs-dont-say.md#what-to-accept)).

**Check:** run [the decline example](scripts/decline-rates.py), [the threshold sweep](scripts/tune-guard-dev.py) and [the held-out example](scripts/guard-held-out.py). Each rate prints with its count.

**Pitfalls:** the trap is exact-match decline detection, which counts a differently worded decline as an answer, so it hides over-declines ([Over-declining](references/read-the-outputs.md#over-declining)). A rate can hide the few items that matter ([Two errors, both counted](references/declining-when-the-docs-dont-say.md#two-errors)). A zero-event interval is degenerate, never a finding ([What a reader should accept](references/declining-when-the-docs-dont-say.md#what-to-accept), [Faithfulness](references/grounded-answers.md#faithfulness)).

## Gate a change in CI and handle flaky items

**When:** a change must pass an evaluation before it merges, or some items flip between samples.

1. Compute the paired difference in pass rate between candidate and baseline, over the same items, with its bootstrapped interval. Drop an item whose baseline verdict was unreadable from both runs ([A gate that respects the interval](references/keep-the-evaluation-running.md#a-gate-that-respects-the-interval)).
2. Fail only when the upper bound of that interval lies below minus the threshold. Set the threshold before the run, and say it is a team choice ([A gate that respects the interval](references/keep-the-evaluation-running.md#a-gate-that-respects-the-interval)).
3. Decide a release on held-out, run once per comparison, not on dev after each change ([A gate that respects the interval](references/keep-the-evaluation-running.md#a-gate-that-respects-the-interval)).
4. In CI, run the gate on per-item values. A job that fails to run is a failed gate ([A gate that respects the interval](references/keep-the-evaluation-running.md#a-gate-that-respects-the-interval)).
5. Run the evaluation's own tests before any run that reads a number. Treat exit code 5 as a failure, not a pass ([The evaluation's own tests](references/keep-the-evaluation-running.md#the-evaluations-own-tests)).
6. Flag an item whose verdicts differ across samples, print its count, and never edit or delete it ([Flag flaky items, never edit them](references/keep-the-evaluation-running.md#flaky-cases)).
7. Report the flip rate with its denominator; a low rate holds for this assistant, judge and set only ([Flag flaky items, never edit them](references/keep-the-evaluation-running.md#flaky-cases)).
8. When you map onto a framework, name its version and documentation date ([Running it as a framework task](references/keep-the-evaluation-running.md#running-it-as-a-framework-task)).
9. For live traffic, assign variants at random and record each one beside its vote ([Variants on traffic](references/keep-the-evaluation-running.md#variants-on-traffic)).

**Check:** run [the gate example](scripts/gate-real-drop.py), [the own-tests example](scripts/own-tests-run.py) and [the flaky-items example](scripts/flaky-items.py). The gate prints its interval and n, and the tests exit with code 0.

**Pitfalls:** the gate fails only when the upper bound of the difference lies below minus the threshold; a point estimate below it is not a fail. With m metrics, take each interval at 1 − 0.05/m ([A gate that respects the interval](references/keep-the-evaluation-running.md#a-gate-that-respects-the-interval)). A pass with a wide interval is weak. Do not use a judge on its own model to compare two models ([Self-preference](references/when-the-judge-stops-being-reliable.md#self-preference)). An unreadable sample is not a fail: flag or set aside the item ([Flag flaky items, never edit them](references/keep-the-evaluation-running.md#flaky-cases)). A vote table is not a set of labels ([Variants on traffic](references/keep-the-evaluation-running.md#variants-on-traffic)).

## Teach this book, when asked

**When:** only when the person you're working with explicitly asks to be taught, tutored or quizzed on this book, one of its chapters or a topic it covers ("teach me", "tutor me", "quiz me", "help me master"). A one-off question ("explain X", "what is X", "how do I use X") gets a normal answer from the procedures above, with no quiz. If you can't tell which they want, ask one short question: a quick answer, or should you teach it properly?

When they do, read `references/tutor.md` first and follow it: how to teach the book a question at a time, then every chapter's sections with their examples and terms.

## Reading in another language

When the person you're working with wants to read part of this book in another language, and the Rolling Edition MCP server is connected, first call its `get_section` with `language`: where Rolling Edition has its own translation of the book in that language (`get_contents` lists them), present each section as it comes, with the facts of its `translation`, and translate only the sections it lists as `untranslated`. Otherwise, translate it for them from the chapter in `references/`. Translate the prose faithfully and in full: don't summarize, skip or add anything. Leave these exactly as they are: code, commands, output, file names, identifiers, inline code, package names and versions, numbers and URLs. Where practitioners who read the language usually keep a technical term in English, keep it, and give a short gloss in parentheses the first time, where that helps. Keep the headings and the structure: lists, tables, and the examples in their places. Begin by saying that it's your translation of *Evaluating LLM Applications*, Edition 2026.11.7, from Rolling Edition, licensed CC BY-NC 4.0, with the chapter's link, `canonical` in its front matter, and keep each section's link, https://rollingedition.com/evaluating-llm-applications/s/ followed by the ID in its heading's `{#…}`. For a long chapter, translate a section at a time and offer to go on after each. The Rolling Edition MCP server's `read_in_my_language` prompt asks for the same.
