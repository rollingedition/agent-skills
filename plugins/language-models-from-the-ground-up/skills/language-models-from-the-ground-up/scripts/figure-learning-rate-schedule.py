"""Draws the step size for every step of the run, computed from the recorded settings, with the saved step sizes over it,
and the warm-up zoomed in below. The printed lines give the warm-up's share of the run, the step at which the step size
first reaches half its peak, the share of the run from there to the last step, and the largest gap from the saved sizes."""
from lib import transformer
from lib.figures import ACCENT, INK, MUTED, new_figure, save

import json

import numpy as np

_, _, manifest = transformer.load()
settings, total = manifest["settings"], manifest["steps"]
warmup, peak = settings["warmup_steps"], settings["peak_rate"]
saved = np.array(json.loads((transformer.RECORDED / "curves.json").read_text())["rates"])
saved_steps = np.arange(len(saved)) * 10 + 1      # saved[i] was written after step 10 * i: the size used at step 10 * i + 1

steps = np.arange(total)
progress = np.clip(steps - warmup, 0, None) / (total - warmup)
# the schedule of learning-rate-schedule.py, steps counted from 0, so step 0 is already a share of the peak
schedule = np.where(steps < warmup, peak * (steps + 1) / warmup,
                    peak * (0.1 + 0.9 * 0.5 * (1 + np.cos(np.pi * progress))))
half = warmup + int(np.argmax(schedule[warmup:] <= peak / 2))   # the decay starts above half the peak
assert np.all(schedule[half:] <= peak / 2)                       # and from there on, every step stays at or below it
assert np.allclose(np.diff(schedule[:warmup], 2), 0, rtol=0, atol=1e-12)   # the warm-up adds the same amount each step
assert np.all(np.diff(schedule[warmup:]) <= 0)                  # the decay never rises
gap = np.max(np.abs(saved - schedule[saved_steps]))
assert gap < 1e-9                                               # the tolerance learning-rate-schedule.py uses
print(f"share of the run spent warming up: {warmup / total:.1%}")
print(f"first step at or below half the peak: {half:,}")
print(f"share of the run from that step to the last: {(total - half) / total:.0%}")
print(f"largest gap from a saved step size: {gap:.1e}")
print("warm-up is a straight line: yes")
print("decay never rises: yes")

fig, (whole, zoom) = new_figure(rows=2, height=4.8, sharex=False)
# the whole run is drawn every tenth step and the zoom every step, which keeps the SVG under its size limit;
# the whole run draws the saved sizes as a dotted line, the zoom marks each one
panels = ((whole, total, 10, "the whole run", {"linestyle": ":"}),
          (zoom, 400, 1, "the warm-up, zoomed in", {"marker": "o", "linestyle": "none", "markersize": 2.5}))
for ax, last, every, title, style in panels:                  # the zoom stops at step 400, past the warm-up's end
    kept = saved_steps < last
    ax.plot(steps[:last:every], schedule[:last:every], color=ACCENT, label="schedule from the recorded settings")
    ax.plot(saved_steps[kept], saved[kept], color=INK, linewidth=1.2, label="saved step sizes, every 10th step", **style)
    ax.axvline(warmup, color=MUTED, linestyle=":", linewidth=1)
    ax.set(title=title, xlabel="training step, counted from 0", ylabel="step size", ylim=(0, None))
whole.axhline(peak / 2, color=MUTED, linestyle="--", linewidth=1)
whole.text(13500, peak * 0.55, "half the peak", color=MUTED)     # above the dashed line, where the curve is lower
zoom.annotate("end of the warm-up", xy=(warmup, peak), xytext=(warmup + 60, peak * 0.4), color=MUTED,
              arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8})
zoom.legend(loc="lower right")                  # the empty lower right, short labels so the warm-up line crosses no text
save(fig, "learning-rate-schedule")
