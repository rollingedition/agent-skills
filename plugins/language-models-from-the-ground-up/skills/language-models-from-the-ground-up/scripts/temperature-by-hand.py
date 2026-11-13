import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
start = decoding.prompt("front porch welcome sign wall décor")
so_far = decoding.generate(start, longest=9)                   # the greedy description's first 9 tokens
logits = decoding.next_logits(start + so_far)
print("text so far:", decoding.text(so_far))
print("tokens in the vocabulary:", f"{len(vocabulary):,}")
cover = np.argsort(-transformer.softmax(logits), kind="stable")    # at temperature 1, the likeliest first
cover = cover[:int(np.searchsorted(np.cumsum(transformer.softmax(logits)[cover]), 0.9)) + 1]
for temperature in [0.5, 1.0, 1.5]:
    probabilities = transformer.softmax(logits / temperature)     # divide the logits, then softmax
    top = np.argsort(-probabilities, kind="stable")
    covering = int(np.searchsorted(np.cumsum(probabilities[top]), 0.9)) + 1
    print(f"temperature {temperature}, top 3:", ", ".join(f'"{vocabulary[i].replace("</w>", "")}" {probabilities[i]:.2f}' for i in top[:3]))
    print(f"temperature {temperature}, tokens needed to cover 90% of the probability:", covering)
    print(f"temperature {temperature}, probability outside temperature 1.0's 90% cover:",
          f"{1 - probabilities[cover].sum():.0%}")
