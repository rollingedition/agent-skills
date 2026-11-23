"""Gate the top-8 release r3 and the cache-off release r4 against r0, each on the same 60 paired messages, with the same rules and limits as the other gates. The top-8 release retrieves more articles, so its input tokens rise, and its time and cost rise with them. The cache-off release sends the same prompts, so its input total does not move, but its cost and time rise. The gate flags r3 on all three amounts and r4 on time and cost alone."""
from lib.gate import judge, measured, paired
from lib.report import fmt_int

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
before = measured("baseline-day-1", DAY, MODEL)
verdicts = {}
for name, folder in (("r3", "release-top-8"), ("r4", "release-cache-off")):
    ids, base, release = paired(before, measured(folder, DAY, MODEL))
    print(f"{name} against r0, messages (paired):", fmt_int(len(ids)))
    verdicts[name] = judge(f"{name} against r0", base, release, paired=True)
assert verdicts["r3"] == ("fail", ["message time, mean", "input tokens per message, mean", "cost per message, mean"])
assert verdicts["r4"] == ("fail", ["message time, mean", "cost per message, mean"])   # its input total does not move
