import numpy as np

from lib.tinynet import backprop, forward, parameters

p = parameters()                                  # the tiny model: 5 tokens, a window of 2, 3 hidden units
context, target = np.array([1, 3]), 4

worst, step = 0.0, 1e-6
gradients = backprop(p, context, target)
for name, value in p.items():                     # nudge each parameter both ways, and see how the loss moves
    for i in np.ndindex(value.shape):
        value[i] += step
        up = forward(p, context, target)[3]
        value[i] -= 2 * step
        down = forward(p, context, target)[3]
        value[i] += step
        worst = max(worst, abs((up - down) / (2 * step) - gradients[name][i]))
print("loss:", round(float(forward(p, context, target)[3]), 4))
print("parameters checked:", sum(v.size for v in p.values()))
print("backprop agrees with nudging to 6 decimal places:", worst < 1e-6)
