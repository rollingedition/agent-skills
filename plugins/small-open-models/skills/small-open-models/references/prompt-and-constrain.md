---
title: "Small Open Models"
chapter: "Prompt a small model and constrain its answers to the teams"
chapter_id: prompt-and-constrain
book: small-open-models
edition: 2026.11.16
verified: 2026-11-23
edition_code: ND69-JQ1D
canonical: https://rollingedition.com/small-open-models/prompt-and-constrain
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Prompt a small model and constrain its answers to the teams,” chapter 4 of Small Open Models, Edition 2026.11.16, examples passed Nov 23, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/prompt-and-constrain. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Prompt a small model and constrain its answers to the teams

By the end of this chapter, you can write a router prompt for a small open model, constrain its answer so that it can only be a team name, and measure how many of those answers are right. You will also see why a valid answer is not a correct one, which is why the next chapter trains a model instead of asking it better questions.

A router needs every answer to be a team name, and when [chapter 1](route-a-message) let a small model answer in free text, the model did not return teams. This chapter first makes the answer a team by construction. It then runs the two open models from [chapter 3](choose-a-base-model), SmolLM2-135M-Instruct and SmolLM2-360M-Instruct, with one prompt and one constraint, and measures what they return. The 135M model is the one [chapter 5](fine-tune-with-lora) trains, so the counts here are the ones that training has to beat.

Two kinds of number appear, and the chapter keeps them apart. The live examples run on the first six messages of `test_40`, the first 40 messages of the [fixed sample](measure-the-routing-task#dev-test-and-fixed-samples), and the same six for both models. They show the mechanism. Six messages cannot separate two models, so the comparison uses a recording: each model and prompt answered all 200 messages of `test_200`, the first 200 of that sample, which includes those six, once, and the answers were saved. Reading the recording loads no model, and its counts come from the saved answers and nothing else.

## The prompt, settled before any recording {#the-prompt-settled-before-any-recording}

Every example in this chapter uses one router prompt. It tells the model that the message comes from an online bank, asks for one support team and the team name only, lists the 77 teams, and ends with `Team:`, so the model's next words are the answer. A raw model that has not been trained for the task gets nothing else, so the wording matters. This chapter does not tune it. The prompt was fixed before any recording, and the recording's manifest holds the prompt's hash. A changed prompt is a different recording, and its counts cannot be set beside the ones here.

The list of teams in the prompt is the same list the constraint uses. The trie in the next section is built from the same label names in the same order, so the prompt and the constraint cannot disagree about which teams exist. The same dependency works the other way. A reader who adds or renames a team changes the prompt, and so changes the recording's hash. The counts in this chapter then no longer describe that prompt, and the reader must record again before comparing.

The raw form passes the router prompt's text to the model as it stands. The chat form wraps the router prompt's text in the model's chat template, which adds a default system prompt. To see what the template changes, run the chat form on the same six messages:

Example `constrained-decode-135m-chat` (Python 3.12.15 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Route the first 6 messages of test_40 with the 135M model through its chat template, decoding only team names.
The template adds the model's default system prompt. The prose quotes this run's accuracy line next to the raw form's, and the messages are never printed."""

import os

# no network: the pinned model must already be in the local cache
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402

import torch  # noqa: E402

# two threads, so the sums add in the same order on every run
torch.set_num_threads(2)

import router_lib  # noqa: E402

# seeds 0 for random and torch, deterministic algorithms and float32, so greedy decoding repeats
router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

tokenizer, model = router_lib.load_model(SMALL)
trie = router_lib.build_trie(tokenizer)
# (text, label index) for every test row, in file order; the index is the gold team
rows = router_lib.read_rows("test")
# row numbers of the first six messages of the fixed 40-message sample
sample = router_lib.read_sample("test_40", 6)
teams = set(router_lib.LABELS)

results = []
for i in sample:
    # the chat template wraps the message in the model's chat format, with its default system prompt
    text = router_lib.chat_prompt(tokenizer, rows[i][0])
    # the template has already written the special tokens, so the tokenizer adds none
    results.append(router_lib.constrained_team_text(tokenizer, model, trie, text, add_special_tokens=False))
valid = [text in teams for _, text in results]
# the walk's index, never the decoded text, is what counts
right = [index == rows[i][1] for (index, _), i in zip(results, sample)]
given = collections.Counter(text for _, text in results)
# most given team; a tie in count goes to the team listed first
top = min(given, key=lambda team: (-given[team], router_lib.LABELS.index(team)))

print(f"messages: {len(sample)}")
print(f"answers that are a team: {sum(valid)}/{len(sample)}")
print(f"accuracy: {sum(right)}/{len(sample)} ({100 * sum(right) / len(sample):.1f}%)")
print(f"distinct teams given: {len(given)}")
print(f"most given team: {top}, {given[top]}/{len(sample)}")
```

Output:

```text
messages: 6
answers that are a team: 6/6
accuracy: 0/6 (0.0%)
distinct teams given: 3
most given team: cancel_transfer, 3/6
```

The book uses the raw form as its default. The choice was made before any recording was read: both models in the comparison are measured on it, so the comparison is between models, not between prompts. The chat form was recorded afterwards, as an observation. On the 200 messages it got 11/200 (5.5%) right, and the raw form got 9/200 (4.5%). A gap of two messages in 200 is not a difference this sample can show in either direction, so the chat form is not shown to help, and the raw form is not shown to hurt, and the default is not changed because of this count. The trie's names begin with a space, which follows `Team:` in the raw form but not the new line that opens the answer in the chat template. The chat count is therefore for this trie as well as for the template. The result is not evidence that raw prompts beat chat templates for small models in general, and one sample of 200 messages does not settle that.

**Working rule:** Use one prompt for every model you compare, in the form the comparison needs. Before you adopt a chat template, measure it on the same sample as the raw form, and report a small gap as a small gap.

## Why free text fails {#why-free-text-fails}

Chapter 1 asked the raw model for one team with no constraint, and the model decoded freely: greedy, taking the highest-scoring token at each step, as in this chapter, but with no mask on the tokens it could pick. Its example counted the answers. 0/20 were team names, so the router had nothing to send on.

Nothing in the model's own decoding stops an answer from being a sentence, a team that is not on the list, or a near-miss spelling of one. At each step the decoder may pick any token in the vocabulary, so the answer can go anywhere. Chapter 1's stand-in did not show this failure, because its recorded answers came from a grammar that allowed only the team names. A model that runs in the router needs the same guarantee from the decoder itself.

The tempting repair is to take whatever the model wrote and match it to the nearest team name. That repair is a guess. A near-miss spelling may match the right team, or a wrong team that is close in letters, and the router would then send the message to a team the model never named. Chapter 1 said what to do instead: an answer that is not a team counts as an error, is counted on the sample, and the message goes to a person. A constraint removes most of those answers before they are written. The count is still kept, so that a constraint which fails to hold shows up as a number and not as a quiet change in routing.

**Working rule:** Treat an answer that is not a team as a failed route. Count such answers on a fixed sample before a model routes anything, and do not match a near-miss to the closest team. Constrain the answer at decode time, and keep the count, so that a broken constraint shows up as a number.

## A token trie allows only team names {#a-token-trie-allows-only-team-names}

A model writes tokens, not words, and a team name is a short run of them. `build_trie` in `router_lib`, the book's shared module, stores the 77 names as a trie: a tree whose paths spell out each team's tokens, with the team's index at the node where its path ends. The function asserts that no two teams end at the same node, so each path names one team.

The decoder walks this tree as it writes. At the start, the allowed tokens are the first token of each team name. After each token, the allowed set narrows to the children of the node the decoder has reached. Where a path has ended on a team, the end-of-answer token joins the allowed set, so the answer can stop there. No one of the 77 names is the start of another, so every path ends at a leaf. The code would still handle a name that was: at that node the decoder could stop, or continue along the longer name. A walk of this kind cannot leave the list, because every token it may choose leads toward a team.

Greedy decoding then takes the highest-scoring of the allowed tokens at each step. Transformers applies the rule through a callback, `prefix_allowed_tokens_fn`, which returns the allowed tokens for each position. The processor starts from a mask of minus infinity for every token, sets the allowed tokens' entries to zero, and adds the mask to the scores with `scores_processed = scores + mask`. Every token that is not allowed keeps minus infinity, so greedy decoding cannot pick it ([transformers 5.24.0, `src/transformers/generation/logits_process.py`](https://raw.githubusercontent.com/huggingface/transformers/v5.22.2/src/transformers/generation/logits_process.py)).

Chapter 1's stand-in got the same guarantee from its library. `recordings/common.py` builds a grammar, `root ::= "card_arrival" | ...`, that lists the 77 names as literal strings, and the recordings applied it through the chat template. llama-cpp-python adds a grammar to its sampler before the greedy step. In `llama_cpp/llama.py` the line `sampler.add_grammar(self._model, grammar)` runs under `if grammar is not None:`, and `sampler.add_greedy()` runs after it, under `elif temp == 0.0:` ([llama-cpp-python v0.3.36, `llama_cpp/llama.py`](https://raw.githubusercontent.com/abetlen/llama-cpp-python/v0.3.36/llama_cpp/llama.py)). So the stand-in's answers were limited to the names by the library, where this chapter's callback does the same job in the decoder.

Two details of that code shape the callback. The processor calls it as `self._prefix_allowed_tokens_fn(batch_id, sent)`, so the batch index comes first. And an empty list is an error: the processor raises `ValueError` when the callback returns no tokens. The book's callback therefore never returns an empty list. When no path can continue, it returns the end-of-answer token, and the answer stops there. The end-of-answer token is the model's `<|im_end|>`, which is also its pad token (id 2). The decoder stops after 32 new tokens (`max_new_tokens=32`). Every one of the 600 recorded answers ended on a team. A node with no children always holds a team, so the empty-list case is a guard and not a case the 77 names produce.

First, the 135M model with the trie, on those six messages.

Example `constrained-decode-135m` (Python 3.12.15 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Route the first 6 messages of test_40 with the 135M model, decoding only team names, and count how many right answers that gives.
The point rests on the count of answers that are team names, which the trie guarantees, and on the accuracy line, which the measurement section reads. The messages are read from the test split and are never printed."""

import os

# no network: the pinned model must already be in the local cache
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402

import torch  # noqa: E402

# two threads, so the sums add in the same order on every run
torch.set_num_threads(2)

import router_lib  # noqa: E402

# seeds 0 for random and torch, deterministic algorithms and float32, so greedy decoding repeats
router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

tokenizer, model = router_lib.load_model(SMALL)
trie = router_lib.build_trie(tokenizer)
# (text, label index) for every test row, in file order; the index is the gold team
rows = router_lib.read_rows("test")
# row numbers of the first six messages of the fixed 40-message sample
sample = router_lib.read_sample("test_40", 6)
teams = set(router_lib.LABELS)

# (label index, team text); the index comes from the trie walk, not from parsing the text
results = [router_lib.constrained_team(tokenizer, model, trie, rows[i][0]) for i in sample]
valid = [text in teams for _, text in results]
# the walk's index, never the decoded text, is what counts
right = [index == rows[i][1] for (index, _), i in zip(results, sample)]
given = collections.Counter(text for _, text in results)
# most given team; a tie in count goes to the team listed first
top = min(given, key=lambda team: (-given[team], router_lib.LABELS.index(team)))

print(f"messages: {len(sample)}")
print(f"answers that are a team: {sum(valid)}/{len(sample)}")
print(f"accuracy: {sum(right)}/{len(sample)} ({100 * sum(right) / len(sample):.1f}%)")
print(f"distinct teams given: {len(given)}")
print(f"most given team: {top}, {given[top]}/{len(sample)}")
```

Output:

```text
messages: 6
answers that are a team: 6/6
accuracy: 1/6 (16.7%)
distinct teams given: 3
most given team: card_arrival, 4/6
```

Run on 6 messages, the model's answers are team names in every case, 6/6, which is the guarantee the trie gives. The accuracy on the same messages is 1/6 (16.7%). The [measurement section](#measure-the-constrained-answers) takes that second number apart.

The router does not read the team out of the text. `constrained_team` returns the index stored at the node where the walk ended, and the text is decoded only so that a reader can see it. The index is fixed by the trie and not by a parser that runs after the model. That is the reason the constraint is worth the code: a parser that matches text to teams can fail in ways the trie cannot. These examples return the team only so that it can be counted. Nothing in this chapter routes a message. A route returns a team only through `handoff`, which sends an uncertain answer to a person, and the examples here do not call it.

**Working rule:** Constrain the answer to the labels with a token trie built from the label names, and count the answers that are labels on a fixed sample. The constraint makes every answer a team. It does not make any answer right, so count the right answers as a separate measure.

## Decode greedily so every count repeats {#ties-and-determinism}

Every example here uses greedy decoding: the highest score wins, and nothing is sampled. That matters for the counts. A sampled answer would differ from one run to the next, and then no printed count could be checked against a recording. The examples fix their seeds and float32 through `router_lib.setup_runtime` and set two threads, so on one machine a run repeats its answers. Each example calls `torch.set_num_threads(2)` itself, at the top, so that it does not depend on how its runner was started. Each example's printed output is compared with its recorded output on every run, and a changed line fails the check.

Repeatable on one machine is not the same as repeatable everywhere. The [PyTorch 2.15.0+cpu notes on randomness](https://docs.pytorch.org/docs/2.15/notes/randomness.html) say that completely reproducible results are not guaranteed across releases, individual commits or platforms. So the book claims repeatability for the versions pinned in `examples/requirements.txt`, on the kind of machine the book ran on. A reader on another platform should expect to check the recorded lines again. If a recorded line fails there, read the changed line before touching the example. A different count of right answers can come from a different machine, a different library version or a changed prompt, and each of those needs a different fix.

Ties need a fixed rule as well. Label scoring in [the last section](#why-the-prior-wins) breaks a tie in score by the lower team index, through its sort key `(score, -index)`, and the most-given-team count breaks a tie in count by team name. Constrained decoding has no team scores. Its greedy step takes the first maximum among the allowed tokens, so a tie there goes to the lower token id.

**Working rule:** Use greedy decoding, fix the seeds and the thread count, and compare each printed line with a recorded copy on every run. Do not describe a result as reproducible beyond the versions and the kind of machine it was run on.

## Measure the constrained answers {#measure-the-constrained-answers}

The [live examples](#a-token-trie-allows-only-team-names) cover six messages. The 135M model with the raw prompt got 1/6 (16.7%) right, and the 360M model got 0/6 (0.0%). Six messages cannot rank these models: one right answer is the whole difference between those two counts. The 135M model's most common answer was card_arrival, 4/6, and the chat form on the same six messages got 0/6 (0.0%).

The 360M run is the same program with the larger model.

Example `constrained-decode-360m` (Python 3.12.15 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Decode team names for the first 6 messages of test_40 with the 360M model, and count how many of them are right.
The prose sets its accuracy line against the 135M model's, on the same six messages. The messages are read from the test split and are never printed."""

import os

# no network: the pinned model must already be in the local cache
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402

import torch  # noqa: E402

# two threads, so the sums add in the same order on every run
torch.set_num_threads(2)

import router_lib  # noqa: E402

# seeds 0 for random and torch, deterministic algorithms and float32, so greedy decoding repeats
router_lib.setup_runtime()

MEDIUM = "HuggingFaceTB/SmolLM2-360M-Instruct"

tokenizer, model = router_lib.load_model(MEDIUM)
trie = router_lib.build_trie(tokenizer)
# (text, label index) for every test row, in file order; the index is the gold team
rows = router_lib.read_rows("test")
# row numbers of the first six messages of the fixed 40-message sample
sample = router_lib.read_sample("test_40", 6)
teams = set(router_lib.LABELS)

# (label index, team text); the index comes from the trie walk, not from parsing the text
results = [router_lib.constrained_team(tokenizer, model, trie, rows[i][0]) for i in sample]
valid = [text in teams for _, text in results]
# the walk's index, never the decoded text, is what counts
right = [index == rows[i][1] for (index, _), i in zip(results, sample)]
given = collections.Counter(text for _, text in results)
# most given team; a tie in count goes to the team listed first
top = min(given, key=lambda team: (-given[team], router_lib.LABELS.index(team)))

print(f"messages: {len(sample)}")
print(f"answers that are a team: {sum(valid)}/{len(sample)}")
print(f"accuracy: {sum(right)}/{len(sample)} ({100 * sum(right) / len(sample):.1f}%)")
print(f"distinct teams given: {len(given)}")
print(f"most given team: {top}, {given[top]}/{len(sample)}")
```

Output:

```text
messages: 6
answers that are a team: 6/6
accuracy: 0/6 (0.0%)
distinct teams given: 4
most given team: card_payment_wrong_exchange_rate, 3/6
```

For the comparison, each variant answered 200 messages. The recording's counts are in the table, with the same messages in every row:

| Variant on test_200 | Answers outside the team list | Correct | Distinct teams given |
| --- | --- | --- | --- |
| 135M, raw prompt | 0/200 | 9/200 (4.5%) | 18 |
| 135M, chat template | 0/200 | 11/200 (5.5%) | 17 |
| 360M, raw prompt | 0/200 | 12/200 (6.0%) | 8 |

This example reads the table's counts from the recording:

Example `prompting-on-test-200` (Python 3.12.15 · torch 2.15.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Compare the three prompting variants on test_200, from the recording only. No model is loaded.
The chapter's table takes its three columns from the first three lines printed for each variant, and the point rests on the correct count.

recordings/prompting_eval.py wrote one answer per variant and message to examples/data/recorded/prompting-eval/answers.jsonl.
"""

import collections
import json
from pathlib import Path

import torch

# two threads, as in the other examples
torch.set_num_threads(2)

import router_lib  # noqa: E402

# seeds 0 for random and torch, deterministic algorithms and float32, as in the other examples
router_lib.setup_runtime()

ANSWERS = Path(__file__).resolve().parent / "data" / "recorded" / "prompting-eval" / "answers.jsonl"
teams = set(router_lib.LABELS)
# (text, label index) for every test row, in file order; the index is the gold team
rows = router_lib.read_rows("test")
# the 200 messages of the fixed sample; every variant answers all of them
total = len(router_lib.read_sample("test_200"))

by_variant = collections.defaultdict(list)
with open(ANSWERS) as f:
    for line in f:
        answer = json.loads(line)
        by_variant[answer["variant"]].append(answer)

for variant in sorted(by_variant):
    answers = by_variant[variant]
    outside = sum(answer["team"] not in teams for answer in answers)
    # answer["label"] is the team index the variant chose; rows[...][1] is the message's gold index
    right = sum(answer["label"] == rows[answer["index"]][1] for answer in answers)
    given = collections.Counter(answer["team"] for answer in answers)
    # most given team; a tie in count goes to the team name that sorts first, not to the index
    top = min(given, key=lambda team: (-given[team], team))
    # the gold index becomes a team name, to compare with the most given team
    gold_top = sum(router_lib.LABELS[rows[answer["index"]][1]] == top for answer in answers)
    print(f"{variant} answers outside the team list: {outside}/{total}")
    print(f"{variant} correct: {right}/{total} ({100 * right / total:.1f}%)")
    print(f"{variant} distinct teams given: {len(given)}")
    print(f"{variant} most given team: {top}, {given[top]}/{total}")
    print(f"{variant} gold for most given team: {gold_top}/{total}")
```

Output:

```text
135m-chat answers outside the team list: 0/200
135m-chat correct: 11/200 (5.5%)
135m-chat distinct teams given: 17
135m-chat most given team: topping_up_by_card, 55/200
135m-chat gold for most given team: 1/200
135m-raw answers outside the team list: 0/200
135m-raw correct: 9/200 (4.5%)
135m-raw distinct teams given: 18
135m-raw most given team: card_arrival, 165/200
135m-raw gold for most given team: 0/200
360m-raw answers outside the team list: 0/200
360m-raw correct: 12/200 (6.0%)
360m-raw distinct teams given: 8
360m-raw most given team: card_payment_wrong_exchange_rate, 94/200
360m-raw gold for most given team: 4/200
```

No row is close to a router, though the constraint holds in every one: no answer in any row is outside the team list. The 360M raw row has the most right answers, at 12/200 (6.0%), and no row beats another by more than a few messages.

Distinct teams alone mislead. The 135M raw row gives 18 distinct teams, against 8 for the 360M raw row, but most of the 135M row's answers go to one team, card_arrival, 165/200, while the 360M raw row's most given team gets only card_payment_wrong_exchange_rate, 94/200.

Figure 4.1 ranks each variant's teams by answers given. Every variant's top team dwarfs the even share over the 73 gold teams, 1.4%.

*Figure 4.1. Share of each variant's 200 answers given to its ten most given teams, ranked from the most given.*

![Every variant's most given team takes far more than an even share of the answers.](https://rollingedition.ai/books/small-open-models/2026.11.16/figures/answers-pile-on-one-team.svg)

Example `figure-answers-pile-on-one-team` (Python 3.12.15 · matplotlib 3.11.2 · torch 2.15.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Draw how each prompting variant's answers pile onto its most given teams, against the even share over the gold teams of test_200.
The prose reads the gold-team count and the even share. The counts are recomputed from the recording with the tie-break prompting-on-test-200 uses, and no model runs here."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402
import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

from lib.figures import ACCENT, INK, MUTED, new_figure, save  # noqa: E402

ANSWERS = router_lib.HERE / "data" / "recorded" / "prompting-eval" / "answers.jsonl"
STYLES = {"135m-raw": (ACCENT, "o", "135M, raw prompt"), "135m-chat": (MUTED, "s", "135M, chat template"),
          "360m-raw": (INK, "^", "360M, raw prompt")}
RANKS = 10

rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")  # the messages every variant answers
total = len(sample)
gold = collections.Counter(router_lib.LABELS[rows[i][1]] for i in sample)
even = 100 / len(gold)  # the share an even spread over the gold teams gives each one

with open(ANSWERS) as f:
    records = [json.loads(line) for line in f]

fig, ax = new_figure()
for variant, (color, marker, name) in STYLES.items():
    given = collections.Counter(r["team"] for r in records if r["variant"] == variant)
    # every variant answers all the sample's messages, so each share below uses the same total
    assert sum(given.values()) == total
    # a tie in count goes to the team name that sorts first, as in prompting-on-test-200
    ordered = sorted(given.items(), key=lambda item: (-item[1], item[0]))
    # a variant with fewer than ten teams gives no answers at the ranks past its last team
    counts = [ordered[r][1] if r < len(ordered) else 0 for r in range(RANKS)]
    print(f"{variant} most given team: {counts[0]}/{total} ({100 * counts[0] / total:.1f}%)")
    print(f"{variant} distinct teams given: {len(given)}")
    ax.plot(range(1, RANKS + 1), [100 * c / total for c in counts], color=color, marker=marker, markersize=4, label=name)

print(f"gold teams in test_200: {len(gold)}")
print(f"even share over the gold teams: {even:.1f}%")
ax.axhline(even, color=MUTED, linestyle=":", linewidth=1.4, label=f"even share over the {len(gold)} gold teams")
ax.set_xticks(range(1, RANKS + 1))
ax.set_xlabel("rank of the team, from the team given most")
ax.set_ylabel("share of the 200 answers, %")
ax.set_ylim(bottom=0)
ax.legend(frameon=False)
save(fig, "answers-pile-on-one-team")
```

Output:

```text
135m-raw most given team: 165/200 (82.5%)
135m-raw distinct teams given: 18
135m-chat most given team: 55/200 (27.5%)
135m-chat distinct teams given: 17
360m-raw most given team: 94/200 (47.0%)
360m-raw distinct teams given: 8
gold teams in test_200: 73
even share over the gold teams: 1.4%
figure: figures/answers-pile-on-one-team.svg
```

To read a row, start with the first column. If it is not zero, the constraint has not held, and the other two columns mean nothing until that is fixed. The second column is the one that matters for routing: it counts the messages whose team is the gold label, out of the whole sample, with the wrong answers counted as wrong. The third column says how many teams the variant uses at all. A variant that gives only a few teams is either guessing a few popular teams or has learned something narrow, and the count does not say which. A large count does not rule out concentration either, as the 135M raw row shows. A reader who runs the same three counts on a sample of their own messages gets a comparison on their own data, with the same meaning in each column.

The 360M model is the larger of the two, and [chapter 3](choose-a-base-model) counted how much larger it is. The table shows what that cost buys on this prompt and this constraint: 12/200 (6.0%) right, against 9/200 (4.5%) for the 135M model on the same raw form. That is a few more messages for a larger model, and the chapter does not count it as a reason to pay for the extra size.

The book computes no interval for these counts, and a gap of a few messages out of 200 could come from the sample, so the table supports one statement: the three variants are close, and none of them is a router. A reader who wants to choose between two prompts should run both on a sample of their own messages and count the same three things.

The trie checks the shape of the answer and nothing else. It does not read the message beyond the prompt, and it does not know which team is right. Any team that is on the list is allowed at every step where its name could still be written, so the decoder's choice among them is the model's choice, and the mask only decides which teams can be written at all.

Here is one valid wrong answer, described by its teams only, since messages are never quoted in this book. One test message whose gold team is `card_not_working` got `card_arrival` from the 135M raw row, a team on the list, so the constraint let it through and the count of answers outside the list stays at zero.

The lesson the outputs support is that constrained decoding makes every answer a team, but a valid answer is not a right one. The constraint only removes answers that are not teams. It does not choose a better team, and the prompt change did not either. Chapter 5 is the next step: it trains a head on the labelled messages and measures whether the trained model routes better on the same sample.

In production the failure does not show up as an error. The count of answers that are not teams stays at zero, so a check that watches only that count stays green. Only a count of right answers on a fixed, labelled sample shows the problem.

The cost falls on the people who receive the message. A valid wrong team sends the message to the wrong destination, where support staff see a request that is not theirs, and they must find the right team and move it, which is the same work a hand-off creates, with no sign on the message that it was misrouted. A router that cannot say when it is unsure gives those people nothing to act on. Constrained decoding also returns no score for the other 76 teams, so a hand-off rule built on it would have no per-team scores to compare.

**Working rule:** Report the count of right answers beside the count of valid answers, on one fixed sample, for every variant you compare. A router whose answers are all valid can still be wrong on most messages, and only the second count shows it.

## Why a prior is not a router {#why-the-prior-wins}

Constrained decoding returns one answer and no scores. Label scoring gives every team a score. For each team, label scoring sums the log-probability of the team's tokens after the prompt, where a log-probability is the logarithm of the probability the model gives a token. The team with the highest sum is the model's top team for the message.

Run it on three messages and read the top team of each:

Example `label-scoring-prior` (Python 3.12.15 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.24.0), passing in Edition 2026.11.16:

```python
"""Score every team for the first 3 messages of test_40 with the 135M model, by the summed log-probability of its tokens.
This shows the model's prior, the team it favours before any fine-tuning. The point rests on the most frequent top team and how many messages it tops. The messages are never printed."""

import os

# no network: the pinned model must already be in the local cache
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402

import torch  # noqa: E402

# two threads, so the sums add in the same order on every run
torch.set_num_threads(2)

import router_lib  # noqa: E402

# seeds 0 for random and torch, deterministic algorithms and float32, so greedy decoding repeats
router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

tokenizer, model = router_lib.load_model(SMALL)
rows = router_lib.read_rows("test")
# row numbers of the first three messages of the fixed 40-message sample
sample = router_lib.read_sample("test_40", 3)
# each team's token ids, padded to the longest name, built once for all messages
table = router_lib.label_token_table(tokenizer)

tops = []
for i in sample:
    scores = router_lib.label_scores(tokenizer, model, table, rows[i][0])
    # index of the highest-scoring team; a tie goes to the lower index
    tops.append(max(range(len(scores)), key=lambda k: (scores[k], -k)))

counts = collections.Counter(tops)
# most frequent top team; a tie in count goes to the lower index
best = min(counts, key=lambda k: (-counts[k], k))

print(f"messages: {len(sample)}")
print(f"distinct top teams: {len(counts)}")
print(f"most frequent top team name: {router_lib.LABELS[best]}")
print(f"most frequent top team: {counts[best]} of {len(sample)}")
```

Output:

```text
messages: 3
distinct top teams: 1
most frequent top team name: card_arrival
most frequent top team: 3 of 3
```

Before any training, the model puts one team first for every message: card_arrival tops 3 of 3 messages. That team is the model's prior, and three messages are too few to say more about it.

If the top team is the same for every message, the score is the model's prior and says little about any one message. The 200-message recording shows the same prior in constrained decoding: card_arrival, 165/200, the 135M raw row's favourite, is the gold team of 0/200 messages in the sample.

The sum favours short names. Each token of a team's name adds a log-probability, which is never above zero, so a team with more tokens has more terms to pull its total down. The example adds the terms without dividing by length, and the chapter does not claim to correct for it. A reader who uses label scoring should check the top teams against a sample with gold labels before trusting them.

Label scoring does give a score for each team, which is what a hand-off rule needs. Each message is scored against all 77 team names, which the code scores in one batch after the prompt runs once. Chapter 5 gets a score for each team from a single forward pass through a head that is trained on labelled messages. Label scoring is the bridge from this chapter to that one: it shows that the model already has per-team scores, and that before training they say little about the message.

**Working rule:** Use label scoring to see which team a model favours before training, and do not route with it. Do not route messages with a prompted model of this size on this task; the 200-message recording is the evidence. Train a head on the labelled messages instead, as [chapter 5](fine-tune-with-lora) does.

## What this chapter decided {#what-this-chapter-decided}

The rules in this chapter are scoped to these two models, this prompt and this constraint, on the 200 messages of the recording. A larger model, a different prompt or a longer sample could move the counts, and the book has not tested any of them on that sample. What the chapter does establish is narrower: with the raw prompt and the trie, a model of this size returns valid teams and few right ones, and the count of right ones is the number to watch.

Each decision is tested in its own section: the prompt in the first, the trie in [its section](#a-token-trie-allows-only-team-names) and greedy decoding in [its section](#ties-and-determinism), and the two counts in the measurement section. A reader who changes any of them must record again before comparing, as the first section says. A constraint makes every answer valid, and only training can make it right.

This chapter made these decisions:

- The router prompt is the raw form, and both models in the comparison use it.
- Constrained decoding uses a token trie over the 77 team names, with greedy decoding and fixed seeds.
- Every variant is reported with its count of valid answers and its count of right answers, on one fixed sample.
- The live examples show how each piece works, and only the 200-message recording compares models.
