"""Counts what LoRA would train on SmolLM2-360M, adapting the query and value weights of every layer at two ranks, and
what full fine-tuning trains. The prose's point rests on the rank 8 lines and the full fine-tuning count.
"""
from lib import open_model

config = open_model.config("SmolLM2-360M")
width, layers = config["hidden_size"], config["num_hidden_layers"]
# keys and values share heads, so their width is the query width scaled by the ratio of key-value heads to heads
key_value_width = config["num_key_value_heads"] * width // config["num_attention_heads"]
# every parameter of the model: the full fine-tuning count, and the denominator of each share
total = open_model.parameters(config)["total"]
for rank in [8, 64]:
    # LoRA adds two small matrices beside each adapted weight: width x rank, then rank x output width.
    added = layers * (rank * (width + width) + rank * (width + key_value_width))       # on the query and value weights
    print(f"rank {rank}, parameters trained:", f"{added:,}")
    print(f"rank {rank}, share of the model's parameters:", f"{added / total:.2%}")
print("parameters trained by full fine-tuning:", f"{total:,}")
