"""Compare the same 60 messages under r0 (the baseline, on baseline day 1) and r3 (the top-8 release): the answer calls'
prefill, tokens and cache, and the route calls' cache. More articles make the prompt longer, and prefill follows the tokens the
model had to evaluate, since a cached prefix is not read again while the cache holds it. The correlations are over all of
baseline day 1's answer calls, computed; the paired interval belongs to chapter 10, so none is printed here."""

from lib.case import load_messages
from lib.dayrun import DATA
from lib.report import fmt_int, fmt_ms

import json
from collections import Counter
from statistics import correlation


def load(folder):
    return [json.loads(line) for line in (DATA / folder / "traces.jsonl").read_text(encoding="utf-8").splitlines()]


def total(rows, step, field):
    return sum(row[field] for row in rows if row["step"] == step)


paired = {message.message_id for message in load_messages("2026-12-08-paired")}   # the 60 messages, same arrivals
base = load("baseline-day-1")
releases = {"r0": [row for row in base if row["message_id"] in paired], "r3": load("release-top-8")}
assert {row["message_id"] for row in releases["r3"]} == paired     # r3 was recorded for exactly these messages
for name, rows in releases.items():
    print(f"{name}, prefill summed over the answer calls:", fmt_ms(total(rows, "answer", "prefill_ns")))
    print(f"{name}, prompt tokens summed over the answer calls:", fmt_int(total(rows, "answer", "prompt_tokens")))
    print(f"{name}, prompt tokens evaluated summed over the answer calls:", fmt_int(total(rows, "answer", "tokens_evaluated")))
    print(f"{name}, cached prompt tokens summed over the answer calls:", fmt_int(total(rows, "answer", "cached_tokens_derived")))
    print(f"{name}, prompt tokens evaluated summed over the route calls:", fmt_int(total(rows, "route", "tokens_evaluated")))
print("prefill, r3 over r0, computed:", f"{total(releases['r3'], 'answer', 'prefill_ns') / total(releases['r0'], 'answer', 'prefill_ns'):.2f}")

# The same answer calls under both releases: sorted by message, then by call, so each pair is one message's n-th answer.
before = sorted((row for row in releases["r0"] if row["step"] == "answer"), key=lambda row: (row["message_id"], row["seq"]))
after = sorted((row for row in releases["r3"] if row["step"] == "answer"), key=lambda row: (row["message_id"], row["seq"]))
assert all(b["message_id"] == a["message_id"] and b["prompt_tokens"] <= a["prompt_tokens"] for b, a in zip(before, after))
gained = sum(a["prompt_tokens"] > b["prompt_tokens"] for b, a in zip(before, after))   # the assert: none loses any
print("paired answer calls, r3 with more prompt tokens than r0:", f"{gained} of {len(before)}")

route = {name: {row["message_id"]: row for row in rows if row["step"] == "route"} for name, rows in releases.items()}
assert all(route["r0"][m]["input_key"] == route["r3"][m]["input_key"]
           and route["r0"][m]["prompt_tokens"] == route["r3"][m]["prompt_tokens"] for m in paired)   # identical route prompts
cached = {name: [row["cached_tokens_derived"] for row in rows if row["step"] == "route"] for name, rows in releases.items()}
instruction = Counter(cached["r0"]).most_common(1)[0][0]        # the cached count most route calls get: the instruction
print("route instruction, cached tokens in most route calls:", fmt_int(instruction))
for name in releases:
    print(f"{name}, route calls that re-read most of the instruction:", sum(c < instruction for c in cached[name]))

answer_calls = [row for row in base if row["step"] == "answer"]
by_prompt = correlation([row["prompt_tokens"] for row in answer_calls], [row["prefill_ns"] for row in answer_calls])
by_evaluated = correlation([row["tokens_evaluated"] for row in answer_calls], [row["prefill_ns"] for row in answer_calls])
print("prefill against prompt tokens, correlation, computed:", f"{by_prompt:.2f}")
print("prefill against tokens evaluated, correlation, computed:", f"{by_evaluated:.2f}")
assert by_evaluated > 0.9 and by_evaluated > by_prompt   # the cached prefix adds to the prompt, not to the prefill
