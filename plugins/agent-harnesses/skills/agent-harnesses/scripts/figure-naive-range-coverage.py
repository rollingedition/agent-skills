"""Draw how often the naive 95% range for 20 tasks covers the true proportion, for each proportion from 0.05 to 0.95.
The range is the one score-task-set prints, with its multiplier and its formula, taken from lib.tasks. Coverage is an
exact binomial sum over every count from 0 to 20, with no simulation. The lines name the coverage at the observed
proportion (the recorded task set's done count over its tasks), how many grid proportions have coverage under the 95%
label, the lowest coverage on the grid and the proportions where it falls, and the highest coverage and where it falls.
The two ends of the grid have the same coverage, which the code checks."""
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.models import load_recording
from lib.tasks import count_range

from math import comb

manifest, _ = load_recording("task-set")
n = len(manifest["tasks"])
observed = sum(1 for t in manifest["tasks"] if t["done"])
p_obs = observed / n


def covers(done: int, p: float) -> bool:
    """Whether the naive range for `done` of `n` covers the true proportion p, compared in counts as score-task-set does."""
    low, high = count_range(done, n)
    return low <= n * p <= high


def coverage(p: float) -> float:
    """The chance, under a binomial with n tasks at proportion p, that the naive range covers p."""
    return sum(comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1) if covers(k, p))


grid = [round(0.05 + 0.01 * i, 2) for i in range(91)]        # 0.05 to 0.95 in steps of 0.01
cover = [coverage(p) for p in grid]
cover_obs = coverage(p_obs)
assert abs(coverage(grid[0]) - coverage(grid[-1])) < 1e-9, "coverage is symmetric"
lows = " and ".join(f"{p:.2f}" for p, c in zip(grid, cover) if abs(c - min(cover)) < 1e-9)  # every tie for the lowest
high_cov, high_p = max(zip(cover, grid))

fig, ax = new_figure(height=2.8)
ax.plot(grid, cover, color=ACCENT, marker="o", markersize=2.5, label=f"naive 95% range, {n} tasks")
ax.axhline(0.95, color=INK, linestyle="--", linewidth=1.2, label="the 95% label")
ax.plot([p_obs], [cover_obs], color=INK, marker="s", markersize=6, linestyle="none",
        label=f"observed proportion, {observed} of {n} done")
ax.set_xlabel("true proportion of tasks done")
ax.set_ylabel("how often the range covers it")
ax.set_ylim(0, 1)
ax.legend(loc="lower center", ncol=1)

print(f"tasks: {n}")
print(f"grid: {grid[0]:.2f} to {grid[-1]:.2f} in steps of 0.01")
print(f"observed proportion: {p_obs:.2f}")
print(f"coverage at the observed proportion: {cover_obs:.1%}")
print(f"proportions on the grid under the 95% label: {sum(1 for c in cover if c < 0.95)} of {len(grid)}")
print(f"lowest coverage on the grid: {min(cover):.1%}")
print(f"proportions with the lowest coverage: {lows}")
print(f"highest coverage on the grid: {high_cov:.1%}")
print(f"proportion with the highest coverage: {high_p:.2f}")
save(fig, "naive-range-coverage")
