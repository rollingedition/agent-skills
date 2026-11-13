"""The training script's record of training and validation perplexity after each epoch, and the epoch whose weights were
kept. The prose's point rests on the validation column, and on the two validation figures printed after the table."""
import json
import math

curves = json.load(open("data/recorded/neural-lm/curves.json", encoding="utf-8"))
manifest = json.load(open("data/recorded/neural-lm/manifest.json", encoding="utf-8"))

print(f"{'epoch':>5}  {'training perplexity':>19}  {'validation perplexity':>21}")
for c in curves:                                             # losses are averages of log probabilities: exp turns them into perplexities
    print(f"{c['epoch']:>5}  {math.exp(c['train_loss']):>19.1f}  {math.exp(c['validation_loss']):>21.1f}")
best = min(curves, key=lambda c: c["validation_loss"])       # the epoch with the lowest validation loss, which the kept epoch should match
print("epoch kept:", manifest["kept_epoch"])
print("validation perplexity at the kept epoch:", f"{math.exp(best['validation_loss']):.1f}")
print("validation perplexity at the last epoch:", f"{math.exp(curves[-1]['validation_loss']):.1f}")   # curves[-1]: the final epoch's record, whatever was kept
