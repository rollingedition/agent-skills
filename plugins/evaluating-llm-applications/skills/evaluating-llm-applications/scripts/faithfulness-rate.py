"""The faithfulness rate of assistant-baseline's answered items, as judged in judge-faithfulness-baseline, dev and held-out apart.

An answered item is one the baseline did not decline and whose reply is not empty; a decline is left out. The judge writes
SUPPORTED or UNSUPPORTED on its first line. A reply that is neither is printed by item ID and left out of the denominator,
never counted as UNSUPPORTED. The judge is uncalibrated: this book has no human ratings for it, so the rates are not
corrected for its errors and are not a calibrated measure. When every readable verdict is the same, the percentile
bootstrap cannot vary, so the example says so and prints the exact binomial bound for n of n instead."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import parse_reply
from lib.judging import parse_support_verdict
from lib.prompts import FAITH_SHA256, P1_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_pct, pct
from lib.testset import load_items

answers = ReplayModel("assistant-baseline", P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1
judge = ReplayModel("judge-faithfulness-baseline", FAITH_SHA256)  # the judge's replies, made from the faithfulness prompt

print("judge: judge-4b, uncalibrated (no human ratings in this book)")
for split in ("dev", "held-out"):
    answered = []
    for item in load_items(split=split):
        reply = parse_reply(answers.reply(item.id, 0))
        if not reply.declined and reply.text:
            answered.append(item.id)
    readable = {}  # item id -> 1.0 for SUPPORTED, 0.0 for UNSUPPORTED
    for item_id in answered:
        raw = judge.reply(item_id, 0)
        verdict = parse_support_verdict(raw)
        if verdict is None:
            line = next((ln.strip().strip("*`").strip() for ln in raw.splitlines() if ln.strip()), "")
            print(f'{split} unreadable verdict, left out: {item_id} ("{line}")')
        else:
            readable[item_id] = 1.0 if verdict == "SUPPORTED" else 0.0
    scores = list(readable.values())
    lo, hi = bootstrap_mean(scores)  # level 0.95; seed SEED, 2,000 resamples
    print(f"{split} answered items: {len(answered)}")
    print(f"{split} unreadable verdicts: {len(answered) - len(readable)}")
    print(f"{split} faithfulness rate: {pct(int(sum(scores)), len(scores))}")
    print(f"{split} 95% interval of the faithfulness rate: {interval_pct(lo, hi)}")
    if len(set(scores)) == 1:  # every readable verdict is the same, so resampling cannot vary
        print(f"{split} bootstrap interval is degenerate: all {len(scores)} readable verdicts are the same")
        if sum(scores) == len(scores):
            print(f"{split} exact 95% lower bound for {len(scores)} of {len(scores)}: {100 * 0.025 ** (1 / len(scores)):.1f}%")
    if split == "dev":
        unfaithful = sorted(item_id for item_id, score in readable.items() if score == 0.0)
        print(f"dev unfaithful items, first five: {', '.join(unfaithful[:5])}")
