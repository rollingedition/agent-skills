"""Estimate baseline day 1's total tokens and cost from a 10 percent head sample, scaled by one over the ratio, with the 95
percent interval (the estimate plus or minus 1.96 standard errors). The estimate is set against the full count, summed over
every message, and against the token counter's total for the day. The point is coverage: over 2,000 independent samples the
interval holds the full count in only some of them, and the printed count says how many."""
from decimal import Decimal

from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from lib.dayrun import RELEASE, run_day_traced
from lib.metrics import USAGE, make_meter_provider, totals
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_share, fmt_usd
from lib.sampling import draws_holding, estimate_total, head_sample, message_traces, only_messages

MODEL = "Qwen3-4B-Instruct-2507"
DAY, RATIO, DRAWS, SEED = "2026-12-08", 0.1, 2000, 20261207  # SEED is PL-6's; each draw salts the trace IDs with its number
reader = InMemoryMetricReader()
provider = make_meter_provider(reader, service_instance_id=f"{DAY}-metrics", service_version=RELEASE.service_version)
traced = run_day_traced(DAY, live=False, meter_provider=provider)  # the assistant's live meter counts each call's tokens
traces = only_messages(message_traces(traced.spans, DAY, MODEL, PriceTable()))
counter = totals(reader)
counter_tokens = int(counter[USAGE["input"]]["sum"]) + int(counter[USAGE["output"]]["sum"])
sample = head_sample(traces, RATIO)
full_tokens = sum(t.tokens for t in traces)
full_cost = sum((t.cost for t in traces), Decimal(0))
print(f"messages kept at ratio {RATIO}, of {len(traces)}:", fmt_int(len(sample)))
tokens, tokens_interval = estimate_total([t.tokens for t in sample], RATIO)
print("full count of tokens, all messages:", fmt_int(full_tokens))
print("token counter total for the day, input plus output:", fmt_int(counter_tokens))
print(f"estimated tokens, ratio {RATIO}:", fmt_int(int(tokens)))
print("estimate as a share of the full count, tokens:", fmt_share(tokens, full_tokens))
print("interval as shares of the full count, tokens, low end:", fmt_share(tokens_interval[0], full_tokens))
print("interval as shares of the full count, tokens, high end:", fmt_share(tokens_interval[1], full_tokens))
cost, cost_interval = estimate_total([t.cost for t in sample], RATIO)
print("full cost of the day, Qwen3-4B-Instruct-2507 at the book's rates:", fmt_usd(full_cost))
print(f"estimated cost, ratio {RATIO}:", fmt_usd(cost))
print("estimate as a share of the full cost:", fmt_share(cost, full_cost))
print("interval as shares of the full cost, low end:", fmt_share(cost_interval[0], full_cost))
print("interval as shares of the full cost, high end:", fmt_share(cost_interval[1], full_cost))
assert counter_tokens == full_tokens          # the counter reads each call once, so it matches the root spans
print("samples of the same day, drawn independently:", fmt_int(DRAWS))
held_tokens, held_cost = draws_holding(traces, RATIO, DRAWS, SEED)
print(f"intervals that hold the full count, of {fmt_int(DRAWS)} samples at ratio {RATIO}, tokens:", fmt_int(held_tokens))
print(f"intervals that hold the full count, of {fmt_int(DRAWS)} samples at ratio {RATIO}, cost:", fmt_int(held_cost))
