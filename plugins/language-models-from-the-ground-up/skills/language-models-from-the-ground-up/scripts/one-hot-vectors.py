import numpy as np

from lib.vectors import BREAK, training_ids

ids, vocabulary = training_ids()
index = {token: i for i, token in enumerate(vocabulary)}


def one_hot(token):
    vector = np.zeros(len(vocabulary))
    vector[index[token]] = 1.0                       # one column per token: 1 for this token, 0 everywhere else
    return vector


def cosine(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


print("numbers in each vector:", len(vocabulary))
print("cosine(patio, outdoor):", cosine(one_hot("patio</w>"), one_hot("outdoor</w>")))
print("cosine(patio, sofa):", cosine(one_hot("patio</w>"), one_hot("sofa</w>")))
print("cosine(patio, patio):", cosine(one_hot("patio</w>"), one_hot("patio</w>")))
print("share of training tokens with a vector:", f"{(ids >= 0).sum() / (ids != BREAK).sum():.0%}")
