from collections import Counter

from lib import bpe
from lib.store import load_products, words

training, validation = load_products("train"), load_products("validation")
counts = Counter(w for text in training["name"] + " " + training["description"] for w in words(text))
merges = bpe.train(counts, merges=16000)             # the first k merges of a longer run are a k-merge tokenizer
validation_words = [w for text in validation["name"] + " " + validation["description"] for w in words(text)]

results = {}
print(f"{'merges':>6}  {'tokens used':>11}  {'tokens per word':>15}  {'rare types':>10}")
for k in [0, 1000, 2000, 4000, 8000, 16000]:
    tokenizer = bpe.Tokenizer(merges[:k], bpe.alphabet(counts)) if k else None
    encode = tokenizer.encode_word if k else bpe.symbols
    seen = Counter(t for w, n in counts.items() for t in encode(w) for _ in range(n))
    per_word = sum(len(encode(w)) for w in validation_words) / len(validation_words)
    rare = sum(1 for n in seen.values() if n < 20) / len(seen)  # share of different tokens seen fewer than 20 times
    print(f"{k:>6,}  {len(seen):>11,}  {per_word:>15.2f}  {rare:>10.0%}")
    results[k] = per_word, rare
print("tokens per word at 4,000 merges:", f"{results[4000][0]:.2f}")
print("rare token types with characters only:", f"{results[0][1]:.0%}")
print("rare token types at 4,000 merges:", f"{results[4000][1]:.0%}")
print("rare token types at 16,000 merges:", f"{results[16000][1]:.0%}")
