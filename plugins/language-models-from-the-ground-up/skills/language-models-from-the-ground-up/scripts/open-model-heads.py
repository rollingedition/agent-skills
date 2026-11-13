"""Reads SmolLM2's recorded head averages over the recorded texts, and compares them with an even spread averaged the same way.
The point that a few heads specialize and many put their weight on the first token rests on the head counts and the first-token averages."""
import numpy as np
from tokenizers import Tokenizer

from lib import open_model, transformer
from lib.products import product_texts
from lib.store import load_products

heads = open_model.read("heads")
previous, first = np.array(heads["previous"]), np.array(heads["first"])   # (layers, heads)
print("texts averaged:", heads["texts"])
print("heads in all:", previous.size)
print("heads with more than half their weight on the previous token:", int((previous > 0.5).sum()))   # a position's weights sum to 1, so above 0.5 is most of it
print("the most weight a head puts on the previous token:", f"{previous.max():.2f}")
print("average weight on the first token, layers 1 to 4:", f"{first[:4].mean():.2f}")     # rows count layers from 0: rows 0 to 3
print("average weight on the first token, layers 5 to 32:", f"{first[4:].mean():.2f}")    # rows from 4 on are layers 5 to 32
print("heads with more than half their weight on the first token:", int((first > 0.5).sum()))

# An even spread, averaged the same way: each position i shares its weight equally among the i + 1 tokens it sees.
smollm2 = Tokenizer.from_file("data/smollm2-tokenizer/tokenizer.json")
end = transformer.load()[1].index(transformer.END)      # [1] is the vocabulary: load() returns weights, vocabulary, manifest
rows = load_products("validation").head(500)            # the first 500 validation products, the ones product_texts reads
# The same products as product_texts, with their names and descriptions, filtered the same way. Each text is a name, a newline
# and a description, as the recording wrote it.
texts = [f"{name}\n{description}\n" for (ids, sep), name, description in
         zip(product_texts("validation", 500), rows["name"], rows["description"]) if ids[-1] == end and sep < len(ids) - 2]
# Only the texts the recording averaged. The +1 is the start token the recording put before every text.
lengths = [len(smollm2.encode(text, add_special_tokens=False).ids) + 1 for text in texts[:heads["texts"]]]
# A position with k tokens to see gives an even spread 1 / k on each of them. k runs from 2 to the text's length.
print("an even spread's weight on the previous token, and on the first:",
      f"{np.mean([np.mean(1 / np.arange(2, n + 1)) for n in lengths]):.2f}")
