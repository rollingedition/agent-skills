---
title: "Language Models from the Ground Up"
chapter: "The transformer block"
chapter_id: the-transformer-block
book: language-models-from-the-ground-up
edition: 2026.11.11
verified: 2026-11-13
edition_code: 3Y9C-0N1E
canonical: https://rollingedition.com/language-models-from-the-ground-up/the-transformer-block
license: CC BY 4.0
attribution: "“The transformer block,” chapter 7 of Language Models from the Ground Up, Edition 2026.11.11, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/the-transformer-block. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# The transformer block

By the end of this chapter you can assemble a transformer block from its parts, joined by residual connections: attention, normalization, a gated feed-forward layer and position information. You can then stack blocks into a complete language model. You'll check each part on the store's trained model, check the whole model against PyTorch's own implementations, measure what each block and each detail contributes, and count where the parameters go.

[Chapter 6](#attention) built attention: each position looks back at earlier ones and takes a weighted average of what it finds. Attention alone isn't a language model, and the store, an online furniture and home-goods shop, needs more than attention. It moves information between positions but transforms little of it, and it has almost no sense of word order. Layers of it stacked directly also degrade: without the other parts of a block, the output of pure attention tends towards the same vector at every position, faster with every layer ([Dong et al., 2021](https://arxiv.org/abs/2103.03404)). The **transformer block** adds the parts that fix those problems around attention ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762)).

This chapter builds the block in the form the LLaMA models popularized: normalization of each part's input with RMSNorm, a gated feed-forward layer and rotary position embeddings in every layer ([Touvron et al., 2023](https://arxiv.org/abs/2302.13971), section 2.2). SmolLM2, whose tokenizer [chapter 2](#read-an-open-tokenizer) read, is built the same way. Its 360-million-parameter model has 960 dimensions, 32 layers and 15 heads, and differs from the store's model in two details covered below: its heads share keys and values, and its rotary positions turn more slowly ([configuration](https://huggingface.co/HuggingFaceTB/SmolLM2-360M/blob/f8027fd0eaeea54caa13c31d31b9fdc459c38b49/config.json)).

The store's model, trained on the store's product text, is 4 of these blocks between an embedding table and an output layer, and [chapter 6](#read-trained-heads) read its heads. This book calls each block a layer of the model. At every position, each block does two things in order:

1. normalize the vector, run attention, and add the result back to the vector;
2. normalize again, run a feed-forward layer, and add that result back too.

## Add each part's output to a residual stream {#add-to-the-residual-stream}

In [chapter 5](#a-neural-language-model)'s [window model](#predict-from-a-window), each layer replaced its input: the hidden layer's output was all the output layer saw. A transformer block adds to its input instead. Each part computes something from the current vector and adds its output to it: x ← x + attention(x), then x ← x + feed-forward(x). That's a **residual connection**. It comes from image models, where very deep stacks of layers trained well only once each layer added to its input instead of replacing it ([He et al., 2016](https://arxiv.org/abs/1512.03385)).

Two consequences follow. With the additions, the signal can pass "directly from one block to any other block", forwards and, as [gradients](#compute-gradients), backwards, so a deep stack trains far more reliably than it would without them ([He et al., 2016b](https://arxiv.org/abs/1603.05027)). And every position's vector becomes a shared workspace that each part reads from and writes to: the token's embedding goes in at the bottom, each part adds what it computes, and the output layer reads the sum at the top. Elhage and colleagues call this running sum the **residual stream** ([Elhage et al., 2021](https://transformer-circuits.pub/2021/framework/index.html)).

Run the store's model on one validation product and, at every layer, measure the length of what attention adds, of what the feed-forward layer adds, and of the vectors after both additions, averaged over positions. A vector's length here is the square root of the sum of its squared numbers:

Example `residual-stream` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Runs the store's model on one validation product, one block at a time, and prints how much attention and the
feed-forward layer add to the residual stream at each layer. The prose's point rests on the two lengths printed
first and last: the vectors entering layer 1 and leaving the last layer."""
import numpy as np

from lib import transformer
from lib.products import product_texts

weights, _, manifest = transformer.load()
ids, sep = product_texts("validation", 1)[0]          # the first validation product; sep, its <sep> position, isn't needed here
x = weights["embedding"][np.array(ids)]               # the stream entering block 1: each token's embedding
print("length of the vectors entering layer 1:", f"{np.linalg.norm(x, axis=1).mean():.2f}")
for layer in range(manifest["settings"]["layers"]):
    layer_weights = transformer.layer_weights(layer)
    added_by_attention, _ = transformer.attention(transformer.rms_norm(x, layer_weights["norm1"]), layer_weights, manifest["settings"]["heads"])
    x = x + added_by_attention
    normalized = transformer.rms_norm(x, layer_weights["norm2"])
    added_by_feed_forward = (transformer.silu(normalized @ layer_weights["gate"]) * (normalized @ layer_weights["up"])) @ layer_weights["down"]
    x = x + added_by_feed_forward
    print(f"layer {layer + 1}: attention adds {np.linalg.norm(added_by_attention, axis=1).mean():.2f}, "
          f"feed-forward adds {np.linalg.norm(added_by_feed_forward, axis=1).mean():.2f}, "
          f"vectors now {np.linalg.norm(x, axis=1).mean():.2f}")
print("length of the vectors leaving the last layer:", f"{np.linalg.norm(x, axis=1).mean():.2f}")
print("largest number in the stream:", f"{np.abs(x).max():.1f}")
```

Output:

```text
length of the vectors entering layer 1: 1.17
layer 1: attention adds 2.90, feed-forward adds 3.00, vectors now 4.65
layer 2: attention adds 2.05, feed-forward adds 2.90, vectors now 6.14
layer 3: attention adds 2.26, feed-forward adds 4.12, vectors now 8.46
layer 4: attention adds 4.08, feed-forward adds 6.33, vectors now 13.16
length of the vectors leaving the last layer: 13.16
largest number in the stream: 50.6
```

The stream grows through the layers, because each addition piles onto the last. It goes from an average length of 1.17 entering the first layer to 13.16 leaving the last. Every layer adds to it, and what attention adds is comparable in size to what the feed-forward layer adds, though the feed-forward layer adds more at every layer, and by more in the later ones: both parts do real work at every layer. A layer reading the long vectors near the top would need very differently scaled weights from one reading the short ones at the bottom, unless something rescales what each layer reads; the [next section](#normalize-before-each-part) does.

**Working rule:** Write every block as additions to the residual stream, never as replacements, and keep the stream's width the same through the whole model so the additions line up. When you debug a deep model, measure what each part adds: a part that adds almost nothing is doing almost nothing.

## Normalize before each part {#normalize-before-each-part}

The residual stream grows through the layers, as the [previous section](#add-to-the-residual-stream) measured, so each part should read a rescaled copy of it. **Normalization** rescales a vector to a standard size before a part reads it, so the part's weights work the same whether the stream is short or long. The original transformer normalized after each addition, with **layer normalization**, which subtracts each vector's mean and divides by its standard deviation ([Ba et al., 2016](https://arxiv.org/abs/1607.06450)). Xiong and colleagues showed that normalizing before each part instead trains more stably, because only the copy each part reads is rescaled, never the stream itself ([Xiong et al., 2020](https://arxiv.org/abs/2002.04745)). And **RMSNorm** drops the mean: it divides each vector by its root mean square, the square root of the average of its squared numbers, and multiplies each dimension by a learned gain ([Zhang and Sennrich, 2019](https://arxiv.org/abs/1910.07467)):

RMSNorm(x) = x / √(mean(x²) + ε) · g

where ε is a tiny number, 10⁻⁵ here, that keeps the division safe, and g is the gain, which starts at 1. Zhang and Sennrich found RMSNorm about as accurate as layer normalization, and faster. The store's model uses it before attention, before the feed-forward layer, and once more before the output layer.

Normalize the stream of the same validation product by hand at both ends of the model, entering the first block and leaving the last, with the gain left at 1, and compare every position's vector with `lib.transformer.rms_norm`:

Example `rms-norm-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Normalizes one validation product's residual stream by hand, entering the first block and leaving the last, and
asserts that the result matches the shared module's rms_norm. The prose's point rests on the root mean square before
and after normalizing, and on the largest mean of a position's numbers, which RMSNorm does not remove."""
import numpy as np

from lib import transformer
from lib.products import product_texts

ids, _ = product_texts("validation", 1)[0]            # the first validation product; its <sep> position isn't needed
streams, _ = transformer.run(ids)                      # the residual stream entering block 1 and leaving each block
gain = np.ones(streams[0].shape[1])                    # the learned gain set to 1, to show the normalization alone
for label, x in [("entering block 1", streams[0]), ("leaving the last block", streams[-1])]:
    root_mean_square = np.sqrt((x ** 2).mean(1, keepdims=True) + 1e-5)   # one per position; 1e-5 is the ε
    by_hand = x / root_mean_square * gain
    print(f"root mean square {label}, before:", f"{root_mean_square.mean():.2f}")
    print(f"root mean square {label}, after:", f"{np.sqrt((by_hand ** 2).mean(1)).mean():.2f}")
    assert np.allclose(by_hand, transformer.rms_norm(x, gain), atol=1e-4)   # the library's function, to 4 decimal places
    print(f"same as lib.transformer.rms_norm, {label}:", "yes")
    # layer normalization would subtract the mean first; RMSNorm doesn't, so this mean need not be zero
    print(f"largest mean of a position's numbers after, {label}:", f"{np.abs(by_hand.mean(1)).max():.2f}")
```

Output:

```text
root mean square entering block 1, before: 0.10
root mean square entering block 1, after: 1.00
same as lib.transformer.rms_norm, entering block 1: yes
largest mean of a position's numbers after, entering block 1: 0.23
root mean square leaving the last block, before: 1.16
root mean square leaving the last block, after: 1.00
same as lib.transformer.rms_norm, leaving the last block: yes
largest mean of a position's numbers after, leaving the last block: 0.26
```

Normalizing brings both ends to the same scale. The root mean square averages 0.10 entering the first block and 1.16 leaving the last, and 1.00 at both once normalized; the hand calculation matches the library's at both ends. RMSNorm rescales but doesn't centre: a position's numbers can still average away from zero afterwards, by up to 0.26 here. That's the step it saves over layer normalization.

So though the stream grew many times longer across the layers, every attention and feed-forward layer read vectors of the same scale, times its learned gains.

**Working rule:** Normalize before each part of the block, not after, and normalize the stream once more before the output layer. Use RMSNorm unless you're matching a model that uses layer normalization. When you load another model's weights, check which normalization it uses, where, and with what ε, before anything else: the [mismatched-details example](#measure-mismatched-details) shows what a small mismatch costs.

## Transform each position with a gated feed-forward layer {#transform-each-position}

Attention moves information between positions; the **feed-forward layer** transforms it, at each position separately. It's the same idea as [chapter 5](#a-neural-language-model)'s [hidden layer](#predict-from-a-window): widen the vector, apply a function that isn't a straight line, and narrow the result back to the stream's width. The store's model widens 128 numbers to 352.

The form the LLaMA models use is **gated**. It computes two widened vectors from the input, passes one through a function called SiLU, and multiplies the two number by number, so the first decides how much of the second gets through ([Shazeer, 2020](https://arxiv.org/abs/2002.05202)):

FFN(x) = (SiLU(x W_gate) ⊙ (x W_up)) W_down

where ⊙ multiplies number by number, and SiLU(z) = z · σ(z), with σ the logistic function from [chapter 4](#learn-by-predicting-neighbours). SiLU passes large positive numbers almost unchanged and turns large negative ones to nearly zero, smoothly. Shazeer compared several gated forms with the plain one, at the same number of parameters, and found the gated ones predicted better; this form is called SwiGLU.

What does the gate shut? Compute SiLU at three points, then run the first block's real feed-forward layer on the same validation product and count, at each position, how many of its hidden units the gate nearly shuts:

Example `gated-feed-forward` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Computes SiLU at three points, then runs block 1's feed-forward layer on one validation product and counts the hidden
units its gate nearly shuts at each position. The prose's point rests on the three SiLU values and on that count."""
import numpy as np

from lib import transformer
from lib.products import product_texts

print("silu(-3), silu(0), silu(3):", ", ".join(f"{v:.2f}" for v in transformer.silu(np.array([-3.0, 0.0, 3.0]))))

ids, _ = product_texts("validation", 1)[0]            # the first validation product; its <sep> position isn't needed
heads = transformer.load()[2]["settings"]["heads"]    # load returns (weights, vocabulary, manifest): index 2 is the manifest
first = transformer.layer_weights(0)                   # block 1's weights
x = transformer.load()[0]["embedding"][np.array(ids)]  # index 0 is the weights: the embeddings, the stream entering block 1
attended, _ = transformer.attention(transformer.rms_norm(x, first["norm1"]), first, heads)
normalized = transformer.rms_norm(x + attended, first["norm2"])   # what block 1's feed-forward layer reads
gate = transformer.silu(normalized @ first["gate"])    # how much of each hidden unit to let through
up = normalized @ first["up"]                          # what each hidden unit carries
output = (gate * up) @ first["down"]                   # gated, then projected back to the stream's width
shut = (np.abs(gate) < 0.05).sum(1)                    # per position; 0.05 is the threshold for "nearly shut"
print("hidden units:", gate.shape[1])
print("hidden units nearly shut at a position (gate under 0.05 in size), on average:", f"{shut.mean():.0f}")
print("fewest and most nearly shut at a position:", f"{shut.min()} and {shut.max()}")
print("positions:", len(ids))
print("output shape:", output.shape)
```

Output:

```text
silu(-3), silu(0), silu(3): -0.14, 0.00, 2.86
hidden units: 352
hidden units nearly shut at a position (gate under 0.05 in size), on average: 49
fewest and most nearly shut at a position: 33 and 67
positions: 133
output shape: (133, 128)
```

SiLU of −3, 0 and 3 gives -0.14, 0.00, 2.86: nearly zero for the negative number, nearly unchanged for the positive one.

Which units the gate shuts depends on the input. At a typical position it nearly shuts 49 of the first block's 352 hidden units, and the count ranges between 33 and 67 over the positions. So each position uses its own mix of them. The output has one vector per position at the stream's width again, (133, 128), ready to add.

The feed-forward layers hold most of a block's parameters: in the store's model, three matrices of 128 by 352, against attention's four of 128 by 128. Geva and colleagues found that in trained models these layers work like stores of patterns: each hidden unit responds to particular patterns in the text, and pushes the prediction towards particular next tokens ([Geva et al., 2021](https://arxiv.org/abs/2012.14913)).

**Working rule:** Use a gated feed-forward layer with SiLU. Set its width so its three matrices hold as many parameters as a plain layer four times the stream's width, the original transformer's ratio, 2,048 for 512 ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762), section 3.3): that's about 8/3 times the width. SmolLM2-360M uses exactly 8/3, 2,560 for 960. The store's model rounds 8/3 of its width up to a multiple of 32, a rule of thumb that keeps matrix sizes convenient for hardware. When you load another model, check whether its feed-forward layer is gated, since a gated layer has three matrices where a plain one has two.

## Give attention positions with rotations {#rotary-positions}

A weighted average ignores the order of what it averages, as [chapter 6](#look-back-with-a-weighted-average) showed, so attention gets at most a weak sense of position from the causal mask alone. The original transformer added a vector for each position to each token's embedding ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762), section 3.5). The LLaMA models instead use **rotary position embeddings**, RoPE, which work inside attention, at each layer ([Su et al., 2021](https://arxiv.org/abs/2104.09864); [Touvron et al., 2023](https://arxiv.org/abs/2302.13971), section 2.2). Before scoring, each query and key is rotated by angles that grow with its position. The vector's d numbers are taken in pairs, number i with number i + d/2 in the store's model, and each pair (a, b) is treated as a point on a plane and turned around the origin. At position p, pair i turns by the angle p·θᵢ, where θᵢ = 10000^(−i/(d/2)):

(a, b) → (a cos pθᵢ − b sin pθᵢ, a sin pθᵢ + b cos pθᵢ)

So the first pairs turn fast, a full radian per position, and the last pairs slowly. The line `angles = ...` in `lib.transformer.rope` computes p·θᵢ for every position and pair, and the line after it applies the rotation.

Rotation has two properties that suit attention. It doesn't change a vector's length, so it adds position without distorting content. And if a query at position m is turned by mθᵢ and a key at position n by nθᵢ, their dot product depends only on the difference, (m − n)θᵢ: the score depends on how far apart they are, not on where they sit in the text. A head can learn to look 3 tokens back, and it works the same at the start of a name and deep in a description.

Rotate a random query and key of 32 numbers, the size of the store's heads, for positions 0 to 19, and compare scaled scores, as [chapter 6](#attention) defines them, at three pairs, which tests that:

Example `rope-by-hand` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.11:

```python
"""Rotates one random query and key for each of 20 positions, checks that the rotation keeps their lengths, and scores
three pairs of positions. The prose's point rests on the two scores for pairs 3 apart, which match, and the score for
the pair 6 apart, which doesn't."""
import numpy as np

from lib.transformer import rope

rng = np.random.default_rng(2026)                             # a fixed seed: the same random query and key on every run
size = 32                                                      # 32 numbers: the store's width of 128 split across 4 heads
query, key = rng.normal(0, 1, size), rng.normal(0, 1, size)
positions = 20
rotated_q = rope(np.tile(query, (positions, 1)))              # the same query, rotated for each position 0 to 19
rotated_k = rope(np.tile(key, (positions, 1)))
kept = np.allclose(np.linalg.norm(rotated_q, axis=1), np.linalg.norm(query)) and \
    np.allclose(np.linalg.norm(rotated_k, axis=1), np.linalg.norm(key))   # rotation turns a vector, never changes its length
assert kept
print("length kept by the rotation, for the query and the key:", "yes")
for i, j in [(2, 5), (12, 15), (2, 8)]:                       # (key position, query position): the first two are 3 apart, the third 6
    print(f"score with the key at {i} and the query at {j}:", f"{rotated_q[j] @ rotated_k[i] / np.sqrt(size):.3f}")   # scaled, as chapter 6 defines it
```

Output:

```text
length kept by the rotation, for the query and the key: yes
score with the key at 2 and the query at 5: 0.217
score with the key at 12 and the query at 15: 0.217
score with the key at 2 and the query at 8: -0.765
```

Pairs the same distance apart score the same, wherever they sit. The key at position 2 and the query at 5 score 0.217, and the key at 12 and the query at 15 score 0.217, the same, because both pairs are 3 apart. The key at 2 and the query at 8, 6 apart, score -0.765: the same query and key, scored differently because they're further apart. The rotation keeps both vectors' lengths, which the example asserts.

RoPE has no learned parameters: the angles are fixed, and the model learns queries and keys that use them. The store's model applies it to the queries and keys of every head in every layer, which gives [chapter 6's](#attend-to-the-previous-token) previous-token heads a direct way to find the previous token, alongside the weak signal the mask provides.

**Working rule:** Use rotary position embeddings, applied to queries and keys, never values. When you load another model's weights, check how its RoPE pairs the numbers and what base it uses. Some implementations pair neighbouring numbers; others pair the first half with the second, as `lib.transformer.rope` does and as SmolLM2's configuration states with `"rope_interleaved": false`. SmolLM2 uses a base of 100,000 where the store's model uses 10,000.

## Tie the output layer to the embeddings {#tie-the-output}

With all the parts built, the whole model is short enough to read in one piece. `lib.transformer.block` is one block, exactly as the chapter has described it:

```python
def block(x: np.ndarray, layer_weights: dict[str, np.ndarray], heads: int, positions=rope):
    """One transformer block: attention, then the gated feed-forward layer, each added to the residual stream."""
    attended, weights = attention(rms_norm(x, layer_weights["norm1"]), layer_weights, heads, positions)
    x = x + attended
    normalized = rms_norm(x, layer_weights["norm2"])
    x = x + (silu(normalized @ layer_weights["gate"]) * (normalized @ layer_weights["up"])) @ layer_weights["down"]
    return x, weights
```

`lib.transformer.run` passes each token's embedding through the blocks in turn, and these lines of `lib.transformer.forward` turn the final stream into one logit per token in the vocabulary, the scores [chapter 5](#a-neural-language-model)'s softmax turns into probabilities:

```python
    streams, kept = run(ids, name, positions, skip)
    weights, _, _ = load(name)
    logits = rms_norm(streams[-1], weights["final_norm"]) @ weights["embedding"].T
```

The last line holds one more idea: the output layer reuses the embedding table, turned on its side, instead of learning a matrix of its own. A token's logit is the dot product of the final vector with that token's embedding. Press and Wolf found that this **weight tying** lowers perplexity as well as saving the output layer's parameters ([Press and Wolf, 2017](https://arxiv.org/abs/1608.05859)). SmolLM2 ties them too (`"tie_word_embeddings": true` in its configuration), since for a model of its size a separate output layer would be a large share of the whole. The [parameter count](#count-the-parameters) shows what tying saves in the store's model.

**Working rule:** Tie the output layer to the embeddings in a small model, and check whether a model you load ties them before you look for a separate output matrix. Keep your own forward pass short enough to read whole, as `lib.transformer` is, so that every detail the next sections test is visible.

## Check the model against PyTorch {#check-against-pytorch}

PyTorch trained the store's model once, in `recordings/transformer.py`, as it trained [chapter 5](#a-neural-language-model)'s (see [Train with PyTorch](#train-with-pytorch)), and the script saved PyTorch's own logits for every position of one validation product. The training script uses PyTorch's own RMSNorm, causal attention and SiLU, so comparing them with `lib.transformer` checks the NumPy code against a library's, not against a second copy of itself. RoPE is the exception: PyTorch has no built-in version, so both programs write it out, and the check confirms only that they agree. The [rope-by-hand example](#rotary-positions) checks its properties instead.

To test the whole forward pass, recompute the saved product's logits in NumPy and compare every position with PyTorch's:

Example `transformer-same-as-pytorch` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.11:

```python
"""Recomputes the store's model's logits in NumPy for the validation product the training script saved, and checks every
one against PyTorch's to four decimal places. The prose's point rests on the count of logits compared, and on the
assertion that they all match."""
import numpy as np

from lib import transformer

_, _, manifest = transformer.load()
check = np.load("data/recorded/transformer/check.npz")      # one validation product's ids, and PyTorch's logits

ours = transformer.forward(list(check["ids"]))               # forward takes a list of token ids, not an array
print("PyTorch version:", manifest["torch"])
print("positions compared:", len(check["ids"]))
print("logits compared:", f"{ours.size:,}")
assert np.abs(ours - check["logits"]).max() < 1e-4           # 1e-4 is four decimal places
print("same as PyTorch to 4 decimal places:", "yes")
```

Output:

```text
PyTorch version: 2.14.1+cpu
positions compared: 133
logits compared: 550,886
same as PyTorch to 4 decimal places: yes
```

The NumPy model reproduces all 550,886 of PyTorch's logits, for 133 positions, to four decimal places, with PyTorch 2.14.1+cpu. Because the check covers a whole text, it covers the parts that depend on position, the mask and the rotations, as well as the norms, gates and tied output.

**Working rule:** Check your own forward pass against the training library's outputs on a full text, not a single position. Where the library has its own implementation of a part, train with it, so the check compares two independent implementations; where it doesn't, as with RoPE here, test the part's properties by hand.

## Leave out a block to see what it does {#leave-out-a-block}

The model is checked; now measure what its blocks contribute. Because every block adds to the residual stream, a block can be left out and the model still runs: the stream passes through it unchanged, and the next block reads it as before. That allows a simple experiment, called an **ablation**: remove one part, and measure what the model loses. It shows how much each block contributes to the trained model's predictions, which reading its weights can't.

Which block's removal hurts most? Predict one, then score the names and descriptions of the first 100 validation products, 7,624 predictions in all, with the full model and with each block left out in turn:

Example `skip-a-block` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Scores the names and descriptions of the first 100 validation products with the full model, and with each block left
out in turn, reporting perplexity and the top token's average probability. The prose's point rests on the perplexity
with each block left out, set against the full model's."""
import numpy as np

from lib import transformer
from lib.products import product_texts

layers = transformer.load()[2]["settings"]["layers"]     # load returns (weights, vocabulary, manifest): index 2 is the manifest
texts = [ids for ids, _ in product_texts("validation", 100)]   # the <sep> positions aren't needed: each text is scored whole


def measure(skip=None):
    """Perplexity per token, and the average probability of the top token, with one block left out."""
    surprise, top, count = 0.0, 0.0, 0
    for ids in texts:
        p = transformer.softmax(transformer.forward(ids, skip=skip)[:-1])   # [:-1] drops the last position: nothing follows it
        surprise -= np.log(p[np.arange(len(ids) - 1), ids[1:]]).sum()       # position i predicts token i + 1
        top += p.max(1).sum()
        count += len(ids) - 1
    return np.exp(surprise / count), top / count                             # perplexity: exp of the average surprise per token


print("tokens scored, names and descriptions:", f"{sum(len(ids) - 1 for ids in texts):,}")
for skip in [None] + list(range(layers)):                # None keeps all four blocks: the full model
    label = "all blocks" if skip is None else f"without block {skip + 1}"   # skip counts blocks from 0, so block skip + 1 is left out
    perplexity, top = measure(skip)
    print(f"{label}:", f"{perplexity:,.1f}")
    print(f"{label}, average probability of the top token:", f"{top:.2f}")
```

Output:

```text
tokens scored, names and descriptions: 7,624
all blocks: 24.3
all blocks, average probability of the top token: 0.42
without block 1: 17,896.9
without block 1, average probability of the top token: 0.21
without block 2: 77.8
without block 2, average probability of the top token: 0.29
without block 3: 64.3
without block 3, average probability of the top token: 0.34
without block 4: 77.3
without block 4, average probability of the top token: 0.37
```

Leaving out block 2, 3 or 4 more than doubles the [perplexity](#score-with-perplexity) per token, from 24.3 with all four blocks to 77.8, 64.3 and 77.3: each later block contributes a share of the model's skill, and none is dispensable. This perplexity covers names and descriptions together, so it can't be set beside the [baseline](#the-baseline) of chapter 3 or the [window model](#predict-from-a-window) of chapter 5, which are scored on validation names alone. [Chapter 8](#training-a-small-model) makes that comparison.

Leaving out block 1 fails differently. Perplexity rises to 17,896.9, worse than guessing evenly among all 4,142 tokens, which would score 4,142.

The reason is in what the later blocks expect. They were trained on a stream that block 1 had already written to, and without it they read vectors unlike any they saw in training. Their predictions become less confident, with the top token's average probability falling from 0.42 to 0.21, and they put that probability on the wrong tokens. Block 1 turns raw embeddings into the form everything after it is built on, partly by gathering context from the text so far, as three of [chapter 6's](#read-trained-heads) first-layer heads did. Blocks in a trained model aren't independent modules: each depends on what the earlier ones write.

**Working rule:** To learn what a part of a model does, remove it and measure, rather than inferring from its weights. Expect the first block to matter most, since everything later is built on it; beyond that, measure, because here the second and last blocks mattered about equally, and more than the third. Read a small loss from removing a part with care: the remaining parts were trained alongside it, so the measurement says what the trained model relies on, not what the part could do alone.

## Measure what a mismatched detail costs {#measure-mismatched-details}

Every detail of a block has to match the weights it runs with, and a mismatch doesn't announce itself: the model still produces probabilities. The details most often wrong when loading another model's weights are in RoPE, because implementations differ in how they pair numbers and in their base, as SmolLM2's differs from the store's model's.

One wrong detail of RoPE at a time shows what each costs: score the same 100 validation products with the trained weights, pairing neighbouring numbers instead of halves, a base of 100,000, SmolLM2's, instead of the store's 10,000, and no RoPE at all:

Example `mismatched-details` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Scores the same 100 validation products with the trained weights, changing one detail of RoPE at a time: how it pairs
numbers, its base, and whether it is applied at all. The prose's point rests on each variant's perplexity, printed
beside the trained model's."""
import numpy as np

from lib import transformer
from lib.products import product_texts

texts = [ids for ids, _ in product_texts("validation", 100)]   # the <sep> positions aren't needed: each text is scored whole


def neighbours(x, base=10000.0):
    """RoPE that pairs neighbouring numbers, (0, 1), (2, 3) and so on, instead of the first half with the second."""
    half = x.shape[-1] // 2
    rotated = transformer.rope(np.concatenate([x[..., 0::2], x[..., 1::2]], axis=-1), base)   # even numbers, then odd: rope pairs halves, so these are neighbours
    out = np.empty_like(x)
    out[..., 0::2], out[..., 1::2] = rotated[..., :half], rotated[..., half:]                 # each rotated number back where its dimension was
    return out


for label, positions in [("as trained", transformer.rope),
                         ("RoPE pairing neighbouring numbers", neighbours),
                         ("RoPE with base 100,000", lambda x: transformer.rope(x, base=100000.0)),   # 100,000 is SmolLM2's base
                         ("no RoPE", lambda x: x)]:          # no RoPE: the queries and keys pass through unrotated
    print(f"perplexity, {label}:", f"{transformer.perplexity(texts, positions=positions):,.1f}")
```

Output:

```text
perplexity, as trained: 24.3
perplexity, RoPE pairing neighbouring numbers: 112.2
perplexity, RoPE with base 100,000: 26.4
perplexity, no RoPE: 182.0
```

Two mismatches would be caught by the first sample of generated text. Pairing neighbouring numbers instead of halves raises the perplexity from 24.3 to 112.2, and leaving RoPE out raises it to 182.0.

The base is the dangerous one. At 100,000 the perplexity is 26.4, slightly worse than 24.3, with no error and fluent-looking output, a mistake that could ship.

The other difference from SmolLM2 is **grouped-query attention**: its 15 query heads share 5 sets of keys and values, so its key and value matrices are a third of the size of its query matrix ([Ainslie et al., 2023](https://arxiv.org/abs/2305.13245)). Loading such weights into a model that expects a key and value for every head fails with a shape error, which is the kind of mismatch you want.

**Working rule:** Check another model's configuration against your code, line by line, when you load its weights: normalization and its ε, RoPE's pairing and base, the feed-forward layer's gating, tied outputs, and how many heads share keys and values. Then score text you know against the original implementation's outputs; a small loss with no error is the case to fear.

## Count where the parameters go {#count-the-parameters}

With every part built, count what the model learns, and where. A model's parameters are its capacity to learn, and where they sit says what it spends that capacity on. The trained model's count, by part:

Example `transformer-parameters` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.11:

```python
"""Counts the store's model's parameters by part from its saved weights, and prints its settings. The prose's point
rests on the total, the feed-forward count and the embedding's share of it."""
from lib import transformer

weights, vocabulary, manifest = transformer.load()
settings = manifest["settings"]
# one table serves as input and output, so the embedding is counted once; a weight's group is the last part of its name
groups = {"embedding (shared with the output)": ["embedding"], "attention": ["q", "k", "v", "o"],
          "feed-forward": ["gate", "up", "down"], "normalization": ["norm1", "norm2", "final_norm"]}
for group, parts in groups.items():
    count = sum(v.size for k, v in weights.items() if k.split(".")[-1] in parts)   # a weight's name ends in its part: layer3.q is attention's q
    print(f"{group}:", f"{count:,}")
print("total:", f"{sum(v.size for v in weights.values()):,}")
print("embedding's share of the total:", f"{weights['embedding'].size / sum(v.size for v in weights.values()):.0%}")
print("layers:", settings["layers"])
print("width:", settings["dimensions"])                  # the width of the residual stream, which the manifest calls dimensions
print("heads:", settings["heads"])
print("feed-forward width:", settings["feed_forward"])
print("longest text, in tokens:", settings["longest"])  # longer texts were cut to this many tokens
print("vocabulary:", f"{len(vocabulary):,}")             # the store tokenizer's tokens, plus the four markers
```

Output:

```text
embedding (shared with the output): 530,176
attention: 262,144
feed-forward: 540,672
normalization: 1,152
total: 1,334,144
embedding's share of the total: 40%
layers: 4
width: 128
heads: 4
feed-forward width: 352
longest text, in tokens: 160
vocabulary: 4,142
```

The model has 1,334,144 parameters, slightly fewer than the 1,394,732 of [chapter 5](#a-neural-language-model)'s window model. The two are about the same size but spend their parameters differently. The window model put about three quarters of its parameters in its output layer, and could see four tokens back. The transformer puts most of its parameters in its blocks, 540,672 of them in feed-forward layers alone. It shares its embeddings with its output, and can see every earlier token in a text of up to 160 tokens.

The embedding table, shared with the output layer, holds 530,176 parameters, 40% of the total, because it has a row of 128 numbers for each of the 4,142 tokens. Those are the store tokenizer's vocabulary plus four markers: start, separator, end, and padding, which fills out short texts in a training batch. [Chapter 8](#training-a-small-model) explains how the model was trained, and measures it against the baseline.

**Working rule:** Count parameters by part whenever you design or load a model. At small sizes, the embedding table is a large share of the total, so tie it to the output layer, and choose the vocabulary size with that cost in mind, as [chapter 2's](#choose-how-many-merges) choice of merges did.

## What goes wrong in production {#transformer-in-production}

A transformer's parts have to fit together exactly, and most of what goes wrong is a part that almost fits:

- **Mismatched details can fail quietly.** Where the norms go, how RoPE pairs numbers and its base, whether the feed-forward layer is gated and whether the output is tied all have to match the trained weights. Some mismatches give nonsense at once; others, like the RoPE base [measured here](#measure-mismatched-details), cost a little accuracy with no error. Check against reference outputs.
- **Lengths beyond training are untested.** RoPE gives an angle for any position, but a model trained on texts of up to 160 tokens has never learned to use the angles beyond. Treat the training length as the model's limit until you've measured past it.
- **Large values can overflow at reduced precision.** Formats with fewer bits keep the same relative precision at every ordinary magnitude, but float16 can't hold values above 65,504, and in 8-bit formats a few large outliers ruin the precision of every other value ([Dettmers et al., 2022](https://arxiv.org/abs/2208.07339)). The store's model's stream peaks at 50.6 for the product measured here, far from float16's limit; check the largest values in your model's stream before serving it at lower precision.
- **Keep the reference outputs with the weights.** Results depend on the machine, as [chapter 4](#compare-learned-and-counted) explains, so keep the weights, the reference outputs and the exact training script together, and rerun the check after any change to the code or libraries.
- **Every part runs at every position.** The feed-forward layers cost the same at every position, and attention's cost grows with the square of the length, as [chapter 6](#attention-in-production) showed. Measure which dominates for your texts before you optimize either.

## What this chapter decided {#transformer-decisions}

- **The store's transformer uses the LLaMA-style block,** at a toy size: RMSNorm before each part, rotary positions in attention, a gated SiLU feed-forward layer, and an output layer tied to the embeddings. It has 4 layers, a width of 128, 4 heads and a feed-forward width of 352. SmolLM2-360M has the same kinds of parts, larger, with grouped-query attention and a RoPE base of 100,000.
- **The NumPy forward pass in `lib.transformer` is the book's reference,** checked against PyTorch's own RMSNorm, attention and SiLU on every position of a validation product, to four decimal places. Every later example that uses the model runs it.
- **Every block adds to the residual stream, and every part reads a normalized copy of it,** so the stream can grow through the layers while each part sees vectors of a fixed scale.
- **Parts are judged by measuring the model without them, or with them changed.** Leaving out any one block makes the store's model much worse, and leaving out the first makes it useless, so the book treats a trained model's blocks as one system. A wrong RoPE base costs a little and raises no error, so loaded weights are always checked against reference outputs.
- **The model is about the size of [chapter 5](#a-neural-language-model)'s window model, with its parameters spent on the blocks instead of the output layer.** The embedding table, shared with the output, is still 40% of it, so vocabulary size remains a cost the book watches.
