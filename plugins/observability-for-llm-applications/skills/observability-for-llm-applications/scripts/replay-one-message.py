"""Replay one dev-day message through the assistant, answering each model call from the recording, and print what each
call cost on the virtual clock. The printed times and token counts are the recording's; the point rests on the route
call and the answer call of this one message."""
from lib.dayrun import run_dev_day
from lib.report import fmt_int, fmt_ms

(run,) = run_dev_day(["809"])                          # a device request: route, retrieve, answer
outcome = run.outcome

print("message text:", run.message.text)
print("route chosen:", outcome.route)
print("reply source:", outcome.source)
print("steps:", ", ".join(step.step for step in outcome.steps))
calls = [step for step in outcome.steps if step.step in ("route", "answer")]   # retrieve takes no model time
for step in calls:
    print(f"{step.step} call, time:", fmt_ms(step.end_ns - step.start_ns))
    print(f"{step.step} call, input tokens:", fmt_int(step.prompt_tokens))
    print(f"{step.step} call, cached input tokens:", fmt_int(step.cached_tokens))
    print(f"{step.step} call, output tokens:", fmt_int(step.completion_tokens))
print("message, time in model calls:", fmt_ms(sum(s.end_ns - s.start_ns for s in calls)))
# The clock moved by exactly the steps' times, so the steps account for all of the message's time.
assert run.replied_ns - run.arrived_ns == sum(step.end_ns - step.start_ns for step in outcome.steps)
assert outcome.source == "model"
