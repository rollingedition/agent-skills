from collections import Counter

from lib import bpe
from lib.store import load_products, words

word_counts = Counter(w for name in load_products("train")["name"] for w in words(name))
spelled = {w: list(w) + ["</w>"] for w in word_counts}       # every word as characters, plus an end marker

learned = []
for step in range(1, 9):
    pairs = Counter()
    for w, syms in spelled.items():                           # count every adjacent pair of symbols
        for pair in zip(syms, syms[1:]):
            pairs[pair] += word_counts[w]
    best = min(pairs, key=lambda p: (-pairs[p], p))           # the most frequent pair; ties go to the first in order
    for w, syms in spelled.items():                           # replace it everywhere with one new symbol
        merged, i = [], 0
        while i < len(syms):
            if syms[i:i + 2] == list(best):
                merged.append(syms[i] + syms[i + 1])
                i += 2
            else:
                merged.append(syms[i])
                i += 1
        spelled[w] = merged
    learned.append(best)
    print(f"merge {step}: {best[0]!r} + {best[1]!r} -> {best[0] + best[1]!r}  ({pairs[best]:,} times)")
print("table spelled now:", spelled["table"])
print("same merges as lib.bpe.train:", learned == bpe.train(word_counts, 8))
