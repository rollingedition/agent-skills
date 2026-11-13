"""Classes both models' answers to the material question, split by whether the product's name or description names a
material. The prose's point rests on the rows for products whose data names none: made up and declined.
"""
from collections import Counter

from lib import claims, recorded

asked = recorded.read("instruction-tuning", "answers")
print("products asked, each with its description given:", len(asked))
# a product's data names a material if its description or its name does: the union of the two sets
given = [bool(claims.materials(row["description"]) | claims.materials(row["name"])) for row in asked]
print("products whose name or description names a material:", sum(given))
print("products whose name and description name none:", len(given) - sum(given))
for role in ["base", "tuned"]:
    for label, keep in [("data names a material", True), ("data names none", False)]:
        rows = [row for row, named in zip(asked, given) if named == keep]
        # each answer is classed against the product's data, by the rules in lib.claims
        counts = Counter(claims.classify(row[role]["text"], row["description"], row["name"]) for row in rows)
        for kind in ["supported", "made up", "none", "declined"]:
            print(f"{role} model, {label}, {kind}:", counts[kind])
