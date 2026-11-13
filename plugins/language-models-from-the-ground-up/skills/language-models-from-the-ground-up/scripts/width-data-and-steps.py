import json
import math

from lib import transformer

runs = [("width 64, 4 epochs", "transformer-width-64"), ("width 128, 4 epochs", "transformer-width-128"),
        ("width 256, 4 epochs", "transformer-width-256"), ("width 128, 16 epochs", "transformer"),
        ("a quarter of the data, 4 epochs", "transformer-data-25"), ("half the data, 4 epochs", "transformer-data-50"),
        ("a quarter of the data, 16 epochs", "transformer-data-25-same-steps"),
        ("half the data, 8 epochs", "transformer-data-50-same-steps")]

for label, folder in runs:
    run = transformer.RECORDED.parent / folder
    manifest = json.loads((run / "manifest.json").read_text())
    curves = json.loads((run / "curves.json").read_text())["epochs"]
    best = min(curves, key=lambda curve: curve["validation_name_loss"] + curve["validation_description_loss"])
    print(f"{label}, parameters:", f"{manifest['parameters']:,}")
    print(f"{label}, steps:", f"{manifest['steps']:,}")
    print(f"{label}, best epoch:", best["epoch"])
    print(f"{label}, perplexity on names:", f"{math.exp(best['validation_name_loss']):.1f}")
    print(f"{label}, perplexity on descriptions:", f"{math.exp(best['validation_description_loss']):.1f}")
    print(f"{label}, perplexity on names, last epoch:", f"{math.exp(curves[-1]['validation_name_loss']):.1f}")
    print(f"{label}, perplexity on descriptions, last epoch:", f"{math.exp(curves[-1]['validation_description_loss']):.1f}")
