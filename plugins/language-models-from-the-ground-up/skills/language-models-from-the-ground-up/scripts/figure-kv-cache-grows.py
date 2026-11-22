"""Draws SmolLM2-135M's key and value cache against text length, with and without grouped keys and values, beside its
weights' memory, all computed as open-model-memory computes them. The crossing line rests on the ungrouped cache's
bytes per token, and the grouped line says whether that cache reaches the weights within the longest text."""
from lib import open_model
from lib.figures import ACCENT, INK, MUTED, new_figure, save

import numpy as np

config = open_model.config("SmolLM2-135M")
longest = open_model.config("SmolLM2-360M")["max_position_embeddings"]    # the longest text the models are set up for
head_size = config["hidden_size"] // config["num_attention_heads"]        # the width shared out over the query heads, grouped or not
layers = config["num_hidden_layers"]
weights = open_model.parameters(config)["total"] * 2                       # 16-bit numbers: 2 bytes each
grouped = layers * 2 * config["num_key_value_heads"] * head_size * 2       # bytes per token: a key and a value per layer, 2 bytes each
ungrouped = layers * 2 * config["num_attention_heads"] * head_size * 2     # the same cache with every query head keeping its own
lengths = np.arange(longest + 1)                                           # text lengths in tokens, from 0 to the longest text
cache_grouped, cache_ungrouped = grouped * lengths, ungrouped * lengths    # bytes: each token adds the same amount
assert (np.diff(cache_grouped) == grouped).all() and (np.diff(cache_ungrouped) == ungrouped).all()
print("each token adds the same bytes to the cache, grouped and not: yes")

# The first text length whose ungrouped cache reaches the weights; the grouped cache is checked over the same lengths.
crossing = int(np.argmax(cache_ungrouped >= weights))
print("text length at which the cache without grouping passes the weights, in tokens:", f"{crossing:,}")
grouped_passes = bool((cache_grouped >= weights).any())
print("the grouped cache passes the weights within the longest text:", "yes" if grouped_passes else "no")
assert not grouped_passes                                                  # the prose's claim: grouping keeps it under the weights

fig, ax = new_figure()
ax.plot(lengths, cache_grouped / 1e9, color=ACCENT, label="cache with grouped keys and values")
ax.plot(lengths, cache_ungrouped / 1e9, color=INK, label="cache without grouping")
ax.axhline(weights / 1e9, color=MUTED, linestyle="--", label="weights, in 16-bit numbers")
ax.set(xlabel="text length, in tokens", ylabel="memory, in GB", ylim=(0, None))
ax.legend(frameon=False, loc="upper left")
save(fig, "kv-cache-grows")
