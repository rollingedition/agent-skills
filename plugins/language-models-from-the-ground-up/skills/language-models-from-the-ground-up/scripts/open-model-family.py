import math

from lib import open_model

for name in open_model.SIZES:
    config = open_model.config(name)
    parts = open_model.parameters(config)
    print(f"{name}, layers:", config["num_hidden_layers"])
    print(f"{name}, width:", f"{config['hidden_size']:,}")
    print(f"{name}, query heads:", config["num_attention_heads"])
    print(f"{name}, query heads per key and value head:", config["num_attention_heads"] // config["num_key_value_heads"])
    print(f"{name}, feed-forward width:", f"{config['intermediate_size']:,}")
    print(f"{name}, RoPE base:", f"{config['rope_theta']:,}")
    print(f"{name}, parameters:", f"{parts['total']:,}")
    print(f"{name}, embedding's share:", f"{parts['embedding'] / parts['total']:.0%}")
recorded = sum(math.prod(shape) for key, shape in open_model.read("parameters").items() if key != "lm_head.weight")
print("SmolLM2-360M, parameters in the recorded weights:", f"{recorded:,}")
