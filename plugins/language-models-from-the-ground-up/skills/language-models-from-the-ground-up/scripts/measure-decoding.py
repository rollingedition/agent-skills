import numpy as np

from lib import decoding
from lib.products import product_texts

longest, sample, seed = 60, 20, 2026
described = [(ids, sep) for ids, sep in product_texts("validation") if sep < len(ids) - 2]
products = [described[i] for i in np.random.default_rng(seed).choice(len(described), sample, replace=False)]
print("products, drawn at random from the validation products with a description:", sample)
print("longest description, in tokens:", longest)


settings = [("real descriptions", None), ("greedy", {}), ("greedy, repetition penalty 1.3", {"penalty": 1.3}),
            ("sampling, temperature 1.0", {"sample": True}), ("sampling, temperature 0.7", {"sample": True, "temperature": 0.7}),
            ("top-k 20", {"sample": True, "top_k": 20}), ("top-p 0.9", {"sample": True, "top_p": 0.9})]
for label, chosen in settings:
    rows = []
    for number, (ids, sep) in enumerate(products):
        start = ids[:sep + 1]
        if chosen is None:
            written = ids[sep + 1:][:longest]
        else:
            options = {option: value for option, value in chosen.items() if option != "sample"}
            rng = np.random.default_rng(seed + number) if chosen.get("sample") else None
            written = decoding.generate(start, rng=rng, longest=longest, **options)
        rows.append(decoding.measures(start, written))
    repeated, log_p, ended, uses_name, length = zip(*rows)
    print(f"{label}, repeated 4-token phrases:", f"{np.mean(repeated):.0%}")
    print(f"{label}, the model's perplexity of the text:", f"{np.exp(-np.concatenate(log_p).mean()):.1f}")
    print(f"{label}, ended within {longest} tokens:", f"{np.mean(ended):.0%}")
    print(f"{label}, uses a whole word of the name:", f"{np.mean(uses_name):.0%}")
    print(f"{label}, average length in tokens:", f"{np.mean(length):.0f}")
