"""Cached input tokens for each model call, derived as prompt tokens minus the tokens llama.cpp evaluated (PL-21), on baseline
day 1 and on the same 60 messages with the prompt cache reset before each call (release r4). The reset leaves the input
tokens the model reads unchanged; what it removes is the cached part, so the same tokens are all evaluated again. Each call
is priced at its own start on the replay clock."""
from decimal import Decimal

from lib.case import load_messages
from lib.dayrun import run_day
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share, fmt_usd
from lib.tokens import derived_cached, recorded_calls

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
paired = {m.message_id for m in load_messages("2026-12-08-paired")}   # the 60 messages r1, r3 and r4 replay
day = recorded_calls("baseline-day-1")
day_input, _, day_cached = derived_cached(day)
print("baseline day 1, model calls:", fmt_int(len(day)))
print("baseline day 1, input tokens, total:", fmt_int(day_input))
print("baseline day 1, cached input tokens, derived, total:", fmt_int(day_cached))
print("baseline day 1, cached share of input:", fmt_share(day_cached, day_input))
# The recorder's own derived field is the same subtraction, call by call.
assert all(c["cached_tokens_derived"] == c["prompt_tokens"] - c["tokens_evaluated"] for c in day)

base = recorded_calls("baseline-day-1", paired)
cache_off = recorded_calls("release-cache-off", paired)
assert [(c["message_id"], c["step"]) for c in base] == [(c["message_id"], c["step"]) for c in cache_off]  # the same calls
b_input, b_evaluated, b_cached = derived_cached(base)
o_input, o_evaluated, o_cached = derived_cached(cache_off)
print("same 60 messages, model calls:", fmt_int(len(base)))
print("r0, input tokens:", fmt_int(b_input))
print("r0, tokens evaluated:", fmt_int(b_evaluated))
print("r0, cached input tokens, derived:", fmt_int(b_cached))
print("r4, input tokens:", fmt_int(o_input))
print("r4, tokens evaluated:", fmt_int(o_evaluated))
print("r4, cached input tokens, derived:", fmt_int(o_cached))
print("tokens evaluated, r4 minus r0:", fmt_int(o_evaluated - b_evaluated))
assert o_input == b_input and o_cached == 0          # same input tokens; the cache reset leaves no cached part
assert o_evaluated - b_evaluated == b_cached         # every cached token is evaluated again without the cache

# The same calls at the book's rates. A recorded call has no clock of its own, so each takes the start the baseline replay
# gave its message and step, and r4 makes the same calls, so its calls take the same starts.
starts = {(run.message.message_id, s.step): s.start_ns for run in run_day(DAY, paired)
          for s in run.outcome.steps if s.name == "chat"}
price = PriceTable()


def money(calls):
    """The money of recorded calls at the book's rates, each at its own start."""
    return sum((price.cost(MODEL, c["prompt_tokens"], c["cached_tokens_derived"], c["completion_tokens"],
                           starts[(c["message_id"], c["step"])]) for c in calls), Decimal(0))


print(f"cost difference, r4 minus r0, same 60 messages, {price.version}:", fmt_usd(money(cache_off) - money(base)))
