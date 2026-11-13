"""Scores the same 100 validation products with the trained weights, changing one detail of RoPE at a time: how it pairs
numbers, its base, and whether it is applied at all. The prose's point rests on each variant's perplexity, printed
beside the trained model's."""
import numpy as np

from lib import transformer
from lib.products import product_texts

texts = [ids for ids, _ in product_texts("validation", 100)]   # the <sep> positions aren't needed: each text is scored whole


def neighbours(x, base=10000.0):
    """RoPE that pairs neighbouring numbers, (0, 1), (2, 3) and so on, instead of the first half with the second."""
    half = x.shape[-1] // 2
    rotated = transformer.rope(np.concatenate([x[..., 0::2], x[..., 1::2]], axis=-1), base)   # even numbers, then odd: rope pairs halves, so these are neighbours
    out = np.empty_like(x)
    out[..., 0::2], out[..., 1::2] = rotated[..., :half], rotated[..., half:]                 # each rotated number back where its dimension was
    return out


for label, positions in [("as trained", transformer.rope),
                         ("RoPE pairing neighbouring numbers", neighbours),
                         ("RoPE with base 100,000", lambda x: transformer.rope(x, base=100000.0)),   # 100,000 is SmolLM2's base
                         ("no RoPE", lambda x: x)]:          # no RoPE: the queries and keys pass through unrotated
    print(f"perplexity, {label}:", f"{transformer.perplexity(texts, positions=positions):,.1f}")
