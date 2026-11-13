import numpy as np

from lib import neural, transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

# The test names, untouched until now: every model scores each name's tokens and its end. The mixing shares are the
# ones chosen on the validation names, in chapters 5 and 8.
test = name_tokens("test")
counted = KneserNey(name_tokens("train"), 4)
from_counts = np.array([counted.probability(c, t) for text in test for c, t in ngrams(padded(text, 4), 4)])
from_window = neural.token_probabilities(test)
_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
from_transformer = []
for name in test:
    ids = [index[transformer.START]] + [index[t] for t in name] + [index[transformer.SEP]]
    probabilities = transformer.softmax(transformer.forward(ids)[:-1])
    from_transformer += list(probabilities[np.arange(len(ids) - 1), ids[1:]])
from_transformer = np.array(from_transformer)

perplexity = lambda p: f"{np.exp(-np.log(p).mean()):.1f}"
print("test names:", f"{len(test):,}")
print("test perplexity, the 4-gram baseline:", perplexity(from_counts))
print("test perplexity, the window model:", perplexity(from_window))
print("test perplexity, the window model mixed with the counts, share 0.2:", perplexity(0.2 * from_window + 0.8 * from_counts))
print("test perplexity, the store's transformer:", perplexity(from_transformer))
print("test perplexity, the store's transformer mixed with the counts, share 0.5:", perplexity((from_transformer + from_counts) / 2))
