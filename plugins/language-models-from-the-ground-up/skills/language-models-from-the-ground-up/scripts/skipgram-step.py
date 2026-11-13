"""Three updates of skip-gram with negative sampling on one real pair, patio and umbrella, with sofa and 48 as noise tokens,
printing each pair's probability before and after. The prose's point rests on the four probability lines: umbrella's rises,
and the noise tokens' fall."""
import numpy as np

from lib.skipgram import sigmoid, step                              # one gradient step, and the logistic function
from lib.vectors import training_ids

_, vocabulary = training_ids()
rng = np.random.default_rng(2026)                                   # a fixed seed, so the starting vectors are the same on every run
inputs = (rng.random((len(vocabulary), 8)) - 0.5) / 8     # each token's vector as a centre, small and random
outputs = np.zeros((len(vocabulary), 8))                 # and as a neighbour: zero, as training starts
centre, context = [vocabulary.index("patio</w>")], [vocabulary.index("umbrella</w>")]   # the real pair: patio as the centre, umbrella its real neighbour
noise = np.array([[vocabulary.index("sofa</w>"), vocabulary.index("48</w>")]])          # noise tokens, picked by hand here; training draws them at random


def chances():
    real = sigmoid(inputs[centre[0]] @ outputs[context[0]])
    fake = sigmoid(outputs[noise[0]] @ inputs[centre[0]])
    return real, fake


before = chances()                                       # zero neighbour vectors give every score zero, so every probability is one half
for _ in range(3):                                       # three updates on the same pair
    step(np.array(centre), np.array(context), noise, inputs, outputs, rate=1.0)   # rate 1.0, far above the 0.025 that training starts from, so three steps show
after = chances()
print("P(umbrella is a real neighbour of patio), before:", f"{before[0]:.3f}")
print("P(umbrella is a real neighbour of patio), after 3 steps:", f"{after[0]:.3f}")
print("P(sofa, 48 are real neighbours), before:", ", ".join(f"{p:.3f}" for p in before[1]))
print("P(sofa, 48 are real neighbours), after 3 steps:", ", ".join(f"{p:.3f}" for p in after[1]))
