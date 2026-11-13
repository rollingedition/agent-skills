"""Splits the validation tokens by whether their three-token context occurs in the training names, and scores both models
on each part. The prose's point rests on the four perplexities printed for the two parts."""
import math

import numpy as np

from lib import neural
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

train, validation = name_tokens("train"), name_tokens("validation")
counted = KneserNey(train, 4)
pairs = [(c, t) for text in validation for c, t in ngrams(padded(text, 4), 4)]   # padding gives each name's first tokens a context
seen = np.array([c in counted.totals[4] for c, _ in pairs])     # was this 3-token context in the training names?
from_counts = np.array([counted.probability(c, t) for c, t in pairs])
from_network = neural.token_probabilities(validation)           # in the same order as pairs, so each entry is for the same token

print("validation tokens with a context seen in training:", f"{seen.mean():.0%}")
for part, where in [("seen", seen), ("unseen", ~seen)]:                  # ~seen: the complement, the contexts the training names lack
    for model, p in [("4-gram", from_counts), ("network", from_network)]:
        print(f"{model} perplexity, {part} contexts: {math.exp(-np.log(p[where]).mean()):.1f}")   # exp of the average surprise, over this part
