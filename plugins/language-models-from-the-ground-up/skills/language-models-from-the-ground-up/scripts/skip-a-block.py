import numpy as np

from lib import transformer
from lib.products import product_texts

layers = transformer.load()[2]["settings"]["layers"]
texts = [ids for ids, _ in product_texts("validation", 100)]


def measure(skip=None):
    """Perplexity per token, and the average probability of the top token, with one block left out."""
    surprise, top, count = 0.0, 0.0, 0
    for ids in texts:
        p = transformer.softmax(transformer.forward(ids, skip=skip)[:-1])
        surprise -= np.log(p[np.arange(len(ids) - 1), ids[1:]]).sum()
        top += p.max(1).sum()
        count += len(ids) - 1
    return np.exp(surprise / count), top / count


print("tokens scored, names and descriptions:", f"{sum(len(ids) - 1 for ids in texts):,}")
for skip in [None] + list(range(layers)):
    label = "all blocks" if skip is None else f"without block {skip + 1}"
    perplexity, top = measure(skip)
    print(f"{label}:", f"{perplexity:,.1f}")
    print(f"{label}, average probability of the top token:", f"{top:.2f}")
