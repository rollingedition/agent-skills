"""The repetition penalty applied by hand to the next token's logits, checked against lib.decoding.penalize, and then
used for a whole greedy description. The two P(distressed) lines are the ones the prose quotes, and the
assert against lib.decoding.penalize is the match it states as fact."""
import numpy as np

from lib import decoding, transformer

_, vocabulary, _ = transformer.load()
start, factor = decoding.prompt("front porch welcome sign wall décor"), 1.3
written = decoding.generate(start)                                    # greedy, as in greedy-description
distressed = vocabulary.index("distressed</w>")
position = [i for i, token in enumerate(written) if token == distressed][1]   # where greedy writes it a second time
before = written[:position]
print("text so far:", decoding.text(before))
print("penalty factor:", factor)

logits = decoding.next_logits(start + before)
seen = np.unique(before)                                              # every token the description has used
penalized = logits.copy()
penalized[seen] = np.where(logits[seen] > 0, logits[seen] / factor, logits[seen] * factor)   # less likely either way
assert np.allclose(penalized, decoding.penalize(logits, before, factor))   # the hand calculation is the library's
for label, adjusted in [("without a penalty", logits), ("with the penalty", penalized)]:
    probabilities = transformer.softmax(adjusted)
    top = np.argsort(-probabilities, kind="stable")[:3]
    print(f"next token, {label}:", ", ".join(f"{vocabulary[i].replace('</w>', '')} {probabilities[i]:.2f}" for i in top))
    print(f"P(distressed), {label}:", f"{probabilities[distressed]:.2f}")
print("greedy with the penalty:", decoding.text(decoding.generate(start, penalty=factor)))
