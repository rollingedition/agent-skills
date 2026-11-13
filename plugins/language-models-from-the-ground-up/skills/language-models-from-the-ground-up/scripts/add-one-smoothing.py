from lib.bigrams import Bigrams, perplexity
from lib.store import load_products

model = Bigrams(load_products("train")["name"])
train, validation = load_products("train")["name"], load_products("validation")["name"]

print("vocabulary:", f"{len(model.vocabulary):,}")
print("P(table | coffee) counted:", round(model.probability("coffee", "table"), 3))
print("P(table | coffee) add-one:", round(model.probability("coffee", "table", add_one=True), 3))
print("training perplexity, counted:", round(perplexity(model, train), 1))
print("training perplexity, add-one:", f"{perplexity(model, train, add_one=True):,.1f}")
print("validation perplexity, add-one:", f"{perplexity(model, validation, add_one=True):,.1f}")
