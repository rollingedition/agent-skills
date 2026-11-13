import numpy as np

from lib import transformer
from lib.products import product_texts

weights, _, manifest = transformer.load()
ids, sep = product_texts("validation", 1)[0]
x = weights["embedding"][np.array(ids)]
print("length of the vectors entering layer 1:", f"{np.linalg.norm(x, axis=1).mean():.2f}")
for layer in range(manifest["settings"]["layers"]):
    layer_weights = transformer.layer_weights(layer)
    added_by_attention, _ = transformer.attention(transformer.rms_norm(x, layer_weights["norm1"]), layer_weights, manifest["settings"]["heads"])
    x = x + added_by_attention
    normalized = transformer.rms_norm(x, layer_weights["norm2"])
    added_by_feed_forward = (transformer.silu(normalized @ layer_weights["gate"]) * (normalized @ layer_weights["up"])) @ layer_weights["down"]
    x = x + added_by_feed_forward
    print(f"layer {layer + 1}: attention adds {np.linalg.norm(added_by_attention, axis=1).mean():.2f}, "
          f"feed-forward adds {np.linalg.norm(added_by_feed_forward, axis=1).mean():.2f}, "
          f"vectors now {np.linalg.norm(x, axis=1).mean():.2f}")
print("length of the vectors leaving the last layer:", f"{np.linalg.norm(x, axis=1).mean():.2f}")
print("largest number in the stream:", f"{np.abs(x).max():.1f}")
