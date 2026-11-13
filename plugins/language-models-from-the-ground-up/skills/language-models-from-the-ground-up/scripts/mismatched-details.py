import numpy as np

from lib import transformer
from lib.products import product_texts

texts = [ids for ids, _ in product_texts("validation", 100)]


def neighbours(x, base=10000.0):
    """RoPE that pairs neighbouring numbers, (0, 1), (2, 3) and so on, instead of the first half with the second."""
    half = x.shape[-1] // 2
    rotated = transformer.rope(np.concatenate([x[..., 0::2], x[..., 1::2]], axis=-1), base)
    out = np.empty_like(x)
    out[..., 0::2], out[..., 1::2] = rotated[..., :half], rotated[..., half:]
    return out


for label, positions in [("as trained", transformer.rope),
                         ("RoPE pairing neighbouring numbers", neighbours),
                         ("RoPE with base 100,000", lambda x: transformer.rope(x, base=100000.0)),
                         ("no RoPE", lambda x: x)]:
    print(f"perplexity, {label}:", f"{transformer.perplexity(texts, positions=positions):,.1f}")
