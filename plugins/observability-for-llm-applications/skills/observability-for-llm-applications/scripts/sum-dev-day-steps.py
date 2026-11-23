"""Replay all 20 dev-day messages and add up each model step over the day: its calls, its recorded time, its tokens, and its
share of the day's model time and tokens. Tool time is not in the recording (the tools are modelled), so it is counted
and left out of the shares; retrieve and fallback take no time. The route-to-answer gap is the recorder's, not the replay's."""
from collections import Counter
from lib.dayrun import recorded_gap_ns, run_dev_day
from lib.report import fmt_int, fmt_ms, fmt_share

MODEL_STEPS = ("route", "answer")
runs = run_dev_day()                                   # all 20 messages, in arrival order
calls, time_ns, tokens = Counter(), Counter(), Counter()
cached, overlapping, fallbacks = Counter(), 0, 0
for run in runs:
    ordered = sorted(run.outcome.steps, key=lambda s: s.start_ns)
    overlapping += any(later.start_ns < earlier.end_ns for earlier, later in zip(ordered, ordered[1:]))
    fallbacks += run.outcome.source == "fallback"
    for step in run.outcome.steps:
        calls[step.step] += 1
        if step.step in MODEL_STEPS:       # the recording's times and tokens; input counts cached tokens too
            time_ns[step.step] += step.end_ns - step.start_ns
            tokens[step.step] += step.prompt_tokens + step.completion_tokens
            cached[step.step] += step.cached_tokens
            tokens[f"{step.step} input"] += step.prompt_tokens

slowest = max(runs, key=lambda run: run.replied_ns - run.arrived_ns)     # the first of the slowest, if two tie
total_time, total_tokens = sum(time_ns[s] for s in MODEL_STEPS), sum(tokens[s] for s in MODEL_STEPS)
input_total = sum(tokens[f"{s} input"] for s in MODEL_STEPS)
print("messages in the dev day:", fmt_int(len(runs)))
print("messages whose steps overlap in time:", f"{overlapping} of {len(runs)}")
print("messages answered by the fallback reply:", f"{fallbacks} of {len(runs)}")
print("slowest message:", slowest.message.message_id)
print("slowest message time:", fmt_ms(slowest.replied_ns - slowest.arrived_ns))
print("slowest message route:", slowest.outcome.route)
for step in MODEL_STEPS:
    print(f"{step} calls:", fmt_int(calls[step]))
    print(f"{step}, recorded time:", fmt_ms(time_ns[step]))
    print(f"{step}, share of model time:", fmt_share(time_ns[step], total_time))
    print(f"{step}, share of tokens (input plus output):", fmt_share(tokens[step], total_tokens))
print("tool calls:", fmt_int(calls["tool"]))
print("retrieve calls:", fmt_int(calls["retrieve"]))
print("route to answer gap, message 809:", fmt_ms(recorded_gap_ns("809", "route", "answer")))
print("input tokens, total:", fmt_int(input_total))
print("cached input tokens, total:", fmt_int(sum(cached[s] for s in MODEL_STEPS)))
print("output tokens, total:", fmt_int(total_tokens - input_total))
assert calls["route"] == len(runs)               # every message is routed once
assert overlapping == 0                          # the steps never overlap in the replay
