---
title: "Language Models from the Ground Up"
chapter: "Counting further back"
chapter_id: counting-further-back
book: language-models-from-the-ground-up
edition: 2026.11.12
verified: 2026-11-13
edition_code: J2AF-6HWB
canonical: https://rollingedition.com/language-models-from-the-ground-up/counting-further-back
license: CC BY 4.0
attribution: "“Counting further back,” chapter 3 of Language Models from the Ground Up, Edition 2026.11.12, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/counting-further-back. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Counting further back

By the end of this chapter you can build an n-gram language model that looks several tokens back, smooth it with Kneser-Ney so it handles text it hasn't seen (smoothing gives some probability to what the counts never saw, as chapter 1 showed), measure the baseline that every neural model in this book is measured against, and see why counting, however clever, runs out of road.

[Chapter 1](#predicting-the-next-word) built a model that predicted the next word from the one before it, and two things went wrong. It looked back only one word, so a shopper who typed `patio bar` got the suggestions for `bar`. And it gave probability zero to every pair of words it hadn't counted, which made its perplexity on new text infinite. [Chapter 2](#tokens) then gave the book better units to count: the store's tokenizer, which splits every word into pieces it knows, so almost every word is spelled from tokens it has seen. This chapter goes back to counting with those tokens, looks further back, and handles the unseen properly.

Every method here is tried where the store, an online furniture and home-goods shop, needs it: on the product names its search box completes. From this chapter on, every model in the book is scored the same way: by its [perplexity](#score-with-perplexity) per token on the store's [validation names](#words-leave-gaps), tokenized with the store's tokenizer. Product names are what the search box's autocomplete has to predict, and they're short enough for every example to run in seconds. One fixed text, one tokenizer and one measure make every model in the book comparable with every other on names; later chapters add descriptions, from [chapter 8](#training-a-small-model), and per-word scores, in [chapter 10](#inside-an-open-model), where a model's tokenizer differs.

## Longer contexts fit the training text better {#longer-contexts-fit-training}

An **n-gram model** predicts each token from the n − 1 tokens before it: a **bigram** model (n = 2) from one, a trigram model (n = 3) from two, and so on. The tokens before the one being predicted are its **context**. More context should mean better predictions: after `patio bar`, the next token is far more predictable than after `bar` alone. Counting works exactly as in [chapter 1](#predicting-the-next-word), except that the counts are now of a context of n − 1 tokens followed by a token, and each text is padded with n − 1 start markers, so even its first token has a full context.

Scored on the names they were counted from, with no smoothing, the orders show what a model does with text it has already memorized:

Example `ngram-memorizes` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Counts the n-grams of orders 1 to 5 in the training names, and scores each order on those same names with no smoothing.
Read the training perplexity lines, which fall as the order grows, against the seen-once lines, which rise."""
import math
from collections import Counter

from lib.names import name_tokens
from lib.ngrams import ngrams, padded

train = name_tokens("train")
for n in [1, 2, 3, 4, 5]:
    # padded adds n-1 start markers and one end marker, so a name's first token has a full context
    pairs = Counter(pair for text in train for pair in ngrams(padded(text, n), n))
    contexts = Counter()
    for (context, _), count in pairs.items():
        contexts[context] += count
    # the total surprise, in nats: each n-gram's probability is its count over its context's count, the model's own estimate
    surprise = -sum(count * math.log(count / contexts[context]) for (context, _), count in pairs.items())
    print(f"{n}-gram training perplexity: {math.exp(surprise / sum(pairs.values())):.1f}")
    print(f"{n}-grams seen once: {sum(1 for c in pairs.values() if c == 1) / len(pairs):.0%}")
```

Output:

```text
1-gram training perplexity: 676.4
1-grams seen once: 8%
2-gram training perplexity: 23.9
2-grams seen once: 60%
3-gram training perplexity: 4.9
3-grams seen once: 76%
4-gram training perplexity: 3.2
4-grams seen once: 82%
5-gram training perplexity: 2.9
5-grams seen once: 85%
```

Perplexity falls fast as the context grows: 676.4 with no context at all, 23.9 with one token, and 2.9 with four. At four tokens of context the model is choosing among about three tokens at each step, because most n-grams that long occur only once: 85% of the 5-grams in the training names are seen a single time, and the model has memorized what followed each.

That's the trap. On the text it counted, a longer context always looks better, because with enough context every text is unique and the model can recite it. Scoring a model on its own training text measures memory, which is why [chapter 1](#predicting-the-next-word) set aside validation text in the first place.

**Working rule:** Never judge an n-gram model, or any language model, by its perplexity on its own training text: it falls toward 1 as the model memorizes. Choose the order by perplexity on held-out text, as the rest of this chapter does.

## Longer contexts run out of evidence {#longer-contexts-run-out}

Memorizing the training names says nothing about new ones. A model can only use a context it has counted, and the number of possible contexts grows exponentially with their length: with four thousand tokens, there are sixteen million possible pairs and sixty-four billion possible triples. No training text comes close to covering them. So the longer the context, the more often a new text uses one the model has never seen.

Settle on a number first: for 4-grams, what share of the validation names' 4-grams never occur in the training names? The share for every order from 1 to 5 follows:

Example `unseen-ngrams` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Counts, for each order from 1 to 5, the share of the validation names' n-grams that never occur in the training names.
Compare the lines for 2-grams to 5-grams: that share rises with the order."""
from lib.names import name_tokens
from lib.ngrams import ngrams, padded

train, validation = name_tokens("train"), name_tokens("validation")
print("training tokens:", f"{sum(len(t) for t in train):,}")
print("validation tokens:", f"{sum(len(t) for t in validation):,}")
for n in [1, 2, 3, 4, 5]:
    seen = {pair for text in train for pair in ngrams(padded(text, n), n)}     # padded, as in the model, so name starts count too
    held_out = [pair for text in validation for pair in ngrams(padded(text, n), n)]
    unseen = sum(pair not in seen for pair in held_out)
    print(f"{n}-grams in validation never seen in training: {unseen / len(held_out):.1%}")
```

Output:

```text
training tokens: 337,071
validation tokens: 42,422
1-grams in validation never seen in training: 0.1%
2-grams in validation never seen in training: 12.7%
3-grams in validation never seen in training: 31.1%
4-grams in validation never seen in training: 43.9%
5-grams in validation never seen in training: 53.4%
```

The longer the context, the more of the validation names' n-grams are new. Only 0.1% of the validation tokens are unseen, which is the store's tokenizer doing its job. Among validation bigrams, 12.7% are unseen, 43.9% of the 4-grams and 53.4% of the 5-grams. With four tokens of context, the model has never seen more than half of what it needs to predict.

More training text helps less than you might hope. In language, a few n-grams occur very often and most occur rarely, so each doubling of the text adds mostly n-grams seen once or twice, which barely improve the counts behind any one prediction. The store's catalog shows the same pattern in miniature: a common phrase such as `coffee table` is counted more than a thousand times, while 82% of the training names' 4-grams are counted once. Our judgement, not a measurement, is that a catalog ten times as large would still leave a large share of new 4-grams unseen, because new product lines and new combinations of sizes and materials keep appearing.

The two examples together are the core problem of counting. Longer contexts predict better when they've been seen, and are seen less and less often. Every method in the rest of this chapter is a way to use long contexts when the counts support them, and fall back to shorter ones when they don't.

**Working rule:** Before choosing an n-gram order, measure the share of held-out n-grams your training text never contains. As a rule of thumb, where it nears a third, as it does for trigrams in the store's names, a model of that order depends mostly on how it handles the unseen, so its smoothing matters more than its order.

## Mix short and long contexts {#mix-short-and-long-contexts}

The obvious fix for unseen long contexts is to fall back on shorter ones. **Interpolation** does it smoothly: the probability of a token is a weighted mix of what the trigram, bigram and unigram counts say, so a long context the model has seen contributes its sharp prediction, and the shorter ones fill in what it hasn't. With weights λ₃, λ₂ and λ₁ that sum to one:

P(token | a b) = λ₃ · P₃(token | a b) + λ₂ · P₂(token | b) + λ₁ · P₁(token)

where each P is a maximum-likelihood estimate from counts, as in [chapter 1's probabilities](#counts-to-probabilities). Chen and Goodman's study of smoothing methods covers interpolation and its variants in detail ([Chen and Goodman, 1996](https://aclanthology.org/P96-1041/)).

Hand-set weights make the idea plain. Take an interpolated trigram with 0.6, 0.3 and 0.09 for the three orders, and the last 0.01 spread evenly over every token, so no token gets probability zero. When a context was never seen, its weight passes to the orders below, so the probabilities still sum to one:

Example `interpolate-orders` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Builds an interpolated trigram model by hand, with fixed weights, and an add-one bigram model on the same tokens.
The two validation perplexity lines to compare are the interpolated trigram's and the add-one bigram's."""
import math
from collections import Counter

from lib.names import name_tokens
from lib.ngrams import ngrams, padded, perplexity

train, validation = name_tokens("train"), name_tokens("validation")
counts = {k: Counter() for k in (1, 2, 3)}             # counts[k][(the k-1 tokens before, token)]
for text in train:
    for context, token in ngrams(padded(text, 3), 3):
        for k in (1, 2, 3):
            # a trigram's context holds two tokens; an order-k model conditions on the last k-1 of them
            counts[k][(context[3 - k:], token)] += 1
totals = {k: Counter() for k in (1, 2, 3)}
for k in (1, 2, 3):
    for (context, _), count in counts[k].items():
        totals[k][context] += count
# the tokens the training names contain, plus one slot for a token they never contain
vocabulary = len({token for (_, token) in counts[1]}) + 1
weights = {3: 0.6, 2: 0.3, 1: 0.09}                   # and 0.01 spread evenly over every token


class Interpolated:
    n = 3

    def probability(self, context, token):
        p, carried = 0.0, 0.0
        for k in (3, 2, 1):
            # each order's own context
            weight, total = weights[k] + carried, totals[k][context[3 - k:]]
            if total:                                    # an unseen context passes its weight down
                p, carried = p + weight * counts[k][(context[3 - k:], token)] / total, 0.0
            else:
                carried = weight
        # the even 0.01 share, plus any weight passed down from unseen contexts, over the vocabulary
        return p + (0.01 + carried) / vocabulary


print("interpolated 3-gram validation perplexity:", round(perplexity(Interpolated(), validation), 1))

# a bigram's context is the one token before the token
bigram_pairs = Counter((context[-1:], token) for text in train for context, token in ngrams(padded(text, 2), 2))
bigram_totals = Counter()
for (context, _), count in bigram_pairs.items():
    bigram_totals[context] += count


class AddOne:
    n = 2

    def probability(self, context, token):
        # add-one: one added to every pair's count, and one per vocabulary token added to the total
        return (bigram_pairs[(context, token)] + 1) / (bigram_totals[context] + vocabulary)


print("add-one 2-gram validation perplexity:", round(perplexity(AddOne(), validation), 1))
```

Output:

```text
interpolated 3-gram validation perplexity: 31.4
add-one 2-gram validation perplexity: 218.6
```

Mixing orders beats [chapter 1's add-one smoothing](#smooth-unseen-pairs). For a fair comparison, add-one here runs on a bigram model of the same validation tokens, since perplexities over different tokens can't be compared. The interpolated trigram scores 31.4, and add-one scores 218.6. Add-one spreads most of its probability over pairs that never happen; mixing orders keeps what each order knows.

It has two weaknesses. The weights are fixed, and these were picked by hand, not tuned: the same 0.6 goes to the trigram whether its context was seen once or a thousand times, though a context seen a thousand times deserves more trust. And the unigram part gives each token probability in proportion to how often it occurs, which, as the next section shows, is the wrong question for a fallback.

**Working rule:** Never use a single n-gram order alone; always combine it with lower orders, so every token keeps some probability. Prefer methods that set each context's weight from its counts, such as Kneser-Ney below, over fixed weights. If you do use fixed weights, choose them on held-out text, not the text you counted.

## Count the contexts a token follows {#count-contexts-a-token-follows}

When a model backs off to a shorter context, it's asking a specific question: how likely is this token to show up in a context we haven't seen? Raw frequency answers a different one. A token can be very common and still occur only after one or two particular tokens, and such a token is a poor guess for a new context. The better measure is the number of different tokens it follows, its **continuation count**: a token that has followed many different tokens is likely to follow a new one too.

Among the 300 most frequent tokens in the training names, these three come after the fewest different tokens for how often they occur, set beside two ordinary product words:

Example `continuation-counts` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Counts, for each token in the training names, how often it occurs and how many different tokens come right before it.
Look at the three narrowest tokens, which occur often but follow few different tokens, beside table and chair."""
from collections import Counter, defaultdict

from lib.names import name_tokens

occurrences, before = Counter(), defaultdict(set)
for text in name_tokens("train"):
    for previous, token in zip(["<s>"] + text, text):      # the start marker stands before each name's first token, so that token has something to follow too
        occurrences[token] += 1
        before[token].add(previous)                 # the different tokens this one follows

common = [t for t, _ in occurrences.most_common(300)]     # the 300 most frequent tokens: the pool the prose ranks
# different tokens followed, per occurrence, lowest first: the three narrowest
narrow = sorted(common, key=lambda t: len(before[t]) / occurrences[t])[:3]
for token in narrow + ["table</w>", "chair</w>"]:       # </w> marks a token that ends a word, as the store's tokenizer writes it
    print(f"{token:<14} occurs {occurrences[token]:>5,} times, after {len(before[token]):>4,} different tokens")
```

Output:

```text
tvs</w>        occurs   323 times, after    1 different tokens
wide</w>       occurs 1,985 times, after   14 different tokens
''</w>         occurs 10,335 times, after   85 different tokens
table</w>      occurs 3,487 times, after  154 different tokens
chair</w>      occurs 2,791 times, after  138 different tokens
```

The token `tvs` occurs hundreds of times, after only one other token: in the store's names it's always part of the same phrase, in products made for TVs. A model that backed off to raw frequency would think `tvs` a reasonable guess anywhere, and it almost never is. `wide` follows only a handful of tokens, mostly numbers' inch marks, and the inch mark itself, `''`, follows mostly digits. Meanwhile `table` and `chair` each follow well over a hundred different tokens: `coffee table`, `side table`, `outdoor table`. Their continuation counts say what their frequency doesn't: they turn up after well over a hundred different tokens.

Continuation counts are cheap to compute: for each token, keep the set of tokens seen before it, and count the set. They need no extra text and no tuning, only a different question asked of the same counts, and the next section builds on them.

This is the insight behind Kneser-Ney smoothing ([Kneser and Ney, 1995](https://doi.org/10.1109/ICASSP.1995.479394)): when the model falls back to a shorter context, it uses continuation counts instead of raw counts, so tokens that appear in many contexts get the probability, and tokens that appear in one fixed phrase don't.

**Working rule:** Weight tokens by how many different contexts they follow, not by how often they occur, whenever you back off from a long context to a short one. Use raw counts only at the highest order, where the context has actually been seen.

## Smooth with Kneser-Ney {#smooth-with-kneser-ney}

Kneser-Ney smoothing combines [interpolation of orders](#mix-short-and-long-contexts) with [continuation counts](#count-contexts-a-token-follows). At each order, it subtracts a fixed **discount** d from every count it has seen, and gives the probability it took to the next order down, so a context seen often keeps nearly all its own prediction, and a context seen rarely leans on the shorter context, with the discount it frees going to tokens that turn up in many contexts.

The same formula applies at every order. Below the highest, the counts are continuation counts, except for n-grams that start a text, which keep their raw counts, as the KenLM toolkit does. For a context h and a token w, with c(h w) the count of the pair, c(h) the count of the context, and N(h) the number of different tokens seen after h:

P(w | h) = max(c(h w) − d, 0) / c(h) + d · N(h) / c(h) · P(w | shorter h)

The book's shared module `lib.ngrams` implements interpolated Kneser-Ney as Chen and Goodman describe it ([Chen and Goodman, 1999](https://doi.org/10.1006/csla.1999.0128)), with a discount of 0.75, a common default. Its lowest order mixes in a uniform share over the vocabulary, so even a token never seen in training keeps a small probability.

Before trusting the module, work out one probability by hand: `stool` after a name that starts `patio bar`, order by order. Set it beside the module's answer, and beside the module's probabilities after this context, summed over every token:

Example `kneser-ney-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Works out the probability of stool after a name that starts patio bar, order by order, with the chapter's formula.
It checks the result against lib.ngrams and against the module's probabilities summed over the vocabulary: the
by hand line should match the lib.ngrams line, and the summed line should be a probability distribution's total."""
from lib import bpe
from lib.names import name_tokens
from lib.ngrams import START, KneserNey

model = KneserNey(name_tokens("train"), 4)     # a 4-gram model; below the top order its counts are continuation counts, except for n-grams that start a name
context = tuple([START] + bpe.store_tokenizer().encode("patio bar"))     # a name that starts "patio bar"
token, d = "stool</w>", model.d                # </w> ends a word; d is the discount, 0.75 by default


def by_hand(context, k):                         # the chapter's formula, one order at a time
    if k == 0:
        return 1 / (len(model.vocabulary) + 1)   # order 0 is uniform over the vocabulary, with one more slot for an unseen token
    context = context[len(context) - (k - 1):] if k > 1 else ()     # the last k-1 tokens: the order-k model's own context
    following, total = model.counts[k][context], model.totals[k].get(context, 0)
    if total == 0:
        return by_hand(context, k - 1)           # a context never seen gives all its weight to the order below
    kept = max(following[token] - d, 0) / total                  # the discounted count
    passed_down = d * len(following) / total                     # what the discount frees for the order below
    print(f"order {k}: kept {kept:.4f}, passed down {passed_down:.4f}")
    return kept + passed_down * by_hand(context, k - 1)


print("by hand:", f"{by_hand(context, 4):.4f}")
print("lib.ngrams:", f"{model.probability(context, token):.4f}")
total = sum(model.probability(context, t) for t in model.vocabulary)
print("probabilities after the context, summed:", f"{total:.4f}")
```

Output:

```text
order 4: kept 0.2500, passed down 0.7500
order 3: kept 0.8056, passed down 0.1667
order 2: kept 0.0630, passed down 0.1275
order 1: kept 0.0007, passed down 0.0318
by hand: 0.8621
lib.ngrams: 0.8621
probabilities after the context, summed: 1.0000
```

Worked by hand, the formula gives 0.8621 for `stool`, the same as the module's 0.8621. Each order keeps a share and passes the rest down; the shares add up to that answer. Over every token in the vocabulary, the module's probabilities after this context sum to 1.0000, as a probability distribution must.

Kneser-Ney models of every order from 1 to 5, scored on the validation names, show whether longer contexts now pay off:

Example `kneser-ney-by-order` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Builds Kneser-Ney models of orders 1 to 5 on the training names, scores each on the validation names, and estimates a
discount from the 4-gram counts. The lines to read are the validation perplexities, the 3-gram's set against the interpolated trigram's, and the discount line."""
from lib.names import name_tokens
from lib.ngrams import KneserNey, perplexity

train, validation = name_tokens("train"), name_tokens("validation")
for n in [1, 2, 3, 4, 5]:
    model = KneserNey(train, n)
    print(f"{n}-gram validation perplexity: {perplexity(model, validation):.1f}")

model = KneserNey(train, 4)
# the highest order keeps raw counts, not continuation counts, so these are how often each 4-gram occurs in training
top = [c for following in model.counts[4].values() for c in following.values()]
once, twice = top.count(1), top.count(2)
print("4-grams seen once:", f"{once:,}")
print("4-grams seen twice:", f"{twice:,}")
# Chen and Goodman's estimate of the discount: D = n1 / (n1 + 2 n2), with n1 and n2 the counts seen once and twice
print("discount estimated from them:", f"{once / (once + 2 * twice):.2f}")
```

Output:

```text
1-gram validation perplexity: 687.2
2-gram validation perplexity: 46.9
3-gram validation perplexity: 24.9
4-gram validation perplexity: 23.1
5-gram validation perplexity: 23.5
4-grams seen once: 164,374
4-grams seen twice: 18,359
discount estimated from them: 0.82
```

Kneser-Ney beats the hand-weighted interpolated trigram from the [interpolation section](#mix-short-and-long-contexts) at the same order, with no weights to choose. Its trigram scores 24.9, against 31.4 for the hand-weighted one.

Longer contexts now help on new text, instead of only on the text the model counted, up to a point: validation perplexity falls from 46.9 for the bigram to 23.1 for the 4-gram, then rises to 23.5 for the 5-gram. The step from trigram to 4-gram is small, and the 5-gram is worse, because by then most contexts are unseen and the extra order adds noise. The discount, too, can be estimated from the counts: Chen and Goodman give D = n₁ / (n₁ + 2 n₂), where n₁ and n₂ are the numbers of n-grams seen once and twice, and on the store's 4-grams it's 0.82, close to the default.

**Working rule:** Smooth n-gram models with interpolated Kneser-Ney and a discount of 0.75 unless held-out text says otherwise. Raise the order only while validation perplexity keeps falling noticeably, and stop when a step barely helps or hurts, as the step from 4-gram to 5-gram does. A variant, modified Kneser-Ney, uses three discounts instead of one and is the one toolkits such as KenLM build; it would likely lower the baseline a little, and this book keeps the single discount because it's easier to follow by hand.

## Autocomplete with three tokens of context {#autocomplete-with-more-context}

A longer context should fix the search box's worst suggestion from [chapter 1](#predicting-the-next-word), where `patio bar` got the same suggestions as `bar`. The 4-gram Kneser-Ney model sees the last three tokens a shopper typed, so `patio` stays in view.

Do the suggestions change from `bar` to `patio bar` to `outdoor bar`? Take the 4-gram model's three likeliest next tokens after each. Each prefix is treated as the start of a name, as a shopper's typing is, and each suggestion shows its token without the end-of-word marker:

Example `ngram-autocomplete` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.12:

```python
"""Asks the 4-gram model for its three likeliest next tokens after bar, patio bar and outdoor bar, each typed as the start
of a name, then counts the training names that contain outdoor bar. The three suggestion lines carry the point, and the last line
counts the training names with outdoor bar in them."""
from lib import bpe
from lib.names import name_tokens
from lib.ngrams import START, KneserNey

model = KneserNey(name_tokens("train"), 4)
tokenizer = bpe.store_tokenizer()
candidates = sorted(model.vocabulary)       # sorted first, so tokens with equal probability keep alphabetical order

for typed in ["bar", "patio bar", "outdoor bar"]:
    # padded with start markers, then the last three tokens: a short prefix still gives a full context
    context = tuple([START] * 3 + tokenizer.encode(typed))[-3:]
    ranked = sorted(candidates, key=lambda t: -model.probability(context, t))[:3]     # negated, so the likeliest sort first
    print(f"{typed:<12} -> " + ", ".join(f"{t.replace('</w>', '')} {model.probability(context, t):.2f}" for t in ranked))
# each name as one string of tokens, so the check below matches whole tokens rather than parts of them
names = [" ".join(t) for t in name_tokens("train")]
print("training names containing 'outdoor bar':", sum("outdoor</w> bar</w>" in n for n in names))
```

Output:

```text
bar          -> & 0.23, unit 0.13, with 0.11
patio bar    -> stool 0.86, & 0.03, with 0.02
outdoor bar  -> & 0.23, with 0.19, stool 0.06
training names containing 'outdoor bar': 0
```

After `bar` alone, the model suggests continuations such as `&` and `with`, which belong to names that start like `bar & counter stools`; [chapter 1](#predicting-the-next-word)'s bigram, which ignored where the word sat, suggested `stool` first. After `patio bar`, it suggests `stool` with high probability: the context changed the prediction, which a bigram model can't do. After `outdoor bar`, though, the suggestions drift back toward `&` and `with`, because no training name contains `outdoor bar`, as the example's last line shows, and the model backs off to what follows `bar`.

Suggestions such as `&` and `with` are real continuations of the store's names, but a shopper rarely wants them offered. A search box would filter them out, as [chapter 1](#predicting-the-next-word) suggested for punctuation, or complete to whole phrases instead of single tokens. That's a choice about presentation; the model's probabilities are the same either way.

The `outdoor bar` line is the limit of counting in miniature. The model has seen `patio bar stool` and `outdoor patio` and `bar stool` many times, so it has the pieces to guess that an outdoor bar probably comes with stools. But a count of `outdoor bar stool` is a separate entry in a table, and nothing connects it to `patio bar stool`. A model needs some notion that `outdoor` and `patio` are alike, which counting doesn't have. [Chapter 4](#words-as-vectors) gives the store's tokens that notion.

**Working rule:** Use the longest context your model can support for suggestions, and check suggestions for contexts that are rare in training, such as `outdoor bar`, separately from common ones: that's where a counted model falls back to generic guesses.

## The baseline every later model is measured against {#the-baseline}

Every chapter from here on builds a model that learns, not one that counts, and each claims to predict the store's text better. A claim like that needs a fixed yardstick: one model, one text, one tokenizer and one measure that every later model is compared against. That's a **baseline**, and it should be the strongest simple model available, so that beating it means something.

The baseline for this book is the 4-gram Kneser-Ney model of this chapter, scored on the store's validation names with the store's tokenizer. Its validation perplexity is 23.1 per token, from the [Kneser-Ney example](#smooth-with-kneser-ney). The 5-gram model is worse, at 23.5, and holds more counts, so the 4-gram is the baseline: the best of this chapter's counted models on the store's names. A stronger counted baseline exists, modified Kneser-Ney, and the book doesn't use it, for the reason the [Kneser-Ney section](#smooth-with-kneser-ney) gives.

The baseline also sets expectations. A perplexity near twenty means the model is, on average, choosing among about twenty likely tokens at each step of a product name. Some steps are nearly certain, such as `table` after `coffee`, and some are wide open, such as the first token of a product line's name. A neural model that beats the baseline should do so by predicting the open steps better, because it can relate one context to another, not by memorizing more.

Two things about the baseline will stay fixed for the rest of the book. Every perplexity is per token of the store's tokenizer, on the validation names, so the numbers in every chapter can be set side by side. And the test names stay untouched until the book's final comparison, so nothing in the book is tuned on them.

**Working rule:** Before building a learned model, build the strongest counted model you can and record its held-out perplexity as the baseline. Report every later model against it, on the same text and with the same tokenizer, and treat a learned model that doesn't beat it as a result to explain, never as a success. Later chapters find exactly that, and earn the learned models their place another way.

## What goes wrong in production {#ngrams-in-production}

N-gram models are still useful where speed and transparency matter more than the last point of perplexity, such as fast autocomplete. These are the problems they bring:

- **The tables grow.** Every order adds another table of counts, and the number of distinct n-grams grows almost as fast as the text. Prune n-grams seen once, and measure validation perplexity after pruning, since some rare n-grams carry real information.
- **Rare contexts get generic answers.** As `outdoor bar` showed, a context the model rarely saw falls back to what the shorter context suggests. Monitor the suggestions for rare prefixes, not only the common ones.
- **The discount is a choice.** A discount of 0.75 is a sound default, not a law. If your text differs a lot from the store's, tune it on held-out text.
- **New text changes the counts.** Product lines come and go, and the counts behind every suggestion are only as current as the last rebuild. Rebuild on a schedule, and compare validation perplexity on recent text to the baseline to see when the model has gone stale.
- **The probabilities must sum to one.** Hand-written backoff schemes often lose or double-count probability, which makes perplexity look better or worse than it is. Check, on a few contexts, that each one's probabilities over the vocabulary sum to one.

## What this chapter decided {#ngrams-decisions}

- **Every model in the book is scored by perplexity per token on the store's validation names, through the store's tokenizer.** One text, one tokenizer and one measure make every chapter's numbers comparable on names, and the test names are kept for the book's final comparison, in [chapter 11](#look-back-at-the-yardstick).
- **N-gram models are smoothed with interpolated Kneser-Ney, discount 0.75.** It beat hand-weighted interpolation at the same order, with no weights to tune, because it trusts each context in proportion to its counts and backs off to tokens that follow many contexts.
- **The baseline is the 4-gram Kneser-Ney model,** at 23.1 per token on the validation names. The 5-gram model scores worse and holds more counts, so the 4-gram is the yardstick.
- **Autocomplete uses the 4-gram model's suggestions, with three tokens of context.** It fixes `patio bar`, and still falls back to generic suggestions for rare contexts such as `outdoor bar`, which is where a learned model has to do better.
- **Longer contexts stop helping because they're unseen, not because they don't matter.** More than half of the validation names' 5-grams never occur in training, and the model can't relate an unseen context to similar seen ones. [Chapter 4](#words-as-vectors) starts on that problem, by giving tokens vectors that say which ones are alike.
