"""The trained model's logits, recomputed in NumPy from its saved weights and compared with the logits PyTorch computed
for the same saved validation contexts. The prose's point rests on the agreement, which the last line prints."""
import numpy as np

from lib import neural

weights, _, manifest = neural.load()
check = np.load("data/recorded/neural-lm/check.npz")                 # saved by the training script, so this runs without PyTorch: contexts, and PyTorch's logits for them

ours = neural.forward(weights, check["contexts"])
print("PyTorch version:", manifest["torch"])
print("contexts compared:", len(check["contexts"]))
print("logits compared:", f"{ours.size:,}")                          # every logit: one per context and per token in the vocabulary
print("same as PyTorch to 4 decimal places:", bool(np.abs(ours - check["logits"]).max() < 1e-4))   # 1e-4: four decimal places
