"""Count the backbone Linear layers the int8 copy quantizes, and the weight bytes they store.
Bytes come from shapes: float32 is 4 bytes a weight; int8 is 1 byte a weight plus one float32 scale (4 bytes) per output row.
Prints counts and one rate: no file sizes, no timings."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"

_, model = router_lib.int8_classifier(RECORDED / "adapter")
layers = router_lib.backbone_linears(model)
quantized = [layer for _, layer in layers if router_lib.is_int8(layer)]
weights = sum(layer.weight.numel() for _, layer in layers)
rows = sum(layer.weight.shape[0] for _, layer in layers)

print(f"backbone Linear layers: {len(layers)}")
print(f"backbone Linear layers quantized to int8: {len(quantized)}")
print(f"score head quantized: {router_lib.is_int8(model.score)}")
print(f"score head weight dtype: {model.score.weight.dtype}")
print(f"weights in backbone Linear layers: {weights}")
print(f"output rows in backbone Linear layers: {rows}")
float_bytes = 4 * weights
int8_bytes = 1 * weights + 4 * rows
print(f"weight bytes, int8 as a share of float32: {int8_bytes / float_bytes:.1%}")
