"""Gate the prompt-change release r1 against r0 on the same 60 messages, with the gate's own rules. The gate reads the traces only: message time, input tokens, cost, errors and route accuracy. A rule flags a release when the end of its interval nearest the limit lies past the limit. The prompt change adds tokens to every route call, and the gate catches it only because the messages are paired: the same 60 messages judged as unrelated samples pass."""
from lib.gate import judge, measured, paired, tokens_by_step
from lib.report import fmt_int
from lib.stats import mean_of, paired_interval, paired_mean_difference

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
before = measured("baseline-day-1", DAY, MODEL)
after = measured("release-prompt-v2", DAY, MODEL)
ids, base, release = paired(before, after)      # the paired 60: r0 has every one of them
print("messages (paired):", fmt_int(len(ids)))
verdict, flagged = judge("r1 against r0", base, release, paired=True)
assert verdict == "fail" and flagged == ["input tokens per message, mean"]   # the prompt change, and only its tokens
assert "message time, mean" not in flagged   # its message time is not flagged: the interval's end stays under the limit
# The same 60 messages, judged as if they were two unrelated samples: the same release passes.
unpaired, unpaired_flagged = judge("r1 against r0, unpaired", base, release, paired=False)
assert unpaired == "pass" and unpaired_flagged == []   # without the pairing, the gate misses the change it must catch
steps0, steps1 = tokens_by_step("baseline-day-1", DAY, MODEL), tokens_by_step("release-prompt-v2", DAY, MODEL)
def change(steps, step):
    """r1 minus r0 in input tokens, for each message, in one step's calls; zero where the message made no such call."""
    return {i: steps[i].get(step, {"input": 0})["input"] - steps0[i].get(step, {"input": 0})["input"] for i in ids}
route_in, answer_in = change(steps1, "route"), change(steps1, "answer")
changed = {i for i in ids if before[i]["route"] != after[i]["route"]}
assert len(set(route_in.values())) == 1      # the six examples add the same tokens to every route call
assert all(answer_in[i] == 0 for i in ids if i not in changed)   # only a message whose route changed gets another answer call
route_share, answer_share = mean_of(list(route_in.values())), mean_of(list(answer_in.values()))
assert route_share + answer_share == mean_of([m["tokens"] for m in release]) - mean_of([m["tokens"] for m in base])
print("r1 against r0, route call input tokens per call, mean difference:", fmt_int(round(route_share)))
print("r1 against r0, messages whose route changed:", fmt_int(len(changed)))
print("r1 against r0, input tokens per message, answer calls' share:", fmt_int(round(answer_share)))
tokens_base, tokens_release = [m["tokens"] for m in base], [m["tokens"] for m in release]
_, (token_low, _) = paired_interval(tokens_base, tokens_release, paired_mean_difference)
print("r1 against r0, input tokens per message, low end of interval:", fmt_int(round(token_low)))
print("r1 against r0, input tokens per message, limit:", fmt_int(round(mean_of(tokens_base) / 10)))
