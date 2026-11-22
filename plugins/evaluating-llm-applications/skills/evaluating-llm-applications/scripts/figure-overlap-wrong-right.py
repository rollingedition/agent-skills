"""Draws each pair's wrong answer and right answer by ROUGE-1 F1, one row per pair.

The printed counts show the wrong answer scoring higher in every pair, and the smallest gap is the number the prose rests
on. The pairs and the two functions are copied from overlap-misleads, so this example stands on its own."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import json
import re
from collections import Counter
from pathlib import Path

from lib.figures import ACCENT, INK, MUTED, new_figure, save

PAIRS = json.loads((Path(__file__).resolve().parent / "data" / "overlap-pairs.json").read_text(encoding="utf-8"))


def words(text: str) -> list[str]:
    """Lowercase runs of letters and digits: `--apply` is the word apply, and `lock.json` is two words."""
    return re.findall(r"[a-z0-9]+", text.lower())


def rouge_1_f1(candidate: str, reference: str) -> float:
    """ROUGE-1 F1: shared words, counted with repeats up to the smaller count, over both lengths."""
    cand, ref = words(candidate), words(reference)
    overlap = sum((Counter(cand) & Counter(ref)).values())
    if overlap == 0:
        return 0.0
    precision, recall = overlap / len(cand), overlap / len(ref)
    return 2 * precision * recall / (precision + recall)


wrong = [rouge_1_f1(p["wrong"], p["reference"]) for p in PAIRS]
right = [rouge_1_f1(p["right"], p["reference"]) for p in PAIRS]
gaps = [w - r for w, r in zip(wrong, right)]  # the gap is wrong minus right, pair by pair
rows = range(len(PAIRS), 0, -1)  # pair 1 on the top row

fig, ax = new_figure(height=2.4)
ax.hlines(rows, right, wrong, color=MUTED, linewidth=1)  # the grey line joins each pair's two markers
ax.scatter(wrong, rows, color=ACCENT, marker="o", s=36, label="wrong answer")
ax.scatter(right, rows, color=INK, marker="D", s=24, label="right answer")
ax.set(xlim=(0, 1), xlabel="ROUGE-1 F1, 0 to 1",
       yticks=rows, yticklabels=[f"pair {i}" for i in range(1, len(PAIRS) + 1)])
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2)  # above the plot, where no marker crosses it

higher = sum(g > 0 for g in gaps)  # a gap above zero means the wrong answer scored higher
assert higher == len(PAIRS), f"higher in only {higher} pairs"
print(f"pairs: {len(PAIRS)}")
print(f"pairs where the wrong answer has the higher ROUGE-1 F1: {higher} of {len(PAIRS)}")
print(f"smallest wrong-minus-right gap, ROUGE-1 F1: {min(gaps):.3f}")
save(fig, "overlap-wrong-right")
