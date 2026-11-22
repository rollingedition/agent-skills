"""Mixes the network's and the 4-gram's probability of every validation token at 21 shares for the network, from 0 to 1 in
steps of 0.05, and draws the validation perplexity of each mix against its share. The prose quotes the lowest share, the
counts alone and the gain over them, and the first and last shares of the flat bottom, all printed below."""
from lib import neural
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded
from lib.figures import ACCENT, INK, MUTED, new_figure, save
import math
import numpy as np

train, validation = name_tokens("train"), name_tokens("validation")
# each model's probability of every validation token is computed once, in order; the mixes below are then cheap
from_network = neural.token_probabilities(validation)
counted = KneserNey(train, 4)
from_counts = np.array([counted.probability(c, t) for text in validation for c, t in ngrams(padded(text, 4), 4)])

# round(...) keeps the shares exact (0.15, not 0.15000000000000002), so each one prints the same as the chapter's
shares = [round(s, 2) for s in np.linspace(0, 1, 21)]
perplexity = []
for share in shares:
    mixed = share * from_network + (1 - share) * from_counts
    perplexity.append(math.exp(-np.log(mixed).mean()))

low = min(range(len(shares)), key=lambda i: perplexity[i])
# the gain is measured against the counts alone (share 0), so the tolerance scales with how much the mix helps at all
tolerance = (perplexity[0] - perplexity[low]) / 10
# the flat bottom: the shares within a tenth of that gain of the lowest, so each keeps most of the gain over the counts
flat = [s for s, p in zip(shares, perplexity) if p <= perplexity[low] + tolerance]
print(f"share step: {shares[1] - shares[0]:.2f}")
print(f"lowest validation perplexity share: {shares[low]:.2f}")
print(f"validation perplexity, counts alone (share 0): {perplexity[0]:.1f}")
print(f"validation perplexity, network alone (share 1): {perplexity[-1]:.1f}")
print(f"gain of the lowest over the counts alone: {perplexity[0] - perplexity[low]:.1f}")
print(f"flat bottom tolerance, a tenth of the gain: {tolerance:.2f}")
print(f"flat bottom, first share within the tolerance: {flat[0]:.2f}")
print(f"flat bottom, last share within the tolerance: {flat[-1]:.2f}")
# the curve falls to its low point and rises after it, with no second dip on the grid
assert all(a > b for a, b in zip(perplexity[:low], perplexity[1:low + 1]))  # each point before the low is higher than the next
assert all(a < b for a, b in zip(perplexity[low:], perplexity[low + 1:]))  # each point from the low on is lower than the next
print("curve falls then rises: yes")

fig, ax = new_figure()
ax.plot(shares, perplexity, color=ACCENT, marker="o", markersize=3,
        label="mix of the network and the 4-gram counts")
ax.axhline(perplexity[0], color=MUTED, linestyle="--", linewidth=1, label="4-gram counts alone (share 0)")
ax.plot([shares[low]], [perplexity[low]], marker="o", markersize=6, color=INK, linestyle="none",
        label="lowest point on the grid")
ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_xlabel("network's share of the mix (0 = counts only, 1 = network only)")
ax.set_ylabel("validation perplexity per token")
ax.legend(loc="upper center")
save(fig, "mixing-curve")
