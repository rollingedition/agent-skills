import numpy as np

from lib import neural

weights, _, manifest = neural.load()
check = np.load("data/recorded/neural-lm/check.npz")                 # contexts, and PyTorch's logits for them

ours = neural.forward(weights, check["contexts"])
print("PyTorch version:", manifest["torch"])
print("contexts compared:", len(check["contexts"]))
print("logits compared:", f"{ours.size:,}")
print("same as PyTorch to 4 decimal places:", bool(np.abs(ours - check["logits"]).max() < 1e-4))
