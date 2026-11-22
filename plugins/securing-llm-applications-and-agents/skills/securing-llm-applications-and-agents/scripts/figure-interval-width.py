"""Draw how wide the bootstrap interval is for an observed rate of one half, as the number of cases grows from 10 to 200.

The prose rests on the widths printed at 20, 60, 100 and 200 cases: the interval narrows fast at first, then slowly.
No model and no recording are used here.
"""
from lib import stats  # lib first: threads and seeds are fixed here
from lib.figures import ACCENT, MUTED, new_figure, save

SIZES = list(range(10, 201, 10))   # set sizes, in steps of 10 cases
MARKED = (20, 60, 100, 200)        # the rough set of 20, and the three larger sizes the prose quotes


def width(successes, total):
    """The width of the bootstrap interval for `successes` of `total` cases, in points."""
    values = [1.0] * successes + [0.0] * (total - successes)  # one item per case, 1 for a success
    lo, hi = stats.bootstrap_mean(values)
    return 100 * (hi - lo)


def main():
    widths = [width(size // 2, size) for size in SIZES]   # half the cases succeed at every size
    for size in MARKED:
        print(f"interval width at half success, {size} cases: {widths[SIZES.index(size)]:.1f} points")
    fig, ax = new_figure(height=2.6)
    ax.plot(SIZES, widths, color=ACCENT, marker="o", markersize=3, label="width of the 95% interval, half the cases succeed")
    ax.plot(MARKED, [widths[SIZES.index(s)] for s in MARKED], linestyle="none", marker="o", markersize=7,
            markerfacecolor="none", color=MUTED, label="20, 60, 100 and 200 cases")
    ax.set_xlabel("cases in the set")
    ax.set_ylabel("interval width, points")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    save(fig, "interval-width")


if __name__ == "__main__":
    main()
