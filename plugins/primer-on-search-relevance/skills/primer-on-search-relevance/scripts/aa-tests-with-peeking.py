import numpy as np
from scipy import stats

# Assumptions for the simulation, not the store's data: 2,000 shoppers a day in each group,
# 5% of them buy, and the test is planned to run 14 days. Both groups get the same search (an A/A test).
TESTS, DAYS, SHOPPERS_PER_DAY, CONVERSION = 2000, 14, 2000, 0.05

rng = np.random.default_rng(2026)
buyers = rng.binomial(SHOPPERS_PER_DAY, CONVERSION, size=(TESTS, DAYS, 2)).cumsum(axis=1)   # running totals
shoppers = SHOPPERS_PER_DAY * np.arange(1, DAYS + 1)[None, :]                               # per group, by day
rate_a, rate_b = buyers[..., 0] / shoppers, buyers[..., 1] / shoppers
pooled = (rate_a + rate_b) / 2
z = (rate_b - rate_a) / np.sqrt(pooled * (1 - pooled) * 2 / shoppers)    # two-proportion z-test, every day
p_value = 2 * stats.norm.sf(np.abs(z))

print(f"simulated A/A tests: {TESTS:,}")
print(f"significant at the planned end: {(p_value[:, -1] < 0.05).mean():.3f}")
print(f"significant on some day, checked daily: {(p_value < 0.05).any(axis=1).mean():.3f}")

# A sample ratio mismatch: the split was planned 50/50, but the groups came out unequal.
control, treatment = 28_000, 27_100
p = stats.binomtest(treatment, control + treatment).pvalue
print(f"sample ratio mismatch p: {p:.3f}" if p >= 0.001 else "sample ratio mismatch p: below 0.001")
