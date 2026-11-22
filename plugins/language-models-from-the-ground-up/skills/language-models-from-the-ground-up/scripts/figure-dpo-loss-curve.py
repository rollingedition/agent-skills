"""Draws the DPO loss against the margin, with the two cases of dpo-loss-by-hand marked at their margins.
The printed losses at the two ends and at zero show the loss climbing on one side and flattening on the other."""
import numpy as np

from lib.figures import ACCENT, INK, MUTED, new_figure, save

beta = 0.1                                       # as dpo-loss-by-hand sets it
# the same two cases as dpo-loss-by-hand: (preferred, rejected) under the tuned model, then under the reference model
cases = {"favours preferred more": (-12.0, -20.0, -14.0, -18.0), "favours it less": (-15.0, -15.0, -14.0, -18.0)}
brackets = {name: (p - pr) - (q - qr) for name, (p, q, pr, qr) in cases.items()}   # the bracket dpo-loss-by-hand computes
margins = {name: beta * bracket for name, bracket in brackets.items()}   # margin = beta × bracket, as in the example


def loss_at(margin):
    """-log σ(margin), written so it can't overflow, as dpo-loss-by-hand writes it."""
    return np.log1p(np.exp(-margin))


grid = np.linspace(-4, 4, 401)                   # the margins the two cases reach, with room either side
assert np.all(np.diff(loss_at(grid)) < 0)        # a larger margin always lowers the loss; the prose states this
print("loss at a margin of 0:", f"{loss_at(0.0):.3f}")
print("loss at a margin of -4:", f"{loss_at(-4.0):.3f}")
print("loss at a margin of 4:", f"{loss_at(4.0):.3f}")
for name in cases:
    print(f"{name}, margin:", f"{margins[name]:.2f}")

fig, ax = new_figure(height=3.2)
ax.plot(grid, loss_at(grid), color=ACCENT, label="loss")
for name, color, marker in [("favours preferred more", INK, "o"), ("favours it less", MUTED, "s")]:
    ax.scatter([margins[name]], [loss_at(margins[name])], color=color, marker=marker, s=36, zorder=3, label=name)
ax.set_xlim(-4, 4)
ax.set_ylim(0, 4.5)
ax.set_xlabel("margin = β × (change in preferred's log-probability − change in rejected's)")
ax.set_ylabel("loss, −log σ(margin)")
ax.legend(loc="upper right")
save(fig, "dpo-loss-curve")
