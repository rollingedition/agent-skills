import numpy as np

from lib.vectors import cooccurrence, ppmi, training_ids

ids, vocabulary = training_ids()
weights = ppmi(cooccurrence(ids, len(vocabulary)))
patio = vocabulary.index("patio</w>")

print("share of PPMI entries that are zero:", f"{(weights == 0).mean():.0%}")
for i in np.argsort(-weights[patio], kind="stable")[:6]:
    print(f"  PPMI with patio: {vocabulary[i]:<12} {weights[patio, i]:.2f}")
