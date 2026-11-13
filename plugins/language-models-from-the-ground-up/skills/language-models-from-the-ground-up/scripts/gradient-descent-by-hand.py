import numpy as np

from lib.tinynet import backprop, forward, parameters

p = parameters()
examples = [(np.array([1, 3]), 4), (np.array([0, 1]), 3), (np.array([3, 4]), 2)]     # three (window, next token) pairs
rate = 0.5                                                   # the step size


def average_loss():
    return np.mean([forward(p, c, t)[3] for c, t in examples])


print("average loss before:", f"{average_loss():.3f}")
for step in range(1, 21):
    for c, t in examples:
        for name, gradient in backprop(p, c, t).items():
            p[name] -= rate * gradient / len(examples)       # w <- w - rate * dL/dw, averaged over the examples
    if step in (1, 5, 20):
        print(f"average loss after {step} steps:", f"{average_loss():.3f}")
