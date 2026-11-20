"""Counts the drafting model's failure codes over the dev items, per variant, and prints one table and one labelled line
per count.

The point rests on the table's reading of each mode: the codes were made by the drafting model, as one coder, and are not
human labels. The codes live in data/failure-codes.json; the checks below stop a reply being counted twice or left out.
The labelled lines are the numbers the chapter's prose quotes."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import json
from collections import Counter
from pathlib import Path

from lib.testset import load_items

CODES = Path(__file__).resolve().parent / "data" / "failure-codes.json"
VARIANTS = ("baseline", "unfiltered", "second-model")

book = json.loads(CODES.read_text(encoding="utf-8"))
assert book["labelled"] == "coded by the drafting model (one coder; not human labels)", "the codes are the model's, not human labels"  # the label the prose uses
assert book["variants"] == list(VARIANTS), "the variants in the file are the three the chapter names"

dev_ids = {item.id for item in load_items(split="dev")}
n = len(dev_ids)
codes = book["codes"]
assert {code["item"] for code in codes} <= dev_ids, "a code names an item that is not in the dev split"
pairs = [(code["item"], code["variant"]) for code in codes]
# One code per dev item and variant: a pair repeated would be counted twice, a missing one would go unseen.
assert len(pairs) == len(set(pairs)) == n * len(VARIANTS), "expected one code per dev item and variant"
assert all(code["mode"] in book["modes"] for code in codes), "a code uses a mode the file does not define"

counts = Counter((code["variant"], code["mode"]) for code in codes)
print(f"dev items: {n}")
print(f"replies coded: {len(codes)}")
print(f"labelled: {book['labelled']}")
print(f"{'mode':<22}" + "".join(f"{variant:>14}" for variant in VARIANTS))
for mode in book["modes"]:  # the file's order: ok first, then the failure modes
    total = sum(counts[(variant, mode)] for variant in VARIANTS)
    if total == 0:  # a mode no variant shows is printed as zero of N, so the reader sees it was looked for
        print(f"{mode}: 0 of {n}")
        continue
    print(f"{mode:<22}" + "".join(f"{counts[(variant, mode)]:>14}" for variant in VARIANTS))
totals = {variant: sum(counts[(variant, mode)] for mode in book["modes"]) for variant in VARIANTS}
assert all(total == n for total in totals.values()), "each variant's counts add up to the dev items"
print(f"{'all modes':<22}" + "".join(f"{totals[variant]:>14}" for variant in VARIANTS))
print()
for variant in VARIANTS:  # one labelled line per count, the form the chapter's prose binds to
    for mode in book["modes"]:
        print(f"{mode}, {variant}: {counts[(variant, mode)]}")
    print(f"defective, {variant}: {n - counts[(variant, 'ok')]}")
