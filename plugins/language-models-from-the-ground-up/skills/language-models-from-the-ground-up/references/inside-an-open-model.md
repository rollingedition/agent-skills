---
title: "Language Models from the Ground Up"
chapter: "Inside an open model"
chapter_id: inside-an-open-model
book: language-models-from-the-ground-up
edition: 2026.11.10
verified: 2026-11-13
edition_code: ZD73-7XB0
canonical: https://rollingedition.com/language-models-from-the-ground-up/inside-an-open-model
license: CC BY 4.0
attribution: "“Inside an open model,” chapter 10 of Language Models from the Ground Up, Edition 2026.11.10, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/inside-an-open-model. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Inside an open model

By the end of this chapter you can read an open language model with what this book has built: count where its parameters go, work out what it costs to run, score text with it fairly against a model with a different tokenizer, find the attention patterns of chapter 6 in its heads, and test what it copies. You'll also see what its size buys on the store's text, and what it doesn't.

[Chapter 9](#choosing-the-next-token) ended with descriptions from the store's own model that need checking before anyone reads them. The store's model is the small transformer that chapters 6 to 9 built, trained and used, on one catalog: the names and descriptions of the online furniture and home-goods store this book follows. **SmolLM2-360M**, an open model released by Hugging Face under the Apache 2.0 licence, is built from the same parts, as [chapter 7](#the-transformer-block) showed. But it has more than two hundred times as many parameters, and it was trained on 4 trillion tokens ([model card](https://huggingface.co/HuggingFaceTB/SmolLM2-360M/blob/f8027fd0eaeea54caa13c31d31b9fdc459c38b49/README.md)) of web text, code, mathematics and synthetic textbooks ([Allal et al., 2025](https://arxiv.org/abs/2502.02737), section 6). For the store, the question is whether a free, downloadable model trained on so much more text could do its own model's jobs: suggesting the next word in the search box, and predicting its descriptions. [Chapter 2](#read-an-open-tokenizer) read SmolLM2's tokenizer; this chapter reads the model.

Running SmolLM2 needs PyTorch and a download of about 0.7 gigabytes, its weights stored as 16-bit numbers, so, like every result in this book that depends on the machine, it ran once. The script `recordings/open_model.py` loaded the **base** model, the one trained only to predict the next token, as the store's model was, at a pinned revision, a fixed version of its repository. It ran the model on the store's text and saved what this chapter reads: every weight's shape, its scores on the store's validation names and descriptions, its heads' attention habits, [chapter 6](#attention)'s copying test and [chapter 8](#training-a-small-model)'s search-box prefixes. A second script, `recordings/open_model_family.py`, downloaded only the configuration files of SmolLM2's three sizes, also at pinned revisions. The examples read both recordings, in `examples/data/recorded/`, through `lib.open_model`.

## Count the parameters at scale {#parameters-at-scale}

The parts are familiar, so the first question is where the parameters sit. [Chapter 7](#count-the-parameters) counted the store's model by part: 1,334,144 parameters, 40% of them in the embedding table it shares with its output.

For the store, count SmolLM2's recorded weights by part, the same way:

Example `open-model-parameters` (Python 3.12.15), passing in Edition 2026.11.10:

```python
import math

from lib import open_model

shapes = {name: shape for name, shape in open_model.read("parameters").items()
          if name != "lm_head.weight"}       # the output layer is tied to the embeddings: the same weights, counted once
parts = {"embedding (shared with the output)": ["embed_tokens"], "attention": ["q_proj", "k_proj", "v_proj", "o_proj"],
         "feed-forward": ["gate_proj", "up_proj", "down_proj"], "normalization": ["layernorm", "model.norm"]}
total = sum(math.prod(shape) for shape in shapes.values())
for part, keys in parts.items():
    count = sum(math.prod(shape) for name, shape in shapes.items() if any(key in name for key in keys))
    print(f"{part}:", f"{count:,}", f"({count / total:.0%})")
print("total:", f"{total:,}")
config = open_model.read("manifest")["config"]
print("layers:", config["num_hidden_layers"])
print("width:", config["hidden_size"])
print("query heads:", config["num_attention_heads"])
print("key and value heads:", config["num_key_value_heads"])
print("feed-forward width:", config["intermediate_size"])
print("vocabulary:", f"{config['vocab_size']:,}")
print("one layer's query weights:", shapes["model.layers.0.self_attn.q_proj.weight"])
print("one layer's key weights:", shapes["model.layers.0.self_attn.k_proj.weight"])
```

Output:

```text
embedding (shared with the output): 47,185,920 (13%)
attention: 78,643,200 (22%)
feed-forward: 235,929,600 (65%)
normalization: 62,400 (0%)
total: 361,821,120
layers: 32
width: 960
query heads: 15
key and value heads: 5
feed-forward width: 2560
vocabulary: 49,152
one layer's query weights: [960, 960]
one layer's key weights: [320, 960]
```

SmolLM2 has 361,821,120 parameters, in 32 layers 960 numbers wide, with a feed-forward width of 2560 and a vocabulary of 49,152 tokens. The balance has shifted from the store's model. The embedding table, still shared with the output, holds 47,185,920 (13%); the feed-forward layers hold 235,929,600 (65%); attention holds 78,643,200 (22%); and the normalization gains almost nothing. The blocks grow with the number of layers times the square of the width, and the embedding table, for a fixed vocabulary, only with the width, so as a model grows, the blocks take over.

Attention holds fewer parameters than 15 full heads would, because of **grouped-query attention**. Each layer has 15 query heads but only 5 heads of keys and values, each shared by 3 query heads ([Ainslie et al., 2023](https://arxiv.org/abs/2305.13245)). The weights show it: one layer's query weights have the shape [960, 960], and its key weights [320, 960], a third as many. Per layer, with the head size being the width divided by the number of query heads:

attention parameters = 2 × width² + 2 × width × key and value heads × head size

for the query and output weights, then the key and value weights. During generation, a model keeps every layer's keys and values for every earlier token, so sharing them shrinks that store, as a [later section](#cost-to-run) measures; Ainslie and colleagues found it costs little in quality.

**Working rule:** Count an open model's parameters by part from its weights before you use it, as here, and read the shapes for its design choices: tied embeddings, grouped keys and values, a gated feed-forward layer. Expect the blocks, not the embeddings, to hold most of a large model's parameters.

## Compare a family's sizes {#grow-the-same-design}

SmolLM2 comes in three sizes, each built from the same parts, and their configurations show how a model's makers spend more parameters. Each configuration file gives the layers, the width, the heads and the feed-forward width, and those are enough to count every parameter, part by part, with the arithmetic of [chapter 7](#count-the-parameters) and the formula above. `lib.open_model.parameters` does it.

For the store, count all three sizes from their recorded configurations, and check the count for the 360M model against the weights the first recording saved:

Example `open-model-family` (Python 3.12.15), passing in Edition 2026.11.10:

```python
import math

from lib import open_model

for name in open_model.SIZES:
    config = open_model.config(name)
    parts = open_model.parameters(config)
    print(f"{name}, layers:", config["num_hidden_layers"])
    print(f"{name}, width:", f"{config['hidden_size']:,}")
    print(f"{name}, query heads:", config["num_attention_heads"])
    print(f"{name}, query heads per key and value head:", config["num_attention_heads"] // config["num_key_value_heads"])
    print(f"{name}, feed-forward width:", f"{config['intermediate_size']:,}")
    print(f"{name}, RoPE base:", f"{config['rope_theta']:,}")
    print(f"{name}, parameters:", f"{parts['total']:,}")
    print(f"{name}, embedding's share:", f"{parts['embedding'] / parts['total']:.0%}")
recorded = sum(math.prod(shape) for key, shape in open_model.read("parameters").items() if key != "lm_head.weight")
print("SmolLM2-360M, parameters in the recorded weights:", f"{recorded:,}")
```

Output:

```text
SmolLM2-135M, layers: 30
SmolLM2-135M, width: 576
SmolLM2-135M, query heads: 9
SmolLM2-135M, query heads per key and value head: 3
SmolLM2-135M, feed-forward width: 1,536
SmolLM2-135M, RoPE base: 100,000
SmolLM2-135M, parameters: 134,515,008
SmolLM2-135M, embedding's share: 21%
SmolLM2-360M, layers: 32
SmolLM2-360M, width: 960
SmolLM2-360M, query heads: 15
SmolLM2-360M, query heads per key and value head: 3
SmolLM2-360M, feed-forward width: 2,560
SmolLM2-360M, RoPE base: 100,000
SmolLM2-360M, parameters: 361,821,120
SmolLM2-360M, embedding's share: 13%
SmolLM2-1.7B, layers: 24
SmolLM2-1.7B, width: 2,048
SmolLM2-1.7B, query heads: 32
SmolLM2-1.7B, query heads per key and value head: 1
SmolLM2-1.7B, feed-forward width: 8,192
SmolLM2-1.7B, RoPE base: 130,000
SmolLM2-1.7B, parameters: 1,711,376,384
SmolLM2-1.7B, embedding's share: 6%
SmolLM2-360M, parameters in the recorded weights: 361,821,120
```

The counts from the configurations match the weights exactly: 361,821,120 counted, 361,821,120 recorded. The three sizes have 134,515,008, 361,821,120 and 1,711,376,384 parameters. The smallest has 30 layers, 576 wide, with 9 query heads; the middle one 32 layers, 960 wide, with 15; and the largest 24 layers, 2,048 wide, with 32, fewer layers than either and much wider. Width, not depth, is where most of the largest model's extra parameters went.

The embedding table's share falls as the models grow, from 21% to 13% to 6%, because all three share one vocabulary while their blocks grow. And the largest differs in more than size. It doesn't group keys and values: it has 1 query head per key and value head, where the two smaller ones share each among 3. Its feed-forward layer is 8,192 wide, four times its width, where the 360M model's is 2,560, 8/3 of its width. And its rotary positions turn more slowly, with a base of 130,000 against 100,000.

**Working rule:** Count a model's parameters from its configuration, and check the count against its weights, as here; a mismatch means you've misread a detail. Compare a family's sizes to see how its makers scaled the design, and don't assume a larger model differs from a smaller one only in size.

## Count what it costs to run {#cost-to-run}

Parameters set what a model can learn; they also set what it costs to run. Its weights have to sit in memory, at two bytes each in 16-bit formats, the form SmolLM2's weights are stored in ([model card](https://huggingface.co/HuggingFaceTB/SmolLM2-360M/blob/f8027fd0eaeea54caa13c31d31b9fdc459c38b49/README.md)). And during generation, as [chapter 9](#decoding-in-production) noted, every layer keeps a key and a value for every earlier token, so each new token doesn't redo the work for the text before it. That **key and value cache** grows with the length of the text:

cache per token, in bytes = layers × 2 × key and value heads × head size × 2

counting a key and a value per layer, and two bytes per number.

For the store, compute both for the three sizes: the weights, the cache per token, and the cache for the longest text the models are set up for, 8,192 tokens, with and without grouped keys and values:

Example `open-model-memory` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from lib import open_model

longest = open_model.config("SmolLM2-360M")["max_position_embeddings"]   # the longest text the models are set up for
print("longest text, in tokens:", f"{longest:,}")
for name in open_model.SIZES:
    config = open_model.config(name)
    head_size = config["hidden_size"] // config["num_attention_heads"]
    weights = open_model.parameters(config)["total"] * 2          # 16-bit numbers: 2 bytes each
    cache = config["num_hidden_layers"] * 2 * config["num_key_value_heads"] * head_size * 2   # a key and a value per layer
    ungrouped = config["num_hidden_layers"] * 2 * config["num_attention_heads"] * head_size * 2
    print(f"{name}, weights in 16-bit numbers, in GB:", f"{weights / 1e9:.1f}")
    print(f"{name}, key and value cache per token, in KB:", f"{cache / 1e3:.0f}")
    print(f"{name}, cache for the longest text, in GB:", f"{cache * longest / 1e9:.2f}")
    print(f"{name}, cache for the longest text without grouping, in GB:", f"{ungrouped * longest / 1e9:.2f}")
```

Output:

```text
longest text, in tokens: 8,192
SmolLM2-135M, weights in 16-bit numbers, in GB: 0.3
SmolLM2-135M, key and value cache per token, in KB: 23
SmolLM2-135M, cache for the longest text, in GB: 0.19
SmolLM2-135M, cache for the longest text without grouping, in GB: 0.57
SmolLM2-360M, weights in 16-bit numbers, in GB: 0.7
SmolLM2-360M, key and value cache per token, in KB: 41
SmolLM2-360M, cache for the longest text, in GB: 0.34
SmolLM2-360M, cache for the longest text without grouping, in GB: 1.01
SmolLM2-1.7B, weights in 16-bit numbers, in GB: 3.4
SmolLM2-1.7B, key and value cache per token, in KB: 197
SmolLM2-1.7B, cache for the longest text, in GB: 1.61
SmolLM2-1.7B, cache for the longest text without grouping, in GB: 1.61
```

The weights take 0.3, 0.7 and 3.4 gigabytes. The 360M model's cache takes 41 kilobytes per token, so one text of the longest length needs 0.34 gigabytes, and would need 1.01 without grouping: grouping keys and values cut it to a third. The 1.7B model, which doesn't group them, needs 197 kilobytes per token, and 1.61 gigabytes for one long text, about half its weights' size. A service writing many descriptions at once keeps one cache per text, so with long texts, the caches can outgrow the weights.

**Working rule:** Budget a model's memory as its weights plus one cache per text in progress, computed from its configuration, as here. Prefer models that group keys and values when you serve long texts or many at once, and cap the text length you allow to what you've budgeted for.

## Score the store's text with a general model {#score-the-store-text}

A model with two hundred times the parameters, trained on more than a million times as many tokens as the store's catalog holds, might be expected to predict the store's text better than the store's own small model. Measuring that takes care, because the two models use different tokenizers: SmolLM2's vocabulary of 49,152 tokens splits text differently from the store's, so their [perplexities per token](#score-with-perplexity) count different things. What they share is the text. So divide each model's total log-probability of the same text by the number of words in it: a **perplexity per word**. In symbols, for a text of W words whose tokens the model gives probabilities p₁ to pₙ, however many tokens that takes:

perplexity per word = exp(−(log p₁ + … + log pₙ) / W)

Dividing each model's total by the same number of words puts both on one scale, however many tokens each spent.

Each model scores the same events. For a name, the store's model starts from `<s>` and SmolLM2 from its own start token, `<|endoftext|>`, and both predict the name's words and then its end: `<sep>` for the store's model, a newline for SmolLM2. For a description, both are given the name and predict the description's words and its end. The names are the first 500 validation names, and the descriptions are [chapter 8's](#compare-on-descriptions) 446 products. The recording also scored each name after a label, `Product name: `, to test whether telling SmolLM2 what it's reading helps.

Before you run it, predict which model scores the store's names better per word, and by how much. Then compute the store's model's scores in NumPy, read SmolLM2's from the recording, and compare, per token and per word:

Example `open-model-on-the-store` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.10:

```python
import math

from lib import bpe, open_model, transformer
from lib.products import product_texts
from lib.store import load_products

_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
scores, tokenizer = open_model.read("scores"), bpe.store_tokenizer()
per = lambda log_p, count: f"{math.exp(-log_p / count):,.1f}"

# Names: each name's tokens and its end (<sep> for the store's model, a newline for SmolLM2), from the start token.
names = list(load_products("validation")["name"])[:len(scores["names"])]
encoded = [[index[transformer.START]] + [index[t] for t in tokenizer.encode(name)] + [index[transformer.SEP]] for name in names]
store = sum(transformer.total_log_probability(ids, 1) for ids in encoded)
smollm2 = sum(row["log_p"] for row in scores["names"])
words = sum(row["words"] for row in scores["names"])
print("validation names scored:", len(names))
print("names, per-token perplexity, the store's model:", per(store, sum(len(ids) - 1 for ids in encoded)))
print("names, per-token perplexity, SmolLM2-360M:", per(smollm2, sum(row["tokens"] for row in scores["names"])))
print("names, per-word perplexity, the store's model:", per(store, words))
print("names, per-word perplexity, SmolLM2-360M:", per(smollm2, words))
print("names after a label, per-word perplexity, SmolLM2-360M:", per(sum(r["log_p"] for r in scores["labelled names"]), words))

# Descriptions: chapter 8's products, each description's tokens and its end, given the name.
end = index[transformer.END]
store = sum(transformer.total_log_probability(ids, sep + 1) for ids, sep in product_texts("validation", 500)
            if ids[-1] == end and sep < len(ids) - 2)
words = sum(row["words"] for row in scores["descriptions"])
print("descriptions scored:", len(scores["descriptions"]))
print("descriptions, per-word perplexity, the store's model:", per(store, words))
print("descriptions, per-word perplexity, SmolLM2-360M:", per(sum(r["log_p"] for r in scores["descriptions"]), words))
```

Output:

```text
validation names scored: 500
names, per-token perplexity, the store's model: 25.8
names, per-token perplexity, SmolLM2-360M: 564.8
names, per-word perplexity, the store's model: 199.3
names, per-word perplexity, SmolLM2-360M: 54,352.8
names after a label, per-word perplexity, SmolLM2-360M: 67,101.5
descriptions scored: 446
descriptions, per-word perplexity, the store's model: 37.0
descriptions, per-word perplexity, SmolLM2-360M: 61.2
```

Per token, on these names, the store's model scores 25.8 and SmolLM2 564.8. Per word, the gap is far wider: 199.3 against 54,352.8, because SmolLM2 spends more tokens on each of the store's words, and per token hides it. On the descriptions, per word, the store's model scores 37.0, and SmolLM2 61.2. The small model wins on both, by a wide margin on names.

Telling SmolLM2 it's reading a product name doesn't close the gap. After the label, it scores 67,101.5 per word, no better than without. So the gap isn't that SmolLM2 doesn't know a name is coming; it's the names themselves. Our judgement, untested here, is that two features of the store's text account for much of it: many names begin with a product line's made-up name, which the store's model has seen across its catalog, and the store's text is lowercased with spaces around its punctuation, unlike most of what SmolLM2 learned from.

The lesson isn't that small models are better. A model predicts best the kind of text it learned from: SmolLM2 knows far more English than the store's model, and little of the store's habits. Teaching it those habits takes further training on the store's text, which [chapter 11](#adapt-a-model) describes.

**Working rule:** Compare models with different tokenizers per word, or per character, on exactly the same text and events, never per token. Before choosing a large general model over a small one trained on your own text, measure both on your text, as here; size doesn't make up for text unlike anything the model learned from.

## Find the same heads at scale {#same-heads-at-scale}

[Chapter 6](#attend-to-the-previous-token) measured the store's model's heads by their habits, against an **even spread**, which puts 1 / (i + 1) of a position's weight on each of the i + 1 tokens position i can see. The same measures work on any model, and SmolLM2 has 480 heads to measure.

For the store, read the recorded averages over the first 50 of the 446 products scored above, each text a name, a newline and its description: each head's average weight on the previous token and on the first token, and an even spread's weight on each, averaged the same way:

Example `open-model-heads` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1 · tokenizers 0.23.3), passing in Edition 2026.11.10:

```python
import numpy as np
from tokenizers import Tokenizer

from lib import open_model, transformer
from lib.products import product_texts
from lib.store import load_products

heads = open_model.read("heads")
previous, first = np.array(heads["previous"]), np.array(heads["first"])   # (layers, heads)
print("texts averaged:", heads["texts"])
print("heads in all:", previous.size)
print("heads with more than half their weight on the previous token:", int((previous > 0.5).sum()))
print("the most weight a head puts on the previous token:", f"{previous.max():.2f}")
print("average weight on the first token, layers 1 to 4:", f"{first[:4].mean():.2f}")
print("average weight on the first token, layers 5 to 32:", f"{first[4:].mean():.2f}")
print("heads with more than half their weight on the first token:", int((first > 0.5).sum()))

# An even spread, averaged the same way: each position i shares its weight equally among the i + 1 tokens it sees.
smollm2 = Tokenizer.from_file("data/smollm2-tokenizer/tokenizer.json")
end = transformer.load()[1].index(transformer.END)
rows = load_products("validation").head(500)
texts = [f"{name}\n{description}\n" for (ids, sep), name, description in
         zip(product_texts("validation", 500), rows["name"], rows["description"]) if ids[-1] == end and sep < len(ids) - 2]
lengths = [len(smollm2.encode(text, add_special_tokens=False).ids) + 1 for text in texts[:heads["texts"]]]
print("an even spread's weight on the previous token, and on the first:",
      f"{np.mean([np.mean(1 / np.arange(2, n + 1)) for n in lengths]):.2f}")
```

Output:

```text
texts averaged: 50
heads in all: 480
heads with more than half their weight on the previous token: 3
the most weight a head puts on the previous token: 0.79
average weight on the first token, layers 1 to 4: 0.13
average weight on the first token, layers 5 to 32: 0.61
heads with more than half their weight on the first token: 286
an even spread's weight on the previous token, and on the first: 0.05
```

A few heads specialize sharply. 3 put more than half their weight on the previous token, the most of them 0.79, against an even spread's 0.05; the store's model's most previous-token head put 0.35, measured the same way. With hundreds of heads, a model can afford to give a few of them one narrow job.

The first token's weight is the larger surprise. In the first four layers, heads put 0.13 of their weight on it on average; from layer 5 on, 0.61, against an even spread's 0.05, and 286 heads put more than half there. That's the **attention sink** that Xiao and colleagues found in large models ([Xiao et al., 2024](https://arxiv.org/abs/2309.17453)). They explain it by softmax: a head with nothing useful to attend to still has to put its weight somewhere, and the first token is always there. [Chapter 6](#reach-past-the-window) found the pattern only weakly in the store's model, whose description tokens put 0.11 of their attention on its two markers, against an even spread's 0.05.

**Working rule:** Describe a large model's heads by the same measured averages you'd use on a small one, compared with an even spread. Expect a few specialized heads and many that put their weight on the first token, and keep that token when you cut a model's context to save memory.

## Test copying at scale {#copying-at-scale}

[Chapter 6](#test-what-the-model-copies) showed the store's model copying `cover` from a product's name into its description, by changing the name and watching the prediction follow. The same test asks whether SmolLM2 does it too. Whether its training text held this product's text can't be checked, and the test doesn't need it: if SmolLM2 predicted `cover` from memory of the product, taking `cover` out of the name wouldn't move it.

For the store, read SmolLM2's recorded probabilities for `cover` and `set` after `this outdoor patio furniture`, in the description of `double chaise patio furniture cover`, with the name as sold, without `cover`, and ending in `set`:

Example `open-model-copying` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from lib import open_model

copying = open_model.read("copying")
for label, probabilities in copying.items():
    for token, p in probabilities.items():
        print(f"SmolLM2-360M, {label}, P({token.strip()}):", f"{p:.2f}")
```

Output:

```text
SmolLM2-360M, name as sold, P(cover): 0.75
SmolLM2-360M, name as sold, P(set): 0.00
SmolLM2-360M, name without cover, P(cover): 0.02
SmolLM2-360M, name without cover, P(set): 0.02
SmolLM2-360M, name ending in set, P(cover): 0.01
SmolLM2-360M, name ending in set, P(set): 0.77
```

With the name as sold, SmolLM2 gives `cover` 0.75. Take `cover` out of the name and it falls to 0.02; end the name in `set` and `set` gets 0.77. The store's model behaved the same way: 0.97, 0.00 and 0.70. Both models copy the next word of an earlier phrase when the phrase repeats, the behaviour of [induction heads](#read-trained-heads), heads that find an earlier copy of the current token and attend to what followed it. Olsson and colleagues found them in every model they studied with more than one layer ([Olsson et al., 2022](https://arxiv.org/abs/2209.11895)).

So copying isn't something scale adds; the store's 4-layer model learned it too. For a store, the habit is useful and risky at once: a model that copies words from the product's name stays on the product, and one that copies from the wrong product's text spreads its mistake.

**Working rule:** Test a behaviour by changing the input and watching the output, as here, and run the same test on every model you compare. When two models of very different sizes share a behaviour, it's a basic one; look for what differs elsewhere.

## Suggest the next word at scale {#suggestions-at-scale}

The search box is where the store's text matters most. [Chapter 8](#autocomplete-in-the-search-box) found the store's model alone giving `stool` a probability of 0.50 after `outdoor bar`, and the mix of the store's model and its counts, the model the search box serves, 0.28.

For the store, read SmolLM2's three likeliest next tokens after the same five prefixes, each given with nothing before it, as the store's model got them:

Example `open-model-autocomplete` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from lib import open_model

for prefix, recorded in open_model.read("prefixes").items():
    shown = ", ".join(f"{token!r} {p:.2f}" for token, p in recorded["top"][:3])
    print(f"{prefix:<12} -> {shown}")
print("P(stool | outdoor bar), SmolLM2-360M:", f"{open_model.read('prefixes')['outdoor bar']['P( stool)']:.4f}")
```

Output:

```text
bar          -> 'ry' 0.05, 'ley' 0.05, 'b' 0.04
patio bar    -> '\n' 0.21, 'be' 0.06, ',' 0.06
outdoor bar  -> '\n' 0.28, ',' 0.06, '\n\n' 0.04
kitchen bar  -> '\n' 0.37, '\n\n' 0.03, ',' 0.02
wine bar     -> '\n' 0.20, ',' 0.09, '\n\n' 0.03
P(stool | outdoor bar), SmolLM2-360M: 0.0002
```

SmolLM2 gives `stool` after `outdoor bar` a probability of 0.0002. Its likeliest next token after `outdoor bar`, `patio bar`, `kitchen bar` and `wine bar` is a newline: it takes each prefix as a complete line, likely because short lines like these end in a newline in much of the text it learned from. After `bar` alone, it suggests pieces of longer words, such as `ry` and `ley`, as in `barry` or `barley`. None of that is wrong English; it's the wrong text. A search box needs the store's habits, and the store's own models have them. A search box also has to answer within a keystroke, and the store's model runs a small fraction of SmolLM2's arithmetic per token.

**Working rule:** Don't put a general model in front of shoppers without measuring its suggestions on your own prefixes against what you have. Where a model trained on your text suggests better, keep it, and measure a general model on the jobs where its broader knowledge could matter.

## Set the two models side by side {#side-by-side}

With every measure taken, the two models can be compared in one table. The store's model is the book's own, measured in chapters 6 to 8; SmolLM2-360M is read from its recordings in this chapter.

| | The store's model | SmolLM2-360M |
| --- | --- | --- |
| Parameters | 1,334,144 | 361,821,120 |
| Layers and width | 4 layers, 128 wide | 32 layers, 960 wide |
| Query heads, and key and value heads, per layer | 4 and 4 | 15 and 5 |
| Vocabulary | 4,142 | 49,152 |
| Text, in tokens: the catalog, or tokens trained on | 2,843,222, the store's catalog | 4 trillion, mostly general text |
| Per-word perplexity on the store's names | 199.3 | 54,352.8 |
| Per-word perplexity on the store's descriptions | 37.0 | 61.2 |
| P(`cover`) when the description repeats the name | 0.97 | 0.75 |
| The most weight one head puts on the previous token | 0.35 | 0.79 |

Read down the columns and the pattern of this chapter shows. SmolLM2 is far larger on every measure of size, and both models have learned the same basic behaviours, copying and attending to the previous token. Everything about the store's own text favours the small model, because that's all it learned. The store's choice isn't between a small model and a big one; it's which job each does.

**Working rule:** Set every model you're choosing between side by side on the measures that matter for your jobs, as here, with the same text and the same tests in every column. Choose a model per job, not one model for everything.

## What goes wrong in production {#open-models-in-production}

An open model brings its makers' choices with it, and they don't announce themselves:

- **Its text isn't your text.** SmolLM2 scored the store's names far worse than the store's own small model, and a label didn't help. Measure any model on your own text before you trust it there.
- **Its tokenizer isn't yours.** Per-token numbers from two tokenizers can't be compared; score per word or per character, on the same events.
- **Its details have to match the code that runs it.** Grouped keys and values, a RoPE base of 100,000 and tied embeddings are all in SmolLM2-360M's configuration. [Chapter 7](#measure-mismatched-details) measured what a wrong RoPE base costs: a little accuracy and no error. Load models with the code their makers publish, at a pinned version, or check every detail against it.
- **Its revision changes.** A model's repository can be updated under the same name. Pin the revision, as `recordings/open_model.py` does, and record it with every result.
- **Its first token matters.** Most of SmolLM2's later heads lean on the first token. Keep it when you trim context, and never let a pipeline drop it silently.
- **Its size sets its speed.** Every generated token runs every layer, so a model a few hundred times larger takes a few hundred times the arithmetic per token. Measure the time per token on the machine you'll serve from, at the text lengths you'll serve, before you promise a response time.
- **Its licence and terms travel with it.** SmolLM2 is Apache 2.0; other open models carry other terms. Check the licence of the exact model and revision before you build on it.

## What this chapter decided {#open-model-decisions}

- **The book's open model is SmolLM2-360M, read from two recordings** at pinned revisions: its run on the store's text, and the configurations of its family. Every example runs without PyTorch or a download, and the results can be checked against what was recorded.
- **Models with different tokenizers are compared per word,** on the same text and the same events: each name's words and its end, from the start token; each description's words and its end, given the name.
- **On the store's text, the store's small model beats SmolLM2,** 199.3 against 54,352.8 per word on names, and 37.0 against 61.2 on descriptions. The search box keeps the mix of the store's model and its counts that [chapter 8](#autocomplete-in-the-search-box) chose.
- **Heads are compared across models by the same measures,** against an even spread. SmolLM2 shows both of [chapter 6](#attention)'s patterns, more sharply: a few heads that specialize in the previous token, and many that put their weight on the first token.
- **Copying from earlier in a text is basic,** shared by a 4-layer model and a 32-layer one, and tested the same way in both.
- **A model's cost is counted from its configuration before it's served:** its weights, plus one key and value cache per text in progress. Among the SmolLM2 sizes, grouped keys and values cut the 360M model's cache to a third.
