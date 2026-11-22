"""The gate reads the upper bound of attack success, so its pass line falls well below the count where the rate reaches the ceiling.

The sweep is the regression example's: the first k dev cases in ID order succeed, and the attack check runs on each count.
The figure draws the observed rate and the bound against k, with the stored ceiling as a line.
"""
from lib import gate  # lib first: threads and seeds are fixed here
from lib.figures import ACCENT, INK, MUTED, new_figure, save


def main():
    thresholds = gate.Thresholds.load()  # the ceiling that gate-thresholds chose from dev
    baseline = gate.dev_run("baseline")
    defended = gate.dev_run("enforce-args")
    cases = sorted(defended.attack)

    counts, rates, bounds, passing = [], [], [], []
    for k in range(13):  # 0 to 12 of the 60 cases: the region where the pass line falls
        swept = gate.Run(f"{k} successes", {case: i < k for i, case in enumerate(cases)}, defended.utility)
        rate, _, hi = gate.attack_interval(swept)  # the rate and the upper bound the check reads
        counts.append(k)
        rates.append(100 * rate)
        bounds.append(100 * hi)
        if gate.gate(swept, baseline, thresholds)[0].passed:
            passing.append(k)

    ceiling = 100 * thresholds.attack_upper_max
    largest = max(passing)
    smallest_fail = min(k for k in counts if k not in passing)
    # The count where the rate alone would reach the ceiling, for comparison with the pass line the bound sets.
    rate_reaches = next(k for k, r in zip(counts, rates) if r >= ceiling)
    print(f"ceiling, stored: {ceiling:.1f}%")
    print(f"largest count that passes, of {len(cases)} cases: {largest}")
    print(f"smallest count that fails, of {len(cases)} cases: {smallest_fail}")
    print(f"upper bound at the largest passing count: {bounds[largest]:.1f}%")
    print(f"upper bound at the smallest failing count: {bounds[smallest_fail]:.1f}%")
    print(f"count at which the rate alone reaches the ceiling: {rate_reaches}")

    fig, ax = new_figure(height=3.2)
    ax.plot(counts, rates, color=INK, marker="o", markersize=3, label="observed rate")
    ax.plot(counts, bounds, color=ACCENT, marker="o", markersize=3, label="upper bound of the interval")
    ax.axhline(ceiling, color=MUTED, linestyle="--", label="stored ceiling")
    ax.axvline(largest, color=MUTED, linestyle=":", linewidth=0.8, label="largest count that passes")
    ax.set_xlabel(f"successes among {len(cases)} dev cases")
    ax.set_ylabel("percent")
    ax.set_xticks(counts)
    ax.legend(loc="upper left")
    save(fig, "gate-boundary")


if __name__ == "__main__":
    main()
