"""Counts every word pair in the training names, padded with start and end markers, and lists the words that most often
follow coffee. The four lines under "words after coffee" are what the prose's point rests on."""
from collections import Counter

from lib.store import load_products, words

names = load_products("train")["name"]                # training split only, so validation and test names never add counts
pairs = Counter()
for name in names:
    tokens = ["<s>"] + words(name) + ["</s>"]       # the markers record how a name starts and where it stops
    pairs.update(zip(tokens, tokens[1:]))            # tokens[1:] is the same list one word on, so each word pairs with the next

print("word pairs:", f"{sum(pairs.values()):,}")
print("different pairs:", f"{len(pairs):,}")

after_coffee = {following: n for (word, following), n in pairs.items() if word == "coffee"}   # pairs that start with coffee, by the word after
print("words after coffee:", f"{sum(after_coffee.values()):,}")
for following, n in sorted(after_coffee.items(), key=lambda item: -item[1])[:4]:   # the key negates the count, so largest first
    print(f"  coffee {following:<6} {n:>6,}")
