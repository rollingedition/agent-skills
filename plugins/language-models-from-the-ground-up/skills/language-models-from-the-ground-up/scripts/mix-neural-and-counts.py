import math

import numpy as np

from lib import neural
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

train, validation = name_tokens("train"), name_tokens("validation")
from_network = neural.token_probabilities(validation)
counted = KneserNey(train, 4)
from_counts = np.array([counted.probability(c, t) for text in validation for c, t in ngrams(padded(text, 4), 4)])

for share in [0.0, 0.2, 0.3, 0.5, 1.0]:                # the network's share of the mix; the counts get the rest
    mixed = share * from_network + (1 - share) * from_counts
    print(f"validation perplexity, network share {share:.1f}: {math.exp(-np.log(mixed).mean()):.1f}")
