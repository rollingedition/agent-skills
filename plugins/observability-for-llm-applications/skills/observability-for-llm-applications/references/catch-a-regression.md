---
title: "Observability for LLM Applications"
chapter: "Catch a regression in the traces"
chapter_id: catch-a-regression
book: observability-for-llm-applications
edition: 2026.11.3
verified: 2026-11-23
edition_code: 9P10-Q8SD
canonical: https://rollingedition.com/observability-for-llm-applications/catch-a-regression
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Catch a regression in the traces,” chapter 10 of Observability for LLM Applications, Edition 2026.11.3, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/observability-for-llm-applications/catch-a-regression. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Catch a regression in the traces

By the end of this chapter you can say whether a release moved a number, by how much, and whether that move is bigger than the day's noise. You can also write the rule that stops a release from shipping when it moves too far. Four changes to the assistant wait to ship, and each claims to change nothing that matters. One adds six routing examples to the route prompt. One swaps the 4B model, Qwen3-4B-Instruct-2507, for the smaller Qwen3-0.6B. One retrieves more articles for the routes that retrieve, and one turns the prompt cache off. Which of them moved latency, tokens, cost, errors or route accuracy? And would a gate catch the ones that did, without stopping a normal day?

The question has two parts, and the second is the harder one. A release can move a number on the messages it was measured on and still sit inside what an ordinary day would show. So the comparison has to run both releases on the same messages, and it has to say how far the difference could move. The chapter builds a comparison of the two releases on the same messages, and turns it into a gate with fixed limits. It marks each trace with its release so a query can split them, pairs the releases message by message, and puts an interval beside every difference.

## Release markers in the spans {#release-markers-in-the-spans}

A comparison can only split traces by release if each trace says which release made it. Chapter 2 put the markers in place. The resource carries `service.version`, which names the release, and each inference span carries `gen_ai.prompt.version`, which names the prompt it was sent with ([who made the span](#who-made-the-span), and [the requirement levels](#requirement-levels), where the prompt pair appears). A release is marked by `service.version` on the resource and `gen_ai.prompt.version` on the inference span, so a query can split traces by release.

The marker does more than label. Without it, a query over a week of traces would mix the releases into one average, and no release would show its own movement. With it, the same query returns one row per release. Below, the same 60 messages are replayed under the baseline and under each of the four changes, and every span of the five replays goes into one file. Each replay keeps its own markers, and the span IDs come from one sequence, so no two replays share an ID.

Example `release-markers-query` (Python 3.13.16 · bm25s 0.3.16 · duckdb 2.0.1 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""Replay the same 60 messages under each of the five releases, export every span to one store, and query the release
markers: the resource's service.version and the inference span's gen_ai.prompt.version. Each release's markers are the
only thing that tells its traces apart, so the query must give five distinct pairs. The span IDs come from one sequence,
so no two releases share an ID in the store."""
from lib.assistant import RELEASES
from lib.case import load_messages
from lib.export import write_jsonl
from lib.gate import release_spans
from lib.query import connect
from lib.report import fmt_int

import tempfile
from pathlib import Path

DAY = "2026-12-08"
FOLDERS = {"r0": "baseline-day-1", "r1": "release-prompt-v2", "r2": "release-model-swap",
           "r3": "release-top-8", "r4": "release-cache-off"}
PAIRED = {m.message_id for m in load_messages("2026-12-08-paired")}   # the 60 messages, in every release's recording
rows = release_spans(DAY, FOLDERS, PAIRED)
with tempfile.TemporaryDirectory() as folder:
    rows_file = Path(folder) / "spans.jsonl"     # the stored rows, as a file a query can read
    write_jsonl(rows_file, rows)
    db = connect(rows_file)
    markers = db.execute(
        "WITH inference AS (SELECT json_extract_string(resource, '$.\"service.version\"') AS version, "
        "json_extract_string(attributes, '$.\"gen_ai.prompt.version\"') AS prompt, "
        "json_extract_string(attributes, '$.\"gen_ai.prompt.name\"') AS name, trace_id FROM spans "
        "WHERE json_extract_string(attributes, '$.\"gen_ai.operation.name\"') = 'chat') "
        "SELECT version, prompt, name, count(*), count(DISTINCT trace_id) FROM inference "
        "GROUP BY version, prompt, name ORDER BY version, prompt, name").fetchall()
    per_version = db.execute(
        "SELECT json_extract_string(resource, '$.\"service.version\"') AS version, count(DISTINCT trace_id) "
        "FROM spans GROUP BY version ORDER BY version").fetchall()

for version, prompt, name, calls, traces in markers:
    print(f"service.version {version}, gen_ai.prompt.version {prompt}, {name}: {fmt_int(calls)} inference spans")
for version, traces in per_version:
    print(f"service.version {version}, messages (traces): {fmt_int(traces)}")
pairs = {(version, prompt) for version, prompt, _, _, _ in markers}
assert pairs == {(r.service_version, r.prompt_version) for r in RELEASES.values() if r.name in FOLDERS}
assert all(traces == len(PAIRED) for _, traces in per_version)   # every release answered every paired message
```

Output:

```text
service.version 1.0.0, gen_ai.prompt.version p1, ambrewick.answer: 33 inference spans
service.version 1.0.0, gen_ai.prompt.version p1, ambrewick.route: 60 inference spans
service.version 1.1.0, gen_ai.prompt.version p2, ambrewick.answer: 33 inference spans
service.version 1.1.0, gen_ai.prompt.version p2, ambrewick.route: 60 inference spans
service.version 1.2.0, gen_ai.prompt.version p1, ambrewick.answer: 16 inference spans
service.version 1.2.0, gen_ai.prompt.version p1, ambrewick.route: 60 inference spans
service.version 1.3.0, gen_ai.prompt.version p1, ambrewick.answer: 33 inference spans
service.version 1.3.0, gen_ai.prompt.version p1, ambrewick.route: 60 inference spans
service.version 1.4.0, gen_ai.prompt.version p1, ambrewick.answer: 33 inference spans
service.version 1.4.0, gen_ai.prompt.version p1, ambrewick.route: 60 inference spans
service.version 1.0.0, messages (traces): 60
service.version 1.1.0, messages (traces): 60
service.version 1.2.0, messages (traces): 60
service.version 1.3.0, messages (traces): 60
service.version 1.4.0, messages (traces): 60
```

The query groups the inference spans by their two markers and counts them, and it counts the traces each release produced. Every release answers the same 60 messages, which is why the trace counts match. The run asserts that the five marker pairs are exactly the pairs the release table gives, and that every release answered every message, so a missing marker fails the run rather than thinning a row.

Each release produced 60 traces, one per message. The table shows what the markers separate, and the answer calls are the count to check: the model swap is the row that differs from its neighbours.

| Release | Prompt version | Answer calls |
| --- | --- | --- |
| Baseline | p1 | 33 inference spans |
| Prompt change | p2 | 33 inference spans |
| Model swap | p1 | 16 inference spans |
| Top-8 release | p1 | 33 inference spans |
| Cache-off release | p1 | 33 inference spans |

Under the model swap there are fewer answer calls than under the baseline, on the same 60 messages. An answer call is the model call that writes the reply, and a message routed to fallback makes none. The model swap makes fewer of them because it routes more messages to fallback. [The CI gate](#the-ci-gate) counts the routes that changed later in this chapter. Without the markers the five rows would collapse into one, and nothing in the table would say which release made which call.

**Working rule:** Mark every trace with its release and its prompt version, and split each query by both before you read a number.

## Paired comparison on messages {#paired-comparison-on-messages}

Two releases measured on different messages differ for two reasons: the release, and the messages. A day's messages vary a great deal. Some are long requests, some route to the fallback reply, and some wait on a slow tool. Run both releases on the same messages and the second reason drops out of each difference, because each message serves as its own control. A paired comparison runs two releases on the same messages and summarises, for each message, the release's value minus the baseline's.

The method is the one that Evaluating LLM Applications calls a [paired comparison](https://rollingedition.com/concepts/artificial-intelligence/paired-comparison). That book subtracts verdicts; this one subtracts the values it reads from traces. Every latency here comes from the recording machine, a 4-vCPU Intel Xeon at 2.10 GHz, as chapter 1 describes, and the replays run on the virtual clock. Message time is the sum of the recorded durations of a message's model calls and contacts-tool calls, which is the number chapter 7 counts. The gaps the recorder left between calls are not in it.

Each measure has its own statistic. For message time, input tokens, cost, errors and [route accuracy](#wrong-routes-against-labels), the statistic is the mean of the per-message differences. The percentile is different, and the text says which statistic each difference is. For the 95th percentile, the book takes the difference of the two p95s, and it resamples the messages jointly: each resample draws the same messages for both releases and takes the 95th percentile on each side. The interval around every difference is chapter 7's percentile bootstrap, run on the messages and resampled as pairs. For a mean, the statistic is the mean of the per-message differences, and for the p95 it is the difference of the two p95s. The unit resampled is the message and never the span. Chapter 7 built that bootstrap for one release's percentile, and here the same resampling runs on pairs.

Input tokens here are the recorded counts, and [chapter 6](#three-token-counts) says where each count comes from.

Next, the example sets each change beside the baseline on the messages that change recorded.

Example `paired-latency-and-tokens` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""Compare each release with baseline r0 on the same messages, in message time and input tokens: the mean of the per-message differences, and the p95 difference with the two p95s resampled jointly (PL-6). Each interval is a bootstrap of 2,000 resamples at 95 %, seed 20261207. The unpaired width for the input tokens is printed beside the paired one: the messages' own lengths cancel out of the paired difference."""
from lib.gate import measured, paired, paired_report

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
RELEASES_TO_COMPARE = [   # name, the release's recording folder, the model it ran
    ("r1", "release-prompt-v2", MODEL),       # p2: six routing examples in the route prompt
    ("r2", "release-model-swap", "Qwen3-0.6B"),
    ("r3", "release-top-8", MODEL),            # top 8 articles instead of 3
    ("r4", "release-cache-off", MODEL),        # a fresh state per call, so no cached prefix
]
base = measured("baseline-day-1", DAY, MODEL)  # r0, the cache on, on all 200 messages of baseline day 1
for name, folder, model in RELEASES_TO_COMPARE:
    _, before, after = paired(base, measured(folder, DAY, model))   # the messages this release recorded
    paired_report(name, before, after)
```

Output:

```text
r1, messages (paired with r0): 60
r1, r0 p95 message time on these messages: 17,128.2 ms
r1, message time, mean difference: 726.1 ms (95% interval 79.8 ms to 1,333.3 ms)
r1, message time, p95 difference: -345.3 ms (95% interval -495.9 ms to 2,301.0 ms)
r1, input tokens per message, mean difference: 90 (95% interval 70 to 115)
r1, input tokens, interval width paired: 45
r1, input tokens, interval width if unpaired: 276
r1, cost per 1,000 messages, mean difference: $0.006281 (95% interval $0.003197 to $0.009519)
r1, error rate, mean difference: +0.0% (95% interval +0.0% to +0.0%)
r1, route accuracy, mean difference: +3.3% (95% interval +0.0% to +8.3%)
r2, messages (paired with r0): 200
r2, r0 p95 message time on these messages: 18,351.2 ms
r2, message time, mean difference: -6,750.9 ms (95% interval -7,599.5 ms to -5,921.4 ms)
r2, message time, p95 difference: -14,109.1 ms (95% interval -16,749.8 ms to -12,105.6 ms)
r2, input tokens per message, mean difference: -200 (95% interval -258 to -148)
r2, input tokens, interval width paired: 110
r2, input tokens, interval width if unpaired: 137
r2, cost per 1,000 messages, mean difference: -$0.033156 (95% interval -$0.037326 to -$0.029012)
r2, error rate, mean difference: +0.0% (95% interval +0.0% to +0.0%)
r2, route accuracy, mean difference: -21.0% (95% interval -28.0% to -14.5%)
r3, messages (paired with r0): 60
r3, r0 p95 message time on these messages: 17,128.2 ms
r3, message time, mean difference: 2,222.5 ms (95% interval 1,099.6 ms to 3,462.8 ms)
r3, message time, p95 difference: 7,618.8 ms (95% interval 1,914.5 ms to 12,517.7 ms)
r3, input tokens per message, mean difference: 115 (95% interval 60 to 179)
r3, input tokens, interval width paired: 119
r3, input tokens, interval width if unpaired: 337
r3, cost per 1,000 messages, mean difference: $0.012542 (95% interval $0.006844 to $0.018909)
r3, error rate, mean difference: +0.0% (95% interval +0.0% to +0.0%)
r3, route accuracy, mean difference: +0.0% (95% interval +0.0% to +0.0%)
r4, messages (paired with r0): 60
r4, r0 p95 message time on these messages: 17,128.2 ms
r4, message time, mean difference: 2,881.5 ms (95% interval 2,209.1 ms to 3,677.3 ms)
r4, message time, p95 difference: 2,128.9 ms (95% interval 1,839.2 ms to 16,968.2 ms)
r4, input tokens per message, mean difference: 0 (95% interval 0 to 0)
r4, input tokens, interval width paired: 0
r4, input tokens, interval width if unpaired: 280
r4, cost per 1,000 messages, mean difference: $0.023233 (95% interval $0.018860 to $0.028303)
r4, error rate, mean difference: +0.0% (95% interval +0.0% to +0.0%)
r4, route accuracy, mean difference: +0.0% (95% interval +0.0% to +0.0%)
```

Pairing narrows the prompt change's token interval from 276 tokens wide to 45. On its 60 paired messages, input tokens per message rise by 90 (95% interval 70 to 115), and that rise is the change the gate has to see.

Its mean message time rises by 726.1 ms (95% interval 79.8 ms to 1,333.3 ms), and its 95th percentile moves the other way, by -345.3 ms (95% interval -495.9 ms to 2,301.0 ms). The mean and the p95 disagree in sign, and the p95's interval runs from below zero to far above it. On 60 messages the tail cannot say which way it moved. The p95 is printed here and not gated, and [what the gate misses](#what-the-gate-misses) says why.

Cost per 1,000 messages rises by $0.006281 (95% interval $0.003197 to $0.009519), priced at the book's price table, version `book-2026-11-02`, as [chapter 6](#the-price-table) sets out. The error rate does not move: +0.0% (95% interval +0.0% to +0.0%). The route accuracy difference is +3.3% (95% interval +0.0% to +8.3%). Its interval starts at zero, so this release has not been shown to change routing.

The model swap is the line with the most movement, and its comparison carries a caveat that applies to every line in it. The 0.6B's prompt carries `/no_think` as well as the smaller model, so the swap is not a pure model swap, as [prompt versions](#prompt-versions) explains. Its prompt version still reads p1. Mean message time changes by -6,750.9 ms (95% interval -7,599.5 ms to -5,921.4 ms). Route accuracy changes by -21.0% (95% interval -28.0% to -14.5%), and that change is the model and the suffix together. The swap ran all 200 messages of the baseline day. Its cost line rests on the 0.6B's row in the price table. The book wrote that row, and it has no source. The cost difference of -$0.033156 (95% interval -$0.037326 to -$0.029012) is therefore only as firm as that assumed rate.

The top-8 release retrieves more articles on the three routes that retrieve. [Chapter 7](#retrieved-context-against-prefill) measured the prefill that comes with the extra context. Here its input tokens rise by 115 (95% interval 60 to 179), and its mean message time by 2,222.5 ms (95% interval 1,099.6 ms to 3,462.8 ms).

The cache-off release is the one that should not move input tokens, and it does not. Its input total differs by 0 (95% interval 0 to 0), because the prompt the model reads is the same. Its cost rises by $0.023233 (95% interval $0.018860 to $0.028303), and its mean message time by 2,881.5 ms (95% interval 2,209.1 ms to 3,677.3 ms). The printed lines give the input total and the cost, not the cached count, so the cost line is the evidence here. [Chapter 6](#cached-prompt-tokens) explains how the cached count is derived.

Figure 10.1 draws the two differences for each release, the p95 message time on the left and input tokens per message on the right, each with its interval. The zero line is the reference. The prompt change's p95 interval crosses it, which is the tail's uncertainty in one picture. The token intervals for the prompt change, the model swap and the top-8 release lie clear of zero, and the cache-off release's token interval sits on it, as its input total says.

Example `figure-paired-differences` (Python 3.13.16 · bm25s 0.3.16 · matplotlib 3.11.2 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""Draw each release's paired difference from baseline r0 on the same messages, in p95 message time and in input tokens per message, each with its interval. A line that crosses the zero line is a difference the interval cannot rule out; the p95 uses messages resampled jointly, and the token mean uses per-message differences."""
from lib.gate import P95, measured, paired
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.report import fmt_int, fmt_ms
from lib.stats import paired_interval, paired_mean_difference
from matplotlib.ticker import FuncFormatter

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
RELEASES_TO_DRAW = [   # name, the row's label as the prose gives it, the recording folder, the model; each against r0
    ("r1", "Prompt change", "release-prompt-v2", MODEL),
    ("r2", "Model swap", "release-model-swap", "Qwen3-0.6B"),
    ("r3", "Top-8 release", "release-top-8", MODEL),
    ("r4", "Cache-off release", "release-cache-off", MODEL),
]
def show(line, point, low, high, fmt):
    """Print one difference with its 95% interval."""
    print(line, fmt(round(point)), f"(interval {fmt(round(low))} to {fmt(round(high))})")

base = measured("baseline-day-1", DAY, MODEL)
fig, (left, right) = new_figure(height=3.2, columns=2, sharex=False)
ticks = []
for row, (name, label, folder, model) in zip(range(len(RELEASES_TO_DRAW))[::-1], RELEASES_TO_DRAW):   # the top row first
    ids, before, after = paired(base, measured(folder, DAY, model))
    time_p, (time_low, time_high) = paired_interval([m["time"] for m in before], [m["time"] for m in after], P95)
    token_p, (token_low, token_high) = paired_interval([m["tokens"] for m in before], [m["tokens"] for m in after],
                                                       paired_mean_difference)
    show(f"{name}, p95 message time, difference:", time_p, time_low, time_high, fmt_ms)
    show(f"{name}, input tokens per message, difference:", token_p, token_low, token_high, fmt_int)
    left.hlines(row, time_low / 1e6, time_high / 1e6, color=MUTED, linewidth=3)
    left.scatter([time_p / 1e6], [row], color=ACCENT, zorder=3)
    right.hlines(row, token_low, token_high, color=MUTED, linewidth=3)
    right.scatter([token_p], [row], color=ACCENT, zorder=3)
    ticks.append((row, f"{label} (n = {len(ids)})"))
for axis in (left, right):
    axis.axvline(0, color=INK, linewidth=0.8)            # no difference: a release that changed nothing
    axis.set_yticks(*zip(*ticks))
right.tick_params(axis="y", labelleft=False)          # the rows are named once, on the left
left.set_xlabel("difference in p95\nmessage time (ms)")
left.set_xticks([-10_000, 0, 10_000])
left.xaxis.set_major_formatter(FuncFormatter(lambda ms, _: f"{ms:,.0f}".replace("-", "−")))   # thousands separators
right.set_xlabel("mean difference in input\ntokens per message")
right.set_xticks([-200, 0, 200])
save(fig, "paired-differences")
```

Output:

```text
r1, p95 message time, difference: -345.3 ms (interval -495.9 ms to 2,301.0 ms)
r1, input tokens per message, difference: 90 (interval 70 to 115)
r2, p95 message time, difference: -14,109.1 ms (interval -16,749.8 ms to -12,105.6 ms)
r2, input tokens per message, difference: -200 (interval -258 to -148)
r3, p95 message time, difference: 7,618.8 ms (interval 1,914.5 ms to 12,517.7 ms)
r3, input tokens per message, difference: 115 (interval 60 to 179)
r4, p95 message time, difference: 2,128.9 ms (interval 1,839.2 ms to 16,968.2 ms)
r4, input tokens per message, difference: 0 (interval 0 to 0)
figure: figures/paired-differences.svg
```

*Figure 10.1. Each release's paired difference from the baseline with its 95% interval: p95 message time on the left, input tokens per message on the right.*

![Two panels, one row per release: the prompt change's p95 interval crosses the zero line, the cache-off release's token interval sits on it, and the other intervals lie clear of zero](https://rollingedition.ai/books/observability-for-llm-applications/2026.11.3/figures/paired-differences.svg)

**Working rule:** Subtract the baseline's value for each message before you summarise. Resample the messages jointly for a percentile, and print each difference with its count and its interval.

## Prompt versions {#prompt-versions}

The releases differ in their prompts, and one of them differs in its model as well, so this section says what changed in each prompt before the gate judges the numbers. The baseline's prompt is `p1`. The prompt change is `p2`, which adds six routing examples to the route prompt. The six examples add 86 tokens to every route call, and every message makes one. The rest of the prompt change's rise, 4 tokens per message, and the width of its paired interval come from the 2 messages whose route changed, as [the paired comparison](#paired-comparison-on-messages) shows. The markers confirm that both prompts make one route call per message, on the same 60 messages. The top-8 release keeps `p1`'s template, and only its retrieved context grows.

The model swap keeps `p1` as its prompt version, and this is the point to read carefully. Its prompt is not the baseline's, because it carries `/no_think`. Qwen3-0.6B is hybrid-thinking, and its [model card at the pinned commit](https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/README.md) says that with thinking enabled the model always writes a `<think>...</think>` block, whose content may be empty when thinking is turned off. The recording script adds the suffix to the prompts. We decided that the release carries it, and that its prompt version stays `p1`. The release marker cannot show the suffix, so a query that splits by prompt version would count the model swap as the baseline's prompt. Under the suffix, the recording's model replies open with an empty block in 256 of their 257, and the assistant's parser drops that block from each reply. The pair still costs output tokens: on average, each route call's output grows by 4 tokens. One answer reply writes its reasoning into its block instead, and the parser drops that as well.

That matters for the token comparison. The two models share one Qwen3 tokenizer. The book checked that on three texts, and the 4B and the 0.6B give identical token IDs for each, so their input counts compare directly. The check covers three texts, not every message, and the chapter claims no more than that. The model swap's token difference is therefore the smaller model and the suffix together. The model-swap gate prints the split: the suffix adds 4 tokens to each route call, and the answer calls change it by -204 tokens per message, since the messages routed to fallback make no such call.

**Working rule:** Read a release's prompt version with the prompt's differences beside it. Say beside any model comparison whether the prompt changed as well.

## The CI gate {#the-ci-gate}

A comparison gives numbers, and a gate turns them into a decision. A regression gate is a check in CI that stops a release from merging when a number read from its traces has moved past its threshold, judged against its paired interval. A regression is a release's change that makes a trace-derived number worse than its limit allows, judged by the end of its interval nearest the limit. The limits are set below. The interval is the one [chapter 7](#tail-percentiles-with-intervals) builds for a number measured on a day's messages. [Evaluating LLM Applications](https://rollingedition.com/concepts/llm-evaluation/gate) shares that rule, a rule that stops a change from merging, and [Business Intelligence with Agents'](https://rollingedition.com/concepts/llm-evaluation/regression-gate) regression gate uses a different one. Evaluating LLM Applications also describes a [naive gate](https://rollingedition.com/concepts/llm-evaluation/naive-gate), which fails on the point estimate alone. This gate waits for the interval.

The gate has one job here: catch the prompt change without flagging the baseline's second day, with the same rules for both. The five rules are fixed in code, and the gate prints every line it judges. Message time, input tokens and cost may each rise by a tenth of the baseline's mean on the same messages, which is why the limits differ on 60 and 200 messages. The error rate may rise by two points, and route accuracy may fall by five points. Each rule reads the interval of the release's difference, and a rule flags a release when the end of that interval nearest the limit lies past the limit. For a rise, that is the lower end. For a fall in route accuracy, it is the upper end. So a flag means the release is worse than its limit, beyond its 95% interval. A release whose interval merely reaches past the limit is not flagged.

We set these limits, and the chapter applies them as printed rather than tuning them to these recordings. The relative limits scale with the baseline's mean. The error rate's baseline is zero, so a relative limit would leave it no room, and its limit is two points. Route accuracy is a share of messages, so it moves in points, and its limit is five. The rules read traces, never an answer's text. For route accuracy, the gate reads the route the reply names and checks it against the scenario table.

The error rule uses the definition [chapter 8](#how-a-span-records-failure) gives. A reply cut at its token cap, or a route reply that names no route, is not an error under that definition. Chapter 8 counts those as quality findings, and route accuracy already counts the second.

The gate has to pass a normal day, or a team would stop reading it. Gating baseline day 2 against day 1 shows whether it does, with the same rules and limits.

Example `gate-on-baseline-day-two` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""Gate baseline day 2 against baseline day 1, both on release r0, with the same rules and limits as the prompt release's gate. The two days share no message, so each interval resamples each day on its own. The day is a normal day with no incident, and the gate must pass it, or a gate that flags every normal day would never reach CI."""
from lib.gate import judge, measured
from lib.report import fmt_int

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
before = measured("baseline-day-1", DAY, MODEL)            # r0 on all 200 messages of baseline day 1
after = measured("baseline-day-2", "2026-12-10", MODEL)    # r0 again, on 80 other messages, two days later
print("messages, baseline day 1:", fmt_int(len(before)))
print("messages, baseline day 2:", fmt_int(len(after)))
print("messages shared by the two days:", fmt_int(len(set(before) & set(after))))   # no message is in both
verdict, flagged = judge("baseline day 2 against day 1", list(before.values()), list(after.values()), paired=False)
assert verdict == "pass" and flagged == []     # the same release on a normal day must pass the same gate
```

Output:

```text
messages, baseline day 1: 200
messages, baseline day 2: 80
messages shared by the two days: 0
baseline day 2 against day 1, message time, mean: 168.8 ms, limit 801.9 ms (95% interval -1,599.0 ms to 1,895.0 ms)
baseline day 2 against day 1, message time, mean, flagged: no
baseline day 2 against day 1, input tokens per message, mean: -5, limit 52 (95% interval -108 to 99)
baseline day 2 against day 1, input tokens per message, mean, flagged: no
baseline day 2 against day 1, cost per message, mean, per 1,000 messages: $0.000545, limit $0.003781 (95% interval -$0.007950 to $0.008940)
baseline day 2 against day 1, cost per message, mean, flagged: no
baseline day 2 against day 1, error rate: +0.0%, limit +2.0% (95% interval +0.0% to +0.0%)
baseline day 2 against day 1, error rate, flagged: no
baseline day 2 against day 1, route accuracy: -3.3%, limit -5.0% (95% interval -14.5% to +7.8%)
baseline day 2 against day 1, route accuracy, flagged: no
baseline day 2 against day 1, gate verdict: pass
```

The two days share 0 messages, so the intervals are unpaired. Message time rises by 168.8 ms, limit 801.9 ms (95% interval -1,599.0 ms to 1,895.0 ms), and the lower end of that interval is far below the limit, so the rule does not flag. The other rules pass as well, and the verdict is pass.

Paired, the prompt change should fail on tokens; unpaired, the same 60 messages should pass. Both judgements run on the same messages, and the run asserts both results.

Example `gate-on-prompt-release` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""Gate the prompt-change release r1 against r0 on the same 60 messages, with the gate's own rules. The gate reads the traces only: message time, input tokens, cost, errors and route accuracy. A rule flags a release when the end of its interval nearest the limit lies past the limit. The prompt change adds tokens to every route call, and the gate catches it only because the messages are paired: the same 60 messages judged as unrelated samples pass."""
from lib.gate import judge, measured, paired, tokens_by_step
from lib.report import fmt_int
from lib.stats import mean_of, paired_interval, paired_mean_difference

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
before = measured("baseline-day-1", DAY, MODEL)
after = measured("release-prompt-v2", DAY, MODEL)
ids, base, release = paired(before, after)      # the paired 60: r0 has every one of them
print("messages (paired):", fmt_int(len(ids)))
verdict, flagged = judge("r1 against r0", base, release, paired=True)
assert verdict == "fail" and flagged == ["input tokens per message, mean"]   # the prompt change, and only its tokens
assert "message time, mean" not in flagged   # its message time is not flagged: the interval's end stays under the limit
# The same 60 messages, judged as if they were two unrelated samples: the same release passes.
unpaired, unpaired_flagged = judge("r1 against r0, unpaired", base, release, paired=False)
assert unpaired == "pass" and unpaired_flagged == []   # without the pairing, the gate misses the change it must catch
steps0, steps1 = tokens_by_step("baseline-day-1", DAY, MODEL), tokens_by_step("release-prompt-v2", DAY, MODEL)
def change(steps, step):
    """r1 minus r0 in input tokens, for each message, in one step's calls; zero where the message made no such call."""
    return {i: steps[i].get(step, {"input": 0})["input"] - steps0[i].get(step, {"input": 0})["input"] for i in ids}
route_in, answer_in = change(steps1, "route"), change(steps1, "answer")
changed = {i for i in ids if before[i]["route"] != after[i]["route"]}
assert len(set(route_in.values())) == 1      # the six examples add the same tokens to every route call
assert all(answer_in[i] == 0 for i in ids if i not in changed)   # only a message whose route changed gets another answer call
route_share, answer_share = mean_of(list(route_in.values())), mean_of(list(answer_in.values()))
assert route_share + answer_share == mean_of([m["tokens"] for m in release]) - mean_of([m["tokens"] for m in base])
print("r1 against r0, route call input tokens per call, mean difference:", fmt_int(round(route_share)))
print("r1 against r0, messages whose route changed:", fmt_int(len(changed)))
print("r1 against r0, input tokens per message, answer calls' share:", fmt_int(round(answer_share)))
tokens_base, tokens_release = [m["tokens"] for m in base], [m["tokens"] for m in release]
_, (token_low, _) = paired_interval(tokens_base, tokens_release, paired_mean_difference)
print("r1 against r0, input tokens per message, low end of interval:", fmt_int(round(token_low)))
print("r1 against r0, input tokens per message, limit:", fmt_int(round(mean_of(tokens_base) / 10)))
```

Output:

```text
messages (paired): 60
r1 against r0, message time, mean: 726.1 ms, limit 737.3 ms (95% interval 79.8 ms to 1,333.3 ms)
r1 against r0, message time, mean, flagged: no
r1 against r0, input tokens per message, mean: 90, limit 49 (95% interval 70 to 115)
r1 against r0, input tokens per message, mean, flagged: yes
r1 against r0, cost per message, mean, per 1,000 messages: $0.006281, limit $0.003453 (95% interval $0.003197 to $0.009519)
r1 against r0, cost per message, mean, flagged: no
r1 against r0, error rate: +0.0%, limit +2.0% (95% interval +0.0% to +0.0%)
r1 against r0, error rate, flagged: no
r1 against r0, route accuracy: +3.3%, limit -5.0% (95% interval +0.0% to +8.3%)
r1 against r0, route accuracy, flagged: no
r1 against r0, gate verdict: fail
r1 against r0, unpaired, message time, mean: 726.1 ms, limit 737.3 ms (95% interval -1,627.6 ms to 3,141.5 ms)
r1 against r0, unpaired, message time, mean, flagged: no
r1 against r0, unpaired, input tokens per message, mean: 90, limit 49 (95% interval -45 to 231)
r1 against r0, unpaired, input tokens per message, mean, flagged: no
r1 against r0, unpaired, cost per message, mean, per 1,000 messages: $0.006281, limit $0.003453 (95% interval -$0.005244 to $0.018074)
r1 against r0, unpaired, cost per message, mean, flagged: no
r1 against r0, unpaired, error rate: +0.0%, limit +2.0% (95% interval +0.0% to +0.0%)
r1 against r0, unpaired, error rate, flagged: no
r1 against r0, unpaired, route accuracy: +3.3%, limit -5.0% (95% interval -10.0% to +16.7%)
r1 against r0, unpaired, route accuracy, flagged: no
r1 against r0, unpaired, gate verdict: pass
r1 against r0, route call input tokens per call, mean difference: 86
r1 against r0, messages whose route changed: 2
r1 against r0, input tokens per message, answer calls' share: 4
r1 against r0, input tokens per message, low end of interval: 70
r1 against r0, input tokens per message, limit: 49
```

The token rise clears its limit even at the low end of its interval: 70 tokens against a limit of 49. The rule flags, and the release's verdict is fail. The flag belongs to the input tokens alone.

Message time rises by 726.1 ms, limit 737.3 ms (95% interval 79.8 ms to 1,333.3 ms), which is under its limit, and the nearer end of its interval is under it too. The upper end runs past the limit, but the rule reads the end nearer the limit, so the rule does not flag. Cost rises by $0.006281, limit $0.003453 (95% interval $0.003197 to $0.009519) per 1,000 messages. Its lower end is under its limit, so cost is not flagged either, though tokens rise on the same messages.

Judged as unrelated samples, the same 60 messages pass. The token rise is still 90, limit 49 (95% interval -45 to 231), but its interval runs from below zero to above the limit, its nearer end is under the limit, and the verdict is pass. The interval widths in [the paired comparison](#paired-comparison-on-messages) are why. The shared messages hold the interval narrow enough to see the change through, and the unpaired interval is too wide to see it. The gate catches the change only because the messages are paired.

**Working rule:** Pair the releases whenever their messages overlap, and judge each rule on the end of its interval nearest the limit. Print every line, so a flag can be checked by eye.

## Gating the other changes {#gating-the-other-changes}

Gating the model swap on all 200 messages shows a different failure. Its amounts fall, which the rules pass, and its routes fall, which one rule catches.

Example `gate-on-model-swap` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""Gate release r2, the 0.6B model swap, against r0 on the same 200 messages, with the same rules and limits. Its route accuracy falls, and the gate flags it. Its message time, input tokens and cost fall too, and the rules for those amounts pass a fall. The fall comes from the answer calls: r2 routes more messages to the fallback reply, which makes no answer call. The suffix adds a few tokens to every route call. The gate reads each message's route reply against the route its scenario gives, never an answer."""
from lib.gate import judge, measured, paired, tokens_by_step, to_decimal
from lib.report import fmt_int, fmt_ms, fmt_usd
from lib.stats import mean_of

DAY, MODEL, SWAP = "2026-12-08", "Qwen3-4B-Instruct-2507", "Qwen3-0.6B"
before = measured("baseline-day-1", DAY, MODEL)
after = measured("release-model-swap", DAY, SWAP)   # r2: the 0.6B model, on all 200 messages
ids, base, release = paired(before, after)
verdict, flagged = judge("r2 against r0", base, release, paired=True)
print("messages (paired):", fmt_int(len(ids)))
assert verdict == "fail" and flagged == ["route accuracy"]   # the model swap is caught on route accuracy alone

steps0, steps2 = tokens_by_step("baseline-day-1", DAY, MODEL), tokens_by_step("release-model-swap", DAY, SWAP)
def change(step, field):
    """r2 minus r0 for each message, in one step's calls; zero where the message made no such call."""
    return [steps2[i].get(step, {field: 0})[field] - steps0[i].get(step, {field: 0})[field] for i in ids]
answered0 = {i for i in ids if "answer" in steps0[i]}
answered2 = {i for i in ids if "answer" in steps2[i]}
print("messages answered by r0 and not by r2:", fmt_int(len(answered0 - answered2)))
print("messages answered by r2 and not by r0:", fmt_int(len(answered2 - answered0)))
route_in, answer_in = change("route", "input"), change("answer", "input")
assert len(set(route_in)) == 1                      # every route call grew by the same amount: the suffix's tokens
route_share, answer_share = mean_of(route_in), mean_of(answer_in)
assert route_share + answer_share == mean_of([m["tokens"] for m in release]) - mean_of([m["tokens"] for m in base])
print("r2 against r0, route call input tokens per call, mean difference:", fmt_int(round(route_share)))
print("r2 against r0, route call output tokens per call, mean difference:",
      fmt_int(round(mean_of(change("route", "output")))))
print("r2 against r0, input tokens per message, route calls' share:", fmt_int(round(route_share)))
print("r2 against r0, input tokens per message, answer calls' share:", fmt_int(round(answer_share)))
print("r2 against r0, message time, answer calls' share:", fmt_ms(round(mean_of(change("answer", "time")))))
print("r2 against r0, cost per 1,000 messages, answer calls' share:",
      fmt_usd(to_decimal(mean_of(change("answer", "cost")) * 1000)))
replies = [text for i in ids for step in steps2[i].values() for text in step["replies"]]
empty = [text for text in replies if text.startswith("<think>\n\n</think>")]
assert all(text.startswith("<think>") for text in replies)   # the 0.6B still writes its block under /no_think
print("r2, model replies:", fmt_int(len(replies)))
print("r2, model replies with an empty <think> block:", fmt_int(len(empty)))
print("r2, model replies with text in their <think> block:", fmt_int(len(replies) - len(empty)))
```

Output:

```text
r2 against r0, message time, mean: -6,750.9 ms, limit 801.9 ms (95% interval -7,599.5 ms to -5,921.4 ms)
r2 against r0, message time, mean, flagged: no
r2 against r0, input tokens per message, mean: -200, limit 52 (95% interval -258 to -148)
r2 against r0, input tokens per message, mean, flagged: no
r2 against r0, cost per message, mean, per 1,000 messages: -$0.033156, limit $0.003781 (95% interval -$0.037326 to -$0.029012)
r2 against r0, cost per message, mean, flagged: no
r2 against r0, error rate: +0.0%, limit +2.0% (95% interval +0.0% to +0.0%)
r2 against r0, error rate, flagged: no
r2 against r0, route accuracy: -21.0%, limit -5.0% (95% interval -28.0% to -14.5%)
r2 against r0, route accuracy, flagged: yes
r2 against r0, gate verdict: fail
messages (paired): 200
messages answered by r0 and not by r2: 59
messages answered by r2 and not by r0: 4
r2 against r0, route call input tokens per call, mean difference: 4
r2 against r0, route call output tokens per call, mean difference: 4
r2 against r0, input tokens per message, route calls' share: 4
r2 against r0, input tokens per message, answer calls' share: -204
r2 against r0, message time, answer calls' share: -5,706.8 ms
r2 against r0, cost per 1,000 messages, answer calls' share: -$0.027870
r2, model replies: 257
r2, model replies with an empty <think> block: 256
r2, model replies with text in their <think> block: 1
```

The amounts fall because the model swap leaves 59 messages without the answer call the baseline made. Those answer calls change the count by -204 tokens per message. The suffix adds 4 tokens to each route call, and the two together make the fall. The rules for those amounts flag a rise, so a fall passes them, and the gate's pass on them follows from its route failure, not from a cheaper model.

Route accuracy changes by -21.0%, limit -5.0% (95% interval -28.0% to -14.5%), and the upper end of its interval is past the limit, so that rule flags it and the release's verdict is fail. Choosing a smaller model is the subject of [Small Open Models](https://rollingedition.com/small-open-models/s/where-the-small-model-still-loses), which this chapter does not take up. The release is the 0.6B with `/no_think`, as [prompt versions](#prompt-versions) says, so the route change belongs to the model and the suffix together. The error rate does not move: +0.0%, limit +2.0% (95% interval +0.0% to +0.0%), which matches the other releases in this chapter.

The route check counts a route as wrong when it differs from the scenario table, and it does not read the answer that follows. A right route with a wrong answer passes this rule.

The top-8 release and the cache-off release get the same gate on the same 60 paired messages, and the example runs both.

Example `gate-on-retrieval-and-cache` (Python 3.13.16 · bm25s 0.3.16 · mcp 2.3.0 · numpy 2.5.5 · opentelemetry-api 1.45.2 · opentelemetry-exporter-http-transport 0.66b2 · opentelemetry-exporter-otlp-common 0.66b2 · opentelemetry-exporter-otlp-proto-common 1.45.2 · opentelemetry-exporter-otlp-proto-http 1.45.2 · opentelemetry-instrumentation 0.66b2 · opentelemetry-instrumentation-genai-openai 1.3b0 · opentelemetry-proto 1.45.2 · opentelemetry-sdk 1.45.2 · opentelemetry-semantic-conventions 0.66b2 · opentelemetry-util-genai 1.3b0 · pydantic 2.14.4), passing in Edition 2026.11.3:

```python
"""Gate the top-8 release r3 and the cache-off release r4 against r0, each on the same 60 paired messages, with the same rules and limits as the other gates. The top-8 release retrieves more articles, so its input tokens rise, and its time and cost rise with them. The cache-off release sends the same prompts, so its input total does not move, but its cost and time rise. The gate flags r3 on all three amounts and r4 on time and cost alone."""
from lib.gate import judge, measured, paired
from lib.report import fmt_int

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
before = measured("baseline-day-1", DAY, MODEL)
verdicts = {}
for name, folder in (("r3", "release-top-8"), ("r4", "release-cache-off")):
    ids, base, release = paired(before, measured(folder, DAY, MODEL))
    print(f"{name} against r0, messages (paired):", fmt_int(len(ids)))
    verdicts[name] = judge(f"{name} against r0", base, release, paired=True)
assert verdicts["r3"] == ("fail", ["message time, mean", "input tokens per message, mean", "cost per message, mean"])
assert verdicts["r4"] == ("fail", ["message time, mean", "cost per message, mean"])   # its input total does not move
```

Output:

```text
r3 against r0, messages (paired): 60
r3 against r0, message time, mean: 2,222.5 ms, limit 737.3 ms (95% interval 1,099.6 ms to 3,462.8 ms)
r3 against r0, message time, mean, flagged: yes
r3 against r0, input tokens per message, mean: 115, limit 49 (95% interval 60 to 179)
r3 against r0, input tokens per message, mean, flagged: yes
r3 against r0, cost per message, mean, per 1,000 messages: $0.012542, limit $0.003453 (95% interval $0.006844 to $0.018909)
r3 against r0, cost per message, mean, flagged: yes
r3 against r0, error rate: +0.0%, limit +2.0% (95% interval +0.0% to +0.0%)
r3 against r0, error rate, flagged: no
r3 against r0, route accuracy: +0.0%, limit -5.0% (95% interval +0.0% to +0.0%)
r3 against r0, route accuracy, flagged: no
r3 against r0, gate verdict: fail
r4 against r0, messages (paired): 60
r4 against r0, message time, mean: 2,881.5 ms, limit 737.3 ms (95% interval 2,209.1 ms to 3,677.3 ms)
r4 against r0, message time, mean, flagged: yes
r4 against r0, input tokens per message, mean: 0, limit 49 (95% interval 0 to 0)
r4 against r0, input tokens per message, mean, flagged: no
r4 against r0, cost per message, mean, per 1,000 messages: $0.023233, limit $0.003453 (95% interval $0.018860 to $0.028303)
r4 against r0, cost per message, mean, flagged: yes
r4 against r0, error rate: +0.0%, limit +2.0% (95% interval +0.0% to +0.0%)
r4 against r0, error rate, flagged: no
r4 against r0, route accuracy: +0.0%, limit -5.0% (95% interval +0.0% to +0.0%)
r4 against r0, route accuracy, flagged: no
r4 against r0, gate verdict: fail
```

Both releases fail. The top-8 release is caught on all three amounts, and its input tokens rise by 115, limit 49 (95% interval 60 to 179) per message. The cache-off release is caught on time and cost alone, because its input stays the same, and its cost rises by $0.023233, limit $0.003453 (95% interval $0.018860 to $0.028303) per 1,000 messages.

| Comparison | Messages | Verdict | Rule flagged |
| --- | --- | --- | --- |
| Baseline day 2 against day 1, unpaired | 80 | pass | None |
| Prompt change against baseline, paired | 60 | fail | Input tokens |
| Prompt change against baseline, unpaired | 60 | pass | None |
| Model swap against baseline, paired | 200 | fail | Route accuracy |
| Top-8 release against baseline, paired | 60 | fail | Message time, input tokens and cost |
| Cache-off release against baseline, paired | 60 | fail | Message time and cost |

Each of the four changes moved something the gate reads, and the gate flags each one: the prompt change through its tokens, the model swap through its routes, the top-8 release on all three amounts, and the cache-off release on time and cost. The normal day passes, and no release moved the error rate. That answers the question at the top of the chapter, with the rules the gate was given.

**Working rule:** Check each flagged rule against the amount it reads, and ask what in the release moved that amount.

## What the gate misses {#what-the-gate-misses}

A gate passes whatever it does not read. The five rules read message time, input tokens, cost, the error rate and route accuracy, and a release can change other things the gate never sees. Four of these matter in this chapter.

The first is quality. The gate reads traces, not answers. A release can route every message correctly, keep its tokens and its time, and still write worse replies, and this gate passes it. Judging a reply is a different job. Evaluating LLM Applications gives it a [code check](https://rollingedition.com/concepts/llm-evaluation/code-check), which reads a reply's text against the item's own reference answer. A regression in quality needs a check of that kind, run on the same messages with the same paired comparison, and this chapter does not run one. The book judges no answer's quality.

The second is the tail. The 95th percentile is printed and not gated. On the 60 paired messages the prompt change's p95 difference points down while its mean points up, and the p95's interval is much wider than the mean's, as [the paired comparison](#paired-comparison-on-messages) shows. The gate reads the mean because, on 60 messages, the mean's interval is the narrower of the two. A release whose tail grew could still pass this gate on its mean.

The third is the interval itself. A rule flags only when the end of the interval nearest the limit passes it, so a real rise can pass. The prompt change's message time is the example. Its mean sits under the limit, and its interval's upper end reaches past it. The gate cannot say whether that release moved time past its limit. It can only decline to flag it.

The fourth is the record. In production, two releases rarely meet the same messages, and comparing them on live traffic is the subject of Evaluating LLM Applications' [variants on traffic](https://rollingedition.com/evaluating-llm-applications/s/variants-on-traffic). Every release in this chapter is a replay of calls the book recorded, and a replay answers only the calls its recording holds. A change that sends different calls cannot be gated here, because nothing answers them. Two more gaps follow from the same place. The error rate of the prompt change changes by +0.0% (95% interval +0.0% to +0.0%), and the baseline's own count of ERROR spans on its replay is 0, the status that [chapter 8](#how-a-span-records-failure) explains. The error rule is in the gate, but these recordings do not trip it, so the chapter cannot show it catch an error. The cost lines rest on the book's price table. Chapter 6 says that a self-hosted model is billed by its machine and not by its tokens, so the dollar figures compare token prices and do not compare bills.

**Working rule:** Name in each gate's report what it does not read, beside its verdict, so a pass is not taken for a clean release.

## The decisions this chapter made {#catch-a-regression-decisions}

- The prompt change is gated on its 60 paired messages, the model swap on all 200, the top-8 and cache-off releases on their 60, and the normal day on two unpaired days. The paired messages are the ones the baseline and the release share.
- We set the limits; the error rule is chapter 8's. The chapter applies them as printed and does not tune them to these recordings.
- The 95th percentile is printed and not gated, and the gate judges the mean of message time.
- The model swap's amounts are split into the suffix and the answers it lost, and its route accuracy is the model and the suffix together. Its cost rests on a price row with no source, and the chapter says so beside the cost line.
- The gate reads recorded calls, not live traffic, so every verdict here describes the recordings.

A difference means little without its interval, and the same messages are what keep the interval narrow enough to read. On 60 paired messages the prompt change's token difference is visible. The same 60 judged unpaired would hide it. That is why the chapter pairs every comparison it can, and why a reader who copies this gate should keep the pairing before the limits: the same limits, judged unpaired, pass the prompt change.

**Working rule:** Read a difference only with its interval beside it, on the same messages, and with the gate's blind spots printed beside its verdict.
