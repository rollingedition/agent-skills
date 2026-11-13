"""The network's three likeliest next tokens after five typed prefixes, its probability of `stool` after `outdoor bar`,
and the cosine similarity of `patio` with three other tokens in its embedding table. The prose's point rests on the
suggestions after each prefix, and on the three cosines printed last."""
import numpy as np

from lib import bpe, neural
from lib.ngrams import START

weights, vocabulary, manifest = neural.load()
index, width = {t: i for i, t in enumerate(vocabulary)}, manifest["settings"]["context"]
tokenizer = bpe.store_tokenizer()

for typed in ["bar", "patio bar", "outdoor bar", "kitchen bar", "wine bar"]:    # each typed prefix is read as the start of a name
    context = ([START] * width + tokenizer.encode(typed))[-width:]               # pad with start markers, keep the last width tokens
    logits = neural.forward(weights, np.array([[index[t] for t in context]]))[0]   # forward takes a batch: one row, so take row 0
    probabilities = np.exp(neural.log_softmax(logits[None])[0])                 # log_softmax wants a batch too: add an axis, then take it off
    best = np.argsort(-probabilities, kind="stable")[:3]                        # the three likeliest; a stable sort keeps ties in vocabulary order
    # the end-of-word marker </w> is shown as nothing, so the tokens read as the words they came from
    print(f"{typed:<12} -> " + ", ".join(f"{vocabulary[i].replace('</w>', '')} {probabilities[i]:.2f}" for i in best))

outdoor_bar = ([START] * width + tokenizer.encode("outdoor bar"))[-width:]      # the same padding as above
p_stool = np.exp(neural.log_softmax(neural.forward(weights, np.array([[index[t] for t in outdoor_bar]])))[0, index["stool</w>"]])
print("P(stool | outdoor bar):", f"{p_stool:.2f}")
table = weights["embedding"] / np.linalg.norm(weights["embedding"], axis=1, keepdims=True)   # unit-length rows, so a dot product is a cosine
for a, b in [("patio</w>", "outdoor</w>"), ("patio</w>", "kitchen</w>"), ("patio</w>", "wine</w>")]:
    print(f"cosine({a.replace('</w>', '')}, {b.replace('</w>', '')}) in the model's embeddings:", f"{float(table[index[a]] @ table[index[b]]):.2f}")
