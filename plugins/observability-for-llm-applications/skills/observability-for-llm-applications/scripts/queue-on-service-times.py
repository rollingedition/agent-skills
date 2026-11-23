"""Queue baseline day 1's recorded message times behind one first-come, first-served server at three loads, with seeded Poisson
arrivals and each message's service drawn from the recorded times. The number in system is walked from the queue's events and
checked against the arrival rate times the time in system, and the last check compares exponential service with the M/M/1 formula."""
from lib.dayrun import run_day
from lib.report import fmt_int, fmt_ms
from lib.stats import nearest_rank

from fractions import Fraction

import numpy as np

SEED, N, CHECK_N = 20261208, 50_000, 200_000                   # one seed; messages per run; the M/M/1 check's run
recorded = [run.replied_ns - run.arrived_ns for run in run_day("2026-12-08")]   # the day's 200 recorded message times
mean_service = sum(recorded) / len(recorded)


recorded_services = lambda rng, n: rng.choice(np.asarray(recorded, dtype=np.int64), n)   # resampled with replacement
exponential_services = lambda rng, n: rng.exponential(mean_service, n).round().astype(np.int64)


def simulate(rng, rho, n, services):
    """Serve n messages arriving at rate rho / mean_service. Returns arrivals, waits, times in system, the last finish
    and the total service time, in ns."""
    arrivals = np.cumsum(rng.exponential(mean_service / rho, n)).round().astype(np.int64).tolist()
    finish, waits, sojourn, busy = 0, [], [], 0
    for arrive, serve in zip(arrivals, services(rng, n).tolist()):
        start = max(arrive, finish)          # the server finishes the message before it, then starts this one
        finish = start + serve
        waits.append(start - arrive)
        sojourn.append(finish - arrive)
        busy += serve
    return arrivals, waits, sojourn, finish, busy


print("mean recorded message time:", fmt_ms(round(mean_service)))
for rho in (0.5, 0.8, 0.9):
    arrivals, waits, sojourn, finish, busy = simulate(np.random.Generator(np.random.PCG64(SEED)), rho, N, recorded_services)
    span = finish - arrivals[0]                                # first arrival to last departure
    # Each arrival adds one to the count in system and each departure takes one away; the area under the count is L times the span.
    area, count, when = 0, 0, arrivals[0]
    for moment, step in sorted([(a, 1) for a in arrivals] + [(a + s, -1) for a, s in zip(arrivals, sojourn)]):
        area, count, when = area + count * (moment - when), count + step, moment
    number, rate_times_time = Fraction(area, span), Fraction(N, span) * Fraction(sum(sojourn), N)   # L, and lambda W
    print(f"load {rho}, utilisation, computed: {busy / span:.2f}")
    print(f"load {rho}, wait before service, computed, p95 (n = {fmt_int(N)}):", fmt_ms(nearest_rank(waits, 95)))
    print(f"load {rho}, number in system, time average, computed: {float(number):.2f}")
    print(f"load {rho}, arrival rate times time in system, computed: {float(rate_times_time):.2f}")
    assert number == rate_times_time     # exact, with no tolerance: the window starts at the first arrival and ends at the last departure

# M/M/1: the mean time in system is 1 / (mu - lambda), which is mean_service / (1 - rho) for exponential service.
sojourn = simulate(np.random.Generator(np.random.PCG64(SEED)), 0.8, CHECK_N, exponential_services)[2]
simulated, formula = sum(sojourn) / CHECK_N, mean_service / (1 - 0.8)
print(f"exponential service, load 0.8, mean time in system, simulated (n = {fmt_int(CHECK_N)}):", fmt_ms(round(simulated)))
print("exponential service, load 0.8, mean time in system, formula:", fmt_ms(round(formula)))
assert abs(simulated - formula) / formula < 0.02
