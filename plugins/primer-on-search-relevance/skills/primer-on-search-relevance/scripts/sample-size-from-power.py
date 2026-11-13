"""Kohavi et al.'s rule of thumb for users per group, its coefficient, and the users the store would need for smaller changes, assuming its 5% conversion rate. The prose's point rests on the two 'users per group for a change' lines, read against the coefficient line."""
from scipy import stats

SIGNIFICANCE, POWER = 0.05, 0.80
z = stats.norm.ppf(1 - SIGNIFICANCE / 2) + stats.norm.ppf(POWER)    # 1.96 + 0.84
print(f"coefficient for two groups: {2 * z ** 2:.1f}")                # rounds to the 16 of the rule of thumb


def users_per_group(variance, change):
    """Kohavi et al.'s rule of thumb: about 16 * variance / change**2 users in each group."""
    return 16 * variance / change ** 2


# Their worked examples: revenue per user (mean $3.75, standard deviation $30), and a 5% conversion rate,
# each with a 5% relative change to detect.
print(f"users per group, revenue: {users_per_group(30 ** 2, 0.05 * 3.75):,.0f}")
# a conversion rate's variance is p times (1 - p), here with p = 5%; the change is 5% of that rate
print(f"users per group, conversion: {users_per_group(0.05 * 0.95, 0.05 * 0.05):,.0f}")

# The store, assuming a 5% conversion rate like theirs: smaller changes need far more users.
for relative in [0.02, 0.01]:
    # the change in conversion, as an absolute rate: a relative change of this size in the 5% rate
    print(f"users per group for a {relative:.0%} change: {users_per_group(0.05 * 0.95, 0.05 * relative):,.0f}")
