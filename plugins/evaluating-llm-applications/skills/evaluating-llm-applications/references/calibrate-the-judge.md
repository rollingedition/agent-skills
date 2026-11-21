---
title: "Evaluating LLM Applications"
chapter: "Measure a judge's errors against human ratings, then correct a pass rate"
chapter_id: calibrate-the-judge
book: evaluating-llm-applications
edition: 2026.11.2
verified: 2026-11-21
edition_code: G0M7-3TW7
canonical: https://rollingedition.com/evaluating-llm-applications/calibrate-the-judge
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Measure a judge's errors against human ratings, then correct a pass rate,” chapter 6 of Evaluating LLM Applications, Edition 2026.11.2, examples passed Nov 21, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/calibrate-the-judge. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Measure a judge's errors against human ratings, then correct a pass rate

By the end of this chapter you can measure how a judge's verdicts differ from human ratings, split those differences into misses and false passes, and correct an observed pass rate for them, with the assumption the correction rests on written beside it.

[Chapter 5](a-judge-with-a-rubric) ended with a second wording of the calibration task, and with the rule that a judge's wording is measured, not assumed. The answer judge reads each reply against a written reference and marks it PASS or FAIL, and the baseline run of the assistant gets its pass rate from that judge. The rate is a number about the judge as much as about the assistant, because a judge can pass a wrong reply or fail a right one. [Chapter 5](a-judge-with-a-rubric) wrote the rubric and read the verdicts. This chapter asks how often those verdicts are wrong, in which direction, and what a team does to a rate once it knows.

## Human ratings, and what they are {#human-ratings}

A judge can only be checked against labels that were made some other way. This book uses human ratings from [HelpSteer2](https://huggingface.co/datasets/nvidia/HelpSteer2), a public dataset from NVIDIA. Each row holds a prompt, one response to it, and five attribute scores from 0 to 4, given by people. The responses come from other models. This chapter uses one attribute, correctness. The sampling code turns the score into pass or fail: a score of 3 or 4 is read as PASS, and a score of 0 to 2 as FAIL. That cut is the book's choice, made before any judge was run.

HelpSteer2 is not the book's own data. Its responses come from other models, its prompts are general, and nobody wrote them for sablefile. So these labels measure how the judge does on a different question from the one the answer judge answers. That gap is the subject of [the transfer assumption](#transfer-assumption), and the rest of the chapter keeps returning to it.

The calibration judge reads with a rubric written for that one attribute. It asks whether every fact and result in a reply is right, and it tells the judge to set aside length, tone, style and formatting, as [chapter 5](a-judge-with-a-rubric#what-a-judge-is-asked) describes. The book's own test set could serve as the calibration, but the book has no human ratings of sablefile's replies. So the calibration uses public rows instead, and pays for that with the transfer assumption. The dataset does not hand the book a pass line for correctness. The book sets the line itself, and every rate in this chapter is read against it. A different line would move every rate, so a reader who compares this chapter with another study should first check where that study put its line.

The calibration rows are a sample of the dataset's validation split, drawn with a fixed seed. Rows whose text held characters outside printable ASCII were dropped before the draw. The draw takes about 45 FAIL and 45 PASS rows from each split, and it keeps one row per prompt. The base rate is therefore set by the sampling, not found in the dataset. The sample is split into dev and held-out. The same dataset also holds pairs of responses to one prompt, with a human preference between them. Pairs whose preference strength is zero are left out.

The split decides how the numbers may be used. Dev is where the book sets anything, including the rates a correction uses. Held-out is read once, in this chapter, after everything else is fixed, and nothing here is chosen with it. The held-out figures were first computed at the recording check, before this chapter was written. They are reported here as they stood, not recomputed to choose anything.

**Working rule:** Calibrate against labels made for the question the judge answers, or say in the text how far they are from it. Write down the rule that turns a score into the judge's pass or fail before you look at any result. Keep the split you tune on apart from the one you report once.

## Agreement and kappa {#agreement-and-kappa}

Agreement is the share of rows on which the judge and the human give the same verdict. It can mislead when one verdict dominates. A judge that passes everything agrees well with a sample that is mostly PASS, and agreement alone cannot tell that judge from a careful one. The fix is to ask what agreement the two verdicts would reach by chance, from their two PASS rates alone, and then take the chance out. Kappa does that. For two raters on pass or fail, kappa is the observed agreement minus the chance agreement, divided by one minus the chance agreement. [The kappa statistic, a review by McHugh](https://hrcak.srce.hr/file/132393), gives that formula. Kappa is one when the two raters agree on every row.

Example `calibration-agreement` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""How often the reference-free correctness judge agrees with the human ratings on the HelpSteer2 sample, and Cohen's kappa
for the same counts, on dev, on held-out and on both together.

Agreement alone reads higher than the judge's skill when most rows are one verdict, so the kappa line is the one to read
against chance: the chance agreement printed beside it is what the judge would reach by guessing at its own PASS rate."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import agreement, chance_agreement, cohens_kappa, confusion, helpsteer2_judgments
from lib.stats import pct

for label, split in (("all", None), ("dev", "dev"), ("held-out", "held-out")):
    counts = confusion(helpsteer2_judgments(split))
    print(f"agreement, {label}: {pct(counts.tp + counts.tn, counts.n)}")
    # the chance figure is an expected rate, not a count, so it has no denominator beside it
    print(f"chance agreement, {label}: {100 * chance_agreement(counts):.1f}%")
    # kappa is printed with two decimals (plan section 6.5), not as a percentage
    print(f"kappa, {label}: {cohens_kappa(counts):.2f}")
```

Output:

```text
agreement, all: 70.6% (127 of 180)
chance agreement, all: 50.3%
kappa, all: 0.41
agreement, dev: 71.1% (64 of 90)
chance agreement, dev: 50.2%
kappa, dev: 0.42
agreement, held-out: 70.0% (63 of 90)
chance agreement, held-out: 50.3%
kappa, held-out: 0.40
```

Agreement on all rows is 70.6% (127 of 180). Chance agreement, from the two PASS rates alone, is 50.3%. Kappa is 0.41, with two decimals and no percent sign, because it is a statistic on its own scale, not a rate. Agreement and chance agreement are both percentages, so they can be compared directly. Kappa is the figure that already has the chance taken out, so it is the one to read as the judge's agreement beyond chance.

Kappa runs from −1 to 1. It is 0 at chance agreement, and it is negative when the two raters agree less often than chance would, as [McHugh's review](https://hrcak.srce.hr/file/132393) notes.

Read the three figures in order: agreement, then the chance figure beside it, then kappa. If agreement rises while chance rises with it, the gain may come from the base rate rather than from the judge.

The two splits read the same way. On dev, agreement is 71.1% (64 of 90). Kappa on dev is 0.42. On held-out, agreement is 70.0% (63 of 90), and kappa is 0.40.

The base rate is the reason kappa matters. When one verdict dominates the rows, chance agreement is high, and a judge can post a high agreement while telling the two verdicts apart badly. Here the draw holds about as many PASS rows as FAIL rows, so chance agreement sits near half. The human PASS rate on dev is 51.1% (46 of 90). A team with a lopsided sample should expect chance agreement to sit near its agreement, so kappa is near zero even when agreement looks high. It should read kappa first.

Agreement measures closeness to the human labels, not whether the replies are right. High agreement says the judge's verdicts match the people's, not that the assistant's replies are right. Kappa tells you how far the agreement is from chance, but not which way the judge errs. That needs the next two rates.

Chapter 5 described a second calibration wording, rubric B. The calibration rubric, rubric A from here on, says that a reply which makes no false claim is "not incorrect". Rubric B rewords it: it says "right" where A says "not incorrect", and it drops the points about misleading and confidence. Rubric B was recorded on dev only. The next example sets the two wordings side by side on the same dev rows.

Example `rubric-b-agreement` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""How often the second rubric's verdicts agree with the human ratings on the HelpSteer2 sample, beside the first rubric's,
on dev and on held-out, with kappa, TPR and TNR and the PASS rates of judge and humans.

The second rubric was recorded on dev only, so its held-out line says so instead of printing a rate. The paired difference
is on dev alone: each dev row's agreement under rubric B minus its agreement under rubric A, bootstrapped over rows. A
reply with no readable verdict is printed by row ID and left out; it is never counted as FAIL."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from dataclasses import replace

from lib.calibration import cohens_kappa, confusion, helpsteer2_judgments, readable_verdicts
from lib.prompts import HS2B_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_points, pct

RUBRIC_B = "judge-helpsteer2-rubric-b"


def report(name, split, judgments):
    c = confusion(judgments)
    print(f"agreement, {name}, {split}: {pct(c.tp + c.tn, c.n)}")
    print(f"kappa, {name}, {split}: {cohens_kappa(c):.2f}")
    print(f"TPR, {name}, {split}: {pct(c.tp, c.tp + c.fn)}")
    print(f"TNR, {name}, {split}: {pct(c.tn, c.tn + c.fp)}")
    print(f"judge PASS rate, {name}, {split}: {pct(c.tp + c.fp, c.n)}")
    print(f"human PASS rate, {name}, {split}: {pct(c.tp + c.fn, c.n)}")


def same(j):
    return int(j.judge_pass == j.human_pass)


base = {j.id: j for j in helpsteer2_judgments()}  # rubric A's verdicts and the human PASS for every row, by id
recorded = {item for item, _ in ReplayModel(RUBRIC_B, HS2B_SHA256).keys()}
verdicts_b, unreadable = readable_verdicts(RUBRIC_B, sorted(recorded & base.keys()), HS2B_SHA256)
rows_b = {i: replace(base[i], judge_pass=v == "PASS") for i, v in verdicts_b.items()}

print(f"unreadable, rubric B: {len(unreadable)} of {len(recorded)} replies")
for item_id, _ in unreadable:
    print(f"unreadable, rubric B, row {item_id}: excluded, not counted as FAIL")
for split in ("dev", "held-out"):
    report("rubric A", split, [j for j in base.values() if j.split == split])
    b = [j for j in rows_b.values() if j.split == split]
    if b:
        report("rubric B", split, b)
    else:
        print(f"rubric B, {split}: no readable replies recorded")

dev_ids = [i for i in verdicts_b if base[i].split == "dev"]
diffs = [same(rows_b[i]) - same(base[i]) for i in dev_ids]  # the same row under both rubrics
lo, hi = bootstrap_mean(diffs)  # level 0.95 for one comparison; seed SEED, 2,000 resamples
n = len(dev_ids)
print(f"paired difference, dev: {100 * sum(diffs) / n:+.1f} points, 95% interval {interval_points(lo, hi)}, n = {n}")
reading = "rubric B better" if lo > 0 else "rubric B worse" if hi < 0 else f"no difference detected at n = {n}"
caveat = ", on dev only with no held-out run" if lo > 0 or hi < 0 else ""  # a dev-only difference carries its caveat
print(f"paired difference, dev, reading: {reading}{caveat}")
```

Output:

```text
unreadable, rubric B: 0 of 90 replies
agreement, rubric A, dev: 71.1% (64 of 90)
kappa, rubric A, dev: 0.42
TPR, rubric A, dev: 80.4% (37 of 46)
TNR, rubric A, dev: 61.4% (27 of 44)
judge PASS rate, rubric A, dev: 60.0% (54 of 90)
human PASS rate, rubric A, dev: 51.1% (46 of 90)
agreement, rubric B, dev: 74.4% (67 of 90)
kappa, rubric B, dev: 0.49
TPR, rubric B, dev: 84.8% (39 of 46)
TNR, rubric B, dev: 63.6% (28 of 44)
judge PASS rate, rubric B, dev: 61.1% (55 of 90)
human PASS rate, rubric B, dev: 51.1% (46 of 90)
agreement, rubric A, held-out: 70.0% (63 of 90)
kappa, rubric A, held-out: 0.40
TPR, rubric A, held-out: 82.6% (38 of 46)
TNR, rubric A, held-out: 56.8% (25 of 44)
judge PASS rate, rubric A, held-out: 63.3% (57 of 90)
human PASS rate, rubric A, held-out: 51.1% (46 of 90)
rubric B, held-out: no readable replies recorded
paired difference, dev: +3.3 points, 95% interval [-1.1, +7.8] points, n = 90
paired difference, dev, reading: no difference detected at n = 90
```

No difference shown on dev. Agreement under rubric B is 74.4% (67 of 90). Under rubric A, on the same rows, it is 71.1% (64 of 90). The paired difference is +3.3 points, 95% interval [-1.1, +7.8] points, n = 90. For each dev row, the code scores 1 when a wording agrees with the humans and 0 when it does not. The paired difference is rubric B's score minus rubric A's, averaged over the dev rows, and its interval is bootstrapped over those rows. The example's reading of that interval is no difference detected at n = 90.

The interval includes zero, so the dev estimate does not show that rubric B is better. Rubric B has no held-out run, so its dev estimate has no second check. Its unreadable replies are 0 of 90 replies, so no reply was left out.

**Working rule:** Report agreement beside kappa, and read kappa against the chance figure printed next to it. Name the rubric and the split with every number, so two wordings are never read as one. Call one wording better only when the lower bound of its paired interval is above zero, and only on held-out, or on dev with that caveat beside the claim. When the interval spans zero, say that no difference was detected at the n you have, and do not turn a higher point estimate into a claim.

## True positive and true negative rates {#tpr-and-tnr}

Agreement and kappa say how often the judge agrees with the humans. They do not say which way it errs. The two rates that do are the true positive rate and the true negative rate. The true positive rate, TPR, is the share of human PASS rows that the judge passes. The true negative rate, TNR, is the share of human FAIL rows that the judge fails. A judge that passes too much has a high TPR and a low TNR, because its errors are false passes. A judge that fails too much is the reverse. The correction in the next section needs both rates, since each one fixes a different error.

Example `tpr-tnr` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""The judge's true positive rate and true negative rate on the HelpSteer2 sample, with the counts beside each, on dev, on
held-out and on both together.

PASS is the positive class: TPR is the share of human PASS rows the judge passes, and TNR the share of human FAIL rows it
fails. The two rates are the judge's error profile; a lenient judge has a high TPR and a low TNR."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import confusion, helpsteer2_judgments
from lib.stats import pct

# PASS is the positive class: the rows a human rated PASS are the positives, and TPR is taken over them.
print("positive class: PASS")
for label, split in (("all", None), ("dev", "dev"), ("held-out", "held-out")):
    counts = confusion(helpsteer2_judgments(split))
    print(f"TPR, {label}: {pct(counts.tp, counts.tp + counts.fn)}")
    print(f"TNR, {label}: {pct(counts.tn, counts.tn + counts.fp)}")
```

Output:

```text
positive class: PASS
TPR, all: 81.5% (75 of 92)
TNR, all: 59.1% (52 of 88)
TPR, dev: 80.4% (37 of 46)
TNR, dev: 61.4% (27 of 44)
TPR, held-out: 82.6% (38 of 46)
TNR, held-out: 56.8% (25 of 44)
```

Here PASS is the positive class, so TPR is taken over the human PASS rows and TNR over the human FAIL rows. Each rate prints its counts beside it, so a reader can see how many rows it rests on.

On all rows, TPR is 81.5% (75 of 92). TNR is 59.1% (52 of 88). The judge passes most of the replies that humans passed, and it also passes a fair share of the replies humans failed. The weaker of the two rates is TNR, which makes this judge lenient.

The direction matters for anyone who reads a pass rate, and it depends on where the rate sits. The correction in the next section leaves a rate unchanged at the crossover point, p* = (1 − TNR) / (2 − TPR − TNR). Below p* the correction lowers the rate, and above p* it raises the rate. For a lenient judge, p* sits high, so a reported rate below it reads too high and a rate above it reads too low. On dev, the crossover point is 66.4% (TPR 80.4%, TNR 61.4%). Knowing where a rate sits against that point tells a team which way its reported number leans, before any correction is applied. Agreement alone would hide this. Two judges can agree with the humans to the same degree and still differ in which error they make more often, and the rates they report would differ with it.

On dev, TPR is 80.4% (37 of 46), and TNR is 61.4% (27 of 44). On held-out, TPR is 82.6% (38 of 46), and TNR is 56.8% (25 of 44). The held-out split lands close to dev on both rates, with TNR a few points lower.

Each rate is taken over one group of human labels, and each split has few enough rows that another sample could move the rates. This chapter prints no interval for TPR or TNR. Read the rates as the judge's error on this sample, not as its error in general.

**Working rule:** Report TPR and TNR together, with their counts, and say which way the judge errs. Take the rates a correction uses from dev alone, and quote both beside any corrected rate. Report held-out once, after the choices are made, and keep it out of every choice.

## Correcting a pass rate {#correcting-a-pass-rate}

The observed pass rate counts two kinds of verdict: true passes the judge caught, and false passes it let through. The correction tries to undo both at once. Given the judge's TPR and TNR, it solves for the true share of passes that would produce the observed rate. The book writes it as (observed + TNR - 1) / (TPR + TNR - 1). [Rogan and Gladen](https://doi.org/10.1093/oxfordjournals.aje.a112510) (1978) address the same problem for screening tests, and their abstract says that adjustments of this kind are given. The book has read only that abstract, so the formula here is the book's own statement of the correction, as its code computes it, and not a quotation from the paper.

The correction has a limit. It divides by TPR + TNR - 1. A judge whose two rates sit near what chance would give has a denominator near zero, and then small errors in either rate become large swings in the corrected rate. The book's code refuses to correct when that denominator is below 0.1, and it raises an error instead of printing a rate. The run below stays well clear of that floor. In practice a team does four things in order: measure TPR and TNR on a calibration set kept apart from the set it will correct, check that the denominator clears the floor, apply the correction to the observed rate over the readable replies, and write the transfer assumption beside the result.

Example `corrected-pass-rate` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.2:

```python
"""The baseline's answer-judge pass rate over the test items the judge gave a readable verdict, corrected for the judge's errors
with TPR and TNR from dev only. The corrected rate is printed beside the observed rate and the two rates the correction uses.

One judge reply has no PASS or FAIL on its first line. It is left out of the rate and printed by name, never counted as a
FAIL. The TPR and TNR come from HelpSteer2, where the judge rates other models' answers without a reference. This judge reads
the answers against a written reference. The correction assumes the two error profiles transfer; nothing here tests that.
The last lines apply the same correction to the calibration set itself: the rates are measured on those same rows, so that
check shows the arithmetic, not how well the correction generalises."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import (
    confusion,
    corrected_pass_rate,
    crossover_pass_rate,
    helpsteer2_judgments,
    readable_verdicts,
    tnr,
    tpr,
)
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import pct
from lib.testset import load_items

items = load_items()  # all 120 items of the test set, dev and held-out together
found, unreadable = readable_verdicts("judge-answers-baseline", [item.id for item in items], REF_SHA256)
details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
print(f"unreadable verdicts: {len(unreadable)}{details}")  # left out of the rate below, not counted as FAIL
passes = int(passed(found).sum())  # found is keyed in sorted id order
observed = passes / len(found)
print(f"observed pass rate, readable items: {pct(passes, len(found))}")

dev = confusion(helpsteer2_judgments("dev"))  # the only rows the correction's TPR and TNR may come from
print(f"TPR, dev: {pct(dev.tp, dev.tp + dev.fn)}")
print(f"TNR, dev: {pct(dev.tn, dev.tn + dev.fp)}")
# Below this observed rate the correction lowers the rate; above it, the correction raises it.
crossover = crossover_pass_rate(tpr(dev), tnr(dev))
print(f"crossover point, dev: {100 * crossover:.1f}% (TPR {100 * tpr(dev):.1f}%, TNR {100 * tnr(dev):.1f}%)")

corrected = corrected_pass_rate(observed, tpr(dev), tnr(dev))  # refused if TPR + TNR - 1 is below 0.1
print(f"corrected pass rate: {100 * corrected:.1f}%")

# The sanity check: the same correction on the calibration set, with rates measured on those same rows. It checks the
# arithmetic, not transfer to the answers: it should return the human PASS rate, and it does by construction.
calibration = confusion(helpsteer2_judgments())
judge_rate = (calibration.tp + calibration.fp) / calibration.n
print(f"calibration set, judge PASS rate: {pct(calibration.tp + calibration.fp, calibration.n)}")
print(f"calibration set, corrected judge PASS rate: {100 * corrected_pass_rate(judge_rate, tpr(calibration), tnr(calibration)):.1f}%")
print(f"calibration set, human PASS rate: {pct(calibration.tp + calibration.fn, calibration.n)}")
calibration_crossover = crossover_pass_rate(tpr(calibration), tnr(calibration))  # the same test, on the same rows
print(f"crossover point, calibration set: {100 * calibration_crossover:.1f}% "
      f"(TPR {100 * tpr(calibration):.1f}%, TNR {100 * tnr(calibration):.1f}%)")
```

Output:

```text
unreadable verdicts: 1 (q-0043, "VERDICT: PARTIAL")
observed pass rate, readable items: 76.5% (91 of 119)
TPR, dev: 80.4% (37 of 46)
TNR, dev: 61.4% (27 of 44)
crossover point, dev: 66.4% (TPR 80.4%, TNR 61.4%)
corrected pass rate: 90.5%
calibration set, judge PASS rate: 61.7% (111 of 180)
calibration set, corrected judge PASS rate: 51.1%
calibration set, human PASS rate: 51.1% (92 of 180)
crossover point, calibration set: 68.9% (TPR 81.5%, TNR 59.1%)
```

The input is the baseline's answer-judge verdicts for the test items, all 120 of them, dev and held-out together. One reply had no readable verdict, because its first line was not PASS or FAIL. The example prints it by name and leaves it out of the rate, since a reply the judge could not read is not a FAIL. [Chapter 5](a-judge-with-a-rubric#verdict-first) explains the two ways the code reads an unreadable verdict. The line for it reads 1 (q-0043, "VERDICT: PARTIAL"). [Chapter 1](measure-before-you-change#a-pass-rate-and-its-interval) defines the pass rate over every item in the set. This rate is over the readable items, so it departs from that definition by the one reply left out.

The observed pass rate over the readable items is 76.5% (91 of 119). The correction uses TPR and TNR from dev, and those are the only rows it may use. Its TPR on dev is 80.4% (37 of 46). Its TNR on dev is 61.4% (27 of 44).

The corrected rate is 90.5%. It estimates the share of sablefile's replies that a person would pass, under the book's correctness cut. It is not the judge's pass rate, which is the observed rate above, and it is not the assistant's accuracy. The estimate holds only if the judge's errors on sablefile's answers match its errors on HelpSteer2 rows. That is the [transfer assumption](#transfer-assumption), and the TPR and TNR above come from a reference-free judge rating other models' responses, while the answer judge checks sablefile's replies against a reference.

The corrected rate is higher than the observed rate, and the crossover point shows why. The observed rate sits above the crossover point, where the judge reads low. At that rate the judge's misses on true passes outweigh its false passes, so the correction raises it.

The result is also close to the code's ceiling. The code clips the corrected rate to the range from 0 to 1. The unclipped value passes 1 exactly when the observed rate is above TPR, because then the numerator is larger than the denominator. Here the observed rate sits under TPR by less than four points. If two of the dev PASS rows the judge passed had been failed instead, TPR would fall below the observed rate, and the corrected rate would print 100.0%.

**Working rule:** Correct a pass rate only with TPR and TNR measured on a calibration set. Quote both beside the corrected rate, refuse when the denominator is small, and say in the same paragraph what the correction assumes. The next section gives the interval and the one-row moves that go beside any corrected rate.

## How much one row moves the corrected rate {#how-much-one-row-moves-it}

Example `correction-sensitivity` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.2:

```python
"""How much the corrected pass rate of corrected-pass-rate depends on its inputs. A 95% bootstrap interval resamples both the
dev calibration rows and the readable test items, with the book's fixed seed. It prints the share of resamples that reach
the 100% cap, and the corrected rate when one dev row moves TPR or TNR up or down. Only dev rows set the correction's rates."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from dataclasses import replace

from lib.calibration import confusion, correction_interval, corrected_pass_rate, helpsteer2_judgments, readable_verdicts, tnr, tpr
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import RESAMPLES, interval_pct, pct
from lib.testset import load_items

items = load_items()  # all 120 items of the test set, as in corrected-pass-rate
found, _ = readable_verdicts("judge-answers-baseline", [item.id for item in items], REF_SHA256)
observed = int(passed(found).sum()) / len(found)

dev_rows = helpsteer2_judgments("dev")
dev = confusion(dev_rows)
lo, hi, capped, refused = correction_interval(dev_rows, passed(found))  # resamples the dev rows and the readable items
print(f"corrected pass rate, 95% interval: {interval_pct(lo, hi)}")
print(f"resamples at the 100% cap: {pct(capped, RESAMPLES)}")
print(f"resamples refused, TPR + TNR - 1 below 0.1: {pct(refused, RESAMPLES)}")

# One dev row moved: a human PASS row judged the other way changes TPR; a human FAIL row changes TNR.
moved = {
    "TPR one row higher": replace(dev, tp=dev.tp + 1, fn=dev.fn - 1),
    "TPR one row lower": replace(dev, tp=dev.tp - 1, fn=dev.fn + 1),
    "TNR one row higher": replace(dev, tn=dev.tn + 1, fp=dev.fp - 1),
    "TNR one row lower": replace(dev, tn=dev.tn - 1, fp=dev.fp + 1),
}
for label, counts in moved.items():
    print(f"corrected, {label}: {100 * corrected_pass_rate(observed, tpr(counts), tnr(counts)):.1f}%")
```

Output:

```text
corrected pass rate, 95% interval: [62.1%, 100.0%]
resamples at the 100% cap: 29.5% (590 of 2000)
resamples refused, TPR + TNR - 1 below 0.1: 0.1% (2 of 2000)
corrected, TPR one row higher: 86.0%
corrected, TPR one row lower: 95.5%
corrected, TNR one row higher: 91.0%
corrected, TNR one row lower: 90.0%
```

The example resamples both the dev rows and the readable items, 2,000 times, with the book's fixed seed, and it reads the spread of the corrected rate. The 95% interval is [62.1%, 100.0%]. It is wide, because TPR and TNR each rest on a few dozen dev rows, and its upper end is the cap itself. Some resamples reach the cap. Their share is 29.5% (590 of 2000). Resamples refused for a denominator under 0.1 are 0.1% (2 of 2000), and the interval is taken over the rest.

The one-row moves are these. If one dev row that humans passed had been judged PASS rather than FAIL, TPR would be one row higher, and the corrected rate would be 86.0%. If one such row had been judged FAIL, TPR would be one row lower, and the corrected rate would be 95.5%. For TNR, one dev row that humans failed and the judge passed would change the rate to 91.0% if it were judged FAIL, and to 90.0% if it were judged PASS. TPR is the rate to watch: one row there moves the answer by four to five points, while one row of TNR moves it by about half a point.

The interval covers the sampling of the dev rows and the readable items. It does not cover the transfer assumption. A judge whose errors differ on sablefile's replies could move the rate by more than the resamples show.

**Working rule:** Give the corrected rate with the bootstrap interval the book uses for its rates, the share of resamples at the cap, and the one-row moves beside it, so a reader can see how far single rows matter.

## The transfer assumption {#transfer-assumption}

The TPR and TNR above come from rows where the judge read other models' responses with no reference, under the correctness rubric, and the PASS line there is HelpSteer2 correctness of 3 or more. The answer judge reads sablefile's replies against a written reference, and a PASS there means the reply agrees with the reference, with a correct decline counting as a pass. The two judges answer different questions about what right means. The correction assumes that the judge's miss rate on human passes, and its pass-through rate on human fails, are the same on sablefile's replies as on the HelpSteer2 rows. Nothing in this chapter tests that. The correction holds only if the differences in input, replies, questions and PASS criterion leave the error profile unchanged. [Chapter 5](a-judge-with-a-rubric#reference-guided) sets out the difference between a judge with a reference and one without.

The last lines of the same example apply the correction to the calibration rows, with rates taken from those rows. On those rows, the judge's PASS rate is 61.7% (111 of 180). Its crossover point is 68.9% (TPR 81.5%, TNR 59.1%), and the judge's rate sits below it, so the correction lowers the rate. The corrected judge PASS rate is 51.1%. The human PASS rate is 51.1% (92 of 180).

The corrected judge rate returns the human rate. That follows from the algebra, because the rates were measured on those same rows. The check confirms that the arithmetic is right. It says nothing about whether the correction applies to sablefile, and a reader should not take it as evidence for the transfer.

The better fix is labels on the book's own replies. The book has none, because no person has rated sablefile's replies. A reader with such labels should calibrate on them, keeping a split apart from the set being corrected, as this chapter keeps dev apart from held-out. That would remove most of the transfer assumption, where the public rows only pay for it.

**Working rule:** Write the transfer assumption beside every corrected rate, in the same paragraph, and name the difference between the calibration judge and the judge the rate describes. Check the arithmetic on the rows the rates came from, and say that such a check does not test transfer. Until human labels on the answers the rate describes exist and have been checked against the judge, call the corrected rate an estimate that holds if the assumption does.

## Pairwise calibration {#pairwise-calibration}

A pairwise judge reads two replies and picks the better one, rather than passing or failing each. The human side is the HelpSteer2 preference between the two responses to a prompt. A pairwise judge has a known weakness: which reply sits in position A and which in B can decide the pick. [Chapter 5](a-judge-with-a-rubric#one-answer-or-two) explains why the book asks the judge about each pair in both orders, and [chapter 7](when-the-judge-stops-being-reliable#position) analyses the order changes that position causes. This section asks what agreement with the human preference looks like when both orders are counted. The order-changed count it prints is the one chapter 5 printed, and it is shown here only to explain the gap.

Each pair is a HelpSteer2 prompt with two responses and a human preference between them. Pairs with a tie were dropped, so every pair has a human pick. A TIE from the judge is a miss, because the judge said the two replies were equal when the human chose one. A single order gives a rate that depends on which letter the judge favoured, so a team that reports one order reports a number that the position of the replies can move. Counting both orders removes that freedom at the cost of a lower number. We recommend reporting the stricter rate for a pairwise judge, and reading the single-order rates only as a diagnostic of the gap between them.

Before you run the example, predict whether a pair that counts only when both orders pick the human's response will score above or below either order taken alone. Then check the guess against the output.

Example `pairwise-agreement` (Python 3.12.15 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""How often the pairwise judge's verdict agrees with the human preference on each HelpSteer2 pair, dev and held-out apart.
Three rates: the A,B order alone, the B,A order alone (both mapped back to the original responses), and both orders together,
where a pair counts only when both orders pick the human's response. A flipped pair (the same letter won both times) can
never count in the last rate, so the flipped count printed beside it is the number of misses that come from position.

Each single-order rate uses the pairs whose verdict in that order is readable; a TIE is judged and is not a pick, so it is
a miss. The interval is the 95% percentile bootstrap over pairs of the both-orders rate."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.judging import both_orders, human_pairs
from lib.stats import bootstrap_mean, interval_pct, pct

AB = "judge-hs2-pairs-ab"
BA = "judge-hs2-pairs-ba"

pairs = human_pairs()  # all 150 pairs, sorted by id, each with its split and the human's pick
orders = both_orders(AB, BA, list(pairs))  # both recordings read for every pair, sorted by id

for split in ("dev", "held-out"):
    rows = [o for o in orders if pairs[o.pair_id].split == split]
    human = {o.pair_id: pairs[o.pair_id].preferred for o in rows}
    ab = [o.ab == human[o.pair_id] for o in rows if o.ab is not None]
    ba = [o.ba == human[o.pair_id] for o in rows if o.ba is not None]
    both = [o.ab == human[o.pair_id] and o.ba == human[o.pair_id] for o in rows if o.ab is not None and o.ba is not None]
    flipped = sum(1 for o in rows if o.kind == "flipped")
    print(f"agreement, A,B order, {split}: {pct(sum(ab), len(ab))}")
    print(f"agreement, B,A order, {split}: {pct(sum(ba), len(ba))}")
    print(f"agreement, both orders, {split}: {pct(sum(both), len(both))}; flipped pairs: {flipped}")
    lo, hi = bootstrap_mean([float(hit) for hit in both])  # 95% interval over pairs, the level for one comparison
    print(f"95% interval, both orders, {split}: {interval_pct(lo, hi)}")
```

Output:

```text
agreement, A,B order, dev: 77.3% (58 of 75)
agreement, B,A order, dev: 73.3% (55 of 75)
agreement, both orders, dev: 65.3% (49 of 75); flipped pairs: 15
95% interval, both orders, dev: [53.3%, 76.0%]
agreement, A,B order, held-out: 74.7% (56 of 75)
agreement, B,A order, held-out: 76.0% (57 of 75)
agreement, both orders, held-out: 62.7% (47 of 75); flipped pairs: 19
95% interval, both orders, held-out: [52.0%, 73.3%]
```

Counted in both orders, agreement is lower than in either order alone, and the gap comes from the order-changed pairs. On dev, the A,B order alone gives 77.3% (58 of 75). The B,A order alone gives 73.3% (55 of 75). Counting both orders gives the stricter rate, 65.3% (49 of 75); flipped pairs: 15.

The count after the semicolon is the order-changed pairs, which the example's output labels flipped. An order-changed pair, as [chapter 5](a-judge-with-a-rubric#one-answer-or-two) defines it, is one where the verdict followed the position and not the reply. An order-changed pair can never count in the both-orders rate, so each one is a miss there.

The held-out split shows the same pattern. The A,B order gives 74.7% (56 of 75), the B,A order gives 76.0% (57 of 75), and both orders give 62.7% (47 of 75); flipped pairs: 19.

The interval on the both-orders rate, over pairs, is [53.3%, 76.0%] on dev. On held-out it is [52.0%, 73.3%]. These intervals are wide because each split has few pairs. The reading that holds is the pattern: a judge that changes its pick with position cannot be read as agreeing with people in any single order.

After this chapter the reader can measure a judge's agreement beyond chance, its misses and false passes on this sample, and a corrected pass rate with its transfer assumption written beside it. Those measures rest on public rows, not on sablefile's replies, and a pairwise judge counted in both orders still loses pairs to position. [Chapter 7](when-the-judge-stops-being-reliable) tests the limits a judge can show on the book's own recordings, starting with position, and it is where a reader learns when to stop trusting a verdict.

**Working rule:** When a judge compares two replies, run it in both orders, and report agreement counted both ways with the order-changed pairs beside it. Never read a single-order rate as the judge's agreement with people. Report the interval over pairs, and say that an order-changed pair is a miss, because it is the cost of position.
