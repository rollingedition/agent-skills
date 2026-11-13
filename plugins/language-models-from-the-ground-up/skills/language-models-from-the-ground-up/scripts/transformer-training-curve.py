"""Prints the recorded run's perplexity for each epoch, then the epoch kept and its validation perplexities.
The prose's point rests on the two validation columns and the epoch kept."""
import json
import math

from lib import transformer

_, _, manifest = transformer.load()
curves = json.loads((transformer.RECORDED / "curves.json").read_text())["epochs"]

print("perplexity per token; training mixes names and descriptions, as the training text does")
print("epoch  training  validation names  validation descriptions")
for curve in curves:
    print(f"{curve['epoch']:>5}  {math.exp(curve['train_loss']):>8.1f}  {math.exp(curve['validation_name_loss']):>16.1f}"
          f"  {math.exp(curve['validation_description_loss']):>23.1f}")
kept = next(curve for curve in curves if curve["epoch"] == manifest["kept_epoch"])   # the epoch whose weights were kept
print("epoch kept, the lowest name and description losses added together:", manifest["kept_epoch"])
print("validation perplexity on names, kept epoch:", f"{math.exp(kept['validation_name_loss']):.1f}")
print("validation perplexity on descriptions, kept epoch:", f"{math.exp(kept['validation_description_loss']):.1f}")
print("validation perplexity on names, epoch 4:", f"{math.exp(curves[3]['validation_name_loss']):.1f}")   # the list starts at epoch 1, so index 3 is epoch 4
