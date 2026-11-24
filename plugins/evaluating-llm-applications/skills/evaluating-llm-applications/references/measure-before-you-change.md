---
title: "Evaluating LLM Applications"
chapter: "Measure an assistant before you change it"
chapter_id: measure-before-you-change
book: evaluating-llm-applications
edition: 2026.11.7
verified: 2026-11-22
edition_code: WCKB-Y7EK
canonical: https://rollingedition.com/evaluating-llm-applications/measure-before-you-change
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Measure an assistant before you change it,” chapter 1 of Evaluating LLM Applications, Edition 2026.11.7, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/measure-before-you-change. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Measure an assistant before you change it

By the end of this chapter you can measure a documentation assistant with a fixed set of questions, read the result with its interval, and say when twenty questions are too few to tell two prompts apart.

The assistant in this book answers questions about sablefile, a command-line tool that keeps a project's generated files in step with the templates they come from. Users ask how to run a command or what a setting does, and the assistant answers from the tool's documentation, citing the section behind each statement. Suppose someone on the team wants a different prompt. They try it on three questions, the answers look better, and they ship it. Three questions can't show whether the change helped. Nobody can say what the assistant did before the change either, because nothing was written down.

So the first thing to build is a measurement: a set of questions with the answers they should get, a way to run the assistant on them the same way each time, and a number that comes with its size. Changes come after that. This chapter builds the measurement in its simplest form, and it ends by showing where that form stops.

## The tool and its docs {#the-tool-and-its-docs}

An evaluation is only as steady as the thing it measures. The sablefile docs come in three versions, 1.0, 1.1 and 2.0, and they disagree in places. An answer that is right for one version can be wrong for another, so every question has to name its version before anything else about it is settled.

Start with the docs. Load the three versions, count the sections in each, and count the section IDs that all three share.

Example `list-the-docs` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.7:

```python
"""Loads the three doc versions and prints each one's section count, and how many section IDs all three share.

The shared IDs are the sections whose concept keeps one ID across versions (plan section 2.2)."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.docs import load_sections, versions

sections = load_sections()  # every version, sorted by version and section ID
all_versions = versions()  # the version labels present, sorted
for version in all_versions:
    print(f"sections in version {version}: {sum(1 for s in sections if s.version == version)}")

ids = {version: {s.section_id for s in sections if s.version == version} for version in all_versions}
shared = set.intersection(*ids.values())  # IDs present in every version
print(f"section IDs in all {len(all_versions)} versions: {len(shared)}")
print(f"section IDs in 2.0 but in neither 1.0 nor 1.1: {len(ids['2.0'] - ids['1.0'] - ids['1.1'])}")
```

Output:

```text
sections in version 1.0: 35
sections in version 1.1: 36
sections in version 2.0: 40
section IDs in all 3 versions: 35
section IDs in 2.0 but in neither 1.0 nor 1.1: 4
```

The output opens with the section counts: 35 in 1.0, 36 in 1.1, and 40 in 2.0.

Most sections keep their IDs across versions, since 35 IDs appear in all three. The last line matters most for what follows. 4 IDs exist only in 2.0, so an assistant that answers from the older pages has nothing to cite for them.

The versions also differ in what the tool does, and the difference that matters here is in `sync`, the command that writes the generated files. The 1.1 docs say that `sync` with no flags writes the files and records each one in `sablefile.lock`, the lock file in the project root. The 2.0 docs say that `sync` with no flag prints a plan and writes nothing, that `--apply` writes the files, and that the lock file lives at `.sablefile/lock.json`. A question about `sync` has one right answer for 1.1 and another for 2.0. An assistant that reads the wrong version's page sounds sure of itself and is wrong.

This book measures answers. Retrieval ranking, tracing, cost, latency, attacks and agents' task sets belong to other books, named where they come up.

**Working rule:** Write the version into every question, and let that version's own docs be the only source for its answer. When two versions use the same wording and give different answers, make them two items, one for each version. Never let the newest version's page stand in for an older one.

## The twenty items {#the-twenty-items}

A test set is a list of questions, each with the answer it should get. Twenty items is deliberately small. You can read each one, check its expected answer against the docs, and say why it is there. A set nobody reads can't tell you what it measures.

The items fall into four kinds. Answerable items have their answer on the page. Unanswerable items ask about something the docs don't cover, and the right reply is the decline. Version-dependent items have an answer that changes from one version to the next, and several of them have a twin: the same question asked about another version. Ambiguous items could mean two things, and their reference answer covers both readings.

Each item is printed in ID order, with its version, kind, twin and whether it was planted.

Example `twenty-questions` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Prints the twenty chapter items in id order: version, kind, planted flag and question, then the counts by kind.

The counts are the set's make-up that the chapter describes (plan section 3.4)."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.answers import chapter_items

items = chapter_items()  # sorted by id
for item in items:
    twin = item.twin_of if item.twin_of else "none"
    planted = f"planted ({item.planted_why})" if item.planted else "not planted"
    print(f"{item.id} | version {item.version} | {item.kind} | {planted} | twin {twin} | {item.question}")

kinds = Counter(item.kind for item in items)
for kind in ("answerable", "unanswerable", "version-dependent", "ambiguous"):
    print(f"items of kind {kind}: {kinds[kind]}")
print(f"planted items: {sum(1 for item in items if item.planted)}")
print(f"items in the dev split: {sum(1 for item in items if item.split == 'dev')}")
```

Output:

```text
q-0001 | version 1.1 | version-dependent | not planted | twin q-0002 | In sablefile 1.1, if I run sync with no flags, are the target files written straight away?
q-0002 | version 2.0 | version-dependent | not planted | twin q-0001 | In sablefile 2.0, if I run sync with no flags, are the target files written?
q-0003 | version 1.0 | version-dependent | planted (version-swap) | twin q-0004 | In sablefile 1.0, is ${project} the right way to insert the project name into a template?
q-0004 | version 2.0 | version-dependent | not planted | twin q-0003 | In sablefile 2.0, is ${project} the right way to insert the project name into a template?
q-0005 | version 2.0 | answerable | planted (near-miss-term) | twin none | Does sablefile 2.0 still read sablefile.lock in my project root?
q-0006 | version 2.0 | answerable | not planted | twin none | Is there a way to make check exit with status 0 even when a file has drifted in 2.0?
q-0007 | version 1.1 | answerable | not planted | twin none | In 1.1, will an ignore entry of docs/**/*.tmp catch a file two folders down, like docs/x/y/a.tmp?
q-0008 | version 2.0 | answerable | not planted | twin none | In 2.0, is there a way to re-include something that an earlier ignore line had excluded?
q-0009 | version 1.0 | answerable | not planted | twin none | What does one line of the 1.0 lock file hold?
q-0010 | version 2.0 | answerable | not planted | twin none | Will syncing the same content twice in 2.0 produce a different lock file each time?
q-0011 | version 1.1 | answerable | not planted | twin none | How many times does 1.1 retry a remote template fetch that keeps failing, and can a flag change that?
q-0012 | version 2.0 | answerable | not planted | twin none | I want sync to retry a slow remote template only twice in 2.0. What do I pass?
q-0013 | version 1.0 | answerable | not planted | twin none | In 1.0, which table in sablefile.toml holds the values a placeholder can name?
q-0014 | version 1.1 | answerable | not planted | twin none | What does sablefile init put into a new sablefile.toml in 1.1?
q-0015 | version 1.0 | unanswerable | planted (false-premise) | twin none | In sablefile 1.0, what does the --dry-run flag on sync print?
q-0016 | version 2.0 | unanswerable | not planted | twin none | Does sablefile 2.0 run on Windows?
q-0017 | version 2.0 | unanswerable | not planted | twin none | How fast is sablefile check on a project with several thousand generated files?
q-0018 | version 1.1 | unanswerable | not planted | twin none | Can sablefile 1.1 fetch a remote template from a private URL that needs a login token?
q-0019 | version 2.0 | ambiguous | planted (ambiguous-target) | twin none | If I edit the file and then run check, will it fail?
q-0020 | version 2.0 | ambiguous | not planted | twin none | Does sync change the lock file?
items of kind answerable: 10
items of kind unanswerable: 4
items of kind version-dependent: 4
items of kind ambiguous: 2
planted items: 4
items in the dev split: 20
```

The last lines give the make-up of the set by kind, and answerable items are the largest group. 4 items are planted. A planted item was written to catch one particular mistake, and the set labels it, so a failure on that item can be read against its trap.

Each trap is simple. `q-0003` asks whether `${project}` is the right placeholder in 1.0, where the syntax is `{{project}}`. Its twin, `q-0004`, asks the same about 2.0, where `${project}` is right. `q-0005` asks whether 2.0 still reads `sablefile.lock` in the project root, which uses the 1.x file name for a version where that name matters only for migration. `q-0015` asks what the `--dry-run` flag does in 1.0, and the 1.0 docs name no such flag. `q-0019` asks whether a file fails a check after you edit it, without saying which file, so it has two readings.

**Working rule:** Write each item with its version, its kind and its expected answer before you run the assistant, and label any item written to catch a specific mistake. Keep the set small enough to read in one sitting, and never change an expected answer to fit what the assistant said.

## Retrieve, then answer {#retrieve-then-answer}

The assistant doesn't read all the docs for every question. For each question it takes the three sections most likely to hold the answer, from the index of the version the question names, and answers from those three alone. A wrong answer can therefore come from two places: the right section was never retrieved, or the model misread the section it was given. A measurement that can't tell these apart can't say what to fix.

The index is built with BM25, which scores each section by the words it shares with the question, giving rarer words more weight and long sections less. The scoring runs through bm25s at 0.3.16. Take one question: whether an ignore entry such as `docs/**/*.tmp` catches a file two folders down in 1.1. Its output shows the words the index keeps from the question, and the top three sections, ordered by score and then by section ID.

Example `retrieve-top-sections` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Shows BM25 retrieval for one question (q-0007, version 1.1): the words kept, then the top three sections.

The sections come from the version's own index, ranked by score and then by section ID, so a tie has one order.
The tokeniser drops one-letter words, so the `3` of `3.5mm` is lost and only `5mm` is matched."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import bm25s

from lib.docs import load_sections
from lib.retrieval import Retriever
from lib.testset import load_items

item = next(item for item in load_items() if item.id == "q-0007")
print(f"question {item.id} (version {item.version}): {item.question}")

# The words the index actually matches on: the same tokeniser, stopwords and token pattern as lib.retrieval.
kept = bm25s.tokenize([item.question], stopwords="en", return_ids=False, show_progress=False)[0]
print(f"words kept for matching: {' '.join(kept)}")
dropped = bm25s.tokenize(["a 3.5mm jack"], stopwords="en", return_ids=False, show_progress=False)[0]
print(f"words kept from the text 'a 3.5mm jack': {' '.join(dropped)}")

hits = Retriever(load_sections(item.version)).retrieve(item.question, 3)  # top 3 of the version's index
for rank, hit in enumerate(hits, start=1):
    print(f"rank {rank}: {hit.section_id} | score {hit.score:.3f}")
```

Output:

```text
question q-0007 (version 1.1): In 1.1, will an ignore entry of docs/**/*.tmp catch a file two folders down, like docs/x/y/a.tmp?
words kept for matching: ignore entry docs tmp catch file two folders down like docs tmp
words kept from the text 'a 3.5mm jack': 5mm jack
rank 1: ignore-recursive | score 9.156
rank 2: sync-create-dirs | score 3.386
rank 3: ignore-syntax | score 3.348
```

Read the two lines of kept words before the ranking. The tokeniser drops every token of one character. The `a` in the question goes, and so do both `1`s of `1.1`, so the version number never reaches the index. That does no harm here, because each question is searched only in the index of its own version. The same rule takes the `3` out of `3.5mm`: what is left of `a 3.5mm jack` is `5mm jack`, so a question about a 3.5 mm jack can match only on `5mm`. Neither loss raises an error, and the second one changes what the index can find.

The ranking puts `ignore-recursive` first, the section on recursive ignore entries, and the next two are the section on creating folders and the one on ignore syntax. Ties are broken by section ID, so the same question gives the same three sections on every run.

**Working rule:** Check retrieval before you check the answer. For each item, record the sections the assistant was given next to its reply. A wrong reply that lacks the right section is a retrieval problem, and a wrong reply that had the right section is a problem with the prompt or the model. Keep the wording of questions plain, because a tokeniser that drops one-character tokens will lose a measurement or a version number.

## Replay the answers {#replay-the-answers}

A model's reply to the same question can change with its runtime, its settings and the hardware it runs on. If every measurement calls the model again, each one measures something slightly different, and a change in the number might be noise. So the book records each reply once, from a pinned open model, and replays the recording. A replay returns the same text every time.

The recording is a folder of replies, one per item. It was made with a 4-bit build of Qwen3-4B-Instruct-2507, an open model pinned to one file and one revision, run at temperature zero on a CPU. It holds a reply for every item in the full set, and this chapter reads twenty of them by ID. Replay one of them: the reply to `q-0006`, which asks whether `check` can exit with status 0 when a file has drifted in 2.0.

Example `replay-one-answer` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Replays the recorded baseline reply to q-0006 and parses it: the sections it was given, the reply, its citations.

Nothing is generated here: the reply is the recorded text, read back as the same string."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.contract import format_problems
from lib.prompts import P1_SHA256, P1_SYSTEM

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)  # the prompt hash must match the manifest
item = next(item for item in chapter_items() if item.id == "q-0006")
print(f"question {item.id} (version {item.version}, {item.kind}): {item.question}")
for rank, section in enumerate(assistant.sections(item), start=1):  # the top 3, in rank order
    print(f"section in context, rank {rank}: {section.section_id}")

reply = assistant.reply(item)
print("recorded reply:")
print(reply.text)
print(f"citations, in order: {' '.join(reply.citations)}")
print(f"format problems: {', '.join(format_problems(reply, context_ids=assistant.context_ids(item), expect_decline=False)) or 'none'}")
# A reply to an answerable item must answer and cite; this is the one fact the prose relies on here.
assert reply.citations and not reply.declined, "q-0006 should be answered, with at least one citation"
```

Output:

```text
question q-0006 (version 2.0, answerable): Is there a way to make check exit with status 0 even when a file has drifted in 2.0?
section in context, rank 1: check-exit-status
section in context, rank 2: no-fail-flag
section in context, rank 3: quickstart-check
recorded reply:
Yes, there is a way to make `check` exit with status 0 even when a file has drifted in 2.0. Use the `--no-fail` flag with `sablefile check`. This flag ensures that the check exits with status 0 even when files have drifted, without changing which files are reported. [sec:no-fail-flag]
citations, in order: no-fail-flag
format problems: none
```

The output lists the three sections the assistant was given, in rank order, and then prints the reply exactly as it was recorded. The reply says yes, and it cites `no-fail-flag`, which was among the three. Check the citation against that list. The reply cites a section it was given, so it didn't reach outside its context. An assert also requires the reply to be an answer with at least one citation, since a decline on this answerable item would be an error.

To put a live model in place of the recording, pass `live=True` to `Assistant`. That loads the pinned Qwen3-0.6B on the CPU and answers each question as it's asked. It is a smaller model than the 4B build the recording was made with, so its live replies, and any rate built on them, will differ from the recorded ones. This book quotes no live replies. Its numbers come from the recording, so you can check each one against a file.

**Working rule:** Replay for every comparison. Record again only when the model, the prompt or the sections the assistant sees have changed, and note in the recording what changed. Each recording names its prompt by hash, and the example checks that hash against the recording's manifest, so one recording can't stand in for a different prompt.

## Two code checks {#two-code-checks}

Some errors need no judge. A citation to a section that wasn't in the prompt, or a decline that also gives an answer, can be found by reading the reply's text. Checks in code cost nothing to run and give the same result each time, so the book runs both of them before any model is asked to judge a reply.

### Citations {#citations-in-code}

The assistant must cite every statement with the citation form, a section ID after `sec:` in square brackets, such as `[sec:no-fail-flag]`, and it may cite only the IDs it was given. A citation can fail in two ways. The ID may not exist at all, or it may exist in another version, which is the mistake the version-swap items are written to provoke. The check calls a citation to any section that was not in the prompt `unknown-section`, whichever way it went wrong. It also flags an answer that has no citation.

The citation and format checks run over the twenty baseline replies, and the output counts each kind of failure.

Example `check-citations` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Runs the citation and format checks on the baseline replies to the twenty chapter items, and counts each problem.

A citation is a problem when its section was not in the item's prompt, which covers a section of another version."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.contract import PROBLEMS, format_problems, parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256, P1_SYSTEM
from lib.stats import pct

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)
items = chapter_items()
counts = {name: 0 for name in PROBLEMS}  # items with each problem, by its fixed name
items_with_problems = 0
answered = 0
answered_uncited = 0
citations = 0
citations_outside = 0  # cited IDs that were not in the item's prompt
for item in items:
    reply = assistant.reply(item)
    problems = format_problems(reply, context_ids=assistant.context_ids(item), expect_decline=item.kind == "unanswerable")
    items_with_problems += bool(problems)
    for name in problems:
        counts[name] += 1
    if not reply.declined and reply.text:
        answered += 1
        answered_uncited += not reply.citations
    citations += len(reply.citations)
    citations_outside += sum(1 for cid in reply.citations if cid not in assistant.context_ids(item))
assert citations_outside == 0, "every citation must point at a section that was in its item's prompt"
# A zero rate shows nothing unless the check can fire: a 1.1 section cited for a 2.0 item must be flagged as unknown.
planted_item = next(item for item in items if item.version == "2.0")
planted = sorted(section_ids_by_version()["1.1"] - assistant.context_ids(planted_item))[0]
planted_problems = format_problems(parse_reply(f"Yes. [sec:{planted}]"), context_ids=assistant.context_ids(planted_item), expect_decline=False)
assert "unknown-section" in planted_problems, "the check must fire on a planted bad citation"

print(f"items: {len(items)}")
print(f"items with a format problem: {pct(items_with_problems, len(items))}")
for name in sorted(counts):  # sorted by problem name
    print(f"items with problem {name}: {counts[name]}")
print(f"answered items: {answered}")
print(f"answered items with no citation: {pct(answered_uncited, answered)}")
print(f"citations: {citations}")
print(f"citations to a section not in the prompt: {pct(citations_outside, citations)}")
```

Output:

```text
items: 20
items with a format problem: 0.0% (0 of 20)
items with problem answered-declined-expected: 0
items with problem declined-with-text: 0
items with problem empty: 0
items with problem no-citation: 0
items with problem unknown-section: 0
answered items: 15
answered items with no citation: 0.0% (0 of 15)
citations: 16
citations to a section not in the prompt: 0.0% (0 of 16)
```

The baseline gave 16 citations in total, and each one points at a section it was given. The output puts rates on that: citations to a section outside the prompt come to 0.0% (0 of 16), and answered items with no citation come to 0.0% (0 of 15).

**Working rule:** Run the citation check on every reply, and report its rates apart from the answer rate, since the two count different mistakes. A rate of zero is only a result if the check could have found a problem, so keep a fixture reply that cites outside its prompt, and run the check on it, to show the check still fires.

### Declines {#declines-in-code}

When the docs don't answer a question, the assistant must reply with the decline phrase, "The docs don't say.", and nothing else. When the docs do answer, it must not use that sentence. These are two different errors, so each gets its own rate. A false refusal is an answerable item declined, and a false answer is an unanswerable item answered. Version-dependent and ambiguous items are left out of both rates. A version-dependent item has a rate of its own, version-correctness, which [chapter 9](grounded-answers) builds. An ambiguous item is judged by the pass rate alone, since a reply's text alone can't show which version or which reading was meant.

Both decline errors are counted over the baseline's replies.

Example `check-declines` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Counts the two decline errors over the baseline replies: answerable items declined, and unanswerable items answered.

Version-dependent and ambiguous items are left out of both rates: a version-dependent item is scored by its own rate,
version-correctness, and an ambiguous item has no rate yet. The last lines name any excluded item the baseline declined."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.prompts import P1_SHA256, P1_SYSTEM
from lib.stats import pct

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)
items = chapter_items()
answerable = [item for item in items if item.kind == "answerable"]
unanswerable = [item for item in items if item.kind == "unanswerable"]

false_refusals = [item.id for item in answerable if assistant.reply(item).declined]  # already in id order
false_answers = [item.id for item in unanswerable if not assistant.reply(item).declined]
print(f"answerable items: {len(answerable)}")
print(f"false refusal rate (answerable items declined): {pct(len(false_refusals), len(answerable))}")
for item_id in false_refusals:
    print(f"false refusal: {item_id}")
print(f"unanswerable items: {len(unanswerable)}")
print(f"false answer rate (unanswerable items answered): {pct(len(false_answers), len(unanswerable))}")
for item_id in false_answers:
    print(f"false answer: {item_id}")
print(f"items not counted here (version-dependent and ambiguous): {len(items) - len(answerable) - len(unanswerable)}")
excluded = [item for item in items if item.kind in ("version-dependent", "ambiguous")]
declined_excluded = [item.id for item in excluded if assistant.reply(item).declined]  # the decline is not counted
print(f"declined, not counted here: {', '.join(declined_excluded) or 'none'}")
```

Output:

```text
answerable items: 10
false refusal rate (answerable items declined): 0.0% (0 of 10)
unanswerable items: 4
false answer rate (unanswerable items answered): 0.0% (0 of 4)
items not counted here (version-dependent and ambiguous): 6
declined, not counted here: q-0004
```

Among the answerable and unanswerable items, the baseline makes neither error. The false refusal rate is 0.0% (0 of 10) of the 10 answerable items. The false answer rate is 0.0% (0 of 4) of the 4 unanswerable ones, so every unanswerable item got the decline, `q-0015` among them.

The rates leave out 6 items, and the last line names the one of them that the baseline declined: q-0004. Item `q-0004` asks whether `${project}` is the right placeholder in 2.0, where it is. The baseline replied with the decline phrase, but the 2.0 docs answer it, in the `placeholders` section, so the decline is a wrong reply. The rate above doesn't count it as a false refusal, because that rate covers answerable items only. Version-correctness does count it as a miss.

**Working rule:** Keep the two decline rates apart, and leave version-dependent and ambiguous items out of both. A reply counts as a correct decline only when it is the decline phrase and nothing else, so a reply that gives the sentence and then an answer counts as the error it is. Read each false refusal by hand before you change the prompt, since one of them may point at a real gap in the docs. Read each decline on a version-dependent item too, since the rate doesn't count those.

## One judge {#one-judge}

Citations and declines check the shape of a reply. They can't check whether the reply is right, and that's the question the team cares about. For that, the book uses a judge: a model that grades a reply, here by reading the question, a written reference answer and the assistant's reply, and returning PASS or [FAIL](#verdict-first). The judge here is Qwen3-4B-Instruct-2507, the same model that wrote the replies. A judge and an assistant that are one model can share blind spots, and then the judge misses the errors the assistant makes for the same reason. This book can't test for that with this setup. What it does instead is check the same model, under a calibration rubric, against public human ratings, and say what carrying those rates to this judge assumes, in [chapter 6](calibrate-the-judge).

The judge's rules are short, and they're worth reading in full. A reply is correct only if it says what the reference says. Other words are fine, and so is extra detail that doesn't contradict the reference. A reply that says something the reference doesn't support, or contradicts it, fails. If the reference has more than one reading, the reply must answer every one of them, and a partial answer fails. If the reference is "none", the docs don't answer, and the only correct reply is the decline. A reply that gives an answer and also the decline phrase fails. The judge writes its verdict on the first line and a short reason after it. The prompt asks for one sentence, and the judge doesn't always stop there.

Here is the judge's verdict on `q-0005`, the near miss. The assistant's reply to it says that 2.0 does not read `sablefile.lock`, and points vaguely at migration.

Example `judge-one-answer` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Reads the reference-guided judge's verdict on the baseline reply to q-0005, a planted near-miss item, from its recording.

The judge sees the question, the written reference and the reply; the first line of its reply is the verdict."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.contract import parse_verdict
from lib.prompts import P1_SHA256, P1_SYSTEM, REF_SHA256
from lib.replay import ReplayModel

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)
item = next(item for item in chapter_items() if item.id == "q-0005")
print(f"question {item.id} (version {item.version}, {item.kind}, planted: {item.planted_why}): {item.question}")
print(f"reference answer: {item.reference_answer}")
reply = assistant.reply(item)
print(f"assistant reply: {reply.text}")

judge = ReplayModel("judge-answers-baseline", REF_SHA256)  # the prompt hash must match the judge's manifest
raw = judge.reply(item.id, 0)
verdict = parse_verdict(raw)
assert verdict is not None, "the judge's first line must be a verdict"
print(f"judge verdict: {verdict}")
reason = [line.strip() for line in raw.splitlines() if line.strip()][1:]  # the line after the verdict
print(f"judge reason: {reason[0] if reason else 'none'}")
```

Output:

```text
question q-0005 (version 2.0, answerable, planted: near-miss-term): Does sablefile 2.0 still read sablefile.lock in my project root?
reference answer: Only as a fallback. If the new file is missing and an old sablefile.lock is present, a 2.0 command reads the old file but warns you about it. Once the new file exists, 2.0 reads only that one, and sablefile never deletes the old file.
assistant reply: No, sablefile 2.0 does not read `sablefile.lock` in the project root. Version 2.0 moves the lock file to a new place. The first 2.0 command that reads an older lock file handles it as described in lock-migration. [sec:install-upgrade]
judge verdict: FAIL
judge reason: The response incorrectly states that sablefile 2.0 "does not read `sablefile.lock`" and that it "moves the lock file to a new place," which contradicts the reference answer that says sablefile 2.0 reads the old lock file as a fallback and only reads the new file once it exists. The reference explicitly states that it reads the old file as a fallback and warns users, not that it moves or stops reading it.
```

The reference answer says something different: 2.0 reads the old file only as a fallback, when no new file exists, and it warns you when it does. The judge's verdict is FAIL, and its reason says the reply contradicts the reference. The 2.0 migration section of the docs says what the reference says, so on this item the judge is right. One correct verdict doesn't show that the judge is reliable, though.

That is why the judge needs checking against people. A judge that agrees with your own labels is not thereby calibrated. Shankar and colleagues' [*Who Validates the Validators?*](https://arxiv.org/abs/2404.12272) (2024) is a study of nine participants, and it found that people refine their grading criteria while they grade outputs, so the criteria they settle on change as they read more outputs. A rubric written once can drift from what its graders come to mean. [Chapter 5](a-judge-with-a-rubric) says how to write one down, and that is worth doing for a reason of its own: a written rubric is what a second reader can check a verdict against, and what later verdicts can be compared with. The check against human ratings is in [chapter 6](calibrate-the-judge).

**Working rule:** Give the judge a written reference for every item, and read its FAIL verdicts as closely as its PASS verdicts before you trust a rate built on them. Don't count agreement with your own labels as calibration. Until a judge has been checked against human ratings, report its rate as the judge's rate, not as a measure of the assistant's quality.

## A pass rate and its interval {#a-pass-rate-and-its-interval}

A pass rate is a count divided by a denominator, and the denominator decides what the rate means. The same rate on a much larger set is a different claim, and a set of twenty moves a lot when one item changes. Here the denominator is every item in the set, and a correct decline counts as a pass.

```
pass rate = passed items / items
```

An interval answers a different question from the pass rate: how far would the rate move if the set had been another set of as many items, drawn the same way? The method is a percentile bootstrap. The bootstrap itself is Efron's: his 1979 paper [*Bootstrap Methods: Another Look at the Jackknife*](https://doi.org/10.1214/aos/1176344552), in the *Annals of Statistics*, set out resampling as a way to estimate how much a statistic varies. The percentile bootstrap is the simplest interval built on resampling, the middle 95% of the resampled rates, or another share when a different level is chosen. The procedure draws items from the set with replacement, without regard to kind, so one draw can hold any mix of kinds. It computes the pass rate of each draw, and repeats the draws many times. The interval shows how much twenty items could say.

Compute the rate and its interval for the baseline, then break the rate down by kind.

Example `pass-rate-interval` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""The baseline's pass rate over the twenty chapter items, judged by the reference-guided judge, with its 95% interval.

Every item is in the denominator, and a correct decline counts as a pass. The interval resamples items."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import chapter_items
from lib.judging import passed, verdicts
from lib.stats import bootstrap_mean, interval_pct, pct

items = chapter_items()
found = verdicts("judge-answers-baseline", [item.id for item in items])  # keyed in sorted id order
scores = passed(found)  # 1.0 for PASS, 0.0 for FAIL, in the same order
print(f"items: {len(items)}")
print(f"pass rate: {pct(int(scores.sum()), len(items))}")
lo, hi = bootstrap_mean(scores)  # level 0.95 for one comparison; seed SEED, 2,000 resamples
print(f"95% interval of the pass rate: {interval_pct(lo, hi)}")

kind_of = {item.id: item.kind for item in items}
for kind in ("answerable", "unanswerable", "version-dependent", "ambiguous"):
    ids = [item_id for item_id in found if kind_of[item_id] == kind]
    passes = sum(1 for item_id in ids if found[item_id] == "PASS")
    print(f"pass rate, {kind}: {pct(passes, len(ids))}")
```

Output:

```text
items: 20
pass rate: 85.0% (17 of 20)
95% interval of the pass rate: [70.0%, 100.0%]
pass rate, answerable: 90.0% (9 of 10)
pass rate, unanswerable: 100.0% (4 of 4)
pass rate, version-dependent: 75.0% (3 of 4)
pass rate, ambiguous: 50.0% (1 of 2)
```

The baseline's pass rate is 85.0% (17 of 20). Its 95% interval is [70.0%, 100.0%]. The interval sits the same distance either side of the rate. Its upper end sits at the ceiling for any rate. It reaches the ceiling because more than 2.5% of the draws contain no failing item, so the top of the middle 95% is that ceiling. That means the interval can't rule out an assistant that never fails, which is what the single number hides.

Answerable items pass at 90.0% (9 of 10), unanswerable items at 100.0% (4 of 4), version-dependent items at 75.0% (3 of 4), and ambiguous items at 50.0% (1 of 2). The three failures fall in three different kinds. The one answerable failure is `q-0005`, read above. The one version-dependent failure is the decline on `q-0004`, read above. The one ambiguous failure is `q-0019`, which the judge fails under the baseline's reply, as the example in the next section shows.

Only the answerable kind has more than a few items: 10 of them. Each other kind holds 4 items or fewer, so their lines are notes about a few items, not results.

The interval covers only the spread that comes from drawing items. It says nothing about whether the twenty items represent the questions real users ask, and no interval can say that. [Chapter 3](build-the-test-set) covers what a set must contain before a score on it means anything, and why this one is written from the docs rather than sampled from users.

**Working rule:** Report every pass rate with its denominator, its interval and its rate for each kind of item. Treat a kind with only a few items as a note, not a result, and say how many items it rests on.

## Two prompts {#two-prompts}

The team's proposed prompt is the change to measure. P1 is the baseline prompt. P2 keeps the same ground rules and changes the form of the reply: it asks the model to quote first the sentence its answer relies on, then give the answer, with the citation on each line. The question is whether the quote helps. Two pass rates over different items mostly measure the items, so the comparison has to pass the same items through both prompts. Each item then gets two verdicts, and the difference is taken item by item. That's a [paired comparison](#paired-comparisons).

Both prompts run over the same twenty items, and the output reports the difference with its interval.

Example `compare-two-prompts` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Compares the baseline prompt (P1) with prompt-b (P2) on the twenty chapter items: each pass rate, the paired difference, its interval and n.

The word 'better' is used only when the whole interval is above zero, and 'worse' only when it is below zero. A difference
whose interval includes zero is reported as no difference detected."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import chapter_items
from lib.judging import paired
from lib.stats import interval_points, pct

result = paired("judge-answers-baseline", "judge-answers-prompt-b", [item.id for item in chapter_items()])
first, second = result.first, result.second  # 1.0 or 0.0 per item, in id order
print(f"P1 (baseline) pass rate: {pct(int(first.sum()), result.n)}")
print(f"P2 (prompt-b) pass rate: {pct(int(second.sum()), result.n)}")
print(f"items that P2 passes and P1 fails: {int(((second == 1) & (first == 0)).sum())}")
print(f"items that P1 passes and P2 fails: {int(((second == 0) & (first == 1)).sum())}")
print(f"paired items (n): {result.n}")
print(f"difference, P2 minus P1: {100 * result.difference:+.1f} points")
print(f"95% interval of the difference: {interval_points(result.diff_lo, result.diff_hi)}")
if result.diff_lo > 0:
    reading = f"P2 is better at n = {result.n}"
elif result.diff_hi < 0:
    reading = f"P2 is worse at n = {result.n}"
else:
    reading = f"no difference detected at n = {result.n}"
print(f"reading: {reading}")
# The two prompts tie: the same number of items pass under each, so the pass rates and the reading say the same thing.
assert int(first.sum()) == int(second.sum()), "the two prompts must tie: the same pass count under each"
```

Output:

```text
P1 (baseline) pass rate: 85.0% (17 of 20)
P2 (prompt-b) pass rate: 85.0% (17 of 20)
items that P2 passes and P1 fails: 1
items that P1 passes and P2 fails: 1
paired items (n): 20
difference, P2 minus P1: +0.0 points
95% interval of the difference: [-15.0, +15.0] points
reading: no difference detected at n = 20
```

On this set the two prompts tie. P1 passes 85.0% (17 of 20) of the items, and P2 passes 85.0% (17 of 20).

The paired view shows what sits under the tie. P2 passes 1 item that P1 fails, and P1 passes 1 item that P2 fails. These are the judge's verdicts, not facts about the prompts. The first is `q-0019`, and the judge's PASS on it breaks the judge's own rule 3. The difference, P2 minus P1, is +0.0 points, and its interval is [-15.0, +15.0] points. The interval includes zero, so at this size the example reports [no difference detected](#paired-comparisons).

Here the judge's verdicts on `q-0019` are read under both prompts, and the rule the PASS breaks is printed beside them.

Example `judge-gets-one-wrong` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Shows one judge verdict that breaks the judge's own rule: on q-0019, the judge passes P2's reply, which answers only one of the
two readings in the reference. The rule it breaks is rule 3 of the judge's prompt, printed below from that prompt.

The hand verdict is a person's reading, written into this file. It is printed beside the judge's verdict and is the only
number here that is not a recorded one; the count of passes with it is taken from the judge's own verdicts."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.judging import verdicts
from lib.prompts import P1_SHA256, P1_SYSTEM, P2_SHA256, P2_SYSTEM, REF_SYSTEM
from lib.replay import ReplayModel

ITEM_ID = "q-0019"
HAND = {"q-0019": "FAIL"}  # read by hand against rule 3: the reply answers reading 1 and not reading 2

item = next(item for item in chapter_items() if item.id == ITEM_ID)
print(f"question {item.id} (version {item.version}, {item.kind}, planted: {item.planted_why}): {item.question}")
print(f"reference answer: {item.reference_answer}")
print(f"P2 reply: {Assistant('assistant-prompt-b', P2_SYSTEM, P2_SHA256).reply(item).text}")

raw = ReplayModel("judge-answers-prompt-b", None).reply(item.id, 0)  # the judge's recorded reply to P2's answer
print(f"judge verdict on P2's reply: {verdicts('judge-answers-prompt-b', [item.id])[item.id]}")
reason = [line.strip() for line in raw.splitlines() if line.strip()][1:]  # the line after the verdict
print(f"judge reason: {reason[0] if reason else 'none'}")
print(f"judge verdict on P1's reply to the same item: {verdicts('judge-answers-baseline', [item.id])[item.id]}")
print(f"hand verdict on P2's reply, under rule 3: {HAND[item.id]}")
rule_3 = next(line for line in REF_SYSTEM.splitlines() if line.startswith("3. "))
print(f"rule it breaks: {rule_3}")

ids = [item.id for item in chapter_items()]
judged = verdicts("judge-answers-prompt-b", ids)
passes = sum(verdict == "PASS" for verdict in judged.values())
by_hand = passes - sum(1 for item_id in HAND if judged[item_id] == "PASS" and HAND[item_id] == "FAIL")
print(f"P2 passes, as judged: {passes} of {len(ids)}")
print(f"P2 passes, with {ITEM_ID} read by hand: {by_hand} of {len(ids)}")
```

Output:

```text
question q-0019 (version 2.0, ambiguous, planted: ambiguous-target): If I edit the file and then run check, will it fail?
reference answer: Reading 1: if you edited a generated file (a target), check prints DRIFT and the path for it and exits with status 1, because its hash no longer matches the lock.
Reading 2: if you edited a template, check prints nothing and exits with status 0, since a template change is not drift.
P2 reply: Quote: "Run `sablefile check` after a sync. If no output appears, no generated file has drifted since the last sync. To see what drift looks like, open a generated file, change one line, and run the check again. The check prints `DRIFT` and the path of the file." [sec:quickstart-check]
Answer: Yes, if you edit the file and then run check, it will print `DRIFT` and the path of the file, indicating a drift [sec:quickstart-check].
judge verdict on P2's reply: PASS
judge reason: The response correctly identifies that editing a generated file and running check will result in a DRIFT message and path output, aligning with Reading 1 of the reference. It does not contradict or omit any part of the reference.
judge verdict on P1's reply to the same item: FAIL
hand verdict on P2's reply, under rule 3: FAIL
rule it breaks: 3. If the reference has several readings, the response must answer every reading. A partial answer is incorrect.
P2 passes, as judged: 17 of 20
P2 passes, with q-0019 read by hand: 16 of 20
```

Read this output as a record of the judge's verdicts. The reference for `q-0019` has two readings, and P2's reply answers only the first. Rule 3 of the judge's prompt says a partial answer fails, and the judge fails P1's reply to the same item, which also answers only the first reading. On P2's reply it passes, and its reason says the reply covers the reference and omits nothing. Read by hand, P2 passes 16 of 20 items, not 17 of 20. The tie is one judge error away from not being one. That is why the rates here are the judge's rates, and why [chapter 6](calibrate-the-judge) checks the judge against public human ratings.

**Working rule:** Compare prompts on the same items, paired, and report the difference with its interval. Call one prompt better only when the whole interval lies above zero, and worse only when it lies below zero. When the interval includes zero, say that no difference was detected at this size, which is not the same as saying the prompts are equal.

## What twenty questions can't show {#what-twenty-questions-cant-show}

This last example takes the same two prompts and asks what the twenty items can show about them. Twenty items turn out to say very little about these two prompts.

Example `twenty-cannot-tell` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Shows that twenty items cannot tell the two prompts apart: the interval of the paired difference includes zero.

The assert is the chapter's claim, checked against the numbers; the example prints no verdict word."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import chapter_items
from lib.judging import paired
from lib.stats import interval_points

result = paired("judge-answers-baseline", "judge-answers-prompt-b", [item.id for item in chapter_items()])
print(f"paired items (n): {result.n}")
differing = int((result.first != result.second).sum())
print(f"items where the two verdicts differ: {differing}")
print(f"difference, P2 minus P1: {100 * result.difference:+.1f} points")
print(f"95% interval of the difference: {interval_points(result.diff_lo, result.diff_hi)}")
print(f"interval width: {100 * (result.diff_hi - result.diff_lo):.1f} points")
# Zero inside the interval is the claim: no difference that twenty items can show.
assert result.diff_lo <= 0.0 <= result.diff_hi, "the interval of the difference must include zero"
# Two items carry the whole comparison: the pass rates differ only where these two verdicts differ.
assert differing == 2, "exactly two items must have differing verdicts"
```

Output:

```text
paired items (n): 20
items where the two verdicts differ: 2
difference, P2 minus P1: +0.0 points
95% interval of the difference: [-15.0, +15.0] points
interval width: 30.0 points
```

Only 2 items get different verdicts from the two prompts, so the difference can move only in coarse steps, one item at a time. The interval of the difference is 30.0 points wide. An assert in the code requires the interval to include zero, so the claim fails loudly if the numbers ever stop supporting it. An interval that wide can detect only a large change, and a smaller change that still matters to users can hide inside it.

*Figure 1.1. The bootstrap distribution of P2 minus P1 over the twenty items.*

![The resampled differences peak at zero, and the middle 95% of them spread wide on both sides of it](https://rollingedition.ai/books/evaluating-llm-applications/2026.11.7/figures/twenty-difference.svg)

Example `figure-twenty-difference` (Python 3.12.15 · bm25s 0.3.16 · matplotlib 3.11.2 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Draws the bootstrap distribution of the paired difference, P2 minus P1, over the twenty items of twenty-cannot-tell:
how many resamples give each possible difference. The printed interval and its width are the ones that example prints,
and the asserts check that the resamples drawn here give the same ends, land on whole steps, and reach past zero."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import numpy as np

from lib import SEED
from lib.answers import chapter_items
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.judging import paired
from lib.stats import RESAMPLES, interval_points

result = paired("judge-answers-baseline", "judge-answers-prompt-b", [item.id for item in chapter_items()])
diff = result.second - result.first  # per item: +1, 0 or -1, in the sorted item order the interval uses
# bootstrap_mean keeps only the interval, so this redraws its resamples: the same generator, seed and count.
rng = np.random.default_rng(SEED)
picks = rng.integers(0, diff.size, size=(RESAMPLES, diff.size))
gaps = 100 * diff[picks].mean(axis=1)  # each resampled difference, in points
lo, hi = np.quantile(gaps, [0.025, 0.975])  # the middle 95% of the resampled differences
assert np.isclose(lo, 100 * result.diff_lo) and np.isclose(hi, 100 * result.diff_hi), "the resamples must give the interval"
assert lo < 0.0 < hi, "the middle 95% must reach past zero on both sides"
# One differing item moves the difference by 100 / n points, so every resample is a whole number of steps.
step = 100 / result.n
assert np.allclose(gaps / step, np.round(gaps / step)), "every resampled difference must be a multiple of the step"
values, value_counts = np.unique(np.round(gaps, 6), return_counts=True)
assert values[value_counts.argmax()] == 0.0, "the most common resampled difference must be zero"

print(f"paired items (n): {result.n}")
differing = int((result.first != result.second).sum())
print(f"items where the two verdicts differ: {differing}")
print(f"bootstrap resamples: {RESAMPLES}")
print(f"difference, P2 minus P1: {100 * result.difference:+.1f} points")
print(f"95% interval of the difference: {interval_points(result.diff_lo, result.diff_hi)}")
print(f"interval width: {100 * (result.diff_hi - result.diff_lo):.1f} points")
print(f"step between possible differences: {step:.1f} points")
print(f"most common difference: {values[value_counts.argmax()]:+.1f} points")
print(f"resamples at the most common difference: {value_counts.max()}")

fig, ax = new_figure(height=2.8)
# One bar per step, centred on each possible difference, so a resample at -25 gets a bar of its own.
edges = np.arange(gaps.min() - step / 2, gaps.max() + step, step)
counts, _, _ = ax.hist(gaps, bins=edges, rwidth=0.8, color=ACCENT, label="resampled differences")
assert counts.sum() == RESAMPLES, "every resample must fall in a bar"
# Zero is the claim: the interval includes it, so no difference is ruled out at this size.
ax.axvline(0, color=INK, linewidth=1.2, label="zero: no difference")
ax.axvline(100 * result.diff_lo, color=MUTED, linestyle="--", label="ends of the middle 95%")
ax.axvline(100 * result.diff_hi, color=MUTED, linestyle="--")
ax.set_xlabel("difference, P2 minus P1, in percentage points")
ax.set_ylabel("resamples")
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2)  # above the plot, where no line crosses it
save(fig, "twenty-difference")
```

Output:

```text
paired items (n): 20
items where the two verdicts differ: 2
bootstrap resamples: 2000
difference, P2 minus P1: +0.0 points
95% interval of the difference: [-15.0, +15.0] points
interval width: 30.0 points
step between possible differences: 5.0 points
most common difference: +0.0 points
resamples at the most common difference: 606
figure: figures/twenty-difference.svg
```

Figure 1.1 counts how many resamples land on each possible difference, one bar per step. Each time a resample draws one of the differing items, the difference moves by a twentieth of the set, 5.0 points. The most common difference is +0.0 points, the bar at zero. Zero is the solid line, and the dashed lines mark the middle 95%, which runs over [-15.0, +15.0] points and reaches past zero on both sides.

In production, the same mistake shows up in three forms: trusting a number that can't carry the claim made for it. A team picks the prompt with the higher number on the twenty items it wrote first, and the report leaves out the interval, so nobody sees how little the number holds. A judge gets trusted because its verdicts look sensible, and nobody reads its FAIL reasons against the reference. A set of recorded replies, kept after the sections the assistant sees have changed, measures the old system while its numbers keep looking fine. You notice the first when a report carries an interval beside each rate. You notice the second when someone reads the judge's FAIL reasons against the references on every run. The third shows only if the recording also hashes the docs it was given. This book's manifests hash the prompt and the test set, so a prompt change is refused on replay, but a change to the sections goes unseen.

Two later chapters take the next steps. [Chapter 3](build-the-test-set) builds the larger set this chapter lacks, and [chapter 8](intervals-and-sample-size) works out how many items a difference needs before it can show.

The chapter made these decisions:

- Every question names its version, and its answer comes from that version's docs only.
- This chapter's set is twenty items, read in full, with the planted items labelled.
- Each recording is made once per model, prompt and docs, and replayed for every comparison.
- Citations and declines are checked in code before any judge reads a reply.
- The judge grades against a written reference, and its rate counts as the judge's rate until calibration checks it.
- A pass rate comes with its denominator, its interval and its rate for each kind of item.
- Prompts are compared on the same items, and only an interval wholly on one side of zero makes one of them better or worse.

**Working rule:** Report the interval beside every comparison. Twenty items can find broken answers; they can't rank two prompts.
