"""Runs format_problems over the baseline replies to every item, and counts each problem by its fixed name.

Dev and held-out items are counted apart, and held-out items appear only as counts. An item can have more than one
problem, so the counts by name can add up to more than the number of items with a problem."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.answers import Assistant
from lib.contract import PROBLEMS, format_problems
from lib.prompts import P1_SHA256, P1_SYSTEM
from lib.stats import pct
from lib.testset import load_items

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)
assert len(load_items()) == 120  # the baseline recording holds one reply per item, so every item is counted

for split in ("dev", "held-out"):
    items = load_items(split=split)
    counts = Counter()
    with_problem = 0
    for item in items:
        problems = format_problems(
            assistant.reply(item),
            context_ids=assistant.context_ids(item),
            expect_decline=item.kind == "unanswerable",  # an unanswerable item must be declined
        )
        with_problem += bool(problems)
        counts.update(problems)
    print(f"{split} items: {len(items)}")
    print(f"{split} items with a format problem: {pct(with_problem, len(items))}")
    for name in PROBLEMS:  # the fixed names, in the order lib.contract lists them
        print(f"{split} problem {name}: {counts[name]}")
