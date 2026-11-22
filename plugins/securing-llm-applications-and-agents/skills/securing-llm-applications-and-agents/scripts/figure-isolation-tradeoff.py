"""Each isolation design on the dev split as one point, attack success against utility, with 95% bootstrap intervals in both directions.
The prose rests on the printed rates and intervals, which are the same numbers the points are drawn from."""
from lib import cases, replay, report, runs, scorers, stats  # lib first: threads and seeds are fixed here
from lib.figures import ACCENT, INK, new_figure, save

DESIGNS = ["design-dual-llm", "design-plan-then-execute", "design-taint"]  # sorted, as isolation-paired prints them
# Each point's label as the chapter's table names it, its offset in points from the point, and its alignment, clear of the other bars.
LABEL_AT = {"baseline": ("undefended", 6, 5, "left", "bottom"), "design-dual-llm": ("dual LLM", 4, -8, "left", "top"), "design-plan-then-execute": ("plan-then-execute", 110, 0, "left", "center"), "design-taint": ("taint labels", 6, 5, "left", "bottom")}


def scores(name, tasks, attacks):
    """Utility per benign task and attack success per case, in ID order, for the baseline or one design on dev."""
    rec = f"{name}-dev"  # the baseline's recording is baseline-dev, and each design's is design-*-dev
    model = replay.ReplayModel(rec)  # one model per recording: it reads its file once
    variant = None if name == "baseline" else name  # None replays the undefended prompt, a design names its own
    benign = runs.replay_tasks(rec, tasks, variant=variant, model=model)
    attack = runs.replay_cases(rec, attacks, variant=variant, model=model)
    return [scorers.utility(t, benign[t.id]) for t in tasks], [scorers.attack_success(c, attack[c.id]) for c in attacks]


def interval(flags):
    """The 95% bootstrap interval of the rate of `flags`, in points."""
    lo, hi = stats.bootstrap_mean([1.0 if flag else 0.0 for flag in flags])  # one 0 or 1 per item
    return 100 * lo, 100 * hi


def main():
    tasks, attacks = cases.load_tasks("dev"), cases.load_cases("dev")  # 15 benign tasks, 60 attack cases
    assert (len(tasks), len(attacks)) == (15, 60)  # the counts the prose names
    fig, ax = new_figure(height=3.4)
    u_lo, u_hi, a_lo, a_hi = {}, {}, {}, {}  # the printed intervals, in points, by run
    for name in ["baseline"] + DESIGNS:
        utility, success = scores(name, tasks, attacks)
        base = name == "baseline"  # the labels isolation-paired prints for the undefended run, and each design's
        report.rate_lines("baseline utility, 15 benign tasks" if base else f"utility, {name}, 15 benign tasks", utility)
        report.rate_lines("baseline attack success, 60 cases" if base else f"attack success, {name}, 60 cases", success)
        x, y = 100 * sum(success) / len(success), 100 * sum(utility) / len(utility)  # attack success, utility
        (a_lo[name], a_hi[name]), (u_lo[name], u_hi[name]) = interval(success), interval(utility)
        # The undefended run in ink, plan-then-execute in muted, dual LLM and taint in the accent: its bars stay apart from taint's, both at 6.7% utility.
        color = INK if name == "baseline" else ACCENT  # the undefended run in ink, each design in the accent, as the prompt-defence figure does
        _, caps, bars = ax.errorbar(x, y, xerr=[[x - a_lo[name]], [a_hi[name] - x]], yerr=[[y - u_lo[name]], [u_hi[name] - y]], fmt="o", color=color, markersize=4, capsize=2, elinewidth=1)
        if name == "design-plan-then-execute": [a.set_linestyle("--") for a in (*caps, *bars)]  # its bar meets taint's lower cap
        text, dx, dy, ha, va = LABEL_AT[name]
        ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", color=color, ha=ha, va=va)
    # The two claims the figure and its prose make, checked on the printed intervals.
    assert u_lo["design-dual-llm"] > max(u_hi["design-taint"], u_hi["design-plan-then-execute"])  # utility splits the runs
    assert all(a_lo[d] < a_hi["baseline"] and a_hi[d] > a_lo["baseline"] for d in DESIGNS)  # attack intervals overlap
    ax.set(xlim=(-1, 25), ylim=(0, 105), xlabel="attack success, percent of 60 dev cases", ylabel="utility, percent of 15 dev benign tasks")
    save(fig, "isolation-tradeoff")


if __name__ == "__main__":
    main()
