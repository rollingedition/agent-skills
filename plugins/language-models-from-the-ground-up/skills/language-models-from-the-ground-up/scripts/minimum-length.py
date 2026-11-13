from lib import decoding, transformer

end = transformer.load()[1].index(transformer.END)
start, shortest = decoding.prompt("5 light light bulb"), 10
print("P(the description is empty):", f"{transformer.softmax(decoding.next_logits(start))[end]:.2f}")
print("greedy description:", decoding.text(decoding.generate(start)) or "(empty)")
print("minimum length, in tokens:", shortest)
print("greedy description, with the minimum:", decoding.text(decoding.generate(start, shortest=shortest)))
