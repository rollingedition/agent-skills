"""Each isolation design against the undefended baseline, on the dev set and on the held-out set, with the paired differences between them.

The chapter's claim that isolation cuts attacks rests on the attack success line for each design, and its claim that
isolation costs utility rests on the utility difference line. A difference is design minus baseline, so a negative
attack difference means fewer successes and a negative utility difference means fewer benign tasks answered. The dev
lines are the first run; the held-out lines name the split in their labels and come from the one held-out run.
"""
from lib import cases, replay, report, runs, scorers  # lib first: threads and seeds are fixed here

# Designs in sorted order, each with its label. Taint also acts on calls (the harness), so its label says so.
DESIGNS = [("design-dual-llm", "design (isolation)"),
           ("design-plan-then-execute", "design (isolation)"),
           ("design-taint", "design (isolation), also acts on calls")]


def scores(split, name, tasks, attacks):
    """Utility per benign task and attack success per case, in ID order, for one design or the baseline on a split."""
    rec = f"{name}-{split}" if name != "baseline" else f"baseline-{split}"  # replayed; no model is called
    model = replay.ReplayModel(rec)  # one model per recording: it reads its file once
    variant = None if name == "baseline" else name
    benign = runs.replay_tasks(rec, tasks, variant=variant, model=model)
    attack = runs.replay_cases(rec, attacks, variant=variant, model=model)
    utility = [scorers.utility(task, benign[task.id]) for task in tasks]
    success = [scorers.attack_success(case, attack[case.id]) for case in attacks]
    return utility, success


def main():
    for split, prefix in [("dev", ""), ("held-out", "held-out ")]:  # dev keeps its labels; held-out names its split
        tasks, attacks = cases.load_tasks(split), cases.load_cases(split)  # 15 benign tasks, 60 attack cases
        assert (len(tasks), len(attacks)) == (15, 60), split  # the counts the prose names
        base_utility, base_success = scores(split, "baseline", tasks, attacks)
        report.rate_lines(f"{prefix}baseline utility, {len(tasks)} benign tasks", base_utility)
        report.rate_lines(f"{prefix}baseline attack success, {len(attacks)} cases", base_success)
        for name, label in DESIGNS:  # sorted by design, as the printed lines must be
            utility, success = scores(split, name, tasks, attacks)
            print(f"design: {name}{'' if split == 'dev' else ', held-out'}")
            print(f"label: {label}")
            report.rate_lines(f"{prefix}utility, {name}, {len(tasks)} benign tasks", utility)
            report.rate_lines(f"{prefix}attack success, {name}, {len(attacks)} cases", success)
            report.paired(f"{prefix}utility difference from baseline, {name}", base_utility, utility)
            report.paired(f"{prefix}attack success difference from baseline, {name}", base_success, success)
            report.newly_lines(f"{prefix}newly blocked, {name}", f"{prefix}newly allowed, {name}", base_success, success)
            if split == "dev":  # the chapter's claims are checked on dev; held-out is printed as it is (the prose says so)
                assert sum(success) < sum(base_success), name
                assert sum(utility) < sum(base_utility), name


if __name__ == "__main__":
    main()
