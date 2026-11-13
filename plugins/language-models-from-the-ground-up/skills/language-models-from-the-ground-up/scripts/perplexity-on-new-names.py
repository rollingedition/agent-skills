from lib.bigrams import Bigrams, padded, perplexity
from lib.store import load_products, masked

model = Bigrams(load_products("train")["name"])
validation = load_products("validation")["name"]

print("validation perplexity:", perplexity(model, validation))

pairs = [(w, f) for name in validation for w, f in zip(padded(name), padded(name)[1:])]
unseen = [pair for pair in pairs if model.probability(*pair) == 0]
print("validation word pairs:", f"{len(pairs):,}")
print("pairs never seen in training:", f"{len(unseen):,}")
print("share never seen in training:", f"{len(unseen) / len(pairs):.0%}")
names_hit = sum(any(model.probability(*p) == 0 for p in zip(padded(n), padded(n)[1:])) for n in validation)
print("names with an unseen pair:", f"{names_hit:,}")
print("validation names:", f"{len(validation):,}")
print("first unseen pairs:", ", ".join(masked(f"{w} {f}") for w, f in unseen[:3]))   # [name]: a rare word
