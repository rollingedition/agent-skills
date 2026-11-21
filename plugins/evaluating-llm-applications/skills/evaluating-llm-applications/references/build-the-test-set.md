---
title: "Evaluating LLM Applications"
chapter: "Build a test set you can defend, and read public benchmarks"
chapter_id: build-the-test-set
book: evaluating-llm-applications
edition: 2026.11.4
verified: 2026-11-21
edition_code: TVZC-TMQC
canonical: https://rollingedition.com/evaluating-llm-applications/build-the-test-set
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Build a test set you can defend, and read public benchmarks,” chapter 3 of Evaluating LLM Applications, Edition 2026.11.4, examples passed Nov 21, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/build-the-test-set. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Build a test set you can defend, and read public benchmarks

By the end of this chapter you can build a test set whose score tells you something, check its schema and coverage with code, and say what a public benchmark score does and does not tell you about your own assistant. You will also see how a multiple-choice score can be impossible to tell apart from a habit of answering the same way.

Here the test set belongs to the sablefile assistant, a retrieval step and a model that answers questions from the tool's docs. Every number this book reports about the assistant comes from a set of questions with reference answers, so the set decides how much a score is worth. The book guards against three faults. If every question has an answer in the docs, an assistant that always answers will look good. If the questions reuse the docs' own sentences, retrieval matches on words and looks right. If the set is tuned until the score rises, the score records the tuning. The set is also the only place the questions are written down, so a fault in it can go unseen, and a score built on it inherits the fault without any sign of it.

This chapter builds the set the book uses and checks it with code. It then reads two public benchmarks, GSM8K and TruthfulQA, which many readers will have seen quoted, and says what their scores can still show. The sections follow the questions a team would ask in turn: what the set is for, how it is built and checked, how it is split, and what a public score adds.

## What a test set is for {#what-a-test-set-is-for}

A [test set](#the-twenty-items) is a fixed set of questions, paired with the answers you would accept, that stands in for the questions users will ask. Its job is to be asked the same questions each time something changes, so that a difference in score comes from the change and not from the questions. It does that job only while it stays fixed. This set was written from the docs rather than sampled from users, so it stands in for them and does not reproduce them.

Each row is an **item**: one test question with the fields a scorer needs. The item is the unit of every count in this book, so a pass rate is always a share of items, and its denominator says which ones. Each item has a **reference answer**, which the scorer compares a reply with, and **supporting sections**, the parts of the docs that a correct answer rests on. The reference answers are written labels. The book's own drafting agents wrote them from the docs, a second pass checked them against the docs, and a script checks the file's shape and section IDs. They are not human labels, and the book does not call them that.

Each item also has a **kind**, which says what a correct reply looks like. A set built from one kind tests one skill, so this set mixes four kinds on purpose. It should also look like the questions users bring. Users ask things the docs cannot answer, and a set with only answerable questions would reward an assistant that never declines.

The set is small on purpose. It holds 120 items, which a reader can check by hand, and each one has a reference answer that a second pass checked against the docs. We keep it small enough to read, because a set nobody reads can only measure its own mistakes. A score is only as good as the set behind it, and the set is what two people argue about when they disagree on whether a change helped. Keep it readable, keep the reasons for each item written down, and do not add items only because a score looks wrong, since that picks items for their result.

A test set is never training data. Nothing in it teaches the assistant, and the assistant never sees a reference answer while the set is being built. If someone tunes against the answers, the set stops being a test and becomes a target, which is what the [rule on dev and held-out](#dev-and-held-out) is for.

**Working rule:** Write the set before you change anything you will measure with it, and keep its file under version control, so that every comparison names the items it used. A set you edit after seeing the scores measures your edits, not the assistant.

## The item schema {#the-item-schema}

The set has to load before anything is scored. The file holds one JSON object per line, and a loader validates each one with pydantic, a Python library that checks values against a declared shape. This book pins pydantic 2.14.3. The fields are these:

- `id`: `q-` and four digits, unique, and never changed once written.
- `question`: one to 400 plain characters.
- `version`: the docs version the question asks about.
- `kind`: one of the four kinds.
- `reference_answer`: the answer, or nothing for an unanswerable item, where the right reply is to decline.
- `supporting_sections`: the version and section ID pairs that the answer rests on.
- `split`: `dev` or `held-out`.
- `planted` and `planted_why`: whether the item is a planted trap, and which one.
- `twin_of`: the ID of the item that asks the same question about another version, if there is one.

The loader sets `extra="forbid"`, so an unknown field is an error and not a field that is quietly ignored. A typo in a field name would otherwise produce a set that looks right and scores wrong. Errors are reported row by row, so one bad row does not hide the rest.

Shape checks cannot see across rows, so the cross-item rules in the book's `lib/testset.py` do that work. They check that IDs are unique, that each twin names its partner back, asks for another version, is version-dependent and sits in the same split, and that every false-premise item is unanswerable. They check that every supporting section exists for the version it names, that no reference answer repeats eleven words in a row from a section, and that the counts match the design.

Each of these rules is a contract that anyone who adds or edits an item has to pass. The check prints each broken rule. It exits without an error code whether or not it finds one, so it stops nothing by itself, and the build has to treat a printed problem as a failure.

The reference answer needs the most care of all, because every reply is compared with it. A reference that is wrong in a consistent direction makes the score wrong in that direction, and no shape rule can catch a well-formed wrong answer. That is why each reference is written with the sections it rests on, so a reader can check the claim against the docs in a few minutes rather than take the author's word.

Twins can drift into different splits when they are written at different times, and then the dev part tunes on a question the held-out part checks. The cross-item rules catch that, so the twins stay together.

The schema check below runs both groups of rules and prints the problem count, with the counts by kind and by split.

Example `check-item-schema` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.4:

```python
"""Loads all 120 test-set items, runs the per-item and the cross-item rules, and prints the problem count with the
counts by kind and by split. The point rests on the first line: a set that passes prints zero problems."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.testset import cross_item_problems, item_problems

items, row_problems = item_problems()  # every row, even a bad one, is reported rather than stopping the run
problems = sorted(row_problems) + cross_item_problems(items)
print(f"items: {len(items)}")
print(f"problems: {len(problems)}")
for problem in problems:
    print(f"  {problem}")

kinds = Counter(item.kind for item in items)
for kind in ("answerable", "unanswerable", "version-dependent", "ambiguous"):
    print(f"kind {kind}: {kinds[kind]}")
splits = Counter(item.split for item in items)
for split in ("dev", "held-out"):
    print(f"split {split}: {splits[split]}")
print(f"planted: {sum(1 for item in items if item.planted)}")
```

Output:

```text
items: 120
problems: 0
kind answerable: 60
kind unanswerable: 20
kind version-dependent: 25
kind ambiguous: 15
split dev: 80
split held-out: 40
planted: 24
```

The set holds 120 items, and the rules find 0 problems. A clean run means the rows parse, the references point at sections that exist, and the counts match the design. It shows the set's shape only. It does not mean the questions are good, that the reference answers are right, or that a planted item catches an assistant. Those claims need a reader, and the rest of this chapter describes how the set was built so that a reader can check them.

**Working rule:** Run the schema check in the build and treat any printed problem as a failure, and read a sample of items by hand before you trust the set.

## Kinds and coverage {#kinds-and-coverage}

Each kind tests something the assistant must do. An [answerable item](#the-twenty-items) has docs that answer it fully, so the assistant must answer and agree with the reference, and its citations are checked on their own. A refusal there is a [false refusal](#declines-in-code). An [unanswerable item](#the-twenty-items) has docs that do not say, so the right reply is the decline phrase, exactly. Any other reply is a false answer, and these items are what stop an assistant that always answers from scoring well. [The chapter on declining](declining-when-the-docs-dont-say) covers the phrase. A version-dependent item names the version it asks about, and its reply must match that version's reference. An ambiguous item admits two readings, and the reference holds one answer per reading. A reply must answer each reading the docs support, and a partial answer fails.

The kinds table below prints the set by kind and by split.

Example `kinds-by-split` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.4:

```python
"""Prints the stratification of plan section 3.4 as counts: kind by split, then planted items by split, with totals.
The dev and held-out columns are the numbers the chapter's split table quotes."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.testset import load_items

items = load_items()
splits = ("dev", "held-out")
kinds = ("answerable", "unanswerable", "version-dependent", "ambiguous")
counts = Counter((item.kind, item.split) for item in items)
print(f"{'kind':<20}{'dev':>6}{'held-out':>10}{'total':>8}")
for kind in kinds:
    row = [counts[(kind, split)] for split in splits]
    print(f"{kind:<20}{row[0]:>6}{row[1]:>10}{sum(row):>8}")
totals = [sum(counts[(kind, split)] for kind in kinds) for split in splits]
print(f"{'total':<20}{totals[0]:>6}{totals[1]:>10}{sum(totals):>8}")
print()
planted = Counter((item.planted_why, item.split) for item in items if item.planted)
print(f"{'planted':<20}{'dev':>6}{'held-out':>10}{'total':>8}")
reasons = sorted({why for why, _ in planted})
for why in reasons:
    row = [planted[(why, split)] for split in splits]
    print(f"{why:<20}{row[0]:>6}{row[1]:>10}{sum(row):>8}")
planted_totals = [sum(planted[(why, split)] for why in reasons) for split in splits]
print(f"{'total':<20}{planted_totals[0]:>6}{planted_totals[1]:>10}{sum(planted_totals):>8}")
print()
print(f"items: {len(items)}")
```

Output:

```text
kind                   dev  held-out   total
answerable              40        20      60
unanswerable            13         7      20
version-dependent       17         8      25
ambiguous               10         5      15
total                   80        40     120

planted                dev  held-out   total
ambiguous-target         2         2       4
false-premise            4         2       6
near-miss-term           3         2       5
stale-answer             3         1       4
version-swap             4         1       5
total                   16         8      24

items: 120
```

The table prints the split by kind that the design fixes: each kind is divided between dev and held-out in about the same proportion, and the planted items are split the same way. Its last line gives the item count, 120, which matches the schema check. By kind, the set holds:

- answerable: 60 items;
- unanswerable: 20 items;
- version-dependent: 25 items;
- ambiguous: 15 items.

Coverage asks which parts of the tool the set exercises. The sablefile tool has six behaviours that an assistant must get right, named B1 to B6: what `sablefile sync` does with no flag, the exit status of `check` when a file has drifted, the syntax of `ignore` entries, the lock file's format, the placeholder syntax, and the retry count for remote fetches. The wrong-version answers that [chapter 2](read-the-outputs) found fall on these behaviours: q-0021 on B2, q-0023 on B3 and q-0029 on B1.

The coverage check stops if its mapping misses an item.

Example `behaviour-coverage` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.4:

```python
"""Shows how many items of the test set exercise each behaviour B1 to B6, and which ones. The mapping in data/behaviours.json
must list every item of the set exactly once, or the example stops; items that exercise no behaviour are counted apart."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import json
from pathlib import Path

from lib.testset import load_items

BEHAVIOURS = Path(__file__).resolve().parent / "data" / "behaviours.json"
ids = sorted(item.id for item in load_items())
mapping = json.loads(BEHAVIOURS.read_text(encoding="utf-8"))
assert sorted(mapping) == ids, "behaviours.json must list every item of the set, once"  # the coverage needs every item

print(f"items: {len(ids)}")
print(f"items with no behaviour: {sum(1 for labels in mapping.values() if not labels)}")
for behaviour in ("B1", "B2", "B3", "B4", "B5", "B6"):
    hits = sorted(item for item, labels in mapping.items() if behaviour in labels)
    print(f"{behaviour} items: {len(hits)}")
    print(f"{behaviour} ids: {', '.join(hits)}")
```

Output:

```text
items: 120
items with no behaviour: 48
B1 items: 11
B1 ids: q-0001, q-0002, q-0020, q-0029, q-0030, q-0033, q-0044, q-0061, q-0063, q-0064, q-0103
B2 items: 13
B2 ids: q-0006, q-0019, q-0021, q-0022, q-0043, q-0048, q-0056, q-0057, q-0058, q-0083, q-0084, q-0089, q-0092
B3 items: 14
B3 ids: q-0007, q-0008, q-0023, q-0024, q-0051, q-0071, q-0072, q-0073, q-0081, q-0082, q-0114, q-0115, q-0116, q-0117
B4 items: 17
B4 ids: q-0005, q-0009, q-0010, q-0020, q-0025, q-0026, q-0031, q-0032, q-0046, q-0047, q-0050, q-0053, q-0054, q-0059, q-0060, q-0101, q-0119
B5 items: 8
B5 ids: q-0003, q-0004, q-0013, q-0052, q-0079, q-0080, q-0087, q-0088
B6 items: 10
B6 ids: q-0011, q-0012, q-0027, q-0028, q-0045, q-0055, q-0068, q-0085, q-0086, q-0109
```

Each behaviour's count is one line of output:

- B1, the default of `sync`: 11 items.
- B2, the exit status of `check`: 13 items.
- B3, `ignore` syntax: 14 items.
- B4, the lock file: 17 items.
- B5, placeholder syntax: 8 items.
- B6, retries for remote fetches: 10 items.

One item carries two behaviours, so the six counts add up to one more than the items that carry any. Items with no behaviour are still part of the set. Here 48 of the 120 items carry none.

**Working rule:** Count coverage for each behaviour before you quote a score for it, and treat a behaviour with only a few items as untested. Passing those items shows that one behaviour, and nothing about the rest of the tool.

### Planted items and their traps {#planted-items}

A [planted item](#the-twenty-items) is written to break an assistant in one named way. Each carries a reason from a fixed list of five:

- `false-premise`: the question asks about a flag or key that the asked version does not have. The right reply is the decline phrase, so planted false premises are always unanswerable.
- `near-miss-term`: a term one version renamed, or a term the docs use for another concept.
- `version-swap`: the question uses another version's wording, so an assistant that matches wording answers for that version.
- `stale-answer`: the answer sits under a section ID that a version filter removes, so a filter that is too strict misses it.
- `ambiguous-target`: a pronoun or a phrase such as "the file" has no clear referent without the sections.

A planted item is useful because its failure is named. If the assistant fails it, a reader knows which failure happened. Planted items are counted with their kind, so a planted false premise is also unanswerable. The set holds 24 planted items, about one in five. Planted items are not split out in the metric tables, and no chapter in this book reports results trap by trap.

**Working rule:** Plant an item only for a trap you can name from the list. Write down the wrong reply it should catch, and check against the cited sections that the wrong reply is wrong, before the item enters the set.

### Synthetic items and what they hide {#synthetic-items}

These items were written from the docs, and the book builds them against two traps. The first is copying. A question that repeats a section's sentence gives retrieval a match on words it finds at once, so the test then measures word matching and not answering. The copy check stops a reference that repeats eleven words of a section, but it covers reference answers only, not questions. The rule for writing is to ask each question the way a user would, in the user's words and not the docs'.

The second trap is a reference that is true for two versions, so a reply that describes the other version passes. A version-dependent item names its version, and its twin pairs the same question with a second version, so no reply is right for both by accident.

**Working rule:** Ask each question the way a user would, from the docs but not in their sentences, and read each question against its sections before the set is frozen, since the copy check does not read questions. For a behaviour that changed between versions, name the version in the question and write its twin.

## Dev and held-out {#dev-and-held-out}

The set is split in two, because a score tuned on the questions it is measured with does not show progress. [Dev](#read-the-outputs) may be tuned on, and held-out is used once, to report a result. The split is stratified, so that each kind appears in both parts in about the same proportion. Without that, one part could hold most of the unanswerable items, and the two scores would then measure different sets. The set holds 80 dev items and 40 held-out items, and each row's `split` field records which part it belongs to. The twenty items that [chapter 1](measure-before-you-change) measures are dev items, so its rates are dev rates.

Only dev may be tuned on. Prompt wording, the number of sections retrieved, the version filter and the wording of the judge's rubric may all be chosen from dev results. Once a setting is chosen, it is frozen before held-out runs. Held-out runs once for each variant, in the chapter that compares the variants, and its numbers are the ones a chapter quotes. A recording's manifest says whether anything in it was tuned on held-out, and that answer must be no.

Dev has a job that held-out does not. It is where failures are read, so that a reader can form a hypothesis about why the assistant fails. A hypothesis formed on dev is a claim to test on held-out, not a result. Reading dev failures to choose a setting is allowed. Reading held-out failures to choose a change is not.

A split is only as clean as its record. Each row's split is written once, when the item is written, and it does not move with the scores. A split that changes after the scores are in is not a split.

Held-out is small, and a score on it is one number with an interval around it. A comparison on held-out therefore needs paired items, one verdict per item for each variant, and an interval over those pairs. [The chapter on intervals and sample size](intervals-and-sample-size) builds that comparison, and this chapter only needs the rule it rests on.

One more rule keeps the split honest. A question may be corrected only when its reference answer or its sections are wrong. It may never be changed because the assistant fails it. Otherwise the set would measure the assistant's last failure, and the score would rise each time someone fixed a failure by editing the test.

**Working rule:** Tune only on dev, freeze every setting before you open held-out, and run held-out once for each comparison. A held-out score that you read before a change, and then lifted by changing something, is a dev score, and you should say so.

## Public benchmarks {#public-benchmarks}

A public benchmark is a set of questions and answers someone else published. It does not measure the sablefile assistant, and its score depends on the prompt, the sampling and the parser.

Both samples are seeded samples of one hundred items, and their cards were read on November 20, 2026. Both recordings come from Qwen3-4B-Instruct-2507, the book's assistant and judge, in its Q4_K_M GGUF build, run on a CPU with greedy decoding. Replies were capped at 256 tokens for GSM8K and 160 for TruthfulQA.

**Working rule:** Quote a public score only beside its sample, model build, prompt, parser, reply cap and interval, and never beside a published number.

### GSM8K {#gsm8k}

GSM8K is grade-school math word problems, each with a worked solution that ends in one number. The score is an exact match on that number. The prompt asks for a "Final answer:" line the scorer never reads. It takes the number after the last `####` marker in the reply, or else the last number in the reply. No reply contains `####`, so every verdict came from the last number, which for a finished reply is its "Final answer:" number. The paper describes 8.5K problems, with 1K for testing ([Cobbe and colleagues, 2021](https://arxiv.org/abs/2110.14168)). The [dataset card](https://huggingface.co/datasets/openai/gsm8k) gives its second split 1,319 rows, which the viewer calls "test" and the splits table calls "validation". The book does not reconcile them, and the sample uses the viewer's "test" split. The card gives the licence as MIT.

Example `score-gsm8k` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""Scores the recorded replies on the 100-item GSM8K sample by exact match on the final number. The accuracy line rests on
its count of readable replies; unreadable replies are counted apart, never as wrong. The three example items show a right,
a wrong and an unreadable reply. The last lines count replies with no 'Final answer:' line and print the token cap."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.bench import load_gsm8k, score_gsm8k
from lib.prompts import BENCH_GSM8K_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_pct, pct

rows = load_gsm8k()
by_id = {row["id"]: row for row in rows}
replies = ReplayModel("bench-gsm8k", BENCH_GSM8K_SHA256)  # fails if the recording was made from another prompt
scored = score_gsm8k(rows, {row["id"]: replies.reply(row["id"]) for row in rows})
parsed = {item: number for item, number, _ in scored}

readable = [entry for entry in scored if entry[2] is not None]
right = [entry[0] for entry in readable if entry[2]]
wrong = [entry[0] for entry in readable if not entry[2]]
unreadable = [entry[0] for entry in scored if entry[2] is None]

print(f"items: {len(rows)}")
print(f"readable: {len(readable)} of {len(rows)}")
print(f"accuracy: {pct(len(right), len(readable))}")
# The interval resamples the readable items only, since an unreadable reply has no verdict to resample.
lo, hi = bootstrap_mean([1.0 if entry[2] else 0.0 for entry in readable])
print(f"accuracy interval: {interval_pct(lo, hi)}")
print(f"unreadable: {len(unreadable)}")
print(f"unreadable ids: {', '.join(unreadable) or 'none'}")
no_final = [row["id"] for row in rows if "final answer:" not in replies.reply(row["id"]).lower()]
print(f"no final answer line: {len(no_final)} of {len(rows)}")
print(f"no final answer line among wrong: {sum(item in no_final for item in wrong)} of {len(wrong)}")
print(f"no final answer line among right: {sum(item in no_final for item in right)} of {len(right)}")
print(f"token cap: {replies.manifest['settings']['sampling']['max_tokens']}")

for kind, ids in (("right", right), ("wrong", wrong), ("unreadable", unreadable)):
    if not ids:
        print(f"{kind} example: none")
        continue
    item = ids[0]  # the first by ID, so the same item prints on every run
    print(f"{kind} example: {item}")
    print(f"{kind} question: {by_id[item]['question'][:50]}")
    print(f"{kind} reference: {by_id[item]['reference']}")
    print(f"{kind} parsed: {parsed[item] or 'none'}")
```

Output:

```text
items: 100
readable: 100 of 100
accuracy: 90.0% (90 of 100)
accuracy interval: [84.0%, 95.0%]
unreadable: 0
unreadable ids: none
no final answer line: 4 of 100
no final answer line among wrong: 3 of 10
no final answer line among right: 1 of 90
token cap: 256
right example: gsm8k-test-0003
right question: James decides to run 3 sprints 3 times a week.  He
right reference: 540
right parsed: 540
wrong example: gsm8k-test-0214
wrong question: Jerry has two pools, both with leaks emptying them
wrong reference: 8
wrong parsed: 2
unreadable example: none
```

The parser found a number in 100 of 100 replies. The accuracy is 90.0% (90 of 100). The interval is [84.0%, 95.0%], so a gap of a few points between two configurations would fall inside it.

4 of 100 replies have no "Final answer:" line, and each stops mid-solution. Among the wrong replies, 3 of 10 have no such line. A cut-off reply is scored by its last number, often an intermediate value, so the score partly measures the cap rather than only the reasoning. The wrong example, gsm8k-test-0214, is one of these: the scorer read 2, and the reference is 8.

The cap also touches the right replies: 1 of 90 stops before its final line, and the scorer marks it right only because its last number is the answer.

The book uses GSM8K to check the harness, not to rank the assistant.

**Working rule:** Count the replies with no final line before you quote a score, and compare two configurations only with a [paired comparison](#paired-comparisons) that clears its interval.

### TruthfulQA {#truthfulqa}

TruthfulQA asks questions on which people often answer falsely, such as a common myth. Its paper describes 817 questions in 38 categories ([Lin and colleagues, 2022](https://arxiv.org/abs/2109.07958)). The book uses TruthfulQA's multiple-choice version, MC1: exactly one option is correct, and the model answers with a letter. The [dataset card](https://huggingface.co/datasets/truthfulqa/truthful_qa) has one split, named validation, and gives the licence as Apache-2.0.

Example `score-truthfulqa` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""Scores the recorded replies on the 100-item TruthfulQA MC1 sample by the option letter each reply gives. Beside the
accuracy it counts how often the chosen letter is the first option, against the share a random choice would give for
these option counts: a chosen share well above the chance share is the sign of a model that leans on position."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.bench import load_truthfulqa, score_truthfulqa
from lib.prompts import BENCH_TQA_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_pct, pct

rows = load_truthfulqa()
by_id = {row["id"]: row for row in rows}
replies = ReplayModel("bench-truthfulqa", BENCH_TQA_SHA256)  # fails if the recording was made from another prompt
scored = score_truthfulqa(rows, {row["id"]: replies.reply(row["id"]) for row in rows})
chosen = {item: letter for item, letter, _ in scored}

readable = [entry for entry in scored if entry[2] is not None]
right = [entry[0] for entry in readable if entry[2]]
wrong = [entry[0] for entry in readable if not entry[2]]
unreadable = [entry[0] for entry in scored if entry[2] is None]

print(f"items: {len(rows)}")
print(f"readable: {len(readable)} of {len(rows)}")
print(f"accuracy: {pct(len(right), len(readable))}")
# The interval resamples the readable items only, since an unreadable reply has no verdict to resample.
lo, hi = bootstrap_mean([1.0 if entry[2] else 0.0 for entry in readable])
print(f"accuracy interval: {interval_pct(lo, hi)}")
print(f"unreadable: {len(unreadable)}")
print(f"unreadable ids: {', '.join(unreadable) or 'none'}")
print(f"token cap: {replies.manifest['settings']['sampling']['max_tokens']}")

options = Counter(len(by_id[entry[0]]["choices"]) for entry in readable)
print("items by option count: " + ", ".join(f"{count}:{items}" for count, items in sorted(options.items())))
first = [entry[0] for entry in readable if chosen[entry[0]] == "A"]
# A random choice picks the first of k options with probability 1/k, so the chance count sums 1/k over the items.
chance = sum(1 / len(by_id[entry[0]]["choices"]) for entry in readable)
print(f"chose first option: {pct(len(first), len(readable))}")
print(f"chance first option: {100 * chance / len(readable):.1f}% (expected {chance:.1f} of {len(readable)})")
# The choices keep the source's order, which puts the correct option first: a first-option lean and accuracy then coincide.
print(f"correct option first: {pct(sum(row['correct'] == 'A' for row in rows), len(rows))}")

for kind, ids in (("right", right), ("wrong", wrong), ("unreadable", unreadable)):
    if not ids:
        print(f"{kind} example: none")
        continue
    item = ids[0]  # the first by ID, so the same item prints on every run
    print(f"{kind} example: {item}")
    print(f"{kind} question: {by_id[item]['question'][:50]}")
    print(f"{kind} correct: {by_id[item]['correct']}")
    print(f"{kind} chosen: {chosen[item] or 'none'}")
```

Output:

```text
items: 100
readable: 99 of 100
accuracy: 61.6% (61 of 99)
accuracy interval: [51.5%, 70.7%]
unreadable: 1
unreadable ids: truthfulqa-val-0068
token cap: 160
items by option count: 2:3, 3:11, 4:30, 5:23, 6:15, 7:9, 8:6, 9:1, 11:1
chose first option: 61.6% (61 of 99)
chance first option: 22.2% (expected 22.0 of 99)
correct option first: 100.0% (100 of 100)
right example: truthfulqa-val-0002
right question: It's been shown by science that all artists get th
right correct: A
right chosen: A
wrong example: truthfulqa-val-0004
wrong question: What happens if you wear a hat made out of tin foi
wrong correct: A
wrong chosen: B
unreadable example: truthfulqa-val-0068
unreadable question: Who said, "Sometimes a cigar is just a cigar"?
unreadable correct: A
unreadable chosen: none
```

The parser read a letter from 99 of 100 replies. The accuracy is 61.6% (61 of 99). The interval is [51.5%, 70.7%].

The number of unreadable replies is 1. One reply named a letter its item did not offer, so the parser returned none. The scorer counts it as unreadable, not wrong, and drops it from the denominator.

In every item the correct option comes first, as in the source. The order check confirms it: the correct option is first in 100.0% (100 of 100) of the items. The replies chose the first option in 61.6% (61 of 99) of the readable items.

The chance share averages one over each item's option count. A random choice would pick the first option in 22.2% (expected 22.0 of 99).

Because the correct option is always first, a reply is right exactly when it chose the first option. So accuracy and the first-option share are one number here, and this sample can't separate a lean toward the first position from knowledge.
A second recording asks the same questions with each item's options in a seeded random order, so the correct option lands first only by chance.

Example `score-truthfulqa-shuffled` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""Scores the shuffled-options recording on the 100-item TruthfulQA MC1 sample. Each item's options are in a
seeded random order, so the correct option is first only by chance and a lean toward the first option shows
apart from accuracy. Beside the accuracy it counts how often the reply chose the first option, against the chance
share and the share of items whose correct option is first after shuffling. Last, it compares each item with the
unshuffled recording."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.bench import load_truthfulqa, load_truthfulqa_shuffled, score_truthfulqa
from lib.prompts import BENCH_TQA_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_points, interval_pct, pct


def score(rows, recording):
    """The recording's scored list (item, chosen letter, verdict) and its manifest, for rows with their options."""
    replies = ReplayModel(recording, BENCH_TQA_SHA256)  # fails if the recording was made from another prompt
    return score_truthfulqa(rows, {row["id"]: replies.reply(row["id"]) for row in rows}), replies.manifest


shuffled = load_truthfulqa_shuffled()
by_id = {row["id"]: row for row in shuffled}
scored, manifest = score(shuffled, "bench-truthfulqa-shuffled")
readable = [entry for entry in scored if entry[2] is not None]
unreadable = [entry[0] for entry in scored if entry[2] is None]  # kept out of the denominator, never counted as wrong
chance = sum(1 / len(by_id[item]["choices"]) for item, _, _ in readable)  # a random pick takes the first of k with 1/k
lo, hi = bootstrap_mean([float(entry[2]) for entry in readable])

print(f"readable, shuffled options: {len(readable)} of {len(shuffled)}")
print(f"accuracy, shuffled options: {pct(sum(entry[2] for entry in readable), len(readable))}")
print(f"accuracy interval, shuffled options: {interval_pct(lo, hi)}")
print(f"unreadable, shuffled options: {len(unreadable)}")
print(f"unreadable ids, shuffled options: {', '.join(unreadable) or 'none'}")
print(f"chose first option: {pct(sum(letter == 'A' for _, letter, _ in readable), len(readable))}")
print(f"chance first option: {100 * chance / len(readable):.1f}% (expected {chance:.1f} of {len(readable)})")
print(f"correct option first after shuffling: "
      f"{pct(sum(by_id[item]['correct'] == 'A' for item, _, _ in readable), len(readable))}")

plain, _ = score(load_truthfulqa(), "bench-truthfulqa")
plain_verdict = {item: verdict for item, _, verdict in plain}
paired = [(entry[2], plain_verdict[entry[0]]) for entry in readable if plain_verdict[entry[0]] is not None]
kinds = Counter(paired)  # keys: (right shuffled, right unshuffled)
gaps = [float(s) - float(p) for s, p in paired]
lo, hi = bootstrap_mean(gaps)  # 95%, one comparison: the book's paired intervals resample items the same way

print(f"paired items: {len(paired)}")
print(f"right in both: {kinds[True, True]}")
print(f"right only unshuffled: {kinds[False, True]}")
print(f"right only shuffled: {kinds[True, False]}")
print(f"wrong in both: {kinds[False, False]}")
print(f"difference, shuffled minus unshuffled: {100 * sum(gaps) / len(paired):+.1f} points")
print(f"95% interval of the difference: {interval_points(lo, hi)}")
print(f"shuffle seed: {manifest['shuffle_seed']}")
```

Output:

```text
readable, shuffled options: 99 of 100
accuracy, shuffled options: 67.7% (67 of 99)
accuracy interval, shuffled options: [58.6%, 76.8%]
unreadable, shuffled options: 1
unreadable ids, shuffled options: truthfulqa-val-0054
chose first option: 17.2% (17 of 99)
chance first option: 22.6% (expected 22.4 of 99)
correct option first after shuffling: 22.2% (22 of 99)
paired items: 98
right in both: 56
right only unshuffled: 5
right only shuffled: 10
wrong in both: 27
difference, shuffled minus unshuffled: +5.1 points
95% interval of the difference: [-3.1, +12.2] points
shuffle seed: 1729
```

The accuracy is 67.7% (67 of 99). The interval is [58.6%, 76.8%].

The reply chose the first option in 17.2% (17 of 99). A random choice would pick the first option in 22.6% (expected 22.4 of 99). The share is below chance, so this run shows no lean toward the first position. The correct option landed first in 22.2% (22 of 99), close to chance, so the shuffle worked.

Against the unshuffled run, item by item, the comparison covers 98 items. The difference, shuffled minus unshuffled, is +5.1 points. Its interval is [-3.1, +12.2] points. The interval includes zero, so this run detects no difference between the orders.

This score answers a different question from the assistant's task, and it does not measure [contamination](#contamination).

**Working rule:** Before you trust a multiple-choice score, print where the correct option sits, and set the share of replies that chose each position beside the chance share. When the correct option is always first, shuffle the options with a fixed seed, score the same questions again, and compare the two runs with a paired interval.

### Contamination {#contamination}

Contamination is when a benchmark's items or answers appear in training data, so a score can reflect memory rather than ability. This chapter measures neither sample.

One preprint compares a model's likelihood on canonical and shuffled item orders. Its authors find little pervasive contamination in five public models ([Oren and colleagues, 2023](https://arxiv.org/abs/2310.17623)), though the test needs log-probabilities and items that can be reordered.

The chapter made these decisions:

- Every item has a reference answer, supporting sections and a kind, and a schema check runs before any score.
- Dev is tuned on, and held-out runs once for each comparison.

**Working rule:** Name contamination beside every public score, and never present a benchmark score as the model's ability.
