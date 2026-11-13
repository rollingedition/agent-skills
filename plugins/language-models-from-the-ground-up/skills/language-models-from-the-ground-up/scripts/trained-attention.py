import numpy as np

from lib import transformer
from lib.store import load_products

_, vocabulary, manifest = transformer.load()
settings = manifest["settings"]
index = {t: i for i, t in enumerate(vocabulary)}
product = load_products("validation").query("name == 'double chaise patio furniture cover'").iloc[0]
ids = transformer.product_ids(product["name"], product["description"], index, settings["longest"])
sep = ids.index(index[transformer.SEP])
position = ids.index(ids[sep - 1], sep) - 1           # just before the description first repeats the name's last token
logits, attention = transformer.forward(ids, keep=True)
probabilities = transformer.softmax(logits[position])


def label(i):
    """Where a token sits: the current position, the name, the description, or a marker."""
    if i == position:
        return f"current:{vocabulary[ids[i]]}"
    if i == 0 or i == sep:
        return vocabulary[ids[i]]
    return f"{'name' if i < sep else 'description'}:{vocabulary[ids[i]]}"


print("layers:", settings["layers"])
print("heads per layer:", settings["heads"])
print("dimensions per head:", settings["dimensions"] // settings["heads"])
print("name:", " ".join(vocabulary[i] for i in ids[1:sep]))
print("description so far:", " ".join(vocabulary[i] for i in ids[sep + 1:position + 1]))
print(f"P(next token is {vocabulary[ids[position + 1]]}): {probabilities[ids[position + 1]]:.2f}")
for layer in [0, len(attention) - 1]:
    for head, weights in enumerate(attention[layer]):
        top = np.argsort(-weights[position], kind="stable")[:3]
        print(f"layer {layer + 1}, head {head + 1}: " + ", ".join(f"{label(i)} {weights[position, i]:.2f}" for i in top))

name_cover = sep - 1                                     # the name's last token, `cover`
earlier = ids.index(ids[position], sep + 1)              # the description's earlier `furniture`
last = attention[-1][:, position]                        # the last layer's heads, at the current position
head = int(last[:, name_cover].argmax())
print("last-layer head with the most weight on the name's cover:", f"head {head + 1}")
print("its weight on the name's cover:", f"{last[head, name_cover]:.2f}")
print(f"its weight on {vocabulary[ids[earlier + 1]].removesuffix('</w>')}, after the description's earlier furniture:",
      f"{last[head, earlier + 1]:.2f}")
