"""Gate release r2, the 0.6B model swap, against r0 on the same 200 messages, with the same rules and limits. Its route accuracy falls, and the gate flags it. Its message time, input tokens and cost fall too, and the rules for those amounts pass a fall. The fall comes from the answer calls: r2 routes more messages to the fallback reply, which makes no answer call. The suffix adds a few tokens to every route call. The gate reads each message's route reply against the route its scenario gives, never an answer."""
from lib.gate import judge, measured, paired, tokens_by_step, to_decimal
from lib.report import fmt_int, fmt_ms, fmt_usd
from lib.stats import mean_of

DAY, MODEL, SWAP = "2026-12-08", "Qwen3-4B-Instruct-2507", "Qwen3-0.6B"
before = measured("baseline-day-1", DAY, MODEL)
after = measured("release-model-swap", DAY, SWAP)   # r2: the 0.6B model, on all 200 messages
ids, base, release = paired(before, after)
verdict, flagged = judge("r2 against r0", base, release, paired=True)
print("messages (paired):", fmt_int(len(ids)))
assert verdict == "fail" and flagged == ["route accuracy"]   # the model swap is caught on route accuracy alone

steps0, steps2 = tokens_by_step("baseline-day-1", DAY, MODEL), tokens_by_step("release-model-swap", DAY, SWAP)
def change(step, field):
    """r2 minus r0 for each message, in one step's calls; zero where the message made no such call."""
    return [steps2[i].get(step, {field: 0})[field] - steps0[i].get(step, {field: 0})[field] for i in ids]
answered0 = {i for i in ids if "answer" in steps0[i]}
answered2 = {i for i in ids if "answer" in steps2[i]}
print("messages answered by r0 and not by r2:", fmt_int(len(answered0 - answered2)))
print("messages answered by r2 and not by r0:", fmt_int(len(answered2 - answered0)))
route_in, answer_in = change("route", "input"), change("answer", "input")
assert len(set(route_in)) == 1                      # every route call grew by the same amount: the suffix's tokens
route_share, answer_share = mean_of(route_in), mean_of(answer_in)
assert route_share + answer_share == mean_of([m["tokens"] for m in release]) - mean_of([m["tokens"] for m in base])
print("r2 against r0, route call input tokens per call, mean difference:", fmt_int(round(route_share)))
print("r2 against r0, route call output tokens per call, mean difference:",
      fmt_int(round(mean_of(change("route", "output")))))
print("r2 against r0, input tokens per message, route calls' share:", fmt_int(round(route_share)))
print("r2 against r0, input tokens per message, answer calls' share:", fmt_int(round(answer_share)))
print("r2 against r0, message time, answer calls' share:", fmt_ms(round(mean_of(change("answer", "time")))))
print("r2 against r0, cost per 1,000 messages, answer calls' share:",
      fmt_usd(to_decimal(mean_of(change("answer", "cost")) * 1000)))
replies = [text for i in ids for step in steps2[i].values() for text in step["replies"]]
empty = [text for text in replies if text.startswith("<think>\n\n</think>")]
assert all(text.startswith("<think>") for text in replies)   # the 0.6B still writes its block under /no_think
print("r2, model replies:", fmt_int(len(replies)))
print("r2, model replies with an empty <think> block:", fmt_int(len(empty)))
print("r2, model replies with text in their <think> block:", fmt_int(len(replies) - len(empty)))
