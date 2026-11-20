"""Scores the recorded replies on the 100-item TruthfulQA MC1 sample by the option letter each reply gives. Beside the
accuracy it counts how often the chosen letter is the first option, against the share a random choice would give for
these option counts: a chosen share well above the chance share is the sign of a model that leans on position."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.bench import load_truthfulqa, score_truthfulqa
from lib.prompts import BENCH_TQA_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_pct, pct

rows = load_truthfulqa()
by_id = {row["id"]: row for row in rows}
replies = ReplayModel("bench-truthfulqa", BENCH_TQA_SHA256)  # fails if the recording was made from another prompt
scored = score_truthfulqa(rows, {row["id"]: replies.reply(row["id"]) for row in rows})
chosen = {item: letter for item, letter, _ in scored}

readable = [entry for entry in scored if entry[2] is not None]
right = [entry[0] for entry in readable if entry[2]]
wrong = [entry[0] for entry in readable if not entry[2]]
unreadable = [entry[0] for entry in scored if entry[2] is None]

print(f"items: {len(rows)}")
print(f"readable: {len(readable)} of {len(rows)}")
print(f"accuracy: {pct(len(right), len(readable))}")
# The interval resamples the readable items only, since an unreadable reply has no verdict to resample.
lo, hi = bootstrap_mean([1.0 if entry[2] else 0.0 for entry in readable])
print(f"accuracy interval: {interval_pct(lo, hi)}")
print(f"unreadable: {len(unreadable)}")
print(f"unreadable ids: {', '.join(unreadable) or 'none'}")
print(f"token cap: {replies.manifest['settings']['sampling']['max_tokens']}")

options = Counter(len(by_id[entry[0]]["choices"]) for entry in readable)
print("items by option count: " + ", ".join(f"{count}:{items}" for count, items in sorted(options.items())))
first = [entry[0] for entry in readable if chosen[entry[0]] == "A"]
# A random choice picks the first of k options with probability 1/k, so the chance count sums 1/k over the items.
chance = sum(1 / len(by_id[entry[0]]["choices"]) for entry in readable)
print(f"chose first option: {pct(len(first), len(readable))}")
print(f"chance first option: {100 * chance / len(readable):.1f}% (expected {chance:.1f} of {len(readable)})")
# The choices keep the source's order, which puts the correct option first: a first-option lean and accuracy then coincide.
print(f"correct option first: {pct(sum(row['correct'] == 'A' for row in rows), len(rows))}")

for kind, ids in (("right", right), ("wrong", wrong), ("unreadable", unreadable)):
    if not ids:
        print(f"{kind} example: none")
        continue
    item = ids[0]  # the first by ID, so the same item prints on every run
    print(f"{kind} example: {item}")
    print(f"{kind} question: {by_id[item]['question'][:50]}")
    print(f"{kind} correct: {by_id[item]['correct']}")
    print(f"{kind} chosen: {chosen[item] or 'none'}")
