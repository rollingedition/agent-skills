"""Scores the five models the book chose between on the test names, each name's tokens and its end, and prints each
model's test perplexity. The prose's point rests on the five test perplexity lines.
"""
import numpy as np

from lib import neural, transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

# The test names, untouched until now: every model scores each name's tokens and its end. The mixing shares are the
# ones chosen on the validation names, in chapters 5 and 8.
test = name_tokens("test")
counted = KneserNey(name_tokens("train"), 4)
# padded adds the start marker three times and the end marker, so each name's first tokens have a context and its end is scored
from_counts = np.array([counted.probability(c, t) for text in test for c, t in ngrams(padded(text, 4), 4)])
from_window = neural.token_probabilities(test)
_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
from_transformer = []
for name in test:
    # the transformer reads the start marker, the name, then <sep>, which ends a name where the counts end with </s>
    ids = [index[transformer.START]] + [index[t] for t in name] + [index[transformer.SEP]]
    probabilities = transformer.softmax(transformer.forward(ids)[:-1])
    # position i predicts token i + 1, so ids[1:] is each token's target, the end of the name included
    from_transformer += list(probabilities[np.arange(len(ids) - 1), ids[1:]])
from_transformer = np.array(from_transformer)

# pooled over every token of every name, not averaged per name
perplexity = lambda p: f"{np.exp(-np.log(p).mean()):.1f}"
print("test names:", f"{len(test):,}")
print("test perplexity, the 4-gram baseline:", perplexity(from_counts))
print("test perplexity, the window model:", perplexity(from_window))
# the mix averages the probabilities, not their logs: a share of 0.2 is 20% of the window model
print("test perplexity, the window model mixed with the counts, share 0.2:", perplexity(0.2 * from_window + 0.8 * from_counts))
print("test perplexity, the store's transformer:", perplexity(from_transformer))
print("test perplexity, the store's transformer mixed with the counts, share 0.5:", perplexity((from_transformer + from_counts) / 2))
