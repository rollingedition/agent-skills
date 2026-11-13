"""Compares the counted and add-one bigram models on one probability and on perplexity, to show what add-one smoothing
costs. The printed validation perplexity, add-one, is the line the prose's point rests on: it is finite, where the
counted model's is infinite."""
from lib.bigrams import Bigrams, perplexity
from lib.store import load_products

model = Bigrams(load_products("train")["name"])
train, validation = load_products("train")["name"], load_products("validation")["name"]   # the counts come from the training names; validation tests them

print("vocabulary:", f"{len(model.vocabulary):,}")   # every word the model can predict: training words, </s> and <unk>, but not <s>, which is never predicted
print("P(table | coffee) counted:", round(model.probability("coffee", "table"), 3))
print("P(table | coffee) add-one:", round(model.probability("coffee", "table", add_one=True), 3))   # add_one adds one to every count, and the vocabulary's size to every total
print("training perplexity, counted:", round(perplexity(model, train), 1))   # on the names the counts came from, so every pair has a count
print("training perplexity, add-one:", f"{perplexity(model, train, add_one=True):,.1f}")
print("validation perplexity, add-one:", f"{perplexity(model, validation, add_one=True):,.1f}")   # add-one gives no pair probability zero, so this is finite
