import json
import math

curves = json.load(open("data/recorded/neural-lm/curves.json", encoding="utf-8"))
manifest = json.load(open("data/recorded/neural-lm/manifest.json", encoding="utf-8"))

print(f"{'epoch':>5}  {'training perplexity':>19}  {'validation perplexity':>21}")
for c in curves:
    print(f"{c['epoch']:>5}  {math.exp(c['train_loss']):>19.1f}  {math.exp(c['validation_loss']):>21.1f}")
best = min(curves, key=lambda c: c["validation_loss"])
print("epoch kept:", manifest["kept_epoch"])
print("validation perplexity at the kept epoch:", f"{math.exp(best['validation_loss']):.1f}")
print("validation perplexity at the last epoch:", f"{math.exp(curves[-1]['validation_loss']):.1f}")
