from collections import Counter

from lib import claims, recorded

described = recorded.read("instruction-tuning", "descriptions")
product = next(row for row in described if row["name"] == "front porch welcome sign wall décor")
print("product:", product["name"])
print("base model:", " ".join(product["base"]["text"].split()))
print("tuned model:", " ".join(product["tuned"]["text"].split()))


def repeats(text):
    """The share of four-word phrases that repeat an earlier one in the text."""
    words = text.lower().split()
    phrases = [tuple(words[i:i + 4]) for i in range(len(words) - 3)]
    return sum(count - 1 for count in Counter(phrases).values()) / max(len(phrases), 1)


print("products described, none of which has a description to draw on:", len(described))
for role in ["base", "tuned"]:
    texts = [row[role]["text"] for row in described]
    invented = sum(bool(claims.materials(row[role]["text"]) - claims.materials(row["name"])) for row in described)
    print(f"{role} model, descriptions that name a material the name doesn't:", f"{invented} of {len(described)}")
    print(f"{role} model, repeated four-word phrases:", f"{sum(map(repeats, texts)) / len(texts):.0%}")
