"""Draws the 40 likeliest next tokens after the temperature example's text, at temperatures 0.5, 1 and 1.5, on a log scale.
The printed shares outside the 40 drawn show the shape: the higher the temperature, the more probability sits in the tail."""
import numpy as np

from lib import decoding, transformer
from lib.figures import ACCENT, INK, MUTED, new_figure, save

start = decoding.prompt("front porch welcome sign wall décor")
so_far = decoding.generate(start, longest=9)                  # the same nine greedy tokens temperature-by-hand stops at
logits = decoding.next_logits(start + so_far)
ranks = np.arange(1, 41)
outside = {}
fig, ax = new_figure(height=3.8)
for temperature, color, style in [(0.5, INK, "-"), (1.0, ACCENT, "-"), (1.5, MUTED, "--")]:
    probabilities = transformer.softmax(logits / temperature)    # divide the logits, then softmax, as temperature-by-hand does
    top = np.sort(probabilities)[::-1]                          # likeliest first, at this temperature
    outside[temperature] = 1 - top[:40].sum()
    print(f"temperature {temperature}, probability of the likeliest token: {top[0]:.3f}")
    print(f"temperature {temperature}, probability of the 40th likeliest token: {top[39]:.5f}")
    print(f"temperature {temperature}, probability outside the 40 drawn: {outside[temperature]:.1%}")
    ax.plot(ranks, top[:40], color=color, linestyle=style, marker="o", markersize=2.5, label=f"temperature {temperature}")

# A higher temperature leaves more probability past the 40th token, and a lower one less: the claim the figure shows.
assert outside[0.5] < outside[1.0] < outside[1.5]
print("tail grows with temperature: yes")
ax.set_yscale("log")
ax.set_xticks([1, 5, 10, 20, 30, 40])
ax.set_xlabel("rank of the next token, likeliest first")
ax.set_ylabel("probability, log scale")
ax.legend(frameon=False)
save(fig, "temperature-flattens")
