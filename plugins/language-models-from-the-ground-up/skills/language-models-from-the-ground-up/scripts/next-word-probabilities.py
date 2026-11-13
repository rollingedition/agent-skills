from lib.bigrams import Bigrams
from lib.store import load_products

model = Bigrams(load_products("train")["name"])
after_coffee, total = model.counts["coffee"], model.totals["coffee"]

for following in ["table", "mug", "jar", "lamp"]:
    print(f"P({following} | coffee): {after_coffee[following] / total:.3f}  ({after_coffee[following]} of {total})")
print("sum over every word after coffee:", round(sum(n / total for n in after_coffee.values()), 6))
