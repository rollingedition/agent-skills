from collections import defaultdict

from lib import claims, recorded

context = recorded.read("instruction-tuning", "context")
others = recorded.read("instruction-tuning", "manifest")["settings"]["context_others"]
print("product listings in each context:", others + 1)
results = defaultdict(list)
for row in context:
    if claims.materials(row["description"]) | claims.materials(row["name"]):   # only products whose data names one
        results[row["place"]].append(claims.classify(row["tuned"]["text"], row["description"], row["name"]) == "supported")
print("products asked about at each place:", len(results["first"]))
for place in ["first", "middle", "last"]:
    print(f"product placed {place}, answers that name only its own materials:", f"{sum(results[place])} of {len(results[place])}")
