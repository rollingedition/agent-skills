---
title: "Language Models from the Ground Up"
chapter: "Predicting the next word"
chapter_id: predicting-the-next-word
book: language-models-from-the-ground-up
edition: 2026.11.11
verified: 2026-11-13
edition_code: 3Y9C-0N1E
canonical: https://rollingedition.com/language-models-from-the-ground-up/predicting-the-next-word
license: CC BY 4.0
attribution: "“Predicting the next word,” chapter 1 of Language Models from the Ground Up, Edition 2026.11.11, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/predicting-the-next-word. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Predicting the next word

By the end of this chapter you can build a complete language model from a store's product names by counting, use it to suggest the next word as a shopper types, generate text with it, and measure with one number how well it predicts text it has never seen. Every later chapter replaces one part of this model with a better one, and from [chapter 3](#counting-further-back) on, measures each change the same way.

Throughout the book, one case study recurs: an online furniture and home-goods store, which we call the store. Its search box needs autocomplete, so that a shopper who types `coffee` sees `table` offered as the next word, and its short product descriptions need writing and checking. Both are problems of predicting the next word, and the store has the text to learn them from: the names and descriptions of every product in its catalog.

A **language model** is a program that assigns a probability to every word that could come next, given the words so far. That one ability covers a lot. Suggesting how to finish a search query means picking a likely next word. Writing a sentence means picking a next word, adding it, and picking again. A model that predicts well has learned something about the text it was trained on, so how well it predicts is how you measure it. The large language models behind chat assistants do the same thing at a vastly larger scale: given the text so far, they assign a probability to each possible next piece of text. This book builds that machinery one part at a time, small enough to run on a laptop, so you can see what each part does.

In this chapter you count which word follows which in the product names, turn the counts into probabilities, and put them to work. The model you build here has a serious flaw, and the chapter ends by measuring it.

## Load the store's text {#load-the-store-text}

Before a model can learn which words follow which, it needs text to learn from, and a way to tell whether what it learned carries over to text it hasn't seen. The second need matters as much as the first. A model can predict the text it learned from perfectly by memorizing it, which says nothing about how it will do on the next product the store adds. So the text is split once, before anything learns from it, into three parts: a **training split** that models learn from, a **validation split** for comparing models while you build them, and a **test split** kept for final reports. Each product belongs to exactly one split, so no name or description a model is scored on appears in what it learned from.

The store's text, which every example in this book learns from, is real. It comes from WANDS, a public product-search dataset that Wayfair published with a paper at ECIR 2022 ([Chen et al., 2022](https://easychair.org/publications/preprint/wm4R)), under the MIT licence ([licence](https://github.com/wayfair/WANDS/blob/main/LICENSE)). The script `prep/wands_text.py` prepares it, and its data card, `examples/data/wands-text/README.md`, says how: the text is already lowercased, with spaces around punctuation, and descriptions are cut at a sentence end to keep the file small. Products whose text names the store itself are left out, so no model in this book learns to write the store's name. The examples read the text through `lib.store`, one of the book's shared modules: short files in `examples/lib/` that hold setup code many examples need, which you can open and read.

Before counting anything, look at the text: the size of each split, and a few names:

Example `store-text` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Counts the store's products in each split and the words in its training names, then prints one ordinary training name
for each of four kinds of product. The line "different words in training names" is the one the prose's point rests on,
since the rare product-line names are among the words it counts."""
from lib.store import load_products, ordinary_words, words

products = load_products()                            # no split given: every product, in all three splits
print("products:", f"{len(products):,}")
for split in ["train", "validation", "test"]:
    print(f"{split} products:", f"{(products['split'] == split).sum():,}")

train = products[products["split"] == "train"]        # only the training names count toward the word totals
print("words in training names:", f"{sum(len(words(name)) for name in train['name']):,}")
print("different words in training names:", f"{len({w for name in train['name'] for w in words(name)}):,}")
print()
common = ordinary_words(300)                          # words in 300 descriptions or more: a stricter bar than the book's 30
for kind in ["coffee table", "bar stool", "area rug", "bathroom vanity"]:      # one name of each kind, as examples
    print(next(name for name in train["name"] if kind in name and all(w in common or not w.isalpha() for w in words(name))))   # the first name whose words are all common; numbers and punctuation pass
```

Output:

```text
products: 42,815
train products: 34,252
validation products: 4,282
test products: 4,281
words in training names: 231,048
different words in training names: 25,907

solid wood coffee table
25 '' bar stool
hand-knotted wool/silk teal/plum area rug
36 '' single bathroom vanity
```

Product names are short and repetitive enough for counting to work, so this chapter learns from them alone. The store's text covers 42,815 products, 34,252 of them in the training split. The training names hold 231,048 words, of 25,907 different kinds. That second count is large for a catalog of furniture, because many names start with a product line's name, a word that appears in a handful of products and nowhere else. This book doesn't print those names. Where an example's output would show one, it prints `[name]` instead, for any word used in fewer than 30 of the training descriptions, most often a product line's name. Those rare words will matter by the end of the chapter.

**Working rule:** Split your text into training, validation and test parts before any model sees it, and split by document (here, by product), so near-duplicates of one item never straddle two parts. Compare models on validation text while you work, and touch the test text only for the final report. Learn from the shortest, most regular text you have first; this chapter starts with names, and descriptions come later in the book.

## Count which word follows which {#count-word-pairs}

With the training names loaded, a simple model of what comes next is a table of how often each word followed each other word. A **bigram** is a pair of adjacent words, such as `coffee table`. Count every bigram in the training names, and you know, for any word, which words came after it and how often. Claude Shannon used exactly this idea in the paper that founded information theory, approximating English by choosing each word according to how often it follows the one before ([Shannon, 1948](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x)).

Two details make the counts complete. A name's first word follows nothing, and its last word is followed by nothing, but both are worth predicting: the first word decides what kind of product a shopper is typing, and knowing where a name ends lets a model stop. So each name is padded with two markers, `<s>` at the start and `</s>` at the end, which count as words. The pair `<s> coffee` then records that a name started with `coffee`, and `table </s>` records that a name ended with `table`.

Start with a word whose next word matters to the search box, `coffee`. The example counts every pair in the training names, then lists what followed it:

Example `count-next-words` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Counts every word pair in the training names, padded with start and end markers, and lists the words that most often
follow coffee. The four lines under "words after coffee" are what the prose's point rests on."""
from collections import Counter

from lib.store import load_products, words

names = load_products("train")["name"]                # training split only, so validation and test names never add counts
pairs = Counter()
for name in names:
    tokens = ["<s>"] + words(name) + ["</s>"]       # the markers record how a name starts and where it stops
    pairs.update(zip(tokens, tokens[1:]))            # tokens[1:] is the same list one word on, so each word pairs with the next

print("word pairs:", f"{sum(pairs.values()):,}")
print("different pairs:", f"{len(pairs):,}")

after_coffee = {following: n for (word, following), n in pairs.items() if word == "coffee"}   # pairs that start with coffee, by the word after
print("words after coffee:", f"{sum(after_coffee.values()):,}")
for following, n in sorted(after_coffee.items(), key=lambda item: -item[1])[:4]:   # the key negates the count, so largest first
    print(f"  coffee {following:<6} {n:>6,}")
```

Output:

```text
word pairs: 265,300
different pairs: 84,529
words after coffee: 1,260
  coffee table   1,129
  coffee mug        45
  coffee ,          28
  coffee jar        13
```

One word dominates. Almost every `coffee` in the store's names is a `coffee table`, and of the 1,260 words that follow `coffee` in the training names, almost all are `table`. A comma comes third, because the store's text treats punctuation as words of its own. That's a choice about tokens, the units a model counts, and [chapter 2](#tokens) shows how much it matters.

The table of counts is the whole model. It has no rules about grammar and no knowledge of furniture; it has seen `coffee table` many times and `coffee lamp` never, and that is all it knows. The shared module `lib.bigrams` holds this same counting code, as the class `Bigrams`, so later examples can build the model in one line.

**Working rule:** Count pairs in the training split only, and pad every text with start and end markers so the model learns how texts begin and end. Keep the raw counts, not only the probabilities you'll derive from them: the counts tell you how much evidence each probability rests on, and the next sections need them.

## Turn counts into probabilities {#counts-to-probabilities}

Counts say what happened, but a language model needs probabilities: how likely each next word is. The step from one to the other is division. The probability of a word given the word before it is the number of times the pair occurred, divided by the number of times the first word occurred with anything after it. In symbols, writing `w` for the previous word and `v` for the next one:

P(v | w) = count(w v) / count(w)

Read it as "the probability of `v`, given `w`". Estimating probabilities this way, from the fraction of times something happened, is called **maximum likelihood estimation**: of all the probability tables you could choose, it's the one that makes the training text likeliest ([Jurafsky and Martin, chapter 3](https://web.stanford.edu/~jurafsky/slp3/3.pdf)).

Apply the formula to `coffee` and four words that might follow it, printing each probability beside the counts behind it, and then the sum over every word that followed `coffee`:

Example `next-word-probabilities` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Divides how often each of four words followed coffee by how often coffee was followed by anything, then prints the sum of the
probabilities of every word after coffee. The line for lamp, which prints 0.000, is the one the prose's point rests on:
the bigram model gives a pair it never counted no probability at all."""
from lib.bigrams import Bigrams
from lib.store import load_products

model = Bigrams(load_products("train")["name"])
after_coffee, total = model.counts["coffee"], model.totals["coffee"]   # counts[word] is a Counter of the words after word; totals[word] is their sum

for following in ["table", "mug", "jar", "lamp"]:
    print(f"P({following} | coffee): {after_coffee[following] / total:.3f}  ({after_coffee[following]} of {total})")   # a Counter returns 0 for a word never seen after coffee, not an error
print("sum over every word after coffee:", round(sum(n / total for n in after_coffee.values()), 6))   # rounded, so float error doesn't show in the sum
```

Output:

```text
P(table | coffee): 0.896  (1129 of 1260)
P(mug | coffee): 0.036  (45 of 1260)
P(jar | coffee): 0.010  (13 of 1260)
P(lamp | coffee): 0.000  (0 of 1260)
sum over every word after coffee: 1.0
```

The probabilities of every word that followed `coffee` add up to 1.0, as a distribution must, because whatever comes next is one of those words. `table` takes most of that probability, 0.896  (1129 of 1260), and `mug` far less, 0.036  (45 of 1260).

The fourth line is the one to remember. `coffee lamp` never occurs in the training names, so its probability is 0.000  (0 of 1260). The model doesn't say that a coffee lamp is unlikely; it says a coffee lamp is impossible. For a furniture store that's a reasonable bet, but the same zero applies to every pair the model hasn't seen, including perfectly ordinary ones. That's the flaw this chapter ends on.

**Working rule:** Derive probabilities from counts by division, and check that each word's probabilities sum to one; a sum that doesn't is a bug in the counting. Treat a probability as only as good as the count under it: 0.9 from 1,000 pairs is evidence, while 1.0 from a single pair is an anecdote.

## Suggest the next word as a shopper types {#suggest-next-words}

Autocomplete, the store's first need, wants the likeliest next words, and a probability table ranks them. A shopper who has typed `coffee` sees `table` first. With the bigram model, the suggestions for any typed text are the words with the highest probability after its last word. The bigram model's class, `Bigrams`, from [count which word follows which](#count-word-pairs), has a method, `next_words`, that returns them, likeliest first.

Five typed prefixes, from one word to two, show where the suggestions help and where they go wrong. Three suggestions come back for each:

Example `autocomplete` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Asks the bigram model for its three likeliest next words after five typed prefixes, then counts the training names that
contain outdoor door. The patio bar line, which gets the same suggestions as bar, is the one the prose's point rests on."""
from lib.bigrams import Bigrams
from lib.store import load_products

model = Bigrams(load_products("train")["name"])

for typed in ["coffee", "bar", "kitchen", "outdoor", "patio bar"]:
    last_word = typed.split()[-1]                    # the model reads only this word, so patio never reaches it
    suggestions = model.next_words(last_word, k=3)   # (word, probability) pairs, likeliest first
    print(f"{typed:<10} -> " + ", ".join(f"'{word}' {p:.2f}" for word, p in suggestions))

names = load_products("train")["name"]               # the training names as plain strings, for the substring counts
print("training names containing 'outdoor door':", sum("outdoor door" in n for n in names))   # a substring test, so `outdoor doors` counts too
print("of them, followed by 'mat':", sum("outdoor door mat" in n for n in names))   # the same test, with mat after them
```

Output:

```text
coffee     -> 'table' 0.90, 'mug' 0.04, ',' 0.02
bar        -> 'stool' 0.32, 'pull' 0.18, '&' 0.15
kitchen    -> 'sink' 0.17, 'island' 0.16, 'canister' 0.12
outdoor    -> 'door' 0.22, 'patio' 0.07, 'area' 0.06
patio bar  -> 'stool' 0.32, 'pull' 0.18, '&' 0.15
training names containing 'outdoor door': 215
of them, followed by 'mat': 214
```

After `coffee`, `bar` and `kitchen`, the top suggestions are what a shopper would want: tables, stools, sinks and islands. After `outdoor` they're weaker. The top suggestion, `door`, starts a real product type: 214 of the 215 training names containing `outdoor door` go on to `mat`. But a one-word suggestion can't offer a two-word product type, and after `door` the shares are small, because `outdoor` is followed by many different words. A comma and an ampersand also show up as suggestions, which no search box should offer. Filtering punctuation out of suggestions is a reasonable patch, and [chapter 2](#tokens) treats the cause.

The last line shows the model's real limit. A shopper who types `patio bar` gets exactly the suggestions for `bar`, because a bigram model looks at one word of context and nothing before it. `patio` is lost, so the model offers `pull` and `&`, which belong to cabinet hardware and to names such as `bar & counter stools`. Using more context is the subject of [chapter 3](#counting-further-back), and a model that weighs every earlier word is where the book is heading.

**Working rule:** For autocomplete, offer the top few next words by probability, and drop tokens that aren't words, such as punctuation. Expect a bigram model's suggestions to be good after words that are almost always followed by the same thing, such as `coffee`, and poor after words with many possible continuations, such as `outdoor`. When the earlier words matter, as they do in `patio bar`, a bigram model can't help, however much text it learns from.

## Generate names one word at a time {#generate-one-word-at-a-time}

The same probability table can write text as well as complete it. To **generate**, start at `<s>`, draw the next word at random in proportion to its probability, append it, and repeat from the word you drew, until the model draws `</s>`. Drawing at random, rather than always taking the likeliest word, is what lets the model produce varied names instead of the same one every time. The large language models this book builds toward write text the same way: one token at a time, each chosen from probabilities computed from the text so far.

Six names, drawn from those probabilities by a seeded random generator, come out the same on every run, so the names in this book match what the code produces:

Example `generate-names` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Draws six product names from the bigram model, one word at a time, with a fixed seed so the same six come out on every
run. The count of generated words never seen in training is the line the prose's point rests on."""
import numpy as np

from lib.bigrams import END, START, Bigrams
from lib.store import load_products, masked

model = Bigrams(load_products("train")["name"])
rng = np.random.default_rng(2026)                    # fixed seed: any seed gives six names, this one gives the book's


def generate(longest=12):                            # twelve words at most, if the end marker hasn't come first
    word, name = START, []
    while len(name) < longest:
        candidates = list(model.counts[word])        # the words seen after word: the only ones the model can draw
        chances = [model.probability(word, c) for c in candidates]
        word = candidates[rng.choice(len(candidates), p=chances)]   # choice returns an index into candidates, drawn with these chances
        if word == END:
            break
        name.append(word)
    return " ".join(name)


generated = [generate() for _ in range(6)]
print("\n".join(masked(name) for name in generated))   # masked shows each rare word, used in fewer than 30 training descriptions, as [name]; most are product lines' names
print("generated words never seen in training:", sum(w not in model.counts for name in generated for w in name.split()))   # every training word is a key, since each is followed by something
```

Output:

```text
waterproof table
long bistro set , dimmable led , smart dryer
[name] 3 '' wide genuine leather lounge chair
[name] kitchen cart
[name] pressure balanced tub door , french [name] panel post cap
[name] 68.75 '' wide armchair
generated words never seen in training: 0
```

Each adjacent pair of words is plausible, because each pair occurred in a real name: `genuine leather`, `kitchen cart`, `lounge chair`. The names as a whole often aren't, because nothing keeps a name on one product. One name runs from a bistro set to a dimmable light to a smart dryer, joined by commas, since after a comma almost anything can follow. The model has no memory beyond the last word, so it can't know it was describing a bistro set. Others attach a product line's name, printed as `[name]`, to a product of a different kind, such as a leather lounge chair, because names that start with a product line are common in the training text. Nothing is invented: a bigram model can only write words it counted, and the output confirms it, with 0 generated words that the training names don't contain.

Generated names make a model's limits visible in a way a number can't, which makes them worth reading. They don't measure anything, though: six names are too few to compare two models, and a reader's sense of "plausible" changes from day to day. The next section gives the number.

**Working rule:** Generate samples whenever you change a model, and read them, because they show failures that a score hides, such as text drifting from one product to another. Use a fixed seed so the samples are reproducible. Never compare models by their samples; compare them by perplexity on validation text.

## Score a model with perplexity {#score-with-perplexity}

A language model is good when it gives high probability to the text that actually occurs. That suggests a score: run the model over real text, and see how much probability it gave to each word that came next. The standard way to summarize this is **perplexity**, and this book uses it to compare every model it builds.

Start from one pair. If the model gave the actual next word probability p, its **surprise** at that word is −log p: zero when it was certain (p = 1) and larger the less it expected the word. The **cross-entropy** of a text is the average surprise over every word in it, written with N as the number of predicted words:

cross-entropy = −(1/N) Σ log P(next word | previous word)

**Perplexity** is that average turned back into a count: perplexity = exp(cross-entropy) ([Jurafsky and Martin, chapter 3](https://web.stanford.edu/~jurafsky/slp3/3.pdf)). It reads as the number of equally likely words the model was choosing between, on average, at each step. A perplexity of 10 means the model was, on average, as uncertain as if it had to pick among 10 equally likely words. Lower is better, and a model that knew every next word would score 1. This book uses natural logarithms throughout, which changes cross-entropy's units but not perplexity.

Score one training name, `sled coffee table`, pair by pair to see where its surprise sits, and then every training name at once:

Example `perplexity-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Scores the training name sled coffee table pair by pair, to show where its surprise sits, then scores every training name
at once. The printed line for P(sled | <s>), the largest surprise in the name, is the one the prose's point rests on."""
import math

from lib.bigrams import Bigrams, padded, perplexity
from lib.store import load_products

train = load_products("train")["name"]
model = Bigrams(train)

name = "sled coffee table"                  # a training name, so every pair in it has a count
tokens = padded(name)                       # the name with <s> and </s> around it, as in training
surprise = 0.0
for word, following in zip(tokens, tokens[1:]):   # tokens[1:] shifts the list one word on, so each pair is a word and the next
    p = model.probability(word, following)
    surprise += -math.log(p)                # natural log, so surprise is in nats, the units that exp() undoes
    print(f"P({following} | {word}) = {p:.4f}   -log P = {-math.log(p):.2f}")
print("average -log P:", round(surprise / (len(tokens) - 1), 3))   # pairs: one fewer than the tokens, one per word predicted, </s> included
print("perplexity of the name:", round(math.exp(surprise / (len(tokens) - 1)), 1))   # perplexity is exp of the average surprise
print("perplexity of every training name:", round(perplexity(model, train), 1))   # pooled over every pair in every name, not averaged name by name
```

Output:

```text
P(sled | <s>) = 0.0001   -log P = 8.83
P(coffee | sled) = 0.7846   -log P = 0.24
P(table | coffee) = 0.8960   -log P = 0.11
P(</s> | table) = 0.6903   -log P = 0.37
average -log P: 2.389
perplexity of the name: 10.9
perplexity of every training name: 16.9
```

Almost all the surprise falls on the first pair. Few names begin with `sled`, so the model was surprised by it, and after that each word was close to expected: `coffee` follows `sled` in most training names that contain `sled`, and `table` follows `coffee`. The name's average surprise is 2.389, and its perplexity 10.9. Over every training name, the model's perplexity is 16.9: on the text it learned from, it was choosing among about that many likely words at each step.

That number flatters the model, because it's measured on the text the counts came from. Every pair in the training names has a count, so no pair surprises the model infinitely. The real test is text it hasn't seen.

**Working rule:** Score every language model by its perplexity on validation text, computed exactly as above, with natural logarithms and every predicted word counted, the end marker included. Compare perplexities only between models that use the same tokens and the same validation text, since splitting text differently changes N and what counts as a word. Report training perplexity only beside validation perplexity, to show how much the model memorized.

## Unseen word pairs break the model {#unseen-pairs-break-the-model}

A model trained by counting knows only the pairs it has counted, and the validation names were kept apart from the training names for exactly this reason: they show what happens when the model meets text it never saw. The model scored 16.9 on the training names, in [score a model with perplexity](#score-with-perplexity). Before you run the next example, guess its perplexity on the 4,282 validation names.

Example `perplexity-on-new-names` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Scores the bigram model on the validation names, which it never learned from, then counts the pairs in them that never
occurred in training. The printed validation perplexity, which is infinite, is the line the prose's point rests on."""
from lib.bigrams import Bigrams, padded, perplexity
from lib.store import load_products, masked

model = Bigrams(load_products("train")["name"])
validation = load_products("validation")["name"]   # products the model never learned from

print("validation perplexity:", perplexity(model, validation))   # inf as soon as one pair has probability zero, rather than an error

pairs = [(w, f) for name in validation for w, f in zip(padded(name), padded(name)[1:])]   # each neighbouring pair in a padded name
unseen = [pair for pair in pairs if model.probability(*pair) == 0]   # probability is 0 for a pair the training names never contain
print("validation word pairs:", f"{len(pairs):,}")
print("pairs never seen in training:", f"{len(unseen):,}")
print("share never seen in training:", f"{len(unseen) / len(pairs):.0%}")
names_hit = sum(any(model.probability(*p) == 0 for p in zip(padded(n), padded(n)[1:])) for n in validation)   # a name counts once, if any of its pairs is unseen
print("names with an unseen pair:", f"{names_hit:,}")
print("validation names:", f"{len(validation):,}")
print("first unseen pairs:", ", ".join(masked(f"{w} {f}") for w, f in unseen[:3]))   # the first three in validation order, not the most common
```

Output:

```text
validation perplexity: inf
validation word pairs: 33,336
pairs never seen in training: 8,278
share never seen in training: 25%
names with an unseen pair: 3,724
validation names: 4,282
first unseen pairs: [name] [name], [name] 4, wood half-circle
```

The validation perplexity is infinite: the example prints inf. One pair the model gave probability zero is enough, because its surprise, −log 0, is infinite, and so is any average that includes it. And there isn't only one. 25% of the validation word pairs never occur in the training names, and 3,724 of the validation names contain at least one. The first unseen pairs show why: a validation name that starts with a product line the training names never mention, printed as `[name]`, makes both its first pair and its second unseen.

This is the flaw the [probabilities section](#counts-to-probabilities) warned about. Maximum likelihood gives every unseen pair probability zero, and in real text most new documents contain something unseen: a new product line, an unusual size, a familiar word in an unfamiliar place, such as `half-circle` after `wood`. More training text helps a little, but it can't solve the problem. Language keeps producing new combinations, so a model that calls every unseen combination impossible will always fail on new text.

The fix has to give unseen pairs some probability, which means taking a little away from the pairs the model has seen. That's called **smoothing**.

**Working rule:** Never trust a language model that gives zero probability to anything; check for infinite or undefined perplexity on validation text before you compare models. When you see one, count the unseen pairs, as above, to know how much of the text the model can't handle.

## Give unseen pairs a little probability {#smooth-unseen-pairs}

The model in [unseen word pairs break the model](#unseen-pairs-break-the-model) fails because it gives unseen pairs probability zero, and smoothing gives them some. The simplest smoothing method, **add-one smoothing**, pretends that every possible pair occurred once more than it did. Every count goes up by one, including the zeros, and the totals grow to match:

P(v | w) = (count(w v) + 1) / (count(w) + V)

where V is the size of the **vocabulary**, every word the model can predict. A word the training text doesn't contain at all is counted as one more vocabulary entry, `<unk>`, for unknown, so the probabilities still sum to one. No pair now has probability zero, so perplexity on new text is finite. The question is what it costs.

Two numbers show the cost, the probability of `table` after `coffee` and perplexity, under each model:

Example `add-one-smoothing` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.11:

```python
"""Compares the counted and add-one bigram models on one probability and on perplexity, to show what add-one smoothing
costs. The printed validation perplexity, add-one, is the line the prose's point rests on: it is finite, where the
counted model's is infinite."""
from lib.bigrams import Bigrams, perplexity
from lib.store import load_products

model = Bigrams(load_products("train")["name"])
train, validation = load_products("train")["name"], load_products("validation")["name"]   # the counts come from the training names; validation tests them

print("vocabulary:", f"{len(model.vocabulary):,}")   # every word the model can predict: training words, </s> and <unk>, but not <s>, which is never predicted
print("P(table | coffee) counted:", round(model.probability("coffee", "table"), 3))
print("P(table | coffee) add-one:", round(model.probability("coffee", "table", add_one=True), 3))   # add_one adds one to every count, and the vocabulary's size to every total
print("training perplexity, counted:", round(perplexity(model, train), 1))   # on the names the counts came from, so every pair has a count
print("training perplexity, add-one:", f"{perplexity(model, train, add_one=True):,.1f}")
print("validation perplexity, add-one:", f"{perplexity(model, validation, add_one=True):,.1f}")   # add-one gives no pair probability zero, so this is finite
```

Output:

```text
vocabulary: 25,909
P(table | coffee) counted: 0.896
P(table | coffee) add-one: 0.042
training perplexity, counted: 16.9
training perplexity, add-one: 1,232.8
validation perplexity, add-one: 1,575.1
```

The vocabulary holds 25,909 words, the end marker and `<unk>` included, and that's the problem. Add-one smoothing adds one imagined occurrence for every one of them after every word, so after `coffee` it imagines tens of thousands of extra pairs against about a thousand real ones.

The probability of `table` after `coffee` falls from 0.896 to 0.042. The model now believes far less in what it has seen, and the perplexities show it: on the training names, perplexity rises from 16.9 to 1,232.8.

The validation perplexity is finite, 1,575.1, which is progress, but the model gives so much probability to word pairs that never happen that its predictions are nearly useless.

Add-one smoothing fixes the infinity and breaks almost everything else, because it adds one imagined pair for every word in the vocabulary, however much evidence the real counts hold, and spreads them evenly. Better smoothing methods take far less probability away from seen pairs, and give it to unseen pairs in proportion to how often their words occur elsewhere. [Chapter 3](#counting-further-back) covers those methods. There, the counted model of this chapter, looking further back and with a better smoothing method, becomes the baseline that every later model in the book is measured against.

**Working rule:** Never ship a counted model without smoothing, and never ship one with add-one smoothing: measure validation perplexity and expect add-one to lose to every method in [chapter 3](#counting-further-back), which compares them on the same tokens. Use add-one only as this chapter does, to show that zero probabilities are fixable and that the fix needs care.

## What goes wrong in production {#next-word-in-production}

A bigram autocomplete is cheap and fast, and it's still a fair baseline for a search box. These are the problems that come with it:

- **The catalog moves on.** A model counted from last month's names doesn't know this month's product lines. A shopper who types a new product line gets no suggestions at all, because the model has no counts after it, until the counts are rebuilt, so rebuild them on a schedule and whenever the catalog changes.
- **Suggestions can embarrass.** The model suggests whatever followed a word in its training text, punctuation included. Filter suggestions through a list of allowed tokens, and review the most frequent suggestions by hand before they go live.
- **Popular products crowd out the rest.** A word followed by one product type most of the time, such as `coffee`, will always suggest that type. Shoppers looking for a coffee mug have to type more. Offer several suggestions, not one.
- **One word of context is too little.** As `patio bar` showed, the model ignores everything but the last word. If shoppers type long queries, measure how often the suggestions change once you condition on more of them, which [chapter 3](#counting-further-back) does.
- **The table grows with the text.** A bigram table has an entry for every pair ever seen; with longer contexts, the number of entries explodes. Count only what you need, and prune pairs seen once if memory is tight.

## What this chapter decided {#next-word-decisions}

- **The store's text is split once, by product, into training, validation and test splits, and models learn from the training split only.** A score on text a model learned from measures memory, not prediction, and splitting by product keeps near-duplicate names of one product from landing on both sides.
- **Every text is padded with `<s>` and `</s>`.** Models then learn how texts start and end, which autocomplete needs for a shopper's first word and generation needs to stop.
- **Models are compared by perplexity on validation text,** with natural logarithms and every predicted word counted, the end marker included. Generated samples are read for what they show, but never used to choose between models.
- **The bigram model of the store's product names, built from counts, is the book's first model.** It suggests good next words after words with one common continuation, such as `coffee`, and poor ones after words with many, such as `outdoor`. It sees one word of context, so `patio bar` and `bar` get the same suggestions.
- **Unsmoothed, the model's validation perplexity is infinite, and with add-one smoothing it's finite but poor.** [Chapter 3](#counting-further-back) gives it a better smoothing method, makes it the baseline, and keeps the same splits and the same measure, so every later model is compared with it on equal terms.
