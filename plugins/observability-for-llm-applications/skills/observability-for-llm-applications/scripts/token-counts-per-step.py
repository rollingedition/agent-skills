"""Tokens per model call (a request), per message, per resolved message and per route, over baseline day 1's 200
messages. Each rate names its denominator (PL-11): a resolved message is one the model answered, not the fallback reply.
The input count includes the cached part, so the cached share is printed beside it."""
from lib.dayrun import run_day
from lib.report import fmt_int, fmt_share

runs = run_day("2026-12-08")
model_steps = {run.message.message_id: [s for s in run.outcome.steps if s.name == "chat"] for run in runs}


def totals(steps):
    """Input (cached part included), cached input (derived) and output tokens, summed over some model steps."""
    return (sum(s.prompt_tokens for s in steps), sum(s.cached_tokens for s in steps),
            sum(s.completion_tokens for s in steps))


requests = [s for steps in model_steps.values() for s in steps]
inp, cached, out = totals(requests)
print("messages:", fmt_int(len(runs)))
print("requests (model calls):", fmt_int(len(requests)))
print("input tokens, total:", fmt_int(inp))
print("cached input tokens, derived, total:", fmt_int(cached))
print("output tokens, total:", fmt_int(out))
print("cached share of input tokens:", fmt_share(cached, inp))
print("input tokens per request:", f"{inp / len(requests):.1f}")
print("output tokens per request:", f"{out / len(requests):.1f}")
print("input tokens per message:", f"{inp / len(runs):.1f}")
# Every message makes a route call first; a fallback message stops there, so it has no answer call.
for step in ("route", "answer"):
    steps = [s for s in requests if s.step == step]
    print(f"{step} requests:", fmt_int(len(steps)))
    print(f"{step} requests, input tokens per request:", f"{totals(steps)[0] / len(steps):.1f}")
model_calls = {run.message.message_id: len(model_steps[run.message.message_id]) for run in runs}
assert all(sum(s.step == "route" for s in model_steps[m]) == 1 for m in model_calls)   # one route call per message
print("most model calls in one message:", max(model_calls.values()))   # the route call and up to two answer calls
resolved = [run for run in runs if run.outcome.source == "model"]
r_inp, _, r_out = totals([s for run in resolved for s in model_steps[run.message.message_id]])
print("resolved messages:", fmt_int(len(resolved)))
print("input tokens per resolved message:", f"{r_inp / len(resolved):.1f}")
print("output tokens per resolved message:", f"{r_out / len(resolved):.1f}")
for route in sorted({run.outcome.route for run in runs}):
    mine = [run for run in runs if run.outcome.route == route]
    route_inp, _, route_out = totals([s for run in mine for s in model_steps[run.message.message_id]])
    print(f"route {route}, messages:", fmt_int(len(mine)))
    print(f"route {route}, input tokens per message:", f"{route_inp / len(mine):.1f}")
    print(f"route {route}, output tokens per message:", f"{route_out / len(mine):.1f}")
assert sum(totals(steps)[0] for steps in model_steps.values()) == inp   # every request belongs to exactly one message
