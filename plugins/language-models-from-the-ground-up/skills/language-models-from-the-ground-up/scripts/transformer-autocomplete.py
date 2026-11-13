"""Asks the transformer and its half-and-half mix with the 4-gram for their three likeliest next tokens after five prefixes,
treated as the start of a name, and prints the probability of stool after outdoor bar. The prose's point rests on the
stool lines and the control prefixes beside them."""
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
    context = tuple(["<s>"] * 3 + tokens)[-3:]   # the 4-gram looks at the last three tokens, padded with start markers for a short prefix
    from_counts = np.array([counted.probability(context, token) for token in as_counted])
    mixed = (from_transformer + from_counts) / 2
    for label, p in [("transformer", from_transformer), ("half and half", mixed)]:
        top = np.argsort(-p, kind="stable")[:3]   # the three likeliest; a stable sort keeps tied tokens in vocabulary order
        print(f"{prefix:<12} {label:<13} -> " + ", ".join(f"{show(vocabulary[i])} {p[i]:.2f}" for i in top))
    if prefix == "outdoor bar":
        stool = index["stool</w>"]   # </w> marks the end of a word in the tokenizer, so this is the whole word stool
        print("P(stool | outdoor bar), transformer:", f"{from_transformer[stool]:.2f}")
        print("P(stool | outdoor bar), 4-gram:", f"{from_counts[stool]:.2f}")
        print("P(stool | outdoor bar), half and half:", f"{mixed[stool]:.2f}")
