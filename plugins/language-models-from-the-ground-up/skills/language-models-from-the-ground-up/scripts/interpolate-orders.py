import math
from collections import Counter

from lib.names import name_tokens
from lib.ngrams import ngrams, padded, perplexity

train, validation = name_tokens("train"), name_tokens("validation")
counts = {k: Counter() for k in (1, 2, 3)}             # counts[k][(the k-1 tokens before, token)]
for text in train:
    for context, token in ngrams(padded(text, 3), 3):
        for k in (1, 2, 3):
            counts[k][(context[3 - k:], token)] += 1
totals = {k: Counter() for k in (1, 2, 3)}
for k in (1, 2, 3):
    for (context, _), count in counts[k].items():
        totals[k][context] += count
vocabulary = len({token for (_, token) in counts[1]}) + 1
weights = {3: 0.6, 2: 0.3, 1: 0.09}                   # and 0.01 spread evenly over every token


class Interpolated:
    n = 3

    def probability(self, context, token):
        p, carried = 0.0, 0.0
        for k in (3, 2, 1):
            weight, total = weights[k] + carried, totals[k][context[3 - k:]]
            if total:                                    # an unseen context passes its weight down
                p, carried = p + weight * counts[k][(context[3 - k:], token)] / total, 0.0
            else:
                carried = weight
        return p + (0.01 + carried) / vocabulary


print("interpolated 3-gram validation perplexity:", round(perplexity(Interpolated(), validation), 1))

bigram_pairs = Counter((context[-1:], token) for text in train for context, token in ngrams(padded(text, 2), 2))
bigram_totals = Counter()
for (context, _), count in bigram_pairs.items():
    bigram_totals[context] += count


class AddOne:
    n = 2

    def probability(self, context, token):
        return (bigram_pairs[(context, token)] + 1) / (bigram_totals[context] + vocabulary)


print("add-one 2-gram validation perplexity:", round(perplexity(AddOne(), validation), 1))
