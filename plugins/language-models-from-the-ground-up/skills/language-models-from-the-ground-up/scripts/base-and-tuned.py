"""Prints what the base and the tuned model wrote for one product with no description, then measures every such product's
text for materials its name doesn't give and for repeated four-word phrases. The prose's points rest on the last four
printed lines, the two models' invented-material counts and repeat shares.
"""
from collections import Counter

from lib import claims, recorded

# the recording's saved texts for every product, read back rather than generated again
described = recorded.read("instruction-tuning", "descriptions")
product = next(row for row in described if row["name"] == "front porch welcome sign wall décor")
print("product:", product["name"])
print("base model:", " ".join(product["base"]["text"].split()))
print("tuned model:", " ".join(product["tuned"]["text"].split()))


def repeats(text):
    """The share of four-word phrases that repeat an earlier one in the text."""
    words = text.lower().split()
    # every window of four consecutive words, so a text of n words has n - 3 of them
    phrases = [tuple(words[i:i + 4]) for i in range(len(words) - 3)]
    # a phrase counts as repeated each time after its first appearance; max keeps a text of fewer than four words from dividing by zero
    return sum(count - 1 for count in Counter(phrases).values()) / max(len(phrases), 1)


print("products described, none of which has a description to draw on:", len(described))
for role in ["base", "tuned"]:
    texts = [row[role]["text"] for row in described]
    # materials the text names that the product's name doesn't give: a set difference, not the text's whole list
    invented = sum(bool(claims.materials(row[role]["text"]) - claims.materials(row["name"])) for row in described)
    print(f"{role} model, descriptions that name a material the name doesn't:", f"{invented} of {len(described)}")
    print(f"{role} model, repeated four-word phrases:", f"{sum(map(repeats, texts)) / len(texts):.0%}")
