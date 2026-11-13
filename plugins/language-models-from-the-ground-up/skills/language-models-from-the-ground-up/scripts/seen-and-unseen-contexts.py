import math

import numpy as np

from lib import neural
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

train, validation = name_tokens("train"), name_tokens("validation")
counted = KneserNey(train, 4)
pairs = [(c, t) for text in validation for c, t in ngrams(padded(text, 4), 4)]
seen = np.array([c in counted.totals[4] for c, _ in pairs])     # was this 3-token context in the training names?
from_counts = np.array([counted.probability(c, t) for c, t in pairs])
from_network = neural.token_probabilities(validation)

print("validation tokens with a context seen in training:", f"{seen.mean():.0%}")
for part, where in [("seen", seen), ("unseen", ~seen)]:
    for model, p in [("4-gram", from_counts), ("network", from_network)]:
        print(f"{model} perplexity, {part} contexts: {math.exp(-np.log(p[where]).mean()):.1f}")
