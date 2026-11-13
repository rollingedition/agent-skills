import numpy as np

from lib import bpe, transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey

_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
counted = KneserNey(name_tokens("train"), 4)
tokenizer = bpe.store_tokenizer()
as_counted = [{transformer.SEP: "</s>"}.get(token, token) for token in vocabulary]   # <sep> ends a name, as </s> does
show = lambda token: token.replace("</w>", "")

for prefix in ["bar", "patio bar", "outdoor bar", "kitchen bar", "wine bar"]:
    tokens = tokenizer.encode(prefix)
    ids = [index[transformer.START]] + [index[token] for token in tokens]
    from_transformer = transformer.softmax(transformer.forward(ids)[-1])
    context = tuple(["<s>"] * 3 + tokens)[-3:]
    from_counts = np.array([counted.probability(context, token) for token in as_counted])
    mixed = (from_transformer + from_counts) / 2
    for label, p in [("transformer", from_transformer), ("half and half", mixed)]:
        top = np.argsort(-p, kind="stable")[:3]
        print(f"{prefix:<12} {label:<13} -> " + ", ".join(f"{show(vocabulary[i])} {p[i]:.2f}" for i in top))
    if prefix == "outdoor bar":
        stool = index["stool</w>"]
        print("P(stool | outdoor bar), transformer:", f"{from_transformer[stool]:.2f}")
        print("P(stool | outdoor bar), 4-gram:", f"{from_counts[stool]:.2f}")
        print("P(stool | outdoor bar), half and half:", f"{mixed[stool]:.2f}")
