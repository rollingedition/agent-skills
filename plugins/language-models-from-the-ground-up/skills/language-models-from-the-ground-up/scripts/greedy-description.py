from collections import Counter

from lib import decoding, transformer
from lib.store import load_products

validation, training = load_products("validation"), load_products("train")
empty = lambda rows: rows["description"].fillna("").str.strip() == ""
print("validation products:", f"{len(validation):,}")
print("validation products with no description:", f"{empty(validation).sum():,}")
print("training products with no description:", f"{empty(training).mean():.0%}")
bulbs = training[training["name"].str.contains(r"\bbulbs?\b")]
print("training products named as bulbs with no description:", f"{empty(bulbs).mean():.0%}")

longest = 60
print("longest description, in tokens:", longest)
ids = decoding.generate(decoding.prompt("front porch welcome sign wall décor"), longest=longest)   # always the likeliest
print("greedy description:", decoding.text(ids))
fourgrams = Counter(tuple(ids[i:i + 4]) for i in range(len(ids) - 3))
print("4-token phrases it uses twice or more:", " | ".join(decoding.text(list(g)) for g, n in fourgrams.items() if n > 1))

end = transformer.load()[1].index(transformer.END)
probabilities = transformer.softmax(decoding.next_logits(decoding.prompt("5 light light bulb")))
print("P(the description is empty), 5 light light bulb:", f"{probabilities[end]:.2f}")
