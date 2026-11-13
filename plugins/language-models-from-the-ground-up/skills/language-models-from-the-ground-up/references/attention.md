---
title: "Language Models from the Ground Up"
chapter: "Attention"
chapter_id: attention
book: language-models-from-the-ground-up
edition: 2026.11.10
verified: 2026-11-13
edition_code: ZD73-7XB0
canonical: https://rollingedition.com/language-models-from-the-ground-up/attention
license: CC BY 4.0
attribution: "“Attention,” chapter 6 of Language Models from the Ground Up, Edition 2026.11.10, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/attention. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Attention

By the end of this chapter you can compute attention by hand: score how well each token's query matches every earlier token's key, turn the scores into weights, and average the values those weights select. You'll add the causal mask that keeps a language model from seeing the future, the scaling that keeps the weights from collapsing onto one token, and several heads that look for different things at once. Then you'll read what a trained model attends to, test what it copies, and measure how far back it looks.

This book follows one case throughout: an online furniture and home-goods store, which it calls the store, and the text of its product names and descriptions. [Chapter 5](#a-neural-language-model)'s window model predicted the next token of that text from exactly four earlier tokens, joined side by side, each slot with its own weights. That design has two limits. It can't see a fifth token back, however much it matters, and it learns about a token in the first slot separately from the same token in the third. The store's descriptions show why the first limit hurts: a description often repeats words from the product's name, tens of tokens later, as in `protect your outdoor patio furniture from harsh elements with this outdoor patio furniture cover`. A model that can look back at the name can see which word comes next. One that sees only the last four tokens, `this outdoor patio furniture`, has to guess among everything that follows those words in other products.

**Attention** lets every position look at every earlier one, and decide from their contents how much each matters. It was introduced to let a translation model look back at the words of the sentence it was translating ([Bahdanau et al., 2015](https://arxiv.org/abs/1409.0473)), and it is the core of the transformer ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762)), the design of the open models this book reads in [chapter 10](#inside-an-open-model). This chapter builds attention on its own, then reads it inside the book's small transformer, which this book calls the store's model: a transformer trained once on the store's text, which [chapter 7](#the-transformer-block) assembles part by part.

## Look back with a weighted average {#look-back-with-a-weighted-average}

Attention replaces [chapter 5](#a-neural-language-model)'s fixed slots with a weighted average. At each position, the model computes a new vector as an average of vectors from the positions it can see, with weights it chooses from their content: high for the positions that matter here, low for the rest. The weights come from three vectors that each token's embedding is turned into, by three learned matrices:

- a **query**, what this position is looking for,
- a **key**, what this position offers to the positions that look at it,
- a **value**, what this position passes on when it's looked at.

The score of position j for position i is the dot product of i's query with j's key, divided by the square root of d, the size of each query and key, meaning how many numbers it holds. Softmax turns each row of scores into weights that are positive and sum to one, and the output at position i is the weighted sum of the values. In matrix form, for all positions at once:

Attention(Q, K, V) = softmax(QKᵀ / √d) V

where Q, K and V hold every position's query, key and value as rows ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762), section 3.2.1). The division by √d is the subject of a [later section](#scale-the-scores).

For the store, take four tokens, the start marker and `sled coffee table`, a table whose base is shaped like a sled's runners. Give each a random vector of 8 numbers, as an untrained embedding table would, and compute attention with random 8-by-4 query, key and value matrices:

Example `attention-by-hand` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.10:

```python
import numpy as np

tokens = ["<s>", "sled</w>", "coffee</w>", "table</w>"]
rng = np.random.default_rng(2026)
x = rng.normal(0, 1, (4, 8))                        # one 8-number vector per token, as an embedding table gives
w_query, w_key, w_value = (rng.normal(0, 0.5, (8, 4)) for _ in range(3))

queries, keys, values = x @ w_query, x @ w_key, x @ w_value   # what each token looks for, offers, and passes on
scores = queries @ keys.T / np.sqrt(4)                       # how well each query matches each key, scaled
weights = np.exp(scores - scores.max(1, keepdims=True))
weights /= weights.sum(1, keepdims=True)                     # softmax along each row: each row sums to 1
output = weights @ values                                     # each token: a weighted average of all the values

np.set_printoptions(precision=2, suppress=True)
print("attention weights (rows attend to columns):")
for token, row in zip(tokens, weights):
    print(f"  {token:<11}", row)
print("each row sums to 1:", bool(np.allclose(weights.sum(1), 1)))
print("output shape:", output.shape)
```

Output:

```text
attention weights (rows attend to columns):
  <s>         [0.02 0.97 0.01 0.  ]
  sled</w>    [0.21 0.52 0.16 0.11]
  coffee</w>  [0.04 0.   0.03 0.94]
  table</w>   [0.16 0.   0.03 0.81]
each row sums to 1: True
output shape: (4, 4)
```

Each row of the printed weights is one position's average: which positions it draws from, and how much. Every row sums to one, as the line `each row sums to 1: True` confirms, and the output has one 4-number vector per position. The weights are random, because the matrices are, but they already show attention's freedom: `coffee` puts most of its weight on `table`, and the start marker on `sled`, because nothing restricts which positions a row can draw from. For predicting the next token, that freedom is a bug, as the [next section](#hide-the-future) shows.

Three properties of this arithmetic matter for everything that follows. The weights depend on content, through queries and keys, so the same token can attend to different places in different texts. The number of positions doesn't matter: the same three matrices work for a name of 4 tokens or a description of 150, so the model learns one way of looking back, not one per slot. And a weighted average ignores the order of what it averages. Without a mask, attention gives `bar` the same output in `bar stool` as in `stool bar`. The causal mask of the next section lets a little order back in, because each token then sees a different number of earlier tokens, and Haviv and colleagues found that language models can infer positions from that alone ([Haviv et al., 2022](https://arxiv.org/abs/2203.16634)). Models still add explicit position information, as [chapter 7](#the-transformer-block) does.

**Working rule:** Write out attention's four lines once, as this example does, and print the weight matrix: its rows say exactly where each position looks. Keep queries, keys and values as separate matrices while you're learning. Libraries often keep them in one matrix, as PyTorch's `MultiheadAttention` does with its `in_proj_weight` ([source](https://github.com/pytorch/pytorch/blob/v2.14.1/torch/nn/modules/activation.py)), and split the result, which computes the same thing.

## Hide the future with a causal mask {#hide-the-future}

In the [first section](#look-back-with-a-weighted-average), `coffee` drew most of its average from `table`, a later token. A language model can't be allowed to do that, because it predicts each token from the tokens before it. If position i could attend to position i + 1, it would see the answer: training would reward copying the next token, and the model would learn nothing it could use when generating text, where the next token doesn't exist yet. The fix is the **causal mask**: before softmax, set every score for a later position to minus infinity. The exponential of minus infinity is zero, so those positions get a weight of zero, and each position averages only over itself and the positions before it.

The mask also makes training efficient. With it, one pass over a text predicts every position at once, each from its own past, where [chapter 5](#a-neural-language-model)'s window model needed a separate window for every prediction.

For the store, apply the mask to the same four tokens' scores. Then test what the mask is for: replace the last token, `table`, with a different vector, and check whether the output at `coffee` changes, without the mask and with it:

Example `causal-mask` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.10:

```python
import numpy as np

tokens = ["<s>", "sled</w>", "coffee</w>", "table</w>"]
rng = np.random.default_rng(2026)
x = rng.normal(0, 1, (4, 8))
w_query, w_key, w_value = (rng.normal(0, 0.5, (8, 4)) for _ in range(3))   # the same draws as attention-by-hand
allowed = np.tril(np.ones((4, 4), dtype=bool))               # position i may look at positions 0 to i only


def attend(x, mask):
    scores = (x @ w_query) @ (x @ w_key).T / np.sqrt(4)
    if mask:
        scores = np.where(allowed, scores, -np.inf)          # a score of minus infinity becomes a weight of 0
    weights = np.exp(scores - scores.max(1, keepdims=True))
    weights /= weights.sum(1, keepdims=True)
    return weights, weights @ (x @ w_value)


weights, _ = attend(x, mask=True)
np.set_printoptions(precision=2, suppress=True)
print("weights with the causal mask:")
for token, row in zip(tokens, weights):
    print(f"  {token:<11}", row)
print("weight on later tokens:", float(weights[~allowed].sum()))

changed = x.copy()
changed[3] = rng.normal(0, 1, 8)                             # a different last token in place of `table`
for mask in [False, True]:
    before, after = attend(x, mask)[1][2], attend(changed, mask)[1][2]
    print(f"output at coffee changes with the last token, {'with' if mask else 'without'} the mask:",
          bool(not np.allclose(before, after)))
```

Output:

```text
weights with the causal mask:
  <s>         [1. 0. 0. 0.]
  sled</w>    [0.29 0.71 0.   0.  ]
  coffee</w>  [0.58 0.01 0.41 0.  ]
  table</w>   [0.16 0.   0.03 0.81]
weight on later tokens: 0.0
output at coffee changes with the last token, without the mask: True
output at coffee changes with the last token, with the mask: False
```

The weight matrix is now lower-triangular, with zeros above the diagonal, so the total weight on later tokens is 0.0. The start marker can attend only to itself, so its row is a single 1. `sled` splits its weight between the start marker and itself. `coffee`, which put almost all its weight on the later `table` before the mask, now spreads it over the positions it's allowed, because softmax divides only among the positions left. The last row, `table`, is unchanged, since it had no later positions to lose.

The last two lines show the leak the mask closes. Without the mask, changing the last token changes the output at `coffee`: True. With it, `coffee`'s output can't depend on what comes later: False. A model trained without the mask can learn to copy each answer from the next position, so its training loss can fall close to zero while it learns nothing it can use to generate text. Nothing crashes along the way, which is what makes a wrong mask hard to notice.

**Working rule:** Apply the mask to scores before softmax, never to weights after it, so each row still sums to one. Test it the way this example does: check that the weight on later positions is exactly zero, and that changing a later token leaves earlier outputs unchanged. If a model's training loss falls far faster than expected, check the mask first.

## Scale the scores {#scale-the-scores}

Attention's formula divides every score by √d, and the reason is in the dot product. A dot product of two vectors adds up one product per number. If the numbers in queries and keys are independent and random, with mean 0 and variance 1, a score has variance d, so queries and keys of a larger size give larger scores ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762), section 3.2.1, footnote 4). Softmax turns large differences between scores into extreme weights: one position gets nearly all the weight, and the rest nearly none. Vaswani and colleagues suspected that a model in that state learns slowly, because softmax's gradients are tiny when one weight is close to 1. Dividing by √d brings the scores back to variance 1, whatever the size.

The store's model makes this concrete: its heads work with queries and keys of 32 numbers. For the store, draw random queries and keys of three sizes, 4, 32 and 256, score each query against 16 keys with and without the division, and report the largest weight in each row, averaged over 1,000 queries. Before you run it, predict the largest weight with 256 numbers and no division:

Example `scaling-matters` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.10:

```python
import numpy as np

rng = np.random.default_rng(2026)
for size in [4, 32, 256]:
    queries, keys = rng.normal(0, 1, (1000, size)), rng.normal(0, 1, (16, size))
    for divide in [False, True]:
        scores = queries @ keys.T / (np.sqrt(size) if divide else 1)
        weights = np.exp(scores - scores.max(1, keepdims=True))
        weights /= weights.sum(1, keepdims=True)
        label = "scaled" if divide else "unscaled"
        print(f"size {size}, {label}, average largest weight in a row: {weights.max(1).mean():.2f}")
```

Output:

```text
size 4, unscaled, average largest weight in a row: 0.45
size 4, scaled, average largest weight in a row: 0.25
size 32, unscaled, average largest weight in a row: 0.78
size 32, scaled, average largest weight in a row: 0.24
size 256, unscaled, average largest weight in a row: 0.92
size 256, scaled, average largest weight in a row: 0.25
```

Without the division, the largest weight grows with the size: 0.45 with 4 numbers, 0.78 with 32, the size of the store's model's heads, and 0.92 with 256. At the larger sizes, each query attends mostly to one key before any training has happened. With the division, the largest weight stays at 0.25 at every size: spread over several keys, though not evenly, since 16 equal weights would be about 0.06 each.

That's the state training should start from. Every position looks at several others, so the gradients reach all of them, and training sharpens the weights where sharp weights help. A trained head can still put most of its weight on one position, as some of the [store's model's heads](#read-trained-heads) do; the scaling only keeps heads from starting there.

**Working rule:** Divide attention scores by the square root of the query's size, as the transformer paper does. A few models, such as T5, leave the division out and fold the factor into how the query weights start instead ([source](https://github.com/huggingface/transformers/blob/v4.46.0/src/transformers/models/t5/modeling_t5.py)), so check which a model does before you load its weights. If you change how queries and keys are computed or initialized, print the average largest weight of an untrained model, as here, and expect it to be well below 1.

## Several heads look for different things {#several-heads}

Each attention computation so far gives one set of weights per position, which can look for one kind of thing: the previous token, say, or the product's name. A model usually needs several at once. **Multi-head attention** runs several attention computations, called **heads**, side by side, each with its own query, key and value matrices, and each in a share of the vector's numbers: with 8 numbers and 2 heads, each head works in 4. The heads' outputs are joined side by side and mixed back together by one more learned matrix, the **output projection** ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762), section 3.2.2).

Splitting the numbers keeps the cost about the same as one head over all of them, and gives each head its own pattern of weights. The store's model has 4 heads in each layer, each working in 32 numbers.

For the store, run two heads over four positions of random vectors, with the causal mask, and compare what the last position attends to in each:

Example `attention-heads` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.10:

```python
import numpy as np

rng = np.random.default_rng(2026)
positions, dims, heads = 4, 8, 2
size = dims // heads                                          # each head works in 4 of the 8 dimensions
x = rng.normal(0, 1, (positions, dims))
w_query, w_key, w_value, output_projection = (rng.normal(0, 0.5, (dims, dims)) for _ in range(4))


def split(m):                                                 # (positions, dims) -> (heads, positions, size)
    return m.reshape(positions, heads, size).transpose(1, 0, 2)


queries, keys, values = split(x @ w_query), split(x @ w_key), split(x @ w_value)
scores = queries @ keys.transpose(0, 2, 1) / np.sqrt(size)             # one score matrix per head
scores = np.where(np.tril(np.ones((positions, positions), dtype=bool)), scores, -np.inf)
weights = np.exp(scores - scores.max(-1, keepdims=True))
weights /= weights.sum(-1, keepdims=True)
joined = (weights @ values).transpose(1, 0, 2).reshape(positions, dims)   # the heads' outputs side by side
output = joined @ output_projection                                       # mixed back together by one more matrix

print("weights shape (heads, positions, positions):", weights.shape)
print("what the last token attends to, head 1:", np.round(weights[0, -1], 2))
print("what the last token attends to, head 2:", np.round(weights[1, -1], 2))
print("output shape:", output.shape)
```

Output:

```text
weights shape (heads, positions, positions): (2, 4, 4)
what the last token attends to, head 1: [0.41 0.18 0.29 0.11]
what the last token attends to, head 2: [0.04 0.32 0.14 0.5 ]
output shape: (4, 8)
```

The weights now have one matrix per head, of shape (2, 4, 4). The last position's rows differ between the heads, though both read the same input: head 1 puts its largest weight on the first position, and head 2 on the last, its own. With random matrices the difference means nothing yet, but it's the room training uses: each head can learn a different way of looking back, and the output projection combines what they found. The output has the input's shape again, (4, 8), so attention layers can be stacked, as [chapter 7](#the-transformer-block) does.

**Working rule:** As a rule of thumb, keep each head at least 32 numbers wide. In the transformer paper's experiments, 16 heads of 32 did as well as 8 heads of 64, while 32 heads of 16 did worse, and reducing the size of keys hurt ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762), table 3). Check the weight tensor's shape, heads by positions by positions, whenever you change the model: a head axis in the wrong place mixes heads together without any error.

## Read what trained heads attend to {#read-trained-heads}

Random matrices show the arithmetic; a trained model shows what attention is for. The store's model has 4 layers, each with 4 heads of attention. It was trained once, in `recordings/transformer.py`, on the store's training names and descriptions, each product as one text: the start marker, the name, a separator token `<sep>`, the description and the end marker. Each layer's attention reads the output of the layer before, so later layers can attend on the basis of what earlier ones found. As in [chapter 5](#a-neural-language-model), the examples read the saved weights and recompute the model in NumPy, with `lib.transformer`, which also returns every head's weights.

For the store, take a validation product the model never trained on, `double chaise patio furniture cover`, whose description repeats the end of its name. Stop at the description's second `furniture`, where the next token is `cover`. Print the model's probability for `cover`, and each head's three largest weights in the first and last layers. `current:` marks the position being predicted from, `name:` a token in the name, and `description:` an earlier token in the description:

Example `trained-attention` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.10:

```python
import numpy as np

from lib import transformer
from lib.store import load_products

_, vocabulary, manifest = transformer.load()
settings = manifest["settings"]
index = {t: i for i, t in enumerate(vocabulary)}
product = load_products("validation").query("name == 'double chaise patio furniture cover'").iloc[0]
ids = transformer.product_ids(product["name"], product["description"], index, settings["longest"])
sep = ids.index(index[transformer.SEP])
position = ids.index(ids[sep - 1], sep) - 1           # just before the description first repeats the name's last token
logits, attention = transformer.forward(ids, keep=True)
probabilities = transformer.softmax(logits[position])


def label(i):
    """Where a token sits: the current position, the name, the description, or a marker."""
    if i == position:
        return f"current:{vocabulary[ids[i]]}"
    if i == 0 or i == sep:
        return vocabulary[ids[i]]
    return f"{'name' if i < sep else 'description'}:{vocabulary[ids[i]]}"


print("layers:", settings["layers"])
print("heads per layer:", settings["heads"])
print("dimensions per head:", settings["dimensions"] // settings["heads"])
print("name:", " ".join(vocabulary[i] for i in ids[1:sep]))
print("description so far:", " ".join(vocabulary[i] for i in ids[sep + 1:position + 1]))
print(f"P(next token is {vocabulary[ids[position + 1]]}): {probabilities[ids[position + 1]]:.2f}")
for layer in [0, len(attention) - 1]:
    for head, weights in enumerate(attention[layer]):
        top = np.argsort(-weights[position], kind="stable")[:3]
        print(f"layer {layer + 1}, head {head + 1}: " + ", ".join(f"{label(i)} {weights[position, i]:.2f}" for i in top))

name_cover = sep - 1                                     # the name's last token, `cover`
earlier = ids.index(ids[position], sep + 1)              # the description's earlier `furniture`
last = attention[-1][:, position]                        # the last layer's heads, at the current position
head = int(last[:, name_cover].argmax())
print("last-layer head with the most weight on the name's cover:", f"head {head + 1}")
print("its weight on the name's cover:", f"{last[head, name_cover]:.2f}")
print(f"its weight on {vocabulary[ids[earlier + 1]].removesuffix('</w>')}, after the description's earlier furniture:",
      f"{last[head, earlier + 1]:.2f}")
```

Output:

```text
layers: 4
heads per layer: 4
dimensions per head: 32
name: double</w> chaise</w> patio</w> furniture</w> cover</w>
description so far: protect</w> your</w> outdoor</w> patio</w> furniture</w> from</w> har sh</w> elements</w> with</w> this</w> outdoor</w> patio</w> furniture</w>
P(next token is cover</w>): 0.97
layer 1, head 1: current:furniture</w> 0.80, description:furniture</w> 0.11, description:elements</w> 0.03
layer 1, head 2: current:furniture</w> 0.31, name:furniture</w> 0.13, description:furniture</w> 0.11
layer 1, head 3: current:furniture</w> 0.18, description:patio</w> 0.18, <sep> 0.12
layer 1, head 4: description:protect</w> 0.17, current:furniture</w> 0.14, description:patio</w> 0.11
layer 4, head 1: name:cover</w> 0.48, name:double</w> 0.18, name:furniture</w> 0.13
layer 4, head 2: name:cover</w> 0.37, <s> 0.13, name:chaise</w> 0.11
layer 4, head 3: description:patio</w> 0.27, current:furniture</w> 0.25, description:outdoor</w> 0.21
layer 4, head 4: description:with</w> 0.38, description:from</w> 0.21, description:elements</w> 0.06
last-layer head with the most weight on the name's cover: head 1
its weight on the name's cover: 0.48
its weight on from, after the description's earlier furniture: 0.00
```

The model gives `cover` a probability of 0.97, and the heads show where it may have looked. In the first layer, one head attends mostly to the current token, `furniture`, and the other three spread their weight over the description and the name so far. In the last layer, head 1 puts 0.48 of its weight on `cover` in the name, many tokens back: the token that followed `furniture` in the name. The description's own earlier `furniture` was followed by `from`, and that head gives `from` only 0.00. A second last-layer head also puts its largest weight on the name's `cover`.

That pattern has a name. Olsson and colleagues found pairs of heads that work this way in small models made only of attention layers, and heads with the same behaviour in large models. They call the later head of each pair an **induction head**: a head in an earlier layer copies each token's predecessor into its position, and the induction head uses that to find earlier positions that followed the current token, and attends to them ([Olsson et al., 2022](https://arxiv.org/abs/2209.11895)). The weights above are consistent with that behaviour, but weights show where a head drew its average from, not what the model used, so the [next section](#test-what-the-model-copies) tests it.

**Working rule:** When you inspect a trained model, start with specific tokens in texts you understand, where you know what the model should look at, as here. Treat what the weights suggest as a hypothesis, and test it by changing the input, as the next section does.

## Test what the model copies {#test-what-the-model-copies}

If the model predicts `cover` by copying it from the name, then changing the name should change the prediction. If it predicts `cover` because descriptions of this kind often continue that way, the name shouldn't matter much. A test that changes the input and watches the output answers that, where attention weights can't.

For the store, keep the description and change the name: the name as sold, the name without `cover`, and the name ending in `set` instead. Print the probabilities of `cover` and `set` at the same position. Then count what follows `this outdoor patio furniture` in the training descriptions, the four tokens a window model would see:

Example `copy-from-the-name` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.10:

```python
from lib import transformer
from lib.store import load_products

_, vocabulary, manifest = transformer.load()
index = {t: i for i, t in enumerate(vocabulary)}
product = load_products("validation").query("name == 'double chaise patio furniture cover'").iloc[0]
cover, other = index["cover</w>"], index["set</w>"]

for name, label in [("double chaise patio furniture cover", "name as sold"),
                    ("double chaise patio furniture", "name without cover"),
                    ("double chaise patio furniture set", "name ending in set")]:
    ids = transformer.product_ids(name, product["description"], index, manifest["settings"]["longest"])
    sep = ids.index(index[transformer.SEP])
    furniture = [i for i in range(sep + 1, len(ids)) if ids[i] == index["furniture</w>"]]
    p = transformer.softmax(transformer.forward(ids)[furniture[1]])   # at the description's second `furniture`
    print(f"{label}, P(cover): {p[cover]:.2f}")
    print(f"{label}, P(set): {p[other]:.2f}")

phrase = "this outdoor patio furniture "
after = [d.split(phrase, 1)[1].split()[0] for d in load_products("train")["description"]
         if isinstance(d, str) and phrase in d and d.split(phrase, 1)[1].split()]
print("training descriptions with 'this outdoor patio furniture':", len(after))
print("followed by cover:", after.count("cover"))
```

Output:

```text
name as sold, P(cover): 0.97
name as sold, P(set): 0.02
name without cover, P(cover): 0.00
name without cover, P(set): 0.29
name ending in set, P(cover): 0.00
name ending in set, P(set): 0.70
training descriptions with 'this outdoor patio furniture': 6
followed by cover: 2
```

With the name as sold, the model gives `cover` 0.97. Take `cover` out of the name and its probability falls to 0.00. End the name in `set` instead, and the model gives `set` 0.70 and `cover` 0.00. The prediction follows the name. In the training descriptions, 6 contain `this outdoor patio furniture`, and 2 of them continue with `cover`. So the four tokens alone point only weakly at `cover`; the name decides it.

That's the behaviour the previous section's weights suggested, now shown by its effect: the model copies a word from the product's name, many tokens back, which a model limited to a window of four tokens can't do. One product isn't a measure of how often the model does it; the [next two sections](#attend-to-the-previous-token) measure its heads over many products.

**Working rule:** Test a claim about what a model uses by changing that input and measuring the output, as here, and include a change that should leave the output alone. Read attention weights for hypotheses, and use tests like this one for conclusions.

## Some heads attend to the previous token {#attend-to-the-previous-token}

One text can mislead; an average over many shows a head's habits. One habit worth measuring is attending to the previous token. A head that does it carries each token's predecessor forward into its position, so later layers see pairs of tokens, as [chapter 1](#predicting-the-next-word)'s bigram counts did, and the copying of the [previous sections](#read-trained-heads) depends on it: to find what followed `furniture` before, a head needs each earlier position to know its predecessor.

For the store, average each head's weight on the previous token over the first 300 validation products, find the head that puts the most there, and compare with an even spread, which puts 1 / (i + 1) on each of the i + 1 tokens position i can see:

Example `previous-token-heads` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.10:

```python
import numpy as np

from lib import transformer
from lib.products import product_texts

texts = product_texts("validation", 300)
layers, heads = len(transformer.forward(texts[0][0], keep=True)[1]), transformer.load()[2]["settings"]["heads"]
on_previous = np.zeros((layers, heads))
for ids, _ in texts:
    _, attention = transformer.forward(ids, keep=True)
    for layer, weights in enumerate(attention):        # weights: (heads, positions, positions)
        on_previous[layer] += weights[:, np.arange(1, len(ids)), np.arange(len(ids) - 1)].mean(1)
on_previous /= len(texts)
even = np.mean([np.mean(1 / np.arange(2, len(ids) + 1)) for ids, _ in texts])   # spread evenly over the visible tokens

print("average weight on the previous token (rows: layers, columns: heads):")
for layer, row in enumerate(on_previous, start=1):
    print(f"  layer {layer}: " + "  ".join(f"{w:.2f}" for w in row))
layer, head = np.unravel_index(on_previous.argmax(), on_previous.shape)
print("head with the most weight on the previous token:", f"layer {layer + 1}, head {head + 1}")
print("its weight on the previous token:", f"{on_previous.max():.2f}")
print("an even spread's weight on the previous token:", f"{even:.2f}")
```

Output:

```text
average weight on the previous token (rows: layers, columns: heads):
  layer 1: 0.03  0.06  0.13  0.10
  layer 2: 0.32  0.13  0.27  0.24
  layer 3: 0.13  0.33  0.09  0.07
  layer 4: 0.11  0.07  0.35  0.27
head with the most weight on the previous token: layer 4, head 3
its weight on the previous token: 0.35
an even spread's weight on the previous token: 0.07
```

The head that puts the most weight on the previous token is layer 4, head 3, with 0.35 on average. An even spread, averaged the same way, would put 0.07 there, so that head favours the previous token about five times over. Several heads in the later layers put a quarter or more of their weight there, and the first layer's heads put much less: in the [trained-attention example](#read-trained-heads), one of them attended mostly to the current token.

No head is purely a previous-token head; each mixes it with other habits. A head's average says what it does most, not all it does, so describing a head as having one job oversimplifies.

**Working rule:** Describe a trained head by measured averages, such as its weight on the previous token, the current token or the start marker, over a few hundred texts. Compare each with what an even spread would give, averaged the same way, so a number such as 0.3 can be read as large or small.

## Reach past the window {#reach-past-the-window}

Attention's promise was to see past [chapter 5](#a-neural-language-model)'s four-token window, which predicts from the current token and the three before it. Whether the store's model does is measurable. For every description token in the first 300 validation products, leaving out the end marker, add up the weight each head puts on tokens 4 or more positions back, the nearest a four-token window can't see, and separately the weight on the two markers, `<s>` and `<sep>`. Average over tokens, heads and layers, and compare with an even spread over the positions each token can see:

Example `attention-reaches-back` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.10:

```python
import numpy as np

from lib import transformer
from lib.products import product_texts

_, vocabulary, manifest = transformer.load()
end = vocabulary.index(transformer.END)
texts = product_texts("validation", 300)
layers = manifest["settings"]["layers"]
far, markers, even_far, even_markers, counted = np.zeros(layers), np.zeros(layers), 0.0, 0.0, 0
for ids, sep in texts:
    queries = np.array([i for i in range(sep + 1, len(ids)) if ids[i] != end])    # the description's tokens
    if len(queries) == 0:
        continue                                          # a product with no description
    _, attention = transformer.forward(ids, keep=True)
    stacked = np.stack(attention)[:, :, queries]          # (layers, heads, description tokens, positions)
    positions = np.arange(len(ids))
    is_marker = np.isin(positions, [0, sep])              # <s> and <sep>
    beyond = (queries[:, None] - positions[None, :] >= 4) & ~is_marker   # what a 4-token window can't see
    far += (stacked * beyond).sum(-1).mean(1).sum(-1)
    markers += (stacked * is_marker).sum(-1).mean(1).sum(-1)
    even_far += (beyond.sum(1) / (queries + 1)).sum()     # an even spread over the positions each token can see
    even_markers += (2 / (queries + 1)).sum()
    counted += len(queries)

print("description tokens measured:", f"{counted:,}")
print("average attention weight of a description token, by layer:")
for layer in range(layers):
    print(f"  layer {layer + 1}: 4 or more tokens back {far[layer] / counted:.2f}, on <s> and <sep> {markers[layer] / counted:.2f}")
print("all layers, weight 4 or more tokens back:", f"{far.mean() / counted:.2f}")
print("an even spread's weight 4 or more tokens back:", f"{even_far / counted:.2f}")
print("all layers, weight on <s> and <sep>:", f"{markers.mean() / counted:.2f}")
print("an even spread's weight on <s> and <sep>:", f"{even_markers / counted:.2f}")
described = [(ids[1:sep], ids[sep + 1:]) for ids, sep in texts if any(i != end for i in ids[sep + 1:])]
print("products with a description:", len(described))
print("descriptions that repeat a token of the name:", sum(bool(set(n) & set(d)) for n, d in described))
```

Output:

```text
description tokens measured: 20,571
average attention weight of a description token, by layer:
  layer 1: 4 or more tokens back 0.42, on <s> and <sep> 0.12
  layer 2: 4 or more tokens back 0.39, on <s> and <sep> 0.04
  layer 3: 4 or more tokens back 0.58, on <s> and <sep> 0.13
  layer 4: 4 or more tokens back 0.47, on <s> and <sep> 0.13
all layers, weight 4 or more tokens back: 0.46
an even spread's weight 4 or more tokens back: 0.85
all layers, weight on <s> and <sep>: 0.11
an even spread's weight on <s> and <sep>: 0.05
products with a description: 262
descriptions that repeat a token of the name: 244
```

Across all layers, description tokens put 0.46 of their attention on tokens 4 or more back. An even spread would put 0.85 there, because most of what a description token can see is far back. So the heads favour nearby tokens, as you'd expect for predicting the next word, and still send a large share of their attention past the window, which no earlier model in this book could use. That matters for this text: of the 262 products with a description, 244 have a description that repeats at least one token of the name.

The markers get 0.11 of the attention, against 0.05 for an even spread: about twice as much as chance, though they predict no word themselves. One likely reason is a pattern found in larger models. Softmax makes every row of weights sum to one, so a head that finds nothing useful at a position still has to put its weight somewhere, and Xiao and colleagues found that language models put large weights on the first tokens of a text whatever they are, calling them **attention sinks** ([Xiao et al., 2024](https://arxiv.org/abs/2309.17453)). In the store's model, `<s>` always comes first and `<sep>` is in every text, so both could serve; `<sep>` also marks where the description starts, which is useful in itself. This example can't tell the two apart.

**Working rule:** Measure how far back a trained model attends, as here, before deciding how long its context needs to be, and compare with an even spread so the number means something. Report the weight on markers separately, so marker weight doesn't look like long-range attention, and keep the first tokens when you cut a model's context to save space.

## What goes wrong in production {#attention-in-production}

Attention is the part of a language model whose cost grows fastest with text length, and the part most often misread:

- **Cost grows with the square of the length.** Every position scores every earlier one, so a text twice as long costs four times as much attention. Set a maximum length, as the store's model does at 160 tokens, and check how many of your texts the limit cuts.
- **A wrong mask fails silently.** A model that can see the future can reach a low training loss and still be useless for generating text. Test that the weight on later positions is zero, and that changing a later token leaves earlier outputs alone, in the training code and the generation code.
- **Attention weights aren't explanations.** A high weight says where a head drew its average from, not why the model predicted what it did. In the same model, very different attention weights can give the same prediction ([Jain and Wallace, 2019](https://aclanthology.org/N19-1357/), on recurrent and convolutional classifiers). Use weights to form hypotheses, and test them by changing the input, as this chapter did with the product's name.
- **Marker weight looks like importance.** Heavy weight on the first token or a separator may mean a head has nothing to do there. Don't remove those tokens, and don't read their weight as meaning.
- **Softmax overflows without care.** Subtract each row's largest score before exponentiating, as `lib.transformer.softmax` does. Make sure every row keeps at least one unmasked position, or the row becomes NaN: a causal mask always leaves each position itself, but a mask that hides padding can hide a whole row.

## What this chapter decided {#attention-decisions}

- **The book's models use causal, scaled, multi-head attention,** as Vaswani et al. defined it: scores divided by the square root of the size of each head's queries and keys, minus infinity on every later position before softmax, and heads that each work in a share of the numbers, mixed by an output projection.
- **The store's model has 4 layers of 4 heads, each head 32 numbers wide,** trained once in `recordings/transformer.py` on names and descriptions joined by a `<sep>` marker, and recomputed in NumPy by `lib.transformer`.
- **Claims about what a model uses are tested by changing its input.** Attention weights suggest hypotheses; changing the product's name showed that the model copies `cover` from it.
- **Trained heads are described by measured averages over many texts,** compared with an even spread: the weight on the previous token, the weight on tokens 4 or more back, and the weight on markers, counted separately.
- **On the store's descriptions, attention reaches well past [chapter 5](#a-neural-language-model)'s window.** Description tokens put 0.46 of their attention on tokens 4 or more back, and the model copies from the name, which a fixed window can't.
- **Attention needs explicit position information.** A weighted average ignores order, and the causal mask restores only a little of it, so [chapter 7](#the-transformer-block) adds rotary positions, as the store's model does inside every head.
