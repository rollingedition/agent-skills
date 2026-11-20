"""How the pairwise judge's verdict follows the position it was shown in, on the HelpSteer2 pairs. Each pair is judged in both
orders and sorted as consistent, flipped, tie or unreadable. The flipped pairs are split by the position that won both orders,
and the consistent pairs are checked against the human preference."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.bias import flip_direction
from lib.judging import both_orders, human_pairs
from lib.stats import bootstrap_mean, interval_pct, pct

AB = "judge-hs2-pairs-ab"
BA = "judge-hs2-pairs-ba"
SPLITS = ("dev", "held-out")

pairs = human_pairs()  # all 150 pairs, sorted by id, each with its split and the human's preferred response
orders = both_orders(AB, BA, list(pairs))  # every pair judged in both orders, sorted by id

for split in SPLITS:
    in_split = [o for o in orders if pairs[o.pair_id].split == split]
    for kind in ("consistent", "flipped", "tie", "unreadable"):
        # the denominator is the split's pairs, so the counts add up to the split's size
        print(f"{kind}, {split}: {sum(1 for o in in_split if o.kind == kind)} of {len(in_split)} pairs")

for split in SPLITS:
    flipped = [o for o in orders if o.kind == "flipped" and pairs[o.pair_id].split == split]
    # the letter A's position won both times when flip_direction says 'first'; B's when it says 'second'
    first = sum(1 for o in flipped if flip_direction(o) == "first")
    print(f"flipped, first position won both orders, {split}: {pct(first, len(flipped))}")

# both splits pooled, one 0 or 1 per flipped pair: 1.0 when the first position won both orders
flipped_all = [1.0 if flip_direction(o) == "first" else 0.0 for o in orders if o.kind == "flipped"]
print(f"flipped, first position won both orders, both splits: {pct(int(sum(flipped_all)), len(flipped_all))}")
lo, hi = bootstrap_mean(flipped_all)  # percentile bootstrap over the flipped pairs, as every interval in the book
print(f"first-position share interval, both splits: {interval_pct(lo, hi)}")

for split in SPLITS:
    consistent = [o for o in orders if o.kind == "consistent" and pairs[o.pair_id].split == split]
    # in a consistent pair the two orders agree, so ab is the original response the judge picked
    agree = sum(1 for o in consistent if o.ab == pairs[o.pair_id].preferred)
    print(f"consistent pairs agreeing with the human, {split}: {pct(agree, len(consistent))}")
