"""One prediction of the trained window model, computed by hand from its saved weights: the embeddings, the tanh layer,
the output scores and the softmax. The prose's point rests on the shapes, the parameter counts and the three likeliest
tokens after `patio bar`."""
import numpy as np

from lib import bpe, neural
from lib.ngrams import START

weights, vocabulary, manifest = neural.load()
index, width = {t: i for i, t in enumerate(vocabulary)}, manifest["settings"]["context"]   # token -> row; the window's width, from the saved settings
context = ([START] * width + bpe.store_tokenizer().encode("patio bar"))[-width:]   # pad with start markers, keep the last width tokens
ids = np.array([[index[t] for t in context]])

vectors = weights["embedding"][ids]                                    # one 64-number vector per token
joined = vectors.reshape(1, -1)                                        # -1 lets numpy work out the length: 4 vectors of 64 make 256
hidden = np.tanh(joined @ weights["hidden_w"] + weights["hidden_b"])   # one layer, squashed into -1 to 1
logits = hidden @ weights["output_w"] + weights["output_b"]            # one score for every token
probabilities = np.exp(logits - logits.max())                          # subtract the largest score first: same probabilities, and exp can't overflow
probabilities /= probabilities.sum()                                   # softmax: scores into probabilities

print("context:", " ".join(context))
for name, array in [("embeddings", vectors), ("joined", joined), ("hidden", hidden), ("logits", logits)]:
    print(f"{name} shape:", array.shape)
print("vocabulary size:", f"{len(vocabulary):,}")
print("parameters:", f"{sum(w.size for w in weights.values()):,}")
for part in ["embedding", "hidden_w", "output_w"]:
    print(f"parameters in {part}:", f"{weights[part].size:,}")
for i in np.argsort(-probabilities[0], kind="stable")[:3]:             # the three likeliest; a stable sort keeps ties in vocabulary order
    print(f"P({vocabulary[i]} | patio bar): {probabilities[0, i]:.2f}")
