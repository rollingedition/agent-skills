import numpy as np

from lib.vectors import BREAK, cooccurrence, training_ids

ids, vocabulary = training_ids()
counts = cooccurrence(ids, len(vocabulary))          # how often each token appears within 2 tokens of another
patio = vocabulary.index("patio</w>")

print("training tokens:", f"{int((ids != BREAK).sum()):,}")
print("vocabulary kept:", f"{len(vocabulary):,}")
print("tokens near patio, counting repeats:", f"{int(counts[patio].sum()):,}")
for i in np.argsort(-counts[patio], kind="stable")[:6]:
    print(f"  near patio: {vocabulary[i]:<12} {int(counts[patio, i]):>6,}")
