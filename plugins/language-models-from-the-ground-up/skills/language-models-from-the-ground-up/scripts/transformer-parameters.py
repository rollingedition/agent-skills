from lib import transformer

weights, vocabulary, manifest = transformer.load()
settings = manifest["settings"]
groups = {"embedding (shared with the output)": ["embedding"], "attention": ["q", "k", "v", "o"],
          "feed-forward": ["gate", "up", "down"], "normalization": ["norm1", "norm2", "final_norm"]}
for group, parts in groups.items():
    count = sum(v.size for k, v in weights.items() if k.split(".")[-1] in parts)
    print(f"{group}:", f"{count:,}")
print("total:", f"{sum(v.size for v in weights.values()):,}")
print("embedding's share of the total:", f"{weights['embedding'].size / sum(v.size for v in weights.values()):.0%}")
print("layers:", settings["layers"])
print("width:", settings["dimensions"])
print("heads:", settings["heads"])
print("feed-forward width:", settings["feed_forward"])
print("longest text, in tokens:", settings["longest"])
print("vocabulary:", f"{len(vocabulary):,}")
