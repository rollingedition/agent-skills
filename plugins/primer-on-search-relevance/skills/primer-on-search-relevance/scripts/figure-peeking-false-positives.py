"""Draws the share of simulated A/A tests declared significant on some day so far, checked after each of 14 days, against the planned 0.05. The prose rests on the 'significant at the planned end' and 'significant on some day, checked daily' lines, which are the same lines aa-tests-with-peeking prints."""
from lib.figures import ACCENT, MUTED, new_figure, save

import numpy as np
from scipy import stats

# the same assumptions and seed as aa-tests-with-peeking, so the same simulated tests
TESTS, DAYS, SHOPPERS_PER_DAY, CONVERSION = 2000, 14, 2000, 0.05
rng = np.random.default_rng(2026)
buyers = rng.binomial(SHOPPERS_PER_DAY, CONVERSION, size=(TESTS, DAYS, 2)).cumsum(axis=1)   # running totals
shoppers = SHOPPERS_PER_DAY * np.arange(1, DAYS + 1)[None, :]
rate_a, rate_b = buyers[..., 0] / shoppers, buyers[..., 1] / shoppers
pooled = (rate_a + rate_b) / 2
z = (rate_b - rate_a) / np.sqrt(pooled * (1 - pooled) * 2 / shoppers)
p_value = 2 * stats.norm.sf(np.abs(z))

# a test counts once it has been significant on any day up to the day shown
seen_so_far = np.logical_or.accumulate(p_value < 0.05, axis=1)
share_so_far = seen_so_far.mean(axis=0)                  # one share per day
days = np.arange(1, DAYS + 1)

print(f"significant at the planned end: {(p_value[:, -1] < 0.05).mean():.3f}")
print(f"significant on some day, checked daily: {share_so_far[-1]:.3f}")

fig, ax = new_figure(height=2.8)
ax.plot(days, share_so_far, color=ACCENT, marker="o", markersize=3.5, label="significant on some day so far, checked daily")
ax.axhline(0.05, color=MUTED, linestyle="--", label="planned 0.05")
ax.set_xticks(days)
ax.set_xlabel("day of the test, checked after each day (day 14 is the planned end)")
ax.set_ylabel("share significant")
ax.set_ylim(0, 0.3)
ax.legend(loc="upper left", frameon=False)
save(fig, "peeking-false-positives")
