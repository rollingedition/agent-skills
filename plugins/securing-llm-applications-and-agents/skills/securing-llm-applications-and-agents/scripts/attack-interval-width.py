"""How wide a bootstrap interval is on 20 cases, and on 100 and 200, for the same observed rate.

The chapter's caution about small sets rests on the first line: an observed 10 of 20 gives an interval about
40 points wide, against 13.5 points for 100 of 200 at the same rate. No model and no recording are used here.
"""
from lib import stats  # lib first: threads and seeds are fixed here


def width(successes, total):
    """The width of the bootstrap interval for a rate observed as `successes` of `total` items, in points."""
    values = [1.0] * successes + [0.0] * (total - successes)  # one item per case, 1 for a success
    lo, hi = stats.bootstrap_mean(values)
    return 100 * (hi - lo)


def main():
    for successes, total in ((10, 20), (50, 100), (100, 200)):
        print(f"interval width, {successes} of {total}: {width(successes, total):.1f} points")


if __name__ == "__main__":
    main()
