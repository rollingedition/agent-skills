"""The gate's thresholds come from dev, once, and the defended run passes both checks on its interval bounds.

The point rests on `attack success, upper bound at most the ceiling: PASS`: the defended run's upper bound is at or
below the ceiling, so the gate passes on the interval, not on the point rate.

This example writes nothing. recordings/gate_thresholds.py wrote examples/data/gate/thresholds.json once; here the
stored file is read, the same rule (lib/gate.py choose) is run again on dev, and the two must be equal.
"""
from lib import gate  # lib first: threads and seeds are fixed here


def main():
    baseline = gate.dev_run("baseline")
    defended = gate.dev_run("enforce-args")  # the defended configuration the gate protects
    print(f"attack cases compared: {len(defended.attack)}")
    print(f"benign tasks compared: {len(defended.utility)}")
    thresholds, n = gate.choose(defended, baseline)
    print(f"dev attack success, defended: {n['rate']:.1%}, upper bound {n['hi']:.1%}")
    print(f"dev attack success, upper bound with one more case: {n['one_hi']:.1%}")
    print(f"rule, ceiling: that bound rounded up to whole points: {n['ceiling']:.2f}")
    print(f"dev utility difference, lower bound: {n['lo']:+.1%}")
    print(f"rule, floor: lower bound rounded down to {gate.STEP:.0%} steps: {n['floor']:+.2f}")
    stored = gate.Thresholds.load()
    assert stored == thresholds, f"stored thresholds {stored} differ from the dev choice {thresholds}"
    print("stored thresholds: match the dev choice")
    checks = gate.gate(defended, baseline, stored)
    for check in checks:  # one line per check: its name, PASS or FAIL, and the numbers it used
        print(f"{check.name}: {'PASS' if check.passed else 'FAIL'} ({check.numbers})")
    assert all(check.passed for check in checks), "the defended run fails its own gate"


if __name__ == "__main__":
    main()
