import unicodedata

from lib.store import load_products, words

train_names, validation_names = load_products("train")["name"], load_products("validation")["name"]
characters = {c for name in train_names for c in name}

unseen = {c for name in validation_names for c in name} - characters
word_tokens = sum(len(words(name)) for name in validation_names)
character_tokens = sum(len(name) for name in validation_names)

print("different characters in training names:", len(characters))
print("validation characters never seen in training:", len(unseen))
print("they are:", ", ".join(unicodedata.name(c).lower() for c in sorted(unseen)))
print("validation tokens as words:", f"{word_tokens:,}")
print("validation tokens as characters:", f"{character_tokens:,}")
print("characters per word:", round(character_tokens / word_tokens, 1))
