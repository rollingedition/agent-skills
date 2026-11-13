"""Scores the descriptions of the first 500 validation products with a 4-gram trained on whole texts, with the transformer,
and with their even mix, then splits the tokens by whether their context was seen in training. The prose's point rests on the
4-gram baseline and transformer lines, the half-and-half line and the unseen-context lines."""
import numpy as np

from lib import transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded
from lib.products import product_texts

_, vocabulary, _ = transformer.load()
end = vocabulary.index(transformer.END)
as_tokens = lambda ids: [vocabulary[i] for i in ids[1:] if i != end]          # padded() adds its own <s> and </s>
counted = KneserNey([as_tokens(ids) for ids, _ in product_texts("train")], 4)   # whole texts: name, <sep>, description

from_counts, from_transformer, seen, products = [], [], [], 0
for ids, sep in product_texts("validation", 500):
    if ids[-1] != end or sep == len(ids) - 2:
        continue                                          # cut at the length limit, or no description
    pairs = list(ngrams(padded(as_tokens(ids), 4), 4))[sep:]    # from <sep> on: the description's tokens, then </s>
    from_counts += [counted.probability(context, token) for context, token in pairs]
    seen += [context in counted.totals[4] for context, _ in pairs]   # was this 3-token context in the training texts?
    probabilities = transformer.softmax(transformer.forward(ids)[sep:-1])   # from <sep> on: each position predicts the next token
    from_transformer += list(probabilities[np.arange(len(probabilities)), ids[sep + 1:]])   # the description starts after <sep>, at sep + 1
    products += 1
from_counts, from_transformer, seen = np.array(from_counts), np.array(from_transformer), np.array(seen)
perplexity = lambda p: f"{np.exp(-np.log(p).mean()):.1f}"

print("products scored:", products)
print("description tokens scored:", f"{len(from_counts):,}")
mixed = (from_counts + from_transformer) / 2
for label, p in [("4-gram baseline", from_counts), ("transformer", from_transformer), ("half and half", mixed)]:
    print(f"{label}, validation perplexity on descriptions:", perplexity(p))
print("description tokens whose 3-token context is in the training texts:", f"{seen.mean():.0%}")
for part, where in [("seen", seen), ("unseen", ~seen)]:
    print(f"4-gram, {part} contexts:", perplexity(from_counts[where]))
    print(f"transformer, {part} contexts:", perplexity(from_transformer[where]))

names = [list(ngrams(padded(name + [transformer.SEP], 4), 4))[:-1] for name in name_tokens("validation")]   # to <sep>: the last pair predicts </s>, which a name stops short of
on_names = [counted.probability(context, token) for pairs in names for context, token in pairs]
print("this 4-gram, trained on whole texts, validation perplexity on names:", perplexity(np.array(on_names)))
