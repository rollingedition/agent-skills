import json

import numpy as np

from lib import bpe
from lib.store import load_products, masked

vectors = np.load("data/recorded/skipgram/vectors.npy")
vocabulary = json.load(open("data/recorded/skipgram/vocabulary.json", encoding="utf-8"))
index, tokenizer = {t: i for i, t in enumerate(vocabulary)}, bpe.store_tokenizer()


def name_vector(text):                               # the average of the text's token vectors, at unit length
    found = [index[t] for t in tokenizer.encode(text) if t in index]
    average = vectors[found].mean(0) if found else np.zeros(vectors.shape[1])
    return average / (np.linalg.norm(average) or 1.0)


names = load_products("train")["name"].tolist()
matrix = np.array([name_vector(n) for n in names])
for query in ["outdoor bar", "patio umbrella"]:
    best = np.argsort(-(matrix @ name_vector(query)), kind="stable")[:4]
    print(f"{query}: " + " | ".join(masked(names[i]) for i in best))   # [name]: a rare word
