"""Scores every validation name, its end included, with the 4-gram baseline and with the transformer, then mixes them
at several shares. The prose's point rests on the share 0.5 line, the lowest of the five."""
import numpy as np

from lib import transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}   # each token's id in the vocabulary, which is its column in the model's output
counted = KneserNey(name_tokens("train"), 4)                     # chapter 3's baseline, trained on names
from_counts, from_transformer = [], []
for name in name_tokens("validation"):
    ids = [index[transformer.START]] + [index[token] for token in name] + [index[transformer.SEP]]   # the name as the model reads it
    probabilities = transformer.softmax(transformer.forward(ids)[:-1])   # the last position predicts past <sep>, which a name never needs
    from_transformer += list(probabilities[np.arange(len(ids) - 1), ids[1:]])   # each position's probability for the token after it
    from_counts += [counted.probability(context, token) for context, token in ngrams(padded(name, 4), 4)]   # then </s>
from_counts, from_transformer = np.array(from_counts), np.array(from_transformer)

print("validation tokens scored, each name's end included:", f"{len(from_counts):,}")
for share in [0.0, 0.3, 0.5, 0.7, 1.0]:
    mixed = (1 - share) * from_counts + share * from_transformer
    print(f"validation perplexity on names, transformer share {share:.1f}:", f"{np.exp(-np.log(mixed).mean()):.1f}")
