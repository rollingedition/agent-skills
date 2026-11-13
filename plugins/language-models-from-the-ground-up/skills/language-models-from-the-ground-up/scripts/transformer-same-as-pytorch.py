import numpy as np

from lib import transformer

_, _, manifest = transformer.load()
check = np.load("data/recorded/transformer/check.npz")      # one validation product's ids, and PyTorch's logits

ours = transformer.forward(list(check["ids"]))
print("PyTorch version:", manifest["torch"])
print("positions compared:", len(check["ids"]))
print("logits compared:", f"{ours.size:,}")
print("same as PyTorch to 4 decimal places:", bool(np.abs(ours - check["logits"]).max() < 1e-4))
