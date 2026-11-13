import numpy as np

from lib import transformer
from lib.products import product_texts

texts = product_texts("validation", 300)
layers, heads = len(transformer.forward(texts[0][0], keep=True)[1]), transformer.load()[2]["settings"]["heads"]
on_previous = np.zeros((layers, heads))
for ids, _ in texts:
    _, attention = transformer.forward(ids, keep=True)
    for layer, weights in enumerate(attention):        # weights: (heads, positions, positions)
        on_previous[layer] += weights[:, np.arange(1, len(ids)), np.arange(len(ids) - 1)].mean(1)
on_previous /= len(texts)
even = np.mean([np.mean(1 / np.arange(2, len(ids) + 1)) for ids, _ in texts])   # spread evenly over the visible tokens

print("average weight on the previous token (rows: layers, columns: heads):")
for layer, row in enumerate(on_previous, start=1):
    print(f"  layer {layer}: " + "  ".join(f"{w:.2f}" for w in row))
layer, head = np.unravel_index(on_previous.argmax(), on_previous.shape)
print("head with the most weight on the previous token:", f"layer {layer + 1}, head {head + 1}")
print("its weight on the previous token:", f"{on_previous.max():.2f}")
print("an even spread's weight on the previous token:", f"{even:.2f}")
