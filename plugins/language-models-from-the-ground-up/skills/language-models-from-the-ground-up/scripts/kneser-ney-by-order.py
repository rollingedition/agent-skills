from lib.names import name_tokens
from lib.ngrams import KneserNey, perplexity

train, validation = name_tokens("train"), name_tokens("validation")
for n in [1, 2, 3, 4, 5]:
    model = KneserNey(train, n)
    print(f"{n}-gram validation perplexity: {perplexity(model, validation):.1f}")

model = KneserNey(train, 4)
top = [c for following in model.counts[4].values() for c in following.values()]
once, twice = top.count(1), top.count(2)
print("4-grams seen once:", f"{once:,}")
print("4-grams seen twice:", f"{twice:,}")
print("discount estimated from them:", f"{once / (once + 2 * twice):.2f}")
