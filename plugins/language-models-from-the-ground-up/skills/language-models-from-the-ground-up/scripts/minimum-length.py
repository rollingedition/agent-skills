"""Greedy decoding of the bulb's description, without a minimum length and with one that forbids the end marker until
it has that many tokens. The prose quotes the printed probability of an empty description, and
the description the minimum produces."""
from lib import decoding, transformer

end = transformer.load()[1].index(transformer.END)                    # the index of </s>, to read its probability
start, shortest = decoding.prompt("5 light light bulb"), 10
print("P(the description is empty):", f"{transformer.softmax(decoding.next_logits(start))[end]:.2f}")   # the first token is </s>: an empty description
print("greedy description:", decoding.text(decoding.generate(start)) or "(empty)")
print("minimum length, in tokens:", shortest)
print("greedy description, with the minimum:", decoding.text(decoding.generate(start, shortest=shortest)))   # shortest: </s> stays forbidden until then
