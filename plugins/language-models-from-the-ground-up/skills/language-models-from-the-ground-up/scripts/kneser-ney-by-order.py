"""Builds Kneser-Ney models of orders 1 to 5 on the training names, scores each on the validation names, and estimates a
discount from the 4-gram counts. The lines to read are the validation perplexities, the 3-gram's set against the interpolated trigram's, and the discount line."""
from lib.names import name_tokens
from lib.ngrams import KneserNey, perplexity

train, validation = name_tokens("train"), name_tokens("validation")
for n in [1, 2, 3, 4, 5]:
    model = KneserNey(train, n)
    print(f"{n}-gram validation perplexity: {perplexity(model, validation):.1f}")

model = KneserNey(train, 4)
# the highest order keeps raw counts, not continuation counts, so these are how often each 4-gram occurs in training
top = [c for following in model.counts[4].values() for c in following.values()]
once, twice = top.count(1), top.count(2)
print("4-grams seen once:", f"{once:,}")
print("4-grams seen twice:", f"{twice:,}")
# Chen and Goodman's estimate of the discount: D = n1 / (n1 + 2 n2), with n1 and n2 the counts seen once and twice
print("discount estimated from them:", f"{once / (once + 2 * twice):.2f}")
