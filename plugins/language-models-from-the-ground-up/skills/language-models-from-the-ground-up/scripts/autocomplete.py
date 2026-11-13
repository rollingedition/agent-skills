"""Asks the bigram model for its three likeliest next words after five typed prefixes, then counts the training names that
contain outdoor door. The patio bar line, which gets the same suggestions as bar, is the one the prose's point rests on."""
from lib.bigrams import Bigrams
from lib.store import load_products

model = Bigrams(load_products("train")["name"])

for typed in ["coffee", "bar", "kitchen", "outdoor", "patio bar"]:
    last_word = typed.split()[-1]                    # the model reads only this word, so patio never reaches it
    suggestions = model.next_words(last_word, k=3)   # (word, probability) pairs, likeliest first
    print(f"{typed:<10} -> " + ", ".join(f"'{word}' {p:.2f}" for word, p in suggestions))

names = load_products("train")["name"]               # the training names as plain strings, for the substring counts
print("training names containing 'outdoor door':", sum("outdoor door" in n for n in names))   # a substring test, so `outdoor doors` counts too
print("of them, followed by 'mat':", sum("outdoor door mat" in n for n in names))   # the same test, with mat after them
