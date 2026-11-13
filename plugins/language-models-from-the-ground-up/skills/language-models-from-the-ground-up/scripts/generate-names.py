import numpy as np

from lib.bigrams import END, START, Bigrams
from lib.store import load_products, masked

model = Bigrams(load_products("train")["name"])
rng = np.random.default_rng(2026)                    # a fixed seed, so the same names come out every run


def generate(longest=12):
    word, name = START, []
    while len(name) < longest:
        candidates = list(model.counts[word])
        chances = [model.probability(word, c) for c in candidates]
        word = candidates[rng.choice(len(candidates), p=chances)]   # draw the next word by its probability
        if word == END:
            break
        name.append(word)
    return " ".join(name)


generated = [generate() for _ in range(6)]
print("\n".join(masked(name) for name in generated))   # [name]: a rare word, most often a product line's name
print("generated words never seen in training:", sum(w not in model.counts for name in generated for w in name.split()))
