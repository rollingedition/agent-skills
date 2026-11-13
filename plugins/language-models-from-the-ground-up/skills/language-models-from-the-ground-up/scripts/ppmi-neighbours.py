"""Reweights the co-occurrence counts with positive PMI, and lists the six tokens with the strongest weight beside patio.
The prose's point rests on that list: the commas and common words of the raw counts are gone."""
import numpy as np

from lib.vectors import cooccurrence, ppmi, training_ids

ids, vocabulary = training_ids()                     # each training token as a number; RARE for tokens outside the vocabulary
weights = ppmi(cooccurrence(ids, len(vocabulary)))   # PPMI of the co-occurrence counts, within the same window of 2 tokens
patio = vocabulary.index("patio</w>")                # </w> marks a word's last token: patio</w> is the whole word

print("share of PPMI entries that are zero:", f"{(weights == 0).mean():.0%}")   # zero for pairs that never co-occur and for pairs seen no more often than chance
for i in np.argsort(-weights[patio], kind="stable")[:6]:      # the largest weights first; ties keep vocabulary order
    print(f"  PPMI with patio: {vocabulary[i]:<12} {weights[patio, i]:.2f}")
