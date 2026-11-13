from lib import open_model

longest = open_model.config("SmolLM2-360M")["max_position_embeddings"]   # the longest text the models are set up for
print("longest text, in tokens:", f"{longest:,}")
for name in open_model.SIZES:
    config = open_model.config(name)
    head_size = config["hidden_size"] // config["num_attention_heads"]
    weights = open_model.parameters(config)["total"] * 2          # 16-bit numbers: 2 bytes each
    cache = config["num_hidden_layers"] * 2 * config["num_key_value_heads"] * head_size * 2   # a key and a value per layer
    ungrouped = config["num_hidden_layers"] * 2 * config["num_attention_heads"] * head_size * 2
    print(f"{name}, weights in 16-bit numbers, in GB:", f"{weights / 1e9:.1f}")
    print(f"{name}, key and value cache per token, in KB:", f"{cache / 1e3:.0f}")
    print(f"{name}, cache for the longest text, in GB:", f"{cache * longest / 1e9:.2f}")
    print(f"{name}, cache for the longest text without grouping, in GB:", f"{ungrouped * longest / 1e9:.2f}")
