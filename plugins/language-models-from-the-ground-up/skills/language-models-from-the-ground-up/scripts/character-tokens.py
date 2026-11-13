"""Compares the characters of the training names with those of the validation names, and counts the validation tokens
both ways. Its characters-per-word line is the one to read."""
import unicodedata

from lib.store import load_products, words

train_names, validation_names = load_products("train")["name"], load_products("validation")["name"]
characters = {c for name in train_names for c in name}     # a set: each distinct character once

unseen = {c for name in validation_names for c in name} - characters
word_tokens = sum(len(words(name)) for name in validation_names)   # a word is a token here, as in chapter 1
character_tokens = sum(len(name) for name in validation_names)     # len counts the spaces too, as characters

print("different characters in training names:", len(characters))
print("validation characters never seen in training:", len(unseen))
print("they are:", ", ".join(unicodedata.name(c).lower() for c in sorted(unseen)))   # printed by Unicode name, because a soft hyphen itself prints as nothing
print("validation tokens as words:", f"{word_tokens:,}")
print("validation tokens as characters:", f"{character_tokens:,}")
print("characters per word:", round(character_tokens / word_tokens, 1))
