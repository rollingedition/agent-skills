"""Counts the store's model's parameters by part from its saved weights, and prints its settings. The prose's point
rests on the total, the feed-forward count and the embedding's share of it."""
from lib import transformer

weights, vocabulary, manifest = transformer.load()
settings = manifest["settings"]
# one table serves as input and output, so the embedding is counted once; a weight's group is the last part of its name
groups = {"embedding (shared with the output)": ["embedding"], "attention": ["q", "k", "v", "o"],
          "feed-forward": ["gate", "up", "down"], "normalization": ["norm1", "norm2", "final_norm"]}
for group, parts in groups.items():
    count = sum(v.size for k, v in weights.items() if k.split(".")[-1] in parts)   # a weight's name ends in its part: layer3.q is attention's q
    print(f"{group}:", f"{count:,}")
print("total:", f"{sum(v.size for v in weights.values()):,}")
print("embedding's share of the total:", f"{weights['embedding'].size / sum(v.size for v in weights.values()):.0%}")
print("layers:", settings["layers"])
print("width:", settings["dimensions"])                  # the width of the residual stream, which the manifest calls dimensions
print("heads:", settings["heads"])
print("feed-forward width:", settings["feed_forward"])
print("longest text, in tokens:", settings["longest"])  # longer texts were cut to this many tokens
print("vocabulary:", f"{len(vocabulary):,}")             # the store tokenizer's tokens, plus the four markers
