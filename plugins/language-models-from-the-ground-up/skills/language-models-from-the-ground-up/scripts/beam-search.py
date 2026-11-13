"""Beam search with a beam of four, on a search query and on a product's description. The prose quotes the two
completions of outdoor bar, then the likeliest description, its probability and the likeliest per token."""
import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
width, longest = 4, 4
print("beam width:", width)
print("longest completion, in tokens, its end included:", longest)
start = decoding.prompt("outdoor bar")[:-1]                  # a search query: <s> and the words typed so far
for score, written in decoding.beam(start, width=width, longest=longest, stops=(transformer.SEP,))[:2]:   # stop at <sep>, where a name ends; keep the two likeliest
    print("completion of outdoor bar:", decoding.text([t for t in written if vocabulary[t] != transformer.SEP]),
          f"(probability {np.exp(score):.3f})")

kept = decoding.beam(decoding.prompt("front porch welcome sign wall décor"), width=width)   # longest and stops take their defaults: 60 tokens, </s>
score, written = kept[0]                                     # the likeliest text overall
print("likeliest description:", decoding.text(written) or "(empty)")
print("its probability:", f"{np.exp(score):.2f}")
score, written = max(kept, key=lambda candidate: candidate[0] / len(candidate[1]))   # the likeliest per token
print("likeliest description per token:", decoding.text(written))
