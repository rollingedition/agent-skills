from collections import Counter, defaultdict

from lib.names import name_tokens

occurrences, before = Counter(), defaultdict(set)
for text in name_tokens("train"):
    for previous, token in zip(["<s>"] + text, text):
        occurrences[token] += 1
        before[token].add(previous)                 # the different tokens this one follows

common = [t for t, _ in occurrences.most_common(300)]
narrow = sorted(common, key=lambda t: len(before[t]) / occurrences[t])[:3]
for token in narrow + ["table</w>", "chair</w>"]:
    print(f"{token:<14} occurs {occurrences[token]:>5,} times, after {len(before[token]):>4,} different tokens")
