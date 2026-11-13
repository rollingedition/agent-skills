"""Mixes the network's and the 4-gram's probability of every validation token, at five shares for the network, and prints
the validation perplexity of each mix. The prose's point rests on the printed perplexity at share 0.2, and at the two ends."""
import math

import numpy as np

from lib import neural
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

train, validation = name_tokens("train"), name_tokens("validation")
from_network = neural.token_probabilities(validation)           # the network's probability of each actual next token, in order
counted = KneserNey(train, 4)
# the 4-gram's probability for the same tokens, in the same order: each name padded with three start markers first
from_counts = np.array([counted.probability(c, t) for text in validation for c, t in ngrams(padded(text, 4), 4)])

for share in [0.0, 0.2, 0.3, 0.5, 1.0]:                # the network's share of the mix; the counts get the rest
    mixed = share * from_network + (1 - share) * from_counts
    print(f"validation perplexity, network share {share:.1f}: {math.exp(-np.log(mixed).mean()):.1f}")
