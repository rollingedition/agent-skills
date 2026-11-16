"""Load the 135M and 360M SmolLM2 models at their pins, offline, and print each one's parameter count and layer count. The chapter's size claims rest on both lines; the parameter line is rounded to whole millions."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

# Seeds, deterministic algorithms and float32, set before either model loads.
router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"
MEDIUM = "HuggingFaceTB/SmolLM2-360M-Instruct"


def size(model):
    """Return (parameter count in millions, rounded to a whole number) and the layer count."""
    # parameters() yields a shared tensor once, so the tied embedding and output head count once.
    total = sum(p.numel() for p in model.parameters())
    return round(total / 1e6), model.config.num_hidden_layers


# load_model returns (tokenizer, model). This example needs only the models.
_, small = router_lib.load_model(SMALL)
_, medium = router_lib.load_model(MEDIUM)

small_millions, small_layers = size(small)
medium_millions, medium_layers = size(medium)

print(f"parameters, millions, rounded: {small_millions} and {medium_millions}")
print(f"layers: {small_layers} and {medium_layers}")
