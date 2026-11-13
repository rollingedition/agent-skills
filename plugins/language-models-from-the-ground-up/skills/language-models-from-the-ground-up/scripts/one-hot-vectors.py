"""One-hot vectors for the 2,000 most frequent tokens, and the cosine similarity of patio with outdoor, with sofa and with
itself. The prose's point rests on the patio–outdoor and patio–sofa lines: patio is as unrelated to outdoor as to sofa."""
import numpy as np

from lib.vectors import BREAK, training_ids                 # the book's shared module; BREAK marks the gap between two texts

ids, vocabulary = training_ids()                            # each training token as a number; RARE for tokens outside the vocabulary
index = {token: i for i, token in enumerate(vocabulary)}


def one_hot(token):
    vector = np.zeros(len(vocabulary))
    vector[index[token]] = 1.0                       # one column per token: 1 for this token, 0 everywhere else
    return vector


def cosine(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


print("numbers in each vector:", len(vocabulary))
print("cosine(patio, outdoor):", cosine(one_hot("patio</w>"), one_hot("outdoor</w>")))    # </w> marks a word's last token: patio</w> is the whole word
print("cosine(patio, sofa):", cosine(one_hot("patio</w>"), one_hot("sofa</w>")))
print("cosine(patio, patio):", cosine(one_hot("patio</w>"), one_hot("patio</w>")))
print("share of training tokens with a vector:", f"{(ids >= 0).sum() / (ids != BREAK).sum():.0%}")   # ids >= 0 are the kept tokens; BREAK gaps aren't tokens
