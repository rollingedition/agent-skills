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
