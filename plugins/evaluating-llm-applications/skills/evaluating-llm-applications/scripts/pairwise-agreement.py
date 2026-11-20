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
