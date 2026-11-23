"""The most expensive 1% of baseline day 1's messages, and their share of the day's cost at the book's rates. The count is
exact over the day's 200 messages, with no interval: an interval for another day is chapter 7's. The count is the
nearest-rank count for 1% of n (PL-5), and equal costs are ordered by message ID so the choice is stable."""
import math
from decimal import Decimal
from fractions import Fraction

from lib.dayrun import run_day
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share, fmt_usd

MODEL = "Qwen3-4B-Instruct-2507"
runs = run_day("2026-12-08")
price = PriceTable()
cost = {}                                   # Decimal money per message ID
for run in runs:
    cost[run.message.message_id] = sum((price.cost(MODEL, s.prompt_tokens, s.cached_tokens, s.completion_tokens,
                                                   s.start_ns)
                                        for s in run.outcome.steps if s.name == "chat"), Decimal(0))
ranked = sorted(runs, key=lambda run: (-cost[run.message.message_id], int(run.message.message_id)))
k = math.ceil(Fraction(1, 100) * len(runs))  # 1% of 200 is 2 messages
tail = ranked[:k]
total = sum(cost.values(), Decimal(0))
tail_money = sum((cost[run.message.message_id] for run in tail), Decimal(0))
print("messages:", fmt_int(len(runs)))
print("messages in the most expensive 1%:", fmt_int(k))
print(f"cost of the day, {price.version}:", fmt_usd(total))
print(f"cost of the most expensive 1%, {price.version}:", fmt_usd(tail_money))
print("share of the day's cost, most expensive 1%:", fmt_share(tail_money, total))
print("most expensive message, route:", tail[0].outcome.route)
print(f"most expensive message, cost, {price.version}:", fmt_usd(cost[tail[0].message.message_id]))
print("most expensive 1%, messages resolved by the model:", fmt_int(sum(run.outcome.source == "model" for run in tail)))
assert tail_money * len(runs) > total * k        # the tail costs more per message than the day does on average
