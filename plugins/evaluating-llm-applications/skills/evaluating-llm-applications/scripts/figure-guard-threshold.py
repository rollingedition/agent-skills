"""Draws the dev false refusal rate and false answer rate against the guard's threshold, with their sum dashed and the
rule's pick marked. The printed lines are the first threshold, the last threshold at the lowest sum, and that sum. The
asserts check that the pick is the rule's, that the sum is lowest up to its last tie and higher after, that a higher threshold
never lowers the false refusals or raises the false answers, and that both rates change across the sweep."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from fractions import Fraction

from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.guard import GRID, denominators, errors, pick_threshold, rows

dev = rows("dev")  # the same recording, items and grid as tune-guard-dev
answerable, unanswerable = denominators(dev)
refusal, answer, total = [], [], []
for threshold in GRID:
    refusals, answers = errors(dev, threshold)
    refusal.append(len(refusals) / answerable)
    answer.append(len(answers) / unanswerable)
    total.append(Fraction(len(refusals), answerable) + Fraction(len(answers), unanswerable))  # exact, so ties are real

chosen = pick_threshold(dev)
lowest = min(total)
last_tie = max(i for i, t in enumerate(total) if t == lowest)  # the last grid index at the lowest sum, read from the data
print(f"first threshold on the grid: {GRID[0]:.2f}")
print(f"last threshold at the lowest sum: {GRID[last_tie]:.2f}")
print(f"lowest sum of the two rates: {100 * float(lowest):.1f}%")

# The section's conclusion, that the rule's pick is no guard, rests on this: at 0.00 no score falls below the threshold.
assert chosen == 0.0, f"tune-guard-dev's recorded pick is 0.00, not {chosen:.2f}"
assert chosen == GRID[total.index(lowest)], "the pick is the lowest threshold with the smallest sum"
assert set(total[:last_tie + 1]) == {lowest} and min(total[last_tie + 1:]) > lowest, "the sum must be lowest up to the last tie and higher after"  # the slice includes the last tie
# Raising the threshold only adds declines: refusals never fall, answers never rise. The figure's trade rests on this.
assert all(a <= b for a, b in zip(refusal, refusal[1:])), "a higher threshold must not lower the false refusal rate"
assert all(a >= b for a, b in zip(answer, answer[1:])), "a higher threshold must not raise the false answer rate"
assert answer[-1] < answer[0] and refusal[-1] > refusal[0], "the sweep must trade one error for the other"

fig, ax = new_figure(height=3.0)
ax.plot(GRID, [100 * r for r in refusal], color=ACCENT, label="false refusal rate")
ax.plot(GRID, [100 * a for a in answer], color=INK, label="false answer rate")
ax.plot(GRID, [100 * float(t) for t in total], color=MUTED, linestyle="--", label="sum of the two rates")
ax.axvline(chosen, color=MUTED, linestyle=":", linewidth=1.0)  # the rule's pick, labelled beside the line
ax.text(chosen + 0.2, 3, f"rule's pick: {chosen:.2f}", color=MUTED)  # low on the plot, where no line runs
ax.set_xlim(-0.5, 10.5)
ax.set_ylim(0, 105)
ax.set_xlabel("guard threshold: a top score below it is declined")
ax.set_ylabel("rate on dev, in percent points")  # the dashed sum is two rates added, so it is in points too
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3)  # above the plot, where no line crosses it
save(fig, "guard-threshold")
