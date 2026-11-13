"""Simulates A/A tests, where both groups get the same search, read at the planned end and every day, and checks one split for a mismatch. The prose's point rests on the 'significant at the planned end' and 'significant on some day' lines, and on the sample ratio mismatch line."""
import numpy as np
from scipy import stats

# Assumptions for the simulation, not the store's data: 2,000 shoppers a day in each group,
# 5% of them buy, and the test is planned to run 14 days. Both groups get the same search (an A/A test).
TESTS, DAYS, SHOPPERS_PER_DAY, CONVERSION = 2000, 14, 2000, 0.05

# a fixed seed, so the simulated tests are the same on every run
rng = np.random.default_rng(2026)
buyers = rng.binomial(SHOPPERS_PER_DAY, CONVERSION, size=(TESTS, DAYS, 2)).cumsum(axis=1)   # running totals
shoppers = SHOPPERS_PER_DAY * np.arange(1, DAYS + 1)[None, :]                               # per group, by day
rate_a, rate_b = buyers[..., 0] / shoppers, buyers[..., 1] / shoppers
pooled = (rate_a + rate_b) / 2
# two-proportion z for each day, using the pooled rate of the two groups
z = (rate_b - rate_a) / np.sqrt(pooled * (1 - pooled) * 2 / shoppers)
# two-sided: a gap in either direction counts
p_value = 2 * stats.norm.sf(np.abs(z))

print(f"simulated A/A tests: {TESTS:,}")
# the last day is the planned end, day 14
print(f"significant at the planned end: {(p_value[:, -1] < 0.05).mean():.3f}")
print(f"significant on some day, checked daily: {(p_value < 0.05).any(axis=1).mean():.3f}")

# A sample ratio mismatch: the split was planned 50/50, but the groups came out unequal.
control, treatment = 28_000, 27_100
# the default expected share is one half, as in a 50/50 split
p = stats.binomtest(treatment, control + treatment).pvalue
print(f"sample ratio mismatch p: {p:.3f}" if p >= 0.001 else "sample ratio mismatch p: below 0.001")
