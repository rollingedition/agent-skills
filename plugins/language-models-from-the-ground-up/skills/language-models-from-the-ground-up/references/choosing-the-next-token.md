---
title: "Language Models from the Ground Up"
chapter: "Choosing the next token"
chapter_id: choosing-the-next-token
book: language-models-from-the-ground-up
edition: 2026.11.12
verified: 2026-11-13
edition_code: J2AF-6HWB
canonical: https://rollingedition.com/language-models-from-the-ground-up/choosing-the-next-token
license: CC BY 4.0
attribution: "“Choosing the next token,” chapter 9 of Language Models from the Ground Up, Edition 2026.11.12, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/choosing-the-next-token. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Choosing the next token

By the end of this chapter you can turn a language model's probabilities into text, and choose how: always the likeliest token, the likeliest whole text by beam search, or a sample shaped by a temperature, a top-k or top-p cut, a repetition penalty and a minimum length. You'll measure what each choice does to the text, and learn which failures no choice of setting can fix.

A language model gives a probability for every possible next token; it doesn't write. To write, something has to choose one token, append it, ask for the next probabilities, and repeat until the model predicts the end marker, `</s>`. That choosing is called **decoding**, and it decides much of what the text reads like, with the model unchanged.

The store has a reason to write: of the furniture and home goods in its validation split, 597 of 4,282 products have no description, and so do 14% of its training products. The store's model, the transformer that [chapter 8](#training-a-small-model) trained and measured, learned descriptions from the store's own text, so it can draft one from a product's name: start the text with the name and `<sep>`, as every training text was laid out, and let the model continue. This chapter does that with greedy decoding, beam search and sampling, using the book's shared module `lib.decoding`, built in NumPy on `lib.transformer`. Then it measures what each method writes against the store's real descriptions, and fixes two failures that the measurements expose: repetition, and descriptions that come out empty.

## Choose the likeliest token {#choose-the-likeliest-token}

The simplest decoder is **greedy**: at every step, take the single likeliest token. It needs no randomness, so it always writes the same text for the same start, and each step costs one [forward pass](#tie-the-output) of the model. The text it writes is, token by token, the model's best guess.

A product with no description is the store's need, so start with one: `front porch welcome sign wall décor`, decoded greedily for up to 60 tokens. Then take a second product, `5 light light bulb`, and print the probability that its description is empty:

Example `greedy-description` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Greedy decoding writes one description of a product that has none, and shows how it repeats itself, and how likely
the model is to leave a bulb's description empty. The prose quotes the greedy description, its repeated phrases, and
the line with the bulb's probability of an empty description."""
from collections import Counter

from lib import decoding, transformer
from lib.store import load_products

validation, training = load_products("validation"), load_products("train")
empty = lambda rows: rows["description"].fillna("").str.strip() == ""
print("validation products:", f"{len(validation):,}")
print("validation products with no description:", f"{empty(validation).sum():,}")
print("training products with no description:", f"{empty(training).mean():.0%}")
bulbs = training[training["name"].str.contains(r"\bbulbs?\b")]
print("training products named as bulbs with no description:", f"{empty(bulbs).mean():.0%}")

longest = 60
print("longest description, in tokens:", longest)
ids = decoding.generate(decoding.prompt("front porch welcome sign wall décor"), longest=longest)   # no rng: each step takes the likeliest token
print("greedy description:", decoding.text(ids))
fourgrams = Counter(tuple(ids[i:i + 4]) for i in range(len(ids) - 3))   # the four tokens from i: a window that slides one token at a time
print("4-token phrases it uses twice or more:", " | ".join(decoding.text(list(g)) for g, n in fourgrams.items() if n > 1))

end = transformer.load()[1].index(transformer.END)                     # the index of </s> in the vocabulary
probabilities = transformer.softmax(decoding.next_logits(decoding.prompt("5 light light bulb")))   # the first token after <sep>
print("P(the description is empty), 5 light light bulb:", f"{probabilities[end]:.2f}")
```

Output:

```text
validation products: 4,282
validation products with no description: 597
training products with no description: 14%
training products named as bulbs with no description: 24%
longest description, in tokens: 60
greedy description: this welcome sign is a great way to add a touch of rustic charm to your home . it is made of natural wood and features a distressed finish with a distressed finish . this welcome sign is made of wood and has a distressed finish that adds a rustic touch to your home . this sign is made from
4-token phrases it uses twice or more: this welcome sign is | to your home .
P(the description is empty), 5 light light bulb: 0.28
```

The greedy description reads like the store's own text, then loops. It reads that way because it is the store's text, recombined, as in `this welcome sign is a great way to add a touch of rustic charm to your home`. It writes `features a distressed finish with a distressed finish`, and later `has a distressed finish` again, and it uses two four-token phrases twice, `this welcome sign is` and `to your home .`, which the example lists. Greedy decoding loops because the same likeliest continuation wins whenever the text reaches a similar point: `distressed` is the model's favourite finish for a sign, so it comes back whenever a finish is due. Holtzman and colleagues found the same in large models: decoding that always maximizes probability leads to text that is "bland, incoherent, or gets stuck in repetitive loops" ([Holtzman et al., 2020](https://arxiv.org/abs/1904.09751)).

The greedy description also says the sign is `made of natural wood`, which nothing in the product's name says. The bulb shows a different failure: for `5 light light bulb`, the model gives the immediate end, an empty description, with a probability of 0.28. The model learned the catalog as it is, gaps included. Of the training products named as bulbs, 24% have no description, against 14% of all products. A [later section](#forbid-an-empty-description) deals with the empty one.

**Working rule:** Use greedy decoding when you want the same output every time and short text, such as a search-box suggestion, where the likeliest next word is the point. For anything longer than a phrase, expect it to repeat itself, and choose one of the methods in the [sections that follow](#search-for-the-likeliest-text).

## Search for the likeliest text {#search-for-the-likeliest-text}

[Greedy decoding](#choose-the-likeliest-token) picks the likeliest token at each step, which isn't the same as the likeliest text: a slightly less likely first word can lead to much likelier words after it. **Beam search** looks further. It keeps the k likeliest partial texts, the beam, scored by their **total log-probability**, the sum of the logarithms of their tokens' probabilities, where higher means likelier. At each step it extends every text in the beam by its k likeliest next tokens, and keeps the best k of the results. A text that reaches the end marker is finished and stays in the running. The heart of `lib.decoding.beam` is the line that scores each extension:

```python
            candidates += [(score + log_p[token], written + [int(token)]) for token in np.argsort(-log_p, kind="stable")[:width]]
```

Which description do you expect beam search to rank likeliest for the welcome sign? Run it twice, with a beam of 4. The first run completes the search query `outdoor bar` by up to 4 tokens, the end of the name included, the way a search box might offer whole phrases; the second writes the welcome sign's description and prints the likeliest text overall and per token, its total log-probability divided by its length.

Example `beam-search` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Beam search with a beam of four, on a search query and on a product's description. The prose quotes the two
completions of outdoor bar, then the likeliest description, its probability and the likeliest per token."""
import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
width, longest = 4, 4
print("beam width:", width)
print("longest completion, in tokens, its end included:", longest)
start = decoding.prompt("outdoor bar")[:-1]                  # a search query: <s> and the words typed so far
for score, written in decoding.beam(start, width=width, longest=longest, stops=(transformer.SEP,))[:2]:   # stop at <sep>, where a name ends; keep the two likeliest
    print("completion of outdoor bar:", decoding.text([t for t in written if vocabulary[t] != transformer.SEP]),
          f"(probability {np.exp(score):.3f})")

kept = decoding.beam(decoding.prompt("front porch welcome sign wall décor"), width=width)   # longest and stops take their defaults: 60 tokens, </s>
score, written = kept[0]                                     # the likeliest text overall
print("likeliest description:", decoding.text(written) or "(empty)")
print("its probability:", f"{np.exp(score):.2f}")
score, written = max(kept, key=lambda candidate: candidate[0] / len(candidate[1]))   # the likeliest per token
print("likeliest description per token:", decoding.text(written))
```

Output:

```text
beam width: 4
longest completion, in tokens, its end included: 4
completion of outdoor bar: stool (probability 0.365)
completion of outdoor bar: stool cushion (probability 0.089)
likeliest description: (empty)
its probability: 0.15
likeliest description per token: welcome guests to your home with this welcome sign . crafted of iron , this welcome sign is a great way to add a rustic touch to your home .
```

On the query, beam search gives what a search box should: short, likely phrases, with `stool` first and then `stool cushion`. This uses the transformer alone; the mix that [chapter 8](#training-a-small-model) chose for autocomplete would need the 4-gram's probability for every candidate at every step, which `lib.decoding` doesn't compute.

The likeliest description overall is empty. Ending at once has a probability of 0.15, and every longer text multiplies many probabilities below one, so none comes close. Stahlberg and Byrne found the same in translation models: for most sentences the most probable translation was empty, and beam search worked only because it searched badly ([Stahlberg and Byrne, 2019](https://arxiv.org/abs/1908.10090)). Ranking by probability per token removes that bias, and gives a sensible description. It still invents a material, though: this time the sign is `crafted of iron`.

**Working rule:** Use beam search for short completions where the likeliest phrase is the goal, such as search queries, ranked by total probability. For longer text, rank finished texts per token, since total probability favours the shortest, and even then prefer the sampling methods of the [next sections](#sample-with-a-temperature), which write text closer to what people write.

## Sample, with a temperature {#sample-with-a-temperature}

Greedy decoding and beam search use only the top of the distribution. **Sampling**, which [chapter 1](#predicting-the-next-word) used to generate names, uses all of it: draw the next token at random, in proportion to its probability, so a token with probability 0.2 is chosen one time in five. Before sampling, the distribution can be made sharper or flatter with a **temperature**, T: divide every logit by T before the softmax. In symbols, with zᵢ the logit of token i, as in [chapter 5](#predict-from-a-window):

P(token i) = exp(zᵢ / T) / Σⱼ exp(zⱼ / T)

A temperature below 1 sharpens the distribution, giving more of the probability to the likeliest tokens; above 1, it flattens it, giving more to unlikely ones. A temperature near 0 approaches greedy decoding, and a temperature of 1 leaves the model's probabilities as they are. Dividing by T keeps the order of the tokens; it only changes how far apart their probabilities are.

To see what temperature does to one real choice, stop the greedy description early and read the next token's distribution at three temperatures. For each one, the example prints the three likeliest tokens, how many cover 90% of the probability, and how much falls outside temperature 1's 90% cover.

Example `temperature-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""The next token's distribution after the first nine tokens of the greedy description, at three temperatures, and how
many tokens each needs to cover 90% of the probability. The prose quotes the three counts, and the share at 1.5 that
falls outside temperature 1's 90% cover."""
import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
start = decoding.prompt("front porch welcome sign wall décor")
so_far = decoding.generate(start, longest=9)                   # the greedy description's first 9 tokens
logits = decoding.next_logits(start + so_far)
print("text so far:", decoding.text(so_far))
print("tokens in the vocabulary:", f"{len(vocabulary):,}")
cover = np.argsort(-transformer.softmax(logits), kind="stable")    # at temperature 1, the likeliest first
cover = cover[:int(np.searchsorted(np.cumsum(transformer.softmax(logits)[cover]), 0.9)) + 1]   # temperature 1's 90% cover, its last token included
for temperature in [0.5, 1.0, 1.5]:
    probabilities = transformer.softmax(logits / temperature)     # divide the logits, then softmax
    top = np.argsort(-probabilities, kind="stable")
    covering = int(np.searchsorted(np.cumsum(probabilities[top]), 0.9)) + 1   # +1: the token that reaches 90% counts
    print(f"temperature {temperature}, top 3:", ", ".join(f'"{vocabulary[i].replace("</w>", "")}" {probabilities[i]:.2f}' for i in top[:3]))
    print(f"temperature {temperature}, tokens needed to cover 90% of the probability:", covering)
    print(f"temperature {temperature}, probability outside temperature 1.0's 90% cover:",
          f"{1 - probabilities[cover].sum():.0%}")
```

Output:

```text
text so far: this welcome sign is a great way to add
tokens in the vocabulary: 4,142
temperature 0.5, top 3: "a" 0.61, "style" 0.20, "some" 0.11
temperature 0.5, tokens needed to cover 90% of the probability: 3
temperature 0.5, probability outside temperature 1.0's 90% cover: 0%
temperature 1.0, top 3: "a" 0.26, "style" 0.15, "some" 0.11
temperature 1.0, tokens needed to cover 90% of the probability: 78
temperature 1.0, probability outside temperature 1.0's 90% cover: 10%
temperature 1.5, top 3: "a" 0.09, "style" 0.06, "some" 0.05
temperature 1.5, tokens needed to cover 90% of the probability: 640
temperature 1.5, probability outside temperature 1.0's 90% cover: 42%
```

The temperature sets how far the probability spreads. After `this welcome sign is a great way to add`, at temperature 1 the model needs 78 tokens to cover 90%, and the rest is a long tail, each token in it unlikely. At 0.5, 3 tokens cover 90%. At 1.5, it takes 640 tokens, and 42% of the probability falls outside temperature 1's 90% cover.

| Temperature | Three likeliest tokens | Tokens to cover 90% | Outside T = 1's 90% cover |
| --- | --- | --- | --- |
| 0.5 | "a" 0.61, "style" 0.20, "some" 0.11 | 3 | 0% |
| 1 | "a" 0.26, "style" 0.15, "some" 0.11 | 78 | 10% |
| 1.5 | "a" 0.09, "style" 0.06, "some" 0.05 | 640 | 42% |

That tail is the risk in sampling. Most tokens in it are wrong here, and at temperature 1 a sampler draws from it about once in every ten tokens, more often as the temperature rises.

**Working rule:** Treat temperature as the dial between predictable and varied text. Keep it at or a little below 1 for text that should stay close to what the training text usually says, such as product descriptions. A lower temperature makes text more predictable, not more accurate.

## Sample, and cut the tail {#sample-and-cut-the-tail}

Lowering the temperature shrinks the tail but never removes it. Two methods remove it directly, before sampling. **Top-k** keeps only the k likeliest tokens and renormalizes their probabilities to sum to one ([Fan et al., 2018](https://arxiv.org/abs/1805.04833)). **Top-p**, also called nucleus sampling, keeps the smallest set of likeliest tokens whose probabilities reach at least p ([Holtzman et al., 2020](https://arxiv.org/abs/1904.09751), equation 2). Both are options of `lib.decoding.truncate`, whose core is three steps: sort the tokens, add up their probabilities in that order, and find where the sum reaches p:

```python
    order = np.argsort(-probabilities, kind="stable")
    ...
        keep = int(np.searchsorted(np.cumsum(probabilities[order]), top_p)) + 1
```

Top-p adapts to the model's confidence, where top-k doesn't. At the point in the [previous section's example](#sample-with-a-temperature) where the model was unsure of the next word, it took 78 tokens to cover 90% of the probability, so top-p 0.9 would keep that many, while top-k 20 would keep only 20. After a word that the model predicts with near certainty, top-p keeps one or two tokens and top-k still keeps 20, most of them wrong. Holtzman and colleagues argued for top-p on exactly this ground: a fixed k is "sub-optimal across varying contexts".

Four samplers, each from the same random seed, write the welcome sign's description up to 40 tokens: sampling at temperature 1, sampling at 0.7, top-k with k = 20, and top-p with p = 0.9. Then the example replays the temperature-1 sample, listing the tokens drawn from outside each step's 90% nucleus, which top-p 0.9 would have cut.

Example `sample-descriptions` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Four samplers write the same description from one seed, and the temperature-1 draws are then replayed to mark the
tokens outside each step's 90% nucleus. The last two lines are the ones the prose quotes: how many draws came from
the tail, and which tokens they were."""
import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
start, longest, seed = decoding.prompt("front porch welcome sign wall décor"), 40, 2026
print("longest description, in tokens:", longest)
print("random seed:", seed)
for label, settings in [("sampling, temperature 1.0", {}), ("sampling, temperature 0.7", {"temperature": 0.7}),
                        ("top-k 20", {"top_k": 20}), ("top-p 0.9", {"top_p": 0.9})]:
    ids = decoding.generate(start, rng=np.random.default_rng(seed), longest=longest, **settings)
    print(f"{label}:", decoding.text(ids))

rng, written, tail = np.random.default_rng(seed), [], []    # replay temperature 1.0's draws, step by step
for _ in range(longest):
    probabilities = transformer.softmax(decoding.next_logits(start + written))
    token = int(rng.choice(len(probabilities), p=decoding.truncate(probabilities)))   # no cut: draw from all of it
    order = np.argsort(-probabilities, kind="stable")
    before = probabilities[order[:int(np.where(order == token)[0][0])]].sum()   # the probability ranked above it
    if before >= 0.9:                                        # top-p 0.9 would have cut this token
        tail.append(vocabulary[token].replace("</w>", ""))
    written.append(token)
    if vocabulary[token] == transformer.END:
        break
print("temperature 1.0, tokens drawn from outside the 90% nucleus:", f"{len(tail)} of {len(written)}")
print("temperature 1.0, those tokens:", ", ".join(tail))
```

Output:

```text
longest description, in tokens: 40
random seed: 2026
sampling, temperature 1.0: enhance your home even glywheel design with this welcome welcome sign sign . this piece is ideal for both indoor and inviting . made in the usa , mini spirits decorate .
sampling, temperature 0.7: the sign is a great way to add some extra whimsy to your home and get colorful ! made of high-quality metal , this sign comes with a hanging dustroke hanger to help you gli
top-k 20: if you have a new product with a personalized sign wall décor that will help you entertain . look no further like a home decor , this sign is constructed to make life more wonderful . this welcome sign
top-p 0.9: express your guests with this cast iron sign from the nature of the world . it features a meditating podishade design . the hose and symbol in this metal piece will be
temperature 1.0, tokens drawn from outside the 90% nucleus: 5 of 36
temperature 1.0, those tokens: inviting, in, mini, spir, decorate
```

Cutting the tail removes the rarest mistakes, not all of them. Sampling at temperature 1 wanders: it writes `welcome welcome sign sign`, invents a word, `glywheel`, and claims the sign is `made in the usa`. Only some of that comes from the tail: 5 of 36 tokens did, inviting, in, mini, spir, decorate. The doubled words and the made-up word were built from tokens inside the nucleus, which top-p would have kept. At 0.7 the text holds together better, though it now says the sign is `made of high-quality metal`, where greedy decoding said wood. Top-k and top-p read more like the catalog than plain sampling, and still invent: top-p's sign is `cast iron`, with a `podishade` design.

Across this chapter, the welcome sign has been given a material six times, by greedy decoding, beam search, three of these samples and the [penalized greedy text](#penalize-repetition) below, and nothing in its name says what it's made of. The model writes what descriptions of welcome signs usually say, and they usually state a material. A decoding method changes which plausible material the model picks; none of them can make it pick the true one.

**Working rule:** For varied text, cut the tail with top-p around 0.9 or top-k around 20, with a temperature at or a little below 1, and fix the random seed when you need to reproduce a result. Don't expect any setting to make the text true: decoding chooses among what the model finds plausible, and checking facts is a separate job.

## Measure what each setting writes {#measure-each-setting}

Single samples show the flavour of each method; measurements show the trade-offs. Several properties can be measured without a person reading the text:

- **repetition:** the share of four-token phrases that repeat an earlier one in the same description
- **the model's own [perplexity](#score-with-perplexity) of the text:** how surprising the model finds what it wrote, pooled over every token, where low means predictable
- **whether the description ends** within the limit, as real ones do
- **whether it uses a whole word of the product's name**, as a description of that product should
- **its average length** in tokens

How close does each setting come to real text? Draw 20 validation products at random from those with a description, write a description for each with every method, and compare them with the real ones, cut at the same 60-token limit:

Example `measure-decoding` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Seven ways of choosing the next token, measured on the same 20 product descriptions: how often each repeats
itself, how likely the model finds its own text, whether it ends, and whether it stays on the product. The real
descriptions come first, as the bar the others are read against. The prose quotes these lines for each setting."""
import numpy as np

from lib import decoding                    # the store's model, and the decoding methods this chapter builds
from lib.products import product_texts

longest, sample, seed = 60, 20, 2026
# Validation products, which the model never trained on, that have at least one token of description after <sep>
described = [(ids, sep) for ids, sep in product_texts("validation") if sep < len(ids) - 2]
products = [described[i] for i in np.random.default_rng(seed).choice(len(described), sample, replace=False)]
print("products, drawn at random from the validation products with a description:", sample)
print("longest description, in tokens:", longest)


settings = [("real descriptions", None), ("greedy", {}), ("greedy, repetition penalty 1.3", {"penalty": 1.3}),
            ("sampling, temperature 1.0", {"sample": True}), ("sampling, temperature 0.7", {"sample": True, "temperature": 0.7}),
            ("top-k 20", {"sample": True, "top_k": 20}), ("top-p 0.9", {"sample": True, "top_p": 0.9})]
for label, chosen in settings:
    rows = []
    for number, (ids, sep) in enumerate(products):
        start = ids[:sep + 1]                                 # the start marker, the name and <sep>: the model writes on from here
        if chosen is None:
            written = ids[sep + 1:][:longest]                 # the description as sold, cut where generating would stop
        else:
            options = {option: value for option, value in chosen.items() if option != "sample"}
            # generate samples when it's given a generator, and is greedy without one. Each product gets its own
            # seed, the same for every sampling setting, so the settings differ only in how they choose.
            rng = np.random.default_rng(seed + number) if chosen.get("sample") else None
            written = decoding.generate(start, rng=rng, longest=longest, **options)
        rows.append(decoding.measures(start, written))        # repetition, each token's log-probability, ended, uses the name, length
    repeated, log_p, ended, uses_name, length = zip(*rows)
    print(f"{label}, repeated 4-token phrases:", f"{np.mean(repeated):.0%}")
    print(f"{label}, the model's perplexity of the text:", f"{np.exp(-np.concatenate(log_p).mean()):.1f}")   # over all 20 texts' tokens at once
    print(f"{label}, ended within {longest} tokens:", f"{np.mean(ended):.0%}")
    print(f"{label}, uses a whole word of the name:", f"{np.mean(uses_name):.0%}")
    print(f"{label}, average length in tokens:", f"{np.mean(length):.0f}")
```

Output:

```text
products, drawn at random from the validation products with a description: 20
longest description, in tokens: 60
real descriptions, repeated 4-token phrases: 0%
real descriptions, the model's perplexity of the text: 30.5
real descriptions, ended within 60 tokens: 35%
real descriptions, uses a whole word of the name: 95%
real descriptions, average length in tokens: 53
greedy, repeated 4-token phrases: 11%
greedy, the model's perplexity of the text: 2.7
greedy, ended within 60 tokens: 25%
greedy, uses a whole word of the name: 80%
greedy, average length in tokens: 52
greedy, repetition penalty 1.3, repeated 4-token phrases: 0%
greedy, repetition penalty 1.3, the model's perplexity of the text: 3.9
greedy, repetition penalty 1.3, ended within 60 tokens: 70%
greedy, repetition penalty 1.3, uses a whole word of the name: 80%
greedy, repetition penalty 1.3, average length in tokens: 41
sampling, temperature 1.0, repeated 4-token phrases: 0%
sampling, temperature 1.0, the model's perplexity of the text: 22.6
sampling, temperature 1.0, ended within 60 tokens: 50%
sampling, temperature 1.0, uses a whole word of the name: 50%
sampling, temperature 1.0, average length in tokens: 45
sampling, temperature 0.7, repeated 4-token phrases: 0%
sampling, temperature 0.7, the model's perplexity of the text: 7.2
sampling, temperature 0.7, ended within 60 tokens: 45%
sampling, temperature 0.7, uses a whole word of the name: 65%
sampling, temperature 0.7, average length in tokens: 45
top-k 20, repeated 4-token phrases: 0%
top-k 20, the model's perplexity of the text: 7.6
top-k 20, ended within 60 tokens: 50%
top-k 20, uses a whole word of the name: 80%
top-k 20, average length in tokens: 40
top-p 0.9, repeated 4-token phrases: 0%
top-p 0.9, the model's perplexity of the text: 10.7
top-p 0.9, ended within 60 tokens: 30%
top-p 0.9, uses a whole word of the name: 60%
top-p 0.9, average length in tokens: 47
```

Greedy text is far more predictable than anything a person wrote, with a perplexity of 2.7, and 11% of its four-token phrases repeat. The real descriptions repeat nothing (0% of their four-token phrases), and the model finds them fairly surprising, at a perplexity of 30.5. That figure is higher than [chapter 8](#training-a-small-model)'s for descriptions, because these are a different sample and only their first 60 tokens. [Holtzman and colleagues](https://arxiv.org/abs/1904.09751) made the same observation at scale: human text isn't the text a model finds most probable.

No setting matches the real descriptions on every measure. Sampling at temperature 1 comes closest on perplexity, at 22.6, but only 50% of its descriptions use a word of the product's name, against 95% of the real ones, so it drifts off the product. Top-p 0.9 ends nearly as often as the real text, 30% against 35%, but stays on the product in only 60%. Top-k 20 stays on the product most among the samplers, at 80%, with no repetition and descriptions of 40 tokens on average. Twenty products is a small sample, so read these as directions, not exact rates.

What the measures can't say is whether a description is true. A description can be fluent, varied, on topic and wrong, and [the previous section's](#sample-and-cut-the-tail) were, about the sign's material.

**Working rule:** Compare decoding settings on measures like these, against real text of the same kind, before reading samples. Decide which measure matters most for the job: for product descriptions, staying on the product and not repeating come first. Then read a sample of the outputs anyway, for what no measure catches, and check every factual claim against the product's data.

## Penalize repetition {#penalize-repetition}

[Greedy decoding's](#choose-the-likeliest-token) loops can also be fixed without sampling. Keskar and colleagues proposed a **repetition penalty**: divide the logit of every token already generated by a factor θ above 1, so it becomes less likely ([Keskar et al., 2019](https://arxiv.org/abs/1909.05858), section 4.1). Dividing a negative logit would raise it, so implementations multiply negative logits by θ, as `lib.decoding.penalize` does, so the token becomes less likely either way. Keskar and colleagues found a factor around 1.2 balanced avoiding repetition against writing sensibly.

Go back to where the [greedy description](#choose-the-likeliest-token) was about to write `distressed` a second time. Apply the penalty by hand to the next token's logits, check the result against `lib.decoding.penalize`, and compare the probabilities before and after. Then write it greedily with the penalty, to see whether the loop goes:

Example `repetition-penalty-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""The repetition penalty applied by hand to the next token's logits, checked against lib.decoding.penalize, and then
used for a whole greedy description. The two P(distressed) lines are the ones the prose quotes, and the
assert against lib.decoding.penalize is the match it states as fact."""
import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
start, factor = decoding.prompt("front porch welcome sign wall décor"), 1.3
written = decoding.generate(start)                                    # greedy, as in greedy-description
distressed = vocabulary.index("distressed</w>")
position = [i for i, token in enumerate(written) if token == distressed][1]   # where greedy writes it a second time
before = written[:position]
print("text so far:", decoding.text(before))
print("penalty factor:", factor)

logits = decoding.next_logits(start + before)
seen = np.unique(before)                                              # every token the description has used
penalized = logits.copy()
penalized[seen] = np.where(logits[seen] > 0, logits[seen] / factor, logits[seen] * factor)   # less likely either way
assert np.allclose(penalized, decoding.penalize(logits, before, factor))   # the hand calculation is the library's
for label, adjusted in [("without a penalty", logits), ("with the penalty", penalized)]:
    probabilities = transformer.softmax(adjusted)
    top = np.argsort(-probabilities, kind="stable")[:3]
    print(f"next token, {label}:", ", ".join(f"{vocabulary[i].replace('</w>', '')} {probabilities[i]:.2f}" for i in top))
    print(f"P(distressed), {label}:", f"{probabilities[distressed]:.2f}")
print("greedy with the penalty:", decoding.text(decoding.generate(start, penalty=factor)))
```

Output:

```text
text so far: this welcome sign is a great way to add a touch of rustic charm to your home . it is made of natural wood and features a distressed finish with a
penalty factor: 1.3
next token, without a penalty: distressed 0.20, black 0.03, weathered 0.03
P(distressed), without a penalty: 0.20
next token, with the penalty: black 0.04, weathered 0.03, distressed 0.03
P(distressed), with the penalty: 0.03
greedy with the penalty: this welcome sign is a great way to add style and functionality to any room . the worn look of these beautiful signs are made from natural coir , so it can be used indoors or outdoors .
```

With a factor of 1.3, `distressed` falls from a probability of 0.20 to 0.03, and another token wins in its place. The hand calculation matches the library's, and the penalized greedy description doesn't loop. It does still invent: this time the sign is made of `natural coir`, a fibre from coconut husks.

The penalty has a side effect that the [measurements](#measure-each-setting) show: descriptions end sooner. It penalizes every token already used, including common words such as `the` and `and` that a description needs many times, but never the end marker, which hasn't been used yet. So the end becomes relatively likelier, and 70% of the penalized greedy descriptions ended within the limit, against 25% without the penalty, with an average length of 41 tokens against 52. Its repetition fell from 11% to 0%.

**Working rule:** Add a repetition penalty around 1.2 to 1.3 when you decode greedily or at a low temperature, and check what it does to length, since it shortens text. As a rule of thumb, if descriptions come out clipped, leave common function words and punctuation out of the penalty.

## Forbid an empty description {#forbid-an-empty-description}

The [greedy example](#choose-the-likeliest-token) found the model ready to write nothing for a bulb, and [beam search](#search-for-the-likeliest-text) found nothing to be the likeliest description for a sign. Both come from the catalog: many products have no description, so the model learned that ending at once is common. To fill exactly those gaps, the model has to be stopped from reproducing them. The simple fix is a **minimum length**: forbid the end marker, by setting its logit to minus infinity, until the description has some number of tokens. `lib.decoding.generate` takes it as `shortest`.

The bulb that greedy decoding left empty is the test case. Decode it twice, with no minimum and then with a minimum of 10 tokens; the output first gives the chance its description ends at once:

Example `minimum-length` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Greedy decoding of the bulb's description, without a minimum length and with one that forbids the end marker until
it has that many tokens. The prose quotes the printed probability of an empty description, and
the description the minimum produces."""
from lib import decoding, transformer

end = transformer.load()[1].index(transformer.END)                    # the index of </s>, to read its probability
start, shortest = decoding.prompt("5 light light bulb"), 10
print("P(the description is empty):", f"{transformer.softmax(decoding.next_logits(start))[end]:.2f}")   # the first token is </s>: an empty description
print("greedy description:", decoding.text(decoding.generate(start)) or "(empty)")
print("minimum length, in tokens:", shortest)
print("greedy description, with the minimum:", decoding.text(decoding.generate(start, shortest=shortest)))   # shortest: </s> stays forbidden until then
```

Output:

```text
P(the description is empty): 0.28
greedy description: (empty)
minimum length, in tokens: 10
greedy description, with the minimum: this light is a great light for a light , a light , and more light . it is made of metal and has a long , high gloss finish that will make it a perfect accent piece for your home . this light is dimmable , compatible with most standard bulbs , which are not included .
```

The minimum fills the gap, but it can't supply the facts. Without it, greedy decoding takes the empty description, at a probability of 0.28. With the minimum, it writes one, and two failures from earlier in this chapter appear in it. It repeats itself, `a light , a light , and more light`, and it states things the name doesn't: that the bulb is `made of metal`, `dimmable`, and `compatible with most standard bulbs`.

**Working rule:** Set a minimum length whenever the training text includes empty or very short examples of what you're generating. Combine it with the other settings in this chapter, not instead of them, and expect the text it forces out to need the same checking as any other.

## What goes wrong in production {#decoding-in-production}

Most of decoding's failures are quiet:

- **Fluent text states made-up facts.** Six descriptions in this chapter gave the welcome sign a material, and they disagreed. Never publish generated product text without checking each factual claim against the product's data; [chapter 11](#from-predicting-to-following) measures how often a model invents.
- **Gaps in the training text become outputs.** The model predicts an empty description for a bulb, because the catalog has many, and beam search finds the empty description likeliest of all. Forbid the end marker until a [minimum length](#forbid-an-empty-description), or the model will reproduce the gaps you're trying to fill.
- **Greedy text loops.** Use sampling with a cut tail, or a repetition penalty, for anything longer than a phrase, and measure repetition on a sample of outputs.
- **Sampled text isn't reproducible by default.** Fix and record the random seed with every generated text, so a complaint about one description can be traced and repeated.
- **Settings drift with the model.** A retrained model has a different distribution, so a temperature or top-k tuned on the last model can write differently with the next. Rerun the measurements of this chapter after every retrain, before the new model writes anything a shopper sees.
- **Each token costs a forward pass.** `lib.decoding` reruns the model over the whole text for every new token, which is simple and fine for 60 tokens. Serving systems keep every layer's keys and values from earlier positions, so each new token's matrix multiplications cover one position, though attention still reads the cached keys and values of every earlier one ([Pope et al., 2022](https://arxiv.org/abs/2211.05102)).

## What this chapter decided {#decoding-decisions}

- **Autocomplete uses the likeliest tokens.** Search-box suggestions show the top few tokens of the mix chosen in [chapter 8](#training-a-small-model), and beam search, ranked by total probability, can extend them to short phrases.
- **Descriptions use top-k 20 sampling,** the setting that stayed on the product most often without repeating, on the measures above, with a fixed, recorded seed and a minimum length so they can't come out empty. With only twenty products behind it, the choice is rechecked on a larger sample before any description reaches a shopper.
- **Beam search ranks longer texts per token,** because total probability favours the empty text. Short completions of search queries are ranked by total probability, where the likeliest phrase is what a shopper wants.
- **Decoding settings are chosen by measurement against real text:** repetition, the model's own perplexity, whether descriptions end, whether they use the name, and their length, over a random set of products, before samples are read, and again after every retrain.
- **Generated descriptions are drafts, never a source of product facts.** A person or a checking step corrects every claim that the name and the catalog can't support: every method here invented a material for a product whose name gives none.
