"""Scores the recorded replies on the 100-item GSM8K sample by exact match on the final number. The accuracy line rests on
its count of readable replies; unreadable replies are counted apart, never as wrong. The three example items show a right,
a wrong and an unreadable reply. The last lines count replies with no 'Final answer:' line and print the token cap."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.bench import load_gsm8k, score_gsm8k
from lib.prompts import BENCH_GSM8K_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_pct, pct

rows = load_gsm8k()
by_id = {row["id"]: row for row in rows}
replies = ReplayModel("bench-gsm8k", BENCH_GSM8K_SHA256)  # fails if the recording was made from another prompt
scored = score_gsm8k(rows, {row["id"]: replies.reply(row["id"]) for row in rows})
parsed = {item: number for item, number, _ in scored}

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
no_final = [row["id"] for row in rows if "final answer:" not in replies.reply(row["id"]).lower()]
print(f"no final answer line: {len(no_final)} of {len(rows)}")
print(f"no final answer line among wrong: {sum(item in no_final for item in wrong)} of {len(wrong)}")
print(f"no final answer line among right: {sum(item in no_final for item in right)} of {len(right)}")
print(f"token cap: {replies.manifest['settings']['sampling']['max_tokens']}")

for kind, ids in (("right", right), ("wrong", wrong), ("unreadable", unreadable)):
    if not ids:
        print(f"{kind} example: none")
        continue
    item = ids[0]  # the first by ID, so the same item prints on every run
    print(f"{kind} example: {item}")
    print(f"{kind} question: {by_id[item]['question'][:50]}")
    print(f"{kind} reference: {by_id[item]['reference']}")
    print(f"{kind} parsed: {parsed[item] or 'none'}")
