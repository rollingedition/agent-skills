---
title: "Observability for LLM Applications"
chapter: "Attribute tokens and cost to each step"
chapter_id: tokens-and-cost
book: observability-for-llm-applications
edition: 2026.11.1
verified: 2026-11-23
edition_code: B95K-8RWR
canonical: https://rollingedition.com/observability-for-llm-applications/tokens-and-cost
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Attribute tokens and cost to each step,” chapter 6 of Observability for LLM Applications, Edition 2026.11.1, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/tokens-and-cost. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Attribute tokens and cost to each step

By the end of this chapter you can split a day's model calls into input tokens, cached input tokens and output tokens, total them without counting any token twice, and say which step, route and user the money went to. You can also say which of those numbers depends on a price table and which does not.

Ambrewick's finance team asks two questions of the assistant's traces. The first is what one message costs, by route and by user. It sounds like a sum over the spans, and it is the question that goes wrong first: usage sits on more than one kind of span, so a sum over all of them is too high. The second is what the same messages would cost in other languages. This book's assistant serves English only, but the dataset's other locales hold the same utterances, and the same utterance takes a different number of tokens in each language. The chapter measures both on one day, baseline day 1, 2026-12-08, which holds 200 messages. Each message ran through the assistant on the baseline release, with Qwen3-4B-Instruct-2507 as the model, and each model call was recorded once and replayed on the virtual clock, as [chapter 1](#replay-and-the-virtual-clock) describes.

Tokens come first, because they are what the model did. Money comes second, because it needs a price, and the price is a choice the book makes and dates.

## Three counts for each call {#three-token-counts}

A token count is the number of tokens a model reads or writes for one call, in that model's own vocabulary. The book keeps three counts for each call. Input tokens are the whole prompt the model read, cached part included; cached input tokens are the part its cache held; output tokens are what it wrote. The GenAI conventions, at version 0.1.0, define the input total the same way: `gen_ai.usage.input_tokens` includes the cached tokens. So the cached count sits inside the input count, and adding the two together counts the cached part twice.

The [prompt count and completion count](https://rollingedition.com/agent-harnesses/s/token-counts) in Agent Harnesses are close to these two, and they have no cached part. This book adds one, and it adds a price to the counts later in the chapter.

Each message makes one route call, and a message on any route but `fallback` makes one or more answer calls. The most calls one message made on this day is 3: a route call and two answer calls, when a tool's request comes before the reply. The script below sorts every call of the day by its three counts and its step.

Example `token-counts-per-step` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
messages: 200
requests (model calls): 321
input tokens, total: 104,811
cached input tokens, derived, total: 61,460
output tokens, total: 4,996
cached share of input tokens: 58.6%
input tokens per request: 326.5
output tokens per request: 15.6
input tokens per message: 524.1
route requests: 200
route requests, input tokens per request: 145.5
answer requests: 121
answer requests, input tokens per request: 625.6
most model calls in one message: 3
resolved messages: 111
input tokens per resolved message: 827.7
output tokens per resolved message: 40.2
route alarms, messages: 16
route alarms, input tokens per message: 883.6
route alarms, output tokens per message: 43.4
route calendar, messages: 27
route calendar, input tokens per message: 903.5
route calendar, output tokens per message: 38.8
route devices, messages: 17
route devices, input tokens per message: 627.9
route devices, output tokens per message: 44.5
route fallback, messages: 89
route fallback, input tokens per message: 145.4
route fallback, output tokens per message: 6.0
route lists, messages: 13
route lists, input tokens per message: 936.5
route lists, output tokens per message: 29.0
route media, messages: 31
route media, input tokens per message: 663.9
route media, output tokens per message: 41.6
route messages, messages: 7
route messages, input tokens per message: 1415.4
route messages, output tokens per message: 42.1
```

Most of the day's input is cached. Of 104,811 input tokens across the day's model calls, 61,460 were cached, which is 58.6% of the input. The output is small by comparison, 4,996 tokens in all.

The two steps differ in size. A route request reads 145.5 input tokens on average, and an answer request reads 625.6, because the answer call carries more of the prompt, such as the retrieved articles and a tool's result.

Input tokens are the call's messages rendered through the chat template in the model's GGUF file and re-tokenized with the model's own tokenizer. Output tokens are the reply re-tokenized with the model's own tokenizer. Cached input is derived rather than reported, as [chapter 1](#replay-and-the-virtual-clock) says, and the cached-input section below shows the subtraction.

Divided by the messages, the day's input is 524.1 tokens per message. Per resolved message it is 827.7 input and 40.2 output tokens. A resolved message is one the assistant answered with a model reply, not a fallback reply. Each rate here names its denominator, because a count per request and a count per message answer different questions.

**Working rule:** Report a call's input as the whole prompt, cached part included, and report cached input beside it, never added to it. Give output on its own. Name the count's source beside any token total, because the same text takes a different number of tokens in a different vocabulary.

## Summing spans double counts {#totals-from-metrics-not-spans}

The obvious way to total a day's tokens is to add the usage on every span. That is the sum a backend's query would run first, and here it is wrong. The [conventions' note on aggregating token usage](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/gen-ai-token-metrics.md) says not to sum `gen_ai.usage.*` over all spans without filtering by operation name, because the same tokens can be reported on more than one type of span, such as an agent span and an inference span. Usage sits on each model call's inference span, and the assistant also sets the message's total on its agent span, as the conventions allow. [Chapter 2](#span-types-for-each-step) names both span types.

Adding the usage up three ways over the same day shows where the extra comes from.

Example `totals-metric-against-spans` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Summing usage over every span counts each input token twice, because the agent span carries its message's usage as well as
its model calls do (the registry's aggregation note). The assistant's live meter counts each call once, as the call ends,
and matches the inference spans. The two asserts are the facts the prose relies on."""
from lib.dayrun import RELEASE, run_day_traced
from lib.metrics import PER_OPERATION, USAGE, make_meter_provider, totals
from lib.names_map import NAMES, REGISTRY_VERSION
from lib.report import fmt_int
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

DAY = "2026-12-08"
INPUT = "gen_ai.usage.input_tokens"
reader = InMemoryMetricReader()
provider = make_meter_provider(reader, service_instance_id=f"{DAY}-metrics", service_version=RELEASE.service_version)
traced = run_day_traced(DAY, live=False, meter_provider=provider)   # the assistant records each call's tokens as it ends
attributes = [s["attributes"] for s in traced.spans]
inference = [a for a in attributes if a.get("gen_ai.operation.name") == "chat"]
agents = [a for a in attributes if a.get("gen_ai.operation.name") == "invoke_agent"]   # one per message


def summed(rows, key):
    """The sum of one usage attribute over span attributes; a span without it adds zero."""
    return sum(row.get(key, 0) for row in rows)


got = totals(reader)
spans_input = summed(inference, INPUT)
every_span_input = summed(attributes, INPUT)
counter_input = int(got[USAGE["input"]]["sum"])
print("messages:", fmt_int(len(traced.runs)))
print("inference spans, one per model call:", fmt_int(len(inference)))
print("agent spans, invoke_agent, one per message:", fmt_int(len(agents)))
print("input tokens, summed over the inference spans:", fmt_int(spans_input))
print("input tokens, summed over every span:", fmt_int(every_span_input))
print("input tokens, token counter total:", fmt_int(counter_input))
print("input tokens, per-operation histogram sum:", fmt_int(int(got[PER_OPERATION["input"]]["sum"])))
print("per-operation histogram, count of operations:", fmt_int(got[PER_OPERATION["input"]]["count"]))
print("output tokens, token counter total:", fmt_int(int(got[USAGE["output"]]["sum"])))
print("GenAI conventions version:", REGISTRY_VERSION)
print("package token histogram, gen_ai.client.token.usage, v0.1.0 names:", ", ".join(NAMES["gen_ai.client.token.usage"]))
assert every_span_input == 2 * spans_input      # the agent spans repeat every inference token once more
assert counter_input == spans_input             # the counter reads each call's usage once, as the call ends
```

Output:

```text
messages: 200
inference spans, one per model call: 321
agent spans, invoke_agent, one per message: 200
input tokens, summed over the inference spans: 104,811
input tokens, summed over every span: 209,622
input tokens, token counter total: 104,811
input tokens, per-operation histogram sum: 104,811
per-operation histogram, count of operations: 321
output tokens, token counter total: 4,996
GenAI conventions version: 0.1.0
package token histogram, gen_ai.client.token.usage, v0.1.0 names: gen_ai.client.inference.operation.input_tokens, gen_ai.client.inference.operation.output_tokens
```

The assistant records each model call's tokens on its meter as the call ends, and the book reads two instruments from that meter. A metric is a measurement the SDK aggregates over many operations and exports without each one's detail; a counter only adds, and a histogram counts values into buckets with their sum and count. The input-token counter, `gen_ai.client.inference.usage.input_tokens`, gives one total for the day. The per-operation histogram records one value for each model call, its input tokens, and keeps their sum and their count.

Summed over the inference spans, the input is 104,811 tokens. Summed over every span, it is 209,622. The second figure is the first with the agent spans' copy added, so it is too high by exactly that copy. The token counter, which the assistant adds to on each model call, gives 104,811, the same total as the inference spans. The point to keep is that the counter and the inference spans agree, and the sum over every span does not.

The per-operation histogram's sum is 104,811 over 321 operations, the model calls, which matches the counter. The output counter gives 4,996 output tokens.

The package this book uses writes an older token metric: one histogram, `gen_ai.client.token.usage`, that splits by `gen_ai.token.type`. [Chapter 3](#what-the-package-emits) shows its names beside the registry's, and in v0.1.0 that histogram's names are gen_ai.client.inference.operation.input_tokens, gen_ai.client.inference.operation.output_tokens. The counters split by `gen_ai.token.modality` instead, and for each operation the modality counts add up to the total. The conventions' note says that the token counters are not affected by trace sampling, so a total read from them survives a sampler that drops spans, and a total read from spans does not. A counter filled at each call counts every call whatever a sampler keeps; a total rebuilt from sampled spans falls with the sample, and must be scaled up, with an [error](#how-a-span-records-failure), as [chapter 11](#estimating-totals-from-a-sample) shows.

**Working rule:** Take a day's token total from the counters, or sum usage over inference spans only, filtered by operation name. Usage on an agent span is that agent's total over its calls, so never add it to the calls' usage. In production we read totals from the counters, because a sampler cannot thin them.

## Cached input, derived from the counters {#cached-prompt-tokens}

The runtime does not report the reused count, so the book derives it: cached input is the prompt tokens minus the tokens the runtime evaluated. Reuse happens in two places. The runtime keeps the evaluated prefix of the last prompt, and a call whose prompt starts with the same tokens evaluates only the new suffix; the baseline also turns on a RAM cache, `PromptCache(LlamaRAMCache)` with `cache_prompt: true`, which restores the saved state of an earlier prompt with the longest shared prefix once the context's own prefix has been overwritten. The assistant's system prompt and its tool list sit at the front of every prompt, so most calls reuse them.

The pinned llama-cpp-python 0.3.37 has no cached-token field in its Python API or in the performance counters it ships. The recorder takes `n_p_eval`, the prompt tokens evaluated, as a difference between calls, because the counters accumulate. The counter `n_reused` sits in the same structure, but it counts graph reuse, not tokens, so this book does not read it as the cached count. We judge that a derived count of reused prefix tokens belongs in `gen_ai.usage.cache_read.input_tokens` and the cache-read counter, and we record a zero when nothing is reused. The registry defines that attribute as tokens served from a provider-managed cache, as the provider reports them, so the count is the book's own judgement and not a provider's report.

The same 60 messages run twice here, a seeded sample of baseline day 1: once on the baseline release, `r0`, and once on the cache-off release, `r4`. Release `r4` differs from `r0` in two ways. Its RAM cache is off, and `llm.reset()` clears the runtime's state before each call, which is the way the book's recorder gives each call a fresh state. Setting the cache to none is not enough, because the next call still reuses the prefix of the last one, as the book's probe at the pinned version found.

Example `cached-tokens-from-replay` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4 · tokenizers 0.23.3), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
baseline day 1, model calls: 321
baseline day 1, input tokens, total: 104,811
baseline day 1, cached input tokens, derived, total: 61,460
baseline day 1, cached share of input: 58.6%
same 60 messages, model calls: 93
r0, input tokens: 29,107
r0, tokens evaluated: 11,682
r0, cached input tokens, derived: 17,425
r4, input tokens: 29,107
r4, tokens evaluated: 29,107
r4, cached input tokens, derived: 0
tokens evaluated, r4 minus r0: 17,425
cost difference, r4 minus r0, same 60 messages, book-2026-11-02: $0.001394
```

Under the baseline the 60 messages read 29,107 input tokens, and only 11,682 of them were evaluated; the rest were cached. Under the cache-off release they read the same 29,107 tokens, and all of them were evaluated. Resetting the state did not change what the model read; it changed how much of it the runtime had to evaluate, so 17,425 more tokens were evaluated.

That difference is the money. At the book's table the cache-off release [costs](#cost-per-route) $0.001394 more on those 60 messages, because cached tokens are billed at the cached rate and evaluated ones at the input rate. A release which changes the cache changes cost and leaves input tokens alone, so a comparison of input tokens would miss that change.

**Working rule:** Derive cached input at each call from the runtime's counters, never from a release's label. When a release changes the cache, we compare cost on the same messages, because the input count will not move.

## The same utterances in other languages {#the-same-requests-in-other-languages}

Tokens are counted per vocabulary, and the same text can take very different numbers of tokens in different languages. Petrov and colleagues measured the gap for several tokenizers, found differences of up to fifteen times in some language pairs, and found the gap persisted in tokenizers built for many languages, as [their NeurIPS 2023 paper](https://arxiv.org/abs/2305.15425) reports. This section measures the gap for the dataset's utterances.

Only the English messages ran through the assistant. The other five locales are the same 200 utterances in the dataset's other locale files, joined by id. No model read them and no assistant served them, so each cost is an input rate on that text. The six locales are English (en-US), German (de-DE), Japanese (ja-JP), Hindi (hi-IN), Arabic (ar-SA) and Chinese (zh-CN). The example counts all six with the tokenizer file of the model the book uses, and prices the counts at [the book's table](#the-price-table).

Each locale's count is the tokenizer file's count: the utterance's text alone, normalised to NFC and tokenized by `tokenizers` 0.23.3 with the 4B's `tokenizer.json`; no model read it, and it is not a whole prompt.

Example `count-locales-with-the-tokenizer` (Python 3.13.16 · huggingface-hub 2.4.0 · numpy 2.5.5 · tokenizers 0.23.3), passing in Edition 2026.11.1:

```python
"""Count the same 200 baseline utterances in six locales with the 4B's own tokenizer file, and price the counts at the book's
input rate. The printed hi-IN ratio is the point the prose rests on: the same request takes several times the English
tokens. Each count is the utterance's text alone, not a whole prompt."""
from decimal import Decimal

from lib.case import load_locale, load_messages
from lib.clock import VirtualClock
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_usd
from lib.tokens import LocaleCounter, is_nfc

DAY = "2026-12-08"
MODEL = "Qwen3-4B-Instruct-2507"
LOCALES = ("en-US", "de-DE", "ja-JP", "hi-IN", "ar-SA", "zh-CN")
messages = load_messages(DAY)
ids = [m.message_id for m in messages]
texts = {m.message_id: m.text for m in messages}
by_id = sorted(messages, key=lambda m: int(m.message_id))   # the order load_locale returns each locale's utterances in
arrivals = [VirtualClock(DAY, start_ns=m.arrival_ns).now_ns for m in by_id]   # each message's own arrival, on the day's clock
counter, price = LocaleCounter(), PriceTable()

print("price table:", price.version)
print("utterances, the baseline day's messages joined by id:", fmt_int(len(ids)))
means = {}
for locale in LOCALES:
    utterances = load_locale(locale, ids)   # the same messages, in ascending ID order, so the locales line up
    counts = [counter.count(text) for text in utterances]
    total = sum(counts)
    means[locale] = total / len(counts)
    # The text is not cached, so every token bills at the input rate, each utterance at its message's arrival.
    per_thousand = sum((price.cost(MODEL, n, 0, 0, at) for n, at in zip(counts, arrivals)), Decimal(0)) * 1000 / len(counts)
    print(f"{locale}, tokens, total:", fmt_int(total))
    print(f"{locale}, tokens per utterance:", f"{means[locale]:.1f}")
    print(f"{locale}, input cost per 1,000 utterances, {price.version}:", fmt_usd(per_thousand))

print("hi-IN tokens per utterance, as a multiple of en-US:", f"{means['hi-IN'] / means['en-US']:.1f}")
hindi = load_locale("hi-IN", ids)
# NFC is applied by the tokenizer file, so only text that is not already NFC can count differently under another counter.
print(f"hi-IN utterances not in NFC, of {len(hindi)}:", sum(not is_nfc(text) for text in hindi))
assert [texts[i] for i in sorted(ids, key=int)] == load_locale("en-US", ids)  # the English texts are the traffic's own
assert all(is_nfc(t) for locale in LOCALES if locale != "hi-IN" for t in load_locale(locale, ids))
```

Output:

```text
price table: book-2026-11-02
utterances, the baseline day's messages joined by id: 200
en-US, tokens, total: 1,508
en-US, tokens per utterance: 7.5
en-US, input cost per 1,000 utterances, book-2026-11-02: $0.000754
de-DE, tokens, total: 2,194
de-DE, tokens per utterance: 11.0
de-DE, input cost per 1,000 utterances, book-2026-11-02: $0.001097
ja-JP, tokens, total: 1,979
ja-JP, tokens per utterance: 9.9
ja-JP, input cost per 1,000 utterances, book-2026-11-02: $0.000990
hi-IN, tokens, total: 6,864
hi-IN, tokens per utterance: 34.3
hi-IN, input cost per 1,000 utterances, book-2026-11-02: $0.003432
ar-SA, tokens, total: 2,015
ar-SA, tokens per utterance: 10.1
ar-SA, input cost per 1,000 utterances, book-2026-11-02: $0.001008
zh-CN, tokens, total: 1,314
zh-CN, tokens per utterance: 6.6
zh-CN, input cost per 1,000 utterances, book-2026-11-02: $0.000657
hi-IN tokens per utterance, as a multiple of en-US: 4.6
hi-IN utterances not in NFC, of 200: 8
```

The same 200 utterances cost 4.6 times as many tokens in Hindi as in English. The table gives each locale's count per utterance, and the input cost of 1,000 utterances at the book's table.

| Locale | Tokens per utterance | Input cost per 1,000 utterances |
| --- | --- | --- |
| English, en-US | 7.5 | $0.000754 |
| German, de-DE | 11.0 | $0.001097 |
| Japanese, ja-JP | 9.9 | $0.000990 |
| Hindi, hi-IN | 34.3 | $0.003432 |
| Arabic, ar-SA | 10.1 | $0.001008 |
| Chinese, zh-CN | 6.6 | $0.000657 |

The English utterances take 7.5 tokens each, and the Hindi ones take 34.3. A budget for input tokens written in English tokens is therefore wrong for a Hindi user, and the same holds for the cost of a request. The counts are of the utterance alone, so they understate a whole prompt in every locale. What carries into a budget is the ratio between locales, and that ratio should be measured on the traffic that will run.

Some of the Hindi text is not in the normal form the tokenizer expects. 8 of the 200 Hindi utterances are not in Unicode normalisation form NFC, as the [Unicode report on normalisation](https://unicode.org/reports/tr15/) defines it. The tokenizer file normalises them before counting. The GGUF tokenizer that llama.cpp uses applies no normalisation, so its count can differ from this one on those utterances, and at most 8 of the 200 can differ; the GGUF count was not run. This chapter prints the file's count and no other, and it says which counter each number comes from. The chapter quotes no utterance text, because no example prints it.

**Working rule:** Count each locale with the tokenizer that serves it, after the same normalisation, and name the counter beside every figure. Budget input in the locale's own tokens, and measure the locale's ratio on your own traffic before you rely on a multiple.

## The price table {#the-price-table}

Every money figure in this chapter comes from one file, the book's price table, `examples/data/case/prices.toml`, at version `book-2026-11-02`. The price table is a dated, versioned file of rates per million tokens, read at each call's virtual timestamp. For each model it gives rates in US dollars for input, cached input and output, and a date from which each row applies. The rows were written for this book, not quoted from any provider; each row says what a hosted endpoint would charge at those rates. The ratios matter most: on the 4B row, output costs 4.0 times input, and cached input 0.2 of input.

Hosted providers do not all report input the same way. Anthropic's `input_tokens` excludes cached tokens, and the conventions' [Anthropic note](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/v0.1.0/docs/gen-ai/anthropic.md) asks instrumentation to add them in, so a reader pricing such a provider normalises its fields to the registry's input total before pricing. Cache writes are counted apart, in `gen_ai.usage.cache_write.input_tokens`. The book's runtime writes no cache, so its table has no cache-write rate.

A self-hosted model is billed by its machine, not by its tokens. The table therefore attaches a money figure to a token count so that the book can compare requests. It is not a bill for the local model, and [Small Open Models](https://rollingedition.com/small-open-models/s/count-the-bill-and-the-machine) works out a machine's bill against per-token prices.

The nearest real price is the genai-prices listing, and it differs from the book's rows in three ways: it names a provider, it has no cache price, and it carries no date. genai-prices 0.2.5 lists the repository `Qwen/Qwen3-4B-Instruct-2507` under the provider `huggingface_nscale`, with an input rate and an output rate. With no cache price, the listing bills cached input at the input rate. The rates are the snapshot the library bundles, and the library makes no network call unless its updater is started. A lookup needs both the full repository name and `provider_id="huggingface_nscale"`: without the provider it raises `LookupError`, and so does a provider it does not list, as the example asserts. The listing has no text-model row for `Qwen3-0.6B`, so the book's 0.6B row has no source. The library's 4B row has no start date, and the book's probe at the pinned version found that it prices the same request the same on 2026-11-01, 2026-11-02 and 2026-12-08. So the 2026-11-02 date in the book's table is the book's own, and the library does not supply it.

One answer request from the day, priced three ways, shows how the tables differ.

Example `price-one-request` (Python 3.13.16 · bm25s 0.3.16 · genai-prices 0.2.5 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
request, input tokens, total: 212
request, cached input tokens, derived: 201
request, output tokens: 27
book's table, cached input at its own rate, book-2026-11-02: $0.000016
book's table, the same request with no cached input, book-2026-11-02: $0.000032
book's table, output rate to input rate: 4.0
book's table, cached input rate to input rate: 0.2
genai-prices listing, huggingface_nscale, the same request: $0.000003
```

The request reads 212 input tokens, most of them cached, and writes 27 output tokens. At the book's table it costs $0.000016. With the cache removed from the same request it would cost $0.000032, so the cache is what brings the bill down for this call.

The listing prices the same request at $0.000003. The gap between the two is the gap between the rate rows, since the tokens are the same in both.

A cost tool needs one more guard. The book's spans record `gen_ai.provider.name` as `openai`, because the assistant's client speaks OpenAI's API to a local server, as [chapter 2](#span-types-for-each-step) explains. A cost tool that reads that value could look up OpenAI's rates for a model OpenAI does not serve, and price the local model at OpenAI's rates. The listing fails loudly on that lookup, since it raises `LookupError` for the 4B under `openai`, so the risk is a tool that falls back to a default model or a fuzzy match. The book's table is keyed by model and does not read the provider value, and the listing is queried with its provider named by hand. A query that prices spans should do the same, and should never take the provider from the span. MLflow is one such tool: it prices a span only when its catalog knows the span's model, which is why it stored no cost for the 4B in [chapter 5](#mlflow-on-sqlite), and a self-hosted model reported under a hosted model's name could be priced at that model's rates.

The table's version and dates matter once a price changes. The release comparison in [chapter 10](#paired-comparison-on-messages) reads its money from this same table version, so one version holds every money figure that is compared.

**Working rule:** Attach a price table's version and its date to every money figure. Price each call at its own timestamp, and name the provider when you use a listing. Never take a provider from a span to choose the price. We key the book's table by model, and never by the span's provider.

## Cost by route and step {#cost-per-route}

A call's cost is its tokens priced by a named, dated price table, and cost attribution assigns each call's cost to the step, route and user that caused it. [Agent Harnesses](https://rollingedition.com/agent-harnesses/s/cost-not-money) stops its cost at counts on purpose; this book adds money, tokens first. The book computes cost at query time, from each call's tokens and the table, and does not store cost on the spans. A price change then reprices the query and leaves the stored spans as they were. [Chapter 1](#where-the-time-went-in-twenty-messages) asked which step costs the most money, and this section answers it.

Example `cost-by-route-and-user` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
messages: 200
cost, all messages, book-2026-11-02: $0.007563
route requests, cost, book-2026-11-02: $0.001379
route requests, share of cost: 18.2%
answer requests, cost, book-2026-11-02: $0.006184
answer requests, share of cost: 81.8%
route alarms, messages: 16
route alarms, cost per 1,000 messages, book-2026-11-02: $0.063688
route calendar, messages: 27
route calendar, cost per 1,000 messages, book-2026-11-02: $0.057486
route devices, messages: 17
route devices, cost per 1,000 messages, book-2026-11-02: $0.056201
route fallback, messages: 89
route fallback, cost per 1,000 messages, book-2026-11-02: $0.006630
route lists, messages: 13
route lists, cost per 1,000 messages, book-2026-11-02: $0.074429
route media, messages: 31
route media, cost per 1,000 messages, book-2026-11-02: $0.057041
route messages, messages: 7
route messages, cost per 1,000 messages, book-2026-11-02: $0.101463
resolved messages: 111
cost of a resolved message, its own calls, book-2026-11-02: $0.000063
users with a message: 121
cost per user, mean over users with a message, book-2026-11-02: $0.000063
costliest user, messages: 3
costliest user, share of cost: 3.0%
```

The answer step costs most. Over the day's 200 messages, the answer requests cost $0.006184, which is 81.8% of the day's cost. The route requests cost $0.001379, or 18.2%. The route call is smaller, but every message makes one, so it still holds nearly a fifth of the money.

The routes differ in what a message costs. The table gives each route's messages, its tokens per message from the same day, and its cost per 1,000 messages. The denominator is the messages on each route.

| Route | Messages | Input tokens per message | Output tokens per message | Cost per 1,000 messages |
| --- | --- | --- | --- | --- |
| `alarms` | 16 | 883.6 | 43.4 | $0.063688 |
| `calendar` | 27 | 903.5 | 38.8 | $0.057486 |
| `devices` | 17 | 627.9 | 44.5 | $0.056201 |
| `fallback` | 89 | 145.4 | 6.0 | $0.006630 |
| `lists` | 13 | 936.5 | 29.0 | $0.074429 |
| `media` | 31 | 663.9 | 41.6 | $0.057041 |
| `messages` | 7 | 1415.4 | 42.1 | $0.101463 |

The `messages` route costs the most per message. It rests on 7 messages, though, so read it as one day's sample and not as a settled rate. The `fallback` route costs the least. Its reply is the fixed one that [chapter 1](#where-the-time-went-in-twenty-messages) describes, and its span records that no model wrote it. The route makes its one route call and no answer call, so its row carries the route call alone.

Example `figure-route-token-mix` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
"""Draw the input, cached and output tokens per message on each route, over baseline day 1's 200 messages. The cached part is
drawn inside the input bar, hatched, so no reader adds it to input; output stands beside it. Every bar is printed by route
with its message count, since a tokens-per-message rate names its denominator (PL-11)."""
from lib.dayrun import run_day
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int

runs = run_day("2026-12-08")
routes = sorted({run.outcome.route for run in runs})
per_message = {}                            # route: (input, cached, output) tokens per message, as floats
for route in routes:
    mine = [run for run in runs if run.outcome.route == route]
    steps = [s for run in mine for s in run.outcome.steps if s.name == "chat"]   # model calls only; no tool time here
    averages = tuple(sum(values) / len(mine) for values in (
        [s.prompt_tokens for s in steps], [s.cached_tokens for s in steps], [s.completion_tokens for s in steps]))
    per_message[route] = averages
    print(f"route {route}, messages:", fmt_int(len(mine)))
    print(f"route {route}, input tokens per message:", f"{averages[0]:.1f}")
    print(f"route {route}, cached input tokens per message:", f"{averages[1]:.1f}")
    print(f"route {route}, output tokens per message:", f"{averages[2]:.1f}")

fig, ax = new_figure(height=2.8)
positions, width = list(range(len(routes))), 0.36
left, right = [p - width / 2 for p in positions], [p + width / 2 for p in positions]
cached = [per_message[r][1] for r in routes]
uncached = [per_message[r][0] - per_message[r][1] for r in routes]   # input minus its cached part, stacked on top of it
ax.bar(left, cached, width=width, color=MUTED, hatch="///", edgecolor=INK, label="cached input, part of input")
ax.bar(left, uncached, bottom=cached, width=width, color=ACCENT, label="input not cached")
ax.bar(right, [per_message[r][2] for r in routes], width=width, color=INK, label="output tokens")
ax.set_xticks(positions, routes)
ax.set_ylabel("tokens per message")
ax.set_ylim(0, 1.35 * max(v[0] for v in per_message.values()))   # headroom above the tallest bar for the legend
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False)   # below the plot, clear of the top tick
save(fig, "route-token-mix")
```

Output:

```text
route alarms, messages: 16
route alarms, input tokens per message: 883.6
route alarms, cached input tokens per message: 525.3
route alarms, output tokens per message: 43.4
route calendar, messages: 27
route calendar, input tokens per message: 903.5
route calendar, cached input tokens per message: 604.9
route calendar, output tokens per message: 38.8
route devices, messages: 17
route devices, input tokens per message: 627.9
route devices, cached input tokens per message: 305.1
route devices, output tokens per message: 44.5
route fallback, messages: 89
route fallback, input tokens per message: 145.4
route fallback, cached input tokens per message: 128.9
route fallback, output tokens per message: 6.0
route lists, messages: 13
route lists, input tokens per message: 936.5
route lists, cached input tokens per message: 385.3
route lists, output tokens per message: 29.0
route media, messages: 31
route media, input tokens per message: 663.9
route media, cached input tokens per message: 325.1
route media, output tokens per message: 41.6
route messages, messages: 7
route messages, input tokens per message: 1415.4
route messages, cached input tokens per message: 711.7
route messages, output tokens per message: 42.1
figure: figures/route-token-mix.svg
```

Figure 6.1 shows each route's input tokens per message, with the cached part inside the input bar, and its output tokens beside it. A route can be cheap in output and still expensive in prompt.

*Figure 6.1. Input, cached input and output tokens per message, by route. The fallback route's bars are its route call alone.*

![Each route's input tokens per message, with the cached part hatched inside the input bar, and its output tokens beside it. The messages route's input is the tallest bar, and every route's output is short.](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.1/figures/route-token-mix.svg)

Figure 6.1 shows that the lists route writes the least output of any route but the fallback route, 29.0 tokens per message, and still reads 936.5 input tokens per message. The messages route reads 1415.4 input tokens per message, of which 711.7 are cached. Every route reads far more than it writes.

Two per-unit figures close the section, each with its denominator. A [resolved message](#three-token-counts) costs $0.000063 in its own calls, over the 111 messages the model answered. Per user, the day costs $0.000063 on average, over the 121 users who sent a message that day.

The costliest of those users sent 3 messages and holds 3.0% of the day's cost.

**Working rule:** Attribute each call's cost to its step, route and user from each call's recorded counts, print each share beside its total, and name the denominator of every per-unit rate. Read a route's rate with its message count beside it, because a route with a handful of messages can move a lot from one day to the next. For the finance question we report each route's rate, not one mean over the day, because the money differs by route.

## The expensive tail {#the-expensive-tail}

An average hides the few messages that cost much more than the rest. The check is to rank the messages by cost and ask what share of the day's money the top 1% holds. With 200 messages, the top 1% is two messages.

Example `expensive-tail-share` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
messages: 200
messages in the most expensive 1%: 2
cost of the day, book-2026-11-02: $0.007563
cost of the most expensive 1%, book-2026-11-02: $0.000234
share of the day's cost, most expensive 1%: 3.1%
most expensive message, route: messages
most expensive message, cost, book-2026-11-02: $0.000118
most expensive 1%, messages resolved by the model: 2
```

On this day there is no concentrated expensive tail. The two most expensive messages cost $0.000234 of the day's $0.007563, which is 3.1% of the cost. The most expensive of them, on the `messages` route, cost $0.000118. Both of the top two were resolved by the model, so [the tail](#tail-percentiles-with-intervals) is an answer tail, not a fallback one.

The count is exact over one day, so it says what this day's messages cost and nothing about another day. How far another day would move the share needs a method this chapter does not use. The method is the bootstrap, which applies to any per-message statistic, and [chapter 7](#tail-percentiles-with-intervals) introduces it. Until then, a tail on one day is a count to report with its denominator, and not a rate to plan a budget on.

**Working rule:** Report the top 1% of messages as a count and as a share of the day's total, with the day named. Do not call a share small or large until a second day gives something to compare it with.

## What goes wrong in production {#tokens-and-cost-in-production}

A token total on a dashboard can double after a gateway or a rollup starts carrying the usage of the calls beneath it, and nothing else in the pipeline changed. The sum over spans counts those tokens twice. Read totals from the counters, or filter the spans by operation name, as the conventions' note says.

A dashboard total read from spans halves when the backend starts keeping half its traces, because the spans fall with the sample. The counters are unaffected. Keep the counters for totals, and keep the spans for questions the counters cannot answer, such as which route a message took. [Chapter 11](#estimating-totals-from-a-sample) scales a sampled total up, with its error.

The bill moves while the input count stays flat, because a release changed how much of the prompt was cached. A dashboard that tracks input tokens alone misses the change. Track cost beside input and cached input, and read the cached count against the release it belongs to.

A local model is priced at a hosted provider's rates when a cost tool takes the provider from the span, and the span says `openai`. The listing fails loudly on that lookup, so the danger is a tool that falls back to a default model or a fuzzy match. The book's table is keyed by model, and a listing is queried with its provider named. Any tool that prices a span should do the same.

A month's cost changes on the day a price changes, though no message did. Each row in the book's table carries a valid-from date, and each call is priced at its own timestamp. A cost stored on a span would keep the old price, so the book computes cost at query time.

A budget set in English tokens fails for Hindi users, and the difference lies in the vocabulary, not in the traffic. Measure each locale's ratio on the traffic that will run, and count with the tokenizer that serves the locale.

**Working rule:** Keep totals on the counters, cost on the table with its version, and each locale's count on its own tokenizer. When a release changes the prompt or the cache, read its cost next to its tokens, because the two can move apart.

## What this chapter decided {#tokens-and-cost-decisions}

- Tokens come first and money second. Every money figure names the price table's version, `book-2026-11-02`, and its date.
- Input tokens include the cached part. Cached input is derived from the runtime's counters, and it is never added to input.
- Totals come from the counters. A sum over spans is taken over inference spans only, filtered by operation name. An agent span's usage is that agent's total, and it is never added to the calls' usage.
- Cost is computed at query time from the table and each call's timestamp. It is not stored on spans.
- The cache-off release is called reset per call, because the pinned runtime has no switch for the cache.
- Locale counts use the tokenizer file, after NFC normalisation, and the chapter prints no GGUF count. Utterance text is not quoted, because no example prints it.
- The chapter uses no interval, because a one-day count is exact and needs none. [Chapter 7](#tail-percentiles-with-intervals) gives the method for another day's spread.
- The prices are the book's judgement: dated, versioned and not a quote. A reader who prefers another price changes the table and keeps the counts, and every sentence about tokens still holds. That split is why the chapter does the tokens first.
