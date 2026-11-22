"""The gate fails a run with the defence off, on its attack check, and passes a one-case change that is within noise.

The point rests on `failed checks, regressed run` being the attack check alone, and on the flipped run passing both
checks: one case of 60 moves the upper bound by less than the one-case allowance the stored ceiling already includes.
"""
from lib import gate  # lib first: threads and seeds are fixed here


def show(label, checks):
    """One line per check, PASS or FAIL with the numbers it used, under the run's label."""
    for check in checks:
        print(f"{label}, {check.name}: {'PASS' if check.passed else 'FAIL'} ({check.numbers})")


def main():
    thresholds = gate.Thresholds.load()  # the ceiling and floor that gate-thresholds chose from dev
    print(f"ceiling, stored: {thresholds.attack_upper_max:.2f}")
    print(f"floor, stored: {thresholds.utility_lower_min:+.2f}")
    baseline = gate.dev_run("baseline")
    defended = gate.dev_run("enforce-args")

    # The regression: the rule is switched off, so the run's replies are the undefended baseline's. Its utility is
    # the baseline's own, so the utility check passes trivially; only the attack check can catch the change.
    regressed = gate.Run("regressed", baseline.attack, baseline.utility)
    regressed_checks = gate.gate(regressed, baseline, thresholds)
    show("regressed run", regressed_checks)
    failed = [check.name for check in regressed_checks if not check.passed]
    print(f"failed checks, regressed run: {len(failed)}")
    assert failed == [regressed_checks[0].name], "the regressed run must fail on attack success alone"
    assert regressed_checks[1].passed, "the utility check must pass when utility is unchanged"

    # A change within noise: one case the defended run holds now succeeds. The first such case in ID order is flipped
    # in this example's copy of the run; the data files are not changed.
    held = sorted(case for case, hit in defended.attack.items() if not hit)
    flipped_case = held[0]
    flipped = gate.Run("flipped", {**defended.attack, flipped_case: True}, defended.utility)
    print(f"flipped case: {flipped_case}")
    _, _, before_hi = gate.attack_interval(defended)
    _, _, after_hi = gate.attack_interval(flipped)
    print(f"attack success upper bound, defended: {before_hi:.1%}")
    print(f"attack success upper bound, one case flipped: {after_hi:.1%}")
    flipped_checks = gate.gate(flipped, baseline, thresholds)
    show("flipped run", flipped_checks)
    assert all(check.passed for check in flipped_checks), "a one-case change within noise must not fail the gate"

    # The sensitivity: how many of the dev run's cases may succeed before the attack check fails. The sweep gives the
    # same count of successes to the first k cases in ID order, and runs the same attack check on each count.
    cases = sorted(defended.attack)
    passing = []
    for k in range(len(cases) + 1):
        swept = gate.Run(f"{k} successes", {case: i < k for i, case in enumerate(cases)}, defended.utility)
        if gate.gate(swept, baseline, thresholds)[0].passed:
            passing.append(k)
    print(f"largest count of successes that passes the attack check, of {len(cases)} cases: {max(passing)}")
    print(f"smallest count of successes that fails the attack check: {max(passing) + 1}")


if __name__ == "__main__":
    main()
