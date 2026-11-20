"""The judge's limits as one table, one labelled line per limit, each computed as in position-flips and length-and-verdicts.
The length line compares the longest band with the shortest, fixed in advance by length order: each band holds different
items, so each is resampled on its own. The unreadable count is over every answer-judge recording on every item."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.bias import band_outcomes, paired_passes, read_verdicts, reply_lengths, same_model_count, unreadable_count
from lib.judging import both_orders, human_pairs
from lib.stats import RESAMPLES, bootstrap_difference, bootstrap_mean, interval_points, pct
from lib.testset import load_items

JUDGE = "judge-answers-baseline"
ANSWER_JUDGES = tuple(f"judge-answers-{variant}" for variant in ("baseline", "k5", "prompt-b", "second-model", "unfiltered"))
items = [item.id for item in load_items()]
dev = [item.id for item in load_items(split="dev")]

# Order-change rate: flipped pairs over the pairs read in both orders. A tie is a readable verdict; an unreadable pair is left out.
pairs = human_pairs()
read_both = [o for o in both_orders("judge-hs2-pairs-ab", "judge-hs2-pairs-ba", list(pairs)) if o.kind != "unreadable"]
print(f"order-change rate: {pct(sum(1 for o in read_both if o.kind == 'flipped'), len(read_both))}")

# Length gap: the longest band's PASS rate minus the shortest band's, fixed by length order, on the dev items.
shortest, _, longest = band_outcomes(reply_lengths("assistant-baseline", dev), read_verdicts(JUDGE, dev))
lo, hi = bootstrap_difference(shortest[1], longest[1])
print(f"length gap, longest band minus shortest band: {100 * (longest[1].mean() - shortest[1].mean()):+.1f} points, "
      f"interval {interval_points(lo, hi)}")
print(f"length gap method: percentile bootstrap over items, each band resampled alone, {RESAMPLES} resamples, 95% level")
print(f"shortest band, {shortest[0]}: {pct(int(shortest[1].sum()), shortest[1].size)}")
print(f"longest band, {longest[0]}: {pct(int(longest[1].sum()), longest[1].size)}")

unreadable, total = unreadable_count(ANSWER_JUDGES, items)
print(f"unreadable verdicts, five answer-judge recordings: {unreadable} of {total}")
print(f"items per answer-judge recording: {len(items)}")
worst = max((unreadable_count([name], items) for name in ANSWER_JUDGES), key=lambda found: found[0])
print(f"most unreadable in one recording: {worst[0]} of {worst[1]}")

same, judged = same_model_count(ANSWER_JUDGES)
print("self-preference test on these recordings: not possible")
print(f"same-model recordings: {same} of {judged}")

# Second model beside the baseline, on the dev items both judged: a None verdict in either leaves the item out.
both, base_pass, second_pass = paired_passes(JUDGE, "judge-answers-second-model", dev)
print(f"baseline PASS rate, same dev items: {pct(int(base_pass.sum()), len(both))}")
print(f"second-model PASS rate, same dev items: {pct(int(second_pass.sum()), len(both))}")
diff_lo, diff_hi = bootstrap_mean(second_pass - base_pass)
print(f"second-model minus baseline, same dev items: {100 * (second_pass - base_pass).mean():+.1f} points, "
      f"interval {interval_points(diff_lo, diff_hi)}, n = {len(both)}")
