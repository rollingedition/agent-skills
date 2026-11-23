"""Price one answer call twice: at the book's own rates, and at the genai-prices 0.2.5 listing for the 4B, which needs its
provider and a virtual timestamp (B-59). The two prices differ because the rates differ; the book's rates were written
for the book and the listing is the real one, so the prose names which is which. Money prints with its table's version."""
from decimal import Decimal

from lib.dayrun import run_day
from lib.prices import PriceTable, datetime_of
from lib.report import fmt_int, fmt_usd
from genai_prices import Usage, calc_price

MODEL, LISTED = "Qwen3-4B-Instruct-2507", "Qwen/Qwen3-4B-Instruct-2507"   # the book's name, and the listing's repo name
runs = run_day("2026-12-08")
call = next(s for run in runs for s in run.outcome.steps if s.step == "answer")   # the day's first answer call
print("request, input tokens, total:", fmt_int(call.prompt_tokens))
print("request, cached input tokens, derived:", fmt_int(call.cached_tokens))
print("request, output tokens:", fmt_int(call.completion_tokens))

book = PriceTable()
money = book.cost(MODEL, call.prompt_tokens, call.cached_tokens, call.completion_tokens, call.start_ns)
no_cache = book.cost(MODEL, call.prompt_tokens, 0, call.completion_tokens, call.start_ns)
print(f"book's table, cached input at its own rate, {book.version}:", fmt_usd(money))
print(f"book's table, the same request with no cached input, {book.version}:", fmt_usd(no_cache))
row = book.row(MODEL, call.start_ns)   # the row in force at the call's start
print("book's table, output rate to input rate:", f"{Decimal(row['output_per_mtok']) / Decimal(row['input_per_mtok']):.1f}")
print("book's table, cached input rate to input rate:",
      f"{Decimal(row['cache_read_per_mtok']) / Decimal(row['input_per_mtok']):.1f}")

usage = Usage(input_tokens=call.prompt_tokens, cache_read_tokens=call.cached_tokens, output_tokens=call.completion_tokens)
when = datetime_of(call.start_ns)   # the call's virtual time, never the machine's clock
listed = calc_price(usage, LISTED, provider_id="huggingface_nscale", genai_request_timestamp=when)
print("genai-prices listing, huggingface_nscale, the same request:", fmt_usd(listed.total_price))


def lookup_fails(*args, **kwargs) -> bool:
    """True when genai-prices cannot find a price for the call: a LookupError, not a price from another model."""
    try:
        calc_price(*args, **kwargs)
    except LookupError:
        return True
    return False


# The listing has no cache price, so cached input bills at the input rate: the total does not change with the cache.
assert calc_price(Usage(input_tokens=call.prompt_tokens, output_tokens=call.completion_tokens), LISTED,
                  provider_id="huggingface_nscale", genai_request_timestamp=when).total_price == listed.total_price
assert lookup_fails(usage, LISTED, genai_request_timestamp=when)          # no provider given: no price
assert lookup_fails(usage, LISTED, provider_id="openai", genai_request_timestamp=when)   # the span's provider: no price
assert lookup_fails(usage, "Qwen/Qwen3-0.6B", provider_id="huggingface_nscale", genai_request_timestamp=when)
