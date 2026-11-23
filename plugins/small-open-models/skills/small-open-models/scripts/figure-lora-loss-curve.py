"""Draw the loss at each of the recording's steps, with its moving mean, against the uniform guess over 77 teams.
The printed means of the short run's steps and of the last 100 steps, and the step from which the moving mean stays below the guess,
are the points the prose rests on."""

import json
import math
from pathlib import Path

import numpy as np

from lib.figures import ACCENT, INK, MUTED, new_figure, save

RECORDED = Path(__file__).resolve().parent / "data" / "recorded" / "lora-full"
WINDOW = 25  # steps in the moving mean; each point averages its step and the 24 before it
SHORT = 30  # steps the short run trained: the shaded span
manifest = json.loads((RECORDED / "manifest.json").read_text())
rows = [json.loads(line) for line in (RECORDED / "steps.jsonl").read_text().splitlines()]
steps = np.array([r["step"] for r in rows])
loss = np.array([r["loss"] for r in rows])
mean = np.convolve(loss, np.ones(WINDOW) / WINDOW, mode="valid")  # mean[k] covers steps k+1 to k+WINDOW
uniform = math.log(77)
ends = steps[WINDOW - 1:]  # the step each moving-mean point ends at, as plotted below
last_above = int(np.nonzero(mean >= uniform)[0][-1])  # the last window at or above the guess
assert (mean[last_above + 1:] < uniform).all()

print(f"steps in the recording: {len(loss)}")
print(f"window of the moving mean: {WINDOW} steps")
print(f"recording seed: {manifest['settings']['seed']}")
print(f"recording batch size: {manifest['settings']['batch_size']}")
print(f"steps in the short run: {SHORT}")
print(f"mean loss of the short run steps: {loss[:SHORT].mean():.2f}")
print(f"mean loss of the last 100 steps: {loss[-100:].mean():.2f}")
print(f"loss of a uniform guess over 77 teams: {uniform:.2f}")
print(f"moving mean last at or above the guess, ending at step: {ends[last_above]}")
print(f"moving mean below the guess from step on: {ends[last_above + 1]}")  # the next window, which ends one step later

fig, ax = new_figure(height=3.2)
ax.plot(steps, loss, color=MUTED, linewidth=0.5, label="loss at each step")
ax.plot(steps[WINDOW - 1:], mean, color=ACCENT, linewidth=1.8, label=f"mean of the last {WINDOW} steps")  # the first mean ends at step WINDOW
ax.axhline(uniform, color=INK, linestyle="--", linewidth=1.1, label="uniform guess over 77 teams, ln 77")
ax.axvspan(1, SHORT, color=MUTED, alpha=0.3, linewidth=0)
ax.axvline(SHORT, color=MUTED, linewidth=0.8)
ax.text(34, 8.5, f"the short run's {SHORT} steps", ha="left", color=INK)
ax.set_xlabel("training step")
ax.set_ylabel("loss, in nats")
ax.set_ylim(0, 9)
ax.legend(frameon=False, loc="upper right")
save(fig, "lora-loss-curve")
