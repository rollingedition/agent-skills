---
title: "Evaluating LLM Applications"
chapter: "Decide whether a change is better, and how many questions you need"
chapter_id: intervals-and-sample-size
book: evaluating-llm-applications
edition: 2026.11.2
verified: 2026-11-21
edition_code: G0M7-3TW7
canonical: https://rollingedition.com/evaluating-llm-applications/intervals-and-sample-size
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Decide whether a change is better, and how many questions you need,” chapter 8 of Evaluating LLM Applications, Edition 2026.11.2, examples passed Nov 21, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/intervals-and-sample-size. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Decide whether a change is better, and how many questions you need

By the end of this chapter you can say whether a difference between two versions of the assistant is more than noise, using an interval on a paired comparison. You can also work out how many questions a difference of a given size needs before a test can show it.

[Chapter 1](measure-before-you-change) measured the assistant once and gave its pass rate an interval. It then compared two prompts on twenty items. The interval on their difference was 30.0 points wide, and the chapter ended on a promise: a later chapter would work out how many items a difference needs before it can show. This chapter keeps that promise. A team that changes a prompt needs three answers. Did the rate move for a reason beyond the chance in the test? Was the comparison able to show a difference at all? And how many questions would it need to show the difference it cares about?

Every number here comes from one assistant model, Qwen3-4B-Instruct-2507, and one judge, the same model run at temperature zero. The intervals cover the spread that comes from drawing items. The first section measures the spread from sampling replies, without an interval. They don't cover the biases of the judge, which [Chapter 7](when-the-judge-stops-being-reliable) tests. Read each result with that in mind.

## Variance within one item {#variance-within-one-item}

Ask the same question twice and a model can answer differently. This chapter's comparisons use one recorded reply per item and prompt, so each verdict rests on one reply. At a higher temperature the model samples, and an item's verdict can change from one sample to the next. That matters for comparisons. A difference between two prompts that is smaller than the swing from one sample to the next isn't a difference at all, and a rate read from one run hides the swing.

The variance set holds five samples of the assistant's reply to each dev item, drawn at temperature 0.7. The judge reads every reply at temperature zero. An item flips when its five verdicts are not all the same. Counting the flips gives a measure of how much the verdicts move from sample to sample, before any change is made.

Example `flip-rate` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.2:

```python
"""The flip rate over the dev variance set: the share of items whose judge verdict differs across their five samples. The
printed line 'flip rate' rests on the per-item PASS counts, which are printed with it: how many items passed 0, 1, 2, 3, 4
or 5 of 5 samples, and the mean pass rate. The temperature-0 baseline's pass rate over the same items is printed for
comparison. An item with an unreadable verdict is printed by id and left out, never counted as FAIL."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import pct
from lib.testset import load_items
from lib.variance import VARIANCE_SAMPLES, item_pass_counts

VARIANCE = "judge-answers-variance"
BASELINE = "judge-answers-baseline"
SAMPLES = len(VARIANCE_SAMPLES)

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
counts = item_pass_counts(VARIANCE, items)
excluded = [row for row in counts if not row.complete]
kept = [row for row in counts if row.complete]
for row in excluded:
    samples = ", ".join(str(sample) for sample in row.unreadable)
    print(f"unreadable, {row.item_id}: samples {samples} (left out, not counted as FAIL)")
print(f"left out of the flip rate (unreadable verdict): {len(excluded)}")

n = len(kept)
print(f"variance items compared (n): {n}")
print(f"flip rate: {pct(sum(1 for row in kept if row.flaky), n)}")
spread = [sum(1 for row in kept if row.passes == passes) for passes in range(SAMPLES + 1)]
assert sum(spread) == n  # every kept item falls in exactly one PASS count
for passes, count in enumerate(spread):
    print(f"items with {passes} of {SAMPLES} PASS: {count}")
print(f"mean per-item pass rate across samples: {pct(sum(row.passes for row in kept), n * SAMPLES)}")

found, baseline_unreadable = readable_verdicts(BASELINE, [row.item_id for row in kept], REF_SHA256)
assert not baseline_unreadable  # q-0043 is already left out above, so no kept item is unreadable under the baseline
baseline = passed(found)
print(f"baseline pass rate, same items (temperature 0): {pct(int(baseline.sum()), len(baseline))}")
```

Output:

```text
unreadable, q-0043: samples 1, 4 (left out, not counted as FAIL)
left out of the flip rate (unreadable verdict): 1
variance items compared (n): 79
flip rate: 2.5% (2 of 79)
items with 0 of 5 PASS: 16
items with 1 of 5 PASS: 1
items with 2 of 5 PASS: 0
items with 3 of 5 PASS: 0
items with 4 of 5 PASS: 1
items with 5 of 5 PASS: 61
mean per-item pass rate across samples: 78.5% (310 of 395)
baseline pass rate, same items (temperature 0): 78.5% (62 of 79)
```

Counting per item, the code tallies how many of its five samples the judge passed. An item with a verdict that can't be read is left out, not counted as a fail, and the output names the item it left out.

Most items don't move. 61 items pass all five samples, and 16 fail all five. Of the items that flip, 1 passes one sample and 1 passes four.

The flip rate is 2.5% (2 of 79).

The mean pass rate across all the samples is 78.5% (310 of 395). The baseline, one reply per item at temperature zero, passes 78.5% (62 of 79). The two are equal, and the two flipping items pull in opposite directions. That holds for P1, the prompt the variance set uses, and another prompt might be less steady.

That is a narrow result. A set with more borderline questions would flip more, and the flip rate counts items and has no interval of its own. A count of flipping items this small says little about how often the next change will flip.

The flip rate measures only the spread that comes from sampling this assistant's replies, with the items held fixed. A comparison between two prompts also moves with the items each prompt gets right. The last section uses that sampling spread as a lower bound, and only for a comparison that samples its replies: [How many questions a difference needs](#how-many-questions).

**Working rule:** Before you trust one run's rate, run the variance set at the temperature you ship, and read the flip rate beside the mean pass rate. The flip rate says how far sampling moves one prompt's verdicts. It bounds a comparison only when that comparison samples its replies too.

## The bootstrap over items {#bootstrap-over-items}

[Chapter 1](measure-before-you-change#a-pass-rate-and-its-interval) showed an interval on a pass rate and used it to read a small set. This section explains the method, because the rest of the chapter uses it three ways: on a rate, on a paired difference, and on a difference that has to clear a stricter level.

The method is the percentile bootstrap. The items in a set are one sample of the questions a team could have written, so a different set would give a somewhat different rate. To estimate how much, draw items from the set with replacement, as many as the set holds, so that some items come up twice and some not at all. Compute the statistic for that draw, repeat the draw many times, and keep the middle 95% of the results. The bootstrap adds no data. It reuses the items the set already has, and it shows how far the statistic would move if the set had been another draw of the same kind.

The unit of resampling is the item, and that is the rule to keep. For a rate, each item contributes its verdict. For a paired difference, each item contributes one number: the verdict of prompt B minus the verdict of the baseline, which is plus one, zero or minus one. For the variance set, the five samples of an item are kept together, because they answer one question. Drawing them apart would make them look like five independent questions, and the interval would come out too narrow. [Miller (2024)](https://arxiv.org/abs/2411.00640) makes the same point for questions that come in related groups. That paper is a preprint and a practitioner's note, not a reviewed method, so this book uses it for the reason and not as proof.

The book fixes the settings so that a number can be reproduced. The method draws 2,000 resamples with a seed of zero, and it creates a fresh random generator inside each call. The same data therefore gives the same interval, whatever ran before it. The seed is a choice, not a property of the data. A different seed moves the endpoints a little, which is why the settings are written down.

The method also depends on the set being a fair sample of the questions, which [Chapter 1](measure-before-you-change) argued and no interval can check. A small set gives a rough interval. The endpoints of a percentile interval on a set of this size are a first estimate, and they should be read as approximate.

**Working rule:** Resample items, never runs within an item, and keep an item's samples together. Fix the resample count and the seed in the code, so the same data gives the same interval. When the set holds few items, call the interval rough and say so beside it.

## Paired comparisons {#paired-comparisons}

Two prompts answer the same questions, so their results are paired. For each item, subtract the verdict of the baseline from the verdict of prompt B, and average the differences over the set. The average is the comparison, and its interval comes from the bootstrap over items.

Pairing matters because most items agree. An item that both prompts pass, or both fail, contributes nothing to the difference, whatever the question's difficulty. The comparison's spread comes from the items on which the two prompts split. An unpaired comparison takes two separate pass rates and sets them side by side. It carries the variation between questions on every item, including the ones that agree, and that variation can hide a real difference. The paired version cancels the part the two prompts share. The argument for paired differences in Miller (2024) says the same: the variance of a paired difference falls as long as the two models' scores on each item are positively correlated.

Example `paired-prompt-b` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.2:

```python
"""Compares prompt-b (P2) with the baseline prompt (P1) on the eighty dev items: each pass rate, the paired difference with
its 95% interval, and how the items split between the two prompts. 'Better' is used only when the whole interval is above
zero (plan section 6.4); the interval here includes zero, so the reading is no difference detected."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import bootstrap_mean, interval_points, pct
from lib.testset import load_items

BASELINE = "judge-answers-baseline"
PROMPT_B = "judge-answers-prompt-b"

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
p1_found, p1_unreadable = readable_verdicts(BASELINE, items, REF_SHA256)
p2_found, p2_unreadable = readable_verdicts(PROMPT_B, items, REF_SHA256)
for label, unreadable in (("P1 (baseline)", p1_unreadable), ("P2 (prompt-b)", p2_unreadable)):
    details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
    print(f"unreadable verdicts, {label}: {len(unreadable)}{details}")
# An item without a readable verdict under either prompt is dropped from both sides: a paired difference needs the same items.
excluded = {item_id for item_id, _ in p1_unreadable + p2_unreadable}
kept = [item_id for item_id in items if item_id not in excluded]
first = passed({item_id: p1_found[item_id] for item_id in kept})  # 1.0 or 0.0 per item, in id order
second = passed({item_id: p2_found[item_id] for item_id in kept})

n = len(kept)
lo, hi = bootstrap_mean(second - first)  # 95%, one comparison: the default level
print(f"P1 (baseline) pass rate: {pct(int(first.sum()), n)}")
print(f"P2 (prompt-b) pass rate: {pct(int(second.sum()), n)}")
print(f"difference, P2 minus P1: {100 * float((second - first).mean()):+.1f} points")
print(f"95% interval of the difference: {interval_points(lo, hi)}")
print(f"paired items (n): {n}")
print(f"items only P1 passes: {int(((first == 1) & (second == 0)).sum())}")
print(f"items only P2 passes: {int(((first == 0) & (second == 1)).sum())}")
print(f"items both pass: {int(((first == 1) & (second == 1)).sum())}")
print(f"items neither passes: {int(((first == 0) & (second == 0)).sum())}")
if lo > 0:
    print(f"reading: P2 is better at n = {n}")
elif hi < 0:
    print(f"reading: P2 is worse at n = {n}")
else:
    print(f"reading: no difference detected at n = {n}")
```

Output:

```text
unreadable verdicts, P1 (baseline): 1 (q-0043, "VERDICT: PARTIAL")
unreadable verdicts, P2 (prompt-b): 0
P1 (baseline) pass rate: 78.5% (62 of 79)
P2 (prompt-b) pass rate: 81.0% (64 of 79)
difference, P2 minus P1: +2.5 points
95% interval of the difference: [-3.8, +10.1] points
paired items (n): 79
items only P1 passes: 3
items only P2 passes: 5
items both pass: 59
items neither passes: 12
reading: no difference detected at n = 79
```

Here prompt B runs against the baseline on the dev items. An item with a verdict that can't be read under either prompt is left out of both sides, because a paired difference needs the same items on both sides. The printed lines give each pass rate, the difference, its interval and the number of paired items.

The baseline passes 78.5% (62 of 79). Prompt B passes 81.0% (64 of 79). The difference, prompt B minus the baseline, is +2.5 points, with a 95% interval of [-3.8, +10.1] points.

The split shows where the difference lives. 59 items pass under both prompts, and 12 fail under both. Only the items that split move the difference: 5 pass only under prompt B, and 3 pass only under the baseline.

The interval includes zero, so the reading is no difference detected at n = 79. The interval runs from a drop to a rise, and this set can't say which end is nearer. No difference detected is a finding about this set at this size. It is not a claim that the prompts are equal, and the text shouldn't say they are.

**Working rule:** Compare variants on the same items, paired, and report the difference with its interval and n. Call one variant better only when the whole interval sits above zero, and worse only when the whole interval sits below it. When the interval includes zero, report no difference detected at that n, and say how many items the difference would need, as [How many questions a difference needs](#how-many-questions) works out.

## Held-out, once {#held-out-once}

Dev items are for building. A team may tune a prompt on them, read the failures and change the next version. The dev results can't then prove that a change works, because the change was shaped by them. The held-out set is the check that isn't tuned. A comparison on held-out is run once, against rules fixed before the run: the variants, the level and the reading. Run it again after a change of mind, or choose the level after seeing the number, and the interval no longer means what it says.

This section runs three comparisons on the held-out set, each variant against the baseline. Prompt B is the one from [Paired comparisons](#paired-comparisons). The variant k5 retrieves five sections instead of three. The variant unfiltered retrieves from every version of the docs at once, with three sections, instead of only the asked version.

Example `held-out-variants` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.2:

```python
"""Compares prompt-b, k5 and unfiltered with the baseline on the held-out items, each variant once, at the level the
Bonferroni rule gives for three comparisons (98.33%). Each variant gets its paired difference, interval, n and a reading by
plan section 6.4. Nothing was chosen with these numbers: the variants, the level and the reading rule were fixed before
this run, and the run happens once."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import RESAMPLES, bootstrap_mean, interval_points
from lib.testset import load_items

BASELINE = "baseline"
VARIANTS = ("prompt-b", "k5", "unfiltered")
M = len(VARIANTS)  # one comparison per variant, each against the baseline
LEVEL = 1 - 0.05 / M  # Bonferroni: 1 - 0.05/m, which is 98.33% for m = 3 (plan section 6.3)

items = [item.id for item in load_items(split="held-out")]  # sorted by id
print(f"comparisons (m): {M}")
print(f"share of the 5% for each comparison, 0.05 / m: {0.05 / M:.4f}")
print(f"level of each interval, 1 - 0.05 / m: {100 * LEVEL:.2f}%")
print(f"resamples beyond each end of an interval: {RESAMPLES * (1 - LEVEL) / 2:.1f}")
base_found, base_unreadable = readable_verdicts(f"judge-answers-{BASELINE}", items, REF_SHA256)
details = "".join(f' ({item_id}, "{first}")' for item_id, first in base_unreadable)
print(f"unreadable verdicts, baseline: {len(base_unreadable)}{details}")
for name in VARIANTS:
    found, unreadable = readable_verdicts(f"judge-answers-{name}", items, REF_SHA256)
    details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
    print(f"unreadable verdicts, {name}: {len(unreadable)}{details}")
    # An item unreadable under the baseline or this variant is dropped from both sides of this pair only.
    excluded = {item_id for item_id, _ in base_unreadable + unreadable}
    kept = [item_id for item_id in items if item_id not in excluded]
    first = passed({item_id: base_found[item_id] for item_id in kept})
    second = passed({item_id: found[item_id] for item_id in kept})
    n = len(kept)
    lo, hi = bootstrap_mean(second - first, level=LEVEL)
    if name == "prompt-b":  # the chapter says this lower end is exactly zero, so the run must show it
        assert lo == 0.0, "the prompt-b lower bound must be exactly zero"
    print(f"{name} minus baseline, difference: {100 * float((second - first).mean()):+.1f} points")
    print(f"{name} minus baseline, {100 * LEVEL:.2f}% interval: {interval_points(lo, hi)}")
    print(f"{name} minus baseline, n: {n}")
    if lo > 0:
        print(f"{name} minus baseline, reading: better at n = {n}")
    elif hi < 0:
        print(f"{name} minus baseline, reading: worse at n = {n}")
    else:
        print(f"{name} minus baseline, reading: no difference detected at n = {n}")
```

Output:

```text
comparisons (m): 3
share of the 5% for each comparison, 0.05 / m: 0.0167
level of each interval, 1 - 0.05 / m: 98.33%
resamples beyond each end of an interval: 16.7
unreadable verdicts, baseline: 0
unreadable verdicts, prompt-b: 0
prompt-b minus baseline, difference: +10.0 points
prompt-b minus baseline, 98.33% interval: [+0.0, +22.5] points
prompt-b minus baseline, n: 40
prompt-b minus baseline, reading: no difference detected at n = 40
unreadable verdicts, k5: 0
k5 minus baseline, difference: +2.5 points
k5 minus baseline, 98.33% interval: [-12.5, +18.4] points
k5 minus baseline, n: 40
k5 minus baseline, reading: no difference detected at n = 40
unreadable verdicts, unfiltered: 0
unfiltered minus baseline, difference: -10.0 points
unfiltered minus baseline, 98.33% interval: [-27.5, +8.4] points
unfiltered minus baseline, n: 40
unfiltered minus baseline, reading: no difference detected at n = 40
```

Three comparisons share one held-out set, so each interval is set at a higher level than 95%, and [Many comparisons](#many-comparisons) explains why. The level is 98.33%. Each variant gets a difference, an interval, a count of paired items and a reading, all printed.

Held-out has 40 items, against 79 on dev. So its intervals are wider for the same difference, and a result on it can only be as sharp as its item count allows. The split keeps a result honest, and its cost is fewer items to spend.

The difference for prompt B is +10.0 points, with an interval of [+0.0, +22.5] points. The comparison has 40 paired items.

The k5 difference is +2.5 points, with an interval of [-12.5, +18.4] points. The unfiltered difference is -10.0 points, with an interval of [-27.5, +8.4] points.

Dev gave +2.5 points for the same prompt, and the two point estimates differ. The 40 held-out items can't tell which is nearer the truth. The smallest difference that they detect, at 98.33% confidence and 80% power, is 16.2 points, so both point estimates sit below what this set can detect. [How many questions a difference needs](#how-many-questions) works out the arithmetic.

By the rule, all three read as no difference detected. For prompt B the printed reading is no difference detected at n = 40. For k5 it is no difference detected at n = 40, and for unfiltered no difference detected at n = 40.

Prompt B is the close case. Its interval is [+0.0, +22.5] points, and its lower end is exactly zero. The reading rule says better only when the whole interval sits above zero, and this one reaches zero without clearing it, so by the rule the reading is no difference detected. Beyond each end of the interval lie 16.7 of the 2,000 resamples, so the call sits on the line. The seed was fixed before the run for that reason. A reader could argue that a point estimate of that size should count for something, and this section doesn't make that argument. The rule was set before the run, the comparison runs once, and nobody gets to look at these three again with a lower level or a different reading. If prompt B is to be tested further, it needs a fresh held-out set, sized by [How many questions a difference needs](#how-many-questions) and fixed before anyone sees its results, read on its own. Adding items to the 40 already read, and rereading the pool, would be a second look at a result already seen.

**Working rule:** Fix the variants, the level and the reading rule before you open the held-out set, and run each comparison once. An interval that reaches zero is no difference detected at that n. Don't rerun the comparison, lower the level or change the reading to get a different answer. Add held-out items only before they are scored.

## Many comparisons {#many-comparisons}

Each comparison is a chance to be fooled. A 95% interval on a comparison with no real difference still excludes zero by luck about one time in twenty. Run three such comparisons, report each at 95%, and the chance that at least one of them reads as a difference rises above five in a hundred. The more comparisons a chapter reports, the more likely one of them is a lucky result.

The usual fix is the Bonferroni correction, which shares the error budget between the comparisons. With m comparisons of one metric, each interval is set at 1 minus 0.05 divided by m. For three comparisons, 0.05 divided by 3 is 0.0167, so each interval's level is 98.33%, the level the [held-out section](#held-out-once) used. The 0.05 is split between the two tails of each interval, so each tail gets 0.05 divided by twice m. The arithmetic holds whatever the comparisons have in common. The chance that any of them shows a false difference can't exceed the sum of their separate chances, and that sum is 5%.

The code computes the level from m and prints it, so a reader can check it against the count. The price is width. At this level each interval is wider than a 95% one, so a difference has to be larger before its interval clears zero. The sum of the separate chances is an upper bound on the chance of any false difference, so the correction is conservative whenever the comparisons' false results overlap. This book uses this one because its rule is short to state and to check, and a reader can recompute it from the count.

Which comparisons form the count? In this chapter, the dev comparison in the paired section stands alone, and it is reported at 95% because it is a worked example on tuning data. The three held-out comparisons form a family, and they are reported at the adjusted level. A reader who sees both should not read the dev interval as a held-out result, and the held-out result is the one the chapter relies on.

The count is part of the design. Count the comparisons of one metric that the chapter will report before you run any of them. A comparison added after the results is reported apart from the family, as exploratory, with its own count. The family's intervals stay as they were run, because setting them again after the results would change the rule the run was held to.

**Working rule:** Count the comparisons of one metric before you run them, and set each interval's level at 1 minus 0.05 divided by that count. Show the level beside every interval. A comparison added after the results is reported apart as exploratory, and the family's intervals are not set again.

## How many questions a difference needs {#how-many-questions}

The question to ask before a comparison is how many items it needs to show a difference of the size the team cares about. The answer depends on one quantity: how much the two variants disagree, item by item. Two prompts that disagree on few items show a small difference with few items.
The paired formula makes this concrete. Write z-conf for the two-sided normal value at the confidence level and z-power for the one at the power. Then n = (z-conf + z-power)² · var(d) / δ², where var(d) is the variance of one item's paired difference and δ is the difference to detect. The variance is the share of items on which the two variants disagree, minus the square of their average difference. So the estimate is driven by disagreement, not by the pass rates themselves. This section uses 95% confidence and 80% power.

Example `sample-size` (Python 3.12.15 · bm25s 0.3.16 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.2:

```python
"""How many items a paired comparison needs to detect a difference of 5 and of 10 points, with 95% confidence and 80% power.

The main estimate reads the paired differences that prompt-b and the baseline show on the dev items: each item's d is
+1, 0 or -1 (P2 minus P1), and the items on which they disagree set the variance. The floor uses only the judge's
within-item sampling noise over five samples; it leaves the disagreement between variants out, so it is a lower bound.
"""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib import variance
from lib.answers import chapter_items
from lib.calibration import readable_verdicts
from lib.judging import paired, passed
from lib.prompts import REF_SHA256
from lib.stats import pct
from lib.testset import load_items

# n = (z_alpha + z_beta)^2 * var_d / delta^2, rounded up (variance.items_needed). var_d = p_discordant - mean(d)^2.
# Smallest difference that n items detect: (z_alpha + z_beta) * sqrt(var_d / n) (variance.smallest_difference_points).
BASELINE, PROMPT_B = "judge-answers-baseline", "judge-answers-prompt-b"
CHAPTER_ONE_ITEMS = 20  # the chapter 1 set, read below the way twenty-cannot-tell reads it

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
p1_found, p1_unreadable = readable_verdicts(BASELINE, items, REF_SHA256)
p2_found, p2_unreadable = readable_verdicts(PROMPT_B, items, REF_SHA256)
kept = [item_id for item_id in items if item_id not in {i for i, _ in p1_unreadable + p2_unreadable}]
first = passed({item_id: p1_found[item_id] for item_id in kept})  # 1.0 or 0.0 per item
second = passed({item_id: p2_found[item_id] for item_id in kept})
var_d = variance.paired_difference_variance(first, second)
print(f"share of discordant items, P2 and P1 disagree: {pct(int((first != second).sum()), len(kept))}")
print(f"assumption, the next change disagrees with the baseline on about as many items as prompt-b did "
      f"({100 * (first != second).mean():.1f}% of items)")

# Floor: five samples of a 0/1 verdict with k PASS give the unbiased within-item variance k(5 - k) / (5 * 4).
rows = [row for row in variance.item_pass_counts("judge-answers-variance", items) if row.complete]
noise = sum(row.passes * (5 - row.passes) / 20 for row in rows) / len(rows)
print(f"floor, sampling noise only: dev items with five readable verdicts (n): {len(rows)}")
print(f"floor, sampling noise only: mean within-item variance of one verdict: {noise:.4f}")

# Two variants judged separately: their two noises add and the item's difficulty cancels, so the floor is 2 * noise.
for label, var in (("main estimate", var_d), ("floor, sampling noise only", 2 * noise)):
    print(f"{label}, variance of one item's paired difference: {var:.4f}")
    for delta in (5.0, 10.0):
        print(f"{label}, items needed for a {delta:.0f}-point difference: {variance.items_needed(var, delta)}")
    print(f"{label}, smallest difference that {CHAPTER_ONE_ITEMS} items detect, 80% power and 95% confidence: "
          f"{variance.smallest_difference_points(var, CHAPTER_ONE_ITEMS):.1f} points")

# The chapter 1 set, read as twenty-cannot-tell reads it: its share of discordant items and its interval width.
chapter_one = paired(BASELINE, PROMPT_B, [item.id for item in chapter_items()])
width_20 = variance.interval_width_points(var_d, CHAPTER_ONE_ITEMS)
print(f"chapter 1 set, share of items where the two verdicts differ: "
      f"{pct(int((chapter_one.first != chapter_one.second).sum()), chapter_one.n)}")
print(f"chapter 1 set, 95% interval width: {100 * (chapter_one.diff_hi - chapter_one.diff_lo):.1f} points")
print(f"main estimate, 95% width at {CHAPTER_ONE_ITEMS} items: {width_20:.1f} points")
print(f"reading: with {CHAPTER_ONE_ITEMS} items and a change that disagrees with the baseline on "
      f"{100 * (first != second).mean():.1f}% of items, as prompt-b did, the smallest difference detected with 80% power "
      f"at 95% confidence is {variance.smallest_difference_points(var_d, CHAPTER_ONE_ITEMS):.1f} points")
```

Output:

```text
share of discordant items, P2 and P1 disagree: 10.1% (8 of 79)
assumption, the next change disagrees with the baseline on about as many items as prompt-b did (10.1% of items)
floor, sampling noise only: dev items with five readable verdicts (n): 79
floor, sampling noise only: mean within-item variance of one verdict: 0.0051
main estimate, variance of one item's paired difference: 0.1006
main estimate, items needed for a 5-point difference: 316
main estimate, items needed for a 10-point difference: 79
main estimate, smallest difference that 20 items detect, 80% power and 95% confidence: 19.9 points
floor, sampling noise only, variance of one item's paired difference: 0.0101
floor, sampling noise only, items needed for a 5-point difference: 32
floor, sampling noise only, items needed for a 10-point difference: 8
floor, sampling noise only, smallest difference that 20 items detect, 80% power and 95% confidence: 6.3 points
chapter 1 set, share of items where the two verdicts differ: 10.0% (2 of 20)
chapter 1 set, 95% interval width: 30.0 points
main estimate, 95% width at 20 items: 27.8 points
reading: with 20 items and a change that disagrees with the baseline on 10.1% of items, as prompt-b did, the smallest difference detected with 80% power at 95% confidence is 19.9 points
```

Here the code reads the disagreement between prompt B and the baseline on the dev items. Its assumption is printed, and it is the one to check: the next change disagrees with the baseline on about as many items as prompt B did. Here the share of items that disagree is 10.1% (8 of 79).

Example `sample-size-limits` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.2:

```python
"""The arithmetic behind the five-point figure in sample-size, and the limits of its inputs: the interval on the share of
discordant items (a percentile bootstrap over items, as lib.stats computes every interval), the held-out level of 98.33%,
and the difference that the 40 held-out items can detect. The disagreement is the dev items' paired run, as in sample-size."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib import variance
from lib.calibration import readable_verdicts
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import bootstrap_mean, interval_pct
from lib.testset import load_items

BASELINE = "judge-answers-baseline"
PROMPT_B = "judge-answers-prompt-b"
ALPHA_HELD_OUT = 0.05 / 3  # two-sided alpha for each of the three held-out comparisons (Bonferroni)
HELD_OUT_LEVEL = 1 - ALPHA_HELD_OUT

items = [item.id for item in load_items(split="dev")]  # eighty dev items, sorted by id
p1_found, p1_unreadable = readable_verdicts(BASELINE, items, REF_SHA256)
p2_found, p2_unreadable = readable_verdicts(PROMPT_B, items, REF_SHA256)
kept = [item_id for item_id in items if item_id not in {i for i, _ in p1_unreadable + p2_unreadable}]
first = passed({item_id: p1_found[item_id] for item_id in kept})
second = passed({item_id: p2_found[item_id] for item_id in kept})
discordant = (first != second).astype(float)  # 1 where the two prompts disagree on an item, else 0
var_d = variance.paired_difference_variance(first, second)
mean_d = float((second - first).mean())

# The five-point figure, worked: n = (z_alpha + z_beta)^2 * var(d) / delta^2
z2, delta2 = variance.z_sum() ** 2, 0.05 ** 2
print(f"z sum squared, 95% confidence and 80% power: {z2:.2f}")
print(f"var(d), variance of one item paired difference: {var_d:.4f}")
print(f"delta squared, a five-point difference: {delta2:.4f}")
print(f"n for five points: {z2:.2f} x {var_d:.4f} / {delta2:.4f} = {z2 * var_d / delta2:.1f}, "
      f"rounded up to {variance.items_needed(var_d, 5.0)}")

# The share rests on the discordant items alone, so its 95% interval is a range for the answer.
share_lo, share_hi = bootstrap_mean(discordant)
print(f"discordant share, 95% interval: {interval_pct(share_lo, share_hi)}")
for end, share in (("low", share_lo), ("high", share_hi)):
    # mean(d) stays at its observed value; only the share moves
    print(f"items needed for 5 points, {end} end of the share: {variance.items_needed(share - mean_d ** 2, 5.0)}")

print(f"items needed for 5 points at {100 * HELD_OUT_LEVEL:.2f}% confidence: "
      f"{variance.items_needed_at(var_d, 5.0, ALPHA_HELD_OUT)}")

# Only the count is read here: no held-out verdict is opened by this example.
held_out_n = len(load_items(split="held-out"))
print(f"held-out items (n): {held_out_n}")
print(f"smallest difference {held_out_n} held-out items detect at {100 * HELD_OUT_LEVEL:.2f}% and 80% power: "
      f"{variance.smallest_difference_at(var_d, held_out_n, ALPHA_HELD_OUT):.1f} points")
```

Output:

```text
z sum squared, 95% confidence and 80% power: 7.85
var(d), variance of one item paired difference: 0.1006
delta squared, a five-point difference: 0.0025
n for five points: 7.85 x 0.1006 / 0.0025 = 315.9, rounded up to 316
discordant share, 95% interval: [3.8%, 17.7%]
items needed for 5 points, low end of the share: 118
items needed for 5 points, high end of the share: 555
items needed for 5 points at 98.33% confidence: 422
held-out items (n): 40
smallest difference 40 held-out items detect at 98.33% and 80% power: 16.2 points
```

The worked arithmetic for a five-point difference runs in that example. The square of the sum of the two z values is 7.85. The variance of one item's paired difference is 0.1006. The five-point difference squared is 0.0025. So n is 7.85 x 0.1006 / 0.0025 = 315.9, rounded up to 316.

Miller (2024) gives the paired formula in a more general form, with terms for the noise within each item. The formula here is that form with one reply per item, which drops the within-item terms. Its worked example, with the paper's inputs, comes to about 969 items. Those inputs describe a different experiment, so the book's own numbers come from the printed run only.

Power works the other way too. At 80% power, a set sized for a real difference still misses it about one time in five. That is the price of a fixed budget of questions, and a team that can't pay it should either accept a larger difference as its goal or enlarge the set before the run.

Because the items needed scale with that share when the average difference is small, a change that disagrees on twice as many items needs about twice the questions. A team should estimate the share from a paired run on dev, state it, and check it again when the change is bigger than the one it was measured on.

The main estimate says that a five-point difference needs 316 items, and a ten-point difference needs 79. The floor uses only the sampling noise within each item, and it says 32 and 8. Read the floor as a lower bound on what is needed, not as a plan. It leaves out the disagreement between variants, which is real. Two prompts change what the assistant says, not only how steadily it says it. The floor holds only for a comparison that samples one reply per item at temperature 0.7, with variants as steady as P1. Only two of the items add to its noise, so it rests on very few items. A plan made on the floor comes up short whenever a change disagrees more than sampling alone would explain.

The same estimate answers the question for Chapter 1's set. With twenty items, the smallest difference that the test detects with 80% power at 95% confidence is 19.9 points, under the disagreement assumed above.

Chapter 1's set disagreed on 10.0% (2 of 20) of its items.

Its interval was 30.0 points wide. The formula gives 27.8 points at the same disagreement, which is close. The [twenty-item example](https://github.com/rollingedition/book-evaluating-llm-applications/blob/7ea4125515ebebc29a8a8af15855471e1681785d/examples/twenty-cannot-tell.py) shows that set. At that disagreement, twenty items would usually miss a difference of ten points, and a team that wants to see a difference of five points needs hundreds of items, not dozens.

The estimate rests on the discordant items alone, so it is an order of magnitude, not a count. Its 95% interval on the share is [3.8%, 17.7%]. Across that interval, a five-point difference needs 118 items at the low end and 555 at the high end. The formula is a normal approximation, while the reading rule uses a bootstrap, and the two agree only roughly when few items disagree. At the held-out level of 98.33%, the same inputs need 422 items for a five-point difference.

In production, the mistake is to pick a set size by feel and then read the result as a decision. A team that wants a five-point gain and runs a few dozen items will usually get no difference detected, and may take that for a verdict that the change doesn't work. Write the size down before the run, with the disagreement assumption, and report the result against it. No difference detected at a stated n is a finding about that set. It is not a failed change.

**Working rule:** Before a comparison, run a paired comparison on dev to estimate how often the two variants disagree, and state that share as the assumption. Compute the items needed for the difference you care about, at the level the comparison will be read at, and give its range from the interval on that share. If the set is smaller, report that it can't detect a difference that size, and don't read its no difference detected as a ruling against the change. Use the floor only as a lower bound, and only for a comparison that samples its replies.
