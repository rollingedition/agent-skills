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
