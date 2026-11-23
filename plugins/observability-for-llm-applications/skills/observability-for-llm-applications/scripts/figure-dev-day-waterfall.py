"""Draw one dev-day message's trace as a waterfall: each span a bar from its start to its end, after the message arrives.
The bars are the spans of build-one-trace, from the replay's recorded times, so the figure shows the order and length of
the steps. The printed lines are the values the figure's text quotes."""
from lib.dayrun import run_dev_day
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_ms

(run,) = run_dev_day(["809"])
outcome, arrived = run.outcome, run.arrived_ns

# One bar per span: the message first, then its steps in order. The answer is the accent; the route is ink.
bars = [("message", arrived, run.replied_ns, MUTED)]
bars += [(s.step, s.start_ns, s.end_ns, ACCENT if s.step == "answer" else INK) for s in outcome.steps]
fig, ax = new_figure(height=2.4)
for row, (label, start, end, colour) in enumerate(bars):
    left, width = (start - arrived) / 1e9, (end - start) / 1e9             # seconds after arrival
    if width > 0:
        ax.barh(row, width, left=left, height=0.6, color=colour)
    else:                                                                  # a step with no time is a tick, not a bar
        ax.plot([left], [row], marker="|", markersize=10, color=colour)
ax.set_yticks(range(len(bars)), [label for label, _, _, _ in bars])
ax.invert_yaxis()
ax.set_xlabel("seconds after the message arrives")
save(fig, "dev-day-waterfall")

steps = {s.step: s for s in outcome.steps}                                 # one span per step in this message
route, answer = steps["route"], steps["answer"]
print("message, time from arrival to reply:", fmt_ms(run.replied_ns - arrived))
print("route span, time:", fmt_ms(route.end_ns - route.start_ns))
print("retrieve span, time:", fmt_ms(steps["retrieve"].end_ns - steps["retrieve"].start_ns))
print("answer span, time:", fmt_ms(answer.end_ns - answer.start_ns))
print("answer span starts, after arrival:", fmt_ms(answer.start_ns - arrived))
# The steps run one after another: the answer starts exactly when the route ends, so the bars do not overlap.
assert answer.start_ns == route.end_ns
