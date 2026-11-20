"""The reference-guided judge's PASS rate by the length of the assistant's reply, on the dev items the baseline answered. The
reply lengths are in words, in three bands with the edges printed below. Each band's rate is printed with its count. Declined
replies and unreadable verdicts are left out, and each is printed with its count."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.bias import LENGTH_EDGES, band_outcomes, read_verdicts, reply_lengths
from lib.stats import pct
from lib.testset import load_items

ASSISTANT = "assistant-baseline"  # the reply the judge read, and the one whose length is measured
JUDGE = "judge-answers-baseline"

dev = [item.id for item in load_items(split="dev")]  # 80 dev items, sorted by id
lengths = reply_lengths(ASSISTANT, dev)  # the answered items only: declined replies are left out here
verdicts = read_verdicts(JUDGE, dev)  # None where the judge's first line is not a verdict

print(f"band edges, in words: {LENGTH_EDGES[0]} and {LENGTH_EDGES[1]}")
print(f"declined, left out: {len(dev) - len(lengths)} of {len(dev)} dev items")
unreadable = [item_id for item_id in lengths if verdicts[item_id] is None]
print(f"unreadable verdict, left out: {', '.join(unreadable) if unreadable else 'none'}")

for band, outcomes in band_outcomes(lengths, verdicts):
    print(f"{band}: {pct(int(outcomes.sum()), outcomes.size)}")
