"""Draws six product names from the bigram model, one word at a time, with a fixed seed so the same six come out on every
run. The count of generated words never seen in training is the line the prose's point rests on."""
import numpy as np

from lib.bigrams import END, START, Bigrams
from lib.store import load_products, masked

model = Bigrams(load_products("train")["name"])
rng = np.random.default_rng(2026)                    # fixed seed: any seed gives six names, this one gives the book's


def generate(longest=12):                            # twelve words at most, if the end marker hasn't come first
    word, name = START, []
    while len(name) < longest:
        candidates = list(model.counts[word])        # the words seen after word: the only ones the model can draw
        chances = [model.probability(word, c) for c in candidates]
        word = candidates[rng.choice(len(candidates), p=chances)]   # choice returns an index into candidates, drawn with these chances
        if word == END:
            break
        name.append(word)
    return " ".join(name)


generated = [generate() for _ in range(6)]
print("\n".join(masked(name) for name in generated))   # masked shows each rare word, used in fewer than 30 training descriptions, as [name]; most are product lines' names
print("generated words never seen in training:", sum(w not in model.counts for name in generated for w in name.split()))   # every training word is a key, since each is followed by something
