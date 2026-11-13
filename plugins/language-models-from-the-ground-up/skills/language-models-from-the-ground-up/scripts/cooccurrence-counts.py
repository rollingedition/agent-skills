"""Counts how often each of the 2,000 kept tokens appears within two tokens of another, and lists the six tokens seen most
often near patio. The prose's point rests on that list: punctuation and common words come first."""
import numpy as np

from lib.vectors import BREAK, cooccurrence, training_ids          # the book's shared module; BREAK marks the gap between two texts

ids, vocabulary = training_ids()                                   # each training token as a number; RARE for tokens outside the vocabulary
counts = cooccurrence(ids, len(vocabulary))          # how often each token appears within 2 tokens of another
patio = vocabulary.index("patio</w>")                # </w> marks a word's last token: patio</w> is the whole word, not a piece of a longer one

print("training tokens:", f"{int((ids != BREAK).sum()):,}")          # RARE tokens count here, since they are tokens; only the BREAK gaps don't
print("vocabulary kept:", f"{len(vocabulary):,}")
print("tokens near patio, counting repeats:", f"{int(counts[patio].sum()):,}")   # the row's total, a token counted again at each repeat
for i in np.argsort(-counts[patio], kind="stable")[:6]:          # the minus sorts most frequent first; ties keep vocabulary order
    print(f"  near patio: {vocabulary[i]:<12} {int(counts[patio, i]):>6,}")
