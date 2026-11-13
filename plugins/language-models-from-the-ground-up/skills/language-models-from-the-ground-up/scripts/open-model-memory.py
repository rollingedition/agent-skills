"""Works out each size's weights and key and value cache, with and without grouped keys and values, in decimal gigabytes
and kilobytes. The point that grouping cuts the 360M model's cache to a third rests on its two cache lines for the longest text."""
from lib import open_model

longest = open_model.config("SmolLM2-360M")["max_position_embeddings"]   # the longest text the models are set up for
print("longest text, in tokens:", f"{longest:,}")
for name in open_model.SIZES:
    config = open_model.config(name)
    head_size = config["hidden_size"] // config["num_attention_heads"]   # the width shared out over the query heads, grouped or not
    weights = open_model.parameters(config)["total"] * 2          # 16-bit numbers: 2 bytes each
    cache = config["num_hidden_layers"] * 2 * config["num_key_value_heads"] * head_size * 2   # a key and a value per layer, 2 bytes each
    # The same cache with every query head keeping its own key and value.
    ungrouped = config["num_hidden_layers"] * 2 * config["num_attention_heads"] * head_size * 2
    # Decimal units: a gigabyte is 1e9 bytes and a kilobyte 1e3 bytes.
    print(f"{name}, weights in 16-bit numbers, in GB:", f"{weights / 1e9:.1f}")
    print(f"{name}, key and value cache per token, in KB:", f"{cache / 1e3:.0f}")
    print(f"{name}, cache for the longest text, in GB:", f"{cache * longest / 1e9:.2f}")
    print(f"{name}, cache for the longest text without grouping, in GB:", f"{ungrouped * longest / 1e9:.2f}")
