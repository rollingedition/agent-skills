"""Draws the attention weights of two heads over one short text: the start marker, the name copper wire basket, <sep>
and the start of its description. The heads are the two the previous-token averages name, most and least weight on the
previous token, found by the same measure over the same 300 products."""
from lib import transformer
from lib.figures import ACCENT, RULE, new_figure, save
from lib.products import product_texts
from lib.store import load_products

import numpy as np
from matplotlib.colors import LinearSegmentedColormap, to_rgb

NAME, LENGTH = "copper wire basket", 14                 # ordinary words, so no product line is named; the first 14 tokens
_, vocabulary, manifest = transformer.load()

# each head's weight on the previous token, averaged over positions 1 and later, then over the 300 products
on_previous = np.mean([[w[:, np.arange(1, len(ids)), np.arange(len(ids) - 1)].mean(1)
                        for w in transformer.forward(ids, keep=True)[1]] for ids, _ in product_texts("validation", 300)], axis=0)
HEADS = [tuple(int(k) + 1 for k in np.unravel_index(f(on_previous), on_previous.shape)) for f in (np.argmax, np.argmin)]  # (layer, head) from 1
assert HEADS == [(4, 3), (1, 1)]                         # the heads the prose names: a retrained model that moves them fails here

product = load_products("validation").query("name == @NAME").iloc[0]
ids = transformer.product_ids(product["name"], product["description"], {t: i for i, t in enumerate(vocabulary)}, manifest["settings"]["longest"])[:LENGTH]
labels = [vocabulary[i].removesuffix("</w>") for i in ids]   # the tokenizer's end-of-word mark is noise on a page
n = len(ids)
_, attention = transformer.forward(ids, keep=True)
print("tokens:", " ".join(labels))
print("an even spread's weight on the previous token:", f"{np.mean(1 / np.arange(3, n + 1)):.2f}")

# ACCENT at a weight's opacity over RULE: a weight of 0 shows RULE, 1 shows ACCENT, and no colour outside the palette
cmap = LinearSegmentedColormap.from_list("accent-by-weight", [(*to_rgb(ACCENT), 0.0), (*to_rgb(ACCENT), 1.0)], N=20)
fig, axes = new_figure(columns=2, height=3.6, sharex=False)
for ax, (layer, head) in zip(axes, HEADS):
    weights = attention[layer - 1][head - 1]             # (positions, positions): row = query, column = key; lists count from 0
    # positions 2 and later have a previous token other than the start marker; position 1's previous token is the start marker
    print(f"layer {layer}, head {head}, average weight on the previous token: {weights[np.arange(2, n), np.arange(1, n - 1)].mean():.2f}")
    # the current token, averaged over the positions after the start marker
    print(f"layer {layer}, head {head}, average weight on the current token: {weights[np.arange(1, n), np.arange(1, n)].mean():.2f}")
    assert np.triu(weights, k=1).max() == 0              # the causal mask leaves exactly zero above the diagonal
    ax.set_facecolor(RULE)
    image = ax.pcolormesh(np.ma.masked_equal(weights, 0), cmap=cmap, vmin=0, vmax=1, linewidth=0)   # exact zeros are not drawn
    ax.set(xlim=(0, n), ylim=(n, 0), aspect="equal")     # row 0, the start marker, at the top
    ax.set_xticks(np.arange(n) + 0.5, labels, rotation=60, fontsize=7)
    ax.set_yticks(np.arange(n) + 0.5, labels, fontsize=7)
    ax.grid(False)
    ax.tick_params(length=0)
    ax.set(xlabel="key: the token attended to", ylabel="query: the token attending", title=f"layer {layer}, head {head}")
print("weights above the diagonal are zero in both heads: yes")
axes[1].set_ylabel("")                                   # the rows are the same tokens, so they are labelled once
axes[1].tick_params(labelleft=False)
bar = fig.colorbar(image, ax=axes, label="attention weight")   # one scale for both panels
bar.outline.set_visible(False)
save(fig, "previous-token-pattern")
