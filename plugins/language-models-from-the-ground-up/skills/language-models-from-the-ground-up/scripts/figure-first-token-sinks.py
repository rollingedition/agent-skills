"""Draws each of SmolLM2's 480 recorded heads by its layer: its average weight on the first token, with the even spread as
a dashed reference line. It prints how many layers from 5 on most heads put over half their weight on the first token."""
from lib import open_model, transformer
from lib.figures import ACCENT, MUTED, new_figure, save
from lib.products import product_texts
from lib.store import load_products

import numpy as np
from tokenizers import Tokenizer

heads = open_model.read("heads")
first = np.array(heads["first"])                                            # (layers, heads), counted from layer 0 in the rows
layer = np.arange(1, first.shape[0] + 1)                                    # the layer each row is, counted from 1
most = (first > 0.5).sum(1) > first.shape[1] / 2                            # a layer where more than half of its heads put over half on the first token
assert layer[most][0] == 5                                                  # the layer the prose names: a retrained model that moves it fails here
print("layers from 5 on in which most heads do:", f"{most[4:].sum()} of {most[4:].size}")   # rows from 4 on are layers 5 to 32
print("highest first-token weight, layers 1 to 4:", f"{first[:4].max():.2f}")
print("highest first-token weight, layers 5 to 32:", f"{first[4:].max():.2f}")

# The even spread, averaged as open-model-heads averages it: a position's weight 1 / k on each of its k tokens.
smollm2 = Tokenizer.from_file("data/smollm2-tokenizer/tokenizer.json")
end = transformer.load()[1].index(transformer.END)      # [1] is the vocabulary: load() returns weights, vocabulary, manifest
rows = load_products("validation").head(500)            # the first 500 validation products, the ones product_texts reads
# The same products as product_texts, with their names and descriptions, filtered the same way. Each text is a name, a newline
# and a description, as the recording wrote it.
texts = [f"{name}\n{description}\n" for (ids, sep), name, description in
         zip(product_texts("validation", 500), rows["name"], rows["description"]) if ids[-1] == end and sep < len(ids) - 2]
# Only the texts the recording averaged. The +1 is the start token the recording put before every text.
lengths = [len(smollm2.encode(text, add_special_tokens=False).ids) + 1 for text in texts[:heads["texts"]]]
even = np.mean([np.mean(1 / np.arange(2, n + 1)) for n in lengths])

x = np.repeat(layer, first.shape[1])                                        # one dot per head, at its layer
fig, ax = new_figure(height=3.6)
ax.plot(x, first.ravel(), linestyle="none", marker="o", markersize=3.2, color=ACCENT, label="weight on the first token")
ax.axhline(even, color=MUTED, linestyle="--", label="even spread")
ax.set(xlabel="layer", xticks=[1, 5, 10, 15, 20, 25, 30], ylabel="average weight of a head on the first token",
       ylim=(0, 1.3), yticks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.legend(frameon=False, loc="upper center", ncol=2)                       # above the dots, which top out at 1
save(fig, "first-token-sinks")
