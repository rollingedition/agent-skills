import math

from lib import bpe, open_model, transformer
from lib.products import product_texts
from lib.store import load_products

_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
scores, tokenizer = open_model.read("scores"), bpe.store_tokenizer()
per = lambda log_p, count: f"{math.exp(-log_p / count):,.1f}"

# Names: each name's tokens and its end (<sep> for the store's model, a newline for SmolLM2), from the start token.
names = list(load_products("validation")["name"])[:len(scores["names"])]
encoded = [[index[transformer.START]] + [index[t] for t in tokenizer.encode(name)] + [index[transformer.SEP]] for name in names]
store = sum(transformer.total_log_probability(ids, 1) for ids in encoded)
smollm2 = sum(row["log_p"] for row in scores["names"])
words = sum(row["words"] for row in scores["names"])
print("validation names scored:", len(names))
print("names, per-token perplexity, the store's model:", per(store, sum(len(ids) - 1 for ids in encoded)))
print("names, per-token perplexity, SmolLM2-360M:", per(smollm2, sum(row["tokens"] for row in scores["names"])))
print("names, per-word perplexity, the store's model:", per(store, words))
print("names, per-word perplexity, SmolLM2-360M:", per(smollm2, words))
print("names after a label, per-word perplexity, SmolLM2-360M:", per(sum(r["log_p"] for r in scores["labelled names"]), words))

# Descriptions: chapter 8's products, each description's tokens and its end, given the name.
end = index[transformer.END]
store = sum(transformer.total_log_probability(ids, sep + 1) for ids, sep in product_texts("validation", 500)
            if ids[-1] == end and sep < len(ids) - 2)
words = sum(row["words"] for row in scores["descriptions"])
print("descriptions scored:", len(scores["descriptions"]))
print("descriptions, per-word perplexity, the store's model:", per(store, words))
print("descriptions, per-word perplexity, SmolLM2-360M:", per(sum(r["log_p"] for r in scores["descriptions"]), words))
