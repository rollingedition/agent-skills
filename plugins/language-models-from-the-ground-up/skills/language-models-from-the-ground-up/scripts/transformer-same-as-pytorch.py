"""Recomputes the store's model's logits in NumPy for the validation product the training script saved, and checks every
one against PyTorch's to four decimal places. The prose's point rests on the count of logits compared, and on the
assertion that they all match."""
import numpy as np

from lib import transformer

_, _, manifest = transformer.load()
check = np.load("data/recorded/transformer/check.npz")      # one validation product's ids, and PyTorch's logits

ours = transformer.forward(list(check["ids"]))               # forward takes a list of token ids, not an array
print("PyTorch version:", manifest["torch"])
print("positions compared:", len(check["ids"]))
print("logits compared:", f"{ours.size:,}")
assert np.abs(ours - check["logits"]).max() < 1e-4           # 1e-4 is four decimal places
print("same as PyTorch to 4 decimal places:", "yes")
