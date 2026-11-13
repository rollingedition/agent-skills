import math
from collections import Counter

from lib.names import name_tokens
from lib.ngrams import ngrams, padded

train = name_tokens("train")
for n in [1, 2, 3, 4, 5]:
    pairs = Counter(pair for text in train for pair in ngrams(padded(text, n), n))
    contexts = Counter()
    for (context, _), count in pairs.items():
        contexts[context] += count
    surprise = -sum(count * math.log(count / contexts[context]) for (context, _), count in pairs.items())
    print(f"{n}-gram training perplexity: {math.exp(surprise / sum(pairs.values())):.1f}")
    print(f"{n}-grams seen once: {sum(1 for c in pairs.values() if c == 1) / len(pairs):.0%}")
