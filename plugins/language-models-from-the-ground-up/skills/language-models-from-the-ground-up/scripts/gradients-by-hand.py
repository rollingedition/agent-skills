"""Backpropagation's gradients for the tiny model, checked against nudging every one of its parameters up and down.
The assert is the check the prose relies on: the two agree to six decimal places, for every parameter."""
import numpy as np

from lib.tinynet import backprop, forward, parameters

p = parameters()                                  # the tiny model: 5 tokens, a window of 2, 3 hidden units; seeded, so the same every run
context, target = np.array([1, 3]), 4             # the window: token ids 1 and 3; the token that came next is id 4

worst, step = 0.0, 1e-6                           # the nudge: small enough that the loss is nearly a straight line over it
gradients = backprop(p, context, target)
for name, value in p.items():                     # nudge each parameter both ways, and see how the loss moves
    for i in np.ndindex(value.shape):
        value[i] += step
        up = forward(p, context, target)[3]       # forward returns (joined, hidden, logits, loss): index 3 is the loss
        value[i] -= 2 * step                      # from up to down is two steps, so the estimate is centred on the value
        down = forward(p, context, target)[3]
        value[i] += step                          # back where it started
        worst = max(worst, abs((up - down) / (2 * step) - gradients[name][i]))
agrees = worst < 1e-6                             # the largest disagreement over all parameters, against six decimal places
assert agrees
print("loss:", round(float(forward(p, context, target)[3]), 4))
print("parameters checked:", sum(v.size for v in p.values()))
print("backprop agrees with nudging to 6 decimal places:", "yes" if agrees else "no")
