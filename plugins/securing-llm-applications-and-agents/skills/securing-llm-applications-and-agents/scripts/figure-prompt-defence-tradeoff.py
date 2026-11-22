"""Draw each prompt defence's dev attack success against its dev utility, with the undefended baseline and 95% bootstrap intervals.
The lines name each run's attack success and utility with their counts, which the prose rests on.
"""
from lib import cases, runs, scorers, stats  # lib first: threads and seeds are fixed here
from lib.figures import ACCENT, INK, new_figure, save

# Label places in data units, beside their points. The warning's point is the baseline's, so one label names both.
LABELS = {"baseline": (15.5, 88.0), "prompt-delimiters": (1.5, 101.0), "prompt-datamark": (6.5, 76.0),
          "prompt-encode": (1.2, 57.0), "prompt-repeat": (8.5, 12.0)}
# Plain names, the words the chapter's prose uses. The run IDs stay in the printed lines and the bindings.
NAMES = {"baseline": "undefended and warning", "prompt-delimiters": "delimiters", "prompt-datamark": "datamarking", "prompt-encode": "encoding", "prompt-repeat": "repeating the request"}


def run_dev(name):
    """Utility of the 15 dev benign tasks and attack success of the 60 dev cases, in ID order, as 1s and 0s."""
    recording, variant = ("baseline-dev", None) if name == "baseline" else (f"{name}-dev", name)
    benign, attacks = cases.load_tasks("dev"), cases.load_cases("dev")
    assert (len(benign), len(attacks)) == (15, 60), "the dev split has changed"  # the counts the prose names
    traces = runs.replay_tasks(recording, benign, variant=variant)
    case_traces = runs.replay_cases(recording, attacks, variant=variant)
    utility = [float(scorers.utility(t, traces[t.id])) for t in sorted(benign, key=lambda t: t.id)]
    success = [float(scorers.attack_success(c, case_traces[c.id])) for c in sorted(attacks, key=lambda c: c.id)]
    return utility, success


def rate(label, flags):
    """Print a rate with its counts and bootstrap interval, as the paired example does; return it in points."""
    lo, hi = stats.bootstrap_mean(flags)  # the same interval the paired example prints, from the same seed
    print(f"{label}: {stats.pct(int(sum(flags)), len(flags))}\n{label}, interval: {stats.interval_pct(lo, hi)}")
    return 100 * sum(flags) / len(flags), 100 * lo, 100 * hi


def main():
    fig, ax = new_figure(height=3.8)
    # the baseline last, so its ink bars sit on the warning's identical ones
    for name in ("prompt-warning", "prompt-delimiters", "prompt-datamark", "prompt-encode", "prompt-repeat", "baseline"):
        utility, success = run_dev(name)
        x, y = rate(f"{name}, attack success, 60 dev cases", success), rate(f"{name}, utility, 15 dev benign tasks", utility)
        color = INK if name == "baseline" else ACCENT  # the baseline in ink, each defence in the accent
        _, caps, bars = ax.errorbar(x[0], y[0], xerr=[[x[0] - x[1]], [x[2] - x[0]]], yerr=[[y[0] - y[1]], [y[2] - y[0]]], fmt="o",
                                    color=color, capsize=2, elinewidth=0.9, zorder=3 if name == "baseline" else 2,
                                    markersize=9 if name == "prompt-warning" else 5,  # the warning's ring shows around the baseline's point
                                    markerfacecolor="none" if name == "prompt-warning" else color)
        if name == "prompt-delimiters": [a.set_linestyle("--") for a in (*caps, *bars)]  # its bars lie on the baseline's
        if name in LABELS:  # the warning has no label of its own: the baseline's label says it coincides
            ax.annotate(NAMES[name], (x[0], y[0]), xytext=LABELS[name][:2], ha="left", va="center", color=color,
                        arrowprops=dict(arrowstyle="-", color=INK, linewidth=0.5, shrinkA=4, shrinkB=2))
    assert run_dev("prompt-warning") == run_dev("baseline"), "the warning's point is the baseline's"  # the prose says so
    ax.set(xlabel="attack success, percent of 60 dev cases", ylabel="utility, percent of 15 dev benign tasks",
           xlim=(-1, 25), ylim=(0, 105))
    save(fig, "prompt-defence-tradeoff")


if __name__ == "__main__":
    main()
