---
title: "Small Open Models"
chapter: "When a small model is the wrong choice"
chapter_id: when-a-small-model-is-the-wrong-choice
book: small-open-models
edition: 2026.11.1
verified: 2026-11-12
edition_code: 8J4E-MZEZ
canonical: https://rollingedition.com/small-open-models/when-a-small-model-is-the-wrong-choice
license: CC BY 4.0
attribution: "“When a small model is the wrong choice,” chapter 10 of Small Open Models, Edition 2026.11.1, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/when-a-small-model-is-the-wrong-choice. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# When a small model is the wrong choice

By the end of this chapter, you can say where a small router still loses to the stand-in and where a hosted model is expected to do better, count each option's monthly cost from inputs you state with their dates, find the volume at which a machine of your own becomes the cheaper route, and name the requirements that decide the question before any cost does.

The inbox sends each message to one of 77 teams. Over nine chapters this book built a classifier head for it and served the head with a route that hands off the unsure messages, along with the checks that version the router and send its hand-offs to a person. It also tried a distilled student and an int8 copy, and it measured both without shipping either. The stand-in is Qwen3-4B-Instruct-2507, a larger open model run locally in place of the hosted model the inbox uses today. A hosted model's scores will differ from the stand-in's, as [chapter 2](measure-the-routing-task#the-baseline-from-recorded-answers) says, and the chapters that measure the router score it against the stand-in. This chapter sets out where a small model is the wrong choice, the arithmetic for the bill and the machine, the reasons that have nothing to do with money, and a table to choose with.

## Where the small model still loses {#where-the-small-model-still-loses}

[Chapter 2](measure-the-routing-task#the-baseline-from-recorded-answers) set the stand-in's score as the baseline. This section puts the router beside it on the same messages: all 1001 messages of `test_1001`, the committed order that every later chapter scores from. The router is the classifier `banking77-lora-v1`, run live.

Example `router-on-test-1001` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""The router and the stand-in on all 1,001 messages of test_1001, the committed test order. The stand-in's answers
are recorded; the router runs live on 2 threads, and its first 200 messages are the test_200 sample."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
c = router_lib.compare_router_and_standin("test_1001")
n = c["messages"]
print(f"messages on test_1001: {n}")
print(f"router banking77-lora-v1 correct: {c['router_correct']}/{n} ({c['router_correct'] / n:.1%})")
print(f"stand-in correct: {c['standin_correct']}/{n} ({c['standin_correct'] / n:.1%})")
print(f"router handed off: {c['handed_off']}/{n} ({c['handed_off'] / n:.1%})")
print(f"right for the stand-in, wrong for the router: {c['standin_right_router_wrong']}/{n}")
print(f"of those, handed off by the router: {c['of_those_handed_off']}/{c['standin_right_router_wrong']}")
print(f"wrong for the router and sent as an answer: {c['router_wrong_sent']}/{n} ({c['router_wrong_sent'] / n:.1%})")
print(f"right for the router, wrong for the stand-in: {c['router_right_standin_wrong']}/{n}")
```

Output:

```text
messages on test_1001: 1001
router banking77-lora-v1 correct: 847/1001 (84.6%)
stand-in correct: 560/1001 (55.9%)
router handed off: 146/1001 (14.6%)
right for the stand-in, wrong for the router: 48/1001
of those, handed off by the router: 22/48
wrong for the router and sent as an answer: 76/1001 (7.6%)
right for the router, wrong for the stand-in: 335/1001
```

On all of them the router is right on 847/1001 (84.6%), and the stand-in on 560/1001 (55.9%), which is the baseline from chapter 2. The example also counts where the two disagree. The stand-in is right and the router wrong on 48/1001. Of those, the router hands off 22/48, so a person sees them, and the rest reach the caller as wrong answers. The router is right and the stand-in wrong on 335/1001.

The count that matters most for the inbox is the wrong answers the router sends to a caller: 76/1001 (7.6%). Those are messages it kept, because their confidence cleared the threshold. The hand-off is what holds the rest up. [Chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) chose that threshold on the dev split, and [chapter 9](version-watch-and-fall-back#fall-back-to-a-person) says where what the router hands off goes, which is a person.

Example `where-the-router-still-loses` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Where the router still loses: test_200 scored for the router and the stand-in.
The stand-in's answers are recorded; the router runs live on 2 threads."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402
torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
ADAPTER = router_lib.HERE / "data" / "recorded" / "lora-full"
threshold = json.loads((ADAPTER / "manifest.json").read_text())["handoff_threshold"]
answers = router_lib.standin_rows()
test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
standin_preds = [answers[i]["label"] for i in sample]
tokenizer, model = router_lib.load_classifier(ADAPTER / "adapter")
preds, confs = router_lib.classify(model, tokenizer, [test[i][0] for i in sample])
n = len(sample)
router_right = [p == g for p, g in zip(preds, golds)]
standin_right = [p == g for p, g in zip(standin_preds, golds)]
handed_off = [router_lib.handoff(c, threshold) for c in confs]
lost = [i for i in range(n) if standin_right[i] and not router_right[i]]
sent_wrong = sum(not r and not h for r, h in zip(router_right, handed_off))
print(f"messages on test_200: {n}")
print(f"router banking77-lora-v1 correct: {sum(router_right)}/{n} ({sum(router_right) / n:.1%})")
print(f"stand-in correct: {sum(standin_right)}/{n} ({sum(standin_right) / n:.1%})")
print(f"router threshold from manifest: {threshold:.2f}")
print(f"router handed off: {sum(handed_off)}/{n} ({sum(handed_off) / n:.1%})")
print(f"right for the stand-in, wrong for the router: {len(lost)}/{n} ({len(lost) / n:.1%})")
print(f"of those, handed off by the router: {sum(handed_off[i] for i in lost)}/{len(lost)}")
print(f"wrong for the router and sent as an answer: {sent_wrong}/{n} ({sent_wrong / n:.1%})")
print(f"right for the router, wrong for the stand-in: {sum(r and not s for r, s in zip(router_right, standin_right))}/{n}")
```

Output:

```text
messages on test_200: 200
router banking77-lora-v1 correct: 172/200 (86.0%)
stand-in correct: 109/200 (54.5%)
router threshold from manifest: 0.63
router handed off: 33/200 (16.5%)
right for the stand-in, wrong for the router: 6/200 (3.0%)
of those, handed off by the router: 3/6
wrong for the router and sent as an answer: 11/200 (5.5%)
right for the router, wrong for the stand-in: 69/200
```

The same counts on the first 200 messages, `test_200`, show which messages are lost. The example prints them. `test_200` is the first 200 of `test_1001`, a prefix the count script checks, so these counts are part of the full run and not a second sample. On those 200, the router is right on 172/200 (86.0%) and the stand-in on 109/200 (54.5%). The stand-in is right and the router wrong on 6/200 (3.0%), and 3/6 of those are handed off. The router sends 11/200 (5.5%) wrong answers on the 200. On the messages it keeps, its accuracy is 156/167 (93.4%), and 33/200 (16.5%) of all 200 go to a person. The gap between the router's accuracy on all messages and its accuracy on the messages it keeps is the hand-off doing its work.

The second place a small model loses is in prompting. [Chapter 4](prompt-and-constrain#measure-the-constrained-answers) asked the two smaller models for a team and forced each answer onto the team list. The constraint keeps every answer a team, and it does not make the answer right. On the same 200 messages of `test_200`, the three prompted variants were right on 9/200 (4.5%) (SmolLM2-135M-Instruct on the raw prompt), 11/200 (5.5%) (SmolLM2-135M-Instruct on the chat template) and 12/200 (6.0%) (SmolLM2-360M-Instruct on the raw prompt). The raw 135M model gave one answer more often than any other, card_arrival, 165/200, and that team is the gold team for 0/200 of the messages. A model that leans on one answer is a prior, not a router. [Chapter 4](prompt-and-constrain#why-the-prior-wins) shows why a prompt cannot make up for a model this size.

The stand-in fails in patterns too. Across all 1001 messages, its answers never name 4 of the 77 teams, so every message whose gold team is one of them goes to another team. Two confusions tie for its most common error. The clearest is the team `Refund_not_showing_up`, which is answered as `request_refund` on 13/13 of its messages. A pair like that is where a labelled set has to be read before any model is trusted on it, and [chapter 2](measure-the-routing-task#where-the-labels-collide) lists the pairs for every candidate.

A student copies its teacher, including the teacher's mistakes. [Chapter 6](distill-a-larger-model#when-the-teacher-is-wrong) distilled the stand-in's answers into a student. The teacher agreed with the gold label on 549/1000 (54.9%) of the training rows it labelled, so the student learned from labels that were wrong almost half the time. The student reached 69/200 (34.5%) on `test_200`. The same recipe trained on the gold labels of the same rows reached 77/200 (38.5%), and the teacher itself reached 109/200 (54.5%). The student is below both the teacher and the gold-label control, by a gap this sample cannot settle ([chapter 6](distill-a-larger-model#measure-agreement-not-only-accuracy)): the student is right where the control is wrong on 24/200, and the control where the student is wrong on 32/200.

The last place is a new team. A classifier head has one output for each team it was trained on, so a team without an output cannot be routed by it. Adding one means labelled messages for that team, a training run with the recipe from [chapter 5](fine-tune-with-lora), and the checks from [chapter 9](version-watch-and-fall-back#retrain-on-a-trigger) before the router sends a message to it. Whether a prompt change could add a new team is a question for the reader to test. This book did not measure a hosted model, and the table later in this chapter lists the question as open.

Put together, the small models here did three things: a prompted model leaned on one answer, a student copied its teacher's mistakes, and a team with no output could not be routed. None of these is a fault in the router's arithmetic. The stand-in did one thing more: it never named 4 teams and confused a pair. That is the stand-in's, not either option's. A larger threshold trades the router's 11/200 (5.5%) wrong answers on `test_200` for hand-offs ([chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev)), but it gives no team an output and fixes neither the teacher's errors nor the stand-in's. Each changes what a caller sees: a wrong team, a handed-off message, or no team at all.

**Working rule:** Before you route with a small model, run it and the hosted model on the same fixed sample. Count the messages each gets right that the other gets wrong, and the wrong answers that would reach a caller. Count a prompted model's answers against the team list, and count how often its most common answer is the gold team. Do not route a team that has no labelled messages of its own, and do not train a student on a teacher's labels before you have counted how often the teacher agrees with the gold labels.

## Count the bill and the machine {#count-the-bill-and-the-machine}

A hosted model is paid per message. Its monthly bill is the number of messages times what one message costs, and one message costs its input tokens at the input price plus its output tokens at the output price. A price list written per million tokens gives the price per token when divided by one million. A routing message is long on the input side, because the prompt and the message are both counted, and short on the output side, because the answer is one team name.

A machine is paid for whether it is busy or not. Its monthly bill is its hours times its hourly rate. The number of messages it can route in a month is its throughput, in messages per second, times the seconds in a month, times its utilisation, which is the share of the month it is busy. The machine's cost per message therefore depends on how many messages it routes, and the comparison needs a volume before it gives an answer.

The three formulas below hold for any pair of options.

```
hosted cost per month = messages × (input tokens × input price + output tokens × output price)
machine cost per month = hours × machine cost per hour
machine capacity per month = messages per second × seconds per month × utilisation
```

Each input needs a value, and each price needs a date and a source. The book quotes no hosted price, because it has none with both a source and a date that a reader could check. Read your provider's price page on the day you run the comparison, and write the price, its date and its address beside the number.

Input tokens also need a tokenizer. A hosted provider's count may differ from an open model's count of the same text, and this book did not measure one. The routing prompt is what a hosted model would receive for each message: the list of 77 team names and the message, as `router_prompt` builds it. The monthly example counts it with the tokenizer of SmolLM2-135M-Instruct, which gives 587 tokens per message, and the example labels that count as a stand-in for the provider's.

Throughput is the input that a recording has to supply, because it depends on the machine. The recording names its machine and saves the rates it measured. On a cloud machine with 4 vCPUs and 15 GiB of memory, at 4 threads, the stand-in routed 0.32 messages a second, one message per call. The router's classifier, `banking77-lora-v1`, in float32, routed 19.0 messages a second at one message per call, and 33.0 in batches of 16.

Only the one-per-call pair is like for like. The classifier in batches of 16 takes 16 messages in one forward pass, and the stand-in takes one message per call with its whole router prompt. So the batched ratio of 104.0 mixes model size with batching, and this chapter does not use it for the comparison. The comparison uses the one-per-call ratio of 60.8. Each copy got one timed pass over the 200 messages of `test_200`, after a warm-up of one message, with tokenization inside the timed span. The ratios come from unrounded rates, so they are not exactly the quotient of the printed rates.

The int8 copy ran at 29.0 messages a second in batches of 16, and its ratio over float32 is 0.9. On this machine, at this thread count, the int8 copy was no faster than float32. [Chapter 7](quantize-and-measure#measure-speed-in-a-recording) said that fewer bytes do not settle speed, and this recording measures the speed and saves the rates it measured. The two copies agreed on 200/200 predictions. The recording ran on four threads, and this book's serving budget is two vCPUs, so a reader's rates should come from a recording on their own machine at their own thread count.

Example `cost-ratio-from-recording` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""The throughput rates and ratios as recorded, and the machine they were measured on. Reads the recording only; no model runs."""

import json

import router_lib

folder = router_lib.HERE / "data" / "recorded" / "throughput"
ratios = json.loads((folder / "ratios.json").read_text())
rates = router_lib.recorded_rates()
manifest = json.loads((folder / "manifest.json").read_text())

print(f"machine: {manifest['machine'].split(', ')[0]}")
print(f"threads: {manifest['settings']['n_threads']}")
print(f"messages on test_200: {ratios['messages']}")
print(f"stand-in rate, one per call (messages a second): {rates['standin_one_message_per_call']}")
print(f"classifier fp32 rate, one per call (messages a second): {rates['classifier_fp32_one_message_per_call']}")
print(f"classifier fp32 rate, batches of 16 (messages a second): {rates['classifier_fp32_batches_of_16']}")
print(f"classifier int8 rate, batches of 16 (messages a second): {rates['classifier_int8_batches_of_16']}")
print(f"fp32 over stand-in, one per call, throughput ratio: {ratios['classifier_fp32_one_at_a_time_over_standin']}")
print(f"fp32 over stand-in, batches of 16, throughput ratio: {ratios['classifier_fp32_over_standin']}")
print(f"int8 over stand-in, batches of 16, throughput ratio: {ratios['classifier_int8_over_standin']}")
print(f"int8 over fp32, batches of 16, throughput ratio: {ratios['classifier_int8_over_fp32']}")
print(f"predictions agreeing, fp32 and int8: {ratios['agreement_fp32_int8']}/{ratios['messages']}")
```

Output:

```text
machine: a cloud machine with 4 vCPUs and 15 GiB of memory
threads: 4
messages on test_200: 200
stand-in rate, one per call (messages a second): 0.32
classifier fp32 rate, one per call (messages a second): 19.0
classifier fp32 rate, batches of 16 (messages a second): 33.0
classifier int8 rate, batches of 16 (messages a second): 29.0
fp32 over stand-in, one per call, throughput ratio: 60.8
fp32 over stand-in, batches of 16, throughput ratio: 104.0
int8 over stand-in, batches of 16, throughput ratio: 91.8
int8 over fp32, batches of 16, throughput ratio: 0.9
predictions agreeing, fp32 and int8: 200/200
```

The bill needs a rate for the router, and the recording gives one: the classifier at one message per call, timed as the stand-in was. The route handles one message per request, so the bill uses that rate. A reader replaces it with one taken on their own machine.

Example `monthly-bill-from-labelled-inputs` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""The monthly bill for a hosted model and for the router on one machine. Token counts are live. The prices, volume,
machine cost and utilisation are example values, not published prices; the router's rate is recorded on the machine."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
inputs = router_lib.bill_inputs_recorded()
test = router_lib.read_rows("test")
messages = [test[i][0] for i in router_lib.read_sample("test_200")]

input_tokens = router_lib.router_prompt_tokens(messages)
per_message = (input_tokens * inputs["price_per_million_input_tokens"]
               + inputs["output_tokens_per_message"] * inputs["price_per_million_output_tokens"]) / 1_000_000
hosted_month = inputs["messages_per_month"] * per_message

machine_month = inputs["machine_cost_per_hour"] * inputs["hours_per_month"]
capacity = inputs["router_messages_per_second"] * 3600 * inputs["hours_per_month"] * inputs["utilisation"]

print(f"example input, messages per month: {inputs['messages_per_month']}")
print(f"example input, price per million input tokens, USD: {inputs['price_per_million_input_tokens']}")
print(f"example input, price per million output tokens, USD: {inputs['price_per_million_output_tokens']}")
print(f"example input, output tokens per message: {inputs['output_tokens_per_message']}")
print(f"example input, machine cost per hour, USD: {inputs['machine_cost_per_hour']}")
print(f"example input, hours per month: {inputs['hours_per_month']}")
print(f"example input, utilisation: {inputs['utilisation']}")
print(f"recorded input, router messages per second, one per call: {inputs['router_messages_per_second']}")
print(f"input tokens per message, hosted prompt (counted with SmolLM2-135M-Instruct, a stand-in tokenizer): {input_tokens}")
print(f"example hosted price per message (example prices), USD: {per_message:.6f}")
print(f"example hosted bill per month (example prices), USD: {hosted_month:.2f}")
print(f"example machine bill per month (example cost per hour), USD: {machine_month:.2f}")
print(f"machine capacity per month (recorded rate, example utilisation): {capacity:.0f}")
print(f"example machine cost per message at capacity (example cost per hour), USD: {machine_month / capacity:.6f}")
print(f"example volume within machine capacity: {'yes' if inputs['messages_per_month'] <= capacity else 'no'}")
print(f"example values, cheaper route at the input volume: {'hosted' if hosted_month < machine_month else 'machine'}")
```

Output:

```text
example input, messages per month: 100000
example input, price per million input tokens, USD: 1.0
example input, price per million output tokens, USD: 4.0
example input, output tokens per message: 6
example input, machine cost per hour, USD: 0.4
example input, hours per month: 730
example input, utilisation: 0.5
recorded input, router messages per second, one per call: 19.0
input tokens per message, hosted prompt (counted with SmolLM2-135M-Instruct, a stand-in tokenizer): 587
example hosted price per message (example prices), USD: 0.000611
example hosted bill per month (example prices), USD: 61.10
example machine bill per month (example cost per hour), USD: 292.00
machine capacity per month (recorded rate, example utilisation): 24966000
example machine cost per message at capacity (example cost per hour), USD: 0.000012
example volume within machine capacity: yes
example values, cheaper route at the input volume: hosted
```

At these example inputs, 100000 messages a month cost 61.10 USD on the hosted side, at 0.000611 USD a message. The machine costs 292.00 USD a month whatever the volume. At the recorded rate and the example utilisation, it can route 24966000 messages a month, and at full capacity its cost per message is 0.000012 USD. The example volume sits far below that capacity, and at these example inputs the hosted bill is the lower of the two. The break-even section finds the volume where that reverses. The example cost per hour suits the recorded machine; a two-vCPU machine needs its own recorded rate.

What goes wrong in production is an input that stopped being true. Prices change, so a price read in one month is a fact about that month. The example's utilisation is an assumption about traffic that has not happened yet, and an inbox's volume moves with the products the bank sells and with the events that fill its queue. A machine that was idle half the month in one quarter can be busy all of the next. So count again each month, with the actual volume, the price on its date and the utilisation the machine measured. A comparison made once is a record of the month it was made in.

**Working rule:** Compare the two bills with your own inputs and your own machine. Write each price with its source and the date you read it. Count the input tokens with the tokenizer of the hosted model you compare with, and take the throughput from a recording on the machine you would buy. Where a value is an example, say so beside it, and replace it before you decide.

## Keep the data inside the building {#keep-the-data-inside-the-building}

This section is not a cost comparison, and none of the numbers in this book decide it. Each message the inbox receives is a customer's text. When a hosted model answers it, the text leaves the bank's machines and goes to the provider's. For each message, a hosted call sends the message text and the list of 77 team names. The bank may not want that, for reasons of its own: its customers' data, its contracts, its rules for who may read what. Those reasons hold even when the hosted bill is lower.

The messages in this book are BANKING77's public messages, so the book's own runs show nothing about privacy. The requirement belongs to the bank, and only the bank can say whether it applies.

A small model that stays on the bank's machines meets the requirement by where it runs. The router, its weights and its logs stay under the bank's controls, and the versioning and file checks from [chapter 9](version-watch-and-fall-back#check-the-adapters-files-against-its-manifest) apply to every adapter the route loads. A derived copy, such as the int8 copy, has no manifest or pin of its own, so it needs both before it serves. Staying inside has a cost of its own, which is not a bill. The bank runs the machine, keeps it patched, and keeps the route's checks running, including the hand-off that stays in the route whatever else changes ([chapter 8](serve-the-router-on-a-cpu#one-route-that-returns-the-hand-off)).

A bill is a number that moves with the volume, the price and the date. A requirement does not move. So settle the requirement first, and then compare only the options that meet it. A small model that runs on the bank's machines is one such option. A larger open model that runs there is another. The stand-in is one, and on this machine it routed 0.32 messages a second one per call, against 19.0 for the classifier. That gap is its measured cost in throughput, 60.8 times over, and it is not a cost in money. If no option meets the requirement at the volume the inbox expects, the cost comparison has nothing to decide. A small model that meets the requirement still has to pass the accuracy and hand-off counts in the first section, and meeting the requirement does not excuse it from them.

**Working rule:** Settle the data requirement before the cost. Write it down as a requirement, with the people who own it, and do not count it as a saving or as a cost. When the messages must stay on the bank's machines, choose a model that runs there, and then count its accuracy and its hand-offs as in the first section of this chapter.

## Choose with a table {#choose-with-a-table}

The questions above are not all about cost, and most of them can be answered before anyone runs a recording. The table below sets the questions side by side. For each, it gives what a small router looks like, what a hosted model looks like, and what to count on your own inbox.

| Question | Small router | Hosted model | What to measure |
| --- | --- | --- | --- |
| Must the messages stay on the bank's machines? | Meets it: runs on the bank's machines | Doesn't: the text goes to the provider | Requirement, not a count: decide it first |
| Must every answer be a team? | Yes, by a head or by constrained decoding ([chapter 4](prompt-and-constrain)) | Only if a prompt and a check keep it to the list | Answers outside the team list, on a fixed sample |
| How often does the team list change? | A new team needs labelled messages and a training run ([chapter 9](version-watch-and-fall-back)) | Whether a prompt change is enough: a question to test, not measured here | The labelled messages and steps a new team takes to route |
| How many messages a month? | A fixed monthly bill, up to its capacity | A bill per message, growing with volume | The break-even count in the last section |
| How many labelled messages does each team have? | Enough to train on and to test each team ([chapter 2](measure-the-routing-task)) | Few or none, for a prompt | Labelled messages per team, counted on the training split |
| Does the task need open text or broad knowledge? | Limited to the team list, and its open-text answers failed in this book's first trial | A hosted model was not measured here: a question to test | Accuracy on the same fixed sample, with its count |

The table is a list of what to count, not a score. Read its rows in order: the requirement in the first row, then the team list, then the volume, because each one can end the question before the next is asked. In the last column, a cell that begins "Requirement" names a decision that comes before the counts. Every other cell names a count, taken on your own sample, with its denominator printed. The open-text row rests on the first trial in [chapter 4](prompt-and-constrain#why-free-text-fails): the 135M model's unconstrained answers were team names on 0/20 messages.

**Working rule:** Answer every row from your own inbox before you choose. Where a row asks for a count, take it on a fixed sample and print its denominator. Where a row names a requirement, let the requirement decide before the counts do, and write it into the decision as a requirement.

## Know the break-even {#know-the-break-even}

The break-even is the volume at which the two monthly bills are equal. Below it, the hosted model costs less at the inputs you set. Above it, the machine costs less, provided the volume is inside the machine's capacity. The machine's bill is paid whether it is busy or idle, so the break-even divides that bill by the hosted price per message:

break-even messages per month = machine bill per month ÷ hosted price per message

The formula does not subtract the machine's cost per message from the hosted price. The machine's cost per message at capacity is its fixed bill divided by its capacity, and that bill is already counted once in the numerator. Subtracting the same cost again would count the machine twice. The formula also holds only within capacity. Above it, one machine cannot carry the volume, and the count is made again for a second machine, with its own bill and its own capacity.

Example `break-even-from-recorded-ratio` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Break-even volume for the router on one machine against the hosted model. The prices and the machine's cost are
example values, as in the bill; the router's rate is recorded on the machine."""

import math
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
inputs = router_lib.bill_inputs_recorded()
test = router_lib.read_rows("test")
messages = [test[i][0] for i in router_lib.read_sample("test_200")]

input_tokens = router_lib.router_prompt_tokens(messages)
per_message = (input_tokens * inputs["price_per_million_input_tokens"]
               + inputs["output_tokens_per_message"] * inputs["price_per_million_output_tokens"]) / 1_000_000
machine_month = inputs["machine_cost_per_hour"] * inputs["hours_per_month"]
capacity = inputs["router_messages_per_second"] * 3600 * inputs["hours_per_month"] * inputs["utilisation"]

# The machine's bill is the same each month up to its capacity, so the hosted bill
# equals it at messages = machine bill / hosted price per message.
breakeven = math.ceil(machine_month / per_message)

print(f"input tokens per message, hosted prompt (counted with SmolLM2-135M-Instruct, a stand-in tokenizer): {input_tokens}")
print(f"example hosted price per message (example prices), USD: {per_message:.6f}")
print(f"example machine bill per month (example cost per hour), USD: {machine_month:.2f}")
print(f"machine capacity per month (recorded rate, example utilisation): {capacity:.0f}")
print(f"example break-even messages per month (example prices and cost per hour): {breakeven}")
print(f"break-even within machine capacity: {'yes' if breakeven <= capacity else 'no'}")
```

Output:

```text
input tokens per message, hosted prompt (counted with SmolLM2-135M-Instruct, a stand-in tokenizer): 587
example hosted price per message (example prices), USD: 0.000611
example machine bill per month (example cost per hour), USD: 292.00
machine capacity per month (recorded rate, example utilisation): 24966000
example break-even messages per month (example prices and cost per hour): 477906
break-even within machine capacity: yes
```

With the example values, the machine's bill of 292.00 USD breaks even at 477906 messages a month. The example checks that this count is inside the machine's capacity of 24966000 messages a month. That capacity uses the recorded one-per-call rate with the example utilisation. The break-even does not depend on the rate, only on the bill and the hosted price. The example's volume of 100000 messages a month sits well below the break-even, so at these example inputs the hosted bill is the lower one.

The break-even is a cost point, not a decision, and the inbox still decides the rest. It answers the cost question only after the requirement in [keep the data inside the building](#keep-the-data-inside-the-building) is settled. If the messages must stay inside, the question is which small model meets the accuracy and hand-off counts, and the break-even says what that machine costs against a hosted model at each volume. If the requirement lets a hosted model in, and the volume is below the break-even, the hosted model is the lower-cost route at these inputs. Above the break-even, the machine is the lower-cost route, provided the volume is inside its capacity and the router's wrong answers reaching a caller are numbers the support staff can accept. Hand-offs go to a person whatever the bill says: on the first 200 messages, the router hands off 33/200 (16.5%) of them.

**Working rule:** Compute the break-even with your own machine's bill and your own hosted price, with the price's date and source written beside it. Check that the volume you expect sits inside the capacity you measured on your machine before you read the break-even as a saving. Above that capacity, count a second machine and compute again. Read the break-even as a cost point, not a decision. The requirements and the accuracy counts from the earlier sections still decide whether the router goes live.

## The decisions this book made for the inbox {#the-decisions-this-book-made-for-the-inbox}

On the samples and machines the book names, these are the numbers that bear on the inbox. Each one carries the chapter that counts it.

- **Accuracy.** On all of `test_1001`, the router is right on 847/1001 (84.6%), and the stand-in on 560/1001 (55.9%) ([chapter 2](measure-the-routing-task#the-baseline-from-recorded-answers)). The router hands off the rest to a person, and 76/1001 (7.6%) wrong answers still reach a caller. Those are the count the support staff must accept before the router goes live.
- **Speed.** On the recorded machine, at one message per call, the classifier ran at 19.0 messages a second against the stand-in's 0.32, a ratio of 60.8 ([chapter 7](quantize-and-measure#measure-speed-in-a-recording) says how speed is measured). The int8 copy gave no speed reason to serve: its ratio over float32 in batches of 16 was 0.9. So the float32 adapter stays the one the route serves ([chapter 8](serve-the-router-on-a-cpu#one-route-that-returns-the-hand-off)).
- **Cost.** At the example inputs, 100000 messages a month cost 61.10 USD on the hosted side and 292.00 USD on a machine of your own. The break-even is 477906 messages a month, inside a capacity of 24966000. These are example prices and an example cost per hour, so replace them with your own, each with its date and source, before you read the break-even as a decision.
- **The data requirement.** If the messages must stay on the bank's machines, the hosted model is out, and the choice is among options that run there. Settle that first, as the section on keeping the data inside the building says.
- **Where the small model is not the choice.** A team with no labelled messages has no output in the head, and a new team needs the steps in [chapter 9](version-watch-and-fall-back#retrain-on-a-trigger). Open-text answers failed in this book's first trial ([chapter 4](prompt-and-constrain#why-free-text-fails)). A hosted model is expected to do better on open text and broad knowledge, and this book did not measure one. And at a volume below the break-even, where a hosted model is allowed, the hosted model is the cheaper route at these inputs.

**The verdict for the inbox.** If the messages must stay on the bank's machines, and every team has labelled messages, a small router on the bank's own machine is the choice, provided the volume is above the break-even at the bank's own prices and inside the machine's capacity. The hand-off to a person stays in the route whatever the bill says. Count the wrong answers that reach a caller on the bank's own sample before it goes live.

**Working rule:** Write this list again from your own inbox, with your own numbers, before you choose. A verdict that does not come from your own counts, dates and requirements is not the book's verdict for your inbox.
