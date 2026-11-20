"""A generated table of thumbs-up and thumbs-down rows over the eighty dev items, with what such a table can show and what it
can't. The rows are generated from a stated model with a fixed seed, not taken from users, so the table is a teaching
device only.

The model: an answer is right with probability 0.85. A user who sees a wrong answer gives thumbs-down with probability 0.5 and
thumbs-up with 0.05; one who sees a right answer gives thumbs-down with 0.03 and thumbs-up with 0.15. Most items get no vote.
The table keeps the votes only: whether each answer was right is drawn and then dropped, as it would be in a real log."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import numpy as np

from lib import SEED
from lib.stats import pct
from lib.testset import load_items

P_RIGHT = 0.85
P_DOWN_WRONG, P_UP_WRONG = 0.50, 0.05
P_DOWN_RIGHT, P_UP_RIGHT = 0.03, 0.15

rng = np.random.default_rng(SEED)  # one generator for the whole table, so the same seed gives the same rows
items = [item.id for item in load_items(split="dev")]
rows = []  # (item id, vote) for each item that got a vote
for item_id in items:
    right = rng.random() < P_RIGHT  # hidden: the table has no column for it
    draw = rng.random()
    down, up = (P_DOWN_RIGHT, P_UP_RIGHT) if right else (P_DOWN_WRONG, P_UP_WRONG)
    if draw < down:
        rows.append((item_id, "thumbs-down"))
    elif draw < down + up:
        rows.append((item_id, "thumbs-up"))

print("generated rows from a stated model, not user feedback (seed 0)")
print("item    vote")
for item_id, vote in rows:
    print(f"{item_id}  {vote}")

ups = sum(vote == "thumbs-up" for _, vote in rows)
downs = sum(vote == "thumbs-down" for _, vote in rows)
voted = len({item_id for item_id, _ in rows})
print(f"dev items: {len(items)}")
print(f"items with a vote: {voted}")
print(f"items nobody voted on: {len(items) - voted}")
print(f"thumbs-down among those who voted: {pct(downs, ups + downs)}")
print(f"thumbs-up among those who voted: {pct(ups, ups + downs)}")
print("what the table can show: the share of each kind of vote, among the votes cast, with its n.")
print("what it can't show: anything about the items nobody voted on; whether a thumbs-up answer was right.")
