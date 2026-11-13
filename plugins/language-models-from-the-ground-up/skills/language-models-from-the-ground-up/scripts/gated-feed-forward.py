"""Computes SiLU at three points, then runs block 1's feed-forward layer on one validation product and counts the hidden
units its gate nearly shuts at each position. The prose's point rests on the three SiLU values and on that count."""
import numpy as np

from lib import transformer
from lib.products import product_texts

print("silu(-3), silu(0), silu(3):", ", ".join(f"{v:.2f}" for v in transformer.silu(np.array([-3.0, 0.0, 3.0]))))

ids, _ = product_texts("validation", 1)[0]            # the first validation product; its <sep> position isn't needed
heads = transformer.load()[2]["settings"]["heads"]    # load returns (weights, vocabulary, manifest): index 2 is the manifest
first = transformer.layer_weights(0)                   # block 1's weights
x = transformer.load()[0]["embedding"][np.array(ids)]  # index 0 is the weights: the embeddings, the stream entering block 1
attended, _ = transformer.attention(transformer.rms_norm(x, first["norm1"]), first, heads)
normalized = transformer.rms_norm(x + attended, first["norm2"])   # what block 1's feed-forward layer reads
gate = transformer.silu(normalized @ first["gate"])    # how much of each hidden unit to let through
up = normalized @ first["up"]                          # what each hidden unit carries
output = (gate * up) @ first["down"]                   # gated, then projected back to the stream's width
shut = (np.abs(gate) < 0.05).sum(1)                    # per position; 0.05 is the threshold for "nearly shut"
print("hidden units:", gate.shape[1])
print("hidden units nearly shut at a position (gate under 0.05 in size), on average:", f"{shut.mean():.0f}")
print("fewest and most nearly shut at a position:", f"{shut.min()} and {shut.max()}")
print("positions:", len(ids))
print("output shape:", output.shape)
