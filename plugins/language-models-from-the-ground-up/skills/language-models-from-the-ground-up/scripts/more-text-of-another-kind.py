import json
import math

from lib import neural
from lib.names import name_tokens

validation = name_tokens("validation")
for name in ["neural-lm", "neural-lm-all-text"]:
    manifest = json.load(open(f"data/recorded/{name}/manifest.json", encoding="utf-8"))
    print(f"learned from {manifest['settings']['text']}:", f"{neural.perplexity(validation, name):.1f}")

from lib import bpe
from lib.store import load_products

tokenizer = bpe.store_tokenizer()
names_tokens = sum(len(t) for t in name_tokens("train"))
description_tokens = sum(len(tokenizer.encode(d)) for d in load_products("train")["description"])
print("training tokens, names:", f"{names_tokens:,}")
print("training tokens, names and descriptions:", f"{names_tokens + description_tokens:,}")
curve = json.load(open("data/recorded/neural-lm-all-text/curves.json", encoding="utf-8"))
print("all-text model, validation perplexity by epoch:", ", ".join(f"{math.exp(c['validation_loss']):.1f}" for c in curve))
