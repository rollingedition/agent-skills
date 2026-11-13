import numpy as np

from lib import transformer
from lib.products import product_texts

ids, _ = product_texts("validation", 1)[0]
streams, _ = transformer.run(ids)                      # the residual stream entering block 1 and leaving each block
gain = np.ones(streams[0].shape[1])                    # the learned gain set to 1, to show the normalization alone
for label, x in [("entering block 1", streams[0]), ("leaving the last block", streams[-1])]:
    root_mean_square = np.sqrt((x ** 2).mean(1, keepdims=True) + 1e-5)   # one per position; 1e-5 is the ε
    by_hand = x / root_mean_square * gain
    print(f"root mean square {label}, before:", f"{root_mean_square.mean():.2f}")
    print(f"root mean square {label}, after:", f"{np.sqrt((by_hand ** 2).mean(1)).mean():.2f}")
    print(f"same as lib.transformer.rms_norm, {label}:", bool(np.allclose(by_hand, transformer.rms_norm(x, gain), atol=1e-4)))
    print(f"largest mean of a position's numbers after, {label}:", f"{np.abs(by_hand.mean(1)).max():.2f}")
