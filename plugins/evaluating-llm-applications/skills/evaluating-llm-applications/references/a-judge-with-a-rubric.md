---
title: "Evaluating LLM Applications"
chapter: "Write a rubric a judge can apply"
chapter_id: a-judge-with-a-rubric
book: evaluating-llm-applications
edition: 2026.11.3
verified: 2026-11-21
edition_code: 4V0Y-VKTV
canonical: https://rollingedition.com/evaluating-llm-applications/a-judge-with-a-rubric
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Write a rubric a judge can apply,” chapter 5 of Evaluating LLM Applications, Edition 2026.11.3, examples passed Nov 21, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/a-judge-with-a-rubric. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Write a rubric a judge can apply

By the end of this chapter you can write a rubric that a judge model applies the same way to each reply, read its verdict with code that never counts anything it cannot read as a verdict, and say when a pairwise comparison or a scale is worth its cost.

[Chapter 4](checks-in-code) ended where code stops. A check can keep a reply's shape honest and show which section it cites, but it cannot read what the reply claims, so something has to read the claim against the reference. This chapter builds that reader, a judge: a model that reads a reply, compares it with a written reference answer, and writes whether the reply is correct. The assistant answers questions about [sablefile](measure-before-you-change#the-tool-and-its-docs), a command-line tool, and [chapter 1](measure-before-you-change#one-judge) first used this judge. The judge is Qwen3-4B-Instruct-2507, pinned to commit a06e946 of its GGUF conversion, the same model that answers the questions, so the book does not check a model with a stronger one. The judge's replies were recorded once, and every example in this chapter reads those recordings, so its numbers do not move from one run to the next. A team that reports a pass rate from a judge it never checked is reporting a number about the judge, and a reader of the page cannot tell the two apart without the checks this chapter describes.

A judge works from its instructions, and the instructions are the rubric. A rubric is two texts. The system text states the task, the rules and the form the reply must take. The template wraps the request, the reference and the reply in markers, so the judge can tell them apart. The rubric is part of the measurement, not a note that comes before it, because the wording is what the judge is given. This chapter shows how the book writes its rubrics, how each verdict is read, and where a team has to make a choice.

## What a judge is asked {#what-a-judge-is-asked}

The judge's reply goes to code, and the code reads the first line of it as the verdict. The form the rubric asks for is therefore part of the rubric. A judge that writes its verdict in another shape has given the code nothing to read, and [the section on verdicts below](#verdict-first) says what the code does then.

The book has five rubrics. The answer judge checks a reply about sablefile against the written reference answer for its question. The calibration rubric checks correctness with no reference, on rows from [HelpSteer2](https://huggingface.co/datasets/nvidia/HelpSteer2), a public dataset of human ratings of other models' replies to general prompts, which [chapter 6](calibrate-the-judge#human-ratings) describes. Its dataset card was read on 20 November 2026. Rubric B is a second wording of the calibration task. The pairwise rubric chooses the better of two replies. The faithfulness rubric checks whether an answer is supported by the sections it was given. Each rubric is written as text and carries a hash, and the first example prints the name and the hash of all five. For an item the docs do not cover, the reference is the word none, and the rubric is what tells the judge that a reply passes only when it is the decline sentence.

Example `rubric-text` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.3:

```python
"""The five rubrics the book's judges use, each with the sha256 its recording's manifest holds, and how many lines its system
text has. The hash is the one lib.prompts.sha256_text gives for the system text and the user template together: each
recording's manifest was made from that pair, not from the system text alone, so the check compares the pair. The first
line of each rubric is printed to show which rubric it is; the full texts are in lib/prompts.py."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.prompts import (
    FAITH_SYSTEM, FAITH_TEMPLATE, HS2_SYSTEM, HS2_TEMPLATE, HS2B_SYSTEM, HS2B_TEMPLATE, PAIR_SYSTEM, PAIR_TEMPLATE,
    REF_SYSTEM, REF_TEMPLATE, sha256_text,
)
from lib.replay import ReplayModel

# (the rubric's name, the recording whose manifest holds its hash, its system text, its user template)
RUBRICS = (
    ("answer judge, reference-guided", "judge-answers-baseline", REF_SYSTEM, REF_TEMPLATE),
    ("HelpSteer2 calibration rubric, reference-free", "judge-helpsteer2", HS2_SYSTEM, HS2_TEMPLATE),
    ("HelpSteer2 rubric B, second wording", "judge-helpsteer2-rubric-b", HS2B_SYSTEM, HS2B_TEMPLATE),
    ("pairwise rubric", "judge-hs2-pairs-ab", PAIR_SYSTEM, PAIR_TEMPLATE),
    ("faithfulness rubric", "judge-faithfulness-baseline", FAITH_SYSTEM, FAITH_TEMPLATE),
)

for name, recording, system, template in RUBRICS:
    digest = sha256_text(system, template)
    # ReplayModel raises ValueError when the recording's manifest hash is not this one, so a match is checked, not assumed.
    ReplayModel(recording, digest)
    print(f"{name}: {len(system.splitlines())} lines")
    print(f"  sha256 of system text and template: {digest}")
    print(f"  first line: {system.splitlines()[0]}")
```

Output:

```text
answer judge, reference-guided: 10 lines
  sha256 of system text and template: 4c409dcd59d0926646c3f8f5683da5de589e1586007dcfcf79d71a6b49e7e227
  first line: You check an AI assistant's answer about the sablefile tool against the written reference answer for the question.
HelpSteer2 calibration rubric, reference-free: 20 lines
  sha256 of system text and template: 56d617ac94b9fa5c4f0b2ce1eee17b7e0ce42c7e6b6c617edcb55a7b48d472e6
  first line: You check the correctness of an AI assistant's response to a user's request.
HelpSteer2 rubric B, second wording: 17 lines
  sha256 of system text and template: 7f512725080e8e78437603f7445a0480caaa0d2a344aa51d58d5475cba2ac384
  first line: You grade whether an AI assistant's reply to a user is right.
pairwise rubric: 13 lines
  sha256 of system text and template: 24a735e79373f7fa0b8bf1210c3e516964d93164508c666b8d333b93c27de992
  first line: You compare two AI assistant responses to the same request and say which one is better.
faithfulness rubric: 15 lines
  sha256 of system text and template: a584b8d56f63c212497fa67602f2fbd2add41823ca5895ba2bad541389970555
  first line: You check whether an answer about the sablefile tool is supported by the documentation sections it was given.
```

The output gives the first line of each system text and a hash of that text together with its template. The hash covers both because the judge is given both, and a change to either changes what the judge sees. The run reads each hash back against the recording that was made with that rubric, and it stops with an error if they differ, so a recording cannot be replayed under a rubric it was not made with. A reader who sees a number in this book can find the rubric behind it by name and by hash, and can tell that rubric apart from one with a single word changed.

The template's markers show the judge where the request, the reference and the reply each start and stop. That is what they are for. The book does not test whether they keep a reply that quotes the rubric's own instructions from being read as instructions.

**Working rule:** Write each rubric as text that a team can read, and hash it with the run it produces. Name it by its first line, so a reader can tell which rubric a number came from. Change a rubric's text only by making another rubric with its own recording, and never by editing the rubric that produced the numbers already on the page.

## Reference-guided or reference-free {#reference-guided}

A reference-guided judge is given a written answer for the question, and it checks the reply against that answer. A reference-free judge is given only the request and the reply, and it decides from what it knows whether the reply is right. A reference is a fixed point. The judge does not need to know sablefile, because the reference says what is correct. The same fixed point is also a limit: the judge can be no more right than the reference, and the rubric has to say how to treat a reply that uses other words, adds detail, or covers only part of the question.

The answer rubric's first rule accepts a reply that states what the reference states. The reply may use other words, and it may add detail that does not contradict the reference. A reply that says something the reference does not support is incorrect. The third rule covers a reference with several readings: the reply must answer every reading, and a partial answer is incorrect. Two further rules carry the case's decline into the judge. If the reference is the word "none", the docs do not answer the question, and the reply is correct only when it is exactly the decline sentence, "The docs don't say." And a reply that gives an answer and also says the decline sentence is incorrect. [Chapter 10](declining-when-the-docs-dont-say) measures the two kinds of error that this rule controls, and the judge applies the same rule to every reply.

The [calibration rubric](#what-a-judge-is-asked) is reference-free, so it has to say what counts as wrong without a reference to compare with. It tells the judge to judge correctness only, and it names what the judge must not grade: length, tone, style and formatting. It also says that a reply which makes no false claim is not incorrect, even if it is incomplete or asks for more information. That sentence is a decision. HelpSteer2 rates several attributes, and correctness is one of them. The rubric names correctness alone, so the question is set in the rubric and not left to the judge. [Chapter 6](calibrate-the-judge) measures how far the judge's narrower answer agrees with the human ratings.

When the reference is wrong, the judge fails correct replies, and the verdict gives no sign of it. A team reads a rise in fails as a weaker assistant when the fault is in the reference. Read a sample of fails against the reference before the rate is read.

**Working rule:** Use a reference whenever the set has one, and write the rule for an empty reference into the rubric, as the answer rubric does. Use a reference-free rubric only when no reference exists. In its text, name what the judge must not count against a reply, such as length, tone or incompleteness, so the rubric makes that choice and the judge does not.

## Pass, fail, or a scale {#pass-fail-or-scale}

A pass or fail rubric gives the judge two answers. A scale gives the judge several answers. The human ratings in HelpSteer2 are on a 0 to 4 scale, and a scale can look like more information than a yes or no. Its cost is in the boundaries. The judge has to tell one point from the next, and the team has to say what each point means and then check that the judge's points agree with the human ones. A pass or fail asks for one decision per reply, and every rate in this book is a rate of such decisions.

The answer rubric and both [calibration rubrics](#what-a-judge-is-asked) give pass or fail. The search for this chapter looked for a study that compares a scale with pass and fail on binary human labels, and it found none. So this choice is the book's design, not a finding from a source, and a reader should weigh it as a design.

The question this book asks is whether a reply is right, and that question has two answers. A reply can be almost right and still wrong on one fact or one command. A scale would give it a middle grade, and the team would then have to turn that grade into a yes or no before it could read any rate. The [pass rate](#a-pass-rate-and-its-interval) is the share of items the judge passes, over every item in the set, and a correct decline counts as a pass, as [chapter 10](declining-when-the-docs-dont-say) explains. A scale would need a different summary, such as a mean, and a mean hides which replies sit at which point. Take the decline item. A reply either declines or it does not. A scale would let a judge give a middle grade to a reply that declines and then adds a guess, which is the reply that [chapter 10](declining-when-the-docs-dont-say) counts as an error, and the team would then have to decide which side of the scale counts as passing.

**Working rule:** Use pass and fail when the team needs a yes or no on correctness, and report only rates of such decisions. Use a scale only when each step means something the team will act on, and when human ratings exist at each step to check the judge against. Say in the text which form the team chose and why, because that choice sets every rate the team reports. [Chapter 6](calibrate-the-judge) shows how the judge is compared with human ratings.

## One answer or two {#one-answer-or-two}

A pairwise judgment shows the judge two replies to the same request and asks which is better. It suits a team that must choose between two versions when an absolute grade is hard to set. The pairwise rubric gives the judge two letters, A or B, and no tie. Its cost is position. Each reply has a place in the prompt, first or second, and studies of judges report that the order can decide the pick. Those studies measure other judges in their own setups, and this book does not take their rates as its own. [Chapter 7](when-the-judge-stops-being-reliable#position) reviews them and measures the lean on this judge.

A pairwise judge has no scale points to define, and it only has to say which of two replies is better, which is exactly what a team choosing between two versions asks. It still has to be checked against human preferences, as [chapter 7](when-the-judge-stops-being-reliable#position) does for its consistent pairs. The cost is paid in position, which is why this section judges every pair twice.

The pairwise example uses human preference pairs from HelpSteer2. Each pair is judged twice: once with the first response shown as A, and once with the second response shown as A. Each verdict is then mapped back to the response it picked, so the two orders can be compared. A pair is consistent when the same response wins in both orders. It is order-changed when the same letter wins in both orders, which means the position decided the verdict; the example's output calls these flipped. Tie and unreadable are the two other kinds.

Example `pairwise-both-orders` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.3:

```python
"""How the pairwise judge's verdict on each HelpSteer2 preference pair depends on which response is shown as A. Each pair is
judged twice, once as ab (response_a shown as A) and once as ba (response_b shown as A), and both verdicts are mapped back
to the original responses. A flipped pair picked the same letter both times, so its verdict followed the position: the
flipped lines, on dev and on held-out, are the ones the point rests on.

Only the pair IDs of the examples are printed; the counts are the rates the chapter quotes."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.judging import KINDS, both_orders, human_pairs
from lib.stats import pct

AB = "judge-hs2-pairs-ab"
BA = "judge-hs2-pairs-ba"

pairs = human_pairs()  # all 150 pairs, sorted by id, each with its split
orders = both_orders(AB, BA, list(pairs))  # the two recordings, read for every pair, sorted by id

for split in ("dev", "held-out"):
    in_split = [p for p in pairs if pairs[p].split == split]
    for kind in KINDS:
        # the rate's denominator is the split's pairs, so a kind with no pairs still prints as 0 of that count
        n = sum(1 for o in orders if o.kind == kind and pairs[o.pair_id].split == split)
        print(f"{kind}, {split}: {pct(n, len(in_split))}")

for kind in KINDS:
    picked = [o.pair_id for o in orders if o.kind == kind][:3]  # the first three in id order
    print(f"examples, {kind}: {', '.join(picked) if picked else 'none'}")
```

Output:

```text
consistent, dev: 80.0% (60 of 75)
flipped, dev: 20.0% (15 of 75)
tie, dev: 0.0% (0 of 75)
unreadable, dev: 0.0% (0 of 75)
consistent, held-out: 74.7% (56 of 75)
flipped, held-out: 25.3% (19 of 75)
tie, held-out: 0.0% (0 of 75)
unreadable, held-out: 0.0% (0 of 75)
examples, consistent: hs2-pref-0001, hs2-pref-0002, hs2-pref-0005
examples, flipped: hs2-pref-0003, hs2-pref-0004, hs2-pref-0012
examples, tie: none
examples, unreadable: none
```

The count to keep is the order-changed count, not the winner count. On the dev split, the verdict changed with the order on:

20.0% (15 of 75).

The first order-changed pairs in id order are hs2-pref-0003, hs2-pref-0004, hs2-pref-0012. Ties are the third kind, and on dev the count is zero:

0.0% (0 of 75).

The parser reads a TIE line as well as A and B, so a reply that said TIE would be counted as a tie, not as an unreadable verdict. The pairwise rubric asks only for A or B, though, and no reply on dev gives a TIE. That is why the tie count is zero.

An order-changed pair is one where the verdict followed the position, so it says nothing about which reply is better. A reader who looked at one order only would count that pair as a win for one response. Which position wins is the subject of [chapter 7](when-the-judge-stops-being-reliable#position). This chapter shows only why one order is not enough.

**Working rule:** Judge every pair in both orders, map each verdict back to its response before you count, and report the order-changed count beside the winner count. Count an order-changed pair as no preference, and do not let it decide a comparison. If the order-changed count is high on a set, the comparison is measuring position, and a larger sample in one order does not fix that.

## Verdict first {#verdict-first}

The rubric asks for the verdict on the first line and one short sentence of reason on the next. The code reads only the first non-empty line. The check is short: one line has to hold the verdict, and a reply that does not begin with a verdict is not read as one. The reason comes after the verdict, so the reader and the code can both see the pick before the explanation.

`parse_verdict` returns PASS or FAIL when the first non-empty line is exactly that verdict, and it ignores asterisks or backticks around the line. Anything else returns nothing, and that is an unreadable verdict. It is not a FAIL. A FAIL means the judge judged the answer wrong, and an unreadable verdict means the judge gave no judgment at all. The code has two readers of verdicts, and they treat an unreadable verdict differently. `verdicts` in `lib/judging.py` stops with an error, so a run that reads through it cannot count the reply as a FAIL. `readable_verdicts` in `lib/calibration.py` prints each unreadable reply and leaves it out of the verdicts, and so out of the denominator. Most examples that report a rate read through it. A rate that leaves replies out prints their count beside it.

Fixed replies go through the parser, one line of output each, which prints the verdict, or the label `refused` for a reply with no readable verdict.

Example `parse-verdicts` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.3:

```python
"""What lib.contract.parse_verdict accepts and refuses: the verdict on a reply's first non-empty line, PASS or FAIL in capitals,
after optional emphasis marks. Each fixed reply below prints one line, the verdict or 'refused'. A refusal is not a FAIL:
the judge has not given a verdict, and the evaluation counts that as an error, not a failed answer."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import parse_verdict

CASES = (
    ("verdict first, PASS", "VERDICT: PASS\nReason: The answer matches the reference."),
    ("verdict first, FAIL", "VERDICT: FAIL\nReason: The answer gives a different version number."),
    ("emphasis around the line", "**VERDICT: FAIL**\nReason: The answer gives a different version number."),
    ("backticks around the line", "`VERDICT: PASS`\nReason: The answer matches the reference."),
    ("blank lines before the verdict", "\n\nVERDICT: PASS\nReason: The answer matches the reference."),
    ("no space after the colon", "VERDICT:PASS\nReason: The answer matches the reference."),
    ("two verdict lines, first one read", "VERDICT: FAIL\nVERDICT: PASS\nReason: Two verdicts."),
    ("lower case", "VERDICT: pass\nReason: The answer matches the reference."),
    ("title case", "Verdict: PASS\nReason: The answer matches the reference."),
    ("PARTIAL", "VERDICT: PARTIAL\nReason: Half of the answer matches."),
    ("verdict after a reason", "Reason: The answer matches the reference.\nVERDICT: PASS"),
    ("full stop after the verdict", "VERDICT: PASS.\nReason: The answer matches the reference."),
    ("words after the verdict", "VERDICT: PASS, mostly correct\nReason: The answer matches the reference."),
    ("bullet before the verdict", "- VERDICT: PASS\nReason: The answer matches the reference."),
    ("pairwise letter", "VERDICT: A\nReason: Response A is better."),
    ("bare word", "PASS\nReason: The answer matches the reference."),
    ("empty reply", ""),
    ("blank lines only", "  \n\n   "),
)

for label, raw in CASES:
    verdict = parse_verdict(raw)
    print(f"{label}: {verdict if verdict is not None else 'refused'}")
```

Output:

```text
verdict first, PASS: PASS
verdict first, FAIL: FAIL
emphasis around the line: FAIL
backticks around the line: PASS
blank lines before the verdict: PASS
no space after the colon: PASS
two verdict lines, first one read: FAIL
lower case: refused
title case: refused
PARTIAL: refused
verdict after a reason: refused
full stop after the verdict: refused
words after the verdict: refused
bullet before the verdict: refused
pairwise letter: refused
bare word: refused
empty reply: refused
blank lines only: refused
```

The first lines of the output show the forms the parser accepts. A verdict on the first line is read, and so is one with asterisks or backticks around it, blank lines above it, or no space after the colon. When two verdict lines appear, the parser reads the first, so a reply that says FAIL and then PASS is read as FAIL.

The unreadable lines matter most for a rubric. Lower case, title case and a PARTIAL verdict are all unreadable. So are a verdict placed after the reason, a full stop or extra words after PASS, a bullet in front of the verdict, a pairwise letter sent to a pass-or-fail rubric, a bare PASS with no label, an empty reply, and a reply of blank lines. Each unreadable form is a reply written in a shape the rubric did not ask for. A parser that guessed at what the judge meant would be reading the judge's intent, not its verdict.

The sentence to keep from this example is that a reply the parser cannot read is not a failed answer. It is a reply with no verdict, and no rate in this book turns it into a PASS or a FAIL. The book's advice is to print the unreadable count on each split. A split with more unreadable replies than the other is one the judge formats differently, which is worth finding out before the rate is read, since it may say more about the judge than about the assistant.

**Working rule:** Read the first non-empty line only. Never map an unreadable verdict to PASS or FAIL. Say in each rate what the run does with an unreadable verdict, whether it stops or leaves the reply out, and print the count beside any rate that leaves replies out. Check the parser on the replies the judge actually wrote, since a rubric that works on a sample can still lose verdicts to a format it did not ask for.

## Tuning the wording on dev {#tuning-the-wording}

The wording of a rubric is a setting, and a team will want to tune it until the judge agrees better with its labels. The risk is tuning on the numbers the team then reports. The book divides its items into two splits. [Dev](#read-the-outputs) is where wording is tuned. Held-out is run once, for each comparison a chapter reports, after the wording is fixed. A held-out split that has been used to choose the wording no longer tests it. Tuning a rubric on held-out items turns the reported agreement into a measure of the tuning, and then the agreement says nothing about the judge.

Before any tuning, the team writes the rule for each kind of item the set holds, in the rubric's own words: what passes, what fails, and what a decline is worth. Then it reads the dev replies the rubric gets wrong, one at a time, and changes the wording only when a reply shows a gap the rule does not cover. A change made to fit one reply is a change to the rubric, and it needs a recording of its own.

The answer rubric from [chapter 1](measure-before-you-change) is frozen. Its recording holds the hash of the wording that made it. Changing one word changes the hash, and the replay refuses the recording. A change therefore means the whole answer judge run is recorded again, for every reply, under the changed wording. This book does not tune that rubric, and a reader who wants to tune it should expect to re-record all of its replies.

[Rubric B](#what-a-judge-is-asked) is a second wording of the calibration task, and it is recorded on HelpSteer2. The calibration rubric says that a reply with no false claim is "not incorrect". Rubric B says that such a reply is "right", and it uses "right" and "wrong" where the calibration rubric uses "correct" and "incorrect". Rubric B also leaves out two points from the calibration rubric, that a reply must not mislead and that confidence must not be rewarded, and it drops formatting from the things the judge must not grade. Its instruction paragraph and its reply form read as follows. The rubric also has two made-up examples, which this chapter leaves out. They are part of the text that is hashed.

```
You grade whether an AI assistant's reply to a user is right.

A reply is right when every fact it states is true, every calculation or result in it is correct, and any code or reasoning in it works. Mark it wrong when any of those fail, or when it answers a different question from the one asked. A reply that makes no false claim is right, even when it is short, asks a question back, or leaves something out. Do not grade style, length or tone.

Reply in this form: on the first line, write exactly VERDICT: PASS if the reply is right, or VERDICT: FAIL if it is wrong. Then, on the next line, one short sentence of reason.
```

The example prints the hash of rubric B beside the other four, so a reader can tell the two calibration wordings apart. This chapter shows the text and the hash only, and [chapter 6](calibrate-the-judge) reports how well rubric B agrees with the human ratings.

The chapter made these decisions:

- The judge reads the first non-empty line only. Any other reply is an unreadable verdict, never a FAIL, and the two code paths that read verdicts are described above.
- Every rubric is hashed with its recording, and a changed rubric is a new rubric with a new recording.
- Every rate is pass and fail. A scale is not used, because the book has no human ratings at each step to check one against.
- A pairwise judge is run in both orders, and its order-changed pairs are reported beside its winner counts.

**Working rule:** Write the wording down before you run anything on held-out, and tune it on dev only. When the wording has to change, make it another rubric with its own recording and hash. Report each number with the hash of the wording that made it, so two wordings cannot be read as one.
