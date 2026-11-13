"""Computes the warm-up and cosine schedule by hand from the recorded settings, and checks it against the step sizes
the training script saved. The prose relies on the check: the assert fails the run if the two ever differ."""
import json
import math

from lib import transformer

_, _, manifest = transformer.load()
settings, total = manifest["settings"], manifest["steps"]
recorded_rates = json.loads((transformer.RECORDED / "curves.json").read_text())["rates"]   # every 10th step's, after the scheduler's step


def rate(step):
    """Warm up linearly to the peak, then follow half a cosine down to a tenth of it."""
    if step < settings["warmup_steps"]:
        return settings["peak_rate"] * (step + 1) / settings["warmup_steps"]   # steps count from 0, so step 0 is already a share of the peak
    progress = (step - settings["warmup_steps"]) / (total - settings["warmup_steps"])   # 0 at the warm-up's end, 1 at the last step
    return settings["peak_rate"] * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * progress)))


print("warm-up steps:", settings["warmup_steps"])
print("peak step size:", settings["peak_rate"])
print("weight decay:", settings["weight_decay"])
for step in [0, settings["warmup_steps"] // 2, settings["warmup_steps"], total // 2, total - 1]:
    print(f"step size at step {step:,}:", f"{rate(step):.2e}")
gap = max(abs(recorded - rate(10 * i + 1)) for i, recorded in enumerate(recorded_rates))   # recorded_rates[i] was saved after step 10 * i, so it is the size used at step 10 * i + 1
assert gap < 1e-9                   # every saved step size matches the hand calculation, to a billionth
print("same as the recorded step sizes:", "yes")
