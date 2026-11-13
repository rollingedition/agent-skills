"""Scores the store's model and SmolLM2-360M on the same names and the same descriptions, per word, the unit the two share.
The point that the small model wins on both kinds of text rests on the per-word lines for names and for descriptions."""
import math

from lib import bpe, open_model, transformer
from lib.products import product_texts
from lib.store import load_products

_, vocabulary, _ = transformer.load()           # load() returns the weights, the vocabulary and the manifest; only the vocabulary is used
index = {token: i for i, token in enumerate(vocabulary)}
scores, tokenizer = open_model.read("scores"), bpe.store_tokenizer()
per = lambda log_p, count: f"{math.exp(-log_p / count):,.1f}"    # perplexity: e to the average negative log-probability per count

# Names: each name's tokens and its end (<sep> for the store's model, a newline for SmolLM2), from the start token.
names = list(load_products("validation")["name"])[:len(scores["names"])]     # as many names as SmolLM2 was scored on, from the top of the split
# The start marker, the name's tokens and <sep>: the model scores everything after the start marker.
encoded = [[index[transformer.START]] + [index[t] for t in tokenizer.encode(name)] + [index[transformer.SEP]] for name in names]
store = sum(transformer.total_log_probability(ids, 1) for ids in encoded)     # scores ids[1:], every token after <s>
smollm2 = sum(row["log_p"] for row in scores["names"])
# Words are whitespace-separated, as the recording counted them; both models are divided by the same count.
words = sum(row["words"] for row in scores["names"])
print("validation names scored:", len(names))
print("names, per-token perplexity, the store's model:", per(store, sum(len(ids) - 1 for ids in encoded)))   # all but <s>
print("names, per-token perplexity, SmolLM2-360M:", per(smollm2, sum(row["tokens"] for row in scores["names"])))   # SmolLM2's own count
print("names, per-word perplexity, the store's model:", per(store, words))
print("names, per-word perplexity, SmolLM2-360M:", per(smollm2, words))
# The label is context for the recording and is not scored; the same words count.
print("names after a label, per-word perplexity, SmolLM2-360M:", per(sum(r["log_p"] for r in scores["labelled names"]), words))

# Descriptions: chapter 8's products, each description's tokens and its end, given the name.
end = index[transformer.END]                    # the end marker closes a description
# The first 500 validation products. Keeps those whose text ends rather than being cut at the length limit, and that have
# at least one description token after <sep>. Scores from sep + 1: the description and its end, given everything up to <sep>.
store = sum(transformer.total_log_probability(ids, sep + 1) for ids, sep in product_texts("validation", 500)
            if ids[-1] == end and sep < len(ids) - 2)
words = sum(row["words"] for row in scores["descriptions"])
print("descriptions scored:", len(scores["descriptions"]))
print("descriptions, per-word perplexity, the store's model:", per(store, words))
print("descriptions, per-word perplexity, SmolLM2-360M:", per(sum(r["log_p"] for r in scores["descriptions"]), words))
