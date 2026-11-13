---
title: "Language Models from the Ground Up"
chapter: "Words as vectors"
chapter_id: words-as-vectors
book: language-models-from-the-ground-up
edition: 2026.11.11
verified: 2026-11-13
edition_code: 3Y9C-0N1E
canonical: https://rollingedition.com/language-models-from-the-ground-up/words-as-vectors
license: CC BY 4.0
attribution: "“Words as vectors,” chapter 4 of Language Models from the Ground Up, Edition 2026.11.11, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/words-as-vectors. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Words as vectors

By the end of this chapter you can turn every token of the store's text into a short vector of numbers, so that tokens used in similar ways get similar vectors, by two methods: compressing counts of which tokens appear together, and training a small model to predict each token's neighbours. You'll measure what those vectors know, where they fail, and how they let a model relate text it has never seen to text it has.

[Chapter 3](#counting-further-back) ended on a limit that counting can't get past. Its 4-gram model had seen `patio bar stool` many times, and suggested `stool` after `patio bar`. After `outdoor bar`, which no training name contains, it fell back to generic suggestions, because a count of one context tells it nothing about another. A shopper, or any reader, knows that `outdoor` and `patio` mean nearly the same thing to the store, and a model needs some way to know it too. This chapter gives every token a vector, a list of numbers, and arranges the vectors so that tokens used alike sit close together.

Vectors need text that shows how words get used, and the store, an online seller of furniture and home goods, has plenty of it in its catalog's names and descriptions. Its training split, the 80% of products that models learn from, holds 2,744,320 tokens of that text, and every vector in this chapter comes from it alone, through the store's tokenizer from [chapter 2](#tokens).

## One-hot vectors know nothing {#one-hot-vectors-know-nothing}

Every model so far has treated tokens as names: `patio` is one entry in a table and `outdoor` another, with nothing linking them. Written as vectors, that's a **one-hot** encoding: each token gets a vector as long as the vocabulary, with a 1 in its own position and 0 everywhere else. To measure how alike two vectors are, this book uses **cosine similarity**: the cosine of the angle between them, 1 when they point the same way, 0 when they're at right angles. It ignores how long the vectors are and compares only their directions.

Give the 2,000 most frequent tokens of the training text one-hot vectors, and compare `patio` with `outdoor`, with `sofa` and with itself. Those 2,000 are about half of the store tokenizer's vocabulary, which keeps every matrix in this chapter small enough to compute in seconds:

Example `one-hot-vectors` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""One-hot vectors for the 2,000 most frequent tokens, and the cosine similarity of patio with outdoor, with sofa and with
itself. The prose's point rests on the patio–outdoor and patio–sofa lines: patio is as unrelated to outdoor as to sofa."""
import numpy as np

from lib.vectors import BREAK, training_ids                 # the book's shared module; BREAK marks the gap between two texts

ids, vocabulary = training_ids()                            # each training token as a number; RARE for tokens outside the vocabulary
index = {token: i for i, token in enumerate(vocabulary)}


def one_hot(token):
    vector = np.zeros(len(vocabulary))
    vector[index[token]] = 1.0                       # one column per token: 1 for this token, 0 everywhere else
    return vector


def cosine(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


print("numbers in each vector:", len(vocabulary))
print("cosine(patio, outdoor):", cosine(one_hot("patio</w>"), one_hot("outdoor</w>")))    # </w> marks a word's last token: patio</w> is the whole word
print("cosine(patio, sofa):", cosine(one_hot("patio</w>"), one_hot("sofa</w>")))
print("cosine(patio, patio):", cosine(one_hot("patio</w>"), one_hot("patio</w>")))
print("share of training tokens with a vector:", f"{(ids >= 0).sum() / (ids != BREAK).sum():.0%}")   # ids >= 0 are the kept tokens; BREAK gaps aren't tokens
```

Output:

```text
numbers in each vector: 2000
cosine(patio, outdoor): 0.0
cosine(patio, sofa): 0.0
cosine(patio, patio): 1.0
share of training tokens with a vector: 91%
```

A one-hot encoding says the two outdoor words are exactly as unrelated as a patio and a sofa. The cosine similarity of `patio` and `outdoor` is 0.0, and so is that of `patio` and `sofa`. Only a token compared with itself scores 1.0. Each vector has 2000 numbers. The 2,000 tokens that get vectors make up 91% of the training text; the rest are rarer, and this chapter leaves them out. Every pair of different tokens sits at right angles to every other, so nothing learned about one can carry over to another.

That's the same flaw as [chapter 3](#counting-further-back)'s counts, in another form. A model that reads one-hot vectors has to learn about every token separately, from the contexts that token itself appears in. Rare tokens get little, and unseen combinations get nothing.

**Working rule:** Don't feed one-hot vectors to a model that needs to relate tokens to each other. Use them only as an index, as the next sections do, to look up a learned vector for each token.

## Describe a token by the tokens around it {#describe-by-neighbours}

The way out is to describe a word by the company it keeps. Two words that appear among the same neighbours, such as `patio` and `outdoor`, which both turn up near `furniture`, `chair` and `umbrella`, are likely to mean similar things, even if they rarely appear together. So describe each token by its neighbours: count, for every pair of tokens, how often one appears within a small **window** of the other, here two tokens either side, and never across the gap between two products' texts. Each token's row of counts is then a vector of what it appears near.

Count co-occurrences in the training split's names and descriptions, and list what sits most often near `patio`:

Example `cooccurrence-counts` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Counts how often each of the 2,000 kept tokens appears within two tokens of another, and lists the six tokens seen most
often near patio. The prose's point rests on that list: punctuation and common words come first."""
import numpy as np

from lib.vectors import BREAK, cooccurrence, training_ids          # the book's shared module; BREAK marks the gap between two texts

ids, vocabulary = training_ids()                                   # each training token as a number; RARE for tokens outside the vocabulary
counts = cooccurrence(ids, len(vocabulary))          # how often each token appears within 2 tokens of another
patio = vocabulary.index("patio</w>")                # </w> marks a word's last token: patio</w> is the whole word, not a piece of a longer one

print("training tokens:", f"{int((ids != BREAK).sum()):,}")          # RARE tokens count here, since they are tokens; only the BREAK gaps don't
print("vocabulary kept:", f"{len(vocabulary):,}")
print("tokens near patio, counting repeats:", f"{int(counts[patio].sum()):,}")   # the row's total, a token counted again at each repeat
for i in np.argsort(-counts[patio], kind="stable")[:6]:          # the minus sorts most frequent first; ties keep vocabulary order
    print(f"  near patio: {vocabulary[i]:<12} {int(counts[patio, i]):>6,}")
```

Output:

```text
training tokens: 2,744,320
vocabulary kept: 2,000
tokens near patio, counting repeats: 8,790
  near patio: ,</w>           646
  near patio: or</w>          448
  near patio: with</w>        433
  near patio: your</w>        381
  near patio: .</w>           340
  near patio: furniture</w>    249
```

Of the 8,790 tokens within two places of `patio`, counting a token again each time it appears there, the most frequent are disappointing: a comma, `or`, `with`, `your` and a full stop, before the first word with anything to do with patios, `furniture`. Those tokens appear near almost everything, because they're everywhere. A row of raw counts mostly says how common each neighbour is, not what's special about the token whose row it is.

So raw counts make poor vectors. Two tokens that both appear often will look alike because they share the same frequent neighbours, commas and `with`, whatever they mean. What matters is which neighbours a token has more often than you'd expect from how common those neighbours are.

**Working rule:** Count co-occurrence within a small window, two to five tokens, in text the model will learn from, and never across document boundaries. Don't use the raw counts as vectors: reweight them, as the next section does, so frequent neighbours stop dominating.

## Weigh co-occurrence by surprise {#weigh-by-surprise}

The fix compares each count with what chance would predict. If `patio` and `furniture` appeared independently of each other, they'd co-occur about as often as their separate frequencies imply. **Pointwise mutual information**, or PMI, measures how far the real count departs from that: the log of the ratio between how often two tokens co-occur and how often they would by chance ([Church and Hanks, 1990](https://aclanthology.org/J90-1003/)). In symbols, for tokens a and b:

PMI(a, b) = log [ P(a, b) / (P(a) · P(b)) ]

where P(a, b) is the share of all co-occurrence counts that are of a and b together, and P(a) and P(b) are each token's share. PMI is positive when two tokens appear together more than chance predicts, and negative when less. Negative values are unreliable, since "less than chance" usually means "rarely seen at all", so **positive PMI**, or PPMI, replaces them with zero. The book's shared module `lib.vectors` computes it from the co-occurrence counts of the [previous section](#describe-by-neighbours), in three lines: the count chance would predict for each pair, the log of the real count over it, and zero wherever that's negative or the pair never occurs:

```python
expected = counts.sum(1, keepdims=True) * counts.sum(0, keepdims=True) / total
pmi = np.log(counts / expected)
return np.where(counts > 0, np.maximum(pmi, 0), 0.0)
```

Reweighting is meant to stop frequent neighbours dominating, so swap the raw counts for PPMI and list `patio`'s strongest neighbours again:

Example `ppmi-neighbours` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Reweights the co-occurrence counts with positive PMI, and lists the six tokens with the strongest weight beside patio.
The prose's point rests on that list: the commas and common words of the raw counts are gone."""
import numpy as np

from lib.vectors import cooccurrence, ppmi, training_ids

ids, vocabulary = training_ids()                     # each training token as a number; RARE for tokens outside the vocabulary
weights = ppmi(cooccurrence(ids, len(vocabulary)))   # PPMI of the co-occurrence counts, within the same window of 2 tokens
patio = vocabulary.index("patio</w>")                # </w> marks a word's last token: patio</w> is the whole word

print("share of PPMI entries that are zero:", f"{(weights == 0).mean():.0%}")   # zero for pairs that never co-occur and for pairs seen no more often than chance
for i in np.argsort(-weights[patio], kind="stable")[:6]:      # the largest weights first; ties keep vocabulary order
    print(f"  PPMI with patio: {vocabulary[i]:<12} {weights[patio, i]:.2f}")
```

Output:

```text
share of PPMI entries that are zero: 86%
  PPMI with patio: porch</w>    4.51
  PPMI with patio: deck</w>     4.19
  PPMI with patio: backyard</w> 3.97
  PPMI with patio: sectional</w> 3.75
  PPMI with patio: furniture</w> 3.59
  PPMI with patio: garden</w>   3.53
```

The commas are gone. The strongest neighbours of `patio` by PPMI are `porch`, `deck`, `backyard`, `sectional`, `furniture` and `garden`: words a person would associate with a patio, ranked by how much more often than chance they appear near it. Most pairs of tokens appear together no more often than chance, which is why 86% of the PPMI matrix is zero.

PPMI vectors are already useful: two tokens with similar PPMI rows have similar distinctive neighbours. But each vector is still 2,000 numbers long, mostly zeros, and two tokens with related but not identical neighbours, say `deck` and `porch`, can share few nonzero entries.

**Working rule:** Reweight co-occurrence counts with positive PMI before using them as vectors. Expect PMI to overrate pairs of rare tokens, whose few co-occurrences look far above chance; that's one reason to keep only frequent tokens, as this chapter does, or to require a minimum count.

## Compress counts into dense vectors {#compress-into-dense-vectors}

A [PPMI vector](#weigh-by-surprise) of 2,000 numbers, mostly zeros, has a lot of room and little information. Compressing it into a short, dense vector keeps the strongest patterns of co-occurrence, drops the noise, and puts tokens with related neighbours close together even when they share few exact neighbours. The tool is the **singular value decomposition**, SVD, which finds the 64 directions that together reconstruct the PPMI rows best, and weights each by how much of the rows it explains. A token's 64 weighted coordinates along those directions are its new vector: an **embedding**, a dense vector that stands for a token. The method `lib.vectors.svd_vectors` computes them, scales each to unit length, and `lib.vectors.nearest` finds the tokens with the highest cosine similarity to any vector.

Six tokens' four nearest neighbours show what the 64 numbers keep:

Example `svd-neighbours` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Compresses the PPMI matrix into 64 numbers per token, and lists the four nearest neighbours of six tokens. The prose's
point rests on the first two lists and the last line: patio and outdoor are each other's nearest neighbour, at the cosine printed last."""
from lib.vectors import DIMENSIONS, nearest, svd_vectors          # svd_vectors does the PPMI and SVD steps; nearest ranks tokens by cosine similarity

vectors, vocabulary = svd_vectors()                               # one 64-number row per token, each scaled to unit length
index = {token: i for i, token in enumerate(vocabulary)}

print("dimensions per token:", DIMENSIONS)
for token in ["patio</w>", "outdoor</w>", "sofa</w>", "oak</w>", "blue</w>", "48</w>"]:     # </w> marks a word's last token
    neighbours = nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))   # skip leaves out the token itself, which would otherwise be its own nearest at 1.00
    print(f"{token:<12} -> " + ", ".join(f"{t} {s:.2f}" for t, s in neighbours))
print("cosine(patio, outdoor):", f"{float(vectors[index['patio</w>']] @ vectors[index['outdoor</w>']]):.2f}")   # unit-length vectors, so the dot product is the cosine
```

Output:

```text
dimensions per token: 64
patio</w>    -> outdoor</w> 0.84, bistro</w> 0.79, porch</w> 0.79, lounge</w> 0.77
outdoor</w>  -> patio</w> 0.84, porch</w> 0.82, indoor</w> 0.80, furniture</w> 0.74
sofa</w>     -> sectional</w> 0.93, chaise</w> 0.90, loveseat</w> 0.89, lounge</w> 0.87
oak</w>      -> walnut</w> 0.96, veneers</w> 0.90, espresso</w> 0.89, weathered</w> 0.88
blue</w>     -> green</w> 0.86, beige</w> 0.86, pur 0.80, abstract</w> 0.79
48</w>       -> 36</w> 0.94, 32</w> 0.93, 24</w> 0.92, 30</w> 0.89
cosine(patio, outdoor): 0.84
```

Every token now has 64 numbers, and its neighbours read like a thesaurus built for a furniture store. `patio` and `outdoor` are each other's nearest neighbour, at a cosine similarity of 0.84, where their one-hot vectors scored zero. `sofa` sits beside `sectional`, `chaise` and `loveseat`; `oak` beside `walnut` and `espresso`, a wood finish; `blue` beside other colours; and `48` beside other sizes in inches.

None of that was taught. The method never saw a definition of `sofa`, a list of colours or a hint that `48` is a number. It found that these tokens appear among the same kinds of neighbours in the store's text, and the SVD put them close together because of it. That's the property [chapter 3](#counting-further-back)'s counts lacked: whatever a model learns about `patio bar stool` can now carry over, through the embeddings, to `outdoor bar stool`.

**Working rule:** Compress PPMI with SVD to between 50 and 300 dimensions, and check the result the way this section does: list a handful of tokens' nearest neighbours and read them. If the neighbours are mostly frequent function words, the reweighting went wrong; if they're unrelated, the window or the vocabulary is too small.

## Learn vectors by predicting neighbours {#learn-by-predicting-neighbours}

The other way to get embeddings is to learn them by prediction, which is how every neural language model in this book gets its own. **Skip-gram with negative sampling**, the method behind word2vec, gives each token two vectors, one for when it's the centre token and one for when it's a neighbour, and trains them on one task: given a token, tell its real neighbours apart from random tokens ([Mikolov et al., 2013a](https://arxiv.org/abs/1301.3781); [Mikolov et al., 2013b](https://arxiv.org/abs/1310.4546)). For a token and one of its real neighbours, the model scores the pair by the dot product of their vectors, turns the score into a probability with the logistic function, and nudges the vectors so the probability rises. For a few random **noise** tokens drawn from the vocabulary, it nudges the probability down. Repeated over millions of pairs, tokens with the same neighbours end up with similar vectors. That's no coincidence: Levy and Goldberg showed that skip-gram with negative sampling, trained this way, in effect factorizes a PMI matrix, shifted down by the log of the number of noise tokens, much as the [SVD](#compress-into-dense-vectors) factorizes PPMI ([Levy and Goldberg, 2014](https://papers.nips.cc/paper_files/paper/2014/hash/b78666971ceae55a8e87efb7cbfd9ad4-Abstract.html)).

Write v for the centre token's vector, u for the real neighbour's, and uₙ for each noise token's, and σ for the logistic function, σ(s) = 1 / (1 + e⁻ˢ), which turns a score into a probability. The loss for one pair is the surprise at the real neighbour plus the surprise at each noise token's not being one:

L = −log σ(v·u) − Σₙ log σ(−v·uₙ)

and `lib.skipgram.step` lowers it with three lines of gradient descent, where `real` is σ(v·u), `fake` holds σ(v·uₙ) for each noise token, and `rate` is the step size:

```python
np.add.at(inputs, centre, -rate * grad_v)                               # move v: towards u, away from each uₙ
np.add.at(outputs, context, -rate * (real - 1)[:, None] * v)            # move u towards v
np.add.at(outputs, noise, -rate * fake[:, :, None] * v[:, None, :])     # move each uₙ away from v
```

Run three updates on one real pair, `patio` and `umbrella`, with `sofa` and `48` as noise tokens. The centre vectors start small and random and the neighbour vectors at zero, as `lib.skipgram.train` starts them:

Example `skipgram-step` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Three updates of skip-gram with negative sampling on one real pair, patio and umbrella, with sofa and 48 as noise tokens,
printing each pair's probability before and after. The prose's point rests on the four probability lines: umbrella's rises,
and the noise tokens' fall."""
import numpy as np

from lib.skipgram import sigmoid, step                              # one gradient step, and the logistic function
from lib.vectors import training_ids

_, vocabulary = training_ids()
rng = np.random.default_rng(2026)                                   # a fixed seed, so the starting vectors are the same on every run
inputs = (rng.random((len(vocabulary), 8)) - 0.5) / 8     # each token's vector as a centre, small and random
outputs = np.zeros((len(vocabulary), 8))                 # and as a neighbour: zero, as training starts
centre, context = [vocabulary.index("patio</w>")], [vocabulary.index("umbrella</w>")]   # the real pair: patio as the centre, umbrella its real neighbour
noise = np.array([[vocabulary.index("sofa</w>"), vocabulary.index("48</w>")]])          # noise tokens, picked by hand here; training draws them at random


def chances():
    real = sigmoid(inputs[centre[0]] @ outputs[context[0]])
    fake = sigmoid(outputs[noise[0]] @ inputs[centre[0]])
    return real, fake


before = chances()                                       # zero neighbour vectors give every score zero, so every probability is one half
for _ in range(3):                                       # three updates on the same pair
    step(np.array(centre), np.array(context), noise, inputs, outputs, rate=1.0)   # rate 1.0, far above the 0.025 that training starts from, so three steps show
after = chances()
print("P(umbrella is a real neighbour of patio), before:", f"{before[0]:.3f}")
print("P(umbrella is a real neighbour of patio), after 3 steps:", f"{after[0]:.3f}")
print("P(sofa, 48 are real neighbours), before:", ", ".join(f"{p:.3f}" for p in before[1]))
print("P(sofa, 48 are real neighbours), after 3 steps:", ", ".join(f"{p:.3f}" for p in after[1]))
```

Output:

```text
P(umbrella is a real neighbour of patio), before: 0.500
P(umbrella is a real neighbour of patio), after 3 steps: 0.525
P(sofa, 48 are real neighbours), before: 0.500, 0.500
P(sofa, 48 are real neighbours), after 3 steps: 0.475, 0.475
```

Training pulls real neighbours together and pushes random tokens apart, and three updates show it in miniature. Before any update, the neighbour vectors are zero, so every score is zero, and σ(0) is one half: the model knows nothing. After three, `umbrella` scores 0.525 as a neighbour of `patio`, up from 0.500, and `sofa` and `48` have dropped to 0.475, 0.475. That's all training does, millions of times over.

**Working rule:** When you train embeddings, start the second set of vectors at zero and the first at small random values, as `lib.skipgram.train` does, and draw noise tokens in proportion to their frequency raised to the power 0.75, which Mikolov et al. found works better than plain frequency. Check one update by hand before running millions: a probability moving the wrong way means the gradient's sign is wrong.

## Compare learned vectors with counted ones {#compare-learned-and-counted}

Training skip-gram on all the store's training text runs millions of updates, and its exact result depends on the machine's floating-point arithmetic, which varies slightly between processors. So it runs once, in `recordings/skipgram.py`, with the book's own code and a fixed seed, and the examples read its saved vectors. Its manifest records the settings: a window of two tokens, 64 dimensions, five noise tokens per pair and two passes over the text. One setting is fixed in `lib.skipgram` rather than recorded: pairs centred on very frequent tokens, such as commas, are mostly skipped, with a threshold of 10⁻⁴, which keeps them from dominating training ([Mikolov et al., 2013b](https://arxiv.org/abs/1310.4546), who suggest around 10⁻⁵ for larger text).

Ask the recorded skip-gram vectors for the same six tokens' neighbours, and compare them with the [SVD's](#compress-into-dense-vectors):

Example `skipgram-neighbours` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Reads the skip-gram vectors and training losses that recordings/skipgram.py saved, and lists the same six tokens' four
nearest neighbours as the SVD example. The prose's point rests on the two loss lines and on outdoor's nearest neighbour."""
import json

import numpy as np

from lib.vectors import nearest

recorded = "data/recorded/skipgram/"                 # saved by recordings/skipgram.py, which trains once: its values depend on the machine
vectors = np.load(recorded + "vectors.npy")
vocabulary = json.load(open(recorded + "vocabulary.json", encoding="utf-8"))
losses = np.load(recorded + "losses.npy")            # one loss per batch, in training order
index = {token: i for i, token in enumerate(vocabulary)}

print("training loss, first batch:", f"{losses[0]:.2f}")                        # index 0: the first batch, when nothing has been learned yet
print("training loss, last 100 batches:", f"{losses[-100:].mean():.2f}")
for token in ["patio</w>", "outdoor</w>", "sofa</w>", "oak</w>", "blue</w>", "48</w>"]:
    neighbours = nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))   # skip leaves out the token itself
    print(f"{token:<12} -> " + ", ".join(f"{t} {s:.2f}" for t, s in neighbours))
```

Output:

```text
training loss, first batch: 4.16
training loss, last 100 batches: 2.05
patio</w>    -> porch</w> 0.77, bistro</w> 0.69, garden</w> 0.69, couch</w> 0.67
outdoor</w>  -> indoor</w> 0.75, patio</w> 0.66, garden</w> 0.65, living</w> 0.61
sofa</w>     -> couch</w> 0.85, sleeper</w> 0.84, chaise</w> 0.80, sectional</w> 0.78
oak</w>      -> walnut</w> 0.91, espresso</w> 0.84, weathered</w> 0.81, glossy</w> 0.80
blue</w>     -> beige</w> 0.88, gray</w> 0.87, green</w> 0.85, brown</w> 0.80
48</w>       -> 36</w> 0.94, 32</w> 0.92, 1.5</w> 0.89, 24</w> 0.89
```

The model learned to tell real neighbours from noise: its training loss fell from 4.16 on the first batch to 2.05 on the last hundred. Its neighbours agree with the SVD's on most tokens, `sofa` with `sectional` and `chaise`, `oak` with `walnut` and `espresso`, colours with colours, sizes with sizes, and differ in emphasis on others: skip-gram puts `outdoor` closest to `indoor`, because the two words appear in the same positions in descriptions such as `indoor or outdoor use`.

That difference is worth noticing. Vectors built from neighbours put together words used in the same places, and opposites often are: `indoor` and `outdoor` here, and, in the [next section](#analogies-and-where-they-fail), `small`, whose nearest neighbours include `larger` as well as `smaller`. Similar vectors mean similar use, not similar meaning.

**Working rule:** Treat counted embeddings (PPMI and SVD) and learned ones (skip-gram) as close alternatives: on a few million tokens they give similar neighbours, and counted ones are deterministic and fast. Prefer learned embeddings when they're part of a larger model you're training anyway, as in every later chapter of this book. Never read a high similarity as synonymy without checking for opposites.

## Analogies, and where they fail {#analogies-and-where-they-fail}

Embeddings famously support analogies by arithmetic: if the difference between `chair` and `chairs` is a direction that means "plural", then adding it to `table` should land near `tables`. In vectors, the answer to "a is to b as c is to what?" is the token nearest to b − a + c, leaving out the three tokens in the question ([Mikolov et al., 2013a](https://arxiv.org/abs/1301.3781)). It's a neat test of whether the vectors have learned consistent relationships, and a good place to see their limits.

Three analogies on the [skip-gram vectors](#compare-learned-and-counted) show where the arithmetic holds and where it breaks, and the nearest neighbours of three tokens they raise show why:

Example `analogies` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Three analogies on the skip-gram vectors, each answered by the tokens nearest b minus a plus c; whether lamps and light
have vectors at all; and the nearest tokens to a few single words. The prose rests on the three analogy lines, the lamps line and the neighbour lists."""
import json

import numpy as np

from lib.vectors import nearest

vectors = np.load("data/recorded/skipgram/vectors.npy")               # saved by recordings/skipgram.py, which trains once
vocabulary = json.load(open("data/recorded/skipgram/vocabulary.json", encoding="utf-8"))
index = {token: i for i, token in enumerate(vocabulary)}

for a, b, c in [("chair", "chairs", "table"), ("chair", "chairs", "lamp"), ("black", "white", "dark")]:   # each reads: a is to b as c is to what
    a, b, c = (word + "</w>" for word in (a, b, c))       # the tokenizer marks each word's last token with </w>, so words are looked up in that form
    query = vectors[index[b]] - vectors[index[a]] + vectors[index[c]]   # b - a + c: "c, changed the way a became b"
    answers = nearest(vectors, vocabulary, query, k=3, skip=(a, b, c))  # the words in the question can't be their own answer
    print(f"{a} : {b} :: {c} : ? -> " + ", ".join(t for t, _ in answers))
print("lamps in the vocabulary:", "lamps</w>" in index)
print("light in the vocabulary:", "light</w>" in index)
for token in ["light</w>", "dark</w>", "small</w>"]:
    print(f"{token:<12} -> " + ", ".join(t for t, _ in nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))))
```

Output:

```text
chair</w> : chairs</w> :: table</w> : ? -> tables</w>, cup</w>, stools</w>
chair</w> : chairs</w> :: lamp</w> : ? -> tops</w>, coffee</w>, tray</w>
black</w> : white</w> :: dark</w> : ? -> brown</w>, blue</w>, glossy</w>
lamps in the vocabulary: False
light in the vocabulary: True
light</w>    -> lights</w>, bulb</w>, dimmable</w>, candle</w>
dark</w>     -> brown</w>, walnut</w>, gray</w>, espresso</w>
small</w>    -> smaller</w>, larger</w>, displaying</w>, storing</w>
```

Only the first analogy gets the answer you'd expect: `chair` is to `chairs` as `table` is to `tables`, the top answer. The second fails because `lamps` isn't among the 2,000 tokens that have vectors, so the right answer can't be found at all, and the arithmetic returns whatever is nearest. The third fails differently. `light` is in the vocabulary, but `black` is to `white` as `dark` is to `brown`, by the vectors' reckoning. The neighbour lists show why: `light` sits with `lights`, `bulb`, `dimmable` and `candle`, because in the store's text it's mostly a lamp, as in `ceiling light`, not a shade, while `dark` sits with `brown`, `walnut` and `espresso`, the finishes it describes. And `small` sits with `larger` as well as `smaller`: size words appear in the same places, whichever size they name.

Analogies are a demonstration, not a measure. They work for relationships the text expresses consistently and often, such as plurals of common words, and fail for rare words, for words with several senses, and for relationships the text rarely spells out. A model doesn't use analogies; it uses the vectors' positions, and those carry the same strengths and blind spots.

**Working rule:** Don't judge embeddings by analogies; judge them by how much they help the task they're for, as the next section and every later chapter do. When an analogy fails, check whether the answer is in the vocabulary and whether the words mean what you assume in your text.

## Find similar names with vectors {#find-similar-names}

Embeddings for tokens give, with one more step, embeddings for whole texts: average the vectors of a text's tokens, scale the result to unit length, and similar texts get similar vectors. That's a rough version of what search engines call semantic retrieval, finding texts by meaning rather than by matching words, which this book's companion, *A Primer on Search Relevance*, builds properly with a trained model ([semantic retrieval](https://rollingedition.com/primer-on-search-relevance/semantic-retrieval)). Here it tests the one thing this chapter set out to fix: [chapter 3's](#autocomplete-with-more-context) counted model can't relate `outdoor bar` to `patio bar`.

Averaging every training name's skip-gram vectors turns each name into one vector. Rare words, most often a product line's name, print as `[name]`, as [chapter 1](#load-the-store-text) explained. Two queries show what that buys: `outdoor bar`, the prefix that stumped [chapter 3](#counting-further-back)'s 4-gram model, and `patio umbrella`:

Example `name-vectors` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Averages each training name's skip-gram token vectors into one unit-length vector, and prints the four training names
nearest to each of two queries. The prose's point rests on the first query: two patio bar stool names come up for outdoor bar."""
import json

import numpy as np

from lib import bpe
from lib.store import load_products, masked

vectors = np.load("data/recorded/skipgram/vectors.npy")
vocabulary = json.load(open("data/recorded/skipgram/vocabulary.json", encoding="utf-8"))
index, tokenizer = {t: i for i, t in enumerate(vocabulary)}, bpe.store_tokenizer()


def name_vector(text):                               # the average of the text's token vectors, at unit length
    found = [index[t] for t in tokenizer.encode(text) if t in index]    # tokens outside the 2,000 kept have no vector, so they're left out
    average = vectors[found].mean(0) if found else np.zeros(vectors.shape[1])   # a text with no kept tokens gets the zero vector
    return average / (np.linalg.norm(average) or 1.0)            # `or 1.0`: a zero average stays zero, rather than dividing by zero


names = load_products("train")["name"].tolist()        # the training split's product names, the texts to compare
matrix = np.array([name_vector(n) for n in names])
for query in ["outdoor bar", "patio umbrella"]:
    best = np.argsort(-(matrix @ name_vector(query)), kind="stable")[:4]   # unit vectors, so the dot product is the cosine; the four largest, most similar first
    print(f"{query}: " + " | ".join(masked(names[i]) for i in best))   # [name]: a rare word
```

Output:

```text
outdoor bar: outdoor modern industrial 5 piece bar height dining set | [name] bar & bar stool | 29.5 '' patio bar stool | 28.5 '' patio bar stool
patio umbrella: premium tight weave outdoor patio umbrella cover | patio lantern | garden patio 88 [name] rattan deck box | outdoor patio chair
```

The averaged vectors put two `patio bar stool` names among the closest to `outdoor bar`, and neither contains the word `outdoor`. That model couldn't make that link, because it had counts for `patio bar stool` and none for `outdoor bar`. The link runs through `outdoor` and `patio`, whose vectors are close. For `patio umbrella`, the closest names are patio and outdoor products, and the top one is an umbrella cover, but none of them is an umbrella itself: averaging lets `patio` outweigh `umbrella`.

Averaging is crude: it forgets word order, so `bar stool` and `stool bar` get the same vector, and it lets frequent tokens drown out the one that matters. But it shows the property every later model in this book is built on: a model that reads embeddings instead of one-hot tokens can carry what it learned about one phrase over to another.

**Working rule:** Average token embeddings when you need a quick, order-free representation of short texts, and expect it to find related items but rank them loosely. For real semantic retrieval, use a model trained for it, as the Primer does. For language modeling, give the model the embeddings themselves and let it learn how to combine them, which [chapter 5](#a-neural-language-model) starts doing.

## What goes wrong in production {#vectors-in-production}

Embeddings carry their training text's habits into everything that uses them:

- **Similar use isn't similar meaning.** `indoor` and `outdoor` sit close together. A system that treats close vectors as interchangeable will happily swap opposites; check the nearest neighbours of the words your product depends on.
- **Rare and new tokens get poor vectors, or none.** This chapter kept 2,000 tokens. A token outside that list has no vector, and a token seen a handful of times has a noisy one. The store's tokenizer has more than twice that many tokens, and a rare word that the tokenizer splits into pieces gets a vector only from those of its pieces that are among the 2,000; a model that learns its own embeddings, as every later chapter's does, covers the whole vocabulary.
- **Vectors reflect the text they came from.** The store's text describes `light` as a lamp, so its vector sits with lighting. Embeddings trained on one domain carry its senses, and its biases, into another.
- **Ship the vectors, not the recipe.** Training embeddings by gradient descent gives slightly different vectors on different processors, which is why this book records them. Store the vectors you ship, with the code and settings that made them.
- **Embeddings go stale.** New product lines and words appear in the catalog; retrain or extend embeddings when the vocabulary drifts, and check neighbour lists for the tokens that matter after each retrain.

## What this chapter decided {#vectors-decisions}

- **Tokens are compared by the cosine similarity of their vectors.** It ignores length and compares direction, and it's what `lib.vectors.nearest` returns. Every vector is scaled to unit length first, so the cosine is a plain dot product and frequent tokens, whose raw vectors are longer, don't win by size.
- **Counted embeddings come from positive PMI compressed with SVD,** over a window of two tokens and the 2,000 most frequent tokens, in `lib.vectors`. On the store's text they put `patio` next to `outdoor`, which one-hot vectors couldn't.
- **Learned embeddings come from skip-gram with negative sampling,** trained once in `recordings/skipgram.py` with the book's own code and a fixed seed, because their exact values depend on the machine. They agree with the counted ones on most tokens.
- **Similar vectors mean similar use.** Opposites such as `indoor` and `outdoor` get close vectors, and analogies work only for relationships the text expresses often, so the book judges embeddings by how much they help a task, never by analogies.
- **Every later model learns its own embeddings,** as part of predicting the next token, starting with [chapter 5](#a-neural-language-model)'s neural language model. This chapter's vectors show that embeddings carry knowledge from one context to another, and the rest of the book's models put that to work.
