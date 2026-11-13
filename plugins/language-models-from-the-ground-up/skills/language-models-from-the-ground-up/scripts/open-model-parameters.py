import math

from lib import open_model

shapes = {name: shape for name, shape in open_model.read("parameters").items()
          if name != "lm_head.weight"}       # the output layer is tied to the embeddings: the same weights, counted once
parts = {"embedding (shared with the output)": ["embed_tokens"], "attention": ["q_proj", "k_proj", "v_proj", "o_proj"],
         "feed-forward": ["gate_proj", "up_proj", "down_proj"], "normalization": ["layernorm", "model.norm"]}
total = sum(math.prod(shape) for shape in shapes.values())
for part, keys in parts.items():
    count = sum(math.prod(shape) for name, shape in shapes.items() if any(key in name for key in keys))
    print(f"{part}:", f"{count:,}", f"({count / total:.0%})")
print("total:", f"{total:,}")
config = open_model.read("manifest")["config"]
print("layers:", config["num_hidden_layers"])
print("width:", config["hidden_size"])
print("query heads:", config["num_attention_heads"])
print("key and value heads:", config["num_key_value_heads"])
print("feed-forward width:", config["intermediate_size"])
print("vocabulary:", f"{config['vocab_size']:,}")
print("one layer's query weights:", shapes["model.layers.0.self_attn.q_proj.weight"])
print("one layer's key weights:", shapes["model.layers.0.self_attn.k_proj.weight"])
