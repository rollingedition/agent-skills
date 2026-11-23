"""Cost by step, by route, per resolved message and per user on baseline day 1, at the book's rates. Each call is priced at
its own start, and the price row in force at that time is the one used (PL-20). Every rate names its denominator (PL-11):
messages sent to the route, messages the model resolved, or users. The fallback route makes a route call and no answer call."""
from collections import Counter
from decimal import Decimal

from lib.dayrun import run_day
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share, fmt_usd

MODEL = "Qwen3-4B-Instruct-2507"
runs = run_day("2026-12-08")
price = PriceTable()
cost, by_step = Counter(), Counter()   # Decimal money per message ID, and per step name
for run in runs:
    for step in (s for s in run.outcome.steps if s.name == "chat"):
        money = price.cost(MODEL, step.prompt_tokens, step.cached_tokens, step.completion_tokens, step.start_ns)
        cost[run.message.message_id] += money
        by_step[step.step] += money
total = sum(cost.values(), Decimal(0))
print("messages:", fmt_int(len(runs)))
print(f"cost, all messages, {price.version}:", fmt_usd(total))
for step in ("route", "answer"):
    print(f"{step} requests, cost, {price.version}:", fmt_usd(by_step[step]))
    print(f"{step} requests, share of cost:", fmt_share(by_step[step], total))
assert sum(by_step.values(), Decimal(0)) == total   # the two steps make up the whole cost

for route in sorted({run.outcome.route for run in runs}):
    mine = [run for run in runs if run.outcome.route == route]
    route_cost = sum((cost[run.message.message_id] for run in mine), Decimal(0))
    print(f"route {route}, messages:", fmt_int(len(mine)))
    print(f"route {route}, cost per 1,000 messages, {price.version}:", fmt_usd(route_cost * 1000 / len(mine)))

resolved = [run for run in runs if run.outcome.source == "model"]
resolved_total = sum((cost[run.message.message_id] for run in resolved), Decimal(0))
print("resolved messages:", fmt_int(len(resolved)))
print(f"cost of a resolved message, its own calls, {price.version}:", fmt_usd(resolved_total / len(resolved)))
by_user = Counter()                          # Decimal money per user ID
for run in runs:
    by_user[run.message.user_id] += cost[run.message.message_id]
assert sum(by_user.values(), Decimal(0)) == total   # the users make up the whole cost
costliest = max(sorted(by_user), key=by_user.get)   # ties go to the lower ID, so the choice is stable
print("users with a message:", fmt_int(len(by_user)))
print(f"cost per user, mean over users with a message, {price.version}:", fmt_usd(total / len(by_user)))
print("costliest user, messages:", fmt_int(sum(run.message.user_id == costliest for run in runs)))
print("costliest user, share of cost:", fmt_share(by_user[costliest], total))
