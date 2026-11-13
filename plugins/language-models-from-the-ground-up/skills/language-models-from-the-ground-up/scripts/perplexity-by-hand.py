import math

from lib.bigrams import Bigrams, padded, perplexity
from lib.store import load_products

train = load_products("train")["name"]
model = Bigrams(train)

name = "sled coffee table"                  # a name from the training split
tokens = padded(name)
surprise = 0.0
for word, following in zip(tokens, tokens[1:]):
    p = model.probability(word, following)
    surprise += -math.log(p)
    print(f"P({following} | {word}) = {p:.4f}   -log P = {-math.log(p):.2f}")
print("average -log P:", round(surprise / (len(tokens) - 1), 3))
print("perplexity of the name:", round(math.exp(surprise / (len(tokens) - 1)), 1))
print("perplexity of every training name:", round(perplexity(model, train), 1))
