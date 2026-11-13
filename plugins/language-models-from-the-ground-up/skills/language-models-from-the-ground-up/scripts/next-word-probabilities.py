"""Divides how often each of four words followed coffee by how often coffee was followed by anything, then prints the sum of the
probabilities of every word after coffee. The line for lamp, which prints 0.000, is the one the prose's point rests on:
the bigram model gives a pair it never counted no probability at all."""
from lib.bigrams import Bigrams
from lib.store import load_products

model = Bigrams(load_products("train")["name"])
after_coffee, total = model.counts["coffee"], model.totals["coffee"]   # counts[word] is a Counter of the words after word; totals[word] is their sum

for following in ["table", "mug", "jar", "lamp"]:
    print(f"P({following} | coffee): {after_coffee[following] / total:.3f}  ({after_coffee[following]} of {total})")   # a Counter returns 0 for a word never seen after coffee, not an error
print("sum over every word after coffee:", round(sum(n / total for n in after_coffee.values()), 6))   # rounded, so float error doesn't show in the sum
