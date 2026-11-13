from collections import Counter

from lib.store import load_products, words

names = load_products("train")["name"]
pairs = Counter()
for name in names:
    tokens = ["<s>"] + words(name) + ["</s>"]       # mark where a name starts and ends
    pairs.update(zip(tokens, tokens[1:]))            # each word with the word that follows it

print("word pairs:", f"{sum(pairs.values()):,}")
print("different pairs:", f"{len(pairs):,}")

after_coffee = {following: n for (word, following), n in pairs.items() if word == "coffee"}
print("words after coffee:", f"{sum(after_coffee.values()):,}")
for following, n in sorted(after_coffee.items(), key=lambda item: -item[1])[:4]:
    print(f"  coffee {following:<6} {n:>6,}")
