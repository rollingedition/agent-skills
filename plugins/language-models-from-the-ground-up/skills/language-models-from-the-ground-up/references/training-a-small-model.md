---
title: "Language Models from the Ground Up"
chapter: "Training a small model"
chapter_id: training-a-small-model
book: language-models-from-the-ground-up
edition: 2026.11.12
verified: 2026-11-13
edition_code: J2AF-6HWB
canonical: https://rollingedition.com/language-models-from-the-ground-up/training-a-small-model
license: CC BY 4.0
attribution: "“Training a small model,” chapter 8 of Language Models from the Ground Up, Edition 2026.11.12, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/training-a-small-model. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Training a small model

By the end of this chapter you can train a small transformer from start to finish and judge the result. You'll turn texts into batches, update the weights with AdamW, set the step size's schedule, read the training curve, measure the model fairly against the counted baseline, and find out what more width, more text and more training buy at this scale, and find where the model beats counting and where it needs counting beside it.

[Chapter 7](#the-transformer-block) assembled the store's model and used its trained weights to check every part. This chapter asks where those weights came from: one training run, recorded in `recordings/transformer.py`. That run taught the model to predict each next token of the store's catalog: the names and descriptions of the furniture and home goods it sells online. The chapter then measures the model on the two jobs it's for: suggesting the next word of a product name in the search box, and predicting descriptions, where text runs long enough for distant context to matter.

As in [chapter 5](#train-with-pytorch), training ran once, in PyTorch. The examples read what it saved: the weights, the curves and the settings, recorded in the run's manifest. To train it yourself, install `recordings/requirements.txt` in its own environment, which adds PyTorch's CPU build, and run `python recordings/transformer.py` from the book's folder: it writes the same files to `examples/data/recorded/transformer/`, and runs on a laptop's processor.

## Turn products into batches {#turn-products-into-batches}

Training starts by turning the store's catalog into numbers the model can learn from. Each product becomes one text: the start marker, the name, the separator `<sep>`, the description and the end marker, tokenized by the [store's tokenizer](#train-the-store-tokenizer). A text longer than the model's limit is cut. Each training step takes a **batch** of texts at once, so the arithmetic runs on whole matrices, and texts of different lengths are filled out to the longest in the batch with a padding token.

Each text then gives the model one prediction per position. The **inputs** are its tokens without the last, and the **targets** are its tokens without the first, so position i is trained to predict token i + 1. Thanks to the [causal mask](#hide-the-future), one forward pass makes every one of those predictions at once. The loss is averaged over the targets that aren't padding: the padding costs computation but teaches nothing.

Padding is the cost to watch, so build one shuffled epoch's batches as the training script does, and count how much of each batch is padding:

Example `training-batches` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Builds one shuffled epoch of batches the way the training script does, and measures the padding in them.
The prose's point rests on the share of targets that are padding over that epoch."""
import math

import numpy as np

from lib import transformer
from lib.products import product_texts

_, vocabulary, manifest = transformer.load()
settings = manifest["settings"]
pad, end = vocabulary.index(transformer.PAD), vocabulary.index(transformer.END)
texts = [ids for ids, _ in product_texts("train")]
size = settings["batch"]

order = np.random.default_rng(settings["seed"]).permutation(len(texts))   # one shuffled epoch, from the run's seed, so it repeats
padding, targets_seen, shares = 0, 0, []
for start in range(0, len(texts), size):
    batch = [texts[i] for i in order[start:start + size]]                      # this step's texts: the next `size` in the shuffled order
    longest = max(len(ids) for ids in batch)
    padded = np.array([ids + [pad] * (longest - len(ids)) for ids in batch])   # short texts filled out with <pad>
    inputs, targets = padded[:, :-1], padded[:, 1:]                            # each position predicts the next token
    padding, targets_seen = padding + (targets == pad).sum(), targets_seen + targets.size
    shares.append((targets == pad).mean())
    if start == 0:
        first_shape = (inputs.shape, targets.shape)

print("training texts:", f"{len(texts):,}")
print("tokens in them:", f"{sum(len(ids) for ids in texts):,}")
print(f"texts cut at the length limit, {settings['longest']} tokens:", f"{np.mean([ids[-1] != end for ids in texts]):.1%}")   # a cut text lost its end marker
print("texts per batch:", size)
print("one batch's inputs and targets:", *first_shape)
print("share of targets that are padding, over one shuffled epoch:", f"{padding / targets_seen:.0%}")
print("least and most padding in a batch:", f"{min(shares):.0%} and {max(shares):.0%}")
print("steps per epoch:", f"{math.ceil(len(texts) / size):,}")   # the last, partly filled batch is a step too
print("epochs in the recorded run:", settings["epochs"])
print("steps in the recorded run:", f"{manifest['steps']:,}")
```

Output:

```text
training texts: 34,252
tokens in them: 2,843,222
texts cut at the length limit, 160 tokens: 1.0%
texts per batch: 32
one batch's inputs and targets: (32, 151) (32, 151)
share of targets that are padding, over one shuffled epoch: 46%
least and most padding in a batch: 30% and 59%
steps per epoch: 1,071
epochs in the recorded run: 16
steps in the recorded run: 17,136
```

The training split holds 34,252 texts and 2,843,222 tokens. That count includes each text's start, separator and end markers, which [chapter 4's count](#describe-by-neighbours) of 2,744,320 tokens leaves out, and excludes what the length limit cuts; only 1.0% of the texts are cut.

Each batch holds 32 texts, so one pass over the training texts, an **epoch**, takes 1,071 steps, and the recorded run took 17,136 steps over 16 epochs.

Over one shuffled epoch, 46% of the targets are padding, between 30% and 59% depending on the batch, because one long description sets the width of every shorter text beside it. Each batch is a rectangle: one row per text, one column per position.

Padding on that scale is waste: nearly half of each forward pass computes predictions the loss then ignores. It doesn't change what the model learns, since padding never counts, but it nearly doubles the cost of each step. Krell and colleagues found padding up to half of all tokens in common datasets, and proposed **packing**, several texts end to end in each row, with the attention kept from crossing between them ([Krell et al., 2021](https://arxiv.org/abs/2107.02027)). Putting texts of similar length in the same batch reduces padding too.

**Working rule:** Build batches as inputs and shifted targets, mask padding out of the loss, and shuffle the texts each epoch with a fixed seed, so the run can be repeated. Measure the share of padding in your batches; if it's large, pack texts or group them by length before you buy a bigger machine.

## Update with AdamW and clipped gradients {#update-with-adamw}

With batches in hand, each step is the loop of [chapter 5](#take-gradient-descent-steps): forward pass, loss, [gradients](#compute-gradients), update. These lines of `recordings/transformer.py` are the whole of it, run once per batch:

```python
        ids = pad([train[i] for i in order[start:start + SETTINGS["batch"]]])
        logits = model(ids[:, :-1])
        loss = torch.nn.functional.cross_entropy(logits.transpose(1, 2), ids[:, 1:], ignore_index=index[PAD])
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
```

The first three lines are the [previous section](#turn-products-into-batches): a padded batch, inputs without the last token, and a loss over the shifted targets that ignores padding. Two lines differ from [chapter 5](#a-neural-language-model).

The optimizer is **AdamW**, the Adam of [chapter 5](#train-with-pytorch) with **weight decay** applied apart from the gradient: at every step, each weight is also reduced by its value times the step size times a decay factor, here 0.1 ([PyTorch's AdamW](https://docs.pytorch.org/docs/2.14/generated/torch.optim.AdamW.html)). Loshchilov and Hutter showed that applying the decay this way works better with Adam than adding it to the loss ([Loshchilov and Hutter, 2019](https://arxiv.org/abs/1711.05101)). Decay is a form of [regularization](#stop-at-the-best-epoch), which chapter 5's window model lacked: it pulls every weight towards zero, so a weight stays large only while the training text keeps pushing it there.

The script also **clips** the gradients: when their combined length, measured as if every gradient were one long vector, exceeds 1.0, it scales them all down to that length ([PyTorch's clip_grad_norm_](https://docs.pytorch.org/docs/2.14/generated/torch.nn.utils.clip_grad_norm_.html)). One unusual batch then can't throw the weights far off. Pascanu and colleagues proposed clipping for exactly that: rare, very large gradients that would otherwise undo much of what training had learned ([Pascanu et al., 2013](https://arxiv.org/abs/1211.5063)).

**Working rule:** Use AdamW with a modest weight decay, and clip gradients by their combined length. Keep the training step short enough to read whole, so that every choice in it is visible: what the loss ignores, what the optimizer decays and what gets clipped.

## Warm up, then decay the step size {#warm-up-then-decay}

The last line of the loop, `scheduler.step()`, changes the step size after every batch, following a **schedule**. For the first 200 steps, it rises in a straight line from nearly zero to its peak, 0.003: a **warm-up**, as the transformer paper's schedule had ([Vaswani et al., 2017](https://arxiv.org/abs/1706.03762), section 5.3). In Adam's first steps, its running average of squared gradients rests on only a few batches, so its step sizes vary widely; Liu and colleagues showed that warm-up works by reducing that variance ([Liu et al., 2020](https://arxiv.org/abs/1908.03265)). After the warm-up, the step size falls along half a cosine curve, to a tenth of the peak by the last step ([Loshchilov and Hutter, 2017](https://arxiv.org/abs/1608.03983)). Large steps early cover ground; small steps late let the weights settle into a low point instead of bouncing around it. In symbols, after the warm-up:

rate = peak × (0.1 + 0.9 × ½ (1 + cos(π × progress)))

where progress runs from 0 at the end of the warm-up to 1 at the last step.

Whether the schedule matches the run's is checkable: compute it by hand from the recorded settings, and set it against the step sizes the training script saved every tenth step:

Example `learning-rate-schedule` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.12:

```python
"""Computes the warm-up and cosine schedule by hand from the recorded settings, and checks it against the step sizes
the training script saved. The prose relies on the check: the assert fails the run if the two ever differ."""
import json
import math

from lib import transformer

_, _, manifest = transformer.load()
settings, total = manifest["settings"], manifest["steps"]
recorded_rates = json.loads((transformer.RECORDED / "curves.json").read_text())["rates"]   # every 10th step's, after the scheduler's step


def rate(step):
    """Warm up linearly to the peak, then follow half a cosine down to a tenth of it."""
    if step < settings["warmup_steps"]:
        return settings["peak_rate"] * (step + 1) / settings["warmup_steps"]   # steps count from 0, so step 0 is already a share of the peak
    progress = (step - settings["warmup_steps"]) / (total - settings["warmup_steps"])   # 0 at the warm-up's end, 1 at the last step
    return settings["peak_rate"] * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * progress)))


print("warm-up steps:", settings["warmup_steps"])
print("peak step size:", settings["peak_rate"])
print("weight decay:", settings["weight_decay"])
for step in [0, settings["warmup_steps"] // 2, settings["warmup_steps"], total // 2, total - 1]:
    print(f"step size at step {step:,}:", f"{rate(step):.2e}")
gap = max(abs(recorded - rate(10 * i + 1)) for i, recorded in enumerate(recorded_rates))   # recorded_rates[i] was saved after step 10 * i, so it is the size used at step 10 * i + 1
assert gap < 1e-9                   # every saved step size matches the hand calculation, to a billionth
print("same as the recorded step sizes:", "yes")
```

Output:

```text
warm-up steps: 200
peak step size: 0.003
weight decay: 0.1
step size at step 0: 1.50e-05
step size at step 100: 1.51e-03
step size at step 200: 3.00e-03
step size at step 8,568: 1.68e-03
step size at step 17,135: 3.00e-04
same as the recorded step sizes: yes
```

The hand calculation matches every saved step size. The step size starts at 1.50e-05, peaks at 3.00e-03 at the warm-up's end, and is 3.00e-04 at the last step, a tenth of that peak.

The decay matters. The comparison run trained for four epochs at the same width, with the same seed and the same batches, so its schedule finished its decay at step 4,284, and at that step it scored 27.6 on the validation names. The recorded run was still near its peak step size at that step, and scored 32.6. Same data, same steps: the difference is the decay.

**Working rule:** Warm the step size up over the first few hundred steps, then decay it, and match the schedule's length to the run's. Save the step size as training runs, as the training script does, and check it against the schedule you meant: a schedule bug looks like a training problem, and is far easier to find this way.

## Read the training curve {#read-the-training-curve}

With its batches, updates and schedule set, the store's model trained for 16 epochs, and the script measured it on the validation split after each one, on names and descriptions separately. It kept the weights from the epoch with the lowest validation loss on names and descriptions added together, as [chapter 5](#stop-at-the-best-epoch) kept its best epoch.

Read as [perplexity](#score-with-perplexity) per token, the recorded curves, epoch by epoch, look like this:

Example `transformer-training-curve` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.12:

```python
"""Prints the recorded run's perplexity for each epoch, then the epoch kept and its validation perplexities.
The prose's point rests on the two validation columns and the epoch kept."""
import json
import math

from lib import transformer

_, _, manifest = transformer.load()
curves = json.loads((transformer.RECORDED / "curves.json").read_text())["epochs"]

print("perplexity per token; training mixes names and descriptions, as the training text does")
print("epoch  training  validation names  validation descriptions")
for curve in curves:
    print(f"{curve['epoch']:>5}  {math.exp(curve['train_loss']):>8.1f}  {math.exp(curve['validation_name_loss']):>16.1f}"
          f"  {math.exp(curve['validation_description_loss']):>23.1f}")
kept = next(curve for curve in curves if curve["epoch"] == manifest["kept_epoch"])   # the epoch whose weights were kept
print("epoch kept, the lowest name and description losses added together:", manifest["kept_epoch"])
print("validation perplexity on names, kept epoch:", f"{math.exp(kept['validation_name_loss']):.1f}")
print("validation perplexity on descriptions, kept epoch:", f"{math.exp(kept['validation_description_loss']):.1f}")
print("validation perplexity on names, epoch 4:", f"{math.exp(curves[3]['validation_name_loss']):.1f}")   # the list starts at epoch 1, so index 3 is epoch 4
```

Output:

```text
perplexity per token; training mixes names and descriptions, as the training text does
epoch  training  validation names  validation descriptions
    1     131.4              50.5                     50.4
    2      41.4              38.8                     36.2
    3      32.8              34.5                     31.5
    4      29.0              32.6                     29.3
    5      26.6              30.9                     27.8
    6      24.8              30.2                     26.4
    7      23.3              28.9                     25.0
    8      21.8              28.1                     23.9
    9      20.5              27.1                     22.9
   10      19.2              26.5                     22.2
   11      17.9              25.8                     21.6
   12      16.8              25.1                     20.8
   13      15.8              24.6                     20.4
   14      14.9              24.2                     20.0
   15      14.2              24.0                     19.9
   16      13.8              24.1                     19.9
epoch kept, the lowest name and description losses added together: 15
validation perplexity on names, kept epoch: 24.0
validation perplexity on descriptions, kept epoch: 19.9
validation perplexity on names, epoch 4: 32.6
```

Validation perplexity falls until epoch 15, the epoch kept, and then levels off: the last epoch is no better. At the kept epoch it is 24.0 on names and 19.9 on descriptions. As in [chapter 5](#a-neural-language-model), epoch 1's training perplexity is above validation, because it averages over the epoch's first batches, when the model knew nothing. The training column mixes names and descriptions, as the training text does, so it shows the trend, not a number to set beside either validation column.

[Chapter 5](#a-neural-language-model)'s window model stopped improving after epoch 5; this model kept improving for far longer. The two runs differ in several ways that could explain it. This model learned from names and descriptions, 2,843,222 tokens, against the window model's 337,071 from names alone; its step size decays; it has weight decay; and attention applies the same weights at every position. The run doesn't separate those reasons. What it does show is the gap between training and validation, which grows every epoch: by the end, the model predicts its training texts far better than new ones, so it's starting to memorize.

Descriptions score lower than names, but that doesn't mean the model is better at descriptions. Each kind of text has its own predictability: descriptions repeat phrases from their templates and their names, and names pack a new product into a few words. Perplexities compare models on the same text, never texts with each other.

**Working rule:** Record validation loss per epoch on each kind of text you care about, and keep the best epoch's weights. Read the gap between training and validation as the warning, not the training loss alone. Never compare perplexities across different kinds of text.

## Compare with the baseline on names {#compare-on-names}

With the training read, the result can be measured. The strongest counted model for names is the [4-gram baseline](#the-baseline) trained on the training names. It scores 23.1 on the validation names, the book's yardstick: every model since [chapter 3](#counting-further-back) has been scored on them. The same 4-gram trained on whole texts, names and descriptions, scores 27.7 on them, because descriptions dilute its counts of how names run.

The comparison has to count the same predictions. The 4-gram predicts each name's tokens and then its end marker; the transformer predicts each name's tokens and then `<sep>`, which plays the same part, since it marks where the name ends. A name needs nothing after it, so the transformer reads the name alone. Both models score the same 46,704 predictions.

Make a guess first: can the transformer alone beat the counted baseline that chapter 5's window model couldn't? Then score both models, and mixtures of the two, the way [chapter 5](#mix-with-the-counts) did:

Example `transformer-on-names` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Scores every validation name, its end included, with the 4-gram baseline and with the transformer, then mixes them
at several shares. The prose's point rests on the share 0.5 line, the lowest of the five."""
import numpy as np

from lib import transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}   # each token's id in the vocabulary, which is its column in the model's output
counted = KneserNey(name_tokens("train"), 4)                     # chapter 3's baseline, trained on names
from_counts, from_transformer = [], []
for name in name_tokens("validation"):
    ids = [index[transformer.START]] + [index[token] for token in name] + [index[transformer.SEP]]   # the name as the model reads it
    probabilities = transformer.softmax(transformer.forward(ids)[:-1])   # the last position predicts past <sep>, which a name never needs
    from_transformer += list(probabilities[np.arange(len(ids) - 1), ids[1:]])   # each position's probability for the token after it
    from_counts += [counted.probability(context, token) for context, token in ngrams(padded(name, 4), 4)]   # then </s>
from_counts, from_transformer = np.array(from_counts), np.array(from_transformer)

print("validation tokens scored, each name's end included:", f"{len(from_counts):,}")
for share in [0.0, 0.3, 0.5, 0.7, 1.0]:
    mixed = (1 - share) * from_counts + share * from_transformer
    print(f"validation perplexity on names, transformer share {share:.1f}:", f"{np.exp(-np.log(mixed).mean()):.1f}")
```

Output:

```text
validation tokens scored, each name's end included: 46,704
validation perplexity on names, transformer share 0.0: 23.1
validation perplexity on names, transformer share 0.3: 18.7
validation perplexity on names, transformer share 0.5: 18.4
validation perplexity on names, transformer share 0.7: 18.8
validation perplexity on names, transformer share 1.0: 24.0
```

Mixed half and half, the transformer and the counts score 18.4 on names, the best of any model in this book on names. Alone, the transformer scores 24.0, slightly worse than the baseline's 23.1.

The transformer alone is far better than [chapter 5's](#a-neural-language-model) window model, which scored 36.4, and the mix beats chapter 5's best mix, 21.9.

So on names, counting is still hard to beat alone, for the reason [chapter 5](#a-neural-language-model) gave: names are short and formulaic, and three tokens of context see most of what a name holds. But the transformer is wrong in different places from the counts, and the mix gains from both. The share was chosen on the validation names, so the gain is slightly optimistic; the test names stay untouched for the book's final comparison.

**Working rule:** Compare a new model with the strongest baseline you can build on exactly the same predictions, including how each marks the end of a text. When a learned model and a counted one are close, mix them, and choose the share on held-out text.

## Compare on descriptions {#compare-on-descriptions}

The [names comparison](#compare-on-names) favours counting, because names are short. Descriptions run many times longer, and [chapter 6](#test-what-the-model-copies) showed the model copying from the name many tokens back, so this is where its longer reach should pay. A fair baseline here is a 4-gram trained on the same texts the transformer learned from, the name, `<sep>` and description joined, and scored on the same tokens: each description's tokens and its end, with the same text before them.

Put the longer reach to the test on descriptions: fit the 4-gram on every training text, then score it, the transformer and an even mix on the descriptions of the first 500 validation products, leaving out texts cut at the length limit and products with no description. It also splits the tokens, as [chapter 5](#compare-with-the-baseline) did, by whether their three-token context occurs in the training texts:

Example `transformer-on-descriptions` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Scores the descriptions of the first 500 validation products with a 4-gram trained on whole texts, with the transformer,
and with their even mix, then splits the tokens by whether their context was seen in training. The prose's point rests on the
4-gram baseline and transformer lines, the half-and-half line and the unseen-context lines."""
import numpy as np

from lib import transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded
from lib.products import product_texts

_, vocabulary, _ = transformer.load()
end = vocabulary.index(transformer.END)
as_tokens = lambda ids: [vocabulary[i] for i in ids[1:] if i != end]          # padded() adds its own <s> and </s>
counted = KneserNey([as_tokens(ids) for ids, _ in product_texts("train")], 4)   # whole texts: name, <sep>, description

from_counts, from_transformer, seen, products = [], [], [], 0
for ids, sep in product_texts("validation", 500):
    if ids[-1] != end or sep == len(ids) - 2:
        continue                                          # cut at the length limit, or no description
    pairs = list(ngrams(padded(as_tokens(ids), 4), 4))[sep:]    # from <sep> on: the description's tokens, then </s>
    from_counts += [counted.probability(context, token) for context, token in pairs]
    seen += [context in counted.totals[4] for context, _ in pairs]   # was this 3-token context in the training texts?
    probabilities = transformer.softmax(transformer.forward(ids)[sep:-1])   # from <sep> on: each position predicts the next token
    from_transformer += list(probabilities[np.arange(len(probabilities)), ids[sep + 1:]])   # the description starts after <sep>, at sep + 1
    products += 1
from_counts, from_transformer, seen = np.array(from_counts), np.array(from_transformer), np.array(seen)
perplexity = lambda p: f"{np.exp(-np.log(p).mean()):.1f}"

print("products scored:", products)
print("description tokens scored:", f"{len(from_counts):,}")
mixed = (from_counts + from_transformer) / 2
for label, p in [("4-gram baseline", from_counts), ("transformer", from_transformer), ("half and half", mixed)]:
    print(f"{label}, validation perplexity on descriptions:", perplexity(p))
print("description tokens whose 3-token context is in the training texts:", f"{seen.mean():.0%}")
for part, where in [("seen", seen), ("unseen", ~seen)]:
    print(f"4-gram, {part} contexts:", perplexity(from_counts[where]))
    print(f"transformer, {part} contexts:", perplexity(from_transformer[where]))

names = [list(ngrams(padded(name + [transformer.SEP], 4), 4))[:-1] for name in name_tokens("validation")]   # to <sep>: the last pair predicts </s>, which a name stops short of
on_names = [counted.probability(context, token) for pairs in names for context, token in pairs]
print("this 4-gram, trained on whole texts, validation perplexity on names:", perplexity(np.array(on_names)))
```

Output:

```text
products scored: 446
description tokens scored: 35,651
4-gram baseline, validation perplexity on descriptions: 22.5
transformer, validation perplexity on descriptions: 20.1
half and half, validation perplexity on descriptions: 14.7
description tokens whose 3-token context is in the training texts: 74%
4-gram, seen contexts: 16.3
transformer, seen contexts: 16.6
4-gram, unseen contexts: 57.6
transformer, unseen contexts: 35.0
this 4-gram, trained on whole texts, validation perplexity on names: 27.7
```

On descriptions, the transformer beats counting alone: it scores 20.1 on the 35,651 description tokens of 446 products, against the 4-gram's 22.5. It is the first learned model in this book to beat a counted model of the same text on its own.

The split shows where they differ. 74% of the tokens have a context the training texts contain, and on those the two models tie: 16.3 for the 4-gram, 16.6 for the transformer. On the rest, the transformer scores 35.0 where the 4-gram scores 57.6. Descriptions are formulaic enough that counts do as well as the transformer wherever they have seen the context; where they haven't, the transformer reads further back and relates what it sees to what it learned, and the counts can only back off.

That's also why the mix works so well. Half and half, the two score 14.7, far below either alone: on any one token, at least one of the two is often confident and right, and the even mix keeps half of that probability, enough to avoid the worst surprises of each.

**Working rule:** Measure a model on the kind of text it will predict, against a baseline that sees the same text, and expect the ranking to change from one kind of text to another. Split the comparison by seen and unseen contexts to see where each model wins. Try a mix before concluding that either model is enough: the mix gained more than any change to either model that this chapter measured.

## What width, data and steps buy {#what-width-data-and-steps-buy}

The recorded model is one choice among many: 128 numbers wide, trained on all the training text for 16 epochs. Studies of much larger models found that loss falls smoothly as models get bigger, see more text and train longer, and that bigger models learn more from each token they see ([Kaplan et al., 2020](https://arxiv.org/abs/2001.08361)). For a fixed budget of computation, Hoffmann and colleagues found that model size and training text should grow together ([Hoffmann et al., 2022](https://arxiv.org/abs/2203.15556)). And Muennighoff and colleagues found that repeating the same text for up to about four epochs is nearly as good as new text, with less gained from each further repetition ([Muennighoff et al., 2023](https://arxiv.org/abs/2305.16264)). Whether any of that holds at this toy scale is something to measure, not assume.

So the training script recorded seven cheaper runs beside the main one, each changing one thing:

- three widths, 64, 128 and 256, each trained for four epochs, with every head kept 32 numbers wide;
- random quarters and halves of the training products, each trained for four epochs;
- the same quarter and half trained for as many steps as all the data's four epochs, by repeating them more often.

Which change buys the most? Read the eight runs side by side, each one's size, steps and perplexities at its best and last epochs:

Example `width-data-and-steps` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.12:

```python
"""Reads eight recorded runs and prints each one's parameters, steps, best epoch, and validation perplexities at its best
and last epochs. The prose's point rests on the perplexity-on-names lines."""
import json
import math

from lib import transformer

runs = [("width 64, 4 epochs", "transformer-width-64"), ("width 128, 4 epochs", "transformer-width-128"),
        ("width 256, 4 epochs", "transformer-width-256"), ("width 128, 16 epochs", "transformer"),
        ("a quarter of the data, 4 epochs", "transformer-data-25"), ("half the data, 4 epochs", "transformer-data-50"),
        ("a quarter of the data, 16 epochs", "transformer-data-25-same-steps"),
        ("half the data, 8 epochs", "transformer-data-50-same-steps")]

for label, folder in runs:
    run = transformer.RECORDED.parent / folder   # every run sits in the folder beside the main run's
    manifest = json.loads((run / "manifest.json").read_text())
    curves = json.loads((run / "curves.json").read_text())["epochs"]
    best = min(curves, key=lambda curve: curve["validation_name_loss"] + curve["validation_description_loss"])   # the epoch the script kept
    print(f"{label}, parameters:", f"{manifest['parameters']:,}")
    print(f"{label}, steps:", f"{manifest['steps']:,}")
    print(f"{label}, best epoch:", best["epoch"])
    print(f"{label}, perplexity on names:", f"{math.exp(best['validation_name_loss']):.1f}")
    print(f"{label}, perplexity on descriptions:", f"{math.exp(best['validation_description_loss']):.1f}")
    print(f"{label}, perplexity on names, last epoch:", f"{math.exp(curves[-1]['validation_name_loss']):.1f}")   # the last epoch trained, not the one kept
    print(f"{label}, perplexity on descriptions, last epoch:", f"{math.exp(curves[-1]['validation_description_loss']):.1f}")
```

Output:

```text
width 64, 4 epochs, parameters: 478,656
width 64, 4 epochs, steps: 4,284
width 64, 4 epochs, best epoch: 4
width 64, 4 epochs, perplexity on names: 36.9
width 64, 4 epochs, perplexity on descriptions: 35.9
width 64, 4 epochs, perplexity on names, last epoch: 36.9
width 64, 4 epochs, perplexity on descriptions, last epoch: 35.9
width 128, 4 epochs, parameters: 1,334,144
width 128, 4 epochs, steps: 4,284
width 128, 4 epochs, best epoch: 4
width 128, 4 epochs, perplexity on names: 27.6
width 128, 4 epochs, perplexity on descriptions: 24.7
width 128, 4 epochs, perplexity on names, last epoch: 27.6
width 128, 4 epochs, perplexity on descriptions, last epoch: 24.7
width 256, 4 epochs, parameters: 4,273,920
width 256, 4 epochs, steps: 4,284
width 256, 4 epochs, best epoch: 4
width 256, 4 epochs, perplexity on names: 23.5
width 256, 4 epochs, perplexity on descriptions: 19.5
width 256, 4 epochs, perplexity on names, last epoch: 23.5
width 256, 4 epochs, perplexity on descriptions, last epoch: 19.5
width 128, 16 epochs, parameters: 1,334,144
width 128, 16 epochs, steps: 17,136
width 128, 16 epochs, best epoch: 15
width 128, 16 epochs, perplexity on names: 24.0
width 128, 16 epochs, perplexity on descriptions: 19.9
width 128, 16 epochs, perplexity on names, last epoch: 24.1
width 128, 16 epochs, perplexity on descriptions, last epoch: 19.9
a quarter of the data, 4 epochs, parameters: 1,334,144
a quarter of the data, 4 epochs, steps: 1,072
a quarter of the data, 4 epochs, best epoch: 4
a quarter of the data, 4 epochs, perplexity on names: 51.9
a quarter of the data, 4 epochs, perplexity on descriptions: 54.1
a quarter of the data, 4 epochs, perplexity on names, last epoch: 51.9
a quarter of the data, 4 epochs, perplexity on descriptions, last epoch: 54.1
half the data, 4 epochs, parameters: 1,334,144
half the data, 4 epochs, steps: 2,144
half the data, 4 epochs, best epoch: 4
half the data, 4 epochs, perplexity on names: 35.2
half the data, 4 epochs, perplexity on descriptions: 34.8
half the data, 4 epochs, perplexity on names, last epoch: 35.2
half the data, 4 epochs, perplexity on descriptions, last epoch: 34.8
a quarter of the data, 16 epochs, parameters: 1,334,144
a quarter of the data, 16 epochs, steps: 4,288
a quarter of the data, 16 epochs, best epoch: 11
a quarter of the data, 16 epochs, perplexity on names: 40.0
a quarter of the data, 16 epochs, perplexity on descriptions: 39.6
a quarter of the data, 16 epochs, perplexity on names, last epoch: 44.1
a quarter of the data, 16 epochs, perplexity on descriptions, last epoch: 45.9
half the data, 8 epochs, parameters: 1,334,144
half the data, 8 epochs, steps: 4,288
half the data, 8 epochs, best epoch: 8
half the data, 8 epochs, perplexity on names: 30.4
half the data, 8 epochs, perplexity on descriptions: 28.6
half the data, 8 epochs, perplexity on names, last epoch: 30.4
half the data, 8 epochs, perplexity on descriptions, last epoch: 28.6
```

**Width** helps a lot, at a price. With the same steps, the names' perplexity falls from 36.9 at width 64 to 27.6 at 128 and 23.5 at 256. On names, the widest model, trained for four epochs, even beats the recorded model trained for sixteen, 24.0. But width 256 has 4,273,920 parameters against 1,334,144 at width 128, and each step costs about that much more.

**New text** helps at no extra cost per step. With the same steps, a random quarter of the products scores 40.0 on names at its best, half 30.4, and all of them 27.6. Doubling the text from half to all gained less than doubling the width from 128 to 256, but it cost no extra computation, and the first doubling, from a quarter to half, gained more than either.

**Repetition** helps for a while, then hurts. A quarter of the text seen four times scores 51.9; seen more often, it improves until epoch 11, then gets worse, ending at 44.1 after sixteen passes: the model memorizes what it has seen too often. Repeated text never caught up with new text at the same number of steps.

**More steps** help least. The recorded model's sixteen epochs improve on four, 24.0 against 27.6 on names, for four times the steps.

These runs also show the limits of this book's scale. The store's training text is fixed at what its catalog holds, 2,843,222 tokens. SmolLM2-360M, whose design [chapter 7](#the-transformer-block) compared with the store's model, was trained on 4 trillion tokens ([model card](https://huggingface.co/HuggingFaceTB/SmolLM2-360M/blob/f8027fd0eaeea54caa13c31d31b9fdc459c38b49/README.md)), more than a million times as much, which lets a model 960 numbers wide and 32 layers deep keep learning from new text instead of memorizing old.

**Working rule:** Get more text of the kind you'll predict before repeating what you have more than a few times; it costs nothing per step. With computation to spare, try a wider model for fewer epochs before training a narrow one longer, and measure both. Change one thing per run and hold the number of steps fixed where it matters, or the comparison measures two things at once.

## Suggest the next word in the search box {#autocomplete-in-the-search-box}

Averages say how good a model is; the search box shows what that means to a shopper. [Chapter 3's](#autocomplete-with-more-context) 4-gram suggested `&` and `with` after `outdoor bar`, a context no training name contains, and [chapter 5's](#suggest-from-similar-contexts) window model suggested `stool`. A few training descriptions do contain `outdoor bar`, and the transformer learned from them as well as from the names, while the 4-gram learned from names alone.

A shopper would see the transformer's three likeliest next tokens, and those of the half-and-half mix that the [names comparison](#compare-on-names) favoured, after the same five prefixes, each treated as the start of a name. A suggestion of `<sep>` means the model expects the name to end there:

Example `transformer-autocomplete` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Asks the transformer and its half-and-half mix with the 4-gram for their three likeliest next tokens after five prefixes,
treated as the start of a name, and prints the probability of stool after outdoor bar. The prose's point rests on the
stool lines and the control prefixes beside them."""
import numpy as np

from lib import bpe, transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey

_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
counted = KneserNey(name_tokens("train"), 4)
tokenizer = bpe.store_tokenizer()
as_counted = [{transformer.SEP: "</s>"}.get(token, token) for token in vocabulary]   # <sep> ends a name, as </s> does
show = lambda token: token.replace("</w>", "")

for prefix in ["bar", "patio bar", "outdoor bar", "kitchen bar", "wine bar"]:
    tokens = tokenizer.encode(prefix)
    ids = [index[transformer.START]] + [index[token] for token in tokens]
    from_transformer = transformer.softmax(transformer.forward(ids)[-1])
    context = tuple(["<s>"] * 3 + tokens)[-3:]   # the 4-gram looks at the last three tokens, padded with start markers for a short prefix
    from_counts = np.array([counted.probability(context, token) for token in as_counted])
    mixed = (from_transformer + from_counts) / 2
    for label, p in [("transformer", from_transformer), ("half and half", mixed)]:
        top = np.argsort(-p, kind="stable")[:3]   # the three likeliest; a stable sort keeps tied tokens in vocabulary order
        print(f"{prefix:<12} {label:<13} -> " + ", ".join(f"{show(vocabulary[i])} {p[i]:.2f}" for i in top))
    if prefix == "outdoor bar":
        stool = index["stool</w>"]   # </w> marks the end of a word in the tokenizer, so this is the whole word stool
        print("P(stool | outdoor bar), transformer:", f"{from_transformer[stool]:.2f}")
        print("P(stool | outdoor bar), 4-gram:", f"{from_counts[stool]:.2f}")
        print("P(stool | outdoor bar), half and half:", f"{mixed[stool]:.2f}")
```

Output:

```text
bar          transformer   -> with 0.17, & 0.14, and 0.09
bar          half and half -> & 0.19, with 0.14, unit 0.07
patio bar    transformer   -> stool 0.51, table 0.25, set 0.02
patio bar    half and half -> stool 0.69, table 0.13, & 0.01
outdoor bar  transformer   -> stool 0.50, with 0.05, table 0.04
outdoor bar  half and half -> stool 0.28, & 0.12, with 0.12
P(stool | outdoor bar), transformer: 0.50
P(stool | outdoor bar), 4-gram: 0.06
P(stool | outdoor bar), half and half: 0.28
kitchen bar  transformer   -> room 0.14, with 0.08, cabinet 0.08
kitchen bar  half and half -> with 0.14, & 0.12, room 0.07
wine bar     transformer   -> with 0.43, <sep> 0.22, cabinet 0.08
wine bar     half and half -> with 0.30, <sep> 0.21, cabinet 0.13
```

After `outdoor bar`, the transformer gives `stool` 0.50, where the 4-gram gives it 0.06; the mix, at 0.28, still puts it first. The control prefixes show the models aren't suggesting `stool` after every `bar`: after `kitchen bar` and `wine bar` they suggest other continuations, and after `wine bar` both expect, with good reason, that the name may already be complete. After `patio bar`, a context the names contain often, the mix is more confident in `stool` than the transformer alone.

One prefix is an example, not a measure. The measure is the names comparison, and there the mix won. For the search box, that's the model to serve.

**Working rule:** Serve the mix for autocomplete, and test it on rare prefixes as well as common ones, with control prefixes beside each. Treat a single striking suggestion as an illustration of a measured gain, never as the evidence for it.

## What goes wrong in production {#training-in-production}

Training goes wrong in ways that look fine while they happen:

- **Padding wastes computation.** Nearly half of each step's predictions were padding here. Pack texts, or group them by length, before you buy more computation.
- **A schedule bug looks like a model problem.** As a rule of thumb, a warm-up that never ends, or a decay that starts too early, shows up as a loss that falls too slowly; the decay comparison above shows how much a schedule can move the result. Save the step size, and check it against the schedule you meant.
- **Choices made on validation data flatter the result.** The kept epoch and the mixing share were both chosen on the validation split, so its numbers are slightly optimistic. Keep a test split untouched until the end.
- **Repeated text gets memorized.** A small dataset seen many times looks fine on the training loss and poor on new text. Count how many times training sees each text, and prefer new text to more epochs.
- **One model is measured on one kind of text.** The transformer ranked second to the counts on names and first on descriptions. Score every model on each kind of text it will serve before choosing which to deploy.
- **Results depend on the machine.** PyTorch doesn't guarantee identical results across releases or platforms ([Reproducibility](https://docs.pytorch.org/docs/2.14/notes/randomness.html)). Record the weights, the curves and the exact script, as `recordings/transformer.py` does with the script's hash, and keep them together.

## What this chapter decided {#training-decisions}

- **The store's model is trained in one recorded run:** batches of 32 product texts, AdamW with weight decay 0.1, gradients clipped, a warm-up of 200 steps to a peak step size of 0.003, cosine decay to a tenth, and the weights kept from epoch 15 of 16.
- **Every comparison counts the same predictions.** On names, both models predict each name's tokens and its end, against [chapter 3](#counting-further-back)'s names-only baseline, the stronger one for names. On descriptions, a 4-gram trained on the same texts scores the same tokens, with the same text before them.
- **On the validation names, the transformer alone roughly ties the 4-gram baseline, and mixed half and half with it scores 18.4,** the best on names in this book so far. The mix is the model the book uses for autocomplete, replacing chapter 5's mix of the window model and the counts.
- **From this chapter on, models are also measured on the validation descriptions.** There the transformer beats the baseline alone, 20.1 against 22.5, by winning where the counts haven't seen the context, and the mix scores 14.7.
- **At this scale, new text is the cheapest gain, width the largest at a price, and repetition helps only for a few passes.** The recorded model stays at width 128, because every example from [chapter 6](#attention) on reads it and the examples have to run in seconds on a laptop; a wider one would score better.
