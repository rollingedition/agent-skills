"""Scores the training name sled coffee table pair by pair, to show where its surprise sits, then scores every training name
at once. The printed line for P(sled | <s>), the largest surprise in the name, is the one the prose's point rests on."""
import math

from lib.bigrams import Bigrams, padded, perplexity
from lib.store import load_products

train = load_products("train")["name"]
model = Bigrams(train)

name = "sled coffee table"                  # a training name, so every pair in it has a count
tokens = padded(name)                       # the name with <s> and </s> around it, as in training
surprise = 0.0
for word, following in zip(tokens, tokens[1:]):   # tokens[1:] shifts the list one word on, so each pair is a word and the next
    p = model.probability(word, following)
    surprise += -math.log(p)                # natural log, so surprise is in nats, the units that exp() undoes
    print(f"P({following} | {word}) = {p:.4f}   -log P = {-math.log(p):.2f}")
print("average -log P:", round(surprise / (len(tokens) - 1), 3))   # pairs: one fewer than the tokens, one per word predicted, </s> included
print("perplexity of the name:", round(math.exp(surprise / (len(tokens) - 1)), 1))   # perplexity is exp of the average surprise
print("perplexity of every training name:", round(perplexity(model, train), 1))   # pooled over every pair in every name, not averaged name by name
