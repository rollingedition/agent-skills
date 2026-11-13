import numpy as np

from lib import transformer
from lib.products import product_texts

_, vocabulary, manifest = transformer.load()
end = vocabulary.index(transformer.END)
texts = product_texts("validation", 300)
layers = manifest["settings"]["layers"]
far, markers, even_far, even_markers, counted = np.zeros(layers), np.zeros(layers), 0.0, 0.0, 0
for ids, sep in texts:
    queries = np.array([i for i in range(sep + 1, len(ids)) if ids[i] != end])    # the description's tokens
    if len(queries) == 0:
        continue                                          # a product with no description
    _, attention = transformer.forward(ids, keep=True)
    stacked = np.stack(attention)[:, :, queries]          # (layers, heads, description tokens, positions)
    positions = np.arange(len(ids))
    is_marker = np.isin(positions, [0, sep])              # <s> and <sep>
    beyond = (queries[:, None] - positions[None, :] >= 4) & ~is_marker   # what a 4-token window can't see
    far += (stacked * beyond).sum(-1).mean(1).sum(-1)
    markers += (stacked * is_marker).sum(-1).mean(1).sum(-1)
    even_far += (beyond.sum(1) / (queries + 1)).sum()     # an even spread over the positions each token can see
    even_markers += (2 / (queries + 1)).sum()
    counted += len(queries)

print("description tokens measured:", f"{counted:,}")
print("average attention weight of a description token, by layer:")
for layer in range(layers):
    print(f"  layer {layer + 1}: 4 or more tokens back {far[layer] / counted:.2f}, on <s> and <sep> {markers[layer] / counted:.2f}")
print("all layers, weight 4 or more tokens back:", f"{far.mean() / counted:.2f}")
print("an even spread's weight 4 or more tokens back:", f"{even_far / counted:.2f}")
print("all layers, weight on <s> and <sep>:", f"{markers.mean() / counted:.2f}")
print("an even spread's weight on <s> and <sep>:", f"{even_markers / counted:.2f}")
described = [(ids[1:sep], ids[sep + 1:]) for ids, sep in texts if any(i != end for i in ids[sep + 1:])]
print("products with a description:", len(described))
print("descriptions that repeat a token of the name:", sum(bool(set(n) & set(d)) for n, d in described))
