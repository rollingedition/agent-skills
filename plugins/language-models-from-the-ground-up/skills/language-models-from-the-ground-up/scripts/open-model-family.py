"""Counts all three SmolLM2 sizes from their recorded configurations, part by part, and checks the 360M model's count
against its recorded weights. The claim that the counts match the weights rests on the 360M parameters line and the last line."""
import math

from lib import open_model

for name in open_model.SIZES:
    config = open_model.config(name)
    parts = open_model.parameters(config)           # the count by part, from the configuration alone, grouped keys and values included
    print(f"{name}, layers:", config["num_hidden_layers"])
    print(f"{name}, width:", f"{config['hidden_size']:,}")
    print(f"{name}, query heads:", config["num_attention_heads"])
    print(f"{name}, query heads per key and value head:", config["num_attention_heads"] // config["num_key_value_heads"])   # query heads sharing each key and value head
    print(f"{name}, feed-forward width:", f"{config['intermediate_size']:,}")
    print(f"{name}, RoPE base:", f"{config['rope_theta']:,}")      # the rotary base: a larger base makes positions turn more slowly
    print(f"{name}, parameters:", f"{parts['total']:,}")
    print(f"{name}, embedding's share:", f"{parts['embedding'] / parts['total']:.0%}")
# The output layer is tied to the embeddings, so its weights are skipped: the shared weights are counted once.
recorded = sum(math.prod(shape) for key, shape in open_model.read("parameters").items() if key != "lm_head.weight")
print("SmolLM2-360M, parameters in the recorded weights:", f"{recorded:,}")
