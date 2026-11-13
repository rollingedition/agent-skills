"""Scores the bigram model on the validation names, which it never learned from, then counts the pairs in them that never
occurred in training. The printed validation perplexity, which is infinite, is the line the prose's point rests on."""
from lib.bigrams import Bigrams, padded, perplexity
from lib.store import load_products, masked

model = Bigrams(load_products("train")["name"])
validation = load_products("validation")["name"]   # products the model never learned from

print("validation perplexity:", perplexity(model, validation))   # inf as soon as one pair has probability zero, rather than an error

pairs = [(w, f) for name in validation for w, f in zip(padded(name), padded(name)[1:])]   # each neighbouring pair in a padded name
unseen = [pair for pair in pairs if model.probability(*pair) == 0]   # probability is 0 for a pair the training names never contain
print("validation word pairs:", f"{len(pairs):,}")
print("pairs never seen in training:", f"{len(unseen):,}")
print("share never seen in training:", f"{len(unseen) / len(pairs):.0%}")
names_hit = sum(any(model.probability(*p) == 0 for p in zip(padded(n), padded(n)[1:])) for n in validation)   # a name counts once, if any of its pairs is unseen
print("names with an unseen pair:", f"{names_hit:,}")
print("validation names:", f"{len(validation):,}")
print("first unseen pairs:", ", ".join(masked(f"{w} {f}") for w, f in unseen[:3]))   # the first three in validation order, not the most common
