"""Counts the tuned model's answers that name only the asked product's own materials, with the product first, in the middle
or last of a context of listings. The prose's point rests on the three placement lines.
"""
from collections import defaultdict

from lib import claims, recorded

context = recorded.read("instruction-tuning", "context")
# the other listings in each context; the asked product is one more, as the first printed line shows
others = recorded.read("instruction-tuning", "manifest")["settings"]["context_others"]
print("product listings in each context:", others + 1)
results = defaultdict(list)
for row in context:
    # only products whose data names a material: a product with none gives an answer nothing to name
    if claims.materials(row["description"]) | claims.materials(row["name"]):
        # supported: every material the answer names is in the asked product's own data
        results[row["place"]].append(claims.classify(row["tuned"]["text"], row["description"], row["name"]) == "supported")
print("products asked about at each place:", len(results["first"]))
for place in ["first", "middle", "last"]:
    print(f"product placed {place}, answers that name only its own materials:", f"{sum(results[place])} of {len(results[place])}")
