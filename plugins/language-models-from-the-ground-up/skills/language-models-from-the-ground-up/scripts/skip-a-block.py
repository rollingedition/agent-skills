"""Scores the names and descriptions of the first 100 validation products with the full model, and with each block left
out in turn, reporting perplexity and the top token's average probability. The prose's point rests on the perplexity
with each block left out, set against the full model's."""
import numpy as np

from lib import transformer
from lib.products import product_texts

layers = transformer.load()[2]["settings"]["layers"]     # load returns (weights, vocabulary, manifest): index 2 is the manifest
texts = [ids for ids, _ in product_texts("validation", 100)]   # the <sep> positions aren't needed: each text is scored whole


def measure(skip=None):
    """Perplexity per token, and the average probability of the top token, with one block left out."""
    surprise, top, count = 0.0, 0.0, 0
    for ids in texts:
        p = transformer.softmax(transformer.forward(ids, skip=skip)[:-1])   # [:-1] drops the last position: nothing follows it
        surprise -= np.log(p[np.arange(len(ids) - 1), ids[1:]]).sum()       # position i predicts token i + 1
        top += p.max(1).sum()
        count += len(ids) - 1
    return np.exp(surprise / count), top / count                             # perplexity: exp of the average surprise per token


print("tokens scored, names and descriptions:", f"{sum(len(ids) - 1 for ids in texts):,}")
for skip in [None] + list(range(layers)):                # None keeps all four blocks: the full model
    label = "all blocks" if skip is None else f"without block {skip + 1}"   # skip counts blocks from 0, so block skip + 1 is left out
    perplexity, top = measure(skip)
    print(f"{label}:", f"{perplexity:,.1f}")
    print(f"{label}, average probability of the top token:", f"{top:.2f}")
