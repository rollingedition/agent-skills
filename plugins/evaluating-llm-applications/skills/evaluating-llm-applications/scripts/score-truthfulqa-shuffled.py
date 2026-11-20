"""Scores the shuffled-options recording on the 100-item TruthfulQA MC1 sample. Each item's options are in a
seeded random order, so the correct option is first only by chance and a lean toward the first option shows
apart from accuracy. Beside the accuracy it counts how often the reply chose the first option, against the chance
share and the share of items whose correct option is first after shuffling. Last, it compares each item with the
unshuffled recording."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.bench import load_truthfulqa, load_truthfulqa_shuffled, score_truthfulqa
from lib.prompts import BENCH_TQA_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_points, interval_pct, pct


def score(rows, recording):
    """The recording's scored list (item, chosen letter, verdict) and its manifest, for rows with their options."""
    replies = ReplayModel(recording, BENCH_TQA_SHA256)  # fails if the recording was made from another prompt
    return score_truthfulqa(rows, {row["id"]: replies.reply(row["id"]) for row in rows}), replies.manifest


shuffled = load_truthfulqa_shuffled()
by_id = {row["id"]: row for row in shuffled}
scored, manifest = score(shuffled, "bench-truthfulqa-shuffled")
readable = [entry for entry in scored if entry[2] is not None]
unreadable = [entry[0] for entry in scored if entry[2] is None]  # kept out of the denominator, never counted as wrong
chance = sum(1 / len(by_id[item]["choices"]) for item, _, _ in readable)  # a random pick takes the first of k with 1/k
lo, hi = bootstrap_mean([float(entry[2]) for entry in readable])

print(f"readable, shuffled options: {len(readable)} of {len(shuffled)}")
print(f"accuracy, shuffled options: {pct(sum(entry[2] for entry in readable), len(readable))}")
print(f"accuracy interval, shuffled options: {interval_pct(lo, hi)}")
print(f"unreadable, shuffled options: {len(unreadable)}")
print(f"unreadable ids, shuffled options: {', '.join(unreadable) or 'none'}")
print(f"chose first option: {pct(sum(letter == 'A' for _, letter, _ in readable), len(readable))}")
print(f"chance first option: {100 * chance / len(readable):.1f}% (expected {chance:.1f} of {len(readable)})")
print(f"correct option first after shuffling: "
      f"{pct(sum(by_id[item]['correct'] == 'A' for item, _, _ in readable), len(readable))}")

plain, _ = score(load_truthfulqa(), "bench-truthfulqa")
plain_verdict = {item: verdict for item, _, verdict in plain}
paired = [(entry[2], plain_verdict[entry[0]]) for entry in readable if plain_verdict[entry[0]] is not None]
kinds = Counter(paired)  # keys: (right shuffled, right unshuffled)
gaps = [float(s) - float(p) for s, p in paired]
lo, hi = bootstrap_mean(gaps)  # 95%, one comparison: the book's paired intervals resample items the same way

print(f"paired items: {len(paired)}")
print(f"right in both: {kinds[True, True]}")
print(f"right only unshuffled: {kinds[False, True]}")
print(f"right only shuffled: {kinds[True, False]}")
print(f"wrong in both: {kinds[False, False]}")
print(f"difference, shuffled minus unshuffled: {100 * sum(gaps) / len(paired):+.1f} points")
print(f"95% interval of the difference: {interval_points(lo, hi)}")
print(f"shuffle seed: {manifest['shuffle_seed']}")
