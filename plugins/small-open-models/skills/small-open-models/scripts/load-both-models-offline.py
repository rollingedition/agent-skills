"""Load the 135M and 360M SmolLM2 models at their pins, offline, and print their size counts."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"
MEDIUM = "HuggingFaceTB/SmolLM2-360M-Instruct"


def size(model):
    """Return (parameter count in millions, rounded to a whole number) and the layer count."""
    total = sum(p.numel() for p in model.parameters())
    return round(total / 1e6), model.config.num_hidden_layers


_, small = router_lib.load_model(SMALL)
_, medium = router_lib.load_model(MEDIUM)

small_millions, small_layers = size(small)
medium_millions, medium_layers = size(medium)

print(f"parameters, millions, rounded: {small_millions} and {medium_millions}")
print(f"layers: {small_layers} and {medium_layers}")
