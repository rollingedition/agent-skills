---
title: "Small Open Models"
chapter: "Choose a base model by counting what one message costs"
chapter_id: choose-a-base-model
book: small-open-models
edition: 2026.11.9
verified: 2026-11-20
edition_code: ND0S-78AT
canonical: https://rollingedition.com/small-open-models/choose-a-base-model
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Choose a base model by counting what one message costs,” chapter 3 of Small Open Models, Edition 2026.11.9, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/choose-a-base-model. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Choose a base model by counting what one message costs

By the end of this chapter, you can name the two base models this book keeps, load each one at its pinned revision, and count what one routing message costs in tokens and parameters before you commit to a model.

Every message in the bank's support inbox costs something to route: a model reads it and picks its team, and the model the router starts from sets what that costs. The router is the whole system that [chapter 1](route-a-message) builds, and this chapter chooses the small open model under it. [Chapter 2](measure-the-routing-task#dev-test-and-fixed-samples) fixed the samples that the router is measured on. This chapter chooses by cost first, because the bank can count what a message costs before it builds anything around the model.

## Which candidates we keep {#the-candidates-and-what-we-keep}

A base model is a model already pretrained on a large amount of text, which you adapt to one job. Every later chapter builds on this choice, through the prompt, the training, the distillation and the serving, so it is worth making on evidence. There are many open models, so the book narrows the field with two questions: can the model run on the hardware the bank has, and can the bank use its licence?

The licence comes first in practice. It decides what the bank may do with the model in its own system, and a model the bank may not run is not a candidate, whatever its size. The book records each model's licence beside its pin, so a reader can see the same record the book used.

The first candidate is SmolLM2, a family of models published on Hugging Face. The [model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/tree/12fd25f77366fa6b3b4b768ec3050bf629380bac) for the 135M model, at the commit this book pins, gives the family's three sizes in one sentence: 135M, 360M and 1.7B parameters. The same card lists the licence as `license: apache-2.0`, which the book's pins record for both models it keeps. The card also gives the 135M model's training data as 2 trillion tokens. Those figures come from the card for the 135M model only.

The book keeps two of the three sizes. The list below names them, and the table after it sets all three side by side, with the licence each pin records.

- SmolLM2-135M-Instruct is the core model. The rest of the book trains and serves it.
- SmolLM2-360M-Instruct is a comparison. The book loads it, counts its parameters and layers, and uses it beside the core model in this chapter and in [chapter 4](prompt-and-constrain). The book does not train it.

| Model | Role in this book | Pinned in `models.toml` | Licence |
| --- | --- | --- | --- |
| SmolLM2-135M-Instruct | Core model, trained and served by the rest of the book | Yes | Apache-2.0 |
| SmolLM2-360M-Instruct | Comparison beside the core model | Yes | Apache-2.0 |
| SmolLM2 1.7B | Not pinned and not run | No | None recorded |

The 1.7B model is not pinned in the book's `models.toml` file, and the book does not run it. The book's examples set two CPU threads, so each candidate has to load and run within that budget. For a bank with that budget, we recommend the 135M model as the starting point, for the reasons in the rest of this chapter.

The book's reference point is a different model. In the case, a hosted model routes the bank's messages today, and this book never calls one. Its stand-in is Qwen3-4B-Instruct-2507, a larger open model whose answers to the test messages are recorded once and then read offline. The stand-in is the baseline the candidates are measured against, not a candidate for the router. [Chapter 1](route-a-message#ask-a-model-for-one-team) introduces it.

**Working rule:** Start with the smallest model in the family that passes the measures you set on the dev split, the training messages held back for choosing ([chapter 2](measure-the-routing-task#dev-test-and-fixed-samples)). Move up one size only when the smaller model misses a measure, and only after you have measured the larger model on the same samples. This is a rule of thumb. It holds until your own measurements say otherwise.

## Load each model at its pinned revision {#load-each-model-at-its-pinned-revision}

The [previous section](#the-candidates-and-what-we-keep) named two models. A name alone does not say which version of the model's files you load, because a model is stored in a repository of commits, and a branch such as `main` can move to a new commit. A revision pinned by a full commit hash names one snapshot of the files, and the pins file, `examples/models.toml`, records the SHA-256 of every file in that snapshot, which the runtime checks. The shared loader passes the commit to the transformers library, which the book pins at 5.23.0, and the loader looks up the commit for each model in that file.

For each model, the file holds the repository, the commit, the licence and the SHA-256 of every file the model needs. Its header says the runtime fetches each model once, checks it file by file, and then reads it offline. The file is generated by `re-check models --pin`, and its header says not to edit it by hand. So a reader who changes a pin runs that command rather than typing a new commit into the file. A model without a pin has no commit to look up, so the shared loader does not load it.

The examples set the library's offline flags before they import it, so a load reads only what the runtime already holds. The loader also sets the weights to float32 and runs attention in the library's plain eager form. The book's determinism rules fix both, so every run of an example gives the same numbers. If an offline load fails on a reader's machine, compare the files on disk with the list in the pins file before you change anything else.

The example also watches the pins from the output side. It prints each model's parameter count, so a change in a model's size shows up as a changed line in the book's own output, and every number the chapter quotes from that line changes with it. A reader who sees a different count knows which pin to compare first. A change of commit that keeps the size the same does not show there, so the pin itself stays the record.

One example loads both kept models from the files the runtime fetched and checked against the pins, with no network, and prints the book's first size counts.

Example `load-both-models-offline` (Python 3.12.15 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.9:

```python
"""Load the 135M and 360M SmolLM2 models at their pins, offline, and print each one's parameter count and layer count. The chapter's size claims rest on both lines; the parameter line is rounded to whole millions."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

# Seeds, deterministic algorithms and float32, set before either model loads.
router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"
MEDIUM = "HuggingFaceTB/SmolLM2-360M-Instruct"


def size(model):
    """Return (parameter count in millions, rounded to a whole number) and the layer count."""
    # parameters() yields a shared tensor once, so the tied embedding and output head count once.
    total = sum(p.numel() for p in model.parameters())
    return round(total / 1e6), model.config.num_hidden_layers


# load_model returns (tokenizer, model). This example needs only the models.
_, small = router_lib.load_model(SMALL)
_, medium = router_lib.load_model(MEDIUM)

small_millions, small_layers = size(small)
medium_millions, medium_layers = size(medium)

print(f"parameters, millions, rounded: {small_millions} and {medium_millions}")
print(f"layers: {small_layers} and {medium_layers}")
```

Output:

```text
parameters, millions, rounded: 135 and 362
layers: 30 and 32
```

A parameter is one of the numbers the model learns during training, and a layer is one of the stacked blocks that a token passes through. Parameters and layers are the only two sizes this chapter uses. The 360M is the larger of the two. The first output line gives each model's parameter count, rounded to whole millions: 135 and 362. The second line gives the layer counts, 30 and 32, in the same order. Speed is not among them, because a time depends on the machine. The `throughput` recording measures the classifier and its int8 copy against the stand-in on a named machine ([chapter 7](quantize-and-measure#measure-speed-in-a-recording) says how, and [chapter 10](when-a-small-model-is-the-wrong-choice#count-the-bill-and-the-machine) reports the ratios). The recording does not measure the 360M.

The counts come from loading the models here, not from their cards.

In production, the pin answers the first question you ask when a result changes, which is which files produced it. A change of model shows up as a diff in `models.toml`, where the commit and the file hashes sit. When a reader's copy of a model gives different output from the book's, compare the commit first.

**Working rule:** Pin every model by its commit in `examples/models.toml`, and load it with that commit and the offline flags. Record the parameter and layer counts next to the pin, so that a change in a model's size shows up as a changed output line and not as a surprise in a later chapter.

## Measure what one message costs {#measure-what-one-message-costs}

The [previous section](#load-each-model-at-its-pinned-revision) showed what the two models are. This section shows what one message costs them. A message's cost comes from what the model reads and what it writes. The router's prompt holds the 77 team names, the message and a request for the team, and the team list is the same in every call, so every message pays for it.

The prompt opens with the sentence "Route this customer message from an online bank to one support team." It asks for the team name only, lists the teams, then gives the message and ends with the word "Team:". Everything in that text is the same from one message to the next except the message itself, so the cost of a message is the fixed text plus the message's own length.

The tokenizer turns the prompt's text into tokens, the units a model reads. The count is in tokens rather than characters because a model reads tokens. Counting needs the tokenizer's rules but no weights, so the count is the first cost you can take before you choose a design. A classifier reads the message once and returns a score for each team. A generative model reads the prompt once and then writes its answer one token at a time, and each token it writes is one more pass through the network. The later chapters use both designs.

One example counts the forward passes, each one call of the network, for a single test message under each design. It uses the 135M model with no adapter. The classifier's head is untrained here, so only the pass count matters.

Example `count-forward-passes` (Python 3.12.15 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.23.0), passing in Edition 2026.11.9:

```python
"""Count the forward passes one test_40 message costs a classifier and a generative model, with the 135M model and no adapter. The point rests on the generative line: the model makes one pass for each token it writes, plus one for the end token."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from transformers import AutoModelForSequenceClassification  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"
texts = [text for text, _ in router_lib.read_rows("test")]
# read_sample gives row indices into the test split; index 0 is the sample's first message.
message = texts[router_lib.read_sample("test_40")[0]]


def count_passes(model, run):
    """Return how many forward calls the model makes while run() executes."""
    calls = []
    # A forward hook on the whole model fires once per call to its forward, so each generation step counts.
    handle = model.register_forward_hook(lambda module, args, output: calls.append(1))
    run()
    handle.remove()
    return len(calls)


tokenizer, causal = router_lib.load_model(SMALL)
# SmolLM2's tokenizer sets a pad token; this line keeps the example working with one that doesn't.
tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
# The trie holds each team name's tokens, so constrained_team can write only a team name, one token per pass, then the end token.
trie = router_lib.build_trie(tokenizer)
# The pinned commit from models.toml, and the float32 weights and eager attention that load_model also sets.
# The head is new, with one score per team (77), and untrained here; only the pass count matters.
classifier = AutoModelForSequenceClassification.from_pretrained(
    SMALL, revision=router_lib._pins()[SMALL], num_labels=len(router_lib.LABELS),
    dtype=torch.float32, attn_implementation="eager",
).eval()
# The classification head finds each message's last token through this id, so the config needs it too.
classifier.config.pad_token_id = tokenizer.pad_token_id

classifier_passes = count_passes(classifier, lambda: router_lib.classify(classifier, tokenizer, [message]))
answers = []
generative_passes = count_passes(causal, lambda: answers.append(router_lib.constrained_team(tokenizer, causal, trie, message)))
# answers[0] holds (label index, label text). The text is encoded with a leading space, as the model writes it after "Team:".
answer_tokens = len(tokenizer.encode(" " + answers[0][1], add_special_tokens=False))

print(f"classifier forward passes: {classifier_passes}")
print(f"generative forward passes: {generative_passes}")
print(f"answer tokens, end token not counted: {answer_tokens}")
```

Output:

```text
classifier forward passes: 1
generative forward passes: 8
answer tokens, end token not counted: 7
```

A generative model's cost grows with its answer, and a classifier's does not. For this message the classifier makes 1 pass. The generative model makes 8 passes, one for each of the 7 tokens in its answer and one for the end token.

A second example counts the router prompt's tokens for each of the 40 messages in the fixed test sample, using the 135M model's tokenizer. It runs no model.

Example `count-prompt-tokens` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.23.0), passing in Edition 2026.11.9:

```python
"""Count the router prompt's tokens for each message in test_40, with the 135M model's tokenizer. No model runs. The point rests on the mean line: a day's prompt cost is the mean, not the median, times the number of messages."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

# Only the tokenizer is read from the pinned commit; no weights load.
tokenizer = AutoTokenizer.from_pretrained(SMALL, revision=router_lib._pins()[SMALL])

texts = [text for text, _ in router_lib.read_rows("test")]
# read_sample gives row indices into the test split, in the order the sample lists them.
messages = [texts[i] for i in router_lib.read_sample("test_40")]

# router_prompt builds the same prompt the router sends. encode keeps its default, so any special tokens are counted too.
counts = sorted(len(tokenizer.encode(router_lib.router_prompt(message))) for message in messages)

# The median of an even count is the lower of the two middle values, so it is a whole number of tokens.
median = counts[(len(counts) - 1) // 2]

total = sum(counts)
mean = round(total / len(counts))

print(f"messages: {len(counts)}")
print(f"prompt tokens min: {counts[0]}")
print(f"prompt tokens median: {median}")
print(f"prompt tokens max: {counts[-1]}")
print(f"prompt tokens total: {total}")
print(f"prompt tokens mean, rounded: {mean}")
```

Output:

```text
messages: 40
prompt tokens min: 580
prompt tokens median: 585
prompt tokens max: 614
prompt tokens total: 23493
prompt tokens mean, rounded: 587
```

The prompts differ only in their messages, because the team list is the same text in every prompt. So the spread runs from 580 tokens for the shortest prompt to 614 for the longest, with a median of 585 tokens. The median is the lower of the two middle values, so it is a whole number of tokens.

In production, the count moves when the team list moves. Adding a team adds its name to every prompt, so every message costs more from that day on. Rerun the count after each change to the list, and keep the list in the same order, so that the rest of the prompt does not change with it.

To turn the count into a figure for a day, use the mean, not the median, because a day's prompt tokens are the sum of its prompts. The 40 sample messages total 23493 tokens, a mean of 587 tokens each. The mean is above the median here, so the median times the count would undercount the prompt tokens. Multiply the mean by the number of messages the router handles that day to get the prompt tokens it reads, before any output is counted. The output side depends on the design, and the designs come in later chapters.

This section gives counts only. The time a message takes is the recording's job, as [the load step](#load-each-model-at-its-pinned-revision) noted.

**Working rule:** Count the prompt's tokens with the tokenizer of the model you will run, before you choose a design, and count again whenever the prompt changes. The count belongs to that tokenizer, so a count from another model's tokenizer answers a different question.

## Why 135M is the core {#why-135m-is-the-core}

The [earlier sections](#the-candidates-and-what-we-keep) gave the 135M model its place: it is smaller, and it is the model the rest of the book trains and serves. This section gives the reasons for that choice, and says where the choice is not yet proven.

There are two broad ways to get a small model to route a message. One is to ask a model, in the prompt, which team to pick. The other is to train a model on labelled messages. Bucher and Martini compared fine-tuned BERT-style models with large hosted models, such as ChatGPT and Claude Opus, prompted zero-shot, in a 2024 preprint. Their abstract reports that the smaller fine-tuned models beat the larger prompted ones, consistently and significantly ([arXiv:2406.08660v2](https://arxiv.org/abs/2406.08660v2)). The comparison pits fine-tuned small models against prompted large ones, not small against small, and it comes from one preprint. The book takes it as the reason to measure a fine-tuned small model first. It does not take it as proof that the fine-tuned model wins on the inbox.

The two designs also fail in different ways, and the cost counts do not show that. A generative model writes its answer as text, so the text can be a string that is not one of the 77 teams. A classifier scores each of the 77 teams, so its answer is always one of them, and the score is what the hand-off rule reads to send unsure messages to a person. [Chapter 4](prompt-and-constrain) constrains the generative answer to the 77 names, and [chapter 5](fine-tune-with-lora) trains the classifier.

The cost reasons rest on the counts in the [load step](#load-each-model-at-its-pinned-revision). By both counts it printed, the 135M model is the smaller: 135 and 362 million parameters and 30 and 32 layers, the 135M's figure first in each pair. The [model card for the 135M model](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/tree/12fd25f77366fa6b3b4b768ec3050bf629380bac) describes it as light enough to run on-device, and capable across a wide range of tasks. The book's examples are the evidence for the counts, and the card is the evidence for the description.

The card also limits what the model should do: "These models should be used as assistive tools rather than definitive sources of information." That caveat agrees with the router's design. A model this size is an assistant to support staff, and a message it is unsure about goes to a person. [Chapter 1](route-a-message#hand-off-the-unsure-messages) introduces that hand-off.

This chapter does not show that the 135M model passes the measures. [Chapter 4](prompt-and-constrain) runs both models on the same messages, which is the comparison this section lacks. [Chapter 5](fine-tune-with-lora) trains the 135M model on the labelled messages and measures it on the dev split against the measures set in [chapter 2](measure-the-routing-task#three-measures-each-with-its-denominator). Until then, the choice rests on the cost counts and on the study above.

Three things would change this choice, and each one is settled by a measurement rather than by argument. If the 135M model misses a dev measure after fine-tuning, the next step is to train the 360M from the same training rows, measure it the same way, and compare the two on the dev split. If the 135M model passes the dev measures but hands off more messages than support staff can take, the lever is the hand-off threshold. [Chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev) sets that threshold on the dev split together with the hand-off rate it costs. If the bank routes a different set of messages, the choice starts again, because the measures in this chapter describe the banking messages and no others.

The choice has a cost the reader should weigh, and this chapter does not measure it. It gives neither model's load time nor its run time, and the working rule in the [first section](#the-candidates-and-what-we-keep) asks for that measurement before the choice is final. This chapter makes the choice provisionally, and the later chapters either confirm it or replace it on the same measures.

**Working rule:** Fine-tune the smaller model first, and measure it on the dev split against the measures you set before you looked at the test split. Keep the larger model as a comparison until the smaller one has missed a measure on the dev split, and do not switch models on the test split.

## What a bigger model would need {#what-a-bigger-model-would-need}

The [previous section](#why-135m-is-the-core) chose the smaller model and left the question of the larger one, SmolLM2-360M-Instruct, open. This section sets out what that question needs, and what the book does and does not know about it.

A larger model is not automatically a better one for a narrow task. A study first posted in 2024, and accepted at EMNLP 2025, compares fine-tuning, instruction-tuning, prompting and in-context learning across eight language models and eight text classification tasks. Its abstract concludes that bigger models do not consistently give better performance or lower variance ([arXiv:2402.12819v4](https://arxiv.org/abs/2402.12819v4)). It is one study, and the book uses it to justify measuring the larger model, not to rule the larger model out.

The open question is whether the 360M, trained with the same recipe as the 135M, would pass the dev measures by a margin that pays for its extra cost. The book does not train the 360M, so it does not know. It has not measured the training time or the memory that a 360M run would take on the two CPU threads the book's examples use. [Chapter 4](prompt-and-constrain) uses the 360M as a comparison on the same prompts.

A reader who wants that answer can follow the same path the book follows. The 360M is already pinned and loads offline, as [the load step](#load-each-model-at-its-pinned-revision) shows. Count the router prompt's tokens with its tokenizer, then train it on the same training rows as the 135M. Each step is a separate change, and the comparison stays on the same data, so the two results can be set side by side on the dev split.

The family's largest model, the 1.7B, would need more still. The book does not pin it, and it makes no claim about it.

A larger model's cost per message arrives with every message it serves, and the book does not measure that cost for the 360M. The [load step](#load-each-model-at-its-pinned-revision) already shows how much bigger the 360M is before anyone trains it, with 135 and 362 million parameters and 30 and 32 layers, the 135M's figure first in each pair. The `throughput` recording in [chapter 7](quantize-and-measure#measure-speed-in-a-recording) measures the classifier and its int8 copy against the stand-in on a named machine, and the 360M is not in it.

The decisions this chapter made, for a reader to check against their own bank's needs:

- The core model is SmolLM2-135M-Instruct, and the comparison is SmolLM2-360M-Instruct.
- Both models load at the commits in `examples/models.toml`, offline, through the shared loader.
- The router prompt's cost is counted in tokens with the 135M model's tokenizer, and no model runs for the count.
- No time or memory figure appears in this chapter. Those come later, from a measurement on a named machine.
- The 360M is not trained in this book.

The lesson to carry forward is that a published study can say a bigger model may not help, and only your own measurement on your own samples says whether it does.

**Working rule:** Before you choose a larger model, train it with the same recipe you used for the smaller one, and measure it on the same dev and test samples, on your own machine. Judge it by its measures and by what it costs to run on that machine, and not by a published score.
