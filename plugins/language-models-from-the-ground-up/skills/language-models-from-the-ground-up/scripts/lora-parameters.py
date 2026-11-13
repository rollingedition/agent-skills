from lib import open_model

config = open_model.config("SmolLM2-360M")
width, layers = config["hidden_size"], config["num_hidden_layers"]
key_value_width = config["num_key_value_heads"] * width // config["num_attention_heads"]
total = open_model.parameters(config)["total"]
for rank in [8, 64]:
    # LoRA adds two small matrices beside each adapted weight: width x rank, then rank x output width.
    added = layers * (rank * (width + width) + rank * (width + key_value_width))       # on the query and value weights
    print(f"rank {rank}, parameters trained:", f"{added:,}")
    print(f"rank {rank}, share of the model's parameters:", f"{added / total:.2%}")
print("parameters trained by full fine-tuning:", f"{total:,}")
