import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
start, longest, seed = decoding.prompt("front porch welcome sign wall décor"), 40, 2026
print("longest description, in tokens:", longest)
print("random seed:", seed)
for label, settings in [("sampling, temperature 1.0", {}), ("sampling, temperature 0.7", {"temperature": 0.7}),
                        ("top-k 20", {"top_k": 20}), ("top-p 0.9", {"top_p": 0.9})]:
    ids = decoding.generate(start, rng=np.random.default_rng(seed), longest=longest, **settings)
    print(f"{label}:", decoding.text(ids))

rng, written, tail = np.random.default_rng(seed), [], []    # replay temperature 1.0's draws, step by step
for _ in range(longest):
    probabilities = transformer.softmax(decoding.next_logits(start + written))
    token = int(rng.choice(len(probabilities), p=decoding.truncate(probabilities)))
    order = np.argsort(-probabilities, kind="stable")
    before = probabilities[order[:int(np.where(order == token)[0][0])]].sum()   # the probability ranked above it
    if before >= 0.9:
        tail.append(vocabulary[token].replace("</w>", ""))
    written.append(token)
    if vocabulary[token] == transformer.END:
        break
print("temperature 1.0, tokens drawn from outside the 90% nucleus:", f"{len(tail)} of {len(written)}")
print("temperature 1.0, those tokens:", ", ".join(tail))
