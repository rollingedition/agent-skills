"""Reads eight recorded runs and prints each one's parameters, steps, best epoch, and validation perplexities at its best
and last epochs. The prose's point rests on the perplexity-on-names lines."""
import json
import math

from lib import transformer

runs = [("width 64, 4 epochs", "transformer-width-64"), ("width 128, 4 epochs", "transformer-width-128"),
        ("width 256, 4 epochs", "transformer-width-256"), ("width 128, 16 epochs", "transformer"),
        ("a quarter of the data, 4 epochs", "transformer-data-25"), ("half the data, 4 epochs", "transformer-data-50"),
        ("a quarter of the data, 16 epochs", "transformer-data-25-same-steps"),
        ("half the data, 8 epochs", "transformer-data-50-same-steps")]

for label, folder in runs:
    run = transformer.RECORDED.parent / folder   # every run sits in the folder beside the main run's
    manifest = json.loads((run / "manifest.json").read_text())
    curves = json.loads((run / "curves.json").read_text())["epochs"]
    best = min(curves, key=lambda curve: curve["validation_name_loss"] + curve["validation_description_loss"])   # the epoch the script kept
    print(f"{label}, parameters:", f"{manifest['parameters']:,}")
    print(f"{label}, steps:", f"{manifest['steps']:,}")
    print(f"{label}, best epoch:", best["epoch"])
    print(f"{label}, perplexity on names:", f"{math.exp(best['validation_name_loss']):.1f}")
    print(f"{label}, perplexity on descriptions:", f"{math.exp(best['validation_description_loss']):.1f}")
    print(f"{label}, perplexity on names, last epoch:", f"{math.exp(curves[-1]['validation_name_loss']):.1f}")   # the last epoch trained, not the one kept
    print(f"{label}, perplexity on descriptions, last epoch:", f"{math.exp(curves[-1]['validation_description_loss']):.1f}")
