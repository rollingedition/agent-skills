import math

import numpy as np

from lib import transformer
from lib.products import product_texts

_, vocabulary, manifest = transformer.load()
settings = manifest["settings"]
pad, end = vocabulary.index(transformer.PAD), vocabulary.index(transformer.END)
texts = [ids for ids, _ in product_texts("train")]
size = settings["batch"]

order = np.random.default_rng(settings["seed"]).permutation(len(texts))   # one shuffled epoch
padding, targets_seen, shares = 0, 0, []
for start in range(0, len(texts), size):
    batch = [texts[i] for i in order[start:start + size]]
    longest = max(len(ids) for ids in batch)
    padded = np.array([ids + [pad] * (longest - len(ids)) for ids in batch])   # short texts filled out with <pad>
    inputs, targets = padded[:, :-1], padded[:, 1:]                            # each position predicts the next token
    padding, targets_seen = padding + (targets == pad).sum(), targets_seen + targets.size
    shares.append((targets == pad).mean())
    if start == 0:
        first_shape = (inputs.shape, targets.shape)

print("training texts:", f"{len(texts):,}")
print("tokens in them:", f"{sum(len(ids) for ids in texts):,}")
print(f"texts cut at the length limit, {settings['longest']} tokens:", f"{np.mean([ids[-1] != end for ids in texts]):.1%}")
print("texts per batch:", size)
print("one batch's inputs and targets:", *first_shape)
print("share of targets that are padding, over one shuffled epoch:", f"{padding / targets_seen:.0%}")
print("least and most padding in a batch:", f"{min(shares):.0%} and {max(shares):.0%}")
print("steps per epoch:", f"{math.ceil(len(texts) / size):,}")
print("epochs in the recorded run:", settings["epochs"])
print("steps in the recorded run:", f"{manifest['steps']:,}")
