"""Draws each supported and made-up answer's average probability per token as a dot, with the 0.5 threshold, so the two
groups can be compared by eye. The prose's point rests on the lowest supported and the highest made-up answer."""
import numpy as np

from lib import claims, recorded
from lib.figures import ACCENT, INK, MUTED, new_figure, save

asked = recorded.read("instruction-tuning", "answers")
# only supported and made-up answers are compared, as answer-confidence compares them; the others are left out
by_kind = {"supported": [], "made up": []}
for row in asked:
    kind = claims.classify(row["tuned"]["text"], row["description"], row["name"])
    if kind in by_kind:
        # the geometric mean of the token probabilities: exp of their average log-probability, as answer-confidence has it
        by_kind[kind].append(np.exp(np.mean(np.log(row["tuned"]["token_probabilities"]))))
lowest_supported = min(by_kind["supported"])
highest_made_up = max(by_kind["made up"])
print("lowest supported answer, average probability per token:", f"{lowest_supported:.3f}")
print("highest made-up answer, average probability per token:", f"{highest_made_up:.3f}")
# the groups overlap when some supported answer is less confident than some made-up one; the prose states this
assert lowest_supported < highest_made_up

threshold = 0.5                                       # the same fixed cut answer-confidence uses
fig, ax = new_figure(height=2.6)
for row_y, kind, color in [(0, "made up", ACCENT), (1, "supported", INK)]:
    values = by_kind[kind]
    # a deterministic spread of the dots up and down their row, so overlapping dots stay visible
    jitter = [((i * 0.618) % 1 - 0.5) * 0.4 for i in range(len(values))]
    ax.scatter(values, [row_y + j for j in jitter], color=color, s=28)
ax.axvline(threshold, color=MUTED, linestyle="--")
ax.text(threshold + 0.01, 1.45, "threshold 0.5 per token", ha="left", color=MUTED)
ax.set_xlim(0, 1)
ax.set_ylim(-0.6, 1.6)
ax.set_yticks([0, 1], ["made up", "supported"])
ax.grid(False, axis="y")
ax.set_xlabel("average probability per token, a geometric mean (1 is certain)")
save(fig, "confidence-overlap")
