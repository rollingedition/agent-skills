"""Draw each model step's share of the dev day's model time, beside its share of the tokens (input plus output), over all
20 messages. Each bar is labelled with the share the example prints, so the figure and the printed lines are one set of
numbers. Tool time is not in the recording, so the tool step is not drawn."""
from collections import Counter
from lib.dayrun import run_dev_day
from lib.figures import ACCENT, INK, new_figure, save
from lib.report import fmt_int, fmt_ms, fmt_share

MODEL_STEPS = ("route", "answer")
runs = run_dev_day()
calls, time_ns, tokens = Counter(), Counter(), Counter()
for run in runs:
    for step in (s for s in run.outcome.steps if s.step in MODEL_STEPS):
        calls[step.step] += 1
        time_ns[step.step] += step.end_ns - step.start_ns
        tokens[step.step] += step.prompt_tokens + step.completion_tokens      # input plus output

total_time, total_tokens = sum(time_ns.values()), sum(tokens.values())
time_labels = [fmt_share(time_ns[s], total_time) for s in MODEL_STEPS]
token_labels = [fmt_share(tokens[s], total_tokens) for s in MODEL_STEPS]
fig, ax = new_figure(height=2.6)
positions = list(range(len(MODEL_STEPS)))
time_bars = ax.bar([p - 0.2 for p in positions], [100 * time_ns[s] / total_time for s in MODEL_STEPS], width=0.4,
                   color=ACCENT, label="share of model time")
token_bars = ax.bar([p + 0.2 for p in positions], [100 * tokens[s] / total_tokens for s in MODEL_STEPS], width=0.4,
                    color=INK, label="share of tokens")
ax.bar_label(time_bars, labels=time_labels, padding=2)
ax.bar_label(token_bars, labels=token_labels, padding=2)
ax.set_xticks(positions, list(MODEL_STEPS))
ax.set_ylim(0, 100)
ax.set_ylabel("percent of the dev day")
ax.legend(loc="upper left")          # the route bars reach only about 21 percent, so the top left is clear of labels
save(fig, "dev-day-step-shares")

print("messages in the dev day:", fmt_int(len(runs)))
for step, time_label, token_label in zip(MODEL_STEPS, time_labels, token_labels):
    print(f"{step} calls:", fmt_int(calls[step]))
    print(f"{step}, recorded time:", fmt_ms(time_ns[step]))
    print(f"{step}, share of model time:", time_label)
    print(f"{step}, tokens, input plus output:", fmt_int(tokens[step]))
    print(f"{step}, share of tokens:", token_label)
print("model time, total:", fmt_ms(total_time))
print("tokens, input plus output, total:", fmt_int(total_tokens))
assert sum(calls.values()) == 37     # 20 route calls and 17 answer calls, as the recording holds
