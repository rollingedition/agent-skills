"""Counts, for each token in the training names, how often it occurs and how many different tokens come right before it.
Look at the three narrowest tokens, which occur often but follow few different tokens, beside table and chair."""
from collections import Counter, defaultdict

from lib.names import name_tokens

occurrences, before = Counter(), defaultdict(set)
for text in name_tokens("train"):
    for previous, token in zip(["<s>"] + text, text):      # the start marker stands before each name's first token, so that token has something to follow too
        occurrences[token] += 1
        before[token].add(previous)                 # the different tokens this one follows

common = [t for t, _ in occurrences.most_common(300)]     # the 300 most frequent tokens: the pool the prose ranks
# different tokens followed, per occurrence, lowest first: the three narrowest
narrow = sorted(common, key=lambda t: len(before[t]) / occurrences[t])[:3]
for token in narrow + ["table</w>", "chair</w>"]:       # </w> marks a token that ends a word, as the store's tokenizer writes it
    print(f"{token:<14} occurs {occurrences[token]:>5,} times, after {len(before[token]):>4,} different tokens")
