---
title: "Glossary"
book: "Evaluating LLM Applications"
edition: "2026.11.8"
canonical: "https://rollingedition.com/evaluating-llm-applications/glossary"
---

# Glossary of *Evaluating LLM Applications*

The 124 terms this book defines, as Edition 2026.11.8 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/evaluating-llm-applications/glossary

## agreement

Agreement is the share of rows on which the judge and the human give the same verdict.

- The same as: https://rollingedition.com/concepts/search-and-recommendation/observed-agreement
- Defined in: [Agreement and kappa](calibrate-the-judge.md#agreement-and-kappa)
- Address: https://rollingedition.com/concepts/llm-evaluation/agreement

## ambiguous item

Ambiguous items could mean two things, and their reference answer covers both readings.

- A kind of: item
- Defined in: [The twenty items](measure-before-you-change.md#the-twenty-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/ambiguous-item

## ambiguous target

ambiguous-target: a pronoun or a phrase such as "the file" has no clear referent without the sections.

- Also: ambiguous-target
- Part of: planted item
- Defined in: [Planted items and their traps](build-the-test-set.md#planted-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/ambiguous-target

## answer judge

The answer judge checks a reply about sablefile against the written reference answer for its question.

- Defined in: [What a judge is asked](a-judge-with-a-rubric.md#what-a-judge-is-asked)
- Address: https://rollingedition.com/concepts/llm-evaluation/answer-judge

## answerable item

Answerable items have their answer on the page.

- A kind of: item
- Defined in: [The twenty items](measure-before-you-change.md#the-twenty-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/answerable-item

## answered-declined-expected

answered-declined-expected is an answer to an item that has to be declined.

- Part of: format check
- Defined in: [Format checks](checks-in-code.md#format-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/answered-declined-expected

## autojunk

For sequences of 200 items or more, the documentation treats an item as junk when its repeats make up more than one per cent of the sequence, unless autojunk is turned off.

- Defined in: [Exact and fuzzy match](checks-in-code.md#exact-and-fuzzy)
- Address: https://rollingedition.com/concepts/artificial-intelligence/autojunk

## baseline

The baseline is the setup chapter 1 measured.

- Close to: https://rollingedition.com/concepts/artificial-intelligence/baseline
- Defined in: [What the replies look like](read-the-outputs.md#what-the-replies-look-like)
- Address: https://rollingedition.com/concepts/llm-evaluation/baseline

## BLEU

Papineni and colleagues proposed BLEU in 2002 as a quick and inexpensive way to score machine translation, from modified n-gram precision and a brevity penalty

- Contrasts with: ROUGE-N
- Defined in: [Where BLEU and ROUGE mislead](checks-in-code.md#where-bleu-rouge-mislead)
- Address: https://rollingedition.com/concepts/artificial-intelligence/bleu

## BM25

The index is built with BM25, which scores each section by the words it shares with the question, giving rarer words more weight and long sections less.

- True for: bm25s 0.3.16
- Implemented by: bm25s 0.3.16
- The same as: https://rollingedition.com/concepts/search-and-recommendation/bm25
- Defined in: [Retrieve, then answer](measure-before-you-change.md#retrieve-then-answer)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/bm25

## Bonferroni correction

the Bonferroni correction, which shares the error budget between the comparisons.

- Formula: `1 minus 0.05 divided by m`
- The same as: https://rollingedition.com/concepts/search-and-recommendation/bonferroni-correction
- Defined in: [Many comparisons](intervals-and-sample-size.md#many-comparisons)
- Address: https://rollingedition.com/concepts/artificial-intelligence/bonferroni-correction

## calibration rubric

The calibration rubric checks correctness with no reference, on rows from HelpSteer2

- Also: rubric A
- A kind of: rubric
- Defined in: [What a judge is asked](a-judge-with-a-rubric.md#what-a-judge-is-asked)
- Address: https://rollingedition.com/concepts/llm-evaluation/calibration-rubric

## chance share

The chance share averages one over each item's option count.

- Defined in: [TruthfulQA](build-the-test-set.md#truthfulqa)
- Address: https://rollingedition.com/concepts/llm-evaluation/chance-share

## check candidate

a candidate has four parts: the mode, the input the check reads, the claim it tests, and what it can't see.

- Contrasts with: code check
- Defined in: [From a failure to a check](read-the-outputs.md#from-a-failure-to-a-check)
- Address: https://rollingedition.com/concepts/llm-evaluation/check-candidate

## citation

A citation is a claim about the docs: this section, in this version, supports the sentence it is attached to.

- Close to: https://rollingedition.com/concepts/search-and-recommendation/citation
- Defined in: [Citation accuracy](grounded-answers.md#citation-accuracy)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/citation

## citation accuracy

Citation accuracy asks whether each citation names a section the item lists as supporting in the asked version.

- Contrasts with: faithfulness
- Close to: https://rollingedition.com/concepts/search-and-recommendation/attribution
- Defined in: [Check that answers rest on the cited docs, in the asked version](grounded-answers.md)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/citation-accuracy

## citation form

the citation form, a section ID after sec: in square brackets, such as [sec:no-fail-flag]

- Defined in: [Citations](measure-before-you-change.md#citations-in-code)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/citation-form

## citation rate

The citation rate is the share of all citations in answered items that are supported.

- Contrasts with: item rate
- Defined in: [Citation accuracy](grounded-answers.md#citation-accuracy)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/citation-rate

## citation-first

citation-first, for a reply whose first line opens with a citation

- Defined in: [Format checks](checks-in-code.md#format-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/citation-first

## code check

A code check reads the reply's text and data the run already holds: the item's own data, which holds its reference answer and the list of sections that support it, the sections the prompt gave, and the docs' section IDs.

- Contrasts with: judge
- Defined in: [What a code check can see](checks-in-code.md#what-a-code-check-can-see)
- Address: https://rollingedition.com/concepts/llm-evaluation/code-check

## consistent pair

A pair is consistent when the same response wins in both orders.

- Contrasts with: order-changed pair
- Defined in: [One answer or two](a-judge-with-a-rubric.md#one-answer-or-two)
- Address: https://rollingedition.com/concepts/llm-evaluation/consistent-pair

## contamination

Contamination is when a benchmark's items or answers appear in training data, so a score can reflect memory rather than ability.

- Defined in: [Contamination](build-the-test-set.md#contamination)
- Address: https://rollingedition.com/concepts/llm-evaluation/contamination

## corrected pass rate

The corrected rate estimates the share of sablefile's readable replies that a person would pass, under the book's correctness cut.

- Also: corrected rate
- Formula: `(observed + TNR - 1) / (TPR + TNR - 1)`
- Computed from: true positive rate
- Computed from: true negative rate
- Defined in: [Correcting a pass rate](calibrate-the-judge.md#correcting-a-pass-rate)
- Address: https://rollingedition.com/concepts/llm-evaluation/corrected-pass-rate

## coverage

Coverage asks which parts of the tool the set exercises.

- Defined in: [Kinds and coverage](build-the-test-set.md#kinds-and-coverage)
- Address: https://rollingedition.com/concepts/llm-evaluation/coverage

## crossover point

The pass-rate correction in the next section leaves a rate unchanged at the crossover point, p* = (1 − TNR) / (2 − TPR − TNR).

- Also: p*
- Formula: `p* = (1 − TNR) / (2 − TPR − TNR)`
- Computed from: true positive rate
- Computed from: true negative rate
- Defined in: [True positive and true negative rates](calibrate-the-judge.md#tpr-and-tnr)
- Address: https://rollingedition.com/concepts/llm-evaluation/crossover-point

## decline phrase

When the docs don't answer a question, the assistant must reply with the decline phrase, "The docs don't say.", and nothing else.

- Also: decline sentence
- Defined in: [Declines](measure-before-you-change.md#declines-in-code)
- Address: https://rollingedition.com/concepts/llm-evaluation/decline-phrase

## declined-with-text

declined-with-text is a reply that contains the decline sentence along with other text.

- Part of: format check
- Defined in: [Format checks](checks-in-code.md#format-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/declined-with-text

## dev

dev items, the split of the test set this book works with while it develops its measures

- Also: dev items
- Part of: test set
- Close to: https://rollingedition.com/concepts/artificial-intelligence/validation-split
- Defined in: [Read the replies to find what to measure](read-the-outputs.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/dev

## empty

empty is a reply with no text.

- Part of: format check
- Defined in: [Format checks](checks-in-code.md#format-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/empty

## exact match

An exact match asks whether two strings are equal, and it suits any text that is fixed.

- Contrasts with: fuzzy match
- Defined in: [Exact and fuzzy match](checks-in-code.md#exact-and-fuzzy)
- Address: https://rollingedition.com/concepts/artificial-intelligence/exact-match

## example environment

the book keeps one example environment: one set of files that every chapter's examples import, pinned to the same versions, so the replay model, the checks and the gate are the same code in every chapter.

- Contrasts with: task
- Defined in: [Running it as a framework task](keep-the-evaluation-running.md#running-it-as-a-framework-task)
- Address: https://rollingedition.com/concepts/artificial-intelligence/example-environment

## extra="forbid"

The loader sets extra="forbid", so an unknown field is an error and not a field that is quietly ignored.

- True for: pydantic 2.14.3
- Implemented by: pydantic 2.14.3
- Defined in: [The item schema](build-the-test-set.md#the-item-schema)
- Address: https://rollingedition.com/concepts/artificial-intelligence/extra-forbid

## F1

F1, the harmonic mean of recall and precision

- Contrasts with: ROUGE-N
- Defined in: [Where BLEU and ROUGE mislead](checks-in-code.md#where-bleu-rouge-mislead)
- Address: https://rollingedition.com/concepts/artificial-intelligence/f1

## FAIL

A FAIL means the judge judged the answer wrong

- Defined in: [Verdict first](a-judge-with-a-rubric.md#verdict-first)
- Address: https://rollingedition.com/concepts/llm-evaluation/fail-verdict

## failure mode

Each reply got one mode, its main defect

- Also: mode
- Part of: check candidate
- Defined in: [Coding the failures](read-the-outputs.md#coding-the-failures)
- Address: https://rollingedition.com/concepts/llm-evaluation/failure-mode

## faithfulness

Faithfulness asks whether each claim follows from the sections the assistant was shown.

- Contrasts with: version-correctness
- The same as: https://rollingedition.com/concepts/search-and-recommendation/faithfulness
- Defined in: [Check that answers rest on the cited docs, in the asked version](grounded-answers.md)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/faithfulness

## false answer

a false answer is an unanswerable item answered.

- Defined in: [Declines](measure-before-you-change.md#declines-in-code)
- Address: https://rollingedition.com/concepts/llm-evaluation/false-answer

## false answer rate

The false answer rate is the number of unanswerable items answered, over the number of unanswerable items.

- Computed from: false answer
- Defined in: [Two errors, both counted](declining-when-the-docs-dont-say.md#two-errors)
- Address: https://rollingedition.com/concepts/llm-evaluation/false-answer-rate

## false premise

false-premise: the question asks about a flag or key that the asked version does not have.

- Also: false-premise
- Part of: planted item
- Defined in: [Planted items and their traps](build-the-test-set.md#planted-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/false-premise

## false refusal

A false refusal is an answerable item declined

- Contrasts with: false answer
- Defined in: [Declines](measure-before-you-change.md#declines-in-code)
- Address: https://rollingedition.com/concepts/llm-evaluation/false-refusal

## false refusal rate

The false refusal rate is the number of answerable items declined, over the number of answerable items.

- Computed from: false refusal
- Contrasts with: false answer rate
- Defined in: [Two errors, both counted](declining-when-the-docs-dont-say.md#two-errors)
- Address: https://rollingedition.com/concepts/llm-evaluation/false-refusal-rate

## flip

An item flips when its five verdicts are not all the same.

- Also: flips, flaky
- Measured from: variance set
- Defined in: [Variance within one item](intervals-and-sample-size.md#variance-within-one-item)
- Address: https://rollingedition.com/concepts/llm-evaluation/flip

## flip rate

the flip rate, the share of items that flip

- Computed from: flip
- Defined in: [Flag flaky items, never edit them](keep-the-evaluation-running.md#flaky-cases)
- Address: https://rollingedition.com/concepts/llm-evaluation/flip-rate

## format check

The format check asks whether a reply has the shape the prompt asks for, before anyone reads what it says.

- Defined in: [Format checks](checks-in-code.md#format-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/format-check

## fuzzy match

A fuzzy match scores how alike two strings are.

- Defined in: [Exact and fuzzy match](checks-in-code.md#exact-and-fuzzy)
- Address: https://rollingedition.com/concepts/artificial-intelligence/fuzzy-match

## gate

A gate is a rule that stops a change from merging.

- The same as: https://rollingedition.com/concepts/data-governance/gate
- Defined in: [A gate that respects the interval](keep-the-evaluation-running.md#a-gate-that-respects-the-interval)
- Address: https://rollingedition.com/concepts/llm-evaluation/gate

## grounded

An answer is grounded when a reader who follows its citations finds each of its claims where the citation says it is, in the version they asked about.

- Close to: https://rollingedition.com/concepts/search-and-recommendation/grounding
- Defined in: [What grounded means here](grounded-answers.md#what-grounded-means)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/grounded

## GSM8K

GSM8K is grade-school math word problems, each with a worked solution that ends in one number.

- A kind of: public benchmark
- Defined in: [GSM8K](build-the-test-set.md#gsm8k)
- Address: https://rollingedition.com/concepts/llm-evaluation/gsm8k

## guard

A guard reads the best-matching section's score and declines when it falls below a threshold.

- Also: retrieval-score guard, decline guard
- Computed from: BM25
- Defined in: [A guard on recorded replies](declining-when-the-docs-dont-say.md#a-guard)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/guard

## held-out

held-out is used once for each comparison, to report a result.

- Also: held-out items
- Contrasts with: dev
- Part of: test set
- The same as: https://rollingedition.com/concepts/artificial-intelligence/test-split
- Defined in: [Dev and held-out](build-the-test-set.md#dev-and-held-out)
- Address: https://rollingedition.com/concepts/llm-evaluation/held-out

## interval

An interval answers a different question from the pass rate: how far would the rate move if the set had been another set of as many items, drawn the same way?

- Also: 95% interval
- Computed from: pass rate
- Close to: https://rollingedition.com/concepts/search-and-recommendation/confidence-interval
- Defined in: [A pass rate and its interval](measure-before-you-change.md#a-pass-rate-and-its-interval)
- Address: https://rollingedition.com/concepts/artificial-intelligence/interval

## item

an item: one test question with the fields a scorer needs.

- Part of: test set
- Defined in: [What a test set is for](build-the-test-set.md#what-a-test-set-is-for)
- Address: https://rollingedition.com/concepts/llm-evaluation/item

## item rate

The item rate counts an answered item once if at least one of its citations is supported, over all answered items, so one good citation carries the item.

- Computed from: supported
- Defined in: [Citation accuracy](grounded-answers.md#citation-accuracy)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/item-rate

## judge

a judge: a model that grades a reply, here by reading the question, a written reference answer and the assistant's reply, and returning PASS or FAIL

- Close to: https://rollingedition.com/concepts/search-and-recommendation/judge
- Defined in: [One judge](measure-before-you-change.md#one-judge)
- Address: https://rollingedition.com/concepts/llm-evaluation/judge

## judged-correct rate

The judged-correct rate is the pass rate for version-dependent items alone, so a version miss shows on its own line, and a team can see whether a change to retrieval moved it.

- Computed from: version-dependent item
- Defined in: [Version-correctness](grounded-answers.md#version-correctness)
- Address: https://rollingedition.com/concepts/llm-evaluation/judged-correct-rate

## k5

The variant k5 retrieves five sections instead of three.

- Contrasts with: baseline
- Defined in: [Held-out, once](intervals-and-sample-size.md#held-out-once)
- Address: https://rollingedition.com/concepts/llm-evaluation/k5

## kappa

For two raters on pass or fail, kappa is the observed agreement minus the chance agreement, divided by one minus the chance agreement.

- Computed from: agreement
- Close to: https://rollingedition.com/concepts/search-and-recommendation/cohens-kappa
- Close to: https://rollingedition.com/concepts/llm-evaluation/cohens-kappa
- Defined in: [Agreement and kappa](calibrate-the-judge.md#agreement-and-kappa)
- Address: https://rollingedition.com/concepts/artificial-intelligence/kappa

## kind

Each item also has a kind, which says what a correct reply looks like.

- Part of: item
- Defined in: [What a test set is for](build-the-test-set.md#what-a-test-set-is-for)
- Address: https://rollingedition.com/concepts/llm-evaluation/kind

## length

length: whether the pass rate rises with the length of a reply that says no more.

- Also: verbosity bias
- Contrasts with: position
- Defined in: [Find where a judge's verdict stops being reliable](when-the-judge-stops-being-reliable.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/length

## MC1

The book uses TruthfulQA's multiple-choice version, MC1: exactly one option is correct, and here the model answers with a letter.

- Part of: TruthfulQA
- Defined in: [TruthfulQA](build-the-test-set.md#truthfulqa)
- Address: https://rollingedition.com/concepts/llm-evaluation/mc1

## missed refusal

A missed refusal answers an unanswerable item with content the docs don't hold.

- A kind of: failure mode
- Defined in: [Missed refusals](read-the-outputs.md#missed-refusals)
- Address: https://rollingedition.com/concepts/llm-evaluation/missed-refusal

## missing

missing means no version has a section with the cited ID.

- Defined in: [Citation checks](checks-in-code.md#citation-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/missing

## naive gate

A naive gate would fail whenever the point estimate of the difference is below minus the threshold

- Contrasts with: gate
- Defined in: [A gate that respects the interval](keep-the-evaluation-running.md#a-gate-that-respects-the-interval)
- Address: https://rollingedition.com/concepts/llm-evaluation/naive-gate

## near-miss term

a planted near-miss term, a name that one version renamed or that the docs use for another concept, which catches a careless reply

- Also: near-miss-term
- Part of: planted item
- Defined in: [What the replies look like](read-the-outputs.md#what-the-replies-look-like)
- Address: https://rollingedition.com/concepts/llm-evaluation/near-miss-term

## no difference detected

No difference detected, the reading when the interval includes zero, is a finding about a set at its size.

- Computed from: interval
- Defined in: [Paired comparisons](intervals-and-sample-size.md#paired-comparisons)
- Address: https://rollingedition.com/concepts/artificial-intelligence/no-difference-detected

## no-citation

no-citation is an answer that cites nothing.

- Part of: format check
- Defined in: [Format checks](checks-in-code.md#format-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/no-citation

## ok

a reply with no defect got ok.

- Defined in: [Coding the failures](read-the-outputs.md#coding-the-failures)
- Address: https://rollingedition.com/concepts/llm-evaluation/ok

## order-changed pair

An order-changed pair is one where the verdict followed the position, so it says nothing about which reply is better.

- Also: order-changed
- Defined in: [One answer or two](a-judge-with-a-rubric.md#one-answer-or-two)
- Address: https://rollingedition.com/concepts/llm-evaluation/order-changed-pair

## outcome

Outcome is whether a reply passed.

- Contrasts with: path
- Defined in: [Outcome and path](grounded-answers.md#outcome-and-path)
- Address: https://rollingedition.com/concepts/llm-evaluation/outcome

## outcome against path

Outcome against path asks whether a pass came with its section in hand, and whether a fail had it.

- Computed from: outcome
- Computed from: path
- Defined in: [Check that answers rest on the cited docs, in the asked version](grounded-answers.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/outcome-against-path

## paired comparison

A paired comparison subtracts, for each item, the verdict of the baseline from the verdict of the variant, here prompt B, and averages the differences over the set.

- Contrasts with: unpaired comparison
- Close to: https://rollingedition.com/concepts/search-and-recommendation/paired-test
- Defined in: [Paired comparisons](intervals-and-sample-size.md#paired-comparisons)
- Address: https://rollingedition.com/concepts/artificial-intelligence/paired-comparison

## paired difference

The paired difference is the variant's score minus the baseline's, here rubric B's agreement score minus rubric A's, averaged over the dev rows

- Close to: https://rollingedition.com/concepts/llm-evaluation/paired-difference
- Defined in: [Agreement and kappa](calibrate-the-judge.md#agreement-and-kappa)
- Address: https://rollingedition.com/concepts/artificial-intelligence/paired-difference

## pairwise judge

A pairwise judge reads two replies and picks the better one, rather than passing or failing each.

- Contrasts with: pass or fail rubric
- Defined in: [Pairwise calibration](calibrate-the-judge.md#pairwise-calibration)
- Address: https://rollingedition.com/concepts/llm-evaluation/pairwise-judge

## pairwise judgment

A pairwise judgment shows the judge two replies to the same request and asks which is better.

- Defined in: [One answer or two](a-judge-with-a-rubric.md#one-answer-or-two)
- Address: https://rollingedition.com/concepts/llm-evaluation/pairwise-judgment

## pass or fail rubric

A pass or fail rubric gives the judge two answers.

- A kind of: rubric
- Defined in: [Pass, fail, or a scale](a-judge-with-a-rubric.md#pass-fail-or-scale)
- Address: https://rollingedition.com/concepts/llm-evaluation/pass-or-fail-rubric

## pass rate

A pass rate is a count divided by a denominator

- Formula: `pass rate = passed items / items`
- Computed from: item
- Defined in: [A pass rate and its interval](measure-before-you-change.md#a-pass-rate-and-its-interval)
- Address: https://rollingedition.com/concepts/llm-evaluation/pass-rate

## path

Path is what the steps before the reply reached.

- Defined in: [Outcome and path](grounded-answers.md#outcome-and-path)
- Address: https://rollingedition.com/concepts/llm-evaluation/path

## percentile bootstrap

The percentile bootstrap is the simplest interval built on resampling, the middle 95% of the resampled rates, or another share when a different level is chosen.

- A kind of: interval
- The same as: https://rollingedition.com/concepts/search-and-recommendation/percentile-interval
- Defined in: [A pass rate and its interval](measure-before-you-change.md#a-pass-rate-and-its-interval)
- Address: https://rollingedition.com/concepts/artificial-intelligence/percentile-bootstrap

## planted item

A planted item was written to catch one particular mistake

- Defined in: [The twenty items](measure-before-you-change.md#the-twenty-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/planted-item

## position

position: whether a pairwise verdict depends on which answer was shown first.

- Defined in: [Find where a judge's verdict stops being reliable](when-the-judge-stops-being-reliable.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/position

## public benchmark

A public benchmark is a set of questions and answers someone else published.

- Defined in: [Public benchmarks](build-the-test-set.md#public-benchmarks)
- Address: https://rollingedition.com/concepts/llm-evaluation/public-benchmark

## ratio()

ratio(), which the documentation defines as twice the number of matching elements divided by the total number of elements in both sequences.

- Defined in: [Exact and fuzzy match](checks-in-code.md#exact-and-fuzzy)
- Address: https://rollingedition.com/concepts/artificial-intelligence/ratio

## recording

The recording is a folder of replies, one per item.

- The same as: https://rollingedition.com/concepts/artificial-intelligence/recording
- Defined in: [Replay the answers](measure-before-you-change.md#replay-the-answers)
- Address: https://rollingedition.com/concepts/llm-evaluation/recording

## reference answer

the reference answer, which is the author's statement of what a right reply says

- Part of: item
- Defined in: [What the replies look like](read-the-outputs.md#what-the-replies-look-like)
- Address: https://rollingedition.com/concepts/llm-evaluation/reference-answer

## reference-free judge

A reference-free judge is given only the request and the reply, and it decides from what it knows whether the reply is right.

- Defined in: [Reference-guided or reference-free](a-judge-with-a-rubric.md#reference-guided)
- Address: https://rollingedition.com/concepts/llm-evaluation/reference-free-judge

## reference-guided judge

A reference-guided judge is given a written answer for the question, and it checks the reply against that answer.

- Contrasts with: reference-free judge
- Defined in: [Reference-guided or reference-free](a-judge-with-a-rubric.md#reference-guided)
- Address: https://rollingedition.com/concepts/llm-evaluation/reference-guided-judge

## retrieval-path count

The retrieval-path count asks one question of each item: is a supporting section of the asked version in the top k?

- Measured from: supporting sections
- Defined in: [Retrieval quality belongs to another book](grounded-answers.md#retrieval-quality)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/retrieval-path-count

## ROUGE-1 F1

ROUGE-1 F1 counts the single words a candidate shares with its reference, as an F1.

- Contrasts with: ROUGE-N
- Computed from: F1
- Defined in: [Where BLEU and ROUGE mislead](checks-in-code.md#where-bleu-rouge-mislead)
- Address: https://rollingedition.com/concepts/artificial-intelligence/rouge-1-f1

## ROUGE-N

Lin defined ROUGE-N as an n-gram recall: the share of the reference's word runs that the candidate covers

- Defined in: [Where BLEU and ROUGE mislead](checks-in-code.md#where-bleu-rouge-mislead)
- Address: https://rollingedition.com/concepts/artificial-intelligence/rouge-n

## rubric

A judge works from its instructions, and the instructions are the rubric.

- Defined in: [Write a rubric a judge can apply](a-judge-with-a-rubric.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/rubric

## rubric B

Rubric B is a second wording of the calibration task.

- A kind of: rubric
- Defined in: [What a judge is asked](a-judge-with-a-rubric.md#what-a-judge-is-asked)
- Address: https://rollingedition.com/concepts/llm-evaluation/rubric-b

## scale

A scale gives the judge several answers.

- Contrasts with: pass or fail rubric
- Defined in: [Pass, fail, or a scale](a-judge-with-a-rubric.md#pass-fail-or-scale)
- Address: https://rollingedition.com/concepts/llm-evaluation/scale

## second-model variant

The second-model variant keeps the baseline's prompt and hands the answer to a smaller model, Qwen3 with 0.6 billion parameters in an 8-bit build.

- Also: second model
- Contrasts with: baseline
- Defined in: [What the replies look like](read-the-outputs.md#what-the-replies-look-like)
- Address: https://rollingedition.com/concepts/llm-evaluation/second-model-variant

## self-preference

self-preference: whether the judge favours answers written by its own model over answers of equal quality.

- Contrasts with: length
- Defined in: [Find where a judge's verdict stops being reliable](when-the-judge-stops-being-reliable.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/self-preference

## stale answer

stale-answer: the answer sits under a section ID that only the asked version has, so an answer built from an older version's docs is stale.

- Also: stale-answer
- Part of: planted item
- Defined in: [Planted items and their traps](build-the-test-set.md#planted-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/stale-answer

## stratified

The split is stratified, so that each kind appears in both parts in about the same proportion.

- Defined in: [Dev and held-out](build-the-test-set.md#dev-and-held-out)
- Address: https://rollingedition.com/concepts/artificial-intelligence/stratified-split

## stray-line

stray-line, for a line that ends no sentence once its citations are taken out.

- Defined in: [Format checks](checks-in-code.md#format-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/stray-line

## supported

supported means the ID is on the item's list for the asked version.

- Measured from: supporting sections
- Defined in: [Citation checks](checks-in-code.md#citation-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/supported

## supporting sections

supporting sections, the parts of the docs that a correct answer rests on.

- Part of: item
- Defined in: [What a test set is for](build-the-test-set.md#what-a-test-set-is-for)
- Address: https://rollingedition.com/concepts/llm-evaluation/supporting-sections

## system text

The system text states the task, the rules and the form the reply must take.

- Part of: rubric
- Close to: https://rollingedition.com/concepts/large-language-models/system-message
- Defined in: [Write a rubric a judge can apply](a-judge-with-a-rubric.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/system-text

## task

a task is the recipe for an evaluation, made minimally of a dataset, a solver and a scorer

- Defined in: [Running it as a framework task](keep-the-evaluation-running.md#running-it-as-a-framework-task)
- Address: https://rollingedition.com/concepts/evaluation-frameworks/task

## template

The template wraps the request, the reply and any reference in markers, so the judge can tell them apart.

- Part of: rubric
- Defined in: [Write a rubric a judge can apply](a-judge-with-a-rubric.md)
- Address: https://rollingedition.com/concepts/llm-evaluation/template

## test set

A test set is a list of questions, each with the answer it should get.

- Defined in: [The twenty items](measure-before-you-change.md#the-twenty-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/test-set

## transfer assumption

The transfer assumption is that the judge's miss rate on human passes, and its pass-through rate on human fails, are the same on sablefile's replies as on the HelpSteer2 rows.

- Comes before: corrected pass rate
- Defined in: [The transfer assumption](calibrate-the-judge.md#transfer-assumption)
- Address: https://rollingedition.com/concepts/llm-evaluation/transfer-assumption

## true negative rate

The true negative rate, TNR, is the share of human FAIL rows that the judge fails.

- Also: TNR
- Contrasts with: agreement
- Defined in: [True positive and true negative rates](calibrate-the-judge.md#tpr-and-tnr)
- Address: https://rollingedition.com/concepts/llm-evaluation/true-negative-rate

## true positive rate

The true positive rate, TPR, is the share of human PASS rows that the judge passes.

- Also: TPR
- Close to: https://rollingedition.com/concepts/data-governance/recall
- Defined in: [True positive and true negative rates](calibrate-the-judge.md#tpr-and-tnr)
- Address: https://rollingedition.com/concepts/llm-evaluation/true-positive-rate

## TruthfulQA

TruthfulQA asks questions on which people often answer falsely, such as a common myth.

- A kind of: public benchmark
- Defined in: [TruthfulQA](build-the-test-set.md#truthfulqa)
- Address: https://rollingedition.com/concepts/llm-evaluation/truthfulqa

## twin

a twin: the same question asked about another version

- Defined in: [The twenty items](measure-before-you-change.md#the-twenty-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/twin

## unanswerable item

Unanswerable items ask about something the docs don't cover, and the right reply is the decline.

- Contrasts with: answerable item
- Defined in: [The twenty items](measure-before-you-change.md#the-twenty-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/unanswerable-item

## unfiltered variant

The unfiltered variant drops the baseline's version filter.

- Contrasts with: baseline
- Defined in: [What the replies look like](read-the-outputs.md#what-the-replies-look-like)
- Address: https://rollingedition.com/concepts/llm-evaluation/unfiltered-variant

## unknown-section

The check calls a citation to any section that was not in the prompt unknown-section, whichever way it went wrong.

- Part of: format check
- Defined in: [Citations](measure-before-you-change.md#citations-in-code)
- Address: https://rollingedition.com/concepts/llm-evaluation/unknown-section

## unlisted

unlisted means a section of the asked version that the item doesn't list.

- Defined in: [Citation checks](checks-in-code.md#citation-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/unlisted

## unpaired comparison

An unpaired comparison takes two separate pass rates and sets them side by side.

- Defined in: [Paired comparisons](intervals-and-sample-size.md#paired-comparisons)
- Address: https://rollingedition.com/concepts/artificial-intelligence/unpaired-comparison

## unreadable pair

An unreadable pair has a missing verdict in either order.

- Defined in: [Position](when-the-judge-stops-being-reliable.md#position)
- Address: https://rollingedition.com/concepts/llm-evaluation/unreadable-pair

## unreadable verdict

an unreadable verdict means the judge gave no judgment the code can read.

- Contrasts with: FAIL
- Defined in: [Verdict first](a-judge-with-a-rubric.md#verdict-first)
- Address: https://rollingedition.com/concepts/llm-evaluation/unreadable-verdict

## upper bound

The upper bound is the most favourable reading the interval allows for the candidate

- Part of: interval
- Defined in: [A gate that respects the interval](keep-the-evaluation-running.md#a-gate-that-respects-the-interval)
- Address: https://rollingedition.com/concepts/llm-evaluation/upper-bound

## variance set

The variance set holds five samples of the assistant's reply to each dev item, drawn at temperature 0.7.

- Defined in: [Variance within one item](intervals-and-sample-size.md#variance-within-one-item)
- Address: https://rollingedition.com/concepts/llm-evaluation/variance-set

## version swap

version-swap: the question uses another version's wording, so an assistant that matches wording answers for that version.

- Also: version-swap
- Part of: planted item
- Defined in: [Planted items and their traps](build-the-test-set.md#planted-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/version-swap

## version-correctness

Version-correctness asks whether the answer matches the reference for the asked version.

- Defined in: [Check that answers rest on the cited docs, in the asked version](grounded-answers.md)
- Address: https://rollingedition.com/concepts/retrieval-augmented-generation/version-correctness

## version-dependent item

Version-dependent items have an answer that changes from one version to the next

- A kind of: item
- Defined in: [The twenty items](measure-before-you-change.md#the-twenty-items)
- Address: https://rollingedition.com/concepts/llm-evaluation/version-dependent-item

## weak pass

A pass with a wide interval is a weak pass

- Measured from: interval
- Defined in: [A gate that respects the interval](keep-the-evaluation-running.md#a-gate-that-respects-the-interval)
- Address: https://rollingedition.com/concepts/llm-evaluation/weak-pass

## wrong-version answer

A wrong-version answer gives another version's behaviour for the version the question asks about

- A kind of: failure mode
- Defined in: [Wrong-version answers](read-the-outputs.md#wrong-version-answers)
- Address: https://rollingedition.com/concepts/llm-evaluation/wrong-version-answer

## wrong-version citation

wrong-version means a section that exists in another version only.

- Also: wrong-version
- Contrasts with: wrong-version answer
- Defined in: [Citation checks](checks-in-code.md#citation-checks)
- Address: https://rollingedition.com/concepts/llm-evaluation/wrong-version-citation

## XSTest

XSTest is a test suite of safe prompts that look unsafe, with unsafe prompts beside them as contrasts.

- Defined in: [Outside this book](declining-when-the-docs-dont-say.md#outside-this-book)
- Address: https://rollingedition.com/concepts/llm-evaluation/xstest
