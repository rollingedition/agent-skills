import numpy as np

from lib import bpe, neural
from lib.ngrams import START

weights, vocabulary, manifest = neural.load()
index, width = {t: i for i, t in enumerate(vocabulary)}, manifest["settings"]["context"]
tokenizer = bpe.store_tokenizer()

for typed in ["bar", "patio bar", "outdoor bar", "kitchen bar", "wine bar"]:
    context = ([START] * width + tokenizer.encode(typed))[-width:]
    logits = neural.forward(weights, np.array([[index[t] for t in context]]))[0]
    probabilities = np.exp(neural.log_softmax(logits[None])[0])
    best = np.argsort(-probabilities, kind="stable")[:3]
    print(f"{typed:<12} -> " + ", ".join(f"{vocabulary[i].replace('</w>', '')} {probabilities[i]:.2f}" for i in best))

outdoor_bar = ([START] * width + tokenizer.encode("outdoor bar"))[-width:]
p_stool = np.exp(neural.log_softmax(neural.forward(weights, np.array([[index[t] for t in outdoor_bar]])))[0, index["stool</w>"]])
print("P(stool | outdoor bar):", f"{p_stool:.2f}")
table = weights["embedding"] / np.linalg.norm(weights["embedding"], axis=1, keepdims=True)
for a, b in [("patio</w>", "outdoor</w>"), ("patio</w>", "kitchen</w>"), ("patio</w>", "wine</w>")]:
    print(f"cosine({a.replace('</w>', '')}, {b.replace('</w>', '')}) in the model's embeddings:", f"{float(table[index[a]] @ table[index[b]]):.2f}")
