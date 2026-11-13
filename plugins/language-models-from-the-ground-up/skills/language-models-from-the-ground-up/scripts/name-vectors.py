"""Averages each training name's skip-gram token vectors into one unit-length vector, and prints the four training names
nearest to each of two queries. The prose's point rests on the first query: two patio bar stool names come up for outdoor bar."""
import json

import numpy as np

from lib import bpe
from lib.store import load_products, masked

vectors = np.load("data/recorded/skipgram/vectors.npy")
vocabulary = json.load(open("data/recorded/skipgram/vocabulary.json", encoding="utf-8"))
index, tokenizer = {t: i for i, t in enumerate(vocabulary)}, bpe.store_tokenizer()


def name_vector(text):                               # the average of the text's token vectors, at unit length
    found = [index[t] for t in tokenizer.encode(text) if t in index]    # tokens outside the 2,000 kept have no vector, so they're left out
    average = vectors[found].mean(0) if found else np.zeros(vectors.shape[1])   # a text with no kept tokens gets the zero vector
    return average / (np.linalg.norm(average) or 1.0)            # `or 1.0`: a zero average stays zero, rather than dividing by zero


names = load_products("train")["name"].tolist()        # the training split's product names, the texts to compare
matrix = np.array([name_vector(n) for n in names])
for query in ["outdoor bar", "patio umbrella"]:
    best = np.argsort(-(matrix @ name_vector(query)), kind="stable")[:4]   # unit vectors, so the dot product is the cosine; the four largest, most similar first
    print(f"{query}: " + " | ".join(masked(names[i]) for i in best))   # [name]: a rare word
