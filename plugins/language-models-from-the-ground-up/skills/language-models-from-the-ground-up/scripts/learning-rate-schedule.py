import json
import math

from lib import transformer

_, _, manifest = transformer.load()
settings, total = manifest["settings"], manifest["steps"]
recorded_rates = json.loads((transformer.RECORDED / "curves.json").read_text())["rates"]   # every 10th step's


def rate(step):
    """Warm up linearly to the peak, then follow half a cosine down to a tenth of it."""
    if step < settings["warmup_steps"]:
        return settings["peak_rate"] * (step + 1) / settings["warmup_steps"]
    progress = (step - settings["warmup_steps"]) / (total - settings["warmup_steps"])
    return settings["peak_rate"] * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * progress)))


print("warm-up steps:", settings["warmup_steps"])
print("peak step size:", settings["peak_rate"])
print("weight decay:", settings["weight_decay"])
for step in [0, settings["warmup_steps"] // 2, settings["warmup_steps"], total // 2, total - 1]:
    print(f"step size at step {step:,}:", f"{rate(step):.2e}")
gap = max(abs(recorded - rate(10 * i + 1)) for i, recorded in enumerate(recorded_rates))   # saved after each step
print("same as the recorded step sizes:", gap < 1e-9)
