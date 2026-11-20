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
