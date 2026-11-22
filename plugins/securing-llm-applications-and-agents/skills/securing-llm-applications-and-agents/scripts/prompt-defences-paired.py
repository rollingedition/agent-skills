"""Five prompt-level defences, each replayed on the dev split and paired with the undefended baseline. The line the prose
rests on is `prompt-warning, attack success, 60 dev cases`, with its paired difference beneath it, per case, with interval.
"""
from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

# Each variant is replayed with its row of lib/variants.py: its hooks, and the prompt its recording was made with.
VARIANTS = ("prompt-datamark", "prompt-delimiters", "prompt-encode", "prompt-repeat", "prompt-warning")


def run_dev(recording, variant=None):
    """The 15 dev benign tasks and 60 dev cases of one recording: utility by task ID, attack success by case ID."""
    benign, attacks = cases.load_tasks("dev"), cases.load_cases("dev")
    assert (len(benign), len(attacks)) == (15, 60), "the dev split has changed"  # the counts the prose names
    traces = runs.replay_tasks(recording, benign, variant=variant)
    case_traces = runs.replay_cases(recording, attacks, variant=variant)
    return ({t.id: scorers.utility(t, traces[t.id]) for t in benign},
            {c.id: scorers.attack_success(c, case_traces[c.id]) for c in attacks})


def main():
    base_utility, base_success = run_dev("baseline-dev")  # no hooks: the undefended run
    case_ids, task_ids = sorted(base_success), sorted(base_utility)
    before = [base_success[c] for c in case_ids]
    for name in VARIANTS:
        utility, success = run_dev(f"{name}-dev", name)
        report.rate_lines(f"{name}, utility, 15 dev benign tasks", [utility[t] for t in task_ids],
                          f"{name}, utility interval")
        report.rate_lines(f"{name}, attack success, 60 dev cases", [success[c] for c in case_ids],
                          f"{name}, attack success interval")
        after = [success[c] for c in case_ids]
        report.paired(f"{name}, paired difference in attack success", before, after)
        report.paired(f"{name}, paired difference in utility", [base_utility[t] for t in task_ids],
                      [utility[t] for t in task_ids])
        # Cases the baseline let through that the variant stops, and the reverse.
        report.newly_lines(f"{name}, newly blocked, dev cases", f"{name}, newly let through, dev cases", before, after)


if __name__ == "__main__":
    main()
