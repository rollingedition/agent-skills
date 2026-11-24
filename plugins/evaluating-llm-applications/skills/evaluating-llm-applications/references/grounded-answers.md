---
title: "Evaluating LLM Applications"
chapter: "Check that answers rest on the cited docs, in the asked version"
chapter_id: grounded-answers
book: evaluating-llm-applications
edition: 2026.11.7
verified: 2026-11-22
edition_code: WCKB-Y7EK
canonical: https://rollingedition.com/evaluating-llm-applications/grounded-answers
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Check that answers rest on the cited docs, in the asked version,” chapter 9 of Evaluating LLM Applications, Edition 2026.11.7, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/grounded-answers. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Check that answers rest on the cited docs, in the asked version

By the end of this chapter you can count whether an answer's citations support what it says, whether every claim in it rests on the sections the assistant was given, whether it is right for the version the reader asked about, and whether retrieval reached the right section on the way.

A correct answer can still be a poor one. The assistant in this book answers questions about sablefile from its documentation, and a reply passes when it matches the reference answer for the version the question asks about. A reply can pass that test and still cite a section that doesn't say what its sentence says, add a detail that no section gives, or take its facts from another version of the docs. A pass rate sees none of these. A reader who checks the citation beside a claim can, which is why the assistant is asked to cite at all.

Four checks sit beside the pass rate, and each has its own count over its own denominator. Citation accuracy asks whether each citation names a section the item lists as supporting in the asked version. Faithfulness asks whether each claim follows from the sections the assistant was shown. Version-correctness asks whether the answer matches the reference for the asked version. Outcome against path asks whether a pass came with its section in hand, and whether a fail had it. Citation accuracy and faithfulness leave declines out, since a decline makes no claim to check. Version-correctness and the retrieval table keep the declines, as the pass rate does, and each prints how many declines it holds.

## What grounded means here {#what-grounded-means}

An answer is grounded when a reader who follows its [citations](#citation-accuracy) finds each of its claims where the citation says it is, in the version they asked about. Three things have to hold for that. The citation must exist in that version and support the sentence it is attached to. Every claim in the answer must follow from the sections the assistant read. And the answer must be right for that version, not merely right for some other version that uses the same words.

Take a reader who asks how long a remote fetch waits before it gives up. Suppose the reply gives a plausible answer and cites the section on fetching remote templates, but that section never says how long the wait is. A reader would take the reply as grounded, and the citation looks right. The reader who opens the section finds nothing to support the number. A pass rate would count that reply as correct if the number happened to match the reference. Faithfulness is the check that reads the sections, through a judge. The citation check reads only IDs, and says so.

These failures are different, and each needs its own count. A reply can have a supporting citation and still state a detail the section leaves out, so citation accuracy does not show faithfulness. A reply can be faithful to a section of one version and wrong for another, so faithfulness does not show version-correctness. And a reply can be right and well cited while the retrieval step never reached the section it leans on. Outcome against path exists to find that case.

**Working rule:** Give each check its own count over its own denominator, and treat a pass as the start of the reading, not the end of it.

## Citation accuracy {#citation-accuracy}

A citation is a claim about the docs: this section, in this version, supports the sentence it is attached to. Like any claim, it can be wrong. The section can exist and say something else. It can belong to another version. Or the reply can cite a section the item doesn't list. The Primer covers the sentence-level check, [checking what a cited item supports](https://rollingedition.com/primer-on-search-relevance/s/check-citation-support), and [checking citations against context](https://rollingedition.com/primer-on-search-relevance/s/check-citations-against-context) covers the context a model was given. This book's check is simpler, and [citation checks](checks-in-code#citation-checks) in chapter 4 gives its four outcomes. It matches each cited ID against the item's list of supporting sections for the asked version. It never reads the section, so it says nothing about the sentence.

The code prints two counts from the same replies. The citation rate is the share of all citations in answered items that are supported. The item rate counts an answered item once if at least one of its citations is supported, over all answered items, so one good citation carries the item. A citation to a section of the asked version that the item does not list is printed as unlisted. That section may well be right, so the check does not call it wrong, and it does not open the section to find out. Reading an unlisted citation is a hand decision. If the section supports the sentence, the item's list of supporting sections is incomplete, and the test set's owner should add it. If it does not, the citation is wrong, and the reply should be read as a failed citation.

Run it on both splits, and read the item line before the citation line.

Example `citation-accuracy-counts` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Counts the baseline's answered items that cite a supporting section of the asked version, dev and held-out apart.

An item counts once, and only if one of its citations is supported; its other citations sit in the citation lines. A decline
is not an answer, so it is left out of every count. The check matches each cited ID against the item's listed supporting
section IDs for its asked version. It never reads the section's text, so it does not check what the sentence says.
The first line of each split is the point: the item rate."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import citation_outcomes, parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

ids = section_ids_by_version()  # every version's section IDs, read from the docs, for telling wrong-version from missing
model = ReplayModel("assistant-baseline", P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1


def supporting_ids(item):
    """The item's supporting section IDs in its asked version. Another version's listed sections are not counted here."""
    return frozenset(s.section_id for s in item.supporting_sections if s.version == item.version)


for split in ("dev", "held-out"):
    declined = 0
    results = {}  # item id -> its citation outcomes, for each answered item
    for item in load_items(split=split):
        reply = parse_reply(model.reply(item.id, 0))
        if reply.declined:
            declined += 1
        else:
            results[item.id] = citation_outcomes(reply, item.version, supporting_ids(item), ids)
    # An answer to an unanswerable item lists no section of its asked version, so it can never count as supported here.
    outcomes = [outcome for found in results.values() for outcome in found]  # every citation, in item order
    with_support = [item_id for item_id, found in results.items() if "supported" in found]
    no_support = sorted(set(results) - set(with_support))
    print(f"{split} declined items, left out: {declined}")
    print(f"{split} answered items: {len(results)}")
    print(f"{split} answered items citing a supporting section of the asked version: {pct(len(with_support), len(results))}")
    print(f"{split} answered items with no supported citation: {len(no_support)}")
    print("  " + (", ".join(no_support) or "none"))
    print(f"{split} citations: {len(outcomes)}")
    print(f"{split} citations that are supported: {pct(outcomes.count('supported'), len(outcomes))}")
    print(f"{split} citations that are unlisted: {pct(outcomes.count('unlisted'), len(outcomes))}")
    print(f"{split} citations that are wrong-version or missing: "
          f"{pct(outcomes.count('wrong-version') + outcomes.count('missing'), len(outcomes))}")
```

Output:

```text
dev declined items, left out: 23
dev answered items: 57
dev answered items citing a supporting section of the asked version: 94.7% (54 of 57)
dev answered items with no supported citation: 3
  q-0005, q-0057, q-0058
dev citations: 60
dev citations that are supported: 93.3% (56 of 60)
dev citations that are unlisted: 6.7% (4 of 60)
dev citations that are wrong-version or missing: 0.0% (0 of 60)
held-out declined items, left out: 15
held-out answered items: 25
held-out answered items citing a supporting section of the asked version: 96.0% (24 of 25)
held-out answered items with no supported citation: 1
  q-0090
held-out citations: 33
held-out citations that are supported: 93.9% (31 of 33)
held-out citations that are unlisted: 6.1% (2 of 33)
held-out citations that are wrong-version or missing: 0.0% (0 of 33)
```

On dev, the item rate is 94.7% (54 of 57).

On dev, 3 answered items have no supported citation, and the output names them. On held-out, the count is 1.

The citation rate on dev is 93.3% (56 of 60). The unlisted citations on dev are 6.7% (4 of 60), which the output reports and does not count as errors.

On held-out, the item rate is 96.0% (24 of 25), and the citation rate is 93.9% (31 of 33). Held-out has only 25 answered items, so one item moves its rate a long way. A difference between the splits would need an interval before anyone called it real, and [intervals and sample size](intervals-and-sample-size) explains how to build one.

The citations that are wrong-version or missing are the ones that would be wrong for a reason the check can name. On dev, they are 0.0% (0 of 60). On held-out, they are 0.0% (0 of 33). So the citation rates fall short of 100% because of unlisted citations, and a person has to read those.

The two rates can diverge for a simple reason. An item with one supported citation and one unlisted citation counts in the item rate and lowers the citation rate. Reading both shows whether the misses sit in whole items or in single citations inside items that otherwise hold up.

The idea behind the check has been studied outside this book. Gao and colleagues (2023), at EMNLP 2023 and [on arXiv](https://arxiv.org/abs/2305.14627), built a benchmark for citations in generated answers, and reported that many answers from strong models were not fully supported by their cited passages. Their setup was not this book's, so no number is carried over from them. The paper is cited for the idea.

**Working rule:** Read the item rate and the citation rate together, and read each unlisted citation before you change a prompt. An unlisted citation is a question for the docs, not an error to count.

## Faithfulness {#faithfulness}

Citation accuracy runs without a model, but its counts say how many citations name a listed section, not whether each sentence holds. Faithfulness is the next question, and it is the one that catches claims with no citation at all.

Citation accuracy checks only the sentences that carry a citation. A claim the reply makes without one escapes it, and so does a claim that a cited section supports only in part. Faithfulness asks a wider question: does every claim in the answer follow from the sections the assistant was shown?

Ragas (Es and colleagues, 2023, also a [preprint](https://arxiv.org/abs/2309.15217)) scores faithfulness as the share of an answer's statements that the context supports. It splits the answer into statements and checks each one. This book asks one question per answer instead. The faithfulness prompt in `lib/prompts.py` gives the judge the sections and the answer. The judge reads the answer claim by claim, and writes `VERDICT: SUPPORTED` on its first line only if every claim holds. Otherwise it writes `VERDICT: UNSUPPORTED`, then one sentence of reason.

The difference from citation accuracy shows up in the middle of an answer. Suppose a reply has two sentences. The first carries a citation to a section that supports it, and the second has none, because it adds a detail the section leaves out. Citation accuracy scores the first sentence and says nothing about the second. Faithfulness reads the whole answer, so it can mark the reply unsupported on the second sentence alone. Neither check replaces the other, which is why both are kept.

Nobody has checked this judge's verdicts against a person's, so every faithfulness rate here is uncalibrated. The judge is also the assistant's own model, Qwen3-4B-Instruct-2507, so it grades answers that model wrote. [Self-preference](when-the-judge-stops-being-reliable#self-preference) explains why that matters, and why this book cannot test it. Calibrating the judge would need human ratings of these replies, which this book doesn't have. [Calibrate the judge](calibrate-the-judge) describes the method, which compares the judge with ratings made by hand. Because these rates are not calibrated, there is nothing for the [transfer assumption](calibrate-the-judge#transfer-assumption) to carry over, and the limits in [where to stop](when-the-judge-stops-being-reliable#where-to-stop) apply to them in full.

Example `faithfulness-rate` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""The faithfulness rate of assistant-baseline's answered items, as judged in judge-faithfulness-baseline, dev and held-out apart.

An answered item is one the baseline did not decline and whose reply is not empty; a decline is left out. The judge writes
SUPPORTED or UNSUPPORTED on its first line. A reply that is neither is printed by item ID and left out of the denominator,
never counted as UNSUPPORTED. The judge is uncalibrated: this book has no human ratings for it, so the rates are not
corrected for its errors and are not a calibrated measure. When every readable verdict is the same, the percentile
bootstrap cannot vary, so the example says so and prints the exact binomial bound for n of n instead."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import parse_reply
from lib.judging import parse_support_verdict
from lib.prompts import FAITH_SHA256, P1_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_pct, pct
from lib.testset import load_items

answers = ReplayModel("assistant-baseline", P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1
judge = ReplayModel("judge-faithfulness-baseline", FAITH_SHA256)  # the judge's replies, made from the faithfulness prompt

print("judge: judge-4b, uncalibrated (no human ratings in this book)")
for split in ("dev", "held-out"):
    answered = []
    for item in load_items(split=split):
        reply = parse_reply(answers.reply(item.id, 0))
        if not reply.declined and reply.text:
            answered.append(item.id)
    readable = {}  # item id -> 1.0 for SUPPORTED, 0.0 for UNSUPPORTED
    for item_id in answered:
        raw = judge.reply(item_id, 0)
        verdict = parse_support_verdict(raw)
        if verdict is None:
            line = next((ln.strip().strip("*`").strip() for ln in raw.splitlines() if ln.strip()), "")
            print(f'{split} unreadable verdict, left out: {item_id} ("{line}")')
        else:
            readable[item_id] = 1.0 if verdict == "SUPPORTED" else 0.0
    scores = list(readable.values())
    lo, hi = bootstrap_mean(scores)  # level 0.95; seed SEED, 2,000 resamples
    print(f"{split} answered items: {len(answered)}")
    print(f"{split} unreadable verdicts: {len(answered) - len(readable)}")
    print(f"{split} faithfulness rate: {pct(int(sum(scores)), len(scores))}")
    print(f"{split} 95% interval of the faithfulness rate: {interval_pct(lo, hi)}")
    if len(set(scores)) == 1:  # every readable verdict is the same, so resampling cannot vary
        print(f"{split} bootstrap interval is degenerate: all {len(scores)} readable verdicts are the same")
        if sum(scores) == len(scores):
            print(f"{split} exact 95% lower bound for {len(scores)} of {len(scores)}: {100 * 0.025 ** (1 / len(scores)):.1f}%")
    if split == "dev":
        unfaithful = sorted(item_id for item_id, score in readable.items() if score == 0.0)
        print(f"dev unfaithful items, first five: {', '.join(unfaithful[:5])}")
```

Output:

```text
judge: judge-4b, uncalibrated (no human ratings in this book)
dev answered items: 57
dev unreadable verdicts: 0
dev faithfulness rate: 94.7% (54 of 57)
dev 95% interval of the faithfulness rate: [87.7%, 100.0%]
dev unfaithful items, first five: q-0013, q-0029, q-0055
held-out answered items: 25
held-out unreadable verdicts: 0
held-out faithfulness rate: 100.0% (25 of 25)
held-out 95% interval of the faithfulness rate: [100.0%, 100.0%]
held-out bootstrap interval is degenerate: all 25 readable verdicts are the same
held-out exact 95% lower bound for 25 of 25: 86.3%
```

The example takes the baseline's answered items, leaves out the declines, and asks the judge about each one. It prints a rate only over verdicts it can read. A reply that is neither SUPPORTED nor UNSUPPORTED is printed by item and left out of the denominator. It is never counted as a failure, as [verdict first](a-judge-with-a-rubric#verdict-first) explains.

The uncalibrated faithfulness rate on dev is 94.7% (54 of 57). Its interval is [87.7%, 100.0%]. The top of that interval sits on the upper boundary of the rate scale, because a bootstrap cannot resample past it. The interval is still wide, which is the honest reading of 57 answered items.

The uncalibrated faithfulness rate on held-out is 100.0% (25 of 25). Its printed interval is [100.0%, 100.0%], but that is not an interval. The output says the bootstrap is degenerate: all 25 readable verdicts are the same. A resample of items that all pass can only return the same rate, so the bootstrap says nothing about where the rate lies.

The exact 95% lower bound is 86.3%. Below that true rate, all of the held-out replies passing would happen with probability under 2.5%. The bound is 0.025 to the power of one over n. It shows that the judge passed these replies, on a split too small to show where the rate lies. Do not read the held-out figure as a finding that the assistant is faithful.

The two checks print their own lists. The citation output names the items with no supported citation, and the faithfulness output names the first unfaithful dev items. Read the two lists side by side, since this chapter does not assume they name the same items.

**Working rule:** Put "uncalibrated" beside every faithfulness rate, and read the first unfaithful items before you trust the rate. A faithfulness check shows where the judge says a claim is unsupported. It does not show that the judge is right.

## Version-correctness {#version-correctness}

sablefile has three versions of its docs, 1.0, 1.1 and 2.0, and some questions have different answers in each. A reply can be grounded in a section of 1.1 and still be wrong for a reader on 2.0. The book calls these [version-dependent items](#the-twenty-items). Each has a reference answer for the version the reader asked about, and its check asks whether the reply matches that reference. There are 17 of them on dev and 8 on held-out.

Version-dependent items count in the pass rate with every other item, and they also get their own count, beside it. A reply to one of them is judged against the reference for the asked version, so a correct answer for another version fails. That miss would look like a weak assistant if it were only mixed into the general rate. The judged-correct rate is the pass rate for version-dependent items alone, so a version miss shows on its own line, and a team can see whether a change to retrieval moved it. Declines stay in that denominator, as they do in the pass rate, and each split prints how many it holds.

A wrong-version citation is a separate count. It is a citation to a section that exists only in another version. A reply can be right for the asked version and still cite another version's section, and a reader who copies that citation lands in the wrong docs.

This check sees only what the ID tells it. A citation carries an ID, not a version. Most IDs repeat across versions, so a section ID that appears in 1.0, 1.1 and 2.0 looks the same in each. An ID that appears in every version can never be flagged as wrong-version, whichever version the reader asked about. The check can flag a citation only when the asked version lacks its ID and another version has it. The index matters too. A citation to another version is possible only when that version's sections are in the index the reply was built from, so the count has to be read again when the index changes, and a zero from an old index says nothing about a new one.

Two variants are read here. The baseline retrieves from the index of the asked version only. The unfiltered variant retrieves from the indexes of every version together, and shows each section's version in its header, so the model can see where a section comes from. The unfiltered variant is the one that could cite another version, since it is shown them.

Example `version-correct-answers` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Reads the 25 version-dependent items for two variants: whether the judge passed the answer for the asked version, and whether a
citation names a section that exists only in another version.

The judge's verdict for each variant is read from its own recording, and an unreadable verdict is printed and left out of the
pass rate, never counted as a fail. A declined reply has a verdict like any other reply, so it stays in the denominator; its
count is printed beside each rate. A wrong-version citation is counted per item, over every item, so a zero shows as 0 of 25.
The last lines list the items where the two variants disagree, to read item by item."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.contract import citation_outcomes, parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256, REF_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

ids = section_ids_by_version()  # every version's section IDs, so a section of another version is known as one
# label, the assistant's recording, the judge's recording of that assistant's replies
VARIANTS = (("baseline", "assistant-baseline", "judge-answers-baseline"), ("unfiltered", "assistant-unfiltered", "judge-answers-unfiltered"))
items = [item for item in load_items() if item.kind == "version-dependent"]
item_ids = [item.id for item in items]
listed = {item.id: frozenset(s.section_id for s in item.supporting_sections if s.version == item.version) for item in items}
verdict, wrong = {}, {}  # label -> {item id: PASS or FAIL, readable only}; label -> item ids with a wrong-version citation
for label, assistant, judge in VARIANTS:
    verdict[label], unreadable = readable_verdicts(judge, item_ids, REF_SHA256)
    for item_id, first in unreadable:
        print(f'{label} unreadable verdict, left out: {item_id} ("{first}")')
    replies = ReplayModel(assistant, P1_SHA256)
    wrong[label] = {item.id for item in items
                    if "wrong-version" in citation_outcomes(parse_reply(replies.reply(item.id, 0)), item.version, listed[item.id], ids)}
    for split in ("dev", "held-out"):
        split_items = [item for item in items if item.split == split]
        readable = [item.id for item in split_items if item.id in verdict[label]]
        passed = sum(verdict[label][item_id] == "PASS" for item_id in readable)
        print(f"{label} {split} version-dependent items: {len(split_items)}")
        print(f"{label} {split} declined replies, counted in the denominator: "
              f"{sum(parse_reply(replies.reply(item.id, 0)).declined for item in split_items)}")
        print(f"{label} {split} judged correct for the asked version: {pct(passed, len(readable))}")
        print(f"{label} {split} citing a wrong-version section: "
              f"{pct(sum(item.id in wrong[label] for item in split_items), len(split_items))}")
    print(f"{label} all version-dependent items citing a wrong-version section: {pct(len(wrong[label]), len(items))}")

both = [item_id for item_id in item_ids if item_id in verdict["baseline"] and item_id in verdict["unfiltered"]]
print(f"items with a readable verdict in both variants: {len(both)}")
differ = [i for i in both if verdict["baseline"][i] != verdict["unfiltered"][i]]
print(f"items where the verdicts differ: {len(differ)}")
print("  " + (", ".join(differ) or "none"))
flag_differ = [i for i in item_ids if (i in wrong["baseline"]) != (i in wrong["unfiltered"])]
print(f"items where the wrong-version flag differs: {len(flag_differ)}")
print("  " + (", ".join(flag_differ) or "none"))
```

Output:

```text
baseline dev version-dependent items: 17
baseline dev declined replies, counted in the denominator: 4
baseline dev judged correct for the asked version: 64.7% (11 of 17)
baseline dev citing a wrong-version section: 0.0% (0 of 17)
baseline held-out version-dependent items: 8
baseline held-out declined replies, counted in the denominator: 2
baseline held-out judged correct for the asked version: 75.0% (6 of 8)
baseline held-out citing a wrong-version section: 0.0% (0 of 8)
baseline all version-dependent items citing a wrong-version section: 0.0% (0 of 25)
unfiltered dev version-dependent items: 17
unfiltered dev declined replies, counted in the denominator: 5
unfiltered dev judged correct for the asked version: 52.9% (9 of 17)
unfiltered dev citing a wrong-version section: 0.0% (0 of 17)
unfiltered held-out version-dependent items: 8
unfiltered held-out declined replies, counted in the denominator: 2
unfiltered held-out judged correct for the asked version: 75.0% (6 of 8)
unfiltered held-out citing a wrong-version section: 0.0% (0 of 8)
unfiltered all version-dependent items citing a wrong-version section: 0.0% (0 of 25)
items with a readable verdict in both variants: 25
items where the verdicts differ: 6
  q-0003, q-0021, q-0022, q-0033, q-0082, q-0085
items where the wrong-version flag differs: 0
  none
```

Across every version-dependent item, the wrong-version share is 0.0% (0 of 25) for the baseline and 0.0% (0 of 25) for the unfiltered variant. A zero says only that the check flagged no ID. The next example shows how few IDs it could have flagged.

Example `version-check-detail` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""The two counts behind the version check, and the version-dependent items where the variants' verdicts differ, by split.

A wrong-version citation is one whose ID exists only in another version, so an ID that several versions share cannot be
attributed to one of them. This prints how many section IDs are found in one version only, then how many citations to the
version-dependent items name a shared ID, for each variant. The last lines list the items where the verdicts differ, by split."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.calibration import readable_verdicts
from lib.contract import parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256, REF_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

ids = section_ids_by_version()
shared = Counter(i for found in ids.values() for i in found)  # how many versions each section ID appears in
print("section IDs found in one version only, by version: "
      + ", ".join(f"{v} {sum(shared[i] == 1 for i in found)}" for v, found in ids.items()))
items = [item for item in load_items() if item.kind == "version-dependent"]
split_of = {item.id: item.split for item in items}
verdict = {}  # label -> {item id: PASS or FAIL}, readable only
for label, assistant, judge in (("baseline", "assistant-baseline", "judge-answers-baseline"),
                                ("unfiltered", "assistant-unfiltered", "judge-answers-unfiltered")):
    replies = ReplayModel(assistant, P1_SHA256)
    cited = [cid for item in items for cid in parse_reply(replies.reply(item.id, 0)).citations]
    print(f"{label} citations to a section ID found in more than one version: "
          f"{pct(sum(shared[cid] > 1 for cid in cited), len(cited))}")
    verdict[label], _ = readable_verdicts(judge, list(split_of), REF_SHA256)
differ = [i for i in verdict["baseline"] if i in verdict["unfiltered"] and verdict["baseline"][i] != verdict["unfiltered"][i]]
for split in ("dev", "held-out"):
    part = [i for i in differ if split_of[i] == split]
    print(f"{split} items where the verdicts differ: {len(part)}")
    print("  " + (", ".join(part) or "none"))
```

Output:

```text
section IDs found in one version only, by version: 1.0 0, 1.1 0, 2.0 4
baseline citations to a section ID found in more than one version: 87.0% (20 of 23)
unfiltered citations to a section ID found in more than one version: 63.2% (12 of 19)
dev items where the verdicts differ: 4
  q-0003, q-0021, q-0022, q-0033
held-out items where the verdicts differ: 2
  q-0082, q-0085
```

The section IDs found in only one version, counted by version, are 1.0 0, 1.1 0, 2.0 4. An ID found in more than one version can still be flagged, but only for a reader on a version that lacks it. For the baseline, the share of citations to version-dependent items that name a shared ID is 87.0% (20 of 23). For the unfiltered variant it is 63.2% (12 of 19).

The judged-correct rates differ, though each is read on a small split. On dev, the baseline is judged correct on 64.7% (11 of 17).

The unfiltered variant is judged correct on 52.9% (9 of 17). On these items, the unfiltered variant passes fewer.

On held-out, the baseline is judged correct on 75.0% (6 of 8). The unfiltered variant has the same rate, but it passes different items. The verdicts go in opposite directions on q-0082 and q-0085, and the other held-out items agree.

Across both variants, the verdicts differ on 6 items, out of 25 with a readable verdict in each. On dev, 4 of them differ, and on held-out, 2. The output lists them by split.

No interval is computed for these differences, and a dev split of this size is small. So this chapter reports the counts and does not call either variant better or worse. The counts say three things: on these items the unfiltered variant passed fewer, no citation was flagged as wrong-version on either variant, and the differing verdicts are the place to read first.

**Working rule:** Read each citation's ID with the version of the answer beside it. A zero from this check means no flagged ID, not no wrong-version citation. Keep version-dependent items in their own count beside the pass rate, so a version miss shows up on its own line.

## Outcome and path {#outcome-and-path}

Outcome is whether a reply passed. Path is what the steps before the reply reached. In this book the path is short: one retrieval, then one reply. Two combinations need both counts. A pass whose supporting section never reached the model came from somewhere else, perhaps the model's own knowledge, and that is a warning even when the verdict is right. A fail with the section retrieved is the case the other checks exist to explain.

Runs with several steps have longer paths. [Agent Harnesses](https://rollingedition.com/agent-harnesses/s/t18-path) counts a task through its path, and that book is the place to read about it. This chapter scores the one step the assistant has.

### The retrieval step {#the-retrieval-step}

Retrieval is BM25 over the sections of the asked version. It is deterministic: the same question gets the same top sections every time. So this step needs no recording. The code computes the top sections for each item from the index, and sets them against the verdict the judge gave the baseline's reply.

Dev items with no supporting section of the asked version are left out of the table. Those are the unanswerable items, since no section of their asked version exists for retrieval to find. Their count is 13.

Example `retrieval-path` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""Sets the baseline's judge verdict against whether a supporting section reached the top k, for each dev item that has one.

Retrieval is BM25 over the asked version, so it is the same on every run and needs no recording; k is the baseline's, read from
its manifest. The two diagonal cells are the expected pairs. The two off-diagonal cells are the ones to read: a pass without the
right section retrieved, and a fail with it retrieved. Unanswerable items are left out, since they have no section of their asked
version to retrieve; their count is printed. An unreadable verdict is printed and left out, never counted as a fail. A declined reply is counted in its cell like any
other reply; the count of declines is printed. The FAIL cell is split into declines and answers in fail-with-section."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant
from lib.calibration import readable_verdicts
from lib.contract import parse_reply
from lib.prompts import P1_SHA256, P1_SYSTEM, REF_SHA256
from lib.replay import ReplayModel
from lib.testset import load_items

RECORDING = "assistant-baseline"
k = ReplayModel(RECORDING, P1_SHA256).manifest["k"]  # the top k the baseline's prompt was built from, read from its manifest
assistant = Assistant(RECORDING, P1_SYSTEM, P1_SHA256, k=k)  # its retriever only; the recording is not read here
replies = ReplayModel(RECORDING, P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1, for the decline check

dev = load_items(split="dev")
has_support = [item for item in dev if any(s.version == item.version for s in item.supporting_sections)]
print(f"top k: {k}")
print(f"dev items: {len(dev)}")
print(f"dev items with no supporting section of the asked version, left out: {len(dev) - len(has_support)}")

verdicts, unreadable = readable_verdicts("judge-answers-baseline", [item.id for item in has_support], REF_SHA256)
for item_id, first in unreadable:
    print(f'unreadable verdict, left out: {item_id} ("{first}")')

# Keyed by (retrieved, passed): the four cells of the 2 by 2 table, each a list of item ids in sorted order.
cells = {(True, True): [], (True, False): [], (False, True): [], (False, False): []}
declined = set()  # item ids whose reply is a decline; they sit in their cells like any other reply
for item in has_support:
    if item.id not in verdicts:
        continue
    listed = {s.section_id for s in item.supporting_sections if s.version == item.version}
    top = {section.section_id for section in assistant.sections(item)}  # the top k sections, by BM25 rank
    cells[(bool(listed & top), verdicts[item.id] == "PASS")].append(item.id)
    if parse_reply(replies.reply(item.id, 0)).declined:
        declined.add(item.id)

print(f"items in the table: {sum(len(ids) for ids in cells.values())}")
print(f"declined items in the table, counted in their cells: {len(declined)}")
print(f"right section in the top {k}, PASS: {len(cells[(True, True)])}")
print(f"right section in the top {k}, FAIL: {len(cells[(True, False)])}")
print(f"right section not in the top {k}, PASS: {len(cells[(False, True)])}")
print(f"right section not in the top {k}, FAIL: {len(cells[(False, False)])}")
print("passed without the right section retrieved: " + (", ".join(cells[(False, True)]) or "none"))
print("failed with the right section retrieved: " + (", ".join(cells[(True, False)]) or "none"))
```

Output:

```text
top k: 3
dev items: 80
dev items with no supporting section of the asked version, left out: 13
unreadable verdict, left out: q-0043 ("VERDICT: PARTIAL")
items in the table: 66
declined items in the table, counted in their cells: 10
right section in the top 3, PASS: 49
right section in the top 3, FAIL: 10
right section not in the top 3, PASS: 0
right section not in the top 3, FAIL: 7
passed without the right section retrieved: none
failed with the right section retrieved: q-0019, q-0023, q-0025, q-0029, q-0033, q-0045, q-0046, q-0048, q-0063, q-0074
```

The top k is 3, read from the baseline's manifest. The table holds 66 items, and 10 of them are declines. A decline sits in its cell like any other reply, since the judge gave it a verdict. Each cell pairs a verdict with whether a supporting section reached the top k.

| Verdict | Supporting section in the top k | No supporting section in the top k |
| --- | --- | --- |
| PASS | 49 | 0 |
| FAIL | 10 | 7 |

Read the PASS row first. The cell for passes with the section in the top k holds 49 passes, and the cell for passes without it holds 0. That is consistent with passes coming from the docs. It does not show that they did, because the table counts how often two things occur together, not which one caused the other. The count of passes is also a check on the reference. A pass with no section retrieved can come from a reply that repeats a common fact, or from a reference answer a reader could guess, and the table cannot say which. Reading those items can.

The FAIL row is where the other checks come in. Of the failures with the section in the top k, 5 are declines, and the rest are answers. [Declining when the docs don't say](declining-when-the-docs-dont-say) covers what a decline means when the docs hold the answer. The example below splits the cell.

Example `fail-with-section` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.7:

```python
"""The dev items the baseline failed although a listed section of the asked version was in its top k, split into declines and answers.

For each answer it prints whether the reply cites a listed section, and the faithfulness judge's verdict on it. A decline has no
faithfulness verdict, because the judge reads only answers. An unreadable verdict is printed and left out, never counted as a fail."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import re

from lib.answers import Assistant
from lib.calibration import readable_verdicts
from lib.contract import citation_outcomes, parse_reply, section_ids_by_version
from lib.prompts import FAITH_SHA256, P1_SHA256, P1_SYSTEM, REF_SHA256
from lib.replay import ReplayModel
from lib.testset import load_items

RECORDING = "assistant-baseline"
k = ReplayModel(RECORDING, P1_SHA256).manifest["k"]  # the baseline's top k, as in retrieval-path
assistant = Assistant(RECORDING, P1_SYSTEM, P1_SHA256, k=k)  # its retriever only
replies = ReplayModel(RECORDING, P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1
faith = ReplayModel("judge-faithfulness-baseline", FAITH_SHA256)
ids = section_ids_by_version()
VERDICT = re.compile(r"^VERDICT:\s*(SUPPORTED|UNSUPPORTED)$")


def listed(item):
    """The item's supporting section IDs in its asked version."""
    return frozenset(s.section_id for s in item.supporting_sections if s.version == item.version)


dev = load_items(split="dev")
verdicts, unreadable = readable_verdicts("judge-answers-baseline", [item.id for item in dev], REF_SHA256)
for item_id, first in unreadable:
    print(f'unreadable verdict, left out: {item_id} ("{first}")')
fails = [item for item in dev if verdicts.get(item.id) == "FAIL" and listed(item) & {s.section_id for s in assistant.sections(item)}]
declined = [item for item in fails if parse_reply(replies.reply(item.id, 0)).declined]
answered = [item for item in fails if item not in declined]
print(f"right section in the top {k}, FAIL, declined: {len(declined)}")
print(f"right section in the top {k}, FAIL, answered: {len(answered)}")
print(f"answered FAIL with the section, citing a listed section: "
      f"{sum('supported' in citation_outcomes(parse_reply(replies.reply(item.id, 0)), item.version, listed(item), ids) for item in answered)}")
judged = {}  # item id -> SUPPORTED, UNSUPPORTED or unreadable, for each answered fail
for item in answered:
    line = next((ln.strip().strip("*`").strip() for ln in faith.reply(item.id, 0).splitlines() if ln.strip()), "")
    match = VERDICT.match(line)
    judged[item.id] = match.group(1) if match else "unreadable"
print(f"answered FAIL with the section, faithfulness SUPPORTED: {sum(v == 'SUPPORTED' for v in judged.values())}")
print(f"answered FAIL with the section, faithfulness UNSUPPORTED: {sum(v == 'UNSUPPORTED' for v in judged.values())}")
print("  " + (", ".join(i for i, v in judged.items() if v == "UNSUPPORTED") or "none"))
print(f"answered FAIL with the section, faithfulness unreadable: {sum(v == 'unreadable' for v in judged.values())}")
```

Output:

```text
unreadable verdict, left out: q-0043 ("VERDICT: PARTIAL")
right section in the top 3, FAIL, declined: 5
right section in the top 3, FAIL, answered: 5
answered FAIL with the section, citing a listed section: 5
answered FAIL with the section, faithfulness SUPPORTED: 4
answered FAIL with the section, faithfulness UNSUPPORTED: 1
  q-0029
answered FAIL with the section, faithfulness unreadable: 0
```

Of the answered failures, 5 cite a section the item lists. The faithfulness judge passes 4 of them and marks 1 unsupported, which is q-0029. The counts here do not show whether the wrong refusals, the version misses or the answer judge's errors account for the rest. Reading the replies can.

One verdict reads PARTIAL, not PASS or FAIL. The judge's verdict on q-0043 is PARTIAL, so the table leaves it out. An unreadable verdict is never counted as a fail.

**Working rule:** Treat retrieval as a gate on passes and as a lead on fails. A pass without the supporting section needs an explanation, and a fail with it points at the reply.

### Where agent harnesses picks up {#where-agent-harnesses-picks-up}

When a task takes several steps, each one may call a tool and change what the next step sees. The outcome can pass while a middle step went wrong, so the count has to be taken over the whole path. This book scores one retrieval and one reply, so its path count is a yes or no per item. The section on a task counted through a path in [Agent Harnesses](https://rollingedition.com/agent-harnesses/s/t18-path) covers how to score runs of that kind, and this chapter does not repeat it.

**Working rule:** In this book the path is one retrieval and one reply, so read the retrieval count beside the verdict for each item.

## Retrieval quality belongs to another book {#retrieval-quality}

How well retrieval orders the sections, and how much of the context it fills, is a question about ranking, and it belongs to *A Primer on Search Relevance*. Its [choosing a ranking metric](https://rollingedition.com/primer-on-search-relevance/s/choose-a-ranking-metric) section covers recall at k, mean reciprocal rank and nDCG, and how to choose among them. [Measuring the context](https://rollingedition.com/primer-on-search-relevance/s/measure-the-context) covers the context a model is given. Read both before you pick a metric for this assistant.

The retrieval-path count asks one question of each item: is a supporting section of the asked version in the top k? It returns yes or no, so it is not a ranking metric. It cannot say how far down the list that section sits, and that is what a ranking metric is for. Its k is read from the baseline's manifest and is not chosen in this chapter, so a change to k moves the table, and the table has to be read again.

Taken together, the four checks say that a pass rate on this assistant hides three different ways of being wrong. The reply can cite the wrong thing, state what no section says, or answer for the wrong version. Each one needs its own count, its own denominator and its own word for what it found. The decisions that follow from the results are these:

- Each reply is checked for citations, faithfulness and version, and each check keeps its own count.
- Every faithfulness rate is printed as uncalibrated until someone checks the judge against people.
- Version-dependent items keep their own count beside the pass rate, and their own version check.
- Retrieval is a gate on passes and a lead on fails. A pass whose section was not retrieved is read before it is counted as grounded.

**Working rule:** Before you call a reply grounded, read its citation, its claims and its version, and read the retrieval that came before it.
