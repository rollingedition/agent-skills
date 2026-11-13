from lib.names import name_tokens
from lib.ngrams import ngrams, padded

train, validation = name_tokens("train"), name_tokens("validation")
print("training tokens:", f"{sum(len(t) for t in train):,}")
print("validation tokens:", f"{sum(len(t) for t in validation):,}")
for n in [1, 2, 3, 4, 5]:
    seen = {pair for text in train for pair in ngrams(padded(text, n), n)}
    held_out = [pair for text in validation for pair in ngrams(padded(text, n), n)]
    unseen = sum(pair not in seen for pair in held_out)
    print(f"{n}-grams in validation never seen in training: {unseen / len(held_out):.1%}")
